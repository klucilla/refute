"""v0.5.3 stage B, B0: the information bound of D1 for EB1 and EB2, a diagnostic (#217; the
maintainer's decision of 2026-11-11; `docs/plans/v0.5.3-stageB0-design.md`, sections 3 and 4).
**Development seeds only; it decides nothing by itself and no test is built from it.**
``method_status: not_validated``.

For each development binary (seeds ``refute-v053-b0:<family>:<i>``, i in 0 to 399, EB1 and EB2;
none used before): the frozen C1 generator, the frozen v0.4 candidate generation (detrending,
global prewhitening, search; ``calib05.plans.pair`` on the v0.4 claim's test plan), and v0.5.1's
forecast eligibility (the search candidate's SNR at least the gate's ``min_snr``; an approximation
of C1's gate, stated in the design). For each eligible binary, v0.5.1's oracle, imported
unchanged: the planet at the found period nearest to the noiseless binary
(``d1_routes.nearest_with_bounds``: depth, impact parameter 0 to 1.2, epoch shift, the star's
effective radius ``R / M^(1/3)`` within the 3-sigma bounds of ``d1_routes.effective_bounds``),
and the Mahalanobis distance ``d`` of the two noiseless curves, each multiplied by the star's known
trend factor as C1 applies it (Codex's round 1), under the generator's covariance
(``forecast.mahalanobis2``). Two stars: ``catalog`` (radius and mass errors 5 % each) and
``star_known`` (no error).

**The reading** (fixed before the run; the design's section 4): a binary's non-rejection
probability at a planet false-failure level ``alpha`` is ``Phi(z_alpha - d)``. Per family: the
attempted curves, the eligible count, the C1' projection ``n' = round(200 x eligible /
attempted)``, D1's allowance at ``n'``, the expected non-rejected count at ``n'`` and the
Poisson-binomial probability of at most the allowance over 2,000 bootstrap cohorts of ``n'``
(seed 20261111; a forecast, not a confidence interval). The outcome A, B, C or D of the design's
section 4 is computed here.

Usage: ``run`` through ``scripts/launch_affinity.ps1``, then ``summarize`` (``d1-bound.json``).
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
import time
from pathlib import Path
from statistics import NormalDist

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ledger_b  # noqa: E402,I001  (before budgeted: it points the ledger at stage B's)
import budgeted  # noqa: E402

FEAS = ledger_b.ROOT / "docs/validation/v0.5.1/feasibility"
sys.path.insert(0, str(FEAS))
import d1_routes  # noqa: E402
import forecast  # noqa: E402

DESIGN = ledger_b.ROOT / "docs/plans/v0.5.3-stageB0-design.md"
PART = "b0_bound"
OUT = ledger_b.ROOT / ".cache/v053/stageB/d1-bound"
WORKERS = 12
PIN = tuple(range(8, 32, 2))
MAX_SHARD_SECONDS = 1200.0
PER_SHARD = 10
SIZE = 400
FAMILIES = ("EB1", "EB2")
STARS = {"catalog": (0.05, 0.05), "star_known": (0.0, 0.0)}
ALPHAS = (0.05, 0.01, 0.0027, 0.00135)
PRIMARY_ALPHA = 0.0027
C1_PRIME_PER_FAMILY = 200
BOOTSTRAP = 2000
BOOTSTRAP_SEED = 20261111
MIN_ELIGIBLE = 150  # outcome D below this, per family
A_PASS_PROBABILITY = 0.05  # outcome A: the median cohort's pass probability below this


def seed(family: str, i: int) -> int:
    return int(hashlib.sha256(f"refute-v053-b0:{family}:{i}".encode()).hexdigest()[:16], 16)


def trend_factor(family: str, s: int, t: np.ndarray) -> np.ndarray:
    """The multiplicative trend C1 applies to the model (``c1._noisy``): the star is drawn again
    from the generator's own first draws (``c1.generate`` calls ``_draw_star`` first)."""
    from refute.packs.tess.calib05 import c1

    star = c1._draw_star(family, s, np.random.default_rng(s))
    if star.trend is None:
        return np.ones_like(t)
    tr = star.trend
    return 1.0 + tr["amplitude"] * np.sin(2 * np.pi * t / tr["period_days"] + tr["phase"])


