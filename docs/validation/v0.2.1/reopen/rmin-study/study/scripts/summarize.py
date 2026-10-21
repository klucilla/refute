"""Summary of the R_min study's evaluation (study-evaluation.json, made at 2e4ff99): the criteria
per R and group, and the interruptions (criterion 6) per target and per round, with the reasons
grouped by kind (the text before its first number or colon). Writes summary.json and prints
Markdown tables. Usage: python summarize.py <evaluation> <out summary.json>"""

import collections
import json
import re
import sys
from pathlib import Path

GROUPS = (
    "white, no variability",
    "white, variability",
    "AR(1), no variability",
    "AR(1), variability",
)
CRITERIA = ("false_fail", "coverage", "disappearance", "weakening")
KIND = re.compile(r"^[A-Za-z_\- ]+")


def kind(reason: str) -> str:
    parts = []
    for piece in reason.split("+"):
        m = KIND.match(piece.strip())
        parts.append((m.group(0) if m else piece).strip().rstrip("-_ ") or piece)
    return "+".join(sorted(set(parts)))


def grouped(table: dict) -> dict:
    out = collections.Counter()
    for reason, v in table.items():
        out[kind(reason)] += v["count"]
    return dict(out.most_common())


def main() -> int:
    data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    out = {
        "chosen_r_min": data["chosen_r_min"],
        "complete": data["complete"],
        "source": data["source"],
        "pairs_source": data["pairs_source"],
        "by_r": {},
    }
    for r in sorted(data["results"], key=int):
        res = data["results"][r]
        if res is None:
            out["by_r"][r] = None
            continue
        rows = {}
        for g in GROUPS:
            c = res[g]
            rows[g] = {
                "all_passed": c["all_passed"],
                **{
                    k: {kk: vv for kk, vv in c[k].items() if kk != "last_round_statuses"}
                    for k in CRITERIA
                },
                "interruptions": {
                    sc: {
                        "targets": c["inconclusive"][sc]["targets"],
                        "inconclusive_targets": c["inconclusive"][sc]["inconclusive_targets"],
                        "inconclusive_target_fraction": c["inconclusive"][sc][
                            "inconclusive_target_fraction"
                        ],
                        "rounds": c["inconclusive"][sc]["rounds"],
                        "inconclusive_rounds": c["inconclusive"][sc]["inconclusive_rounds"],
                        "inconclusive_round_fraction": c["inconclusive"][sc][
                            "inconclusive_round_fraction"
                        ],
                        "targets_by_reason_kinds": grouped(
                            c["inconclusive"][sc]["targets_by_reasons"]
                        ),
                        "rounds_by_reason_kind": grouped(c["inconclusive"][sc]["rounds_by_reason"]),
                    }
                    for sc in ("constant", "disappearing", "weakened")
                },
            }
        out["by_r"][r] = rows
    Path(sys.argv[2]).write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8", newline="\n")

    print(
        "| R | group | false FAIL n / FAILs / upper | coverage within1 / within2 / median | "
        "disappearance n / lower | weakening n | all |"
    )
    print("|---|---|---|---|---|---|---|")
    for r, rows in out["by_r"].items():
        for g, c in rows.items():
            ff, cv, di, we = (c[k] for k in CRITERIA)
            mark = lambda x: "ok" if x["passed"] else "fails"  # noqa: E731
            print(
                f"| {r} | {g} | {ff['n']} / {ff['fails']} / {ff['upper']:.4f} ({mark(ff)}) | "
                f"{cv.get('within_1', 0):.3f} / {cv.get('within_2', 0):.3f} / "
                f"{cv.get('median', 0):+.3f} ({mark(cv)}) | "
                f"{di['n']} / {di['lower']:.3f} ({mark(di)}) | "
                f"{we['n']} ({mark(we)}) | {'yes' if c['all_passed'] else 'no'} |"
            )
    for r in ("8",):
        print(f"\nInterruptions at R = {r}:")
        for g, c in out["by_r"][r].items():
            for sc, it in c["interruptions"].items():
                print(
                    f"{g} / {sc}: targets {it['inconclusive_targets']}/{it['targets']} "
                    f"({it['inconclusive_target_fraction']:.3f}), rounds "
                    f"{it['inconclusive_rounds']}/{it['rounds']} "
                    f"({it['inconclusive_round_fraction']:.3f})"
                )
                print("   rounds by kind:", it["rounds_by_reason_kind"])
                top = dict(list(it["targets_by_reason_kinds"].items())[:6])
                print("   targets by kinds (top 6):", top)
    return 0


if __name__ == "__main__":
    sys.exit(main())
