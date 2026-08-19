from __future__ import annotations

import json
import unittest
from pathlib import Path

from booboo.governance import ALLOWED_STATES, policy_snapshot, system_prompt, validate_state

ROOT = Path(__file__).resolve().parents[1]


class GovernanceTests(unittest.TestCase):
    def test_public_rules_are_valid_json(self) -> None:
        path = ROOT / "config" / "governed_rules.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertIsInstance(data.get("rules"), list)
        self.assertGreater(len(data["rules"]), 0)

    def test_config_example_is_valid_json(self) -> None:
        path = ROOT / "config" / "config.example.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(data["schema_version"], 5)
        self.assertEqual(data["governance"]["private_rules_commit"], False)

    def test_verification_states_are_explicit(self) -> None:
        for state in ALLOWED_STATES:
            self.assertTrue(validate_state(state))
        self.assertFalse(validate_state("WORKS_BELIEVE_ME"))

    def test_system_prompt_contains_non_fabrication_policy(self) -> None:
        prompt = system_prompt()
        self.assertIn("Never fabricate evidence", prompt)
        self.assertIn("known failed approach", prompt)
        self.assertIn("authorized", prompt)

    def test_policy_snapshot_does_not_expose_private_contents(self) -> None:
        snapshot = policy_snapshot()
        self.assertEqual(snapshot["private_rule_contents"], "NOT DISPLAYED")
        self.assertIn("system_prompt_sha256", snapshot)


if __name__ == "__main__":
    unittest.main()
