"""v0.5.3 stage A, items (c1) and (c2): the background audit and T2a's bounds (#217;
`docs/plans/v0.5.3-stageA-design.md`, section (c)). **A what-if on development data; it decides
nothing.** ``method_status: not_validated``. No change to ``src/``, to any rule or to T2a's
fingerprint; v0.5.2's records are read through ``driver.Run(...).assemble()`` only.

**What runs.** The 51 T2a development injections that version 4 B loses against v0.4 (the v0.5.2
diagnosis), each rebuilt only as far as its light curves (the sealed host's cached files and the
injection, ``forecast_t2a_diagnosis.one``'s first steps: no search and no battery), with the final
candidate, the chosen sectors and the A0 traces taken from the v0.5.2 diagnosis's record.

**(c1) The background audit** (measurements, not bounds), on the A0-chosen sectors, in the
battery's normalization (``SAP_BKG`` and ``SAP_FLUX`` over each sector's ``SAP_FLUX`` median, the
adapter's): the per-point scatter of the background series (the median absolute deviation of first
differences over 0.6745 and the square root of 2: it may still contain variability), its white box
error at the candidate's in-transit and out-of-transit cadences, A0's error on the background rise
and on the SAP depth (the traces), their ratios, and the out-of-transit variability of the
background (its standard deviation over the per-point scatter); the necessary condition of the
3-error rule alone, error over SAP depth at most 0.8 / (3 + Φ^-1(0.95)) = 0.17223.

**(c2) T2a's bounds.** Kept retention's upper bound: every blocker of these losses is recoverable
under the design's rules (warnings by a warning FAIL; `odd_even`, whose white-noise error below is a
plug-in and not a bound; refusals; `period_alias`), so it is counted, with the stratum above 20
bounded both ways and the forecast's stratified hypergeometric upper end. **Conditional scenarios**
(white noise at the measured per-point scatter, which can understate or overstate the true error;
not bounds): `odd_even`'s joint-information error with the injected template known exactly (odd,
even and one level per sector), its probability at the battery's alternative (the final
candidate's depth) against 0.95; the sinusoid's GLS residual box error with the tested harmonics,
``small`` against 0.95; the background's white box error against 0.17223 of the SAP depth.

Usage: ``run`` through ``scripts/launch_affinity.ps1``, then ``summarize`` (``t2a-bounds.json``).
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
sys.path.insert(0, str(HERE))
import ledger_a  # noqa: E402,I001  (before budgeted: it points the ledger at stage A's)
import a0_refusals as ar  # noqa: E402
import budgeted  # noqa: E402
import forecast_t2a as t  # noqa: E402
import forecast_t2a_diagnosis as td  # noqa: E402

PART = "c1_background_audit"
OUT = ledger_a.ROOT / ".cache/v053/stageA/t2a-bounds"
WORKERS = 12
PIN = tuple(range(8, 32, 2))
MAX_SHARD_SECONDS = 1200.0
KEPT = ("SURVIVED", "WEAKENED")
NECESSARY = 0.8 / (3.0 + 1.6448536269514722)
REQUIRED = 0.95


def losses() -> dict:
    old = ar.t2a_old()
    return {
        k: r
        for k, r in old.items()
        if r.get("status") == "OK"
        and r["v04"]["stage_verdict"] in KEPT
        and r["v4"]["stage_verdict"] not in KEPT
    }


def schedule() -> list:
    rows = [(f"c-{k}-{s:02d}", {"key": k, "slot": s}) for (k, s) in sorted(losses())]
    if len(rows) != 51:
        raise SystemExit(f"not the 51 T2a losses: {len(rows)}")
    return rows


def _rebuild(key: str, slot: int):
    """``forecast_t2a_diagnosis.one``'s first steps: the injected data and the injection."""
    from refute.packs.tess.adapter import TessAdapter
    from refute.packs.tess.calib05 import c2
    from refute.packs.tess.discover import injection as inj

    target = t.targets()[key]
    raw, staged, _ = t._plans()
    randomness = json.loads((t.V04_STEP / "runs" / "r_inj.json").read_text("utf-8"))["beacon"][
        "randomness"
    ]
    catalog = ((t.V04_STEP / "eb_catalog.csv").as_posix(),)
    scan_path = (t.V04_STEP / "eb_catalog_scan.json").as_posix()
    tasks = c2.tasks_for(target, raw, t.CACHE, randomness, catalog, scan_path)
    task = next(x for x in tasks if x.kind == "injection" and x.slot == slot)
    base = TessAdapter().load(target, staged, t.CACHE)
    star = base.star
    drawn = inj.draw_injections(
        task.seed,
        task.k,
        inj.first_time(base),
        star.radius_rsun if star else None,
        star.logg_cgs if star else None,
    )[task.slot]
    return inj.inject(base, drawn), drawn, base


