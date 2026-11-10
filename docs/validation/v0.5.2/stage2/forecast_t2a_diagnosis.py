"""v0.5.2 stage 2: the diagnosis of T2a's losses with battery version 4 (the maintainer's decision
of 2026-11-10, third set, item 1; #216). **A diagnosis on development data; it decides nothing.**
``method_status: not_validated``. No change to ``src/``, to any rule, or to T2a's fingerprint:
``forecast_t2a.py``, ``budgeted.py`` and ``driver.py`` are imported, never edited. Codex reviewed
this design before the run in three rounds, each ``REFUTED``; every finding was applied, round 3's
as Codex wrote them (the tie-break: the more conservative option); the consensus record keeps the
answers.

**What runs.** The same 80 development injections as ``forecast_t2a.run`` (its ``shards``: the
strata of 2 to 4 and 5 to 20 light-curve files), rebuilt the same way (``c2.tasks_for``, the v0.4
R_inj seeds, the candidate generated once). Two batteries attack the shared candidate at stage 1:
the v0.4 battery, checked against its v0.4 record by ``c2.compat_problems`` as in the forecast,
and version 4 with the selector treated as certified (the forecast's C; it equals B at most 20
sectors, which every injection here has). Version 3 and version 4 A are not run again.

**What is kept, for every injection.** Each test of version 4 at three points: as the gauntlet
returned it, after the sensitivity rule, and final (status, severity, message, metrics,
thresholds, coverage, sensitivity blocks; ``aperture_depth`` is deferred to stage 2, so its
gauntlet and sensitivity records are the evidence). The sector selection; the inputs (each
sector's light-curve file and SHA-256, its cadences and its finite PDCSAP, SAP and background
values, CROWDSAP and momentum dumps, and per product the transits of the final ephemeris with data
and with enough finite in-transit cadences; the pixel files, none for an injection); and a trace
of every call of ``a0_v4.a0_depth`` (the A0 group depth of ``systematics`` and ``aperture_depth``):
the caller, the series, the candidate it measured, the finite points, the result (depth, error,
and per event the epoch, depth, weight and sector, losslessly) or, on a None, why, and the
injection's expected response (below). The reason of a None comes from ``_why_none``, a
step-by-step copy of ``a0_v4.a0_depth`` run only on a None, which must reach a None as well; a
disagreement or an error of the instrumentation is recorded apart, never replaces the battery's
result, and quarantines the injection. The collections are attached to the record before the
battery runs, so an error keeps them.

**The injection's expected response.** For each measured event, the injected trapezoid averaged
over the candidate's box at that event (``inject``'s model); the expected group depth is the
measurement's own weighted sum of it: in the normalized PDCSAP series the box average itself, in
the raw SAP series the box average times the sector's CROWDSAP times the sector's median SAP flux
(``inject`` dilutes the SAP dip by CROWDSAP), and zero in the SAP-minus-expected and background
series. **An audit warning**, attached to every blocker whatever its status: in the PDCSAP or SAP
series, the expected depth positive and more than three of A0's errors from zero, and the measured
depth below half of it minus three errors or above twice it plus three errors. The expected
response is a box average of the model on a uniform grid, not the measurement operator on the
observed cadences, and is not validated: a warning is reported as unresolved and never classifies
a blocker.

**The classification, frozen before the run** (``classify``). A loss is v0.4 kept and version 4
not kept. Quarantined first, never classified: an error, a v0.4 record that does not reproduce, a
candidate or a test status or a stage verdict differing from the forecast's version 4 B record, an
instrumentation error or a copy disagreement. Each blocker of a classified loss (a decisive test,
not deferred, FAIL or INCONCLUSIVE) is put in one class, with its evidence:
(c) a code defect, established or suspected, first: "no transit measured" without the A0 None or
    the missing common event that would explain it; common events whose recomputed expected SAP
    depth (``battery_v51_diff.expected_sap_depth``'s formula) is positive, yet none was measured;
(a) missing data: a product without finite values (exact counts), no transit with enough
    in-transit cadences, CROWDSAP absent, fewer transits than a sub-check's minimum; the product
    and the sectors are named;
(b) a lack of power with the data present: the declared sensitivity not reached (the blocks'
    effect, alternative, unit, probability and required probability, and A0's error against the
    declared minimum effect), an event error not measurable, a measured depth not positive, the
    common events' recomputed expected SAP depth not positive;
(d) a refusal by a rule of the battery with the data present: the grid of 2 to 4 contributing
    sectors, A0's event metadata or group variance refused, the comb measuring no event, no event
    common to the two A0 measurements, the selection refused;
(e) a FAIL (not an INCONCLUSIVE; reported, not classified further);
(u) an INCONCLUSIVE whose message no rule above recognizes, read by hand and reported as such.
The INCONCLUSIVE class label of ``systematics`` is compared with the label its identified causes
would have under the battery's priority (``refute.core.inconclusive.PRIORITY``); a disagreement is
a labelling defect, reported apart (it does not cause a loss).

**The stops, frozen before the run, binding.** The maintainer's "a code defect (c) that explains a
large part of the losses" is read as (c) blockers in at least 10 % of the forecast's 51 losses (6),
or any instrumentation quarantine. (1) The preflight (80 injections in the two measured strata; the
forecast's 51 losses, 48 with ``systematics`` INCONCLUSIVE) runs before any dispatch and refuses.
(2) Two smoke injections (the first forecast loss with ``systematics`` INCONCLUSIVE of each
stratum) run as their own ledger part under its cap; their acceptance (no quarantine, no (c)) is
written with this script's fingerprint, and ``run`` refuses without it. (3) During the run each
worker classifies its own injection: an instrumentation quarantine or a failure of the worker's
own classification writes a binding sentinel at once, and a causal (c) blocker of a loss writes a
flag; with the sentinel present, or once the flags reach 6, every later shard returns ``STOPPED``
without computing. (4) ``summarize`` writes ``"stop": true`` on any of these, and nothing else
proceeds before the maintainer.

Usage: ``prepare``; ``smoke`` and ``run`` through ``scripts/launch_affinity.ps1``; ``summarize``
(``forecast-t2a-diagnosis.json``).
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(HERE))
import budgeted  # noqa: E402
import forecast_t2a as t  # noqa: E402

SECTION, PART, SMOKE_PART = t.SECTION, "forecast_t2a_diagnosis", "forecast_t2a_diagnosis_smoke"
ALLOCATION_HOURS, SMOKE_ALLOCATION_HOURS = 5.0, 1.0
FORECAST_CAP_HOURS = 25.0  # the maintainer, 2026-11-10: the whole forecast, this diagnosis included
DRIVER_OVERSHOOT = 1.10  # the driver may pass its cap by up to 10 %: the cap is reserved below it
OUT = ROOT / ".cache/v052/s2/forecast-t2a-diagnosis"
DECISION = (
    "The maintainer, 2026-11-10 (third set, #216), item 1: rerun T2a's 80 development injections "
    "keeping the messages and input data of each INCONCLUSIVE (and of aperture_depth), within "
    "the forecast's 25 CPU-h; no change to src/, to the rules or to T2a's fingerprint."
)
SYSTEMATICS_SERIES = {0: "pdcsap", 1: "sap_minus_expected", 3: "background", 4: "sap"}
PRODUCT = {"pdcsap": "PDCSAP_FLUX", "sap_minus_expected": "SAP_FLUX and PDCSAP_FLUX",
           "background": "SAP_BKG", "sap": "SAP_FLUX"}  # fmt: skip
SUB_CHECK_SERIES = {"sap_vs_pdcsap": ("pdcsap", "sap_minus_expected"),
                    "background": ("background", "sap")}  # fmt: skip
ERROR_SERIES = {"sap_vs_pdcsap": "sap_minus_expected", "background": "background"}
ARRAY_LIMIT = 64
STOP_SHARE = 0.10
EXPECTED_SHARDS, EXPECTED_LOSSES, EXPECTED_SYSTEMATICS = 80, 51, 48  # forecast-t2a.json, B
STOP_FLAGS = math.ceil(STOP_SHARE * EXPECTED_LOSSES)
Z_PRESENT = 3.0
BOX_GRID = 201


# --- json -----------------------------------------------------------------------------------


def _safe(x):
    """JSON-safe, with long arrays summarized and non-finite numbers as strings (never used on
    the lossless event lists of the trace)."""
    if isinstance(x, dict):
        return {str(k): _safe(v) for k, v in x.items()}
    if isinstance(x, np.ndarray):
        if x.size > ARRAY_LIMIT:
            finite = x[np.isfinite(x)] if x.dtype.kind == "f" else x
            return {"array_size": int(x.size), "finite": int(finite.size)}
        x = x.tolist()
    if isinstance(x, (list, tuple, set)):
        x = list(x)
        if len(x) > ARRAY_LIMIT:
            return {"list_size": len(x)}
        return [_safe(v) for v in x]
    if isinstance(x, np.generic):
        x = x.item()
    if isinstance(x, float) and not math.isfinite(x):
        return repr(x)
    if hasattr(x, "value") and not isinstance(x, (int, float, str, bool)):
        return x.value  # an enum
    if x is None or isinstance(x, (bool, int, float, str)):
        return x
    return repr(x)


def _test(r) -> dict:
    return _safe(
        {
            "status": r.status,
            "severity": r.severity,
            "message": r.message,
            "metrics": r.metrics,
            "thresholds": getattr(r, "thresholds", None),
            "coverage": r.coverage,
            "coverage_unit": getattr(r, "coverage_unit", None),
            "sensitivity": getattr(r, "sensitivity", None),
        }
    )


# --- the trace of A0's group depth ------------------------------------------------------------


def _why_none(time_, values, sector, candidate, plan, seed, exclude_phase_half=False) -> str:
    """Why ``a0_v4.a0_depth`` returned None: its steps, in its order (``a0_v4.py``)."""
    from refute.packs.tess import a0
    from refute.packs.tess import a0_v4 as v4
    from refute.packs.tess import detrend_fast as df
    from refute.packs.tess.battery_v51_diff import MIN_MEASURABLE_ERROR
    from refute.packs.tess.battery_v52 import GRID_SECTORS
    from refute.packs.tess.events import per_event_depths, per_point_sigma, transit_mask

    good = np.isfinite(time_) & np.isfinite(values)
    time_, values, sector = time_[good], values[good], sector[good]
    if time_.size < 10:
        return f"fewer than 10 finite cadences ({int(time_.size)})"
    order = np.argsort(time_, kind="stable")
    time_, values, sector = time_[order], values[order], sector[order]
    half = plan.detrend.transit_mask_half_width_durations * candidate.duration
    mask = transit_mask(time_, candidate.period, candidate.t0, half)
    detrender = df.AdditiveDetrender(time_, values, sector, plan.detrend, mask)
    series = detrender.flat()
    ok = np.isfinite(detrender.residuals())
    sigma = per_point_sigma(series, mask[ok])
    cadence = plan.data.exptime_seconds / 86400.0
    ev = plan.gauntlet.events
    events = per_event_depths(
        series, candidate.period, candidate.t0, candidate.duration, cadence, ev, 0.0, sigma
    )
    if len(events) == 0:
        return "no event with enough in-transit coverage in this series"
    measure = v4.comb_measure(detrender.flat, time_, series, candidate.duration, half, ev, cadence)
    measured, windows, _ = v4.empirical_events(
        series, candidate, events, ev, cadence, measure, exclude_phase_half
    )
    if len(measured) == 0:
        return f"the comb measured none of the {len(events)} event(s)"
    expected_in = candidate.duration / cadence
    metas = []
    for centre, n_in in zip(measured.centers.tolist(), measured.n_in.tolist(), strict=True):
        meta = a0.event_meta(
            series.time, series.sector, centre, n_in / expected_in, ev.min_coverage
        )
        if meta is None:
            return "an event's metadata was refused (a0.event_meta)"
        metas.append(meta)
    used = sorted({int(m.sector) for m in metas})
    if len(used) not in GRID_SECTORS:
        return f"{len(used)} contributing sector(s) {used}: outside the grid of 2 to 4"
    errors = measured.errors
    if not np.all(np.isfinite(errors) & (errors > MIN_MEASURABLE_ERROR)):
        return "an event error is not measurable"
    weights = 1.0 / np.square(errors)
    weights = weights / np.sum(weights)
    pooled = {s: a0.shortcut(windows, s, seed + s) for s in {m.sector for m in metas}}
    h = a0.half_width(candidate.duration, ev.baseline_outer_durations)
    if a0.group_variance(weights, errors.tolist(), metas, windows, h, pooled) is None:
        return "the group variance was refused (a0.group_variance)"
    return "COPY DISAGREES: every step succeeded"


def _num(x) -> float | None:
    x = float(x)
    return x if math.isfinite(x) else None


def _tracer(original, calls: list):
    def traced(time_, values, sector, candidate, plan, seed, exclude_phase_half=False):
        got = original(time_, values, sector, candidate, plan, seed, exclude_phase_half)
        row: dict = {
            "caller": sys._getframe(1).f_code.co_name,
            "seed": int(seed),
            "candidate": {
                "period": float(candidate.period),
                "t0": float(candidate.t0),
                "duration": float(candidate.duration),
            },  # fmt: skip
        }
        try:
            good = np.isfinite(time_) & np.isfinite(values)
            row["finite_points"] = int(good.sum())
            row["sectors"] = sorted({int(s) for s in np.unique(sector)})
            if got is None:
                row["result"] = None
                row["why"] = _why_none(
                    time_, values, sector, candidate, plan, seed, exclude_phase_half
                )
            else:
                row["result"] = {
                    "mean": _num(got.mean), "error": _num(got.error),
                    "n_events": int(got.n_events),
                    "epochs": [int(e) for e in got.epochs],
                    "depths": [_num(d) for d in got.depths],
                    "weights": [_num(w) for w in got.weights],
                    "event_sectors": [int(s) for s in got.sectors],
                }  # fmt: skip
        except Exception as exc:  # noqa: BLE001 - recorded apart; the battery's result stands
            row["instrumentation_error"] = repr(exc)
        calls.append(row)
        return got

    return traced


# --- the injection's expected response ------------------------------------------------------


def _expected(call: dict, drawn, scale: dict[int, float]) -> float | None:
    """The measurement's weighted sum of the injected trapezoid averaged over the candidate's box
    at each measured event, times the series' per-sector scale."""
    from refute.packs.tess.discover.injection import INGRESS_FRACTION
    from refute.packs.tess.synthetic import trapezoid

    res = call.get("result")
    if not res or not res["weights"] or any(w is None for w in res["weights"]):
        return None
    cand = call["candidate"]
    total = 0.0
    for epoch, weight, sector in zip(res["epochs"], res["weights"], res["event_sectors"],
                                     strict=True):  # fmt: skip
        centre = cand["t0"] + epoch * cand["period"]
        grid = np.linspace(centre - cand["duration"] / 2, centre + cand["duration"] / 2, BOX_GRID)
        box = float(np.mean(trapezoid(grid, drawn.period_days, drawn.t0_btjd, drawn.depth,
                                      drawn.duration_days, INGRESS_FRACTION)))  # fmt: skip
        if sector not in scale:
            return None
        total += weight * box * scale[sector]
    return total


