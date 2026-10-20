# SalesGenie AI

A Streamlit **frontend and AI-intelligence layer** for sales teams. It provides lead views, evidence-aware research and qualification, editable outreach drafts, explainable lead scoring, transcript intelligence, follow-up recommendations, and sales analytics interpretation.

> **Scope boundary:** this repository does not implement a backend API, database, authentication, migrations, direct SQL, message delivery, or persistent storage. It connects to the separately-owned backend through `services/api_client.py`. Demo mode uses a visibly labelled in-memory adapter and deterministic mock AI so the product remains usable without paid credentials.

## Features

- Eight Streamlit navigation pages: Dashboard, Lead Management, Lead Intelligence, Outreach Generator, Lead Scoring, Conversation Intelligence, Follow-up Recommendations, and AI Activity & Configuration.
- Plotly metric cards and interactive pipeline, score, and activity charts sourced from the configured backend.
- LangGraph operation router that invokes only the required agents:
  - Lead Research and Qualification
  - Outreach generation
  - Conversation intelligence (including chunked/hierarchical treatment for long transcripts)
  - Follow-up recommendation
  - Sales analytics insight
- Validated Pydantic outputs with evidence/provenance, uncertainty, missing-information, and error handling.
- Configurable mock/OpenAI/Gemini provider abstraction, retry policy, timeout configuration, and execution activity log.
- Configurable rule-based lead scoring with factor-level explanations. It intentionally does **not** label heuristic results as conversion probabilities.
- Browser review/edit controls and backend save actions; no outreach is sent automatically.

## Quick start

```bash
cd salesgenie-ai
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows: 
.venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # then export/load these variables with your preferred dotenv workflow
streamlit run app.py
```

The default configuration is demo mode. It shows an in-app banner and returns deterministic demo data / AI output; none of it represents real business analytics or external company research.

Run tests:

```bash
pytest -q
```

## Configuration

Copy `.env.example` and set environment variables (or put equivalent values in Streamlit secrets). Never commit `.env` or `secrets.toml`.

| Variable | Purpose |
|---|---|
| `SALES_GENIE_DEMO_MODE` | `true` uses the clearly marked mock backend and deterministic AI. |
| `SALES_GENIE_BACKEND_BASE_URL` | Existing backend origin, e.g. `https://api.example.com`. |
| `SALES_GENIE_BACKEND_API_PREFIX` | API prefix, default `/api/v1`. |
| `SALES_GENIE_BACKEND_TOKEN` | Optional bearer credential; never rendered or logged. |
| `SALES_GENIE_ENDPOINT_OVERRIDES_JSON` | Optional JSON map to approved backend path overrides. |
| `SALES_GENIE_LLM_PROVIDER` | `mock`, `openai`, or `gemini`. |
| `SALES_GENIE_LLM_MODEL` | Provider model name. |
| `OPENAI_API_KEY` / `GOOGLE_API_KEY` | Provider secret for non-mock execution. |
| timeout/retry/score variables | Safe operational and UI defaults. |

To use a live system set `SALES_GENIE_DEMO_MODE=false`, configure the backend URL/authentication, choose `openai` or `gemini`, set the matching API key, and select an appropriate model. The Configuration page confirms health/provider behaviour without displaying secrets.

## Backend interface

The adapter path/payload contract is documented in [`docs/backend_api_contract.md`](docs/backend_api_contract.md). It supports plain JSON bodies and `{ "data": ... }` envelopes. Update endpoint mappings in `services/api_client.py` or adapt `BackendAdapter` to match the backend’s approved contract; do not add data access to Streamlit.

## Architecture

```text
Streamlit pages + reusable components
        │ forms, review/edit state, loading/error states
        ▼
services/APIClient ─────────────► Existing backend REST API
        │                              ▲
        │                              └─ persistence/auth owned elsewhere
        ▼
ai/graph.py (LangGraph stateful operation router)
        ▼
research | qualification | outreach | conversation | follow-up | sales-insights agents
        ▼
provider boundary (Mock / OpenAI / Gemini) + Pydantic validation
```

- `ai/prompts/templates.py` delimits user-provided material as untrusted data and prohibits prompt instructions from overriding system rules.
- `ai/schemas.py` is the validation boundary before outputs reach UI/save requests.
- `ai/scoring/rule_based.py` is a modular heuristic implementation. `ai/scoring/models.py` also defines an opt-in adapter for an externally fitted/evaluated scikit-learn estimator; it refuses activation without an evaluation note and no model artefact ships here.
- The graph captures typed request, intermediate research/qualification, errors, and final result. Nodes handle failures and the UI records non-sensitive timing/provider diagnostics. `run_workflow(..., checkpointer=..., thread_id=...)` supports an explicitly supplied LangGraph checkpointer for approved resumability; the UI does not silently persist workflow state.
- Runtime UI settings use Streamlit session state only for browser-specific configuration, unsaved draft/review content, and visible execution activity. AI workflows do not depend on Streamlit state.

## Safety and truthfulness

- Website/company research is never claimed unless retrieved through an approved integration. This project ships no web retrieval connector.
- Source-supported facts and AI hypotheses receive different UI treatments.
- Transcripts, notes, uploaded data, and external content are untrusted. Prompts explicitly prevent embedded instructions from changing the task.
- Conversation summaries do not invent requirements, commitments, owners, or dates; absent items remain absent/uncertain.
- Generating a recommendation or draft does not mark external work complete or send a message.

## Project structure

```text
app.py                     # Streamlit entry point
pages/                     # eight required product pages
components/                # reusable UI, charts, editors, panels
ai/                        # LangGraph state/router, agents, schemas, prompts, providers, scoring
services/                  # frontend-to-backend REST client and domain wrappers
integrations/              # backend protocol and in-memory demo adapter
utils/                     # configuration, validation, logging
docs/backend_api_contract.md
tests/                     # offline automated tests
```
