"""v0.5.2 stage 1, E2: the matched estimator's candidates (design: e2-design.md). Development seeds
only.

Usage (heavy; from the project root):
``scripts/launch_affinity.ps1 -Script docs/validation/v0.5.2/stage1/e2_matched.py
-Arguments 'run[,<max units>]' -Log .cache/v052/e2/run``; then
``.venv/Scripts/python.exe <this file> summarize`` writes ``e2-matched.json``.
"""

from __future__ import annotations

import hashlib
import json
import math
import platform
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "docs/validation/v0.5.1/acceptance"))
sys.path.insert(0, str(HERE))
import a0 as runner  # noqa: E402
import runlib  # noqa: E402
import series  # noqa: E402

NOISES = ("white", "correlated", "long")
SNRS = (12, 30)
PERIODS = (3.3, 7.0)
SHORT_PERIOD = 1.5
SHORT_CURVES = 20
SHAPES = ((0.12, 0.1), (0.20, 0.2))
NULL_CURVES = 40
ALT_CURVES = 30
BASELINE = "built"
ESTIMATORS = ("built", "built_masked", "candidate_shape", "crossfit", "pseudo_ephemeris", "box")
ELIGIBLE = tuple(e for e in ESTIMATORS if e != BASELINE)
SIMPLER_ORDER = ("box", "candidate_shape", "built_masked", "crossfit", "pseudo_ephemeris")
J = 4
K = 20
REPEAT_CURVES = 5
BOOTSTRAPS = 2000
PROBE_UNITS = 44
# the number of processes: a measured choice, as in E3 (its design, third correction)
WORKERS = 4
CAP_HOURS = 3.0
BATCH = 88
SIGMA = 1000e-6
CELL_MIN_AVAILABILITY = 0.70
CELL_MAX_ABS_MEAN = 0.4
CELL_SD = (0.70, 1.35)
POOLED_MIN_AVAILABILITY = 0.80
POOLED_MAX_ABS_MEAN = 0.1
POOLED_SD = (0.9, 1.1)
ALT_MIN_POWER = 0.80
TIE = 0.02
PSEUDO_MAX_LOG_RATIO = 0.20
PSEUDO_MAX_SECONDS = 5.0
WILSON = 1.959964


def fingerprint() -> tuple[str, dict]:
    import astropy
    import scipy

    from refute.core.codehash import compute_code_hash

    def sha(path):
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()

    acc = ROOT / "docs/validation/v0.5.1/acceptance"
    doc = {
        "design": sha(HERE / "e2-design.md"),
        "script": sha(Path(__file__)),
        "runlib": sha(HERE / "runlib.py"),
        "e1_result": sha(HERE / "e1-mask.json"),
        "runner_a0": sha(acc / "a0.py"),
        "series": sha(acc / "series.py"),
        "common": sha(acc / "common.py"),
        "code_hash": compute_code_hash(ROOT).sha256,
        "plan": hashlib.sha256(
            json.dumps(runner._plan().model_dump(mode="json"), sort_keys=True).encode()
        ).hexdigest(),
        "constants": [NOISES, SNRS, PERIODS, SHAPES, NULL_CURVES, ALT_CURVES, ESTIMATORS, J, K],
        "python": platform.python_version(),
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "astropy": astropy.__version__,
    }
    return hashlib.sha256(json.dumps(doc, sort_keys=True).encode()).hexdigest()[:16], doc


def dev_seed(kind, noise, snr, period, shape, i):
    text = f"refute-v052-dev:e2:{kind}:{noise}:{snr}:{period}:{shape}:{i}"
    return int(hashlib.sha256(text.encode()).hexdigest()[:16], 16)


def _curve(seed, kind, noise, snr, period, shape):
    from refute.packs.tess import synthetic as syn

    duration, ingress = SHAPES[shape]
    base, _ = runner.c.noise_curve(seed, "white", 2)
    t = base.time
    rng = np.random.default_rng([seed, 11])
    t0 = float(t.min() + rng.uniform(0.0, period))
    dt = np.abs(np.mod(t - t0 + 0.5 * period, period) - 0.5 * period)
    n_in = int(np.count_nonzero(dt <= duration / 2.0))
    depth = snr * SIGMA / math.sqrt(max(n_in, 1))

    def model(time_):
        full = syn.trapezoid(time_, period, t0, depth, duration, ingress)
        if kind != "alt":
            return 1.0 - full
        epoch = np.round((time_ - t0) / period).astype(int)
        return 1.0 - np.where(epoch % 2 != 0, full, 0.0)

    lc, _ = runner.c.noise_curve(seed, noise, 2, model=model)
    return lc, period, duration, depth


