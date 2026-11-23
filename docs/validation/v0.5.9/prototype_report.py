"""v0.5.9 (exploratory prototype): the report of the five questions, with their counting rules
fixed before any result (docs/plans/v0.5.9-plan.md, "The questions"), as revised by Codex's round
1 (blocking item 3 and the non-blocking items), still before any result.

**Inputs:** ``prototype-records.json`` (the 48 mode records and the run's terminal state, written
by ``prototype_run.py bundle``), ``prototype-set.json`` and ``prototype-ledger.json``.
**Outputs:** ``prototype-report.json`` and ``prototype-report.md``.

**Everything is exploratory.** The marks are counts with their Wilson 95 % intervals, never
verdicts, never candidates and never doors with a threshold. The numbers describe these 24 TOIs
only. Every record carries the limits label 'WEAKENED; does not meet D1, D2, D4, T2a'.

**Rules fixed before any result:**
- **Completeness.** Nothing is marked unless:
  - the run reached a terminal state (``complete``, ``stopped`` or ``abandoned``), recorded in the
    bundle;
  - there is exactly one row per TOI and mode (48), each with a status.

  Then each question is marked only if every TOI it reads is complete: both rows have a status
  other than ``NO RECORD``, no required unit is missing, and no consensus is ``INCOMPLETE``. A
  recorded failure with its reason (an ERROR, a download that failed, a unit stopped at a cap)
  is complete; a unit never run is not. The incomplete TOIs are listed.
- **A pair** is one TOI's E row and S row. A row that is not OK makes its pair neither the same
  class nor decided.
- **Q1, the 14 changes** (``changes`` and ``reverse``), without consensus (both bases) and with
  consensus (both consensus outputs):
  - **the headline:** pairs with the same *decided* class;
  - beside it: pairs that are both INCONCLUSIVE (joint abstentions), and pairs with the same
    class of either kind;
  - apart: the same counts over the pairs whose two fits stayed on the TOI ephemeris.
- **Q2, the 8 controls:** a control keeps its class when both bases (without consensus), or both
  consensus outputs (with consensus), give the class its v0.5.6 and v0.5.8 records gave (for the
  two INCONCLUSIVE controls, INCONCLUSIVE).
- **Q3, the two numerical ERRORs:** for each of the four rows:
  - *ended:* a status other than ERROR or ``NO RECORD``, with a reason;
  - *evaluated:* the base ran the tests (an unresolved entry or a unit not run is reported apart);
  - the base's ``centroid_shift`` status and message, and every guarded numerical failure of the
    base and of its probes, with its reason.
- **Q4, decidability:** per mode, the decided outputs (SURVIVED, WEAKENED, REFUTED) over the 24
  and over the 14 changes, without and with consensus; the difference is the cost in
  decidability.
- **Q5, cost:** per probe axis, the whole unit's CPU and the evaluation's CPU apart (mean,
  median, maximum); per mode, the fit's and the base evaluation's CPU; the fetch's CPU; the bytes
  per TOI (the manifest's and the metered transfer); the ledger's totals.

Usage (from the project root): ``prototype_report.py``
"""

from __future__ import annotations

import hashlib
import json
import math
import statistics
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
BUNDLE = HERE / "prototype-records.json"
SET_FILE = HERE / "prototype-set.json"
LEDGER = HERE / "prototype-ledger.json"
OUT_JSON = HERE / "prototype-report.json"
OUT_MD = HERE / "prototype-report.md"
LABEL = "WEAKENED; does not meet D1, D2, D4, T2a"
DECIDED = ("SURVIVED", "WEAKENED", "REFUTED")
MODES = ("E", "S")
TERMINAL = ("complete", "stopped", "abandoned")
AXES = {"p1": "epoch", "p2": "epoch", "p3": "period", "p4": "period", "p5": "duration",
        "p6": "duration"}  # fmt: skip


def wilson(k: int, n: int, z: float = 1.959963984540054) -> list[float] | None:
    if n == 0:
        return None
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return [max(0.0, centre - half), min(1.0, centre + half)]


def rate(k: int, n: int) -> dict:
    return {"k": k, "n": n, "rate": None if n == 0 else k / n, "wilson95": wilson(k, n)}


