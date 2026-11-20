"""GA5 Q4: pull the graded cases out of a Vercel runtime-log export.

The /classify endpoint prints one `CASE {...}` line per graded case (see ga5-api/api/index.py). Vercel's
log viewer has no download button, so: search the logs for CASE, click "Copy visible logs", paste into a
text file, then run

    uv run parse_vercel_log.py exported-logs.txt cases.json

Lines from your own test requests (any id you chose yourself) are kept too, so drop them if needed.
"""
import json
import sys


def cases_from_export(path):
    cases = {}
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line.startswith("{"):
                continue                      # the export starts with a few header lines
            try:
                msg = json.loads(line).get("message", "")
            except json.JSONDecodeError:
                continue
            if msg.startswith("CASE "):
                case = json.loads(msg[5:])
                cases[case["id"]] = case      # a Check sends each case once; keep the latest copy
    return list(cases.values())


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("usage: parse_vercel_log.py EXPORTED_LOGS.txt OUT_CASES.json")
    found = cases_from_export(sys.argv[1])
    with open(sys.argv[2], "w", encoding="utf-8") as f:
        json.dump(found, f, ensure_ascii=False)
    print(f"{len(found)} cases -> {sys.argv[2]}")
