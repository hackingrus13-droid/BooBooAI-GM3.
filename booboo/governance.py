from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_RULES = ROOT / "config" / "governed_rules.json"
PRIVATE_RULES = ROOT / "config" / "private_rules.local.json"
AUDIT_LOG = ROOT / "state" / "governance_audit.jsonl"

ALLOWED_STATES = {
    "VERIFIED",
    "PARTIALLY VERIFIED",
    "UNVERIFIED",
    "FAILED",
    "UNKNOWN",
    "NOT TESTED",
    "NOT APPLICABLE",
}


def _load(path: Path, default: dict[str, Any]) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default.copy()
    return data if isinstance(data, dict) else default.copy()


def load_rules() -> dict[str, Any]:
    public = _load(PUBLIC_RULES, {"rules": []})
    private = _load(PRIVATE_RULES, {"rules": []})
    rules = []
    for source, payload in (("public", public), ("private", private)):
        for rule in payload.get("rules", []):
            if not isinstance(rule, dict):
                continue
            item = dict(rule)
            item["source"] = source
            rules.append(item)
    return {
        "schema_version": max(int(public.get("schema_version", 1)), int(private.get("schema_version", 1))),
        "rules": rules,
        "private_rules_present": PRIVATE_RULES.exists(),
    }


def system_prompt() -> str:
    return (
        "You are BooBooAI-GM, a locally governed personal AI. "
        "Follow the administrator's verified project policy. "
        "Never fabricate evidence, execution results, files, capabilities, "
        "sources, versions, permissions, or successful outcomes. "
        "Use VERIFIED, PARTIALLY VERIFIED, UNVERIFIED, FAILED, UNKNOWN, "
        "NOT TESTED, or NOT APPLICABLE when appropriate. "
        "Separate documented facts from inference. "
        "Inspect before changing files. Test changes after editing. "
        "Do not repeat a known failed approach unless new evidence shows "
        "the relevant condition changed. Optimize for the shortest path to "
        "verified success. Keep private rules local. "
        "Administrator authority means control over this project's approved "
        "configuration and permissions; it does not mean bypassing the host "
        "platform, law, safety controls, authentication, or third-party policy. "
        "Security work must be authorized and scoped to owned or explicitly "
        "permitted systems."
    )


def policy_snapshot() -> dict[str, Any]:
    rules = load_rules()
    public = [r for r in rules["rules"] if r.get("source") == "public"]
    return {
        "schema_version": rules["schema_version"],
        "rule_count": len(rules["rules"]),
        "public_rule_count": len(public),
        "private_rules_present": rules["private_rules_present"],
        "private_rule_contents": "NOT DISPLAYED",
        "verification_states": sorted(ALLOWED_STATES),
        "system_prompt_sha256": hashlib.sha256(system_prompt().encode()).hexdigest(),
    }


def audit(event: str, data: dict[str, Any] | None = None) -> None:
    AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": event,
        "data": data or {},
    }
    with AUDIT_LOG.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")


def validate_state(state: str) -> bool:
    return str(state).upper() in ALLOWED_STATES


def verification_record(objective: str, state: str, evidence: list[str] | None = None) -> dict[str, Any]:
    normalized = str(state).upper()
    if not validate_state(normalized):
        raise ValueError(f"invalid verification state: {state}")
    record = {
        "objective": objective,
        "state": normalized,
        "evidence": evidence or [],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    audit("verification_recorded", record)
    return record
