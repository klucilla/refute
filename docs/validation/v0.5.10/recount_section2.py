"""v0.5.10, part (a): recount, from committed records only, the numbers of section 2 of the research
of 2026-11-23 (docs/plans/research-2026-11-23/fable-research.md, lines 20 to 79), with Codex's
corrections (part B retention 23/100, decidability 24/100). Exploratory: every number is a recount
of recorded statuses, never a new verdict; differences are recorded, never explained away.

Writes recount-section2.json and recount-section2.md next to this file. Deterministic: the same
records give the same bytes. Run from the project's environment:

    .venv/Scripts/python.exe docs/validation/v0.5.10/recount_section2.py
"""

from __future__ import annotations

import json
import math
import statistics
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
KEPT = ("SURVIVED", "WEAKENED")
REFUSAL = "insufficient sensitivity"


def jl(path: str) -> list[dict]:
    with open(ROOT / path, encoding="utf-8") as fh:
        return [json.loads(x) for x in fh if x.strip()]


def js(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def blocks(t: dict) -> bool:
    """A test that is not passed: INCONCLUSIVE, or a FAIL of fatal severity."""
    return t.get("status") == "INCONCLUSIVE" or (
        t.get("status") == "FAIL" and t.get("severity") == "fatal"
    )


def verdict(tests: dict, decisive: list[str], as_pass=lambda name, t: False, cap=None) -> str:
    """The aggregation over the decisive tests (src/refute/core/verdict.py, as the research reads
    it): a fatal FAIL refutes; then any INCONCLUSIVE gives INCONCLUSIVE (``cap``: a warning test's
    INCONCLUSIVE gives at most WEAKENED instead); a warning FAIL weakens; else SURVIVED.
    ``as_pass``: a "what if" that reads a test as PASS."""
    status = {n: ("PASS" if as_pass(n, tests[n]) else tests[n]["status"]) for n in decisive}
    sev = {n: tests[n].get("severity") for n in decisive}
    if any(status[n] == "FAIL" and sev[n] == "fatal" for n in decisive):
        return "REFUTED"
    inc = [n for n in decisive if status[n] == "INCONCLUSIVE"]
    if cap == "warning-caps":
        if any(sev[n] != "warning" for n in inc):
            return "INCONCLUSIVE"
        if inc:
            return "WEAKENED"
    elif inc:
        return "INCONCLUSIVE"
    if any(status[n] == "FAIL" for n in decisive):
        return "WEAKENED"
    return "SURVIVED"


def phi(a: list[bool], b: list[bool]) -> float:
    n11 = sum(x and y for x, y in zip(a, b, strict=True))
    n10 = sum(x and not y for x, y in zip(a, b, strict=True))
    n01 = sum(y and not x for x, y in zip(a, b, strict=True))
    n00 = len(a) - n11 - n10 - n01
    den = math.sqrt((n11 + n10) * (n01 + n00) * (n11 + n01) * (n10 + n00))
    return (n11 * n00 - n10 * n01) / den if den else float("nan")


def rates(records: list[dict], decisive_of) -> dict[str, float]:
    names = sorted({n for r in records for n in decisive_of(r)})
    out = {}
    for n in names:
        rows = [r for r in records if n in decisive_of(r)]
        out[n] = sum(not blocks(r["_tests"][n]) for r in rows) / len(rows)
    return out


def main() -> None:
    rows = []

    def add(item, research, recount, source):
        same = research == recount or (
            isinstance(research, float)
            and isinstance(recount, float)
            and abs(research - recount) < 0.0005
        )
        rows.append(
            {
                "item": item,
                "research": research,
                "recount": recount,
                "difference": None if same else "differs",
                "source": source,
            }
        )

    # --- C1, family P (synthetic, stage 2): report and diagnosis (no per-record file committed)
    c1 = js("calibration/v0.5/runs/c1-confirmation/report.json")["decision_rules"]["D2"]
    diag = js("docs/plans/v0.5.1-wp0/diagnosis.json")
    pfam = next(v for k, v in _walk(diag) if k == "P" and isinstance(v, dict) and "tests" in v)
    n1 = c1["eligible"]
    kept1 = round(c1["v05_kept"] * n1)
    ref1 = round(c1["v05_refuted_fraction"] * n1)
    add("C1 P: n", 186, n1, "c1-confirmation/report.json D2.eligible")
    add("C1 P: kept", 100, kept1, "D2.v05_kept x eligible")
    add("C1 P: INCONCLUSIVE", 83, pfam["inconclusive"], "v0.5.1-wp0/diagnosis.json P")
    add("C1 P: REFUTED", 3, ref1, "D2.v05_refuted_fraction x eligible")
    c1_rates = {t: 1 - k / n1 for t, k in pfam["tests"].items()}
    for t, v in (
        ("systematics", 0.849),
        ("aperture_depth", 0.651),
        ("sinusoid", 0.823),
        ("odd_even", 0.876),
        ("period_alias", 0.995),
    ):
        add(f"C1 P pass rate: {t}", v, round(c1_rates[t], 3), "1 - INCONCLUSIVE count / 186")
    add("C1 P: product of rates", 0.397, round(math.prod(c1_rates.values()), 3), "product")
    add(
        "C1 P: observed (not INCONCLUSIVE)",
        0.554,
        round((n1 - pfam["inconclusive"]) / n1, 3),
        "(186 - 83) / 186",
    )

    # --- C2, T2a (injections in real hosts, stage 1): records of c2 and c2-prefix
    recs = jl("calibration/v0.5/runs/c2/records.jsonl") + jl(
        "calibration/v0.5/runs/c2-prefix/records.jsonl"
    )
    own = {
        r["target_key"]
        for r in recs
        if r["kind"] == "original" and r.get("status") == "OK" and r["chain"]["v04"]["gate_passed"]
    }
    t2a = [
        r
        for r in recs
        if r["kind"] == "injection"
        and r["target_key"] not in own
        and r.get("status") == "OK"
        and (r.get("recovery") or {}).get("recovered")
    ]
    for r in t2a:
        r["_tests"] = r["chain"]["v05"]["tests"]
    dec2 = lambda r: [n for n in r["chain"]["v05"]["stage_tests"] if n in r["_tests"]]  # noqa: E731
    sv2 = Counter(r["chain"]["v05"]["stage_verdict"] for r in t2a)
    kept2 = sv2["SURVIVED"] + sv2["WEAKENED"]
    add("C2 T2a: n", 637, len(t2a), "recovered gate-passing injections, gate-negative hosts")
    add("C2 T2a: kept", 270, kept2, "v05 stage verdict SURVIVED or WEAKENED")
    add("C2 T2a: INCONCLUSIVE", 366, sv2["INCONCLUSIVE"], "v05 stage verdict")
    add("C2 T2a: REFUTED", 1, sv2["REFUTED"], "v05 stage verdict")
    r2 = rates(t2a, dec2)
    for t, v in (
        ("systematics", 0.487),
        ("sinusoid", 0.876),
        ("odd_even", 0.945),
        ("period_alias", 0.947),
    ):
        add(f"C2 T2a pass rate: {t}", v, round(r2.get(t, float("nan")), 3), "stage tests, v05")
    add("C2 T2a: product of rates", 0.381, round(math.prod(r2.values()), 3), "product")
    add("C2 T2a: lowest rate", 0.487, round(min(r2.values()), 3), "min")
    add("C2 T2a: observed", 0.424, round(kept2 / len(t2a), 3), "kept / n")
    inc2 = [r for r in t2a if r["chain"]["v05"]["stage_verdict"] == "INCONCLUSIVE"]
    sys_in = [r for r in inc2 if r["_tests"].get("systematics", {}).get("status") == "INCONCLUSIVE"]
    only_sys = [
        r for r in sys_in if [n for n in dec2(r) if blocks(r["_tests"][n])] == ["systematics"]
    ]
    add("C2: INCONCLUSIVE with systematics INCONCLUSIVE", 327, len(sys_in), "of the INCONCLUSIVE")
    add("C2: systematics the only block", 238, len(only_sys), "the only blocking stage test")
    add("C2: kept without the systematics block", 508, kept2 + len(only_sys), "kept + only-sys")
    hi = [r for r in t2a if (r["chain"]["v05"]["candidate"] or {}).get("snr", 0) >= 50]
    add("C2: SNR >= 50, n", 357, len(hi), "v05 candidate SNR")
    add(
        "C2: SNR >= 50, kept",
        221,
        sum(r["chain"]["v05"]["stage_verdict"] in KEPT for r in hi),
        "v05 stage verdict",
    )
    has = [r for r in t2a if all(t in r["_tests"] for t in ("systematics", "odd_even", "sinusoid"))]
    b = {t: [blocks(r["_tests"][t]) for r in has] for t in ("systematics", "odd_even", "sinusoid")}
    add(
        "C2: phi(systematics, odd_even)",
        0.23,
        round(phi(b["systematics"], b["odd_even"]), 2),
        "blocking indicators",
    )
    add(
        "C2: phi(systematics, sinusoid)",
        0.19,
        round(phi(b["systematics"], b["sinusoid"]), 2),
        "blocking indicators",
    )
    tr = [r for r in recs if r["kind"] == "transform" and r.get("status") == "OK"]
    for slot, name, n_res, kept_res in ((0, "inverted", 24, 14), (1, "rotated", 40, 22)):
        g = [r for r in tr if (r["slot"] == 0) == (slot == 0) and r["chain"]["v05"]["gate_passed"]]
        k_now = sum(r["chain"]["v05"]["stage_verdict"] in KEPT for r in g)
        k_if = 0
        for r in g:
            tests = r["chain"]["v05"]["tests"]
            dec = [n for n in r["chain"]["v05"]["stage_tests"] if n in tests]
            k_if += verdict(tests, dec, as_pass=lambda n, t: t["status"] == "INCONCLUSIVE") in KEPT
        add(f"C2 {name} passing the gate: n", n_res, len(g), "v05 gate_passed transforms")
        add(f"C2 {name}: kept today", 0, k_now, "v05 stage verdict")
        add(f"C2 {name}: kept if every INCONCLUSIVE were PASS", kept_res, k_if, "what if")

    # --- v0.5.6 part B, the planet arm, signal matched to the TOI
    pb = [r["content"] for r in js("docs/validation/v0.5.6/part-b-records.json")["records"]]
    for c in pb:
        c["_tests"] = c.get("tests") or {}
    pl = [
        c
        for c in pb
        if c["arm"] == "planet" and c["status"] == "OK" and (c.get("identity") or {}).get("matched")
    ]
    fp = [
        c
        for c in pb
        if c["arm"] == "fp"
        and c["status"] == "OK"
        and (c.get("identity") or {}).get("matched")
        and c["_tests"].get("snr", {}).get("status") == "PASS"
    ]
    out_pl = Counter(c["outcome"] for c in pl)
    add("Part B planets matched: n", 100, len(pl), "planet arm, status OK, identity matched")
    add(
        "Part B planets: kept (retention, Codex's correction)",
        23,
        out_pl["SURVIVED"] + out_pl["WEAKENED"],
        "outcome",
    )
    add(
        "Part B planets: decidable (Codex's correction)",
        24,
        len(pl) - out_pl["INCONCLUSIVE"],
        "outcome not INCONCLUSIVE",
    )
    add("Part B planets: INCONCLUSIVE", 76, out_pl["INCONCLUSIVE"], "outcome")
    add("Part B planets: REFUTED", 1, out_pl["REFUTED"], "outcome")
    inc = [c for c in pl if c["outcome"] == "INCONCLUSIVE"]

    def refused(t):
        return t.get("status") == "INCONCLUSIVE" and REFUSAL in (t.get("message") or "")

    only, mixed, none_ = 0, 0, 0
    for c in inc:
        dec = [n for n in c["decisive"] if n in c["_tests"]]
        bl = [n for n in dec if c["_tests"][n].get("status") == "INCONCLUSIVE"]
        ref = [n for n in bl if refused(c["_tests"][n])]
        if ref and len(ref) == len(bl):
            only += 1
        elif ref:
            mixed += 1
        else:
            none_ += 1
    add("Part B INCONCLUSIVE: only sensitivity refusals", 53, only, "messages")
    add("Part B INCONCLUSIVE: refusal and another cause", 11, mixed, "messages")
    add("Part B INCONCLUSIVE: no refusal", 12, none_, "messages")
    dec_pl = lambda c: [n for n in c["decisive"] if n in c["_tests"]]  # noqa: E731
    rpb = rates(pl, dec_pl)
    for t, v in (
        ("systematics", 0.42),
        ("aperture_depth", 0.61),
        ("sinusoid", 0.81),
        ("odd_even", 0.85),
        ("period_alias", 0.97),
    ):
        add(f"Part B pass rate: {t}", v, round(rpb.get(t, float("nan")), 2), "decisive tests")
    add("Part B: product of rates", 0.168, round(math.prod(rpb.values()), 3), "product")
    add("Part B: lowest rate", 0.42, round(min(rpb.values()), 2), "min")
    hi = [c for c in pl if (c.get("candidate") or {}).get("snr", 0) >= 60]
    add("Part B: SNR >= 60, n", 26, len(hi), "candidate SNR")
    add("Part B: SNR >= 60, kept", 11, sum(c["outcome"] in KEPT for c in hi), "outcome")
    sysref = [
        c["_tests"]["systematics"]
        for c in pl
        if "systematics" in c["_tests"] and refused(c["_tests"]["systematics"])
    ]
    # the background sub-check's own record (every message lists "background" among its
    # sub-checks, so the message text cannot tell; see log.jsonl, recount-a)
    bg = [
        t
        for t in sysref
        if ((t.get("sensitivity") or {}).get("background") or {}).get("detectable") is False
    ]
    add("Part B: systematics refusals", 57, len(sysref), "messages")
    add(
        "Part B: of them, involving the background",
        54,
        len(bg),
        "sensitivity.background.detectable is false",
    )
    powers = [t["sensitivity"]["background"]["probability"] for t in bg]
    add(
        "Part B: median background power",
        0.76,
        round(statistics.median(powers), 2) if powers else None,
        "sensitivity.background.probability",
    )

    def what_if(group):
        v = Counter(verdict(c["_tests"], dec_pl(c), as_pass=lambda n, t: refused(t)) for c in group)
        return v["SURVIVED"] + v["WEAKENED"], v["SURVIVED"], v["WEAKENED"]

    k, s, w = what_if(pl)
    add("Part B planets: kept if refusals did not block", 76, k, "what if")
    add("  of them SURVIVED", 42, s, "what if")
    add("  of them WEAKENED", 34, w, "what if")
    out_fp = Counter(c["outcome"] for c in fp)
    add("Part B FPs matched, gate passed: n", 86, len(fp), "fp arm, matched, snr PASS")
    add("Part B FPs: kept today", 13, out_fp["SURVIVED"] + out_fp["WEAKENED"], "outcome")
    k, s, w = what_if(fp)
    add("Part B FPs: kept if refusals did not block", 50, k, "what if")
    add("  of them SURVIVED", 3, s, "what if")
    add("  of them WEAKENED", 47, w, "what if")
    r2e = Counter(verdict(c["_tests"], dec_pl(c), cap="warning-caps") for c in pl)
    add(
        "Part B planets under variant (e) of R2",
        43,
        r2e["SURVIVED"] + r2e["WEAKENED"],
        "a warning test's INCONCLUSIVE caps at WEAKENED",
    )
    ap = sum(
        1
        for c in pl
        if verdict(c["_tests"], dec_pl(c), cap="warning-caps") == "INCONCLUSIVE"
        and c["_tests"].get("aperture_depth", {}).get("status") == "INCONCLUSIVE"
    )
    add("Part B: aperture_depth still blocking under (e)", 39, ap, "INCONCLUSIVE under (e)")

    doc = {
        "mode": "exploratory",
        "method_status": "not_validated",
        "limits_label": "WEAKENED; does not meet D1, D2, D4, T2a",
        "source": "docs/plans/research-2026-11-23/fable-research.md, section 2 (lines 20 to 79)",
        "rows": rows,
        "matches": sum(r["difference"] is None for r in rows),
        "differs": sum(r["difference"] is not None for r in rows),
    }
    (HERE / "recount-section2.json").write_text(
        json.dumps(doc, indent=1, ensure_ascii=False) + "\n", "utf-8", newline="\n"
    )
    md = [
        "# v0.5.10 (a): recount of the research's section 2",
        "",
        "Exploratory; generated by `recount_section2.py`. 'differs' is recorded, not explained.",
        "",
        "| Item | Research | Recount | | Source |",
        "|---|---|---|---|---|",
    ]
    for r in rows:
        md.append(
            f"| {r['item']} | {r['research']} | {r['recount']} | "
            f"{'' if r['difference'] is None else '**differs**'} | {r['source']} |"
        )
    md += ["", f"{doc['matches']} match, {doc['differs']} differ."]
    (HERE / "recount-section2.md").write_text("\n".join(md) + "\n", "utf-8", newline="\n")
    print(doc["matches"], "match,", doc["differs"], "differ")


def _walk(obj, key=None):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield k, v
            yield from _walk(v, k)
    elif isinstance(obj, list):
        for v in obj:
            yield from _walk(v, key)


if __name__ == "__main__":
    main()