def _scales(data) -> dict[str, dict[int, float]]:
    """Per series, each sector's factor between the injected box average and the series' depth:
    1 in the normalized PDCSAP series, CROWDSAP times the median SAP flux in the raw SAP series."""
    pdc, sap = {}, {}
    for a in data.aux.sectors if data.aux else []:
        pdc[int(a.sector)] = 1.0
        finite = np.isfinite(a.sap_flux)
        if a.crowdsap is not None and finite.any():
            sap[int(a.sector)] = float(a.crowdsap) * float(np.median(a.sap_flux[finite]))
    return {"pdcsap": pdc, "sap": sap}


def _anomaly(call: dict | None) -> str | None:
    """The audit (a warning, never a class: the expected response is a box average of the model
    on a uniform grid, not the measurement operator on the observed cadences, so it is not
    validated): the measured depth below half the injection's expected depth minus three errors,
    or above twice it plus three errors, while the expected depth is positive and more than three
    errors from zero (Codex, round 3)."""
    if call is None or not call.get("result") or call.get("expected_mean") is None:
        return None
    mean, error = call["result"]["mean"], call["result"]["error"]
    expected = call["expected_mean"]
    if mean is None or error is None or not error > 0:
        return None
    if not expected > Z_PRESENT * error:
        return None
    if mean < 0.5 * expected - Z_PRESENT * error or mean > 2.0 * expected + Z_PRESENT * error:
        return (f"{call.get('series')}: measured {mean:.4g} against the injection's expected "
                f"{expected:.4g} (A0 error {error:.2g})")  # fmt: skip
    return None


