"""Item 3 (d) of the maintainer's decision of 2026-11-08 (#208): the diagnosis of A0's two failures.
Development seeds only (``int(SHA-256("refute-v051-dev:strategy-<task>:<...>:<i>")[:16], 16)``);
no acceptance or confirmation seed, nothing in ``src/`` changes (the variants are patches inside
this process). It decides nothing. ``method_status: not_validated``.

Each unit uses the constructions of the A0 acceptance runner (``acceptance/a0.py``: its noise
curves, candidates, the pipeline's flattened series, its statistics and pulls).

**Task ``matched``: the bias of the matched estimators.** A transit-free curve (noise model x full
coverage x 2 sectors, as A0.2), and ``battery_v51.check_odd_even`` with ``_fit_shape`` replaced:
``current``; ``no_lower_bound`` (the depth may be negative, |lower bound| equal to the upper);
``fixed_shape`` (no fit: the candidate's duration, ingress 0.1, no shift); ``shift_only`` (duration
and ingress frozen, shift and depth free, depth >= 0); ``shape_only`` (shift frozen at 0). Same
curve for all. The hypothesis of 2026-11-08: a positivity bound on the trapezoid's depth, whose
mean on a half-normal is sqrt(2 / pi) = 0.80 standard deviations.

**Task ``matched_nomask``** (added after ``matched`` and ``dispersion`` showed the matched
statistics' standard deviation of about 1.5 and the role of the mask): the same curves and seeds,
detrended without the candidate's mask; variants ``current`` and ``fixed_shape``.

**Task ``dispersion``: the 1.10 to 1.21 standard deviation of the box statistics.** The same
transit-free curves (noise x coverage x 2 sectors, as A0.1 and A0.2) with: ``base`` (as A0);
``lag10`` and ``lag20`` (``a0.MAX_LAG`` 10 and 20: the n_eff sum and the group correlations);
``nomask`` (the pipeline's detrending without the candidate's mask, a question this analysis
adds: in the pipeline the real windows are masked while the pseudo-windows that give their error
are not). Each pull's value and error are kept, so that the summary can separate the variance of
the error estimate from the scale: the standard deviation of the values over the root mean square
of the errors, beside the pull's own.

Usage (heavy; from the project root):
``scripts/launch_affinity.ps1 -Script docs/validation/v0.5.1/feasibility/strategy/diagnose.py
-Arguments 'run,<matched|dispersion>[,<max units>]' -Log .cache/v051/item3/<task>``;
``.venv/Scripts/python.exe <this file> summarize <task>`` writes ``diagnose-<task>.json``.
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
OUT = ROOT / ".cache/v051/item3"
sys.path.insert(0, str(ROOT / "docs/validation/v0.5.1/acceptance"))
import a0 as runner  # noqa: E402

TRIALS = 300
MATCHED_NOISES = ("white", "correlated", "long")
MATCHED_VARIANTS = ("current", "no_lower_bound", "fixed_shape", "shift_only", "shape_only")
MATCHED_NOMASK_VARIANTS = ("current", "fixed_shape")
DISPERSION_NOISES = ("white", "correlated", "long", "correlated_trend")
DISPERSION_KINDS = ("full", "partial")
DISPERSION_VARIANTS = ("base", "lag10", "lag20", "nomask")
GROUP_STATS = ("box_odd", "box_even", "box_diff")
SECTORS = 2


def dev_seed(task: str, key: str, i: int) -> int:
    text = f"refute-v051-dev:strategy-{task}:{key}:{i}"
    return int(hashlib.sha256(text.encode()).hexdigest()[:16], 16)


# --- the trapezoid fit, with what is free as a parameter --------------------------------------


def _fit(time_, flux, candidate, lower_depth_factor=0.0, shift_free=True, shape_free=True):
    from scipy.optimize import least_squares

    from refute.packs.tess import synthetic as syn

    p, t0, dur0 = candidate.period, candidate.t0, candidate.duration
    d0 = max(candidate.depth, 1e-6)
    dt = np.mod(time_ - t0 + 0.5 * p, p) - 0.5 * p
    near = np.abs(dt) <= 1.5 * dur0
    tn, yn = time_[near], flux[near]

    def resid(x):
        depth, dur, f, shift = x
        return (1.0 - syn.trapezoid(tn, p, t0 + shift, depth, dur, f)) - yn

    best = None
    for f0 in (0.05, 0.2) if shape_free else (0.1,):
        lo = [lower_depth_factor * d0 * 10.0, 0.3 * dur0, 0.01, -0.3 * dur0]
        hi = [10 * d0, 3.0 * dur0, 0.5, 0.3 * dur0]
        if not shape_free:
            lo[1], hi[1] = dur0 * (1 - 1e-9), dur0 * (1 + 1e-9)
            lo[2], hi[2] = f0 * (1 - 1e-9), f0 * (1 + 1e-9)
        if not shift_free:
            lo[3], hi[3] = -1e-9 * dur0, 1e-9 * dur0
        fit = least_squares(
            resid,
            [d0, dur0, f0, 0.0],
            bounds=(lo, hi),
            x_scale=[d0, 0.1 * dur0, 0.05, 0.05 * dur0],
            max_nfev=300,
        )
        if best is None or fit.cost < best.cost:
            best = fit
    return tuple(float(v) for v in best.x)


def _variant_fit(name):
    if name == "no_lower_bound":
        return lambda t, f, c: _fit(t, f, c, lower_depth_factor=-1.0)
    if name == "shift_only":
        return lambda t, f, c: _fit(t, f, c, shape_free=False)
    if name == "shape_only":
        return lambda t, f, c: _fit(t, f, c, shift_free=False)
    if name == "fixed_shape":
        return lambda t, f, c: (max(c.depth, 1e-6), c.duration, 0.1, 0.0)
    raise ValueError(name)


def unit_matched_nomask(arg):
    """Task ``matched_nomask``: the same curves and seeds as ``matched``, detrended without the
    candidate's mask, so that the real windows and the pseudo-windows are treated alike."""
    return unit_matched(arg, nomask=True)


