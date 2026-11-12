"""v0.5.3 stage B: the decisive blockers of B1.4's losses, a new record (#217; the maintainer's
decision of 2026-11-12, item 2). **Read only; it decides nothing.** ``method_status:
not_validated``.

**Why a new record.** A verdict aggregates only the decisive tests (``core/verdict.aggregate``
over ``pipeline.expected_by_role``'s decisive set), and a stage verdict only those not deferred at
that stage (``discover/measure.py``, ``stage_tests``). ``duration_excess``, ``event_consistency``,
``single_event``, ``centroid_shift`` and ``holdout_by_year`` are diagnostics
(``calib051/values.py``, ``V051_DIAGNOSTIC``). ``b1_t2a_blockers.py`` and the D2 blocker list of
``b1_b14.d2d4_summary`` counted every INCONCLUSIVE or FAIL test, diagnostics and warning FAILs
included. Neither those scripts nor their outputs are edited.

**A decisive blocker of a loss** (a verdict other than SURVIVED or WEAKENED), by ``aggregate``'s
order: the gate (``snr``) not PASS; a fatal FAIL (REFUTED); a decisive test INCONCLUSIVE; a
decisive test missing. A warning FAIL gives WEAKENED, which is kept, so it never blocks; it is
counted apart, as are the diagnostics, to show what the earlier lists added.

- **T2a** (the census's records, ``b1_b14._records``): the stage tests are each brief's
  ``decisive`` less its ``deferred``; every test's severity is recorded. Configurations A, B and
  C as ``b1_b14.t2a_summary`` reads them (B: C up to 20 measured sectors, A above), by stratum.
  Above 20 sectors A did not run: those losses are the refusal by construction.
- **D2** (the 200 records of the completed part, ``b1_d2d4_rest.complete_records``): the decisive
  set is the version-4 plan's (``expected_by_role(p4, False)``, as ``forecast_v4._verdict``), with
  the tests deferred at stage 2 recorded. The D2 records keep no severity: in an INCONCLUSIVE loss
  every decisive FAIL is a warning (a fatal one gives REFUTED); in a REFUTED loss the decisive
  FAILs are listed with the severity unknown (at least one is fatal).

**The estimators** (item 2(b)): E2 is ``odd_even``, E3 ``sinusoid`` (``box_after_model``), E4
``systematics``' background sub-check. For each configuration's losses: how many have that test
as a decisive blocker, and, among those, whether the estimator operated in that attack (E2
``e2.gls``, E3 ``e3.gls``, E4 ``e4.measured``, each at least once in the record's counters), fell
back to version 4's computation (E4: was called and completed no measurement), or was not
reached. "The only decisive blocker" is the only one in the branch of ``aggregate`` that gave the
verdict: removing a fatal FAIL could reveal INCONCLUSIVEs it hides. Missing tests and
INCONCLUSIVEs are listed together (``aggregate`` returns on the missing ones first; none occurs in
these records). Writes ``b1-blockers-decisive.json``.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import b1_b14  # noqa: E402,I001
import b1_d2d4_rest  # noqa: E402
from b1_b14 import fv, ledger_b  # noqa: E402

OUT_FILE = HERE / "b1-blockers-decisive.json"
KEPT = b1_b14.KEPT
DIAGNOSTIC = ("duration_excess", "event_consistency", "single_event", "centroid_shift",
              "holdout_by_year")  # fmt: skip
ESTIMATORS = {  # estimator: (test, the counter of its own path, the counter of its calls)
    "E2": ("odd_even", "e2.gls", "e2.calls"),
    "E3": ("sinusoid", "e3.gls", "e3.calls"),
    "E4": ("systematics", "e4.measured", "e4.calls"),
}
STRATA = ("2_to_4", "5_to_20", "above_20")


def _label(name: str, row: dict) -> str:
    cls = row.get("inconclusive_class") or row.get("class")
    return f"{name} {row.get('status')}" + (f" ({cls})" if cls else "")


def _refusal(text: str | None) -> str | None:
    if not text:
        return None
    for key, label in (("not certified", "the selector not certified"),
                       ("above the supported", "above 20 sectors"),
                       ("outside the grid", "measured events outside the grid")):  # fmt: skip
        if key in text:
            return label
    return "other: " + text


def t2a_blockers(brief: dict) -> tuple[list, list, list]:
    """(decisive blockers, warning FAILs, diagnostics INCONCLUSIVE or FAIL) of a T2a brief."""
    stage = [n for n in brief["decisive"] if n not in brief["deferred"]]
    tests = brief["tests"]
    verdict = brief["stage_verdict"]
    present = {n: tests[n] for n in stage if n in tests}
    gate = [_label(n, r) for n, r in present.items()
            if r.get("severity") == "gate" and r["status"] != "PASS"]  # fmt: skip
    fatal = [_label(n, r) for n, r in present.items()
             if r["status"] == "FAIL" and r.get("severity") == "fatal"]  # fmt: skip
    warnings = [_label(n, r) for n, r in present.items()
                if r["status"] == "FAIL" and r.get("severity") == "warning"]  # fmt: skip
    # aggregate's order: the gate, then the fatal FAILs, then missing tests and INCONCLUSIVEs
    if gate:
        blockers, expected = gate, "INCONCLUSIVE"
    elif fatal:
        blockers, expected = fatal, "REFUTED"
    else:
        blockers = [f"{n} missing" for n in stage if n not in tests]
        blockers += [_label(n, r) for n, r in present.items() if r["status"] == "INCONCLUSIVE"]
        expected = "INCONCLUSIVE" if blockers else ("WEAKENED" if warnings else "SURVIVED")
    if verdict != expected:
        raise SystemExit(f"a T2a brief whose verdict {verdict} is not aggregate's {expected}")
    if verdict in KEPT:
        blockers = []
    diag = [_label(n, r) for n, r in tests.items()
            if n in DIAGNOSTIC and r["status"] in ("INCONCLUSIVE", "FAIL")]  # fmt: skip
    return blockers, warnings, diag


def d2_blockers(tests: dict, verdict: str, decisive: set) -> tuple[list, list, list]:
    """(decisive blockers, FAILs that are warnings, diagnostics) of a D2 attack."""
    present = {n: tests[n] for n in sorted(decisive) if n in tests}
    fails = [_label(n, r) for n, r in present.items() if r["status"] == "FAIL" and n != "snr"]
    gate = present.get("snr", {}).get("status")
    if verdict in KEPT:
        blockers, warnings = [], fails  # a FAIL in a kept verdict is a warning
    elif gate != "PASS":  # aggregate's first rule
        blockers, warnings = [f"snr {gate}" if gate else "snr missing"], []
    elif verdict == "REFUTED":  # at least one of these FAILs is fatal; the record has no severity
        blockers, warnings = [f + " [severity not recorded]" for f in fails], []
        if not fails:
            raise SystemExit("a REFUTED D2 attack without a decisive FAIL")
    else:  # INCONCLUSIVE: a fatal FAIL would have given REFUTED, so every FAIL is a warning
        blockers = [f"{n} missing" for n in sorted(decisive) if n not in tests]
        blockers += [_label(n, r) for n, r in present.items() if r["status"] == "INCONCLUSIVE"]
        warnings = fails
    diag = [_label(n, r) for n, r in tests.items()
            if n in DIAGNOSTIC and r["status"] in ("INCONCLUSIVE", "FAIL")]  # fmt: skip
    return blockers, warnings, diag


def _estimator_state(counts, estimator: str) -> str:
    _, own, calls = ESTIMATORS[estimator]
    if not isinstance(counts, dict) or not counts.get(calls):
        return "not reached"
    if counts.get(own):
        return "operated"
    # E4 without a completed measurement returns none; it does not call version 4's operator
    # (``battery_b1``, Codex's round 1 of this record)
    return "called, no measurement completed" if estimator == "E4" else "fell back to version 4"


class View:
    """The counts of one configuration over one set of records."""

    def __init__(self) -> None:
        self.n = self.kept = self.unknown = self.lost = self.lost_v04_kept = 0
        self.verdicts: Counter = Counter()
        self.blockers: Counter = Counter()
        self.by_test: Counter = Counter()
        self.sole: Counter = Counter()
        self.sets: Counter = Counter()
        self.refusals: Counter = Counter()
        self.warnings: Counter = Counter()
        self.diagnostics: Counter = Counter()
        self.no_blocker = 0
        self.estimators = {e: Counter() for e in ESTIMATORS}
        self.estimators_all = {e: Counter() for e in ESTIMATORS}

    def add(self, verdict, blockers, warnings, diag, refusal, counts, v04_kept: bool) -> None:
        self.n += 1
        for e in ESTIMATORS:
            self.estimators_all[e][_estimator_state(counts, e)] += 1
        if verdict in KEPT:
            self.kept += 1
            return
        self.lost += 1
        self.lost_v04_kept += v04_kept
        self.verdicts[verdict] += 1
        self.blockers.update(blockers)
        tests = sorted({b.split(" ")[0] for b in blockers})
        self.by_test.update(tests)
        self.sets["+".join(tests) or "(none)"] += 1
        if len(blockers) == 1:
            self.sole[blockers[0]] += 1
        if not blockers:
            self.no_blocker += 1
        if refusal:
            self.refusals[refusal] += 1
        self.warnings.update(warnings)
        self.diagnostics.update(diag)
        for e, (test, _, _) in ESTIMATORS.items():
            if test in tests:
                self.estimators[e][_estimator_state(counts, e)] += 1

    def lost_by_refusal(self, reason: str, v04_kept: bool) -> None:
        """A loss by construction (A above 20 sectors: refused, not run)."""
        self.n += 1
        self.lost += 1
        self.lost_v04_kept += v04_kept
        self.verdicts["not run: " + reason] += 1
        self.sets["(refused: " + reason + ")"] += 1
        self.refusals[reason] += 1

    def as_dict(self) -> dict:
        def top(c: Counter) -> dict:
            return dict(sorted(c.items(), key=lambda kv: (-kv[1], kv[0])))

        return {
            "records": self.n, "kept": self.kept, "unknown": self.unknown, "lost": self.lost,
            "lost_v04_kept": self.lost_v04_kept, "loss_verdicts": top(self.verdicts),
            "decisive_blockers_overlapping": top(self.blockers),
            "decisive_blockers_by_test": top(self.by_test),
            "losses_by_set_of_blocking_tests": top(self.sets),
            "sole_decisive_blocker": top(self.sole),
            "losses_without_a_decisive_blocker": self.no_blocker,
            "selection_refusals_in_losses": top(self.refusals),
            "warning_fails_in_losses_not_blockers": top(self.warnings),
            "diagnostics_in_losses_not_blockers": top(self.diagnostics),
            "estimators_in_losses_with_their_test_blocking": {
                e: {"test": ESTIMATORS[e][0], **top(c)} for e, c in self.estimators.items()
            },
            "estimators_over_every_record": {
                e: {"test": ESTIMATORS[e][0], **top(c)} for e, c in self.estimators_all.items()
            },
        }  # fmt: skip


def t2a() -> dict:
    pop = b1_b14.ft.population()
    got = {}
    for s in STRATA:
        for r in b1_b14._records(s):
            got[(r["key"], r["slot"])] = r
    views = {c: {s: View() for s in STRATA} for c in ("A", "B", "C")}
    for row in pop:
        rec = got.get((row["key"], row["slot"]))
        s = row["stratum"]
        v04_kept = row["v04_stage"] in KEPT
        for c in ("A", "B", "C"):
            view = views[c][s]
            if rec is None or rec.get("status") != "OK" or rec.get("compat_problems"):
                view.n += 1
                view.unknown += 1
                continue
            b = {"A": "v5A", "C": "v5C"}.get(c) or ("v5C" if rec["sectors"] <= 20 else "v5A")
            if b not in rec:
                if b == "v5A" and s == "above_20":
                    view.lost_by_refusal("above 20 sectors (version 5 A not run)", v04_kept)
                    continue
                raise SystemExit(f"{row['key']}/{row['slot']}: {b} missing: refused")
            counts = rec.get(f"{b}_counts")
            if isinstance(counts, str):  # C equals A at most 4 sectors
                counts = rec.get("v5A_counts")
            brief = rec[b]
            blockers, warnings, diag = t2a_blockers(brief)
            refusal = _refusal((brief.get("selection") or {}).get("refused"))
            view.add(brief["stage_verdict"], blockers, warnings, diag, refusal, counts, v04_kept)
    out: dict = {}
    for c, by in views.items():
        out[c] = {"by_stratum": {s: v.as_dict() for s, v in by.items()}}
        measured = by["2_to_4"].kept + by["5_to_20"].kept
        out[c]["kept_2_to_20"] = measured
        out[c]["unknown_2_to_20"] = by["2_to_4"].unknown + by["5_to_20"].unknown
        out[c]["kept_615"] = measured + by["above_20"].kept
    return out


def d2() -> dict:
    from refute.packs.tess.pipeline import expected_by_role

    recs, per_part, _, fp = b1_d2d4_rest.complete_records()
    _, _, p4 = fv.plans()
    decisive = set(expected_by_role(p4, False)[0])
    deferred = sorted(n for n, st in dict(p4.discovery.stages).items() if int(st) > 2)
    eligible = [r for r in recs if r.get("status") == "OK" and r["gate_passed"] and r["identity"]]
    out: dict = {"records": len(recs), "records_per_part": per_part, "fingerprint": fp,
                 "eligible": len(eligible), "decisive_tests": sorted(decisive),
                 "deferred_at_stage_2": deferred}  # fmt: skip
    for b in ("v4", "v5"):
        view = View()
        for r in eligible:
            blockers, warnings, diag = d2_blockers(r[f"{b}_tests"], r[b], decisive)
            refused = next((row.get("refused") for row in r[f"{b}_tests"].values()
                            if row.get("refused")), None)  # fmt: skip
            counts = r.get("v5_counts") if b == "v5" else None
            view.add(r[b], blockers, warnings, diag, _refusal(refused), counts, r["v04"] in KEPT)
        out[b] = view.as_dict()
        if b == "v4":
            out[b].pop("estimators_in_losses_with_their_test_blocking")
            out[b].pop("estimators_over_every_record")
    return out


def summarize() -> None:
    forecast = json.loads((HERE / "b1-forecast.json").read_text("utf-8"))["t2a"]
    t = t2a()
    conf = forecast["configurations"]
    checks = {
        "A_kept_2_to_20": (t["A"]["kept_2_to_20"], conf["v5A"]["kept_2_to_20"]),
        "B_kept_2_to_20 (K_B)": (t["B"]["kept_2_to_20"], conf["v5B"]["kept_2_to_20"]),
        "B_unknown_2_to_20 (U_B)": (t["B"]["unknown_2_to_20"], conf["v5B"]["unknown_2_to_20"]),
        "C_kept_615": (t["C"]["kept_615"], conf["v5C"]["lower_615"]),
    }
    bad = {k: v for k, v in checks.items() if v[0] != v[1]}
    if bad:
        raise SystemExit(f"the counts differ from b1-forecast.json: {bad}: refused")
    out = {
        "label": "B1.4's losses: decisive blockers only (a new record; decides nothing)",
        "method_status": "not_validated",
        "decision": "the maintainer's decision of 2026-11-12, item 2 (#217)",
        "definition": "a decisive blocker of a loss: the gate not PASS, a fatal FAIL (REFUTED), a "
        "decisive stage test INCONCLUSIVE, or a decisive test missing; a warning FAIL gives "
        "WEAKENED (kept) and diagnostics never enter the verdict, so both are counted apart",
        "diagnostic_tests": list(DIAGNOSTIC),
        "supersedes_as_blocker_lists": ["b1-t2a-blockers.json (blockers, sole_blocker)",
                                        "b1-forecast.json (d2_d4.v5_blockers)"],
        "t2a_answer_unchanged": {k: v[0] for k, v in checks.items()},
        "t2a": t,
        "d2": d2(),
    }  # fmt: skip
    OUT_FILE.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n", "utf-8", newline="\n")
    print(json.dumps({"t2a_answer_unchanged": out["t2a_answer_unchanged"]}, indent=1))


if __name__ == "__main__":
    with ledger_b.Exclusive("b1_blockers_decisive"):
        summarize()
