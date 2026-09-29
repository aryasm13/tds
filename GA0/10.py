# /// script
# requires-python = ">=3.11"
# dependencies = ["fastapi", "uvicorn"]
# ///
import csv
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# find the csv next to this script, whatever it is called
CSV = Path(__file__).parent / "q-fastapi.csv"
with CSV.open(newline="", encoding="utf-8-sig") as f:
    STUDENTS = [
        {"studentId": int(r["studentId"]), "class": r["class"].strip()}
        for r in csv.DictReader(f)
    ]


@app.get("/api")
def api(class_: Optional[List[str]] = Query(default=None, alias="class")):
    if not class_:
        return {"students": STUDENTS}
    wanted = set(class_)
    return {"students": [s for s in STUDENTS if s["class"] in wanted]}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)