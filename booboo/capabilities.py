from __future__ import annotations

import json
import os
import platform
import shutil
import socket
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass
class Capability:
    name: str
    category: str
    detected: bool
    detail: str
    state: str = "UNVERIFIED"
    authorized: bool = False


def _command(name: str) -> Capability:
    path = shutil.which(name)
    return Capability(name, "executable", bool(path), path or "not found")


def discover() -> dict[str, Any]:
    """Perform non-destructive capability discovery only.

    This function does not execute discovered tools and does not inspect private
    administrator rules. It records host facts useful for the later registry.
    """
    host = {
        "os": platform.system(),
        "os_release": platform.release(),
        "architecture": platform.machine(),
        "python": platform.python_version(),
        "hostname": socket.gethostname(),
    }
    capabilities = [
        _command("ollama"),
        _command("docker"),
        _command("git"),
        _command("python3"),
        _command("bash"),
        _command("pwsh"),
        _command("ip"),
        _command("nmcli"),
        _command("bluetoothctl"),
        _command("iw"),
    ]
    return {
        "host": host,
        "capabilities": [asdict(item) for item in capabilities],
        "counts": {
            "detected": sum(item.detected for item in capabilities),
            "tested": 0,
            "authorized": 0,
        },
    }


def save_registry(path: Path, registry: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")
