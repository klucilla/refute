"""X0a and X0b, exactly as declared in docs/validation/v0.2.1/reopen/stage-1/x0/DECLARATION.md
(commit ccd43f2): read-only analyses of the R_min study's records with the study's code (2e4ff99).

Run with run-with-study-code.ps1. Usage:
  python x0.py <study run folder> <record-digests.json> <bs-choice-evaluation.json> <out (new)>
"""

import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

# the diagnosis's script, committed at ../../rmin-study/diagnosis/scripts (as run, it sat beside
# this file in .cache/merge-v021/rmin)
sys.path.insert(
    0, str(Path(__file__).resolve().parents[3] / "rmin-study" / "diagnosis" / "scripts")
)
import diagnosis as dg  # noqa: E402  (the diagnosis's gate_of, kind, labels; the study's code)

ev, rs = dg.ev, dg.rs
QS = (0.05, 0.25, 0.5, 0.75, 0.95)


def aggregate_b(statuses: list[str]) -> str:
    """Specification B, B2: any FAIL gives FAIL; PASS only when every year's round is PASS."""
    if "FAIL" in statuses:
        return "FAIL"
    if statuses and all(s == "PASS" for s in statuses):
        return "PASS"
    return "INCONCLUSIVE"


def gate_name(d) -> tuple[str, str]:
    gi, sub = dg.gate_of(d, d["record"])
    return (dg.GATES[gi] if gi >= 0 else "unclassified"), sub


def completeness(records) -> None:
    for rec in records:
        years = sorted(r["hidden_year"] for r in rec["rounds"])
        if years != sorted(set(rec["years"])) or len(years) != len(set(years)):
            raise SystemExit(
                f"{rec['target']} {rec['scenario']}: rounds {years} for {rec['years']}"
            )