# --- one injection ----------------------------------------------------------------------------


def _inputs(data, final, plan) -> dict:
    """Each sector's file, its values per product and, per product, the transits of the final
    ephemeris with data and with enough finite in-transit cadences."""
    from refute.packs.tess.battery import transit_centers_with_data

    files = {int(s.sector): s.filename for s in data.sectors}
    sha = {f.get("name"): f.get("sha256") for f in (data.manifest or {}).get("files", [])}
    cadence = plan.data.exptime_seconds / 86400.0
    need = plan.gauntlet.events.min_coverage * final.duration / cadence
    aux = data.aux
    sectors = []
    for a in aux.sectors if aux else []:
        centers = transit_centers_with_data(a.time, final)
        row = {
            "sector": int(a.sector),
            "file": files.get(int(a.sector)),
            "file_sha256": sha.get(files.get(int(a.sector))),
            "cadences": int(a.time.size),
            "crowdsap": a.crowdsap,
            "momentum_dumps": int(a.dump_times.size),
            "transits_with_data": int(centers.size),
        }
        for name, values in (("pdcsap", a.pdcsap_flux), ("sap", a.sap_flux),
                             ("background", a.sap_bkg)):  # fmt: skip
            finite = np.isfinite(values) & np.isfinite(a.time)
            covered = sum(
                int(np.sum(finite & (np.abs(a.time - c) <= final.duration / 2))) >= need
                for c in centers
            )
            row[f"finite_{name}"] = int(finite.sum())
            row[f"transits_covered_{name}"] = int(covered)
        sectors.append(row)
    return _safe(
        {
            "light_curve_sectors": sorted(files),
            "aux_sectors": sectors,
            "pixel_sectors": sorted(int(p.sector) for p in (aux.pixels if aux else [])),
            "light_curve_cadences": int(data.lc.time.size),
            "in_transit_cadences_needed": need,
        }
    )


