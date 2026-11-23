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
# the statuses of a unit ended by a resource stop, never a scientific outcome
OPERATIONAL = ("STOPPED_AT_CAP", "CPU_ALLOWANCE", "DOWNLOAD_ALLOWANCE", "WORKER_LOST")

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
    - a decided base with a probe not recorded, or ended by a resource stop (``OPERATIONAL``),
      has no consensus (``status: INCOMPLETE``, kept apart from a recorded disagreement);
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
    stopped = [n for n, _, _ in PROBES if probes[n].get("status") in OPERATIONAL]
    if stopped:  # a resource stop is not a scientific disagreement (Codex's round 2, item 4)
        return {"outcome": None, "status": "INCOMPLETE", "first_disagreeing": None,
                "reason": f"probes ended by a resource stop: {', '.join(stopped)}"}  # fmt: skip
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
    """Finite, symmetric (to ``SYMMETRY_RTOL`` of the matrix's own largest entry, checked before
    Cholesky) and positive definite (Cholesky)."""
    m = np.asarray(matrix, dtype=float)
    if not np.all(np.isfinite(m)):
        raise NumericFailureError(f"{what} is not finite")
    scale = float(np.max(np.abs(m))) if m.size else 0.0
    if scale == 0.0 or np.max(np.abs(m - m.T)) > SYMMETRY_RTOL * scale:
        raise NumericFailureError(f"{what} is not symmetric (or is zero)")
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
            cached = {p.resolve(): p.stat().st_size for p in Path(download_dir).rglob(row_name)}
            path = Path(plain_dl(product, row_name, download_dir, **kwargs))
            size = path.stat().st_size
            if cached.get(path.resolve()) == size:
                meter["cache_hits"] = meter.get("cache_hits", 0) + 1  # no transfer: not counted
                return path
            meter["completed_bytes"] += size
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
    """The same input bytes for every unit: each FITS file's SHA-256 is checked against the fetch
    unit's record, and the adapter's manifest (the star and neighbor data the tests read) is
    parsed from the exact bytes whose SHA-256 was checked, with the adapter's own checks, then
    read by the adapter's ``load_from_manifest``. Returns (data, plan) or None (the record says
    why)."""
    from refute.packs.tess import adapter
    from refute.packs.tess.discover.measure import stage_plan
    from refute.packs.tess.params import TessTestPlan

    fetched = _read_record(unit_key(unit["target_key"], "fetch"))
    if fetched is None or fetched.get("status") != "OK":
        rec.update({"status": "NOT_RUN", "reason": "the fetch unit is not OK"})
        return None
    changed = [f["name"] for f in fetched["inputs"]
               if w.sha256_path(DATA / f["path"]) != f["sha256"]]  # fmt: skip
    raw = (DATA / fetched["manifest"]["path"]).read_bytes()
    if hashlib.sha256(raw).hexdigest() != fetched["manifest"]["sha256"]:
        changed.append("manifest")
    rec["inputs_checked"] = len(fetched["inputs"]) + 1  # the FITS files and the manifest
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
    tic = int(unit["tic_id"])
    manifest = json.loads(raw.decode("utf-8"))
    if (
        manifest.get("schema") not in adapter.SUPPORTED_SCHEMAS
        or manifest.get("tic_id") != tic
        or manifest.get("target_key") != f"TIC-{tic}"
    ):
        rec.update({"status": "INPUTS_CHANGED", "reason": "the manifest is not this TOI's"})
        return None
    max_sector, read_pixels = adapter._limits(plan)
    data = adapter.load_from_manifest(manifest, DATA, plan.data, None, max_sector, read_pixels)
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


def run_unit(unit: dict, test_plan: dict, _hist: dict | None = None) -> dict:
    """One work unit, in its own worker process. Any failure is recorded, never hidden."""
    w = _point_worker()
    started, wall = time.process_time(), time.time()
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
        if unit["kind"] == "selftest":  # the supervisor's offline tests only
            end = time.process_time() + float(unit.get("spin_seconds", 0.0))
            while time.process_time() < end:
                pass
            rec.update({"status": "OK", "outcome": "INCONCLUSIVE", "outcome_reason": "selftest"})
        else:
            handler = {"fetch": _fetch, "base": _base, "probe": _probe}[unit["kind"]]
            handler(unit, test_plan, rec, w)
    except Exception as exc:  # noqa: BLE001 - recorded, never hidden
        rec.update({"status": "ERROR", "reason": f"{type(exc).__name__}: {exc}",
                    "trace": traceback.format_exc()[-1500:]})  # fmt: skip
    finally:
        rec["cpu_seconds"] = time.process_time() - started
        rec["wall_seconds"] = time.time() - wall
        rec["ended_utc"] = sr.utc()
    return rec


