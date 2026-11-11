"""v0.5.3 stage B, B1.3: the recalibration screen of the candidate version 5's errors (#217;
``docs/plans/v0.5.3-stageB1-design.md``, section 3, B1.3). **Development; an exploratory veto,
never a calibration.** ``method_status: not_validated``.

- **E1, E2, E3** (part ``b1_recal_c1``): 450 new C1 planets, family P, seeds
  ``c1.development_seed("P", i)`` for i in 4000 to 4449. On each curve the real transits and their
  bands are dropped, and a pseudo-ephemeris (the found candidate shifted by a quarter period,
  refused if any of its windows meets a true window) gives one null contrast per estimator:
  - E1: the odd-even difference with version 4's weights and E1's variance, only where version 4's
    own ``group_variance`` refuses on that curve (counted by ``RefusalProbe``);
  - E2: the same difference by E2's GLS, where its conditions hold;
  - E3: the residual box after the masked GLS fit, where E3 runs without a fallback.
- **E4** (part ``b1_recal_e4``): the real background of the C2 hosts that passed the v0.4 gate
  (outside T2a's population), up to 8 pseudo-ephemerides per host from a frozen draw.

``summarize`` applies the frozen criteria (mean within ±0.15, standard deviation within
[0.85, 1.15], fraction beyond 3 at most 0.015; Bonferroni over 12 at 0.05; t, chi-square and
Clopper-Pearson intervals as conditional diagnostics; E4 by a host-cluster bootstrap), the
availability rules, and writes the composition used by B1.4 (``b1-composition.json``).
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
import time
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import b1_forecast as bf  # noqa: E402,I001
from b1_forecast import battery_b1, budgeted, ft, fv, ledger_b  # noqa: E402
import b1_data  # noqa: E402

C1_PART, C1_HOURS = "b1_recal_c1", 8.5
E4_PART, E4_HOURS = "b1_recal_e4", 1.5
FIRST, N = 4000, 450
E4_PROPOSALS = 8
E4_SEED_LABEL = "refute-v053-b1:e4-null"
BOOT, BOOT_SEED = 2000, 20261113
ALPHA = 0.05 / 12
TOL_MEAN, TOL_SD, TOL_TAIL = 0.15, (0.85, 1.15), 0.015
MIN_CONTRASTS, MIN_AVAILABILITY, MIN_TAIL_SUPPORT = 30, 0.80, 100
OUT = ledger_b.ROOT / ".cache/v053/stageB/b1"

ONLY = {
    "e1": battery_b1.Config(e1=True, e2=False, e3=False, e4=False),
    "e2": battery_b1.Config(e1=False, e2=True, e3=False, e4=False),
    "e3": battery_b1.Config(e1=False, e2=False, e3=True, e4=False),
    "e4": battery_b1.Config(e1=False, e2=False, e3=False, e4=True),
}


def _windows_meet(c1, outer1, c2, outer2) -> bool:
    """Whether any window of centres ``c1`` (half-width ``outer1``) meets one of ``c2``."""
    if not len(c1) or not len(c2):
        return False
    c2 = np.sort(np.asarray(c2))
    j = np.searchsorted(c2, c1)
    near = [c2[np.clip(j - 1, 0, len(c2) - 1)], c2[np.clip(j, 0, len(c2) - 1)]]
    gap = np.minimum(np.abs(c1 - near[0]), np.abs(c1 - near[1]))
    return bool(np.any(gap < outer1 + outer2))


def _centres(t0, period, tmin, tmax):
    first = math.floor((tmin - t0) / period) - 1
    last = math.ceil((tmax - t0) / period) + 1
    return t0 + period * np.arange(first, last + 1)


def _outer(duration, ev) -> float:
    return duration / 2.0 + ev.baseline_outer_durations * duration


def null_curve(i: int) -> dict:
    """One C1 curve's null contrasts for E1, E2 and E3."""
    from refute.packs.tess import a0, a0_v4, power
    from refute.packs.tess import battery_v52 as v52
    from refute.packs.tess.calib05 import c1
    from refute.packs.tess.detrend import detrend
    from refute.packs.tess.events import per_event_depths
    from refute.packs.tess.pipeline import global_prewhitening
    from refute.packs.tess.rednoise_fast import event_noise
    from refute.packs.tess.search import search_period

    started = time.process_time()
    rec: dict = {"index": i}
    try:
        data, truth = c1.generate("P", c1.development_seed("P", i))
    except c1.GenerationFailedError as exc:
        return {**rec, "status": "GENERATION_FAILURE", "reason": str(exc)}
    p04, _, p4 = fv.plans()
    battery_b1.check_active(None)
    flat = detrend(data.lc, p04.detrend)
    _, searched = global_prewhitening(data, p04, flat)
    cand = search_period(searched, p04.search).candidate
    if cand is None:
        return {**rec, "status": "OK", "unavailable": "no search candidate"}
    gp, sp = p4.gauntlet, p4.stronger
    ev, cadence = gp.events, p4.data.exptime_seconds / 86400.0
    t = data.lc.time
    true_dur = truth.get("duration_days") or cand.duration
    true_c = _centres(truth["t0_btjd"], truth["period_days"], t.min(), t.max())
    keep = np.ones(t.size, dtype=bool)
    for c in true_c:
        keep &= np.abs(t - c) > _outer(true_dur, ev)
    pseudo = replace(cand, t0=cand.t0 + cand.period / 4.0)
    pseudo_c = _centres(pseudo.t0, pseudo.period, t.min(), t.max())
    if _windows_meet(pseudo_c, _outer(pseudo.duration, ev), true_c, _outer(true_dur, ev)):
        return {**rec, "status": "OK", "unavailable": "the pseudo-ephemeris meets a true window"}
    lc = data.lc.select(keep)
    data2 = replace(data, lc=lc)
    flat2 = detrend(lc, p04.detrend)
    pw2, _ = global_prewhitening(data2, p04, flat2)
    rec["dropped_cadences"] = int((~keep).sum())
    # --- the A0 odd_even path of pipeline_v52, at the pseudo-ephemeris ---
    choice = v52.choose_sectors(lc.time, lc.sector, pseudo, ev, cadence, False)
    rec["refused"] = choice.refused
    if choice.refused is None:
        components = pw2.components if pw2 is not None and pw2.components else None
        prepared = a0_v4.prepare(lc, pseudo, p4, components)
        cflat = prepared.flat.select(np.isin(prepared.flat.sector, choice.chosen))
        noise = event_noise(cflat, None, pseudo.period, pseudo.t0, pseudo.duration, p4)
        evs = per_event_depths(
            cflat, pseudo.period, pseudo.t0, pseudo.duration, cadence, ev, 0.0, None, noise
        )
        measure = a0_v4.comb_measure(
            prepared.preprocess, prepared.raw.time, cflat, pseudo.duration, prepared.half, ev,
            cadence,
        )  # fmt: skip
        measured, windows, _ = a0_v4.empirical_events(cflat, pseudo, evs, ev, cadence, measure)
        contributing = {a0.sector_of(cflat.time, cflat.sector, c) for c in measured.centers}
        rec["contributing"] = len(contributing)
        if len(contributing) in v52.GRID_SECTORS:
            seed = power.candidate_seed("odd_even", pseudo)
            args = (cflat, measured, windows, pseudo, gp, sp, cadence, False, seed)
            rec["odd_even_called"] = True
            with ContrastProbe() as probe:
                r4 = v52.check_odd_even(*args)
            rec["v4_contrast_refused"] = probe.contrast_refused
            rec["v4_odd_even"] = r4.status.value
            rec["odd_even_runs"] = r4.metrics.get("inconclusive_class") != "not_enough_data"
            rec["e2_eligible"] = True
            if probe.contrast_refused:
                try:
                    with Only("e1") as v:
                        r1 = v52.check_odd_even(*args)
                    rec["e1"] = _signed_v4(r1)
                    rec["e1_counts"], rec["e1_activation"] = v.counts, v.activation
                except Exception as exc:  # noqa: BLE001 - kept per estimator (Codex, round 2)
                    rec["e1_error"] = repr(exc)
            try:
                with Only("e2") as v:
                    r2 = v52.check_odd_even(*args)
                m = r2.metrics
                if v.counts.get("e2.gls") and m.get("gls_difference_err_ppm"):
                    rec["e2"] = m["gls_difference_ppm"] / m["gls_difference_err_ppm"]
                rec["e2_counts"], rec["e2_activation"] = v.counts, v.activation
            except Exception as exc:  # noqa: BLE001 - kept per estimator (Codex, round 2)
                rec["e2_error"] = repr(exc)
    # --- E3: the sinusoid's residual box at the pseudo-ephemeris ---
    rec["sinusoid_called"] = True
    try:
        with Only("e3") as v:
            r3 = v52.check_sinusoid(
                lc, pseudo, sp, p4.v051, ev, cadence, p4.v052.sinusoid_fail_allowed,
                power.candidate_seed("sinusoid", pseudo),
            )  # fmt: skip
        m = r3.metrics
        if v.counts.get("e3.gls") and m.get("box_depth_after_model_err_ppm"):
            rec["e3"] = m["box_depth_after_model_ppm"] / m["box_depth_after_model_err_ppm"]
        rec["e3_counts"], rec["e3_activation"] = v.counts, v.activation
    except Exception as exc:  # noqa: BLE001 - kept per estimator (Codex, round 2)
        rec["e3_error"] = repr(exc)
    rec["status"] = "OK"
    rec["cpu_seconds"] = time.process_time() - started
    return rec


