# GA1 – Tools in Data Science (Sep 2026)

Hi again! These are my GA1 scripts and servers. As with GA0, they're here to help you get unstuck, not to copy.

> This is my personal repo and it's **not affiliated with or endorsed by IIT Madras**.

- Your data and variants differ from mine, so there are no answers here. Run everything on your own files.
- LLMs and discussing with friends are allowed in this course, but do your own submission.
- Some folders still hold the input files the question gave me (`04/`, `08/`, `11/`, `broken_json/`). They're
  only there so the scripts make sense; download your own.

## What's in here

| Q | Folder / file | What it is | Deployed? |
|---|---------------|------------|-----------|
| 6 | [`config-service/`](config-service/) | 12-factor config precedence: `GET /effective-config` merges defaults → `config.development.yaml` → `.env` → env vars → `?set=` overrides | **Vercel**, Root Directory `GA1/config-service` |
| 7 | [`07/reorganize.sh`](07/reorganize.sh) | Moves every `.txt` into its `category:` folder, then prints the hash | No, run in Git Bash / WSL |
| 8 | [`08/sales_data/`](08/sales_data/) | The question's CSV (I did the analysis in the terminal) | No |
| 10 | [`10/history.fastimport`](10/history.fastimport) | The repo history to search for the leaked token | No |
| 11 | [`11/q11.py`](11/q11.py) | Cosine similarity: top 5 documents per query | No, `uv run q11.py q-cosine-similarity-server.json` |
| 13 | [`13/submission.tar.gz`](13/submission.tar.gz) | My termlog recording of decoding the file in the terminal | Served from this repo's raw GitHub URL |
| 15 | [`leader-agent/`](leader-agent/) | Ledger agent: `POST /answer` takes a question, an LLM writes pandas code, the server runs it | **Vercel**, Root Directory `GA1/leader-agent` |

The other questions I did directly on the exam page.

## Deploying the two Vercel apps

1. Vercel → **Add New → Project** → import your fork.
2. Set **Root Directory** to the folder from the table (`GA1/config-service` or `GA1/leader-agent`).
3. Add the environment variables, then **Deploy**:
   - `config-service`: whatever env var the question asks you to set (mine was `APP_LOG_LEVEL`).
   - `leader-agent`: `LEDGER_URL` (your question's server URL, without `&path=...`) and `AIPIPE_TOKEN`.
4. Paste `https://YOUR-APP.vercel.app/effective-config` (Q6) or `https://YOUR-APP.vercel.app/answer` (Q15)
   into the exam page.

## Things that tripped me up

- **Q6:** Vercel only ships `.env` and the YAML if they're listed under `includeFiles` in `vercel.json`. The
  root `.gitignore` ignores `.env`, so I added `!GA1/config-service/.env` to commit this one (it has no
  secrets). Put your own values in it.
- **Q7:** run the script **once** on a freshly extracted folder. Running it twice moves already-moved files
  and changes the hash.
- **Q10:** `git init` an empty repo, run `git fast-import < history.fastimport`, then `git log -p -S <text>`
  across all branches finds the commit that added the token.
- **Q11:** the output keys are `doc_id` / `query_id`, and ties go to the smaller doc id.
- **Q13:** I used termlog in WSL Ubuntu. The Google login callback timed out twice before it worked, so just
  retry. Record with `--headless` and run `termlog verify` before uploading.
- **Q15:** Cloudflare blocks Python's default user agent (403), so the server sends a curl one. The export
  mixes `Z` and `+05:30` timestamps, repeats orders (keep the latest `updated_at`), and months are in IST.
