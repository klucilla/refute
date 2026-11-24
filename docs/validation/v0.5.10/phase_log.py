"""The append-only phase log of v0.5.10 (Process diet 2, item 4; the charter, section 4).

Every run writes one entry before it starts (``before``: the question and the choices) and one
after it ends (``after``: provenance, coverage and every outcome, including failures and abandoned
attempts). Each entry carries a machine timestamp (UTC). Entries are only appended, never edited.

    from phase_log import log
    log("before", "census-d1", question="...", choices={...})
"""

import json
import time
from pathlib import Path

LOG = Path(__file__).resolve().parent / "log.jsonl"


def log(kind: str, run: str, **fields) -> dict:
    if kind not in ("before", "after", "note"):
        raise ValueError(f"unknown entry kind {kind!r}")
    entry = {"utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "kind": kind, "run": run}
    entry.update(fields)
    with open(LOG, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")
    return entry


if __name__ == "__main__":
    import sys

    print(json.dumps(log(sys.argv[1], sys.argv[2], text=" ".join(sys.argv[3:]))))