_ORIGINALS = {}


def _keep():
    from refute.packs.tess import a0
    from refute.packs.tess import battery_v51 as v51

    _ORIGINALS.setdefault("box_measure", a0.box_measure)
    _ORIGINALS.setdefault("matched_measure", a0.matched_measure)
    _ORIGINALS.setdefault("fit_shape", v51._fit_shape)
    return _ORIGINALS


def _combs(raw, grid_flat, cand, plan):
    """The arm-D detrendings: real masks plus every J-th pseudo-window; returned with h."""
    from refute.packs.tess import pipeline as pl

    half = plan.detrend.transit_mask_half_width_durations * cand.duration
    real = pl.transit_mask(raw.time, cand.period, cand.t0, half)
    h = runner._h(cand, plan)
    grid = {}
    for s in np.unique(grid_flat.sector):
        ts = grid_flat.time[grid_flat.sector == s]
        grid[int(s)] = (float(ts.min()), int(math.floor((ts.max() - ts.min()) / (2.0 * h))) + 1)
    flats = []
    for j in range(J):
        mask = real.copy()
        for first, n in grid.values():
            for g in range(n):
                if g % J == j:
                    mask |= np.abs(raw.time - (first + h + 2.0 * g * h)) <= half
        flats.append(pl.detrend(raw, plan.detrend, mask=mask))
    return flats, h


def _dispatcher(grid_flat, h, measures):
    from refute.packs.tess import a0

    time_, sector = grid_flat.time, grid_flat.sector
    firsts = {int(s): float(time_[sector == s].min()) for s in np.unique(sector)}

    def measure(centre):
        s = a0.sector_of(time_, sector, centre)
        return measures[int(round((centre - firsts[s] - h) / (2.0 * h))) % J](centre)

    return measure


def _patched_matched(flat, flats, h):
    """A ``matched_measure`` whose pseudo-window measure reads the comb's series."""
    original = _keep()["matched_measure"]

    def wrapper(time_, flux, flux_err, shape, half_span, expected_in, min_coverage):
        _, info = original(time_, flux, flux_err, shape, half_span, expected_in, min_coverage)
        measures = [
            original(f.time, f.flux, f.flux_err, shape, half_span, expected_in, min_coverage)[0]
            for f in flats
        ]
        return _dispatcher(flat, h, measures), info

    return wrapper


def _odd_even(flat, cand, plan, seed):
    """The production statistic: its difference, and the variance of that difference taken from
    the production call itself (the first ``group_variance`` of ``check_odd_even``)."""
    from refute.core.verdict import TestStatus
    from refute.packs.tess import a0
    from refute.packs.tess import battery_v51 as v51

    original = a0.group_variance
    variances = []

    def spy(*args, **kwargs):
        value = original(*args, **kwargs)
        variances.append(value)
        return value

    a0.group_variance = spy
    try:
        r = v51.check_odd_even(
            flat, cand, plan.gauntlet, plan.stronger, runner.c.CADENCE, False, seed
        )
    finally:
        a0.group_variance = original
    if r.status is TestStatus.INCONCLUSIVE or not variances or not variances[0]:
        return None
    m = r.metrics
    return [(m["depth_odd_ppm"] - m["depth_even_ppm"]) * 1e-6, math.sqrt(variances[0])]


