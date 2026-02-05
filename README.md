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
- `.env` file with `API_SECRET_KEY` and either local Ollama or at least one LLM provider key (see [Configuration](#configuration) and [Local Llama](#local-llama-ollama--dev-without-api-keys))

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
| `USE_LOCAL_LLM_ONLY` | No | When `true`, use **only** local Ollama (ignore Groq, OpenRouter, etc.). Good for dev. |
| `OLLAMA_BASE_URL` | No | Local Ollama (e.g. `http://localhost:11434/v1`); no key needed. |
| `LLM_MODEL` | No | Model name for Ollama (e.g. `deepseek-r1:8b`, `llama3.2`). Default when local: `deepseek-r1:8b`. |
| `LOG_LEVEL` | No | `DEBUG`, `INFO`, `WARNING`, `ERROR` (default: `INFO`). |
| `LOG_FORMAT` | No | `json` (production) or `console` (dev). |
| `LOG_FILE` | No | Optional file path; daily rotation, 30 backups. |
| `SCAM_KEYWORDS_FILE` | No | Path to file with extra scam keywords (one per line). |

See `.env.example` for all options.

## Local Llama / DeepSeek-R1 (Ollama) — dev without API keys

To use **only** local models on your machine via Ollama (e.g. Llama 3, DeepSeek-R1):

1. **Install Ollama**  
   - https://ollama.com — download and install, then start the Ollama app (or run `ollama serve`).

2. **Pull a model** (one-time):
   ```bash
   # Default (recommended for honeypot - reasoning model):
   ollama pull deepseek-r1:8b
   
   # Alternative:
   ollama pull llama3.2
   ```

3. **In `.env`** set:
   ```env
   USE_LOCAL_LLM_ONLY=true
   OLLAMA_BASE_URL=http://localhost:11434/v1
   LLM_MODEL=deepseek-r1:8b
   ```
   (Or `llama3.2`, `llama3`. Omit `LLM_MODEL` to use default `deepseek-r1:8b`.)

4. **Start the app** as usual (`python run.py` or `uvicorn src.main:app --host 0.0.0.0 --port 8000`).  
   The agent and scam-confirmation LLM will use only Ollama; Groq/OpenRouter/etc. are ignored.

To **turn off** local-only and use cloud APIs again, set `USE_LOCAL_LLM_ONLY=false` or remove that line from `.env`.

**Why DeepSeek-R1?** It's a **reasoning model** — better at following complex instructions like "don't reveal you're AI" and "keep scammer engaged" than standard Llama. The 8B version fits in 12GB VRAM (quantized 4-bit/6-bit).

## Best config for hackathon / deployment

**For maximum speed and quality**, use `.env.deployment` as a template or set:

```env
# PRIMARY: Groq (fast, free, high quality - Llama 3.3 70B)
GROQ_API_KEYS=gsk_YOUR_KEY_HERE

# IMPORTANT: Turn OFF Ollama for deployment (adds latency if not running)
# OLLAMA_BASE_URL=

# Speed optimization: disable slow scam LLM confirm (saves ~15s/request)
DISABLE_SCAM_LLM_CONFIRM=true

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

Why this config:
- **Groq Llama 3.3 70B** is free, faster than GPT-4o-mini, and higher quality than 8B models.
- **Disable scam LLM confirm** — heuristics are sufficient; LLM confirmation adds ~15 seconds per request.
- **No Ollama in deployment** — if `OLLAMA_BASE_URL` is set, it tries Ollama first (fails if not running → 14s delay).

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

### Basic tests

1. Start the server (in one terminal):
   ```bash
   set PYTHONPATH=%CD%
   python run.py
   ```
2. Run the test script (in another terminal):
   ```bash
   python scripts/test_api.py
   ```
   The script checks: health, first scam message (expects reply), follow-up (multi-turn), scam with extractable data (UPI/bank), non-scam (expects empty reply). Exit code 0 = all passed, 1 = failure.
3. **Callback**: When a scam is detected, the server POSTs to the GUVI callback. Check the **server terminal** for lines like `callback_sent` with `extracted_intelligence_summary`.

### Multi-turn conversation testing (with Mock Scammer)

Test realistic **20-turn conversations** (~40 messages) where the agent extracts maximum intelligence:

1. **Start Ollama** (if not running): `ollama serve` and `ollama pull deepseek-r1:8b`
2. **Start honeypot**: `python run.py` (terminal 1)
3. **Start mock scammer**: `python scripts/mock_scammer.py` (terminal 2)
4. **Run conversation test**: `python scripts/test_conversation.py` (terminal 3)

Or use the **quick launcher**: `.\scripts\start_mock_test.ps1`

The test runs for **20 turns by default** (auto-ends for quick results). This simulates a real scammer that provides UPI IDs, bank accounts, phone numbers, etc., and your agent keeps them engaged to extract maximum intel. See `MOCK_SCAMMER_GUIDE.md` and `CONVERSATION_STRATEGY.md` for details.

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
