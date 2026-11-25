"""The bootstrap runner of v0.5.12 (charter, step 0), run by v0.5.11's launcher as the unit
``bootstrap-v0512`` (the pre-existing outer meter).

    launch_v9.py docs/validation/v0.5.11/units/bootstrap-v0512.json -- <payload argv...>

It scans the disk roots (``diskbound.py``), runs the payload in a job object (``jobrun.py``: CPU
and written bytes of the whole tree, processors 8 to 31, BelowNormal), scans again, and appends one
line to ``docs/validation/v0.5.12/bootstrap-disk.jsonl``: the payload, its CPU, its written bytes,
the roots before and after, and the bound ``O_start + W`` of that attempt (O measured from the
phase's baseline, the first line of that file). The payload's own stdout and stderr are under
``.cache/v0512/boot/runs/``. Exit code: the payload's.
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import diskbound  # noqa: E402
import jobrun  # noqa: E402

ROOT = diskbound.ROOT
RECORD = ROOT / "docs" / "validation" / "v0.5.12" / "bootstrap-disk.jsonl"


def main() -> int:
    payload = sys.argv[1:]
    if payload and payload[0] == "--":
        payload = payload[1:]
    if not payload:
        raise SystemExit("usage: bootstrap_job.py <payload argv...>")
    payload = [sys.executable if a == "{python}" else a for a in payload]
    baseline = None
    if RECORD.exists():
        first = RECORD.read_text(encoding="utf-8").splitlines()[0]
        baseline = json.loads(first)["baseline_fast_total"]
    attempt = uuid.uuid4().hex[:12]
    run_dir = ROOT / ".cache" / "v0512" / "boot" / "runs" / attempt
    run_dir.mkdir(parents=True, exist_ok=True)
    before = diskbound.scan()
    if baseline is None:
        baseline = before["fast_total"]
    rec = jobrun.run(payload, ROOT, run_dir / "stdout.txt", run_dir / "stderr.txt", timeout_s=1800)
    after = diskbound.scan()
    o_start = before["fast_total"] - baseline
    o_end = after["fast_total"] - baseline
    line = {
        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "attempt": attempt,
        "baseline_fast_total": baseline,
        "payload": [Path(a).name if a == sys.executable else a for a in payload],
        "job": rec,
        "o_start": o_start,
        "o_end": o_end,
        "bound": max(o_start + rec["write_bytes"], o_end),
        "stdout_sha256": hashlib.sha256((run_dir / "stdout.txt").read_bytes()).hexdigest(),
    }
    with RECORD.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(line, sort_keys=True) + "\n")
    sys.stdout.write((run_dir / "stdout.txt").read_text(encoding="utf-8", errors="replace"))
    print(json.dumps({k: line[k] for k in ("attempt", "o_start", "o_end", "bound")}))
    print(json.dumps({k: rec[k] for k in ("exit_code", "cpu_s", "write_bytes", "stopped")}))
    return rec["exit_code"]


if __name__ == "__main__":
    raise SystemExit(main())
