"""X0c, exactly as declared in docs/validation/v0.2.1/reopen/stage-1/x0c/DECLARATION.md: the
constant scenario's false FAIL at R = 8 and R = 20, read only from the R_min study's records with
the study's code (2e4ff99).

Run with run-with-study-code.ps1. Usage:
  python x0c.py <study run folder> <record-digests.json> <bs-choice-evaluation.json> <out (new)>
"""

import hashlib
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

# the diagnosis's script, committed at ../../rmin-study/diagnosis/scripts (as run, it sat beside
# this file in .cache/merge-v021/rmin)
sys.path.insert(
    0, str(Path(__file__).resolve().parents[3] / "rmin-study" / "diagnosis" / "scripts")
)
import diagnosis as dg  # noqa: E402

from refute.packs.tess.holdout import CAPACITY_K, capacity_threshold, fail_rule  # noqa: E402

ev = dg.ev
R_READ = (8, 20)
QS = (0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99)
MAD = 1.4826


def fin(x) -> bool:
    return dg.finite(x)


def completeness(records) -> None:
    for rec in records:
        years = sorted(r["hidden_year"] for r in rec["rounds"])
        if years != sorted(set(rec["years"])) or len(years) != len(set(years)):
            raise SystemExit(
                f"{rec['target']} {rec['scenario']}: rounds {years} for {rec['years']}"
            )


def split(r: dict) -> dict:
    """The derived quantities of item 4 of the declaration, from one record."""
    d_train, e_train = r.get("d_train"), r.get("e_train")
    d_hidden, e_hidden, d_twin = r.get("d_hidden"), r.get("e_hidden"), r.get("d_twin")
    out = {}
    if fin(d_train) and fin(e_train):
        d_c = d_train - CAPACITY_K * e_train
        out["d_c"] = d_c
        for k in (1, 2):
            s = r.get(f"s_pred_{k}")
            out[f"e_pred_{k}"] = d_c / s if fin(s) and s != 0 else None
    if fin(e_hidden) and fin(e_train):
        sigma = math.sqrt(e_train**2 + e_hidden**2)
        out["sigma"] = sigma
        if out.get("e_pred_2") is not None and out["e_pred_2"] != 0:
            out["e_hidden_over_e_pred_2"] = e_hidden / out["e_pred_2"]
        out["e_hidden_over_e_train"] = e_hidden / e_train if e_train else None
        twin_ok = r.get("twin_status") == "ok" and fin(d_twin)
        if twin_ok and fin(d_hidden) and fin(d_train) and sigma > 0:
            out["z_train"] = (d_train - d_twin) / sigma
            out["z_hidden"] = (d_twin - d_hidden) / sigma
            out["pull_hidden"] = (d_twin - d_hidden) / e_hidden if e_hidden > 0 else None
        if fin(d_hidden) and fin(d_train) and d_train:
            out["d_hidden_over_d_train"] = d_hidden / d_train
            if twin_ok:
                out["d_twin_over_d_train"] = d_twin / d_train
    return out


def cause(q: dict, r: dict) -> str:
    if not (r.get("twin_status") == "ok" and fin(r.get("d_twin"))) or "z_train" not in q:
        return "twin unavailable"
    zt, zh = q["z_train"] >= 3.0, q["z_hidden"] >= 3.0
    if zh and not zt:
        return "hidden measurement"
    if zt and not zh:
        return "train or windows"
    if zt and zh:
        return "both"
    return "sum only"


def quantiles(values: list) -> dict:
    v = [x for x in values if fin(x)]
    out = {"n": len(v)}
    if v:
        out.update({f"q{round(q * 100)}": float(np.quantile(v, q)) for q in QS})
    return out


def rank(value, values) -> float | None:
    v = [x for x in values if fin(x)]
    if not fin(value) or not v:
        return None
    return sum(1 for x in v if x <= value) / len(v)


