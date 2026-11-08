"""v0.5.2 stage 1, E1: the detrending mask (design: e1-design.md). Development seeds only.

Usage (heavy; from the project root):
``scripts/launch_affinity.ps1 -Script docs/validation/v0.5.2/stage1/e1_mask.py
-Arguments 'run[,<max units>]' -Log .cache/v052/e1/run``; then
``.venv/Scripts/python.exe <this file> summarize`` writes ``e1-mask.json``. Records go to a folder
named after the experiment's fingerprint, and a record of another fingerprint is refused.
"""

from __future__ import annotations

import hashlib
import json
import math
import platform
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "docs/validation/v0.5.1/acceptance"))
import a0 as runner  # noqa: E402

TRIALS = 300
REFERENCE_CURVES = 20
NOISES = ("white", "correlated", "long", "correlated_trend")
KINDS = ("full", "partial")
ARMS = ("A", "B", "C", "D")
MASKED_ARMS = ("C", "D")
J = 4
GROUP = ("box_odd", "box_even", "box_diff")
SECTORS = 2
BOOTSTRAPS = 500
RMS_LIMIT = 0.10
ERROR_RATIO_LIMIT = 0.02
AVAILABILITY_DISAGREEMENT_LIMIT = 0.01
MIN_CONTRIBUTING_CURVES = 100
MAX_UNDEFINED_REPLICATES = 0.01


def fingerprint() -> tuple[str, dict]:
    """The frozen experiment's identity: design, scripts, code hash, plan, constants, versions."""
    from refute.core.codehash import compute_code_hash

    def sha(path):
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()

    acc = ROOT / "docs/validation/v0.5.1/acceptance"
    doc = {
        "design": sha(HERE / "e1-design.md"),
        "script": sha(Path(__file__)),
        "runner_a0": sha(acc / "a0.py"),
        "runner_common": sha(acc / "common.py"),
        "code_hash": compute_code_hash(ROOT).sha256,
        "plan": hashlib.sha256(
            json.dumps(runner._plan().model_dump(mode="json"), sort_keys=True).encode()
        ).hexdigest(),
        "constants": [TRIALS, REFERENCE_CURVES, NOISES, KINDS, J, SECTORS, BOOTSTRAPS],
        "python": platform.python_version(),
        "numpy": np.__version__,
    }
    text = json.dumps(doc, sort_keys=True)
    return hashlib.sha256(text.encode()).hexdigest()[:16], doc


def dev_seed(noise: str, kind: str, i: int) -> int:
    text = f"refute-v052-dev:e1:{noise}:{kind}:{i}"
    return int(hashlib.sha256(text.encode()).hexdigest()[:16], 16)


_ORIGINAL = {}


def original_box():
    from refute.packs.tess import a0

    return _ORIGINAL.setdefault("box", a0.box_measure)


def _box_on(flat, cand, plan):
    ev = plan.gauntlet.events
    return original_box()(
        flat.time,
        flat.flux,
        cand.duration,
        ev.baseline_gap_durations,
        ev.baseline_outer_durations,
        ev.min_coverage,
        runner.c.CADENCE,
    )


def _grid(flat, h):
    out = {}
    for s in np.unique(flat.sector):
        ts = flat.time[flat.sector == s]
        out[int(s)] = (float(ts.min()), int(math.floor((ts.max() - ts.min()) / (2.0 * h))) + 1)
    return out


def _comb_measures(raw, grid, h, half, base_mask, cand, plan):
    from refute.packs.tess import pipeline as pl

    measures = []
    for j in range(J):
        mask = base_mask.copy()
        for first, n in grid.values():
            for g in range(n):
                if g % J == j:
                    mask |= np.abs(raw.time - (first + h + 2.0 * g * h)) <= half
        measures.append(_box_on(pl.detrend(raw, plan.detrend, mask=mask), cand, plan))
    return measures


def _dispatch(grid_flat, h, measures):
    from refute.packs.tess import a0

    time_, sector = grid_flat.time, grid_flat.sector
    firsts = {int(s): float(time_[sector == s].min()) for s in np.unique(sector)}

    def measure(centre):
        s = a0.sector_of(time_, sector, centre)
        return measures[int(round((centre - firsts[s] - h) / (2.0 * h))) % J](centre)

    return measure


