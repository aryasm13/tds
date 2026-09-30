# TDS – Tools in Data Science (IIT Madras BS, Sep 2026)

Scripts and configs I used for the graded assignments of the IIT Madras BS course *Tools in Data Science*,
cleaned up so classmates can follow along. Every student gets different data, so this repo holds **methods and
code only**: no answers, and no downloaded data except the telemetry file the Q25 Vercel deployment needs.

> **Course policy:** You may use Large Language Models (LLMs). You may collaborate on assignments. Every student's data differs, so run the scripts on your own files.

## Folder layout

```text
.
├── email.json                        Q24 Use GitHub (graded file)
├── .github/workflows/test.yml        Q13 GitHub Action (graded: a step named with the email)
└── GA0/
    ├── q04_calculate_variance.py     Q4  Calculate variance
    ├── q05_code_interpreter.py       Q5  Code interpreter with AI error analysis (FastAPI + AI Pipe)
    ├── q07_crawl_html.py             Q7  Count crawled HTML files
    ├── q10_students_api.py           Q10 FastAPI server to serve CSV data
    ├── q11_sentiment_api.py          Q11 FastAPI batch sentiment analysis (AI Pipe + keyword fallback)
    ├── q14_jigsaw_grayscale.py       Q14 Reconstruct and desaturate an image
    ├── q16_move_rename_files.py      Q16 Move and rename files
    ├── q18_ngrok_policy.yml          Q18 Local Ollama endpoint: ngrok traffic policy (X-Email + CORS headers)
    ├── q19_replace_across_files.py   Q19 Replace across files
    ├── q22_unicode_data.py           Q22 Process files with different encodings
    ├── tds-latency/                  Q25 Vercel POST /api/latency endpoint (deployed from this folder)
    └── _private/                     git-ignored: keep your downloads, outputs and notes here
```

If you fork this repo, put your own email in `email.json`, `.github/workflows/test.yml` and
`GA0/q18_ngrok_policy.yml`, and your own `q-vercel-latency.json` in `GA0/tds-latency/`.

## Running the scripts

Install [uv](https://docs.astral.sh/uv/), `cd GA0`, then pass the path to **your** downloaded file, e.g.

```bash
uv run q04_calculate_variance.py _private/q-calculate-variance.json
```

The docstring at the top of each script shows its run command; scripts that need input files print it when run
without arguments. If `uv` is not on your PATH, use `python -m uv run ...` instead.

## Setting AIPIPE_TOKEN

Q5 and Q11 call an LLM through [AI Pipe](https://aipipe.org/). They read the token **only** from the
`AIPIPE_TOKEN` environment variable, so never paste it into code or commit it.

Windows PowerShell (current terminal session):

```powershell
$env:AIPIPE_TOKEN = "YOUR_AIPIPE_TOKEN"
```

Linux / macOS / Git Bash:

```bash
export AIPIPE_TOKEN="YOUR_AIPIPE_TOKEN"
```
