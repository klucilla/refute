"""Reference digests of complete synthetic analyses, made with the code **before** piece 2 of M4
(docs/validation/v0.2.1/reopen/m4-implementation-map.md, Amendment 2): the check that, with
``gauntlet.corrections.enabled`` false, every later piece leaves the M3 code path byte for byte.

For each case (scenario, seed, noise mode) the full analysis with the fast plan of the suite gives a
record (verdict, reason, every test, the holdout rounds, the candidate) serialized by
``refute.core.io.dumps_json``; its SHA-256 is written to ``analysis-reference.json`` next to this
file (never overwritten). The digests are bound to the platform and numpy version that made them
(the bytes of floating-point results are not portable; correlated-noise-acceptance.md, Amendment 4).

Usage: uv run python docs/validation/v0.2.1/reopen/m4/analysis_reference.py [<out.json>]
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
CASES = [
    (name, seed, "white")
    for name in ("planet", "eb_secondary", "eb_odd_even", "noise", "blend", "vanishing")
    for seed in (0, 1)
] + [("planet", 0, "correlated")]


def record(case: tuple[str, int, str]) -> str:
    from refute.core.io import dumps_json, to_jsonable
    from refute.packs.tess.synthetic import analyze_scenario_seed

    analysis = analyze_scenario_seed(case)
    candidate = analysis.gauntlet.candidate
    data = {
        "verdict": analysis.verdict,
        "reason": analysis.verdict_reason,
        "tests": [t.to_dict() for t in analysis.tests],
        "holdout": analysis.holdout.to_dict(),
        "candidate": asdict(candidate) if candidate is not None else None,
    }
    return hashlib.sha256(dumps_json(to_jsonable(data)).encode("utf-8")).hexdigest()


def main(argv: list[str]) -> int:
    from refute.core.runner import run_processes

    out = Path(argv[0]) if argv else HERE / "analysis-reference.json"
    if out.exists():
        print(f"refusing to overwrite {out}")
        return 1
    dirty = subprocess.run(
        ["git", "-C", str(ROOT), "status", "--porcelain", "--", "src"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    if dirty:
        print("src/ has uncommitted changes: the reference must come from committed code")
        return 1
    commit = subprocess.run(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True, check=True
    ).stdout.strip()
    digests = run_processes(record, CASES, 6)
    payload = {
        "format": "refute-analysis-reference-1",
        "code_commit": commit,
        "platform": sys.platform,
        "numpy": np.__version__,
        "digests": {f"{n}|{s}|{m}": d for (n, s, m), d in zip(CASES, digests, strict=True)},
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )
    print(f"{len(digests)} digests at {commit[:7]} -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
