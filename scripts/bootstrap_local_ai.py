#!/usr/bin/env python3
"""Bootstrap a local Android/arm64 llama.cpp server and a small free GGUF model.

The bootstrap is deliberately evidence-based: downloads are from explicitly
recorded upstream URLs, SHA-256 hashes are checked, and nothing is reported
as operational until the resulting /v1/models endpoint responds.

Because this operation installs executable software and model artifacts, it is
an administrator-controlled capability. It requires explicit approval via
--admin-approve or BOOBOO_ADMIN_APPROVED=1.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import platform
import shutil
import tarfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "runtime" / "llama.cpp"
MODELS = ROOT / "models"

from booboo.authorization import require

# Official llama.cpp Android arm64 release verified against the upstream release page.
LLAMA_VERSION = "b10218"
LLAMA_URL = (
    "https://github.com/ggml-org/llama.cpp/releases/download/"
    f"{LLAMA_VERSION}/llama-{LLAMA_VERSION}-bin-android-arm64.tar.gz"
)
LLAMA_SHA256 = "d92a6e9e63b979d3bad6cc4a4c108644c366cd0e8779d4f196662579e52eb86f"

# Official Qwen 0.5B instruction-tuned GGUF fallback; Q4_K_M is 491 MB.
MODEL_URL = (
    "https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/main/"
    "qwen2.5-0.5b-instruct-q4_k_m.gguf?download=true"
)
MODEL_SHA256 = "74a4da8c9fdbcd15bd1f6d01d621410d31c6fc00986f5eb687824e7b93d7a9db"
MODEL_NAME = "qwen2.5-0.5b-instruct-q4_k_m.gguf"


def download(url: str, target: Path, expected_sha256: str) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".part")
    if tmp.exists():
        tmp.unlink()
    request = urllib.request.Request(url, headers={"User-Agent": "BooBooAI-GM/1.0"})
    print(f"[BOOTSTRAP] Downloading {url}")
    with urllib.request.urlopen(request, timeout=30) as response, tmp.open("wb") as out:
        total = int(response.headers.get("Content-Length", "0"))
        done = 0
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            out.write(chunk)
            done += len(chunk)
            if total:
                print(f"\r[BOOTSTRAP] {done / total * 100:6.1f}%", end="", flush=True)
    print()
    digest = hashlib.sha256(tmp.read_bytes()).hexdigest()
    if digest.lower() != expected_sha256.lower():
        tmp.unlink(missing_ok=True)
        raise RuntimeError(f"SHA-256 mismatch: expected {expected_sha256}, got {digest}")
    tmp.replace(target)
    print(f"[BOOTSTRAP] VERIFIED SHA-256: {target}")


def find_llama_server() -> Path | None:
    for candidate in [
        RUNTIME / "llama-server",
        RUNTIME / "bin" / "llama-server",
        ROOT / "bin" / "llama-server",
        Path.home() / "bin" / "llama-server",
    ]:
        if candidate.is_file():
            return candidate
    return None


def install_llama_server() -> Path:
    existing = find_llama_server()
    if existing:
        existing.chmod(existing.stat().st_mode | 0o111)
        return existing

    archive = RUNTIME.parent / f"llama-{LLAMA_VERSION}-android-arm64.tar.gz"
    download(LLAMA_URL, archive, LLAMA_SHA256)
    RUNTIME.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive, "r:gz") as tar:
        tar.extractall(RUNTIME)
    archive.unlink(missing_ok=True)

    server = find_llama_server()
    if server is None:
        matches = list(RUNTIME.rglob("llama-server"))
        if matches:
            server = matches[0]
    if server is None:
        raise RuntimeError("Verified llama.cpp archive did not contain llama-server")
    server.chmod(server.stat().st_mode | 0o111)
    return server


def install_fallback_model() -> Path:
    MODELS.mkdir(parents=True, exist_ok=True)
    target = MODELS / MODEL_NAME
    if target.is_file() and target.stat().st_size > 100_000_000:
        return target
    free = shutil.disk_usage(ROOT).free
    required = 1_400_000_000
    if free < required:
        raise RuntimeError(
            f"Insufficient free storage for fallback model: {free} bytes available, "
            f"at least {required} recommended"
        )
    download(MODEL_URL, target, MODEL_SHA256)
    return target


def write_wrapper(real_server: Path) -> Path:
    wrapper = ROOT / "runtime" / "llama-server"
    wrapper.parent.mkdir(parents=True, exist_ok=True)
    lib_dirs = sorted({p.parent for p in real_server.parent.rglob("*.so*")})
    paths = ":".join(str(p) for p in lib_dirs)
    wrapper.write_text(
        "#!/data/data/com.termux/files/usr/bin/bash\n"
        "set -euo pipefail\n"
        f"export LD_LIBRARY_PATH=\"{paths}${{LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}}\"\n"
        f"exec \"{real_server}\" \"$@\"\n",
        encoding="utf-8",
    )
    wrapper.chmod(0o755)
    return wrapper


def is_supported_target() -> bool:
    machine = platform.machine().lower()
    prefix = os.environ.get("PREFIX", "")
    termux = prefix.startswith("/data/data/com.termux")
    system = platform.system().lower()
    return machine in {"aarch64", "arm64"} and (system in {"linux", "android"} or termux)


def main() -> int:
    parser = argparse.ArgumentParser(description="Administrator-controlled BooBooAI local AI bootstrap")
    parser.add_argument(
        "--admin-approve",
        action="store_true",
        help="explicitly authorize software/model installation for this invocation",
    )
    args = parser.parse_args()
    approved = args.admin_approve or os.environ.get("BOOBOO_ADMIN_APPROVED") == "1"
    require("software_installation", administrator_approved=approved)

    if not is_supported_target():
        print(
            "[BOOTSTRAP] SKIPPED: supported target is Android/Termux arm64 "
            "or Linux arm64/aarch64."
        )
        return 2

    print(
        f"[BOOTSTRAP] Target: {platform.system()} {platform.machine()}"
        + (" (Termux)" if os.environ.get("PREFIX", "").startswith("/data/data/com.termux") else "")
    )
    MODELS.mkdir(parents=True, exist_ok=True)
    server = install_llama_server()
    model = install_fallback_model()
    wrapper = write_wrapper(server)
    print(f"[BOOTSTRAP] llama-server: {wrapper}")
    print(f"[BOOTSTRAP] model: {model}")
    print(
        "[BOOTSTRAP] Artifacts are downloaded and hash-verified. "
        "Runtime inference is still NOT VERIFIED until the server is started and tested."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