def unit_matched(arg, nomask=False):
    from refute.packs.tess import battery_v51 as v51
    from refute.packs.tess import pipeline as pl

    noise, i, seed = arg
    started = time.process_time()
    plan = runner._plan()
    lc, _ = runner.c.noise_curve(seed, noise, SECTORS)
    cand = runner._candidate(lc.time, np.random.default_rng([seed, 1]))
    flat = pl.detrend(lc, plan.detrend) if nomask else runner._flat(lc, cand, plan)
    rec = {"task": "matched", "unit": f"{noise}:{i}", "noise": noise, "variants": {}}
    variants = MATCHED_NOMASK_VARIANTS if nomask else MATCHED_VARIANTS
    params, _, _ = v51._fit_shape_status(flat.time, flat.flux, cand)
    rec["fit"] = {
        "depth": params[0],
        "duration_over_candidate": params[1] / cand.duration,
        "ingress": params[2],
        "shift_over_duration": params[3] / cand.duration,
        "depth_at_lower_bound": params[0] <= 1e-12,
    }
    original = v51._fit_shape
    try:
        for name in variants:
            v51._fit_shape = original if name == "current" else _variant_fit(name)
            stats, cls = runner._matched_groups(flat, cand, plan)
            rec["variants"][name] = {
                "class": cls,
                "values": {k: list(v) for k, v in stats.items()},
            }
    finally:
        v51._fit_shape = original
    rec["cpu_seconds"] = time.process_time() - started
    return rec