class ContrastProbe:
    """Version 4's ``check_odd_even`` calls ``a0.group_variance`` first for the odd-even contrast,
    then for each group's error (metrics only). Only the first call's refusal places a curve in
    E1's population (Codex's review of B1.3, round 1)."""

    def __enter__(self):
        from refute.packs.tess import a0

        battery_b1.check_active(None)
        self.results = []
        original = a0.group_variance

        def probe(*args, **kwargs):
            out = original(*args, **kwargs)
            self.results.append(out)
            return out

        self._a0, self._original = a0, original
        a0.group_variance = probe
        return self

    def __exit__(self, *exc) -> None:
        self._a0.group_variance = self._original
        battery_b1.check_active(None)

    @property
    def contrast_refused(self) -> bool:
        return bool(self.results) and self.results[0] is None


def _signed_v4(result) -> float | None:
    """The signed z of a version-4-style odd_even result: sign(odd - even) x difference_sigma."""
    m = result.metrics
    a, b, z = m.get("depth_odd_ppm"), m.get("depth_even_ppm"), m.get("difference_sigma")
    if a is None or b is None or z is None:
        return None
    return math.copysign(float(z), a - b)


class Only(bf.Version5):
    def __init__(self, name: str) -> None:
        super().__init__(ONLY[name])


