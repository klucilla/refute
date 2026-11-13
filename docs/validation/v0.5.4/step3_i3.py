"""v0.5.4, second half, step 3: the population version of I3 (#217; the maintainer's decision of
2026-11-12, night, item 4b; the frozen designs are ``docs/plans/v0.5.4-h2-step3-i3-population.md``
and ``v0.5.4-h2-step2-i3-increment.md``). ``method_status: not_validated``.

A new fatal density test on each curve: Λ = χ²_planet − χ²_binary (white-weighted least squares
near every half period of the found ephemeris; the planet family at the found period with the
catalog star's ±3σ effective-radius box; the binary family at the found period or twice it, with
a secondary), FAIL if Λ > τ, INCONCLUSIVE on a failed fit or under 2 events. τ* is calibrated on
fresh planets against step 2's strict budgets. At τ*, one-sided 95 % Clopper-Pearson ends with a
Bonferroni split over eight limits are computed on fresh evaluation planets and on B0's
binaries. Two parts under ``budgeted_v3``.

Usage (launched through ``launch_detached.py``): ``run planets``, ``run binaries``, then
``summarize``.
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import i4_bound  # noqa: E402,I001,F401  (stage A's and B's modules, then ledger_i, last)
from i4_bound import ROOT  # noqa: E402
import i4_rest as r1  # noqa: E402
import ledger_i  # noqa: E402
import budgeted  # noqa: E402
import budgeted_v3  # noqa: E402
import step4_b0_errors as s4  # noqa: E402  (B0's records through its reviewed reader)

b0 = s4.b0
PARTS = {"planets": "h2_step3_planets", "binaries": "h2_step3_binaries"}
ALLOCATIONS = {"planets": 7.7, "binaries": 5.0}  # 1.4 x the pilot's projection
OUT = ROOT / ".cache/v054/step3"
OUT_FILE = HERE / "h2-step3-i3.json"
DESIGNS = (ROOT / "docs/plans/v0.5.4-h2-step3-i3-population.md",
           ROOT / "docs/plans/v0.5.4-h2-step2-i3-increment.md")  # fmt: skip
PLANET_FAMILIES = ("P", "PG", "PV", "PA")
PER_SET = 150
PER_SHARD = 1  # one curve per shard: a checkpoint of many curves (step 4's lesson)
WORKERS = 12
PIN = tuple(range(8, 32, 2))
MAX_SHARD_SECONDS = 300.0  # one curve per shard (the pilot: about 17 CPU-s)
ALPHA = 0.05
LIMITS_IN_BAND = 8  # P: refuted, retention, SNR>=15; PG, PV, PA; EB1, EB2
MAX_ERROR_FRACTION = 0.05
FLOOR = 20  # C1's not_decidable_below
RESERVE_TOKENS = 250_000
PHASE_CPU_STOP = 0.8 * 50.0  # the phase's 80 % CPU barrier
PLAN_RESERVES = {"h2_step6": 6.0, "h2_step3_planets": 7.7, "h2_step3_binaries": 5.0}
B0_ELIGIBLE = {"EB1": 381, "EB2": 373}
D1_PASS = 0.95
SUMMARY_RESERVE_HOURS = 0.02
STRICT = {"P_refuted": 0.05, "P_retention": 0.05, "G_refuted": 0.10, "P15_inconclusive": 0.05}
STRICT_POINT = {"P_refuted": 0.025, "P_retention": 0.05, "G_refuted": 0.05,
                "P15_inconclusive": 0.05}  # fmt: skip
REASON = ("the maintainer's decision of 2026-11-12 (night), item 4b (#217): step 3, the population "
          "version of I3 (budgeted_v3)")  # fmt: skip


def seed(kind: str, family: str, i: int) -> int:
    return int(hashlib.sha256(f"refute-v054-i3-{kind}:{family}:{i}".encode()).hexdigest()[:16], 16)


def candidate_of(family: str, s: int):
    """B0's construction: C1's generator and v0.4's frozen candidate pipeline."""
    from refute.packs.tess.calib05 import c1
    from refute.packs.tess.calib05.plans import pair
    from refute.packs.tess.calib05.steps import v04_test_plan
    from refute.packs.tess.detrend import detrend
    from refute.packs.tess.pipeline import global_prewhitening
    from refute.packs.tess.search import search_period

    data, truth = c1.generate(family, s)
    p04, _ = pair(v04_test_plan(ROOT))
    flat = detrend(data.lc, p04.detrend)
    _, searched = global_prewhitening(data, p04, flat)
    cand = search_period(searched, p04.search).candidate
    eligible = cand is not None and float(cand.snr) >= p04.gauntlet.snr.min_snr
    return data, truth, flat, cand, eligible


