"""v0.5.2 stage 2: the acceptance's sizes under the max-t, before the code (the maintainer's
decision
of 2026-11-08, #216, item 1). Development simulation only; it runs no estimator and reads no seed
of any acceptance or confirmation. It decides nothing about any target. ``method_status:
not_validated``.

The family is the old grid's (``docs/validation/v0.5.1/acceptance/a0r2-result.json``), at the
availability floor 0.25 approved by the maintainer, without the ``matched_*`` statistics (item 2:
``odd_even`` uses the box). A member's size is ``units x fraction``, its run's units being those
of the run's most demanding priced member. Pulls of a member are modelled as ``n`` independent
draws (one per curve), so that this is an idealization of the clustered design.

For a member with ``n`` pulls of mean ``mu``, standard deviation ``sd`` and kurtosis ``kappa``:
the sample mean and variance are drawn from their laws (normal mean; variance through a chi-square
for ``kappa = 3``, a moment-matched gamma otherwise), with ``se(m)^2 = V / n`` and ``se(V)^2 =
(kappa - 1) V^2 / n``. It is *certified* when ``m +- q se(m)`` lies in [-0.1, 0.1] and ``V +- q
se(V)`` in [0.81, 1.21]. The critical value ``q`` is the upper ``2000 - 1935 + 1 = 66``-th-order
point, nominal level ``66 / 2000 = 0.033``, of the maximum over ``4 M`` standard-normal roots,
``M`` the family's size; it is treated as independent across members, which makes ``q`` as large
as dependence allows, and it is checked against a direct bootstrap on small families.

**Three readings of the power**, all reported, since the guideline says "the family": each member
(the median and the minimum over members), each operational cell (statistic x coverage stratum x
sector count: every member of that cell certified at once, as operational permission requires),
and the whole family (every member certified at once).

Usage (from the project root): ``.venv/Scripts/python.exe <this file> [check]``; writes
``sizing.json`` next to this file.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
from scipy import stats

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE.parent / "stage1"))
import worksheet_reprice as wr  # noqa: E402

FLOOR = 0.25
TARGETS = (2800, 3300, 3500, 4000, 4500, 5000, 5500, 6000, 7000, 8000, 9000, 10000)
ORDER = 1935
REPLICATES = 2000
REPS = 200_000
SCENARIOS = {
    "calibrated": (0.0, 1.0, 3.0),
    "kurtosis_4": (0.0, 1.0, 4.0),
    "kurtosis_6": (0.0, 1.0, 6.0),
    "near_0.02_1.03": (0.02, 1.03, 3.0),
    "near_0.04_1.05": (0.04, 1.05, 3.0),
}


def members():
    """The family's members: run, stratum position, old units, fraction and the operational key."""
    doc = json.loads(
        (ROOT / "docs/validation/v0.5.1/acceptance/a0r2-result.json").read_text("utf-8")
    )
    out = []
    for section, body in doc["sections"].items():
        if section.startswith("sabotage"):
            continue
        for path, band in wr._walk(body):
            placed = wr._row(section, path[0], path[-1], band, body.get("branches"))
            if not placed or "matched" in path[-1]:
                continue
            run, _, units, fraction = placed
            if fraction < FLOOR:
                continue
            out.append({"run": run, "units": units, "fraction": fraction, "op": _op(section, path)})
    return out


def _op(section, path):
    """statistic x coverage stratum x sector count; a per-event row is its own statistic."""
    parts = path[-1].split("/")
    if section == "a01":
        return ("per_event", parts[1], "2")
    if section in ("a02", "a04"):
        return (parts[3], parts[1], parts[2])
    if section == "a05":
        return (parts[6], parts[4], parts[5])
    if section == "a07":
        return ("a07", parts[0], "-")
    if section == "a08" and path[0] == "event_bands":
        return ("per_event", parts[1], "2")
    if section == "a08" and parts[0] == "group":
        return (parts[5] if len(parts) > 5 else parts[-1], parts[2], parts[3])
    return ("a08h", parts[-1], "-")


def critical(m: int) -> float:
    return float(stats.norm.isf((REPLICATES - ORDER + 1) / REPLICATES / (4.0 * m)))


def certified(n, q, scenario, rng, reps=REPS):
    """The probability that a member of size ``n`` is certified."""
    mu, sd, kappa = scenario
    v_true = sd * sd
    if kappa == 3.0:
        v = v_true * rng.chisquare(n - 1, reps) / (n - 1)
    else:
        var_v = (kappa - 1.0) * v_true**2 / n
        shape, scale = v_true**2 / var_v, var_v / v_true
        v = rng.gamma(shape, scale, reps)
    m = rng.normal(mu, sd / math.sqrt(n), reps)
    se_m = np.sqrt(v / n)
    se_v = np.sqrt((kappa - 1.0) / n) * v
    ok = (np.abs(m) + q * se_m < 0.1) & (v - q * se_v > 0.81) & (v + q * se_v < 1.21)
    return float(np.mean(ok))