def _self_limit(cpu_allowance: float) -> None:
    """In a worker: a thread that ends the process (``os._exit``) once its own CPU passes the
    unit's allowance, so even a worker whose controller died cannot spend more."""

    def watch() -> None:
        while True:
            time.sleep(1.0)
            if time.process_time() > cpu_allowance:
                os._exit(86)

    threading.Thread(target=watch, daemon=True).start()


def child_main(unit: dict, test_plan: dict, result_path: str) -> None:
    """A worker process: run one unit and write its record to ``result_path`` (atomic, read
    back). The controller turns that file into the unit's record."""
    _self_limit(unit["cpu_allowance_seconds"])
    rec = run_unit(unit, test_plan)
    write_json(Path(result_path), rec)


# --- the controller ----------------------------------------------------------------------------

_UNITS: dict[str, dict] = {}
SAMPLE_SECONDS = 1.0
CPU_HALT_MARGIN_HOURS = 0.02  # the supervisor stops every worker this far below the CPU cap
CPU_ALLOWANCE_FACTOR, MIN_CPU_ALLOWANCE = 4.0, 600.0  # per unit, enforced by both sides
ATTEMPTS = WORK / "run/attempts"
RESULTS = WORK / "run/results"
CHILD_ENV = {
    "OMP_NUM_THREADS": "1",
    "OPENBLAS_NUM_THREADS": "1",
    "MKL_NUM_THREADS": "1",
    "NUMEXPR_NUM_THREADS": "1",
}  # one thread per worker: its CPU is bounded by its wall
ARCHIVE_ROOT = Path("K:/Meu Drive/Pessoal/Projetos/refute")


def cache_roots() -> list[Path]:
    return [LIGHTKURVE, RECORDS, ATTEMPTS, RESULTS, WORK / "run/tpf-deletions",
            *(WORK / rel for rel in sr.ENV_DIRS.values())]  # fmt: skip


def no_link_roots() -> None:
    """Refuse a run whose cache roots are links or junctions (Codex's rounds 1 and 2, item 6):
    every existing component from ``.cache`` down to every configured root, checked before any
    directory is created and before every download."""
    cache = ROOT / ".cache"
    for leaf in cache_roots():
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
    """A fetch unit's byte allowance: 1.25 times the TOI's v0.5.8 bytes, at least 0.3 GB. Other
    units download nothing."""
    if u["kind"] != "fetch":
        return 0.0
    return max(MIN_DOWNLOAD_RESERVE, DOWNLOAD_RESERVE_FACTOR * (u.get("v058_bytes") or 0))


def est_cpu_hours(u: dict) -> float:
    if u["kind"] == "selftest":
        return float(u.get("spin_seconds", 0.0)) / 3600.0
    base = max(60.0, u.get("v058_cpu") or 0.0, 15.0 * len(u.get("sectors") or []))
    return CPU_FACTORS[u["kind"]] * base / 3600.0


def cpu_allowance(u: dict) -> float:
    """A unit's CPU allowance (seconds): enforced by the supervisor and by the worker itself."""
    if u["kind"] == "selftest":
        return float(u.get("cpu_allowance_seconds", 60.0))
    return max(MIN_CPU_ALLOWANCE, CPU_ALLOWANCE_FACTOR * est_cpu_hours(u) * 3600.0)


def est_wall(u: dict) -> float:
    if u["kind"] == "fetch":
        return min(MAX_UNIT_WALL, 1.5 * (u.get("v058_fetch_wall") or 120.0) + 60.0)
    return min(MAX_UNIT_WALL, 3.0 * est_cpu_hours(u) * 3600.0 + 30.0)


def _unit(t: dict, kind: str, mode: str | None = None, probe: str | None = None) -> dict:
    key = unit_key(t["key"], kind, mode, probe)
    u = {**t, "target_key": t["key"], "key": key, "kind": kind, "mode": mode, "probe": probe}
    u["allowance_bytes"] = download_reserve(u)
    u["cpu_allowance_seconds"] = cpu_allowance(u)
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


