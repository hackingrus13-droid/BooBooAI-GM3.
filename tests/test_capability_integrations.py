from __future__ import annotations

import json
import unittest
from pathlib import Path
from unittest.mock import patch

from booboo.authorization import decision
from booboo.kali_registry import OFFICIAL_INDEX
from booboo.yara_registry import RULE_SOURCES, registry

ROOT = Path(__file__).resolve().parents[1]


class CapabilityIntegrationTests(unittest.TestCase):
    def test_kali_source_is_official(self) -> None:
        self.assertEqual(OFFICIAL_INDEX, "https://www.kali.org/tools/all-tools/")

    def test_kali_requires_admin_approval(self) -> None:
        result = decision("kali_tools")
        self.assertEqual(result["state"], "ADMIN APPROVAL REQUIRED")
        approved = decision("kali_tools", administrator_approved=True)
        self.assertEqual(approved["state"], "AUTHORIZED")

    def test_configured_restriction_overrides_approval(self) -> None:
        with patch(
            "booboo.authorization._config",
            return_value={"permissions": {"kali_tools": "DISABLED"}},
        ):
            result = decision("kali_tools", administrator_approved=True)
        self.assertEqual(result["state"], "DISABLED")

    def test_yara_sources_have_provenance(self) -> None:
        self.assertGreaterEqual(len(RULE_SOURCES), 3)
        for source in RULE_SOURCES:
            self.assertTrue(source["repository"])
            self.assertTrue(source["branch"])
            self.assertTrue(source["license"])

    def test_yara_registry_is_non_destructive(self) -> None:
        report = registry(ROOT / "knowledge" / "yara_sources")
        self.assertTrue(report["provenance_required"])
        self.assertEqual(report["execution_policy"], "ADMIN_APPROVAL_REQUIRED")

    def test_rule_sources_json_is_valid(self) -> None:
        data = json.loads((ROOT / "config" / "rule_sources.json").read_text(encoding="utf-8"))
        self.assertEqual(data["schema_version"], 1)
        self.assertTrue(data["behavior"]["license_must_be_recorded"])


if __name__ == "__main__":
    unittest.main()