def _scatter(values: np.ndarray) -> float:
    d = np.diff(values[np.isfinite(values)])
    return (
        float(np.median(np.abs(d - np.median(d))) / 0.6745 / math.sqrt(2.0)) if d.size else math.nan
    )


def _in_out(time_, cand, ev):
    """The in-transit cadences and the baseline band of the candidate's events (A0's box)."""
    dt = np.abs(
        np.mod(time_ - cand["t0"] + 0.5 * cand["period"], cand["period"]) - 0.5 * cand["period"]
    )
    half = cand["duration"] / 2.0
    inner = half + ev.baseline_gap_durations * cand["duration"]
    outer = half + ev.baseline_outer_durations * cand["duration"]
    return dt <= half, (dt > inner) & (dt <= outer)


def _gram_white(columns, sigma) -> np.ndarray:
    w = 1.0 / np.square(sigma)
    x = np.column_stack(columns)
    return (x.T * w) @ x


def one(arg: dict, rec: dict) -> None:
    from refute.packs.tess.battery_v52 import HARMONICS
    from refute.packs.tess.discover.injection import INGRESS_FRACTION
    from refute.packs.tess.power import gaussian_probability
    from refute.packs.tess.synthetic import trapezoid

    old = losses()[(arg["key"], arg["slot"])]
    cand = old["final_candidate"]
    data, drawn, host = _rebuild(arg["key"], arg["slot"])
    _, _, plans = t._plans()
    p4 = plans["v4C"]
    ev = p4.gauntlet.events
    sel = (
        next(
            (
                ((v.get("final") or {}).get("metrics") or {}).get("sector_selection")
                for v in old["v4"]["tests"].values()
                if ((v.get("final") or {}).get("metrics") or {}).get("sector_selection")
            ),
            None,
        )
        or {}
    )
    chosen = set(sel.get("chosen") or [])
    rec["chosen"] = sorted(chosen)
    # (c1) the background audit on the chosen sectors
    sectors = [a for a in (data.aux.sectors if data.aux else []) if a.sector in chosen]
    audit = []
    for a in sectors:
        bkg = a.sap_bkg  # already over the sector's original SAP median (the adapter)
        ins, base = _in_out(a.time, cand, ev)
        s = _scatter(bkg)
        n_in, n_out = int(np.isfinite(bkg[ins]).sum()), int(np.isfinite(bkg[base]).sum())
        audit.append(
            {
                "sector": int(a.sector),
                "scatter": s,
                "n_in": n_in,
                "n_baseline": n_out,
                "variability_over_scatter": float(np.nanstd(bkg[~ins]) / s) if s else None,
            }
        )
    rec["background_sectors"] = audit
    final = old["v4"]["tests"].get("systematics", {}).get("final") or {}
    block = (final.get("sensitivity") or {}).get("background") or {}
    rec["background_cohort"] = bool(
        final.get("status") == "INCONCLUSIVE" and block.get("detectable") is False
    )
    traces = {
        c.get("series"): c
        for c in old["v4"].get("a0_depth_calls", [])
        if c.get("caller") == "check_systematics"
    }
    sap_depth = ((traces.get("sap") or {}).get("result") or {}).get("mean")
    sap_err = ((traces.get("sap") or {}).get("result") or {}).get("error")
    bkg_err = ((traces.get("background") or {}).get("result") or {}).get("error")
    inv = sum(
        1.0 / (x["scatter"] ** 2 * (1.0 / x["n_in"] + 1.0 / x["n_baseline"]))
        for x in audit
        if x["scatter"] and x["n_in"] and x["n_baseline"]
    )
    white = 1.0 / math.sqrt(inv) if inv > 0 else None
    rec["background"] = {
        "sap_depth": sap_depth,
        "sap_depth_a0_error": sap_err,
        "background_a0_error": bkg_err,
        "background_white_box_error": white,
        "a0_over_white": bkg_err / white if bkg_err and white else None,
        "a0_over_sector_scatter": [
            bkg_err / x["scatter"] for x in audit if bkg_err and x["scatter"]
        ],
        "background_a0_over_sap_error": bkg_err / sap_err if bkg_err and sap_err else None,
        "white_over_sap_depth": white / sap_depth if white and sap_depth else None,
        "white_meets_necessary": (white / sap_depth <= NECESSARY) if white and sap_depth else None,
    }
    # (c2) conditional scenarios on the light curve (white noise at the measured scatter)
    lc = data.lc
    flux = lc.flux.copy()
    sig = np.empty(flux.size)
    norm = np.empty(flux.size)
    for s in np.unique(lc.sector):
        m = lc.sector == s
        norm[m] = float(np.median(flux[m]))  # held fixed (an oracle assumption)
        flux[m] /= norm[m]
        sig[m] = _scatter(flux[m])
    # inject's response: host_flux * (1 - depth * template), so d/d(depth) = -host * template
    unit = trapezoid(
        lc.time, drawn.period_days, drawn.t0_btjd, 1.0, drawn.duration_days, INGRESS_FRACTION
    )
    unit = unit * host.lc.flux / norm
    epoch = np.round((lc.time - drawn.t0_btjd) / drawn.period_days).astype(int)
    levels = [(lc.sector == s).astype(float) for s in np.unique(lc.sector)]
    cols = [np.where(epoch % 2 != 0, -unit, 0.0), np.where(epoch % 2 == 0, -unit, 0.0), *levels]
    f = _gram_white(cols, sig)
    c = np.zeros(len(cols))
    c[0], c[1] = 1.0, -1.0
    s_oe = float(math.sqrt(c @ np.linalg.solve(f, c)))
    alt = p4.stronger.odd_even_alternative_depth_fraction * cand["depth"]
    rec["odd_even_white"] = {
        "sigma": s_oe,
        "alternative": alt,
        "probability": gaussian_probability(alt, s_oe, p4.gauntlet.odd_even.max_sigma),
        "not_a_bound": True,
    }
    domain = p4.v051.sinusoid_harmonic_max_period_days
    tested = [cand["period"] * fac for _, fac in HARMONICS if cand["period"] * fac < domain]
    ins, _ = _in_out(lc.time, cand, ev)
    zc = [-ins.astype(float), *levels]
    for period in tested:
        ph = 2.0 * math.pi * lc.time / period
        zc += [np.cos(ph), np.sin(ph)]
    s_box = float(math.sqrt(np.linalg.inv(_gram_white(zc, sig))[0, 0]))
    small = 0.5 * math.erfc(-((0.5 * cand["depth"] / s_box) - 3.0) / math.sqrt(2.0))
    rec["sinusoid_white"] = {
        "sigma_box": s_box,
        "small": small,
        "tested_periods": tested,
        "not_a_bound": True,
    }
    rec["injection"] = drawn.to_dict()