# --- E4 ------------------------------------------------------------------------------------------


def e4_pseudo(key: str, tmin: float, tmax: float, candidate: dict) -> list:
    """The frozen draw of up to ``E4_PROPOSALS`` pseudo-ephemerides for one host (no redraws):
    period U[1, 15] d, duration U[1.5, 6] h, phase U[0, P); kept if none of its windows meets the
    host's catalogued v0.4 candidate (window half-width 0.5 d) or a kept one."""
    seed = int(hashlib.sha256(f"{E4_SEED_LABEL}:{key}".encode()).hexdigest()[:16], 16)
    rng = np.random.default_rng(seed)
    kept = []
    cat = _centres(candidate["t0_btjd"], candidate["period_days"], tmin, tmax)
    for _ in range(E4_PROPOSALS):
        period = rng.uniform(1.0, 15.0)
        duration = rng.uniform(1.5, 6.0) / 24.0
        t0 = tmin + rng.uniform(0.0, period)
        outer = duration / 2.0 + 2.0 * duration
        c = _centres(t0, period, tmin, tmax)
        if _windows_meet(c, outer, cat, 0.5):
            continue
        if any(_windows_meet(c, outer, k["centres"], k["outer"]) for k in kept):
            continue
        kept.append({"period": period, "duration": duration, "t0": t0, "centres": c,
                     "outer": outer})  # fmt: skip
    return [{k: v for k, v in p.items() if k != "centres"} for p in kept]


