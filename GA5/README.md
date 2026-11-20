# GA5 – Tools in Data Science (Sep 2026)

My GA5 work: a RAG server and a safety router on Vercel, an Ollama/FAISS ranking script, and a ball tracker.

> This is my personal repo and it's **not affiliated with or endorsed by IIT Madras**.

- Your knowledge base, dataset, video and graded cases differ from mine, so use these to understand the
  approach and then run them on your own inputs. None of my answers are in here.
- LLMs and discussing with friends are allowed in this course, but do your own submission.

## What's in here

| Q | Folder | What it is | Submitted as |
|---|--------|------------|--------------|
| 1 | [`ga5-api/`](ga5-api/) `POST /query` | RAG over the 50-passage knowledge base: dense retrieval, grounded answer extraction, abstention | Vercel base URL |
| 2 | [`02/q2_rank.py`](02/q2_rank.py) | Two Ollama embedding models, FAISS inner-product search, top-3 from each and Spearman ρ | Pasted result |
| 3 | [`03/track_fb.py`](03/track_fb.py) | Tracks the initially-red ball through every frame and reports its centre at the asked frames | Pasted result |
| 4 | [`ga5-api/`](ga5-api/) `POST /classify` | Harness safety router: deterministic policy rules, no model calls | Vercel URL ending in `/classify` |
| 4 | [`04/`](04/) | Offline tools I used to debug Q4 against the real graded cases | Not submitted |

Q1 and Q4 share one FastAPI app, so there's a single Vercel deployment.

```text
GA5/
├── 02/q2_rank.py                 Q2  Ollama + FAISS + Spearman
├── 03/track_fb.py                Q3  forward-backward multi-ball tracker (the one I trust)
├── 03/track_ball.py              Q3  first, simpler forward-only version
├── 04/parse_vercel_log.py        Q4  pull graded cases out of a Vercel log export
├── 04/replay.py                  Q4  replay cases through rules.py and diff rule changes
└── ga5-api/
    ├── build_kb.py               Q1  embeds the knowledge base into api/kb.npy
    ├── vercel.json               60 s limit, ships passages.json + kb.npy with the function
    └── api/
        ├── index.py              /query (Q1), /classify (Q4)
        ├── rules.py              Q4 policy rules
        ├── passages.json         Q1 knowledge base (mine; replace with yours)
        └── kb.npy                Q1 passage embeddings (mine; rebuild with build_kb.py)
```

## Deploying Q1 + Q4 on Vercel