def bound_one(family: str, i: int) -> dict:
    from refute.packs.tess.calib05 import c1
    from refute.packs.tess.calib05.plans import pair
    from refute.packs.tess.calib05.steps import v04_test_plan
    from refute.packs.tess.detrend import detrend
    from refute.packs.tess.pipeline import global_prewhitening
    from refute.packs.tess.search import search_period

    started = time.process_time()
    s = seed(family, i)
    rec: dict = {"family": family, "index": i, "seed": str(s)}
    try:
        data, truth = c1.generate(family, s)
    except c1.GenerationFailedError as exc:
        return {**rec, "status": "GENERATION_FAILURE", "reason": str(exc),
                "cpu_seconds": time.process_time() - started}  # fmt: skip
    p04, _ = pair(v04_test_plan(ledger_b.ROOT))
    flat = detrend(data.lc, p04.detrend)
    _, searched = global_prewhitening(data, p04, flat)
    cand = search_period(searched, p04.search).candidate
    snr = None if cand is None else float(cand.snr)
    eligible = snr is not None and snr >= p04.gauntlet.snr.min_snr
    true_period = truth.get("true_period_days") or truth["period_days"]
    ratio = truth["secondary_ratio"]
    rec.update(
        status="OK",
        eligible=bool(eligible),
        search_snr=snr,
        correlated=bool(truth["correlated"]),
        secondary_ratio=ratio,
        target_snr=truth["target_snr"],
        impact=truth["impact"],
        depth=truth["depth"],
        mean_depth=truth["depth"] * (1.0 + ratio) / 2.0,
        true_period_days=true_period,
    )
    if eligible:
        found = {"period_days": cand.period, "t0_btjd": cand.t0}
        rec["found"] = found
        rec["folded"] = abs(cand.period / true_period - 0.5) < 0.02
        t, sector = data.lc.time, data.lc.sector
        factor = trend_factor(family, s, t)
        sigma_w = truth["sigma_white_ppm"] * 1e-6
        sigma_r = sigma_w / 2.0 if truth["correlated"] else 0.0
        for name, (sr, sm) in STARS.items():
            bounds = d1_routes.effective_bounds(sr, sm)
            radius, r, at_bound = d1_routes.nearest_with_bounds(
                forecast, t, truth, found, sr, bounds
            )
            d = math.sqrt(forecast.mahalanobis2(t, sector, r * factor, sigma_w, sigma_r))
            rec[name] = {"distance": d, "effective_radius": radius, "at_bound": bool(at_bound)}
    rec["cpu_seconds"] = time.process_time() - started
    return rec


def schedule() -> list:
    """Shards of ``PER_SHARD`` indices, the families alternating, so that the 5 % checkpoint holds
    both families; checked."""
    rows = []
    starts = range(0, SIZE, PER_SHARD)
    chunks = {f: [list(range(k, k + PER_SHARD)) for k in starts] for f in FAMILIES}
    for j in range(len(starts)):
        for f in FAMILIES:
            c = chunks[f][j]
            rows.append((f"{f}-{c[0]:04d}", {"family": f, "indices": c}))
    probe = {arg["family"] for _, arg in budgeted.checkpoint(rows)}
    if probe != set(FAMILIES):
        raise SystemExit(f"the checkpoint does not cover both families: {sorted(probe)}")
    return rows


def shard(arg: dict) -> bytes:
    lines = []
    for i in arg["indices"]:
        try:
            rec = bound_one(arg["family"], i)
        except Exception as exc:  # noqa: BLE001 - recorded, never dropped
            rec = {"family": arg["family"], "index": i, "status": "ERROR", "reason": repr(exc)}
        lines.append(json.dumps(rec, sort_keys=True, default=str))
    return ("\n".join(lines) + "\n").encode()


def fingerprint() -> str:
    from refute.core.codehash import compute_code_hash

    h = hashlib.sha256(compute_code_hash().sha256.encode())
    for path in (
        Path(__file__),
        HERE / "ledger_b.py",
        DESIGN,
        FEAS / "d1_routes.py",
        FEAS / "forecast.py",
        ledger_b.V052 / "budgeted.py",
        ledger_b.V052 / "driver.py",
        ledger_b.ROOT / "calibration/v0.4/claim.yaml",
    ):
        h.update(hashlib.sha256(path.read_bytes()).digest())
    return h.hexdigest()[:16]


def run() -> None:
    before = ledger_b.v052_ledger_sha256()
    try:
        ledger_b.check_caps("b0_bound run", reserve_days=0.3, reserve_tokens=0)
        ledger_b.declare()
        fp = fingerprint()
        rows = schedule()
        cap = ledger_b.hard_cap(PART, WORKERS, MAX_SHARD_SECONDS)
        print(len(rows), "shards; hard cap", round(cap, 2), "CPU-h", flush=True)
        state = budgeted.execute(
            ledger_b.SECTION,
            PART,
            OUT / fp,
            shard,
            rows,
            fp,
            WORKERS,
            pin=PIN,
            max_shard_seconds=MAX_SHARD_SECONDS,
            hard_cap_hours=cap,
            units=lambda arg: len(arg["indices"]),
        )
        print(state, flush=True)
    finally:
        if ledger_b.v052_ledger_sha256() != before:
            raise SystemExit("the v0.5.2 ledger changed: refused")
    if state != "complete":
        raise SystemExit(state)


def _quantiles(values: list[float]) -> list[float] | None:
    return [float(np.quantile(values, q)) for q in (0.1, 0.5, 0.9)] if values else None


