import json, os, re

import httpx
import pandas as pd
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

LEDGER_URL = os.environ.get("LEDGER_URL")      # your q-ledger-agent-server URL, without &path=...
AIPIPE_TOKEN = os.environ.get("AIPIPE_TOKEN")
MODEL = os.environ.get("LEDGER_MODEL", "gpt-4.1")
UA = {"User-Agent": "curl/8.5.0"}               # the API blocks Python's default user agent

_df = None


def load() -> pd.DataFrame:
    """Fetch the full export once, keep the latest row per order, add USD and IST date columns."""
    global _df
    if _df is None:
        rates = httpx.get(LEDGER_URL + "&path=%2Frates", headers=UA, timeout=20).json()["usd_per_unit"]
        text = httpx.get(LEDGER_URL + "&path=%2Fexport", headers=UA, timeout=20).text
        df = pd.DataFrame([json.loads(line) for line in text.splitlines() if line.strip()])
        for col in ("created_at", "updated_at"):
            df[col] = pd.to_datetime(df[col], utc=True, format="ISO8601")   # mixes Z and +05:30
        df = df.sort_values("updated_at").drop_duplicates("id", keep="last")
        df["amount_usd"] = df["amount"] * df["currency"].map(rates)
        ist = df["created_at"].dt.tz_convert("Asia/Kolkata")
        df["date"] = ist.dt.strftime("%Y-%m-%d")
        df["month"] = ist.dt.strftime("%Y-%m")
        _df = df.reset_index(drop=True)
    return _df


def prompt(df: pd.DataFrame) -> str:
    return f"""You answer questions about an order ledger by writing pandas code.
A DataFrame `df` is loaded with one row per order (duplicates already removed). Columns:
- id, customer, region {sorted(df.region.unique())}, product {sorted(df["product"].unique())}
- qty (int), unit_price, amount (original currency), currency, amount_usd (amount in USD)
- status: 'paid', 'refunded' or 'void'
- date ('YYYY-MM-DD') and month ('YYYY-MM'): the order's business date in Asia/Kolkata. Data covers {df.month.min()} to {df.month.max()}.
Rules:
- Revenue = sum of amount_usd where status == 'paid'. Refunds = rows where status == 'refunded'. Void never counts.
- Average order value = mean amount_usd of the matching orders (paid ones unless the question says otherwise).
- Filter time with `month` or `date` only. Use the exact region/product spellings above.
- Money: round(x, 2). Counts: int. Names: the exact string from the data.
Write Python that sets a variable `answer` to one number or string. Reply with only the code, no markdown."""


def ask_llm(df: pd.DataFrame, question: str, error: str = "") -> str:
    messages = [{"role": "system", "content": prompt(df)}, {"role": "user", "content": question}]
    if error:
        messages.append({"role": "user", "content": f"Your previous code failed with: {error}. Fix it."})
    r = httpx.post(
        "https://aipipe.org/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {AIPIPE_TOKEN}"},
        json={"model": MODEL, "messages": messages, "temperature": 0},
        timeout=12,
    )
    r.raise_for_status()
    code = r.json()["choices"][0]["message"]["content"]
    return re.sub(r"^```(?:python)?\s*|\s*```$", "", code.strip())


def run(df: pd.DataFrame, code: str):
    env = {"df": df, "pd": pd}
    exec(code, env)
    ans = env["answer"]
    ans = ans.item() if hasattr(ans, "item") else ans          # numpy -> plain Python
    return round(ans, 2) if isinstance(ans, float) else ans


@app.get("/")
def health():
    return {"ok": True, "orders": len(load())}


@app.post("/")
@app.post("/answer")
async def answer(request: Request):
    question = (await request.json()).get("question", "")
    df = load()
    error = ""
    for _ in range(2):                                          # one retry if the code crashes
        try:
            return {"answer": run(df, ask_llm(df, question, error))}
        except Exception as e:
            error = repr(e)
    return {"answer": None, "error": error}