def disk_bytes(root: Path | None = None) -> int:
    """The disk under ``.cache/v059`` by default."""
    return _ORIGINAL_DISK_BYTES(WORK if root is None else root)


def write_json(path: Path, obj: dict) -> str:
    """Atomic write with a temporary name unique to the process and the thread, read back. A
    replace refused by Windows (v0.5.8's heartbeat departure) is tried again up to 5 times,
    0.2 s apart."""
    text = json.dumps(obj, indent=1, default=sr._plain)
    path.parent.mkdir(parents=True, exist_ok=True)
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


# --- the attempt journal: one durable file per dispatch ---------------------------------------


def attempts() -> list[dict]:
    return [json.loads(p.read_text("utf-8")) for p in sorted(ATTEMPTS.glob("*.json"))]


def charged() -> dict:
    """The one charge used for admission, supervision and settlement: per attempt, its settled
    charge (or, while it runs, its last measured CPU and bytes); plus the controller's CPU of every
    batch. Downloads: per fetch attempt, its charged bytes."""
    cpu, nbytes = 0.0, 0
    for a in attempts():
        cpu += float(a.get("cpu_seconds_charged") or 0.0)
        nbytes += int(a.get("bytes_charged") or 0)
    ledger = sr._ledger()
    controller = sum(float(b.get("controller_cpu_hours") or 0.0) for b in ledger.get("batches", []))
    return {"cpu_hours": cpu / 3600.0 + controller, "download_bytes": nbytes}


def _creation_time(pid: int) -> int | None:
    import ctypes

    h = sr._handle(pid)
    if not h:
        return None
    try:
        t = [ctypes.c_ulonglong() for _ in range(4)]
        if not ctypes.windll.kernel32.GetProcessTimes(h, *(ctypes.byref(x) for x in t)):
            return None
        return int(t[0].value)
    finally:
        ctypes.windll.kernel32.CloseHandle(h)


def same_process_alive(pid: int, created: int | None) -> bool:
    """The process this run started is still alive: its PID is alive with the same creation time
    (a reused PID is another process)."""
    return created is not None and sr.process_alive(pid) and _creation_time(pid) == created


def observe_download(baseline: dict, current: dict, max_seen: dict) -> int:
    """Bytes transferred by a fetch unit, from snapshots of the TOI's files ({path: size}): every
    file absent from the baseline counts at the largest size seen, even if it later vanished (a
    discarded partial file); a file already in the baseline (a cache hit) does not count."""
    for path, size in current.items():
        if path not in baseline:
            max_seen[path] = max(size, max_seen.get(path, 0))
    return sum(max_seen.values())


def _tic_snapshot(tic: int) -> dict:
    out = {}
    if LIGHTKURVE.exists():
        for p in LIGHTKURVE.rglob(f"*{int(tic):016d}*"):
            try:
                if p.is_file():
                    out[str(p)] = p.stat().st_size
            except FileNotFoundError:
                continue
    return out


def settle(a: dict, rec: dict | None, status: str | None = None, reason: str | None = None) -> str:
    """Make one attempt durable: the unit's record first (the worker's, or one the supervisor
    writes for a stopped or lost worker), then its charge in the journal. Returns the record's
    status. Charges: the larger of the worker's own CPU and the supervisor's last reading plus one
    sample; for a fetch, the largest of the observed, the metered and the manifest's new bytes."""
    if rec is None:
        rec = {"unit_key": a["key"], "target_key": a["target_key"], "tic_id": a["tic_id"],
               "toi": a.get("toi"), "kind": a["kind"], "entry_mode": a.get("mode"),
               "probe": a.get("probe"), "phase": "v0.5.9", "mode": "exploratory",
               "limits_label": LABEL, "method_status": "not_validated",
               "started_utc": a["started_utc"], "coverage_state": "unavailable",
               "status": status or "WORKER_LOST", "reason": reason or "no result from the worker",
               "cpu_seconds": a.get("cpu_seconds_seen", 0.0) + SAMPLE_SECONDS,
               "ended_utc": sr.utc()}  # fmt: skip
    rec["attempt_id"] = a["attempt_id"]
    cpu = max(float(rec.get("cpu_seconds") or 0.0),
              float(a.get("cpu_seconds_seen") or 0.0) + SAMPLE_SECONDS)  # fmt: skip
    nbytes = 0
    if a["kind"] == "fetch":
        nbytes = max(int(a.get("bytes_seen") or 0), int(rec.get("metered_download_bytes") or 0),
                     int(rec.get("downloaded_bytes") or 0))  # fmt: skip
        rec["bytes_charged"] = nbytes
    write_json(RECORDS / f"{a['key']}.json", rec)
    a.update({"state": "settled", "settled_utc": sr.utc(), "record_status": rec.get("status"),
              "cpu_seconds_charged": cpu, "bytes_charged": nbytes})  # fmt: skip
    write_json(ATTEMPTS / f"{a['attempt_id']}.json", a)
    return str(rec.get("status"))


