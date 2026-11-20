"""v0.5.5: D2-F's decision-value test, redone (#218; the maintainer's decision of 2026-11-20, night,
item 3b). ``method_status: not_validated``. A reading of existing development records only; it
reads no new data and runs no battery.

**What it bounds.** The best variant for "route" is variant 4 (DATA ∪ INFO ∪ SIN_J ∪ RULE_3): every
other variant's count contains RULE or SIN_F, both at least as large. Its upper count on round 3's
178 planets (C1 version 1, I4's fresh set) is bounded from below by what step 7 and step 1 already
recorded:
- **SIN_J from above, per planet.** The joint block (the flag fires AND the residual is small) is
  at most each marginal, so at most ``min(p_flag, p_small)`` at every harmonic. From step 7's
  per-planet shards (``.cache/v054/step7/<fingerprint>/shards``): a planet whose bound is below
  0.94 is SIN_J True under any joint law; one whose bound is within [0.94, 0.96) is True or
  unknown, so it is in the upper count either way.
- **DATA ∪ INFO** per planet: step 1's data losses (its per-case detail, checked against its
  recorded SHA-256, as step 7 does) and I4's information-limited planets (I4's valid bounds with a
  power below 0.95, read by I4's own reader under the pinned code hash, as ``i4_diagnosis``).
  The union with the SIN_J planets is taken per planet, so no overlap is counted twice.

**The predictive probability.** With the round-3 count ``k`` of 178 as a Beta(k + 1/2,
178 - k + 1/2) rate (Jeffreys), two new sets of 178 eligible each are drawn; "route" needs each
set's point fraction at most 14/178 and the pooled Wilson upper end at most 14/178 (the redesign's
own-unit threshold can only be stricter). RULE_3's additions and I4's remaining invalid bounds are
left out (each can only add to the count).

**What the figures are** (Codex, night round 1; the record ``d2f-decision-value.json``, written
before this note, names them ``p_route_upper_bound`` and is kept as written): **a predictive
estimate conditional on the shared Beta model, the historical classifications used and two sets
of exactly 178 eligible**: about 0.113865 on the upper count and 0.314705 on the strict. **No upper
bound for a run on generator version 2 has been shown**: version 2 changes durations, depths and
other quantities, and it is not shown that the change only adds blockers. The step-7 marginals
and a future joint probability are Monte Carlo estimates, so the inequality between true
probabilities does not make them deterministic bounds of the implemented classification.

Writes ``d2f-decision-value.json`` once; prints the numbers. Usage (from the project root):
``.venv/Scripts/python.exe -B docs/validation/v0.5.5/d2f_decision_value.py``
"""

from __future__ import annotations

import gzip
import json
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import r1_common as rc  # noqa: E402

STEP7 = ROOT / "docs/validation/v0.5.4/h2-step7-sinusoid.json"
STEP1 = ROOT / "docs/validation/v0.5.4/h2-step1-floor.json"
STEP1_CASES = ROOT / ".cache/v054/step1/cases.json"
SHARDS = ROOT / ".cache/v054/step7/82479013a6b08c0b/shards"
OUT_FILE = HERE / "d2f-decision-value.json"
N_SET = 178  # round 3's eligible per 200 attempted (the design's sizing)
SIN_J_TRUE, SIN_J_BAND_TOP = rc.REQUIRED - 0.01, rc.REQUIRED + 0.01
DRAWS = 400_000
SEED = 20261120


def step7_records() -> list:
    out = []
    for f in sorted(SHARDS.glob("*.bin")):
        raw = f.read_bytes()
        try:
            raw = gzip.decompress(raw)
        except OSError:
            pass
        out += [json.loads(x) for x in raw.decode().splitlines() if x.strip()]
    return out


def joint_bounds(recs: list) -> dict:
    ok = [r for r in recs if r.get("status") == "OK"]
    bound = {r["index"]: min(min(p, r["p_small_true"]) for p in r["p_flag"].values()) for r in ok}
    return {
        "planets": len(recs),
        "ok": len(ok),
        "sin_j_true_under_any_joint_law": sorted(i for i, b in bound.items() if b < SIN_J_TRUE),
        "sin_j_true_or_unknown": sorted(
            i for i, b in bound.items() if SIN_J_TRUE <= b < SIN_J_BAND_TOP
        ),
        "bound_per_planet_below_0_97": {
            str(i): round(b, 4) for i, b in sorted(bound.items()) if b < 0.97
        },
    }