def _crossfit(flat, flats, h, cand, plan):
    """Each parity measured with the shape fitted on the other; the errors from each template's
    pseudo-windows on the comb's series; the two group variances summed (an assumption)."""
    from refute.packs.tess import a0
    from refute.packs.tess import battery_v51 as v51
    from refute.packs.tess.events import event_epochs

    ev = plan.gauntlet.events
    cadence = runner.c.CADENCE
    time_, flux = flat.time, flat.flux
    epoch = np.round((time_ - cand.t0) / cand.period).astype(int)
    original_fit = _keep()["fit_shape"]
    original_matched = _keep()["matched_measure"]
    templates = {}
    for parity in (0, 1):
        sel = (epoch % 2) == parity
        _, duration, ingress, shift = original_fit(time_[sel], flux[sel], cand)
        templates[parity] = (v51._unit_trapezoid(duration, ingress), duration, shift)
    groups = {}
    for parity in (0, 1):
        shape, duration, shift = templates[1 - parity]
        t0 = cand.t0 + shift
        expected_in = duration / cadence
        _, info = original_matched(
            time_, flux, flat.flux_err, shape, duration / 2.0, expected_in, ev.min_coverage
        )
        comb_measures = [
            original_matched(
                f.time, f.flux, f.flux_err, shape, duration / 2.0, expected_in, ev.min_coverage
            )[0]
            for f in flats
        ]
        windows = a0.pseudo_windows(
            time_,
            flat.sector,
            cand.period,
            t0,
            cand.duration,
            ev.baseline_outer_durations,
            ev.min_coverage,
            _dispatcher(flat, h, comb_measures),
            exclude_phase_half=False,
        )
        rows, metas, cache = [], [], {}
        for e in event_epochs(time_, cand.period, t0, 0.0):
            if (int(e) % 2) != parity:
                continue
            centre = t0 + e * cand.period
            got = info(centre)
            if got is None:
                continue
            amp, cov, inf = got
            meta = a0.event_meta(time_, flat.sector, centre, cov, ev.min_coverage)
            if meta is None:
                continue
            key = (meta.sector, meta.stratum)
            if key not in cache:
                cache[key] = a0.stratum_error(windows, *key)[0]
            if cache[key] is None:
                continue
            rows.append((amp, max(1.0 / math.sqrt(inf), cache[key])))
            metas.append(meta)
        if len(rows) < 2:
            return None
        w = np.array([1.0 / r[1] ** 2 for r in rows])
        w = w / w.sum()
        pooled = {s: a0.shortcut(windows, s, 7 + s) for s in {m.sector for m in metas}}
        var = a0.group_variance(w, [r[1] for r in rows], metas, windows, h, pooled)
        if var is None:
            return None
        groups[parity] = (float(np.sum(w * np.array([r[0] for r in rows]))), var)
    return [groups[1][0] - groups[0][0], math.sqrt(groups[1][1] + groups[0][1])]


def _diff_at(flat, cand, plan, t0):
    """The information-weighted matched odd-minus-even difference at epoch ``t0``."""
    from dataclasses import replace

    from refute.packs.tess import a0
    from refute.packs.tess import battery_v51 as v51
    from refute.packs.tess.events import event_epochs

    ev = plan.gauntlet.events
    trial = replace(cand, t0=t0)
    _, duration, ingress, shift = _keep()["fit_shape"](flat.time, flat.flux, trial)
    shape = v51._unit_trapezoid(duration, ingress)
    _, info = _keep()["matched_measure"](
        flat.time,
        flat.flux,
        flat.flux_err,
        shape,
        duration / 2.0,
        duration / runner.c.CADENCE,
        ev.min_coverage,
    )
    groups = {0: [], 1: []}
    for e in event_epochs(flat.time, cand.period, t0 + shift, 0.0):
        got = info(t0 + shift + e * cand.period)
        if got is not None and a0.stratum(got[1], ev.min_coverage) is not None:
            groups[int(e) % 2].append((got[0], got[2]))
    if len(groups[0]) < 2 or len(groups[1]) < 2:
        return None

    def mean(rows):
        w = np.array([r[1] for r in rows])
        return float(np.sum(w * np.array([r[0] for r in rows])) / np.sum(w))

    return mean(groups[1]) - mean(groups[0])


def _phases_sd(flat, cand, plan, seed, salt):
    rng = np.random.default_rng([seed, 21, salt])
    guard = 3.0 * cand.duration / cand.period
    values, tries = [], 0
    while len(values) < K and tries < 10 * K:
        tries += 1
        phase = float(rng.uniform(0.0, 1.0))
        if min(abs(phase - c) for c in (0.0, 0.5, 1.0)) < guard:
            continue
        v = _diff_at(flat, cand, plan, cand.t0 + phase * cand.period)
        if v is not None:
            values.append(v)
    return float(np.std(values, ddof=1)) if len(values) == K else None


def _pseudo(flat, cand, plan, seed, repeat):
    """(the estimate, the repeat pair or None, the ordinary CPU, the second set's CPU). The ordinary
    evaluation is the real difference and one phase set; the second set is validation overhead."""
    started = time.process_time()
    real = _diff_at(flat, cand, plan, cand.t0)
    first = None if real is None else _phases_sd(flat, cand, plan, seed, 0)
    ordinary = time.process_time() - started
    started = time.process_time()
    second = None
    if repeat and real is not None:
        second = _phases_sd(flat, cand, plan, seed, 1)
    overhead = time.process_time() - started
    estimate = [real, first] if real is not None and first is not None else None
    pair = [first, second] if repeat else None
    return estimate, pair, ordinary, overhead


