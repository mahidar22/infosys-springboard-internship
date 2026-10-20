# SalesGenie backend adapter contract

This frontend deliberately owns **no** database, authentication, or persistent-storage implementation. `services.api_client.APIClient` is the only backend boundary. In non-demo mode it prefixes these paths with `SALES_GENIE_BACKEND_API_PREFIX` (default `/api/v1`) and wraps payloads from either a plain JSON response or `{ "data": ... }` envelope.

Authentication is configurable: when `SALES_GENIE_BACKEND_TOKEN` is present the client sends `Authorization: Bearer <token>`. Replace or extend this adapter for the existing gateway's authentication contract rather than adding auth in Streamlit. If the approved gateway uses different root paths, set `SALES_GENIE_ENDPOINT_OVERRIDES_JSON` to a JSON map such as `{"follow_ups":"/tasks/follow-ups"}`; resource suffixes remain appended by the adapter.

## Endpoint map

| Operation | Method and path | Request | Expected response |
|---|---|---|---|
| Health | `GET /health` | — | `{status, mode?}` |
| Search leads | `GET /leads` | query: `query`, `status`, `stage`, `industry` | `Lead[]` |
| Read lead | `GET /leads/{lead_id}` | — | `Lead` |
| Create lead | `POST /leads` | `LeadWrite` | `Lead` |
| Update lead | `PATCH /leads/{lead_id}` | partial `LeadWrite` | `Lead` |
| CSV import | `POST /leads/import` | multipart `file` | `{imported, skipped, errors?}` |
| Analytics | `GET /analytics` | optional filters | `Analytics` |
| Save company intelligence | `POST /leads/{lead_id}/insights` | `{research, qualification, execution}` | saved object |
| Save heuristic score | `POST /leads/{lead_id}/scores` | `{score, weights, method}` | saved object |
| List/save outreach | `GET` / `POST /leads/{lead_id}/outreach-drafts` | `OutreachDraftWrite` on POST | `OutreachDraft[]` / saved object |
| List/save conversations | `GET` / `POST /leads/{lead_id}/conversations` | `{summary, execution}` on POST | `Conversation[]` / saved object |
| List follow-ups | `GET /follow-ups` | query: `status` | `Recommendation[]` |
| Update follow-up | `PATCH /follow-ups/{recommendation_id}` | `{status}` | `Recommendation` |

## Schemas

### `Lead`

```json
{
  "id": "string",
  "company_name": "string",
  "contact_name": "string",
  "email": "string",
  "website": "string",
  "industry": "string",
  "company_size": "Unknown | 1-10 | 11-50 | 51-200 | 201-1000 | 1000+",
  "company_description": "string",
  "prospect_role": "string",
  "status": "New | Active | Inactive | Closed",
  "stage": "Prospecting | Discovery | Qualified | Proposal | Negotiation | Closed Won | Closed Lost",
  "engagement_history": "string",
  "explicit_needs": "string",
  "response_behavior": "string",
  "user_research": "string"
}
```

`LeadWrite` omits `id` and may omit optional fields. The frontend validates company name, email format if supplied, and URL shape before sending; the backend remains authoritative for validation errors.

### `Analytics`

```json
{
  "total_leads": 0,
  "qualified_leads": 0,
  "average_lead_score": 0,
  "conversion_rate": null,
  "outreach_activity": 0,
  "follow_up_tasks": 0,
  "pipeline_distribution": [{"stage": "Discovery", "count": 0}],
  "lead_score_distribution": [{"band": "70-100", "count": 0}],
  "activity_trend": [{"date": "2026-10-19", "activity": 0}]
}
```

Return `null` / omit a metric that is not available; the frontend displays “Not provided”, never an invented business value.

### AI payloads

Structured AI models are serialized from Pydantic in `ai/schemas.py`. `research` separates `supported_facts` (with provenance) from `potential_challenges`, `possible_needs`, and `opportunities` (explicit hypotheses). Scores contain a `methodology_note` stating they are heuristic, not a conversion probability. Conversation action items carry source evidence and optional owner/due date only when extracted explicitly.

## Demo adapter

`integrations/mock_backend.py` implements this same adapter in process, with `_demo: true` / source metadata. It is only selected when `SALES_GENIE_DEMO_MODE=true`; it is not a production integration or persistent store.