def data_and_info() -> tuple[set, set]:
    """Step 1's data losses and I4's information-limited planets (fresh set), by index."""
    import hashlib

    import i4_diagnosis

    text = STEP1_CASES.read_text("utf-8")
    want = json.loads(STEP1.read_text("utf-8"))["per_case_detail_sha256"]
    if hashlib.sha256(text.encode()).hexdigest() != want:
        raise SystemExit("step 1's per-case detail does not match its record: STOP")
    data = {
        c["index"]
        for c in json.loads(text)["d2"]
        if any("DATA" in b["categories"] for b in c["blockers"])
    }
    info = {
        r["index"]
        for r in i4_diagnosis.i4_records()
        if r.get("set") == "fresh"
        and r.get("status") == "OK"
        and not r.get("mismatch")
        and not r["nuisance"]["invalid"]
        and r.get("power_nuisance", 1.0) < rc.REQUIRED
    }
    return data, info


def p_route(k_obs: int) -> float:
    pooled = 2 * N_SET
    k_pool = max(k for k in range(pooled + 1) if rc.wilson(k, pooled)[1] <= rc.D2_ROUTE)
    k_set = max(k for k in range(N_SET + 1) if k / N_SET <= rc.D2_ROUTE)
    rng = np.random.default_rng(SEED)
    p = rng.beta(k_obs + 0.5, N_SET - k_obs + 0.5, DRAWS)
    ka, kb = rng.binomial(N_SET, p), rng.binomial(N_SET, p)
    return float(np.mean((ka <= k_set) & (kb <= k_set) & (ka + kb <= k_pool)))


def main() -> None:
    if OUT_FILE.exists():
        raise SystemExit(f"{OUT_FILE.name} exists: the record is written once")
    started = time.process_time()
    d2 = json.loads(STEP7.read_text("utf-8"))["d2"]
    jb = joint_bounds(step7_records())
    if jb["planets"] != d2["planets"]:
        raise SystemExit("step 7's shards do not match its record: STOP")
    fails = set(d2["certificate_fails_planets"])
    sin_j_true = set(jb["sin_j_true_under_any_joint_law"])
    if not sin_j_true >= fails:
        raise SystemExit("a certificate failure is not SIN_J under the bound: STOP")
    data, info = data_and_info()
    if len(data) != d2["data_losses (step 1)"] or len(info) != d2["odd_even_limited (I4)"]:
        raise SystemExit("DATA or INFO differs from step 7's record: STOP")
    if len(data | info | fails) != d2["floor"]:
        raise SystemExit("DATA ∪ INFO ∪ SIN_F differs from step 7's floor: STOP")
    strict = data | info | sin_j_true
    upper = strict | set(jb["sin_j_true_or_unknown"])
    pooled = 2 * N_SET
    doc = {
        "label": "v0.5.5: D2-F's decision-value test, redone (a reading of existing development "
        "records; upper bounds on P(route) for the best variant)",
        "method_status": "not_validated",
        "decision": "the maintainer's decision of 2026-11-20 (night), item 3b (#218)",
        "route_needs": {
            "pooled_upper_count_at_most": max(
                k for k in range(pooled + 1) if rc.wilson(k, pooled)[1] <= rc.D2_ROUTE
            ),
            "of": pooled,
            "each_set_at_most": max(k for k in range(N_SET + 1) if k / N_SET <= rc.D2_ROUTE),
            "of_each": N_SET,
        },
        "round_3": {
            "step7_floor_data_info_sin_f": d2["floor"],
            "step7_certificate_fails": sorted(fails),
            "data_losses_step1": sorted(data),
            "info_limited_i4": sorted(info),
            "joint_bounds": jb,
            "variant_4_strict_lower_bound": len(strict),
            "variant_4_upper_lower_bound": len(upper),
            "i4_invalid_after_the_fix": "0 of 178 (i4-convergence-diagnosis.json, set fresh)",
        },
        "p_route_upper_bound": {
            "on_the_strict_count": p_route(len(strict)),
            "on_the_upper_count": p_route(len(upper)),
        },
        "left_out_each_can_only_lower_p_route": [
            "RULE_3's planets outside DATA, INFO and SIN_J",
            "I4's bounds still invalid after the fix (0 of 178 fresh; 1 of 112 in v0.5.2's set)",
            "generator version 2's change of the star (not measured on these planets)",
        ],
        "draws": DRAWS,
        "seed": SEED,
    }
    used = time.process_time() - started
    doc["cpu_hours"] = round(used / 3600.0, 4)
    OUT_FILE.write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n", "utf-8", newline="\n")
    print(json.dumps({k: doc[k] for k in ("route_needs", "p_route_upper_bound")}, indent=1))
    import ledger_v055 as lv  # last: it binds budgeted to v0.5.5's ledger

    lv.charge(
        f"d2f_decision_value_{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}",
        used / 3600.0,
        f"d2f_decision_value.py: process time {used:.1f} s",
    )
    print("variant 4 lower bounds: strict", len(strict), "upper", len(upper))


if __name__ == "__main__":
    main()
