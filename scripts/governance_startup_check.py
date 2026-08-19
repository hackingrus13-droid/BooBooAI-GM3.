#!/usr/bin/env python3
"""Deterministic startup gate for BooBooAI-GM governance coverage.

This check does not grant authorization and does not execute privileged tools.
It verifies that every declared privileged capability is represented in the
central authorization inventory, that its configured state is explicit, and
that the hard-restriction-over-approval invariant remains true.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> int:
    from booboo.authorization import HARD_RESTRICTIONS, PRIVILEGED_CAPABILITIES, decision
    from booboo.governance import ALLOWED_STATES

    failures: list[str] = []
    config_path = ROOT / "config" / "config.json"
    example_path = ROOT / "config" / "config.example.json"
    path = config_path if config_path.is_file() else example_path

    try:
        config = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"[FAIL] unable to load governance configuration: {exc}")
        return 1

    permissions = config.get("permissions", {})
    print(f"[INFO] governance configuration: {path.relative_to(ROOT)}")
    print(f"[INFO] privileged capabilities enumerated: {len(PRIVILEGED_CAPABILITIES)}")

    for capability in sorted(PRIVILEGED_CAPABILITIES):
        configured = permissions.get(capability)
        if configured is None:
            failures.append(f"missing permission state for {capability}")
            continue
        normalized = str(configured).upper()
        if normalized not in ALLOWED_STATES and normalized not in {"CONFIRM", "ALLOW", "ALLOW_LOCAL", "AUTHORIZED", "ADMIN APPROVAL REQUIRED"}:
            failures.append(f"invalid permission state for {capability}: {configured!r}")
            continue
        denied = decision(capability, administrator_approved=False)["state"]
        approved = decision(capability, administrator_approved=True)["state"]
        print(f"[PASS] {capability}: configured={normalized} no_approval={denied} approval={approved}")

    # Prove the critical invariant independently for every hard restriction.
    for state in sorted(HARD_RESTRICTIONS - {"DENY"}):
        with patch("booboo.authorization._config", return_value={"permissions": {"terminal": state}}):
            result = decision("terminal", administrator_approved=True)["state"]
        if result != state:
            failures.append(f"hard restriction {state!r} did not override approval")
        else:
            print(f"[PASS] hard restriction overrides approval: {state}")

    with patch("booboo.authorization._config", return_value={"permissions": {"terminal": "DENY"}}):
        result = decision("terminal", administrator_approved=True)["state"]
    if result != "DENY":
        failures.append("DENY did not remain terminal")
    else:
        print("[PASS] DENY remains terminal")

    # Unknown capabilities must never acquire implicit access.
    if decision("__unknown_capability__", administrator_approved=True)["state"] != "DENY":
        failures.append("unknown capability was not denied")
    else:
        print("[PASS] unknown capabilities are denied")

    if failures:
        print("GOVERNANCE STARTUP CHECK: FAILED")
        for failure in failures:
            print(f"[FAIL] {failure}")
        return 1

    print("GOVERNANCE STARTUP CHECK: PASSED")
    print("Authorization coverage is enumerated; this check grants no privileges.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
