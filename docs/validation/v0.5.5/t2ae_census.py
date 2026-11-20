"""v0.5.5, R1, check T2a-E: a model-free census of the background error of T2a's 102 class-(i)
injections (#218; the frozen design is ``docs/plans/v0.5.5-r1-designs.md``, section T2a-E).
``method_status: not_validated``. **It decides nothing by itself and is never a draft.**

For each of the 102 injections (I1's ``i2_population``, development records only), replayed as
v0.5.4's step 6 replays them (``step6_i2.replay``, with step 6's stops), and checked against **I1's
own historical record** of that injection (class (i) with ``background``, the background error and
the block's power), two errors of **E4's own contrast** (the background rise in event,
``battery_b1.a0_depth_quadratic``):
- **the placebo error**: E4 itself, unchanged, at K = 24 phase-shifted epochs of the candidate
  whose windows share no cadence with the real events' (nor with phase 0.5 when E4 excludes it);
  the sample standard deviation of the usable rises, times the chi-square factor
  (``r1_common.chi2_upper_factor``). **That factor is a heuristic inflation here: 95 % coverage
  has not been established for these dependent placebo estimates.** At least 12 usable shifts,
  else UNK. Each shift's phase, value and status are kept.
- **the white floor**: the minimum-variance combination of the declared E4 window contrasts under
  the stated white-noise approximation (the series' own first-difference scale). Reported apart;
  it is not the best performance of any estimator and does not model the detrending's effect on
  the noise.

**Freed** means the background block's power (``battery_v51_diff.background_block``, unchanged,
through step 6's ``power``) is at least 0.95 with the inflated placebo error. The frozen outcome
is ``r1_common.t2ae_outcome``.

Usage (from the project root, through ``launch_detached.py``):
``.venv/Scripts/python.exe -B docs/validation/v0.5.5/t2ae_census.py run 1`` then ``summarize 1``;
``run 2`` is refused if stage 1's futility rule holds; then ``summarize 2``.
"""

from __future__ import annotations

import dataclasses
import datetime as dt
import hashlib
import json
import math
import sys
import time
import types
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
V054 = ROOT / "docs/validation/v0.5.4"
V052 = ROOT / "docs/validation/v0.5.2/stage2"
for p in (str(V054), str(HERE)):
    if p not in sys.path:
        sys.path.insert(0, p)
import step6_i2 as s6  # noqa: E402,I001  (stage A's and B's modules, then ledger_i)
from step6_i2 import battery_b1  # noqa: E402
import i1_diagnose  # noqa: E402
import pinned_hash  # noqa: E402
import r1_common as rc  # noqa: E402
import budgeted_v3  # noqa: E402
import ledger_v055 as lv  # noqa: E402  (last: it binds budgeted to v0.5.5's ledger)
import budgeted  # noqa: E402

DESIGN = ROOT / "docs/plans/v0.5.5-r1-designs.md"
CHARTER = ROOT / "docs/plans/v0.5.5-charter.md"
OUT = ROOT / ".cache/v055/t2ae"
STAGES = ("1", "2")
SHIFTS = 24
MIN_SHIFTS = 12
POPULATION = 102
I1_FILE = V054 / "i1-diagnosis.json"
REL_TOL = 1e-9  # the replay against I1's historical record (step 6's tolerance)


def part(stage: str) -> str:
    return f"r1_t2ae_{stage}"


# --- the two errors ----------------------------------------------------------------------------


def _shifted(cand, phi: float):
    """The candidate with its epoch moved by ``phi`` of a period; nothing else changes."""
    t0 = cand.t0 + phi * cand.period
    if dataclasses.is_dataclass(cand):
        return dataclasses.replace(cand, t0=t0)
    return types.SimpleNamespace(**{**vars(cand), "t0": t0})


def shift_phases(cand, plan, exclude_half: bool) -> list[float]:
    """K evenly spaced phases in (0, 1) whose windows (E4's outer half-width) keep at least two
    outer half-widths from phase 0 (the real events) and, when E4 excludes it, from phase 0.5."""
    outer = cand.duration / 2.0 + plan.gauntlet.events.baseline_outer_durations * cand.duration
    gap = 2.0 * outer / cand.period
    out = []
    for m in range(1, SHIFTS + 1):
        phi = m / (SHIFTS + 1)
        if min(phi, 1.0 - phi) <= gap:
            continue
        if exclude_half and abs(phi - 0.5) <= gap:
            continue
        out.append(phi)
    return out


