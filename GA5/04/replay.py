"""GA5 Q4: replay graded cases through rules.py offline and diff against an earlier run.

Each Check costs one of 10 daily attempts, so test rule changes here first:

    uv run replay.py cases.json                       # label counts + how many match the logged output
    uv run replay.py cases.json --save before.json    # remember the current labels
    # ...edit ../ga5-api/api/rules.py...
    uv run replay.py cases.json --diff before.json    # exactly which cases a change moves

`cases.json` comes from parse_vercel_log.py. The logged lines are compacted and truncated, so this
rebuilds just enough of each case for rules.py to run. With unchanged rules it should reproduce the
logged output for every case; if it doesn't, fix the rebuild before trusting a diff.
"""
import argparse
import ast
import collections
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "ga5-api" / "api"))
import rules  # noqa: E402


def rebuild(c):
    """Turn one compact CASE log record back into the case shape rules.classify() expects."""
    kind, iso, ws = (list(c["e"]) + [None, None, None])[:3]
    items = []
    for x in c["x"]:
        try:
            d = ast.literal_eval(x)
        except (ValueError, SyntaxError):    # truncated in the log: recover the fields rules.py uses
            d = {"text": x}
            if "'path'" in x:
                d["path"] = "?"
            if "'tool'" in x:
                d["tool"] = "?"
        if "untrusted" in x:
            d["origin"] = "untrusted"
        items.append(d)
    return {
        "caseId": c["id"],
        "environment": {"kind": kind, "isolation": iso, "workspace": ws},
        "messages": [{"role": "user", "content": m} for m in c["m"]],
        "memory": [i for i in items if "text" in i and "path" not in i and "tool" not in i],
        "repositoryInstructions": [i for i in items if "path" in i],
        "toolResults": [i for i in items if "tool" in i],
        "rollbackPlan": c["rb"],
        "proposedTool": {"resolved": c["t"]} if c["t"] else None,
    }


def label(case):
    r = rules.classify(case)
    return [r["requestDecision"], r["toolDecision"], r["route"], r["trajectory"]]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cases")
    ap.add_argument("--save", help="write the current labels to this file")
    ap.add_argument("--diff", help="compare the current labels with a file written by --save")
    a = ap.parse_args()

    logged = json.loads(Path(a.cases).read_text(encoding="utf-8"))
    now = {c["id"]: label(rebuild(c)) for c in logged}

    same = sum(now[c["id"]] == c["o"] for c in logged)
    print(f"{len(logged)} cases, {same} labelled exactly as in the log")
    for tup, n in collections.Counter(tuple(v) for v in now.values()).most_common():
        print(f"  {n:3d}  {tup}")

    if a.diff:
        before = json.loads(Path(a.diff).read_text(encoding="utf-8"))
        moved = [c for c in logged if before.get(c["id"]) != now[c["id"]]]
        print(f"\n{len(moved)} case(s) changed:")
        for c in moved:
            print(f"  {c['id']}  {before.get(c['id'])} -> {now[c['id']]}")
            print(f"      latest: {c['m'][-1][:110] if c['m'] else '(no message)'}")
    if a.save:
        Path(a.save).write_text(json.dumps(now), encoding="utf-8")
        print(f"\nsaved labels -> {a.save}")


if __name__ == "__main__":
    main()
