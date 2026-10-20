"""In-memory demo adapter. It is clearly marked demo and never impersonates production data."""
from __future__ import annotations
from copy import deepcopy
from datetime import datetime, timezone
import csv
from io import StringIO
from typing import Any


class MockBackend:
    source_label = "Demo data — in-memory mock backend"
    def __init__(self) -> None:
        self.leads: list[dict[str, Any]] = [
            {"id":"demo-001", "company_name":"Northstar Logistics", "contact_name":"Maya Rao", "email":"maya@example.demo", "website":"", "industry":"Logistics", "company_size":"201-1000", "company_description":"Regional logistics operator expanding delivery capacity.", "prospect_role":"Operations Director", "status":"Active", "stage":"Discovery", "engagement_history":"Discovery call requested through the event form.", "explicit_needs":"Reduce manual shipment exception handling.", "response_behavior":"Responded positively", "user_research":"The team is expanding regional operations.", "created_at":"2026-09-20"},
            {"id":"demo-002", "company_name":"Aster Health Systems", "contact_name":"Arjun Mehta", "email":"arjun@example.demo", "website":"", "industry":"Healthcare", "company_size":"1000+", "company_description":"Multi-site health systems group.", "prospect_role":"VP Digital Transformation", "status":"Active", "stage":"Qualified", "engagement_history":"Opened the product overview and replied with an integration question.", "explicit_needs":"", "response_behavior":"Responded", "user_research":"", "created_at":"2026-09-24"},
            {"id":"demo-003", "company_name":"Cedar Retail Co.", "contact_name":"Nisha Kapoor", "email":"nisha@example.demo", "website":"", "industry":"Retail", "company_size":"51-200", "company_description":"Omnichannel retailer with a small ecommerce team.", "prospect_role":"Ecommerce Manager", "status":"New", "stage":"Prospecting", "engagement_history":"", "explicit_needs":"", "response_behavior":"No response", "user_research":"", "created_at":"2026-10-01"},
            {"id":"demo-004", "company_name":"Vertex Manufacturing", "contact_name":"Kiran Shah", "email":"kiran@example.demo", "website":"", "industry":"Manufacturing", "company_size":"201-1000", "company_description":"Industrial parts maker reviewing plant operations tooling.", "prospect_role":"Plant Manager", "status":"Active", "stage":"Proposal", "engagement_history":"Demo completed; requested a commercial proposal.", "explicit_needs":"Needs reporting across three plant locations.", "response_behavior":"Interested", "user_research":"", "created_at":"2026-10-04"},
        ]
        self.outreach: dict[str, list[dict[str, Any]]] = {"demo-001": []}
        self.conversations: dict[str, list[dict[str, Any]]] = {"demo-001": []}
        self.follow_ups: list[dict[str, Any]] = [
            {"id":"rec-demo-001", "lead_id":"demo-001", "related_lead":"Northstar Logistics", "recommended_action":"Send a tailored recap and request a discovery meeting.", "reason":"The lead record records a discovery-call request and a stated operational need.", "supporting_evidence":[{"statement":"Discovery call requested through the event form.","source":"Lead record","source_type":"backend","confidence":"medium"}], "priority":"High", "suggested_timing":"Within one business day", "status":"Open"},
            {"id":"rec-demo-002", "lead_id":"demo-003", "related_lead":"Cedar Retail Co.", "recommended_action":"Verify a relevant business priority before another outreach touch.", "reason":"No engagement or verified need is available.", "supporting_evidence":[], "priority":"Low", "suggested_timing":None, "status":"Open"},
        ]
        self.saved: dict[str, list[dict[str, Any]]] = {"insights": [], "scores": []}

    def _stamp(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {**deepcopy(payload), "_demo": True, "_source": self.source_label, "updated_at": datetime.now(timezone.utc).isoformat()}

    def health(self) -> dict[str, Any]: return {"status":"ok", "mode":"demo", "source":self.source_label}
    def list_leads(self, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        rows = deepcopy(self.leads); filters=filters or {}
        query=str(filters.get("query", "")).lower().strip()
        if query: rows=[x for x in rows if query in " ".join(str(x.get(k,"")) for k in ("company_name","contact_name","industry","email")).lower()]
        for key in ("status", "stage", "industry"):
            value=filters.get(key)
            if value and value != "All": rows=[x for x in rows if x.get(key)==value]
        return [self._stamp(x) for x in rows]
    def get_lead(self, lead_id: str) -> dict[str, Any]:
        for lead in self.leads:
            if lead["id"] == lead_id: return self._stamp(lead)
        raise KeyError(f"Lead '{lead_id}' was not found in demo data.")
    def create_lead(self, payload: dict[str, Any]) -> dict[str, Any]:
        lead={**payload, "id":f"demo-{len(self.leads)+1:03d}", "created_at":datetime.now(timezone.utc).date().isoformat()}
        self.leads.append(lead); return self._stamp(lead)
    def update_lead(self, lead_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        for idx, lead in enumerate(self.leads):
            if lead["id"] == lead_id:
                self.leads[idx]={**lead, **payload, "id":lead_id}; return self._stamp(self.leads[idx])
        raise KeyError(f"Lead '{lead_id}' was not found in demo data.")
    def import_leads(self, filename: str, content: bytes) -> dict[str, Any]:
        try: rows=list(csv.DictReader(StringIO(content.decode("utf-8-sig"))))
        except UnicodeDecodeError as exc: raise ValueError("CSV must be UTF-8 encoded.") from exc
        created=[]
        for row in rows:
            if not (row.get("company_name") or "").strip(): continue
            created.append(self.create_lead({"company_name":row.get("company_name",""), "contact_name":row.get("contact_name",""), "email":row.get("email",""), "industry":row.get("industry",""), "company_size":row.get("company_size","Unknown"), "prospect_role":row.get("prospect_role",""), "status":row.get("status","New"), "stage":row.get("stage","Prospecting"), "website":row.get("website", ""), "company_description":row.get("company_description", ""), "engagement_history":"", "explicit_needs":"", "response_behavior":"", "user_research":""}))
        return {"imported":len(created), "skipped":len(rows)-len(created), "filename":filename, "_demo":True}
    def get_analytics(self, filters: dict[str, Any] | None = None) -> dict[str, Any]:
        leads=self.list_leads(filters)
        stages=["Prospecting","Discovery","Qualified","Proposal","Negotiation","Closed Won"]
        pipe=[{"stage":s,"count":sum(1 for l in leads if l.get("stage")==s)} for s in stages]
        score_dist=[{"band":"0–44","count":1},{"band":"45–69","count":1},{"band":"70–100","count":max(0,len(leads)-2)}]
        return {"source":self.source_label,"is_demo":True,"total_leads":len(leads),"qualified_leads":sum(1 for l in leads if l.get("stage") in {"Qualified","Proposal","Negotiation"}),"average_lead_score":67,"conversion_rate":None,"outreach_activity":3,"follow_up_tasks":sum(1 for r in self.follow_ups if r["status"]=="Open"),"pipeline_distribution":pipe,"lead_score_distribution":score_dist,"activity_trend":[{"date":"2026-10-12","activity":2},{"date":"2026-10-13","activity":4},{"date":"2026-10-14","activity":3},{"date":"2026-10-15","activity":5},{"date":"2026-10-16","activity":4},{"date":"2026-10-17","activity":6},{"date":"2026-10-18","activity":3}]}
    def save_company_insights(self, lead_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        self.get_lead(lead_id); item=self._stamp({"lead_id":lead_id, **payload}); self.saved["insights"].append(item); return item
    def save_lead_score(self, lead_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        self.get_lead(lead_id); item=self._stamp({"lead_id":lead_id, **payload}); self.saved["scores"].append(item); return item
    def save_outreach(self, lead_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        self.get_lead(lead_id); item=self._stamp({"id":f"draft-{len(self.outreach.get(lead_id,[]))+1}","lead_id":lead_id,**payload}); self.outreach.setdefault(lead_id,[]).append(item); return item
    def get_outreach(self, lead_id: str) -> list[dict[str, Any]]: return deepcopy(self.outreach.get(lead_id, []))
    def save_conversation(self, lead_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        self.get_lead(lead_id); item=self._stamp({"id":f"conv-{len(self.conversations.get(lead_id,[]))+1}","lead_id":lead_id,**payload}); self.conversations.setdefault(lead_id,[]).append(item); return item
    def get_conversations(self, lead_id: str) -> list[dict[str, Any]]: return deepcopy(self.conversations.get(lead_id, []))
    def get_follow_ups(self, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        status=(filters or {}).get("status"); rows=deepcopy(self.follow_ups)
        if status and status != "All": rows=[r for r in rows if r["status"]==status]
        return [self._stamp(x) for x in rows]
    def update_follow_up(self, recommendation_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        for idx,r in enumerate(self.follow_ups):
            if r["id"]==recommendation_id:
                self.follow_ups[idx]={**r,**payload}; return self._stamp(self.follow_ups[idx])
        raise KeyError(f"Recommendation '{recommendation_id}' was not found in demo data.")

MOCK_BACKEND = MockBackend()
