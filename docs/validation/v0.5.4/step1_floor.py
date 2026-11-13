"""v0.5.4, second half, step 1: D2's joint floor and T2a's losses that a procedure cannot fix, on
the existing records (#217; the maintainer's decision of 2026-11-12, night, item 4a; the frozen
design is ``docs/plans/v0.5.4-h2-step1-floor.md``). **Read only; it reruns nothing and decides
nothing.** ``method_status: not_validated``.

Per loss, every decisive blocker (``b1_blockers_decisive``'s own functions) and every test I1
classified (tests hidden behind a fatal FAIL included) gets the **set** of categories that apply
to it (DATA, MSG, RULE, INFO, PROC, FATAL, REC, UNK), so simultaneous causes are all kept. A loss
counts in a floor if any category of any of its blockers is in the floor's set:
F_strict = DATA | INFO; F_rule = F_strict | RULE | MSG; F_upper = F_rule | FATAL | UNK.

The records are read through their own reviewed readers:
- I1 through ``i1_diagnose._read``;
- I4 through ``i4_rest2._records``, the driver's sidecar checks, each row once.

The reproduced blocker counts must equal ``b1-blockers-decisive.json``'s, or the step stops.

Usage (from the project root, no bytecode written):
``.venv/Scripts/python.exe -B docs/validation/v0.5.4/step1_floor.py``.
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import i4_bound  # noqa: E402,I001  (binds budgeted to v0.5.4's ledger last)
from i4_bound import ROOT, b1_b14, b1_d2d4_rest, ledger_b  # noqa: E402
import i1_diagnose  # noqa: E402
import i4_rest2  # noqa: E402

sys.path.insert(0, str(i4_bound.STAGE_B))
import b1_blockers_decisive as bd  # noqa: E402

OUT_FILE = HERE / "h2-step1-floor.json"
CACHE = ROOT / ".cache/v054/step1"
PUBLISHED = i4_bound.STAGE_B / "b1-blockers-decisive.json"
REQUIRED = 0.95
D2_ELIGIBLE, D2_LOSSES, D2_ALLOWED = 178, 37, 22
T2A_B, T2A_LOSSES, T2A_ALLOWED, T2A_IF_REFUTED_STAY, T2A_C = 559, 228, 7, 2, 49
STRATA_B = ("2_to_4", "5_to_20")
STRICT = {"DATA", "INFO"}
RULE = STRICT | {"RULE", "MSG"}
UPPER = RULE | {"FATAL", "UNK"}
GRID_TESTS = ("odd_even", "systematics")
NON_GRID_II = 24  # I1: 66 class-(ii) `systematics` losses of T2a, 42 of them grid refusals


def message_categories(why: str) -> set:
    """Every category an I1 reason states (simultaneous causes kept)."""
    out = set()
    if "does not establish the dip's cause" in why:
        out.add("RULE")
    if "outside the grid" in why or "error not measurable" in why:
        out.add("PROC")
    if "no transit measured" in why:
        out.add("MSG")
    if "not enough" in why or "the coverage rule" in why:
        out.add("DATA")
    return out


def i1_categories(c: dict | None) -> set:
    if not c:
        return {"UNK"}
    if c["class"] == "ii":
        return message_categories(c.get("why", "")) or {"UNK"}
    if c["class"] == "i":
        return {"REC?"}
    return {"UNK"}  # iii stops I1 itself; unresolved is unknown


def d2_categories(name: str, row: dict | None, label: str, i1: dict | None, i4: dict | None):
    row = row or {}
    cats = set()
    if label.endswith("[severity not recorded]") or row.get("status") == "FAIL":
        cats.add("FATAL")
    if row.get("class") == "not_enough_data":
        cats.add("DATA")
    if "outside the grid" in str(row.get("refused") or ""):
        cats.add("PROC")
    c = (i1 or {}).get("tests", {}).get(name)
    if row.get("status") == "INCONCLUSIVE" or "hidden" in label:
        found = i1_categories(c) if c else ({"UNK"} if not cats else set())
        rec_candidate = "REC?" in found
        found.discard("REC?")
        cats |= found
        # INFO depends only on an INCONCLUSIVE test and a valid bound below 0.95, whatever I1's
        # class (Codex, h2-step1 round 2); REC only for I1's class (i) with the bound allowing it
        below = _below_bound(name, i4)
        if row.get("status") == "INCONCLUSIVE" and below is True:
            cats.add("INFO")
        elif rec_candidate:
            cats.add("REC" if below is False else "UNK")
    return cats or {"UNK"}


def _below_bound(name: str, i4: dict | None) -> bool | None:
    """Whether I4's bound for this test is below 0.95; None if no valid bound exists."""
    if i4 is None or i4.get("status") != "OK" or i4.get("mismatch"):
        return None
    if name == "odd_even":
        if i4["nuisance"]["invalid"]:
            return None
        p = i4.get("power_nuisance")
    elif name == "sinusoid":
        p = i4.get("sinusoid_small_at_bound")
    else:
        return None
    # an absent, non-numeric, non-finite or out-of-range probability is no bound (Codex, h2-step1
    # round 3): class (i) then stays UNK, never INFO or REC
    if not isinstance(p, (int, float)) or isinstance(p, bool) or not math.isfinite(p) \
            or not 0.0 <= p <= 1.0:  # fmt: skip
        return None
    return p < REQUIRED


