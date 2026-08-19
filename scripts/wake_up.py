#!/usr/bin/env python3
"""BooBooAI-GM verified startup entry point."""
from __future__ import annotations

import json
import platform
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def command_check(name: str, args: list[str] | None = None) -> dict[str, object]:
    path = shutil.which(name)
    if not path:
        return {"state": "NOT DETECTED", "command": name}
    try:
        result = subprocess.run(
            [name] + (args or ["--version"]),
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        output = (result.stdout or result.stderr).strip()
        return {
            "state": "VERIFIED" if result.returncode == 0 else "FAILED",
            "command": name,
            "path": path,
            "output": output[:500],
            "returncode": result.returncode,
        }
    except Exception as exc:
        return {"state": "FAILED", "command": name, "error": str(exc)}


def http_health() -> dict[str, object]:
    url = "http://127.0.0.1:8080/api/health"
    try:
        with urllib.request.urlopen(url, timeout=3) as response:
            data = json.loads(response.read().decode("utf-8"))
        return {"state": "VERIFIED", "url": url, "response": data}
    except Exception as exc:
        return {"state": "NOT RUNNING", "url": url, "error": str(exc)}


def main() -> int:
    from booboo.diagnostics import run
    from booboo.governance import policy_snapshot
    from booboo.kali_registry import discover as discover_kali
    from booboo.yara_registry import registry as yara_registry

    report = run()
    report["host"] = {
        "platform": platform.platform(),
        "machine": platform.machine(),
        "python": sys.version,
    }
    report["software"] = [command_check(x) for x in ("python3", "git", "curl")]
    report["browser_service"] = http_health()
    report["governance"] = policy_snapshot()
    report["kali"] = discover_kali()
    report["yara"] = yara_registry(ROOT / "knowledge" / "yara_sources")
    report["overall_state"] = "PARTIALLY VERIFIED"

    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