def _box(flat, cand, plan):
    _, measured, windows, _ = runner._measured(flat, cand, plan)
    stats, _ = runner._box_groups(flat, cand, measured, windows, plan)
    value = stats.get("box_diff")
    return list(value) if value is not None and value[1] is not None else None


def _timed(results, timing, name, fn):
    started = time.process_time()
    results[name] = fn()
    timing[name] = time.process_time() - started


def unit(arg):
    from refute.packs.tess import a0, power
    from refute.packs.tess import battery_v51 as v51
    from refute.packs.tess import pipeline as pl
    from refute.packs.tess.search import finalize_candidate

    kind, noise, snr, period, shape, i, seed, fp = arg
    started = time.process_time()
    keep = _keep()
    plan = runner._plan()
    lc, p, duration, depth = _curve(seed, kind, noise, snr, period, shape)
    base = pl.detrend(lc, plan.detrend)
    final = finalize_candidate(base, p, duration, plan.search, 10.0, np.full(base.time.size, SIGMA))
    flat = series.pipeline_flat(lc, final, plan)
    flats, h = _combs(lc, flat, final, plan)
    seed_oe = power.candidate_seed("odd_even", final)
    rec = {
        "unit": _uid((kind, noise, snr, period, shape, i)),
        "fingerprint": fp,
        "kind": kind,
        "noise": noise,
        "snr": snr,
        "period": period,
        "shape": shape,
        "i": i,
        "depth": depth,
        "estimators": {},
        "timing": {},
    }
    results, timing = rec["estimators"], rec["timing"]
    _timed(results, timing, "built", lambda: _odd_even(flat, final, plan, seed_oe))
    try:
        a0.matched_measure = _patched_matched(flat, flats, h)
        _timed(results, timing, "built_masked", lambda: _odd_even(flat, final, plan, seed_oe))
        v51._fit_shape = lambda _t, _f, c: (max(c.depth, 1e-6), c.duration, 0.1, 0.0)
        _timed(results, timing, "candidate_shape", lambda: _odd_even(flat, final, plan, seed_oe))
    finally:
        a0.matched_measure = keep["matched_measure"]
        v51._fit_shape = keep["fit_shape"]
    _timed(results, timing, "crossfit", lambda: _crossfit(flat, flats, h, final, plan))
    repeat = kind == "null" and i < REPEAT_CURVES
    estimate, pair, ordinary, overhead = _pseudo(flat, final, plan, seed, repeat)
    results["pseudo_ephemeris"] = estimate
    rec["pseudo_repeat"] = pair
    timing["pseudo_ephemeris"] = ordinary
    rec["pseudo_repeat_overhead_seconds"] = overhead
    ev = plan.gauntlet.events
    measures = [
        keep["box_measure"](
            f.time,
            f.flux,
            final.duration,
            ev.baseline_gap_durations,
            ev.baseline_outer_durations,
            ev.min_coverage,
            runner.c.CADENCE,
        )
        for f in flats
    ]
    try:
        comb = _dispatcher(flat, h, measures)
        a0.box_measure = lambda *_a, **_k: comb
        _timed(results, timing, "box", lambda: _box(flat, final, plan))
    finally:
        a0.box_measure = keep["box_measure"]
    rec["cpu_seconds"] = time.process_time() - started
    return rec


def schedule():
    out = []

    def add(kind, noise, snr, period, shape, i):
        out.append(
            (kind, noise, snr, period, shape, i, dev_seed(kind, noise, snr, period, shape, i))
        )

    for i in range(max(NULL_CURVES, ALT_CURVES)):
        for noise in NOISES:
            for snr in SNRS:
                for period in PERIODS:
                    if i < NULL_CURVES:
                        for shape in range(len(SHAPES)):
                            add("null", noise, snr, period, shape, i)
                    if i < ALT_CURVES:
                        add("alt", noise, snr, period, 0, i)
            if i < SHORT_CURVES:
                add("short", noise, 12, SHORT_PERIOD, 0, i)
    return out


def _uid(a):
    return ":".join(str(x) for x in a[:6])


