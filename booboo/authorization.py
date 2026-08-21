from __future__ import annotations

"""Administrator authorization gate for privileged BooBooAI-GM actions."""

import copy
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


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Merge local configuration over the committed safe baseline.

    Missing keys in an older local config inherit newly introduced defaults
    from config.example.json. Existing local values remain authoritative.
    """
    result = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def _load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _config() -> dict[str, Any]:
    # The committed example is the safe baseline. A local config may override
    # it, but an older local config must not silently remove newly introduced
    # governance capabilities. This keeps upgrades additive and fail-closed.
    baseline = _load_json(EXAMPLE_CONFIG)
    local = _load_json(CONFIG)
    if baseline:
        return _deep_merge(baseline, local)
    return local


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
