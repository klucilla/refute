"""v0.5.2 stage 2: what the odd_even diagnosis implies for D2 (the maintainer's decision of
2026-11-10, second set, item 2 (b)). Reads the diagnosis and the forecast's records; runs no curve.
**A what-if; it decides nothing.** ``method_status: not_validated``.

1. **Power.** For each diagnosed curve, the sensitivity rule's probability of detecting #185's
   alternative (``gaussian_probability``, the test's own threshold), with version 4's A0 error,
   with the box's true error, and with the Cramer-Rao error: would an efficient, calibrated
   estimator at the bound (or the box with its true error) have made ``odd_even`` decisive?
2. **D2, what-if.** For every eligible planet of the forecast, version 4's decisive blockers; D2's
   kept fraction if a set of blockers were removed, keeping every other blocker. The removals are
   scenarios, not designs: (a) ``odd_even`` INCONCLUSIVE by the sensitivity rule, only on curves
   whose power at the Cramer-Rao error reaches the threshold (diagnosed curves) or on all such
   curves (an upper bound); (b) the sinusoid INCONCLUSIVE; (c) both; (d) every A0-dependent or
   sinusoid blocker (the rest of the battery alone).

Usage: ``.venv/Scripts/python.exe <this file>``; writes ``forecast-v4-paths.json``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(HERE))
import budgeted  # noqa: E402
import forecast_v4 as f  # noqa: E402
import forecast_v4_diagnosis as d  # noqa: E402

KEPT = ("SURVIVED", "WEAKENED")
A0_TESTS = ("odd_even", "aperture_depth", "systematics", "single_event", "event_consistency")


def main() -> None:
    from refute.core.sensitivity import gaussian_probability
    from refute.packs.tess.pipeline import expected_by_role

    _, _, p4 = f.plans()
    threshold = p4.gauntlet.odd_even.max_sigma
    fp = d.fingerprint()
    diag = [
        json.loads(x)
        for x in budgeted.assembled(
            d.SECTION, d.PART, d.OUT / fp, d.shard, d.shards(), fp, d.WORKERS, pin=d.PIN,
            max_shard_seconds=d.MAX_SHARD_SECONDS,
        ).decode().splitlines() if x.strip()
    ]  # fmt: skip
    power = {}
    rows = []
    for r in diag:
        block = (r["v4"].get("sensitivity") or {}).get("main")
        if not block or "sigma_a0_ppm" not in r["v4"]:
            continue
        alt, need = block["alternative"], block["required_probability"]
        p = {
            k: gaussian_probability(alt, r["v4"][s] if s in r["v4"] else r[s], threshold)
            for k, s in (
                ("a0", "sigma_a0_ppm"), ("box_true", "sigma_box_true_ppm"), ("cr", "sigma_cr_ppm"),
            )
        }  # fmt: skip
        power[r["index"]] = {**p, "required": need}
        rows.append(
            {"index": r["index"], "group": r["group"], **{k: round(v, 3) for k, v in p.items()}}
        )
    out: dict = {
        "label": "what the odd_even diagnosis implies for D2; a what-if, it decides nothing",
        "method_status": "not_validated",
        "power": {},
    }
    for group in ("inconclusive", "control"):
        mine = [x for x in rows if x["group"] == group]
        out["power"][group] = {
            "n": len(mine),
            "reach_threshold_with": {
                k: sum(power[x["index"]][k] >= power[x["index"]]["required"] for x in mine)
                for k in ("a0", "box_true", "cr")
            },
        }
    out["power_per_curve"] = rows
    fpf = f.fingerprint()
    recs = [
        json.loads(x)
        for x in budgeted.assembled(
            f.SECTION, f.PART, f.OUT / fpf, f.shard, f.shards(), fpf, f.WORKERS, pin=f.PIN,
            max_shard_seconds=f.MAX_SHARD_SECONDS,
        ).decode().splitlines() if x.strip()
    ]  # fmt: skip
    eligible = [r for r in recs if r.get("status") == "OK" and r["gate_passed"] and r["identity"]]
    decisive, _ = expected_by_role(p4, False)
    v04_kept = sum(r["v04"] in KEPT for r in eligible)
    minimum = v04_kept / len(eligible) - 0.10

    def blockers(r) -> set[str]:
        out_ = set()
        for t in decisive:
            row = r["v4_tests"].get(t, {})
            if row.get("status") in ("FAIL", "INCONCLUSIVE"):
                cls = row.get("class") or ("sensitivity" if t == "odd_even" else "none")
                out_.add(f"{t}:{row['status']}:{cls}")
        return out_

    def kept(remove) -> int:
        n = 0
        for r in eligible:
            if r["v4"] in KEPT:
                n += 1
                continue
            left = {b for b in blockers(r) if not remove(r, b)}
            if r["v4"] == "INCONCLUSIVE" and not left:
                n += 1
        return n

    def odd_even_cr(r, b) -> bool:
        p = power.get(r["index"])
        return (
            b == "odd_even:INCONCLUSIVE:sensitivity" and p is not None and p["cr"] >= p["required"]
        )

    def odd_even_any(r, b) -> bool:
        return b == "odd_even:INCONCLUSIVE:sensitivity"

    def sinusoid(r, b) -> bool:
        return b.startswith("sinusoid:INCONCLUSIVE")

    def a0_or_sinusoid(r, b) -> bool:
        return b.split(":")[0] in (*A0_TESTS, "sinusoid") and ":INCONCLUSIVE:" in b

    scenarios = {
        "as_forecast": lambda r, b: False,
        "a_odd_even_at_the_cramer_rao_error": odd_even_cr,
        "a_odd_even_sensitivity_removed_upper_bound": odd_even_any,
        "b_sinusoid_inconclusive_removed": sinusoid,
        "c_a_upper_bound_and_b": lambda r, b: odd_even_any(r, b) or sinusoid(r, b),
        "d_every_a0_or_sinusoid_inconclusive_removed": a0_or_sinusoid,
    }
    out["d2"] = {
        "eligible": len(eligible),
        "minimum": minimum,
        "v04_kept": v04_kept / len(eligible),
        "scenarios": {
            k: {
                "kept": kept(fn) / len(eligible),
                "meets_minimum": kept(fn) / len(eligible) >= minimum,
            }
            for k, fn in scenarios.items()
        },
        "note": "a planet only REFUTED or FAILed by a decisive test stays lost in every scenario",
    }
    (HERE / "forecast-v4-paths.json").write_text(
        json.dumps(out, indent=1, sort_keys=True) + "\n", "utf-8"
    )
    print(json.dumps({k: out[k] for k in ("power", "d2")}, indent=1, sort_keys=True))


if __name__ == "__main__":
    main()