def _battery(data, cand, plan, catalogs, scan, pw, v4: dict) -> tuple[dict, object]:
    """``paired._outcome`` at stage 1, every test kept at three points and A0's trace, written
    into ``v4`` as they are captured (an error keeps what was captured)."""
    from refute.core import sensitivity
    from refute.packs.tess import a0_v4, pipeline
    from refute.packs.tess.discover import paired

    calls: list = v4["a0_depth_calls"]
    stages: dict[str, list] = {"gauntlet": [], "sensitivity": [], "final": []}
    gauntlets: list = []
    saved = (paired.attack_candidate, a0_v4.a0_depth, pipeline.classify_v051,
             sensitivity.enforce_sensitivity)  # fmt: skip

    def spy_attack(*args, **kwargs):
        g = saved[0](*args, **kwargs)
        gauntlets.append(g)
        stages["gauntlet"] = list(g.tests)
        return g

    def spy_classify(*args, **kwargs):
        out = saved[2](*args, **kwargs)
        stages["final"] = list(out)
        return out

    def spy_sensitivity(*args, **kwargs):
        out = saved[3](*args, **kwargs)
        stages["sensitivity"] = list(out)
        return out

    paired.attack_candidate = spy_attack
    a0_v4.a0_depth = _tracer(saved[1], calls)
    pipeline.classify_v051 = spy_classify
    sensitivity.enforce_sensitivity = spy_sensitivity
    try:
        out = paired._outcome(data, cand, plan, 1, catalogs, scan, pw)
    finally:
        (paired.attack_candidate, a0_v4.a0_depth, pipeline.classify_v051,
         sensitivity.enforce_sensitivity) = saved  # fmt: skip
        if not stages["final"]:
            stages["final"] = stages["sensitivity"]
        tests: dict = {}
        for stage, results in stages.items():
            for r in results:
                tests.setdefault(r.name, {})[stage] = _test(r)
        v4["tests"] = tests
    return out, gauntlets[0].candidate


def one(row: dict, rec: dict) -> None:
    """Fill ``rec``; whatever is filled stays if a later step raises."""
    from refute.packs.tess import power
    from refute.packs.tess.adapter import TessAdapter
    from refute.packs.tess.calib05 import c2
    from refute.packs.tess.detrend import detrend
    from refute.packs.tess.discover import injection as inj
    from refute.packs.tess.discover.measure import load_catalogs
    from refute.packs.tess.pipeline import global_prewhitening
    from refute.packs.tess.search import search_period

    target = t.targets()[row["key"]]
    raw, staged, plans = t._plans()
    randomness = json.loads((t.V04_STEP / "runs" / "r_inj.json").read_text("utf-8"))["beacon"][
        "randomness"
    ]
    catalog = ((t.V04_STEP / "eb_catalog.csv").as_posix(),)
    scan_path = (t.V04_STEP / "eb_catalog_scan.json").as_posix()
    tasks = c2.tasks_for(target, raw, t.CACHE, randomness, catalog, scan_path)
    task = next(x for x in tasks if x.kind == "injection" and x.slot == row["slot"])
    base = TessAdapter().load(target, staged, t.CACHE)
    star = base.star
    drawn = inj.draw_injections(
        task.seed, task.k, inj.first_time(base),
        star.radius_rsun if star else None, star.logg_cgs if star else None,
    )[task.slot]  # fmt: skip
    data = inj.inject(base, drawn)
    rec["sectors"] = int(np.unique(data.lc.sector).size)
    rec["injection"] = _safe(drawn.to_dict())
    catalogs, scan = load_catalogs(catalog, scan_path, t.CACHE)
    p04 = plans["v04"]
    flat = detrend(data.lc, p04.detrend)
    pw, searched = global_prewhitening(data, p04, flat)
    cand = search_period(searched, p04.search).candidate
    v04, _ = t._outcome(data, cand, p04, catalogs, scan, pw)
    _, references = c2.references(ROOT)
    mine = {
        "kind": "injection", "status": "OK", "chain": {"v04": v04},
        "injection": drawn.to_dict(),
        "recovery": inj.recovery(drawn, v04["candidate"], v04["gate_passed"]),
    }  # fmt: skip
    rec["compat_problems"] = c2.compat_problems(
        mine, references[f"{row['key']}/injection/{row['slot']}"]
    )
    rec["v04"] = {"stage_verdict": v04["stage_verdict"], "tests": v04["tests"],
                  "candidate": v04["candidate"]}  # fmt: skip
    rec["v4"] = {"a0_depth_calls": [], "tests": {}}
    out, final = _battery(data, cand, plans["v4C"], catalogs, scan, pw, rec["v4"])
    base_seed = power.candidate_seed("systematics", final)
    scales = _scales(data)
    for c in rec["v4"]["a0_depth_calls"]:
        if c["caller"] == "check_systematics":
            c["series"] = SYSTEMATICS_SERIES.get(c["seed"] - base_seed, "other")
        if c.get("series") in ("pdcsap", "sap"):
            c["expected_mean"] = _expected(c, drawn, scales[c["series"]])
        elif c.get("series") in ("sap_minus_expected", "background"):
            c["expected_mean"] = 0.0
    rec["final_candidate"] = _safe(
        {k: getattr(final, k) for k in ("period", "t0", "duration", "depth", "depth_err", "snr")}
    )
    rec["v4"].update(
        candidate=out["candidate"],
        stage_verdict=out["stage_verdict"],
        stage_verdict_reason=out["stage_verdict_reason"],
        deferred=out["deferred"],
        stage_tests=out["stage_tests"],
    )
    rec["inputs"] = _inputs(data, final, plans["v4C"])
    rec["status"] = "OK"


