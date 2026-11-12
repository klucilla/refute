"""v0.5.4, I4: D2's ``odd_even`` bound with the transit shape as a nuisance parameter (#217;
``docs/plans/v0.5.4-h1-design.md``, section I4). **A bound under a stated model; it decides nothing
by itself.** ``method_status: not_validated``.

On the 178 eligible fresh planets of B1.4's completed D2 part (L is counted there) and, for
comparison with stage A's known-template bound, v0.5.2's 112 eligible planets: each planet is
rebuilt (C1's generator and development seed), its attack reruns to give the final candidate's
depth (version 5 on the 178, version 4 on the 112, each reproducing its record), and the Fisher
information of the odd and even depths together with the trapezoid's ``t0``, ``period``,
``duration`` and ``ingress_fraction`` (analytic derivatives, checked against central differences)
and one level per sector, under the generator's covariance (stage A's ``gram`` by polarization of
v0.5.1's ``mahalanobis2``). ``σ_oe = sqrt(cᵀ F⁻¹ c)``; the power is ``gaussian_probability`` at the
battery's own alternative. The frozen rule: L ≥ 23 gives a draft infeasibility of D2 (a stop for
the maintainer), L < 23 ≤ L + E unresolved, L + E < 23 route.

Usage, through ``scripts/launch_affinity.ps1``: ``run``, then ``summarize`` (``i4-bound.json``).
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import math
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
STAGE_A = ROOT / "docs/validation/v0.5.3/stageA"
STAGE_B = ROOT / "docs/validation/v0.5.3/stageB"
sys.path.insert(0, str(STAGE_A))
import d2_bounds as sa  # noqa: E402,I001  (stage A's bound; it binds budgeted to stage A)

sys.path.insert(0, str(STAGE_B))
import b1_b14  # noqa: E402  (stage B's modules: they bind budgeted to stage B)
import b1_d2d4_rest  # noqa: E402
import ledger_b  # noqa: E402
from b1_b14 import bf, fv  # noqa: E402

sys.path.insert(0, str(HERE))
import ledger_i  # noqa: E402,I001  (last: it binds budgeted to v0.5.4's ledger)
import budgeted  # noqa: E402

PART = "h1_i4"
OUT = ROOT / ".cache/v054/i4"
OUT_FILE = HERE / "i4-bound.json"
DESIGN = ROOT / "docs/plans/v0.5.4-h1-design.md"
WORKERS = 12
PIN = tuple(range(8, 32, 2))
MAX_SHARD_SECONDS = 1700.0
KEPT = ("SURVIVED", "WEAKENED")
REQUIRED = 0.95
NEEDED_LOSSES = 23  # 178 eligible, v0.4 keeps 173: at least 156 kept, so 23 lost leave 155
COND_MAX = 1e12
CONVERGENCE_TOL = 1e-2
SIGMA_TOL = 1e-6
MAX_RECORD_BYTES = 50_000  # a record (at most half) and its sidecar
I1_FILE = HERE / "i1-diagnosis.json"
STOP_FILE = OUT / "binding-stop.json"
RUN_OVERHEAD_BYTES = 50_000_000


@contextlib.contextmanager
def _ledger(module):
    """Read an earlier stage's records through its own reviewed readers: ``budgeted`` pointed at
    that stage's ledger for the read only, saving disabled."""
    saved = (budgeted.LEDGER, budgeted.LINES, budgeted.HARD_MAXIMUM, budgeted.SPENT_BEFORE,
             budgeted.save)  # fmt: skip
    budgeted.LEDGER = module.HERE / "ledger.json"
    budgeted.LINES = {module.SECTION: module.CAP_HOURS - getattr(module, "CHARGES_ROOM", 0.0)}
    budgeted.HARD_MAXIMUM, budgeted.SPENT_BEFORE = module.CAP_HOURS, 0.0
    budgeted.save = None
    try:
        yield
    finally:
        (budgeted.LEDGER, budgeted.LINES, budgeted.HARD_MAXIMUM, budgeted.SPENT_BEFORE,
         budgeted.save) = saved  # fmt: skip