def main() -> int:
    run_dir, digests, bs_eval, out = (Path(a) for a in sys.argv[1:5])
    out.mkdir(parents=True, exist_ok=False)
    data = rs.load_lot(run_dir)
    dg.check_digests(run_dir, digests, data)
    records = data["records"]
    completeness(records)
    pairs = json.loads(bs_eval.read_text(encoding="utf-8"))["pairs"]
    x0a, x0b = {}, {}
    for r_min in ev.R_VALUES:
        pair = pairs[str(r_min)]
        a_cells = defaultdict(
            lambda: {
                "pass_targets": 0,
                "decided": 0,
                "last_round_gate": Counter(),
                "passing_year_position": Counter(),
                "s_meas_pass": [],
                "years_pass_targets": Counter(),
                "years_decided": Counter(),
                "targets": [],
            }
        )
        b_cells = defaultdict(
            lambda: {
                "total": 0,
                "today": Counter(),
                "b": Counter(),
                "transitions": Counter(),
                "b_inconclusive_with_no_window_year": 0,
                "b_inconclusive_only_no_window": 0,
                "turned_with_no_window_year": 0,
                "turned_only_no_window": 0,
                "turned_undecided_years": Counter(),
            }
        )
        for rec in records:
            o = ev.target_outcomes(rec, r_min, pair["b"], pair["s"], dg.MIN_SNR)
            g, sc = rec["group"], rec["scenario"]
            cell = f"{g}|{sc}"
            rounds = o["rounds"]
            statuses = [d["status"] for d in rounds]
            today = o["status"]
            new = aggregate_b(statuses)
            # X0b
            b = b_cells[cell]
            b["total"] += 1
            b["today"][today] += 1
            b["b"][new] += 1
            b["transitions"][f"{today}->{new}"] += 1
            if new == "INCONCLUSIVE":
                undecided = [d for d in rounds if d["status"] == "INCONCLUSIVE"]
                kinds = {dg.kind(d["reason"]) for d in undecided}
                has_nw = "no_predicted_window" in kinds
                only_nw = has_nw and kinds == {"no_predicted_window"}
                b["b_inconclusive_with_no_window_year"] += has_nw
                b["b_inconclusive_only_no_window"] += only_nw
                if today == "PASS":
                    b["turned_with_no_window_year"] += has_nw
                    b["turned_only_no_window"] += only_nw
                    for d in undecided:
                        gname, sub = gate_name(d)
                        b["turned_undecided_years"][f"{gname}:{sub}"] += 1
            # X0a
            if sc == "disappearing":
                a = a_cells[g]
                n_years = len(rec["years"])
                if today in ("PASS", "FAIL"):
                    a["decided"] += 1
                    a["years_decided"][str(n_years)] += 1
                if today == "PASS":
                    a["pass_targets"] += 1
                    a["years_pass_targets"][str(n_years)] += 1
                    last_year = max(rec["years"])
                    years_sorted = sorted(rec["years"])
                    last = o["last_round"]
                    lg, lsub = gate_name(last)
                    a["last_round_gate"][f"{lg}:{lsub}"] += 1
                    per_round = []
                    for d in rounds:
                        rr = d["record"]
                        gname, sub = gate_name(d)
                        entry = {
                            "hidden_year": rr["hidden_year"],
                            "status": d["status"],
                            "gate": gname,
                            "reason_kind": sub,
                        }
                        if d["status"] == "PASS":
                            entry["s_meas"] = rr.get("s_meas")
                            a["s_meas_pass"].append(rr.get("s_meas"))
                            pos = len(years_sorted) - 1 - years_sorted.index(rr["hidden_year"])
                            a["passing_year_position"][
                                "last year" if pos == 0 else f"{pos} year(s) before the last"
                            ] += 1
                        per_round.append(entry)
                    a["targets"].append(
                        {
                            "target": rec["target"],
                            "years": rec["years"],
                            "last_year": last_year,
                            "rounds": per_round,
                        }
                    )
        x0a[str(r_min)] = {
            g: {
                "pass_targets": a["pass_targets"],
                "decided_disappearing_targets": a["decided"],
                "last_round_gate": dict(a["last_round_gate"].most_common()),
                "passing_year_position": dict(a["passing_year_position"]),
                "s_meas_of_pass_rounds": {
                    "n": len(a["s_meas_pass"]),
                    **(
                        {f"q{int(q * 100)}": float(np.quantile(a["s_meas_pass"], q)) for q in QS}
                        if a["s_meas_pass"]
                        else {}
                    ),
                },
                "observing_years_of_pass_targets": dict(a["years_pass_targets"]),
                "observing_years_of_decided_targets": dict(a["years_decided"]),
                "targets": a["targets"],
            }
            for g, a in sorted(a_cells.items())
        }
        cells = {}
        for cell, b in sorted(b_cells.items()):
            sc = cell.split("|")[1]
            dec_t = b["today"]["PASS"] + b["today"]["FAIL"]
            dec_b = b["b"]["PASS"] + b["b"]["FAIL"]
            entry = {
                "total": b["total"],
                "today": dict(b["today"]),
                "spec_b": dict(b["b"]),
                "transitions": dict(b["transitions"]),
                "decided_over_total": {
                    "today": dg.frac(dec_t, b["total"]),
                    "spec_b": dg.frac(dec_b, b["total"]),
                },
                "b_inconclusive_with_a_no_window_year": b["b_inconclusive_with_no_window_year"],
                "b_inconclusive_with_only_no_window_years": b["b_inconclusive_only_no_window"],
                "turned_pass_to_inconclusive": b["transitions"]["PASS->INCONCLUSIVE"],
                "turned_with_a_no_window_year": b["turned_with_no_window_year"],
                "turned_with_only_no_window_years": b["turned_only_no_window"],
                "turned_undecided_years_by_gate": dict(b["turned_undecided_years"].most_common()),
            }
            if sc == "constant":
                for rule, c, dec in (("today", b["today"], dec_t), ("spec_b", b["b"], dec_b)):
                    entry[f"false_fail_{rule}"] = {
                        "fail": c["FAIL"],
                        "over_decided": dg.frac(c["FAIL"], dec),
                        "over_total": dg.frac(c["FAIL"], b["total"]),
                    }
            elif sc == "disappearing":
                for rule, c, dec in (("today", b["today"], dec_t), ("spec_b", b["b"], dec_b)):
                    entry[f"false_pass_{rule}"] = {
                        "pass": c["PASS"],
                        "over_decided": dg.frac(c["PASS"], dec),
                        "over_total": dg.frac(c["PASS"], b["total"]),
                        "fail_over_decided": dg.frac(c["FAIL"], dec),
                    }
            else:
                entry["note"] = "weakened: PASS and FAIL without an error label"
            cells[cell] = entry
        x0b[str(r_min)] = cells
    for name, content in (("x0a.json", x0a), ("x0b.json", x0b)):
        (out / name).write_text(
            json.dumps(content, indent=1) + "\n", encoding="utf-8", newline="\n"
        )
        print(name, hashlib.sha256((out / name).read_bytes()).hexdigest())
    return 0


if __name__ == "__main__":
    sys.exit(main())
