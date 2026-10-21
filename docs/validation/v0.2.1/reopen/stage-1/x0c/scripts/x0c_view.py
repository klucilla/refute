"""Print X0c's tables from x0c.json (the cases' FAIL rounds, the causes, the context)."""

# ruff: noqa: E501  (the printed lines are kept as run)

import json
import sys
from pathlib import Path

d = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))


def f(x, p=3):
    return "-" if x is None else (f"{x:.{p}g}" if isinstance(x, float) else str(x))


print("counts", json.dumps(d["counts"]))
print("causes", json.dumps(d["causes_of_fail_rounds"]))
for c in d["cases"]:
    lab = c["labels"]
    print(
        "\n##",
        c["target"],
        "|",
        c["group"],
        "| years",
        c["years"],
        "| FAIL at",
        c["fail_at"],
        "|",
        lab["band"],
        lab["mechanism"],
        lab.get("few_train", ""),
    )
    for r, rows in c["rounds"].items():
        print(
            "  R",
            r,
            [
                (x["hidden_year"], x["status"], x["gate"], x["reason_kind"], f(x["s_meas"]))
                for x in rows
            ],
        )
    for r, frs in c["fail_rounds"].items():
        for x in frs:
            q = x["derived"]
            print(
                f"  FAIL R{r} y{x['hidden_year']} S={f(x['s_meas'])} Z={f(x['z'])} "
                f"dtr={f(x['d_train'])}±{f(x['e_train'])} dh={f(x['d_hidden'])}±{f(x['e_hidden'])} "
                f"dtw={f(x['d_twin'])}({x['twin_status']}) dp={f(x['dp'])} "
                f"Sp1={f(x['s_pred_1'])} Sp2={f(x['s_pred_2'])} T={f(x['threshold_at_r'])} "
                f"nrep={x['min_train_n_rep']}/{x['min_hidden_n_rep']} | "
                f"Ztr={f(q.get('z_train'))} Zh={f(q.get('z_hidden'))} pull={f(q.get('pull_hidden'))} "
                f"eh/ep2={f(q.get('e_hidden_over_e_pred_2'))} eh/etr={f(q.get('e_hidden_over_e_train'))} "
                f"dtw/dtr={f(q.get('d_twin_over_d_train'))} dh/dtr={f(q.get('d_hidden_over_d_train'))} "
                f"| {x['cause']} | ranks {json.dumps(x['rank_in_group'])}"
            )
for r, cells in d["context"].items():
    for g, c in cells.items():
        print(
            f"\nctx R{r} {g}: pull {json.dumps(c['pull_hidden'])} mad {f(c['pull_hidden_mad_scale'])}"
            f"\n   z_train {json.dumps(c['z_train'])}\n   z_hidden {json.dumps(c['z_hidden'])}"
            f"\n   zh>=3 {json.dumps(c['fraction_z_hidden_ge_3'])} ztr>=3 "
            f"{json.dumps(c['fraction_z_train_ge_3'])}"
        )
