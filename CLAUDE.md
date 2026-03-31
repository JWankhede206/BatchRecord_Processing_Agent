# Batch Record Agent

## Project Scope
Local Python pipeline that processes pharma batch record PDFs placed in `data/`, extracts structured information via OpenAI, runs basic completeness checks, and writes JSON + markdown summaries to `output/`.

## Constraints
- No database, Redis, queues, or background workers
- Minimal web UI (FastAPI + single HTML page, no auth)
- No complex multi-agent routing or unnecessary abstractions
- No deep data integrity logic or cross-document reconciliation
- No advanced GMP/compliance engines
- Keep infrastructure minimal and code modular but not over-engineered

## Tech Stack
- Python, PyMuPDF, OpenAI API, Pydantic, python-dotenv, FastAPI, uvicorn

## Running
```bash
python src/main.py                          # CLI: process all PDFs in data/
python src/app.py                           # Web UI on http://localhost:8000
python -m pytest tests/                     # run tests
```

## Key Architecture
- `src/models/` — Pydantic schemas (document, extraction, finding)
- `src/services/` — Pipeline steps (parse, extract, evaluate, summarize)
- `src/utils/` — File I/O and logging helpers
- `src/config.py` — Environment config
- `src/openai_client.py` — Thin OpenAI wrapper
- `src/main.py` — CLI entry point and pipeline orchestration
- `src/app.py` — FastAPI web UI entry point
- `src/templates/index.html` — Single-page eval dashboard
