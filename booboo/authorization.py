from __future__ import annotations

"""Administrator authorization gate for privileged BooBooAI-GM actions."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "config.json"
EXAMPLE_CONFIG = ROOT / "config" / "config.example.json"
AUDIT = ROOT / "state" / "governance_audit.jsonl"


class AuthorizationDenied(PermissionError):
    pass


PRIVILEGED_CAPABILITIES = frozenset({
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
    "model_merging",
})

HARD_RESTRICTIONS = frozenset({
    "DENY",
    "DISABLED",
    "UNAVAILABLE",
    "READ ONLY",
    "TEST ONLY",
    "AUTHORIZED LAB ONLY",
})


def _config() -> dict[str, Any]:
    # Clean repository checkouts intentionally do not contain config/config.json.
    # Use the committed example as the safe baseline until the administrator
    # creates the local configuration.
    for path in (CONFIG, EXAMPLE_CONFIG):
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
    return {}


def decision(capability: str, *, administrator_approved: bool = False) -> dict[str, Any]:
    config = _config()
    permissions = config.get("permissions", {})
    configured = permissions.get(capability)
    requires = capability in PRIVILEGED_CAPABILITIES

    # Unknown capabilities are never implicitly authorized.
    if configured is None:
        state = "DENY"
    else:
        normalized = str(configured).upper()
        # A configured hard restriction always wins over an approval flag.
        if normalized in HARD_RESTRICTIONS:
            state = normalized
        elif normalized in {"CONFIRM", "ADMIN APPROVAL REQUIRED"}:
            state = "AUTHORIZED" if administrator_approved else "ADMIN APPROVAL REQUIRED"
        elif normalized in {"ALLOW", "ALLOW_LOCAL", "AUTHORIZED"}:
            state = "AUTHORIZED"
        elif requires:
            state = "AUTHORIZED" if administrator_approved else "ADMIN APPROVAL REQUIRED"
        else:
            state = "DENY"

    confirmation_required = requires or (
        configured is not None
        and str(configured).upper() in {"CONFIRM", "ADMIN APPROVAL REQUIRED"}
    )
    return {
        "capability": capability,
        "state": state,
        "administrator_confirmation_required": confirmation_required,
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
