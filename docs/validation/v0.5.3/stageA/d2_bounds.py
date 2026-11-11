"""v0.5.3 stage A, item (b): D2's bounds (#217; `docs/plans/v0.5.3-stageA-design.md`, section (b)).
**A what-if on development data; it decides nothing.** ``method_status: not_validated``. No change
to ``src/``, to any rule or to T2a's fingerprint.

**Two quantities, kept apart.** (1) The *evidence-qualified PASS* of a blocking test: could it PASS
with its declared sensitivity at a bound on attainable precision? (2) The *kept retention*: D2
counts WEAKENED as kept, so a warning test's INCONCLUSIVE is recoverable by a warning FAIL; only a
fatal blocker can be bounded as lost.

**What runs.** Every eligible D2 development planet that version 4 does not keep in
``forecast-v4.json`` (C1's generator and development seed, as ``forecast_v4.one``): its candidate
and version 4's attack at stage 2 are rebuilt (checked against the forecast's record), and for it:

- ``odd_even`` (fatal): the joint Fisher information ``F = X^T Σ^-1 X``, ``X``'s columns the true
  template's odd transits, its even transits (both times the generator's known multiplicative
  stellar trend) and one constant level per sector,
  ``Σ`` the generator's covariance (white plus each sector's exponential term, ``mahalanobis2`` of
  v0.5.1's WP1 and polarization for the cross terms); ``σ_oe = sqrt(c^T F^-1 c)``, ``c = (1, -1, 0,
  ...)``; its probability ``gaussian_probability(alternative, σ_oe, max_sigma)`` at the battery's
  own alternative (``odd_even_alternative_depth_fraction`` times the final candidate's depth),
  against the rule's 0.95. Assumptions: Gaussian noise with the generator's covariance; the true
  template; an unbiased estimator. It bounds that model, not "any estimator" in general.
- the sinusoid (warning; for the evidence-qualified PASS only): the oracle GLS standard error of the
  residual box depth, ``σ_box = sqrt([(Z^T Σ^-1 Z)^-1]_(box, box))``, ``Z`` the in-transit indicator
  of the final candidate's ephemeris, one level per sector and a cosine and a sine at each tested
  harmonic (the data-dependent extra frequencies left out, which can only lower ``σ_box``); then
  ``small = Φ(0.5 D / σ_box - 3)`` with ``D`` the final candidate's depth, against 0.95, the flag's
  power taken as 1. Necessary, not sufficient, for the joint sensitivity.

**The count** (``summarize``): the 112 eligible planets enumerated once. Kept retention's upper
bound: a planet is kept if version 4 keeps it, or if every one of its blockers (a decisive test,
INCONCLUSIVE or FAIL) is recoverable: a warning blocker always (a warning FAIL is WEAKENED); a
fatal ``odd_even`` blocker when its bound reaches the rule; a procedural refusal named by item (a)
(``a0-refusals.json``, bound to this script's fingerprint; a quarantined (a) record counts all its
blockers so), a blocker without a bound, a fatal FAIL of this estimator, or a quarantined record
optimistically. The population's uncertainty: the Wilson 95 % upper end of the kept fraction
against D2's requirement, v0.4's kept fraction minus 0.10; the sample's integer requirement (97 of
112) apart.

Usage: ``run`` through ``scripts/launch_affinity.ps1``, then ``summarize`` (``d2-bounds.json``).
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
import budgeted  # noqa: E402
import driver  # noqa: E402
import forecast_v4 as fv  # noqa: E402

PART = "b_d2_bound"
OUT = ledger_a.ROOT / ".cache/v053/stageA/d2-bounds"
WORKERS = 12
PIN = tuple(range(8, 32, 2))
MAX_SHARD_SECONDS = 1200.0
KEPT = ("SURVIVED", "WEAKENED")
REQUIRED = 0.95
SMALL_Z = 3.0  # ATTENUATION_SIGMAS
SMALL_FRACTION = 0.5  # ATTENUATION_FRACTION


def _wp1():
    sys.path.insert(0, str(ledger_a.ROOT / "docs/validation/v0.5.1/feasibility"))
    import forecast as wp1

    return wp1


def d2_old() -> dict:
    data = driver.Run(fv.OUT / fv.fingerprint(), fv.shard, fv.shards(), fv.fingerprint(), 1.0, 1,
                      pin=fv.PIN, max_shard_seconds=fv.MAX_SHARD_SECONDS).assemble()  # fmt: skip
    recs = [json.loads(x) for x in data.decode().splitlines() if x.strip()]
    return {r["index"]: r for r in recs}


def eligible(old: dict) -> list[dict]:
    rows = [
        r for r in old.values() if r.get("status") == "OK" and r["gate_passed"] and r["identity"]
    ]
    if len(rows) != 112:
        raise SystemExit(f"not the 112 eligible planets: {len(rows)}")
    return sorted(rows, key=lambda r: r["index"])


def schedule() -> list:
    return [(f"b-{r['index']:05d}", r["index"]) for r in eligible(d2_old()) if r["v4"] not in KEPT]


def gram(t, sector, columns, sigma_w, sigma_r) -> np.ndarray:
    """``Z^T Σ^-1 Z`` by polarization of ``mahalanobis2`` (u^T Σ^-1 u)."""
    m = _wp1().mahalanobis2
    k = len(columns)
    g = np.zeros((k, k))
    for i in range(k):
        g[i, i] = m(t, sector, columns[i], sigma_w, sigma_r)
        for j in range(i + 1, k):
            plus = m(t, sector, columns[i] + columns[j], sigma_w, sigma_r)
            minus = m(t, sector, columns[i] - columns[j], sigma_w, sigma_r)
            g[i, j] = g[j, i] = (plus - minus) / 4.0
    return g


def trend_multiplier(t, truth) -> np.ndarray:
    """The generator's known multiplicative stellar trend (``c1._noisy``), 1 without one."""
    tr = truth.get("trend")
    if not tr:
        return np.ones_like(t)
    return 1.0 + tr["amplitude"] * np.sin(2 * np.pi * t / tr["period_days"] + tr["phase"])


