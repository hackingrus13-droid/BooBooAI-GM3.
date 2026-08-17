from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


@dataclass
class ServiceRecord:
    name: str
    provider: str
    kind: str
    status: str
    paid: bool
    current_monthly_cost: float = 0.0
    projected_monthly_cost: float = 0.0
    verified_at: str | None = None
    notes: str = ""


def default_services() -> list[dict[str, Any]]:
    """Return an intentionally conservative service inventory.

    Costs are not inferred from provider marketing pages. They remain zero until
    an administrator configures a service and supplies verified usage/cost data.
    """
    services = [
        ServiceRecord("local_ai", "local", "inference", "UNVERIFIED", False),
        ServiceRecord("local_storage", "local", "storage", "UNVERIFIED", False),
        ServiceRecord("local_database", "local", "database", "UNVERIFIED", False),
        ServiceRecord("github", "GitHub", "source_control", "UNVERIFIED", False),
        ServiceRecord("cloudflare", "Cloudflare", "optional_cloud", "DISABLED", False),
        ServiceRecord("google_cloud", "Google Cloud", "optional_cloud", "DISABLED", False),
        ServiceRecord("cloud_ai", "external", "inference", "DISABLED", False),
    ]
    return [asdict(item) for item in services]


def summarize(services: list[dict[str, Any]]) -> dict[str, Any]:
    current = sum(float(item.get("current_monthly_cost", 0)) for item in services)
    projected = sum(float(item.get("projected_monthly_cost", 0)) for item in services)
    paid = [item for item in services if item.get("paid")]
    return {
        "current_monthly_cost": round(current, 2),
        "projected_monthly_cost": round(projected, 2),
        "paid_services": [item["name"] for item in paid],
        "currency": "USD",
    }
