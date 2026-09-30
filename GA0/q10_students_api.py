# /// script
# requires-python = ">=3.11"
# dependencies = ["fastapi", "uvicorn"]
# ///
"""Q10 FastAPI server: GET /api returns the students in q-fastapi.csv, optionally filtered by one or more ?class= values.

Run: uv run q10_students_api.py path/to/q-fastapi.csv   (serves http://127.0.0.1:8001/api)
"""
import csv
import sys
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

# the csv path comes from the command line
if len(sys.argv) < 2:
    sys.exit(__doc__)
CSV = Path(sys.argv[1])
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
    uvicorn.run(app, host="0.0.0.0", port=8001)