def main() -> int:
    run_dir, digests, bs_eval, out = (Path(a) for a in sys.argv[1:5])
    out.mkdir(parents=True, exist_ok=False)
    data = dg.rs.load_lot(run_dir)
    dg.check_digests(run_dir, digests, data)
    records = data["records"]
    completeness(records)
    pairs = json.loads(bs_eval.read_text(encoding="utf-8"))["pairs"]
    constant = [rec for rec in records if rec["scenario"] == "constant"]
    outcomes = {
        r_min: {
            rec["target"]: ev.target_outcomes(
                rec, r_min, pairs[str(r_min)]["b"], pairs[str(r_min)]["s"], dg.MIN_SNR
            )
            for rec in constant
        }
        for r_min in R_READ
    }
    # the context distributions, per R and group, over eligible constant rounds with the twin ok
    context = {}
    for r_min in R_READ:
        cells = defaultdict(lambda: {"pull_hidden": [], "z_train": [], "z_hidden": []})
        for rec in constant:
            for d in outcomes[r_min][rec["target"]]["rounds"]:
                if not d["eligible"]:
                    continue
                q = split(d["record"])
                if "z_train" not in q:
                    continue
                c = cells[rec["group"]]
                c["pull_hidden"].append(q.get("pull_hidden"))
                c["z_train"].append(q["z_train"])
                c["z_hidden"].append(q["z_hidden"])
        context[str(r_min)] = cells
    # the cases
    fail_targets = sorted(
        {t for r_min in R_READ for t, o in outcomes[r_min].items() if o["status"] == "FAIL"}
    )
    by_target = {rec["target"]: rec for rec in constant}
    cases, classes = [], {str(r): Counter() for r in R_READ}
    for target in fail_targets:
        rec = by_target[target]
        entry = {
            "target": target,
            "group": rec["group"],
            "years": rec["years"],
            "labels": dg.labels(target),
            "fail_at": [r for r in R_READ if outcomes[r][target]["status"] == "FAIL"],
            "rounds": {},
            "fail_rounds": {},
        }
        for r_min in R_READ:
            pair = pairs[str(r_min)]
            o = outcomes[r_min][target]
            rows = []
            for d in o["rounds"]:
                r = d["record"]
                gi, sub = dg.gate_of(d, r)
                gname = dg.GATES[gi] if gi >= 0 else "unclassified"
                rows.append(
                    {
                        "hidden_year": r["hidden_year"],
                        "status": d["status"],
                        "reason": d["reason"],
                        "gate": gname,
                        "reason_kind": sub,
                        "decision_1": d["decision_1"],
                        "decision_2": d["decision_2"],
                        "s_meas": r.get("s_meas"),
                    }
                )
                if d["status"] != "FAIL":
                    continue
                status, reason, z = fail_rule(
                    r["s_meas"],
                    dg.MIN_SNR,
                    r["d_train"],
                    r["e_train"],
                    r["d_hidden"],
                    r["e_hidden"],
                )
                if status != "FAIL":
                    raise SystemExit(f"{target} {r['hidden_year']}: fail_rule gives {status}")
                q = split(r)
                cls = cause(q, r)
                classes[str(r_min)][cls] += 1
                ctx = context[str(r_min)][rec["group"]]
                entry["fail_rounds"].setdefault(str(r_min), []).append(
                    {
                        "hidden_year": r["hidden_year"],
                        "s_meas": r["s_meas"],
                        "z": z,
                        **{k: r.get(k) for k in ("d_train", "e_train", "d_hidden", "e_hidden")},
                        "d_twin": r.get("d_twin"),
                        "twin_status": r.get("twin_status"),
                        "dp": r.get("dp"),
                        "s_pred_1": r.get("s_pred_1"),
                        "s_pred_2": r.get("s_pred_2"),
                        "threshold_at_r": capacity_threshold(
                            dg.MIN_SNR, pair["b"], pair["s"], r["n_years"]
                        ),
                        "n_years": r["n_years"],
                        "min_train_n_rep": min(r["train_n_rep"]) if r.get("train_n_rep") else None,
                        "min_hidden_n_rep": (
                            min(r["hidden_n_rep"]) if r.get("hidden_n_rep") else None
                        ),
                        "hidden_noise_undetermined": r.get("hidden_noise_undetermined"),
                        "measurement_status": r.get("measurement_status"),
                        "stage": r.get("stage"),
                        "record_reason": r.get("reason"),
                        "derived": {"capacity_k": CAPACITY_K, **q},
                        "cause": cls,
                        "rank_in_group": {
                            k: rank(q.get(k), ctx[k])
                            for k in ("pull_hidden", "z_train", "z_hidden")
                        },
                    }
                )
            entry["rounds"][str(r_min)] = rows
        cases.append(entry)
    ctx_out = {}
    for r_min, cells in context.items():
        ctx_out[r_min] = {}
        for g, c in sorted(cells.items()):
            pull = [x for x in c["pull_hidden"] if fin(x)]
            ctx_out[r_min][g] = {
                "pull_hidden": quantiles(c["pull_hidden"]),
                "pull_hidden_mad_scale": (
                    MAD * float(np.median(np.abs(np.asarray(pull) - np.median(pull))))
                    if pull
                    else None
                ),
                "z_train": quantiles(c["z_train"]),
                "z_hidden": quantiles(c["z_hidden"]),
                "fraction_z_hidden_ge_3": dg.frac(
                    sum(1 for x in c["z_hidden"] if x >= 3), len(c["z_hidden"])
                ),
                "fraction_z_train_ge_3": dg.frac(
                    sum(1 for x in c["z_train"] if x >= 3), len(c["z_train"])
                ),
            }
    result = {
        "cases": cases,
        "counts": {
            str(r): Counter(
                by_target[t]["group"] for t, o in outcomes[r].items() if o["status"] == "FAIL"
            )
            for r in R_READ
        },
        "causes_of_fail_rounds": {k: dict(v) for k, v in classes.items()},
        "context": ctx_out,
    }
    path = out / "x0c.json"
    path.write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8", newline="\n")
    print("x0c.json", hashlib.sha256(path.read_bytes()).hexdigest())
    return 0


if __name__ == "__main__":
    sys.exit(main())