def base_out(r: dict | None) -> str | None:
    if r is None or r.get("status") != "OK" or r.get("base") is None:
        return None
    return r["base"].get("outcome")


def cons_out(r: dict | None) -> str | None:
    if r is None or r.get("status") != "OK":
        return None
    c = r.get("consensus") or {}
    return c.get("outcome") if c.get("status") == "OK" else None


def complete(records: list[dict], keys: list[str], run_state: str | None) -> tuple[bool, list]:
    """The global conditions: a terminal run and one row with a status per TOI and mode."""
    problems = []
    if run_state not in TERMINAL:
        problems.append(f"the run is not in a terminal state ({run_state!r})")
    found = Counter((r.get("target_key"), r.get("entry_mode")) for r in records)
    want = {(k, m) for k in keys for m in MODES}
    if set(found) != want:
        problems.append(f"{len(want - set(found))} TOI-mode pairs have no row; "
                        f"{len(set(found) - want)} are outside the set")  # fmt: skip
    if any(n > 1 for n in found.values()):
        problems.append("duplicate rows")
    if any(not r.get("status") for r in records):
        problems.append("a row has no status")
    return not problems, problems


def toi_complete(by: dict, k: str) -> bool:
    for m in MODES:
        r = by.get((k, m))
        if r is None or r.get("status") in (None, "NO RECORD") or r.get("required_missing"):
            return False
        if (r.get("consensus") or {}).get("status") == "INCOMPLETE":
            return False
    return True


def pairs(by: dict, keys: list[str], fn) -> dict:
    out = {k: (fn(by.get((k, "E"))), fn(by.get((k, "S")))) for k in keys}
    same = [k for k, (e, s) in out.items() if e is not None and e == s]
    decided = [k for k in same if out[k][0] in DECIDED]
    abstain = [k for k in same if out[k][0] == "INCONCLUSIVE"]
    matched = [k for k in keys
               if all(((by.get((k, m)) or {}).get("identity") or {}).get("stayed_on_toi_ephemeris")
                      for m in MODES)]  # fmt: skip
    return {
        "same_decided_class": rate(len(decided), len(keys)),
        "both_inconclusive": rate(len(abstain), len(keys)),
        "same_class": rate(len(same), len(keys)),
        "identity_matched_pairs": {
            "n": len(matched),
            "same_decided_class": sum(k in decided for k in matched),
            "both_inconclusive": sum(k in abstain for k in matched),
        },
        "per_toi": {k: {"E": e, "S": s} for k, (e, s) in out.items()},
    }


def q2(by: dict, controls: dict[str, list[str]]) -> dict:
    out = {"base": [], "consensus": []}
    for cls, keys in controls.items():
        for k in keys:
            e, s = by.get((k, "E")), by.get((k, "S"))
            if base_out(e) == cls and base_out(s) == cls:
                out["base"].append(k)
            if cons_out(e) == cls and cons_out(s) == cls:
                out["consensus"].append(k)
    n = sum(len(v) for v in controls.values())
    return {"base": rate(len(out["base"]), n), "consensus": rate(len(out["consensus"]), n),
            "kept_base": out["base"], "kept_consensus": out["consensus"]}  # fmt: skip


def q3(by: dict, keys: list[str]) -> dict:
    rows = []
    for k in keys:
        for m in MODES:
            r = by.get((k, m)) or {}
            b = r.get("base") or {}
            reason = r.get("reason") or b.get("outcome_reason") or b.get("reason")
            centroid = (b.get("tests") or {}).get("centroid_shift") or {}
            guarded = {
                f"base:{n}": msg for n, msg in (b.get("numerical_failures_guarded") or {}).items()
            }
            for name, p in (r.get("probes") or {}).items():
                for n, msg in ((p or {}).get("numerical_failures_guarded") or {}).items():
                    guarded[f"{name}:{n}"] = msg
            rows.append({
                "target_key": k, "toi": r.get("toi"), "entry_mode": m,
                "status": r.get("status"), "outcome": b.get("outcome"), "reason": reason,
                "ended_with_status_and_reason":
                    r.get("status") not in (None, "ERROR", "NO RECORD") and bool(reason),
                "evaluated": bool(b.get("tests")),
                "centroid_shift": {"status": centroid.get("status"),
                                   "message": centroid.get("message")},
                "guarded_numerical_failures": guarded,
            })  # fmt: skip
    return {"rows": rows, "all_ended": all(r["ended_with_status_and_reason"] for r in rows),
            "all_evaluated": all(r["evaluated"] for r in rows)}  # fmt: skip


