#!/usr/bin/env python3
from __future__ import annotations

"""Build a non-destructive capability inventory for Kali and YARA."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from booboo.kali_registry import discover as discover_kali
from booboo.yara_registry import registry as yara_registry


def main() -> int:
    output = ROOT / "state" / "capability_inventory.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "project": "BooBooAI-GM3",
        "kali": discover_kali(),
        "yara": yara_registry(ROOT / "knowledge" / "yara_sources"),
        "execution": {
            "tool_execution_performed": False,
            "privileged_actions": "ADMIN APPROVAL REQUIRED",
        },
    }
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
