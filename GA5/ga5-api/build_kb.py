"""GA5 Q1: build the knowledge-base files the /query endpoint loads.

Takes the 50-passage knowledge base from the exam page (a JSON list of strings, or of objects with a
"text" field) and writes, next to api/index.py:
    passages.json  the passage texts, in order (index = passage id in the answers)
    kb.npy         their text-embedding-3-small vectors, L2-normalised, float32, shape (50, 1536)

Embedding once here means each probe only embeds its question, which keeps answers well inside 8 s.

    uv run --with numpy build_kb.py knowledge_base.json            # writes into api/
    uv run --with numpy build_kb.py knowledge_base.json --out tmp  # writes somewhere else

Needs AIPIPE_TOKEN in the environment. 50 passages cost a tiny fraction of a cent.
"""
import argparse
import json
import os
import sys
import urllib.request
from pathlib import Path

import numpy as np

BASE = os.environ.get("AI_BASE_URL", "https://aipipe.org/openai/v1").rstrip("/")


def embed(texts, token):
    req = urllib.request.Request(
        BASE + "/embeddings",
        json.dumps({"model": "text-embedding-3-small", "input": texts}).encode(),
        # AI Pipe sits behind Cloudflare, which rejects Python's default User-Agent with a 403
        {"Content-Type": "application/json", "Authorization": f"Bearer {token}", "User-Agent": "curl/8.4.0"})
    with urllib.request.urlopen(req, timeout=120) as r:
        data = sorted(json.load(r)["data"], key=lambda d: d["index"])
    v = np.array([d["embedding"] for d in data], dtype=np.float32)
    return v / np.linalg.norm(v, axis=1, keepdims=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("knowledge_base")
    ap.add_argument("--out", default=str(Path(__file__).resolve().parent / "api"))
    a = ap.parse_args()

    token = os.environ.get("AIPIPE_TOKEN")
    if not token:
        sys.exit("Set AIPIPE_TOKEN first (see the README).")
    raw = json.loads(Path(a.knowledge_base).read_text(encoding="utf-8"))
    passages = [p["text"] if isinstance(p, dict) else str(p) for p in raw]

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "passages.json").write_text(json.dumps(passages, ensure_ascii=False, indent=1), encoding="utf-8")
    np.save(out / "kb.npy", embed(passages, token))
    print(f"{len(passages)} passages -> {out / 'passages.json'} and {out / 'kb.npy'}")


if __name__ == "__main__":
    main()
