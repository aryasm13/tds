# /// script
# requires-python = ">=3.11"
# dependencies = ["fastapi", "uvicorn", "httpx"]
# ///
"""Q11 Batch sentiment: FastAPI POST /sentiment labels each sentence happy/sad/neutral via an LLM, with a keyword fallback.

Run: uv run q11_sentiment_api.py   (reads AIPIPE_TOKEN; serves http://127.0.0.1:8002/sentiment)
"""
import os, json, re
from typing import List
import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

TOKEN = os.environ.get("AIPIPE_TOKEN")  # set it in your shell, never in code (see README)

HAPPY = ["love", "great", "awesome", "amazing", "excellent", "wonderful", "happy",
         "good", "fantastic", "perfect", "best", "enjoy", "delight", "thrill",
         "beautiful", "glad", "excit", "brilliant", "superb", "pleas", "joy",
         "win", "won", "celebrat", "smile", "laugh", "fun", "grateful", "thank",
         "proud", "nice", "cool", "yay", "blessed", "lucky", "incredible",
         "outstanding", "adore", "like", "cheer", "success", "promot", "ecstatic"]
SAD = ["hate", "terrible", "awful", "horrible", "bad", "worst", "sad",
       "disappoint", "angry", "upset", "miserable", "cry", "broke", "fail",
       "depress", "unhappy", "frustrat", "pain", "suck", "annoy", "lost", "lose",
       "lonely", "alone", "hurt", "sorry", "regret", "tear", "grief", "griev",
       "died", "death", "heartbr", "sick", "tired", "poor", "unfortunat",
       "devastat", "gloomy", "down", "stress", "anxious", "worr", "fired",
       "miss", "reject", "ruin", "wors", "boring", "dread", "awful", "gloom"]
NEG = {"not", "no", "never", "don't", "didn't", "isn't", "wasn't", "can't",
       "won't", "doesn't", "aren't", "nothing", "hardly"}


class Batch(BaseModel):
    sentences: List[str]


def rule(s: str) -> str:
    words = re.findall(r"[a-z']+", s.lower())
    h = sum(1 for w in words for k in HAPPY if w.startswith(k))
    d = sum(1 for w in words for k in SAD if w.startswith(k))
    if any(w in NEG for w in words):
        h, d = d, h
    if h > d:
        return "happy"
    if d > h:
        return "sad"
    return "neutral"


def ask_llm(sentences: List[str]) -> List[str]:
    prompt = (
        "Classify each sentence as exactly one of: happy, sad, neutral.\n"
        "happy = positive emotion. sad = negative emotion. "
        "neutral = factual or no clear emotion.\n"
        'Return ONLY JSON: {"sentiments": ["happy", ...]} with one entry per '
        "sentence, in the same order.\n\nSentences:\n"
        + "\n".join(f"{i+1}. {s}" for i, s in enumerate(sentences))
    )
    r = httpx.post(
        "https://aipipe.org/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {TOKEN}"},
        json={"model": "gpt-4.1-nano", "temperature": 0,
              "messages": [{"role": "user", "content": prompt}],
              "response_format": {"type": "json_object"}},
        timeout=40,
    )
    if r.status_code != 200:
        raise RuntimeError(f"AI Pipe HTTP {r.status_code}: {r.text[:300]}")
    out = json.loads(r.json()["choices"][0]["message"]["content"])["sentiments"]
    if len(out) != len(sentences):
        raise ValueError(f"length mismatch {len(out)} vs {len(sentences)}")
    return [x.lower() if x.lower() in ("happy", "sad", "neutral") else "neutral" for x in out]


@app.post("/sentiment")
def sentiment(batch: Batch):
    try:
        labels = ask_llm(batch.sentences)
        print("LLM OK:", labels)
    except Exception as e:
        print("LLM FAILED ->", repr(e))
        labels = [rule(s) for s in batch.sentences]
        print("fallback:", labels)
    return {"results": [{"sentence": s, "sentiment": l}
                        for s, l in zip(batch.sentences, labels)]}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)