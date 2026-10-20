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
    if payload.get("company_size") and str(payload["company_size"]).strip() not in {"1-10", "11-50", "51-200", "201-1000", "1000+", "Unknown"}:
        errors.append("Select a valid company size.")
    return errors
