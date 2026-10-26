# Team-C utility scope

The following modules are the non-Streamlit utility portion of this handoff:

- `utils/__init__.py`
- `utils/config.py`
- `utils/csv_import.py`
- `utils/logging.py`
- `utils/validation.py`

`utils/config.py` still contains optional Streamlit secrets/session-state
access. Replacing that with a framework-neutral settings provider is an
integration follow-up and has intentionally not been applied in this PR.
