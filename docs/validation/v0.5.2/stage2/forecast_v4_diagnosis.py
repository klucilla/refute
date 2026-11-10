"""v0.5.2 stage 2: a diagnosis of ``odd_even`` in the D2 forecast with version 4 (the maintainer's
decision of 2026-11-10 after the forecast's stop, #216, item 1 (b) and (c)). Development seeds
and data only; no code of ``src/`` changes and no rule is new. **It decides nothing.**
``method_status: not_validated``.

**The curves.** From the forecast's records (``forecast_v4.py``, development seeds
``c1.development_seed("P", i)``): every eligible planet whose ``odd_even`` was INCONCLUSIVE
under version 4, and a control of the first 10 eligible planets (by index) whose ``odd_even``
passed. Each is generated again from its seed, the candidate found again as in the forecast, and
version 3 and version 4 attack it, recording ``odd_even``'s status before and after the
sensitivity rule, its metrics and its sensitivity block.

**The errors**, in ppm, of version 4's odd/even box difference:

- ``sigma_a0``: A0's group error, the one the test divides by and the one the sensitivity rule
  uses (``|depth_odd - depth_even| / difference_sigma``);
- ``sigma_box_true``: the standard error of the same box difference (the same measured events,
  windows and inverse-variance group weights) under the generator's own noise, white plus the
  exponential AR(1) term of each sector (sigma_r = sigma_w / 2 when correlated), on the cadences
  of the preprocessed series, as a quadratic form; the detrending's effect on the noise is left
  out;
- ``sigma_cr``: the Cramer-Rao standard error of the odd/even depth difference with the true
  trapezoid and the same noise, as v0.5.1's WP1 computed it (``feasibility/forecast.py``).

So ``sigma_a0 / sigma_cr = (sigma_a0 / sigma_box_true) x (sigma_box_true / sigma_cr)``: the
first factor is what A0's empirical error (the comb's windows) adds over the box's true error,
the second what the box estimator loses against the optimal one. Version 3's ``odd_even`` (the
matched statistic) is recorded alongside for comparison.

Usage: ``scripts/launch_affinity.ps1 -Script <this file> -Arguments run -Log
.cache/v052/s2/forecast-diagnosis``; then ``summarize`` writes ``forecast-v4-diagnosis.json``.
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(HERE))
import budgeted  # noqa: E402
import forecast_v4 as f  # noqa: E402

OUT = ROOT / ".cache/v052/s2/forecast-v4-diagnosis"
SECTION, PART = "remaining_work_packages", "forecast_diagnosis"
ALLOCATION_HOURS, HARD_CAP_HOURS = 2.2, 3.0  # 35 curves at about 214 CPU-seconds (one smoke)
WORKERS = 12
PIN = tuple(range(8, 32, 2))
MAX_SHARD_SECONDS = 1200.0
CONTROLS = 10
TAU_DAYS = 1.0 / 24.0
KEPT = ("SURVIVED", "WEAKENED")


def selection() -> list[tuple[int, str]]:
    fp = f.fingerprint()
    data = budgeted.assembled(
        f.SECTION, f.PART, f.OUT / fp, f.shard, f.shards(), fp, f.WORKERS, pin=f.PIN,
        max_shard_seconds=f.MAX_SHARD_SECONDS,
    )  # fmt: skip
    recs = [json.loads(x) for x in data.decode().splitlines() if x.strip()]
    eligible = sorted(
        (r for r in recs if r.get("status") == "OK" and r["gate_passed"] and r["identity"]),
        key=lambda r: r["index"],
    )
    status = {r["index"]: r["v4_tests"].get("odd_even", {}).get("status") for r in eligible}
    out = [(i, "inconclusive") for i, s in status.items() if s == "INCONCLUSIVE"]
    out += [(i, "control") for i, s in status.items() if s == "PASS"][:CONTROLS]
    return sorted(out)


def _k_quadratic(t: np.ndarray, u: np.ndarray) -> float:
    """``u^T K u`` for the unit exponential covariance ``exp(-|dt| / tau)`` on sorted times."""
    a = np.exp(-np.diff(t) / TAU_DAYS)
    fwd = np.empty_like(u)
    bwd = np.empty_like(u)
    fwd[0] = u[0]
    for j in range(1, u.size):
        fwd[j] = u[j] + a[j - 1] * fwd[j - 1]
    bwd[-1] = u[-1]
    for j in range(u.size - 2, -1, -1):
        bwd[j] = u[j] + a[j] * bwd[j + 1]
    return float(np.sum(u * (fwd + bwd - u)))


def box_true_sigma(flat, measured, candidate, ev, sigma_w, sigma_r) -> float:
    """The box difference's standard error under the generator's noise (module docstring)."""
    half = candidate.duration / 2.0
    inner = half + ev.baseline_gap_durations * candidate.duration
    outer = half + ev.baseline_outer_durations * candidate.duration
    errors = np.asarray(measured.errors, dtype=float)
    epochs = np.asarray(measured.epochs, dtype=int)
    odd, even = epochs % 2 != 0, epochs % 2 == 0
    w = 1.0 / errors**2
    weight = np.where(odd, w / w[odd].sum(), -w / w[even].sum())
    u = np.zeros(flat.time.size)
    for c, wi in zip(np.asarray(measured.centers, dtype=float), weight, strict=True):
        dt = np.abs(flat.time - c)
        inside = dt <= half
        base = (dt > inner) & (dt <= outer)
        if inside.any():
            u[inside] -= wi / inside.sum()
        if base.any():
            u[base] += wi / base.sum()
    var = sigma_w**2 * float(np.sum(u**2))
    if sigma_r > 0:
        for s in np.unique(flat.sector):
            sel = flat.sector == s
            if np.any(u[sel]):
                var += sigma_r**2 * _k_quadratic(flat.time[sel], u[sel])
    return math.sqrt(var)


def cr_sigma(data, truth, sigma_w, sigma_r) -> float:
    """v0.5.1 WP1's Cramer-Rao error of the odd/even depth difference."""
    from refute.packs.tess import synthetic as syn

    sys.path.insert(0, str(ROOT / "docs/validation/v0.5.1/feasibility"))
    import forecast as wp1

    t, sector = data.lc.time, data.lc.sector
    p, t0 = truth["period_days"], truth["t0_btjd"]
    unit = syn.trapezoid(t, p, t0, 1.0, truth["duration_days"], truth["ingress_fraction"])
    epoch = np.round((t - t0) / p).astype(int)
    i_odd = wp1.mahalanobis2(t, sector, np.where(epoch % 2 != 0, unit, 0.0), sigma_w, sigma_r)
    i_even = wp1.mahalanobis2(t, sector, np.where(epoch % 2 == 0, unit, 0.0), sigma_w, sigma_r)
    return math.sqrt(1 / i_odd + 1 / i_even) if i_odd > 0 and i_even > 0 else math.inf


