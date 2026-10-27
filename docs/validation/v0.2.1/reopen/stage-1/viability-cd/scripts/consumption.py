"""The C/D viability lot's measured consumption (after the lot): per sub-lot, the tasks' summed
wall seconds (LP-s, one process per task), their mean, the invocations' elapsed hours and the cost
check; the determinism checks' and the environment records' files are listed with their SHA-256.
Read only.

  python consumption.py <.cache/viability-lot folder> <out.json>
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


def main(argv: list[str]) -> int:
    base = Path(argv[0])
    out: dict = {"sub_lots": {}, "files": {}}
    for lot in ("viability-c", "viability-d"):
        run = base / lot
        seconds = [
            json.loads(p.read_text(encoding="utf-8"))["seconds"]
            for p in sorted((run / "timings").glob("*.json"))
        ]
        invocations = [
            json.loads(p.read_text(encoding="utf-8"))
            for p in sorted((run / "consumption").glob("*.json"))
        ]
        check = json.loads((run / "cost-check.json").read_text(encoding="utf-8"))
        out["sub_lots"][lot] = {
            "tasks_timed": len(seconds),
            "lp_hours": sum(seconds) / 3600.0,
            "mean_task_seconds": sum(seconds) / len(seconds),
            "invocations": invocations,
            "elapsed_hours": sum(i["elapsed_hours"] for i in invocations),
            "cost_check": check,
            "manifest_sha256": hashlib.sha256((run / "manifest.json").read_bytes()).hexdigest(),
            "records_sha256": hashlib.sha256(
                b"".join(
                    p.relative_to(run).as_posix().encode() + b"\0" + p.read_bytes() + b"\0"
                    for p in sorted((run / "records").rglob("000.json"))
                )
            ).hexdigest(),
        }
    for name in ("env-before.json", "env-after.json", "determinism-viability-c.json",
                 "determinism-viability-d.json", "evaluation.json", "summary.json"):  # fmt: skip
        p = base / name
        out["files"][name] = {
            "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
            "bytes": p.stat().st_size,
        }
    with open(argv[1], "x", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(out, indent=1) + "\n")
    print(json.dumps({k: {x: v[x] for x in ("lp_hours", "mean_task_seconds", "elapsed_hours")}
                      for k, v in out["sub_lots"].items()}, indent=1))  # fmt: skip
    print(json.dumps(out["files"], indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