def _statuses(tests: dict) -> dict:
    return {k: v.get("status") for k, v in tests.items()}


def schedule() -> list:
    with _ledger(ledger_b):
        fresh, _, _, _ = b1_d2d4_rest.complete_records()
    old = sa.d2_old()  # the driver's own reader of v0.5.2's forecast (no ledger involved)
    rows = []
    for r in fresh:
        if r.get("status") == "OK" and r["gate_passed"] and r["identity"]:
            arg = {
                "set": "fresh",
                "index": r["index"],
                "battery": "v5",
                "expected_verdict": r["v5"],
                "expected_tests": _statuses(r["v5_tests"]),
            }
            rows.append((f"f{r['index']:05d}", arg))
    for r in sa.eligible(old):
        arg = {
            "set": "v052",
            "index": r["index"],
            "battery": "v4",
            "expected_verdict": r["v4"],
            "expected_tests": _statuses(r["v4_tests"]),
        }
        rows.append((f"o{r['index']:05d}", arg))
    n_f = sum(a["set"] == "fresh" for _, a in rows)
    n_o = sum(a["set"] == "v052" for _, a in rows)
    if (n_f, n_o) != (178, 112):
        raise SystemExit(f"the populations are {n_f} and {n_o}, not 178 and 112: refused")
    return rows


def shape_and_derivatives(t, truth):
    """The generator's trapezoid (``synthetic.trapezoid`` at depth 1) and its analytic derivatives
    with respect to t0, period, duration and ingress_fraction (the design's formulas)."""
    p, t0 = truth["period_days"], truth["t0_btjd"]
    dur, q = truth["duration_days"], truth["ingress_fraction"]
    dt = np.mod(t - t0 + 0.5 * p, p) - 0.5 * p
    half = dur / 2.0
    w = max(q * dur, 1e-6)
    shape = np.clip((half - np.abs(dt)) / w, 0.0, 1.0)
    ramp = (shape > 0.0) & (shape < 1.0)
    n = np.round((t - t0 - dt) / p)
    sgn = np.sign(dt)
    zero = np.zeros_like(t)
    d_t0 = np.where(ramp, sgn / w, zero)
    d_p = np.where(ramp, n * sgn / w, zero)
    d_dur = np.where(ramp, np.abs(dt) / (q * dur**2), zero)
    d_q = np.where(ramp, -shape / q, zero)
    return shape, {"t0": d_t0, "period": d_p, "duration": d_dur, "ingress_fraction": d_q}, n


def _numeric(t, truth, name, h):
    from refute.packs.tess import synthetic as syn

    def f(delta):
        tr = dict(truth)
        tr[{"t0": "t0_btjd", "period": "period_days", "duration": "duration_days",
            "ingress_fraction": "ingress_fraction"}[name]] += delta  # fmt: skip
        return syn.trapezoid(t, tr["period_days"], tr["t0_btjd"], 1.0, tr["duration_days"],
                             tr["ingress_fraction"])  # fmt: skip

    return (f(h) - f(-h)) / (2.0 * h)


def convergence(t, truth, analytic, n) -> dict:
    """The analytic columns against central differences at the frozen steps; the relative L2
    difference of each."""
    steps = {"t0": 1e-6, "duration": 1e-6 * truth["duration_days"],
             "ingress_fraction": 1e-6 * truth["ingress_fraction"],
             "period": 1e-7 / max(float(np.max(np.abs(n))), 1.0)}  # fmt: skip
    out = {}
    for name, h in steps.items():
        num = _numeric(t, truth, name, h)
        a = analytic[name]
        denom = max(float(np.linalg.norm(a)), 1e-300)
        out[name] = float(np.linalg.norm(num - a) / denom)
    return out