def _paths():
    fp, doc = fingerprint()
    return fp, doc, ROOT / ".cache/v052/e2" / fp


def _warm():
    """One per worker, before any unit: the imports and the plan a unit needs."""
    from refute.packs.tess import a0, battery_v51, power  # noqa: F401
    from refute.packs.tess import pipeline as _pl  # noqa: F401
    from refute.packs.tess.search import finalize_candidate  # noqa: F401

    runner._plan()
    runner.c.noise_curve(0, "white", 1)


def run(limit=None):
    fp, doc, out = _paths()
    out.mkdir(parents=True, exist_ok=True)
    (out / "manifest.json").write_text(json.dumps(doc, indent=1, sort_keys=True), "utf-8")
    runlib.bounded_run(
        unit,
        _uid,
        schedule(),
        fp,
        out,
        CAP_HOURS,
        PROBE_UNITS,
        BATCH,
        WORKERS,
        limit,
        initializer=_warm,
    )


# --- the summary --------------------------------------------------------------------------------


def wilson(k, n):
    if n == 0:
        return None
    z = WILSON
    p = k / n
    den = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return {"k": k, "n": n, "rate": p, "lo": max(0.0, centre - half), "hi": min(1.0, centre + half)}


def _number(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(float(x))


def _valid(v):
    if not (isinstance(v, list) and len(v) == 2 and _number(v[0]) and _number(v[1])):
        return False
    return float(v[1]) > 0.0 and math.isfinite(float(v[0]) / float(v[1]))


def _pull(v):
    return float(v[0]) / float(v[1]) if _valid(v) else None


def _block(pulls, rng):
    """Over scheduled curves (None for unavailable): availability, the pull's mean and standard
    deviation, with bootstrap intervals over the curves."""
    n = len(pulls)
    good = np.array([p for p in pulls if p is not None], dtype=float)
    out = {"n": n, "available": int(good.size), "availability": good.size / n if n else None}
    if n:
        flags = np.array([p is not None for p in pulls], dtype=float)
        idx = rng.integers(0, n, size=(BOOTSTRAPS, n))
        out["availability_ci"] = [
            float(np.percentile(flags[idx].mean(axis=1), 2.5)),
            float(np.percentile(flags[idx].mean(axis=1), 97.5)),
        ]
    if good.size < 3:
        out.update(mean=None, sd=None, mean_ci=None, sd_ci=None)
        return out
    idx = rng.integers(0, good.size, size=(BOOTSTRAPS, good.size))
    boots = good[idx]
    means, sds = boots.mean(axis=1), boots.std(axis=1, ddof=1)
    out.update(
        mean=float(good.mean()),
        sd=float(good.std(ddof=1)),
        mean_ci=[float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))],
        sd_ci=[float(np.percentile(sds, 2.5)), float(np.percentile(sds, 97.5))],
    )
    return out


def _read_any(path):
    """The record lines as parsed, whatever they are: ``_validate`` names the malformed ones."""
    rows = []
    if path.exists():
        for line in path.read_text("utf-8").splitlines():
            if line.strip():
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    rows.append(None)
    return rows


def _validate(raw_recs, fp):
    reasons: list[str] = []
    recs = [r for r in raw_recs if isinstance(r, dict) and isinstance(r.get("unit"), str)]
    if len(recs) != len(raw_recs):
        reasons.append(f"{len(raw_recs) - len(recs)} records are malformed")
    units = [r.get("unit") for r in recs]
    if len(units) != len(set(units)):
        reasons.append("a unit is recorded twice")
    if any(r.get("fingerprint") != fp for r in recs):
        reasons.append("a record of another fingerprint")
    by = {_uid(a): a for a in schedule()}
    if set(units) != set(by):
        reasons.append(f"schedule incomplete or unexpected: {len(set(by) - set(units))} missing")
    for r in recs:
        unit_id = r.get("unit")
        if "estimators" not in r:
            reasons.append(f"{unit_id}: the unit errored")
            continue
        a = by.get(unit_id)
        fields = ("kind", "noise", "snr", "period", "shape", "i")
        if a is None or any(k not in r for k in fields) or tuple(r[k] for k in fields) != a[:6]:
            reasons.append(f"{unit_id}: metadata mismatch")
            continue
        if not isinstance(r["estimators"], dict) or set(r["estimators"]) != set(ESTIMATORS):
            reasons.append(f"{unit_id}: estimator schema")
            continue
        for name, value in r["estimators"].items():
            if value is not None and not _valid(value):
                reasons.append(f"{unit_id} {name}: a malformed result")
        cpu = r.get("cpu_seconds")
        if not _number(cpu) or cpu < 0:
            reasons.append(f"{unit_id}: invalid CPU accounting")
        depth = r.get("depth")
        if not _number(depth) or depth <= 0:
            reasons.append(f"{unit_id}: an invalid depth")
        timing = r.get("timing")
        if not isinstance(timing, dict) or set(timing) != set(ESTIMATORS):
            reasons.append(f"{unit_id}: the timing schema")
        elif not all(_number(v) and v >= 0 for v in timing.values()):
            reasons.append(f"{unit_id}: invalid timing")
        repeat = r.get("pseudo_repeat")
        if repeat is not None and not (
            isinstance(repeat, list)
            and len(repeat) == 2
            and all(x is None or (_number(x) and x > 0) for x in repeat)
        ):
            reasons.append(f"{unit_id}: an invalid repeat")
        due = r["kind"] == "null" and r["i"] < REPEAT_CURVES
        if due != (repeat is not None):
            reasons.append(f"{unit_id}: the repeat is not where it is due")
    return reasons


