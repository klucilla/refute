"""v0.5.5, R1, check D2-F: D2's rule floor at the oracle on new planets, under four variants
(#218; the frozen design is ``docs/plans/v0.5.5-r1-designs.md``, section D2-F, **as redesigned
by** ``docs/plans/v0.5.5-r1-designs-revision-1.md``, section 2). ``method_status: not_validated``.
**Redesigned, not run:** D2-F does not run before its redesign is checked (a stop that is not
delegated), and its decision-value test, redone (``d2f_decision_value.py``), gives "route" at
most about 0.11. **It decides nothing by itself: never a draft, and no variant is
adopted by it** (a design question is R2's, after G1, a stop that is not delegated).

Per planet of two new, disjoint seed sets (A and B; 200 attempted each), from C1 **version 2**:
- C1's eligibility (v0.4's gate passed and the identity), and **version 5**'s verdict and test
  rows (round 3's frozen composition, ``b1_b14.config()``), with each row's class, detail and
  message kept;
- at the oracle (the generator's model, the true ephemeris and depth, the stellar trend known):
  - **INFO**: ``odd_even``'s power with the transit shape as a nuisance (I4's
    ``nuisance_bound``, with I4's convergence check made on the cadences that straddle no corner
    of the trapezoid when it is I4's only invalid reason: ``i4_fix.py``) below 0.95; a bound that
    stays invalid is unknown, and its power is stored apart;
  - **SIN_F**: ``sinusoid``'s Fréchet certificate (step 7's) below 0.95 - 0.02;
  - **SIN_J**: the same block as a **simulated joint probability** of the flag and the small
    residual (their exact Gaussian joint law under the generator's covariance), below 0.95 - 0.01;
  - **RULE**: version 5's ambiguous-cause branch (``AMBIGUOUS_SINUSOID``); **RULE_3**: the same
    branch where, at the oracle, a large residual would not be shown with probability 0.95 (the
    box's GLS mean under the normalized transit approximation, omitting the generator's
    multiplicative stellar trend, computed, not assumed equal to the depth);
  - **DATA**: a decisive test INCONCLUSIVE with the class ``not_enough_data``.
- the counts: **current** = DATA ∪ INFO ∪ SIN_F ∪ RULE; **variant 2** = DATA ∪ INFO ∪ SIN_J ∪ RULE;
  **variant 3** = DATA ∪ INFO ∪ SIN_F ∪ RULE_3; **variant 4** = DATA ∪ INFO ∪ SIN_J ∪ RULE_3
  (frozen before any data); each counted strictly and with every uncertain and unknown planet
  (the upper count, its unknown rate disclosed), then the frozen outcome per variant
  (``r1_common.d2f_variant_outcome``), against the stricter of 14/178 and the set's own unit (its
  own v0.4 kept fraction): "route under the variant" or "unresolved".

**These counts diagnose certificate limitations and observed blockers. They are not demonstrated
lower bounds on unavoidable retention losses** (a certificate's failure does not exclude a warning
FAIL, which keeps the planet; Codex, r0r1 round 1). Counting them as losses makes "route" harder,
which is the conservative side for the one outcome D2-F can give; it has no "closed" outcome.

Usage (from the project root, through ``launch_detached.py``):
``.venv/Scripts/python.exe -B docs/validation/v0.5.5/d2f_floor.py run A`` then ``summarize A``;
``run B`` is refused if set A's futility rule holds; then ``summarize B``.
"""

from __future__ import annotations

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
import i4_bound as i4  # noqa: E402,I001  (stage A's and B's modules, then ledger_i)
from i4_bound import sa, b1_b14  # noqa: E402
import step7_sinusoid as s7  # noqa: E402
import generator_v2 as g2  # noqa: E402
import i4_fix  # noqa: E402
import r1_common as rc  # noqa: E402
import budgeted_v3  # noqa: E402
import ledger_v055 as lv  # noqa: E402  (last: it binds budgeted to v0.5.5's ledger)
import budgeted  # noqa: E402

