from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .capabilities import discover, save_registry
from .config import load_config, privacy_mode
from .governance import policy_snapshot
from .services import default_services, summarize


BOOT_STAGES = [
    "BOOT",
    "SELF-DIAGNOSTICS",
    "HARDWARE DISCOVERY",
    "DEPENDENCY CHECK",
    "MODEL CHECK",
    "TOOL REGISTRY CHECK",
    "NETWORK CHECK",
    "KNOWLEDGE CHECK",
    "PERMISSION CHECK",
    "GOVERNANCE CHECK",
    "TEST",
    "REPORT",
    "READY",
]


def run(config_path: Path | None = None) -> dict[str, Any]:
    """Run safe startup diagnostics without executing registered tools."""
    config = load_config(config_path)
    registry = discover()
    root = Path(__file__).resolve().parents[1]
    state_path = root / "state" / "tool_registry.json"
    save_registry(state_path, registry)

    model_providers = config.get("models", {}).get("providers", [])
    knowledge_path = root / config.get("knowledge", {}).get("library_path", "knowledge/library")
    governance = policy_snapshot()

    return {
        "boot_stages": BOOT_STAGES,
        "privacy": {
            "network_mode": privacy_mode(config),
            "internet_access": bool(config.get("privacy", {}).get("internet_access", False)),
            "cloud_ai": bool(config.get("privacy", {}).get("cloud_ai", False)),
            "telemetry": bool(config.get("privacy", {}).get("remote_telemetry", False)),
        },
        "host": registry["host"],
        "capability_registry": registry,
        "models": {
            "configured_provider_count": len(model_providers),
            "state": "UNVERIFIED" if not model_providers else "CONFIGURED_NOT_TESTED",
        },
        "knowledge": {
            "path": str(knowledge_path),
            "exists": knowledge_path.exists(),
            "state": "UNVERIFIED" if not knowledge_path.exists() else "DETECTED_NOT_INDEXED",
        },
        "governance": governance,
        "services": summarize(default_services()),
        "private_rules": {
            "present": governance["private_rules_present"],
            "contents": "NOT DISPLAYED",
        },
        "overall_state": "PARTIALLY VERIFIED",
    }


def main() -> None:
    result = run()
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