def placebo(cap: dict) -> dict:
    """E4, unchanged, at the shifted epochs of the captured candidate, on the real background;
    each shift's phase, value and status kept."""
    cand, plan = cap["candidate"], cap["plan"]
    phases = shift_phases(cand, plan, bool(cap["excl"]))
    means, shifts = [], []
    for phi in phases:
        try:
            g = battery_b1.a0_depth_quadratic(
                cap["t"], cap["bkg"], cap["s"], _shifted(cand, phi), plan, cap["seed"] + 3,
                cap["excl"],
            )  # fmt: skip
        except Exception as exc:  # noqa: BLE001 - a refused shift is recorded, never a value
            shifts.append({"phase": phi, "status": f"refused: {type(exc).__name__}: {exc}"})
            continue
        mean = getattr(g, "mean", None) if g is not None else None
        err = getattr(g, "error", None) if g is not None else None
        if mean is not None and math.isfinite(float(mean)):
            means.append(float(mean))
            shifts.append({"phase": phi, "status": "OK", "value": float(mean),
                           "e4_error": None if err is None else float(err)})  # fmt: skip
        else:
            shifts.append({"phase": phi, "status": "no finite value"})
    out = {"phases": len(phases), "usable": len(means), "shifts": shifts}
    if len(means) < MIN_SHIFTS:
        return {
            **out,
            "status": "UNK",
            "reason": f"{len(means)} usable shifts, fewer than {MIN_SHIFTS}",
        }
    sd = float(np.std(means, ddof=1))
    out.update(
        status="OK",
        sigma_placebo=sd,
        sigma_placebo_inflated=sd * rc.chi2_upper_factor(len(means)),
        placebo_mean=float(np.mean(means)),
    )
    return out


def white_floor(series, cap: dict) -> dict:
    """The minimum-variance combination of the declared E4 window contrasts at the real events,
    under the stated white-noise approximation (1.4826 × the median absolute first difference /
    sqrt(2), per sector, pooled by median). Not the best performance of any estimator, and the
    detrending's effect on the noise is not modelled."""
    cand, plan = cap["candidate"], cap["plan"]
    ev = plan.gauntlet.events
    cadence = plan.data.exptime_seconds / 86400.0
    t, f, sector = series.time, series.flux, series.sector
    scales = []
    for s in np.unique(sector):
        x = f[(sector == s) & np.isfinite(f)]
        if x.size > 2:
            d = np.diff(x)
            scales.append(1.4826 * float(np.median(np.abs(d - np.median(d)))) / math.sqrt(2.0))
    if not scales:
        return {"status": "UNK", "reason": "no sector to scale the white noise"}
    sigma_w = float(np.median(scales))
    centres = [cand.t0 + e * cand.period for e in cap["g_bkg"].epochs]
    wins = [s6.e4_weights(t, c, cand.duration, ev, cadence) for c in centres]
    if not wins or any(w is None for w in wins):
        return {"status": "UNK", "reason": "an E4 window is not reconstructed"}
    spans = sorted((w[0], w[1]) for w in wins)
    if any(b[0] < a[1] for a, b in zip(spans, spans[1:], strict=False)):
        return {"status": "UNK", "reason": "two E4 windows share cadences"}
    if not (math.isfinite(sigma_w) and sigma_w > 0):
        return {"status": "UNK", "reason": f"the white scale is not finite and positive: {sigma_w}"}
    variances = [sigma_w**2 * float(np.sum(w[2] ** 2)) for w in wins]
    if not all(math.isfinite(v) and v > 0 for v in variances):
        return {"status": "UNK", "reason": "an E4 contrast has no finite positive variance"}
    info = sum(1.0 / v for v in variances)
    if not (info > 0 and math.isfinite(info)):
        return {"status": "UNK", "reason": "the white floor is not finite and positive"}
    return {
        "status": "OK",
        "sigma_white_cadence": sigma_w,
        "sigma_white_floor": 1.0 / math.sqrt(info),
        "events": len(wins),
    }


