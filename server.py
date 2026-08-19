#!/usr/bin/env python3
"""BooBooAI-GM3 local orchestration server.

Standard-library-only local HTTP server. It preserves the existing
ULTRAPLINIAN frontend contract while adding governed behavior, health,
capability, and model-discovery endpoints.
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

from booboo.governance import audit, policy_snapshot, system_prompt

ROOT = Path(__file__).resolve().parent
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8080"))
REQUEST_TIMEOUT = float(os.getenv("MODEL_TIMEOUT", "120"))
TIER_LIMITS = {"fast": 12, "standard": 20, "full": 27}


def parse_endpoints() -> list[dict[str, str]]:
    raw = os.getenv("MODEL_ENDPOINTS", "local=http://127.0.0.1:8081/v1")
    result: list[dict[str, str]] = []
    for item in raw.split(";"):
        if "=" not in item:
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
    return f"event: {event}\ndata: {json.dumps(payload, separators=(',', ':'))}\n\n".encode()


def safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.:/-]", "_", value)[:160]


def candidate_score(text: str, latency_ms: float) -> float:
    """Transparent baseline score; not a semantic-quality claim."""
    text = text.strip()
    if not text:
        return 0.0
    length_score = min(len(text) / 120.0, 30.0)
    sentence_bonus = min(sum(text.count(x) for x in ".?!"), 12) * 1.5
    structure_bonus = min(text.count("\n") + text.count("- "), 8)
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
    text = choice.get("text", "")
    return text if isinstance(text, str) else ""


def probe_endpoint(endpoint: dict[str, str]) -> dict[str, Any]:
    request = urllib.request.Request(
        endpoint["url"] + "/models",
        headers={"Accept": "application/json"},
        method="GET",
    )
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=3) as response:
            data = json.loads(response.read().decode("utf-8"))
        models = [
            item.get("id")
            for item in data.get("data", [])
            if isinstance(item, dict) and item.get("id")
        ]
        return {
            "name": safe_name(endpoint["name"]),
            "url": endpoint["url"],
            "reachable": True,
            "models": models,
            "latency_ms": round((time.perf_counter() - started) * 1000, 1),
        }
    except Exception as exc:
        return {
            "name": safe_name(endpoint["name"]),
            "url": endpoint["url"],
            "reachable": False,
            "models": [],
            "latency_ms": round((time.perf_counter() - started) * 1000, 1),
            "error": str(exc),
        }


def model_status() -> list[dict[str, Any]]:
    return [probe_endpoint(endpoint) for endpoint in ENDPOINTS]


def call_model(endpoint: dict[str, str], messages: list[dict[str, str]]) -> dict[str, Any]:
    request = urllib.request.Request(
        endpoint["url"] + "/chat/completions",
        data=json_bytes({
            "model": endpoint["name"],
            "messages": messages,
            "stream": False,
            "temperature": float(os.getenv("MODEL_TEMPERATURE", "0.2")),
        }),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT) as response:
            data = json.loads(response.read().decode("utf-8"))
        latency_ms = (time.perf_counter() - started) * 1000
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
    server_version = "BooBooAI-GM3/1.1"

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
        path = self.path.split("?", 1)[0]

        if path == "/v1/info":
            statuses = model_status()
            reachable = sum(1 for item in statuses if item["reachable"])
            self.send_json(200, {
                "name": "BooBooAI-GM3",
                "engine": "ULTRAPLINIAN",
                "version": "1.1.0",
                "backend": "local-orchestrator",
                "configured_model_endpoints": len(ENDPOINTS),
                "reachable_model_endpoints": reachable,
                "tiers": TIER_LIMITS,
                "features": [
                    "parallel-racing",
                    "transparent-baseline-scoring",
                    "sse",
                    "local-openai-compatible-models",
                    "governed-behavior",
                    "verified-capability-reporting",
                ],
            })
            return

        if path == "/api/health":
            statuses = model_status()
            self.send_json(200, {
                "success": True,
                "state": "RUNNING",
                "service": "browser_interface",
                "server": "BooBooAI-GM3",
                "model_endpoints_configured": len(ENDPOINTS),
                "model_endpoints_reachable": sum(1 for item in statuses if item["reachable"]),
            })
            return

        if path == "/api/governance":
            self.send_json(200, {
                "success": True,
                "governance": policy_snapshot(),
            })
            return

        if path == "/api/models":
            statuses = model_status()
            self.send_json(200, {
                "success": True,
                "configured": len(ENDPOINTS),
                "reachable": sum(1 for item in statuses if item["reachable"]),
                "models": statuses,
            })
            return

        if path == "/api/diagnostics":
            statuses = model_status()
            report = {
                "system": "BooBooAI-GM3",
                "state": "VERIFIED",
                "server": {
                    "host": HOST,
                    "port": PORT,
                    "browser": f"http://{HOST}:{PORT}/",
                },
                "governance": policy_snapshot(),
                "models": {
                    "configured": len(ENDPOINTS),
                    "reachable": sum(1 for item in statuses if item["reachable"]),
                    "providers": statuses,
                },
                "knowledge": {
                    "library_exists": (ROOT / "knowledge" / "library").exists(),
                    "state": "DETECTED_NOT_INDEXED",
                },
                "overall_state": "PARTIALLY VERIFIED" if not any(item["reachable"] for item in statuses) else "VERIFIED",
            }
            audit("diagnostics_requested", {"reachable_models": report["models"]["reachable"]})
            self.send_json(200, report)
            return

        if path in ("/", "/index.html"):
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

        messages, tier = body.get("messages"), body.get("tier", "fast")
        if not isinstance(messages, list) or not messages:
            self.send_json(400, {"error": "messages must be a non-empty array"})
            return
        if tier not in TIER_LIMITS:
            self.send_json(400, {"error": f"unknown tier: {tier}"})
            return

        governed_messages = [{"role": "system", "content": system_prompt()}]
        for message in messages:
            if isinstance(message, dict) and message.get("role") in {"system", "user", "assistant"}:
                content = message.get("content")
                if isinstance(content, str):
                    governed_messages.append({"role": message["role"], "content": content})

        selected = ENDPOINTS[:TIER_LIMITS[tier]]
        if not selected:
            self.send_json(503, {"error": "no model endpoints configured", "state": "UNVERIFIED"})
            return

        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache, no-store")
        self.send_header("Connection", "keep-alive")
        self.end_headers()
        self.wfile.write(sse("race:start", {"models_queried": len(selected), "tier": tier}))
        self.wfile.flush()

        results: list[dict[str, Any]] = []
        events: queue.Queue[dict[str, Any]] = queue.Queue()
        lock = threading.Lock()

        def worker(endpoint: dict[str, str]) -> None:
            result = call_model(endpoint, governed_messages)
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
            audit("model_race_failed", {"models_queried": len(selected)})
            self.wfile.write(sse("race:error", {"error": "all configured model endpoints failed", "state": "FAILED"}))
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
        audit("model_race_completed", {"winner": winner["model"], "models_responded": responded})
        self.wfile.write(sse("race:complete", {
            "response": winner["content"],
            "winner": {
                "model": winner["model"],
                "score": winner["score"],
                "duration_ms": winner["duration_ms"],
            },
            "race": {
                "rankings": [
                    {"model": r["model"], "score": r["score"], "success": r["success"]}
                    for r in rankings
                ]
            },
        }))
        self.wfile.write(b"data: [DONE]\n\n")
        self.wfile.flush()


def main() -> None:
    print(f"BooBooAI-GM3 ULTRAPLINIAN listening on http://{HOST}:{PORT}")
    print(f"Configured model endpoints: {len(ENDPOINTS)}")
    for item in model_status():
        state = "VERIFIED" if item["reachable"] else "UNVERIFIED"
        print(f"  [{state}] {item['name']}: {item['url']}")
    audit("server_started", {"host": HOST, "port": PORT})
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()


if __name__ == "__main__":
    main()