def _cell_key(r):
    return f"{r['noise']}/snr{r['snr']}/P{r['period']}/shape{r['shape']}"


def _null_tables(null, rng):
    pooled, cells = {}, {}
    for est in ESTIMATORS:
        pooled[est] = {}
        cells[est] = {}
        for noise in NOISES:
            rs = [r for r in null if r["noise"] == noise]
            pooled[est][noise] = _block([_pull(r["estimators"][est]) for r in rs], rng)
        keys = sorted({_cell_key(r) for r in null})
        for key in keys:
            rs = [r for r in null if _cell_key(r) == key]
            cells[est][key] = _block([_pull(r["estimators"][est]) for r in rs], rng)
    return pooled, cells


def _alt_tables(alt):
    out = {}
    for est in ESTIMATORS:
        out[est] = {}
        keys = sorted({f"{r['noise']}/snr{r['snr']}/P{r['period']}" for r in alt})
        for key in keys:
            rs = [r for r in alt if f"{r['noise']}/snr{r['snr']}/P{r['period']}" == key]
            k = sum(
                1
                for r in rs
                if _valid(r["estimators"][est]) and abs(_pull(r["estimators"][est])) >= 3
            )
            out[est][key] = wilson(k, len(rs))
    return out


def _qualify(est, pooled, cells, alt, reasons):
    """(qualifies, details): the frozen rule for one eligible estimator."""
    detail = {"cells_failing": [], "pooled_failing": [], "alternative_failing": []}
    for key, b in cells[est].items():
        if b["mean"] is None or b["sd"] is None or b["availability"] is None:
            reasons.append(f"{est} {key}: an undefined required cell")
            detail["cells_failing"].append(key)
            continue
        good = (
            b["availability"] >= CELL_MIN_AVAILABILITY
            and abs(b["mean"]) <= CELL_MAX_ABS_MEAN
            and CELL_SD[0] <= b["sd"] <= CELL_SD[1]
        )
        if not good:
            detail["cells_failing"].append(key)
    for noise, b in pooled[est].items():
        if b["mean"] is None or b["sd"] is None:
            detail["pooled_failing"].append(noise)
            continue
        good = (
            b["availability"] >= POOLED_MIN_AVAILABILITY
            and abs(b["mean"]) <= POOLED_MAX_ABS_MEAN
            and POOLED_SD[0] <= b["sd"] <= POOLED_SD[1]
        )
        if not good:
            detail["pooled_failing"].append(noise)
    for key, w in alt[est].items():
        if w is None or w["rate"] < ALT_MIN_POWER:
            detail["alternative_failing"].append(key)
    detail["qualifies_pooled_only"] = bool(detail["cells_failing"]) and not detail["pooled_failing"]
    qualifies = not (
        detail["cells_failing"] or detail["pooled_failing"] or detail["alternative_failing"]
    )
    return qualifies, detail