def _check_i1(row: dict, test: dict, recorded, recorded_power, ref: dict) -> None:
    """The replay against I1's own historical record of the injection (Codex, r0r1 round 1):
    class (i) with ``background``, the background error and the block's power."""
    tag = f"{row['key']}/{row['slot']}"
    if ref.get("class") != "i" or "background" not in (ref.get("non_detectable") or []):
        raise RuntimeError(f"STOP: {tag}: I1's record is not class (i) with background")
    if test.get("class") != ref["class"] or sorted(test.get("non_detectable", [])) != sorted(
        ref["non_detectable"]
    ):
        raise RuntimeError(f"STOP: {tag}: the replay's class differs from I1's record")
    want = ref.get("background_rise_err")
    if not (isinstance(want, float) and math.isfinite(want) and want > 0):
        raise RuntimeError(f"STOP: {tag}: I1's record has no background error")
    if abs(float(recorded) / want - 1.0) > REL_TOL:
        raise RuntimeError(f"STOP: {tag}: the replay's background error differs from I1's record")
    want_p = ref.get("power")
    if not (isinstance(want_p, float) and math.isfinite(want_p)):
        raise RuntimeError(f"STOP: {tag}: I1's record has no block power")
    if abs(float(recorded_power) - want_p) > REL_TOL:
        raise RuntimeError(f"STOP: {tag}: the replay's block power differs from I1's record")


def one(arg: dict) -> dict:
    """One injection; the replay checks are step 6's plus I1's historical record, and a failed
    one raises (the driver stops). The replay runs in the current environment (its helpers
    locate no record by the code hash); matching the recorded outputs establishes agreement only
    for the quantities and tolerances checked."""
    import importlib.metadata as md
    import platform

    row = arg["row"]
    out: dict = {
        "key": row["key"],
        "slot": row["slot"],
        "replay_environment": {
            "python": platform.python_version(),
            "numpy": md.version("numpy"),
            "scipy": md.version("scipy"),
            "astropy": md.version("astropy"),
        },
    }
    rec, cap = s6.replay({k: v for k, v in arg.items() if k != "i1_reference"})
    out["replay_record"] = rec  # kept per case (the charter, change 9)
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
    if not s6._probability(recorded_power) or abs(s6.power(cap, recorded) - recorded_power) > 1e-9:
        raise RuntimeError(f"STOP: {row['key']}/{row['slot']}: the block's power differs")
    _check_i1(row, test, recorded, recorded_power, arg["i1_reference"])
    out.update(
        recorded_error=recorded,
        recorded_power=recorded_power,
        other_tests={k: v.get("status") for k, v in rec.get("tests", {}).items()},
    )
    series = s6.e4_series(cap)
    wf = white_floor(series, cap)
    out["white"] = wf
    if wf["status"] == "OK":
        out["white"]["power"] = s6.power(cap, wf["sigma_white_floor"])
    pl = placebo(cap)
    out["placebo"] = pl
    if pl["status"] != "OK":
        return {**out, "status": "UNK", "reason": pl["reason"]}
    p_inf, p_raw = s6.power(cap, pl["sigma_placebo_inflated"]), s6.power(cap, pl["sigma_placebo"])
    if not (s6._probability(p_inf) and s6._probability(p_raw)):
        return {**out, "status": "UNK", "reason": "a power is not a probability"}
    out.update(
        status="OK",
        power_placebo_inflated=p_inf,
        power_placebo=p_raw,
        freed=bool(p_inf >= rc.REQUIRED),
    )
    return out


# --- the run ----------------------------------------------------------------------------------


def i1_references(i1_rows: list) -> dict:
    """I1's historical records of the T2a injections, read by I1's own reader under I1's
    committed fingerprint (``i1-diagnosis.json``), with ``budgeted`` pointed at v0.5.4's ledger
    for the read only; a refusal is a stop."""
    fp = json.loads(I1_FILE.read_text("utf-8"))["fingerprint"]
    with s6.i4._ledger(s6.ledger_i):
        recs, refusal = i1_diagnose._read(i1_rows, fp)
    if refusal:
        raise SystemExit(f"I1's reader: {refusal}: STOP")
    refs = {}
    for r in recs:
        test = (r.get("tests") or {}).get("systematics") if r.get("kind") == "t2a" else None
        if r.get("status") == "OK" and test:
            refs[f"{r['key']}/{r['slot']}"] = {
                "class": test.get("class"),
                "non_detectable": test.get("non_detectable") or [],
                "background_rise_err": (test.get("metrics") or {}).get("background_rise_err"),
                "power": ((test.get("blocks") or {}).get("background") or {}).get("probability"),
            }
    return refs


def population() -> list:
    """Step 6's population (the 102), in step 6's order, each row with I1's historical reference;
    stage 1 is the first 51. The earlier stages' readers run under the pinned code hash."""
    with pinned_hash.pinned():
        rows = s6.schedule()
        refs = i1_references(i1_diagnose.schedule())
    if len(rows) != POPULATION:
        raise SystemExit(f"{len(rows)} injections, not 102: STOP")
    out = []
    for sid, arg in rows:
        tag = f"{arg['row']['key']}/{arg['row']['slot']}"
        if tag not in refs:
            raise SystemExit(f"{tag}: no I1 record: STOP")
        out.append((sid, {**arg, "i1_reference": refs[tag]}))
    return out