def sector_scale(sector, flux) -> np.ndarray:
    """Each cadence's sector median of the flux, the battery's per-sector normalizer: columns in
    normalized units times this scale give ``Z^T Σ_norm^-1 Z = (D Z)^T Σ^-1 (D Z)``."""
    out = np.empty(flux.size)
    for s in np.unique(sector):
        sel = sector == s
        out[sel] = float(np.median(flux[sel]))
    return out


def odd_even_bound(t, sector, truth, sigma_w, sigma_r, scale) -> float:
    from refute.packs.tess import synthetic as syn

    p, t0 = truth["period_days"], truth["t0_btjd"]
    unit = syn.trapezoid(t, p, t0, 1.0, truth["duration_days"], truth["ingress_fraction"])
    unit = unit * trend_multiplier(t, truth)
    epoch = np.round((t - t0) / p).astype(int)
    cols = [np.where(epoch % 2 != 0, -unit, 0.0), np.where(epoch % 2 == 0, -unit, 0.0)]
    cols += [(sector == s).astype(float) for s in np.unique(sector)]
    # the columns are raw physical derivatives (template times trend): no normalizer here
    f = gram(t, sector, cols, sigma_w, sigma_r)
    c = np.zeros(len(cols))
    c[0], c[1] = 1.0, -1.0
    return float(math.sqrt(c @ np.linalg.solve(f, c)))


def sinusoid_bound(t, sector, candidate, harmonics, sigma_w, sigma_r, scale) -> float:
    """The residual box is additive in normalized flux (``box_after_model``): normalized columns,
    converted by each sector's median, a fixed normalizer (an oracle assumption)."""
    dt = np.abs(np.mod(t - candidate.t0 + 0.5 * candidate.period, candidate.period)
                - 0.5 * candidate.period)  # fmt: skip
    cols = [-(dt <= candidate.duration / 2.0).astype(float)]
    cols += [(sector == s).astype(float) for s in np.unique(sector)]
    for period in harmonics:
        phase = 2.0 * math.pi * t / period
        cols += [np.cos(phase), np.sin(phase)]
    g = gram(t, sector, [c * scale for c in cols], sigma_w, sigma_r)
    return float(math.sqrt(np.linalg.inv(g)[0, 0]))


