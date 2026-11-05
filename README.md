# TDS – Tools in Data Science (IIT Madras BS, Sep 2026)

Scripts, servers and configs I used for the graded assignments of the IIT Madras BS course *Tools in Data
Science*, cleaned up so classmates can follow along. Every student gets different data, so this repo holds
**methods and code only**, with no answers. The few data files in here are ones a script or deployment needs.

> **Course policy:** You may use Large Language Models (LLMs). You may collaborate on assignments. Every student's data differs, so run the scripts on your own files.
>
> This is my personal repo and it's **not affiliated with or endorsed by IIT Madras**.

## Progress

| Assignment | Status | Notes |
|---|---|---|
| [GA0](GA0/README.md) | Done | Scripts + one Vercel endpoint |
| [GA1](GA1/README.md) | Done | Scripts + two Vercel apps |
| [GA2](GA2/README.md) | Done | One Vercel app for all live-server questions |
| [GA3](GA3/README.md) | Done | Two Render agents + face GLB, morph video, ranking |
| GA4 | Q1 done | Q1 is the peer review of GA3 faces in the review app, so there's no code. More questions are still being released |

## What's deployed where

| Assignment | Q | What | Platform | Root Directory |
|---|---|---|---|---|
| GA0 | 25 | `POST /api/latency` | Vercel | `GA0/tds-latency` |
| GA1 | 6 | `GET /effective-config` (12-factor config) | Vercel | `GA1/config-service` |
| GA1 | 13 | termlog `submission.tar.gz` | Raw GitHub URL | `GA1/13` |
| GA1 | 15 | `POST /answer` (ledger agent) | Vercel | `GA1/leader-agent` |
| GA2 | 3, 7, 9, 11 | `/stats`, `/analytics`, `/v1/chat/completions`, `/orders` | Vercel | `GA2/ga2-api` |
| GA3 | 2 | A2A invoice agent | Render (Docker + PostgreSQL) | `GA3/01/ga3_invoice_agent/ga3_invoice_agent` |
| GA3 | 4 | Incident triage agent | Render (Docker + PostgreSQL) | `GA3/04` |
| GA3 | 6, 7 | `zapata_face.glb`, `morph.mp4` | Raw GitHub URL | `GA3/06`, `GA3/07` |

Each assignment's README has the exact deploy steps and the environment variables it needs.

## Folder layout

```text
.
├── email.json                        GA0 Q24 Use GitHub (graded file)
├── .github/workflows/test.yml        GA0 Q13 GitHub Action (graded: a step named with the email)
├── GA0/                              Q4–Q22 scripts, tds-latency/ (Q25 Vercel), _private/ (git-ignored)
├── GA1/
│   ├── config-service/               Q6  12-factor config service (Vercel)
│   ├── 07/ 08/ 10/ 11/ 13/           Q7 reorganize, Q8 data, Q10 git forensics, Q11 cosine similarity, Q13 termlog
│   └── leader-agent/                 Q15 LLM ledger agent (Vercel)
├── GA2/
│   └── ga2-api/                      Q3, Q7, Q9, Q11 in one FastAPI app (Vercel)
└── GA3/
    ├── 01/ga3_invoice_agent/…        Q2  A2A invoice agent (Render)
    ├── 04/                           Q4  incident triage agent (Render)
    ├── 06/ 07/                       Q6  face GLB, Q7 face morph video
    └── 08/                           Q8  morph ranking PDF
```

If you fork this repo, replace my values with yours:
- your email in `email.json`, `.github/workflows/test.yml` and `GA0/q18_ngrok_policy.yml`
- your own `q-vercel-latency.json` in `GA0/tds-latency/`
- your `.env` values in `GA1/config-service/`
- the assigned values at the top of `GA2/ga2-api/api/index.py`

## Running the scripts

Install [uv](https://docs.astral.sh/uv/), `cd` into the assignment folder, then pass the path to **your**
downloaded file, e.g.

```bash
uv run q04_calculate_variance.py _private/q-calculate-variance.json
```

The docstring at the top of each script shows its run command. Scripts that need input files print it when
run without arguments. If `uv` is not on your PATH, use `python -m uv run ...` instead.

## Setting AIPIPE_TOKEN

GA0 Q5/Q11, GA1 Q15, GA2 Q9 and the GA3 agents call an LLM through [AI Pipe](https://aipipe.org/). They read
the token **only** from an environment variable (`AIPIPE_TOKEN`, or `AI_API_KEY` for the GA3 agents), so never
paste it into code or commit it. On Vercel and Render, add it under the project's **Environment Variables**.

Windows PowerShell (current terminal session):

```powershell
$env:AIPIPE_TOKEN = "YOUR_AIPIPE_TOKEN"
```

Linux / macOS / Git Bash:

```bash
export AIPIPE_TOKEN="YOUR_AIPIPE_TOKEN"
```
