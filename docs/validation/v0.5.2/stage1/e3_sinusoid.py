"""v0.5.2 stage 1, E3: the sinusoid under stellar trends (design: e3-design.md). Development seeds
only.

Usage (heavy; from the project root):
``scripts/launch_affinity.ps1 -Script docs/validation/v0.5.2/stage1/e3_sinusoid.py
-Arguments 'run[,<max units>]' -Log .cache/v052/e3/run``; then
``.venv/Scripts/python.exe <this file> summarize`` writes ``e3-sinusoid.json``.
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
import runlib  # noqa: E402
import wp3b as runner  # noqa: E402

# one thread per worker: the workers read these at start (E1 and E2 get them from acceptance/a0.py)
runner.c.env_threads()

NOISES = ("trend", "correlated_trend")
SNRS = (12, 20)
PLANETS = 150
ALTERNATIVES = 100
ARMS = ("built", "extra6", "narrow")
NEW_ARMS = ("extra6", "narrow")
ALT_CASES = ("P/2", "P", "2P", "near")
P = runner.P_STD
D = runner.D_STD
FACTORS = {"P/2": 0.5, "P": 1.0, "2P": 2.0}
S_BINS = ((0.0, 0.5), (0.5, 1.0), (1.0, 2.0), (2.0, math.inf))
AMP_BINS = ((0.0, 0.5), (0.5, 1.0), (1.0, math.inf))
WILSON = 1.959964
PROBE_UNITS = 40
CAP_HOURS = 1.5
BATCH = 88
SCREEN_FAILURE = 0.05
DETECTION_BENCHMARK = 0.90
DETECTABLE_BENCHMARK = 0.95
NON_REGRESSION = -0.05
CONCENTRATION = 0.90
STATUSES = ("PASS", "FAIL", "INCONCLUSIVE")


def fingerprint() -> tuple[str, dict]:
    import astropy
    import scipy

    from refute.core.codehash import compute_code_hash

    def sha(path):
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()

    acc = ROOT / "docs/validation/v0.5.1/acceptance"
    doc = {
        "design": sha(HERE / "e3-design.md"),
        "script": sha(Path(__file__)),
        "runlib": sha(HERE / "runlib.py"),
        "runner": sha(acc / "wp3b.py"),
        "common": sha(acc / "common.py"),
        "code_hash": compute_code_hash(ROOT).sha256,
        "plan": hashlib.sha256(
            json.dumps(runner._plan().model_dump(mode="json"), sort_keys=True).encode()
        ).hexdigest(),
        "constants": [NOISES, SNRS, PLANETS, ALTERNATIVES, ARMS, ALT_CASES, CAP_HOURS],
        "python": platform.python_version(),
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "astropy": astropy.__version__,
    }
    return hashlib.sha256(json.dumps(doc, sort_keys=True).encode()).hexdigest()[:16], doc


def dev_seed(case: str, noise: str, i: int) -> int:
    text = f"refute-v052-dev:e3:{case}:{noise}:{i}"
    return int(hashlib.sha256(text.encode()).hexdigest()[:16], 16)


def _with_arm(arm, lc, cand):
    from refute.core.sensitivity import enforce_sensitivity
    from refute.packs.tess import battery_v51 as v51
    from refute.packs.tess import power

    plan = runner._plan()
    cp = plan.v051.model_copy(update={"sinusoid_extra_frequencies": 6 if arm == "extra6" else 3})
    original = v51._ls_peak

    def narrow(time_, resid, err, f_min, f_max, excluded, width):
        return original(time_, resid, err, f_min, f_max, excluded, 0.5 * width)

    try:
        if arm == "narrow":
            v51._ls_peak = narrow
        raw = v51.check_sinusoid(
            lc, cand, plan.stronger, cp, power.candidate_seed("sinusoid", cand)
        )
    finally:
        v51._ls_peak = original
    final = enforce_sensitivity([raw], power.registry_for(plan))[0]
    return runner._describe(raw, final, cand), dict(raw.sensitivity or {})


def _projection(lc, cand, d, trend):
    """The known noise-free trend through this trial's own joint design (row 3.7's method)."""
    from refute.packs.tess import battery_v51 as v51

    t, sec, med, err = runner._kept(lc, cand)
    periods = [P * FACTORS[k] for k in runner.LABELS] + [1.0 / f for f in d["extra"]]
    x = v51._design(t, sec, periods)
    model = trend["amplitude"] * np.sin(2.0 * np.pi * t / trend["period"] + trend["phase"]) / med
    coef, _, _ = v51._wls(x, model, err)
    n_off = len(np.unique(sec))
    return {
        k: math.hypot(float(coef[n_off + 2 * j]), float(coef[n_off + 2 * j + 1])) * 1e6
        for j, k in enumerate(runner.LABELS)
    }


def unit(arg):
    case, snr, noise, i, seed, fp = arg
    started = time.process_time()
    waves = ()
    if case in FACTORS:
        waves = [(P * FACTORS[case], 2.0)]
    elif case == "near":
        lc0, cand0, _, _ = runner._planet_curve(seed, noise, P, D, snr, ())
        t_kept, _, _, _ = runner._kept(lc0, cand0)
        waves = [(1.0 / (1.0 / P + 0.75 / float(t_kept.max() - t_kept.min())), 2.0)]
    lc, cand, _, trend = runner._planet_curve(seed, noise, P, D, snr, waves)
    t, _, _, _ = runner._kept(lc, cand)
    span = float(t.max() - t.min())
    separations = {k: abs(1.0 / trend["period"] - 1.0 / (P * FACTORS[k])) * span for k in FACTORS}
    nearest = min(separations, key=separations.get)
    rec = {
        "unit": f"{case}:{snr}:{noise}:{i}",
        "fingerprint": fp,
        "case": case,
        "snr": snr,
        "noise": noise,
        "i": i,
        "depth": cand.depth,
        "span": span,
        "trend": trend,
        "separations": separations,
        "nearest": nearest,
        "separation": separations[nearest],
        "amplitude_over_depth": trend["amplitude"] / cand.depth,
        "arms": {},
    }
    for arm in ARMS:
        d, blocks = _with_arm(arm, lc, cand)
        rec["arms"][arm] = {
            "status": d["status"],
            "final": d["final"],
            "flagged": d["flagged"],
            "applicable": d["applicable"],
            "detectable": d["detectable"],
            "fits": d["fits"],
            "sensitivity": blocks,
            "extra": d["extra"],
            "inconclusive_class": d["inconclusive_class"],
            "trend_projection_ppm": _projection(lc, cand, d, trend),
        }
    rec["cpu_seconds"] = time.process_time() - started
    return rec


def schedule():
    out = []
    for i in range(max(PLANETS, ALTERNATIVES)):
        for noise in NOISES:
            if i < PLANETS:
                for snr in SNRS:
                    out.append(("planet", snr, noise, i, dev_seed(f"planet-{snr}", noise, i)))
            if i < ALTERNATIVES:
                for case in ALT_CASES:
                    out.append((case, 20, noise, i, dev_seed(f"alt-{case}", noise, i)))
    return out


def _paths():
    fp, doc = fingerprint()
    out = ROOT / ".cache/v052/e3" / fp
    return fp, doc, out


def _uid(a):
    return f"{a[0]}:{a[1]}:{a[2]}:{a[3]}"


def run(limit=None):
    from refute.core.runner import default_workers

    fp, doc, out = _paths()
    out.mkdir(parents=True, exist_ok=True)
    (out / "manifest.json").write_text(json.dumps(doc, indent=1, sort_keys=True), "utf-8")
    runlib.bounded_run(
        unit, _uid, schedule(), fp, out, CAP_HOURS, PROBE_UNITS, BATCH, default_workers(), limit
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


def _finite(v):
    return isinstance(v, (int, float)) and math.isfinite(float(v))


def _validate_arm(unit_id, name, arm, reasons):
    where = f"{unit_id} arm {name}"
    types = {
        "status": str, "final": str, "flagged": list, "applicable": list, "detectable": dict,
        "fits": dict, "sensitivity": dict, "extra": list, "trend_projection_ppm": dict,
    }  # fmt: skip
    for field, kind in types.items():
        if not isinstance(arm.get(field), kind):
            reasons.append(f"{where}: missing or malformed {field}")
            return
    if arm["status"] not in STATUSES or arm["final"] not in STATUSES:
        reasons.append(f"{where}: invalid status")
    if not set(arm["flagged"]) <= set(FACTORS):
        reasons.append(f"{where}: invalid harmonic flagged")
    if set(arm["applicable"]) != set(FACTORS):
        reasons.append(
            f"{where}: not every harmonic is applicable (P = {P} d: all three should be)"
        )
    if set(arm["detectable"]) != set(arm["applicable"]):
        reasons.append(f"{where}: applicable and detectable disagree")
    if not all(isinstance(v, bool) for v in arm["detectable"].values()):
        reasons.append(f"{where}: a detectable value is not boolean")
    if (
        arm["status"] == "INCONCLUSIVE"
    ):  # no fits are expected; their absence is reported, not fatal
        return
    for key in arm["applicable"]:
        fit, block = arm["fits"].get(key), arm["sensitivity"].get(key)
        if not isinstance(fit, dict) or not isinstance(block, dict):
            reasons.append(f"{where}: no fit or no sensitivity block for {key}")
            continue
        values = [
            fit.get(k) for k in ("semi_amplitude_ppm", "semi_amplitude_err_ppm", "significance")
        ]
        if not all(_finite(v) for v in values) or not values[1] > 0:
            reasons.append(f"{where}: an invalid fit at {key}")
        prob, req = block.get("probability"), block.get("required_probability")
        if not (_finite(prob) and 0.0 <= prob <= 1.0 and _finite(req) and 0.0 < req <= 1.0):
            reasons.append(f"{where}: an invalid probability at {key}")
        elif block.get("rule_id") != "compound-sim-1" or block.get("detectable") is not (
            prob >= req
        ):
            reasons.append(f"{where}: an inconsistent sensitivity block at {key}")
    projection = arm["trend_projection_ppm"]
    if set(projection) != set(FACTORS) or not all(_finite(v) for v in projection.values()):
        reasons.append(f"{where}: an invalid projection")


def _validate(recs, fp):
    """Structural problems of the records: the aggregation runs only if there are none."""
    reasons: list[str] = []
    units = [r.get("unit") for r in recs]
    if len(units) != len(set(units)):
        reasons.append("a unit is recorded twice")
    if any(r.get("fingerprint") != fp for r in recs):
        reasons.append("a record of another fingerprint")
    by = {_uid(a): a for a in schedule()}
    if set(units) != set(by):
        reasons.append(f"schedule incomplete or unexpected: {len(set(by) - set(units))} missing")
    for r in recs:
        if "arms" not in r:
            reasons.append(f"{r.get('unit')}: the unit errored")
            continue
        missing = [
            k for k in ("unit", "case", "snr", "noise", "i", "separation", "amplitude_over_depth",
                        "depth", "span", "cpu_seconds") if k not in r
        ]  # fmt: skip
        if missing or not isinstance(r["arms"], dict):
            reasons.append(f"{r.get('unit')}: missing fields {missing}")
            continue
        a = by.get(r["unit"])
        if a is None or (r["case"], r["snr"], r["noise"], r["i"]) != a[:4]:
            reasons.append(f"{r['unit']}: metadata mismatch")
        if set(r["arms"]) != set(ARMS):
            reasons.append(f"{r['unit']}: arms mismatch")
            continue
        for v in (r["separation"], r["amplitude_over_depth"], r["depth"], r["span"]):
            if not _finite(v):
                reasons.append(f"{r['unit']}: a non-finite input")
        if _finite(r["depth"]) and not r["depth"] > 0:
            reasons.append(f"{r['unit']}: a non-positive depth")
        if not _finite(r["cpu_seconds"]) or r["cpu_seconds"] < 0:
            reasons.append(f"{r['unit']}: invalid CPU accounting")
        for name in ARMS:
            _validate_arm(r["unit"], name, r["arms"][name], reasons)
    return reasons


def _fail(r, arm):
    return r["arms"][arm]["status"] == "FAIL"


def _adverse(r, arm):
    return r["arms"][arm]["final"] in ("FAIL", "INCONCLUSIVE")


def _transitions(rs, arm):
    out: dict[str, int] = {}
    for r in rs:
        key = f"{r['arms']['built']['final']} -> {r['arms'][arm]['final']}"
        out[key] = out.get(key, 0) + 1
    return out


def _status_counts(rs, arm):
    counts = {"raw": {}, "final": {}}
    for r in rs:
        for key, field in (("raw", "status"), ("final", "final")):
            v = r["arms"][arm][field]
            counts[key][v] = counts[key].get(v, 0) + 1
    return counts


def _planet_cell(rs, key, reasons, worth):
    cell = {}
    for arm in ARMS:
        block = {
            "failure": wilson(sum(_fail(r, arm) for r in rs), len(rs)),
            "status_counts": _status_counts(rs, arm),
        }
        for lo, hi in S_BINS:
            sub = [r for r in rs if lo <= r["separation"] < hi]
            label = f"s_{lo}_{hi}"
            block[label] = wilson(sum(_fail(r, arm) for r in sub), len(sub))
            for alo, ahi in AMP_BINS:
                part = [r for r in sub if alo <= r["amplitude_over_depth"] < ahi]
                block[f"{label}_amp_{alo}_{ahi}"] = wilson(
                    sum(_fail(r, arm) for r in part), len(part)
                )
        sep = [r for r in rs if r["separation"] >= 1.0]
        block["separated_s_ge_1"] = wilson(sum(_fail(r, arm) for r in sep), len(sep))
        detectable = [
            bool(r["arms"][arm]["applicable"]) and all(r["arms"][arm]["detectable"].values())
            for r in rs
        ]
        block["every_applicable_detectable"] = wilson(sum(detectable), len(rs))
        cell[arm] = block
    fails = [r for r in rs if _fail(r, "built")]
    cell["built_failures"] = len(fails)
    cell["built_failures_s_below_1"] = sum(r["separation"] < 1.0 for r in fails)
    cell["built_failures_trend_below_half_depth"] = sum(
        r["amplitude_over_depth"] < 0.5 for r in fails
    )
    cell["built_failures_by_nearest_harmonic"] = {
        k: sum(r["nearest"] == k for r in fails) for k in FACTORS
    }
    concentrated = cell["built_failures_s_below_1"] / len(fails) >= CONCENTRATION if fails else None
    sep = [r for r in rs if r["separation"] >= 1.0]
    for arm in NEW_ARMS:
        paired = runlib.paired_binary(
            [_adverse(r, "built") for r in sep], [_adverse(r, arm) for r in sep]
        )
        cell[f"{arm}_adverse_minus_built_separated"] = paired
        cell[f"{arm}_final_transitions_separated"] = _transitions(sep, arm)
        w = cell[arm]["separated_s_ge_1"]
        if paired is None or w is None:
            reasons.append(f"{key} {arm}: no separated planets for its decision")
            continue
        good = paired["hi"] < 0.0 and w["hi"] <= SCREEN_FAILURE
        if rs[0]["snr"] == 20:
            good = good and cell[arm]["every_applicable_detectable"]["rate"] >= DETECTABLE_BENCHMARK
        worth[arm] = worth[arm] and good
    return cell, concentrated


def _alt_cell(rs, case, key, reasons, worth):
    target = "P" if case == "near" else case
    cell = {}
    hits = {arm: [target in r["arms"][arm]["flagged"] for r in rs] for arm in ARMS}
    for arm in ARMS:
        one_depth = [bool(r["arms"][arm]["detectable"].get(target)) for r in rs]
        cell[arm] = {
            "detection": wilson(sum(hits[arm]), len(rs)),
            "one_depth_detectable": wilson(sum(one_depth), len(rs)),
            "status_counts": _status_counts(rs, arm),
        }
    baseline = cell["built"]["detection"]["rate"]
    if baseline < DETECTION_BENCHMARK:
        reasons.append(
            f"{key}: the built arm's recovery {baseline:.2f} is below {DETECTION_BENCHMARK}: "
            "preservation cannot be judged"
        )
    for arm in NEW_ARMS:
        paired = runlib.paired_binary(hits["built"], hits[arm])
        cell[f"{arm}_minus_built"] = paired
        good = paired["lo"] > NON_REGRESSION
        if case != "near":
            good = good and cell[arm]["detection"]["rate"] >= DETECTION_BENCHMARK
        worth[arm] = worth[arm] and good
    return cell


def summarize():
    fp, doc, out_dir = _paths()
    recs = runlib.read_records(out_dir / "records.jsonl", fp)
    reasons = _validate(recs, fp)
    run_state = runlib.read_state(out_dir)
    if run_state is None or run_state["state"] != "complete":
        reasons.append(f"the run did not complete under its cap: {run_state}")
    out = {
        "label": "development experiment E3 (v0.5.2 stage 1); it decides nothing about any target",
        "method_status": "not_validated",
        "fingerprint": fp,
        "manifest": doc,
        "units": sum(1 for r in recs if "arms" in r),
        "cpu_hours": round(sum(float(r.get("cpu_seconds", 0.0)) for r in recs) / 3600.0, 3),
        "cells": {},
        "alternatives": {},
    }
    worth = {arm: True for arm in NEW_ARMS}
    concentrated = {}
    if not reasons:
        for snr in SNRS:
            for noise in NOISES:
                key = f"snr{snr}/{noise}"
                rs = [
                    r
                    for r in recs
                    if r["case"] == "planet" and r["snr"] == snr and r["noise"] == noise
                ]
                out["cells"][key], concentrated[key] = _planet_cell(rs, key, reasons, worth)
        for noise in NOISES:
            for case in ALT_CASES:
                key = f"{noise}/{case}"
                rs = [r for r in recs if r["case"] == case and r["noise"] == noise]
                out["alternatives"][key] = _alt_cell(rs, case, key, reasons, worth)
    out["decision"] = {
        "state": "NOT ESTABLISHED" if reasons else "EVALUATED",
        "reasons": reasons[:40],
        "concentrated_at_unseparated_trends_per_cell": None if reasons else concentrated,
        "worth_carrying_to_the_specification": None if reasons else worth,
        "note": "0.05 is an exploratory screening threshold; the 0.0027 requirement is unresolved",
    }
    (HERE / "e3-sinusoid.json").write_text(
        json.dumps(out, indent=1, sort_keys=True, allow_nan=False) + "\n", "utf-8"
    )
    print(json.dumps({k: out[k] for k in ("decision", "units", "cpu_hours")}, indent=1))
    for key, cell in out["cells"].items():
        print(
            key,
            cell["built"]["failure"],
            "s<1:",
            cell["built_failures_s_below_1"],
            "of",
            cell["built_failures"],
        )


if __name__ == "__main__":
    if sys.argv[1:2] == ["run"]:
        run(int(sys.argv[2]) if len(sys.argv) > 2 else None)
    elif sys.argv[1:] == ["summarize"]:
        summarize()
    else:
        raise SystemExit("usage: e3_sinusoid.py run [max units] | summarize")