DESIGN = ROOT / "docs/plans/v0.5.5-r1-designs.md"
CHARTER = ROOT / "docs/plans/v0.5.5-charter.md"
AMENDMENT = ROOT / "docs/plans/v0.5.5-charter-amendment-1.md"
REVISION = ROOT / "docs/plans/v0.5.5-r1-designs-revision-1.md"
OUT = ROOT / ".cache/v055/d2f"
SETS = ("A", "B")
SIZE = 200  # attempted per set (the design's sizing and price)
PER_SHARD = 4
SIN_BAND_F = 0.02  # step 7's band: about four standard errors of a 2,000-draw power
SIN_BAND_J = 0.01  # the joint simulation's band (20,000 draws per phase)
JOINT_DRAWS = 20_000
PHASES = 8
MARGINAL_TOL = 0.02  # the joint draws' marginals must agree with the battery's own computation
VARIANTS = ("current", "variant_2_joint", "variant_3_evidence", "variant_4_combined")
CONVERGENCE_REASON = "the convergence check failed"


def part(set_name: str) -> str:
    return f"r1_d2f_{set_name.lower()}"


def _seed32(*parts) -> int:
    text = "refute-v055-d2f:" + ":".join(str(p) for p in parts)
    return int(hashlib.sha256(text.encode()).hexdigest(), 16) % (2**32)


# --- version 5's verdict, with each row's class, detail and message ---------------------------


def verdict_rows(tests, plan) -> tuple[str, dict, list]:
    """``forecast_v4._verdict`` (the forecasts' own), with each row's ``inconclusive_detail`` and
    message kept, and the decisive tests named."""
    from refute.core.sensitivity import enforce_sensitivity
    from refute.core.verdict import aggregate, defer_tests, enforce_coverage
    from refute.packs.tess.pipeline import expected_by_role
    from refute.packs.tess.power import registry_for

    tests = enforce_sensitivity(enforce_coverage(list(tests)), registry_for(plan))
    tests, _ = defer_tests(tests, dict(plan.discovery.stages), 2)
    decisive, _ = expected_by_role(plan, False)
    verdict, _ = aggregate([t for t in tests if t.name in decisive], expected=decisive)
    rows = {}
    for t in tests:
        row = {"status": t.status.value, "severity": t.severity.value, "message": t.message}
        for key in ("inconclusive_class", "inconclusive_detail"):
            if t.metrics.get(key):
                row[key] = t.metrics[key]
        rows[t.name] = row
    return verdict.value, rows, sorted(decisive)


# --- the sinusoid at the oracle: the Fréchet certificate and the joint probability --------------