def nuisance_bound(t, sector, truth, sigma_w, sigma_r) -> dict:
    """``σ_oe`` with the shape as a nuisance; every validity check of the design's E."""
    shape, deriv, n = shape_and_derivatives(t, truth)
    trend = sa.trend_multiplier(t, truth)
    p, t0, depth = truth["period_days"], truth["t0_btjd"], truth["depth"]
    epoch = np.round((t - t0) / p).astype(int)
    unit = shape * trend
    cols = [np.where(epoch % 2 != 0, -unit, 0.0), np.where(epoch % 2 == 0, -unit, 0.0)]
    for name in ("t0", "period", "duration", "ingress_fraction"):
        cols.append(-trend * depth * deriv[name])
    cols += [(sector == s).astype(float) for s in np.unique(sector)]
    out: dict = {"columns": len(cols), "invalid": []}
    conv = convergence(t, truth, deriv, n)
    out["convergence"] = conv
    if any(not math.isfinite(v) or v > CONVERGENCE_TOL for v in conv.values()):
        out["invalid"].append("the convergence check failed")
    f = sa.gram(t, sector, cols, sigma_w, sigma_r)
    if not np.all(np.isfinite(f)):
        out["invalid"].append("F has a non-finite entry")
        return out
    d = np.sqrt(np.clip(np.diag(f), 0.0, None))
    if np.any(d <= 0):
        out["invalid"].append("F has a zero column")
        return out
    fs = f / np.outer(d, d)
    try:
        np.linalg.cholesky(fs)
    except np.linalg.LinAlgError:
        out["invalid"].append("F is not positive definite")
        return out
    cond = float(np.linalg.cond(fs))
    out["condition_scaled"] = cond
    if not math.isfinite(cond) or cond > COND_MAX:
        out["invalid"].append(f"F is ill-conditioned ({cond:.3g})")
    c = np.zeros(len(cols))
    c[0], c[1] = 1.0, -1.0
    var = float(c @ np.linalg.solve(f, c))
    out["variance"] = var
    if not (math.isfinite(var) and var > 0):
        out["invalid"].append("the variance is not positive and finite")
        return out
    out["sigma"] = math.sqrt(var)
    return out


def one(arg: dict) -> dict:
    from refute.packs.tess.calib05 import c1
    from refute.packs.tess.detrend import detrend
    from refute.packs.tess.pipeline import attack_candidate, global_prewhitening
    from refute.packs.tess.power import gaussian_probability
    from refute.packs.tess.search import search_period

    i = arg["index"]
    data, truth = c1.generate("P", c1.development_seed("P", i))
    p04, _, p4 = fv.plans()
    b1_b14.battery_b1.check_active(None)
    flat = detrend(data.lc, p04.detrend)
    pw, searched = global_prewhitening(data, p04, flat)
    cand = search_period(searched, p04.search).candidate
    if arg["battery"] == "v5":
        with bf.Version5(b1_b14.config()):
            g = attack_candidate(data, cand, p4, None, None, pw)
    else:
        g = attack_candidate(data, cand, p4, None, None, pw)
    verdict, detail = fv._verdict(g.tests, p4)
    rec: dict = {"verdict": verdict, "mismatch": []}
    if verdict != arg["expected_verdict"]:
        rec["mismatch"].append(f"verdict {verdict}, recorded {arg['expected_verdict']}")
    if _statuses(detail) != arg["expected_tests"]:
        rec["mismatch"].append("test statuses differ from the record")
    if rec["mismatch"]:
        return rec
    final = g.candidate
    depth = float(final.depth)
    sigma_w = truth["sigma_white_ppm"] * 1e-6
    sigma_r = sigma_w / 2.0 if truth["correlated"] else 0.0
    t, sector = data.lc.time, data.lc.sector
    scale = sa.sector_scale(sector, data.lc.flux)
    alt = p4.stronger.odd_even_alternative_depth_fraction * depth
    max_sigma = p4.gauntlet.odd_even.max_sigma
    known = sa.odd_even_bound(t, sector, truth, sigma_w, sigma_r, scale)
    nb = nuisance_bound(t, sector, truth, sigma_w, sigma_r)
    rec.update({
        "final_depth": depth, "alternative": alt, "sectors": int(len(np.unique(sector))),
        "sigma_known_template": known,
        "power_known_template": gaussian_probability(alt, known, max_sigma),
        "nuisance": nb,
    })  # fmt: skip
    if "sigma" in nb:
        if nb["sigma"] < known * (1.0 - SIGMA_TOL):
            nb["invalid"].append("the nuisance σ is below the known-template σ")
        power = gaussian_probability(alt, nb["sigma"], max_sigma)
        if not (isinstance(power, float) and math.isfinite(power)):
            nb["invalid"].append("the power is not finite")
        else:
            rec["power_nuisance"] = power
    oe = next((x for x in g.tests if x.name == "odd_even"), None)
    if oe is not None:
        rec["odd_even_battery"] = {
            "status": detail.get("odd_even", {}).get("status"),
            "metrics": {k: v for k, v in oe.metrics.items()
                        if isinstance(v, (int, float)) and ("err" in k or "sigma" in k)},
        }  # fmt: skip
    # the sinusoid's oracle residual (stage A's), kept apart from L: its failure never touches
    # the odd/even result (Codex's round 2)
    try:
        from refute.packs.tess.battery_v52 import HARMONICS

        domain = p4.v051.sinusoid_harmonic_max_period_days
        tested = [final.period * f for _, f in HARMONICS if final.period * f < domain]
        s_box = sa.sinusoid_bound(t, sector, final, tested, sigma_w, sigma_r, scale)
        rec["sinusoid_small_at_bound"] = 0.5 * math.erfc(
            -((sa.SMALL_FRACTION * depth / s_box) - sa.SMALL_Z) / math.sqrt(2.0)
        )
    except Exception as exc:  # noqa: BLE001 - recorded apart, never in E
        rec["sinusoid_error"] = repr(exc)
    return rec