def one(i: int, rec: dict) -> None:
    from refute.core.sensitivity import enforce_sensitivity
    from refute.packs.tess.battery_v52 import HARMONICS
    from refute.packs.tess.calib05 import c1
    from refute.packs.tess.detrend import detrend
    from refute.packs.tess.pipeline import attack_candidate, global_prewhitening
    from refute.packs.tess.power import gaussian_probability, registry_for
    from refute.packs.tess.search import search_period

    data, truth = c1.generate("P", c1.development_seed("P", i))
    p04, _, p4 = fv.plans()
    flat = detrend(data.lc, p04.detrend)
    pw, searched = global_prewhitening(data, p04, flat)
    cand = search_period(searched, p04.search).candidate
    g = attack_candidate(data, cand, p4, None, None, pw)
    rec["v4"], rec["v4_tests"] = fv._verdict(g.tests, p4)
    final = g.candidate
    rec["severity"] = {t.name: t.severity.value for t in g.tests}
    after = {t.name: t for t in enforce_sensitivity(list(g.tests), registry_for(p4))}
    sigma_w = truth["sigma_white_ppm"] * 1e-6
    sigma_r = sigma_w / 2.0 if truth["correlated"] else 0.0
    t, sector = data.lc.time, data.lc.sector
    scale = sector_scale(sector, data.lc.flux)
    depth = float(final.depth)
    rec["final_candidate"] = {"period": final.period, "t0": final.t0, "duration": final.duration,
                              "depth": depth, "snr": final.snr}  # fmt: skip
    rec["truth"] = {k: truth[k] for k in ("depth", "target_snr", "correlated", "sigma_white_ppm",
                                          "trend")}  # fmt: skip
    oe = after.get("odd_even")
    alt = p4.stronger.odd_even_alternative_depth_fraction * depth
    s_oe = odd_even_bound(t, sector, truth, sigma_w, sigma_r, scale)
    rec["odd_even"] = {
        "status": oe.status.value if oe else None,
        "message": oe.message if oe else None,
        "sigma_bound_ppm": s_oe * 1e6,
        "alternative_ppm": alt * 1e6,
        "probability_at_bound": gaussian_probability(alt, s_oe, p4.gauntlet.odd_even.max_sigma),
        "a0_probability": ((oe.sensitivity or {}).get("main") or {}).get("probability") if oe
        else None,
    }  # fmt: skip
    domain = p4.v051.sinusoid_harmonic_max_period_days  # check_sinusoid's ``cp`` is plan.v051
    tested = [final.period * f for _, f in HARMONICS if final.period * f < domain]
    s_box = sinusoid_bound(t, sector, final, tested, sigma_w, sigma_r, scale)
    small = 0.5 * math.erfc(-((SMALL_FRACTION * depth / s_box) - SMALL_Z) / math.sqrt(2.0))
    sn = after.get("sinusoid")
    rec["sinusoid"] = {
        "status": sn.status.value if sn else None,
        "sigma_box_bound_ppm": s_box * 1e6,
        "small_at_bound": small,
        "tested_periods": tested,
    }


def shard(i: int) -> bytes:
    started = time.process_time()
    rec: dict = {"index": i}
    try:
        one(i, rec)
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
        fv.HERE / "forecast_v4.py",
        fv.HERE / "budgeted.py",
        fv.HERE / "driver.py",
        ledger_a.ROOT / "docs/validation/v0.5.1/feasibility/forecast.py",
        REFUSALS,
    ):
        h.update(hashlib.sha256(path.read_bytes()).digest())  # fmt: skip
    return h.hexdigest()[:16]


def run() -> None:
    before = ledger_a.v052_ledger_sha256()
    try:
        ledger_a.check_caps(reserve_days=0.3, reserve_tokens=0)
        ledger_a.declare()
        fp = fingerprint()
        rows = schedule()
        cap = ledger_a.hard_cap(PART, WORKERS, MAX_SHARD_SECONDS)
        print(len(rows), "planets; hard cap", round(cap, 2), "CPU-h", flush=True)
        state = budgeted.execute(
            ledger_a.SECTION, PART, OUT / fp, shard, rows, fp, WORKERS, pin=PIN,
            max_shard_seconds=MAX_SHARD_SECONDS, hard_cap_hours=cap,
        )  # fmt: skip
        print(state, flush=True)
    finally:
        if ledger_a.v052_ledger_sha256() != before:
            raise SystemExit("the v0.5.2 ledger changed: refused")
    if state != "complete":
        raise SystemExit(state)


def _wilson_upper(k: int, n: int, z: float = 1.959963984540054) -> float:
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return centre + half


REFUSALS = HERE / "a0-refusals.json"  # item (a)'s output, bound to this fingerprint
REFUSAL_MESSAGES = ("A0's errors are not available", "no calibrated error")


def _d2_refusals() -> dict[int, list[str]]:
    """Item (a)'s validated D2 records: the version 4 tests whose INCONCLUSIVE message is a
    procedural refusal of A0 or of the selection; a quarantined (a) record gives every test."""
    doc = json.loads(REFUSALS.read_text("utf-8"))
    out: dict[int, list[str]] = {}
    for r in doc["per_record"]:
        if r["record"].startswith("D2 "):
            out[int(r["record"][3:])] = [k for k, m in r["inconclusive_messages"].items()
                                         if m and m.startswith(REFUSAL_MESSAGES)]  # fmt: skip
    for rid in doc["quarantined"]:
        if rid.startswith("D2 "):
            out[int(rid[3:])] = ["*"]
    return out


