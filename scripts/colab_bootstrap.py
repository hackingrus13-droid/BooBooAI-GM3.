"""Google Colab bootstrap for BooBooAI-GM3.

This script is a development/verification bootstrap. Free managed Colab
runtimes are ephemeral and are not treated as guaranteed web hosting.
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
    from booboo.kali_registry import discover as discover_kali
    from booboo.yara_registry import registry as yara_registry

    report = run()
    report["environment"] = {
        "platform": platform.platform(),
        "python": sys.version,
        "colab": bool(Path("/content").exists()),
        "commands": [command_version(x) for x in ("git", "python", "python3")],
    }
    report["governance"] = policy_snapshot()
    report["kali_capability_catalog"] = discover_kali()
    report["yara_registry"] = yara_registry(ROOT / "knowledge" / "yara_sources")
    report["colab_policy"] = {
        "mode": "DEVELOPMENT_AND_VERIFICATION",
        "free_managed_runtime": True,
        "persistent_web_hosting_claim": False,
        "shared_project_contract": True,
        "note": "Colab shares BooBooAI-GM code and verification contracts with local/Termux deployments, while reporting its own runtime capabilities independently.",
    }

    state = ROOT / "state"
    state.mkdir(parents=True, exist_ok=True)
    output = state / "colab_report.json"
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