def _raise_stop(why: str) -> None:
    """A binding stop, written once: every later shard skips its work."""
    OUT.mkdir(parents=True, exist_ok=True)
    try:
        with STOP_FILE.open("x", encoding="utf-8") as fh:
            fh.write(json.dumps({"why": why}) + "\n")
    except FileExistsError:
        pass


def shard(arg: dict) -> bytes:
    key = {"set": arg["set"], "index": arg["index"]}
    started = time.process_time()
    if STOP_FILE.exists():
        rec = {**key, "status": "SKIPPED", "reason": "a binding stop was raised"}
    else:
        try:
            rec = {**key, **one(arg), "status": "OK"}
        except Exception as exc:  # noqa: BLE001 - counted in E, never dropped
            rec = {**key, "status": "ERROR", "reason": repr(exc)}
        if rec["status"] == "ERROR":
            _raise_stop(f"an unexpected error in {key}")
        elif rec.get("mismatch"):
            _raise_stop(f"a rerun did not reproduce its record: {key}")
    rec["cpu_seconds"] = time.process_time() - started
    line = (json.dumps(rec, sort_keys=True, default=str) + "\n").encode()
    if len(line) > MAX_RECORD_BYTES // 2:
        line = (json.dumps({**key, "status": "ERROR", "reason": f"a record of {len(line)} bytes "
                            "above its bound"}, sort_keys=True) + "\n").encode()  # fmt: skip
        _raise_stop(f"an oversized record in {key}")
    return line


