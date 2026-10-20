"""The compute of the ``R_min`` study, from its timing lot (map Amendment 26, 6), for the
maintainer's decision before any lot of the study or of ``refute-v0.2.1-bs-choice`` is generated.

Read-only; writes rmin-cost.json next to this file (never replaced).
Usage: uv run python docs/validation/v0.2.1/reopen/calc/rmin_cost.py <timing record>

The projection declared by Amendment 26, 6, before the timing lot existed: each group and scenario
is costed at **1.25 times the largest per-curve time observed** in it, for every curve of the study
and of the reserve (the realized sizes of ``rmin-sizing.json``, both readings of the lots shown)
and of the lot ``bs-choice``; the generation the same way, per target; the lot overhead 1.2 of
campaign 1; machine time is the worker time divided by the 6 workers (the summed worker hours are
shown apart). Compared with the 397 h ceiling of ``calibration-ceiling-decision.md``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "rmin-cost.json"
SIZING = HERE / "rmin-sizing.json"
MARGIN = 1.25  # on the largest observed time (a sample maximum is not a bound)
LOT_OVERHEAD = 1.2  # campaign 1
WORKERS = 6
CEILING_HOURS = 397
SCENARIOS = ("constant", "disappearing", "weakened")
GROUPS = (
    "white, no variability",
    "white, variability",
    "AR(1), no variability",
    "AR(1), variability",
)
# The lot bs-choice (Amendment 9): the planets of the bands near and measurable, every tenth index,
# per noise model: without variability the indexes 0, 10, ..., 190 of each band (40), with
# variability 200, 210, 220, 230, 240 of each band (10); the constant scenario only.
BS_CHOICE = {
    "white, no variability": 40,
    "white, variability": 10,
    "AR(1), no variability": 40,
    "AR(1), variability": 10,
}
# The other reading of the lots (whole prefixes, Amendment 26, reading 1): 64 prefixes for every
# group, so 64 x 400 targets for the groups without variability.
WHOLE_PREFIXES = {
    "white, no variability": 64 * 400,
    "white, variability": 64 * 100,
    "AR(1), no variability": 64 * 400,
    "AR(1), variability": 64 * 100,
}


def rates(timing: dict) -> dict:
    """Per group: the projected seconds per target of the generation and per curve of each
    scenario (the margin times the largest observed)."""
    out = {}
    for group in GROUPS:
        s = timing["summary"][group]
        out[group] = {
            "generation": MARGIN * s["generation"]["max"],
            **{sc: MARGIN * s[sc]["max"] for sc in SCENARIOS},
        }
    return out


def part(rate: dict, targets: dict, scenarios=SCENARIOS) -> dict:
    worker_seconds = 0.0
    curves = 0
    for group, n in targets.items():
        r = rate[group]
        worker_seconds += n * (r["generation"] + sum(r[sc] for sc in scenarios))
        curves += n * len(scenarios)
    worker_seconds *= LOT_OVERHEAD
    return {
        "targets": sum(targets.values()),
        "light_curves": curves,
        "worker_hours": worker_seconds / 3600.0,
        "machine_hours": worker_seconds / WORKERS / 3600.0,
    }


def main(argv: list[str]) -> None:
    if OUT.exists():
        raise SystemExit(f"{OUT.name} exists; not replaced")
    timing_path = Path(argv[0])
    timing = json.loads(timing_path.read_text(encoding="utf-8"))
    sizing = json.loads(SIZING.read_text(encoding="utf-8"))
    per_group = {g: sizing["per_group"][g]["targets"] for g in GROUPS}
    rate = rates(timing)
    timing_hours = timing["wall_seconds"] / 3600.0
    per_group_reading = {
        "bs_choice": part(rate, BS_CHOICE, ("constant",)),
        "study": part(rate, per_group),
        "reserve": part(rate, per_group),
    }
    whole_reading = {
        "bs_choice": per_group_reading["bs_choice"],
        "study": part(rate, WHOLE_PREFIXES),
        "reserve": part(rate, WHOLE_PREFIXES),
    }

    def total(parts: dict) -> float:
        return timing_hours + sum(p["machine_hours"] for p in parts.values())

    out = {
        "timing_record": {
            "file": timing_path.name,
            "code_commit": timing["code_commit"],
            "configuration": timing["configuration"],
            "wall_hours": timing_hours,
        },
        "projection": {
            "margin_on_largest_observed": MARGIN,
            "lot_overhead": LOT_OVERHEAD,
            "workers": WORKERS,
            "affinity": "logical processors 0 to 7",
        },
        "seconds_per_target_and_curve": rate,
        "reading_per_group": {**per_group_reading, "total_machine_hours": total(per_group_reading)},
        "reading_whole_prefixes": {**whole_reading, "total_machine_hours": total(whole_reading)},
        "ceiling_hours": CEILING_HOURS,
        "note": (
            "the 397 h ceiling was decided for the calibration population of revision 4 "
            "(calibration-ceiling-decision.md); Amendment 19 brings the study's cost to the "
            "maintainer with it, and how the study counts against it is the maintainer's decision"
        ),
    }
    OUT.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main(sys.argv[1:])
