"""v0.5.2 stage 2: the acceptance's schedule sized run by run from version 4's measured
availability, and its price. A projection for the redesign after the failed adequacy check (the
maintainer's decision of 2026-11-09, item 1); it runs no curve and decides nothing.
``method_status: not_validated``.

**The table.** The rebuilt reference (``components-v4.pkl``: version 4's development records at the
whole A0 round 2 schedule) has 717 components and 717 runs: every component holds exactly one run,
so sizing run by run (the maintainer's "cell by cell") equals sizing component by component here.
That is a property of this table, not a rule for future ones (Codex, redesign round 1).

**Each run's size**, in exact integer arithmetic, the largest over the members ``m`` the run carries
(``g_m`` of its ``n_r`` curves): ``point``, ``ceil(T n_r / g_m)``; ``lower``, ``ceil(T / p_m)`` with
``p_m`` the one-sided 95 % Clopper-Pearson lower bound on ``g_m / n_r``, per member (a planning
margin, not a simultaneous guarantee); ``lower_family``, the same with Bonferroni over the family.
``version_3`` is the schedule priced so far (version 3's ``min_g``). ``lower_pilot_a08e`` is a
what-if for a pilot of ten times the curves in the A0.8 event runs only, at the same availability:
it prices the pilot, it is no measurement, and a real pilot would use new records.

**The price.** CPU per curve by section, measured in the adequacy run itself (the ledger's spent
hours over that run's curves, the reboot's crash charge taken out of A0.2: it stays in what was
spent), at 12 workers. The totals add what was spent, the other budget lines as they stand, a fresh
out-of-sample check, and a sensitivity of the known-answer gate scaled by the schedule's curves
(its datasets reproduce the schedule's layout); that last term is a scaling, not a measurement.

Usage: ``.venv/Scripts/python.exe docs/validation/v0.5.2/stage2/sizing_v4.py``; writes
``sizing-v4.json``.
"""

from __future__ import annotations

import json
import pickle
import sys
from pathlib import Path

import numpy as np
from scipy import stats

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(HERE))
import adequacy  # noqa: E402
import budgeted  # noqa: E402

TARGET = 9000
LEVEL = 0.05
PILOT_K = 10
V3 = ROOT / ".cache/v052/s2/plasmode/components.pkl"
V4 = ROOT / ".cache/v052/s2/adequacy/components-v4.pkl"
CRASH_CHARGE_A02_HOURS = 12589.8 / 3600.0  # the batch open at the reboot of 2026-11-09
OTHER_LINES = ("known_answer", "sinusoid", "selector", "sabotages", "remaining_work_packages",
               "comb_reference_check")  # fmt: skip
FRESH_CHECK_HOURS = 85.0  # the units of the whole round 2 schedule (64) and the evaluation (21)
SECTION_OF = {"a01": "a01", "a02": "a02", "a04": "a04", "a05": "a05", "a07": "a07",
              "a08e": "a08", "a08g": "a08"}  # fmt: skip
RULES = ("version_3", "point", "lower", "lower_family", "lower_pilot_a08e")


