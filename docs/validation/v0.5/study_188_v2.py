"""The #188 study, run again with the specified quantity (approved by the maintainer on
2026-11-03; the approval and this procedure are recorded in issue #188 before the run).

Reason: the first run (`study_188.py`, results `study-188.json` and `study-188.md`, kept
unchanged as a recorded deviation, `study-188-deviation.md`) recorded a finalized box SNR, not
the BLS power at the true period that the specification asks for (docs/plans/v0.5-acceptance.md,
WP7).

Procedure: the same 20 synthetic curves, the same inversion and the same two modes, imported
from `study_188.py` unchanged (development seeds). Recorded per curve and mode: the search
candidate, whether it falls at the true period or P/2 or 2P (within 1 %), whether it passes the
gate, and, as specified, the **BLS power at the exact true period**: the BLS log-likelihood power
of the searched curve (binned as the search bins it) at the true period, over the search's
duration grid, and, to read it against noise, the SDE of the true period in each sector's
stage-1 periodogram (``search.kept_peak_sde``, the search's own grid and normalization). The
curves run in worker processes. The result is written once, to new files; it changes no
reporting category of the calibration. Synthetic data only; no network.

usage: study_188_v2.py <out.json> <out.md> [--workers N]
"""

from __future__ import annotations

import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import study_188 as first  # noqa: E402  (the first run's curves and modes, unchanged)


def _bls_power(searched, period: float, params) -> float:
    from refute.packs.tess.search import _bls, _valid_durations, bin_lightcurve

    binned = bin_lightcurve(searched, params.bin_minutes)
    durations = np.asarray(params.durations_hours, dtype=float) / 24.0
    valid = _valid_durations(durations, period)
    if valid.size == 0:
        return float("nan")
    model = _bls(binned)
    return float(model.power(np.array([period]), valid, objective="likelihood").power[0])


def measure(data, truth, plan) -> dict:
    from refute.packs.tess.detrend import detrend
    from refute.packs.tess.pipeline import global_prewhitening
    from refute.packs.tess.search import kept_peak_sde, search_period
    from refute.packs.tess.types import Candidate

    flat = detrend(data.lc, plan.detrend)
    pw, searched = global_prewhitening(data, plan, flat)
    cand = search_period(searched, plan.search).candidate
    p = truth["period"]
    at_true = None
    if cand is not None:
        at_true = next(
            (f for f in first.ALIASES if abs(cand.period - f * p) / (f * p) <= 0.01), None
        )
    probe = Candidate(p, 0.0, truth["duration"], 0.0, 0.0, 0.0, 0.0, 0.0, 0)
    sde = kept_peak_sde(searched, probe, plan.search)
    return {
        "candidate_period_days": None if cand is None else cand.period,
        "candidate_snr": None if cand is None else cand.snr,
        "gate_passed": bool(cand is not None and cand.snr >= plan.gauntlet.snr.min_snr),
        "at_true_period_factor": at_true,
        "bls_power_at_true_period": _bls_power(searched, p, plan.search),
        "sde_at_true_period_per_sector": sde["per_sector"],
        "sde_at_true_period_max": sde["max"],
        "prewhitening_ran": pw is not None,
        "prewhitening_components": 0 if pw is None else len(pw.components),
    }


def one(task: tuple[str, int]) -> dict:
    from refute.packs.tess.synthetic import make_aux, make_data, make_star

    kind, i = task
    started = time.process_time()
    lc, sectors, truth, seed = first.curve(kind, i)
    inverted = first.invert(lc)
    data = make_data(inverted, sectors, make_star(), aux=make_aux(inverted, seed=0))
    row = {"kind": kind, "index": i, "seed": seed, "true_period_days": truth["period"]}
    for mode, plan in first.plans().items():
        row[mode] = measure(data, truth, plan)
    row["processor_seconds"] = time.process_time() - started
    return row


def main(argv: list[str]) -> int:
    from refute.core.runner import default_workers

    out_json, out_md = Path(argv[0]), Path(argv[1])
    workers = int(argv[argv.index("--workers") + 1]) if "--workers" in argv else default_workers()
    if out_json.exists() or out_md.exists():
        print("refusing to overwrite: the study is written once")
        return 1
    tasks = [(kind, i) for kind in ("eb", "sinusoid") for i in range(10)]
    wall = time.time()
    with ProcessPoolExecutor(max_workers=max(1, min(workers, len(tasks)))) as pool:
        rows = list(pool.map(one, tasks))
    cpu = sum(r["processor_seconds"] for r in rows)
    modes = list(first.plans())
    summary = {}
    for kind in ("eb", "sinusoid"):
        for mode in modes:
            sel = [r[mode] for r in rows if r["kind"] == kind]
            sdes = [
                s["sde_at_true_period_max"] for s in sel if s["sde_at_true_period_max"] is not None
            ]
            summary[f"{kind}/{mode}"] = {
                "curves": len(sel),
                "gate_passed": sum(s["gate_passed"] for s in sel),
                "gate_passed_at_true_period_or_alias": sum(
                    s["gate_passed"] and s["at_true_period_factor"] is not None for s in sel
                ),
                "median_bls_power_at_true_period": float(
                    np.nanmedian([s["bls_power_at_true_period"] for s in sel])
                ),
                "median_sde_at_true_period": float(np.median(sdes)) if sdes else None,
            }
    record = {
        "study": "#188 (v0.5 WP7), run again with the specified quantity",
        "approval": "issue #188 (recorded before this run)",
        "script": "docs/validation/v0.5/study_188_v2.py",
        "first_run": "docs/validation/v0.5/study-188.json (kept unchanged; deviation recorded)",
        "workers": workers,
        "processor_seconds": cpu,
        "wall_seconds": time.time() - wall,
        "summary": summary,
        "curves": rows,
    }
    out_json.write_bytes((json.dumps(record, indent=2, sort_keys=True) + "\n").encode("utf-8"))
    lines = [
        "# #188 study, second run: the BLS power at the true period",
        "",
        "Run again with the quantity the specification asks for (docs/plans/v0.5-acceptance.md, "
        "WP7), approved by the maintainer and recorded in issue #188 before the run. The first "
        "run (`study-188.md`) is kept unchanged as a recorded deviation. Same curves, inversion "
        "and modes. Synthetic; not a false-alarm rate; it changes no reporting category of the "
        "calibration. `method_status: not_validated`.",
        "",
        f"Processor time: {cpu / 3600:.3f} h over {workers} workers. Record: `study-188-2.json`.",
        "",
        "| Group | Curves | Gate passed | ... at the true period or an alias "
        "| Median BLS power at the true period | Median SDE at the true period |",
        "|---|---|---|---|---|---|",
    ]
    for name, s in summary.items():
        sde = (
            "n/a"
            if s["median_sde_at_true_period"] is None
            else f"{s['median_sde_at_true_period']:.1f}"
        )
        lines.append(
            f"| {name} | {s['curves']} | {s['gate_passed']} | "
            f"{s['gate_passed_at_true_period_or_alias']} | "
            f"{s['median_bls_power_at_true_period']:.1f} | {sde} |"
        )
    lines.append("")
    out_md.write_bytes("\n".join(lines).encode("utf-8"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