def sizes_of(rows, target):
    """Each member's expected size, its run having the units of the most demanding member."""
    need = {}
    for r in rows:
        need[r["run"]] = max(need.get(r["run"], 0.0), target / r["fraction"])
    return np.array([max(r["units"], math.ceil(need[r["run"]])) * r["fraction"] for r in rows])


def evaluate(rows, target, q, scenario, rng):
    n = sizes_of(rows, target)
    keys = np.round(n).astype(int)
    table = {int(k): certified(int(k), q, scenario, rng) for k in np.unique(keys)}
    p = np.array([table[int(k)] for k in keys])
    per_cell: dict = {}
    for r, pi in zip(rows, p, strict=True):
        per_cell.setdefault(r["op"], []).append(pi)
    cell = np.array([np.prod(v) for v in per_cell.values()])
    return {
        "member_median": float(np.median(p)),
        "member_min": float(np.min(p)),
        "operational_cells": len(cell),
        "operational_cell_median": float(np.median(cell)),
        "operational_cell_min": float(np.min(cell)),
        "operational_fraction_at_0.90": float(np.mean(cell >= 0.90)),
        "expected_cells_permitted": float(np.sum(cell)),
        "whole_family": float(np.exp(np.sum(np.log(np.maximum(p, 1e-300))))),
    }


def cost(rows, target):
    """The processor-hours of the old-grid repricing for the priced runs at this target."""
    measured, all_rows = wr._load()
    run_of = {r["run"] for r in rows}
    fraction = {}
    for r in rows:
        fraction[r["run"]] = min(fraction.get(r["run"], 1.0), r["fraction"])
    total = measured["a06"]["cpu_hours"]
    seen = set()
    for r in all_rows:
        run = r["run"]
        if run in seen:
            continue
        seen.add(run)
        per_unit = measured[wr._section_of(run)]["cpu_seconds_per_unit"] / 3600.0
        units = r["units"]
        if run in run_of:
            units = max(units, math.ceil(target / fraction[run]))
        total += units * per_unit
    return total


def check():
    """The formula's ``q`` against a direct studentized max-t bootstrap, Gaussian pulls."""
    rng = np.random.default_rng(20261108)
    out = []
    for m, n, boots in ((50, 2000, 2000), (200, 2000, 2000)):
        y = rng.normal(0.0, 1.0, (m, n))
        mean = y.mean(axis=1)
        var = y.var(axis=1)
        roots = np.zeros(boots)
        for b in range(boots):
            w = rng.integers(0, n, n)
            s = y[:, w]
            mb = s.mean(axis=1)
            res = (s.T - mb).T
            v = np.mean(res**2, axis=1)
            se_m = np.sqrt(v / n)
            u = res**2 - v[:, None]
            se_v = np.sqrt(np.sum(u**2, axis=1)) / n
            t = np.concatenate([np.abs(mb - mean) / se_m, np.abs(v - var) / se_v])
            roots[b] = t.max()
        q = float(np.sort(roots)[ORDER - 1])
        out.append({"members": m, "n": n, "direct_q": q, "formula_q": critical(m)})
        print(out[-1], flush=True)
    return out


def main():
    rng = np.random.default_rng(20261108)
    rows = members()
    m = len(rows)
    q = critical(m)
    doc = {
        "label": "development sizing under the max-t; it decides nothing",
        "method_status": "not_validated",
        "floor": FLOOR,
        "family_members": m,
        "operational_cells": len({r["op"] for r in rows}),
        "runs": len({r["run"] for r in rows}),
        "critical_value": q,
        "sizes": {},
    }
    if sys.argv[1:] == ["check"]:
        doc["bootstrap_check"] = check()
    for target in TARGETS:
        block = {"cpu_hours_old_grid": cost(rows, target)}
        for name, scenario in SCENARIOS.items():
            block[name] = evaluate(rows, target, q, scenario, rng)
        doc["sizes"][str(target)] = block
        c = block["calibrated"]
        print(
            target,
            round(block["cpu_hours_old_grid"]),
            *(round(c[k], 3) for k in ("member_median", "member_min")),
            round(c["operational_cell_median"], 3),
            round(c["operational_fraction_at_0.90"], 3),
            round(c["whole_family"], 4),
            flush=True,
        )
    (HERE / "sizing.json").write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n", "utf-8")
    print({k: doc[k] for k in ("family_members", "operational_cells", "runs", "critical_value")})


if __name__ == "__main__":
    main()