def e4_host(key: str) -> dict:
    """One host's E4 null contrasts: the background rise at each pseudo-ephemeris, by E4's
    operator, on the sectors the selector would choose (treated as certified)."""
    from refute.packs.tess import battery_v52 as v52
    from refute.packs.tess.adapter import TessAdapter

    started = time.process_time()
    rec: dict = {"key": key}
    raw, staged, plans = ft._plans()
    plan = plans["v4C"]
    target = ft.targets()[key]
    base = TessAdapter().load(target, staged, b1_data.CACHE)
    original = next(
        r for r in b1_data.c2_records() if r["kind"] == "original" and r["target_key"] == key
    )
    t = base.lc.time
    pseudos = e4_pseudo(key, float(t.min()), float(t.max()), original["chain"]["v04"]["candidate"])
    rec["proposals"], rec["kept"] = E4_PROPOSALS, len(pseudos)
    ev, cadence = plan.gauntlet.events, plan.data.exptime_seconds / 86400.0
    sectors = base.aux.sectors if base.aux else []
    contrasts = []
    for k, p in enumerate(pseudos):
        cand = SimpleNamespace(period=p["period"], t0=p["t0"], duration=p["duration"], depth=0.0)
        choice = v52.choose_sectors(base.lc.time, base.lc.sector, cand, ev, cadence, True)
        aux = [a for a in sectors if a.sector in choice.chosen]
        if not aux or choice.refused:
            contrasts.append({"k": k, "unavailable": choice.refused or "no auxiliary sector"})
            continue
        tb = np.concatenate([a.time for a in aux])
        sb = np.concatenate([np.full(a.time.size, a.sector) for a in aux])
        bkg = np.concatenate([a.sap_bkg for a in aux])
        with Only("e4") as v:
            g = battery_b1.a0_depth_quadratic(tb, bkg, sb, cand, plan, 1000 + k, False)
        if g is None or not g.error > 0:
            contrasts.append({"k": k, "unavailable": "no A0 depth", "counts": v.counts})
            continue
        contrasts.append({"k": k, "z": g.mean / g.error, "counts": v.counts,
                          "activation": v.activation})  # fmt: skip
    rec["contrasts"] = contrasts
    rec["status"] = "OK"
    rec["cpu_seconds"] = time.process_time() - started
    return rec


# --- running -------------------------------------------------------------------------------


def shard(arg: dict) -> bytes:
    key = {k: arg[k] for k in ("kind", "index", "key") if k in arg}
    try:
        rec = null_curve(arg["index"]) if arg["kind"] == "c1" else e4_host(arg["key"])
        rec = {**key, **rec}
    except Exception as exc:  # noqa: BLE001 - recorded, never dropped
        rec = {**key, "status": "ERROR", "reason": repr(exc)}
    return bf._bounded(rec, key)


def rows(part: str) -> list:
    if part == C1_PART:
        return [(f"r{i:05d}", {"kind": "c1", "index": i}) for i in range(FIRST, FIRST + N)]
    return [(f"h-{k}", {"kind": "e4", "key": k}) for k in b1_data.e4_hosts()]