def schedule(stage: str) -> list:
    rows = population()
    half = POPULATION // 2
    return rows[:half] if stage == "1" else rows[half:]


def shard(arg: dict) -> bytes:
    try:
        rec = one(arg)
    except Exception as exc:  # the injection's identity on every failure
        row = arg["row"]
        raise RuntimeError(
            f"STOP: {row['key']}/{row['slot']}: {type(exc).__name__}: {exc}"
        ) from exc
    return (json.dumps(rec, sort_keys=True, default=float) + "\n").encode()


FROZEN = (
    Path(__file__),
    HERE / "r1_common.py",
    HERE / "ledger_v055.py",
    HERE / "pinned_hash.py",
    DESIGN,
    CHARTER,
    V054 / "step6_i2.py",
    V054 / "i1_diagnose.py",
    V054 / "i1-diagnosis.json",
    V054 / "i4_bound.py",
    V054 / "ledger_i.py",
    V054 / "budgeted_v3.py",
    V052 / "budgeted.py",
    V052 / "driver.py",
    s6.i4.STAGE_B / "battery_b1.py",
    s6.i4.STAGE_B / "b1_b14.py",
    s6.i4.STAGE_B / "b1_forecast.py",
    s6.i4.STAGE_B / "ledger_b.py",
    s6.i4.STAGE_B / "b1_blockers_decisive.py",
    s6.i4.STAGE_B / "b1_data.py",
    s6.i4.STAGE_B / "b1_d2d4_rest.py",
    V052 / "forecast_t2a.py",
    V052 / "forecast_v4.py",
    V052 / "t2a-fetch.json",
    i1_diagnose.ft.C2_RECORDS,  # T2a's population and the C2 references
    i1_diagnose.ft.V04_STEP / "runs" / "r_inj.json",  # the injections' randomness
    i1_diagnose.ft.V04_STEP / "eb_catalog.csv",
    i1_diagnose.ft.V04_STEP / "eb_catalog_scan.json",
    s6.i4.b1_b14.COMPOSITION,  # the frozen composition the replay's version 5 reads
    ROOT / "calibration/v0.4/claim.yaml",
)


def code_identity() -> dict:
    """The complete identity: ``src/``'s current code hash, the pinned one used to locate the
    earlier records, and every frozen file outside ``src/``, under one digest that a second stage
    compares in full."""
    from refute.core.codehash import compute_code_hash

    ident = {
        "src_code_hash": compute_code_hash().sha256,
        "pinned_code_hash_for_earlier_records": pinned_hash.pinned_code_hash().sha256,
        **rc.identity(ROOT, FROZEN),
    }
    ident["digest"] = rc.digest(ident)
    return ident


def fingerprint(rows: list) -> str:
    h = hashlib.sha256(code_identity()["digest"].encode())
    h.update(json.dumps(rows, sort_keys=True, default=str).encode())
    return h.hexdigest()[:16]


