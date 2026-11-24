"""Step 0's recount of v0.5.11 (charter, step 0, item 2), by the rules of
docs/validation/v0.5.11/recount/RULES.md, committed before the first run.

    .venv/Scripts/python.exe -I -B docs/validation/v0.5.11/tools/recount.py

Read-only: it reads committed records and writes recount.json and recount.md. Exploratory.
"""

from __future__ import annotations

import hashlib
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT / "docs" / "validation" / "v0.5.11" / "recount"
RULES = OUT / "RULES.md"
P1 = "docs/validation/v0.5.6/part-b-records.json"
P2 = ("calibration/v0.5/runs/c2/records.jsonl", "calibration/v0.5/runs/c2-prefix/records.jsonl")
TESTS = ("odd_even", "secondary_eclipse", "plausibility")
NEW_TESTS = ("F1", "F2", "F3", "F4", "U1")
CLASSES = ("assessed_pass", "assessed_fail", "not_assessed", "unknown")
JOINT = ("rejected", "unassessed", "unknown", "retained")
LABELS = ["exploratory", "method_status: not_validated"]


def sha(rel: str) -> str:
    return hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()


def test_class(t: dict | None) -> str:
    """R3."""
    if t is None:
        return "not_assessed"
    status = t.get("status")
    if status not in ("PASS", "FAIL"):
        return "not_assessed"
    if "coverage" not in t or t["coverage"] is None:
        return "unknown"
    cov = t["coverage"]
    if isinstance(cov, int) and cov > 0:
        return "assessed_pass" if status == "PASS" else "assessed_fail"
    return "not_assessed"


def joint_class(classes: dict[str, str]) -> str:
    """R4."""
    v = set(classes.values())
    if "assessed_fail" in v:
        return "rejected"
    if "not_assessed" in v:
        return "unassessed"
    if "unknown" in v:
        return "unknown"
    return "retained"


def summarize(rows: list[dict]) -> dict:
    """R6: counts per test and joint, and the host distribution."""
    per_test = {t: Counter(r["classes"][t] for r in rows) for t in TESTS}
    joint = Counter(r["joint"] for r in rows)
    hosts: dict[str, list[str]] = defaultdict(list)
    for r in rows:
        hosts[r["host"]].append(r["joint"])
    sizes = [len(v) for v in hosts.values()]
    return {
        "records": len(rows),
        "per_test": {t: {c: per_test[t].get(c, 0) for c in CLASSES} for t in TESTS},
        "joint": {c: joint.get(c, 0) for c in JOINT},
        "hosts": len(hosts),
        "records_per_host": (
            {"min": min(sizes), "median": statistics.median(sizes), "max": max(sizes)}
            if sizes
            else None
        ),
        "hosts_all_retained": sum(1 for v in hosts.values() if all(j == "retained" for j in v)),
        "new_tests_assessability": {t: "unknown" for t in NEW_TESTS},
    }


def main() -> int:
    p1 = json.loads((ROOT / P1).read_text(encoding="utf-8"))
    rows1, no_output = [], Counter()
    for rec in p1["records"]:
        c = rec["content"]
        if c.get("status") != "OK":
            no_output[c.get("arm")] += 1
            continue
        tests = c.get("tests") or {}
        classes = {t: test_class(tests.get(t)) for t in TESTS}
        rows1.append(
            {
                "host": str(c["tic_id"]),
                "arm": c.get("arm"),
                "matched": bool((c.get("identity") or {}).get("matched")),
                "classes": classes,
                "joint": joint_class(classes),
            }
        )
    recs = []
    for rel in P2:
        text = (ROOT / rel).read_text(encoding="utf-8")
        recs += [json.loads(x) for x in text.splitlines() if x.strip()]
    own = {
        r["target_key"]
        for r in recs
        if r["kind"] == "original" and r.get("status") == "OK" and r["chain"]["v04"]["gate_passed"]
    }
    rows2 = []
    for r in recs:
        if not (
            r["kind"] == "injection"
            and r["target_key"] not in own
            and r.get("status") == "OK"
            and (r.get("recovery") or {}).get("recovered")
        ):
            continue
        tests = r["chain"]["v05"]["tests"]
        classes = {t: test_class(tests.get(t)) for t in TESTS}
        rows2.append({"host": r["target_key"], "classes": classes, "joint": joint_class(classes)})

    doc = {
        "labels": LABELS,
        "limits_label_p1": p1.get("limits_label"),
        "rules_sha256": hashlib.sha256(RULES.read_bytes()).hexdigest(),
        "inputs_sha256": {P1: sha(P1), **{rel: sha(rel) for rel in P2}},
        "P1_part_b": {
            "all": summarize(rows1),
            "no_output": dict(no_output),
            "by_arm": {
                a: summarize([r for r in rows1 if r["arm"] == a])
                for a in sorted({r["arm"] for r in rows1})
            },
            "by_matched": {
                str(m): summarize([r for r in rows1 if r["matched"] is m]) for m in (True, False)
            },
        },
        "P2_c2_t2a": {"all": summarize(rows2)},
    }
    OUT.mkdir(parents=True, exist_ok=True)
    body = json.dumps(doc, indent=1) + "\n"
    (OUT / "recount.json").write_text(body, encoding="utf-8", newline="\n")

    lines = [
        "# Step 0's recount (v0.5.11)",
        "",
        "Exploratory, `method_status: not_validated`. Read-only, by [RULES.md](RULES.md). Part B "
        f"carries '{p1.get('limits_label')}'. Never a verdict, a candidate or an acceptance.",
        "",
        "| Population | Records | Hosts | retained | rejected | unassessed | unknown |",
        "|---|---|---|---|---|---|---|",
    ]

    def row(name: str, s: dict) -> str:
        j = s["joint"]
        return (
            f"| {name} | {s['records']} | {s['hosts']} | {j['retained']} | {j['rejected']} | "
            f"{j['unassessed']} | {j['unknown']} |"
        )

    lines.append(row("P1 part B, all", doc["P1_part_b"]["all"]))
    for a, s in doc["P1_part_b"]["by_arm"].items():
        lines.append(row(f"P1, arm {a}", s))
    for m, s in doc["P1_part_b"]["by_matched"].items():
        lines.append(row(f"P1, matched {m}", s))
    lines.append(row("P2 C2 T2a, all", doc["P2_c2_t2a"]["all"]))
    lines += [
        "",
        "Per test (assessed_pass / assessed_fail / not_assessed / unknown):",
        "",
        "| Population | " + " | ".join(TESTS) + " |",
        "|---|" + "---|" * len(TESTS),
    ]
    for name, s in (
        ("P1 part B, all", doc["P1_part_b"]["all"]),
        ("P2 C2 T2a, all", doc["P2_c2_t2a"]["all"]),
    ):
        cells = [" / ".join(str(s["per_test"][t][c]) for c in CLASSES) for t in TESTS]
        lines.append(f"| {name} | " + " | ".join(cells) + " |")
    lines += [
        "",
        f"P1 records with no battery output (status not OK): {dict(no_output)}.",
        "",
        "The screen's own tests (F1, F2, F3, F4, U1) were never run on any record: their "
        "assessability is unknown for every record.",
        "",
    ]
    (OUT / "recount.md").write_text("\n".join(lines), encoding="utf-8", newline="\n")
    summary = {"P1": doc["P1_part_b"]["all"]["joint"], "P2": doc["P2_c2_t2a"]["all"]["joint"]}
    print(json.dumps(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
