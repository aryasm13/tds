# /// script
# requires-python = ">=3.11"
# dependencies = ["fastapi", "uvicorn", "httpx"]
# ///
import os, json, re
from typing import List
import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

TOKEN = os.environ.get("AIPIPE_TOKEN", "")

HAPPY = {"love","great","awesome","amazing","excellent","wonderful","happy","good",
         "fantastic","perfect","best","enjoy","enjoyed","delighted","thrilled",
         "beautiful","glad","excited","brilliant","superb","pleased","joy","win"}
SAD   = {"hate","terrible","awful","horrible","bad","worst","sad","disappointed",
         "disappointing","angry","upset","miserable","cry","crying","broken","fail",
         "failed","depressed","unhappy","frustrated","pain","sucks","annoyed","lost"}


class Batch(BaseModel):
    sentences: List[str]


def rule(s: str) -> str:
    w = set(re.findall(r"[a-z']+", s.lower()))
    h, d = len(w & HAPPY), len(w & SAD)
    neg = bool(w & {"not", "no", "never", "n't", "don't", "didn't", "isn't"})
    if neg:
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
    r.raise_for_status()
    out = json.loads(r.json()["choices"][0]["message"]["content"])["sentiments"]
    if len(out) != len(sentences):
        raise ValueError("length mismatch")
    return [x if x in ("happy", "sad", "neutral") else "neutral" for x in out]


@app.post("/sentiment")
def sentiment(batch: Batch):
    try:
        labels = ask_llm(batch.sentences)
    except Exception:
        labels = [rule(s) for s in batch.sentences]
    return {"results": [{"sentence": s, "sentiment": l}
                        for s, l in zip(batch.sentences, labels)]}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)