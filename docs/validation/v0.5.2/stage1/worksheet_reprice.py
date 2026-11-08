"""v0.5.2 stage 1: the acceptance's cost repriced from what A0 round 2 of v0.5.1 measured.

``worksheet.py`` scaled the old schedule by ``n / 400``, from cost probes at two sectors. Codex's
review of the stage's report (round 1, objection 3) showed that this does not price the specified
acceptance. Its outputs stay as the original calculation; this script replaces nothing in them. It
reads ``docs/validation/v0.5.1/acceptance/a0r2-result.json``, which holds each section's measured
CPU (22 workers, the real mix of sector counts) and each row's availability, and for each row asks
how many curves its run needs for ``T`` independent contributing curves. It runs nothing else and
decides nothing. ``method_status: not_validated``.

The model, and its assumptions:

- A row is an entry of the old main tables (3,558, without A0.7's forced-pooling diagnostics). A
  row of a run is one statistic, or one conditional branch, of one cell of that run.
- A group row's availability is ``available / units of its run``: one curve, one pull. A coverage
  stratum is assumed to be the run's coverage kind (A0.2's rows hold at most 700 of 700).
- A per-event row (A0.1, A0.8's event rows) holds several pulls per curve, and the result file does
  not give distinct contributing curves per row. ``T`` is asked of curves. A0.8's event rows use the
  curves of their branch in the run of the same coverage kind (``branches`` in the result file): an
  estimate, not a bound, since an event's stratum can differ from its curve's kind. A0.1's fraction
  is not in the file; it is priced at 1.0 and a sensitivity at 0.25, holding the priced membership
  fixed, is reported (under the floor policy, at floor 0.50 those 15 members would leave the pricing
  instead). The distinct counts are in the archived per-unit records of that acceptance run, which
  this stage does not read.
- ``units needed = max(units run, ceil(max over the run's rows of T / availability))``, over rows
  at or above an availability floor. It delivers ``T`` curves **in expectation**, not with a stated
  probability. A run with no row at or above the floor keeps its old size (retained diagnostic
  expenditure, reported). A row below the floor stays not measured, and its test INCONCLUSIVE; the
  floor selects what is priced and waives nothing: operational permission needs every applicable
  required member. A row with no observation at all is counted apart.
- The CPU per unit is the section's mean: it hides the difference between sector counts.
- ``ideal 22-worker-equivalent days`` is ``CPU hours / (22 x 24)``, a fully occupied machine, not a
  forecast of wall time.
- The sector expansion holds availability, per-curve targets and cost per sector fixed; it does not
  establish the expanded family's required size.

Not priced: the corrected code's extra cost, the reference checks, the known-answer validation, the
sabotages at the new sizes, A0.3 and the remaining acceptances, and C2'/C3'.

Usage (from the project root): ``.venv/Scripts/python.exe <this file>``.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE))
import worksheet as ws  # noqa: E402

TARGETS = (2800, 3300, 3500)
FLOORS = (0.5, 0.25, 0.1)
WORKERS = 22
SECTOR_EXPOSURE = 34.0 / 9.0
INDEXED_BY_SECTORS = ("a02", "a04", "a05", "a07", "a08g", "a08h")


def _walk(node, path=()):
    if isinstance(node, dict):
        if "result" in node and "available" in node:
            yield path, node
            return
        for key, value in node.items():
            yield from _walk(value, (*path, key))


def _row(section, table, key, band, branches):
    """The row's run, its stratum position in the run, its units and its availability."""
    parts = key.split("/")
    available = band["available"]
    if section == "a01":
        return ("a01", parts[0], parts[1]), 2, 200, 1.0
    if section in ("a02", "a04"):
        return (section, *parts[:3]), 2, 700, min(available / 700.0, 1.0)
    if section == "a05":
        return ("a05", *parts[:6]), 5, 400, min(available / 400.0, 1.0)
    if section == "a07":
        if table != "rule_bands":
            return None
        return ("a07", parts[0]), None, 700, min(available / 700.0, 1.0)
    if section == "a08" and table == "event_bands":
        noise, stratum, depth, branch = parts
        counts = branches[f"event/{noise}/{stratum}/2/{depth}"]
        curves = (
            counts["excluded"] if branch == "excluded" else counts["units"] - counts["excluded"]
        )
        fraction = 0.0 if available == 0 else curves / counts["units"]
        return ("a08e", noise, stratum, depth), 2, counts["units"], fraction
    if section == "a08" and parts[0] == "group":
        return ("a08g", *parts[1:5]), 2, 700, min(available / 700.0, 1.0)
    if section == "a08":
        return ("a08h", *parts[3:5]), None, 700, min(available / 700.0, 1.0)
    return None


def _load():
    doc = json.loads(
        (ROOT / "docs/validation/v0.5.1/acceptance/a0r2-result.json").read_text("utf-8")
    )
    measured, rows = {}, []
    for section, body in doc["sections"].items():
        measured[section] = {
            "cpu_hours": body["run"]["cpu_hours"],
            "scheduled": body["run"]["scheduled"],
            "cpu_seconds_per_unit": body["run"]["cpu_hours"] * 3600 / body["run"]["scheduled"],
        }
        if section.startswith("sabotage"):
            continue
        for path, band in _walk(body):
            placed = _row(section, path[0], path[-1], band, body.get("branches"))
            if placed:
                run, stratum, units, fraction = placed
                rows.append(
                    {
                        "section": section,
                        "run": run,
                        "stratum": stratum,
                        "units": units,
                        "fraction": fraction,
                    }
                )
    return measured, rows