def statistic(flat, cand) -> dict:
    """Λ = χ²_planet − χ²_binary on the cadences near every half period (white weights)."""
    from scipy.optimize import least_squares

    from refute.packs.tess.events import per_point_sigma, transit_mask

    fc, rt = b0.forecast, b0.d1_routes
    t, f = flat.time, flat.flux
    p, t0, dur = float(cand.period), float(cand.t0), float(cand.duration)
    sigma = per_point_sigma(flat, transit_mask(t, p, t0, dur))
    half = np.abs(np.mod(t - t0 + 0.25 * p, 0.5 * p) - 0.25 * p)
    near = (half <= 2.0 * dur) & np.isfinite(f) & np.isfinite(sigma) & (sigma > 0)
    events = np.unique(np.round((t[near] - t0) / p).astype(int))
    if events.size < 2:
        return {"outcome": "INCONCLUSIVE", "why": "fewer than 2 events with data"}
    tn, sn = t[near], sigma[near]
    out_mask = transit_mask(tn, p, t0, dur)
    level = float(np.median(f[near][~out_mask])) if np.any(~out_mask) else float(np.median(f[near]))
    y = (level - f[near]) / level
    sn = sn / level  # the errors in the same units
    depth0 = max(float(cand.depth), 1e-6)
    lo_r, hi_r = rt.effective_bounds(0.05, 0.05)

    def best(resid, starts, lower, upper, scale):
        found = None
        for x0 in starts:
            try:
                fit = least_squares(resid, x0, bounds=(lower, upper), x_scale=scale, max_nfev=400)
            except ValueError:
                continue
            if fit.success and np.isfinite(fit.cost) and (found is None or fit.cost < found.cost):
                found = fit
        return found

    def r_planet(x):
        depth, b, shift, radius, c = x
        return (fc.planet_model(tn, p, t0 + shift, depth, b, radius) + c - y) / sn

    starts_p = [[d, b, 0.0, r, 0.0] for b in (0.0, 0.3, 0.6, 0.85)
                for r in (lo_r + 0.25 * (hi_r - lo_r), lo_r + 0.75 * (hi_r - lo_r))
                for d in (depth0, 1.5 * depth0)]  # fmt: skip
    fp = best(r_planet, starts_p, [1e-7, 0.0, -0.1, lo_r, -1.0], [0.5, 1.2, 0.1, hi_r, 1.0],
              [depth0, 0.1, 0.005, 0.05, depth0])  # fmt: skip
    fits_b = []
    for factor in (1.0, 2.0):

        def r_binary(x, factor=factor):
            d, shift, dd, q, ratio, c = x
            truth = {
                "period_days": p * factor, "t0_btjd": t0 + shift, "depth": d,
                "duration_days": dd, "ingress_fraction": q, "secondary_ratio": ratio,
            }  # fmt: skip
            return (fc.binary_model(tn, truth) + c - y) / sn

        starts_b = [[depth0 * (2.0 if factor == 2.0 else 1.0), 0.0, dur, q, ratio, 0.0]
                    for ratio in (0.0, 0.5, 1.0) for q in (0.1, 0.3)]  # fmt: skip
        fb = best(r_binary, starts_b, [1e-7, -0.1, 0.5 * dur, 0.01, 0.0, -1.0],
                  [0.5, 0.1, 2.0 * dur, 0.5, 1.0, 1.0],
                  [depth0, 0.005, 0.1 * dur, 0.05, 0.1, depth0])  # fmt: skip
        if fb is not None:
            fits_b.append((fb, factor))
    if fp is None or not fits_b:
        return {"outcome": "INCONCLUSIVE", "why": "a fit failed"}
    fb, factor = min(fits_b, key=lambda x: x[0].cost)
    chi_p, chi_b = 2.0 * float(fp.cost), 2.0 * float(fb.cost)
    if not (math.isfinite(chi_p) and math.isfinite(chi_b)):
        return {"outcome": "INCONCLUSIVE", "why": "a non-finite chi-square"}
    return {"outcome": "MEASURED", "lambda": chi_p - chi_b, "chi2_planet": chi_p,
            "chi2_binary": chi_b, "alias": factor, "events": int(events.size),
            "cadences": int(near.sum())}  # fmt: skip


