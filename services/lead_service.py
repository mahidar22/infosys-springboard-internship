from __future__ import annotations
from typing import Any
from services.api_client import APIClient
from utils.validation import validate_lead_payload

def fetch_leads(client: APIClient, filters: dict[str, Any] | None=None)->list[dict[str,Any]]: return client.list_leads(filters)
def save_lead(client: APIClient,payload:dict[str,Any],lead_id:str|None=None)->dict[str,Any]:
    errors=validate_lead_payload(payload)
    if errors: raise ValueError(" ".join(errors))
    return client.update_lead(lead_id,payload) if lead_id else client.create_lead(payload)