def _arm(flat, cand, plan, group):
    measured_events, measured, windows, _ = runner._measured(flat, cand, plan)
    metas = runner._metas(flat, cand, measured, plan)
    out = {
        "events": [
            [int(ep), m.stratum, float(d), float(e)]
            for ep, m, d, e in zip(
                measured.epochs, metas, measured.depths, measured.errors, strict=True
            )
        ],
        "n_events": len(measured_events),
        "not_measured": int(measured.dropped.get("a0_not_measured", 0)),
    }
    if group:
        stats, _ = runner._box_groups(flat, cand, measured, windows, plan)
        out["group"] = {k: list(v) for k, v in stats.items()}
    return out


def _windows(flat, cand, plan, measure):
    from refute.packs.tess import a0

    ev = plan.gauntlet.events
    return a0.pseudo_windows(
        flat.time,
        flat.sector,
        cand.period,
        cand.t0,
        cand.duration,
        ev.baseline_outer_durations,
        ev.min_coverage,
        measure,
        exclude_phase_half=False,
    )


def _errors(windows):
    from refute.packs.tess import a0

    keys = sorted({(w.sector, w.stratum) for w in windows})
    return {f"{s}:{st}": a0.stratum_error(windows, s, st)[0] for s, st in keys}


def _reference(raw, flat, cand, plan, h, half, base_mask, comb_measure):
    """The comb against one window masked at a time, as A0 builds its windows and errors."""
    from refute.packs.tess import a0
    from refute.packs.tess import pipeline as pl

    time_, sector = flat.time, flat.sector

    def alone(centre):
        s = a0.sector_of(time_, sector, centre)
        sel = raw.sector == s
        part = raw.select(sel)
        mask = base_mask[sel] | (np.abs(part.time - centre) <= half)
        return _box_on(pl.detrend(part, plan.detrend, mask=mask), cand, plan)(centre)

    ref = _windows(flat, cand, plan, alone)
    comb = _windows(flat, cand, plan, comb_measure)
    by_ref = {(w.sector, w.index): w for w in ref}
    by_comb = {(w.sector, w.index): w for w in comb}
    common = sorted(set(by_ref) & set(by_comb))
    return {
        "pairs": [[by_comb[k].value, by_ref[k].value] for k in common],
        "only_reference": len(set(by_ref) - set(by_comb)),
        "only_comb": len(set(by_comb) - set(by_ref)),
        "errors_reference": _errors(ref),
        "errors_comb": _errors(comb),
    }


def unit(arg):
    from refute.packs.tess import a0
    from refute.packs.tess import pipeline as pl

    noise, kind, i, seed, fp = arg
    started = time.process_time()
    plan = runner._plan()
    lc, _ = runner.c.noise_curve(seed, noise, SECTORS)
    cand = runner._candidate(lc.time, np.random.default_rng([seed, 1]))
    raw = runner._apply_kind(lc, cand, plan, kind)
    half = plan.detrend.transit_mask_half_width_durations * cand.duration
    real = pl.transit_mask(raw.time, cand.period, cand.t0, half)
    none = np.zeros(raw.time.size, dtype=bool)
    h = runner._h(cand, plan)
    flat_a = pl.detrend(raw, plan.detrend, mask=real)
    flat_b = pl.detrend(raw, plan.detrend)
    group = kind == "full"
    rec = {"unit": f"{noise}:{kind}:{i}", "fingerprint": fp, "noise": noise, "kind": kind}
    rec["arms"] = {}
    box = original_box()

    def construction(flat, base):
        measures = _comb_measures(raw, _grid(flat, h), h, half, base, cand, plan)
        return (flat, base, _dispatch(flat, h, measures))

    constructions = {"C": construction(flat_b, none), "D": construction(flat_a, real)}
    try:
        rec["arms"]["A"] = _arm(flat_a, cand, plan, group)
        rec["arms"]["B"] = _arm(flat_b, cand, plan, group)
        for arm, (flat, _, measure) in constructions.items():
            a0.box_measure = lambda *_a, measure=measure, **_k: measure
            rec["arms"][arm] = _arm(flat, cand, plan, group)
    finally:
        a0.box_measure = box
    if i < REFERENCE_CURVES:
        rec["reference"] = {
            arm: _reference(raw, flat, cand, plan, h, half, base, measure)
            for arm, (flat, base, measure) in constructions.items()
        }
    rec["cpu_seconds"] = time.process_time() - started
    return rec


def schedule():
    return [(n, k, i, dev_seed(n, k, i)) for i in range(TRIALS) for n in NOISES for k in KINDS]


