# /// script
# requires-python = ">=3.11"
# dependencies = ["fastapi", "uvicorn", "httpx", "pydantic"]
# ///
import os
import re
import sys
import json
import traceback
from io import StringIO
from typing import List

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

AIPIPE_TOKEN = os.environ.get("AIPIPE_TOKEN", "eyJhbGciOiJIUzI1NiJ9.eyJlbWFpbCI6IjIzZjMwMDIxMjNAZHMuc3R1ZHkuaWl0bS5hYy5pbiIsImlhdCI6MTc5MDcxMTY5NCwiaXNzIjoiaHR0cHM6Ly9haXBpcGUub3JnIiwiYXVkIjoiYWlwaXBlLWFwaSIsImV4cCI6MTc5MTMxNjQ5NH0.BIIam8M1Qg5HUVQ01DxJDJgAeTQoi6jRxNM9WQpf6bo")


class CodeRequest(BaseModel):
    code: str


class ErrorAnalysis(BaseModel):
    error_lines: List[int]


# ---------- Part 1: tool that runs the code ----------
def execute_python_code(code: str) -> dict:
    old_stdout = sys.stdout
    sys.stdout = StringIO()
    try:
        exec(code, {})
        return {"success": True, "output": sys.stdout.getvalue()}
    except Exception:
        return {"success": False, "output": traceback.format_exc()}
    finally:
        sys.stdout = old_stdout


# ---------- Backup: read line numbers straight from the traceback ----------
def lines_from_traceback(tb: str) -> List[int]:
    nums = re.findall(r'File "<string>", line (\d+)', tb)
    return [int(nums[-1])] if nums else []


# ---------- Part 2: AI analysis (only called on error) ----------
def analyze_error_with_ai(code: str, tb: str) -> List[int]:
    prompt = (
        "Analyze this Python code and its error traceback. "
        "Identify the line number(s) in the CODE where the error occurred.\n\n"
        f"CODE:\n{code}\n\nTRACEBACK:\n{tb}"
    )
    resp = httpx.post(
        "https://aipipe.org/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {AIPIPE_TOKEN}"},
        json={
            "model": "gpt-4.1-nano",
            "messages": [{"role": "user", "content": prompt}],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "error_analysis",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "properties": {
                            "error_lines": {"type": "array", "items": {"type": "integer"}}
                        },
                        "required": ["error_lines"],
                        "additionalProperties": False,
                    },
                },
            },
        },
        timeout=30,
    )
    resp.raise_for_status()
    content = resp.json()["choices"][0]["message"]["content"]
    return ErrorAnalysis.model_validate_json(content).error_lines


@app.post("/code-interpreter")
def code_interpreter(req: CodeRequest):
    result = execute_python_code(req.code)
    if result["success"]:
        return {"error": [], "result": result["output"]}

    try:
        lines = analyze_error_with_ai(req.code, result["output"])
    except Exception:
        lines = []
    if not lines:  # AI failed or returned nothing -> use traceback
        lines = lines_from_traceback(result["output"])
    return {"error": lines, "result": result["output"]}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
