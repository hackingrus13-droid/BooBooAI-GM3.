from __future__ import annotations

"""Kali capability catalog and local discovery.

This module does not execute Kali tools. It builds an evidence-based catalog
from the official Kali tools index and from locally installed executables.
Execution remains a separate, administrator-controlled capability.
"""

import html
import json
import re
import shutil
import subprocess
import urllib.request
from pathlib import Path
from typing import Any

OFFICIAL_INDEX = "https://www.kali.org/tools/all-tools/"
PACKAGE_RE = re.compile(r"<a[^>]+href=\"/tools/([^/]+)/\"[^>]*>(.*?)</a>", re.I | re.S)


def fetch_official_catalog(timeout: int = 20) -> dict[str, Any]:
    request = urllib.request.Request(
        OFFICIAL_INDEX,
        headers={"User-Agent": "BooBooAI-GM capability catalog/1.0"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        source = response.read().decode("utf-8", errors="replace")

    packages: dict[str, str] = {}
    for slug, label in PACKAGE_RE.findall(source):
        clean = re.sub(r"<[^>]+>", " ", html.unescape(label))
        clean = " ".join(clean.split())
        if slug and clean:
            packages[slug] = clean

    return {
        "source": OFFICIAL_INDEX,
        "state": "VERIFIED",
        "catalog_type": "official_kali_tools_index",
        "package_count": len(packages),
        "packages": [{"slug": k, "name": v} for k, v in sorted(packages.items())],
    }


def local_kali_packages() -> dict[str, Any]:
    apt = shutil.which("apt-cache")
    if not apt:
        return {"state": "NOT APPLICABLE", "reason": "apt-cache not detected"}
    result = subprocess.run(
        [apt, "pkgnames"],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    names = sorted(
        line.strip()
        for line in result.stdout.splitlines()
        if line.strip().startswith("kali-") or line.strip() in {"metasploit-framework", "yara", "yara-x"}
    )
    return {
        "state": "VERIFIED" if result.returncode == 0 else "FAILED",
        "package_count": len(names),
        "packages": names,
        "returncode": result.returncode,
    }


def discover() -> dict[str, Any]:
    report: dict[str, Any] = {
        "official_catalog": {"state": "UNVERIFIED"},
        "local_packages": local_kali_packages(),
        "execution_policy": "ADMIN_APPROVAL_REQUIRED",
        "tool_execution_performed": False,
    }
    try:
        report["official_catalog"] = fetch_official_catalog()
    except Exception as exc:
        report["official_catalog"] = {
            "state": "FAILED",
            "source": OFFICIAL_INDEX,
            "error": str(exc),
        }
    return report


def save(report: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    print(json.dumps(discover(), indent=2))
