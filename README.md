# Agentic Honey-Pot for Scam Detection

AI-powered honeypot API that detects scam intent, engages with a human-like agent, and extracts intelligence. Built for the **India AI Impact Buildathon (Problem Statement 2)**.

## Overview

- **REST API**: Accepts incoming message events; returns structured JSON (`status`, `reply`).
- **Scam detection**: Heuristics + optional LLM confirmation.
- **Autonomous agent**: Multi-turn, human-like replies via configurable LLM providers.
- **Intelligence extraction**: Bank accounts, UPI IDs, links, phone numbers, keywords.
- **Mandatory callback**: Sends final result to GUVI evaluation endpoint when scam is detected.
- **Authentication**: `x-api-key` header required.

## Requirements

- Python 3.10+
- `.env` file with `API_SECRET_KEY` and at least one LLM provider key (see [Configuration](#configuration))

## Quick start

```bash
# Clone and enter project
cd agentic-honeypot-scam-detection

# Create and activate virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure (copy example and edit)
cp .env.example .env
# Set API_SECRET_KEY and at least one LLM key (e.g. GROQ_API_KEYS)

# Run (development: auto-reload on code and .env changes)
set PYTHONPATH=%CD%   # Windows cmd
# export PYTHONPATH=$PWD  # Linux/macOS
set RELOAD=true && python run.py   # Windows
# RELOAD=true python run.py         # Linux/macOS
# For production, omit RELOAD or use: uvicorn src.main:app --host 0.0.0.0 --port 8000
```

- **Health**: `GET http://localhost:8000/health`
- **Honeypot**: `POST http://localhost:8000/` with header `x-api-key` and JSON body (see `agentic_honeypot_project_description.md` or `docs/READINESS_CHECKLIST.md`).
- **OpenAPI**: http://localhost:8000/docs | http://localhost:8000/redoc

## Configuration

| Variable | Required | Description |
|----------|----------|-------------|
| `API_SECRET_KEY` | Yes | Secret for `x-api-key`; must not be the default placeholder. |
| `GUVI_CALLBACK_URL` | No | Callback endpoint (default: `https://hackathon.guvi.in/api/updateHoneyPotFinalResult`). |
| `GROQ_API_KEYS` | One of | Comma-separated keys; tried first for agent and notes. |
| `OPENROUTER_API_KEYS` | One of | Comma-separated; OpenRouter models. |
| `GITHUB_API_KEYS` | One of | GitHub Models (PAT with `models:read`). |
| `OPENAI_API_KEYS` | One of | OpenAI API keys. |
| `OLLAMA_BASE_URL` | No | Local Ollama (e.g. `http://localhost:11434/v1`); no key needed. |
| `LOG_LEVEL` | No | `DEBUG`, `INFO`, `WARNING`, `ERROR` (default: `INFO`). |
| `LOG_FORMAT` | No | `json` (production) or `console` (dev). |
| `LOG_FILE` | No | Optional file path; daily rotation, 30 backups. |
| `SCAM_KEYWORDS_FILE` | No | Path to file with extra scam keywords (one per line). |

See `.env.example` for all options.

## Production deployment

- **Do not use `reload`** in production. Run:
  ```bash
  uvicorn src.main:app --host 0.0.0.0 --port 8000
  ```
  Or set `RELOAD=false` and use `python run.py` (see `run.py`).

- Set `LOG_FORMAT=json` and optionally `LOG_FILE` for structured logs.
- Use a strong `API_SECRET_KEY` and keep `.env` out of version control (see `.gitignore`).
- Expose the app behind HTTPS and a reverse proxy (e.g. nginx, Caddy) in production.

## Testing

1. Start the server (in one terminal):
   ```bash
   set PYTHONPATH=%CD%
   python run.py
   ```
2. Run the test script (in another terminal):
   ```bash
   python scripts/test_api.py
   ```
   The script checks: health, first scam message (expects reply), follow-up (multi-turn), non-scam (expects empty reply). Exit code 0 = all passed, 1 = failure.
3. **Callback**: When a scam is detected, the server POSTs to the GUVI callback. Check the **server terminal** for lines like `callback session_id=... success=True` and `HTTP Request: POST ... updateHoneyPotFinalResult "HTTP/1.1 200 OK"`.

## Project layout

| Path | Purpose |
|------|----------|
| `src/main.py` | FastAPI app, auth, request pipeline, callback trigger. |
| `src/models.py` | Request/response and callback Pydantic models. |
| `src/config.py` | Settings from environment. |
| `src/logging_config.py` | Structured logging, request context. |
| `src/scam_detection.py` | Scam intent (heuristics + optional LLM). |
| `src/agent.py` | Human-like reply and agent notes (LLM). |
| `src/llm_config.py` | LLM provider selection and fallback order. |
| `src/intelligence.py` | Extract bank/UPI/links/phones/keywords. |
| `src/callback.py` | POST final result to GUVI. |
| `scripts/test_api.py` | Local API test (health, scam, multi-turn, non-scam). |
| `run.py` | Dev entrypoint (uvicorn with optional reload). |
| `docs/READINESS_CHECKLIST.md` | Requirement vs implementation checklist. |
| `docs/azure-content-filter-notes.md` | Notes on Azure content filter and provider choice. |
| `agentic_honeypot_project_description.md` | Full problem statement and API spec. |

## Before submission

- Ensure `.env` is not committed (`.gitignore` excludes it).
- Remove `__pycache__` if you want a clean tree:
  - **Windows (PowerShell)**: `Get-ChildItem -Path . -Recurse -Directory -Filter __pycache__ | Remove-Item -Recurse -Force`
  - **Linux/macOS**: `find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; true`
- Run `python scripts/test_api.py` with the server up to confirm all checks pass.

## License

See repository or project terms.