def _paths():
    fp, doc = fingerprint()
    out = ROOT / ".cache/v052/e1" / fp
    return fp, doc, out, out / "records.jsonl"


def run(limit=None):
    from refute.core.runner import default_workers

    fp, doc, out, records = _paths()
    out.mkdir(parents=True, exist_ok=True)
    (out / "manifest.json").write_text(json.dumps(doc, indent=1, sort_keys=True), "utf-8")
    done = set()
    if records.exists():
        for line in records.read_text("utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                if r.get("fingerprint") != fp:
                    raise SystemExit("a record of another fingerprint: refused")
                done.add(r["unit"])
    todo = [(*a, fp) for a in schedule() if f"{a[0]}:{a[1]}:{a[2]}" not in done]
    if limit is not None:
        todo = todo[:limit]
    with ProcessPoolExecutor(max_workers=default_workers()) as pool:
        futures = {pool.submit(unit, a): a for a in todo}
        with records.open("a", encoding="utf-8") as fh:
            for fut in as_completed(futures):
                a = futures[fut]
                try:
                    rec = fut.result()
                except Exception as exc:  # noqa: BLE001 - recorded, never dropped
                    rec = {"unit": f"{a[0]}:{a[1]}:{a[2]}", "fingerprint": fp, "status": "ERROR",
                           "reason": repr(exc)}  # fmt: skip
                fh.write(json.dumps(rec, sort_keys=True) + "\n")
                fh.flush()


# --- the summary --------------------------------------------------------------------------------


def _sums(rows):
    """Per curve: [count, sum d, sum d^2, sum e^2], rows being (d, e) arrays or empty."""
    return np.array(
        [[len(d), float(np.sum(d)), float(np.sum(d * d)), float(np.sum(e * e))] for d, e in rows]
    )


def _stats(s):
    """NaN where a statistic is undefined (fewer than two events, a non-positive denominator)."""
    n = s[..., 0]
    ok = n >= 2
    with np.errstate(divide="ignore", invalid="ignore"):
        var = np.where(ok, (s[..., 2] - s[..., 1] ** 2 / np.where(ok, n, 2.0)) / (n - 1), np.nan)
        mean_e2 = np.where(ok, s[..., 3] / np.where(ok, n, 2.0), np.nan)
        bias = np.where(ok, s[..., 1] / np.where(ok, n, 2.0), np.nan)
        rho = np.sqrt(np.where(mean_e2 > 0, var / mean_e2, np.nan))
    return {"var_d": var, "mean_e2": mean_e2, "bias": bias, "rho": rho}


def _ci(values):
    """The 95 % percentile interval over the defined replicates; None with too many undefined."""
    values = np.asarray(values, dtype=float)
    good = values[np.isfinite(values)]
    if good.size < (1.0 - MAX_UNDEFINED_REPLICATES) * values.size:
        return None
    return [float(np.percentile(good, 2.5)), float(np.percentile(good, 97.5))]


def _finite(x):
    return float(x) if x is not None and math.isfinite(float(x)) else None


def _clean(node):
    """Undefined quantities as null: the JSON output never holds NaN or infinity."""
    if isinstance(node, dict):
        return {k: _clean(v) for k, v in node.items()}
    if isinstance(node, (list, tuple)):
        return [_clean(v) for v in node]
    if isinstance(node, float) and not math.isfinite(node):
        return None
    return node


def _cell(recs, kind, rng):
    """The per-arm statistics and the paired contrasts against arm A, over whole curves."""
    per_arm = {}
    common = {}
    for arm in ARMS:
        rows, rows_common, rows_a = [], [], []
        for r in recs:
            ev = {e[0]: e for e in r["arms"][arm]["events"] if e[1] == kind}
            ev_a = {e[0]: e for e in r["arms"]["A"]["events"] if e[1] == kind}
            d = np.array([e[2] for e in ev.values()], dtype=float)
            e_ = np.array([e[3] for e in ev.values()], dtype=float)
            rows.append((d, e_))
            shared = sorted(set(ev) & set(ev_a))
            rows_common.append(
                (np.array([ev[k][2] for k in shared], dtype=float),
                 np.array([ev[k][3] for k in shared], dtype=float))
            )  # fmt: skip
            rows_a.append(
                (np.array([ev_a[k][2] for k in shared], dtype=float),
                 np.array([ev_a[k][3] for k in shared], dtype=float))
            )  # fmt: skip
        per_arm[arm] = _sums(rows)
        common[arm] = (_sums(rows_common), _sums(rows_a))
    n_curves = len(recs)
    draws = rng.integers(0, n_curves, size=(BOOTSTRAPS, n_curves))
    out = {}
    base = per_arm["A"].sum(axis=0)
    base_boot = per_arm["A"][draws].sum(axis=1)
    avail = {
        arm: np.array(
            [[len(r["arms"][arm]["events"]), r["arms"][arm]["n_events"]] for r in recs], dtype=float
        )
        for arm in ARMS
    }

    def ratio(a):
        with np.errstate(divide="ignore", invalid="ignore"):
            return np.where(
                a[..., 1] > 0, a[..., 0] / np.where(a[..., 1] > 0, a[..., 1], 1.0), np.nan
            )

    for arm in ARMS:
        total = per_arm[arm].sum(axis=0)
        boot = per_arm[arm][draws].sum(axis=1)
        point, reps = _stats(total), _stats(boot)
        point_a, reps_a = _stats(base), _stats(base_boot)
        block = {
            "events": int(total[0]),
            "contributing_curves": int(np.count_nonzero(per_arm[arm][:, 0] >= 1)),
        }
        for key in ("var_d", "mean_e2", "bias", "rho"):
            block[key] = _finite(point[key])
            block[f"{key}_ci"] = _ci(reps[key])
            block[f"{key}_minus_A"] = _finite(point[key] - point_a[key])
            block[f"{key}_minus_A_ci"] = _ci(reps[key] - reps_a[key])
        a_total, a_boot = avail[arm].sum(axis=0), avail[arm][draws].sum(axis=1)
        r_total, r_boot = ratio(a_total), ratio(a_boot)
        b_total, b_boot = ratio(avail["A"].sum(axis=0)), ratio(avail["A"][draws].sum(axis=1))
        block["availability"] = _finite(r_total)
        block["availability_ci"] = _ci(r_boot)
        block["availability_minus_A"] = _finite(r_total - b_total)
        block["availability_minus_A_ci"] = _ci(r_boot - b_boot)
        same, same_a = common[arm]
        sum_same, sum_same_a = same.sum(axis=0), same_a.sum(axis=0)
        block["common_events"] = int(sum_same[0])
        block["rho_common"] = _finite(_stats(sum_same)["rho"])
        block["rho_A_common"] = _finite(_stats(sum_same_a)["rho"])
        out[arm] = block
    return out


def _reference_summary(recs):
    out = {}
    for arm in MASKED_ARMS:
        for noise in NOISES:
            for kind in KINDS:
                sub = [
                    r["reference"][arm]
                    for r in recs
                    if r["noise"] == noise and r["kind"] == kind and "reference" in r
                ]
                pairs = np.array([p for s in sub for p in s["pairs"]], dtype=float)
                ratios, disagreements, total = [], 0, 0
                for s in sub:
                    keys = set(s["errors_reference"]) | set(s["errors_comb"])
                    for k in keys:
                        total += 1
                        a, b = s["errors_reference"].get(k), s["errors_comb"].get(k)
                        if (a is None) != (b is None):
                            disagreements += 1
                        elif a is not None:
                            ratios.append(abs(b / a - 1.0))
                only = sum(s["only_reference"] + s["only_comb"] for s in sub)
                rms = None
                if pairs.size:
                    difference = float(np.sqrt(np.mean((pairs[:, 0] - pairs[:, 1]) ** 2)))
                    rms = difference / float(np.std(pairs[:, 1], ddof=1))
                error = float(np.mean(ratios)) if ratios else None
                disagree = disagreements / total if total else None
                out[f"{arm}/{noise}/{kind}"] = {
                    "curves": len(sub),
                    "rms_over_reference_sd_pooled": rms,
                    "mean_abs_error_ratio_minus_one": error,
                    "availability_disagreement_fraction": disagree,
                    "windows_in_one_construction_only": only,
                    "established": bool(
                        len(sub) == REFERENCE_CURVES
                        and rms is not None
                        and rms <= RMS_LIMIT
                        and error is not None
                        and error <= ERROR_RATIO_LIMIT
                        and disagree is not None
                        and disagree <= AVAILABILITY_DISAGREEMENT_LIMIT
                    ),
                }
    return out


def summarize():
    fp, doc, _, records = _paths()
    recs = [json.loads(x) for x in records.read_text("utf-8").splitlines() if x.strip()]
    reasons = []
    units = [r["unit"] for r in recs]
    if len(units) != len(set(units)):
        reasons.append("a unit is recorded twice")
    if any(r.get("fingerprint") != fp for r in recs):
        reasons.append("a record of another fingerprint")
    expected = {f"{a[0]}:{a[1]}:{a[2]}" for a in schedule()}
    if set(units) != expected:
        reasons.append(f"schedule incomplete: {len(expected - set(units))} missing")
    bad = [r["unit"] for r in recs if "arms" not in r]
    if bad:
        reasons.append(f"{len(bad)} units errored")
    ok = [r for r in recs if "arms" in r]
    for r in ok:
        for arm in r["arms"].values():
            for e in arm["events"]:
                if not (math.isfinite(e[2]) and math.isfinite(e[3]) and e[3] > 0):
                    reasons.append(f"a non-finite or non-positive input in {r['unit']}")
                    break
    rng = np.random.default_rng(20261108)
    out = {
        "label": "development experiment E1 (v0.5.2 stage 1); it decides nothing about any target",
        "method_status": "not_validated",
        "fingerprint": fp,
        "manifest": doc,
        "units": len(ok),
        "cpu_hours": round(sum(float(r.get("cpu_seconds", 0.0)) for r in ok) / 3600.0, 3),
        "cells": {},
    }
    for noise in NOISES:
        for kind in KINDS:
            sub = [r for r in ok if r["noise"] == noise and r["kind"] == kind]
            if not sub:
                reasons.append(f"no units for {noise}/{kind}")
                continue
            cell = _cell(sub, kind, rng)
            if kind == "full":
                for arm in ARMS:
                    for stat in GROUP:
                        pairs = [
                            r["arms"][arm]["group"][stat]
                            for r in sub
                            if stat in r["arms"][arm].get("group", {})
                        ]
                        pairs = [p for p in pairs if p[1] is not None and p[1] > 0]
                        v = np.array([p[0] / p[1] for p in pairs], dtype=float)
                        cell[arm][stat] = {
                            "n": int(v.size),
                            "pull_mean": float(np.mean(v)) if v.size else None,
                            "pull_sd": float(np.std(v, ddof=1)) if v.size > 1 else None,
                        }
            out["cells"][f"{noise}/{kind}"] = cell
    out["comb_vs_reference"] = _reference_summary(ok)
    established = {
        k: v["established"] for k, v in out["comb_vs_reference"].items()
    }  # fmt: skip
    out["constructions_not_established"] = sorted(k for k, v in established.items() if not v)
    if not all(established.values()):
        reasons.append("comb not established for every construction")
    for key, cell in out["cells"].items():
        for arm in ARMS:
            block = cell[arm]
            if block["contributing_curves"] < MIN_CONTRIBUTING_CURVES:
                reasons.append(f"{key} arm {arm}: fewer than {MIN_CONTRIBUTING_CURVES} curves")
            if block["rho"] is None or block["rho_ci"] is None:
                reasons.append(f"{key} arm {arm}: rho or its interval is undefined")
    pattern = None
    if not reasons:
        pattern = True
        for noise in ("correlated", "long", "correlated_trend"):
            for kind in KINDS:
                d = out["cells"][f"{noise}/{kind}"]["D"]["rho"]
                pattern = pattern and 0.95 <= d <= 1.05
        for kind in KINDS:
            cell = out["cells"][f"white/{kind}"]
            pattern = pattern and abs(cell["D"]["rho"] - cell["A"]["rho"]) <= 0.05
    out["decision"] = {
        "state": "NOT ESTABLISHED" if reasons else "EVALUATED",
        "reasons": reasons[:20],
        "prespecified_development_pattern_observed": pattern,
    }
    out = _clean(out)
    (HERE / "e1-mask.json").write_text(
        json.dumps(out, indent=1, sort_keys=True, allow_nan=False) + "\n", "utf-8"
    )
    print(
        json.dumps({k: out[k] for k in ("decision", "units", "cpu_hours", "fingerprint")}, indent=1)
    )
    print("not established:", out["constructions_not_established"])
    for key, cell in out["cells"].items():
        print(key, " ".join(f"{a}={cell[a]['rho']} {cell[a]['rho_ci']}" for a in ARMS))


if __name__ == "__main__":
    if sys.argv[1:2] == ["run"]:
        run(int(sys.argv[2]) if len(sys.argv) > 2 else None)
    elif sys.argv[1:] == ["summarize"]:
        summarize()
    else:
        raise SystemExit("usage: e1_mask.py run [max units] | summarize")
