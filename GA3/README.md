# GA3 – Tools in Data Science (Sep 2026)

My GA3 work: two AI agent servers on Render, plus the face GLB, morph video and ranking.

> This is my personal repo and it's **not affiliated with or endorsed by IIT Madras**.

- Your photos, pairs and assigned values differ from mine, so use these to understand the approach and then
  build your own.
- LLMs and discussing with friends are allowed in this course, but do your own submission.

## What's in here

| Q | Folder | What it is | Deployed? |
|---|--------|------------|-----------|
| 2 | [`01/ga3_invoice_agent/ga3_invoice_agent/`](01/ga3_invoice_agent/ga3_invoice_agent/) | A2A invoice agent: Agent Card, `message:send`, task list / get / cancel, PostgreSQL state | **Render** (Docker), submitted as `https://YOUR-HOST/a2a/` |
| 4 | [`04/`](04/) | Incident triage agent: `POST /v2/incidents`, receipts, `GET` state and OTLP traces | **Render** (Docker), submitted as the base URL |
| 6 | [`06/make_glb.py`](06/make_glb.py) → `zapata_face.glb` | Textured 3D face relief built from the assigned photo | Raw GitHub URL of the `.glb` |
| 7 | [`07/make_morph.py`](07/make_morph.py) → `morph.mp4` | Landmark face morph (Delaunay warp + cross-dissolve), kept under 95 KB | Raw GitHub URL of the `.mp4` |
| 8 | [`08/ranking.pdf`](08/ranking.pdf) | My ranking of which face pairs are easiest to morph | Uploaded on the exam page |

The other GA3 questions I did directly on the exam page.

## Deploying the two agents on Render

1. Render → **New → PostgreSQL** (Free). Both agents can share one database.
2. Render → **New → Web Service** → your fork, Language **Docker**, Free instance, and set **Root Directory**:
   - Q2: `GA3/01/ga3_invoice_agent/ga3_invoice_agent`
   - Q4: `GA3/04`
3. Environment variables for both:
   - `DATABASE_URL`: the database's **Internal Database URL**
   - `AI_API_KEY`: your AI Pipe token
   - `AI_BASE_URL`: `https://aipipe.org/openai/v1`
   - `AI_MODEL`: `gpt-4o-mini` (fast enough for the time limits)
4. Open `https://YOUR-HOST/healthz` before clicking **Check**. Free instances sleep, and the first request
   after that can take about a minute.

## Running the media scripts

```bash
uv run --with numpy --with pillow 06/make_glb.py your_photo.jpg zapata_face.glb
uv run --with numpy --with opencv-python --with scipy 07/make_morph.py faceA.jpg faceB.jpg morph.mp4
```

`make_morph.py` needs `ffmpeg` on your PATH. Both scripts have **my** crop box and hand-placed landmarks
hard-coded, so you'll need to re-pick them for your photos.

## Things that tripped me up

- **Q2:** only requests with a body need the `application/a2a+json` Content-Type. The model sometimes skipped
  packages or cited refs that weren't in them, so the agent re-asks once and checks every ref against the
  package text.
- **Q4:** the receipts, replays and trace building must never call the model, only planning does. Keeping
  the state machine separate from the LLM call made this much easier.
- **Q6:** validate the `.glb` in the [glTF validator](https://github.khronos.org/glTF-Validator/) before
  submitting.
- **Q7:** the size limit is strict. The script retries with higher CRF until the file fits.