def q4(by: dict, keys: list[str]) -> dict:
    out = {}
    for m in MODES:
        b = sum(base_out(by.get((k, m))) in DECIDED for k in keys)
        c = sum(cons_out(by.get((k, m))) in DECIDED for k in keys)
        out[m] = {"base": rate(b, len(keys)), "consensus": rate(c, len(keys)),
                  "lost_to_consensus": b - c}  # fmt: skip
    return out


def _stats(values: list) -> dict:
    v = [x for x in values if isinstance(x, (int, float))]
    if not v:
        return {"n": 0}
    return {"n": len(v), "mean": statistics.fmean(v), "median": statistics.median(v),
            "max": max(v), "sum": sum(v)}  # fmt: skip


def q5(records: list[dict], ledger: dict | None) -> dict:
    unit = {a: [] for a in ("epoch", "period", "duration")}
    evaluation = {a: [] for a in ("epoch", "period", "duration")}
    fit = {m: [] for m in MODES}
    evals = {m: [] for m in MODES}
    for r in records:
        c = r.get("cost") or {}
        fit[r["entry_mode"]].append(c.get("fit_cpu_seconds"))
        evals[r["entry_mode"]].append(c.get("base_evaluation_cpu_seconds"))
        for name, sec in (c.get("probe_cpu_seconds") or {}).items():
            unit[AXES[name]].append(sec)
        for name, sec in (c.get("probe_evaluation_cpu_seconds") or {}).items():
            evaluation[AXES[name]].append(sec)
    seen, fetch_cpu, gb, metered = set(), [], [], []
    for r in records:
        if r["target_key"] in seen:
            continue
        seen.add(r["target_key"])
        c = r.get("cost") or {}
        fetch_cpu.append(c.get("fetch_cpu_seconds"))
        if c.get("download_bytes_of_the_toi") is not None:
            gb.append(c["download_bytes_of_the_toi"] / 1e9)
        if c.get("metered_download_bytes_of_the_toi") is not None:
            metered.append(c["metered_download_bytes_of_the_toi"] / 1e9)
    totals = None
    if ledger:
        last = (ledger.get("batches") or [{}])[-1]
        totals = {
            "cpu_hours_charged": last.get("cpu_hours_charged"),
            "downloaded_bytes_charged": last.get("downloaded_bytes_charged"),
            "disk_peak_bytes": ledger.get("disk_peak_bytes"),
            "batches": len(ledger.get("batches") or []),
            "state": ledger.get("state"),
            "state_reason": ledger.get("state_reason"),
        }
    return {
        "probe_unit_cpu_seconds_per_axis": {a: _stats(v) for a, v in unit.items()},
        "probe_evaluation_cpu_seconds_per_axis": {a: _stats(v) for a, v in evaluation.items()},
        "fit_cpu_seconds": {m: _stats(v) for m, v in fit.items()},
        "base_evaluation_cpu_seconds": {m: _stats(v) for m, v in evals.items()},
        "fetch_cpu_seconds": _stats(fetch_cpu),
        "downloaded_gb_per_toi": _stats(gb),
        "metered_gb_per_toi": _stats(metered),
        "ledger": totals,
    }  # fmt: skip


def describe(by: dict, keys: list[str]) -> dict:
    """Descriptions, never marks: the entry, the identity, the first disagreeing probes, and the
    all-24 pairs."""
    first = Counter()
    unresolved, matched = Counter(), Counter()
    for k in keys:
        for m in MODES:
            r = by.get((k, m)) or {}
            if r.get("status") != "OK":
                continue
            if not (r.get("fit") or {}).get("resolved"):
                unresolved[m] += 1
            if (r.get("identity") or {}).get("stayed_on_toi_ephemeris"):
                matched[m] += 1
            name = (r.get("consensus") or {}).get("first_disagreeing")
            if name:
                first[f"{m}:{AXES[name]}"] += 1
    return {
        "entry_unresolved": dict(unresolved),
        "stayed_on_toi_ephemeris": dict(matched),
        "first_disagreeing_axis": dict(first),
        "all_24": {"base": pairs(by, keys, base_out), "consensus": pairs(by, keys, cons_out)},
    }