def _clean(value):
    if isinstance(value, dict):
        return {k: _clean(v) for k, v in value.items()}
    if isinstance(value, list | tuple):
        return [_clean(v) for v in value]
    if isinstance(value, float | int | str | bool) or value is None:
        return value
    if isinstance(value, np.generic):
        return value.item()
    return repr(value)


def one(index: int, group: str) -> dict:
    from refute.core.sensitivity import enforce_sensitivity
    from refute.packs.tess import a0_v4
    from refute.packs.tess.calib05 import c1
    from refute.packs.tess.detrend import detrend
    from refute.packs.tess.pipeline import attack_candidate, global_prewhitening
    from refute.packs.tess.power import registry_for
    from refute.packs.tess.search import search_period

    started = time.process_time()
    data, truth = c1.generate("P", c1.development_seed("P", index))
    p04, p3, p4 = f.plans()
    flat = detrend(data.lc, p04.detrend)
    pw, searched = global_prewhitening(data, p04, flat)
    cand = search_period(searched, p04.search).candidate
    sigma_w = truth["sigma_white_ppm"] * 1e-6
    sigma_r = sigma_w / 2.0 if truth["correlated"] else 0.0
    rec: dict = {"index": index, "group": group, "target_snr": truth["target_snr"]}
    for name, plan in (("v3", p3), ("v4", p4)):
        captured = []
        original = a0_v4.empirical_events

        def spy(flat_, candidate, *args, _original=original, _captured=captured, **kwargs):
            got = _original(flat_, candidate, *args, **kwargs)
            if not _captured:
                _captured.append((flat_, candidate, got[0]))
            return got

        a0_v4.empirical_events = spy
        try:
            g = attack_candidate(data, cand, plan, None, None, pw)
        finally:
            a0_v4.empirical_events = original
        raw = next(t for t in g.tests if t.name == "odd_even")
        final = next(
            t
            for t in enforce_sensitivity(list(g.tests), registry_for(plan))
            if t.name == "odd_even"
        )
        row = {
            "status_before_sensitivity": raw.status.value,
            "status": final.status.value,
            "message": raw.message,
            "metrics": _clean(raw.metrics),
            "sensitivity": _clean(raw.sensitivity),
        }
        if name == "v4" and captured:
            fl, c, measured = captured[0]
            m = raw.metrics
            z = m.get("difference_sigma")
            if z:
                row["sigma_a0_ppm"] = abs(m["depth_odd_ppm"] - m["depth_even_ppm"]) / z
            row["sigma_box_true_ppm"] = (
                box_true_sigma(fl, measured, c, plan.gauntlet.events, sigma_w, sigma_r) * 1e6
            )
            row["n_measured"] = len(measured)
        rec[name] = row
    rec["sigma_cr_ppm"] = cr_sigma(data, truth, sigma_w, sigma_r) * 1e6
    rec["depth_ppm"] = truth["depth"] * 1e6
    v4 = rec["v4"]
    if "sigma_a0_ppm" in v4 and rec["sigma_cr_ppm"] > 0:
        v4["ratio_a0_to_cr"] = v4["sigma_a0_ppm"] / rec["sigma_cr_ppm"]
        v4["factor_a0_over_box_true"] = v4["sigma_a0_ppm"] / v4["sigma_box_true_ppm"]
        v4["factor_box_true_over_cr"] = v4["sigma_box_true_ppm"] / rec["sigma_cr_ppm"]
    rec["status"] = "OK"
    rec["cpu_seconds"] = time.process_time() - started
    return rec


