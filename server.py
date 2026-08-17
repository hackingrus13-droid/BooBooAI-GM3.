#!/usr/bin/env python3
"""BooBooAI-GM3 local orchestration server.

Standard-library-only HTTP server that:
- serves the existing static UI;
- exposes /v1/info;
- exposes the frontend-compatible /v1/ultraplinian/completions SSE endpoint;
- fans one request out to configured OpenAI-compatible local model servers;
- scores successful candidates deterministically and returns the winner.

Model endpoints are configured with MODEL_ENDPOINTS, for example:
MODEL_ENDPOINTS='fast=http://127.0.0.1:8080/v1;smart=http://127.0.0.1:8081/v1'

A single llama.cpp server is enough to get started. Additional independent
endpoints can be added later without changing the frontend.
"""

from __future__ import annotations

import json
import os
import queue
import re
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8080"))
REQUEST_TIMEOUT = float(os.getenv("MODEL_TIMEOUT", "120"))
DEFAULT_TIER_LIMITS = {"fast": 12, "standard": 20, "full": 27}


def parse_endpoints() -> list[dict[str, str]]:
    raw = os.getenv("MODEL_ENDPOINTS", "local=http://127.0.0.1:8080/v1")
    result: list[dict[str, str]] = []
    for item in raw.split(";"):
        item = item.strip()
        if not item or "=" not in item:
            continue
        name, url = item.split("=", 1)
        name, url = name.strip(), url.strip().rstrip("/")
        if name and url:
            result.append({"name": name, "url": url})
    return result


ENDPOINTS = parse_endpoints()


def json_bytes(obj: Any) -> bytes:
    return json.dumps(obj, separators=(",", ":")).encode("utf-8")


def sse(event: str, payload: dict[str, Any]) -> bytes:
    return f"event: {event}\ndata: {json.dumps(payload, separators=(',', ':'))}\n\n".encode("utf-8")


def safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.:/-]", "_", value)[:160]


def candidate_score(text: str, latency_ms: float) -> float:
    """Deterministic baseline quality heuristic, not a claim of intelligence.

    The score rewards useful structure and sufficient content while applying a
    small latency penalty. It intentionally avoids pretending to be a semantic
    judge. A future judge model can be plugged in without changing the API.
    """
    stripped = text.strip()
    if not stripped:
        return 0.0
    length = len(stripped)
    sentence_bonus = min(stripped.count(".") + stripped.count("?") + stripped.count("!"), 12) * 1.5
    structure_bonus = min(stripped.count("\n") + stripped.count("- "), 8) * 1.0
    length_score = min(length / 120.0, 30.0)
    latency_penalty = min(latency_ms / 5000.0, 12.0)
    return round(max(0.0, 50.0 + length_score + sentence_bonus + structure_bonus - latency_penalty), 2)


def extract_text(data: dict[str, Any]) -> str:
    choices = data.get("choices") or []
    if not choices:
        return ""
    choice = choices[0] or {}
    message = choice.get("message") or {}
    if isinstance(message.get("content"), str):
        return message["content"]
    if isinstance(choice.get("text"), str):
        return choice["text"]
    return ""


def call_model(endpoint: dict[str, str], messages: list[dict[str, str]]) -> dict[str, Any]:
    url = endpoint["url"] + "/chat/completions"
    body = {
        "model": endpoint["name"],
        "messages": messages,
        "stream": False,
        "temperature": float(os.getenv("MODEL_TEMPERATURE", "0.2")),
    }
    request = urllib.request.Request(
        url,
        data=json_bytes(body),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT) as response:
            raw = response.read()
        latency_ms = (time.perf_counter() - started) * 1000
        data = json.loads(raw.decode("utf-8"))
        text = extract_text(data)
        return {
            "model": safe_name(endpoint["name"]),
            "success": bool(text.strip()),
            "content": text,
            "score": candidate_score(text, latency_ms),
            "duration_ms": round(latency_ms, 1),
        }
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        latency_ms = (time.perf_counter() - started) * 1000
        return {
            "model": safe_name(endpoint["name"]),
            "success": False,
            "content": "",
            "score": 0,
            "duration_ms": round(latency_ms, 1),
            "error": str(exc),
        }


