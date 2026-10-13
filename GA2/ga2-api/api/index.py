"""GA2 live-server questions in one FastAPI app (deployed on Vercel).

Q3  GET  /stats                 strict per-origin CORS, X-Request-ID, X-Process-Time
Q7  POST /analytics             X-API-Key auth + event aggregation
Q9  POST /v1/chat/completions   OpenAI-compatible chat, answered by a real LLM via AI Pipe
Q11 POST /orders, GET /orders   idempotent create, cursor pagination, per-client rate limit
"""
import base64, hashlib, math, os, time, uuid
from collections import defaultdict, deque

import httpx
from fastapi import FastAPI, Header, Query, Request
from fastapi.responses import JSONResponse, Response

# ---- assigned values (from the GA2 question page) ----
EMAIL = "23f3002123@ds.study.iitm.ac.in"
STATS_ORIGIN = "https://dash-n4jyst.example.com"   # Q3: the only origin allowed on /stats
API_KEY = "ak_7ipo6sfmf4g6j4icgr43fvn9"            # Q7
TOTAL_ORDERS = 48                                  # Q11: catalog is ids 1..T
RATE_LIMIT, WINDOW = 19, 10.0                      # Q11: R requests per 10 s, per client
CHAT_MODEL = "gpt-4.1-nano"                        # Q9: model behind /v1/chat/completions
AIPIPE_TOKEN = os.environ.get("AIPIPE_TOKEN")      # set in Vercel, never in code

app = FastAPI()


# ---- CORS + request context, for every response ----
@app.middleware("http")
async def cors_and_context(request: Request, call_next):
    start = time.perf_counter()
    origin = request.headers.get("origin")
    strict = request.url.path.startswith("/stats")          # Q3 policy; everything else is open
    allowed = (origin == STATS_ORIGIN) if strict else True

    if request.method == "OPTIONS" and "access-control-request-method" in request.headers:
        if not allowed:
            resp = Response(status_code=400)                 # rejected preflight: no ACAO header
        else:
            resp = Response(status_code=204)
            resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
            resp.headers["Access-Control-Allow-Headers"] = request.headers.get(
                "access-control-request-headers", "*")
            resp.headers["Access-Control-Max-Age"] = "600"
    else:
        resp = await call_next(request)

    if allowed and (origin or not strict):
        resp.headers["Access-Control-Allow-Origin"] = origin if strict else "*"
        resp.headers["Access-Control-Expose-Headers"] = "X-Request-ID, X-Process-Time, Retry-After"
    if strict:
        resp.headers["Vary"] = "Origin"
    resp.headers["X-Request-ID"] = str(uuid.uuid4())
    resp.headers["X-Process-Time"] = f"{time.perf_counter() - start:.6f}"
    return resp


@app.get("/")
def health():
    return {"ok": True, "routes": ["/stats", "/analytics", "/v1/chat/completions", "/orders"]}


# ---- Q3: descriptive statistics ----
@app.get("/stats")
def stats(values: str = Query(...)):
    try:
        nums = [int(v) for v in values.split(",") if v.strip()]
    except ValueError:
        return JSONResponse({"detail": "values must be comma-separated integers"}, status_code=400)
    if not nums:
        return JSONResponse({"detail": "no values given"}, status_code=400)
    return {"email": EMAIL, "count": len(nums), "sum": sum(nums), "min": min(nums),
            "max": max(nums), "mean": sum(nums) / len(nums)}


# ---- Q7: authenticated analytics ----
@app.post("/analytics")
async def analytics(request: Request, x_api_key: str | None = Header(None)):
    if x_api_key != API_KEY:
        return JSONResponse({"detail": "invalid or missing API key"}, status_code=401)
    events = (await request.json()).get("events", [])
    per_user = defaultdict(float)
    for e in events:
        amount = float(e.get("amount") or 0)
        if amount > 0:                                       # zero and negative amounts are ignored
            per_user[e.get("user")] += amount
    return {"email": EMAIL, "total_events": len(events),
            "unique_users": len({e.get("user") for e in events}),
            "revenue": round(sum(per_user.values()), 2),
            "top_user": max(per_user, key=per_user.get) if per_user else None}


# ---- Q9: OpenAI-compatible chat completions ----
@app.post("/v1/chat/completions")
async def chat(request: Request):
    body = await request.json()
    async with httpx.AsyncClient(timeout=25) as client:
        r = await client.post(
            "https://aipipe.org/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {AIPIPE_TOKEN}"},
            json={"model": CHAT_MODEL, "messages": body.get("messages", []), "temperature": 0},
        )
    return JSONResponse(r.json(), status_code=r.status_code)


# ---- Q11: idempotency, pagination, rate limiting ----
HITS: dict[str, deque] = defaultdict(deque)
CREATED: dict[str, dict] = {}


def rate_limited(client_id: str | None) -> int | None:
    """Sliding window per X-Client-Id. Returns seconds to wait, or None if allowed."""
    if not client_id:
        return None
    now, hits = time.monotonic(), HITS[client_id]
    while hits and now - hits[0] >= WINDOW:
        hits.popleft()
    if len(hits) >= RATE_LIMIT:
        return max(1, math.ceil(WINDOW - (now - hits[0])))
    hits.append(now)
    return None


def too_many(wait: int) -> JSONResponse:
    return JSONResponse({"detail": "rate limit exceeded"}, status_code=429, headers={"Retry-After": str(wait)})


@app.post("/orders", status_code=201)
async def create_order(request: Request, idempotency_key: str | None = Header(None),
                       x_client_id: str | None = Header(None)):
    if (wait := rate_limited(x_client_id)) is not None:
        return too_many(wait)
    if idempotency_key in CREATED:
        return JSONResponse(CREATED[idempotency_key], status_code=200)
    try:
        body = await request.json()
    except Exception:
        body = {}
    key = idempotency_key or str(uuid.uuid4())
    # id derived from the key, so a retry gets the same id even on another server instance
    order = {**(body if isinstance(body, dict) else {}),
             "id": "ord_" + hashlib.sha256(key.encode()).hexdigest()[:16], "status": "created"}
    if idempotency_key:
        CREATED[idempotency_key] = order
    return order


def encode_cursor(next_id: int) -> str:
    return base64.urlsafe_b64encode(f"id:{next_id}".encode()).decode()


def decode_cursor(cursor: str) -> int:
    return int(base64.urlsafe_b64decode(cursor.encode()).decode().split(":")[1])


@app.get("/orders")
def list_orders(limit: int = 10, cursor: str | None = None, x_client_id: str | None = Header(None)):
    if (wait := rate_limited(x_client_id)) is not None:
        return too_many(wait)
    try:
        start = decode_cursor(cursor) if cursor else 1
    except Exception:
        return JSONResponse({"detail": "invalid cursor"}, status_code=400)
    ids = range(start, min(start + max(limit, 1), TOTAL_ORDERS + 1))
    items = [{"id": i, "item": f"Order {i}", "amount": round(10 + i * 2.5, 2)} for i in ids]
    has_more = bool(ids) and ids[-1] < TOTAL_ORDERS
    return {"items": items, "next_cursor": encode_cursor(ids[-1] + 1) if has_more else None}
