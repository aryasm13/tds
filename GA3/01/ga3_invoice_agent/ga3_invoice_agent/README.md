# GA3 A2A Invoice Agent

Python/FastAPI implementation scaffold for the IITM TDS Sep 2026 GA3 invoice-agent contract.

## Required environment variables

- `AI_API_KEY`: API key for an OpenAI-compatible chat-completions provider.
- `AI_BASE_URL`: provider base URL, default `https://api.openai.com/v1`.
- `AI_MODEL`: model name, default `gpt-4o-mini`.
- `DB_PATH`: SQLite file path, default `/data/invoice_agent.sqlite3`.
- `PORT`: listening port, default `8000`.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
export AI_API_KEY='your-key'
uvicorn app:app --host 0.0.0.0 --port 8000
```

The submitted A2A base URL is expected to be `https://YOUR-HOST/a2a/`. The Agent Card is at `https://YOUR-HOST/.well-known/agent-card.json`.

## Important deployment notes

Use a persistent disk for `/data`; an ephemeral filesystem loses task/idempotency state on restart. Set all secrets in the hosting provider's environment settings, never in Git. Before spending a GA3 Check, verify the Agent Card, headers, database persistence, and AI provider settings.

This is a starter implementation and must be tested against the live grader. In particular, verify the host's external URL handling, model response compatibility, package field shapes, and all hidden audit/lifecycle cases before relying on it for marks.