def recover() -> list[str]:
    """Before any dispatch (idempotent): every attempt not settled is settled now. A worker still
    alive refuses the run (the maintainer decides). A worker's result file, if any, becomes its
    record; otherwise the attempt is charged its whole CPU and byte allowances and its unit stays
    unrecorded, so it is dispatched again within the same approved run."""
    notes = []
    for a in attempts():
        if a.get("state") == "settled":
            continue
        if same_process_alive(int(a["pid"]), a.get("created")):
            raise SystemExit(f"refused: a worker of an earlier batch is alive (PID {a['pid']}, "
                             f"{a['key']}); the maintainer decides")  # fmt: skip
        result = RESULTS / f"{a['attempt_id']}.json"
        recorded = _read_record(a["key"])
        if recorded is not None and recorded.get("attempt_id") == a["attempt_id"]:
            a.update({"state": "settled", "settled_utc": sr.utc(), "recovered": True,
                      "cpu_seconds_charged": max(float(recorded.get("cpu_seconds") or 0.0),
                                                 float(a.get("cpu_seconds_seen") or 0.0)),
                      "bytes_charged": int(recorded.get("bytes_charged") or 0)})  # fmt: skip
            write_json(ATTEMPTS / f"{a['attempt_id']}.json", a)
        elif result.exists():
            settle(a, json.loads(result.read_text("utf-8")))
        else:
            a.update({"state": "settled", "settled_utc": sr.utc(), "recovered": True,
                      "record_status": None,
                      "cpu_seconds_charged": float(a["cpu_allowance_seconds"]),
                      "bytes_charged": int(a.get("allowance_bytes") or 0),
                      "rule": "no result: charged its whole CPU and byte allowances; the unit "
                              "stays unrecorded and runs again in this approved run"})  # fmt: skip
            write_json(ATTEMPTS / f"{a['attempt_id']}.json", a)
        notes.append(a["key"])
    return notes


def finish_target(rec: dict) -> None:
    """When a TOI's last required unit is recorded, release its pixel files (manifest first, then
    each file by literal path and SHA-256)."""
    t = _UNITS.get(rec["unit_key"])
    if t is not None and t["kind"] != "selftest" and target_done(t):
        sr.release_tpfs(rec["target_key"], int(rec["tic_id"]))


# --- the supervisor ---------------------------------------------------------------------------


def fingerprints() -> dict[str, str]:
    """The run's code, protocol and environment: the scripts, the set, the plan, the imported
    v0.5.7 and v0.5.8 files, the test plans, the draws, the bundles, every file under ``src/``,
    ``pyproject.toml`` and ``uv.lock``."""
    files = {
        "prototype_run": Path(__file__),
        "prototype_report": REPORT_SCRIPT,
        "prototype_set": SET_FILE,
        "plan": PLAN,
        "seeded_run": V057 / "seeded_run.py",
        "stability_report": V058 / "stability_report.py",
        "v058_records": v058.BUNDLE,
        "pyproject": ROOT / "pyproject.toml",
        "uv_lock": ROOT / "uv.lock",
        **{f"test_plan_{p}": v for p, v in sr.PLANS.items()},
        **{f"draw_{p}": v for p, v in sr.DRAWS.items()},
        **{f"bundle_{p}": v for p, v in sr.BUNDLES.items()},
    }
    out = {k: hashlib.sha256(v.read_bytes()).hexdigest() for k, v in files.items()}
    src = hashlib.sha256()
    for p in sorted((ROOT / "src").rglob("*.py")):
        src.update(p.relative_to(ROOT).as_posix().encode() + b"\0" + p.read_bytes() + b"\0")
    out["src_tree"] = src.hexdigest()
    return out


