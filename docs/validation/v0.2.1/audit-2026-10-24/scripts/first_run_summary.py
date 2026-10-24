"""Summarize a tests' first run (before any code) from its JUnit file: per test, its outcome
and the exception's first line, every absolute path replaced by <path>/<file name>, no host
name. Usage: first_run_summary.py <out.json> <label>=<junit.xml> ..."""

import json
import re
import socket
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

PATH = re.compile(r"(?:[A-Za-z]:|\\\\[^\\/\s'\"]+)(?:[\\/]+[^\\/'\"]+)*[\\/]+([^\\/'\"]+)")


def clean(text: str) -> str:
    text = PATH.sub(lambda m: "<path>/" + m.group(1), text)
    host = socket.gethostname()
    return text.replace(host, "<host>") if host else text


out = {"format": "refute-first-run/1", "runs": []}
for arg in sys.argv[2:]:
    label, path = arg.split("=", 1)
    rows = []
    for case in ET.parse(path).getroot().iter("testcase"):
        outcome, detail = "passed", None
        for tag in ("failure", "error", "skipped"):
            node = case.find(tag)
            if node is not None:
                outcome = tag
                detail = clean((node.get("message") or "").splitlines()[0][:200])
                break
        rows.append(
            {
                "test": f"{case.get('classname')}::{case.get('name')}",
                "outcome": outcome,
                "detail": detail,
            }
        )
    counts = {
        k: sum(r["outcome"] == k for r in rows) for k in ("passed", "failure", "error", "skipped")
    }
    out["runs"].append({"label": label, "tests": len(rows), "counts": counts, "cases": rows})
text = json.dumps(out, indent=1, sort_keys=True)
if re.search(r"[A-Za-z]:[\\/]|Users", text):
    raise SystemExit("a local path is left in the summary")
Path(sys.argv[1]).write_text(text + "\n", encoding="utf-8")
print(json.dumps([{k: r[k] for k in ("label", "tests", "counts")} for r in out["runs"]]))