def i1_verified() -> str:
    """I4 runs only after I1's verified, stop-free result: the report matches I1's current
    fingerprint and its completed, verified part, covers all 206 cases with none skipped, and no
    stop exists in the report, the ledger or I1's stop file (Codex's round 3). Its SHA-256."""
    import i1_diagnose as i1

    ledger_i.assert_bound()
    if not I1_FILE.exists():
        raise SystemExit("I1's result does not exist: I4 refused")
    doc = json.loads(I1_FILE.read_text("utf-8"))
    rows = i1.schedule()
    if doc.get("fingerprint") != i1.fingerprint(rows):
        raise SystemExit("I1's report is not from I1's current fingerprint: I4 refused")
    if doc.get("records") != len(rows) or len(rows) != 206:
        raise SystemExit("I1's report does not cover its 206 cases: I4 refused")
    if doc.get("stop") or doc.get("not_reproduced") or doc.get("errors"):
        raise SystemExit("I1's result carries a stop: I4 refused")
    if doc.get("skipped_after_a_stop") != 0 or i1.STOP_FILE.exists():
        raise SystemExit("I1 raised a binding stop: I4 refused")
    if "unresolved_stop" in ledger_i._rows().get(i1.PART, {}):
        raise SystemExit("I1's part has an unresolved stop: I4 refused")
    budgeted.assembled(
        ledger_i.SECTION,
        i1.PART,
        i1.OUT / doc["fingerprint"],
        i1.shard,
        rows,
        doc["fingerprint"],
        i1.WORKERS,
        pin=i1.PIN,
        max_shard_seconds=i1.MAX_SHARD_SECONDS,
    )  # fmt: skip  (a completed part, every shard verified by its sidecar; refused otherwise)
    return hashlib.sha256(I1_FILE.read_bytes()).hexdigest()


def fingerprint(rows: list) -> str:
    from refute.core.codehash import compute_code_hash

    h = hashlib.sha256(compute_code_hash().sha256.encode())
    h.update(bf.fingerprint("i4").encode())
    for path in (Path(__file__), HERE / "ledger_i.py", DESIGN, STAGE_A / "d2_bounds.py",
                 STAGE_B / "b1_b14.py", STAGE_B / "b1_d2d4_rest.py",
                 STAGE_B / "b1-composition.json",
                 ROOT / "docs/validation/v0.5.1/feasibility/forecast.py"):  # fmt: skip
        h.update(hashlib.sha256(path.read_bytes()).digest())
    h.update(json.dumps(rows, sort_keys=True, default=str).encode())
    h.update(i1_verified().encode())  # bound to I1's verified result
    return h.hexdigest()[:16]


def run() -> None:
    ledger_i.assert_bound()
    i1_verified()  # before any scheduling or mutation
    before = ledger_i.v052_ledger_sha256()
    try:
        rows = schedule()
        reserve = len(rows) * MAX_RECORD_BYTES + RUN_OVERHEAD_BYTES
        ledger_i.check_caps("i4 run", reserve_days=0.3, reserve_tokens=0, reserve_bytes=reserve)
        ledger_i.declare()
        fp = fingerprint(rows)
        ledger_i.refuse_new_identity(PART, fp, rows)
        cap = ledger_i.hard_cap(PART, WORKERS, MAX_SHARD_SECONDS)
        print(len(rows), "rows; hard cap", round(cap, 2), "CPU-h; fingerprint", fp, flush=True)
        state = budgeted.execute(
            ledger_i.SECTION, PART, OUT / fp, shard, rows, fp, WORKERS, pin=PIN,
            max_shard_seconds=MAX_SHARD_SECONDS, hard_cap_hours=cap,
        )  # fmt: skip
        print(state, flush=True)
        ledger_i.check_caps("i4 after the run", 0.0, 0)
    finally:
        if ledger_i.v052_ledger_sha256() != before:
            raise SystemExit("the v0.5.2 ledger changed: refused")
    if state != "complete":
        raise SystemExit(state)


def _read(rows: list, fp: str) -> tuple[list, str | None]:
    """The part's records; if ``budgeted.assembled`` refuses (a driver stop, missing shards), the
    verified shards only, read by the driver's own sidecar check, and the refusal (Codex's round 3:
    a stopped run still writes its report; nothing is reconciled or resumed to get it)."""
    import driver

    try:
        data = budgeted.assembled(
            ledger_i.SECTION, PART, OUT / fp, shard, rows, fp, WORKERS, pin=PIN,
            max_shard_seconds=MAX_SHARD_SECONDS,
        )  # fmt: skip
        return [json.loads(x) for x in data.decode().splitlines() if x.strip()], None
    except SystemExit as exc:
        run_ = driver.Run(OUT / fp, shard, rows, fp, 1.0, 1, pin=PIN,
                          max_shard_seconds=MAX_SHARD_SECONDS)  # fmt: skip
        recs = []
        for sid in run_._done():
            data_p = run_._paths(sid)[0]
            recs += [json.loads(x) for x in data_p.read_text("utf-8").splitlines() if x.strip()]
        return recs, f"the assembly was refused ({exc}); {len(recs)} of {len(rows)} verified"