def one_planet(arg: dict) -> dict:
    s = seed(arg["kind"], arg["family"], arg["index"])
    rec = {"kind": arg["kind"], "family": arg["family"], "index": arg["index"]}
    data, truth, flat, cand, eligible = candidate_of(arg["family"], s)
    rec.update(eligible=bool(eligible), target_snr=float(truth["target_snr"]))
    if eligible:
        rec.update(statistic(flat, cand))
    return rec


def one_binary(arg: dict, item: dict) -> dict:
    s = int(item["seed"])
    rec = {"kind": "binary", "family": arg["family"], "index": item["index"]}
    data, truth, flat, cand, eligible = candidate_of(arg["family"], s)
    same = (cand is not None and abs(float(cand.period) / item["found"]["period_days"] - 1) < 1e-9
            and abs(float(cand.t0) - item["found"]["t0_btjd"]) < 1e-9)  # fmt: skip
    rec.update(eligible=bool(eligible), reproduces_b0=bool(same))
    if eligible and same:
        rec.update(statistic(flat, cand))
    return rec


def shard(arg: dict) -> bytes:
    lines = []
    if arg["kind"] == "binary":
        work = [(lambda item=item: one_binary(arg, item)) for item in arg["items"]]
    else:
        work = [(lambda i=i: one_planet({**arg, "index": i})) for i in arg["indices"]]
    for call in work:
        try:
            rec = call()
        except Exception as exc:  # noqa: BLE001 - recorded; a stop over 5 % of a family
            rec = {"kind": arg["kind"], "family": arg["family"], "status": "ERROR",
                   "reason": repr(exc)}  # fmt: skip
        lines.append(json.dumps(rec, sort_keys=True, default=float))
    return ("\n".join(lines) + "\n").encode()


def schedule(which: str) -> list:
    if which == "planets":
        rows = []
        for kind in ("cal", "eval"):
            for fam in PLANET_FAMILIES:
                for k in range(0, PER_SET, PER_SHARD):
                    rows.append((f"{kind}-{fam}-{k:03d}", {"kind": kind, "family": fam,
                                 "indices": list(range(k, k + PER_SHARD))}))  # fmt: skip
        return rows
    recs = s4.b0_records()
    rows = []
    for _, arg in s4.schedule(recs):
        for it in arg["items"]:  # one binary per shard
            item = {"index": it["index"], "seed": it["seed"], "found": it["found"]}
            rows.append((f"bin-{arg['family']}-{it['index']:04d}",
                         {"kind": "binary", "family": arg["family"], "items": [item]}))  # fmt: skip
    if sum(len(a["items"]) for _, a in rows) != 754:
        raise SystemExit("B0's eligible binaries are not 754: STOP")
    return rows


def fingerprint(which: str, rows: list) -> str:
    from refute.core.codehash import compute_code_hash

    h = hashlib.sha256(compute_code_hash().sha256.encode())
    for path in (Path(__file__), *DESIGNS, HERE / "ledger_i.py", HERE / "budgeted_v3.py",
                 HERE / "step4_b0_errors.py", b0.FEAS / "forecast.py", b0.FEAS / "d1_routes.py",
                 s4.B0_RECORD):  # fmt: skip
        h.update(hashlib.sha256(path.read_bytes()).digest())
    h.update(which.encode())
    h.update(json.dumps(rows, sort_keys=True, default=str).encode())
    return h.hexdigest()[:16]


def _pending_reserve(part: str) -> float:
    """The CPU the plan's other parts may still use: a part not declared, its planned
    allocation; a declared one, its allocation less its consumption (whether it completed or
    stopped), so a reserve never vanishes on a declaration."""
    rows = ledger_i._rows()
    out = 0.0
    for other, planned in PLAN_RESERVES.items():
        if other == part:
            continue
        if other in rows:
            out += max(0.0, rows[other]["allocation_hours"] - ledger_i.part_consumption(other))
        else:
            out += planned
    return out


def _units(arg) -> int:
    return len(arg.get("items") or arg.get("indices"))


