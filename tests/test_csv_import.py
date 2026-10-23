import pytest

from integrations.mock_backend import MockBackend
from utils.csv_import import blank_lead_csv_template, preview_lead_csv


def test_demo_backend_starts_empty_without_fabricated_analytics():
    backend = MockBackend()

    assert backend.list_leads() == []
    assert backend.get_follow_ups() == []
    analytics = backend.get_analytics()
    assert analytics["total_leads"] == 0
    assert analytics["qualified_leads"] == 0
    assert analytics["average_lead_score"] is None
    assert analytics["outreach_activity"] == 0
    assert analytics["activity_trend"] == []


def test_csv_preview_normalizes_headers_and_keeps_blank_values_blank():
    content = (
        "Company Name,contact_name,email,company_size,status,stage\n"
        "Example Co,Ada Example,,,,\n"
    ).encode("utf-8")
    preview = preview_lead_csv(content)

    assert preview.can_import
    assert preview.rows[0]["company_name"] == "Example Co"
    assert preview.rows[0]["company_size"] == ""
    assert preview.rows[0]["status"] == ""
    assert preview.rows[0]["stage"] == ""

    backend = MockBackend()
    outcome = backend.import_leads("leads.csv", content)
    imported = backend.get_lead("demo-001")
    assert outcome["imported"] == 1
    assert imported["company_size"] == ""
    assert imported["status"] == ""
    assert imported["stage"] == ""


def test_invalid_csv_rows_block_the_entire_import():
    backend = MockBackend()
    content = b"company_name,email\nValid Co,valid@example.com\nMissing Name,not-an-email\n"
    preview = preview_lead_csv(content)

    assert not preview.can_import
    assert any("Row 3" in error for error in preview.errors)
    with pytest.raises(ValueError):
        backend.import_leads("bad.csv", content)
    assert backend.list_leads() == []


def test_csv_requires_company_name_and_template_has_no_sample_row():
    preview = preview_lead_csv(b"contact_name,email\nAda,ada@example.com\n")
    assert not preview.can_import
    assert "company_name column is required" in preview.errors[0]

    template = blank_lead_csv_template().decode("utf-8").splitlines()
    assert len(template) == 1
    assert template[0].startswith("company_name,")