def t2a_categories(name: str, row: dict | None, label: str, refused: str, i1: dict | None):
    row = row or {}
    cats = set()
    if label.endswith("missing"):
        return {"UNK"}
    if row.get("status") == "FAIL":
        cats.add("FATAL")
    # T2a's briefs keep ``inconclusive_class`` (paired.py); D2's rows keep ``class``
    if row.get("status") == "INCONCLUSIVE" and "not_enough_data" in (
        row.get("inconclusive_class"),
        row.get("class"),
    ):
        cats.add("DATA")
    if name in GRID_TESTS and "outside the grid" in refused:
        cats.add("PROC")
    if row.get("status") == "INCONCLUSIVE" or "hidden" in label:
        c = (i1 or {}).get("tests", {}).get(name)
        if c:
            found = i1_categories(c)
            found.discard("REC?")  # T2a has no information bound
            cats |= found or {"UNK"}
        elif not cats:
            cats.add("UNK")
    return cats or {"UNK"}


def floors(cases: list[dict]) -> dict:
    def count(cats: set, subset=None) -> int:
        pool = cases if subset is None else [c for c in cases if subset(c)]
        return sum(any(set(b["categories"]) & cats for b in c["blockers"]) for c in pool)

    not_refuted = lambda c: c["verdict"] != "REFUTED"  # noqa: E731
    return {
        "F_strict": count(STRICT),
        "F_rule": count(RULE),
        "F_upper": count(UPPER),
        "outside_refuted": {"F_strict": count(STRICT, not_refuted),
                            "F_rule": count(RULE, not_refuted),
                            "F_upper": count(UPPER, not_refuted)},
        "refuted_losses": sum(c["verdict"] == "REFUTED" for c in cases),
        "blockers_by_category_set": dict(Counter(
            "+".join(sorted(b["categories"])) for c in cases for b in c["blockers"]
        ).most_common()),
        "losses_by_category_union": dict(Counter(
            "+".join(sorted({x for b in c["blockers"] for x in b["categories"]})) for c in cases
        ).most_common()),
    }  # fmt: skip


def _check_published(name: str, cases: list, published: dict) -> None:
    by_test = Counter()
    for c in cases:
        by_test.update({b["test"] for b in c["blockers"] if not b.get("hidden")})
    if dict(by_test) != published:
        raise SystemExit(f"{name}: reproduced blockers {dict(by_test)} != published {published}")