def sinusoid_oracle(data, truth, index_key: str) -> dict:
    """Step 7's construction at the true ephemeris, plus the joint law of the flag's (cos, sin)
    on the out-of-transit cadences and the box depth after the harmonics on every cadence."""
    from refute.packs.tess.battery_v5 import _sinusoid_power
    from refute.packs.tess.battery_v52 import HARMONICS

    _, _, p4 = b1_b14.fv.plans()
    sp, domain = p4.stronger, p4.v051.sinusoid_harmonic_max_period_days
    t, sector = data.lc.time, data.lc.sector
    sigma_w = truth["sigma_white_ppm"] * 1e-6
    sigma_r = sigma_w / 2.0 if truth["correlated"] else 0.0
    scale = sa.sector_scale(sector, data.lc.flux)
    cand = types.SimpleNamespace(
        period=truth["period_days"],
        t0=truth["t0_btjd"],
        duration=truth["duration_days"],
        depth=float(truth["depth"]),
    )
    applicable = [(lab, f) for lab, f in HARMONICS if cand.period * f < domain]
    if ("P/2", 0.5) not in applicable:
        return {"status": "OUTSIDE_DOMAIN"}
    periods = [cand.period * f for _, f in applicable]
    dtb = np.abs(np.mod(t - cand.t0 + 0.5 * cand.period, cand.period) - 0.5 * cand.period)
    cols2 = [-(dtb <= cand.duration / 2.0).astype(float)]
    cols2 += [(sector == s).astype(float) for s in np.unique(sector)]
    for period in periods:
        ph = 2.0 * math.pi * t / period
        cols2 += [np.cos(ph), np.sin(ph)]
    cols2 = [c * scale for c in cols2]
    g2_ = sa.gram(t, sector, cols2, sigma_w, sigma_r)
    why = s7._invalid_matrix(g2_)
    if why:
        return {"status": "UNK", "reason": f"the full Gram matrix: {why}"}
    inv2 = np.linalg.inv(g2_)
    s_box = float(math.sqrt(inv2[0, 0]))
    reference = sa.sinusoid_bound(t, sector, cand, periods, sigma_w, sigma_r, scale)
    if not (math.isfinite(s_box) and s_box > 0) or abs(s_box / reference - 1.0) > 1e-9:
        return {"status": "UNK", "reason": f"sigma_box {s_box} against stage A's {reference}"}
    p_small = 0.5 * math.erfc(
        -((sa.SMALL_FRACTION * cand.depth / s_box) - sa.SMALL_Z) / math.sqrt(2.0)
    )
    # RULE_3's evidence: the box's GLS projection of the true transit, mu_box =
    # [G2^-1 X2' S^-1 mu][0], from the Gram matrix of the columns with mu; a large residual is
    # shown when the box depth exceeds half the depth by 3 sigma:
    # P_large = Phi((mu_box - 0.5 D) / sigma_box - 3) (Codex, r0r1 round 1).
    # mu = -trapezoid x the sector scale is a transit approximation in the columns' normalized
    # units: it leaves out the generator's multiplicative stellar trend (c1._noisy), so it is not
    # exactly the generator's physical mean (Codex, r0r1 round 2)
    from refute.packs.tess import synthetic as syn

    mu = (
        -syn.trapezoid(
            t, cand.period, cand.t0, cand.depth, cand.duration, truth["ingress_fraction"]
        )
        * scale
    )
    with_mu = sa.gram(t, sector, cols2 + [mu], sigma_w, sigma_r)
    mu_box = float((inv2 @ with_mu[:-1, -1])[0])
    p_large = 0.5 * math.erfc(
        -(((mu_box - sa.SMALL_FRACTION * cand.depth) / s_box) - sa.SMALL_Z) / math.sqrt(2.0)
    )
    if not (math.isfinite(mu_box) and _is_probability(p_large)):
        return {"status": "UNK", "reason": f"the box's mean under the transit: {mu_box}"}
    half = cand.duration / 2.0 + sp.sinusoid_mask_durations * cand.duration
    keep = dtb > half
    tk, sk, scl = t[keep], sector[keep], scale[keep]
    cols1 = [(sk == s).astype(float) for s in np.unique(sk)]
    n_off = len(cols1)
    for period in periods:
        phase = 2.0 * math.pi * tk / period
        cols1 += [np.cos(phase), np.sin(phase)]
    cols1 = [c * scl for c in cols1]
    g1 = sa.gram(tk, sk, cols1, sigma_w, sigma_r)
    why = s7._invalid_matrix(g1)
    if why:
        return {"status": "UNK", "reason": f"the out-of-transit Gram matrix: {why}"}
    inv1 = np.linalg.inv(g1)
    # the cross term X1' S11^-1 X2[keep] (S11 the out-of-transit covariance), from the Gram
    # matrix of both column sets on the out-of-transit cadences
    both = sa.gram(tk, sk, cols1 + [c[keep] for c in cols2], sigma_w, sigma_r)
    n1 = len(cols1)
    cross = inv1 @ both[:n1, n1:] @ inv2
    out: dict = {
        "status": "OK",
        "p_small": p_small,
        "sigma_box": s_box,
        "mu_box_under_the_transit": mu_box,
        "p_large": p_large,
        "harmonics": {},
    }
    for j, (label, _) in enumerate(applicable):
        a = n_off + 2 * j
        cov = inv1[a : a + 2, a : a + 2]
        why = s7._invalid_matrix(cov)
        if why:
            return {"status": "UNK", "reason": f"{label}: {why}"}
        p_flag = float(_sinusoid_power(cov, cand.depth, cand.depth, sp, _seed32(index_key, label)))
        joint3 = np.zeros((3, 3))
        joint3[:2, :2] = cov
        joint3[:2, 2] = joint3[2, :2] = cross[a : a + 2, 0]
        joint3[2, 2] = inv2[0, 0]
        why = s7._invalid_matrix(joint3)
        if why:
            return {"status": "UNK", "reason": f"{label}: the joint covariance: {why}"}
        joint, flag_mc, small_mc = _joint(
            joint3, cov, cand.depth, s_box, sp, _seed32(index_key, label, "joint")
        )
        if abs(flag_mc - p_flag) > MARGINAL_TOL or abs(small_mc - p_small) > MARGINAL_TOL:
            return {
                "status": "UNK",
                "reason": f"{label}: the joint draws' marginals differ "
                f"(flag {flag_mc:.4f} vs {p_flag:.4f}; small {small_mc:.4f} vs {p_small:.4f})",
            }
        out["harmonics"][label] = {
            "p_flag": p_flag,
            "frechet": max(0.0, p_flag + p_small - 1.0),
            "joint": joint,
            "flag_mc": flag_mc,
            "small_mc": small_mc,
        }
    out["min_frechet"] = min(h["frechet"] for h in out["harmonics"].values())
    out["min_joint"] = min(h["joint"] for h in out["harmonics"].values())
    return out