def check_pinned(ledger: dict) -> None:
    """The run's fingerprints are pinned before its first dispatch; a resume or a bundle with any
    of those files changed is refused (Codex's rounds 1 and 2, item 5)."""
    pinned = ledger.get("pinned_fingerprints")
    if pinned is not None and pinned != fingerprints():
        now = fingerprints()
        changed = sorted(k for k in set(now) | set(pinned) if pinned.get(k) != now.get(k))
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
    """Point the imported v0.5.7 runner's paths and caps to v0.5.9 (this process). Its batch loop
    is not used: the supervisor below replaces it."""
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
    sr._write_json = write_json


def pick(todo: list[dict], running: dict, elapsed: float, live: dict, k: int) -> int | None | str:
    """Admission: the deadline, the batch time, at most ``k`` downloads at once, the disk, the
    CPU and the downloads, each with every running unit's allowance reserved."""
    if dt.datetime.now() > DEADLINE:
        return f"the phase's deadline ({DEADLINE.isoformat()} local) has passed"
    fetching = sum(r["unit"]["kind"] == "fetch" for r in running.values())
    held_bytes = sum(r["unit"]["allowance_bytes"] for r in running.values())
    held_cpu = sum(r["unit"]["cpu_allowance_seconds"] for r in running.values()) / 3600.0
    measured = disk_bytes()
    for i, u in enumerate(todo):
        if u["kind"] == "fetch" and fetching >= k:
            continue
        if elapsed + est_wall(u) > BATCH_SECONDS:
            continue
        if measured + held_bytes + u["allowance_bytes"] > ADMIT_DISK_BYTES:
            continue
        cpu_need = live["cpu_hours"] + held_cpu + u["cpu_allowance_seconds"] / 3600.0
        if cpu_need > CAP_CPU_HOURS - CPU_HALT_MARGIN_HOURS:
            continue
        if live["download_bytes"] + held_bytes + u["allowance_bytes"] > ADMIT_DOWNLOAD_BYTES:
            continue
        return i
    if not running and elapsed == 0.0:
        return (
            f"no remaining unit fits (disk {measured / 1e9:.2f} GB, CPU "
            f"{live['cpu_hours']:.2f} h, downloads {live['download_bytes'] / 1e9:.2f} GB)"
        )
    return None


def _launch(ctx, u: dict, plan: dict) -> dict:
    attempt_id = f"{u['key']}.{time.time_ns()}"
    a = {"attempt_id": attempt_id, "key": u["key"], "target_key": u["target_key"],
         "tic_id": u["tic_id"], "toi": u.get("toi"), "kind": u["kind"], "mode": u.get("mode"),
         "probe": u.get("probe"), "state": "launching", "started_utc": sr.utc(),
         "cpu_allowance_seconds": u["cpu_allowance_seconds"],
         "allowance_bytes": u["allowance_bytes"]}  # fmt: skip
    write_json(ATTEMPTS / f"{attempt_id}.json", a)  # journaled before the process exists
    result = RESULTS / f"{attempt_id}.json"
    baseline = _tic_snapshot(int(u["tic_id"])) if u["kind"] == "fetch" else {}
    proc = ctx.Process(target=child_main, args=(u, plan, str(result)), daemon=False)
    proc.start()
    a.update({"state": "running", "pid": proc.pid, "created": _creation_time(proc.pid)})
    write_json(ATTEMPTS / f"{attempt_id}.json", a)
    return {"unit": u, "attempt": a, "proc": proc, "result": result, "baseline": baseline,
            "max_seen": {}, "started": time.time()}  # fmt: skip


def _kill(r: dict) -> None:
    """End a worker this run started, by its own process handle (never by name)."""
    if r["proc"].is_alive():
        r["proc"].terminate()
    r["proc"].join(10)