def _family_summary(recs: list[dict], family: str, rng: np.random.Generator) -> dict:
    nd = NormalDist()
    rows = [r for r in recs if r["family"] == family]
    ok = [r for r in rows if r.get("status") == "OK"]
    elig = [r for r in ok if r.get("eligible") and "catalog" in r]
    statuses = sorted({str(r.get("status")) for r in rows})
    n_proj = round(C1_PRIME_PER_FAMILY * len(elig) / len(rows)) if rows else 0
    out: dict = {
        "attempted": len(rows),
        "statuses": {s: sum(str(r.get("status")) == s for r in rows) for s in statuses},
        "eligible": len(elig),
        "folded": sum(bool(r.get("folded")) for r in elig),
        "c1_prime_projection": n_proj,
        "depth_quantiles_10_50_90": {
            "eclipse": _quantiles([r["depth"] for r in elig]),
            "folded_mean": _quantiles([r["mean_depth"] for r in elig]),
        },
        "stars": {},
    }
    distances_finite = all(math.isfinite(r[s]["distance"]) for r in elig for s in STARS)
    out["valid"] = bool(elig) and len(elig) >= MIN_ELIGIBLE and distances_finite
    if not out["valid"]:
        return out
    k = forecast.max_count(n_proj)
    out["d1_allowance"] = k
    folded = np.array([bool(r.get("folded")) for r in elig])
    for star in STARS:
        d = np.array([r[star]["distance"] for r in elig])
        block: dict = {
            "median_distance": float(np.median(d)),
            "at_bound": sum(r[star]["at_bound"] for r in elig),
            "alphas": {},
        }
        for alpha in ALPHAS:
            z = nd.inv_cdf(1.0 - alpha)
            p = np.array([nd.cdf(z - x) for x in d])
            probs = [
                forecast.poisson_binomial_cdf(rng.choice(p, size=n_proj, replace=True), k)
                for _ in range(BOOTSTRAP)
            ]
            expected = float(p.mean() * n_proj)
            block["alphas"][str(alpha)] = {
                "non_rejection_fraction": float(p.mean()),
                "non_rejection_fraction_folded": float(p[folded].mean()) if folded.any() else None,
                "non_rejection_fraction_unfolded": (
                    float(p[~folded].mean()) if (~folded).any() else None
                ),
                "expected_non_rejected_at_projection": expected,
                "pass_probability_median": float(np.median(probs)),
                "pass_probability_p95": float(np.percentile(probs, 95)),
                "illustrative_excess_over_allowance_fraction": max(0.0, expected - k) / n_proj,
            }
        out["stars"][star] = block
    a = str(PRIMARY_ALPHA)
    known = out["stars"]["star_known"]["alphas"][a]
    cat = out["stars"]["catalog"]["alphas"][a]
    out["no_room_star_known"] = (
        known["expected_non_rejected_at_projection"] > k
        and known["pass_probability_median"] < A_PASS_PROBABILITY
    )
    out["room_catalog"] = cat["expected_non_rejected_at_projection"] <= k
    return out


def outcome(recs: list[dict], fams: dict) -> str:
    """The design's section 4: D, then A, then B, else C."""
    if any(r.get("status") == "ERROR" for r in recs) or not all(f["valid"] for f in fams.values()):
        return "D"
    if any(f["no_room_star_known"] for f in fams.values()):
        return "A"
    if all(f["room_catalog"] for f in fams.values()):
        return "B"
    return "C"


SUMMARIZE_RESERVE_HOURS = 0.03  # the summary's estimated cost (about 1 processor-minute) doubled


def summarize() -> None:
    """Checks the caps and the charges' room first; its own processor time is charged even when
    it fails (Codex's round 2)."""
    ledger_b.check_caps("b0_bound summarize", reserve_days=0.05, reserve_tokens=0)
    if ledger_b.charges_left() < SUMMARIZE_RESERVE_HOURS:
        raise SystemExit("too little of the charges' room left for the summary: a STOP")
    started = time.process_time()
    try:
        _summarize()
    finally:
        used = time.process_time() - started
        ledger_b.charge(
            f"b0_summarize_{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}",
            used / 3600.0,
            f"d1_bound.summarize: process time {used:.1f} s",
        )


def _summarize() -> None:
    fp = fingerprint()
    rows = schedule()
    data = budgeted.assembled(
        ledger_b.SECTION, PART, OUT / fp, shard, rows, fp, WORKERS,
        pin=PIN, max_shard_seconds=MAX_SHARD_SECONDS,
    )  # fmt: skip
    recs = [json.loads(x) for x in data.decode().splitlines() if x.strip()]
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    fams = {f: _family_summary(recs, f, rng) for f in FAMILIES}
    out = {
        "label": "D1's information bound for EB1 and EB2 on development seeds, a diagnostic "
        "(#217, stage B, B0); the reading fixed in docs/plans/v0.5.3-stageB0-design.md, "
        "sections 3 and 4",
        "method_status": "not_validated",
        "fingerprint": fp,
        "primary_alpha": PRIMARY_ALPHA,
        "errors": sum(r.get("status") == "ERROR" for r in recs),
        "families": fams,
        "outcome": outcome(recs, fams),
        "cpu_seconds_of_the_records": sum(r.get("cpu_seconds", 0.0) for r in recs),
    }
    (HERE / "d1-bound.json").write_text(json.dumps(out, indent=1, sort_keys=True) + "\n", "utf-8")
    print(json.dumps(out, indent=1, sort_keys=True))


if __name__ == "__main__":
    {"run": run, "summarize": summarize}[sys.argv[1]]()
