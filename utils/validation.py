from __future__ import annotations
from urllib.parse import urlparse
from typing import Any


def require_text(value: str | None, label: str, minimum: int = 1) -> list[str]:
    value = (value or "").strip()
    if len(value) < minimum:
        return [f"{label} is required."]
    return []


def validate_email(value: str | None, required: bool = False) -> list[str]:
    value = (value or "").strip()
    if not value:
        return ["Email is required."] if required else []
    if "@" not in value or value.startswith("@") or value.endswith("@"):
        return ["Enter a valid email address."]
    return []


def validate_url(value: str | None) -> list[str]:
    value = (value or "").strip()
    if not value:
        return []
    parsed = urlparse(value if "://" in value else f"https://{value}")
    return [] if parsed.netloc else ["Enter a valid website URL."]


def validate_lead_payload(payload: dict[str, Any]) -> list[str]:
    errors = require_text(payload.get("company_name"), "Company name")
    errors += validate_email(payload.get("email"), required=False)
    errors += validate_url(payload.get("website"))
    company_size = str(payload.get("company_size") or "").strip()
    if company_size and company_size not in {"1-10", "11-50", "51-200", "201-1000", "1000+", "Unknown"}:
        errors.append("Select a valid company size.")
    status = str(payload.get("status") or "").strip()
    if status and status not in {"New", "Active", "Inactive", "Closed"}:
        errors.append("Select a valid status.")
    stage = str(payload.get("stage") or "").strip()
    if stage and stage not in {"Prospecting", "Discovery", "Qualified", "Proposal", "Negotiation", "Closed Won", "Closed Lost"}:
        errors.append("Select a valid sales stage.")
    return errors