def shard(arg: dict) -> bytes:
    started = time.process_time()
    rec: dict = dict(arg)
    try:
        one(arg, rec)
        rec["status"] = "OK"
    except Exception as exc:  # noqa: BLE001 - recorded, never dropped
        rec["status"], rec["reason"] = "ERROR", repr(exc)
    rec["cpu_seconds"] = time.process_time() - started
    return json.dumps(rec, sort_keys=True, default=str).encode() + b"\n"


def fingerprint() -> str:
    from refute.core.codehash import compute_code_hash

    h = hashlib.sha256(compute_code_hash().sha256.encode())
    for path in (
        Path(__file__),
        HERE / "ledger_a.py",
        HERE / "a0_refusals.py",
        td.HERE / "forecast_t2a_diagnosis.py",
        td.HERE / "forecast_t2a.py",
        td.HERE / "forecast_v4.py",
        td.HERE / "t2a-fetch.json",
        td.HERE / "budgeted.py",
        td.HERE / "driver.py",
    ):
        h.update(hashlib.sha256(path.read_bytes()).digest())
    return h.hexdigest()[:16]


def run() -> None:
    before = ledger_a.v052_ledger_sha256()
    try:
        ledger_a.check_caps(reserve_days=0.3, reserve_tokens=0)
        ledger_a.declare()
        fp = fingerprint()
        rows = schedule()
        cap = ledger_a.hard_cap(PART, WORKERS, MAX_SHARD_SECONDS)
        print(len(rows), "injections; hard cap", round(cap, 2), "CPU-h", flush=True)
        state = budgeted.execute(
            ledger_a.SECTION,
            PART,
            OUT / fp,
            shard,
            rows,
            fp,
            WORKERS,
            pin=PIN,
            max_shard_seconds=MAX_SHARD_SECONDS,
            hard_cap_hours=cap,
        )
        print(state, flush=True)
    finally:
        if ledger_a.v052_ledger_sha256() != before:
            raise SystemExit("the v0.5.2 ledger changed: refused")
    if state != "complete":
        raise SystemExit(state)