def fingerprint(part: str, rws: list) -> str:
    """Code, configuration and rows (``bf.fingerprint``), this script and ``b1_data.py``, and for
    E4 the inputs it reads: v0.5's C2 records (the ephemerides), the C2 fetch record and each
    host's adapter manifest in B1's cache (Codex's review of B1.3, round 1)."""
    from refute.packs.tess.adapter import manifest_path

    h = hashlib.sha256(bf.fingerprint(part + json.dumps(rws, sort_keys=True)).encode())
    for path in (Path(__file__), HERE / "b1_data.py"):
        h.update(hashlib.sha256(path.read_bytes()).digest())
    if part == E4_PART:
        for path in (ft.C2_RECORDS, ft.C2_FETCH):
            h.update(hashlib.sha256(path.read_bytes()).digest())
        targets = ft.targets()
        for _, arg in rws:
            m = manifest_path(b1_data.CACHE, int(targets[arg["key"]]["tic_id"]))
            if not m.exists():
                raise SystemExit(
                    f"{arg['key']}: no manifest in B1's cache (run the fetch): refused"
                )
            h.update(hashlib.sha256(m.read_bytes()).digest())
    return h.hexdigest()[:16]


def run(part: str) -> None:
    hours = {C1_PART: C1_HOURS, E4_PART: E4_HOURS}[part]
    before = ledger_b.v052_ledger_sha256()
    try:
        ledger_b.check_caps(f"b1 recal {part}", reserve_days=0.2, reserve_tokens=0, in_b0=False)
        rws = rows(part)
        bf.disk_check(len(rws))
        bf._part(part, hours, "B1.3's recalibration screen (#217)")
        fp = fingerprint(part, rws)
        ledger_b.refuse_new_identity(part, fp, rws)
        cap = ledger_b.hard_cap(part, bf.WORKERS, bf.MAX_SHARD_SECONDS)
        print(len(rws), "shards; hard cap", round(cap, 2), "CPU-h; fingerprint", fp, flush=True)
        state = budgeted.execute(
            ledger_b.SECTION, part, OUT / part / fp, shard, rws, fp, bf.WORKERS, pin=bf.PIN,
            max_shard_seconds=bf.MAX_SHARD_SECONDS, hard_cap_hours=cap,
        )  # fmt: skip
        print(state, flush=True)
        print("disk used by B1 so far:", bf.disk_after(), "bytes", flush=True)
    finally:
        if ledger_b.v052_ledger_sha256() != before:
            raise SystemExit("the v0.5.2 ledger changed: refused")
    if state != "complete":
        raise SystemExit(state)


# --- the criteria --------------------------------------------------------------------------


def t_quantile(p: float, dof: int) -> float:
    """Student's t quantile by the Cornish-Fisher expansion in 1/dof (Abramowitz and Stegun
    26.7.5), accurate to about 1e-4 for dof >= 30; no dependency beyond the standard library."""
    from statistics import NormalDist

    z = NormalDist().inv_cdf(p)
    v = float(dof)
    return (
        z
        + (z**3 + z) / (4 * v)
        + (5 * z**5 + 16 * z**3 + 3 * z) / (96 * v**2)
        + (3 * z**7 + 19 * z**5 + 17 * z**3 - 15 * z) / (384 * v**3)
    )


def _binom_cdf(k: int, n: int, p: float) -> float:
    if p <= 0.0:
        return 1.0
    if p >= 1.0:
        return 1.0 if k >= n else 0.0
    lp, lq = math.log(p), math.log1p(-p)
    return min(1.0, sum(math.exp(math.lgamma(n + 1) - math.lgamma(i + 1) - math.lgamma(n - i + 1)
                                 + i * lp + (n - i) * lq) for i in range(k + 1)))  # fmt: skip


