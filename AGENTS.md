# Repository Guidelines

## Project Structure & Module Organization
The MCP server lives in `src/`, split into `core/` (Jira client + config), `models/` (Pydantic request/response schemas), and `operations/` (tool handlers invoked by the MCP runtime). `simple_jira.py` is the entry point used by assistant integrations, while `run-jira-mcp.sh` wraps it for local launches. Tests sit at the repo root (`test_mcp.py`, `test_jira_operations.py`) and assume your environment variables mirror the `.env` template. Integration descriptors (`mcp.json`, AI guide docs) stay beside the code for quick reference.

## Build, Test, and Development Commands
Use a virtualenv before installing deps:
```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```
Run the server for local validation:
```bash
./run-jira-mcp.sh
# or
python simple_jira.py --transport stdio
```
Smoke-test the MCP contract:
```bash
python test_mcp.py
python test_jira_operations.py  # requires live JIRA creds
```

## Coding Style & Naming Conventions
Follow PEP 8 with 4-space indentation, `snake_case` for modules/functions, and PascalCase for Pydantic models (e.g., `CloneIssueArgs`). Type hints are expected across the codebase, and public APIs should raise `JiraError` variants or return JSON-friendly dicts. Prefer structured logging through `logging.getLogger("simple_jira")` and keep comments focused on non-obvious logic.

## Testing Guidelines
Both test scripts rely on FastMCP’s stdio client; export `JIRA_URL`, `JIRA_USERNAME`, and `JIRA_API_TOKEN` beforehand. `test_mcp.py` verifies tool discovery, while `test_jira_operations.py` exercises live operations—run it against sandboxes only and inspect JSON payloads it prints for regressions. Add targeted async snippets under `test_*.py` when introducing new tools, keeping fixture setup minimal and flagging network-required tests in docstrings.

## Commit & Pull Request Guidelines
Existing history follows Conventional Commits (`feat:`, `fix:`, `docs:`, `refactor:`). Keep subject lines under ~70 chars and explain scope in the body when behavior changes. Pull requests should link relevant JIRA issues, summarize the user impact, note any MCP tool signature changes, and include manual test notes (e.g., commands above). Mention doc updates when touching user-facing behavior.

## Security & Configuration Tips
Store secrets in `.env` (never commit) and confirm HTTPS endpoints before connecting. Rotate API tokens regularly and audit logs when running `test_jira_operations.py`, as it can create or modify issues depending on arguments. Review `ARCHITECTURE.md` whenever changing authentication or transport concerns to maintain alignment with the documented flow.
