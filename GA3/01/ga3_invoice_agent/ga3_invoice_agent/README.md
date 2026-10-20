# GA3 A2A Invoice Agent

FastAPI implementation for the IITM TDS Sep 2026 GA3 invoice-agent contract, configured for PostgreSQL-backed persistent state.

## Required environment variables

- `DATABASE_URL`: PostgreSQL connection URL. On Render, use the database's **Internal Database URL** when the web service and database are in the same region.
- `AI_API_KEY`: API key for an OpenAI-compatible chat-completions provider.
- `AI_BASE_URL`: provider base URL, default `https://api.openai.com/v1`.
- `AI_MODEL`: model name, default `gpt-4o-mini`.
- `PORT`: listening port, supplied by Render.

Never commit database URLs or API keys to Git.

## Run locally

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
# Set DATABASE_URL, AI_API_KEY, and optional AI_BASE_URL / AI_MODEL in your environment.
uvicorn app:app --host 0.0.0.0 --port 8000
```

The submitted A2A base URL is expected to be `https://YOUR-HOST/a2a/`. The Agent Card is at `https://YOUR-HOST/.well-known/agent-card.json`.

Before spending a GA3 Check, verify the Agent Card, headers, database persistence, AI provider settings, and the hidden audit/lifecycle cases.
