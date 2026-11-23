"""v0.5.8 stage 0 (exploratory, no doors): reproduce the table of section 1 of the independent
recommendation (docs/plans/v0.5.8-consensus/independent-recommendation.md, lines 19 to 41) from
the committed v0.5.6 records only, or record the difference (the maintainer's decision of
2026-11-23, received at 13:27 local, item 2).

It reads ``docs/validation/v0.5.6/part-a-records.json`` and ``part-b-records.json``. It runs no
battery, reads no light curve and uses no network.

**What it recounts:**
- the sensitivity blocks that carry a probability, over the OK records;
- for margins 0.005, 0.01 and 0.02 to the required probability:
  - the blocks of PASS tests that are near;
  - the near refusals (blocks not detectable);
  - the SURVIVED and WEAKENED records with a near PASS block;
- the exact ties (probability equal to the required probability);
- the INCONCLUSIVE records that would become decided only through refusals within 0.02, assuming
  every one of their INCONCLUSIVE decisive tests is a sensitivity refusal with every
  undetectable block that near;
- the 17 FP events of part B: for each, the statistic of its first decisive fatal FAIL against its
  threshold, read from the message where it states the threshold
  (``<value> sigma (> <threshold>)``);
- Fisher's one-sided exact p for 13 of 150 against 1 of 150.

**Exploratory:** never a verdict. Writes ``stage0-records.json`` and ``stage0-records.md``.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
BUNDLES = {"A": ROOT / "docs/validation/v0.5.6/part-a-records.json",
           "B": ROOT / "docs/validation/v0.5.6/part-b-records.json"}  # fmt: skip
OUT_JSON = HERE / "stage0-records.json"
OUT_MD = HERE / "stage0-records.md"
MARGINS = (0.005, 0.01, 0.02)
STAT = re.compile(r"(-?\d+(?:\.\d+)?) sigma \(> (\d+(?:\.\d+)?)\)")
EXPECTED = {  # the recommendation's numbers, to compare with
    "blocks": 4820,
    "table": {0.005: (9, 8, 2, 0), 0.01: (21, 21, 2, 2), 0.02: (43, 30, 2, 4)},
    "survived_total": 31,
    "weakened_total": 60,
    "ties": 3,
    "inconclusive_total": 374,
    "inconclusive_decided_by_refusals_002": 0,
    "fragile_events": ["3165.01", "3753.01", "2208.01", "2111.01"],
    "fisher_13_vs_1": 7.3e-04,
}


def records() -> list[dict]:
    out = []
    for part, path in BUNDLES.items():
        for item in json.loads(path.read_text("utf-8"))["records"]:
            out.append({**item["content"], "_part": part})
    return out


def blocks(test: dict) -> list[tuple[str, dict]]:
    s = test.get("sensitivity")
    if not isinstance(s, dict):
        return []
    return [(k, b) for k, b in s.items() if isinstance(b, dict) and "probability" in b]


def fisher_one_sided(a: int, n1: int, b: int, n2: int) -> float:
    """P(X >= a) for the first group's events, hypergeometric with the margins fixed."""
    k, n = a + b, n1 + n2
    total = math.comb(n, k)
    return sum(math.comb(n1, x) * math.comb(n2, k - x) for x in range(a, min(k, n1) + 1)) / total