def run_batch(selection: list[dict], label: str) -> str | None:
    """One batch under a parent-owned supervisor (Codex's round 2, items 1 to 3): one process per
    unit, journaled before it starts; every second the supervisor reads each worker's CPU and each
    download's bytes on disk, the disk, and the one charge; it ends a worker that passes its CPU
    or byte allowance, and every worker at the CPU or disk cap, then writes their records and
    charges before clearing them. Any failure of the supervisor itself ends every worker, settles
    it, and stops the run. Returns a STOP reason, or None."""
    import multiprocessing

    plans, plan_shas = sr._plans()
    for d in (RECORDS, ATTEMPTS, RESULTS, DATA):
        d.mkdir(parents=True, exist_ok=True)
    todo = [u for u in selection if _read_record(u["key"]) is None]
    n, k = sr.batch_limits()
    ctx = multiprocessing.get_context("spawn")
    controller0, start = time.process_time(), time.time()
    running: dict[str, dict] = {}
    stop, recorded, failures, peak, samples = None, 0, [], disk_bytes(), 0
    os.environ.update(CHILD_ENV)
    settled_charge = charged()
    if settled_charge["cpu_hours"] >= CAP_CPU_HOURS - CPU_HALT_MARGIN_HOURS:
        return f"the cap of {CAP_CPU_HOURS} CPU-h is reached"

    def live() -> dict:
        cpu = settled_charge["cpu_hours"] + (time.process_time() - controller0) / 3600.0
        cpu += sum(r["attempt"].get("cpu_seconds_seen", 0.0) for r in running.values()) / 3600.0
        nbytes = settled_charge["download_bytes"] + sum(
            r["attempt"].get("bytes_seen", 0) for r in running.values()
        )
        return {"cpu_hours": cpu, "download_bytes": nbytes}

    def stop_all(status: str, reason: str) -> None:
        for key in list(running):
            r = running.pop(key)
            _kill(r)
            settle(r["attempt"], None, status, reason)

    try:
        while True:
            while todo and stop is None and len(running) < n:
                elapsed = 0.0 if not running and recorded == 0 else time.time() - start
                i = pick(todo, running, elapsed, live(), k)
                if isinstance(i, str):
                    stop = i
                    break
                if i is None:
                    break
                u = todo.pop(i)
                running[u["key"]] = _launch(ctx, u, plans[u["part"]])
            if not running:
                break
            time.sleep(SAMPLE_SECONDS)
            samples += 1
            peak = max(peak, disk_bytes())
            for key in list(running):
                r = running[key]
                a, u = r["attempt"], r["unit"]
                seen = sr.process_cpu_seconds(r["proc"].pid) if r["proc"].is_alive() else None
                if seen is None:  # unreadable or ended: the wall since the last reading bounds it
                    seen = a.get("cpu_seconds_seen", 0.0) + SAMPLE_SECONDS
                a["cpu_seconds_seen"] = max(a.get("cpu_seconds_seen", 0.0), seen)
                if u["kind"] == "fetch":
                    a["bytes_seen"] = observe_download(
                        r["baseline"], _tic_snapshot(int(u["tic_id"])), r["max_seen"]
                    )
                write_json(ATTEMPTS / f"{a['attempt_id']}.json", a)
                why = None
                if a["cpu_seconds_seen"] > u["cpu_allowance_seconds"]:
                    why = (
                        "CPU_ALLOWANCE",
                        f"the unit passed its CPU allowance of {u['cpu_allowance_seconds']:.0f} s",
                    )
                elif u["kind"] == "fetch" and a.get("bytes_seen", 0) >= u["allowance_bytes"]:
                    why = (
                        "DOWNLOAD_ALLOWANCE",
                        f"the download passed its allowance of {int(u['allowance_bytes'])} bytes",
                    )
                if why is not None:
                    running.pop(key)
                    _kill(r)
                    settle(a, None, *why)
                    recorded += 1
                    continue
                if not r["proc"].is_alive():
                    running.pop(key)
                    r["proc"].join()
                    rec = (
                        json.loads(r["result"].read_text("utf-8")) if r["result"].exists() else None
                    )
                    status = settle(
                        a,
                        rec,
                        None if rec else "WORKER_LOST",
                        None if rec else f"exit code {r['proc'].exitcode}, no result",
                    )
                    recorded += 1
                    finish_target(json.loads((RECORDS / f"{key}.json").read_text("utf-8")))
                    print(key, status, (rec or {}).get("outcome"), round(a["cpu_seconds_seen"]),
                          f"charged {live()['cpu_hours']:.2f} CPU-h", f"peak {peak / 1e9:.2f} GB",
                          flush=True)  # fmt: skip
            now = live()
            write_json(sr.MARKER, {"heartbeat": time.time(), "interval_seconds": SAMPLE_SECONDS,
                                   "running": {k_: r["attempt"]["attempt_id"]
                                               for k_, r in running.items()}})  # fmt: skip
            if now["cpu_hours"] >= CAP_CPU_HOURS - CPU_HALT_MARGIN_HOURS:
                stop = stop or f"the CPU cap: {now['cpu_hours']:.3f} CPU-h charged"
                stop_all("STOPPED_AT_CAP", stop)
            elif peak > CAP_DISK_BYTES:
                stop = stop or f"the disk cap: a sample of {peak / 1e9:.2f} GB"
                stop_all("STOPPED_AT_CAP", stop)
            elif now["download_bytes"] > CAP_DOWNLOAD_BYTES:
                stop = stop or f"the download cap: {now['download_bytes'] / 1e9:.2f} GB charged"
                stop_all("STOPPED_AT_CAP", stop)
    except BaseException as exc:  # a failure of the supervisor itself stops everything
        failures.append(f"supervisor: {type(exc).__name__}: {exc}")
        stop = stop or f"the supervisor failed: {type(exc).__name__}: {exc}"
        try:
            stop_all("STOPPED_AT_CAP", "the supervisor stopped")
        except BaseException as inner:  # noqa: BLE001 - the attempts stay unsettled for recover()
            failures.append(f"settlement: {type(inner).__name__}: {inner}")
    finally:
        for r in running.values():  # anything left is ended; recover() settles it
            _kill(r)
        if sr.MARKER.exists() and not running:
            sr.MARKER.unlink()
    peak = max(peak, disk_bytes())
    ledger = sr._ledger()
    ledger.setdefault("pinned_fingerprints", fingerprints())
    ledger["caps"] = {
        "cpu_hours": CAP_CPU_HOURS,
        "download_bytes": CAP_DOWNLOAD_BYTES,
        "disk_bytes": CAP_DISK_BYTES,
        "deadline_local": DEADLINE.isoformat(),
    }
    ledger["batches"].append({
        "label": label, "started_utc": sr.utc(start), "ended_utc": sr.utc(),
        "wall_seconds": round(time.time() - start, 1), "workers": n,
        "simultaneous_downloads": k, "test_plan_sha256": plan_shas,
        "fingerprints": fingerprints(), "recorded_in_batch": recorded,
        "controller_cpu_hours": round((time.process_time() - controller0) / 3600.0, 6),
        "disk_peak_bytes": peak, "disk_samples": samples, "failures": failures, "stop": stop,
    })  # fmt: skip
    ledger["disk_peak_bytes"] = max(ledger.get("disk_peak_bytes", 0), peak)
    sr._save_ledger(ledger)
    after = charged()
    ledger["batches"][-1].update(
        {
            "cpu_hours_charged": round(after["cpu_hours"], 4),
            "download_bytes_charged": after["download_bytes"],
        }
    )
    sr._save_ledger(ledger)
    if stop is None:  # the caps checked again after the drain
        if after["cpu_hours"] > CAP_CPU_HOURS:
            stop = f"the CPU cap was passed after the drain ({after['cpu_hours']:.3f} CPU-h)"
        elif after["download_bytes"] > CAP_DOWNLOAD_BYTES:
            stop = "the download cap was passed after the drain"
        elif peak > CAP_DISK_BYTES:
            stop = "the disk cap was passed"
    return stop


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
        if "pinned_fingerprints" not in ledger:  # pinned before the first dispatch
            ledger["pinned_fingerprints"] = fingerprints()
            ledger["pinned_utc"] = sr.utc()
            sr._save_ledger(ledger)
        check_pinned(ledger)
        recovered = recover()
        if recovered:
            print("recovered attempts:", recovered, flush=True)
        if sr.MARKER.exists():
            sr.MARKER.unlink()
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
        print("all units recorded", json.dumps(charged()), flush=True)