def ceil_div(a: int, b: int) -> int:
    return -(-a // b)


def cpu_per_curve() -> dict:
    parts = budgeted.load()["sections"]["adequacy"]["parts"]
    out = {}
    for section in adequacy.SECTIONS:
        spent = parts[f"units-{section}"]["spent_hours"]
        if section == "a02":
            spent -= CRASH_CHARGE_A02_HOURS
        curves = sum(len(arg[1]) for _, arg in adequacy.shards_of(section))
        out[section] = {"curves": curves, "cpu_hours": spent, "cpu_seconds": spent * 3600 / curves}
    return out


def lower_size(g: int, n: int, level: float) -> int:
    low = float(stats.beta.ppf(level, g, n - g + 1))
    return int(np.ceil(TARGET / low))


def spent_so_far(ledger: dict) -> float:
    return budgeted.spent(ledger)  # the charges included (Codex, end of round 5)


def main() -> None:
    v3 = pickle.loads(V3.read_bytes())  # noqa: S301 - local cache, written by plasmode.py
    v4 = pickle.loads(V4.read_bytes())  # noqa: S301 - local cache, written by adequacy.py
    if any(len(c["runs"]) != 1 for c in v4):
        raise SystemExit("a component holds several runs: the run-by-run rule needs revisiting")
    family = sum(len(c["members"]) for c in v4)
    cost = cpu_per_curve()
    curves = {rule: {} for rule in RULES}
    pilot = {"runs": 0, "curves": 0, "cpu_hours": 0.0}
    manifest = {}
    for c3, c4 in zip(v3, v4, strict=True):
        r3, r4 = c3["runs"][0], c4["runs"][0]
        key, n_r = r4["key"], int(r4["n"].shape[0])
        g = (r4["n"] > 0).sum(axis=0)
        if (g == 0).any():  # a required member no curve carries cannot be sized (Codex, round 5)
            raise SystemExit(f"{key!r}: a family member with no contributing curve is unpriceable")
        carried = [int(x) for x in g]
        size = {
            "version_3": ceil_div(TARGET * int(r3["n"].shape[0]), int(c3["min_g"])),
            "point": max(ceil_div(TARGET * n_r, x) for x in carried),
            "lower": max(lower_size(x, n_r, LEVEL) for x in carried),
            "lower_family": max(lower_size(x, n_r, LEVEL / family) for x in carried),
        }
        if key[0] == "a08e":
            size["lower_pilot_a08e"] = max(
                lower_size(PILOT_K * x, PILOT_K * n_r, LEVEL) for x in carried
            )
            extra = (PILOT_K - 1) * n_r
            pilot["runs"] += 1
            pilot["curves"] += extra
            pilot["cpu_hours"] += extra * cost["a08"]["cpu_seconds"] / 3600
        else:
            size["lower_pilot_a08e"] = size["lower"]
        section = SECTION_OF[key[0]]
        for rule in RULES:
            curves[rule][section] = curves[rule].get(section, 0) + size[rule]
        manifest[repr(key)] = size
    ledger = budgeted.load()
    spent = spent_so_far(ledger)
    others = sum(budgeted.LINES[k] for k in OTHER_LINES)
    base_curves = sum(curves["version_3"].values())
    totals = {}
    for rule in RULES:
        hours = sum(curves[rule][s] * cost[s]["cpu_seconds"] / 3600 for s in curves[rule])
        ratio = sum(curves[rule].values()) / base_curves
        extra_pilot = pilot["cpu_hours"] if rule == "lower_pilot_a08e" else 0.0
        known_answer_shift = budgeted.LINES["known_answer"] * (ratio - 1.0)
        totals[rule] = {
            "curves": sum(curves[rule].values()),
            "curves_ratio_to_version_3": ratio,
            "a0_acceptance_cpu_hours": hours,
            "pilot_cpu_hours": extra_pilot,
            "total_without_known_answer_rescaling": spent + others + FRESH_CHECK_HOURS + hours
            + extra_pilot,
            "known_answer_rescaling_sensitivity": known_answer_shift,
            "total_with_known_answer_rescaling": spent + others + FRESH_CHECK_HOURS + hours
            + extra_pilot + known_answer_shift,
        }  # fmt: skip
    doc = {
        "label": "the acceptance's schedule sized run by run from version 4; it decides nothing",
        "method_status": "not_validated",
        "target": TARGET,
        "one_sided_level": LEVEL,
        "family_members": family,
        "components_and_runs": len(v4),
        "cpu_per_curve_from_the_adequacy_run": cost,
        "spent_so_far_cpu_hours": spent,
        "other_lines_cpu_hours": others,
        "fresh_check_cpu_hours": FRESH_CHECK_HOURS,
        "hard_maximum": budgeted.HARD_MAXIMUM,
        "pilot_a08e_what_if": {"k": PILOT_K, **pilot},
        "curves_by_section": curves,
        "totals": totals,
    }
    (HERE / "sizing-v4.json").write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n", "utf-8")
    (ROOT / ".cache/v052/s2/sizing-v4-manifest.json").write_text(
        json.dumps(manifest, indent=1, sort_keys=True) + "\n", "utf-8"
    )
    print(json.dumps({k: doc[k] for k in ("spent_so_far_cpu_hours", "pilot_a08e_what_if",
                                          "totals")}, indent=1), flush=True)  # fmt: skip


if __name__ == "__main__":
    main()