def main() -> None:
    recs = [r for r in records() if r.get("status") == "OK"]
    all_blocks = [(r, name, key, b) for r in recs for name, t in r["tests"].items()
                  for key, b in blocks(t)]  # fmt: skip
    table = {}
    for m in MARGINS:

        def near(b, m=m):
            return abs(float(b["probability"]) - float(b["required_probability"])) <= m

        pass_near = [
            x for x in all_blocks if x[0]["tests"][x[1]]["status"] == "PASS" and near(x[3])
        ]
        refusal_near = [x for x in all_blocks if x[3].get("detectable") is False and near(x[3])]

        def has_pass_near(r, m=m):
            return any(t["status"] == "PASS" and any(near(b, m) for _, b in blocks(t))
                       for t in r["tests"].values())  # fmt: skip

        table[str(m)] = {
            "pass_blocks_near": len(pass_near),
            "refusals_near": len(refusal_near),
            "survived_with_pass_near": sum(
                1 for r in recs if r["outcome"] == "SURVIVED" and has_pass_near(r)
            ),  # fmt: skip
            "weakened_with_pass_near": sum(
                1 for r in recs if r["outcome"] == "WEAKENED" and has_pass_near(r)
            ),  # fmt: skip
        }
    ties = [{"toi": r["toi"], "test": name, "block": key}
            for r, name, key, b in all_blocks
            if float(b["probability"]) == float(b["required_probability"])]  # fmt: skip
    inconclusive = [r for r in recs if r["outcome"] == "INCONCLUSIVE"]

    def decided_by_refusals(r: dict) -> bool:
        undecided = [n for n in r.get("decisive", []) if r["tests"].get(n, {}).get("status")
                     == "INCONCLUSIVE"]  # fmt: skip
        if not undecided:
            return False
        for n in undecided:
            t = r["tests"][n]
            if not t.get("message", "").startswith("PASS refused: insufficient sensitivity"):
                return False
            bad = [b for _, b in blocks(t) if b.get("detectable") is False]
            if not bad or any(abs(float(b["probability"]) - float(b["required_probability"]))
                              > 0.02 for b in bad):  # fmt: skip
                return False
        return True

    flips = [r["toi"] for r in inconclusive if decided_by_refusals(r)]
    events = []
    for r in recs:
        if r["_part"] != "B" or r["arm"] != "fp" or r["outcome"] != "REFUTED":
            continue
        if not (r.get("identity") or {}).get("matched"):
            continue
        fails = [n for n in r.get("decisive", []) if r["tests"].get(n, {}).get("status") == "FAIL"
                 and r["tests"][n].get("severity") == "fatal"]  # fmt: skip
        first = fails[0] if fails else None
        msg = r["tests"][first]["message"] if first else ""
        m = STAT.search(msg)
        margin = None if m is None else float(m.group(1)) - float(m.group(2))
        events.append({"toi": r["toi"], "first_fatal_fail": first, "message": msg[:200],
                       "sigma_margin": margin, "within_1_sigma": margin is not None
                       and margin < 1.0})  # fmt: skip
    fragile = sorted(e["toi"] for e in events if e["within_1_sigma"])
    unparsed = sorted(e["toi"] for e in events if e["sigma_margin"] is None)
    doc = {
        "schema": "refute-v058-stage0-1",
        "mode": "exploratory",
        "limits_label": "WEAKENED; does not meet D1, D2, D4, T2a",
        "method_status": "not_validated",
        "code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "bundles_sha256": {
            p: hashlib.sha256(v.read_bytes()).hexdigest() for p, v in BUNDLES.items()
        },  # fmt: skip
        "ok_records": len(recs),
        "blocks": len(all_blocks),
        "table": table,
        "survived_total": sum(r["outcome"] == "SURVIVED" for r in recs),
        "weakened_total": sum(r["outcome"] == "WEAKENED" for r in recs),
        "ties": ties,
        "inconclusive_total": len(inconclusive),
        "inconclusive_decided_by_refusals_002": flips,
        "fp_events": events,
        "fp_events_within_1_sigma": fragile,
        "fp_events_unparsed": unparsed,
        "fisher_13_vs_1": fisher_one_sided(13, 150, 1, 150),
        "expected": {
            k: (v if not isinstance(v, dict) else {str(m): t for m, t in v.items()})
            for k, v in EXPECTED.items()
        },  # fmt: skip
    }
    diffs = []
    if doc["blocks"] != EXPECTED["blocks"]:
        diffs.append(f"blocks: {doc['blocks']} against {EXPECTED['blocks']}")
    for m, want in EXPECTED["table"].items():
        got = table[str(m)]
        row = (got["pass_blocks_near"], got["refusals_near"], got["survived_with_pass_near"],
               got["weakened_with_pass_near"])  # fmt: skip
        if row != want:
            diffs.append(f"margin {m}: {row} against {want}")
    for key in ("survived_total", "weakened_total", "inconclusive_total"):
        if doc[key] != EXPECTED[key]:
            diffs.append(f"{key}: {doc[key]} against {EXPECTED[key]}")
    if len(ties) != EXPECTED["ties"]:
        diffs.append(f"ties: {len(ties)} against {EXPECTED['ties']}")
    if len(flips) != EXPECTED["inconclusive_decided_by_refusals_002"]:
        diffs.append(f"INCONCLUSIVE decided by refusals: {len(flips)} against 0")
    if fragile != sorted(EXPECTED["fragile_events"]):
        diffs.append(f"fragile FP events: {fragile} against {sorted(EXPECTED['fragile_events'])}"
                     f" (unparsed: {unparsed})")  # fmt: skip
    if round(doc["fisher_13_vs_1"], 5) != round(EXPECTED["fisher_13_vs_1"], 5):
        diffs.append(f"Fisher 13 vs 1: {doc['fisher_13_vs_1']:.3g} against 7.3e-04")
    doc["differences"] = diffs
    doc["reproduced"] = not diffs
    OUT_JSON.write_text(json.dumps(doc, indent=1) + "\n", "utf-8", newline="\n")
    OUT_MD.write_text(markdown(doc), "utf-8", newline="\n")
    print(json.dumps({"reproduced": doc["reproduced"], "differences": diffs}, indent=1))


def markdown(doc: dict) -> str:
    lines = [
        "# v0.5.8 stage 0: the recommendation's section 1, recounted from the records "
        "(exploratory, no doors)",
        "",
        f"**Exploratory.** Limits label: '{doc['limits_label']}'. `method_status: not_validated`.",
        "",
        f"OK records: {doc['ok_records']}. Sensitivity blocks with a probability: {doc['blocks']}.",
        "",
        "| Margin | PASS blocks near | Refusals near | SURVIVED with a PASS near (of "
        f"{doc['survived_total']}) | WEAKENED with a PASS near (of {doc['weakened_total']}) |",
        "|---|---|---|---|---|",
    ]
    for m, row in doc["table"].items():
        lines.append(f"| {m} | {row['pass_blocks_near']} | {row['refusals_near']} | "
                     f"{row['survived_with_pass_near']} | "
                     f"{row['weakened_with_pass_near']} |")  # fmt: skip
    lines += [
        "",
        f"- Exact ties: {len(doc['ties'])}: "
        + "; ".join(f"TOI-{t['toi']} {t['test']}.{t['block']}" for t in doc["ties"])
        + ".",
        f"- INCONCLUSIVE records: {doc['inconclusive_total']}; decided only by refusals within "
        f"0.02: {len(doc['inconclusive_decided_by_refusals_002'])}.",
        f"- FP events of part B: {len(doc['fp_events'])}; with the failing statistic within 1 "
        f"sigma of a threshold stated in the message: {doc['fp_events_within_1_sigma']}; "
        f"threshold not stated in the message: {doc['fp_events_unparsed']}.",
        f"- Fisher one-sided, 13 of 150 against 1 of 150: p = {doc['fisher_13_vs_1']:.3g}.",
        "",
        f"**Reproduced:** {doc['reproduced']}.",
    ]
    if doc["differences"]:
        lines += ["", "**Differences from the recommendation:**", ""]
        lines += [f"- {d}" for d in doc["differences"]]
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    main()
