"""Pre-registered choice of the dossiers to review (v0.2), from a run summary.

Implements the review rule of calibration/v0.2/PROTOCOL.md. It refuses to run
before the reviewer drand round fixed in the protocol has been published:

    uv run --frozen python calibration/v0.2/select_reviews.py \\
        calibration/v0.2/results/<run_id>/summary.json

Rule:

1. every known false positive;
2. every unexpected verdict: a known planet REFUTED, or a known false positive
   SURVIVED (already included by 1);
3. three known planets whose verdict is not REFUTED: sorted by TIC ID, shuffled
   with random.Random(seed), the first three. seed = int(randomness, 16) of the
   reviewer drand round, verified exactly as for the target selection.

Prints the list as JSON. Changes nothing.
"""

from __future__ import annotations

import importlib.util
import json
import random
import sys
from pathlib import Path

REVIEW_ROUND = 6542966  # published at 2026-10-11T12:00:00Z
N_RANDOM_PLANETS = 3

_spec = importlib.util.spec_from_file_location(
    "select_targets_v02", Path(__file__).resolve().parent / "select_targets.py"
)
_select = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_select)


def choose(summary: dict, seed: int) -> dict:
    rows = summary["targets"]
    fps = [r["target"] for r in rows if r["kind"] == "false_positive"]
    unexpected = [
        r["target"]
        for r in rows
        if (r["kind"] == "planet" and r["verdict"] == "REFUTED")
        or (r["kind"] == "false_positive" and r["verdict"] == "SURVIVED")
    ]
    pool = sorted(
        (r["target"] for r in rows if r["kind"] == "planet" and r["verdict"] != "REFUTED"),
        key=lambda key: int(key.split("-")[1]),
    )
    random.Random(seed).shuffle(pool)
    drawn = pool[:N_RANDOM_PLANETS]
    return {
        "false_positives": fps,
        "unexpected": unexpected,
        "random_planets": drawn,
        "review": sorted(set(fps) | set(unexpected) | set(drawn)),
        "second_reviewer": unexpected,
    }


def main(argv: list[str]) -> int:
    summary = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
    seed, drand = _select.drand_seed(REVIEW_ROUND)
    print(json.dumps({"drand": drand, "seed": str(seed), **choose(summary, seed)}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
