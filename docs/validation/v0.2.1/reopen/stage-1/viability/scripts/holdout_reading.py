"""The viability check of 2026-10-23, item 1c to 1f (read only): the holdout of the true planets
(the R_min study's `constant` scenario, configuration M4-rmin-study, code 2e4ff99's records) in the
measurable band, per noise model and layout regime, read from the archived records without
extracting them (no lot, no curve, no engine run on data):

- each target derived at R = 8 with bs-choice's committed pair (b, s), by the evaluator's own
  functions (`rmin_evaluate.target_outcomes`), under the legacy aggregation (the engine's default)
  and under specification B (X1b, experimental);
- the rounds' INCONCLUSIVE reasons, split into the capacity decisions (decision 1,
  `insufficient_capacity_train`; decision 2, `insufficient_capacity_hidden_noise`), which spec C can
  alter, and every other reason, which it cannot;
- an optimistic, descriptive bound: every capacity-INCONCLUSIVE round counted as PASS (the most
  favourable hypothesis for the delivery of candidates), every other round as recorded; never an
  engine run;
- the check that the legacy reading reproduces the study's committed INCONCLUSIVE counts per group.

The records hold the holdout rounds only (no search, no gauntlet, no global candidate), so the
final verdict and the global candidate's identity are not identifiable from them.

  python holdout_reading.py <archive.zip> <bs-choice-evaluation.json> <study-evaluation.json> <out>
"""

import json
import re
import sys
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

POP = Path(__file__).resolve().parents[4] / "population"
sys.path.insert(0, str(POP))
import rmin_evaluate as ev  # noqa: E402

R = 8
MIN_SNR = 5.0  # HoldoutParams.min_snr, the hidden-year threshold of the study's plan
CAPACITY = {"insufficient_capacity_train", "insufficient_capacity_hidden_noise"}
AGGREGATIONS = {"legacy": "legacy", "spec_b": "spec_b_experimental"}


def regime(index: int) -> str:
    """population_v2._planet_mechanism: 0-99 two_years, 100-149 three_years, 150-199 few_train,
    200-249 variability_some_years."""
    if index < 100 or 150 <= index < 200:
        return "2 years"
    return "3+ years" if index < 150 else "3+ years, variability"


def parse(target: str) -> tuple[str, str, int]:
    case = target.split("/", 1)[1]  # planet-<band>-<noise>-<index>
    _, band, noise, index = case.split("-")
    return band, "white" if noise == "white" else "AR(1)", int(index)


def kind(reason) -> str:
    """A reason's kind: its text before the first number or parenthesis (as the study's summary
    grouped them), so the timing rule's reasons, which carry their hours, form one kind."""
    return re.split(r"[\d(]", str(reason), maxsplit=1)[0].strip()


def outcome_status(rounds: list[tuple[int, str, str | None]], years, aggregation: str) -> str:
    if aggregation == "legacy":
        return ev.aggregate([s for _, s, _ in sorted(rounds)])
    return ev._holdout.spec_b_outcome(rounds, years)["status"]


def main() -> int:
    archive, bs, study, out = (Path(p) for p in sys.argv[1:5])
    pair = json.loads(bs.read_text(encoding="utf-8"))["pairs"][str(R)]
    b, s = float(pair["b"]), float(pair["s"])
    committed = json.loads(study.read_text(encoding="utf-8"))["results"][str(R)]
    cells: dict = defaultdict(
        lambda: {
            "targets": 0,
            **{
                f"{a}_{k}": Counter() for a in AGGREGATIONS for k in ("status", "optimistic_status")
            },
            "inconclusive_rounds_by_kind": Counter(),
            "rounds": 0,
            "targets_inconclusive_by_kind": Counter(),
            "optimistic_still_inconclusive_by_kinds": Counter(),
        }
    )
    reproduce: dict = defaultdict(Counter)
    with zipfile.ZipFile(archive) as z:
        names = [n for n in z.namelist() if n.endswith(".constant.json")]
        for name in names:
            rec = json.loads(z.read(name))
            legacy = ev.target_outcomes(rec, R, b, s, MIN_SNR)
            reproduce[rec["group"]]["targets"] += 1
            reproduce[rec["group"]]["inconclusive"] += legacy["status"] == "INCONCLUSIVE"
            band, noise, index = parse(rec["target"])
            if band != "measurable":
                continue
            c = cells[f"{noise} | {regime(index)}"]
            c["targets"] += 1
            rounds = [
                (d["record"]["hidden_year"], d["status"], d["reason"]) for d in legacy["rounds"]
            ]
            hopeful = [
                (y, "PASS" if (st == "INCONCLUSIVE" and str(rs) in CAPACITY) else st, rs)
                for y, st, rs in rounds
            ]
            for a in AGGREGATIONS:
                c[f"{a}_status"][outcome_status(rounds, rec["years"], a)] += 1
                c[f"{a}_optimistic_status"][outcome_status(hopeful, rec["years"], a)] += 1
            if outcome_status(hopeful, rec["years"], "legacy") == "INCONCLUSIVE":
                left = sorted({kind(rs) for _, st, rs in hopeful if st == "INCONCLUSIVE"})
                c["optimistic_still_inconclusive_by_kinds"][" + ".join(left)] += 1
            c["rounds"] += len(rounds)
            undecided = {str(rs) for _, st, rs in rounds if st == "INCONCLUSIVE"}
            for _, st, rs in rounds:
                if st == "INCONCLUSIVE":
                    c["inconclusive_rounds_by_kind"][kind(rs)] += 1
            if legacy["status"] == "INCONCLUSIVE":
                which = (
                    "capacity only"
                    if undecided <= CAPACITY
                    else "no capacity reason"
                    if not (undecided & CAPACITY)
                    else "capacity and other"
                )
                c["targets_inconclusive_by_kind"][which] += 1
    check = {}
    for group, cnt in sorted(reproduce.items()):
        stored = committed[group]["inconclusive"]["constant"]
        check[group] = {
            "read": [cnt["inconclusive"], cnt["targets"]],
            "committed": [stored["inconclusive_targets"], stored["targets"]],
            "equal": [cnt["inconclusive"], cnt["targets"]]
            == [stored["inconclusive_targets"], stored["targets"]],
        }
    result = {
        "note": __doc__.split("\n\n")[0],
        "r_min": R,
        "pair": {"b": b, "s": s},
        "min_snr": MIN_SNR,
        "capacity_reasons": sorted(CAPACITY),
        "reproduction_check_legacy_constant": check,
        "measurable": {
            k: {kk: dict(vv) if isinstance(vv, Counter) else vv for kk, vv in v.items()}
            for k, v in sorted(cells.items())
        },
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(check, indent=1))
    # the reproduction contract (Codex's review): every group present and equal, else a failure
    if sorted(check) != sorted(ev.GROUPS) or not all(v["equal"] for v in check.values()):
        print("the reading does not reproduce the study's committed counts")
        return 1
    for k, v in result["measurable"].items():
        print(
            k,
            v["targets"],
            "legacy",
            v["legacy_status"],
            "optimistic",
            v["legacy_optimistic_status"],
        )
        print("   spec_b", v["spec_b_status"], "optimistic", v["spec_b_optimistic_status"])
        print("   inconclusive targets by kind", v["targets_inconclusive_by_kind"])
        print("   inconclusive rounds by kind", v["inconclusive_rounds_by_kind"])
        print("   optimistic, still inconclusive", v["optimistic_still_inconclusive_by_kinds"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
