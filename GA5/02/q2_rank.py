"""GA5 Q2: top-3 from nomic-embed-text and mxbai-embed-large (FAISS IP) + Spearman rho over all 50 docs.

Run: uv run --with faiss-cpu --with numpy --with scipy --with requests q2_rank.py dataset.json   (Ollama running)
"""
import json, sys
import numpy as np, faiss, requests
from scipy.stats import spearmanr

data = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "dataset.json", encoding="utf-8"))


def emb(model, texts):
    a = np.array([requests.post("http://localhost:11434/api/embeddings",
                                json={"model": model, "prompt": t}).json()["embedding"] for t in texts], dtype=np.float32)
    faiss.normalize_L2(a)
    return a


ea, eb = emb("nomic-embed-text", data["sentences"]), emb("mxbai-embed-large", data["sentences"])
qa, qb = emb("nomic-embed-text", data["queries"]), emb("mxbai-embed-large", data["queries"])
ia, ib = faiss.IndexFlatIP(ea.shape[1]), faiss.IndexFlatIP(eb.shape[1])
ia.add(ea)
ib.add(eb)
rows = []
for q in range(len(data["queries"])):
    Da, Ia = ia.search(qa[q:q + 1], 50)
    Db, Ib = ib.search(qb[q:q + 1], 50)
    sa, sb = np.zeros(50), np.zeros(50)
    sa[Ia[0]], sb[Ib[0]] = Da[0], Db[0]
    rows.append(Ia[0][:3].tolist() + Ib[0][:3].tolist() + [round(float(spearmanr(sa, sb)[0]), 4)])
print(json.dumps(rows))