# --- the bundle: 48 records (24 TOIs x 2 modes) ---------------------------------------------


def mode_record(t: dict, mode: str) -> dict:
    """One TOI in one mode, from its unit records only: the base and consensus outputs, the fit
    identity, the first disagreeing probe and the measured costs. A row whose units are not all
    recorded says so (``status: NO RECORD`` or ``required_missing``); a unit ended by a resource
    stop is listed in ``operational_stops``."""
    f = _read_record(unit_key(t["key"], "fetch"))
    b = _read_record(unit_key(t["key"], "base", mode))
    probes = {n: _read_record(unit_key(t["key"], "probe", mode, n)) for n, _, _ in PROBES}
    cons = consensus(b, probes)
    missing = [k for k in required_units(t)
               if k.split(".")[1] in ("fetch", mode) and _read_record(k) is None]  # fmt: skip
    stops = [r["unit_key"] for r in (f, b, *probes.values())
             if r is not None and r.get("status") in OPERATIONAL]  # fmt: skip
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
        "operational_stops": stops,
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
            "charged_download_bytes_of_the_toi": (f or {}).get("bytes_charged"),
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
ARCHIVE_MANIFEST = WORK / "run/archive-manifest.json"


def bundle() -> None:
    """The 48 mode rows (with every unit file's SHA-256, the attempts and the run's terminal
    state) to ``prototype-records.json``; the unit records themselves to ``prototype-units.json``
    if it stays within 5 MB, otherwise staged in ``.cache/v059/run/units.json`` for the Drive
    archive (``verify-archive`` checks the copy before anything local is retired)."""
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
        "attempts": attempts(),
        "tpf_deletions": [{"file": p.name, "sha256": sr.sha256(p.read_bytes()),
                           "content": json.loads(p.read_text("utf-8"))}
                          for p in sorted(sr.TPF_LOGS.glob("*.json"))],
    }  # fmt: skip
    text = json.dumps(unit_doc, indent=1, default=sr._plain) + "\n"
    target = UNITS_BUNDLE if len(text.encode()) <= MAX_GIT_BYTES else ARCHIVE_STAGE
    target.write_text(text, "utf-8", newline="\n")
    doc = {
        "schema": "refute-v059-prototype-records-2",
        "mode": "exploratory",
        "limits_label": LABEL,
        "method_status": "not_validated",
        "written_utc": sr.utc(),
        "fingerprints": fingerprints(),
        "run_state": ledger.get("state"),
        "run_state_reason": ledger.get("state_reason"),
        "charged": charged(),
        "units_file": {"path": target.relative_to(ROOT).as_posix(),
                       "sha256": sr.sha256(text.encode()), "bytes": len(text.encode())},
        "unit_files_sha256": {u["file"]: u["sha256"] for u in unit_doc["units"]},
        "records": [mode_record(t, m) for t in all_targets for m in MODES],
    }  # fmt: skip
    BUNDLE.write_text(json.dumps(doc, indent=1, default=sr._plain) + "\n", "utf-8", newline="\n")
    print(len(doc["records"]), "mode rows;", len(unit_doc["units"]), "unit records in",
          target.relative_to(ROOT).as_posix(), "; run state", ledger.get("state"))  # fmt: skip