def shard(arg) -> bytes:
    index, group = arg
    try:
        rec = one(index, group)
    except Exception as exc:  # noqa: BLE001 - recorded, never dropped
        rec = {"index": index, "group": group, "status": "ERROR", "reason": repr(exc)}
    return json.dumps(rec, sort_keys=True).encode() + b"\n"


def shards() -> list:
    return [(f"d{i:05d}", (i, g)) for i, g in selection()]


def fingerprint() -> str:
    from refute.core.codehash import compute_code_hash

    h = hashlib.sha256(compute_code_hash().sha256.encode())
    for path in (
        Path(__file__),
        HERE / "forecast_v4.py",
        ROOT / "docs/validation/v0.5.1/feasibility/forecast.py",
    ):  # noqa: E501
        h.update(hashlib.sha256(path.read_bytes()).digest())
    return h.hexdigest()[:16]


def run() -> None:
    fp = fingerprint()
    budgeted.declare(SECTION, {**_declared(), PART: ALLOCATION_HOURS})
    state = budgeted.execute(
        SECTION, PART, OUT / fp, shard, shards(), fp, WORKERS, pin=PIN,
        max_shard_seconds=MAX_SHARD_SECONDS, hard_cap_hours=HARD_CAP_HOURS,
    )  # fmt: skip
    print(state, flush=True)
    if state != "complete":
        raise SystemExit(state)


def _declared() -> dict:
    parts = budgeted.load()["sections"][SECTION]["parts"]
    return {k: v["allocation_hours"] for k, v in parts.items()}


def summarize() -> None:
    fp = fingerprint()
    data = budgeted.assembled(
        SECTION, PART, OUT / fp, shard, shards(), fp, WORKERS, pin=PIN,
        max_shard_seconds=MAX_SHARD_SECONDS,
    )  # fmt: skip
    recs = [json.loads(x) for x in data.decode().splitlines() if x.strip()]
    ok = [r for r in recs if r.get("status") == "OK"]

    def stats(group: str, key: str) -> dict | None:
        values = [r["v4"][key] for r in ok if r["group"] == group and key in r["v4"]]
        if not values:
            return None
        q = np.quantile(values, [0.0, 0.25, 0.5, 0.75, 1.0])
        return {"n": len(values), "min_q1_median_q3_max": [round(float(x), 3) for x in q]}

    out: dict = {
        "label": "diagnosis of odd_even in the D2 forecast with version 4; it decides nothing",
        "method_status": "not_validated",
        "curves": len(recs),
        "errors": sum(r.get("status") == "ERROR" for r in recs),
        "groups": {},
    }
    for group in ("inconclusive", "control"):
        mine = [r for r in ok if r["group"] == group]
        out["groups"][group] = {
            "n": len(mine),
            "v4_status_before_and_after_sensitivity": dict(
                __import__("collections").Counter(
                    f"{r['v4']['status_before_sensitivity']} -> {r['v4']['status']}" for r in mine
                )
            ),
            "v3_status_before_and_after_sensitivity": dict(
                __import__("collections").Counter(
                    f"{r['v3']['status_before_sensitivity']} -> {r['v3']['status']}" for r in mine
                )
            ),
            "ratio_a0_to_cr": stats(group, "ratio_a0_to_cr"),
            "factor_a0_over_box_true": stats(group, "factor_a0_over_box_true"),
            "factor_box_true_over_cr": stats(group, "factor_box_true_over_cr"),
        }
    out["cpu_hours"] = round(sum(float(r.get("cpu_seconds", 0.0)) for r in recs) / 3600.0, 3)
    (HERE / "forecast-v4-diagnosis.json").write_text(
        json.dumps(out, indent=1, sort_keys=True) + "\n", "utf-8"
    )
    print(json.dumps(out, indent=1, sort_keys=True))


if __name__ == "__main__":
    {"run": run, "summarize": summarize}[sys.argv[1]]()