1. Put **your** knowledge base in place. Save the 50 passages from the exam page as `knowledge_base.json`
   (a JSON list of strings), set `AIPIPE_TOKEN` (see the [root README](../README.md#setting-aipipe_token)), then:

   ```bash
   cd GA5/ga5-api
   uv run --with numpy build_kb.py knowledge_base.json
   ```

   This overwrites `api/passages.json` and `api/kb.npy`. Commit both, since the function loads them at startup.
2. Vercel → **Add New → Project** → your fork, **Root Directory** `GA5/ga5-api`, framework preset FastAPI.
3. Environment variables:
   - `AIPIPE_TOKEN`: your AI Pipe token. Only Q1 uses it.
   - `LOG_KEY` (optional): any random string. It switches on `GET /debug/log?key=...`, which shows the
     recent requests that one instance saw. Leave it unset and the endpoint stays a 404.
4. Deploy, then open `https://YOUR-APP.vercel.app/` and check it returns `{"ok": true, ...}`.
5. Paste `https://YOUR-APP.vercel.app` into Q1 (no `/query`) and `https://YOUR-APP.vercel.app/classify` into Q4.

Q1 is free to re-run with **Run 20-Probe Gauntlet**. Each Q4 **Check** uses one of your 10 checks a day, and
so does every **Save**, so keep one spare for the Save.

## Running Q2 and Q3

**Q2** needs [Ollama](https://ollama.com/) running locally with both models pulled:

```bash
ollama pull nomic-embed-text
ollama pull mxbai-embed-large
uv run --with faiss-cpu --with numpy --with scipy --with requests 02/q2_rank.py your_dataset.json
```

It prints one row per query: top-3 ids from each model, then ρ.

**Q3** takes the video and the frame numbers the question asks for:

```bash
uv run --with opencv-python-headless --with numpy --with scipy 03/track_fb.py your_video.webm FRAME1 FRAME2 FRAME3
```

It prints one line per smoothing setting and a `BEST:` line, and saves `last_crop.png`, a zoom on the tracked
ball in the final frame, so you can read the number printed on it.

## How I debugged the live questions

Both graders only show a score, not which probes failed, so for a while I was guessing. What fixed that:

1. Make the endpoint `print()` one line per request. Vercel keeps those in **Logs** even after the
   instance that served them is gone. Keeping a list in memory doesn't work: the grader's requests land
   on several instances, and by the time you ask for the list they've been shut down.
2. Run the grader, then in Vercel → your project → **Logs**, search for your line prefix and use
   **Copy visible logs**. For Q4 that's 96 long lines, too much to paste into a chat, so I pasted it into a
   text file.
3. For Q4, `04/parse_vercel_log.py` turns that file into `cases.json`, and `04/replay.py` runs any rule
   change over all 96 cases offline and lists exactly which ones it moves. I only spent a Check once a
   change moved just the cases I meant it to.

```bash
cd GA5/04
uv run parse_vercel_log.py exported-logs.txt cases.json
uv run replay.py cases.json --save before.json
# edit ../ga5-api/api/rules.py
uv run replay.py cases.json --diff before.json
```

## Things that tripped me up

**Q1 – RAG**
- **Retrieval window.** One probe paraphrased its passage so heavily ("cluster coordinator" for leader,
  "subordinate replicas" for followers) that its passage ranked only **11th** by cosine. I was sending the
  model the top 5, so it never saw the answer and abstained. The same question came back in a later round
  with an injection attached, so one gap cost two probes. Sending the top 15 fixed both.
- **Abstain only for the right reasons.** It should abstain when the fact isn't in the knowledge base or
  the question states something that contradicts it (e.g. a quorum size the passage doesn't say). It
  should *not* abstain just because the system isn't named.
- **Synthesis questions** must answer with facts from *both* passages and list both in `sources`.
- **Scores must line up with sources**, be in [0, 1] and descend. I put the passages the model cited first.
- **The 8 s limit includes cold starts.** Vercel's boot happens before your handler's clock starts, so a
  7 s internal budget can still land past 8 s. I cut the budget to about 6 s, open the connection to the
  model API while the function boots, and start a backup call to a faster model if the first one stalls.
- **Plain `def` handlers, not `async def`.** The model calls are blocking, so `async` handlers made
  concurrent probes wait in line. FastAPI runs plain `def` handlers in a thread pool.
- **AI Pipe returns 403 to Python's default User-Agent** (Cloudflare), so scripts calling it from
  `urllib` send a curl one.

**Q4 – safety router**
- **Rules beat an LLM here.** My first version asked a model to label each case. It scored about two
  thirds and changed between runs. The policy is precise enough to code directly, and then it costs no
  tokens and gives the same answer every time.
- **The latest user message decides.** Revocations, explicit forbids and re-authorizations all depend on
  reading the *last* instruction. Watch for a forbid that mentions an earlier approval ("now forbidden,
  even if I approved it earlier"). Don't let the word "approved" in it count as approval.
- **"Authorize" is an approval too**, not only "approve".
- **Out of scope means review, not block.** An approval for staging when the tool resolves to production,
  or for one namespace when it resolves to another, is *missing* authorization. That holds even when
  the approval says "only". Block is for things the user actually forbade or revoked.
- **Defensive analysis routes to primary.** Malware-report analysis and translating a threat message are
  allowed on the primary route. `restricted` is for vulnerability or exploit work and unclear security
  scope. One wrong guess here *lowered* my score while more tuples were correct, because three false
  `restricted` labels wrecked that class's macro-F1.
- **Read the score, not just the tuple count.** Tuples are only 20% of the grade. The other 80% is
  macro-F1 per axis, so a small class (like `restricted`) matters far more per case than a big one.

**Q3 – ball tracking**
- Hough circles missed balls that touch. Peaks of the distance transform separate them better.
- Near the end, numbers appear on the balls and punch holes in the mask. Fill only small holes. Filling
  the whole background also fills the arena between balls.
- Match all balls at once (Hungarian assignment), not greedily one by one, or neighbours swap.
- Track forward from the red ball, then backward from where it ends. Only trust the answer if the backward
  track lands back on the red ball in frame 0.

**Q2 – embeddings**
- L2-normalise before an inner-product index, so the scores are cosine similarities.
- Spearman ρ is over all 50 document scores per query, not just the top 3.
