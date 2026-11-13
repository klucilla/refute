"""v0.5.4, second half, step 6: I2 in stages, on the 102 class-(i) injections (#217; the
maintainer's decision of 2026-11-12, night, item 4e; the frozen design is
``docs/plans/v0.5.4-h2-step6-i2-staged.md``). ``method_status: not_validated``.

Each of I1's 102 ``i2_population`` injections is replayed exactly as I1 replayed it, with the
``systematics`` sub-check's inputs captured. On E4's own preprocessed background series, one
noise family (a per-sector constant, an Ornstein-Uhlenbeck process and white noise) is fitted on
the series binned at a third of the transit's duration, by exact likelihood (a Kalman filter; the
project's own code). Its adequacy is checked at the transit's scale. Two bounds on the background
rise's error use E4's windows (σ_E4op, E4's per-event operator best combined; σ_full, the GLS
bound with E4's quadratic baselines as nuisances). The background block's power is computed
under each. Part ``h2_step6`` under ``budgeted_v3``.

Usage (from the project root, launched through ``launch_detached.py``):
``.venv/Scripts/python.exe -B docs/validation/v0.5.4/step6_i2.py run``, then ``summarize``.
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
import types
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import i4_bound as i4  # noqa: E402,I001  (stage A's and B's modules, then ledger_i, last)
from i4_bound import ROOT, b1_b14  # noqa: E402
import i1_diagnose  # noqa: E402
import i4_rest as r1  # noqa: E402
import ledger_i  # noqa: E402
import budgeted  # noqa: E402
import budgeted_v3  # noqa: E402

battery_b1 = b1_b14.battery_b1

PART = "h2_step6"
ALLOCATION = 6.0
OUT = ROOT / ".cache/v054/step6"
OUT_FILE = HERE / "h2-step6-i2.json"
DESIGN = ROOT / "docs/plans/v0.5.4-h2-step6-i2-staged.md"
I1_FILE = HERE / "i1-diagnosis.json"
STEP1 = HERE / "h2-step1-floor.json"
STEP1_CASES = ROOT / ".cache/v054/step1/cases.json"
POPULATION = 102
WORKERS = 12
PIN = tuple(range(8, 32, 2))
MAX_SHARD_SECONDS = 1200.0
REQUIRED = 0.95
COND_MAX = 1e12
LB_ALPHA = 0.01
MAX_UNK = 20
TAU_MAX_DAYS = 30.0
RESERVE_TOKENS = 450_000
SUMMARY_RESERVE_HOURS = 0.02
T2A_ALLOWED, T2A_IF_REFUTED_STAY, T2A_C = 7, 2, 49
REASON = ("the maintainer's decision of 2026-11-12 (night), item 4e (#217): step 6, I2 in stages "
          "on the 102 class-(i) injections (h2_step6, budgeted_v3)")  # fmt: skip


# --- the replay and its capture ---------------------------------------------------------------


def replay(arg: dict) -> tuple[dict, dict]:
    """I1's own T2a replay, with the ``systematics`` sub-check's inputs captured (the wrapper is
    installed before version 5's activation reads ``battery_b1.check_systematics``)."""
    captured: dict = {}
    original = battery_b1.check_systematics

    def spy(aux, candidate, plan, seed, exclude_phase_half=False, depth=None, a0_aux=None,
            a0_refused=None):  # fmt: skip
        result = original(aux, candidate, plan, seed, exclude_phase_half, depth=depth,
                          a0_aux=a0_aux, a0_refused=a0_refused)  # fmt: skip
        src = aux if a0_aux is None else a0_aux
        if "candidate" not in captured and a0_refused is None and src:
            t_b = np.concatenate([a.time for a in src])
            s_b = np.concatenate([np.full(a.time.size, a.sector) for a in src])
            bkg = np.concatenate([a.sap_bkg for a in src])
            sap = np.concatenate([a.sap_flux for a in src])
            base = depth if depth is not None else battery_b1.a0_v4.a0_depth
            captured.update(
                candidate=candidate, plan=plan, seed=seed, excl=exclude_phase_half,
                t=t_b, s=s_b, bkg=bkg,
                g_bkg=battery_b1.a0_depth_quadratic(t_b, bkg, s_b, candidate, plan, seed + 3,
                                                    exclude_phase_half),
                g_sap=base(t_b, sap, s_b, candidate, plan, seed + 4, exclude_phase_half),
            )  # fmt: skip
        return result

    battery_b1.check_systematics = spy
    try:
        rec = i1_diagnose.t2a_one(arg)
    finally:
        battery_b1.check_systematics = original
    return rec, captured


# --- E4's series and windows ------------------------------------------------------------------


def e4_series(cap: dict):
    """``a0_depth_quadratic``'s own preprocessing of the background series."""
    from refute.packs.tess import detrend_fast as df
    from refute.packs.tess.events import transit_mask

    cand, plan = cap["candidate"], cap["plan"]
    time, values, sector = cap["t"], cap["bkg"], cap["s"]
    good = np.isfinite(time) & np.isfinite(values)
    time, values, sector = time[good], values[good], sector[good]
    order = np.argsort(time, kind="stable")
    time, values, sector = time[order], values[order], sector[order]
    half = plan.detrend.transit_mask_half_width_durations * cand.duration
    mask = transit_mask(time, cand.period, cand.t0, half)
    series = df.AdditiveDetrender(time, values, sector, plan.detrend, mask).flat()
    return series


def e4_weights(time, centre, duration, ev, cadence):
    """``battery_b1.quadratic_box``'s ``weights``, unchanged in substance: (lo, hi, c, inside,
    scaled time, fallback)."""
    half = duration / 2.0
    inner = half + ev.baseline_gap_durations * duration
    outer = half + ev.baseline_outer_durations * duration
    expected_in = 2.0 * half / cadence
    expected_base = 2.0 * (outer - inner) / cadence
    lo = np.searchsorted(time, centre - outer, side="left")
    hi = np.searchsorted(time, centre + outer, side="left")
    if hi <= lo:
        return None
    d = time[lo:hi] - centre
    ad = np.abs(d)
    inside, base = ad <= half, ad > inner
    n_in, n_base = int(inside.sum()), int(base.sum())
    if n_in < ev.min_coverage * expected_in or n_base < ev.min_coverage * expected_base:
        return None
    c = battery_b1.quadratic_weights(d, base, inside, outer)
    fallback = c is None
    if fallback:
        c = np.zeros(d.size)
        c[base] = 1.0 / n_base
        c[inside] = -1.0 / n_in
    return lo, hi, c, inside, d / outer, fallback


# --- the noise family: per-sector constant + OU + white, on binned series ----------------------


def bin_series(t, f, sector, width):
    """Bins of ``width`` within each sector (at least two cadences), with their integer index."""
    out_t, out_f, out_n, out_s, out_b = [], [], [], [], []
    for s in np.unique(sector):
        sel = sector == s
        ts, fs = t[sel], f[sel]
        if ts.size == 0:
            continue
        k = np.floor((ts - ts[0]) / width).astype(int)
        for b in np.unique(k):
            m = k == b
            if m.sum() >= 2:
                out_t.append(ts[m].mean())
                out_f.append(fs[m].mean())
                out_n.append(int(m.sum()))
                out_s.append(s)
                out_b.append(int(b))
    return (
        np.array(out_t),
        np.array(out_f),
        np.array(out_n),
        np.array(out_s),
        np.array(out_b),
    )


def _kalman_ou(t, y, n, sector, sw, sr, tau):
    """Innovations and variances of y = x + e per sector, x a stationary OU (variance sr^2, time
    scale tau), e white of variance sw^2 / n (sw per cadence, a bin of n cadences). Linear in y."""
    innov, var = np.empty(y.size), np.empty(y.size)
    for s in np.unique(sector):
        idx = np.flatnonzero(sector == s)
        m, p = 0.0, sr**2
        prev = None
        for i in idx:
            if prev is not None:
                a = math.exp(-(t[i] - t[prev]) / tau)
                m, p = a * m, a * a * p + sr**2 * (1 - a * a)
            s_ = p + sw**2 / n[i]
            v = y[i] - m
            innov[i], var[i] = v, s_
            k = p / s_
            m, p = m + k * v, (1 - k) * p
            prev = i
    return innov, var


def kalman(t, y, n, sector, sw, sr, tau):
    """Innovations and variances for y = mu_s + x + e, with each sector's constant mu_s profiled
    out by GLS: the filter is linear, so the innovations of y and of a constant one give
    mu_s = sum(v1 vy / S) / sum(v1^2 / S) per sector, and the profiled innovations vy - mu_s v1
    (Codex, h2-step6 round 2: an exact profile, not a finite prior)."""
    vy, s2 = _kalman_ou(t, y, n, sector, sw, sr, tau)
    v1, _ = _kalman_ou(t, np.ones_like(y), n, sector, sw, sr, tau)
    out = vy.copy()
    for s in np.unique(sector):
        idx = sector == s
        den = float(np.sum(v1[idx] ** 2 / s2[idx]))
        mu = float(np.sum(v1[idx] * vy[idx] / s2[idx])) / den if den > 0 else 0.0
        out[idx] = vy[idx] - mu * v1[idx]
    return out, s2


MIN_PAIRS_PER_LAG = 30


def _ljung_box(z, sector, bins, lags):
    """A Box-Pierce statistic on the standardized innovations with each lag's own pair count:
    Q = sum_k n_k r_k^2, r_k the lag-k correlation over the n_k pairs of bins of the same sector
    exactly k bins apart (never across a gap or a sector). A heuristic diagnostic at the transit's
    scale; None (UNK) with fewer than 50 bins, a null denominator, or fewer than
    ``MIN_PAIRS_PER_LAG`` pairs at any lag. Returns (p, pair counts)."""
    from scipy.stats import chi2

    ok = np.isfinite(z)
    nz = int(ok.sum())
    if nz < 50:
        return None, []
    zc = np.where(ok, z - np.nanmean(z), np.nan)
    c0 = float(np.nansum(zc**2)) / nz
    if c0 <= 0:
        return None, []
    key = {}
    for i, (s, b) in enumerate(zip(sector, bins, strict=True)):
        if ok[i]:
            key[(int(s), int(b))] = i
    q, counts = 0.0, []
    for k in range(1, lags + 1):
        prods = [zc[i] * zc[key[(s, b + k)]] for (s, b), i in key.items() if (s, b + k) in key]
        counts.append(len(prods))
        if len(prods) < MIN_PAIRS_PER_LAG:
            return None, counts
        r = (sum(prods) / len(prods)) / c0
        q += len(prods) * r * r
    return float(chi2.sf(q, max(lags - 3, 1))), counts


def fit_noise(t, y, n, sector, bins, duration, width):
    """Maximum likelihood of (sw, sr, tau) with each sector's constant profiled out by GLS."""
    from scipy.optimize import minimize

    mad = float(np.median(np.abs(y - np.median(y))))
    scale = 1.4826 * mad * math.sqrt(float(np.mean(n))) or 1.0

    def nll(theta):
        sw, sr, tau = np.exp(theta)
        v, s2 = kalman(t, y, n, sector, sw, sr, tau)
        return 0.5 * float(np.sum(np.log(2 * np.pi * s2) + v**2 / s2))

    x0 = np.log([scale, scale / 2.0 / math.sqrt(float(np.mean(n))), max(duration, 3.0 * width)])
    ls = math.log(scale)
    limits = [(ls - 12, ls + 6), (ls - 14, ls + 6), (math.log(width), math.log(TAU_MAX_DAYS))]
    res = minimize(nll, x0, method="L-BFGS-B", bounds=limits)
    if not res.success:
        return None, f"the fit did not converge: {res.message}"
    sw, sr, tau = (float(v) for v in np.exp(res.x))
    if tau < 3.0 * width:  # a binned OU is accepted as an approximation only above three bins
        return None, f"tau {tau:.4g} d below three bins: the binned approximation is not accepted"
    v, s2 = kalman(t, y, n, sector, sw, sr, tau)
    lags = max(5, math.ceil(3.0 * duration / width))
    p, counts = _ljung_box(v / np.sqrt(s2), sector, bins, lags)
    if p is None:
        return None, f"the adequacy check lacks bins or pairs (pairs per lag {counts})"
    model = {
        "sigma_w_cad": sw,
        "sigma_r": sr,
        "tau_days": tau,
        "adequacy_lags": lags,
        "adequacy_pairs_per_lag": counts,
        "adequacy_p": p,
        "adequate": p >= LB_ALPHA,
        "bins": int(v.size),
        "adequacy_note": "a heuristic Box-Pierce diagnostic at the transit's scale",
        "fit": "maximum likelihood with each sector's constant profiled out by GLS",
    }
    return model, None


# --- the bounds -------------------------------------------------------------------------------


def _cov(ti, si, tj, sj, model) -> np.ndarray:
    k = model["sigma_r"] ** 2 * np.exp(-np.abs(ti[:, None] - tj[None, :]) / model["tau_days"])
    return np.where(si[:, None] == sj[None, :], k, 0.0)


def _valid(m) -> bool:
    if not np.all(np.isfinite(m)):
        return False
    d = np.sqrt(np.clip(np.diag(m), 0.0, None))
    if np.any(d <= 0):
        return False
    ms = m / np.outer(d, d)
    try:
        np.linalg.cholesky(ms)
    except np.linalg.LinAlgError:
        return False
    return float(np.linalg.cond(ms)) <= COND_MAX


def precision_apply(t, sector, x, model) -> np.ndarray:
    """Sigma^-1 X for Sigma = sw^2 I + sr^2 K, K exponential of time scale tau per sector (the
    banded solve of ``forecast.mahalanobis2``, with this tau)."""
    from scipy.linalg import solve_banded

    sw, sr, tau = model["sigma_w_cad"], model["sigma_r"], model["tau_days"]
    out = np.zeros_like(x)
    for s in np.unique(sector):
        sel = sector == s
        ts, xs = t[sel], x[sel]
        a = np.exp(-np.diff(ts) / tau)
        w = 1.0 / (1.0 - a**2)
        diag = np.ones(ts.size)
        diag[:-1] += a**2 * w
        diag[1:] += w - 1.0
        off = -a * w
        ax = diag[:, None] * xs
        ax[:-1] += off[:, None] * xs[1:]
        ax[1:] += off[:, None] * xs[:-1]
        ab = np.zeros((3, ts.size))
        ab[0, 1:] = sw**2 * off
        ab[1] = sw**2 * diag + sr**2
        ab[2, :-1] = sw**2 * off
        out[sel] = solve_banded((1, 1), ab, ax)
    return out


def bounds(series, step_flat, cap, model) -> dict:
    """σ_E4op and σ_full with E4's windows; both require a unit response to an in-event step that
    went through E4's own detrender (``step_flat``)."""
    cand, plan = cap["candidate"], cap["plan"]
    ev = plan.gauntlet.events
    cadence = plan.data.exptime_seconds / 86400.0
    t, sector = series.time, series.sector
    centres = [cand.t0 + e * cand.period for e in cap["g_bkg"].epochs]
    wins = [e4_weights(t, c, cand.duration, ev, cadence) for c in centres]
    if not wins or any(w is None for w in wins):
        return {"status": "UNK", "reason": "an E4 window is not reconstructed"}
    spans = sorted((w[0], w[1]) for w in wins)
    if any(b[0] < a[1] for a, b in zip(spans, spans[1:], strict=False)):
        # Codex, h2-step6 round 3 (the tie-break): overlapping windows are UNK
        return {"status": "UNK", "reason": "two E4 windows share cadences"}
    sw2 = model["sigma_w_cad"] ** 2
    responses = [-float(c @ step_flat[lo:hi]) for lo, hi, c, _, _, _ in wins]
    if any(not math.isfinite(r) or abs(r - 1.0) > 0.01 for r in responses):
        return {"status": "UNK", "reason": "E4's operator does not keep a unit response"}
    nw = len(wins)
    v = np.zeros((nw, nw))
    for a in range(nw):
        la, ha, ca, _, _, _ = wins[a]
        for b in range(a, nw):
            lb, hb, cb, _, _, _ = wins[b]
            k = _cov(t[la:ha], sector[la:ha], t[lb:hb], sector[lb:hb], model)
            v[a, b] = float(ca @ k @ cb)
            lo, hi = max(la, lb), min(ha, hb)  # the white noise of shared cadences
            if hi > lo:
                v[a, b] += sw2 * float(ca[lo - la : hi - la] @ cb[lo - lb : hi - lb])
            v[b, a] = v[a, b]
    if not _valid(v):
        return {"status": "UNK", "reason": "the event covariance is not valid"}
    one = np.ones(nw)
    vinv1 = np.linalg.solve(v, one)
    sigma_op = 1.0 / math.sqrt(float(one @ vinv1))
    weights = vinv1 / float(one @ vinv1)
    combined = float(weights @ np.array(responses))
    if not math.isfinite(combined) or abs(combined - 1.0) > 0.01:
        return {"status": "UNK", "reason": "the best E4 combination does not keep a unit response"}
    for _lo, _hi, c, _, tau, fallback in wins:  # each operator annihilates its own baseline
        scale_c = float(np.sum(np.abs(c)))
        for power_ in (0,) if fallback else (0, 1, 2):
            if abs(float(c @ tau**power_)) > 1e-8 * scale_c:
                return {"status": "UNK", "reason": "an E4 operator does not null its baseline"}
    idx = np.unique(np.concatenate([np.arange(w[0], w[1]) for w in wins]))
    pos = {int(i): j for j, i in enumerate(idx)}
    cols = [np.zeros(idx.size)]
    for lo, hi, _, inside, tau, fallback in wins:
        rows = np.array([pos[int(i)] for i in range(lo, hi)])
        cols[0][rows[inside]] = 1.0  # the in-event step: the rise
        for power_ in (0,) if fallback else (0, 1, 2):  # E4's own baseline (constant on fallback)
            col = np.zeros(idx.size)
            col[rows] = tau**power_
            cols.append(col)
    x = np.column_stack(cols)
    px = precision_apply(t[idx], sector[idx], x, model)
    g = x.T @ px
    if not _valid(g):
        return {"status": "UNK", "reason": "the GLS information is not valid"}
    cov = np.linalg.inv(g)
    var = float(cov[0, 0])
    beta = cov @ (px.T @ step_flat[idx])  # the GLS estimate on the detrended unit step
    b0_ = float(beta[0])
    if not (math.isfinite(var) and var > 0 and math.isfinite(b0_)) or abs(b0_ - 1.0) > 0.01:
        return {"status": "UNK", "reason": "the GLS step has no unit response or variance"}
    if not (math.isfinite(sigma_op) and sigma_op > 0):
        return {"status": "UNK", "reason": "σ_E4op is not finite and positive"}
    return {
        "status": "OK",
        "sigma_e4op": sigma_op,
        "sigma_full": math.sqrt(var),
        "events": nw,
        "window_cadences": int(idx.size),
        "fallback_windows": int(sum(w[5] for w in wins)),
        "responses_e4op_range": [min(responses), max(responses)],
        "response_full": b0_,
        "response_e4op_combined": combined,
    }


def power(cap, sigma) -> float:
    from refute.packs.tess.battery_v51_diff import background_block

    plan = cap["plan"]
    g_bkg = types.SimpleNamespace(error=sigma, mean=cap["g_bkg"].mean)
    block = background_block(
        g_bkg, cap["g_sap"], plan.gauntlet.systematics, plan.stronger, cap["seed"] + 5
    )
    return float(block["probability"])


def _probability(p) -> bool:
    return isinstance(p, float) and math.isfinite(p) and 0.0 <= p <= 1.0


def one(arg: dict) -> dict:
    """One injection. A replay that does not reproduce I1's record, or a recomputed error that
    differs, raises: the driver stops dispatching (Codex, h2-step6 round 1)."""
    row = arg["row"]
    out: dict = {"key": row["key"], "slot": row["slot"]}
    rec, cap = replay(arg)
    if rec.get("mismatch"):
        raise RuntimeError(f"STOP: {row['key']}/{row['slot']} not reproduced: {rec['mismatch']}")
    test = rec.get("tests", {}).get("systematics", {})
    if test.get("class") != "i" or "background" not in test.get("non_detectable", []):
        raise RuntimeError(f"STOP: {row['key']}/{row['slot']} is not class (i) with background")
    if not cap or cap.get("g_bkg") is None or cap.get("g_sap") is None:
        raise RuntimeError(f"STOP: {row['key']}/{row['slot']}: nothing captured")
    recorded = test.get("metrics", {}).get("background_rise_err")
    if not recorded or abs(cap["g_bkg"].error / recorded - 1.0) > 1e-9:
        raise RuntimeError(f"STOP: {row['key']}/{row['slot']}: background_rise_err differs")
    recorded_power = test["blocks"]["background"].get("probability")
    if not _probability(recorded_power) or abs(power(cap, recorded) - recorded_power) > 1e-9:
        raise RuntimeError(f"STOP: {row['key']}/{row['slot']}: the block's power differs")
    series = e4_series(cap)
    # the transformation's response on the real background: T(b + a s) - T(b), NaNs kept
    size = 3.0 * recorded
    stepped = e4_series({**cap, "bkg": cap["bkg"] + size * unit_step(cap)})
    same = np.array_equal(stepped.time, series.time) and np.array_equal(
        stepped.sector, series.sector
    )
    if not same:
        return {**out, "status": "UNK", "reason": "the stepped series is not aligned"}
    step_flat = (stepped.flux - series.flux) / size
    cand, plan = cap["candidate"], cap["plan"]
    outer = cand.duration / 2.0 + plan.gauntlet.events.baseline_outer_durations * cand.duration
    phase = np.mod(series.time - cand.t0 + 0.5 * cand.period, cand.period) - 0.5 * cand.period
    off = (np.abs(phase) > outer) & np.isfinite(series.flux)
    width = cand.duration / 3.0
    tb, fb, nb, sb, bb = bin_series(series.time[off], series.flux[off], series.sector[off], width)
    model, why = fit_noise(tb, fb, nb, sb, bb, cand.duration, width)
    if model is None:
        return {**out, "status": "UNK", "reason": why}
    out["model"] = model
    if not model["adequate"]:
        return {**out, "status": "UNK", "reason": "inadequate at the transit's scale"}
    b = bounds(series, step_flat, cap, model)
    out.update(b)
    if b["status"] != "OK":
        return out
    p_full, p_op = power(cap, b["sigma_full"]), power(cap, b["sigma_e4op"])
    if not (_probability(p_full) and _probability(p_op)):
        return {**out, "status": "UNK", "reason": "a power is not a probability"}
    out.update(
        recorded_error=recorded,
        recorded_power=recorded_power,
        power_full=p_full,
        power_e4op=p_op,
    )
    return out


def unit_step(cap: dict) -> np.ndarray:
    """A unit step at every in-event cadence of the candidate, zero elsewhere, on the captured
    background's own times (before E4's preprocessing)."""
    cand = cap["candidate"]
    t = cap["t"]
    phase = np.mod(t - cand.t0 + 0.5 * cand.period, cand.period) - 0.5 * cand.period
    return (np.abs(phase) <= cand.duration / 2.0).astype(float)


def shard(arg: dict) -> bytes:
    try:
        rec = one(arg)
    except Exception as exc:  # the injection's identity on every failure (Codex, round 3)
        row = arg["row"]
        raise RuntimeError(
            f"STOP: {row['key']}/{row['slot']}: {type(exc).__name__}: {exc}"
        ) from exc
    return (json.dumps(rec, sort_keys=True, default=float) + "\n").encode()


def schedule() -> list:
    pop = set(json.loads(I1_FILE.read_text("utf-8"))["i2_population"])
    rows = [(sid, a) for sid, a in i1_diagnose.schedule()
            if a["kind"] == "t2a" and f"{a['row']['key']}/{a['row']['slot']}" in pop]  # fmt: skip
    if len(rows) != POPULATION or len(pop) != POPULATION:
        raise SystemExit(f"{len(rows)} rows for {len(pop)} injections, not 102: STOP")
    return rows


def fingerprint(rows: list) -> str:
    from refute.core.codehash import compute_code_hash

    h = hashlib.sha256(compute_code_hash().sha256.encode())
    for path in (Path(__file__), DESIGN, HERE / "ledger_i.py", HERE / "budgeted_v3.py",
                 HERE / "i1_diagnose.py", I1_FILE, STEP1, i4.STAGE_B / "battery_b1.py",
                 i4.STAGE_B / "b1_b14.py"):  # fmt: skip
        h.update(hashlib.sha256(path.read_bytes()).digest())
    h.update(json.dumps(rows, sort_keys=True, default=str).encode())
    return h.hexdigest()[:16]


def run() -> None:
    ledger_i.assert_bound()
    rows = schedule()
    fp = fingerprint(rows)
    if PART not in ledger_i._rows():
        with ledger_i.Exclusive("step6 transfer"):
            ledger_i._transfer("h2_unallocated", PART, ALLOCATION, REASON)
    ledger_i.refuse_new_identity(PART, fp, rows)
    ledger_i.check_caps("step6 run", reserve_days=0.3, reserve_tokens=RESERVE_TOKENS,
                        in_h1=False, reserve_bytes=len(rows) * 50_000 + 100_000_000)  # fmt: skip
    cap = ledger_i.hard_cap(PART, WORKERS, MAX_SHARD_SECONDS)
    print(f"{PART}: {len(rows)} rows; hard cap {cap:.3f} CPU-h; {WORKERS} workers; fp {fp}",
          flush=True)  # fmt: skip
    with ledger_i.Exclusive("step6 run"):
        try:
            state = budgeted_v3.execute(
                ledger_i.SECTION, PART, OUT / fp, shard, rows, fp, WORKERS, pin=PIN,
                max_shard_seconds=MAX_SHARD_SECONDS, hard_cap_hours=cap, pause_at=r1.PAUSE_AT,
            )  # fmt: skip
        except Exception as exc:  # a shard's stop: persisted, binding, before it propagates
            import driver

            handle = driver.Run(OUT / fp, shard, rows, fp, 1.0, WORKERS, pin=PIN,
                                max_shard_seconds=MAX_SHARD_SECONDS)  # fmt: skip
            why = f"stopped: {exc}"[:500]
            book = budgeted.load()
            row = book["sections"][ledger_i.SECTION]["parts"][PART]
            row["spent_hours"] = handle.spent_seconds() / 3600.0
            budgeted._stop(book, row, why)
            if handle.unresolved_stop() is None:
                handle._record_stop(why)
            raise SystemExit(f"STOP for the maintainer: {why}") from exc
    print(state, flush=True)
    ledger_i.check_caps("step6 after the run", 0.0, 0, in_h1=False)
    if state != "complete":
        raise SystemExit(f"STOP for the maintainer: {state}")


def summarize() -> None:
    import time
    import uuid

    ledger_i.assert_bound()
    ledger_i.check_caps("step6 summarize", reserve_days=0.05, reserve_tokens=0, in_h1=False)
    room = ledger_i.CHARGES_ROOM - ledger_i._charges()
    if room < SUMMARY_RESERVE_HOURS:
        raise SystemExit(f"the charges' room ({room:.3f} CPU-h) cannot hold the summary: STOP")
    started = time.process_time()
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()) + "-" + uuid.uuid4().hex[:12]
    try:
        doc = _summarize()
    finally:
        hours = (time.process_time() - started) / 3600.0
        ledger_i.charge(f"{PART}_summarize_{stamp}", hours,
                        "the summary's own CPU, outside the driver")  # fmt: skip
    text = json.dumps(doc, indent=1, sort_keys=True) + chr(10)
    OUT_FILE.write_text(text, "utf-8", newline=chr(10))
    print(json.dumps({k: doc[k] for k in ("valid", "unknown", "freed_full", "outcome")}, indent=1))
    if doc["stops"]:
        raise SystemExit("STOP for the maintainer: " + "; ".join(doc["stops"]))


