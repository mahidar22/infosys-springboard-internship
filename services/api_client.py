"""HTTP client for existing backend. No database operations occur in this layer."""
from __future__ import annotations
import time
from typing import Any
import httpx
from integrations.mock_backend import MOCK_BACKEND
from utils.config import Settings
from utils.logging import get_logger

logger=get_logger(__name__)
class BackendAPIError(RuntimeError): pass

# Paths/payloads are documented in docs/backend_api_contract.md and may be overridden by the backend gateway.
PATHS={"health":"/health","leads":"/leads","analytics":"/analytics","follow_ups":"/follow-ups"}

class APIClient:
    def __init__(self, settings: Settings, transport: httpx.BaseTransport | None = None):
        self.settings=settings; self.mock= settings.demo_mode
        self.paths={**PATHS, **settings.backend_endpoint_overrides}
        self._client=httpx.Client(base_url=f"{settings.backend_base_url}{settings.backend_api_prefix}", timeout=settings.request_timeout_seconds, transport=transport, headers={"Authorization":f"Bearer {settings.backend_token}"} if settings.backend_token else {}) if not self.mock else None
    @property
    def source_label(self)->str: return MOCK_BACKEND.source_label if self.mock else "Backend API"
    def _path(self,key:str,*parts:str)->str: return self.paths[key]+("/"+"/".join(str(x).strip("/") for x in parts) if parts else "")
    def _request(self,method:str,path:str,**kwargs:Any)->Any:
        if not self._client: raise BackendAPIError("Backend client is not configured.")
        last=None
        for i in range(self.settings.request_retries+1):
            try:
                response=self._client.request(method,path,**kwargs); response.raise_for_status()
                data=response.json() if response.content else {}
                return data.get("data",data) if isinstance(data,dict) else data
            except (httpx.HTTPError, ValueError) as exc:
                last=exc
                if i<self.settings.request_retries: time.sleep(min(.3*(2**i),1.5))
        raise BackendAPIError(f"Backend request {method} {path} failed: {last}") from last
    def health(self): return MOCK_BACKEND.health() if self.mock else self._request("GET",self._path("health"))
    def list_leads(self,filters=None): return MOCK_BACKEND.list_leads(filters) if self.mock else self._request("GET",self._path("leads"),params=filters or {})
    def get_lead(self,lead_id):
        try:return MOCK_BACKEND.get_lead(lead_id) if self.mock else self._request("GET",self._path("leads",lead_id))
        except (KeyError, httpx.HTTPError) as e: raise BackendAPIError(str(e)) from e
    def create_lead(self,payload): return MOCK_BACKEND.create_lead(payload) if self.mock else self._request("POST",self._path("leads"),json=payload)
    def update_lead(self,lead_id,payload): return MOCK_BACKEND.update_lead(lead_id,payload) if self.mock else self._request("PATCH",self._path("leads",lead_id),json=payload)
    def import_leads(self,filename,content): return MOCK_BACKEND.import_leads(filename,content) if self.mock else self._request("POST",self._path("leads","import"),files={"file":(filename,content,"text/csv")})
    def get_analytics(self,filters=None): return MOCK_BACKEND.get_analytics(filters) if self.mock else self._request("GET",self._path("analytics"),params=filters or {})
    def save_company_insights(self,lead_id,payload): return MOCK_BACKEND.save_company_insights(lead_id,payload) if self.mock else self._request("POST",self._path("leads",lead_id,"insights"),json=payload)
    def save_lead_score(self,lead_id,payload): return MOCK_BACKEND.save_lead_score(lead_id,payload) if self.mock else self._request("POST",self._path("leads",lead_id,"scores"),json=payload)
    def save_outreach(self,lead_id,payload): return MOCK_BACKEND.save_outreach(lead_id,payload) if self.mock else self._request("POST",self._path("leads",lead_id,"outreach-drafts"),json=payload)
    def get_outreach(self,lead_id): return MOCK_BACKEND.get_outreach(lead_id) if self.mock else self._request("GET",self._path("leads",lead_id,"outreach-drafts"))
    def save_conversation(self,lead_id,payload): return MOCK_BACKEND.save_conversation(lead_id,payload) if self.mock else self._request("POST",self._path("leads",lead_id,"conversations"),json=payload)
    def get_conversations(self,lead_id): return MOCK_BACKEND.get_conversations(lead_id) if self.mock else self._request("GET",self._path("leads",lead_id,"conversations"))
    def get_follow_ups(self,filters=None): return MOCK_BACKEND.get_follow_ups(filters) if self.mock else self._request("GET",self._path("follow_ups"),params=filters or {})
    def update_follow_up(self,rid,payload): return MOCK_BACKEND.update_follow_up(rid,payload) if self.mock else self._request("PATCH",self._path("follow_ups",rid),json=payload)
    def close(self):
        if self._client:self._client.close()
