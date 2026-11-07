"""v0.5.1 amendment 9, item 1: the development measurement of `duration_excess` re-run with the
adopted estimator and its validity rule (the maintainer's decision of 2026-11-07: before amendment
4's figures are cited for this estimator).

Development data only (never confirmation data), the same cases and seeds as
``duration_measurement.py`` (amendment 3, item 2 (b)): planets of the frozen C1 generator (families
P and PG, seeds ``refute-v051-dev:dur-<family>:<i>``, 200 each) and binaries folded at half their
period in the C1 EB1 geometry (secondary ratio 1.0, 0.9 or 0.7, target SNR 10, 20 or 30, impact
parameter uniform in [0, 0.8]; seeds ``refute-v051-dev:dur-EB-<ratio>-<snr>:<i>``, 100 per case).

What changes from the first measurement: the measurement itself is the production function
``refute.packs.tess.battery_v51.check_duration_excess`` (the adopted phase-placement estimate of
``sigma_T`` with its validity rule: the selected fit's success, no parameter at a bound, at least
2 events at A0's minimum coverage; at least 10 valid placements, else INCONCLUSIVE), on the
curve flattened as before (the frozen v0.4 plan's detrending, the candidate's transits masked),
with the candidate at the truth's ephemeris (no search is run), its depth error the generator's
white noise over the in-transit cadences, and the generator's TIC star (radius and mass 1 +- 0.05).

It reports, per case: the statuses (PASS, FAIL = warning, INCONCLUSIVE by class), the fraction
not detectable among the measured, the warning rate, the warning rate among the detectable, and
the valid and rejected placements with their reasons. It decides nothing.

Usage:
  scripts/launch_affinity.ps1 -Script docs/validation/v0.5.1/feasibility/duration_measurement_v2.py
      -Arguments 'run' -Log .cache/v051/duration2/run
  .venv/Scripts/python.exe docs/validation/v0.5.1/feasibility/duration_measurement_v2.py summarize
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

ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT / ".cache/v051/duration2"
RECORDS = OUT / "records.jsonl"
HERE = Path(__file__).resolve().parent
RATIOS = (1.0, 0.9, 0.7)
SNRS = (10.0, 20.0, 30.0)
CADENCE = 2.0 / 1440.0


def seed(text: str) -> int:
    return int(hashlib.sha256(text.encode()).hexdigest()[:16], 16)


def measure(data, period, t0, depth, duration, sigma_w):
    from refute.packs.tess import battery_v51 as v51
    from refute.packs.tess import power
    from refute.packs.tess.calib05.plans import pair
    from refute.packs.tess.calib05.steps import v04_test_plan
    from refute.packs.tess.detrend import detrend
    from refute.packs.tess.events import transit_mask
    from refute.packs.tess.types import Candidate

    p04, _ = pair(v04_test_plan(ROOT))
    mask = transit_mask(data.lc.time, period, t0, duration)
    flat = detrend(data.lc, p04.detrend, mask=mask)
    in_transit = max(1, int(np.count_nonzero(mask)))
    candidate = Candidate(
        period=period,
        t0=t0,
        duration=duration,
        depth=depth,
        depth_err=sigma_w / math.sqrt(in_transit),
        snr=depth / (sigma_w / math.sqrt(in_transit)),
        log_likelihood=0.0,
        sde=0.0,
        n_transits=0,
    )
    result = v51.check_duration_excess(
        flat,
        candidate,
        data.star,
        p04.gauntlet,
        CADENCE,
        power.candidate_seed("duration_excess", candidate),
    )
    m = result.metrics
    block = (result.sensitivity or {}).get("main") or {}
    return {
        "status": result.status.value,
        "inconclusive_class": m.get("inconclusive_class"),
        "placements": m.get("placements"),
        "T_hours": m.get("duration_hours"),
        "sigma_T_hours": m.get("sigma_T_hours"),
        "T_max_P_hours": m.get("T_max_P_hours"),
        "sigma_Tmax_hours": m.get("sigma_Tmax_hours"),
        "excess_sigma": m.get("excess_sigma"),
        "detectable": block.get("detectable"),
    }


def run_planet(family: str, i: int) -> dict:
    from refute.packs.tess.calib05 import c1

    started = time.process_time()
    s = seed(f"refute-v051-dev:dur-{family}:{i}")
    rec = {"case": family, "index": i}
    try:
        data, truth = c1.generate(family, s)
    except c1.GenerationFailedError as exc:
        return {**rec, "status": "GENERATION_FAILURE", "reason": str(exc)}
    sigma_w = float(np.median(data.lc.flux_err))
    m = measure(data, truth["period_days"], truth["t0_btjd"], truth["depth"],
                truth["duration_days"], sigma_w)  # fmt: skip
    rec.update(target_snr=truth["target_snr"], **m)
    rec["cpu_seconds"] = time.process_time() - started
    return rec


def run_binary(ratio: float, snr: float, i: int) -> dict:
    """A C1 EB1-geometry binary with the secondary ratio and target SNR fixed, folded at half."""
    from refute.packs.tess import synthetic as syn
    from refute.packs.tess.calib05 import c1
    from refute.packs.tess.types import LightCurveData

    started = time.process_time()
    label = f"EB-{ratio}-{int(snr)}"
    s = seed(f"refute-v051-dev:dur-{label}:{i}")
    rec = {"case": label, "index": i}
    rng = np.random.default_rng(s)
    star = c1._draw_star("EB1", s, rng)
    t, sector = c1._times(star)
    try:
        tr = c1._transit_truth(rng, star, t, (snr, snr), (0.0, 0.8), "EB1")
    except c1.GenerationFailedError as exc:
        return {**rec, "status": "GENERATION_FAILURE", "reason": str(exc)}
    p, t0, d = tr["period_days"], tr["t0_btjd"], tr["depth"]
    model = 1.0 - syn.trapezoid(t, p, t0, d, tr["duration_days"], tr["ingress_fraction"])
    model -= syn.trapezoid(t, p, t0, ratio * d, tr["duration_days"], tr["ingress_fraction"], 0.5)
    flux = c1._noisy(model, t, sector, star)
    lc = LightCurveData(t, flux, np.full(t.size, star.sigma_w), sector, c1._years(t, sector))
    data = syn.make_data(lc, c1._sector_infos(lc, star), syn.make_star(), 1, None)
    m = measure(data, p / 2.0, t0, d * (1 + ratio) / 2.0, tr["duration_days"], star.sigma_w)
    rec.update(target_snr=snr, ratio=ratio, impact=tr["impact"], **m)
    rec["cpu_seconds"] = time.process_time() - started
    return rec


def _done():
    if not RECORDS.exists():
        return set()
    return {
        (r["case"], r["index"])
        for r in (json.loads(x) for x in RECORDS.read_text(encoding="utf-8").splitlines() if x)
    }


def run() -> None:
    from refute.core.runner import default_workers

    OUT.mkdir(parents=True, exist_ok=True)
    done = _done()
    jobs = [("P", i) for i in range(200)] + [("PG", i) for i in range(200)]
    jobs += [(f"EB-{r}-{int(q)}", i) for r in RATIOS for q in SNRS for i in range(100)]
    with ProcessPoolExecutor(max_workers=default_workers()) as pool:
        futures = {}
        for case, i in jobs:
            if (case, i) in done:
                continue
            if case in ("P", "PG"):
                futures[pool.submit(run_planet, case, i)] = (case, i)
            else:
                _, r, q = case.split("-")
                futures[pool.submit(run_binary, float(r), float(q), i)] = (case, i)
        for fut in as_completed(futures):
            case, i = futures[fut]
            try:
                rec = fut.result()
            except Exception as exc:  # noqa: BLE001 - recorded, kept in the denominators
                rec = {"case": case, "index": i, "status": "ERROR", "reason": repr(exc)}
            with RECORDS.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec, sort_keys=True) + "\n")


def wilson(k, n, z=1.959964):
    if not n:
        return None
    p = k / n
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return [round(c - h, 4), round(c + h, 4)]


def summarize() -> dict:
    recs = [json.loads(x) for x in RECORDS.read_text(encoding="utf-8").splitlines() if x.strip()]
    out = {
        "label": "development measurement (amendment 9, item 1): the adopted estimator with its "
        "validity rule; it decides nothing"
    }
    for case in sorted({r["case"] for r in recs}):
        rows = [r for r in recs if r["case"] == case]
        statuses: dict[str, int] = {}
        for r in rows:
            key = r["status"] + (
                f" ({r['inconclusive_class']})" if r.get("inconclusive_class") else ""
            )
            statuses[key] = statuses.get(key, 0) + 1
        measured = [r for r in rows if r["status"] in ("PASS", "FAIL")]
        det = [r for r in measured if r.get("detectable")]
        warn = sum(r["status"] == "FAIL" for r in measured)
        rejected: dict[str, int] = {}
        valid = 0
        for r in rows:
            pl = r.get("placements") or {}
            valid += pl.get("valid", 0)
            for reason, n in (pl.get("rejected") or {}).items():
                rejected[reason] = rejected.get(reason, 0) + n
        n = len(measured)
        out[case] = {
            "records": len(rows),
            "statuses": statuses,
            "measured": n,
            "not_detectable_fraction": (n - len(det)) / n if n else None,
            "not_detectable_wilson": wilson(n - len(det), n),
            "warning_fraction": warn / n if n else None,
            "warning_wilson": wilson(warn, n),
            "warning_fraction_among_detectable": (
                sum(r["status"] == "FAIL" for r in det) / len(det) if det else None
            ),
            "placements": {"valid": valid, "rejected": rejected},
        }
    out["cpu_hours"] = round(sum(r.get("cpu_seconds", 0) for r in recs) / 3600.0, 2)
    return out


if __name__ == "__main__":
    if sys.argv[1:] == ["run"]:
        run()
    elif sys.argv[1:] == ["summarize"]:
        doc = summarize()
        with open(HERE / "duration-measurement-v2.json", "x", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(doc, indent=1, sort_keys=True) + "\n")
        print(json.dumps(doc, indent=1, sort_keys=True))
    else:
        raise SystemExit("usage: duration_measurement_v2.py run|summarize")