def _is_probability(p) -> bool:
    return isinstance(p, float) and math.isfinite(p) and 0.0 <= p <= 1.0


def _joint(joint3, cov, depth, s_box, sp, seed) -> tuple[float, float, float]:
    """At the worst of eight phases of a sinusoid of semi-amplitude ``depth``: the probability
    that the battery's own flag rule fires AND the box depth after the harmonics is small (below
    half the depth by 3σ); the box's mean is 0 under that alternative (the harmonics absorb the
    sinusoid). Also, for the check, the flag's marginal at its own worst phase (the battery's
    ``_sinusoid_power`` reading) and the small residual's marginal over every draw (its law does
    not depend on the phase)."""
    chol = np.linalg.cholesky(joint3)
    rng = np.random.default_rng(seed)
    joints, flags, smalls = [], [], []
    for k in range(PHASES):
        angle = 2.0 * math.pi * k / PHASES
        mean = np.array([depth * math.cos(angle), depth * math.sin(angle), 0.0])
        x = mean + rng.standard_normal((JOINT_DRAWS, 3)) @ chol.T
        a, b, r = x[:, 0], x[:, 1], x[:, 2]
        amp = np.hypot(a, b)
        with np.errstate(divide="ignore", invalid="ignore"):
            var = (a * a * cov[0, 0] + b * b * cov[1, 1] + 2 * a * b * cov[0, 1]) / amp**2
            sig = np.where(var > 0, amp / np.sqrt(np.abs(var)), 0.0)
        flag = (sig > sp.sinusoid_min_significance) & (
            amp >= sp.sinusoid_min_amplitude_ratio * depth
        )
        small = r + sa.SMALL_Z * s_box < sa.SMALL_FRACTION * depth
        joints.append(float(np.mean(flag & small)))
        flags.append(float(np.mean(flag)))
        smalls.append(float(np.mean(small)))
    return min(joints), min(flags), float(np.mean(smalls))


# --- one planet -------------------------------------------------------------------------------


