"""The objective choice of point (A) of map Amendment 6: the noise bands of revision 3, 4.2 against
the replicas of revision 4, 1 (the maintainer's item 4 of 2026-10-18).

For each option, the expected fraction of holdout rounds that end INCONCLUSIVE for a reason of the
option (too few usable replicas, or the hidden-year noise undetermined), computed **only from
metadata and synthetic training data**: the generator builds every year of a case, but the
planner and the geometric evaluation use no hidden-year flux and no hidden-year timestamps; they
use the train part and cadences rebuilt from the sector metadata (``SectorInfo.t_start``,
``t_end``) on the generator's 2-minute grid (``synthetic.sector_times``), as the cadence and orbit
layout of a TESS sector are known in advance. A replica or a transit window is **usable** only if
its box and its baseline bands are covered by at least ``min_window_coverage`` of their expected
cadences on that grid (the rule of ``holdout._measure``; added after the Codex check of the first
run, which counted registered replicas and predicted windows).

Options (map Amendment 6, point (A)):

- **O1, revision 3, 4.2 as written:** noise bands at the train ephemeris' phases 0.25 and 0.75,
  half-width 2 T14 (train), minus the measurement spans of the transit and control windows; their
  A1 support is the cadences not masked by the hidden detrending (windows and replicas out to
  ``baseline_inner``), split into segments at masks and gaps, in bins of ``n_T`` per sector.
- **O2, the replicas' baseline bands:** the same A1 support taken from the baseline bands of the
  accepted replicas (between ``baseline_inner`` and ``L / 2``).
- **O3, the replicas avoid the noise bands:** O1's bands, and the replica rule with the added
  condition that a replica's span does not overlap a noise band.

A round is INCONCLUSIVE for the option when its replicas are fewer than ``R_min`` (20), or when
no hidden sector has at least ``B_min`` (20) bins at ``n_T`` in the option's support, or when
fewer than ``min_predicted_transits`` transit windows lie in sectors with that support. The
replica rule is that of revision 4, 1 (phases 0.25, 0.75, then the dyadic levels down to 1/64;
the span inside one sector; no overlap with a window's measurement span or an accepted replica;
the masked time fraction of the sector at most 0.5), with ``L = 2 max(baseline_outer)`` over the
round's transit windows and the replica mask ``max(baseline_inner)`` (declared readings of the
calculation).

The lot: the development structure (``population_v2.population_cases``) under the new prefix
``refute-v0.2.1-option-a-geometry`` (never used), planets of the bands near and measurable, every
tenth index (25 per noise model and band, 100 light curves). Each round's train part goes through
``holdout.plan_round`` with the corrections switch on (the code of the commit that runs this).

Run from the worktree root with the virtual environment's Python (threads 0 to 7, at most 6
workers): ``docs/validation/v0.2.1/reopen/calc/option_a_geometry.py``. Writes
``option-a-geometry.json`` next to this file.
"""

from __future__ import annotations

import importlib.util
import json
import math
import os
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
PREFIX = "refute-v0.2.1-option-a-geometry"
WORKERS = 6
R_MIN = 20
B_MIN = 20
GAP_SPLIT = 5.0
PHASE_LEVELS = (4, 8, 16, 32, 64)