def d2_part(i1_by: dict, i4_by: dict, published: dict) -> dict:
    from refute.packs.tess.pipeline import expected_by_role

    with i4_bound._ledger(ledger_b):
        recs, _, _, _ = b1_d2d4_rest.complete_records()
    _, _, p4 = b1_b14.fv.plans()
    decisive = set(expected_by_role(p4, False)[0])
    eligible = [r for r in recs if r.get("status") == "OK" and r["gate_passed"] and r["identity"]]
    lost = [r for r in eligible if r["v5"] not in bd.KEPT]
    if (len(eligible), len(lost)) != (D2_ELIGIBLE, D2_LOSSES):
        raise SystemExit(f"D2: {len(eligible)} eligible, {len(lost)} lost: STOP")
    cases = []
    for r in lost:
        blockers, _, _ = bd.d2_blockers(r["v5_tests"], r["v5"], decisive)
        i1, i4 = i1_by.get(("d2", r["index"])), i4_by.get(r["index"])
        out = []
        for label in blockers:
            name = label.split(" ")[0]
            cats = d2_categories(name, r["v5_tests"].get(name), label, i1, i4)
            out.append({"test": name, "label": label, "categories": sorted(cats)})
        if r["v5"] == "REFUTED" and i1:  # the tests I1 found behind the fatal FAIL
            for name in sorted(set(i1.get("tests", {})) - {b["test"] for b in out}):
                label = f"{name} hidden behind a fatal FAIL"
                cats = d2_categories(name, r["v5_tests"].get(name), label, i1, i4)
                out.append({"test": name, "label": label, "categories": sorted(cats),
                            "hidden": True})  # fmt: skip
        cases.append({"index": r["index"], "verdict": r["v5"], "blockers": out,
                      "i1": i1 is not None, "i4": i4 is not None})  # fmt: skip
    _check_published("D2", cases, published)
    f = floors(cases)
    if f["F_upper"] <= D2_ALLOWED:
        outcome = "a margin is left, if every REC and PROC loss is recovered (assumed)"
    elif f["F_strict"] > D2_ALLOWED:
        outcome = "the margin is exhausted under the stated assumptions (no draft)"
    else:
        outcome = "INCONCLUSIVE"
    return {"eligible": len(eligible), "losses": len(lost), "allowed": D2_ALLOWED, **f,
            "margins": {k: D2_ALLOWED - f[k] for k in ("F_strict", "F_rule", "F_upper")},
            "outcome": outcome, "cases": cases}  # fmt: skip


def t2a_part(i1_by: dict, published: dict) -> dict:
    pop = b1_b14.ft.population()
    with i4_bound._ledger(ledger_b):
        got = {}
        for s in STRATA_B:
            for r in b1_b14._records(s):
                if (r["key"], r["slot"]) in got:
                    raise SystemExit(f"T2a: {r['key']}/{r['slot']} twice: STOP")
                got[(r["key"], r["slot"])] = r
    rows = [row for row in pop if row["stratum"] in STRATA_B]
    cases = []
    for row in rows:
        rec = got.get((row["key"], row["slot"]))
        if rec is None or rec.get("status") != "OK" or rec.get("compat_problems"):
            cases.append({"key": row["key"], "slot": row["slot"], "verdict": "unknown record",
                          "blockers": [{"test": "(record)", "label": "unknown",
                                        "categories": ["UNK"]}], "i1": False})  # fmt: skip
            continue
        brief = rec["v5C"]  # B: C up to 20 measured sectors
        if brief["stage_verdict"] in bd.KEPT:
            continue
        refused = str((brief.get("selection") or {}).get("refused") or "")
        blockers, _, _ = bd.t2a_blockers(brief)
        i1 = i1_by.get(("t2a", row["key"], row["slot"]))
        out = []
        for label in blockers:
            name = label.split(" ")[0]
            cats = t2a_categories(name, brief["tests"].get(name), label, refused, i1)
            entry = {"test": name, "label": label, "categories": sorted(cats)}
            c = (i1 or {}).get("tests", {}).get(name)
            if c:
                entry["i1_class"] = c["class"]
                entry["i1_grid_refusal"] = "outside the grid" in c.get("why", "")
            out.append(entry)
        if brief["stage_verdict"] == "REFUTED" and i1:
            for name in sorted(set(i1.get("tests", {})) - {b["test"] for b in out}):
                label = f"{name} hidden behind a fatal FAIL"
                cats = t2a_categories(name, brief["tests"].get(name), label, refused, i1)
                out.append({"test": name, "label": label, "categories": sorted(cats),
                            "hidden": True})  # fmt: skip
        cases.append({"key": row["key"], "slot": row["slot"], "verdict": brief["stage_verdict"],
                      "blockers": out, "i1": i1 is not None})  # fmt: skip
    if (len(rows), len(cases)) != (T2A_B, T2A_LOSSES):
        raise SystemExit(f"T2a B: {len(rows)} injections, {len(cases)} losses: STOP")
    _check_published("T2a B", [c for c in cases if c["verdict"] != "unknown record"], published)
    f = floors(cases)
    # I1's class-(ii) `systematics` blockers other than the grid refusals: the published 24
    non_grid_ii = Counter(
        "+".join(b["categories"]) for c in cases for b in c["blockers"]
        if b["test"] == "systematics" and b.get("i1_class") == "ii"
        and not b.get("i1_grid_refusal")
    )  # fmt: skip
    if sum(non_grid_ii.values()) != NON_GRID_II:
        raise SystemExit(f"T2a: {sum(non_grid_ii.values())} non-grid class (ii), not 24: STOP")
    exhausted = []
    if f["F_strict"] > T2A_ALLOWED:
        exhausted.append("F_strict (data limits)")
    if f["F_rule"] > T2A_ALLOWED:
        exhausted.append("F_rule (with the messages taken at face value)")
    if exhausted:
        outcome = "exhausted under the stated assumptions (no draft): " + "; ".join(exhausted)
    elif f["F_upper"] <= T2A_ALLOWED:
        outcome = "margin left, if every REC and PROC loss is recovered (assumed)"
    else:
        outcome = "INCONCLUSIVE"
    o = f["outside_refuted"]
    return {"injections": len(rows), "losses": len(cases), "allowed": T2A_ALLOWED,
            "allowed_if_the_5_refuted_stay": T2A_IF_REFUTED_STAY,
            "allowed_in_c_conditional": T2A_C, **f,
            "margins": {
                "B": {k: T2A_ALLOWED - f[k] for k in ("F_strict", "F_rule", "F_upper")},
                "B_refuted_stay": {k: T2A_IF_REFUTED_STAY - o[k]
                                   for k in ("F_strict", "F_rule", "F_upper")},
                "C_conditional": {k: T2A_C - f[k] for k in ("F_strict", "F_rule", "F_upper")}},
            "systematics_class_ii_non_grid_by_categories": dict(non_grid_ii),
            "outcome": outcome, "cases": cases}  # fmt: skip