def one(set_name: str, i: int) -> dict:
    from refute.packs.tess.calib05 import c1
    from refute.packs.tess.detrend import detrend
    from refute.packs.tess.discover.paired import _outcome as paired_outcome
    from refute.packs.tess.pipeline import attack_candidate, global_prewhitening
    from refute.packs.tess.power import gaussian_probability
    from refute.packs.tess.search import search_period

    started = time.process_time()
    s = rc.seed("d2f", set_name, "P", i)
    rec: dict = {"set": set_name, "index": i, "seed": str(s)}
    try:
        data, truth = g2.generate("P", s)
    except c1.GenerationFailedError as exc:
        return {
            **rec,
            "status": "GENERATION_FAILURE",
            "reason": str(exc),
            "cpu_seconds": time.process_time() - started,
        }
    rec["truth"] = truth  # the whole truth, kept per case (the charter, change 9)
    p04, _, p4 = b1_b14.fv.plans()
    b1_b14.battery_b1.check_active(None)
    flat = detrend(data.lc, p04.detrend)
    pw, searched = global_prewhitening(data, p04, flat)
    cand = search_period(searched, p04.search).candidate
    v04 = paired_outcome(data, cand, p04, 2, None, None, pw)
    rec["gate_passed"] = bool(v04["gate_passed"])
    rec["identity"] = bool(c1.identity(truth, v04["candidate"]))
    rec["v04"] = v04["verdict"]
    rec["status"] = "OK"
    if not (rec["gate_passed"] and rec["identity"]):
        rec["cpu_seconds"] = time.process_time() - started
        return rec
    with b1_b14.bf.Version5(b1_b14.config()):
        g = attack_candidate(data, cand, p4, None, None, pw)
    rec["v5"], rec["v5_tests"], rec["decisive"] = verdict_rows(g.tests, p4)
    fc = g.candidate
    rec["final_candidate"] = {
        k: float(getattr(fc, k))
        for k in ("period", "t0", "depth", "duration", "snr")
        if getattr(fc, k, None) is not None
    }
    rec["search_candidate"] = None if cand is None else {"period": cand.period, "t0": cand.t0}
    depth = float(fc.depth)
    sigma_w = truth["sigma_white_ppm"] * 1e-6
    sigma_r = sigma_w / 2.0 if truth["correlated"] else 0.0
    t, sector = data.lc.time, data.lc.sector
    nb = i4.nuisance_bound(t, sector, truth, sigma_w, sigma_r)
    alt = p4.stronger.odd_even_alternative_depth_fraction * depth
    oe = {"final_depth": depth, "alternative": alt, "invalid_by_i4": list(nb["invalid"])}
    oe["convergence_i4"] = nb.get("convergence")
    invalid = list(nb["invalid"])
    if invalid == [CONVERGENCE_REASON]:  # only when it is I4's only invalid reason
        # the redesign (3b): I4's check on the cadences that straddle no corner (i4_fix.py, the
        # diagnosis of record-defects.md section 3); the reason is dropped only if it passes
        _, deriv, n = i4.shape_and_derivatives(t, truth)
        conv = i4_fix.masked_convergence(
            t, truth, deriv, n, lambda name, h: i4._numeric(t, truth, name, h)
        )
        oe["masked_convergence"] = conv
        if i4_fix.passes(conv) is True:
            invalid.remove(CONVERGENCE_REASON)
    oe["invalid"] = invalid
    if "sigma" in nb:
        power = gaussian_probability(alt, nb["sigma"], p4.gauntlet.odd_even.max_sigma)
        if isinstance(power, float) and math.isfinite(power):
            if invalid:
                oe["power_of_an_invalid_bound"] = power  # stored apart, never counted
            else:
                oe["power"] = power
    rec["odd_even_oracle"] = oe
    rec["sinusoid_oracle"] = sinusoid_oracle(data, truth, f"{set_name}:{i}")
    rec["cpu_seconds"] = time.process_time() - started
    return rec


# --- the categories and the floors ---------------------------------------------------------------