_STATE: dict = {}


def _flags_dir() -> Path:
    if "flags" not in _STATE:
        _STATE["flags"] = OUT / fingerprint() / "defect-flags"
    return _STATE["flags"]


def _sentinel() -> Path:
    """The binding stop of an instrumentation or classification failure (Codex, round 3)."""
    return _flags_dir().parent / "stop-instrumentation.json"


def shard(row: dict) -> bytes:
    """One injection; a worker classifies its own result. An instrumentation or classification
    failure writes the binding sentinel at once; a causal (c) blocker writes a flag; with the
    sentinel present or the flags at the threshold, a shard computes nothing more."""
    started = time.process_time()
    rec: dict = {"key": row["key"], "slot": row["slot"], "stratum": row["stratum"]}
    flags = _flags_dir()
    if _sentinel().exists() or (flags.exists() and len(list(flags.glob("*.json"))) >= STOP_FLAGS):
        rec["status"] = "STOPPED"
        return json.dumps(rec, sort_keys=True).encode() + b"\n"
    try:
        one(row, rec)
    except Exception as exc:  # noqa: BLE001 - recorded with what was filled, never dropped
        rec["status"], rec["reason"] = "ERROR", repr(exc)
    rec["cpu_seconds"] = time.process_time() - started
    try:
        if "old" not in _STATE:
            _STATE["old"] = _old_records()
        kind, defect = _defect(rec, _STATE["old"].get((row["key"], row["slot"])))
    except Exception as exc:  # noqa: BLE001 - a failed self-check stops the run
        kind, defect = "instrumentation", f"the worker's classification failed: {exc!r}"
    note = json.dumps({"injection": f"{row['key']}/{row['slot']}", "defect": defect})
    if kind == "instrumentation":
        _sentinel().parent.mkdir(parents=True, exist_ok=True)
        _sentinel().write_text(note, "utf-8")
    elif kind == "code":
        flags.mkdir(parents=True, exist_ok=True)
        (flags / f"{row['key']}-{row['slot']:02d}.json").write_text(note, "utf-8")
    return json.dumps(rec, sort_keys=True).encode() + b"\n"


# --- the part -------------------------------------------------------------------------------


def fingerprint() -> str:
    from refute.core.codehash import compute_code_hash

    h = hashlib.sha256(compute_code_hash().sha256.encode())
    for path in (Path(__file__), HERE / "forecast_t2a.py", HERE / "t2a-fetch.json",
                 HERE / "budgeted.py", HERE / "driver.py"):  # fmt: skip
        h.update(hashlib.sha256(path.read_bytes()).digest())
    return h.hexdigest()[:16]


def forecast_used(book: dict | None = None) -> float:
    """Everything the forecast has consumed: its parts with these two, every attempt, and its
    charged smokes."""
    book = book or budgeted.load()
    parts = book["sections"][SECTION]["parts"]
    total = sum(c["hours"] for c in book.get("charges", []) if c["name"].startswith("forecast"))
    for part in (t.D2D4_PART, t.DIAGNOSIS_PART, t.PART, PART, SMOKE_PART):
        row = parts.get(part, {})
        total += row.get("spent_hours", 0.0) + sum(
            a["spent_hours"] for a in row.get("attempts", [])
        )
    return total


def _old_records() -> dict:
    """The forecast's records (read only; ``budgeted.assembled`` writes nothing)."""
    forecast = t.fingerprint()
    data = budgeted.assembled(
        SECTION, t.PART, t.OUT / forecast, t.shard, t.shards(), forecast, t.WORKERS, pin=t.PIN,
        max_shard_seconds=t.MAX_SHARD_SECONDS,
    )  # fmt: skip
    return {(r["key"], r["slot"]): r for r in map(json.loads, data.decode().splitlines()) if r}


def _losses(old: dict) -> list[dict]:
    return [r for r in old.values() if r["v04"]["stage_verdict"] in t.KEPT
            and r["v4B"]["stage_verdict"] not in t.KEPT]  # fmt: skip


def preflight() -> tuple[list, dict]:
    """The schedule and the forecast's records, checked before any dispatch; refused otherwise."""
    shards = t.shards()
    if len(shards) != EXPECTED_SHARDS or any(
        a["stratum"] not in t.MEASURED_STRATA for _, a in shards
    ):
        raise SystemExit("preflight: the schedule is not the forecast's 80 injections")
    old = _old_records()
    losses = _losses(old)
    systematics = sum(
        r["v4B"]["tests"].get("systematics", {}).get("status") == "INCONCLUSIVE" for r in losses
    )
    if (len(old), len(losses), systematics) != (
        EXPECTED_SHARDS, EXPECTED_LOSSES, EXPECTED_SYSTEMATICS
    ):  # fmt: skip
        raise SystemExit(f"preflight: the forecast's records give {len(old)}, {len(losses)}, "
                         f"{systematics}")  # fmt: skip
    return shards, old


def _smoke_shards(shards: list, old: dict) -> list:
    """The first forecast loss with ``systematics`` INCONCLUSIVE in each stratum."""
    out = []
    for stratum in t.MEASURED_STRATA:
        for sid, row in shards:
            r = old[(row["key"], row["slot"])]
            if row["stratum"] == stratum and r in _losses({0: r}) and (
                r["v4B"]["tests"].get("systematics", {}).get("status") == "INCONCLUSIVE"
            ):  # fmt: skip
                out.append((sid, row))
                break
    return out


def _cap(part: str, fp: str, shards: list) -> float:
    book = budgeted.load()
    row = book["sections"][SECTION]["parts"][part]
    same = row.get("identity") == budgeted._identity(fp, shards, row["allocation_hours"])
    # this attempt's own spending is added back only when it is the same attempt; the driver may
    # pass its cap by up to 10 %, so the cap is reserved below what is left
    left = FORECAST_CAP_HOURS - forecast_used(book) + (row.get("spent_hours", 0.0) if same else 0)
    return left / DRIVER_OVERSHOOT