def clopper_pearson(k: int, n: int, alpha: float) -> tuple[float, float]:
    """The exact two-sided interval by bisection on the binomial CDF."""

    def solve(f) -> float:
        lo, hi = 0.0, 1.0
        for _ in range(100):
            mid = (lo + hi) / 2
            lo, hi = (mid, hi) if f(mid) > 0 else (lo, mid)
        return (lo + hi) / 2

    upper = 1.0 if k == n else solve(lambda p: _binom_cdf(k, n, p) - alpha / 2)
    lower = 0.0 if k == 0 else solve(lambda p: alpha / 2 - (1.0 - _binom_cdf(k - 1, n, p)))
    return lower, upper


def _iid_criteria(z: np.ndarray) -> dict:
    """Mean (Student t), standard deviation (chi-square), the fraction beyond 3 (Clopper-Pearson),
    each two-sided at 1 - 0.05/12: conditional diagnostics."""
    from refute.core.chi2 import chi2_isf

    n = z.size
    out: dict = {"n": int(n)}
    mean, sd = float(z.mean()), float(z.std(ddof=1))
    q = t_quantile(1 - ALPHA / 2, n - 1)
    out["mean"] = {
        "value": mean,
        "interval": [mean - q * sd / math.sqrt(n), mean + q * sd / math.sqrt(n)],
    }
    lo = math.sqrt((n - 1) * sd**2 / chi2_isf(ALPHA / 2, n - 1))
    hi = math.sqrt((n - 1) * sd**2 / chi2_isf(1 - ALPHA / 2, n - 1))
    out["sd"] = {"value": sd, "interval": [lo, hi]}
    k = int(np.sum(np.abs(z) > 3.0))
    plo, phi = clopper_pearson(k, n, ALPHA)
    out["tail"] = {"count": k, "value": k / n, "interval": [plo, phi]}
    return out


def _weighted(groups: list) -> tuple[float, float, float]:
    """Host-weighted mean, standard deviation and fraction beyond 3: each host's values weigh
    1 / n_host, so that every host weighs the same (Codex's review of B1.3, round 1)."""
    z = np.concatenate([np.asarray(g, dtype=float) for g in groups])
    w = np.concatenate([np.full(len(g), 1.0 / len(g)) for g in groups])
    w = w / w.sum()
    mean = float(np.sum(w * z))
    var = float(np.sum(w * (z - mean) ** 2))
    v2 = float(np.sum(w**2))
    sd = math.sqrt(var / (1.0 - v2)) if v2 < 1.0 else float("nan")  # reliability weights
    tail = float(np.sum(w * (np.abs(z) > 3.0)))
    return mean, sd, tail


DEGENERATE_TOL = 1e-9  # relative spread of the replicates below which the bootstrap is degenerate


def _degenerate(v: np.ndarray) -> bool:
    """A bootstrap whose replicates do not vary beyond rounding (Codex's review of B1.3, round 2):
    spread at most ``DEGENERATE_TOL`` times max(1, |median|), or no finite replicate."""
    f = v[np.isfinite(v)]
    if f.size == 0:
        return True
    return bool(np.ptp(f) <= DEGENERATE_TOL * max(1.0, abs(float(np.median(f)))))


def _cluster_criteria(by_host: dict) -> dict:
    """The host-cluster bootstrap with equal host weights, percentile intervals."""
    hosts = sorted(h for h, v in by_host.items() if v)
    groups = [by_host[h] for h in hosts]
    rng = np.random.default_rng(BOOT_SEED)
    reps = {"mean": [], "sd": [], "tail": []}
    for _ in range(BOOT):
        pick = rng.choice(len(hosts), size=len(hosts), replace=True)
        m, sd, t = _weighted([groups[j] for j in pick])
        reps["mean"].append(m)
        reps["sd"].append(sd)
        reps["tail"].append(t)
    m, sd, t = _weighted(groups)
    n = sum(len(g) for g in groups)
    out: dict = {"n": n, "hosts": len(hosts)}
    for k, value in (("mean", m), ("sd", sd), ("tail", t)):
        v = np.asarray(reps[k])
        lo, hi = np.nanpercentile(v, [100 * ALPHA / 2, 100 * (1 - ALPHA / 2)])
        out[k] = {"value": value, "interval": [float(lo), float(hi)],
                  "degenerate": _degenerate(v)}  # fmt: skip
    out["tail"]["count"] = int(sum(np.sum(np.abs(np.asarray(g)) > 3.0) for g in groups))
    return out


