"""v0.5.2 stage 2: what the T2a forecast implies for the maintainer's paths (decision of
2026-11-10, second set, item 2). Reads the T2a forecast's records (``forecast_t2a.py``); runs no
curve. **A what-if; it decides nothing.** ``method_status: not_validated``.

For version 3 and version 4 B (the selector certified, the refusal above 20 sectors kept), every
loss's decisive blockers, and T2a's kept fraction if a set of INCONCLUSIVE blockers were removed,
keeping every other blocker. A warning FAIL gives WEAKENED, which is kept, so only an INCONCLUSIVE
or a fatal FAIL blocks. The stratum above 20 sectors was not run (``forecast_t2a.py``); each
scenario is reported with it all lost and all kept, which bounds it both ways. The removals are
scenarios, not designs.

Usage: ``.venv/Scripts/python.exe <this file>``; writes ``forecast-t2a-paths.json``.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(HERE))
import budgeted  # noqa: E402
import forecast_t2a as t  # noqa: E402

KEPT = ("SURVIVED", "WEAKENED")
A0_TESTS = ("odd_even", "aperture_depth", "systematics", "single_event", "event_consistency")
MEASURED = ("2_to_4", "5_to_20")


def _inc(*names: str, cls: str | None = None):
    def rm(x: tuple) -> bool:
        return x[0] in names and x[1] == "INCONCLUSIVE" and (cls is None or x[2] == cls)

    return rm


SCENARIOS = {
    "as_run": lambda x: False,
    "a_odd_even_inconclusive_removed": _inc("odd_even"),
    "b_sinusoid_inconclusive_removed": _inc("sinusoid"),
    "c_odd_even_and_sinusoid": _inc("odd_even", "sinusoid"),
    "d_systematics_sensitivity_rule_removed": _inc("systematics", cls="insufficient_sensitivity"),
    "e_systematics_inconclusive_removed": _inc("systematics"),
    "f_odd_even_sinusoid_and_systematics_sensitivity": lambda x: (
        _inc("odd_even", "sinusoid")(x) or _inc("systematics", cls="insufficient_sensitivity")(x)
    ),
    "g_odd_even_sinusoid_and_systematics": _inc("odd_even", "sinusoid", "systematics"),
    "h_every_sensitivity_rule_inconclusive": lambda x: (
        x[1] == "INCONCLUSIVE" and x[2] == "insufficient_sensitivity"
    ),
    "i_every_inconclusive": lambda x: x[1] == "INCONCLUSIVE",
    "j_every_inconclusive_but_systematics_not_enough_data": lambda x: (
        x[1] == "INCONCLUSIVE" and not (x[0] == "systematics" and x[2] == "not_enough_data")
    ),
}


def main() -> None:
    fp = t.fingerprint()
    data = budgeted.assembled(
        t.SECTION, t.PART, t.OUT / fp, t.shard, t.shards(), fp, t.WORKERS, pin=t.PIN,
        max_shard_seconds=t.MAX_SHARD_SECONDS,
    )  # fmt: skip
    recs = [json.loads(x) for x in data.decode().splitlines() if x.strip()]
    recs = [r for r in recs if r.get("status") == "OK" and not r.get("compat_problems")]
    rows = t.population()
    pop = Counter(r["stratum"] for r in rows)
    v04_population = sum(r["v04_stage"] in KEPT for r in rows)
    minimum = v04_population / len(rows) - 0.10

    def blockers(r: dict, b: str) -> set[tuple]:
        out = set()
        for name in r[b]["decisive"]:
            row = r[b]["tests"].get(name, {})
            if name in r[b]["deferred"]:
                continue
            if row.get("status") == "INCONCLUSIVE" or (
                row.get("status") == "FAIL" and row.get("severity") == "fatal"
            ):
                out.add((name, row["status"], row.get("inconclusive_class")))
        return out

    out: dict = {
        "label": "what the T2a forecast implies for the paths; a what-if, it decides nothing",
        "method_status": "not_validated",
        "minimum": minimum,
        "population": dict(pop),
        "measured_records": len(recs),
        "note": "the stratum above 20 sectors (56 of 615) was not run: every scenario's point is "
        "given with it all lost and all kept; a warning FAIL gives WEAKENED (kept); the upper "
        "sampling bound is the forecast's stratified hypergeometric upper end with that stratum "
        "all kept, a sampling statement, not a point",
        "batteries": {},
    }
    for b in ("v3", "v4B"):
        classes, single = Counter(), Counter()
        for r in recs:
            if r["v04"]["stage_verdict"] not in KEPT or r[b]["stage_verdict"] in KEPT:
                continue
            bl = blockers(r, b)
            for x in bl:
                classes[f"{r['stratum']}: {x[0]} {x[1]} {x[2] or ''}".strip()] += 1
            if len(bl) == 1:
                x = next(iter(bl))
                single[f"{r['stratum']}: {x[0]} {x[1]} {x[2] or ''}".strip()] += 1
        block: dict = {
            "loss_blockers_overlapping": dict(sorted(classes.items())),
            "loss_single_blockers": dict(sorted(single.items())),
            "scenarios": {},
        }
        for name, rm in SCENARIOS.items():
            per, upper = {}, 0
            for s in MEASURED:
                mine = [r for r in recs if r["stratum"] == s]
                k = 0
                for r in mine:
                    if r[b]["stage_verdict"] in KEPT:
                        k += 1
                    elif r[b]["stage_verdict"] == "INCONCLUSIVE":
                        k += not {x for x in blockers(r, b) if not rm(x)}
                per[s] = round(k / len(mine), 4)
                # the forecast's own stratified interval (alpha over the three strata)
                upper += t._hypergeometric(k, len(mine), pop[s], t.ALPHA / len(t.STRATA))[1]
            low = sum(pop[s] * per[s] for s in MEASURED) / len(rows)
            high = low + pop["above_20"] / len(rows)
            # share of the stratum above 20 that would have to be kept for the point to reach it
            need = (minimum - low) * len(rows) / pop["above_20"]
            block["scenarios"][name] = {
                "per_stratum": per,
                "kept_above_20_all_lost": round(low, 4),
                "kept_above_20_all_kept": round(high, 4),
                "share_above_20_kept_needed": round(min(max(need, 0.0), 1.0), 3)
                if need <= 1 else None,
                "upper_sampling_bound_above_20_all_kept": round(
                    (upper + pop["above_20"]) / len(rows), 4
                ),
                "meets_minimum": "yes" if low >= minimum else "no" if high < minimum else
                f"only if {need:.0%} of the stratum above 20 is kept",
            }  # fmt: skip
        out["batteries"][b] = block
    (HERE / "forecast-t2a-paths.json").write_text(
        json.dumps(out, indent=1, sort_keys=True) + "\n", "utf-8"
    )
    print(json.dumps({b: {k: (v["kept_above_20_all_lost"], v["kept_above_20_all_kept"],
                              v["upper_sampling_bound_above_20_all_kept"], v["meets_minimum"])
                          for k, v in x["scenarios"].items()}
                      for b, x in out["batteries"].items()}, indent=1))  # fmt: skip


if __name__ == "__main__":
    main()
