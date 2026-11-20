"""v0.5.5, R1, check D1-P: D1's SURVIVED-denial price curve for EB1 and EB2 (#218; the frozen
design is ``docs/plans/v0.5.5-r1-designs.md``, section D1-P). ``method_status: not_validated``.
**It decides nothing by itself: no D1 draft, no infeasibility record, no test is built.**

Per binary of two new, disjoint seed sets (A and B; 200 attempted per family per set):
- the curve from C1 **version 2** (``generator_v2``: the true star drawn within the catalog's
  declared 5 %), the locked v0.5 battery's chain (``paired_chain``: v0.4's gate and v0.5's
  verdict, exactly as C1's runs);
- for each binary the battery leaves **SURVIVED** (the others are already denied it), B0's oracle
  distance to the nearest planet at the found period, under three readings of the catalog star:
  - ``prior`` (**primary**, the charter's (b)): the planet's effective radius free with a
    Gaussian penalty ``((rho - rho_B) / sigma_rho)^2``, ``rho_B`` the binary's true effective
    radius and ``sigma_rho`` the catalog's (0.0527, a first-order approximation); the distance
    is the smallest evaluated ``M^2 + penalty`` over **three fits** (prior-weighted,
    box-constrained and known-star), each an upper bound on the minimum, so the reading leans
    toward "route";
  - ``box`` (a reference reading): B0's ±3σ box on the effective radius around the catalog's centre;
  - ``known`` (a reference reading): the effective radius fixed at the binary's true one.
- the reading per family, exit price and set: the expected SURVIVED count at C1's projection and
  the bootstrap pass probability (B0's method), then the frozen reading per exit
  (``r1_common.d1p_set_reading`` / ``d1p_exit_outcome``).

**What the primary reading is, and is not** (Codex, r0r1 round 1): an oracle surrogate under an
explicitly specified catalog experiment (the catalog taken as a measurement of the true star, with
the true star drawn from the same law as the declared error). Planet-side calibration and the
interpretation of ``Phi(z_x - d)`` with fitted parameters and the battery's survivor selection
have **not** been established. Its outcomes are readings for G1, never a basis for a record by
themselves.

Usage (from the project root, through ``launch_detached.py``):
``.venv/Scripts/python.exe -B docs/validation/v0.5.5/d1p_price.py run A`` then ``summarize A``;
``run B`` is refused if set A's futility rule holds; then ``summarize B``.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
FEAS = ROOT / "docs/validation/v0.5.1/feasibility"
STAGE_B = ROOT / "docs/validation/v0.5.3/stageB"
V054 = ROOT / "docs/validation/v0.5.4"
V052 = ROOT / "docs/validation/v0.5.2/stage2"
for p in (str(FEAS), str(STAGE_B), str(V054), str(HERE)):
    if p not in sys.path:
        sys.path.insert(0, p)
import d1_routes  # noqa: E402,I001
import forecast  # noqa: E402
import d1_bound  # noqa: E402  (stage B's: it binds budgeted to stage B; ledger_v055 rebinds it)
import generator_v2 as g2  # noqa: E402
import r1_common as rc  # noqa: E402
import budgeted_v3  # noqa: E402
import ledger_v055 as lv  # noqa: E402  (last: it binds budgeted to v0.5.5's ledger)
import budgeted  # noqa: E402

DESIGN = ROOT / "docs/plans/v0.5.5-r1-designs.md"
CHARTER = ROOT / "docs/plans/v0.5.5-charter.md"
OUT = ROOT / ".cache/v055/d1p"
FAMILIES = ("EB1", "EB2")
SETS = ("A", "B")
SIZE = 200  # attempted per family per set (the design's sizing and price; C1' is 200 too)
PER_SHARD = 5
C1_PRIME_PER_FAMILY = 200
MIN_ELIGIBLE = 150  # below this, per family and set, the reading is INCONCLUSIVE
BOOTSTRAP = 2000
BOOTSTRAP_SEED = {"A": 20261120, "B": 20261121}
SIGMA_RHO = g2.effective_sigma()
BOX = d1_routes.effective_bounds(0.05, 0.05)  # B0's ±3σ box around the catalog's centre
# The exit prices (the charter's (a)). The decisive readings for G1: the warning exit at the
# tolerance unit, and the INCONCLUSIVE exit at step 2's increment, conditional on D2 and D4 met in
# full (it has no room while D2 fails its rule).
EXITS = {
    "weakened": 0.10,
    "inconclusive_if_d2_d4_met": 0.05,
}
# The fatal exit is reported as scenarios only (Codex, r0r1 round 1): its room must be measured
# on the battery and population the new test would join, which D1-P does not draw. 0.05 - 3/178
# uses version 5's REFUTED fraction on round 3's D2 population (3 of 178, published in
# docs/validation/v0.5.4/pause-record.md): a historical reference scenario, not measured room
# for this battery on C1 version 2; 0.05 is the frozen budget's whole, with nothing used.
FATAL_SCENARIOS = {
    "fatal_reference_scenario": 0.05 - 3 / 178,
    "fatal_whole_budget_scenario": 0.05,
}
GRID = (0.0027, 0.01, 0.03, 0.05, 0.10, 0.15, 0.20, 0.30)
READINGS = ("prior", "box", "known")
PRIMARY = "prior"


def part(set_name: str) -> str:
    return f"r1_d1p_{set_name.lower()}"


# --- one binary -------------------------------------------------------------------------------


def _prior_fit(t, truth, found, rho_b: float, sigma_w: float):
    """The planet at the found period nearest to the binary with the effective radius under the
    Gaussian penalty: least squares on the near-event residual over ``sigma_w`` and the penalty
    term together (white weights in the fit; the distance is evaluated with the full covariance
    afterwards, as B0 does). Returns (the fitted parameters, the full residual) of the best of
    the starts."""
    from scipy.optimize import least_squares

    pf, t0f = found["period_days"], found["t0_btjd"]
    target = forecast.binary_model(t, truth)
    dt_ = np.mod(t - t0f + 0.5 * pf, pf) - 0.5 * pf
    near = np.abs(dt_) <= 2.0 * truth["duration_days"]
    tn, yn = t[near], target[near]
    mean_depth = truth["depth"] * (1.0 + truth["secondary_ratio"]) / 2.0
    lo, hi = rho_b - 5.0 * SIGMA_RHO, rho_b + 5.0 * SIGMA_RHO

    def resid(x):
        depth, b, shift, rho = x
        curve = (forecast.planet_model(tn, pf, t0f + shift, depth, b, rho) - yn) / sigma_w
        return np.append(curve, (rho - rho_b) / SIGMA_RHO)

    best = None
    for b0 in (0.0, 0.3, 0.6, 0.85):
        for r0 in (rho_b, lo + 0.25 * (hi - lo), lo + 0.75 * (hi - lo)):
            for depth0 in (mean_depth, truth["depth"]):
                try:
                    fit = least_squares(
                        resid,
                        [depth0, b0, 0.0, r0],
                        bounds=([1e-7, 0.0, -0.1, lo], [0.5, 1.2, 0.1, hi]),
                        x_scale=[mean_depth, 0.1, 0.005, 0.05],
                        max_nfev=400,
                    )
                except ValueError:
                    continue
                if best is None or fit.cost < best.cost:
                    best = fit
    if best is None:
        raise RuntimeError("no start of the prior-weighted fit succeeded")
    depth, b, shift, rho = (float(v) for v in best.x)
    params = {
        "depth": depth,
        "impact": b,
        "epoch_shift_days": shift,
        "effective_radius": rho,
        "cost": float(best.cost),
        "nfev": int(best.nfev),
        "status": int(best.status),
    }
    return params, forecast.planet_model(t, pf, t0f + shift, depth, b, rho) - target


def distances(family: str, s: int, data, truth, found: dict) -> dict:
    t, sector = data.lc.time, data.lc.sector
    factor = d1_bound.trend_factor(family, s, t)
    sigma_w = truth["sigma_white_ppm"] * 1e-6
    sigma_r = sigma_w / 2.0 if truth["correlated"] else 0.0
    rho_b = truth["true_star"]["effective_radius"]

    def m2(r) -> float:
        return float(forecast.mahalanobis2(t, sector, r * factor, sigma_w, sigma_r))

    out: dict = {}
    fits = {}
    for name, bounds in (("box", BOX), ("known", (rho_b - 1e-9, rho_b + 1e-9))):
        rho, r, at_bound = d1_routes.nearest_with_bounds(forecast, t, truth, found, 0.05, bounds)
        out[name] = {
            "distance": math.sqrt(m2(r)),
            "effective_radius": rho,
            "at_bound": bool(at_bound),
        }
        fits[name] = (rho, r)
    params, r = _prior_fit(t, truth, found, rho_b, sigma_w)
    fits["prior_fit"] = (params["effective_radius"], r)
    objectives = {k: m2(rr) + ((rh - rho_b) / SIGMA_RHO) ** 2 for k, (rh, rr) in fits.items()}
    best = min(objectives, key=objectives.get)
    out["prior"] = {
        "distance": math.sqrt(objectives[best]),
        "effective_radius": fits[best][0],
        "from_fit": best,
        "objectives": objectives,
        "prior_fit_parameters": params,
        "rho_true": rho_b,
        "sigma_rho": SIGMA_RHO,
    }
    # B0's own fit (d1_routes.nearest_with_bounds) returns the radius only: the box and known
    # readings keep B0's function unchanged, for comparability, with that limit
    return out


def one(family: str, set_name: str, i: int) -> dict:
    from refute.packs.tess.calib05 import c1
    from refute.packs.tess.calib05.plans import pair
    from refute.packs.tess.calib05.steps import v04_test_plan
    from refute.packs.tess.discover.paired import paired_chain

    started = time.process_time()
    s = rc.seed("d1p", set_name, family, i)
    rec: dict = {"family": family, "set": set_name, "index": i, "seed": str(s)}
    try:
        data, truth = g2.generate(family, s)
    except c1.GenerationFailedError as exc:
        return {
            **rec,
            "status": "GENERATION_FAILURE",
            "reason": str(exc),
            "cpu_seconds": time.process_time() - started,
        }
    p04, p05 = pair(v04_test_plan(ROOT))
    chain = paired_chain(data, p04, p05, stage=2)
    v05 = chain["v05"]
    rec.update(
        status="OK",
        truth=truth,  # the whole truth, kept per case (the charter, change 9)
        true_star=truth["true_star"],
        target_snr=truth["target_snr"],
        secondary_ratio=truth["secondary_ratio"],
        eligible=bool(chain["v04"]["gate_passed"]),
        v05_verdict=v05["verdict"],
        search_candidate=chain["search_candidate"],
        chain=chain,  # the whole chain kept per case, as C1's records (the charter, change 9)
    )
    if rec["eligible"] and v05["verdict"] == "SURVIVED" and chain["search_candidate"]:
        found = {
            "period_days": chain["search_candidate"]["period_days"],
            "t0_btjd": chain["search_candidate"]["t0_btjd"],
        }
        rec["found"] = found
        rec["distances"] = distances(family, s, data, truth, found)
    rec["cpu_seconds"] = time.process_time() - started
    return rec


# --- the run ----------------------------------------------------------------------------------


def schedule(set_name: str) -> list:
    """Shards of ``PER_SHARD`` indices, the families alternating, so that the driver's
    checkpoint holds both."""
    rows = []
    for k in range(0, SIZE, PER_SHARD):
        for f in FAMILIES:
            rows.append(
                (
                    f"{set_name}-{f}-{k:04d}",
                    {"family": f, "set": set_name, "indices": list(range(k, k + PER_SHARD))},
                )
            )
    return rows


def shard(arg: dict) -> bytes:
    lines = []
    for i in arg["indices"]:
        try:
            rec = one(arg["family"], arg["set"], i)
        except Exception as exc:  # noqa: BLE001 - recorded, never dropped; a stop in the summary
            rec = {
                "family": arg["family"],
                "set": arg["set"],
                "index": i,
                "status": "ERROR",
                "reason": f"{type(exc).__name__}: {exc}",
            }
        lines.append(json.dumps(rec, sort_keys=True, default=str))
    return ("\n".join(lines) + "\n").encode()


FROZEN = (
    Path(__file__),
    HERE / "generator_v2.py",
    HERE / "r1_common.py",
    HERE / "ledger_v055.py",
    DESIGN,
    CHARTER,
    FEAS / "d1_routes.py",
    FEAS / "forecast.py",
    STAGE_B / "d1_bound.py",
    STAGE_B / "ledger_b.py",
    V054 / "budgeted_v3.py",
    V052 / "budgeted.py",
    V052 / "driver.py",
    ROOT / "calibration/v0.4/claim.yaml",
)


def code_identity() -> dict:
    """``src/``'s code hash and every frozen file outside it (the charter, process change 4)."""
    from refute.core.codehash import compute_code_hash

    ident = {"src_code_hash": compute_code_hash().sha256, **rc.identity(ROOT, FROZEN)}
    ident["digest"] = rc.digest(ident)
    return ident