def run(which: str) -> None:
    ledger_i.assert_bound()
    part = PARTS[which]
    rows = schedule(which)
    fp = fingerprint(which, rows)
    ledger_i.check_caps(f"step3 {which} run", reserve_days=0.3, reserve_tokens=RESERVE_TOKENS,
                        in_h1=False, reserve_bytes=len(rows) * 30_000 + 50_000_000)  # fmt: skip
    with ledger_i.Exclusive(f"step3 {which} run"):
        # the phase's 80 % CPU barrier, read under the run's lock: the margin left after the
        # consumption, the plan's other parts, one interrupted batch's charge and the charges'
        # room (Codex, h2-step3 round 3, the conservative option)
        crash = WORKERS * (MAX_SHARD_SECONDS + 20.0) / 3600.0
        charges_room = max(0.0, ledger_i.CHARGES_ROOM - ledger_i._charges())
        margin = PHASE_CPU_STOP - ledger_i.spent() - _pending_reserve(part) - crash - charges_room
        if part in ledger_i._rows():
            margin += ledger_i.part_consumption(part)  # a resume: its own spent is in spent()
        if ALLOCATIONS[which] > margin:
            raise SystemExit(f"the phase's 80 % CPU barrier: a margin of {margin:.2f} CPU-h for "
                             f"{ALLOCATIONS[which]}: a STOP")  # fmt: skip
        if part not in ledger_i._rows():
            ledger_i._transfer("h2_unallocated", part, ALLOCATIONS[which], REASON)
        ledger_i.refuse_new_identity(part, fp, rows)
        cap = min(ledger_i.hard_cap(part, WORKERS, MAX_SHARD_SECONDS),
                  (margin - ledger_i.part_consumption(part)) / ledger_i.OVERSHOOT)  # fmt: skip
        if cap <= 0:
            raise SystemExit("no room under the phase's 80 % CPU barrier: a STOP")
        print(f"{part}: {len(rows)} shards; hard cap {cap:.3f} CPU-h; fp {fp}", flush=True)
        state = budgeted_v3.execute(
            ledger_i.SECTION, part, OUT / which / fp, shard, rows, fp, WORKERS, pin=PIN,
            max_shard_seconds=MAX_SHARD_SECONDS, hard_cap_hours=cap, pause_at=r1.PAUSE_AT,
            units=_units,
        )  # fmt: skip
    print(state, flush=True)
    ledger_i.check_caps(f"step3 {which} after the run", 0.0, 0, in_h1=False)
    if state != "complete":
        raise SystemExit(f"STOP for the maintainer: {state}")


def clopper_upper(k: int, n: int, alpha: float) -> float:
    from scipy.stats import beta

    return 1.0 if k >= n else float(beta.ppf(1.0 - alpha, k + 1, n - k))


def _records(which: str) -> list:
    rows = schedule(which)
    fp = fingerprint(which, rows)
    data = budgeted.assembled(ledger_i.SECTION, PARTS[which], OUT / which / fp, shard, rows, fp,
                              WORKERS, pin=PIN, max_shard_seconds=MAX_SHARD_SECONDS)  # fmt: skip
    return [json.loads(x) for x in data.decode().splitlines() if x.strip()]


def _rates(recs: list, tau: float) -> dict:
    """Per family: eligible n, fatal FAILs, INCONCLUSIVE, and INCONCLUSIVE in SNR ≥ 15."""
    out = {}
    for fam in PLANET_FAMILIES:
        el = [
            r
            for r in recs
            if r["family"] == fam and (r.get("eligible") or r.get("status") == "ERROR")
        ]  # an error counts as lost
        fail = sum(r.get("outcome") == "MEASURED" and r["lambda"] > tau for r in el)
        inc = sum(r.get("outcome") == "INCONCLUSIVE" or r.get("status") == "ERROR" for r in el)
        hi = [r for r in el if r.get("target_snr", 0) >= 15.0 or r.get("status") == "ERROR"]
        inc15 = sum(r.get("outcome") == "INCONCLUSIVE" or r.get("status") == "ERROR" for r in hi)
        out[fam] = {"n": len(el), "fail": fail, "inconclusive": inc, "n15": len(hi),
                    "inconclusive15": inc15}  # fmt: skip
    return out


def _budgets_hold(rates: dict, upper: bool) -> bool:
    a = ALPHA / LIMITS_IN_BAND

    def frac(k, n):
        return clopper_upper(k, n, a) if upper else (k / n if n else 1.0)

    lim = STRICT if upper else STRICT_POINT
    p = rates["P"]
    ok = (frac(p["fail"], p["n"]) <= lim["P_refuted"]
          and frac(p["fail"] + p["inconclusive"], p["n"]) <= lim["P_retention"]
          and frac(p["inconclusive15"], p["n15"]) <= lim["P15_inconclusive"])  # fmt: skip
    for fam in ("PG", "PV", "PA"):
        g = rates[fam]
        ok = ok and frac(g["fail"], g["n"]) <= lim["G_refuted"]
    return ok