def judge(c: dict, eligible: int, cluster: bool) -> dict:
    """PASS, FAIL or UNRESOLVED per criterion, and the estimator's use (the design, B1.3)."""
    n = c["n"]
    res = {}
    lo, hi = c["mean"]["interval"]
    res["mean"] = "PASS" if -TOL_MEAN <= lo and hi <= TOL_MEAN else (
        "FAIL" if hi < -TOL_MEAN or lo > TOL_MEAN else "UNRESOLVED")  # fmt: skip
    lo, hi = c["sd"]["interval"]
    res["sd"] = "PASS" if TOL_SD[0] <= lo and hi <= TOL_SD[1] else (
        "FAIL" if lo > TOL_SD[1] else "UNRESOLVED")  # fmt: skip
    res["sd_conservative"] = bool(hi < TOL_SD[0])
    lo, hi = c["tail"]["interval"]
    res["tail"] = "PASS" if hi <= TOL_TAIL else ("FAIL" if lo > TOL_TAIL else "UNRESOLVED")
    if cluster:  # the safeguards hold whatever the outcome, FAIL included (Codex, round 1)
        for k in ("mean", "sd", "tail"):
            if c[k].get("degenerate"):
                res[k] = "UNRESOLVED"
        if c["tail"]["count"] == 0 or n < MIN_TAIL_SUPPORT:
            res["tail"] = "UNRESOLVED"
    available = n / eligible if eligible else 0.0
    if n < MIN_CONTRASTS or available < MIN_AVAILABILITY:
        for k in ("mean", "sd", "tail"):
            if res[k] == "PASS":
                res[k] = "UNRESOLVED"
    if n < MIN_CONTRASTS:
        for k in ("mean", "sd", "tail"):
            if res[k] == "FAIL":
                res[k] = "UNRESOLVED"  # a FAIL needs at least 30 contrasts to stand
    res["availability"] = available
    res["used"] = not any(res[k] == "FAIL" for k in ("mean", "sd", "tail"))
    return res