def _section_of(run):
    return "a08" if run[0].startswith("a08") else run[0]


def _price(rows, measured, target, floor):
    needs: dict = {}
    below = empty = kept = 0
    for r in rows:
        needs.setdefault(r["run"], {"units": r["units"], "stratum": r["stratum"], "need": 0.0})
        if r["fraction"] == 0.0:
            empty += 1
        elif r["fraction"] < floor:
            below += 1
        else:
            kept += 1
            run = needs[r["run"]]
            run["need"] = max(run["need"], target / r["fraction"])
    retained = sum(
        v["units"] * measured[_section_of(k)]["cpu_seconds_per_unit"] / 3600.0
        for k, v in needs.items()
        if v["need"] == 0.0
    )
    for run in needs.values():
        run["need"] = max(math.ceil(run["need"]), run["units"])

    def cpu_of(run, units):
        return units * measured[_section_of(run)]["cpu_seconds_per_unit"] / 3600.0

    by_section: dict = {}
    for run, v in needs.items():
        by_section[run[0]] = by_section.get(run[0], 0.0) + cpu_of(run, v["need"])
    a06 = measured["a06"]["cpu_hours"]
    total = sum(by_section.values()) + a06

    grouped: dict = {}
    for run, v in needs.items():
        s = v["stratum"]
        key = run if s is None else run[:s] + run[s + 1 :]
        grouped[key] = max(grouped.get(key, 0.0), cpu_of(run, v["need"]))
    grouped_total = sum(grouped.values()) + a06

    keep_a05_at_old = (
        total - by_section.get("a05", 0.0) + measured["a05"]["cpu_hours"]
        if "a05" in by_section
        else total
    )
    indexed = sum(v for k, v in by_section.items() if k in INDEXED_BY_SECTORS)
    a01_at_quarter = (target / 0.25 - target) * 15 * measured["a01"]["cpu_seconds_per_unit"] / 3600
    return {
        "rows_priced": kept,
        "rows_below_floor_not_measured": below,
        "rows_with_no_observation": empty,
        "cpu_hours": total,
        "retained_old_size_of_runs_with_no_row_at_the_floor_cpu_hours": retained,
        "a01_extra_cpu_hours_if_fraction_0.25_holding_priced_membership_fixed": a01_at_quarter,
        "ideal_22_worker_equivalent_days": total / WORKERS / 24.0,
        "cpu_hours_by_run_kind": by_section,
        "strata_grouped_cpu_hours": grouped_total,
        "a05_left_at_its_old_size_cpu_hours": keep_a05_at_old,
        "with_sector_counts_5_8_12_cpu_hours": total + indexed * (SECTOR_EXPOSURE - 1.0),
    }


def main():
    measured, rows = _load()
    rng = np.random.default_rng(20261109)
    out = {
        "label": "the old-grid repricing from A0 round 2's measurements; it decides nothing",
        "method_status": "not_validated",
        "source": "docs/validation/v0.5.1/acceptance/a0r2-result.json",
        "measured_a0r2": measured,
        "measured_a0r2_total_cpu_hours": sum(v["cpu_hours"] for v in measured.values()),
        "rows": len(rows),
        "reference_cpu_hours_old_design": sum(
            v["cpu_hours"] for k, v in measured.items() if not k.startswith("sabotage")
        ),
        "workers_for_machine_days": WORKERS,
        "scenarios": {},
        "family_sizes": {},
    }
    for floor in FLOORS:
        members = sum(r["fraction"] >= floor for r in rows)
        z = ws._z_star(members)
        out["family_sizes"][f"floor_{floor:g}"] = {
            "family_members": members,
            "z_star": z,
            "n_fixed_90pct": ws._fixed_n(z, rng),
        }
        for target in TARGETS:
            out["scenarios"][f"T{target}_floor{floor:g}"] = _price(rows, measured, target, floor)
    (HERE / "worksheet-reprice.json").write_text(
        json.dumps(out, indent=1, sort_keys=True) + "\n", "utf-8"
    )
    assert math.isfinite(out["measured_a0r2_total_cpu_hours"])
    print(out["measured_a0r2_total_cpu_hours"], out["reference_cpu_hours_old_design"], out["rows"])
    print(json.dumps(out["family_sizes"], indent=0))
    for key, v in out["scenarios"].items():
        print(
            key,
            v["rows_priced"],
            v["rows_below_floor_not_measured"],
            v["rows_with_no_observation"],
            round(v["cpu_hours"], 1),
            round(v["ideal_22_worker_equivalent_days"], 2),
            round(v["retained_old_size_of_runs_with_no_row_at_the_floor_cpu_hours"], 2),
            round(v["a01_extra_cpu_hours_if_fraction_0.25_holding_priced_membership_fixed"], 1),
            round(v["strata_grouped_cpu_hours"], 1),
            round(v["a05_left_at_its_old_size_cpu_hours"], 1),
            round(v["with_sector_counts_5_8_12_cpu_hours"], 1),
        )


if __name__ == "__main__":
    main()