def summarize() -> None:
    fp = fingerprint()
    rows = schedule()
    data = budgeted.assembled(
        ledger_a.SECTION,
        PART,
        OUT / fp,
        shard,
        rows,
        fp,
        WORKERS,
        pin=PIN,
        max_shard_seconds=MAX_SHARD_SECONDS,
    )
    recs = [json.loads(x) for x in data.decode().splitlines() if x.strip()]
    ok = [r for r in recs if r["status"] == "OK"]
    cohort = [r for r in ok if r["background_cohort"]]
    bg = [r["background"] for r in cohort]
    others = [
        r["background"]
        for r in ok
        if not r["background_cohort"] and r["background"]["background_a0_error"]
    ]

    def med(xs):
        xs = [x for x in xs if x is not None]
        return float(np.median(xs)) if xs else None

    pop = t.population()
    counts = {s: sum(r["stratum"] == s for r in pop) for s in t.STRATA}
    n = len(pop)
    out = {
        "label": "T2a's background audit and bounds; a what-if, decides nothing (#217, (c1), (c2))",
        "method_status": "not_validated",
        "fingerprint": fp,
        "injections": len(recs),
        "errors": [
            f"{r['key']}/{r['slot']}: {r.get('reason')}" for r in recs if r["status"] != "OK"
        ],
        "background_audit": {
            "cohort": "the losses whose systematics INCONCLUSIVE carries an undetectable "
            "background block (the 23 background-sensitivity losses); others reported apart",
            "cohort_size": len(cohort),
            "others_with_a_background_measurement": len(others),
            "median_a0_over_sector_scatter": med(
                [x for b in bg for x in b["a0_over_sector_scatter"]]
            ),
            "median_a0_over_white": med([b["a0_over_white"] for b in bg]),
            "median_background_a0_over_sap_error": med(
                [b["background_a0_over_sap_error"] for b in bg]
            ),
            "median_white_over_sap_depth": med([b["white_over_sap_depth"] for b in bg]),
            "white_meets_necessary": sum(bool(b["white_meets_necessary"]) for b in bg),
            "necessary_condition": NECESSARY,
            "median_variability_over_scatter": med(
                [x["variability_over_scatter"] for r in cohort for x in r["background_sectors"]]
            ),
            "not_a_bound": True,
            "qualification": (
                "measurements: the scatter may still contain variability, and the white box error "
                "is one estimator's; the 0.17223 condition is necessary for the 3-error rule "
                "alone, not the compound rule with an uncertain SAP depth"
            ),
        },
        "kept_upper_bound": {
            "rule": "every blocker of the 51 losses is recoverable (warnings, plug-in odd_even, "
            "refusals, period_alias); the stratum above 20 bounded both ways",
            "measured_strata": 1.0,
            "above_20_all_lost": (counts["2_to_4"] + counts["5_to_20"]) / n,
            "above_20_all_kept": 1.0,
        },
        "conditional_white_noise": {
            "not_a_bound": True,
            "qualification": (
                "white noise at the measured per-point scatter (it can understate or overstate "
                "the true error), the per-sector normalizer held fixed; the sinusoid's is the "
                "joint GLS oracle scenario, not box_after_model's masked-fit error nor the "
                "compound test's power"
            ),
            "odd_even_probability_reaches_0.95": sum(
                r["odd_even_white"]["probability"] >= REQUIRED for r in ok
            ),
            "sinusoid_small_reaches_0.95": sum(
                r["sinusoid_white"]["small"] >= REQUIRED for r in ok
            ),
            "of": len(ok),
        },
        "per_injection": ok,
    }
    (HERE / "t2a-bounds.json").write_text(
        json.dumps(out, indent=1, sort_keys=True, default=str) + "\n", "utf-8"
    )
    print(json.dumps({k: v for k, v in out.items() if k != "per_injection"}, indent=1))


if __name__ == "__main__":
    {"run": run, "summarize": summarize}[sys.argv[1]]()