def summary(c1_recs: list, e4_recs: list) -> dict:
    out: dict = {"label": "B1.3 recalibration screen of version 5's errors (development; an "
                 "exploratory conservative veto, never a calibration)",
                 "method_status": "not_validated", "estimators": {}}  # fmt: skip
    ok = [r for r in c1_recs if r.get("status") == "OK"]
    out["c1"] = {"curves": len(c1_recs), "ok": len(ok),
                 "errors": sum(r.get("status") == "ERROR" for r in c1_recs),
                 "unavailable": sum("unavailable" in r for r in ok)}  # fmt: skip
    # each branch's population: every curve given to it (Codex's review of B1.3, round 1)
    pops = {
        "e1": [r for r in ok if r.get("v4_contrast_refused")],
        "e2": [r for r in ok if r.get("e2_eligible")],
        "e3": [r for r in ok if r.get("sinusoid_called")],
    }
    ran = {
        "e1": lambda r: "e1" in r,
        "e2": lambda r: bool((r.get("e2_counts") or {}).get("e2.calls")),
        "e3": lambda r: bool((r.get("e3_counts") or {}).get("e3.calls")),
    }
    fell = {
        "e1": lambda r: (r.get("e1_counts") or {}).get("e1.still_undefined", 0) > 0,
        "e2": lambda r: any("v4_path" in k for k in (r.get("e2_counts") or {})),
        "e3": lambda r: any("fallback" in k for k in (r.get("e3_counts") or {})),
    }
    # a curve whose record is an ERROR has an unknown eligibility: it counts as eligible with no
    # contrast for every estimator, which can only block a PASS (Codex's review, round 2)
    unknown = sum(r.get("status") == "ERROR" for r in c1_recs)
    for name, pop in pops.items():
        z = np.array([r[name] for r in pop if r.get(name) is not None], dtype=float)
        entry: dict = {
            "attempts": len(ok) + unknown,
            "eligible": len(pop) + unknown,
            "unknown_eligibility": unknown,
            "errors": sum(f"{name}_error" in r for r in pop),
            "ran": sum(ran[name](r) for r in pop),
            "fallback": sum(fell[name](r) for r in pop),
            "contrasts": int(z.size),
        }
        if z.size >= 2:
            c = _iid_criteria(z)
            entry["criteria"] = c
            entry["judgement"] = judge(c, len(pop) + unknown, cluster=False)
        else:
            entry["judgement"] = {"used": True, "availability": 0.0, "mean": "UNRESOLVED",
                                  "sd": "UNRESOLVED", "tail": "UNRESOLVED"}  # fmt: skip
        out["estimators"][name] = entry
    by_host: dict = {}
    eligible4 = 0
    for r in e4_recs:
        if r.get("status") != "OK":
            eligible4 += E4_PROPOSALS  # a failed host keeps its proposals in the denominator
            continue
        eligible4 += len(r["contrasts"])
        by_host[r["key"]] = [c["z"] for c in r["contrasts"] if "z" in c]
    entry = {
        "eligible": eligible4,
        "contrasts": sum(len(v) for v in by_host.values()),
        "hosts": len(e4_recs),
        "hosts_ok": sum(r.get("status") == "OK" for r in e4_recs),
    }
    if sum(len(v) for v in by_host.values()) >= 2 and sum(1 for v in by_host.values() if v) >= 2:
        c = _cluster_criteria(by_host)
        entry["criteria"] = c
        entry["judgement"] = judge(c, eligible4, cluster=True)
    else:
        entry["judgement"] = {"used": True, "availability": 0.0, "mean": "UNRESOLVED",
                              "sd": "UNRESOLVED", "tail": "UNRESOLVED"}  # fmt: skip
    entry["limit"] = (
        "these hosts passed the v0.4 gate and T2a's did not: the transport is not shown; "
        "dependence between hosts through the instrument is not excluded"
    )
    out["estimators"]["e4"] = entry
    used = {k: v["judgement"]["used"] for k, v in out["estimators"].items()}
    # the composition, by the design's frozen rule: an estimator with any FAIL is not used; if E1
    # is not used, E2 runs only where its own conditions hold (it already does: its fallback is
    # then version 4's); if E2 is not used, odd_even is version 4's (with E1 if used)
    out["composition"] = {"e1": used["e1"], "e2": used["e2"], "e3": used["e3"], "e4": used["e4"]}
    return out


def _records(part: str) -> list:
    rws = rows(part)
    fp = fingerprint(part, rws)
    data = budgeted.assembled(
        ledger_b.SECTION, part, OUT / part / fp, shard, rws, fp, bf.WORKERS, pin=bf.PIN,
        max_shard_seconds=bf.MAX_SHARD_SECONDS,
    )  # fmt: skip
    return [json.loads(x) for x in data.decode().splitlines() if x.strip()]


def summarize() -> None:
    out = summary(_records(C1_PART), _records(E4_PART))
    (HERE / "b1-recal.json").write_text(json.dumps(out, indent=1, sort_keys=True) + "\n", "utf-8")
    comp = {"composition": out["composition"], "source": "b1-recal.json (B1.3), frozen before B1.4"}
    (HERE / "b1-composition.json").write_text(json.dumps(comp, indent=1) + "\n", "utf-8")
    print(json.dumps({k: v for k, v in out.items()}, indent=1, sort_keys=True, default=str)[:6000])


if __name__ == "__main__":
    with ledger_b.Exclusive(f"b1_recal {' '.join(sys.argv[1:])}"):
        {"run": lambda: run(sys.argv[2]), "summarize": summarize}[sys.argv[1]]()