def main() -> None:
    if OUT_FILE.exists():
        raise SystemExit(f"{OUT_FILE.name} exists: written once")
    published = json.loads(PUBLISHED.read_text("utf-8"))
    rows1 = i1_diagnose.schedule()
    i1, refusal = i1_diagnose._read(rows1, i1_diagnose.fingerprint(rows1))
    if refusal:
        raise SystemExit(f"I1: {refusal}: STOP")
    i1_by = {}
    for r in i1:
        if r.get("status") != "OK" or r.get("mismatch"):
            continue
        if r["kind"] not in ("d2", "t2a"):
            raise SystemExit(f"I1: an unexpected kind {r['kind']}: STOP")
        k = ("d2", r["index"]) if r["kind"] == "d2" else ("t2a", r["key"], r["slot"])
        if k in i1_by:
            raise SystemExit(f"I1: {k} twice: STOP")
        i1_by[k] = r
    rows4 = i4_bound.schedule()
    i4, refusal, _ = i4_rest2._records(rows4, i4_bound.fingerprint(rows4))
    if refusal:
        raise SystemExit(f"I4: {refusal}: STOP")
    i4_by = {r["index"]: r for r in i4 if r.get("set") == "fresh"}
    d2 = d2_part(i1_by, i4_by, published["d2"]["v5"]["decisive_blockers_by_test"])
    t2a_pub = Counter()
    for s in STRATA_B:
        t2a_pub.update(published["t2a"]["B"]["by_stratum"][s]["decisive_blockers_by_test"])
    t2a = t2a_part(i1_by, dict(t2a_pub))
    CACHE.mkdir(parents=True, exist_ok=True)
    detail = {"d2": d2.pop("cases"), "t2a": t2a.pop("cases")}
    text = json.dumps(detail, indent=1, sort_keys=True) + "\n"
    (CACHE / "cases.json").write_text(text, "utf-8", newline="\n")
    doc = {
        "label": "v0.5.4 step 1: D2's joint floor and T2a's losses no procedure fixes (a reading "
        "of existing records under stated assumptions; never a draft)",
        "method_status": "not_validated",
        "decision": "the maintainer's decision of 2026-11-12 (night), item 4a (#217)",
        "design": "docs/plans/v0.5.4-h2-step1-floor.md",
        "disclosure": "the marginal counts were known before this reading; only the per-case "
        "overlaps are new (see the design's disclosure)",
        "categories": {"strict": sorted(STRICT), "rule": sorted(RULE), "upper": sorted(UPPER)},
        "i1_records": len(i1),
        "i4_fresh_records": len(i4_by),
        "d2": d2,
        "t2a": t2a,
        "per_case_detail_sha256": hashlib.sha256(text.encode()).hexdigest(),
    }
    OUT_FILE.write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n", "utf-8", newline="\n")
    print(json.dumps({k: {x: doc[k][x] for x in ("F_strict", "F_rule", "F_upper", "outcome")}
                      for k in ("d2", "t2a")}, indent=1))  # fmt: skip


if __name__ == "__main__":
    main()