def prepare() -> None:
    """Declare the parts and record the maintainer's release of both failed gates for them."""
    book = budgeted.load()
    parts = book["sections"][SECTION]["parts"]
    allocations = {p: r["allocation_hours"] for p, r in parts.items()}
    allocations[PART] = ALLOCATION_HOURS
    allocations[SMOKE_PART] = SMOKE_ALLOCATION_HOURS
    budgeted.declare(SECTION, allocations)
    have = {(e["gate"], e["part"]) for e in budgeted.load().get("gate_exemptions", [])}
    for part in (SMOKE_PART, PART):
        for gate in ("adequacy", "planet_forecast"):
            if (gate, part) not in have:
                budgeted.exempt(gate, SECTION, part, DECISION)


def smoke() -> None:
    fp = fingerprint()
    shards, old = preflight()
    chosen = _smoke_shards(shards, old)
    cap = _cap(SMOKE_PART, fp, chosen)
    print("smoke hard cap", round(cap, 2), "CPU-h", flush=True)
    state = budgeted.execute(
        SECTION, SMOKE_PART, OUT / "smoke" / fp, shard, chosen, fp, len(chosen), pin=t.PIN[:2],
        max_shard_seconds=t.MAX_SHARD_SECONDS, hard_cap_hours=cap,
    )  # fmt: skip
    if state != "complete":
        raise SystemExit(state)
    data = budgeted.assembled(
        SECTION, SMOKE_PART, OUT / "smoke" / fp, shard, chosen, fp, len(chosen), pin=t.PIN[:2],
        max_shard_seconds=t.MAX_SHARD_SECONDS,
    )  # fmt: skip
    report = []
    for rec in (json.loads(x) for x in data.decode().splitlines() if x):
        before = old.get((rec["key"], rec["slot"]))
        report.append({"injection": f"{rec['key']}/{rec['slot']}",
                       "defect": _defect(rec, before),
                       "quarantine": _quarantine(rec, before),
                       "blockers": [] if _quarantine(rec, before) else [
                           {k: b.get(k) for k in ("test", "cls", "evidence")}
                           for b in classify(rec)]})  # fmt: skip
    accepted = not any(r["defect"][0] or r["quarantine"] for r in report)
    doc = {"fingerprint": fp, "accepted": accepted, "smokes": report}
    (OUT / "smoke-acceptance.json").write_text(json.dumps(doc, indent=1) + "\n", "utf-8")
    print(json.dumps(doc, indent=1), flush=True)
    if not accepted:
        raise SystemExit("STOP: a smoke shows a code defect or a quarantine")


def run() -> None:
    fp = fingerprint()
    shards, _ = preflight()
    accept = OUT / "smoke-acceptance.json"
    doc = json.loads(accept.read_text("utf-8")) if accept.exists() else {}
    if doc.get("fingerprint") != fp or doc.get("accepted") is not True:
        raise SystemExit("the smokes of this fingerprint have not been accepted")
    cap = _cap(PART, fp, shards)
    print("hard cap", round(cap, 2), "CPU-h", flush=True)
    state = budgeted.execute(
        SECTION, PART, OUT / fp, shard, shards, fp, t.WORKERS, pin=t.PIN,
        max_shard_seconds=t.MAX_SHARD_SECONDS, hard_cap_hours=cap,
    )  # fmt: skip
    print(state, flush=True)
    if state != "complete":
        raise SystemExit(state)


# --- the classification, frozen before the run ----------------------------------------------


def _instrumentation(rec: dict) -> list[str]:
    why = []
    for c in (rec.get("v4") or {}).get("a0_depth_calls", []):
        if "instrumentation_error" in c:
            why.append(f"instrumentation error: {c['instrumentation_error']}")
        elif "COPY DISAGREES" in (c.get("why") or ""):
            why.append("this script's copy of A0 disagrees")
    return why


def _quarantine(rec: dict, before: dict | None) -> list[str]:
    """Why an injection is not classified (empty when it is)."""
    why = _instrumentation(rec)
    if rec.get("status") != "OK":
        return [f"{rec.get('status')}: {rec.get('reason')}", *why]
    if rec.get("compat_problems"):
        why.append("the v0.4 record does not reproduce")
    if before is None:
        why.append("no forecast record")
    else:
        if before["v4B"]["candidate"] != rec["v4"]["candidate"]:
            why.append("the candidate differs from the forecast's")
        old = {k: v["status"] for k, v in before["v4B"]["tests"].items()}
        new = {k: v["final"]["status"] for k, v in rec["v4"]["tests"].items() if "final" in v}
        if old != new:
            diff = sorted(k for k in set(old) | set(new) if old.get(k) != new.get(k))
            why.append(f"test statuses differ from the forecast's version 4 B: {diff}")
        if before["v4B"]["stage_verdict"] != rec["v4"]["stage_verdict"]:
            why.append("the stage verdict differs from the forecast's version 4 B")
    return why


def _defect(rec: dict, before: dict | None) -> tuple[str | None, str | None]:
    """What a worker records: ("instrumentation", ...) for an instrumentation quarantine,
    ("code", ...) for a causal (c) blocker of a loss, else (None, None)."""
    if rec.get("status") == "STOPPED":
        return None, None
    inst = _instrumentation(rec)
    if inst:
        return "instrumentation", "; ".join(inst)
    if _quarantine(rec, before):
        return None, None
    if rec["v04"]["stage_verdict"] not in t.KEPT or rec["v4"]["stage_verdict"] in t.KEPT:
        return None, None
    found = [f"{b['test']}: {b['evidence']}" for b in classify(rec) if b["cls"] == "c"]
    return ("code", "; ".join(found)) if found else (None, None)


