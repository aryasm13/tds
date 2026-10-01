# GA0 – Tools in Data Science (Sep 2026)

Hey! I'm Arya, and I'm doing TDS this term just like you. These are the scripts I wrote for GA0. I'm putting
them up in case they help you get unstuck. They're here so you can understand the questions, not copy them.

> Just so it's clear: this is my personal repo and it's **not affiliated with or endorsed by IIT Madras**.
> I'm just a student trying to help out.

A couple of things:

- Your data and variants are different from mine, so there are no answers here. You'll need to run things on
  your own files anyway.
- Please give each question a real try first. Use this only when you're stuck, figure out why it works, and
  then write your own version. That's how GA0 actually helps you later.
- LLMs and discussing with friends are allowed in this course, but do your own submission.

## Setup

- Install [uv](https://docs.astral.sh/uv/). If `uv` isn't found, `python -m uv run ...` works too.
- I keep my downloads in `GA0/_private/`. That folder is git-ignored, so nothing personal gets pushed.
- Run things from inside `GA0/`. If you run a script without arguments, it tells you what it needs.
- For Q5 and Q11, set your AI Pipe token as an environment variable (steps are in the main
  [README](../README.md)). Please don't paste it into code.
- On Windows, I ran the `sha256sum` commands in Git Bash.

## What's in here

| Q | File | How I ran it |
|---|------|--------------|
| 4 | [`q04_calculate_variance.py`](q04_calculate_variance.py) | `uv run q04_calculate_variance.py _private/q-calculate-variance.json` |
| 5 | [`q05_code_interpreter.py`](q05_code_interpreter.py) | `uv run q05_code_interpreter.py` |
| 7 | [`q07_crawl_html.py`](q07_crawl_html.py) | `uv run q07_crawl_html.py B N` (your letters) |
| 10 | [`q10_students_api.py`](q10_students_api.py) | `uv run q10_students_api.py _private/q-fastapi.csv` |
| 11 | [`q11_sentiment_api.py`](q11_sentiment_api.py) | `uv run q11_sentiment_api.py` |
| 14 | [`q14_jigsaw_grayscale.py`](q14_jigsaw_grayscale.py) | `uv run q14_jigsaw_grayscale.py _private/jigsaw.webp _private/mapping.txt` |
| 16 | [`q16_move_rename_files.py`](q16_move_rename_files.py) | `uv run q16_move_rename_files.py _private/q-move-rename-files.zip` |
| 18 | [`q18_ngrok_policy.yml`](q18_ngrok_policy.yml) | `uvx ngrok http 11434 --traffic-policy-file q18_ngrok_policy.yml` |
| 19 | [`q19_replace_across_files.py`](q19_replace_across_files.py) | `uv run q19_replace_across_files.py _private/q-replace-across-files.zip` |
| 22 | [`q22_unicode_data.py`](q22_unicode_data.py) | `uv run q22_unicode_data.py _private/q-unicode-data.zip` |
| 25 | [`tds-latency/`](tds-latency/) | Deployed on Vercel with this folder as the Root Directory |

Q13 and Q24 are in the repo root ([`.github/workflows/test.yml`](../.github/workflows/test.yml) and
[`email.json`](../email.json)). I did the rest directly on the exam page.

## Things that tripped me up

- **Q4:** it wants the *sample* variance (N-1), not the population one.
- **Q14:** the mapping is scrambled → original, and the rounding has to match JavaScript's `Math.round`.
  For `mapping.txt`, just paste the table from your question.
- **Q16 / Q19:** line endings and sort order change the hash, so run the commands exactly as the question
  says.
- **Q18:** put your own email in the YAML first.
- **Q22:** open the script and fill in `SYMBOLS` with the symbols from your question.

That's it! If something doesn't work or you find a bug, just open an issue or ping me. All the best for GA0 🙂
