"""v0.5.1 WP5, row 5.3: the v0.5 battery reproduces its own C1 development prefix records.

A re-execution of recorded calibration records: it runs only after the maintainer's approval,
recorded on the tracking issue with this procedure (CLAUDE.md, "Pre-registration process").

It rebuilds the 260 tasks of the v0.5 C1 development prefix exactly as the v0.5 step did
(``calib05.steps._c1_prefix_tasks``: the v0.4 claim's plan, ``c1.development_seed``), runs
``calib05.c1.run_task`` on each with the current code, and compares every record with the
recorded one (``.cache/v05/calibration/c1-prefix/records.jsonl``, checked first against the
SHA-256 given on the command line), field by field except ``cpu_seconds`` and the runner's
``task`` identity. Development data only;
decides nothing; never writes into the recorded run folder.

Run (heavy, about 3.2 processor-hours; from the project root):
    scripts/launch_affinity.ps1 -Script docs/validation/v0.5.1/wp5/reproduce_c1_prefix.py \
        -Arguments '<records sha256>' -Log .cache/v051/wp5/reproduce-c1-prefix
Writes ``reproduce-c1-prefix.json`` next to this script (exclusively, never over a file).
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
RECORDS = ROOT / ".cache" / "v05" / "calibration" / "c1-prefix" / "records.jsonl"
# the processor time, and the task identity the runner adds to each stored record
IGNORED = ("cpu_seconds", "task")


def _differences(a, b, path="$") -> list[str]:
    if isinstance(a, dict) and isinstance(b, dict):
        out = [f"{path}: keys {sorted(a)} != {sorted(b)}"] if set(a) != set(b) else []
        return out + [
            d for k in sorted(set(a) & set(b)) for d in _differences(a[k], b[k], f"{path}.{k}")
        ]
    if isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        return [
            d
            for i, (x, y) in enumerate(zip(a, b, strict=True))
            for d in _differences(x, y, f"{path}[{i}]")
        ]
    return [] if a == b else [f"{path}: {a!r} != {b!r}"]


def _task(args):
    from refute.packs.tess.calib05 import c1

    return c1.run_task(args)


def main(argv: list[str]) -> int:
    sys.path.insert(0, str(ROOT / "src"))
    from refute.core.runner import default_workers
    from refute.packs.tess.calib05 import steps

    expected_sha = argv[0]
    raw = RECORDS.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected_sha:
        raise SystemExit("the recorded prefix's SHA-256 is not the one given")
    recorded = {
        f"{r['family']}/{r['index']}": r for r in map(json.loads, raw.decode().splitlines())
    }
    tasks = steps._c1_prefix_tasks(ROOT)
    if sorted(f"{t.family}/{t.index}" for t in tasks) != sorted(recorded):
        raise SystemExit("the rebuilt tasks are not the recorded ones")
    with ProcessPoolExecutor(max_workers=default_workers()) as pool:
        records = list(pool.map(_task, tasks))
    report = {"records_sha256": expected_sha, "tasks": len(tasks), "differences": {}}
    report["commit"] = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()
    for task, new in zip(tasks, records, strict=True):
        key = f"{task.family}/{task.index}"
        old = {k: v for k, v in recorded[key].items() if k not in IGNORED}
        new = {
            k: v for k, v in json.loads(json.dumps(new, default=str)).items() if k not in IGNORED
        }
        diff = _differences(new, old)
        if diff:
            report["differences"][key] = diff[:20]
    report["reproduced"] = len(tasks) - len(report["differences"])
    report["processor_hours"] = sum(float(r["cpu_seconds"]) for r in records) / 3600.0
    with open(HERE / "reproduce-c1-prefix.json", "x", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(report, indent=1) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "differences"}, indent=1))
    return 0 if not report["differences"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