def _trace_class(call: dict, inputs: dict) -> tuple[str, str]:
    """The class of an A0 None, with its evidence."""
    why = call["why"]
    product = PRODUCT.get(call.get("series", ""), call.get("series", "the series"))
    if why.startswith("fewer than 10 finite"):
        return "a", f"{product}: {why} in sectors {call.get('sectors')}"
    if why.startswith("no event with enough"):
        key = {"pdcsap": "pdcsap", "sap": "sap", "background": "background"}.get(
            call.get("series", ""), "sap"
        )
        cover = {s["sector"]: s.get(f"transits_covered_{key}") for s in inputs["aux_sectors"]
                 if s["sector"] in (call.get("sectors") or [])}  # fmt: skip
        return "a", f"{product}: {why}; transits covered per sector {cover}"
    if "outside the grid" in why or "comb measured none" in why or "refused" in why:
        return "d", f"{product}: {why}"
    if why == "an event error is not measurable":
        return "b", f"{product}: {why}"
    return "u", f"{product}: {why}"


def _systematics_causes(test: dict, rec: dict) -> list[dict]:
    """Each sub-check of ``systematics`` that did not run, with its class and evidence."""
    m = test["metrics"]
    calls = rec["v4"]["a0_depth_calls"]
    inputs = rec["inputs"]
    by_series = {c.get("series"): c for c in calls if c["caller"] == "check_systematics"}
    out = []
    for sub, why in (m.get("sub_checks_not_run") or {}).items():
        cause: dict = {"sub_check": sub, "reason": why}
        series = SUB_CHECK_SERIES.get(sub, ())
        nones = {s: by_series[s]["why"] for s in series
                 if s in by_series and by_series[s].get("result") is None}  # fmt: skip
        if nones:
            cause["a0_depth_none"] = nones
        anomalies = [x for x in (_anomaly(by_series.get(s)) for s in series) if x]
        if anomalies:
            cause["audit_warnings"] = anomalies  # unresolved; never a class (Codex, round 3)
        if why.startswith("only ") and "transit" in why:
            cause.update(cls="a", evidence=f"{why}: the light curve's transits with data "
                         f"{m.get('n_transits_with_data')}")  # fmt: skip
        elif why == "no CROWDSAP value":
            missing = [s["sector"] for s in inputs["aux_sectors"] if s["crowdsap"] is None]
            cause.update(cls="a", evidence=f"CROWDSAP absent in sector(s) {missing}")
        elif why.startswith("A0's errors are not available"):
            cause.update(cls="d", evidence=why)
        elif nones:
            ranked = sorted(_trace_class(by_series[s], inputs) for s in nones)
            cls = next(k for k in "cuadb" if k in {r[0] for r in ranked} | {"b"})
            cause.update(cls=cls, evidence="; ".join(r[1] for r in ranked))
        elif why == "no transit measured in both the PDCSAP and SAP series":
            a, b = by_series.get("pdcsap"), by_series.get("sap_minus_expected")
            if a and b and a.get("result") and b.get("result"):
                detail = {"pdcsap": a["result"], "sap_minus_expected": b["result"]}
                crowd = {s["sector"]: s["crowdsap"] for s in inputs["aux_sectors"]}
                depth = _common_expected(a["result"], b["result"], crowd)
                cause["measurements"] = detail
                cause["common_event_expected_depth"] = depth
                if depth == "no common event":
                    cause.update(cls="d", evidence="no event common to the two A0 measurements")
                elif isinstance(depth, float) and not depth > 0:
                    cause.update(cls="b", evidence=f"the common events' expected SAP depth "
                                 f"{depth:.4g} is not positive")  # fmt: skip
                elif isinstance(depth, float):
                    cause.update(
                        cls="c",
                        evidence=f"suspected: the common events' expected SAP depth {depth:.4g} "
                        "is positive, yet none was measured",
                    )
                else:
                    cause.update(cls="u", evidence=f"the common-event depth: {depth}")
            else:
                cause.update(cls="c", evidence="suspected: no A0 None explains it")
        elif why == "error not measurable":
            r = by_series.get(ERROR_SERIES.get(sub, ""))
            cause.update(cls="b", evidence=f"{ERROR_SERIES.get(sub)} error "
                         f"{(r or {}).get('result', {}) and r['result'].get('error')}")  # fmt: skip
        elif why.endswith("depth is not positive"):
            cause.update(cls="b", evidence=f"{why} (audit warnings, if any, kept apart)")
        elif why.startswith("no transit measured"):
            cause.update(cls="c", evidence="suspected: no A0 None explains it")
        else:
            cause.update(cls="u", evidence=why)
        out.append(cause)
    return out


def _common_expected(pdc: dict, r: dict, crowd: dict) -> float | str:
    """``battery_v51_diff.expected_sap_depth`` recomputed from the two traces: the SAP-minus-
    expected weights over the common events, times each event's sector CROWDSAP and PDCSAP
    depth."""
    depth_of = dict(zip(pdc["epochs"], pdc["depths"], strict=True))
    common = [i for i, e in enumerate(r["epochs"]) if e in depth_of]
    if not common:
        return "no common event"
    try:
        w = np.array([r["weights"][i] for i in common], dtype=float)
        w = w / np.sum(w)
        c = np.array([crowd[r["event_sectors"][i]] for i in common], dtype=float)
        d = np.array([depth_of[r["epochs"][i]] for i in common], dtype=float)
        return float(np.sum(w * c * d))
    except (KeyError, TypeError, ValueError) as exc:
        return f"not recomputable: {exc!r}"


def _label_of(causes: list[dict]) -> str | None:
    """The INCONCLUSIVE label the identified causes would carry under the battery's priority."""
    from refute.core.inconclusive import PRIORITY

    labels = set()
    for c in causes:
        if c["cls"] == "a":
            labels.add("missing_input" if "CROWDSAP" in c["evidence"] else "not_enough_data")
        elif c["cls"] == "b":
            labels.add("insufficient_sensitivity")
        elif c["cls"] == "d":
            labels.add("outside_domain")
    return next((x for x in PRIORITY if x in labels), None)