def _whole(rates: dict) -> bool:
    """C1's whole allowances (point and upper criteria), for information only: P REFUTED point
    <= 0.05 and upper <= 0.10; P retention cost upper <= 0.10; P SNR >= 15 INCONCLUSIVE upper
    <= 0.30; PG, PV, PA REFUTED point <= 0.10 and upper <= 0.20."""
    a = ALPHA / LIMITS_IN_BAND
    p = rates["P"]

    def point(k, n):
        return k / n if n else 1.0

    ok = (point(p["fail"], p["n"]) <= 0.05
          and clopper_upper(p["fail"], p["n"], a) <= 0.10
          and clopper_upper(p["fail"] + p["inconclusive"], p["n"], a) <= 0.10
          and clopper_upper(p["inconclusive15"], p["n15"], a) <= 0.30)  # fmt: skip
    for fam in ("PG", "PV", "PA"):
        g = rates[fam]
        ok = ok and point(g["fail"], g["n"]) <= 0.10 and clopper_upper(g["fail"], g["n"], a) <= 0.20
    return ok


def _separation(cal: list, binaries: list) -> list:
    """Descriptive only (no inference over the deciles): P's REFUTED fraction and each binary
    family's rejected fraction over τ at the calibration Λ deciles, with the decision's
    conservative denominators (a planet error stays in P's denominator, not rejected; every binary
    of B0's frozen population stays, a non-measured one not rejected)."""
    lam = [r["lambda"] for r in cal if r.get("outcome") == "MEASURED"]
    if not lam:
        return []
    p_den = [
        r for r in cal if r["family"] == "P" and (r.get("eligible") or r.get("status") == "ERROR")
    ]
    out = []
    for q in np.quantile(lam, np.linspace(0.0, 1.0, 11)):
        row = {"tau": float(q)}
        row["P_rejected"] = sum(r.get("outcome") == "MEASURED" and r["lambda"] > q
                                for r in p_den) / max(len(p_den), 1)  # fmt: skip
        for fam in ("EB1", "EB2"):
            den = [r for r in binaries if r["family"] == fam]
            measured = [
                r for r in den
                if r.get("eligible") and r.get("reproduces_b0") and r.get("outcome") == "MEASURED"
            ]  # fmt: skip
            rej = sum(r["lambda"] > q for r in measured)
            row[f"{fam}_rejected"] = rej / max(len(den), 1)
        out.append(row)
    return out


def summarize() -> None:
    import time
    import uuid

    ledger_i.assert_bound()
    ledger_i.check_caps("step3 summarize", reserve_days=0.05, reserve_tokens=0, in_h1=False)
    room = ledger_i.CHARGES_ROOM - ledger_i._charges()
    if room < SUMMARY_RESERVE_HOURS:
        raise SystemExit(f"the charges' room ({room:.3f} CPU-h) cannot hold the summary: STOP")
    started = time.process_time()
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()) + "-" + uuid.uuid4().hex[:12]
    try:
        doc = _summarize()
    finally:
        hours = (time.process_time() - started) / 3600.0
        ledger_i.charge(f"h2_step3_summarize_{stamp}", hours,
                        "the summary's own CPU, outside the driver")  # fmt: skip
    text = json.dumps(doc, indent=1, sort_keys=True) + chr(10)
    OUT_FILE.write_text(text, "utf-8", newline=chr(10))
    print(json.dumps({k: doc.get(k) for k in ("tau_star", "outcome", "stops")}, indent=1))
    if doc["stops"]:
        raise SystemExit("STOP for the maintainer: " + "; ".join(doc["stops"]))