def categories(rec: dict) -> dict:
    """Per eligible planet: each category as True, False or None (unknown), from the frozen
    definitions of the design."""
    rows, decisive = rec["v5_tests"], set(rec["decisive"])
    data_ = any(
        rows[n]["status"] == "INCONCLUSIVE"
        and rows[n].get("inconclusive_class") == "not_enough_data"
        for n in decisive
        if n in rows
    )
    oe = rec["odd_even_oracle"]
    info = None if "power" not in oe else oe["power"] < rc.REQUIRED
    so = rec["sinusoid_oracle"]
    if so.get("status") == "OUTSIDE_DOMAIN":
        sin_f = sin_j = False
        p_large = None
    elif so.get("status") != "OK":
        sin_f = sin_j = p_large = None
    else:
        lo_f = so["min_frechet"]
        sin_f = (
            True
            if lo_f < rc.REQUIRED - SIN_BAND_F
            else False
            if lo_f >= rc.REQUIRED + SIN_BAND_F
            else None
        )
        lo_j = so["min_joint"]
        sin_j = (
            True
            if lo_j < rc.REQUIRED - SIN_BAND_J
            else False
            if lo_j >= rc.REQUIRED + SIN_BAND_J
            else None
        )
        # a large residual shown: the box depth after the harmonics above half the depth by 3σ,
        # with the box's GLS mean under the true transit computed (sinusoid_oracle)
        p_large = so["p_large"]
    sin_row = rows.get("sinusoid", {})
    rule = sin_row.get("inconclusive_detail") == "AMBIGUOUS_SINUSOID"
    rule_3 = rule and (None if p_large is None else p_large < rc.REQUIRED)
    return {
        "DATA": data_,
        "INFO": info,
        "SIN_F": sin_f,
        "SIN_J": sin_j,
        "RULE": rule,
        "RULE_3": rule_3,
    }


FLOOR_SETS = {
    "current": ("DATA", "INFO", "SIN_F", "RULE"),
    "variant_2_joint": ("DATA", "INFO", "SIN_J", "RULE"),
    "variant_3_evidence": ("DATA", "INFO", "SIN_F", "RULE_3"),
    # frozen before any data (the decision of 2026-11-20, night, 3b): both method changes at once
    "variant_4_combined": ("DATA", "INFO", "SIN_J", "RULE_3"),
}


def floors(cats: list[dict]) -> dict:
    """Per variant: (strict, upper): strict counts a planet with some category True; upper also
    counts a planet with some category unknown (None)."""
    out = {}
    for v, keys in FLOOR_SETS.items():
        strict = sum(any(c[k] is True for k in keys) for c in cats)
        upper = sum(any(c[k] is True or c[k] is None for k in keys) for c in cats)
        out[v] = (strict, upper)
    return out


# --- the run ----------------------------------------------------------------------------------


def schedule(set_name: str) -> list:
    return [
        (f"{set_name}-P-{k:04d}", {"set": set_name, "indices": list(range(k, k + PER_SHARD))})
        for k in range(0, SIZE, PER_SHARD)
    ]


def shard(arg: dict) -> bytes:
    lines = []
    for i in arg["indices"]:
        try:
            rec = one(arg["set"], i)
        except Exception as exc:  # noqa: BLE001 - recorded, never dropped; a stop in the summary
            rec = {
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
    HERE / "i4_fix.py",
    HERE / "r1_common.py",
    HERE / "ledger_v055.py",
    DESIGN,
    CHARTER,
    AMENDMENT,
    REVISION,
    V054 / "i4_bound.py",
    V054 / "step7_sinusoid.py",
    V054 / "ledger_i.py",
    V054 / "budgeted_v3.py",
    V052 / "budgeted.py",
    V052 / "driver.py",
    V052 / "forecast_v4.py",
    V052 / "forecast_t2a.py",
    V054 / "i4_rest.py",
    V054 / "i4_rest2.py",
    i4.STAGE_A / "d2_bounds.py",
    i4.STAGE_A / "ledger_a.py",
    i4.STAGE_B / "b1_b14.py",
    i4.STAGE_B / "b1_forecast.py",
    i4.STAGE_B / "battery_b1.py",
    i4.STAGE_B / "ledger_b.py",
    i4.STAGE_B / "b1_d2d4_rest.py",
    i4.STAGE_B / "b1_data.py",
    i4.STAGE_B / "b1_blockers_decisive.py",
    V054 / "i1_diagnose.py",
    ROOT / "docs/validation/v0.5.1/feasibility/forecast.py",  # d2_bounds._wp1 (mahalanobis2)
    b1_b14.COMPOSITION,  # the frozen composition config() reads (round 3's B1.3)
    ROOT / "calibration/v0.4/claim.yaml",
)


