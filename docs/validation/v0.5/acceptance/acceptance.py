"""The rate cases of the v0.5 acceptance documents (docs/plans/v0.5-acceptance.md, WP1 to WP4),
run on synthetic data with known truth.

Each case builds a synthetic light curve (and pixel data for WP4) from its seed, measures the
candidate's events at the known ephemeris as the v0.5 pipeline does (detrending with the transits
masked, the red-noise error model), runs the test, attaches its sensitivity block and applies the
engine's rule, and records the status. A case is decided by the binomial band of the acceptance
conventions: "FAILs at least at rate p" means a FAIL count at or above the lower 2.5 % quantile of
Binomial(N, p); "false-failure rate at most a" means a FAIL count at or below the upper 97.5 %
quantile of Binomial(N, a); "never PASS" means zero PASS. Noise: white, and correlated (AR(1),
half the white level, one-hour correlation time).

Seeds: ``--seeds dev`` uses the development rule (smoke runs and the cost projection only);
``--seeds accept`` uses the acceptance rule, unseen until the one acceptance run. The cases and
their parameters are fixed in this file before that run; a failed case is recorded as FAIL and
its test is diagnostic only in v0.5 (docs/plans/v0.5-plan.md, section 3); nothing is retuned.

usage: acceptance.py --seeds dev|accept --trials N --out <json> [--md <md>] [--workers N]
       [--cases name,name]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace
from pathlib import Path

import numpy as np

CADENCE = 2.0 / 1440.0
NOISE_PPM = 1000.0


def seed_of(rule: str, case: str, i: int) -> int:
    prefix = {"dev": "refute-v05-dev", "accept": "refute-v05-accept"}[rule]
    return int(hashlib.sha256(f"{prefix}:{case}:{i}".encode()).hexdigest()[:16], 16)


# --- binomial bands (no scipy) ---------------------------------------------------------------


def _pmf(n: int, k: int, p: float) -> float:
    return math.comb(n, k) * p**k * (1 - p) ** (n - k)


def lower_quantile(n: int, p: float, q: float = 0.025) -> int:
    """The smallest k with P(X <= k) >= q."""
    total = 0.0
    for k in range(n + 1):
        total += _pmf(n, k, p)
        if total >= q:
            return k
    return n


def upper_quantile(n: int, p: float, q: float = 0.975) -> int:
    return lower_quantile(n, p, q)


# --- the shared synthetic machinery ----------------------------------------------------------


def _plan():
    from refute.packs.tess.params import TessTestPlan
    from refute.packs.tess.synthetic import discovery_v05_plan_dict

    return TessTestPlan.model_validate(discovery_v05_plan_dict())


def _curve(spec, seed: int, noise: str, extra=None):
    from refute.packs.tess.synthetic import make_lightcurve
    from refute.packs.tess.types import LightCurveData

    red = {"red_noise_ppm": NOISE_PPM / 2.0, "red_tau_days": 1.0 / 24.0} if noise == "red" else {}
    lc, sectors = make_lightcurve(spec, noise_ppm=NOISE_PPM, seed=seed % (2**31), **red)
    if extra is not None:
        lc = LightCurveData(lc.time, lc.flux - extra(lc.time), lc.flux_err, lc.sector, lc.year)
    return lc, sectors


def _candidate(period, t0, duration, depth):
    from refute.packs.tess.types import Candidate

    return Candidate(period, t0, duration, depth, depth / 20.0, 20.0, 0.0, 10.0, 5)


def _events(lc, cand, plan, phase=0.0):
    from refute.packs.tess.detrend import detrend
    from refute.packs.tess.events import per_event_depths, transit_mask
    from refute.packs.tess.rednoise import event_noise

    half = plan.detrend.transit_mask_half_width_durations * cand.duration
    flat = detrend(lc, plan.detrend, mask=transit_mask(lc.time, cand.period, cand.t0, half))
    noise = event_noise(flat, None, cand.period, cand.t0, cand.duration, plan)
    ev = per_event_depths(
        flat, cand.period, cand.t0, cand.duration, CADENCE, plan.gauntlet.events, phase, None, noise
    )
    return flat, ev


def _final(lc, period, t0, duration, plan):
    """The candidate as the pipeline finalizes it (depth and its error measured), from the
    known period and duration."""
    from refute.packs.tess.detrend import detrend
    from refute.packs.tess.events import per_point_sigma, transit_mask
    from refute.packs.tess.search import finalize_candidate

    half = plan.detrend.transit_mask_half_width_durations * duration
    mask = transit_mask(lc.time, period, t0, half)
    flat = detrend(lc, plan.detrend, mask=mask)
    sigma = per_point_sigma(flat, transit_mask(flat.time, period, t0, half))
    return finalize_candidate(flat, period, duration, plan.search, 10.0, sigma)


def _enforced(result):
    from refute.core.sensitivity import enforce_sensitivity
    from refute.packs.tess.power import TESS_REGISTRY

    (out,) = enforce_sensitivity([result], TESS_REGISTRY)
    return out


def _box(period, t0, duration, depth):
    def f(time):
        dt = np.abs(np.mod(time - t0 + 0.5 * period, period) - 0.5 * period)
        return np.where(dt <= duration / 2.0, depth, 0.0)

    return f


# --- the cases ---------------------------------------------------------------------------------
# Each returns the final status ("PASS", "FAIL", "INCONCLUSIVE") of one trial.

P, T0, DUR = 3.0, 1326.3, 0.1


def odd_even(seed, noise, sub):
    from refute.packs.tess import power
    from refute.packs.tess.gauntlet import check_odd_even
    from refute.packs.tess.synthetic import SignalSpec

    plan = _plan()
    depth = {"a": 1500e-6, "b": 150e-6, "c": 1500e-6}[sub]
    odd = {"a": 0.0, "b": 0.0, "c": 1.0}[sub]
    spec = SignalSpec(P, T0, depth, DUR, ingress_fraction=0.1, odd_depth_factor=odd)
    lc, _ = _curve(spec, seed, noise)
    cand = _candidate(P, T0, DUR, depth)
    _, ev = _events(lc, cand, plan)
    test = check_odd_even(ev, plan.gauntlet.odd_even)
    return _enforced(
        power.attach(test, power.odd_even_blocks(test, depth, plan.stronger))
    ).status.value


def secondary(seed, noise, sub):
    from refute.packs.tess.battery_v5 import check_secondary_two_sided
    from refute.packs.tess.synthetic import SignalSpec

    plan = _plan()
    depth = {"a": 1500e-6, "b": 150e-6, "c": 1500e-6, "bright": 1500e-6}[sub]
    sec = {"a": depth, "b": depth, "c": 0.0, "bright": 0.0}[sub]
    spec = SignalSpec(P, T0, depth, DUR, ingress_fraction=0.1, secondary_depth=sec)
    extra = None
    if sub == "bright":  # a brightening at phase 0.5 of half the depth
        bump = _box(P, T0 + 0.5 * P, DUR, -0.5 * depth)
        extra = bump
    lc, _ = _curve(spec, seed, noise, extra)
    cand = _candidate(P, T0, DUR, depth)
    _, primary = _events(lc, cand, plan, 0.0)
    _, half = _events(lc, cand, plan, 0.5)
    test = check_secondary_two_sided(
        primary, half, plan.gauntlet.secondary_eclipse, plan.stronger, seed
    )
    return _enforced(test).status.value


def single_event(seed, noise, sub):
    from refute.packs.tess.battery_v5 import check_single_event

    plan = _plan()
    n_target = int(sub.split("-")[1])
    span = 54.0
    period = span / n_target
    depth = 1500e-6
    kind = sub.split("-")[0]
    if kind == "equal":
        extra = _box(period, T0, DUR, depth)
    else:  # one dip only, the other windows covered with no dip

        def extra(time):
            return np.where(np.abs(time - (T0 + period)) <= DUR / 2.0, 6 * depth, 0.0)

    lc, _ = _curve(None, seed, noise, extra)
    cand = _candidate(period, T0, DUR, depth)
    _, ev = _events(lc, cand, plan)
    return _enforced(check_single_event(ev, plan.stronger, seed)).status.value


def event_consistency(seed, noise, sub):
    from refute.packs.tess.battery_v5 import check_event_consistency
    from refute.packs.tess.synthetic import SignalSpec

    plan = _plan()
    depth = 2000e-6
    spec = SignalSpec(P, T0, depth, DUR, ingress_fraction=0.1)
    extra = None
    if sub == "a":  # one event deepened by a full depth

        def extra(time):
            return np.where(np.abs(time - (T0 + 2 * P)) <= DUR / 2.0, depth, 0.0)

    lc, _ = _curve(spec, seed, noise, extra)
    cand = _candidate(P, T0, DUR, depth)
    _, ev = _events(lc, cand, plan)
    return _enforced(check_event_consistency(ev, plan.stronger)).status.value


def sinusoid(seed, noise, sub):
    from refute.packs.tess.battery_v5 import check_sinusoid
    from refute.packs.tess.synthetic import SignalSpec

    sp = _plan().stronger
    depth = 2000e-6
    if sub == "a":  # variability at P found as a box: semi-amplitude 2 x depth
        lc, _ = _curve(None, seed, noise, lambda t: -2 * depth * np.cos(2 * np.pi * (t - T0) / P))
    else:  # c: a box-only curve
        lc, _ = _curve(SignalSpec(P, T0, depth, DUR, ingress_fraction=0.1), seed, noise)
    return _enforced(check_sinusoid(lc, _candidate(P, T0, DUR, depth), sp, seed)).status.value


def centroid(seed, noise, sub):
    from refute.packs.tess.centroid_v5 import check_centroid_v5
    from refute.packs.tess.synthetic import (
        PLANET,
        SignalSpec,
        make_aux,
        make_blend_sky,
        make_lightcurve,
        with_sky_jacobian,
    )

    plan = _plan()
    red = {"red_noise_ppm": 150.0, "red_tau_days": 1.0 / 24.0} if noise == "red" else {}
    s = seed % (2**31)
    if sub in ("a", "opposite"):  # an off-target source in 3 sectors (4.1); 4.6 below
        offset = 42.0 if sub == "a" else 63.0  # 2 px; 4.6: 3 px
        spec = SignalSpec(period=5.1, t0=1326.2, depth=0.08, duration=2.4 / 24)
        lc, _, aux = make_blend_sky(spec, (offset, 0.0), seed=s)
        cand = _final(lc, spec.period, spec.t0, spec.duration, plan)
        pixels, sectors = aux.pixels, aux.sectors
        if sub == "opposite":  # 4.6: one sector's offset read twice, in opposite sky frames
            first, second = pixels[0], pixels[1]
            jac = tuple(map(tuple, -np.asarray(first.sky_jacobian)))
            pixels = [first, replace(first, sector=second.sector, sky_jacobian=jac)]
    else:
        from refute.packs.tess.synthetic import THREE_YEARS

        lc, _ = make_lightcurve(PLANET, sector_starts=THREE_YEARS, seed=s, noise_ppm=300.0, **red)
        aux = make_aux(lc, seed=s)
        pixels = [with_sky_jacobian(px) for px in aux.pixels]
        sectors = aux.sectors
        cand = _final(lc, PLANET.period, PLANET.t0, PLANET.duration, plan)
    return _enforced(check_centroid_v5(pixels, sectors, cand, plan, seed)).status.value


def pulls(seed, noise, sub):
    """1.10: the pull of one transit-free group mean at a pseudo ephemeris (no signal)."""
    from refute.packs.tess.events import group_mean

    plan = _plan()
    lc, _ = _curve(None, seed, noise)
    cand = _candidate(P, T0 + 0.37, DUR, 1e-3)
    _, ev = _events(lc, cand, plan)
    if len(ev) < 3:
        return "nan"
    g = group_mean(ev.depths, ev.errors)
    return f"{g.mean / g.error:.6f}"


def period_alias(seed, noise, sub):
    """1.11: a pure sinusoid at the alternative (peak to trough = the depth)."""
    from refute.packs.tess.battery import check_period_alias
    from refute.packs.tess.power import period_alias_blocks

    plan = _plan()
    depth = 3000e-6
    lc, _ = _curve(None, seed, noise, lambda t: -0.5 * depth * np.cos(2 * np.pi * (t - T0) / P))
    cand = _candidate(P, T0, DUR, depth)
    test = check_period_alias(lc, cand, plan)
    block = period_alias_blocks(lc, cand, plan, check_period_alias, seed)["main"]
    return f"{test.status.value}|{int(block['detectable'])}"


# name: (function, sub-case, rule, parameter)
CASES = {
    "1.8-odd_even-a": (odd_even, "a", "fail_at_least", 0.95),
    "1.8-odd_even-b": (odd_even, "b", "never_pass", None),
    "1.8-odd_even-c": (odd_even, "c", "false_fail_at_most", 0.0027),
    "1.8-secondary-a": (secondary, "a", "fail_at_least", 0.95),
    "1.8-secondary-b": (secondary, "b", "never_pass", None),
    "1.8-secondary-c": (secondary, "c", "false_fail_at_most", 0.0027),
    "3.1-brightening": (secondary, "bright", "fail_at_least", 0.95),
    "2.1-single_event-equal-6": (single_event, "equal-6", "false_fail_at_most", 0.0027),
    "2.1-single_event-equal-20": (single_event, "equal-20", "false_fail_at_most", 0.0027),
    "2.2-single_event-one-6": (single_event, "one-6", "fail_at_least", 0.95),
    "2.2-single_event-one-20": (single_event, "one-20", "fail_at_least", 0.95),
    "2.3-event_consistency": (event_consistency, "a", "fail_at_least", 0.95),
    "1.8-event_consistency-c": (event_consistency, "c", "false_fail_at_most", 0.0027),
    "3.3-sinusoid": (sinusoid, "a", "fail_at_least", 0.95),
    "3.8-sinusoid-box": (sinusoid, "c", "false_fail_at_most", 0.0027),
    "4.1-centroid-off-target": (centroid, "a", "fail_at_least", 0.95),
    "4.5-centroid-on-target": (centroid, "c", "false_fail_at_most", 0.0027),
    "4.6-centroid-opposite": (centroid, "opposite", "inconclusive_at_least", 0.95),
    "1.10-pulls": (pulls, "", "pulls", None),
    "1.11-period_alias": (period_alias, "", "alias", 0.9),
}
NOISES = ("white", "red")


def run_task(task):
    name, noise, i, rule = task
    fn, sub, _kind, _param = CASES[name]
    seed = seed_of(rule, f"{name}:{noise}", i)
    started = time.process_time()
    try:
        out = fn(seed, noise, sub)
    except Exception as exc:  # noqa: BLE001 - recorded: an error counts against the case
        out = f"ERROR {type(exc).__name__}: {exc}"
    return {"case": name, "noise": noise, "i": i, "out": out, "cpu": time.process_time() - started}


def decide(name, outs):
    _fn, _sub, kind, param = CASES[name]
    n = len(outs)
    statuses = [o.split("|")[0] for o in outs]
    fails = sum(s == "FAIL" for s in statuses)
    passes = sum(s == "PASS" for s in statuses)
    inconcl = sum(s == "INCONCLUSIVE" for s in statuses)
    errors = sum(o.startswith("ERROR") for o in outs)
    row = {"n": n, "PASS": passes, "FAIL": fails, "INCONCLUSIVE": inconcl, "errors": errors}
    if kind == "fail_at_least":
        need = lower_quantile(n, param)
        row.update(rule=f"FAIL >= {need} (lower 2.5 % of Bin({n}, {param}))", result=fails >= need)
    elif kind == "false_fail_at_most":
        limit = upper_quantile(n, param)
        row.update(
            rule=f"FAIL <= {limit} (upper 97.5 % of Bin({n}, {param}))", result=fails <= limit
        )
    elif kind == "never_pass":
        row.update(rule="no PASS", result=passes == 0 and errors == 0)
    elif kind == "inconclusive_at_least":
        need = lower_quantile(n, param)
        row.update(rule=f"INCONCLUSIVE >= {need}", result=inconcl >= need)
    elif kind == "pulls":
        values = np.array(
            [float(o) for o in outs if o not in ("nan",) and not o.startswith("ERROR")]
        )
        sd, mean = float(np.std(values, ddof=1)), float(np.mean(values))
        row.update(
            pull_sd=sd,
            pull_mean=mean,
            used=int(values.size),
            rule="pull sd in [0.9, 1.1] and |mean| <= 0.1",
            result=bool(0.9 <= sd <= 1.1 and abs(mean) <= 0.1),
        )
    elif kind == "alias":
        detectable = [o for o in outs if o.endswith("|1")]
        fails_d = sum(o.startswith("FAIL") for o in detectable)
        need = lower_quantile(len(detectable), param) if detectable else 0
        row.update(
            detectable=len(detectable),
            fail_when_detectable=fails_d,
            rule=f"FAIL >= {need} among the detectable (lower 2.5 % of Bin(n, {param}))",
            result=bool(detectable) and fails_d >= need,
        )
    row["result"] = "PASS" if row["result"] else "FAIL"
    return row


def main(argv):
    from refute.core.runner import default_workers

    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", choices=("dev", "accept"), required=True)
    ap.add_argument("--trials", type=int, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--md", type=Path)
    ap.add_argument("--workers", type=int, default=default_workers())
    ap.add_argument("--cases", default="")
    args = ap.parse_args(argv)
    if args.out.exists() or (args.md and args.md.exists()):
        print("refusing to overwrite: each run is written once")
        return 1
    names = [c for c in args.cases.split(",") if c] or list(CASES)
    tasks = [
        (name, noise, i, args.seeds)
        for name in names
        for noise in NOISES
        for i in range(args.trials)
    ]
    wall = time.time()
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        rows = list(pool.map(run_task, tasks, chunksize=4))
    cpu = sum(r["cpu"] for r in rows)
    results = {}
    for name in names:
        for noise in NOISES:
            outs = [r["out"] for r in rows if r["case"] == name and r["noise"] == noise]
            results[f"{name}/{noise}"] = decide(name, outs)
    record = {
        "seeds": args.seeds,
        "trials": args.trials,
        "workers": args.workers,
        "processor_seconds": cpu,
        "wall_seconds": time.time() - wall,
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "results": results,
        "trials_detail": rows,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes((json.dumps(record, indent=2, sort_keys=True) + "\n").encode("utf-8"))
    if args.md:
        lines = [
            f"# v0.5 acceptance rate cases ({args.seeds} seeds, "
            f"{args.trials} trials per noise model)",
            "",
            "Synthetic data with known truth (docs/plans/v0.5-acceptance.md). A FAIL here is a "
            "recorded result: the test is diagnostic only in v0.5; nothing is retuned. "
            "`method_status: not_validated`.",
            "",
            f"Processor time: {cpu / 3600:.2f} h over {args.workers} workers. Record: "
            f"`{args.out.name}`.",
            "",
            "| Case / noise | N | PASS | FAIL | INCONCLUSIVE | Errors | Rule | Result |",
            "|---|---|---|---|---|---|---|---|",
        ]
        for key, r in results.items():
            extra = ""
            if "pull_sd" in r:
                extra = f" (sd {r['pull_sd']:.3f}, mean {r['pull_mean']:.3f})"
            if "detectable" in r:
                extra = (
                    f" (detectable {r['detectable']}, FAIL among them {r['fail_when_detectable']})"
                )
            lines.append(
                f"| {key} | {r['n']} | {r['PASS']} | {r['FAIL']} | {r['INCONCLUSIVE']} | "
                f"{r['errors']} | {r['rule']}{extra} | **{r['result']}** |"
            )
        lines.append("")
        args.md.write_bytes("\n".join(lines).encode("utf-8"))
    print(json.dumps({k: v["result"] for k, v in results.items()}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