def build() -> dict:
    s = json.loads(SET_FILE.read_text("utf-8"))
    keys = list(s["order"])
    doc = json.loads(BUNDLE.read_text("utf-8")) if BUNDLE.exists() else {}
    records = doc.get("records", [])
    ledger = json.loads(LEDGER.read_text("utf-8")) if LEDGER.exists() else None
    ok, problems = complete(records, keys, doc.get("run_state"))
    by = {(r["target_key"], r["entry_mode"]): r for r in records}
    changes = [*s["changes"], *s["reverse"]]
    controls = [k for v in s["controls"].values() for k in v]
    rep = {
        "schema": "refute-v059-prototype-report-2",
        "mode": "exploratory",
        "limits_label": LABEL,
        "method_status": "not_validated",
        "code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "set_sha256": hashlib.sha256(SET_FILE.read_bytes()).hexdigest(),
        "records_sha256": hashlib.sha256(BUNDLE.read_bytes()).hexdigest()
        if BUNDLE.exists() else None,
        "run_state": doc.get("run_state"),
        "records": len(records),
        "complete": ok,
        "completeness_problems": problems,
    }  # fmt: skip
    if not ok:
        return rep
    rep["incomplete_tois"] = [k for k in keys if not toi_complete(by, k)]

    def marked(scope: list[str], fn):
        missing = [k for k in scope if k in rep["incomplete_tois"]]
        return {"incomplete": missing} if missing else fn()

    rep.update({
        "q1": marked(changes, lambda: {"base": pairs(by, changes, base_out),
                                       "consensus": pairs(by, changes, cons_out)}),
        "q2": marked(controls, lambda: q2(by, s["controls"])),
        "q3": marked(s["numeric_errors"], lambda: q3(by, s["numeric_errors"])),
        "q4": marked(keys, lambda: {"all_24": q4(by, keys), "changes_14": q4(by, changes)}),
        "q5": q5(records, ledger),
        "describe": describe(by, keys),
    })  # fmt: skip
    return rep


def fmt(r: dict) -> str:
    if r["n"] == 0:
        return "0 of 0"
    lo, hi = r["wilson95"]
    return f"{r['k']} of {r['n']} ({r['rate']:.3f}; Wilson 95 % {lo:.3f} to {hi:.3f})"


def _stat_line(label: str, st: dict) -> str | None:
    if not st.get("n"):
        return None
    return (f"- {label}: {st['n']} units, CPU mean {st['mean']:.0f} s, median {st['median']:.0f} "
            f"s, max {st['max']:.0f} s.")  # fmt: skip


