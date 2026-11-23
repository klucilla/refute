"""v0.5.9 Ephemeris entry: exploratory prototype (docs/plans/v0.5.9-plan.md; the maintainer's
decision of 2026-11-23, received at 19:28 local, #218, comment 7115813315).

**Exploratory from start to end.** Nothing here is a verdict, a candidate or a disposition. No
lock, no drand, no new target, no change in ``src/``. Every record carries the limits label
'WEAKENED; does not meet D1, D2, D4, T2a' and ``method_status: not_validated``.

**The question.** When the v0.5 battery enters through the TOI's ephemeris, with a bounded and
declared refit, and its output is checked on a declared set of local perturbations, do the cases
that changed class in v0.5.8 stabilise, and at what cost in decidability and CPU?

**What runs, per TOI of the set** (``prototype-set.json``, written once by ``draw``):
- **one download** (the adapter's, unchanged), its files hashed (SHA-256) and bound to the TOI's
  v0.5.6 record by ``seeded_run.provenance`` (other sectors are refused);
- **two entry modes on the same bytes**, each in its own work units, each unit checking the SHA-256
  of every input file before it reads them:
  - **E, the TOI's ephemeris:** a bounded two-pass refit (``entry_fit``);
  - **S, the battery's own search:** ``search_period``, then the battery's own refit
    (``attack_candidate``'s mask, detrend and ``finalize_candidate``), unchanged;
- **the base output of each mode:** the battery's tests evaluated at that mode's final ephemeris,
  held fixed (``evaluate_fixed``);
- **six local probes** around a decided base: epoch, period and duration, plus and minus one step
  (``probe_ephemerides``), each evaluated at its fixed ephemeris;
- **the consensus output:** the base class if every probe gives the same class, else INCONCLUSIVE
  with the first disagreeing probe (``consensus``). It only demotes.

**Codex's first three blocking items, at prototype level** (``docs/plans/v0.5.9-consensus/
codex-answer.md``):
1. **An explicit path** (``explicit_path``): only discovery version 2, with the corrections off and
   neither the version-3 nor the version-4 sections. Nothing reads or writes a schema; no version
   >= 3 rule is inherited. Any other plan is refused with its reason.
2. **A fixed evaluation** (``evaluate_fixed``): ``attack_candidate`` runs unchanged, except that
   its refit step (``pipeline.finalize_candidate``) is replaced, in this process only and only for
   that call, by a remeasurement at the given ephemeris (``box_stats``: depth, its error, SNR and
   the transits covered). Frozen: the detrending mask at the evaluated ephemeris; the likelihood
   objective; the epoch pivot (the cycle nearest the middle of the light curve); the box
   convention (half-open, at least three points); the tie rule (the first maximum in period,
   epoch, duration order). The probe steps actually used are recorded in every probe record.
3. **The centroid's numerical failures** (``guarded_centroid``): a singular or non-positive-definite
   covariance, an overflow, or a negative or non-finite quadratic form, in the observed statistic
   or in ``sky_power``'s simulations, give ``centroid_shift: INCONCLUSIVE`` with the reason, never
   ERROR. The guard is installed only during that test's call.

**Caps** (the decision, item 2): 15 GB of downloads, 8 CPU-h, 10 GB of disk peak, all measured
under ``.cache/v059``; the deadline 2026-12-07 23:59 local. No dependency changes.

**Machine.** CPUs 8 to 31 and BelowNormal (``pinrun``). Workers and simultaneous downloads follow
``seeded_run``'s business-hours limits (10 and 2 Monday to Friday, 08:00 to 18:00; otherwise 20
and 6). Batches stop admitting after 28 minutes. Resumable: one record per work unit, a recorded
unit never runs again, the run lock is held by the operating system.

**Files.** Pixel files are deleted when a TOI's last unit is recorded, with a manifest; light
curves at the end by ``clean``, by literal path with their SHA-256, inside ``.cache/v059`` only.

Usage (from the project root, pinned): ``prototype_run.py draw|run|bundle|clean``.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import os
import random
import sys
import threading
import time
import traceback
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
V057 = ROOT / "docs/validation/v0.5.7"
V058 = ROOT / "docs/validation/v0.5.8"
for _p in (V057, V058):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))
import seeded_run as sr  # noqa: E402 - the v0.5.7 runner, imported, never edited
import stability_report as v058  # noqa: E402 - the v0.5.8 report script, imported, never edited

WORK = ROOT / ".cache/v059"
DATA = WORK / "data"
LIGHTKURVE = DATA / "lightkurve"
RECORDS = WORK / "run/records"
SET_FILE = HERE / "prototype-set.json"
LEDGER = HERE / "prototype-ledger.json"
BUNDLE = HERE / "prototype-records.json"
REPORT_SCRIPT = HERE / "prototype_report.py"
PLAN = ROOT / "docs/plans/v0.5.9-plan.md"
LABEL = "WEAKENED; does not meet D1, D2, D4, T2a"

# --- the set (written once by ``draw``) -----------------------------------------------------
CONTROL_SEED_TEXT = b"refute v0.5.9 prototype: 2 unchanged controls per class, provenance same"
CLASSES = ("SURVIVED", "WEAKENED", "REFUTED", "INCONCLUSIVE")
DECIDED = ("SURVIVED", "WEAKENED", "REFUTED")
CONTROLS_PER_CLASS = 2
NUMERIC_KINDS = ("OverflowError", "LinAlgError")
NAMED_NUMERIC = {"734.01", "5218.01"}  # named by the decision; the rule must give exactly these

# --- caps -----------------------------------------------------------------------------------
CAP_CPU_HOURS = 8.0
CAP_DOWNLOAD_BYTES, ADMIT_DOWNLOAD_BYTES = 15e9, 14e9
CAP_DISK_BYTES, ADMIT_DISK_BYTES = 10e9, 8.5e9
DOWNLOAD_RESERVE_FACTOR, MIN_DOWNLOAD_RESERVE = 1.25, 0.3e9
DEADLINE = dt.datetime(2026, 12, 7, 23, 59)
FETCH_ATTEMPTS, FETCH_WAITS = 3, (60.0, 180.0)  # bounded retries inside one approved attempt
BATCH_SECONDS = sr.BATCH_SECONDS
MAX_UNIT_WALL = 25 * 60.0
CPU_FACTORS = {"fetch": 0.2, "base": 2.5, "probe": 1.5}  # times max(60 s, the v0.5.8 run's CPU)

# --- the entry (mode E) and the probes --------------------------------------------------------
PERIOD_WINDOW = 0.001  # relative: v0.5.6's identity tolerance
EPOCH_WINDOW_DURATIONS = 0.5  # +- half a TOI duration at the pivot: v0.5.6's identity rule
MAX_PERIOD_STEPS = 2000  # per side; a coarser step is recorded when it applies
MIN_IN_BOX = 3
PROBES = (
    ("p1", "epoch", +1),
    ("p2", "epoch", -1),
    ("p3", "period", +1),
    ("p4", "period", -1),
    ("p5", "duration", +1),
    ("p6", "duration", -1),
)
MODES = ("E", "S")
MAX_GIT_BYTES = 5_000_000  # raw outputs above 5 MB never enter git (the maintainer's rule)

_ORIGINAL_DISK_BYTES = sr.disk_bytes


# --- the set ----------------------------------------------------------------------------------


def _numeric_error(rec: dict) -> bool:
    return rec.get("status") == "ERROR" and str(rec.get("reason", "")).startswith(NUMERIC_KINDS)


def build_set() -> dict:
    """The 24 TOIs from the committed v0.5.8 and v0.5.6 records (pure: the tests call it).

    - ``changes``: the decided v0.5.6 records whose completed v0.5.8 run changed class (13);
    - ``reverse``: the drawn INCONCLUSIVE records whose completed run became decided (1);
    - ``numeric_errors``: the v0.5.8 runs that ended in a numerical ERROR (2);
    - ``controls``: per class, 2 records whose completed v0.5.8 run kept the v0.5.6 class, with
      provenance ``same`` and the fit on the TOI ephemeris; the keys sorted by TIC, then
      ``random.Random(int(sha256(CONTROL_SEED_TEXT + b'|' + class), 16)).sample(keys, 2)``.
    The three network ERRORs are not in the set."""
    s = json.loads(v058.SET_FILE.read_text("utf-8"))
    keys = [*s["decided"], *s["inconclusive_drawn"]]
    base = v058.v056()
    new = {r["target_key"]: r for r in v058.load()}
    if sorted(new) != sorted(keys):
        raise SystemExit("the v0.5.8 records and the v0.5.8 set disagree")

    def ok(k: str) -> bool:
        return new[k].get("status") == "OK"

    def toi(k: str) -> str:
        return str(new[k].get("toi"))

    changes = sorted(k for k in s["decided"]
                     if ok(k) and v058.outcome(new[k]) != v058.outcome(base[k]))  # fmt: skip
    reverse = sorted(k for k in s["inconclusive_drawn"]
                     if ok(k) and v058.outcome(new[k]) != v058.outcome(base[k]))  # fmt: skip
    numeric = sorted(k for k in keys if _numeric_error(new[k]))
    if {toi(k) for k in numeric} != NAMED_NUMERIC:
        raise SystemExit("the numerical ERRORs are not the two the decision names")
    taken = set(changes) | set(reverse) | set(numeric)
    controls, pools = {}, {}
    for c in CLASSES:
        pool = sorted(
            (k for k in keys
             if k not in taken and ok(k) and v058.outcome(base[k]) == c
             and v058.outcome(new[k]) == c
             and (new[k].get("provenance") or {}).get("overall") == "same"
             and (new[k].get("identity") or {}).get("matched") is True),
            key=lambda k: int(k.split("-")[1]),
        )  # fmt: skip
        seed = int(hashlib.sha256(CONTROL_SEED_TEXT + b"|" + c.encode()).hexdigest(), 16)
        controls[c] = random.Random(seed).sample(pool, CONTROLS_PER_CLASS)
        pools[c] = len(pool)
    every = [*changes, *reverse, *numeric, *(k for c in CLASSES for k in controls[c])]
    if len(set(every)) != len(every):
        raise SystemExit("the groups overlap")
    return {
        "schema": "refute-v059-prototype-set-1",
        "mode": "exploratory",
        "limits_label": LABEL,
        "method_status": "not_validated",
        "rule": (
            "changes: decided v0.5.6 records whose completed v0.5.8 run changed class; reverse: "
            "drawn INCONCLUSIVE records whose completed v0.5.8 run became decided; numeric_errors: "
            "v0.5.8 runs that ended in OverflowError or LinAlgError; controls: per class, 2 "
            "records whose completed v0.5.8 run kept the v0.5.6 class, with provenance same and "
            "identity matched, the keys sorted by TIC, then random.Random(int(sha256("
            "CONTROL_SEED_TEXT + b'|' + class), 16)).sample(keys, 2); the network ERRORs are out"
        ),
        "control_seed_text": CONTROL_SEED_TEXT.decode(),
        "sources_sha256": {
            "v058_records": hashlib.sha256(v058.BUNDLE.read_bytes()).hexdigest(),
            "v058_set": hashlib.sha256(v058.SET_FILE.read_bytes()).hexdigest(),
            **{
                f"v056_{p}": hashlib.sha256(v.read_bytes()).hexdigest()
                for p, v in v058.BUNDLES.items()
            },
        },  # fmt: skip
        "changes": changes,
        "reverse": reverse,
        "numeric_errors": numeric,
        "controls": controls,
        "control_pools": pools,
        "order": every,
        "tois": {k: toi(k) for k in every},
    }


def set_keys() -> list[str]:
    return list(json.loads(SET_FILE.read_text("utf-8"))["order"])


# --- pure functions: the box, the entry, the probes, the consensus ------------------------------


def pivot_epoch(t0: float, period: float, t_mid: float) -> float:
    """``t0`` moved by whole periods to the cycle nearest ``t_mid`` (the frozen epoch pivot)."""
    return float(t0 + round((t_mid - t0) / period) * period)


def box_stats(time_: np.ndarray, flux: np.ndarray, sigma: np.ndarray, period: float, t0: float,
              duration: float) -> dict:  # fmt: skip
    """The weighted box at a fixed ephemeris, over the finite points with a positive noise: in the
    box when the phase offset is in [-D/2, D/2); depth = weighted mean outside minus inside; its
    error from the weights; SNR = depth / error; the likelihood objective 0.5 * SNR^2 for a
    positive depth, else 0. ``n_transits`` counts the cycles with at least one point in that
    same box (the same membership as the depth; Codex's round 1, blocking item 1)."""
    ok = np.isfinite(time_) & np.isfinite(flux) & np.isfinite(sigma) & (sigma > 0)
    t, f, w = time_[ok], flux[ok], 1.0 / sigma[ok] ** 2
    ph = (t - t0 + 0.5 * period) % period - 0.5 * period
    inside = (ph >= -duration / 2.0) & (ph < duration / 2.0)
    n_in = int(inside.sum())
    cycles = int(np.unique(np.round((t[inside] - ph[inside] - t0) / period)).size)
    w_in, w_out = float(w[inside].sum()), float(w[~inside].sum())
    if n_in < MIN_IN_BOX or w_out <= 0:
        return {"depth": float("nan"), "depth_err": float("nan"), "snr": float("nan"),
                "log_likelihood": 0.0, "n_in": n_in, "n_transits": cycles}  # fmt: skip
    depth = float((w[~inside] * f[~inside]).sum() / w_out - (w[inside] * f[inside]).sum() / w_in)
    err = float(math.sqrt(1.0 / w_in + 1.0 / w_out))
    snr = depth / err
    return {"depth": depth, "depth_err": err, "snr": snr, "n_in": n_in, "n_transits": cycles,
            "log_likelihood": 0.5 * snr * snr if depth > 0 else 0.0}  # fmt: skip


def entry_grids(period: float, duration: float, span: float, search) -> dict:
    """The bounded window of mode E around the TOI's ephemeris, with the steps actually used.

    - period: +- ``PERIOD_WINDOW`` relative, both ends exact, in n equal steps per side with
      n = ceil(half / fine), where ``fine`` is the battery's fine period step
      (``finalize_candidate``: duration * period / (refine_samples_per_width * span) / 10); so
      the step is at most ``fine``, and no trial lies outside the window. n is at most
      ``MAX_PERIOD_STEPS`` (a coarser step is then used and recorded);
    - epoch: +- ``EPOCH_WINDOW_DURATIONS`` TOI durations at the pivot, in steps of
      duration / ``final_oversample``;
    - duration: ``final_duration_steps`` values over 0.5 to 1.5 TOI durations, kept below 0.9
      period and above 3 minutes (``finalize_candidate``'s grid)."""
    fine = duration * period / (search.refine_samples_per_width * span) / 10.0
    half = PERIOD_WINDOW * period
    n = max(1, math.ceil(half / fine))
    coarsened = n > MAX_PERIOD_STEPS
    if coarsened:
        n = MAX_PERIOD_STEPS
    step = half / n
    periods = period + half * np.arange(-n, n + 1) / n
    periods[0], periods[-1] = period - half, period + half  # the exact ends
    estep = duration / search.final_oversample
    m = int(round(EPOCH_WINDOW_DURATIONS * duration / estep))
    offsets = estep * np.arange(-m, m + 1)
    offsets[0], offsets[-1] = -EPOCH_WINDOW_DURATIONS * duration, EPOCH_WINDOW_DURATIONS * duration
    durations = duration * np.linspace(0.5, 1.5, search.final_duration_steps)
    durations = durations[(durations < 0.9 * period) & (durations > 3.0 / 1440.0)]
    return {
        "periods": periods,
        "offsets": offsets,
        "durations": durations,
        "period_step_days": float(step),
        "period_fine_step_days": float(fine),
        "period_step_coarsened": bool(coarsened),
        "period_points": int(periods.size),
        "epoch_step_days": float(estep),
        "epoch_points": int(offsets.size),
        "duration_points": int(durations.size),
        "span_days": float(span),
    }


def bounded_fit(time_: np.ndarray, flux: np.ndarray, sigma: np.ndarray, pivot: float,
                grids: dict) -> dict | None:  # fmt: skip
    """The maximum of the likelihood objective over the bounded grid (positive depths only).
    Ties: the first maximum in period, then epoch, then duration order. None when no box in the
    window has a positive depth."""
    ok = np.isfinite(time_) & np.isfinite(flux) & np.isfinite(sigma) & (sigma > 0)
    t, f, w = time_[ok], flux[ok], 1.0 / sigma[ok] ** 2
    total_w, total_s = float(w.sum()), float((w * f).sum())
    offsets, durations = grids["offsets"], grids["durations"]
    if durations.size == 0:
        return None
    lo = offsets[:, None] - durations[None, :] / 2.0
    hi = offsets[:, None] + durations[None, :] / 2.0
    reach = float(np.max(np.abs(offsets)) + np.max(durations) / 2.0)
    best = None
    for i, p in enumerate(grids["periods"]):
        ph = (t - pivot + 0.5 * p) % p - 0.5 * p
        near = np.abs(ph) <= reach
        order = np.argsort(ph[near], kind="stable")
        phs = ph[near][order]
        cw = np.concatenate(([0.0], np.cumsum(w[near][order])))
        cs = np.concatenate(([0.0], np.cumsum((w * f)[near][order])))
        i0 = np.searchsorted(phs, lo, side="left")
        i1 = np.searchsorted(phs, hi, side="left")
        n_in = i1 - i0
        w_in = cw[i1] - cw[i0]
        s_in = cs[i1] - cs[i0]
        w_out = total_w - w_in
        valid = (n_in >= MIN_IN_BOX) & (w_out > 0) & (w_in > 0)
        with np.errstate(invalid="ignore", divide="ignore"):
            depth = np.where(valid, (total_s - s_in) / w_out - s_in / w_in, np.nan)
            ll = np.where(valid & (depth > 0), 0.5 * depth**2 * w_in * w_out / (w_in + w_out),
                          -np.inf)  # fmt: skip
        j = int(np.argmax(ll))
        if not np.isfinite(ll.flat[j]):
            continue
        if best is None or ll.flat[j] > best["log_likelihood"]:
            a, b = np.unravel_index(j, ll.shape)
            err = math.sqrt(1.0 / w_in[a, b] + 1.0 / w_out[a, b])
            best = {
                "period": float(p),
                "t0": float(pivot + offsets[a]),
                "duration": float(durations[b]),
                "depth": float(depth[a, b]),
                "depth_err": float(err),
                "snr": float(depth[a, b] / err),
                "log_likelihood": float(ll[a, b]),
                "period_index": i,
                "epoch_index": int(a),
                "duration_index": int(b),
            }
    return best


def edges(best: dict, grids: dict) -> list[str]:
    """The window edges the optimum sits on (period or epoch: the entry is then unresolved)."""
    out = []
    if best["period_index"] in (0, grids["period_points"] - 1):
        out.append("period")
    if best["epoch_index"] in (0, grids["epoch_points"] - 1):
        out.append("epoch")
    return out


def probe_steps(period: float, duration: float, span: float, search) -> dict:
    """The declared probe offsets, frozen as formulas of the final fit (both modes): the epoch
    step duration / final_oversample, the battery's fine period step
    duration * period / (refine_samples_per_width * span) / 10, and one step of the duration
    grid, duration / (final_duration_steps - 1). For E they can differ from the steps its own
    window used (a coarsened period step, or the TOI's duration in place of the fit's); those are
    recorded in the fit's window."""
    return {
        "epoch_days": duration / search.final_oversample,
        "period_days": duration * period / (search.refine_samples_per_width * span) / 10.0,
        "duration_days": duration / (search.final_duration_steps - 1),
    }


def probe_ephemerides(period: float, t0: float, duration: float, span: float, search) -> list:
    """The six local probes, in the frozen order; the period probes pivot on ``t0`` (the pivot
    cycle)."""
    steps = probe_steps(period, duration, span, search)
    out = []
    for name, axis, sign in PROBES:
        p, e, d = period, t0, duration
        if axis == "epoch":
            e = t0 + sign * steps["epoch_days"]
        elif axis == "period":
            p = period + sign * steps["period_days"]
        else:
            d = duration + sign * steps["duration_days"]
        out.append({"probe": name, "axis": axis, "sign": sign, "period": p, "t0": e,
                    "duration": d, "step_days": steps[f"{axis}_days"]})  # fmt: skip
    return out


def consensus(base: dict | None, probes: dict[str, dict | None]) -> dict:
    """The consensus output of one mode. It only demotes:
    - a base that is missing or not OK has no output (its status is kept);
    - an INCONCLUSIVE base stays INCONCLUSIVE (no probe runs);
    - a decided base with a probe not recorded has no consensus yet (``status: INCOMPLETE``,
      kept apart from a recorded failure);
    - a decided base keeps its class only if all six probes are recorded, OK, and give that
      class; otherwise INCONCLUSIVE, naming the first disagreeing probe in the frozen order
      (a recorded probe that is not OK disagrees)."""
    if base is None or base.get("status") != "OK":
        return {"outcome": None, "status": None if base is None else base.get("status"),
                "reason": "no base output"}  # fmt: skip
    cls = base.get("outcome")
    if cls not in DECIDED:
        return {"outcome": cls, "status": "OK", "first_disagreeing": None,
                "reason": "the base is not decided; the rule only demotes"}  # fmt: skip
    missing = [n for n, _, _ in PROBES if probes.get(n) is None]
    if missing:
        return {"outcome": None, "status": "INCOMPLETE", "first_disagreeing": None,
                "reason": f"probes not recorded: {', '.join(missing)}"}  # fmt: skip
    for name, _, _ in PROBES:
        p = probes.get(name)
        why = None
        if p.get("status") != "OK":
            why = f"status {p.get('status')}"
        elif p.get("outcome") != cls:
            why = f"{p.get('outcome')} against {cls}"
        if why is not None:
            return {"outcome": "INCONCLUSIVE", "status": "OK", "first_disagreeing": name,
                    "reason": f"probe {name} disagrees: {why}"}  # fmt: skip
    return {"outcome": cls, "status": "OK", "first_disagreeing": None,
            "reason": "all six probes give the base class"}  # fmt: skip


def explicit_path(plan) -> str | None:
    """Codex's blocking item 1 at prototype level: the only path this script runs. None when the
    plan is on it, else the reason it is refused."""
    if plan.discovery is None or plan.discovery.version != 2:
        return "only discovery version 2 is supported"
    if plan.gauntlet.corrections.active:
        return "the corrections must be off"
    if plan.is_v051 or plan.is_v052 or not plan.v05:
        return "the version-3 and version-4 sections are not supported"
    return None


# --- the centroid guard (Codex's blocking item 3) ----------------------------------------------


SYMMETRY_RTOL = 1e-9  # relative to the largest entry
NEGATIVE_FORM_TOL = 1e-9  # a quadratic form below -this is a numerical failure


class NumericFailureError(Exception):
    """A numerical failure the guard turns into ``centroid_shift`` INCONCLUSIVE."""


def _check_pd(matrix, what: str) -> None:
    """Finite, symmetric (to ``SYMMETRY_RTOL``) and positive definite (Cholesky)."""
    m = np.asarray(matrix, dtype=float)
    if not np.all(np.isfinite(m)):
        raise NumericFailureError(f"{what} is not finite")
    if np.max(np.abs(m - m.T)) > SYMMETRY_RTOL * max(1.0, float(np.max(np.abs(m)))):
        raise NumericFailureError(f"{what} is not symmetric")
    try:
        np.linalg.cholesky(m)
    except np.linalg.LinAlgError as exc:
        raise NumericFailureError(f"{what} is not positive definite") from exc


def _check_forms(values, what: str) -> None:
    v = np.asarray(values, dtype=float)
    if not np.all(np.isfinite(v)):
        raise NumericFailureError(f"{what} is not finite")
    if np.any(v < -NEGATIVE_FORM_TOL):
        raise NumericFailureError(f"{what} is negative ({float(np.min(v))!r})")


def _weights(rows, where: str):
    """The sectors' weights, their sum, its inverse (the combined covariance) and that inverse's
    inverse, each checked; a singular inverse is a numerical failure."""
    for r in rows:
        _check_pd(r["cov_sky"], f"sector {r.get('sector')}'s sky covariance ({where})")
    try:
        weights = [np.linalg.inv(r["cov_sky"]) for r in rows]
        total = sum(weights)
        _check_pd(total, f"the summed weights ({where})")
        cov = np.linalg.inv(total)
        _check_pd(cov, f"the combined covariance ({where})")
        inv = np.linalg.inv(cov)
    except np.linalg.LinAlgError as exc:
        raise NumericFailureError(f"a singular matrix ({where}): {exc}") from exc
    return weights, cov, inv


def guarded_combine(original):
    """``centroid_v5.combine`` with its inputs and its heterogeneity form checked."""

    def combine(rows):
        _weights(rows, "observed")
        try:
            mean, cov, chi2 = original(rows)
        except np.linalg.LinAlgError as exc:
            raise NumericFailureError(f"a singular matrix (observed): {exc}") from exc
        _check_pd(cov, "the combined covariance (observed)")
        _check_forms([chi2], "the observed heterogeneity quadratic form")
        return mean, cov, chi2

    return combine


def guarded_sky_power(original, module):
    """``centroid_v5.sky_power`` with its inputs checked, and, during its call only, its
    simulations' ``simulated_probability`` wrapped: before the rule reads the draws, both
    simulated quadratic forms (heterogeneity and significance) are computed as ``sky_power``
    computes them and checked."""

    def sky_power(rows, *args, **kwargs):
        weights, cov, inv = _weights(rows, "simulations")
        plain = module.simulated_probability

        def simulated_probability(draw, reject, seed, *a, **k):
            def checked(o):
                mean = np.einsum(
                    "ij,nj->ni", cov, sum(o[:, i] @ w.T for i, w in enumerate(weights))
                )
                het = sum(
                    np.einsum("ni,ij,nj->n", o[:, i] - mean, w, o[:, i] - mean)
                    for i, w in enumerate(weights)
                )
                _check_forms(het, "a simulated heterogeneity quadratic form")
                _check_forms(np.einsum("ni,ij,nj->n", mean, inv, mean),
                             "a simulated significance quadratic form")  # fmt: skip
                return reject(o)

            return plain(draw, checked, seed, *a, **k)

        module.simulated_probability = simulated_probability
        try:
            return original(rows, *args, **kwargs)
        except np.linalg.LinAlgError as exc:
            raise NumericFailureError(f"a singular matrix (simulations): {exc}") from exc
        finally:
            module.simulated_probability = plain

    return sky_power


def guarded_sigma(original):
    """``battery.gaussian_sigma_from_chi2`` with its input checked and an overflow caught."""

    def gaussian_sigma_from_chi2(chi2, dof):
        _check_forms([chi2], "a significance quadratic form")
        try:
            return original(max(0.0, chi2), dof)
        except OverflowError as exc:
            raise NumericFailureError(f"overflow in the significance of chi2 = {chi2!r}") from exc

    return gaussian_sigma_from_chi2


def guarded_centroid(original):
    """``check_centroid_v5`` with the guards installed only during its call. Only a
    ``NumericFailureError`` raised by a guard (at the operation it checks) becomes
    ``centroid_shift`` INCONCLUSIVE, with its reason and zero coverage; any other exception
    propagates unchanged. Every patch is restored in ``finally``."""

    def check(pixels, sectors_aux, candidate, plan, seed):
        from refute.core.verdict import Severity, TestResult, TestStatus
        from refute.packs.tess import battery, centroid_v5

        saved = (centroid_v5.combine, centroid_v5.sky_power, battery.gaussian_sigma_from_chi2)
        centroid_v5.combine = guarded_combine(saved[0])
        centroid_v5.sky_power = guarded_sky_power(saved[1], centroid_v5)
        battery.gaussian_sigma_from_chi2 = guarded_sigma(saved[2])
        try:
            return original(pixels, sectors_aux, candidate, plan, seed)
        except NumericFailureError as exc:
            return TestResult(
                centroid_v5.NAME,
                TestStatus.INCONCLUSIVE,
                Severity.FATAL,
                f"numerical failure, INCONCLUSIVE by the v0.5.9 prototype's guard: {exc}",
                metrics={"numerical_failure": {"reason": str(exc)}},
                coverage=0,
                coverage_unit=centroid_v5.UNIT,
            )
        finally:
            centroid_v5.combine, centroid_v5.sky_power = saved[0], saved[1]
            battery.gaussian_sigma_from_chi2 = saved[2]

    return check


# --- the evaluation at a fixed ephemeris (Codex's blocking item 2) ------------------------------


def masked_flat(data, plan, period: float, t0: float, duration: float):
    """``attack_candidate``'s mask, detrend and per-point noise at an ephemeris (the corrections
    are off on the explicit path, so the raw curve is detrended directly)."""
    from refute.packs.tess.detrend import detrend
    from refute.packs.tess.events import per_point_sigma, transit_mask

    half = plan.detrend.transit_mask_half_width_durations * duration
    mask = transit_mask(data.lc.time, period, t0, half)
    flat = detrend(data.lc, plan.detrend, mask=mask)
    sigma = per_point_sigma(flat, transit_mask(flat.time, period, t0, half))
    return flat, sigma


def evaluate_fixed(data, plan, period: float, t0: float, duration: float, sde: float) -> dict:
    """The battery's tests at a fixed ephemeris: ``attack_candidate`` unchanged, its refit step
    replaced for this call by ``box_stats`` at the ephemeris, the centroid guarded; then the
    coverage and sensitivity rules, deferral and the decisive aggregate, as ``seeded_run``."""
    from refute.core.sensitivity import enforce_sensitivity
    from refute.core.verdict import aggregate, defer_tests, enforce_coverage
    from refute.packs.tess import centroid_v5, pipeline
    from refute.packs.tess.power import registry_for
    from refute.packs.tess.types import Candidate

    def fixed(lc, period_, duration_hint, params, sde_, sigma=None):
        if period_ != period or duration_hint != duration or sigma is None:
            raise RuntimeError("the fixed evaluation was called off its ephemeris")
        st = box_stats(lc.time, lc.flux, sigma, period, t0, duration)
        return Candidate(period=period, t0=t0, duration=duration, depth=st["depth"],
                         depth_err=st["depth_err"], snr=st["snr"],
                         log_likelihood=st["log_likelihood"], sde=float(sde_),
                         n_transits=st["n_transits"])  # fmt: skip

    entry = Candidate(period=period, t0=t0, duration=duration, depth=0.0, depth_err=float("nan"),
                      snr=0.0, log_likelihood=0.0, sde=float(sde), n_transits=0)  # fmt: skip
    saved = (pipeline.finalize_candidate, centroid_v5.check_centroid_v5)
    pipeline.finalize_candidate = fixed
    centroid_v5.check_centroid_v5 = guarded_centroid(saved[1])
    try:
        gauntlet = pipeline.attack_candidate(data, entry, plan, None, None, None)
    finally:
        pipeline.finalize_candidate, centroid_v5.check_centroid_v5 = saved
    tests = enforce_coverage(gauntlet.tests)
    tests = enforce_sensitivity(tests, registry_for(plan))
    tests, deferred = defer_tests(tests, dict(plan.discovery.stages), 2)
    decisive, _ = pipeline.expected_by_role(plan, False)
    verdict, reason = aggregate([t for t in tests if t.name in decisive], expected=decisive)
    cand = gauntlet.candidate
    numeric = {t.name: t.message for t in tests if "numerical_failure" in (t.metrics or {})}
    return {
        "candidate": {
            "period_days": float(cand.period),
            "t0_btjd": float(cand.t0),
            "duration_hours": float(cand.duration) * 24.0,
            "depth": float(cand.depth),
            "depth_err": float(cand.depth_err),
            "snr": float(cand.snr),
            "n_transits": int(cand.n_transits),
        },
        "tests": {t.name: sr._test(t) for t in tests},
        "decisive": list(decisive),
        "deferred": deferred,
        "outcome": verdict.value,
        "outcome_reason": reason,
        "numerical_failures_guarded": numeric,
    }


def entry_fit(data, plan, toi: dict, t_mid: float, span: float) -> dict:
    """Mode E: two passes in the bounded window around the TOI's ephemeris at the pivot. Pass 1
    masks the TOI's ephemeris; pass 2 masks pass 1's fit; both search the same window, anchored
    on the TOI. Unresolved (no positive box, or the optimum on the period or epoch edge) gives
    INCONCLUSIVE with the reason."""
    values = (toi.get("period"), toi.get("epoch"), toi.get("duration"))
    if not all(isinstance(v, float) and math.isfinite(v) for v in values) or not (
        0.0 < toi["duration"] < toi["period"]
    ):
        return {"resolved": False, "passes": [],
                "unresolved_reason": "the TOI ephemeris is missing or invalid"}  # fmt: skip
    pivot = pivot_epoch(toi["epoch"], toi["period"], t_mid)
    grids = entry_grids(toi["period"], toi["duration"], span, plan.search)
    ephem = (toi["period"], pivot, toi["duration"])
    passes = []
    best = None
    for _ in (1, 2):
        flat, sigma = masked_flat(data, plan, *ephem)
        best = bounded_fit(flat.time, flat.flux, sigma, pivot, grids)
        if best is None:
            break
        passes.append({k: best[k] for k in ("period", "t0", "duration", "depth", "depth_err",
                                            "snr", "log_likelihood")})  # fmt: skip
        ephem = (best["period"], best["t0"], best["duration"])
    window = {k: v for k, v in grids.items() if not isinstance(v, np.ndarray)}
    window.update({"pivot_btjd": pivot, "period_window_relative": PERIOD_WINDOW,
                   "epoch_window_durations": EPOCH_WINDOW_DURATIONS})  # fmt: skip
    out = {"window": window, "passes": passes, "resolved": False, "unresolved_reason": None}
    if best is None:
        out["unresolved_reason"] = "no box in the window has a positive depth"
        return out
    on = edges(best, grids)
    out["duration_on_edge"] = best["duration_index"] in (0, grids["duration_points"] - 1)
    if on:
        out["unresolved_reason"] = f"the optimum is on the window's {' and '.join(on)} edge"
        out["edge"] = on
        return out
    final = {"period": best["period"], "t0": best["t0"], "duration": best["duration"], "sde": 0.0}
    out.update({"resolved": True, "final": final})
    return out


def search_fit(data, plan, searched, t_mid: float) -> dict:
    """Mode S: the battery's own search, then its own refit (``attack_candidate``'s mask, detrend
    and ``finalize_candidate``, unchanged); the final epoch moved to the pivot cycle."""
    from refute.packs.tess.search import finalize_candidate, search_period

    found = search_period(searched, plan.search)
    cand = found.candidate
    if cand is None:
        return {"resolved": False,
                "unresolved_reason": f"the search found no candidate "
                                     f"({found.diagnostics.get('reason')})"}  # fmt: skip
    flat, sigma = masked_flat(data, plan, cand.period, cand.t0, cand.duration)
    final = finalize_candidate(flat, cand.period, cand.duration, plan.search, cand.sde, sigma)
    return {
        "resolved": True,
        "search": {"period_days": float(cand.period), "t0_btjd": float(cand.t0),
                   "duration_hours": float(cand.duration) * 24.0, "snr": float(cand.snr),
                   "sde": float(cand.sde)},  # fmt: skip
        "refit": {"period_days": float(final.period), "t0_btjd": float(final.t0),
                  "duration_hours": float(final.duration) * 24.0, "snr": float(final.snr)},
        "final": {"period": float(final.period),
                  "t0": pivot_epoch(float(final.t0), float(final.period), t_mid),
                  "duration": float(final.duration), "sde": float(cand.sde)},
    }  # fmt: skip


# --- the work units (in a worker) ------------------------------------------------------------


def unit_key(target_key: str, kind: str, mode: str | None = None, probe: str | None = None) -> str:
    """``TIC-1.fetch``, ``TIC-1.E.base`` or ``TIC-1.E.p3``."""
    if kind == "fetch":
        return f"{target_key}.fetch"
    if kind == "base":
        return f"{target_key}.{mode}.base"
    return f"{target_key}.{mode}.{probe}"


def _point_worker():
    import seeded_run as w

    w.DATA = DATA
    w.LIGHTKURVE = LIGHTKURVE
    return w


def _read_record(key: str) -> dict | None:
    path = RECORDS / f"{key}.json"
    return json.loads(path.read_text("utf-8")) if path.exists() else None


def _toi(unit: dict) -> dict:
    return {"period": float(unit["period_days"]), "epoch": float(unit["epoch_bjd"]) - sr.BTJD,
            "duration": float(unit["duration_hours"]) / 24.0}  # fmt: skip


def _compare_manifest(now: list[dict], then: list[dict] | None) -> str:
    if not then:
        return "unknown"
    a = {f["name"]: f["sha256"] for f in now}
    b = {f["name"]: f["sha256"] for f in then}
    return "same" if a == b else "different"


class DownloadAllowanceError(Exception):
    """A fetch unit reached its byte allowance before a product download."""


def metered(adapter, allowance: float, meter: dict):
    """Context manager: the adapter's ``download_checked`` and ``discard_if_incomplete`` wrapped
    for one fetch unit (this process only). Every completed product's bytes and every discarded
    partial file's bytes are added to ``meter``; a product download is refused once the metered
    bytes reach ``allowance``. Limits, stated: a partial transfer that leaves no file, and the
    catalog queries, are not metered."""
    import contextlib

    @contextlib.contextmanager
    def ctx():
        plain_dl, plain_discard = adapter.download_checked, adapter.discard_if_incomplete

        def discard(path, cache_root):
            p = Path(path)
            size = p.stat().st_size if p.is_file() else 0
            removed = plain_discard(path, cache_root)
            if removed:
                meter["partial_bytes"] += size
            return removed

        def download(product, row_name, download_dir, **kwargs):
            used = meter["completed_bytes"] + meter["partial_bytes"]
            if used >= allowance:
                raise DownloadAllowanceError(
                    f"{used} bytes metered, at the unit's allowance of {int(allowance)}"
                )
            path = plain_dl(product, row_name, download_dir, **kwargs)
            meter["completed_bytes"] += Path(path).stat().st_size
            meter["files"] += 1
            return path

        adapter.download_checked, adapter.discard_if_incomplete = download, discard
        try:
            yield meter
        finally:
            adapter.download_checked, adapter.discard_if_incomplete = plain_dl, plain_discard

    return ctx()


def _fetch(unit: dict, test_plan: dict, rec: dict, w) -> None:
    from refute.core.io import read_json
    from refute.packs.tess import adapter
    from refute.packs.tess.adapter import NoProductsError, TessAdapter, manifest_path
    from refute.packs.tess.discover.measure import stage_plan

    no_link_roots()
    plan_dict = stage_plan(test_plan, 2)
    tgt = {"key": unit["target_key"], "tic_id": int(unit["tic_id"])}
    before = {p.name for p in w._tic_files(int(unit["tic_id"]))}
    attempts = []
    meter = {"completed_bytes": 0, "partial_bytes": 0, "files": 0}
    rec["download_allowance_bytes"] = int(unit["allowance_bytes"])
    started = time.time()
    try:
        for i in range(FETCH_ATTEMPTS):
            t = time.time()
            try:
                with metered(adapter, unit["allowance_bytes"], meter):
                    if w._DOWNLOADS is None:
                        TessAdapter().fetch(tgt, plan_dict, DATA)
                    else:
                        with w._DOWNLOADS:
                            TessAdapter().fetch(tgt, plan_dict, DATA)
                attempts.append({"attempt": i + 1, "ok": True, "wall_seconds": time.time() - t})
                break
            except NoProductsError as exc:
                attempts.append({"attempt": i + 1, "ok": False, "error": f"NoProductsError: {exc}",
                                 "wall_seconds": time.time() - t})  # fmt: skip
                rec.update({"status": "MISSING_PRODUCTS", "reason": str(exc)})
                return
            except DownloadAllowanceError as exc:
                attempts.append({"attempt": i + 1, "ok": False, "error": str(exc),
                                 "wall_seconds": time.time() - t})  # fmt: skip
                rec.update({"status": "DOWNLOAD_ALLOWANCE", "reason": str(exc)})
                return
            except Exception as exc:  # noqa: BLE001 - bounded retries, each recorded
                attempts.append({"attempt": i + 1, "ok": False,
                                 "error": f"{type(exc).__name__}: {exc}"[:500],
                                 "wall_seconds": time.time() - t})  # fmt: skip
                if i + 1 == FETCH_ATTEMPTS:
                    raise
                time.sleep(FETCH_WAITS[i])
    finally:
        rec["fetch_attempts"] = attempts
        rec["fetch_wall_seconds"] = time.time() - started
        rec["metered_download_bytes"] = meter["completed_bytes"] + meter["partial_bytes"]
        rec["metered"] = dict(meter)
        if w._FETCHED is not None:
            w._FETCHED.put(unit["key"])
    mpath = manifest_path(DATA, int(unit["tic_id"]))
    rec["manifest"] = {"path": mpath.relative_to(DATA).as_posix(), "sha256": w.sha256_path(mpath)}
    manifest = read_json(mpath)
    every = [*manifest["files"], *manifest["pixel_files"]]
    inputs, bad = [], []
    for f in every:
        digest = w.sha256_path(DATA / f["path"])
        if digest != f["sha256"]:
            bad.append(f["name"])
        inputs.append({"name": f["name"], "path": f["path"], "sector": int(f["sector"]),
                       "bytes": int(f["bytes"]), "sha256": digest})  # fmt: skip
    rec["inputs"] = inputs
    rec["bytes"] = w._bytes(manifest)
    rec["downloaded_bytes"] = sum(int(f["bytes"]) for f in every if f["name"] not in before)
    rec["reused_bytes"] = sum(int(f["bytes"]) for f in every if f["name"] in before)
    rec["light_curve_sectors"] = sorted({int(f["sector"]) for f in manifest["files"]})
    rec["pixel_file_sectors"] = sorted({int(f["sector"]) for f in manifest["pixel_files"]})
    rec["light_curve_manifest"] = [w._file_entry(f) for f in manifest["files"]]
    rec["tpf_manifest"] = [w._file_entry(f) for f in manifest["pixel_files"]]
    if bad:
        rec.update({"status": "INPUTS_CORRUPT", "reason": f"SHA-256 differs from the manifest: "
                    f"{bad[:5]}"})  # fmt: skip
        return
    prov = w.provenance(manifest["files"], manifest["pixel_files"], unit.get("hist56"))
    v58 = unit.get("v058") or {}
    prov["v058_light_curves"] = _compare_manifest(
        manifest["files"], v58.get("light_curve_manifest")
    )
    prov["v058_pixel_files"] = _compare_manifest(manifest["pixel_files"], v58.get("tpf_manifest"))
    rec["provenance"] = prov
    if prov["refuse"]:
        rec.update({"status": "INPUTS_DIFFER",
                    "reason": "the downloaded sectors differ from the v0.5.6 record"})  # fmt: skip
        return
    rec["status"] = "OK"


def _load(unit: dict, test_plan: dict, rec: dict, w):
    """The same input bytes for every unit: each file's SHA-256 is checked against the fetch
    unit's record before anything is read. Returns (data, plan) or None (the record says why)."""
    from refute.packs.tess.adapter import TessAdapter
    from refute.packs.tess.discover.measure import stage_plan
    from refute.packs.tess.params import TessTestPlan

    fetched = _read_record(unit_key(unit["target_key"], "fetch"))
    if fetched is None or fetched.get("status") != "OK":
        rec.update({"status": "NOT_RUN", "reason": "the fetch unit is not OK"})
        return None
    pinned = [*fetched["inputs"], {"name": "manifest", **fetched["manifest"]}]
    changed = [f["name"] for f in pinned
               if w.sha256_path(DATA / f["path"]) != f["sha256"]]  # fmt: skip
    rec["inputs_checked"] = len(
        pinned
    )  # the FITS files and the adapter's manifest (star, neighbors)
    if changed:
        rec.update({"status": "INPUTS_CHANGED", "reason": f"SHA-256 changed: {changed[:5]}"})
        return None
    rec["provenance"] = fetched.get("provenance")
    plan_dict = stage_plan(test_plan, 2)
    plan = TessTestPlan.model_validate(plan_dict)
    why = explicit_path(plan)
    if why is not None:
        rec.update({"status": "PATH_REFUSED", "reason": why})
        return None
    tgt = {"key": unit["target_key"], "tic_id": int(unit["tic_id"])}
    data = TessAdapter().load(tgt, plan_dict, DATA)
    return data, plan


def _identity(toi: dict, final: dict | None, data) -> dict:
    from refute.packs.tess.pipeline import matching_factor
    from refute.packs.tess.search import count_transits

    found = None if final is None else float(final["period"])
    factor = matching_factor(toi["period"], found, sr.FACTORS, sr.IDENTITY_TOLERANCE)
    covered = count_transits(data.lc, toi["period"], toi["epoch"], toi["duration"])
    return sr.ephemeris_record(
        toi["period"], toi["epoch"], toi["duration"], found,
        None if final is None else float(final["t0"]), factor,
        float(np.nanmin(data.lc.time)), float(np.nanmax(data.lc.time)), covered,
    )  # fmt: skip


def _base(unit: dict, test_plan: dict, rec: dict, w) -> None:
    from refute.packs.tess.detrend import detrend
    from refute.packs.tess.pipeline import global_prewhitening

    loaded = _load(unit, test_plan, rec, w)
    if loaded is None:
        return
    data, plan = loaded
    toi = _toi(unit)
    t_mid = 0.5 * (float(np.nanmin(data.lc.time)) + float(np.nanmax(data.lc.time)))
    span = float(data.lc.span)
    t = time.process_time()
    if unit["mode"] == "E":
        fit = entry_fit(data, plan, toi, t_mid, span)
    else:
        _, searched = global_prewhitening(data, plan, detrend(data.lc, plan.detrend))
        fit = search_fit(data, plan, searched, t_mid)
    rec["fit_cpu_seconds"] = time.process_time() - t
    rec["fit"] = fit
    rec["t_mid_btjd"], rec["span_days"] = t_mid, span
    final = fit.get("final") if fit.get("resolved") else None
    rec["identity"] = _identity(toi, final, data)
    if final is None:
        rec.update({"status": "OK", "outcome": "INCONCLUSIVE", "coverage_state": "unavailable",
                    "outcome_reason": f"entry unresolved: {fit['unresolved_reason']}",
                    "tests": {}})  # fmt: skip
        return
    t = time.process_time()
    ev = evaluate_fixed(data, plan, final["period"], final["t0"], final["duration"], final["sde"])
    rec["evaluation_cpu_seconds"] = time.process_time() - t
    rec.update({"status": "OK", "coverage_state": "measured", **ev})


def _probe(unit: dict, test_plan: dict, rec: dict, w) -> None:
    base = _read_record(unit_key(unit["target_key"], "base", unit["mode"]))
    if base is None or base.get("status") != "OK" or base.get("outcome") not in DECIDED:
        rec.update({"status": "NOT_RUN", "reason": "the base is not a decided OK output"})
        return
    loaded = _load(unit, test_plan, rec, w)
    if loaded is None:
        return
    data, plan = loaded
    final = base["fit"]["final"]
    spec = next(p for p in probe_ephemerides(final["period"], final["t0"], final["duration"],
                                             base["span_days"], plan.search)
                if p["probe"] == unit["probe"])  # fmt: skip
    rec["probe_spec"] = spec
    t = time.process_time()
    ev = evaluate_fixed(data, plan, spec["period"], spec["t0"], spec["duration"], final["sde"])
    rec["evaluation_cpu_seconds"] = time.process_time() - t
    differ = sorted(n for n in set(ev["tests"]) | set(base.get("tests") or {})
                    if (ev["tests"].get(n) or {}).get("status")
                    != ((base.get("tests") or {}).get(n) or {}).get("status"))  # fmt: skip
    rec.update({"status": "OK", "coverage_state": "measured", **ev,
                "tests_differing_from_base": differ})  # fmt: skip


_HALT = None  # the batch's halt event, in a worker (set by ``init_worker``)


def init_worker(semaphore, fetched, halt) -> None:
    """A worker's initializer: ``seeded_run``'s download semaphore and fetched queue, and the
    batch's halt event."""
    global _HALT
    w = _point_worker()
    w._init(semaphore, fetched)
    _HALT = halt


class _Watchdog(threading.Thread):
    """In a worker, during one unit: when the batch's halt event is set (a cap is reached), the
    unit's main thread is interrupted, so the unit ends with its record."""

    def __init__(self) -> None:
        super().__init__(daemon=True)
        self.done = threading.Event()
        self.fired = False

    def run(self) -> None:
        import _thread

        while not self.done.wait(1.0):
            if _HALT is not None and _HALT.is_set():
                self.fired = True
                _thread.interrupt_main()
                return


def run_unit(unit: dict, test_plan: dict, _hist: dict | None) -> dict:
    """One work unit, in a worker. Any failure is recorded, never hidden."""
    w = _point_worker()
    if unit["kind"] != "fetch" and w._FETCHED is not None:
        w._FETCHED.put(unit["key"])  # no download in this unit
    started, wall = time.process_time(), time.time()
    dog = _Watchdog()
    rec = {
        "unit_key": unit["key"],
        "target_key": unit["target_key"],
        "tic_id": unit["tic_id"],
        "toi": unit["toi"],
        "part": unit["part"],
        "arm": unit["arm"],
        "group": unit["group"],
        "kind": unit["kind"],
        "entry_mode": unit.get("mode"),
        "probe": unit.get("probe"),
        "phase": "v0.5.9",
        "mode": "exploratory",
        "limits_label": LABEL,
        "method_status": "not_validated",
        "started_utc": sr.utc(wall),
        "worker_pid": os.getpid(),
        "test_plan_source": sr.PLANS[unit["part"]].relative_to(ROOT).as_posix(),
        "coverage_state": "unavailable",
    }
    try:
        if _HALT is not None and _HALT.is_set():
            raise KeyboardInterrupt
        dog.start()
        {"fetch": _fetch, "base": _base, "probe": _probe}[unit["kind"]](unit, test_plan, rec, w)
    except KeyboardInterrupt:
        if not (dog.fired or (_HALT is not None and _HALT.is_set())):
            raise
        rec.update(
            {
                "status": "STOPPED_AT_CAP",
                "coverage_state": "unavailable",
                "reason": "the batch reached a cap (CPU or disk) while this unit ran",
            }
        )
    except Exception as exc:  # noqa: BLE001 - recorded, never hidden
        rec.update({"status": "ERROR", "reason": f"{type(exc).__name__}: {exc}",
                    "trace": traceback.format_exc()[-1500:]})  # fmt: skip
    finally:
        dog.done.set()
        rec["cpu_seconds"] = time.process_time() - started
        rec["wall_seconds"] = time.time() - wall
        rec["ended_utc"] = sr.utc()
    return rec


# --- the controller ----------------------------------------------------------------------------

_UNITS: dict[str, dict] = {}
SAMPLE_SECONDS = 2.0
CPU_HALT_MARGIN_HOURS = 0.02  # the live halt fires this far below the CPU cap


def no_link_roots() -> None:
    """Refuse a run whose cache roots are links or junctions (Codex's round 1, item 6): every
    existing component from ``.cache`` down to the records and the light curves."""
    cache = ROOT / ".cache"
    for leaf in (LIGHTKURVE, RECORDS, WORK / "run/tpf-deletions"):
        p = leaf
        while True:
            if p.exists() and (p.is_symlink() or p.is_junction()):
                raise SystemExit(f"refused: {p.relative_to(ROOT).as_posix()} is a link")
            if p == cache or p.parent == p:
                break
            p = p.parent


def _v058_records() -> dict[str, dict]:
    return {r["target_key"]: r for r in v058.load()}


def targets() -> list[dict]:
    """The set's TOIs, in the set's order, with their draw entries and the v0.5.6 and v0.5.8
    facts the units need."""
    doc = json.loads(SET_FILE.read_text("utf-8"))
    group = {k: g for g in ("changes", "reverse", "numeric_errors") for k in doc[g]}
    group.update({k: f"control:{c}" for c, ks in doc["controls"].items() for k in ks})
    every = {t["key"]: t for t in sr.targets()}
    hist, new = sr.search_records(), _v058_records()
    out = []
    for k in doc["order"]:
        t = dict(every[k])
        h = hist.get(k) or {}
        n = new.get(k) or {}
        t.update({
            "group": group[k],
            "hist56": {x: h[x] for x in ("light_curve_sectors", "pixel_file_sectors",
                                         "light_curve_manifest", "tpf_manifest") if x in h},
            "v058": {x: n.get(x) for x in ("light_curve_manifest", "tpf_manifest")},
            "v058_cpu": float(n.get("cpu_seconds") or 0.0),
            "v058_bytes": int(n.get("bytes") or 0),
            "v058_fetch_wall": float(n.get("fetch_wall_seconds") or 0.0),
        })  # fmt: skip
        out.append(t)
    return out


def download_reserve(u: dict) -> float:
    """A fetch unit's byte allowance, enforced in the worker (``metered``): 1.25 times the TOI's
    v0.5.8 bytes, at least 0.3 GB. Other units download nothing."""
    if u["kind"] != "fetch":
        return 0.0
    return max(MIN_DOWNLOAD_RESERVE, DOWNLOAD_RESERVE_FACTOR * (u.get("v058_bytes") or 0))


def _unit(t: dict, kind: str, mode: str | None = None, probe: str | None = None) -> dict:
    key = unit_key(t["key"], kind, mode, probe)
    u = {**t, "target_key": t["key"], "key": key, "kind": kind, "mode": mode, "probe": probe}
    u["allowance_bytes"] = download_reserve(u)
    _UNITS[key] = u
    return u


def ready_units(all_targets: list[dict]) -> list[dict]:
    """The units whose inputs are recorded and which are not, in the set's order (the changes
    first, then the reverse case, the numerical ERRORs and the controls)."""
    out = []
    for t in all_targets:
        f = _read_record(unit_key(t["key"], "fetch"))
        if f is None:
            out.append(_unit(t, "fetch"))
            continue
        if f.get("status") != "OK":
            continue
        for mode in MODES:
            b = _read_record(unit_key(t["key"], "base", mode))
            if b is None:
                out.append(_unit(t, "base", mode))
                continue
            if b.get("status") != "OK" or b.get("outcome") not in DECIDED:
                continue
            for name, _, _ in PROBES:
                if _read_record(unit_key(t["key"], "probe", mode, name)) is None:
                    out.append(_unit(t, "probe", mode, name))
    return out


def required_units(t: dict) -> list[str]:
    """Every unit a TOI needs, from its recorded units: the fetch; if it is OK, both bases; for a
    decided OK base, its six probes."""
    keys = [unit_key(t["key"], "fetch")]
    f = _read_record(keys[0])
    if f is None or f.get("status") != "OK":
        return keys
    for mode in MODES:
        keys.append(unit_key(t["key"], "base", mode))
        b = _read_record(keys[-1])
        if b is not None and b.get("status") == "OK" and b.get("outcome") in DECIDED:
            keys += [unit_key(t["key"], "probe", mode, n) for n, _, _ in PROBES]
    return keys


def target_done(t: dict) -> bool:
    return all(_read_record(k) is not None for k in required_units(t))


def est_cpu_hours(u: dict) -> float:
    base = max(60.0, u.get("v058_cpu") or 0.0, 15.0 * len(u.get("sectors") or []))
    return CPU_FACTORS[u["kind"]] * base / 3600.0


def est_wall(u: dict) -> float:
    if u["kind"] == "fetch":
        return min(MAX_UNIT_WALL, 1.5 * (u.get("v058_fetch_wall") or 120.0) + 60.0)
    return min(MAX_UNIT_WALL, 3.0 * est_cpu_hours(u) * 3600.0 + 30.0)


def downloaded_so_far() -> int:
    """The bytes charged to the download cap: per fetch record, the larger of the metered
    transfer and the manifest's new files; plus every interrupted fetch's whole allowance."""
    total = 0
    for p in sorted(RECORDS.glob("*.fetch.json")):
        r = json.loads(p.read_text("utf-8"))
        total += max(int(r.get("metered_download_bytes") or 0), int(r.get("downloaded_bytes") or 0))
    ledger = sr._ledger()
    return total + sum(int(i.get("bytes", 0)) for i in ledger.get("download_interruptions", []))


def disk_bytes(root: Path | None = None) -> int:
    """The disk under ``.cache/v059`` by default."""
    return _ORIGINAL_DISK_BYTES(WORK if root is None else root)


def write_json(path: Path, obj: dict) -> str:
    """Atomic write with a temporary name unique to the process and the thread, read back. A
    replace refused by Windows (v0.5.8's heartbeat departure) is tried again up to 5 times,
    0.2 s apart."""
    text = json.dumps(obj, indent=1, default=sr._plain)
    tmp = path.with_name(f"{path.name}.{os.getpid()}.{threading.get_ident()}.tmp")
    tmp.write_text(text, "utf-8", newline="\n")
    for attempt in range(6):
        try:
            os.replace(tmp, path)
            break
        except PermissionError:
            if attempt == 5:
                raise
            time.sleep(0.2)
    if path.read_text("utf-8") != text:
        raise RuntimeError(f"{path.name} did not read back as written")
    return text


def finish(rec: dict) -> str | None:
    """Write the unit's record; when the TOI's last required unit is recorded, release its pixel
    files (the manifest first, then each file by literal path and SHA-256)."""
    RECORDS.mkdir(parents=True, exist_ok=True)
    try:
        write_json(RECORDS / f"{rec['unit_key']}.json", rec)
    except Exception as exc:  # noqa: BLE001 - stops the run
        return f"{rec['unit_key']}'s record could not be written: {exc}"
    t = _UNITS.get(rec["unit_key"])
    try:
        if t is not None and target_done(t):
            sr.release_tpfs(rec["target_key"], int(rec["tic_id"]))
    except Exception as exc:  # noqa: BLE001 - stops the run
        return f"{rec['target_key']}'s pixel files were not released: {exc}"
    return None


def fingerprints() -> dict[str, str]:
    files = {
        "prototype_run": Path(__file__),
        "prototype_report": REPORT_SCRIPT,
        "prototype_set": SET_FILE,
        "plan": PLAN,
        "seeded_run": V057 / "seeded_run.py",
        "stability_report": V058 / "stability_report.py",
        "v058_records": v058.BUNDLE,
        **{f"test_plan_{p}": v for p, v in sr.PLANS.items()},
        **{f"draw_{p}": v for p, v in sr.DRAWS.items()},
        **{f"bundle_{p}": v for p, v in sr.BUNDLES.items()},
    }
    return {k: hashlib.sha256(v.read_bytes()).hexdigest() for k, v in files.items()}


def check_pinned(ledger: dict) -> None:
    """The run's fingerprints are pinned by its first batch; a resume or a bundle with other
    files is refused (Codex's round 1, item 5)."""
    pinned = ledger.get("pinned_fingerprints")
    if pinned is not None and pinned != fingerprints():
        changed = sorted(k for k, v in fingerprints().items() if pinned.get(k) != v)
        raise SystemExit(f"refused: the files changed since the run was pinned: {changed}")


class OsLock:
    """An exclusive lock held by the operating system on an open file (released when the
    process ends)."""

    def __enter__(self):
        import msvcrt

        path = WORK / "run" / "run.lock"
        path.parent.mkdir(parents=True, exist_ok=True)
        self._fh = open(path, "a+b")  # noqa: SIM115 - held for the whole run
        try:
            self._fh.seek(0)
            msvcrt.locking(self._fh.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError as exc:
            self._fh.close()
            raise SystemExit("refused: the run lock is held by another process") from exc
        return self

    def __exit__(self, *exc):
        import msvcrt

        self._fh.seek(0)
        msvcrt.locking(self._fh.fileno(), msvcrt.LK_UNLCK, 1)
        self._fh.close()


def point_runner() -> None:
    """Point the imported v0.5.7 runner's paths, caps and helpers to v0.5.9 (this process). Its
    batch loop is not used: ``run_batch`` below replaces it."""
    sr.WORK = WORK
    sr.DATA = DATA
    sr.LIGHTKURVE = LIGHTKURVE
    sr.RECORDS = RECORDS
    sr.TPF_LOGS = WORK / "run/tpf-deletions"
    sr.LC_LOG = WORK / "run/lc-deletions.json"
    sr.MARKER = WORK / "run/in-flight.json"
    sr.LEDGER = LEDGER
    sr.CAP_CPU_HOURS = CAP_CPU_HOURS
    sr.CAP_DISK_BYTES = CAP_DISK_BYTES
    sr.DEADLINE = DEADLINE
    sr.disk_bytes = disk_bytes
    sr.fingerprints = fingerprints
    sr._write_json = write_json
    sr.RunLock = OsLock


class Monitor(threading.Thread):
    """The batch's monitor and the only writer of the in-flight marker (a write lock serializes
    the thread's heartbeat and the controller's updates). Every 2 s it samples the disk and the
    live CPU charge (the CPU charged before the batch, the batch's live worker CPU and the
    controller's); at the CPU cap (less a margin) or over the disk cap it sets the halt event,
    which stops every running unit with its record."""

    def __init__(self, halt, charged_before: float, parent_start: float) -> None:
        super().__init__(daemon=True)
        self.halt, self.charged_before, self.parent_start = halt, charged_before, parent_start
        self.lock, self.write_lock = threading.Lock(), threading.Lock()
        self.flight: dict[str, float] = {}
        self.allowances: dict[str, float] = {}
        self.pool = None
        self.peak, self.samples = disk_bytes(), 1
        self.live_hours = charged_before
        self.halt_reason: str | None = None
        self._stop_event = threading.Event()
        self.beat()

    def worker_cpu(self) -> float:
        total = 0.0
        for p in list(getattr(self.pool, "_processes", {}).values()):
            total += sr.process_cpu_seconds(p.pid) or 0.0
        return total

    def beat(self) -> None:
        with self.write_lock:
            with self.lock:
                flight, allow = dict(self.flight), dict(self.allowances)
            sr.MARKER.parent.mkdir(parents=True, exist_ok=True)
            write_json(sr.MARKER, {"heartbeat": time.time(), "interval_seconds": SAMPLE_SECONDS,
                                   "in_flight": flight, "allowances": allow})  # fmt: skip

    def sample(self) -> None:
        self.peak = max(self.peak, disk_bytes())
        self.samples += 1
        parent = (time.process_time() - self.parent_start) / 3600.0
        self.live_hours = self.charged_before + self.worker_cpu() / 3600.0 + parent
        if self.halt_reason is None:
            if self.live_hours >= CAP_CPU_HOURS - CPU_HALT_MARGIN_HOURS:
                self.halt_reason = f"the CPU cap: {self.live_hours:.3f} CPU-h charged live"
            elif self.peak > CAP_DISK_BYTES:
                self.halt_reason = f"the disk cap: a sample of {self.peak / 1e9:.2f} GB"
            if self.halt_reason is not None:
                self.halt.set()

    def run(self) -> None:
        while not self._stop_event.wait(SAMPLE_SECONDS):
            self.sample()
            self.beat()

    def stop(self) -> None:
        self._stop_event.set()
        self.join()
        self.peak = max(self.peak, disk_bytes())
        with self.write_lock:
            if sr.MARKER.exists():
                sr.MARKER.unlink()


def pick(todo: list[dict], in_flight: dict, elapsed: float, monitor: Monitor) -> int | None | str:
    """Admission: the deadline, the batch time, the disk, the CPU and the downloads. The caps are
    also enforced while units run: the CPU and the disk by the monitor's halt, the downloads by
    each fetch unit's metered allowance."""
    if dt.datetime.now() > DEADLINE:
        return f"the phase's deadline ({DEADLINE.isoformat()} local) has passed"
    if monitor.halt_reason is not None:
        return monitor.halt_reason
    measured = disk_bytes()
    held = sum(_UNITS[v["key"]]["allowance_bytes"] for v in in_flight.values())
    cpu = monitor.live_hours + sum(v["cpu"] for v in in_flight.values())
    dl = downloaded_so_far() + held
    for i, u in enumerate(todo):
        if elapsed + est_wall(u) > BATCH_SECONDS:
            continue
        if measured + held + u["allowance_bytes"] > ADMIT_DISK_BYTES:
            continue
        if cpu + est_cpu_hours(u) > CAP_CPU_HOURS - CPU_HALT_MARGIN_HOURS:
            continue
        if dl + u["allowance_bytes"] > ADMIT_DOWNLOAD_BYTES:
            continue
        return i
    if not in_flight and elapsed == 0.0:
        return (f"no remaining unit fits (disk {measured / 1e9:.2f} GB, CPU {cpu:.2f} h, "
                f"downloads {dl / 1e9:.2f} GB)")  # fmt: skip
    return None


def run_batch(selection: list[dict], label: str) -> str | None:
    """One batch, after ``seeded_run.run_batch`` with v0.5.9's changes (Codex's round 1, items 4
    and 5): a halt event enforced in the workers, one serialized marker writer, the monitor and
    the marker always stopped in ``finally``, and the workers' CPU read before they exit. Returns
    a STOP reason, or None."""
    import multiprocessing
    import queue
    from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, wait

    plans, plan_shas = sr._plans()
    RECORDS.mkdir(parents=True, exist_ok=True)
    DATA.mkdir(parents=True, exist_ok=True)
    todo = [u for u in selection if _read_record(u["key"]) is None]
    charged_before = sr._charged()
    if charged_before >= CAP_CPU_HOURS - CPU_HALT_MARGIN_HOURS:
        return f"the cap of {CAP_CPU_HOURS} CPU-h is reached"
    n, k = sr.batch_limits()
    parent_cpu = time.process_time()
    ctx = multiprocessing.get_context("spawn")
    semaphore, fetched, halt = ctx.Semaphore(k), ctx.Queue(), ctx.Event()
    monitor = Monitor(halt, charged_before, parent_cpu)
    monitor.start()
    start, stop, in_flight, recorded, failures, worker_cpu = time.time(), None, {}, 0, [], None
    try:
        with ProcessPoolExecutor(max_workers=n, mp_context=ctx, initializer=init_worker,
                                 initargs=(semaphore, fetched, halt)) as pool:  # fmt: skip
            monitor.pool = pool
            while True:
                while True:
                    try:
                        done_key = fetched.get_nowait()
                    except queue.Empty:
                        break
                    for v in in_flight.values():
                        if v["key"] == done_key:
                            v["fetching"] = False
                while todo and stop is None and len(in_flight) < n:
                    if sum(v["fetching"] for v in in_flight.values()) >= k:
                        break
                    elapsed = 0.0 if not in_flight and recorded == 0 else time.time() - start
                    i = pick(todo, in_flight, elapsed, monitor)
                    if isinstance(i, str):
                        stop = i
                        break
                    if i is None:
                        break
                    u = todo.pop(i)
                    with monitor.lock:  # journaled before the dispatch
                        monitor.flight[u["key"]] = time.time()
                        if u["allowance_bytes"]:
                            monitor.allowances[u["key"]] = u["allowance_bytes"]
                    monitor.beat()
                    fut = pool.submit(run_unit, u, plans[u["part"]], None)
                    in_flight[fut] = {"key": u["key"], "cpu": est_cpu_hours(u), "fetching": True}
                if not in_flight:
                    break
                finished, _ = wait(list(in_flight), timeout=SAMPLE_SECONDS,
                                   return_when=FIRST_COMPLETED)  # fmt: skip
                for fut in finished:
                    v = in_flight.pop(fut)
                    try:
                        rec = fut.result()
                    except BaseException as exc:  # noqa: BLE001 - a worker failure stops admission
                        failures.append(f"{v['key']}: {type(exc).__name__}: {exc}")
                        stop = stop or f"a worker failed on {v['key']}"
                        continue
                    problem = finish(rec)
                    with monitor.lock:
                        monitor.flight.pop(v["key"], None)
                        monitor.allowances.pop(v["key"], None)
                    if problem:
                        failures.append(problem)
                        stop = stop or problem
                        continue
                    recorded += 1
                    print(rec["unit_key"], rec["status"], rec.get("outcome"),
                          round(rec["cpu_seconds"]), f"live {monitor.live_hours:.2f} CPU-h",
                          f"peak {monitor.peak / 1e9:.2f} GB", flush=True)  # fmt: skip
                if monitor.halt_reason is not None and stop is None:
                    stop = monitor.halt_reason
            worker_cpu = monitor.worker_cpu()  # the workers are still alive here
    finally:
        monitor.stop()
    if monitor.halt_reason is not None and stop is None:
        stop = monitor.halt_reason
    spent, nbytes, done = sr._spent()
    ledger = sr._ledger()
    ledger.setdefault("pinned_fingerprints", fingerprints())
    ledger["caps"] = {
        "cpu_hours": CAP_CPU_HOURS,
        "download_bytes": CAP_DOWNLOAD_BYTES,
        "disk_bytes": CAP_DISK_BYTES,
        "deadline_local": DEADLINE.isoformat(),
    }
    ledger["batches"].append({
        "label": label,
        "started_utc": sr.utc(start),
        "ended_utc": sr.utc(),
        "wall_seconds": round(time.time() - start, 1),
        "workers": n,
        "simultaneous_downloads": k,
        "test_plan_sha256": plan_shas,
        "fingerprints": fingerprints(),
        "recorded_in_batch": recorded,
        "records": done,
        "cpu_hours_spent_records": round(spent, 4),
        "worker_process_cpu_hours": None if worker_cpu is None else round(worker_cpu / 3600, 4),
        "parent_cpu_hours": round((time.process_time() - parent_cpu) / 3600.0, 6),
        "downloaded_bytes_charged": downloaded_so_far(),
        "disk_peak_bytes": monitor.peak,
        "disk_samples": monitor.samples,
        "halt_reason": monitor.halt_reason,
        "failures": failures,
        "stop": stop,
    })  # fmt: skip
    ledger["disk_peak_bytes"] = max(ledger.get("disk_peak_bytes", 0), monitor.peak)
    sr._save_ledger(ledger)
    ledger["batches"][-1]["cpu_hours_charged"] = round(sr._charged(), 4)
    sr._save_ledger(ledger)
    return stop


def charge_interruptions() -> None:
    """Before any redispatch: an unclean end is charged as ``seeded_run`` does (each unrecorded
    in-flight unit's wall time up to the last heartbeat), and each unrecorded in-flight fetch
    unit's whole byte allowance is charged to the download cap."""
    if not sr.MARKER.exists():
        return
    m = json.loads(sr.MARKER.read_text("utf-8"))
    lost = {k: b for k, b in (m.get("allowances") or {}).items()
            if not (RECORDS / f"{k}.json").exists()}  # fmt: skip
    charged = sr.charge_interruption()  # reads and removes the marker
    ledger = sr._ledger()
    if lost:
        ledger.setdefault("download_interruptions", []).append(
            {
                "detected_utc": sr.utc(),
                "units": sorted(lost),
                "bytes": int(sum(lost.values())),
                "rule": "the whole allowance of each fetch unit in flight without a record",
            }
        )
        sr._save_ledger(ledger)
    print("interruption charged:", json.dumps(charged), "download bytes:", sum(lost.values()),
          flush=True)  # fmt: skip


def sweep(all_targets: list[dict]) -> list[str]:
    """Release the pixel files of every TOI whose last required unit is recorded (a restart)."""
    done = []
    for t in all_targets:
        log = sr.TPF_LOGS / f"{t['key']}.json"
        if log.exists() and json.loads(log.read_text("utf-8")).get("status") == "deleted":
            continue
        if target_done(t):
            sr.release_tpfs(t["key"], int(t["tic_id"]))
            done.append(t["key"])
    return done


def run() -> None:
    all_targets = targets()
    if len(all_targets) != len(set_keys()):
        raise SystemExit("the set and the draws disagree")
    with OsLock():
        ledger = sr._ledger()
        if ledger.get("state") in ("complete", "abandoned"):
            raise SystemExit(f"refused: the run is {ledger.get('state')}")
        check_pinned(ledger)
        charge_interruptions()
        sweep(all_targets)
        while True:
            todo = ready_units(all_targets)
            if not todo:
                break
            stop = run_batch(todo, "prototype")
            if stop:
                sr._terminal("stopped", stop)
                print("STOP:", stop, flush=True)
                raise SystemExit(2)
        sweep(all_targets)
        sr._terminal("complete", "every required unit of the set is recorded")
        print("all units recorded", json.dumps(sr._totals()), flush=True)


# --- the bundle: 48 records (24 TOIs x 2 modes) ---------------------------------------------


def mode_record(t: dict, mode: str) -> dict:
    """One TOI in one mode, from its unit records only: the base and consensus outputs, the fit
    identity, the first disagreeing probe and the measured costs. A row whose units are not all
    recorded says so (``status: NO RECORD`` or ``required_missing``)."""
    f = _read_record(unit_key(t["key"], "fetch"))
    b = _read_record(unit_key(t["key"], "base", mode))
    probes = {n: _read_record(unit_key(t["key"], "probe", mode, n)) for n, _, _ in PROBES}
    cons = consensus(b, probes)
    missing = [k for k in required_units(t)
               if k.split(".")[1] in ("fetch", mode) and _read_record(k) is None]  # fmt: skip
    reason = None
    if f is None or (f.get("status") == "OK" and b is None):
        status = "NO RECORD"
    elif f.get("status") != "OK":
        status, reason = f"NOT_RUN (fetch {f.get('status')})", f.get("reason")
    else:
        status, reason = b.get("status"), b.get("reason") or b.get("outcome_reason")
    fit = (b or {}).get("fit") or {}
    return {
        "target_key": t["key"],
        "toi": t["toi"],
        "group": t["group"],
        "entry_mode": mode,
        "phase": "v0.5.9",
        "mode": "exploratory",
        "limits_label": LABEL,
        "method_status": "not_validated",
        "started_utc": (b or f or {}).get("started_utc"),
        "status": status,
        "reason": reason,
        "required_missing": missing,
        "coverage_state": (b or {}).get("coverage_state", "unavailable"),
        "provenance": (f or {}).get("provenance") or {"overall": "unknown",
                                                      "reason": "no fetch record"},  # fmt: skip
        "inputs_sha256": {x["name"]: x["sha256"] for x in (f or {}).get("inputs", [])},
        "manifest_sha256": ((f or {}).get("manifest") or {}).get("sha256"),
        "base": None if b is None else {
            "outcome": b.get("outcome"),
            "outcome_reason": b.get("outcome_reason"),
            "reason": b.get("reason"),
            "tests": b.get("tests"),
            "candidate": b.get("candidate"),
            "numerical_failures_guarded": b.get("numerical_failures_guarded"),
        },
        "fit": {"resolved": fit.get("resolved"), "final": fit.get("final"),
                "unresolved_reason": fit.get("unresolved_reason"),
                "detail": {k: v for k, v in fit.items()
                           if k not in ("resolved", "final", "unresolved_reason")}},
        "identity": (b or {}).get("identity"),
        "probes": {n: None if p is None else {
            "status": p.get("status"), "outcome": p.get("outcome"),
            "reason": p.get("reason") or p.get("outcome_reason"),
            "spec": p.get("probe_spec"), "candidate": p.get("candidate"),
            "tests_differing_from_base": p.get("tests_differing_from_base"),
            "cpu_seconds": p.get("cpu_seconds"),
            "evaluation_cpu_seconds": p.get("evaluation_cpu_seconds"),
            "numerical_failures_guarded": p.get("numerical_failures_guarded"),
        } for n, p in probes.items()},
        "consensus": cons,
        "cost": {
            "fetch_cpu_seconds": (f or {}).get("cpu_seconds"),
            "download_bytes_of_the_toi": (f or {}).get("downloaded_bytes"),
            "metered_download_bytes_of_the_toi": (f or {}).get("metered_download_bytes"),
            "bytes_of_the_toi": (f or {}).get("bytes"),
            "base_cpu_seconds": (b or {}).get("cpu_seconds"),
            "fit_cpu_seconds": (b or {}).get("fit_cpu_seconds"),
            "base_evaluation_cpu_seconds": (b or {}).get("evaluation_cpu_seconds"),
            "probe_cpu_seconds": {n: (p or {}).get("cpu_seconds") for n, p in probes.items()},
            "probe_evaluation_cpu_seconds": {n: (p or {}).get("evaluation_cpu_seconds")
                                             for n, p in probes.items()},
        },
    }  # fmt: skip


UNITS_BUNDLE = HERE / "prototype-units.json"
ARCHIVE_STAGE = WORK / "run/units.json"


def bundle() -> None:
    """The 48 mode records (with every unit file's SHA-256 and the run's terminal state) to
    ``prototype-records.json``; the unit records themselves to ``prototype-units.json`` if it
    stays within 5 MB, otherwise staged in ``.cache/v059/run/units.json`` for the Drive archive
    (``verify-archive`` checks the copy against its SHA-256 before anything local is retired)."""
    ledger = sr._ledger()
    check_pinned(ledger)
    all_targets = targets()
    units = sorted(RECORDS.glob("*.json"))
    unit_doc = {
        "schema": "refute-v059-prototype-units-1",
        "mode": "exploratory",
        "limits_label": LABEL,
        "units": [{"file": p.name, "sha256": sr.sha256(p.read_bytes()),
                   "content": json.loads(p.read_text("utf-8"))} for p in units],
        "tpf_deletions": [{"file": p.name, "sha256": sr.sha256(p.read_bytes()),
                           "content": json.loads(p.read_text("utf-8"))}
                          for p in sorted(sr.TPF_LOGS.glob("*.json"))],
    }  # fmt: skip
    text = json.dumps(unit_doc, indent=1, default=sr._plain) + "\n"
    target = UNITS_BUNDLE if len(text.encode()) <= MAX_GIT_BYTES else ARCHIVE_STAGE
    target.write_text(text, "utf-8", newline="\n")
    doc = {
        "schema": "refute-v059-prototype-records-1",
        "mode": "exploratory",
        "limits_label": LABEL,
        "method_status": "not_validated",
        "written_utc": sr.utc(),
        "fingerprints": fingerprints(),
        "run_state": ledger.get("state"),
        "run_state_reason": ledger.get("state_reason"),
        "units_file": {"path": target.relative_to(ROOT).as_posix(),
                       "sha256": sr.sha256(text.encode()), "bytes": len(text.encode())},
        "unit_files_sha256": {u["file"]: u["sha256"] for u in unit_doc["units"]},
        "records": [mode_record(t, m) for t in all_targets for m in MODES],
    }  # fmt: skip
    BUNDLE.write_text(json.dumps(doc, indent=1, default=sr._plain) + "\n", "utf-8", newline="\n")
    print(len(doc["records"]), "mode records;", len(unit_doc["units"]), "unit records in",
          target.relative_to(ROOT).as_posix(), "; run state", ledger.get("state"))  # fmt: skip


def verify_archive(copy: str) -> None:
    """The Drive copy of the staged unit records against the bundle's SHA-256, with a manifest of
    source and destination; nothing is deleted here."""
    doc = json.loads(BUNDLE.read_text("utf-8"))
    want = doc["units_file"]["sha256"]
    src = ROOT / doc["units_file"]["path"]
    got_src = sr.sha256_path(src) if src.exists() else None
    got = sr.sha256_path(Path(copy))
    manifest = {"utc": sr.utc(), "source": doc["units_file"]["path"], "source_sha256": got_src,
                "expected_sha256": want, "copy_sha256": got,
                "match": got == want and got_src == want}  # fmt: skip
    write_json(WORK / "run/archive-manifest.json", manifest)
    print(json.dumps(manifest))
    if not manifest["match"]:
        raise SystemExit("the archive copy does not match")


def abandon(reason: str) -> None:
    """The maintainer's explicit, irreversible end of a stopped run: ``run`` refuses to resume it,
    and only then may ``clean`` delete inputs that pending units would need."""
    ledger = sr._ledger()
    if ledger.get("state") != "stopped":
        raise SystemExit(f"refused: only a stopped run can be abandoned ({ledger.get('state')!r})")
    sr._terminal("abandoned", reason)


def clean() -> None:
    """The light curves at the end, only for a run that is complete or explicitly abandoned, with
    no unit in flight: every pixel file released (manifest first), then each light curve by
    literal path and SHA-256, inside ``.cache/v059`` only."""
    ledger = sr._ledger()
    if ledger.get("state") not in ("complete", "abandoned"):
        raise SystemExit(f"refused: the run is {ledger.get('state')!r}, not complete or abandoned")
    if sr.MARKER.exists():
        raise SystemExit("refused: a unit is still marked in flight")
    entries, freed = [], 0
    for t in targets():
        f = _read_record(unit_key(t["key"], "fetch"))
        if f is None:
            continue
        log = sr.TPF_LOGS / f"{t['key']}.json"
        if not log.exists() or json.loads(log.read_text("utf-8")).get("status") != "deleted":
            sr.release_tpfs(t["key"], int(t["tic_id"]))
        for e in f.get("light_curve_manifest", []):
            path = DATA / e["path"]
            if not path.exists():
                entries.append({"path": e["path"], "status": "absent"})
                continue
            freed += sr.delete_literal(path, int(t["tic_id"]), e["sha256"], "_lc.fits")
            entries.append({"path": e["path"], "sha256": e["sha256"], "status": "deleted"})
    write_json(sr.LC_LOG, {"utc": sr.utc(), "bytes_deleted": freed, "files": entries})
    print(f"light curves deleted: {sum(e['status'] == 'deleted' for e in entries)} files, "
          f"{freed} bytes")  # fmt: skip


USAGE = "usage: prototype_run.py draw|run|bundle|clean|abandon <reason>|verify-archive <copy>"


def main(argv: list[str]) -> None:
    step = argv[0] if argv else ""
    if step == "draw":
        if SET_FILE.exists():
            raise SystemExit(f"{SET_FILE.name} exists; it is written once")
        doc = build_set()
        SET_FILE.write_text(json.dumps(doc, indent=1) + "\n", "utf-8", newline="\n")
        print({g: len(doc[g]) for g in ("changes", "reverse", "numeric_errors")},
              {c: v for c, v in doc["controls"].items()})  # fmt: skip
        return
    point_runner()
    no_link_roots()
    sr.isolate_caches()  # every cache inside .cache/v059 (sr.WORK is pointed there)
    if step == "run":
        run()
    elif step in ("bundle", "clean", "abandon", "verify-archive"):
        with OsLock():
            if step == "bundle":
                bundle()
            elif step == "clean":
                clean()
            elif step == "abandon" and len(argv) > 1:
                abandon(" ".join(argv[1:]))
            elif step == "verify-archive" and len(argv) == 2:
                verify_archive(argv[1])
            else:
                raise SystemExit(USAGE)
    else:
        raise SystemExit(USAGE)


if __name__ == "__main__":
    main(sys.argv[1:])