def summarize() -> None:
    ledger_i.assert_bound()
    rows = schedule()
    fp = fingerprint(rows)
    recs, refusal = _read(rows, fp)
    mismatched = [r for r in recs if r["status"] == "OK" and r.get("mismatch")]
    skipped = [r for r in recs if r["status"] == "SKIPPED"]
    out: dict = {
        "label": "v0.5.4 I4: odd_even's bound with the transit shape as a nuisance (a bound "
        "under the generator's model; decides nothing by itself)",
        "method_status": "not_validated", "fingerprint": fp,
        "decision": "the maintainer's decision of 2026-11-12, 14:00, item 3 (#217)",
        "not_reproduced": [{"set": r["set"], "index": r["index"], "mismatch": r["mismatch"]}
                           for r in mismatched],
        "sets": {},
    }  # fmt: skip
    for name in ("fresh", "v052"):
        rs = [r for r in recs if r["set"] == name]
        valid = [r for r in rs if r["status"] == "OK" and not r.get("mismatch")
                 and not r["nuisance"]["invalid"] and "power_nuisance" in r]  # fmt: skip
        invalid = [r for r in rs if r not in valid]
        low = [r for r in valid if r["power_nuisance"] < REQUIRED]
        low_known = [r for r in rs if r.get("power_known_template") is not None
                     and r["power_known_template"] < REQUIRED]  # fmt: skip
        ratio = [r["nuisance"]["sigma"] / r["sigma_known_template"] for r in valid]
        out["sets"][name] = {
            "planets": len(rs), "valid": len(valid), "E": len(invalid), "L": len(low),
            "below_at_known_template": len(low_known),
            "E_reasons": [{"index": r["index"], "why": r.get("reason") or r.get("mismatch")
                           or r["nuisance"]["invalid"]} for r in invalid],
            "L_planets": sorted(r["index"] for r in low),
            "sigma_nuisance_over_known_template": {
                "min": min(ratio), "median": float(np.median(ratio)), "max": max(ratio)}
            if ratio else None,
            "sinusoid_below_at_oracle (apart, never in L)": sum(
                r.get("sinusoid_small_at_bound", 1.0) < REQUIRED for r in rs
                if r["status"] == "OK" and not r.get("mismatch")),
        }  # fmt: skip
    f = out["sets"]["fresh"]
    big_l, big_e = f["L"], f["E"]
    out["outcome"] = (
        "draft infeasibility of D2 (a stop for the maintainer)"
        if big_l >= NEEDED_LOSSES
        else "unresolved"
        if big_l + big_e >= NEEDED_LOSSES
        else "route"
    )
    out["stop"] = [refusal] if refusal else []
    out["skipped_after_a_stop"] = len(skipped)
    if STOP_FILE.exists():
        out["stop"].append("a binding stop: " + json.loads(STOP_FILE.read_text("utf-8"))["why"])
    if mismatched:
        out["stop"].append("a rerun did not reproduce its record")
    if big_l >= NEEDED_LOSSES:
        out["stop"].append("a draft infeasibility of D2")
    out["cpu_hours"] = round(ledger_i.part_consumption(PART), 4)
    OUT_FILE.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n", "utf-8", newline="\n")
    print(json.dumps({k: out[k] for k in ("outcome", "stop")} | {"fresh": {k: f[k] for k in (
        "L", "E", "valid", "below_at_known_template")}}, indent=1))  # fmt: skip
    if out["stop"]:
        raise SystemExit("STOP for the maintainer: " + "; ".join(out["stop"]))


if __name__ == "__main__":
    ledger_i.assert_bound()
    with ledger_i.Exclusive(f"i4 {' '.join(sys.argv[1:])}"):
        {"run": run, "summarize": summarize}[sys.argv[1]]()
