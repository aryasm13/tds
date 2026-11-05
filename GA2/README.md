# GA2 – Tools in Data Science (Sep 2026)

My GA2 live-server questions. They all share one FastAPI app, so there's a single Vercel deployment.

> This is my personal repo and it's **not affiliated with or endorsed by IIT Madras**.

- Your assigned values differ from mine. The top of [`ga2-api/api/index.py`](ga2-api/api/index.py) holds
  **my** email, allowed origin, API key, order count and rate limit, so replace them with your own first.
- LLMs and discussing with friends are allowed in this course, but do your own submission.

## What's in here

| Q | Endpoint | What it does |
|---|----------|--------------|
| 3 | `GET /stats` | Strict CORS for one allowed origin, plus `X-Request-ID` and `X-Process-Time` headers |
| 7 | `POST /analytics` | `X-API-Key` auth and event aggregation |
| 9 | `POST /v1/chat/completions` | OpenAI-compatible chat endpoint, answered by a real model through AI Pipe |
| 11 | `POST /orders`, `GET /orders` | Idempotent create (`Idempotency-Key`), cursor pagination, per-client rate limit |

The other GA2 questions I did directly on the exam page.

## Where it's deployed

**Vercel**, from [`ga2-api/`](ga2-api/):

1. Vercel → **Add New → Project** → import your fork, and set **Root Directory** to `GA2/ga2-api`.
2. Add the environment variable `AIPIPE_TOKEN` (only Q9 needs it). Never put it in the code.
3. **Deploy**, then paste `https://YOUR-APP.vercel.app` plus the path each question asks for into the exam page.

## Things that tripped me up

- **Q3:** a preflight from a wrong origin must be rejected **without** an `Access-Control-Allow-Origin`
  header, and only `/stats` is strict. Everything else stays open so the exam page can reach it.
- **Q9:** if `AIPIPE_TOKEN` isn't set in Vercel, the chat endpoint fails. Redeploy after adding env vars.
- **Q11:** the rate limit and idempotency store live in memory, so test against the live URL and not just
  locally. A cold start resets them.