class Handler(BaseHTTPRequestHandler):
    server_version = "BooBooAI-GM3/1.0"

    def log_message(self, fmt: str, *args: Any) -> None:
        print(f"[{self.log_date_time_string()}] {fmt % args}")

    def send_json(self, status: int, obj: dict[str, Any]) -> None:
        body = json_bytes(obj)
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path == "/v1/info":
            self.send_json(200, {
                "name": "BooBooAI-GM3",
                "engine": "ULTRAPLINIAN",
                "version": "1.0.0",
                "backend": "local-orchestrator",
                "model_endpoints": len(ENDPOINTS),
                "tiers": DEFAULT_TIER_LIMITS,
                "features": ["parallel-racing", "deterministic-baseline-scoring", "sse", "local-openai-compatible-models"],
            })
            return

        if self.path in ("/", "/index.html"):
            try:
                body = (ROOT / "index.html").read_bytes()
            except OSError as exc:
                self.send_json(500, {"error": str(exc)})
                return
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)
            return

        self.send_json(404, {"error": "not found"})

    def do_POST(self) -> None:
        if self.path != "/v1/ultraplinian/completions":
            self.send_json(404, {"error": "not found"})
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            body = json.loads(self.rfile.read(length).decode("utf-8"))
        except (ValueError, json.JSONDecodeError):
            self.send_json(400, {"error": "invalid JSON request"})
            return

        messages = body.get("messages")
        tier = body.get("tier", "fast")
        if not isinstance(messages, list) or not messages:
            self.send_json(400, {"error": "messages must be a non-empty array"})
            return
        if tier not in DEFAULT_TIER_LIMITS:
            self.send_json(400, {"error": f"unknown tier: {tier}"})
            return

        selected = ENDPOINTS[:DEFAULT_TIER_LIMITS[tier]]
        if not selected:
            self.send_json(503, {"error": "no model endpoints configured"})
            return

        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache, no-store")
        self.send_header("Connection", "keep-alive")
        self.end_headers()

        self.wfile.write(sse("race:start", {"models_queried": len(selected), "tier": tier}))
        self.wfile.flush()

        results: list[dict[str, Any]] = []
        lock = threading.Lock()
        events: queue.Queue[dict[str, Any]] = queue.Queue()

        def worker(endpoint: dict[str, str]) -> None:
            result = call_model(endpoint, messages)
            with lock:
                results.append(result)
            events.put(result)

        threads = [threading.Thread(target=worker, args=(ep,), daemon=True) for ep in selected]
        for thread in threads:
            thread.start()

        responded = 0
        while responded < len(threads):
            try:
                result = events.get(timeout=REQUEST_TIMEOUT + 5)
            except queue.Empty:
                break
            responded += 1
            self.wfile.write(sse("race:model", {
                "model": result["model"],
                "success": result["success"],
                "score": result["score"],
                "models_responded": responded,
                "models_total": len(selected),
            }))
            self.wfile.flush()

        successful = [r for r in results if r["success"]]
        if not successful:
            self.wfile.write(sse("race:error", {"error": "all configured model endpoints failed"}))
            self.wfile.write(b"data: [DONE]\n\n")
            self.wfile.flush()
            return

        successful.sort(key=lambda r: (-r["score"], r["duration_ms"], r["model"]))
        winner = successful[0]
        self.wfile.write(sse("race:leader", {
            "model": winner["model"],
            "score": winner["score"],
            "content": winner["content"],
        }))
        self.wfile.flush()

        rankings = sorted(results, key=lambda r: (-r["score"], r["duration_ms"], r["model"]))
        self.wfile.write(sse("race:complete", {
            "response": winner["content"],
            "winner": {
                "model": winner["model"],
                "score": winner["score"],
                "duration_ms": winner["duration_ms"],
            },
            "race": {"rankings": [
                {"model": r["model"], "score": r["score"], "success": r["success"]}
                for r in rankings
            ]},
        }))
        self.wfile.write(b"data: [DONE]\n\n")
        self.wfile.flush()


def main() -> None:
    print(f"BooBooAI-GM3 ULTRAPLINIAN listening on http://{HOST}:{PORT}")
    print(f"Configured model endpoints: {len(ENDPOINTS)}")
    for ep in ENDPOINTS:
        print(f"  - {ep['name']}: {ep['url']}")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()


if __name__ == "__main__":
    main()