def verify_archive(copy: str) -> None:
    """The Drive copy of the staged unit records: a distinct file under the approved archive
    root, whose SHA-256 equals the bundle's and the staged source's; the receipt (destination and
    both hashes) is written to ``.cache/v059/run/archive-manifest.json``. Nothing is deleted."""
    doc = json.loads(BUNDLE.read_text("utf-8"))
    want = doc["units_file"]["sha256"]
    src = (ROOT / doc["units_file"]["path"]).resolve()
    dest = Path(copy).resolve()
    if dest == src or ROOT.resolve() in dest.parents:
        raise SystemExit("refused: the copy must be a distinct file outside the project")
    if ARCHIVE_ROOT.resolve() not in dest.parents:
        raise SystemExit(f"refused: the copy must be under {ARCHIVE_ROOT.as_posix()}")
    got_src = sr.sha256_path(src) if src.exists() else None
    got = sr.sha256_path(dest)
    receipt = {"utc": sr.utc(), "source": doc["units_file"]["path"], "source_sha256": got_src,
               "destination": dest.as_posix(), "destination_sha256": got,
               "expected_sha256": want, "match": got == want and got_src == want}  # fmt: skip
    write_json(ARCHIVE_MANIFEST, receipt)
    print(json.dumps(receipt))
    if not receipt["match"]:
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
    no unit in flight and every attempt settled, and, when unit records were staged for the Drive,
    only after the archive receipt matches: every pixel file released (manifest first), then each
    light curve by literal path and SHA-256, inside ``.cache/v059`` only."""
    ledger = sr._ledger()
    if ledger.get("state") not in ("complete", "abandoned"):
        raise SystemExit(f"refused: the run is {ledger.get('state')!r}, not complete or abandoned")
    if sr.MARKER.exists() or any(a.get("state") != "settled" for a in attempts()):
        raise SystemExit("refused: a unit is still in flight or not settled")
    if ARCHIVE_STAGE.exists():
        receipt = (
            json.loads(ARCHIVE_MANIFEST.read_text("utf-8")) if ARCHIVE_MANIFEST.exists() else {}
        )
        if not receipt.get("match"):
            raise SystemExit("refused: the staged unit records have no matching archive receipt")
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
    no_link_roots()  # before any directory is created
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
