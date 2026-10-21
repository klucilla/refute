"""Read-only diagnosis of the weakening criterion's n = 0 (R_min study, evaluated at 2e4ff99):
for each R with its bs-choice pair, the capacity threshold that decisions 1 and 2 use, and the
weakened targets whose last round passes both decisions, with their S_pred,2 against the filter
0.3 * S_pred,2 <= 3 (S_pred,2 <= 10). Also the same counts on the constant scenario.

Run with run-with-study-code.ps1. Usage: python diag_weakening.py <run folder> <bs eval> <out>
"""

import collections
import json
import sys
from pathlib import Path

WT = Path("C:/Projetos/refute/.cache/wt-v021")
sys.path.insert(0, str(WT / "docs/validation/v0.2.1/population"))
import rmin_evaluate as ev  # noqa: E402
import rmin_study as rs  # noqa: E402

from refute.packs.tess.holdout import capacity_threshold  # noqa: E402


def main() -> int:
    run_dir, bs_file, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    plan = rs.v3._plan()
    min_snr = plan.gauntlet.holdout_by_year.min_snr
    pairs = json.loads(bs_file.read_text(encoding="utf-8"))["pairs"]
    records = rs.load_lot(run_dir)["records"]
    weakened = [r for r in records if r["scenario"] == "weakened"]
    report = {"min_snr": min_snr, "weakened_targets": len(weakened), "by_r": {}}
    for r_min in ev.R_VALUES:
        pair = pairs[str(r_min)]
        if pair is None:
            report["by_r"][str(r_min)] = None
            continue
        thresholds = {n: capacity_threshold(min_snr, pair["b"], pair["s"], n) for n in (2, 3, 4)}
        rows = collections.defaultdict(lambda: collections.Counter())
        s2_values = collections.defaultdict(list)
        for rec in weakened:
            o = ev.target_outcomes(rec, r_min, pair["b"], pair["s"], min_snr)
            last = o["last_round"]
            g = rec["group"]
            rows[g]["targets"] += 1
            reason = (
                "no_last_round"
                if last is None
                else (
                    "decisions_pass" if ev._passes_decisions(last) else f"stops: {last['reason']}"
                )
            )
            key = (
                reason
                if not reason.startswith("stops:")
                else (
                    "stops: " + "".join(ch for ch in reason[7:] if not ch.isdigit()).split(" ")[0]
                )
            )
            rows[g][key] += 1
            if last is not None and ev._passes_decisions(last):
                s2 = last["record"].get("s_pred_2")
                s2_values[g].append(s2)
                if ev._finite(s2) and ev.WEAKENED_S * s2 <= ev.WEAKENING_FILTER:
                    rows[g]["decisions_pass_and_filter"] += 1
        report["by_r"][str(r_min)] = {
            "pair": pair,
            "capacity_threshold_by_n_years": thresholds,
            "groups": {
                g: {
                    "counts": dict(c),
                    "s_pred_2_of_decision_passing": (
                        {
                            "n": len(s2_values[g]),
                            "min": min(s2_values[g]),
                            "max": max(s2_values[g]),
                        }
                        if s2_values[g]
                        else None
                    ),
                }
                for g, c in rows.items()
            },
        }
    out.write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(report, indent=1)[:9000])
    return 0


if __name__ == "__main__":
    sys.exit(main())