def summarize():
    fp, doc, out_dir = _paths()
    raw_recs = _read_any(out_dir / "records.jsonl")
    recs = [r for r in raw_recs if isinstance(r, dict) and isinstance(r.get("unit"), str)]
    reasons = _validate(raw_recs, fp)
    state = runlib.read_state(out_dir)
    if state is None or state["state"] != "complete":
        reasons.append(f"the run did not complete under its cap: {state}")
    rng = np.random.default_rng(20261108)
    out = {
        "label": "development experiment E2 (v0.5.2 stage 1); it decides nothing about any target",
        "method_status": "not_validated",
        "restriction": "periods 3.3 and 7.0 d; the short-period question is carried forward",
        "fingerprint": fp,
        "manifest": doc,
        "units": sum(1 for r in recs if "estimators" in r),
        "cpu_hours": round(
            sum(float(r["cpu_seconds"]) for r in recs if _number(r.get("cpu_seconds"))) / 3600.0, 3
        ),
    }
    choice = None
    if not reasons:
        null = [r for r in recs if r["kind"] == "null"]
        alt = [r for r in recs if r["kind"] == "alt"]
        short = [r for r in recs if r["kind"] == "short"]
        pooled, cells = _null_tables(null, rng)
        alternatives = _alt_tables(alt)
        out["null_pooled"] = pooled
        out["null_cells"] = cells
        out["alternative"] = alternatives
        out["short_period_availability"] = {
            est: wilson(sum(1 for r in short if _valid(r["estimators"][est])), len(short))
            for est in ESTIMATORS
        }
        out["cpu_seconds_per_curve"] = {
            est: float(np.mean([r["timing"][est] for r in recs])) for est in ESTIMATORS
        }
        due = [r["pseudo_repeat"] for r in recs if r.get("pseudo_repeat") is not None]
        complete = [p for p in due if p[0] is not None and p[1] is not None]
        ratio = (
            float(np.mean([abs(math.log(a) - math.log(b)) for a, b in complete]))
            if due and len(complete) == len(due)
            else None
        )
        cost = out["cpu_seconds_per_curve"]["pseudo_ephemeris"]
        affordable = (
            None
            if ratio is None
            else bool(ratio <= PSEUDO_MAX_LOG_RATIO and cost <= PSEUDO_MAX_SECONDS)
        )
        out["pseudo_ephemeris_affordability"] = {
            "repeats_due": len(due),
            "repeats_complete": len(complete),
            "mean_abs_log_ratio": ratio,
            "ordinary_cpu_seconds_per_curve": cost,
            "affordable": affordable,
            "note": "null when a due repeat is missing: the precision is then not established",
        }
        details = {}
        qualifies = {}
        for est in ELIGIBLE:
            qualifies[est], details[est] = _qualify(est, pooled, cells, alternatives, reasons)
        if affordable is not True:
            qualifies["pseudo_ephemeris"] = False
            details["pseudo_ephemeris"]["not_affordable_or_not_established"] = True
        power_ = {}
        for est in ESTIMATORS:
            rates = [w["rate"] for w in alternatives[est].values() if w is not None]
            power_[est] = float(np.mean(rates)) if rates else None
        out["qualifies"] = qualifies
        out["qualification_detail"] = details
        out["mean_power"] = power_
        if not reasons:
            eligible = [e for e in ELIGIBLE if qualifies[e] and power_[e] is not None]
            if eligible:
                best = max(power_[e] for e in eligible)
                near = [e for e in eligible if power_[e] >= best - TIE]
                choice = min(near, key=SIMPLER_ORDER.index)
    out["decision"] = {
        "state": "NOT ESTABLISHED" if reasons else "EVALUATED",
        "reasons": reasons[:40],
        "choice": choice,
        "no_candidate_qualifies": None if reasons else choice is None,
    }
    (HERE / "e2-matched.json").write_text(
        json.dumps(out, indent=1, sort_keys=True, allow_nan=False) + "\n", "utf-8"
    )
    print(
        json.dumps(
            {k: out.get(k) for k in ("decision", "qualifies", "mean_power", "cpu_hours")}, indent=1
        )
    )
    for est in ESTIMATORS:
        if "null_pooled" in out:
            print(
                est,
                {
                    n: (
                        b["mean"] and round(b["mean"], 3),
                        b["sd"] and round(b["sd"], 3),
                        round(b["availability"], 3),
                    )
                    for n, b in out["null_pooled"][est].items()
                },
            )


if __name__ == "__main__":
    if sys.argv[1:2] == ["run"]:
        run(int(sys.argv[2]) if len(sys.argv) > 2 else None)
    elif sys.argv[1:] == ["summarize"]:
        summarize()
    else:
        raise SystemExit("usage: e2_matched.py run [max units] | summarize")