def _harness():
    spec = importlib.util.spec_from_file_location(
        "population_v2", ROOT / "docs" / "validation" / "v0.2.1" / "population" / "population_v2.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["population_v2"] = module  # its dataclasses look their module up
    spec.loader.exec_module(module)
    return module


def lot(pv2) -> list[dict]:
    cases = pv2.population_cases(f"confirm:{PREFIX}")
    return [
        c
        for c in cases
        if c["class"] == "planet" and c["band"] in ("near", "measurable") and c["index"] % 10 == 0
    ]


def phases() -> list[float]:
    out = []
    for d in PHASE_LEVELS:
        out += [j / d for j in range(1, d, 2)]
    return out


def _union_length(intervals, lo, hi) -> float:
    pieces = sorted((max(lo, a), min(hi, b)) for a, b in intervals if min(hi, b) > max(lo, a))
    total, cur_a, cur_b = 0.0, None, None
    for a, b in pieces:
        if cur_b is None or a > cur_b:
            if cur_b is not None:
                total += cur_b - cur_a
            cur_a, cur_b = a, b
        else:
            cur_b = max(cur_b, b)
    if cur_b is not None:
        total += cur_b - cur_a
    return total


def _overlaps(a0, a1, intervals) -> bool:
    return any(a0 < b1 and b0 < a1 for b0, b1 in intervals)


def replicas(ephemeris, windows, spans, avoid=()):
    """The accepted replica centers of revision 4, 1 (with ``avoid`` intervals for O3)."""
    transit = [w for w in windows if w.kind == "transit"]
    if not transit:
        return [], 0.0, 0.0
    half_l = max(w.baseline_outer for w in transit)
    inner = max(w.baseline_inner for w in transit)
    spans_meas = [(w.t_pred - w.baseline_outer, w.t_pred + w.baseline_outer) for w in windows]
    masks = {
        i: [(w.t_pred - w.baseline_inner, w.t_pred + w.baseline_inner) for w in windows]
        for i in range(len(spans))
    }
    accepted: list[float] = []
    for phase in phases():
        centers = []
        for i, (lo, hi) in enumerate(spans):
            m0 = math.ceil((lo - ephemeris.t_ref) / ephemeris.period - phase)
            m1 = math.floor((hi - ephemeris.t_ref) / ephemeris.period - phase)
            centers += [
                (ephemeris.t_ref + (m + phase) * ephemeris.period, i) for m in range(m0, m1 + 1)
            ]
        for c, i in sorted(centers):
            lo, hi = spans[i]
            a0, a1 = c - half_l, c + half_l
            if a0 < lo or a1 > hi:
                continue
            if _overlaps(a0, a1, spans_meas):
                continue
            if _overlaps(a0, a1, [(r - half_l, r + half_l) for r in accepted]):
                continue
            if _overlaps(a0, a1, avoid):
                continue
            trial = masks[i] + [(c - inner, c + inner)]
            if _union_length(trial, lo, hi) / (hi - lo) > 0.5:
                continue
            masks[i] = trial
            accepted.append(c)
    return sorted(accepted), half_l, inner


def noise_bands(ephemeris, windows, spans, t14):
    """Revision 3, 4.2: bands at phases 0.25 and 0.75, half-width 2 T14, minus the windows'
    measurement spans; clipped to the sector spans."""
    cut = sorted((w.t_pred - w.baseline_outer, w.t_pred + w.baseline_outer) for w in windows)
    out = []
    for phase in (0.25, 0.75):
        for lo, hi in spans:
            m0 = math.ceil((lo - ephemeris.t_ref) / ephemeris.period - phase) - 1
            m1 = math.floor((hi - ephemeris.t_ref) / ephemeris.period - phase) + 1
            for m in range(m0, m1 + 1):
                c = ephemeris.t_ref + (m + phase) * ephemeris.period
                pieces = [(max(lo, c - 2 * t14), min(hi, c + 2 * t14))]
                for b0, b1 in cut:
                    nxt = []
                    for a0, a1 in pieces:
                        if b1 <= a0 or b0 >= a1:
                            nxt.append((a0, a1))
                            continue
                        if a0 < b0:
                            nxt.append((a0, b0))
                        if b1 < a1:
                            nxt.append((b1, a1))
                    pieces = nxt
                out += [(a0, a1) for a0, a1 in pieces if a1 > a0]
    return out


def bins_per_sector(times_by_sector, support, masked, n, cadence):
    """Complete bins of ``n`` cadences in the support, unmasked, split at masks and gaps."""
    out = {}
    for sector, t in times_by_sector.items():
        keep = np.zeros(t.size, bool)
        for a0, a1 in support:
            keep |= (t >= a0) & (t <= a1)
        for a0, a1 in masked:
            keep &= ~((t >= a0) & (t <= a1))
        count, run = 0, 0
        prev = None
        for i in range(t.size):
            if not keep[i]:
                count += run // n
                run, prev = 0, None
                continue
            if prev is not None and t[i] - t[prev] > GAP_SPLIT * cadence:
                count += run // n
                run = 0
            run += 1
            prev = i
        count += run // n
        out[sector] = count
    return out


def evaluate(windows_info, times_by_sector, n_t, cadence, min_windows, coverage, option):
    ephemeris, windows, spans, t14 = windows_info
    sector_of_span = list(times_by_sector)
    bands = noise_bands(ephemeris, windows, spans, t14)
    avoid = bands if option == "O3" else ()
    reps, half_l, inner = replicas(ephemeris, windows, spans, avoid)
    masked = [(w.t_pred - w.baseline_inner, w.t_pred + w.baseline_inner) for w in windows]
    masked += [(c - inner, c + inner) for c in reps]
    if option in ("O1", "O3"):
        support = bands
    else:
        support = [(c - half_l, c - inner) for c in reps] + [(c + inner, c + half_l) for c in reps]
    nbins = bins_per_sector(times_by_sector, support, masked, n_t, cadence)
    ok = {s for s, b in nbins.items() if b >= B_MIN}
    # Usable = the coverage rule of holdout._measure on the rebuilt cadences (Codex check):
    # box cadences >= min_window_coverage of 2 half_width / cadence, and the same for the
    # baseline bands (inner < |dt| <= outer).
    all_t = np.concatenate(list(times_by_sector.values()))
    transit = [w for w in windows if w.kind == "transit"]
    box_half = max(w.half_width for w in transit)

    def covered(center, half, inner_, outer_):
        dt = np.abs(all_t - center)
        n_box = int(np.count_nonzero(dt <= half))
        n_base = int(np.count_nonzero((dt > inner_) & (dt <= outer_)))
        return (
            n_box >= coverage * 2.0 * half / cadence
            and n_base >= coverage * 2.0 * (outer_ - inner_) / cadence
        )

    usable_reps = [c for c in reps if covered(c, box_half, inner, half_l)]
    transit_ok = 0
    for w in transit:
        if not covered(w.t_pred, w.half_width, w.baseline_inner, w.baseline_outer):
            continue
        for k, (lo, hi) in enumerate(spans):
            if lo <= w.t_pred <= hi and sector_of_span[k] in ok:
                transit_ok += 1
    reasons = []
    if len(usable_reps) < R_MIN:
        reasons.append("replicas_below_r_min")
    if not ok:
        reasons.append("hidden_noise_undetermined")
    elif transit_ok < min_windows:
        reasons.append("too_few_windows_with_noise")
    return {
        "n_replicas_registered": len(reps),
        "n_replicas": len(usable_reps),
        "n_transit_windows_usable": transit_ok,
        "bins": {str(s): b for s, b in nbins.items()},
        "inconclusive": bool(reasons),
        "reasons": reasons,
    }


def run_case(case: dict) -> dict:
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    pv2 = _harness()
    from refute.packs.tess import synthetic
    from refute.packs.tess.holdout import plan_round
    from refute.packs.tess.params import TessTestPlan

    plan_dict = synthetic.fast_plan_dict()
    plan_dict["gauntlet"] = {"corrections": {"enabled": True}}
    plan = TessTestPlan.model_validate(plan_dict)
    cadence = plan.data.exptime_seconds / 86400.0
    params = plan.gauntlet.holdout_by_year
    try:
        blob, _ = pv2.build_case(case)
    except Exception as exc:  # noqa: BLE001 - a case the generator cannot build is recorded
        return {"id": case["id"], "noise": case["noise"], "error": repr(exc), "rounds": []}
    meta, arrays = pv2.deserialize(blob)
    data = pv2.parts_to_data(meta, arrays)
    rounds = []
    for year in data.lc.years:
        hidden_sectors = [s for s in data.sectors if s.year == year]
        spans = [(s.t_start, s.t_end) for s in hidden_sectors]
        train = data.lc.select(data.lc.year != year)
        prepared = plan_round(train, spans, year, plan)
        row = {"year": int(year)}
        if prepared.decided is not None:
            row["decided_before"] = prepared.decided.message
            rounds.append(row)
            continue
        times_by_sector = {}
        for s in hidden_sectors:
            t = synthetic.sector_times(s.t_start)
            times_by_sector[s.sector] = t[t <= s.t_end + 1e-9]
        n_t = max(1, int(round(prepared.train.duration / cadence)))
        info = (prepared.ephemeris, prepared.windows, spans, prepared.train.duration)
        for option in ("O1", "O2", "O3"):
            row[option] = evaluate(
                info,
                times_by_sector,
                n_t,
                cadence,
                params.min_predicted_transits,
                params.min_window_coverage,
                option,
            )
        rows_sigma = [
            (w.half_width - prepared.train.duration / 2) / params.timing_sigma
            for w in prepared.windows
            if w.kind == "transit"
        ]
        row["max_sigma_t_over_t14"] = (
            max(rows_sigma) / prepared.train.duration if rows_sigma else None
        )
        rounds.append(row)
    return {
        "id": case["id"],
        "noise": case["noise"],
        "mechanism": case["mechanism"],
        "rounds": rounds,
    }


def summarize(results: list[dict]) -> dict:
    out = {}
    reached = [r for res in results for r in res["rounds"] if "O1" in r]
    total = [r for res in results for r in res["rounds"]]
    for option in ("O1", "O2", "O3"):
        inc = sum(1 for r in reached if r[option]["inconclusive"])
        reasons: dict[str, int] = {}
        for r in reached:
            for why in r[option]["reasons"]:
                reasons[why] = reasons.get(why, 0) + 1
        out[option] = {
            "rounds_reaching_the_geometry": len(reached),
            "inconclusive": inc,
            "fraction_inconclusive": inc / len(reached) if reached else None,
            "reasons": reasons,
            "median_replicas": float(np.median([r[option]["n_replicas"] for r in reached]))
            if reached
            else None,
        }
    out["rounds_total"] = len(total)
    out["rounds_decided_before"] = len(total) - len(reached)
    out["cases"] = len(results)
    out["cases_not_built"] = sum(1 for r in results if "error" in r)
    return out


def main() -> None:
    pv2 = _harness()
    cases = lot(pv2)
    with ProcessPoolExecutor(max_workers=WORKERS) as pool:
        results = list(pool.map(run_case, cases))
    record = {
        "prefix": PREFIX,
        "n_cases": len(cases),
        "summary": summarize(results),
        "cases": results,
        "platform": sys.platform,
        "numpy": np.__version__,
    }
    (HERE / "option-a-geometry.json").write_text(
        json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )
    print(json.dumps(record["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
