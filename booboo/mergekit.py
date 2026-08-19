from __future__ import annotations

"""Optional, administrator-governed integration with Arcee MergeKit.

MergeKit is intentionally not a core startup dependency. This module only
reports/verifies the pinned integration and builds an explicit command after
the normal BooBooAI authorization gate has approved model merging.
"""

import subprocess
from pathlib import Path
from typing import Sequence

from booboo.authorization import require

ROOT = Path(__file__).resolve().parents[1]
MERGEKIT_DIR = ROOT / "vendor" / "mergekit"
MERGEKIT_ENV = ROOT / "state" / "mergekit-venv"
PINNED_REVISION = "a6e402884ba9bc30da7f23e8304a35f19485de95"
SOURCE = "https://github.com/arcee-ai/mergekit.git"


def status() -> dict[str, object]:
    present = (MERGEKIT_DIR / ".git").exists()
    revision = None
    if present:
        try:
            revision = subprocess.check_output(
                ["git", "-C", str(MERGEKIT_DIR), "rev-parse", "HEAD"],
                text=True,
                stderr=subprocess.DEVNULL,
            ).strip()
        except (OSError, subprocess.CalledProcessError):
            revision = None
    return {
        "source": SOURCE,
        "pinned_revision": PINNED_REVISION,
        "present": present,
        "revision": revision,
        "verified_revision": revision == PINNED_REVISION,
        "optional": True,
    }


def command(args: Sequence[str], *, administrator_approved: bool = False) -> list[str]:
    require("model_merging", administrator_approved=administrator_approved)
    if not args:
        raise ValueError("MergeKit command arguments cannot be empty")
    executable = MERGEKIT_ENV / "bin" / "mergekit-yaml"
    if not executable.exists():
        raise FileNotFoundError(
            "MergeKit is not installed. Run scripts/install-mergekit.sh on a supported environment."
        )
    return [str(executable), *args]