def _first_stage() -> dict:
    """Stage 1's record, checked before stage 2 uses it: written, with the same code identity."""
    path = HERE / "t2ae-1.json"
    if not path.exists():
        raise SystemExit("stage 1 has no record: stage 2 refused")
    first = json.loads(path.read_text("utf-8"))
    if first.get("code_identity", {}).get("digest") != code_identity()["digest"]:
        raise SystemExit("stage 1 ran under another complete code identity: stage 2 refused")
    first["_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    return first


def run(stage: str) -> None:
    if stage not in STAGES:
        raise SystemExit(f"unknown stage {stage}")
    lv.assert_bound()
    if stage == "2" and _first_stage().get("futile_after_1") is not False:
        raise SystemExit("stage 1's futility rule holds: stage 2 refused")
    rows = schedule(stage)
    fp = fingerprint(rows)
    workers = rc.workers_now(dt.datetime.now(rc.BRT))

    def launch(cap: float) -> str:
        return budgeted_v3.execute(
            lv.SECTION,
            part(stage),
            OUT / fp,
            shard,
            rows,
            fp,
            workers,
            pin=rc.pin()[:workers],
            max_shard_seconds=rc.MAX_SHARD_SECONDS,
            hard_cap_hours=cap,
            pause_at=rc.NO_PAUSE,
        )

    state = lv.guarded_run(
        part(stage),
        fp,
        rows,
        f"t2ae run {stage}",
        0.3,
        len(rows) * 20_000 + 50_000_000,
        workers,
        rc.MAX_SHARD_SECONDS,
        launch,
    )
    print(state, flush=True)
    lv.check_caps(f"t2ae after the run {stage}", 0.0, 0)
    if state != "complete":
        raise SystemExit(f"STOP for the maintainer: {state}")


def summarize(stage: str) -> None:
    lv.assert_bound()
    lv.check_caps(f"t2ae summarize {stage}", reserve_days=0.05, reserve_tokens=0)
    if lv.charges_left() < 0.02:
        raise SystemExit("too little of the charges' room left for the summary: a STOP")
    started = time.process_time()
    try:
        _summarize(stage)
    finally:
        used = time.process_time() - started
        stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
        lv.charge(
            f"t2ae_summarize_{stage}_{stamp}",
            used / 3600.0,
            f"t2ae_census.summarize {stage}: process time {used:.1f} s",
        )


def _records(stage: str) -> list:
    rows = schedule(stage)
    fp = fingerprint(rows)
    data = budgeted.assembled(
        lv.SECTION,
        part(stage),
        OUT / fp,
        shard,
        rows,
        fp,
        rc.WORKERS_WORKING,
        pin=rc.pin()[: rc.WORKERS_WORKING],
        max_shard_seconds=rc.MAX_SHARD_SECONDS,
    )
    return [json.loads(x) for x in data.decode().splitlines() if x.strip()]


def _counts(recs: list) -> dict:
    valid = [r for r in recs if r.get("status") == "OK"]
    return {
        "injections": len(recs),
        "valid": len(valid),
        "unknown": len(recs) - len(valid),
        "freed": sum(r["freed"] for r in valid),
        "freed_uninflated": sum(r["power_placebo"] >= rc.REQUIRED for r in valid),
        "white_floor_power_at_least_0.95": sum(
            r["white"].get("power", 0.0) >= rc.REQUIRED
            for r in recs
            if r["white"].get("status") == "OK"
        ),
    }


def _summarize(stage: str) -> None:
    recs = _records(stage)
    counts = _counts(recs)
    doc: dict = {
        "label": "v0.5.5 R1, T2a-E: a model-free census of the background error of T2a's 102 "
        "class-(i) injections (development records; decides nothing by itself; never a draft)",
        "method_status": "not_validated",
        "stage": stage,
        "design": "docs/plans/v0.5.5-r1-designs.md (T2a-E)",
        "code_identity": code_identity(),
        "counts": counts,
        "note": "the chi-square factor is a heuristic inflation here: 95 % coverage has not been "
        "established for these dependent placebo estimates; the white floor is the "
        "minimum-variance combination of the declared E4 window contrasts under the stated "
        "white-noise approximation",
        "cpu_hours": round(lv.part_consumption(part(stage)), 4),
    }
    if stage == "1":
        futile = rc.t2ae_futile_after_first(
            counts["freed"], counts["valid"], counts["unknown"], POPULATION - len(recs)
        )
        doc["futile_after_1"] = futile
        if futile:  # stage 2 does not run: the outcome is read now
            doc["outcome"] = rc.t2ae_outcome(counts["freed"], counts["valid"], counts["unknown"])
            if counts["unknown"] <= rc.T2A_MAX_UNK:
                doc["outcome"] = "unresolved (no completion could reach a decisive outcome)"
    else:
        first_doc = _first_stage()
        doc["stage_1_record_sha256"] = first_doc["_sha256"]
        first = first_doc["counts"]
        total = {k: first[k] + counts[k] for k in ("valid", "unknown", "freed")}
        doc["total"] = total
        doc["outcome"] = rc.t2ae_outcome(total["freed"], total["valid"], total["unknown"])
    out = HERE / f"t2ae-{stage}.json"
    if out.exists():
        raise SystemExit(f"{out.name} exists: the record is written once")
    out.write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n", "utf-8", newline="\n")
    print(
        json.dumps(
            {k: doc[k] for k in doc if k in ("counts", "futile_after_1", "total", "outcome")},
            indent=1,
        )
    )


if __name__ == "__main__":
    if budgeted.LEDGER != lv.HERE / "ledger.json":
        raise SystemExit("budgeted is not pointed at v0.5.5's ledger: refused")
    {"run": run, "summarize": summarize}[sys.argv[1]](sys.argv[2])
