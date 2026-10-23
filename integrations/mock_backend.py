"""Empty in-memory demo adapter; imported/created records exist only for this process."""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

from utils.csv_import import preview_lead_csv


PIPELINE_STAGES = ("Prospecting", "Discovery", "Qualified", "Proposal", "Negotiation", "Closed Won", "Closed Lost")
SCORE_BANDS = (("0–44", 0, 44), ("45–69", 45, 69), ("70–100", 70, 100))


class MockBackend:
    source_label = "Demo data — in-memory mock backend"

    def __init__(self) -> None:
        # Demo mode starts empty. Users add their own data by creating a lead or
        # uploading a CSV; no sample customer records are silently preloaded.
        self.leads: list[dict[str, Any]] = []
        self.outreach: dict[str, list[dict[str, Any]]] = {}
        self.conversations: dict[str, list[dict[str, Any]]] = {}
        self.follow_ups: list[dict[str, Any]] = []
        self.saved: dict[str, list[dict[str, Any]]] = {"insights": [], "scores": []}

    def _stamp(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {
            **deepcopy(payload),
            "_demo": True,
            "_source": self.source_label,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

    def health(self) -> dict[str, Any]:
        return {"status": "ok", "mode": "demo", "source": self.source_label}

    def list_leads(self, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        rows = deepcopy(self.leads)
        filters = filters or {}
        query = str(filters.get("query", "")).lower().strip()
        if query:
            rows = [
                row for row in rows
                if query in " ".join(str(row.get(key, "")) for key in ("company_name", "contact_name", "industry", "email")).lower()
            ]
        for key in ("status", "stage", "industry"):
            value = filters.get(key)
            if value and value != "All":
                rows = [row for row in rows if row.get(key) == value]
        return [self._stamp(row) for row in rows]

    def get_lead(self, lead_id: str) -> dict[str, Any]:
        for lead in self.leads:
            if lead["id"] == lead_id:
                return self._stamp(lead)
        raise KeyError(f"Lead '{lead_id}' was not found in demo data.")

    def create_lead(self, payload: dict[str, Any]) -> dict[str, Any]:
        lead = {
            **payload,
            "id": f"demo-{len(self.leads) + 1:03d}",
            "created_at": datetime.now(timezone.utc).date().isoformat(),
        }
        self.leads.append(lead)
        return self._stamp(lead)

    def update_lead(self, lead_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        for idx, lead in enumerate(self.leads):
            if lead["id"] == lead_id:
                self.leads[idx] = {**lead, **payload, "id": lead_id}
                return self._stamp(self.leads[idx])
        raise KeyError(f"Lead '{lead_id}' was not found in demo data.")

    def import_leads(self, filename: str, content: bytes) -> dict[str, Any]:
        preview = preview_lead_csv(content)
        if not preview.can_import:
            detail = " ".join(preview.errors) or "CSV contains no valid lead rows."
            raise ValueError(detail)

        # Validate the full file before mutating the in-memory backend so a bad
        # row can never leave a partial import behind.
        for row in preview.rows:
            self.create_lead(row)
        return {
            "imported": len(preview.rows),
            "skipped": preview.skipped_rows,
            "filename": filename,
            "warnings": preview.warnings,
            "_demo": True,
        }

    def get_analytics(self, filters: dict[str, Any] | None = None) -> dict[str, Any]:
        leads = self.list_leads(filters)
        lead_ids = {str(lead.get("id")) for lead in leads}
        stages = [
            {"stage": stage, "count": sum(1 for lead in leads if lead.get("stage") == stage)}
            for stage in PIPELINE_STAGES
        ] if leads else []
        scores: list[int] = []
        for item in self.saved["scores"]:
            if str(item.get("lead_id")) not in lead_ids:
                continue
            value = item.get("score", {})
            value = value.get("score") if isinstance(value, dict) else value
            if isinstance(value, (int, float)):
                scores.append(int(value))
        score_distribution = [
            {"band": label, "count": sum(1 for score in scores if lower <= score <= upper)}
            for label, lower, upper in SCORE_BANDS
        ] if scores else []
        outreach_count = sum(len(drafts) for lead_id, drafts in self.outreach.items() if lead_id in lead_ids)
        open_followups = sum(
            1 for item in self.follow_ups
            if item.get("status") == "Open" and str(item.get("lead_id")) in lead_ids
        )
        qualified_count = sum(
            1 for lead in leads if lead.get("stage") in {"Qualified", "Proposal", "Negotiation"}
        )
        return {
            "source": self.source_label,
            "is_demo": True,
            "total_leads": len(leads),
            "qualified_leads": qualified_count,
            "average_lead_score": sum(scores) / len(scores) if scores else None,
            "conversion_rate": None,
            "outreach_activity": outreach_count,
            "follow_up_tasks": open_followups,
            "pipeline_distribution": stages,
            "lead_score_distribution": score_distribution,
            # The demo adapter does not record an activity timeline, so it does
            # not fabricate a chart when there is no source data for one.
            "activity_trend": [],
        }

    def save_company_insights(self, lead_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        self.get_lead(lead_id)
        item = self._stamp({"lead_id": lead_id, **payload})
        self.saved["insights"].append(item)
        return item

    def save_lead_score(self, lead_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        self.get_lead(lead_id)
        item = self._stamp({"lead_id": lead_id, **payload})
        self.saved["scores"].append(item)
        return item

    def save_outreach(self, lead_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        self.get_lead(lead_id)
        item = self._stamp({"id": f"draft-{len(self.outreach.get(lead_id, [])) + 1}", "lead_id": lead_id, **payload})
        self.outreach.setdefault(lead_id, []).append(item)
        return item

    def get_outreach(self, lead_id: str) -> list[dict[str, Any]]:
        return deepcopy(self.outreach.get(lead_id, []))

    def save_conversation(self, lead_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        self.get_lead(lead_id)
        item = self._stamp({"id": f"conv-{len(self.conversations.get(lead_id, [])) + 1}", "lead_id": lead_id, **payload})
        self.conversations.setdefault(lead_id, []).append(item)
        return item

    def get_conversations(self, lead_id: str) -> list[dict[str, Any]]:
        return deepcopy(self.conversations.get(lead_id, []))

    def get_follow_ups(self, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        status = (filters or {}).get("status")
        rows = deepcopy(self.follow_ups)
        if status and status != "All":
            rows = [row for row in rows if row.get("status") == status]
        return [self._stamp(row) for row in rows]

    def update_follow_up(self, recommendation_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        for idx, recommendation in enumerate(self.follow_ups):
            if recommendation["id"] == recommendation_id:
                self.follow_ups[idx] = {**recommendation, **payload}
                return self._stamp(self.follow_ups[idx])
        raise KeyError(f"Recommendation '{recommendation_id}' was not found in demo data.")


MOCK_BACKEND = MockBackend()