def code_identity() -> dict:
    """``src/``'s code hash and every frozen file outside it (the charter, process change 4)."""
    from refute.core.codehash import compute_code_hash

    rc.require_frozen(ROOT, FROZEN)  # the list is complete (4c)
    ident = {"src_code_hash": compute_code_hash().sha256, **rc.identity(ROOT, FROZEN)}
    ident["digest"] = rc.digest(ident)
    return ident


def fingerprint(rows: list) -> str:
    h = hashlib.sha256(code_identity()["digest"].encode())
    h.update(json.dumps(rows, sort_keys=True).encode())
    return h.hexdigest()[:16]


def _first_set() -> dict:
    """Set A's record, checked before set B uses it: written, with the same code identity."""
    path = HERE / "d2f-A.json"
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
        f"d2f run {set_name}",
        0.5,
        len(rows) * 60_000 + 50_000_000,
        workers,
        rc.MAX_SHARD_SECONDS,
        launch,
    )
    print(state, flush=True)
    lv.check_caps(f"d2f after the run {set_name}", 0.0, 0)
    if state != "complete":
        raise SystemExit(f"STOP for the maintainer: {state}")


def summarize(set_name: str) -> None:
    lv.assert_bound()
    lv.check_caps(f"d2f summarize {set_name}", reserve_days=0.05, reserve_tokens=0)
    if lv.charges_left() < 0.02:
        raise SystemExit("too little of the charges' room left for the summary: a STOP")
    started = time.process_time()
    try:
        _summarize(set_name)
    finally:
        used = time.process_time() - started
        stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
        lv.charge(
            f"d2f_summarize_{set_name}_{stamp}",
            used / 3600.0,
            f"d2f_floor.summarize {set_name}: process time {used:.1f} s",
        )


def _read(set_name: str) -> list:
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
    return [json.loads(x) for x in data.decode().splitlines() if x.strip()]


def _set_counts(recs: list) -> dict:
    ok = [r for r in recs if r.get("status") == "OK"]
    elig = [r for r in ok if r["gate_passed"] and r["identity"]]
    cats = [categories(r) for r in elig]
    n = len(elig)
    kept = sum(r["v5"] in ("SURVIVED", "WEAKENED") for r in elig)
    v04_kept = sum(r["v04"] in ("SURVIVED", "WEAKENED") for r in elig)
    tally = {
        k: {"true": sum(c[k] is True for c in cats), "unknown": sum(c[k] is None for c in cats)}
        for k in ("DATA", "INFO", "SIN_F", "SIN_J", "RULE", "RULE_3")
    }
    fl = floors(cats)
    oe = [r["odd_even_oracle"] for r in elig]
    return {
        "attempted": len(recs),
        "eligible": n,
        "generation_failures": sum(r.get("status") == "GENERATION_FAILURE" for r in recs),
        "errors": sorted(r["index"] for r in recs if r.get("status") == "ERROR"),
        "version_5_kept": kept,
        "v04_kept": v04_kept,
        # the threshold in the population's own unit (the redesign, 3b); the stricter decides
        "route_fraction_own_unit": rc.d2f_route_fraction(v04_kept, n) if n else None,
        "route_fraction_fixed": rc.D2_ROUTE,
        "categories": tally,
        "floors": fl,
        # the unknowns stay in the upper count; their rate is disclosed (the redesign, 3b)
        "unknown_rate_per_variant": {
            v: ((fl[v][1] - fl[v][0]) / n if n else None) for v in VARIANTS
        },
        "i4_bound": {
            "invalid_by_i4": sum(bool(o["invalid_by_i4"]) for o in oe),
            "convergence_failures_by_i4": sum(CONVERGENCE_REASON in o["invalid_by_i4"] for o in oe),
            "valid_after_the_fix": sum(bool(o["invalid_by_i4"]) and not o["invalid"] for o in oe),
            "invalid_after_the_fix": sum(bool(o["invalid"]) for o in oe),
            "reasons_after_the_fix": sorted({x for o in oe for x in o["invalid"]}),
            # the power of the bounds that stay invalid, apart; never counted
            "powers_of_invalid_bounds": sorted(
                o["power_of_an_invalid_bound"] for o in oe if "power_of_an_invalid_bound" in o
            ),
        },
    }