def _dispersion_one(flat, cand, plan):
    events, measured, windows, details = runner._measured(flat, cand, plan)
    metas = runner._metas(flat, cand, measured, plan)
    stats, _ = runner._box_groups(flat, cand, measured, windows, plan)
    neff = sorted(info["n_eff"] for info in details.values() if info.get("n_eff"))
    return {
        "events": [
            [m.stratum, float(d), float(e)]
            for m, d, e in zip(metas, measured.depths, measured.errors, strict=True)
        ],
        "group": {k: list(v) for k, v in stats.items()},
        "median_n_eff": neff[len(neff) // 2] if neff else None,
        "group_stratum": runner._lowest([m.stratum for m in metas]),
    }


def unit_dispersion(arg):
    from refute.packs.tess import a0
    from refute.packs.tess import pipeline as pl

    noise, kind, i, seed = arg
    started = time.process_time()
    plan = runner._plan()
    lc, _ = runner.c.noise_curve(seed, noise, SECTORS)
    cand = runner._candidate(lc.time, np.random.default_rng([seed, 1]))
    raw = runner._apply_kind(lc, cand, plan, kind)
    flat = runner._flat(raw, cand, plan)
    rec = {
        "task": "dispersion",
        "unit": f"{noise}:{kind}:{i}",
        "noise": noise,
        "kind": kind,
        "variants": {},
    }
    original = a0.MAX_LAG
    try:
        rec["variants"]["base"] = _dispersion_one(flat, cand, plan)
        for name, lag in (("lag10", 10), ("lag20", 20)):
            a0.MAX_LAG = lag
            rec["variants"][name] = _dispersion_one(flat, cand, plan)
        a0.MAX_LAG = original
        nomask = pl.detrend(raw, plan.detrend)
        rec["variants"]["nomask"] = _dispersion_one(nomask, cand, plan)
    finally:
        a0.MAX_LAG = original
    rec["cpu_seconds"] = time.process_time() - started
    return rec


def schedule(task):
    if task in ("matched", "matched_nomask"):
        fn = unit_matched if task == "matched" else unit_matched_nomask
        args = [(n, i, dev_seed("matched", n, i)) for i in range(TRIALS) for n in MATCHED_NOISES]
    else:
        fn = unit_dispersion
        args = [
            (n, k, i, dev_seed("dispersion", n, i))
            for i in range(TRIALS)
            for n in DISPERSION_NOISES
            for k in DISPERSION_KINDS
        ]
    return fn, args


def _unit_id(task, arg):
    return ":".join(str(x) for x in arg[:-1])


def run(task, limit=None):
    from refute.core.runner import default_workers

    path = OUT / task / "records.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    done = set()
    if path.exists():
        done = {json.loads(x)["unit"] for x in path.read_text("utf-8").splitlines() if x.strip()}
    fn, args = schedule(task)
    todo = [a for a in args if _unit_id(task, a) not in done]
    if limit is not None:
        todo = todo[:limit]
    with ProcessPoolExecutor(max_workers=default_workers()) as pool:
        futures = {pool.submit(fn, a): a for a in todo}
        with path.open("a", encoding="utf-8") as fh:
            for fut in as_completed(futures):
                try:
                    rec = fut.result()
                except Exception as exc:  # noqa: BLE001 - recorded, never dropped
                    a = futures[fut]
                    rec = {"unit": _unit_id(task, a), "status": "ERROR", "reason": repr(exc)}
                fh.write(json.dumps(rec, sort_keys=True) + "\n")
                fh.flush()


# --- the summaries ----------------------------------------------------------------------------


def _ratio_block(pairs):
    """Over (value, error): the pull's mean and standard deviation, and the standard deviation of
    the values over the root mean square of the errors (the scale without the error's scatter)."""
    without = sum(1 for p in pairs if p[1] is None or p[1] <= 0)
    pairs = [p for p in pairs if p[1] is not None and p[1] > 0]
    if len(pairs) < 3:
        return {"n": len(pairs), "no_calibrated_error": without}
    v = np.array([p[0] for p in pairs])
    e = np.array([p[1] for p in pairs])
    pull = v / e
    sd = float(np.std(pull, ddof=1))
    return {
        "n": len(pairs),
        "no_calibrated_error": without,
        "pull_mean": float(np.mean(pull)),
        "pull_sd": sd,
        "pull_sd_se": sd / math.sqrt(2.0 * (len(pairs) - 1)),
        "values_sd_over_rms_error": float(np.std(v, ddof=1) / math.sqrt(np.mean(e * e))),
        "mean_value_over_rms_error": float(np.mean(v) / math.sqrt(np.mean(e * e))),
    }


def summarize_matched(recs, variants=MATCHED_VARIANTS):
    ok = [r for r in recs if "variants" in r]
    out = {
        "units": len(ok),
        "errors": sum(1 for r in recs if "variants" not in r),
        "half_normal_mean": math.sqrt(2.0 / math.pi),
    }
    for noise in MATCHED_NOISES:
        sub = [r for r in ok if r["noise"] == noise]
        block = {
            "depth_at_lower_bound_fraction": float(
                np.mean([r["fit"]["depth_at_lower_bound"] for r in sub])
            ),
            "fitted_duration_over_candidate_median": float(
                np.median([r["fit"]["duration_over_candidate"] for r in sub])
            ),
            "fitted_duration_at_0_3_fraction": float(
                np.mean([r["fit"]["duration_over_candidate"] <= 0.301 for r in sub])
            ),
        }
        for name in variants:
            vs = [r["variants"][name] for r in sub]
            inner = {
                "inconclusive": sum(v["class"] is not None for v in vs),
            }
            for stat in ("matched_odd", "matched_even", "matched_diff"):
                inner[stat] = _ratio_block([v["values"][stat] for v in vs if stat in v["values"]])
            sums = [
                (v["values"]["matched_odd"][0] / v["values"]["matched_odd"][1]
                 + v["values"]["matched_even"][0] / v["values"]["matched_even"][1])
                / math.sqrt(2.0)
                for v in vs
                if "matched_odd" in v["values"] and "matched_even" in v["values"]
            ]  # fmt: skip
            inner["odd_even_sum_pull_mean"] = float(np.mean(sums)) if sums else None
            block[name] = inner
        cur = [r for r in sub if "matched_odd" in r["variants"]["current"]["values"]]
        for label, flag in (("at_lower_bound", True), ("above_lower_bound", False)):
            part = [r for r in cur if r["fit"]["depth_at_lower_bound"] == flag]
            pulls = [
                r["variants"]["current"]["values"]["matched_odd"][0]
                / r["variants"]["current"]["values"]["matched_odd"][1]
                for r in part
            ]
            block[f"current_matched_odd_pull_mean_{label}"] = (
                float(np.mean(pulls)) if pulls else None
            )
            block[f"units_{label}"] = len(part)
        out[noise] = block
    return out


def summarize_dispersion(recs):
    ok = [r for r in recs if "variants" in r]
    out = {"units": len(ok), "errors": sum(1 for r in recs if "variants" not in r)}
    for noise in DISPERSION_NOISES:
        for kind in DISPERSION_KINDS:
            sub = [r for r in ok if r["noise"] == noise and r["kind"] == kind]
            block = {}
            for name in DISPERSION_VARIANTS:
                vs = [r["variants"][name] for r in sub]
                inner = {
                    "median_n_eff": float(
                        np.median([v["median_n_eff"] for v in vs if v["median_n_eff"]])
                    )
                }
                events = [(d, e) for v in vs for s, d, e in v["events"] if s == kind]
                inner["per_event"] = _ratio_block(events)
                for stat in GROUP_STATS:
                    inner[stat] = _ratio_block([v["group"][stat] for v in vs if stat in v["group"]])
                block[name] = inner
            nu = block["base"]["median_n_eff"]
            block["t_distribution_sd_at_median_n_eff"] = (
                math.sqrt(nu / (nu - 2.0)) if nu > 2 else None
            )
            out[f"{noise}/{kind}"] = block
    return out


def summarize(task):
    path = OUT / task / "records.jsonl"
    recs = [json.loads(x) for x in path.read_text("utf-8").splitlines() if x.strip()]
    if task == "matched":
        doc = summarize_matched(recs)
    elif task == "matched_nomask":
        doc = summarize_matched(recs, MATCHED_NOMASK_VARIANTS)
    else:
        doc = summarize_dispersion(recs)
    doc["label"] = "development diagnostic (item 3 (d), #208); it decides nothing"
    doc["method_status"] = "not_validated"
    doc["cpu_hours"] = round(sum(float(r.get("cpu_seconds", 0.0)) for r in recs) / 3600.0, 3)
    (HERE / f"diagnose-{task}.json").write_text(
        json.dumps(doc, indent=1, sort_keys=True) + "\n", "utf-8"
    )
    print(json.dumps(doc, indent=1, sort_keys=True))


if __name__ == "__main__":
    if (
        len(sys.argv) >= 3
        and sys.argv[1] == "run"
        and sys.argv[2]
        in (
            "matched",
            "matched_nomask",
            "dispersion",
        )
    ):
        run(sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else None)
    elif len(sys.argv) == 3 and sys.argv[1] == "summarize":
        summarize(sys.argv[2])
    else:
        raise SystemExit("usage: diagnose.py run <task> [max units] | summarize <task>")
