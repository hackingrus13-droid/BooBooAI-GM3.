from __future__ import annotations

import json
import unittest
from pathlib import Path

from booboo.authorization import PRIVILEGED_CAPABILITIES, AuthorizationDenied, decision, require
from booboo.governance import ALLOWED_STATES, policy_snapshot, system_prompt, validate_state

ROOT = Path(__file__).resolve().parents[1]


class GovernanceTests(unittest.TestCase):
    def test_public_rules_are_valid_json(self) -> None:
        path = ROOT / "config" / "governed_rules.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertIsInstance(data.get("rules"), list)
        self.assertGreater(len(data["rules"]), 0)
        self.assertGreaterEqual(len(data["rules"]), 30)

    def test_config_example_is_valid_json(self) -> None:
        path = ROOT / "config" / "config.example.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(data["schema_version"], 6)
        self.assertEqual(data["governance"]["private_rules_commit"], False)
        self.assertEqual(data["permissions"]["kali_tools"], "CONFIRM")
        self.assertEqual(data["permissions"]["yara_sources"], "CONFIRM")

    def test_verification_states_are_explicit(self) -> None:
        for state in ALLOWED_STATES:
            self.assertTrue(validate_state(state))
        self.assertFalse(validate_state("WORKS_BELIEVE_ME"))

    def test_system_prompt_contains_non_fabrication_policy(self) -> None:
        prompt = system_prompt()
        self.assertIn("Never fabricate evidence", prompt)
        self.assertIn("known failed approach", prompt)
        self.assertIn("authorized", prompt)
        self.assertIn("Kali capabilities", prompt)
        self.assertIn("YARA", prompt)

    def test_policy_snapshot_does_not_expose_private_contents(self) -> None:
        snapshot = policy_snapshot()
        self.assertEqual(snapshot["private_rule_contents"], "NOT DISPLAYED")
        self.assertIn("system_prompt_sha256", snapshot)

    def test_every_configured_privileged_capability_requires_approval(self) -> None:
        config = json.loads((ROOT / "config" / "config.example.json").read_text(encoding="utf-8"))
        permissions = config["permissions"]
        for capability in PRIVILEGED_CAPABILITIES:
            self.assertIn(capability, permissions)
            self.assertEqual(permissions[capability], "CONFIRM")
            self.assertEqual(decision(capability)["state"], "ADMIN APPROVAL REQUIRED")
            self.assertEqual(decision(capability, administrator_approved=True)["state"], "AUTHORIZED")

    def test_unknown_capabilities_are_denied(self) -> None:
        self.assertEqual(decision("not-a-real-capability")["state"], "DENY")
        with self.assertRaises(AuthorizationDenied):
            require("not-a-real-capability", administrator_approved=True)

    def test_hard_restriction_overrides_approval(self) -> None:
        from unittest.mock import patch

        for state in ("DISABLED", "UNAVAILABLE", "READ ONLY", "TEST ONLY", "AUTHORIZED LAB ONLY"):
            with patch(
                "booboo.authorization._config",
                return_value={"permissions": {"terminal": state}},
            ):
                self.assertEqual(
                    decision("terminal", administrator_approved=True)["state"],
                    state,
                )


if __name__ == "__main__":
    unittest.main()