def markdown(rep: dict) -> str:
    lines = [
        "# v0.5.9: ephemeris entry, exploratory prototype",
        "",
        f"**Exploratory.** Limits label: '{rep['limits_label']}'. `method_status: "
        "not_validated`. Never a verdict, a candidate or a disposition; the numbers describe "
        "these 24 TOIs only. E enters through the TOI's ephemeris, S through the battery's own "
        "search, on the same input bytes.",
        "",
        f"Rows: {rep['records']}; run state: {rep['run_state']}; complete: {rep['complete']}.",
    ]
    if not rep["complete"]:
        lines += ["", "Not complete (nothing is marked):", ""]
        lines += [f"- {p}" for p in rep["completeness_problems"]]
        return "\n".join(lines) + "\n"
    if rep["incomplete_tois"]:
        lines += ["", f"Incomplete TOIs (their questions are not marked): {rep['incomplete_tois']}"]

    def unmarked(q: dict) -> bool:
        if "incomplete" in q:
            lines.append(f"- Not marked: incomplete TOIs {q['incomplete']}.")
            return True
        return False

    lines += ["", "## Q1: the 14 changes, E against S", ""]
    if not unmarked(rep["q1"]):
        for v in ("base", "consensus"):
            p = rep["q1"][v]
            im = p["identity_matched_pairs"]
            lines.append(
                f"- **{'Without' if v == 'base' else 'With'} consensus:** the same decided class "
                f"in {fmt(p['same_decided_class'])}; both INCONCLUSIVE "
                f"{fmt(p['both_inconclusive'])}; the same class of either kind "
                f"{fmt(p['same_class'])}. Over the {im['n']} pairs whose two fits stayed on the "
                f"TOI ephemeris: same decided class {im['same_decided_class']}, both INCONCLUSIVE "
                f"{im['both_inconclusive']}."
            )
    lines += ["", "## Q2: the 8 controls keep their class", ""]
    if not unmarked(rep["q2"]):
        lines += [f"- Without consensus: {fmt(rep['q2']['base'])}.",
                  f"- With consensus: {fmt(rep['q2']['consensus'])}."]  # fmt: skip
    lines += ["", "## Q3: the two numerical ERRORs of v0.5.8", ""]
    if not unmarked(rep["q3"]):
        for r in rep["q3"]["rows"]:
            lines.append(
                f"- TOI-{r['toi']} {r['entry_mode']}: {r['status']}, {r['outcome']}; "
                f"{r['reason']}; evaluated {r['evaluated']}; "
                f"centroid_shift {r['centroid_shift']['status']}; "
                f"guarded: {r['guarded_numerical_failures'] or 'none'}."
            )
        lines += [f"- All four ended with a status and a reason: {rep['q3']['all_ended']}; all "
                  f"four evaluated: {rep['q3']['all_evaluated']}."]  # fmt: skip
    lines += ["", "## Q4: decided outputs, without and with consensus", ""]
    if not unmarked(rep["q4"]):
        for scope, label in (("all_24", "the 24"), ("changes_14", "the 14 changes")):
            for m in MODES:
                d = rep["q4"][scope][m]
                lines.append(f"- {label}, {m}: without {fmt(d['base'])}; with "
                             f"{fmt(d['consensus'])}; lost to consensus "
                             f"{d['lost_to_consensus']}.")  # fmt: skip
    q5_ = rep["q5"]
    lines += ["", "## Q5: cost", ""]
    for axis in ("epoch", "period", "duration"):
        for kind, key in (("whole unit", "probe_unit_cpu_seconds_per_axis"),
                          ("evaluation", "probe_evaluation_cpu_seconds_per_axis")):  # fmt: skip
            line = _stat_line(f"probe `{axis}`, {kind}", q5_[key][axis])
            if line:
                lines.append(line)
    for m in MODES:
        for label, key in (("fit", "fit_cpu_seconds"),
                           ("base evaluation", "base_evaluation_cpu_seconds")):  # fmt: skip
            line = _stat_line(f"{m}, {label}", q5_[key][m])
            if line:
                lines.append(line)
    line = _stat_line("fetch", q5_["fetch_cpu_seconds"])
    if line:
        lines.append(line)
    for label, key in (("manifest", "downloaded_gb_per_toi"), ("metered", "metered_gb_per_toi")):
        g = q5_[key]
        if g["n"]:
            lines.append(f"- Downloads ({label}): {g['sum']:.2f} GB over {g['n']} TOIs (mean "
                         f"{g['mean']:.3f}).")  # fmt: skip
    if q5_["ledger"]:
        lines.append(f"- Ledger: {q5_['ledger']}.")
    d = rep["describe"]
    lines += ["", "## Descriptions (not marks)", "",
              f"- Entries unresolved: {d['entry_unresolved']}; fits on the TOI ephemeris: "
              f"{d['stayed_on_toi_ephemeris']}; first disagreeing axis: "
              f"{d['first_disagreeing_axis']}.",
              f"- All 24, same decided class: without consensus "
              f"{fmt(d['all_24']['base']['same_decided_class'])}; with consensus "
              f"{fmt(d['all_24']['consensus']['same_decided_class'])}."]  # fmt: skip
    return "\n".join(lines) + "\n"


def main() -> None:
    rep = build()
    OUT_JSON.write_text(json.dumps(rep, indent=1) + "\n", "utf-8", newline="\n")
    OUT_MD.write_text(markdown(rep), "utf-8", newline="\n")
    print("complete:", rep["complete"])


if __name__ == "__main__":
    main()
