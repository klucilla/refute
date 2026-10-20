"""The decomposition of the interrupted holdout rounds (the maintainer's item 3 of 2026-10-18).

Reads only the record already computed and examined, ``option-a-geometry.json`` (map Amendment 10:
100 planets of the bands near and measurable, prefix ``refute-v0.2.1-option-a-geometry``; only
metadata and synthetic training data were used to make it), and counts every reason of
interruption separately, **per round and per target**, under option O2 (the one chosen). Nothing
is generated or rerun. The rounds are those of that record, computed with the code of its commit
(before pieces 4 and 5 changed the train gate): these counts describe that record, not the
current code.

Writes ``interruptions-decomposition.json`` next to this file and prints a summary.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "option-a-geometry.json"
OPTION = "O2"

# The rules that end a round before the geometry (holdout.plan_round), by their messages.
BEFORE = (
    ("no training data", "no_training_data"),
    ("found no candidate", "no_train_candidate"),
    ("train SNR", "train_snr_below_gate"),
    ("duration/period", "duration_period_ratio_above_max"),
    ("train transit times", "too_few_train_transit_times"),
    ("timing uncertainty", "timing_uncertainty_above_one_duration"),
    ("transit windows cover", "hidden_window_fraction_above_max"),
)


def before_reasons(message: str) -> list[str]:
    found = [code for text, code in BEFORE if text in message]
    return found or ["other: " + message[:60]]


def main() -> None:
    record = json.loads(SOURCE.read_text(encoding="utf-8"))
    rows = []
    for case in record["cases"]:
        for r in case["rounds"]:
            if "decided_before" in r:
                stage, reasons = "before_geometry", before_reasons(r["decided_before"])
            elif r[OPTION]["inconclusive"]:
                stage, reasons = "geometry", list(r[OPTION]["reasons"])
            else:
                stage, reasons = "reaches_measurement", []
            rows.append(
                {
                    "case": case["id"],
                    "noise": case["noise"],
                    "band": case["id"].split("-")[1],
                    "mechanism": case.get("mechanism"),
                    "year": r["year"],
                    "stage": stage,
                    "reasons": reasons,
                    "n_replicas": None if stage == "before_geometry" else r[OPTION]["n_replicas"],
                }
            )

    def tally(selected):
        out = {"rounds": len(selected), "by_stage": Counter(x["stage"] for x in selected)}
        each = Counter(reason for x in selected for reason in x["reasons"])
        out["each_reason"] = dict(sorted(each.items()))
        combos = Counter(" + ".join(x["reasons"]) or "none" for x in selected)
        out["reason_combinations"] = dict(sorted(combos.items()))
        out["by_stage"] = dict(sorted(out["by_stage"].items()))
        return out

    per_round = {"all": tally(rows)}
    for key in ("noise", "band", "mechanism"):
        for value in sorted({str(x[key]) for x in rows}):
            per_round[f"{key}={value}"] = tally([x for x in rows if str(x[key]) == value])

    targets = {}
    for x in rows:
        targets.setdefault(x["case"], []).append(x)
    per_target_rows = []
    for case, rounds in sorted(targets.items()):
        reaches = sum(1 for x in rounds if x["stage"] == "reaches_measurement")
        per_target_rows.append(
            {
                "case": case,
                "noise": rounds[0]["noise"],
                "band": rounds[0]["band"],
                "mechanism": rounds[0]["mechanism"],
                "rounds": len(rounds),
                "rounds_reaching_measurement": reaches,
                "every_round_interrupted": reaches == 0,
                "reasons_of_its_rounds": sorted(
                    {reason for x in rounds for reason in x["reasons"]}
                ),
            }
        )

    def target_tally(selected):
        out = {
            "targets": len(selected),
            "with_at_least_one_round_reaching_measurement": sum(
                1 for t in selected if not t["every_round_interrupted"]
            ),
            "every_round_interrupted": sum(1 for t in selected if t["every_round_interrupted"]),
        }
        each = Counter(
            reason
            for t in selected
            if t["every_round_interrupted"]
            for reason in t["reasons_of_its_rounds"]
        )
        out["reasons_among_targets_with_every_round_interrupted"] = dict(sorted(each.items()))
        return out

    per_target = {"all": target_tally(per_target_rows)}
    for key in ("noise", "band", "mechanism"):
        for value in sorted({str(t[key]) for t in per_target_rows}):
            per_target[f"{key}={value}"] = target_tally(
                [t for t in per_target_rows if str(t[key]) == value]
            )

    out = {
        "source": SOURCE.name,
        "option": OPTION,
        "note": "counts of rounds and of targets of the examined record; not a C3 rate",
        "per_round": per_round,
        "per_target": per_target,
        "rounds": rows,
        "targets": per_target_rows,
    }
    (HERE / "interruptions-decomposition.json").write_text(
        json.dumps(out, indent=2, sort_keys=True, default=dict) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps({"per_round": per_round["all"], "per_target": per_target["all"]}, indent=2))
    for key in sorted(per_round):
        if key != "all":
            print(key, per_round[key]["by_stage"], per_round[key]["each_reason"])
    for key in sorted(per_target):
        if key != "all":
            print("T", key, {k: v for k, v in per_target[key].items()})


if __name__ == "__main__":
    main()
