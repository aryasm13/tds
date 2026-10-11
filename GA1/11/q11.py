# /// script
# dependencies = ["numpy"]
# ///
"""Q11 Cosine similarity: top-5 documents per query, ties broken by smaller doc id.

Run: uv run q11.py path/to/q-cosine-similarity-server.json   (or: python -m uv run ...)
"""
import json, sys
import numpy as np

if len(sys.argv) < 2:
    sys.exit(__doc__)
data = json.load(open(sys.argv[1]))
docs, queries = data["documents"], data["queries"]

ids = [d["doc_id"] for d in docs]
D = np.array([d["embedding"] for d in docs], dtype=float)
D /= np.linalg.norm(D, axis=1, keepdims=True)        # safe even if already normalised

out = {}
for q in queries:
    v = np.array(q["embedding"], dtype=float)
    v /= np.linalg.norm(v)
    sims = np.round(D @ v, 12)                        # tiny float noise shouldn't break ties
    order = sorted(range(len(ids)), key=lambda i: (-sims[i], ids[i]))
    out[q["query_id"]] = [ids[i] for i in order[:5]]

print(json.dumps(out))
