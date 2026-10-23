"""CSV preview and normalization for importing lead records."""
from __future__ import annotations

import csv
import re
from dataclasses import dataclass, field
from io import StringIO
from typing import Any

from utils.validation import validate_lead_payload


LEAD_CSV_FIELDS = (
    "company_name",
    "contact_name",
    "email",
    "website",
    "industry",
    "company_size",
    "prospect_role",
    "status",
    "stage",
    "company_description",
)


@dataclass
class LeadCSVPreview:
    """Validated lead rows plus diagnostics suitable for the import UI."""

    rows: list[dict[str, str]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    total_rows: int = 0
    skipped_rows: int = 0

    @property
    def can_import(self) -> bool:
        return bool(self.rows) and not self.errors


def _normalize_header(value: str) -> str:
    return re.sub(r"[\s-]+", "_", value.strip().lower())


def preview_lead_csv(content: bytes | str) -> LeadCSVPreview:
    """Decode, parse, and validate a UTF-8 lead CSV without importing any records.

    The required header is ``company_name``. Other fields are optional. Spaces and
    hyphens in headings are normalized to underscores; unrecognized columns are
    ignored with a warning. A file with any invalid non-empty row cannot be imported.
    """
    result = LeadCSVPreview()
    try:
        text = content.decode("utf-8-sig") if isinstance(content, bytes) else content.lstrip("\ufeff")
    except UnicodeDecodeError:
        result.errors.append("CSV must use UTF-8 encoding.")
        return result

    reader = csv.reader(StringIO(text, newline=""), strict=True)
    try:
        headers = next(reader, None)
        if not headers or not any(header.strip() for header in headers):
            result.errors.append("CSV is empty or does not contain a header row.")
            return result

        normalized_headers = [_normalize_header(header) for header in headers]
        if any(not header for header in normalized_headers):
            result.errors.append("Every CSV column must have a header.")
            return result
        duplicates = sorted({header for header in normalized_headers if normalized_headers.count(header) > 1})
        if duplicates:
            result.errors.append("Duplicate CSV columns after normalization: " + ", ".join(duplicates) + ".")
            return result
        if "company_name" not in normalized_headers:
            result.errors.append("A company_name column is required.")
            return result

        unknown_headers = [header for header in normalized_headers if header not in LEAD_CSV_FIELDS]
        if unknown_headers:
            result.warnings.append("Unrecognized columns will be ignored: " + ", ".join(unknown_headers) + ".")

        for values in reader:
            row_number = reader.line_num
            if not values or not any(value.strip() for value in values):
                result.skipped_rows += 1
                continue
            result.total_rows += 1
            if len(values) > len(normalized_headers):
                result.errors.append(f"Row {row_number}: contains more values than the header row.")
                continue
            values.extend([""] * (len(normalized_headers) - len(values)))
            source_row = dict(zip(normalized_headers, values))
            lead = {
                field_name: (source_row.get(field_name) or "").strip()
                for field_name in LEAD_CSV_FIELDS
            }
            row_errors = validate_lead_payload(lead)
            if row_errors:
                result.errors.append(f"Row {row_number}: " + " ".join(row_errors))
                continue
            result.rows.append(lead)
    except csv.Error as exc:
        result.errors.append(f"CSV could not be parsed: {exc}.")
        return result

    if result.total_rows == 0:
        result.errors.append("CSV contains no non-empty lead rows.")
    elif not result.rows and not result.errors:
        result.errors.append("CSV contains no valid lead rows.")
    return result


def serialize_lead_csv(rows: list[dict[str, Any]]) -> bytes:
    """Return normalized UTF-8 CSV containing only the supported lead columns."""
    output = StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=LEAD_CSV_FIELDS, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({field_name: row.get(field_name, "") or "" for field_name in LEAD_CSV_FIELDS})
    return output.getvalue().encode("utf-8")


def blank_lead_csv_template() -> bytes:
    """CSV header-only template; it contains no example or pre-populated values."""
    return serialize_lead_csv([])
