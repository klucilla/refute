"""v0.5.2 stage 2: D2's what-if again, severity-aware (Codex, forecast round 2, finding 6).
A new derived record; ``forecast-v4-paths.json`` stays as committed. Reads the D2/D4
forecast's and the diagnosis's records; runs no curve. **A what-if; it decides nothing.**
``method_status: not_validated``.

The D2 records keep no severity, so each scenario is read twice: every FAIL blocks (the
committed reading), and a FAIL of a test that is always a warning gives WEAKENED, which is
kept (as in ``forecast_t2a_paths.py``). A planet the battery REFUTED stays lost. The
``odd_even`` sensitivity blocker is removed either only on diagnosed curves whose power at
the Cramer-Rao error reaches the rule's threshold ("bound-supported") or on every curve (an
upper bound).

Usage: ``.venv/Scripts/python.exe <this file>``; writes ``forecast-v4-paths-r2.json``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(HERE))
import forecast_v4 as f  # noqa: E402

KEPT = ("SURVIVED", "WEAKENED")
A0_TESTS = ("odd_even", "aperture_depth", "systematics", "single_event", "event_consistency")
# tests whose severity is always "warning" in version 4's records of the T2a forecast (period_alias
# is fatal or warning there, so it stays a blocker); a warning FAIL gives WEAKENED, which is kept
WARNING_ONLY = frozenset(
    {"duration_excess", "edge_events", "nearby_contamination", "secondary_eclipse", "sinusoid",
     "systematics"}
)  # fmt: skip


def main() -> None:
    import budgeted
    import forecast_v4_diagnosis as d

    from refute.core.sensitivity import gaussian_probability
    from refute.packs.tess.pipeline import expected_by_role

    _, _, p4 = f.plans()
    threshold = p4.gauntlet.odd_even.max_sigma
    dfp = d.fingerprint()
    bound_ok = set()
    for x in budgeted.assembled(
        d.SECTION, d.PART, d.OUT / dfp, d.shard, d.shards(), dfp, d.WORKERS, pin=d.PIN,
        max_shard_seconds=d.MAX_SHARD_SECONDS,
    ).decode().splitlines():  # fmt: skip
        if not x.strip():
            continue
        r = json.loads(x)
        block = (r["v4"].get("sensitivity") or {}).get("main")
        if not block or "sigma_a0_ppm" not in r["v4"]:
            continue
        sigma = r["v4"]["sigma_cr_ppm"] if "sigma_cr_ppm" in r["v4"] else r["sigma_cr_ppm"]
        p = gaussian_probability(block["alternative"], sigma, threshold)
        if p >= block["required_probability"]:
            bound_ok.add(r["index"])
    fp = f.fingerprint()
    recs = [
        json.loads(x)
        for x in budgeted.assembled(
            f.SECTION, f.PART, f.OUT / fp, f.shard, f.shards(), fp, f.WORKERS, pin=f.PIN,
            max_shard_seconds=f.MAX_SHARD_SECONDS,
        ).decode().splitlines() if x.strip()
    ]  # fmt: skip
    eligible = [r for r in recs if r.get("status") == "OK" and r["gate_passed"] and r["identity"]]
    decisive, _ = expected_by_role(p4, False)
    minimum = sum(r["v04"] in KEPT for r in eligible) / len(eligible) - 0.10

    def blockers(r, warning_kept: bool) -> set[tuple]:
        out = set()
        for t in decisive:
            row = r["v4_tests"].get(t, {})
            st = row.get("status")
            if st == "INCONCLUSIVE" or (st == "FAIL" and not (warning_kept and t in WARNING_ONLY)):
                cls = row.get("class") or ("sensitivity" if t == "odd_even" else "none")
                out.add((t, st, cls))
        return out

    def oe_bound(r, b):
        return b[:3] == ("odd_even", "INCONCLUSIVE", "sensitivity") and r["index"] in bound_ok

    def oe_any(r, b):
        return b[:3] == ("odd_even", "INCONCLUSIVE", "sensitivity")

    def sin(r, b):
        return b[0] == "sinusoid" and b[1] == "INCONCLUSIVE"

    scenarios = {
        "as_forecast": lambda r, b: False,
        "a_odd_even_bound_supported": oe_bound,
        "a_odd_even_upper_bound": oe_any,
        "b_sinusoid_inconclusive_removed": sin,
        "c_odd_even_bound_supported_and_sinusoid": lambda r, b: oe_bound(r, b) or sin(r, b),
        "c_odd_even_upper_bound_and_sinusoid": lambda r, b: oe_any(r, b) or sin(r, b),
        "d_every_a0_or_sinusoid_inconclusive": lambda r, b: (
            b[0] in (*A0_TESTS, "sinusoid") and b[1] == "INCONCLUSIVE"
        ),
    }

    def kept(rm, warning_kept: bool) -> int:
        n = 0
        for r in eligible:
            if r["v4"] in KEPT:
                n += 1
            elif r["v4"] == "INCONCLUSIVE":
                n += not {b for b in blockers(r, warning_kept) if not rm(r, b)}
        return n

    out = {
        "label": "D2 what-if, with the warning FAILs read both ways; it decides nothing",
        "method_status": "not_validated",
        "eligible": len(eligible),
        "minimum": minimum,
        "bound_supported_curves": sorted(bound_ok),
        "warning_only_tests": sorted(WARNING_ONLY),
        "note": "the D2 records keep no severity: 'every_fail_blocks' is the committed reading; "
        "'warning_only_fail_kept' lets a FAIL of a test that is always a warning give WEAKENED",
        "scenarios": {
            mode: {
                k: {
                    "kept": kept(fn, wk),
                    "fraction": round(kept(fn, wk) / len(eligible), 4),
                    "meets_minimum": kept(fn, wk) / len(eligible) >= minimum,
                }
                for k, fn in scenarios.items()
            }
            for mode, wk in (("every_fail_blocks", False), ("warning_only_fail_kept", True))
        },  # fmt: skip
    }
    (HERE / "forecast-v4-paths-r2.json").write_text(
        json.dumps(out, indent=1, sort_keys=True) + "\n", "utf-8"
    )
    print(json.dumps(out, indent=1, sort_keys=True))


if __name__ == "__main__":
    main()