def _upper(counts: dict, v: str) -> tuple[int, int, int]:
    return counts["floors"][v][1], counts["eligible"], counts["v04_kept"]


def _summarize(set_name: str) -> None:
    counts = _set_counts(_read(set_name))
    stops = []
    if counts["errors"]:
        stops.append(f"{len(counts['errors'])} planets raised an error")
    if counts["eligible"] < 150:
        stops.append(f"{counts['eligible']} eligible planets, fewer than 150")
    doc: dict = {
        "label": "v0.5.5 R1, D2-F (redesigned): D2's rule counts at the oracle on new planets "
        "(C1 version 2), four variants; decides nothing by itself; never a draft; no variant is "
        "adopted by it",
        "method_status": "not_validated",
        "set": set_name,
        "design": "docs/plans/v0.5.5-r1-designs.md (D2-F, the redesign)",
        "code_identity": code_identity(),
        "counts": counts,
        "stops": stops,
        "threshold": {
            "route": "the upper count against the stricter of 14/178 and the population's own "
            "unit (r1_common.d2f_route_fraction)"
        },
        "note": "These counts diagnose certificate limitations and observed blockers. They are "
        "not demonstrated lower bounds on unavoidable retention losses.",
        "cpu_hours": round(lv.part_consumption(part(set_name)), 4),
    }
    per_upper = {v: _upper(counts, v) for v in VARIANTS}
    if set_name == "A":
        doc["futile_after_A"] = bool(stops) or rc.d2f_futile_after_first(per_upper)
        if doc["futile_after_A"]:  # set B does not run: the outcome is read now
            doc["outcome_per_variant"] = {v: "unresolved" for v in VARIANTS}
    else:
        first_doc = _first_set()
        doc["set_A_record_sha256"] = first_doc["_sha256"]
        first = first_doc["counts"]
        doc["outcome_per_variant"] = (
            {v: "unresolved (a stop)" for v in VARIANTS}
            if stops
            else {
                v: rc.d2f_variant_outcome({"A": _upper(first, v), "B": per_upper[v]})
                for v in VARIANTS
            }
        )
    out = HERE / f"d2f-{set_name}.json"
    if out.exists():
        raise SystemExit(f"{out.name} exists: the record is written once")
    out.write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n", "utf-8", newline="\n")
    shown = {"floors": counts["floors"], "eligible": counts["eligible"], "stops": stops}
    for key in ("futile_after_A", "outcome_per_variant"):
        if key in doc:
            shown[key] = doc[key]
    print(json.dumps(shown, indent=1))
    if stops:
        raise SystemExit("STOP for the maintainer: " + "; ".join(stops))


if __name__ == "__main__":
    if budgeted.LEDGER != lv.HERE / "ledger.json":
        raise SystemExit("budgeted is not pointed at v0.5.5's ledger: refused")
    {"run": run, "summarize": summarize}[sys.argv[1]](sys.argv[2])
