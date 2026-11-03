"""The bounded study of #188 (docs/plans/v0.5-acceptance.md, WP7): does detrending a reflected
(inverted) curve leave structure at the true period of a strong own signal, with and without the
global prewhitening?

Specification (fixed in the acceptance documents before this script): 20 synthetic curves with a
strong own signal (10 eclipsing-binary-like, 10 sinusoidal), inverted (each sector reflected about
its median), searched after detrending without and with the prewhitening of the corrections;
recorded per curve and mode: the search candidate, whether it falls at the true period (or P/2 or
2P, within 1 %), whether it passes the gate, and the SNR of a box at the true period. The result
is written once and changes no reporting category of the calibration (fixed in the plan). Caps: at
most 0.5 agent-day and 2 processor-hours. Seeds: the development rule of the acceptance
documents. Synthetic data only; no network.

usage: study_188.py <out.json> <out.md>
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np

from refute.packs.tess.detrend import detrend
from refute.packs.tess.params import TessTestPlan
from refute.packs.tess.pipeline import global_prewhitening
from refute.packs.tess.search import finalize_candidate, search_period
from refute.packs.tess.synthetic import (
    SignalSpec,
    discovery_plan_dict,
    make_aux,
    make_data,
    make_lightcurve,
    make_star,
)
from refute.packs.tess.types import LightCurveData

ALIASES = (1.0, 0.5, 2.0)


def dev_seed(case: str, i: int) -> int:
    text = f"refute-v05-dev:{case}:{i}"
    return int(hashlib.sha256(text.encode()).hexdigest()[:16], 16)


def curve(kind: str, i: int):
    seed = dev_seed(f"study-188-{kind}", i)
    rng = np.random.default_rng(seed)
    if kind == "eb":
        period = float(rng.uniform(1.0, 6.0))
        spec = SignalSpec(
            period=period,
            t0=1325.5 + float(rng.uniform(0, period)),
            depth=0.02,
            duration=0.15,
            ingress_fraction=0.4,
            secondary_depth=0.01,
        )
        lc, sectors = make_lightcurve(spec, seed=seed % (2**31))
        truth = {"period": period, "duration": 0.15}
    else:
        period = float(rng.uniform(0.7, 5.0))
        lc, sectors = make_lightcurve(None, seed=seed % (2**31))
        wave = 0.004 * np.sin(2 * np.pi * (lc.time - 1325.3) / period + float(rng.uniform(0, 6.28)))
        lc = LightCurveData(lc.time, lc.flux + wave, lc.flux_err, lc.sector, lc.year)
        truth = {"period": period, "duration": 0.1}
    return lc, sectors, truth, seed


def invert(lc: LightCurveData) -> LightCurveData:
    flux = lc.flux.copy()
    for s in np.unique(lc.sector):
        sel = lc.sector == s
        flux[sel] = 2.0 * np.median(flux[sel]) - flux[sel]
    return LightCurveData(lc.time, flux, lc.flux_err, lc.sector, lc.year)


def plans() -> dict[str, TessTestPlan]:
    base = discovery_plan_dict()
    with_pw = json.loads(json.dumps(base))
    with_pw.setdefault("gauntlet", {})["corrections"] = {"version": 2, "enabled": True}
    return {
        "without_prewhitening": TessTestPlan.model_validate(base),
        "with_prewhitening": TessTestPlan.model_validate(with_pw),
    }


def measure(data, truth, plan: TessTestPlan) -> dict:
    flat = detrend(data.lc, plan.detrend)
    pw, searched = global_prewhitening(data, plan, flat)
    cand = search_period(searched, plan.search).candidate
    p = truth["period"]
    at_true = None
    if cand is not None:
        at_true = next((f for f in ALIASES if abs(cand.period - f * p) / (f * p) <= 0.01), None)
    box = finalize_candidate(searched, p, truth["duration"], plan.search, 0.0)
    return {
        "candidate_period_days": None if cand is None else cand.period,
        "candidate_snr": None if cand is None else cand.snr,
        "gate_passed": bool(cand is not None and cand.snr >= plan.gauntlet.snr.min_snr),
        "at_true_period_factor": at_true,
        "box_snr_at_true_period": box.snr,
        "prewhitening_ran": pw is not None,
        "prewhitening_components": 0 if pw is None else len(pw.components),
    }


def main(argv: list[str]) -> int:
    out_json, out_md = Path(argv[0]), Path(argv[1])
    if out_json.exists() or out_md.exists():
        print("refusing to overwrite: the study is written once")
        return 1
    started = time.process_time()
    rows = []
    the_plans = plans()
    for kind in ("eb", "sinusoid"):
        for i in range(10):
            lc, sectors, truth, seed = curve(kind, i)
            inverted = invert(lc)
            data = make_data(inverted, sectors, make_star(), aux=make_aux(inverted, seed=0))
            row = {"kind": kind, "index": i, "seed": seed, "true_period_days": truth["period"]}
            for mode, plan in the_plans.items():
                row[mode] = measure(data, truth, plan)
            rows.append(row)
            print(kind, i, {m: row[m]["gate_passed"] for m in the_plans}, flush=True)
    cpu = time.process_time() - started
    summary = {}
    for kind in ("eb", "sinusoid"):
        for mode in the_plans:
            sel = [r[mode] for r in rows if r["kind"] == kind]
            summary[f"{kind}/{mode}"] = {
                "curves": len(sel),
                "gate_passed": sum(r["gate_passed"] for r in sel),
                "gate_passed_at_true_period_or_alias": sum(
                    r["gate_passed"] and r["at_true_period_factor"] is not None for r in sel
                ),
                "median_box_snr_at_true_period": float(
                    np.median([r["box_snr_at_true_period"] for r in sel])
                ),
            }
    record = {
        "study": "#188 (v0.5 WP7), bounded",
        "script": "docs/validation/v0.5/study_188.py",
        "processor_seconds": cpu,
        "summary": summary,
        "curves": rows,
    }
    out_json.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# #188 study: does an inverted curve keep structure at the true period?",
        "",
        "Bounded study of v0.5 WP7 (docs/plans/v0.5-acceptance.md), run once on synthetic curves "
        "(seeds of the development rule). It changes no reporting category of the calibration: "
        "inverted curves and signal-bearing hosts are reported apart by the plan whatever this "
        "shows. Not a false-alarm rate. `method_status: not_validated`.",
        "",
        f"Processor time: {cpu / 3600:.3f} h. Record: `study-188.json`.",
        "",
        "| Group | Curves | Gate passed | ... at the true period or an alias "
        "| Median box SNR at the true period |",
        "|---|---|---|---|---|",
    ]
    for name, s in summary.items():
        lines.append(
            f"| {name} | {s['curves']} | {s['gate_passed']} | "
            f"{s['gate_passed_at_true_period_or_alias']} | "
            f"{s['median_box_snr_at_true_period']:.1f} |"
        )
    lines.append("")
    out_md.write_text("\n".join(lines), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
