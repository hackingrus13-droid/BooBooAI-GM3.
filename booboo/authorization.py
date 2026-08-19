from __future__ import annotations

"""Administrator authorization gate for privileged BooBooAI-GM actions."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "config.json"
AUDIT = ROOT / "state" / "governance_audit.jsonl"


class AuthorizationDenied(PermissionError):
    pass


def _config() -> dict[str, Any]:
    try:
        return json.loads(CONFIG.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def decision(capability: str, *, administrator_approved: bool = False) -> dict[str, Any]:
    config = _config()
    privileged = {
        "terminal",
        "filesystem",
        "network",
        "database",
        "servers",
        "plugins",
        "security_tools",
        "software_installation",
        "external_source_import",
        "kali_tools",
        "yara_sources",
    }
    configured = config.get("permissions", {}).get(capability)
    requires = capability in privileged

    # A configured hard restriction takes precedence over an approval flag.
    # Approval cannot turn a DISABLED, UNAVAILABLE, READ ONLY, TEST ONLY, or
    # AUTHORIZED LAB ONLY capability into unrestricted authorization.
    restricted_states = {
        "DISABLED",
        "UNAVAILABLE",
        "READ ONLY",
        "TEST ONLY",
        "AUTHORIZED LAB ONLY",
    }
    if isinstance(configured, str) and configured.upper() in restricted_states:
        state = configured.upper()
    elif requires and not administrator_approved:
        state = "ADMIN APPROVAL REQUIRED"
    else:
        state = "AUTHORIZED"

    return {
        "capability": capability,
        "state": state,
        "administrator_confirmation_required": requires,
        "administrator_approved": administrator_approved,
        "configured_security_policy": configured,
    }


def require(capability: str, *, administrator_approved: bool = False) -> dict[str, Any]:
    result = decision(capability, administrator_approved=administrator_approved)
    if result["state"] != "AUTHORIZED":
        raise AuthorizationDenied(f"{capability}: {result['state']}")
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.open("a", encoding="utf-8").write(
        json.dumps(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "event": "administrator_authorization",
                "data": {"capability": capability, "state": result["state"]},
            },
            sort_keys=True,
        ) + "\n"
    )
    return result