def _summarize() -> dict:
    rows = schedule()
    fp = fingerprint(rows)
    data = budgeted.assembled(ledger_i.SECTION, PART, OUT / fp, shard, rows, fp, WORKERS, pin=PIN,
                              max_shard_seconds=MAX_SHARD_SECONDS)  # fmt: skip
    recs = [json.loads(x) for x in data.decode().splitlines() if x.strip()]
    stops = []
    bad = [f"{r['key']}/{r['slot']}" for r in recs if r["status"] in ("NOT_REPRODUCED", "ERROR")]
    if bad:
        stops.append(f"{len(bad)} injections not reproduced or in error")
    valid = [r for r in recs if r["status"] == "OK"]
    unk = [r for r in recs if r["status"] == "UNK"]
    doc: dict = {
        "label": "v0.5.4 step 6: I2's first stage on the 102 class-(i) injections (a bound under "
        "a fitted noise model; never a draft)",
        "method_status": "not_validated", "fingerprint": fp,
        "decision": "the maintainer's decision of 2026-11-12 (night), item 4e (#217)",
        "design": "docs/plans/v0.5.4-h2-step6-i2-staged.md",
        "injections": len(recs), "valid": len(valid), "unknown": len(unk),
        "unknown_reasons": sorted({r.get("reason", "") for r in unk}),
        "not_reproduced_or_error": bad, "stops": stops,
        "cpu_hours": round(ledger_i.part_consumption(PART), 4),
    }  # fmt: skip
    if stops:
        doc.update(freed_full=None, outcome="INCONCLUSIVE (a stop)")
        return doc
    freed = {f"{r['key']}/{r['slot']}" for r in valid if r["power_full"] >= REQUIRED}
    freed_op = sum(r["power_e4op"] >= REQUIRED for r in valid)
    ratio = [r["recorded_error"] / r["sigma_full"] for r in valid]
    f, v = len(freed), len(valid)
    if len(unk) > MAX_UNK:
        outcome = "INCONCLUSIVE (too many unknown)"
    elif f >= 0.8 * v:
        outcome = (
            "an estimator is worth designing (for GLS estimators of a common step with "
            "E4's windows and nuisances, under the fitted covariance)"
        )
    elif f <= 0.4 * v:
        outcome = (
            "the full bound, with FAIL controls, is worth designing (limited for that "
            "class of estimators, under the fitted covariance)"
        )
    else:
        outcome = "INCONCLUSIVE"
    step1 = json.loads(STEP1.read_text("utf-8"))
    text = STEP1_CASES.read_text("utf-8")
    if hashlib.sha256(text.encode()).hexdigest() != step1["per_case_detail_sha256"]:
        raise SystemExit("step 1's per-case detail does not match its record: STOP")
    cases = json.loads(text)["t2a"]
    by_key = {f"{c['key']}/{c['slot']}": c for c in cases}
    per_injection = []
    for r in recs:
        k = f"{r['key']}/{r['slot']}"
        others = sorted(
            {b["test"] for b in by_key.get(k, {}).get("blockers", [])} - {"systematics"}
        )
        per_injection.append(
            {
                "injection": k,
                "status": r["status"],
                "freed": k in freed,
                "other_blocking_tests": others,
            }
        )
    recovered = [c for c in cases if c["blockers"]
                 and all(b["test"] == "systematics" for b in c["blockers"])
                 and f"{c['key']}/{c['slot']}" in freed]  # fmt: skip
    left = len(cases) - len(recovered)
    left_nonref = sum(1 for c in cases if c["verdict"] != "REFUTED") - len(recovered)
    doc.update({
        "freed_full": f, "freed_e4op": freed_op,
        "recorded_error_over_sigma_full_quartiles":
            [float(q) for q in np.quantile(ratio, [0.25, 0.5, 0.75])] if ratio else None,
        "tau_days_quartiles": [float(q) for q in np.quantile(
            [r["model"]["tau_days"] for r in valid], [0.25, 0.5, 0.75])] if valid else None,
        "t2a_losses_recoverable_if_the_freed_are": len(recovered),
        "t2a_losses_left": left,
        "margins": {"B (7)": T2A_ALLOWED - left,
                    "B, the 5 REFUTED staying (2)": T2A_IF_REFUTED_STAY - left_nonref,
                    "C conditional (49)": T2A_C - left},
        "per_injection": per_injection,
        "scope": "a GLS estimator of a common in-event step with E4's windows and baselines, "
        "under each host's fitted covariance, its uncertainty not propagated; no conclusion on "
        "the 615 injections and no draft",
        "outcome": outcome,
    })  # fmt: skip
    return doc


if __name__ == "__main__":
    if budgeted.LEDGER != ledger_i.HERE / "ledger.json":
        raise SystemExit("budgeted is not pointed at v0.5.4's ledger: refused")
    {"run": run, "summarize": summarize}[sys.argv[1]]()
