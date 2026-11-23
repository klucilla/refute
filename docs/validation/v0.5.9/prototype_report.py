"""v0.5.9 (exploratory prototype): the report of the five questions, with their counting rules
fixed before any result (docs/plans/v0.5.9-plan.md, "The questions").

**Inputs:** ``prototype-records.json`` (the 48 mode records, written by ``prototype_run.py
bundle``), ``prototype-set.json`` and ``prototype-ledger.json``.
**Outputs:** ``prototype-report.json`` and ``prototype-report.md``.

**Everything is exploratory.** The marks are counts with their Wilson 95 % intervals, never
verdicts, never candidates and never doors with a threshold. The numbers describe these 24 TOIs
only. Every record carries the limits label 'WEAKENED; does not meet D1, D2, D4, T2a'.

**Rules fixed before any result:**
- **Completeness.** The marks are given only when there is exactly one record per TOI and mode
  (48) and every record has a status; until then the report says ``incomplete`` and marks nothing.
- **A pair** is one TOI's E record and S record. A record that is not OK makes its pair not
  stable and not decided.
- **Q1, the 14 changes** (``changes`` and ``reverse``): a pair is *stable without consensus* when
  both bases are OK and give the same class; *stable with consensus* when both consensus outputs
  are OK and give the same class. Each count is split into both decided and both INCONCLUSIVE.
- **Q2, the 8 controls:** a control *stays unchanged* when both bases (without consensus), or both
  consensus outputs (with consensus), give the class its v0.5.6 and v0.5.8 records gave.
- **Q3, the two numerical ERRORs:** each of the four records ends with a status other than ERROR
  and a reason (an OK record has an outcome and its reason). The guarded numerical failures are
  listed.
- **Q4, decidability:** per mode, the decided outputs (SURVIVED, WEAKENED, REFUTED) over the 24
  TOIs and over the 14 changes, without and with consensus; the difference is the cost in
  decidability.
- **Q5, cost:** CPU seconds of the fit, the base evaluation and each probe axis (mean, median and
  maximum over the recorded units), the fetch and the bytes per TOI, and the ledger's totals.

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


def complete(records: list[dict], keys: list[str]) -> tuple[bool, list[str]]:
    problems = []
    found = Counter((r.get("target_key"), r.get("entry_mode")) for r in records)
    want = {(k, m) for k in keys for m in MODES}
    if set(found) != want:
        problems.append(f"{len(want - set(found))} TOI-mode pairs have no record; "
                        f"{len(set(found) - want)} are outside the set")  # fmt: skip
    if any(n > 1 for n in found.values()):
        problems.append("duplicate records")
    if any(not r.get("status") for r in records):
        problems.append("a record has no status")
    return not problems, problems


def pairs(by: dict, keys: list[str], fn) -> dict:
    same = [k for k in keys if fn(by.get((k, "E"))) is not None
            and fn(by.get((k, "E"))) == fn(by.get((k, "S")))]  # fmt: skip
    return {
        "stable": rate(len(same), len(keys)),
        "both_decided": sum(fn(by[(k, "E")]) in DECIDED for k in same),
        "both_inconclusive": sum(fn(by[(k, "E")]) == "INCONCLUSIVE" for k in same),
        "per_toi": {k: {"E": fn(by.get((k, "E"))), "S": fn(by.get((k, "S")))} for k in keys},
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
            "unchanged_base": out["base"], "unchanged_consensus": out["consensus"]}  # fmt: skip


def q3(by: dict, keys: list[str]) -> dict:
    rows = []
    for k in keys:
        for m in MODES:
            r = by.get((k, m)) or {}
            b = r.get("base") or {}
            ended = r.get("status") not in (None, "ERROR", "NO RECORD") and bool(
                (b.get("outcome") and b.get("outcome_reason")) or b.get("reason")
                or r.get("status") != "OK"
            )  # fmt: skip
            guarded = sorted({*(b.get("numerical_failures_guarded") or []),
                              *(x for p in (r.get("probes") or {}).values() if p
                                for x in (p.get("numerical_failures_guarded") or []))})  # fmt: skip
            rows.append({"target_key": k, "toi": r.get("toi"), "entry_mode": m,
                         "status": r.get("status"), "outcome": b.get("outcome"),
                         "reason": b.get("outcome_reason") or b.get("reason"),
                         "ended_with_status_and_reason": ended,
                         "guarded_numerical_failures": guarded})  # fmt: skip
    return {"rows": rows, "all_ended": all(r["ended_with_status_and_reason"] for r in rows)}


def q4(by: dict, keys: list[str]) -> dict:
    out = {}
    for m in MODES:
        b = sum(base_out(by.get((k, m))) in DECIDED for k in keys)
        c = sum(cons_out(by.get((k, m))) in DECIDED for k in keys)
        out[m] = {"base": rate(b, len(keys)), "consensus": rate(c, len(keys)),
                  "lost_to_consensus": b - c}  # fmt: skip
    return out


def _stats(values: list[float]) -> dict:
    v = [x for x in values if isinstance(x, (int, float))]
    if not v:
        return {"n": 0}
    return {"n": len(v), "mean": statistics.fmean(v), "median": statistics.median(v),
            "max": max(v), "sum": sum(v)}  # fmt: skip


def q5(records: list[dict], ledger: dict | None) -> dict:
    per_axis: dict[str, list[float]] = {"epoch": [], "period": [], "duration": []}
    fit = {m: [] for m in MODES}
    evals = {m: [] for m in MODES}
    for r in records:
        c = r.get("cost") or {}
        fit[r["entry_mode"]].append(c.get("fit_cpu_seconds"))
        evals[r["entry_mode"]].append(c.get("base_evaluation_cpu_seconds"))
        for name, sec in (c.get("probe_cpu_seconds") or {}).items():
            if sec is not None:
                per_axis[AXES[name]].append(sec)
    seen, fetch_cpu, gb = set(), [], []
    for r in records:
        if r["target_key"] in seen:
            continue
        seen.add(r["target_key"])
        c = r.get("cost") or {}
        fetch_cpu.append(c.get("fetch_cpu_seconds"))
        if c.get("download_bytes_of_the_toi") is not None:
            gb.append(c["download_bytes_of_the_toi"] / 1e9)
    totals = None
    if ledger:
        last = (ledger.get("batches") or [{}])[-1]
        totals = {"cpu_hours_charged": last.get("cpu_hours_charged"),
                  "disk_peak_bytes": ledger.get("disk_peak_bytes"),
                  "batches": len(ledger.get("batches") or []),
                  "state": ledger.get("state")}  # fmt: skip
    return {
        "probe_cpu_seconds_per_axis": {a: _stats(v) for a, v in per_axis.items()},
        "fit_cpu_seconds": {m: _stats(v) for m, v in fit.items()},
        "base_evaluation_cpu_seconds": {m: _stats(v) for m, v in evals.items()},
        "fetch_cpu_seconds": _stats(fetch_cpu),
        "downloaded_gb_per_toi": _stats(gb),
        "ledger": totals,
    }


def describe(by: dict, keys: list[str]) -> dict:
    """Descriptions, never marks: the entry, the identity, the first disagreeing probes."""
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
    return {"entry_unresolved": dict(unresolved), "stayed_on_toi_ephemeris": dict(matched),
            "first_disagreeing_axis": dict(first),
            "all_24": {"base": pairs(by, keys, base_out)["stable"],
                       "consensus": pairs(by, keys, cons_out)["stable"]}}  # fmt: skip


def build() -> dict:
    s = json.loads(SET_FILE.read_text("utf-8"))
    keys = list(s["order"])
    records = json.loads(BUNDLE.read_text("utf-8"))["records"] if BUNDLE.exists() else []
    ledger = json.loads(LEDGER.read_text("utf-8")) if LEDGER.exists() else None
    ok, problems = complete(records, keys)
    by = {(r["target_key"], r["entry_mode"]): r for r in records}
    changes = [*s["changes"], *s["reverse"]]
    rep = {
        "schema": "refute-v059-prototype-report-1",
        "mode": "exploratory",
        "limits_label": LABEL,
        "method_status": "not_validated",
        "code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "set_sha256": hashlib.sha256(SET_FILE.read_bytes()).hexdigest(),
        "records_sha256": hashlib.sha256(BUNDLE.read_bytes()).hexdigest()
        if BUNDLE.exists() else None,
        "records": len(records),
        "complete": ok,
        "completeness_problems": problems,
    }  # fmt: skip
    if not ok:
        return rep
    rep.update({
        "q1": {"base": pairs(by, changes, base_out), "consensus": pairs(by, changes, cons_out)},
        "q2": q2(by, s["controls"]),
        "q3": q3(by, s["numeric_errors"]),
        "q4": {"all_24": q4(by, keys), "changes_14": q4(by, changes)},
        "q5": q5(records, ledger),
        "describe": describe(by, keys),
    })  # fmt: skip
    return rep


def fmt(r: dict) -> str:
    if r["n"] == 0:
        return "0 of 0"
    lo, hi = r["wilson95"]
    return f"{r['k']} of {r['n']} ({r['rate']:.3f}; Wilson 95 % {lo:.3f} to {hi:.3f})"


def markdown(rep: dict) -> str:
    lines = [
        "# v0.5.9: ephemeris entry, exploratory prototype",
        "",
        f"**Exploratory.** Limits label: '{rep['limits_label']}'. `method_status: "
        "not_validated`. Never a verdict, a candidate or a disposition; the numbers describe "
        "these 24 TOIs only. E enters through the TOI's ephemeris, S through the battery's own "
        "search, on the same input bytes.",
        "",
        f"Records: {rep['records']}; complete: {rep['complete']}.",
    ]
    if not rep["complete"]:
        lines += ["", "Not complete (nothing is marked):", ""]
        lines += [f"- {p}" for p in rep["completeness_problems"]]
        return "\n".join(lines) + "\n"
    q1, q2_, q3_, q4_, q5_ = rep["q1"], rep["q2"], rep["q3"], rep["q4"], rep["q5"]
    lines += ["", "## Q1: the 14 changes, E against S", ""]
    for v in ("base", "consensus"):
        p = q1[v]
        lines.append(f"- **{'Without' if v == 'base' else 'With'} consensus:** the same class in "
                     f"{fmt(p['stable'])}; both decided {p['both_decided']}, both INCONCLUSIVE "
                     f"{p['both_inconclusive']}.")  # fmt: skip
    lines += ["", "## Q2: the 8 controls keep their class", ""]
    lines += [f"- Without consensus: {fmt(q2_['base'])}.",
              f"- With consensus: {fmt(q2_['consensus'])}."]  # fmt: skip
    lines += ["", "## Q3: the two numerical ERRORs of v0.5.8", ""]
    for r in q3_["rows"]:
        lines.append(
            f"- TOI-{r['toi']} {r['entry_mode']}: {r['status']}, {r['outcome']}; "
            f"{r['reason']}; guarded: {', '.join(r['guarded_numerical_failures']) or 'none'}."
        )
    lines.append(f"- All four end with a status and a reason: {q3_['all_ended']}.")
    lines += ["", "## Q4: decided outputs, without and with consensus", ""]
    for scope, label in (("all_24", "the 24"), ("changes_14", "the 14 changes")):
        for m in MODES:
            d = q4_[scope][m]
            lines.append(
                f"- {label}, {m}: without {fmt(d['base'])}; with "
                f"{fmt(d['consensus'])}; lost to consensus {d['lost_to_consensus']}."
            )
    lines += ["", "## Q5: cost", ""]
    for axis, st in q5_["probe_cpu_seconds_per_axis"].items():
        if st["n"]:
            lines.append(f"- probe `{axis}`: {st['n']} units, CPU mean {st['mean']:.0f} s, median "
                         f"{st['median']:.0f} s, max {st['max']:.0f} s.")  # fmt: skip
    for m in MODES:
        f, e = q5_["fit_cpu_seconds"][m], q5_["base_evaluation_cpu_seconds"][m]
        if f["n"]:
            lines.append(f"- {m}: fit CPU mean {f['mean']:.0f} s; base evaluation mean "
                         f"{e.get('mean', 0):.0f} s.")  # fmt: skip
    g = q5_["downloaded_gb_per_toi"]
    if g["n"]:
        lines.append(f"- Downloads: {g['sum']:.2f} GB over {g['n']} TOIs (mean {g['mean']:.3f}).")
    if q5_["ledger"]:
        lines.append(f"- Ledger: {q5_['ledger']}.")
    lines += ["", "## Descriptions (not marks)", "", f"- {rep['describe']}"]
    return "\n".join(lines) + "\n"


def main() -> None:
    rep = build()
    OUT_JSON.write_text(json.dumps(rep, indent=1) + "\n", "utf-8", newline="\n")
    OUT_MD.write_text(markdown(rep), "utf-8", newline="\n")
    print("complete:", rep["complete"])


if __name__ == "__main__":
    main()
