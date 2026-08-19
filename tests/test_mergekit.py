from __future__ import annotations

import unittest
from unittest.mock import patch

from booboo.authorization import AuthorizationDenied
from booboo.mergekit import PINNED_REVISION, SOURCE, command, status


class MergeKitIntegrationTests(unittest.TestCase):
    def test_source_and_pin_are_explicit(self) -> None:
        self.assertEqual(SOURCE, "https://github.com/arcee-ai/mergekit.git")
        self.assertEqual(len(PINNED_REVISION), 40)

    def test_status_is_optional(self) -> None:
        report = status()
        self.assertTrue(report["optional"])
        self.assertEqual(report["pinned_revision"], PINNED_REVISION)

    def test_command_requires_admin_approval(self) -> None:
        with patch("booboo.mergekit.MERGEKIT_ENV") as env:
            env.__truediv__.return_value.exists.return_value = True
            with self.assertRaises(AuthorizationDenied):
                command(["--help"], administrator_approved=False)


if __name__ == "__main__":
    unittest.main()
