"""Google Colab bootstrap for BooBooAI-GM3.

This script is intentionally a development/verification bootstrap. Free managed
Colab runtimes are ephemeral and are not treated as guaranteed web hosting.
"""
from __future__ import annotations

import json
import platform
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def command_version(command: str) -> dict[str, object]:
    path = shutil.which(command)
    if not path:
        return {"command": command, "available": False}
    try:
        result = subprocess.run(
            [command, "--version"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        return {
            "command": command,
            "available": result.returncode == 0,
            "version": (result.stdout or result.stderr).strip()[:500],
            "returncode": result.returncode,
        }
    except Exception as exc:
        return {"command": command, "available": False, "error": str(exc)}


def main() -> None:
    sys.path.insert(0, str(ROOT))
    from booboo.governance import policy_snapshot
    from booboo.diagnostics import run

    report = run()
    report["environment"] = {
        "platform": platform.platform(),
        "python": sys.version,
        "colab": bool(Path("/content").exists()),
        "commands": [command_version(x) for x in ("git", "python", "python3")],
    }
    report["governance"] = policy_snapshot()
    report["colab_policy"] = {
        "mode": "DEVELOPMENT_AND_VERIFICATION",
        "free_managed_runtime": True,
        "persistent_web_hosting_claim": False,
        "note": "Use Termux/local hardware for the persistent localhost browser service."
    }

    state = ROOT / "state"
    state.mkdir(parents=True, exist_ok=True)
    output = state / "colab_report.json"
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