def summarize() -> None:
    fp = fingerprint()
    rows = schedule()
    data = budgeted.assembled(
        ledger_a.SECTION, PART, OUT / fp, shard, rows, fp, WORKERS, pin=PIN,
        max_shard_seconds=MAX_SHARD_SECONDS,
    )  # fmt: skip
    recs = {r["index"]: r for r in (json.loads(x) for x in data.decode().splitlines() if x)}
    old = d2_old()
    el = eligible(old)
    v04_kept = sum(r["v04"] in KEPT for r in el)
    requirement = v04_kept / len(el) - 0.10
    refused = _d2_refusals()
    kept, evidence, per = 0, 0, []
    for r in el:
        if r["v4"] in KEPT:
            kept += 1
            continue
        b = recs.get(r["index"])
        row: dict = {"index": r["index"], "v04": r["v04"], "v4": r["v4"], "blockers": {}}
        quarantined = b is None or b["status"] != "OK" or b["v4"] != r["v4"] or b[
            "v4_tests"] != r["v4_tests"]  # fmt: skip
        recoverable, qualified = True, True
        for name, st in r["v4_tests"].items():
            if st["status"] not in ("INCONCLUSIVE", "FAIL") or name not in DECISIVE:
                continue
            sev = (b or {}).get("severity", {}).get(name, "fatal")
            # an absent or failed (a) diagnosis is unknown: counted optimistically ("*")
            classification = refused.get(r["index"], ["*"])
            procedural = name in classification or "*" in classification
            if st["status"] == "FAIL":
                ok, how = None, "a FAIL of this estimator (no bound; counted optimistically)"
            elif procedural:
                ok, how = None, "a procedural refusal (item (a)); counted optimistically"
            elif name == "odd_even" and b and not quarantined:
                ok = b["odd_even"]["probability_at_bound"] >= REQUIRED
                how = f"odd_even bound {b['odd_even']['probability_at_bound']:.3f}"
            elif name == "sinusoid" and b and not quarantined:
                ok = b["sinusoid"]["small_at_bound"] >= REQUIRED
                how = f"sinusoid small at bound {b['sinusoid']['small_at_bound']:.3f}"
            else:
                ok, how = None, "no bound"
            rec_kept = sev == "warning" or ok is not False
            row["blockers"][name] = {"status": st["status"], "severity": sev, "bound": how,
                                     "evidence_pass_possible": ok,
                                     "recoverable_for_kept": rec_kept}  # fmt: skip
            recoverable &= rec_kept
            qualified &= ok is not False
        row["quarantined"] = quarantined
        row["kept_upper_bound"] = recoverable
        row["evidence_upper_bound"] = qualified
        kept += recoverable
        evidence += qualified
        per.append(row)
    n = len(el)
    v4_kept = sum(r["v4"] in KEPT for r in el)
    out = {
        "label": "D2's bounds; a what-if, decides nothing (#217, stage A (b))",
        "method_status": "not_validated",
        "fingerprint": fp,
        "eligible": n,
        "v04_kept": v04_kept,
        "v4_kept": v4_kept,
        "requirement_population": requirement,
        "requirement_sample": math.ceil(requirement * n - 1e-12),
        "kept_upper_bound": kept,
        "kept_upper_bound_wilson95_upper": _wilson_upper(kept, n),
        "evidence_qualified_upper_bound": v4_kept + evidence,
        "assumptions": [
            "odd_even: Gaussian noise with the generator's covariance (white plus each sector's "
            "exponential term), the true template, an unbiased estimator",
            "sinusoid: the oracle GLS residual box under the generator's covariance, tested "
            "harmonics only, the flag's power taken as 1; necessary, not sufficient",
            "warning blockers recoverable for kept retention; refusals, blockers without a "
            "bound, fatal FAILs of this estimator and quarantined records counted optimistically",
        ],
        "per_planet": per,
    }
    (HERE / "d2-bounds.json").write_text(json.dumps(out, indent=1, sort_keys=True, default=str)
                                         + "\n", "utf-8")  # fmt: skip
    print(json.dumps({k: v for k, v in out.items() if k != "per_planet"}, indent=1))


DECISIVE = (
    "aperture_depth",
    "duty_cycle",
    "edge_events",
    "nearby_contamination",
    "odd_even",
    "period_alias",
    "plausibility",
    "secondary_eclipse",
    "sinusoid",
    "snr",
    "systematics",
)

if __name__ == "__main__":
    {"run": run, "summarize": summarize}[sys.argv[1]]()
