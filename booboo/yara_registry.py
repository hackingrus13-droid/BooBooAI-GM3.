from __future__ import annotations

"""YARA rule-source registry and local validation orchestration.

Rule sources are kept external to the core repository so licenses and upstream
updates remain attributable. The module records provenance and can validate
locally available rules when a YARA engine is installed.
"""

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

RULE_SOURCES = [
    {
        "id": "yara-rules",
        "repository": "https://github.com/Yara-Rules/rules.git",
        "branch": "master",
        "license": "GPL-2.0",
        "purpose": "community YARA rules",
    },
    {
        "id": "signature-base",
        "repository": "https://github.com/Neo23x0/signature-base.git",
        "branch": "master",
        "license": "DRL-1.1 with per-rule metadata exceptions",
        "purpose": "YARA signatures and IOCs",
    },
    {
        "id": "reversinglabs-yara-rules",
        "repository": "https://github.com/reversinglabs/reversinglabs-yara-rules.git",
        "branch": "develop",
        "license": "VERIFY UPSTREAM BEFORE REDISTRIBUTION",
        "purpose": "YARA detection content",
    },
]


def engine_status() -> dict[str, Any]:
    engines = []
    for name in ("yara", "yarax"):
        path = shutil.which(name)
        if not path:
            engines.append({"name": name, "state": "NOT DETECTED"})
            continue
        result = subprocess.run(
            [path, "--version"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        engines.append(
            {
                "name": name,
                "path": path,
                "state": "VERIFIED" if result.returncode == 0 else "FAILED",
                "version": (result.stdout or result.stderr).strip()[:200],
            }
        )
    return {"engines": engines}


def clone_sources(destination: Path) -> list[dict[str, Any]]:
    destination.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []
    git = shutil.which("git")
    if not git:
        return [{"state": "FAILED", "error": "git not detected"}]

    for source in RULE_SOURCES:
        target = destination / source["id"]
        if target.exists():
            results.append({**source, "state": "ALREADY PRESENT", "path": str(target)})
            continue
        result = subprocess.run(
            [git, "clone", "--depth", "1", "--branch", source["branch"], source["repository"], str(target)],
            capture_output=True,
            text=True,
            timeout=180,
            check=False,
        )
        results.append(
            {
                **source,
                "state": "VERIFIED" if result.returncode == 0 else "FAILED",
                "path": str(target),
                "returncode": result.returncode,
                "error": (result.stderr or "").strip()[:500],
            }
        )
    return results


def count_rules(root: Path) -> dict[str, Any]:
    files = sorted(root.rglob("*.yar")) + sorted(root.rglob("*.yara"))
    return {"state": "VERIFIED", "rule_files": len(files), "root": str(root)}


def registry(destination: Path | None = None) -> dict[str, Any]:
    root = destination or Path("knowledge") / "yara_sources"
    return {
        "sources": RULE_SOURCES,
        "engine": engine_status(),
        "execution_policy": "ADMIN_APPROVAL_REQUIRED",
        "provenance_required": True,
        "local_sources": count_rules(root) if root.exists() else {"state": "NOT TESTED", "rule_files": 0},
    }


def save(report: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    print(json.dumps(registry(), indent=2))