def fingerprint(rows: list) -> str:
    h = hashlib.sha256(code_identity()["digest"].encode())
    h.update(json.dumps(rows, sort_keys=True).encode())
    return h.hexdigest()[:16]


def _first_set() -> dict:
    """Set A's record, checked before set B uses it: written, with the same code identity."""
    path = HERE / "d1p-A.json"
    if not path.exists():
        raise SystemExit("set A has no record: set B refused")
    first = json.loads(path.read_text("utf-8"))
    if first.get("code_identity", {}).get("digest") != code_identity()["digest"]:
        raise SystemExit("set A ran under another complete code identity: set B refused")
    first["_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    return first


def run(set_name: str) -> None:
    if set_name not in SETS:
        raise SystemExit(f"unknown set {set_name}")
    lv.assert_bound()
    if set_name == "B" and _first_set().get("futile_after_A") is not False:
        raise SystemExit("set A's futility rule holds: set B refused")
    rows = schedule(set_name)
    fp = fingerprint(rows)
    workers = rc.workers_now(dt.datetime.now(rc.BRT))

    def launch(cap: float) -> str:
        return budgeted_v3.execute(
            lv.SECTION,
            part(set_name),
            OUT / fp,
            shard,
            rows,
            fp,
            workers,
            pin=rc.pin()[:workers],
            max_shard_seconds=rc.MAX_SHARD_SECONDS,
            hard_cap_hours=cap,
            pause_at=rc.NO_PAUSE,
            units=lambda arg: len(arg["indices"]),
        )

    state = lv.guarded_run(
        part(set_name),
        fp,
        rows,
        f"d1p run {set_name}",
        0.5,
        len(rows) * 40_000 + 50_000_000,
        workers,
        rc.MAX_SHARD_SECONDS,
        launch,
    )
    print(state, flush=True)
    lv.check_caps(f"d1p after the run {set_name}", 0.0, 0)
    if state != "complete":
        raise SystemExit(f"STOP for the maintainer: {state}")


# --- the reading ------------------------------------------------------------------------------


def _family(recs: list, family: str, rng) -> dict:
    rows = [r for r in recs if r["family"] == family]
    ok = [r for r in rows if r.get("status") == "OK"]
    elig = [r for r in ok if r["eligible"]]
    surv = [r for r in elig if r["v05_verdict"] == "SURVIVED"]
    out: dict = {
        "attempted": len(rows),
        "generation_failures": sum(r.get("status") == "GENERATION_FAILURE" for r in rows),
        "eligible": len(elig),
        "survived_by_the_battery": len(surv),
        "survived_without_a_distance": sum("distances" not in r for r in surv),
    }
    out["valid"] = len(elig) >= MIN_ELIGIBLE and out["survived_without_a_distance"] == 0
    if not out["valid"]:
        return out
    n_proj = round(C1_PRIME_PER_FAMILY * len(elig) / len(rows))
    k = forecast.max_count(n_proj)
    out.update(c1_prime_projection=n_proj, d1_allowance=k)
    levels = sorted(set(GRID) | set(EXITS.values()) | set(FATAL_SCENARIOS.values()))
    out["readings"] = {}
    for reading in READINGS:
        d = np.array([r["distances"][reading]["distance"] for r in surv])
        block = {}
        for x in levels:
            p_surv = np.array([rc.non_rejection(v, x) for v in d])
            p = np.concatenate([p_surv, np.zeros(len(elig) - len(surv))])  # denied already
            probs = [
                forecast.poisson_binomial_cdf(rng.choice(p, size=n_proj, replace=True), k)
                for _ in range(BOOTSTRAP)
            ]
            expected = float(p.mean() * n_proj)
            block[f"{x:.6g}"] = {
                "expected_survived_at_projection": expected,
                "pass_probability_p05": float(np.percentile(probs, 5)),
                "pass_probability_median": float(np.median(probs)),
                "pass_probability_p95": float(np.percentile(probs, 95)),
                "reading": rc.d1p_set_reading(
                    expected, k, float(np.percentile(probs, 5)), float(np.percentile(probs, 95))
                ),
            }
        out["readings"][reading] = block
    return out


def summarize(set_name: str) -> None:
    lv.assert_bound()
    lv.check_caps(f"d1p summarize {set_name}", reserve_days=0.05, reserve_tokens=0)
    if lv.charges_left() < 0.05:
        raise SystemExit("too little of the charges' room left for the summary: a STOP")
    started = time.process_time()
    try:
        _summarize(set_name)
    finally:
        used = time.process_time() - started
        stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
        lv.charge(
            f"d1p_summarize_{set_name}_{stamp}",
            used / 3600.0,
            f"d1p_price.summarize {set_name}: process time {used:.1f} s",
        )


def _summarize(set_name: str) -> None:
    rows = schedule(set_name)
    fp = fingerprint(rows)
    data = budgeted.assembled(
        lv.SECTION,
        part(set_name),
        OUT / fp,
        shard,
        rows,
        fp,
        rc.WORKERS_WORKING,
        pin=rc.pin()[: rc.WORKERS_WORKING],
        max_shard_seconds=rc.MAX_SHARD_SECONDS,
    )
    recs = [json.loads(x) for x in data.decode().splitlines() if x.strip()]
    rng = np.random.default_rng(BOOTSTRAP_SEED[set_name])
    fams = {f: _family(recs, f, rng) for f in FAMILIES}
    errors = sorted(f"{r['family']}/{r['index']}" for r in recs if r.get("status") == "ERROR")
    stops = []
    if errors:
        stops.append(f"{len(errors)} binaries raised an error")
    if not all(f["valid"] for f in fams.values()):
        stops.append("a family has fewer than 150 eligible binaries, or a survivor has no distance")

    def reading_at(x: float) -> dict:
        return {
            f: (fams[f]["readings"][PRIMARY][f"{x:.6g}"]["reading"] if not stops else "unresolved")
            for f in FAMILIES
        }

    per_exit = {e: reading_at(x) for e, x in EXITS.items()}
    scenarios = {e: reading_at(x) for e, x in FATAL_SCENARIOS.items()}
    doc = {
        "label": "v0.5.5 R1, D1-P: D1's SURVIVED-denial price curve (development, C1 version 2; "
        "an oracle surrogate; decides nothing by itself; never a draft)",
        "method_status": "not_validated",
        "fingerprint": fp,
        "code_identity": code_identity(),
        "set": set_name,
        "design": "docs/plans/v0.5.5-r1-designs.md (D1-P)",
        "exit_prices": EXITS,
        "fatal_scenarios": FATAL_SCENARIOS,
        "primary_reading": PRIMARY,
        "families": fams,
        "per_exit_primary": per_exit,
        "fatal_scenarios_primary": scenarios,
        "errors": errors,
        "stops": stops,
        "cpu_hours": round(lv.part_consumption(part(set_name)), 4),
    }
    if set_name == "A":
        doc["futile_after_A"] = bool(stops) or rc.d1p_futile_after_first(per_exit)
    else:
        first = _first_set()
        doc["set_A_record_sha256"] = first["_sha256"]
        both = {e: {"A": first["per_exit_primary"][e], "B": per_exit[e]} for e in EXITS}
        doc["outcome_per_exit"] = {e: rc.d1p_exit_outcome(both[e]) for e in EXITS}
        doc["outcome_note"] = (
            "route / closed / unresolved per exit at its price, under the primary reading (an "
            "oracle surrogate) on both sets; 'inconclusive_if_d2_d4_met' is conditional: that "
            "exit has no room while D2 fails its rule; the fatal exit is reported as scenarios "
            "only, its room not measured here"
        )
    out = HERE / f"d1p-{set_name}.json"
    if out.exists():
        raise SystemExit(f"{out.name} exists: the record is written once")
    out.write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n", "utf-8", newline="\n")
    print(
        json.dumps(
            {
                "per_exit_primary": per_exit,
                "stops": stops,
                **(
                    {"futile_after_A": doc["futile_after_A"]}
                    if set_name == "A"
                    else {"outcome_per_exit": doc["outcome_per_exit"]}
                ),
            },
            indent=1,
        )
    )
    if stops:
        raise SystemExit("STOP for the maintainer: " + "; ".join(stops))


if __name__ == "__main__":
    if budgeted.LEDGER != lv.HERE / "ledger.json":
        raise SystemExit("budgeted is not pointed at v0.5.5's ledger: refused")
    {"run": run, "summarize": summarize}[sys.argv[1]](sys.argv[2])
