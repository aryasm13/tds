import json, math
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Access-Control-Allow-Origin", "*"],
)

ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = next(p for p in ROOT.glob("*.json") if p.name != "vercel.json")
RECORDS = json.loads(DATA_FILE.read_text())


def p95(values):
    v = sorted(values)
    k = (len(v) - 1) * 0.95
    lo, hi = math.floor(k), math.ceil(k)
    return v[lo] if lo == hi else v[lo] + (v[hi] - v[lo]) * (k - lo)


@app.post("/api/latency")
@app.post("/")
async def latency(req: Request):
    body = await req.json()
    regions = body.get("regions", [])
    threshold = body.get("threshold_ms", 180)
    out = {}
    for r in regions:
        rows = [x for x in RECORDS if x["region"] == r]
        if not rows:
            continue
        lat = [x["latency_ms"] for x in rows]
        up = [x["uptime_pct"] for x in rows]
        out[r] = {
            "avg_latency": round(sum(lat) / len(lat), 2),
            "p95_latency": round(p95(lat), 2),
            "avg_uptime": round(sum(up) / len(up), 3),
            "breaches": sum(1 for x in lat if x > threshold),
        }
    return {"regions": out}