def classify(rec: dict) -> list[dict]:
    """The blockers of a loss, each with its class (the module's docstring) and evidence."""
    tests = rec["v4"]["tests"]
    calls = rec["v4"]["a0_depth_calls"]
    audit = {}
    for c in calls:
        found = _anomaly(c)
        if found:
            audit.setdefault(c["caller"], []).append(found)
    callers = {"systematics": "check_systematics", "aperture_depth": "check_aperture_depth"}
    blockers = []
    for name in rec["v4"]["stage_tests"]:
        test = (tests.get(name) or {}).get("final")
        if test is None or test["status"] not in ("FAIL", "INCONCLUSIVE"):
            continue
        b = {"test": name, "status": test["status"], "severity": test["severity"],
             "message": test["message"],
             "label": (test["metrics"] or {}).get("inconclusive_class")}  # fmt: skip
        anomalies = audit.get(callers.get(name, ""), [])
        if anomalies:
            b["audit_warnings"] = anomalies  # every status; unresolved, never a class
        if name == "systematics" and test["status"] == "INCONCLUSIVE":
            causes = _systematics_causes(test, rec)
            b["causes"] = causes
            expected = _label_of(causes)
            b["label_from_causes"] = expected
            b["label_defect"] = expected is not None and expected != b["label"]
        if test["status"] == "FAIL":
            b.update(cls="e", evidence=test["message"])
        elif test["message"].startswith("PASS refused: insufficient sensitivity"):
            blocks = {k: {x: v.get(x) for x in ("effect", "alternative", "unit", "probability",
                                                 "required_probability")}
                      for k, v in (test.get("sensitivity") or {}).items()
                      if isinstance(v, dict) and v.get("detectable") is False}  # fmt: skip
            b.update(cls="b", evidence=test["message"], blocks_not_detectable=blocks)
        elif test["message"].startswith("A0's errors are not available"):
            b.update(cls="d", evidence=test["message"])
        elif "causes" in b:
            classes = {c["cls"] for c in b["causes"]}
            # the test is INCONCLUSIVE when any sub-check did not run: a defect or an
            # unrecognized cause names the blocker first, then a, d, b; all causes are kept
            b.update(
                cls=next((k for k in "cuadb" if k in classes), "u"),
                evidence="; ".join(f"{c['sub_check']}: {c['evidence']}" for c in b["causes"]),
            )
        else:
            b.update(cls="u", evidence=test["message"])
        blockers.append(b)
    return blockers


def summarize() -> None:
    fp = fingerprint()
    shards, old = preflight()
    data = budgeted.assembled(
        SECTION, PART, OUT / fp, shard, shards, fp, t.WORKERS, pin=t.PIN,
        max_shard_seconds=t.MAX_SHARD_SECONDS,
    )  # fmt: skip
    got = [json.loads(x) for x in data.decode().splitlines() if x]
    flags = sorted(p.name for p in (OUT / fp / "defect-flags").glob("*.json"))
    out: dict = {
        "label": "diagnosis, decides nothing (#216): T2a's losses with battery version 4",
        "method_status": "not_validated",
        "decision": DECISION,
        "fingerprint": fp,
        "preflight": {"injections": len(got), "forecast_losses_b": EXPECTED_LOSSES,
                      "forecast_losses_b_with_systematics_inconclusive": EXPECTED_SYSTEMATICS},
        "stopped_shards": sum(r.get("status") == "STOPPED" for r in got),
        "defect_flags": flags,
        "instrumentation_sentinel": (OUT / fp / "stop-instrumentation.json").exists(),
        "quarantined": {},
        "losses": [],
    }  # fmt: skip
    classes: Counter = Counter()
    per_test: Counter = Counter()
    per_loss: Counter = Counter()
    label_defects: Counter = Counter()
    instrumentation = False
    for r in got:
        q = _quarantine(r, old.get((r["key"], r["slot"])))
        if q:
            out["quarantined"][f"{r['key']}/{r['slot']}"] = q
            instrumentation |= bool(_instrumentation(r))
            continue
        if r["v04"]["stage_verdict"] not in t.KEPT or r["v4"]["stage_verdict"] in t.KEPT:
            continue
        blockers = classify(r)
        for b in blockers:
            classes[b["cls"]] += 1
            per_test[f"{b['test']} {b['status']}: {b['cls']}"] += 1
            if b.get("label_defect"):
                label_defects[f"{b['label']} -> {b['label_from_causes']}"] += 1
        per_loss["+".join(sorted({b["cls"] for b in blockers}))] += 1
        out["losses"].append(
            {
                "injection": f"{r['key']}/{r['slot']}",
                "stratum": r["stratum"],
                "sectors": r["sectors"],
                "stage_verdict": r["v4"]["stage_verdict"],
                "blockers": blockers,
            }
        )
    with_c = sum(any(b["cls"] == "c" for b in x["blockers"]) for x in out["losses"])
    out["blockers_by_class"] = dict(classes)
    out["blockers_by_test_and_class"] = dict(sorted(per_test.items()))
    out["losses_by_set_of_classes"] = dict(sorted(per_loss.items()))
    out["losses_with_a_code_defect_blocker"] = with_c
    out["systematics_label_defects"] = dict(label_defects)
    out["stop_rule"] = (f"(c) blockers in at least {STOP_FLAGS} of the forecast's "
                        f"{EXPECTED_LOSSES} losses, or any instrumentation quarantine")  # fmt: skip
    out["audit_warnings"] = sum(
        bool(b.get("audit_warnings")) for x in out["losses"] for b in x["blockers"]
    )
    out["stop"] = bool(
        instrumentation
        or out["instrumentation_sentinel"]
        or with_c >= STOP_FLAGS
        or out["stopped_shards"] > 0
        or len(flags) >= STOP_FLAGS
    )
    out["cpu_hours"] = round(sum(float(r.get("cpu_seconds", 0.0)) for r in got) / 3600, 3)
    (HERE / "forecast-t2a-diagnosis.json").write_text(
        json.dumps(out, indent=1, sort_keys=True) + "\n", "utf-8"
    )
    print(json.dumps({k: v for k, v in out.items() if k != "losses"}, indent=1, sort_keys=True))


if __name__ == "__main__":
    {"prepare": prepare, "smoke": smoke, "run": run, "summarize": summarize}[sys.argv[1]]()