def _summarize() -> dict:
    planets, binaries = _records("planets"), _records("binaries")
    cal = [r for r in planets if r.get("kind") == "cal"]
    ev = [r for r in planets if r.get("kind") == "eval"]
    stops = []
    for name, group, fams in (("cal", cal, PLANET_FAMILIES), ("eval", ev, PLANET_FAMILIES),
                              ("binaries", binaries, ("EB1", "EB2"))):  # fmt: skip
        for fam in fams:
            rows = [r for r in group if r.get("family") == fam]
            errs = sum(r.get("status") == "ERROR" for r in rows)
            if rows and errs > MAX_ERROR_FRACTION * len(rows):
                stops.append(f"{name} {fam}: {errs} of {len(rows)} raised an error")
            if sum(bool(r.get("eligible")) for r in rows) < FLOOR:
                stops.append(f"{name} {fam}: fewer than {FLOOR} eligible curves")
    not_repro = sum(
        bool(r.get("kind") == "binary" and r.get("eligible") and not r.get("reproduces_b0"))
        for r in binaries
    )  # counted as not rejected, never a stop (the design)
    doc: dict = {
        "label": "v0.5.4 step 3: the population version of I3 (a new fatal density test's "
        "separation under step 2's rule; never a negative result or a draft)",
        "method_status": "not_validated",
        "decision": "the maintainer's decision of 2026-11-12 (night), item 4b (#217)",
        "designs": [str(d.relative_to(ROOT)).replace(chr(92), "/") for d in DESIGNS],
        "stops": stops,
        "binaries_not_reproducing_b0 (counted as not rejected)": not_repro,
        "cpu_hours": {w: round(ledger_i.part_consumption(p), 4) for w, p in PARTS.items()},
    }
    if stops:
        doc.update(tau_star=None, outcome="INCONCLUSIVE (a stop)")
        return doc
    lam = sorted({r["lambda"] for r in cal if r.get("outcome") == "MEASURED"})
    tau_star = next((tau for tau in lam if _budgets_hold(_rates(cal, tau), upper=False)), None)
    if tau_star is None:
        doc.update(tau_star=None, outcome="INCONCLUSIVE (no threshold meets the strict budgets "
                   "on the calibration planets)")  # fmt: skip
        return doc
    from scipy.stats import binom

    rates = _rates(ev, tau_star)
    a = ALPHA / LIMITS_IN_BAND
    planets_ok = _budgets_hold(rates, upper=True)
    bin_side = {}
    b0recs = s4.b0_records()
    for fam in ("EB1", "EB2"):
        # B0's frozen eligible population: an error or a non-reproduction counts as not rejected
        el = [r for r in binaries if r["family"] == fam]
        if len(el) != B0_ELIGIBLE[fam]:
            raise SystemExit(f"{fam}: {len(el)} binaries, not {B0_ELIGIBLE[fam]}: STOP")
        rejected = sum(
            bool(r.get("eligible") and r.get("reproduces_b0") and r.get("outcome") == "MEASURED")
            and r["lambda"] > tau_star
            for r in el
        )
        kept = len(el) - rejected
        attempted = sum(r["family"] == fam for r in b0recs)
        n_proj = round(b0.C1_PRIME_PER_FAMILY * len(el) / attempted) if attempted else 0
        k = b0.forecast.max_count(n_proj)
        up = clopper_upper(kept, len(el), a)
        pass_probability = float(binom.cdf(k, n_proj, up))
        bin_side[fam] = {
            "eligible": len(el), "not_rejected": kept, "upper": up, "projection": n_proj,
            "allowance": k, "pass_probability_at_upper": pass_probability,
            "meets_d1": pass_probability >= D1_PASS,
        }  # fmt: skip
    # both families must hold at once: the conservative bound 1 - sum(1 - p_f) >= 0.95
    joint = 1.0 - sum(1.0 - b["pass_probability_at_upper"] for b in bin_side.values())
    for b in bin_side.values():
        b["meets_d1_alone"] = b.pop("meets_d1")
    route = planets_ok and joint >= D1_PASS
    doc.update({
        "tau_star": tau_star, "calibration_rates": _rates(cal, tau_star),
        "evaluation_rates": rates, "planet_budgets_hold_at_upper_ends": planets_ok,
        "binaries": bin_side,
        "d1_joint_pass_probability_lower_bound": joint,
        "outcome": "route (by this test alone, under step 2's strict budgets)" if route
        else "INCONCLUSIVE",
        "warning_class_note": "Λ > τ* as a warning (WEAKENED) is for the maintainer's step 8",
        "band": f"one-sided Clopper-Pearson at 1 - {ALPHA}/{LIMITS_IN_BAND} per limit (8 limits)",
        "whole_allowance_budgets_hold_at_upper_ends": _whole(rates),
        "separation": _separation(cal, binaries),
        "scope": "PASS means non-rejection: the new test has no sensitivity block, so its "
        "INCONCLUSIVE is understated and a route stays conditional on that; the binary side "
        "assumes the other tests reject nothing; never a negative result or a draft",
    })  # fmt: skip
    return doc


if __name__ == "__main__":
    if budgeted.LEDGER != ledger_i.HERE / "ledger.json":
        raise SystemExit("budgeted is not pointed at v0.5.4's ledger: refused")
    if sys.argv[1] == "run":
        run(sys.argv[2])
    else:
        summarize()
