#!/usr/bin/env python3
from __future__ import annotations

"""Deterministic final verification for the committed BooBooAI-GM deployment."""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_COMMIT = "701fc2a3bf30eae73af2f0dd10dda69e8f9872e0"


def run(*args: str) -> tuple[int, str]:
    result = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False)
    return result.returncode, (result.stdout + result.stderr).strip()


def main() -> int:
    failures: list[str] = []

    code, head = run("git", "rev-parse", "HEAD")
    if code != 0 or head != EXPECTED_COMMIT:
        failures.append(f"HEAD is {head!r}; expected {EXPECTED_COMMIT}")
    else:
        print(f"[PASS] deployment commit = {EXPECTED_COMMIT}")

    code, status = run("git", "status", "--porcelain", "--untracked-files=no")
    if code != 0:
        failures.append("unable to inspect tracked git status")
    elif status:
        failures.append(f"tracked working-tree modifications present: {status}")
    else:
        print("[PASS] no tracked working-tree modifications")

    required = [
        "server.py",
        "booboo/authorization.py",
        "booboo/governance.py",
        "booboo/kali_registry.py",
        "booboo/yara_registry.py",
        "scripts/bootstrap_local_ai.py",
        "scripts/launch-termux.sh",
        "scripts/launch-final-termux.sh",
        "scripts/launch-linux.sh",
        "scripts/launch-windows.ps1",
        "tests/test_governance.py",
        "tests/test_capability_integrations.py",
        "config/config.example.json",
        "config/governed_rules.json",
        "config/rule_sources.json",
    ]
    for relative in required:
        if not (ROOT / relative).is_file():
            failures.append(f"missing required file: {relative}")
    if not failures:
        print(f"[PASS] required project files present ({len(required)})")

    try:
        config = json.loads((ROOT / "config" / "config.example.json").read_text(encoding="utf-8"))
        for capability in (
            "terminal", "filesystem", "network", "database", "servers", "plugins",
            "security_tools", "software_installation", "external_source_import",
            "kali_tools", "yara_sources",
        ):
            if config["permissions"][capability] != "CONFIRM":
                failures.append(f"privileged capability {capability} is not CONFIRM")
        print("[PASS] privileged configuration baseline requires CONFIRM")
    except Exception as exc:
        failures.append(f"configuration validation failed: {exc}")

    code, output = run(sys.executable, "-m", "compileall", "-q", "server.py", "booboo", "scripts", "tests")
    if code:
        failures.append(f"compileall failed: {output}")
    else:
        print("[PASS] Python compilation")

    code, output = run(sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v")
    if code:
        failures.append(f"unit/integration tests failed:\n{output}")
    else:
        print("[PASS] governance and integration test suite")

    if failures:
        print("\nFINAL VERIFICATION: FAILED")
        for failure in failures:
            print(f"[FAIL] {failure}")
        return 1

    print("\nFINAL VERIFICATION: PASSED")
    print("Governance, authorization guards, committed deployment state, and tests are verified for this repository checkout.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
