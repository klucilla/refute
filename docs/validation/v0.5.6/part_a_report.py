"""v0.5.6 part A: the exploratory report (docs/plans/v0.5.6-plan.md, "What would count as
'looks like a door'"; the maintainer's decisions of 2026-11-21, 22:30, item 3, and 22:45,
item 3; #218).

**Exploratory.** Every number here describes the drawn sample, never the TOI population; no
output is a verdict on any TOI or a candidate in a public claim. ``method_status:
not_validated``. Limits label: 'WEAKENED; does not meet D1, D2, D4, T2a'.

**Written before the rest of part A ran** (only the 10 pilot records existed): the subgroup
family of door 1 is fixed here, so that it is not chosen after the outcomes are seen.

- **Denominators.** A record "has nonzero coverage" when its status is OK and at least one of its
  decisive tests examined data (coverage > 0). ERROR and MISSING_PRODUCTS records, and OK records
  with zero coverage, are coverage losses, counted per arm.
- **Door 1, a subgroup** (planet arm only). The family: for each observable property (TOI depth,
  TESS magnitude, predicted transits, number of listed sectors), the planet arm's records with
  nonzero coverage are cut at their median (2 subgroups) and at their tertiles (3 subgroups);
  values on a cut go to the lower group. A subgroup qualifies when it holds at least 20 records,
  the rest is nonzero, its SURVIVED rate is at least twice the rest's (with zero SURVIVED in the
  rest: at least 5 SURVIVED in the subgroup) and its INCONCLUSIVE rate is at most half the
  rest's.
- **Door 2, a systematic disagreement** (planet arm only): at least 5 REFUTED records whose first
  decisive fatal FAIL, in the battery's order, is the same test. A tie for the largest count
  counts for neither.
- **Door 3, a dominant cause** (planet arm only): a test with at least 10 INCONCLUSIVE results,
  more than half of them from one recorded cause. The cause is the test's recorded message with
  every number replaced by ``#``; a tie for the largest count counts for neither.
- If several doors qualify, the first in this order proceeds to part B; the others are reported.
- **The open arm** is described, never scored: outcomes by the TOI table's ``tfopwg_disp``
  (descriptive only; NExScI's answer of 2026-11-22), never as a label, a score or a verdict.
- **Signal identity:** the battery searches for its own candidate. Whether it matched the TOI
  (period factor 1 within 0.1 %, epoch within half the TOI's duration) is reported per arm as
  context; the doors use every record with nonzero coverage, as the plan writes them.

Usage: ``part_a_report.py [out_dir]`` (reads ``.cache/v056/run/records``; writes
``part-a-report.json`` and ``part-a-report.md`` next to this script, or into ``out_dir``).
"""

from __future__ import annotations

import hashlib
import json
import re
import statistics
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
RECORDS = ROOT / ".cache/v056/run/records"
DRAW = HERE / "part-a-draw.json"
LEDGER = HERE / "part-a-ledger.json"
LABEL = "WEAKENED; does not meet D1, D2, D4, T2a"
OUTCOMES = ("SURVIVED", "WEAKENED", "REFUTED", "INCONCLUSIVE")
DISPOSITIONS = ("PC", "APC", "FP", "FA", "KP", "CP")
PROPERTIES = {
    "depth_ppm": "TOI depth (ppm)",
    "tmag": "TESS magnitude",
    "predicted_transits": "predicted transits",
    "n_sectors": "listed sectors",
}
MIN_SUBGROUP = 20
MIN_REFUTED_CAUSE = 5
MIN_INCONCLUSIVE = 10
ACKNOWLEDGMENT = (
    "This research has made use of the Exoplanet Follow-up Observation Program (ExoFOP; DOI: "
    "10.26134/ExoFOP5) website, which is operated by the California Institute of Technology, "
    "under contract with the National Aeronautics and Space Administration under the Exoplanet "
    "Exploration Program."
)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load() -> list[dict]:
    draw = json.loads(DRAW.read_text("utf-8"))
    meta = {}
    for arm in ("planet", "open"):
        for c in draw["arms"][arm]["chosen"]:
            meta[f"TIC-{c['tic_id']}"] = c
    out = []
    for f in sorted(RECORDS.glob("*.json")):
        r = json.loads(f.read_text("utf-8"))
        c = meta[r["target_key"]]
        r["props"] = {
            "depth_ppm": float(c["depth_ppm"]) if c.get("depth_ppm") not in (None, "") else None,
            "tmag": float(c["tmag"]) if c.get("tmag") not in (None, "") else None,
            "predicted_transits": int(c["predicted_transits"]),
            "n_sectors": len(c["sectors"]),
        }
        r["disposition"] = c.get("tfopwg_disp_descriptive") or "(blank)"
        out.append(r)
    return out


def covered(r: dict) -> bool:
    if r.get("status") != "OK":
        return False
    return any((r["tests"].get(n, {}).get("coverage") or 0) > 0 for n in r["decisive"])


def first_fatal(r: dict) -> str | None:
    for name, t in r["tests"].items():
        if name in r["decisive"] and t["status"] == "FAIL" and t["severity"] == "fatal":
            return name
    return None


def cause(message: str) -> str:
    return re.sub(r"[-+]?\d+(\.\d+)?([eE][-+]?\d+)?", "#", message).strip()


def rates(rs: list[dict]) -> dict:
    n = len(rs)
    c = Counter(r["outcome"] for r in rs)
    return {
        "n": n,
        "counts": {o: c.get(o, 0) for o in OUTCOMES},
        "rates": {o: (c.get(o, 0) / n if n else None) for o in OUTCOMES},
    }


def _cuts(values: list[float], k: int) -> list[float]:
    return statistics.quantiles(values, n=k, method="inclusive")


def door1(planet: list[dict]) -> list[dict]:
    rows = []
    for prop, title in PROPERTIES.items():
        have = [r for r in planet if r["props"][prop] is not None]
        if len(have) < 2:
            continue
        values = [r["props"][prop] for r in have]
        for k in (2, 3):
            edges = _cuts(values, k)
            for i in range(k):
                lo = -float("inf") if i == 0 else edges[i - 1]
                hi = float("inf") if i == k - 1 else edges[i]
                sub = [r for r in have if lo < r["props"][prop] <= hi]
                rest = [r for r in planet if r not in sub]
                s, o = rates(sub), rates(rest)
                ok = len(sub) >= MIN_SUBGROUP and len(rest) > 0
                if ok:
                    sv, rv = s["counts"]["SURVIVED"], o["counts"]["SURVIVED"]
                    if rv == 0:
                        ok = sv >= 5
                    else:
                        ok = s["rates"]["SURVIVED"] >= 2 * o["rates"]["SURVIVED"]
                    si, ri = s["rates"]["INCONCLUSIVE"], o["rates"]["INCONCLUSIVE"]
                    ok = ok and si is not None and ri is not None and si <= ri / 2
                rows.append(
                    {
                        "property": title,
                        "cut": f"{'median' if k == 2 else 'tertile'} group {i + 1} of {k}",
                        "range": [lo, hi],
                        "subgroup": s,
                        "rest": o,
                        "qualifies": ok,
                    }
                )
    return rows


def _top(counter: Counter) -> tuple[str | None, int, bool]:
    if not counter:
        return None, 0, False
    (a, na), *others = counter.most_common()
    tie = bool(others) and others[0][1] == na
    return a, na, tie


def door2(planet: list[dict]) -> dict:
    refuted = [r for r in planet if r["outcome"] == "REFUTED"]
    c = Counter(first_fatal(r) or "(none recorded)" for r in refuted)
    name, n, tie = _top(c)
    return {
        "refuted": len(refuted),
        "first_fatal_fail": dict(c.most_common()),
        "largest": name,
        "largest_count": n,
        "tie": tie,
        "found": n >= MIN_REFUTED_CAUSE and not tie,
    }


def door3(planet: list[dict]) -> dict:
    per_test: dict[str, Counter] = {}
    for r in planet:
        for name, t in r["tests"].items():
            if t["status"] == "INCONCLUSIVE":
                per_test.setdefault(name, Counter())[cause(t["message"])] += 1
    rows = []
    for name, c in sorted(per_test.items()):
        total = sum(c.values())
        top, n, tie = _top(c)
        rows.append(
            {
                "test": name,
                "inconclusive": total,
                "largest_cause": top,
                "largest_count": n,
                "tie": tie,
                "qualifies": total >= MIN_INCONCLUSIVE and n > total / 2 and not tie,
                "causes": dict(c.most_common()),
            }
        )
    return {"tests": rows, "found": any(r["qualifies"] for r in rows)}


def identity(rs: list[dict]) -> dict:
    ok = [r for r in rs if r.get("status") == "OK"]
    matched = [r for r in ok if r["identity"]["matched"]]
    factors = Counter(str(r["identity"]["factor"]) for r in ok)
    return {
        "ok_records": len(ok),
        "matched": len(matched),
        "factor": dict(factors),
        "outcomes_when_matched": rates(matched)["counts"],
    }


def per_arm(rs: list[dict]) -> dict:
    status = Counter(r.get("status") for r in rs)
    cov = [r for r in rs if covered(r)]
    return {
        "records": len(rs),
        "status": dict(status),
        "coverage_losses": len(rs) - len(cov),
        "with_nonzero_coverage": rates(cov),
        "outcome_reasons": dict(
            Counter(cause(r.get("outcome_reason", "")) for r in cov).most_common(12)
        ),
        "identity": identity(rs),
    }


def main() -> None:
    rs = load()
    by_arm = {a: [r for r in rs if r["arm"] == a] for a in ("planet", "open")}
    planet = [r for r in by_arm["planet"] if covered(r)]
    d1, d2, d3 = door1(planet), door2(planet), door3(planet)
    found = [
        name
        for name, ok in (
            ("1 (a subgroup)", any(r["qualifies"] for r in d1)),
            ("2 (a systematic disagreement)", d2["found"]),
            ("3 (a dominant cause)", d3["found"]),
        )
        if ok
    ]
    open_cov = [r for r in by_arm["open"] if covered(r)]
    disp = {}
    for d in sorted({r["disposition"] for r in by_arm["open"]}):
        group = [r for r in open_cov if r["disposition"] == d]
        disp[d] = {
            "records": sum(1 for r in by_arm["open"] if r["disposition"] == d),
            "with_nonzero_coverage": rates(group)["counts"],
        }
    ledger = json.loads(LEDGER.read_text("utf-8")) if LEDGER.exists() else {}
    cpu = sum(r.get("cpu_seconds", 0.0) for r in rs) / 3600.0
    doc = {
        "label": "v0.5.6 part A: exploratory report",
        "mode": "exploratory",
        "limits_label": LABEL,
        "method_status": "not_validated",
        "draw_sha256": _sha(DRAW.read_bytes()),
        "report_code_sha256": _sha(Path(__file__).read_bytes()),
        "records": len(rs),
        "cpu_hours": round(cpu, 4),
        "bytes": sum(r.get("bytes", 0) for r in rs),
        "ledger_batches": len(ledger.get("batches", [])),
        "arms": {a: per_arm(v) for a, v in by_arm.items()},
        "doors": {
            "1_subgroup": {"found": any(r["qualifies"] for r in d1), "rows": d1},
            "2_systematic_disagreement": d2,
            "3_dominant_cause": d3,
            "found": found,
            "proceeds_to_part_b": found[0] if found else None,
        },
        "open_arm_by_disposition_descriptive": disp,
        "acknowledgment": ACKNOWLEDGMENT,
    }
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE
    (out / "part-a-report.json").write_text(
        json.dumps(doc, indent=1, default=str) + "\n", "utf-8", newline="\n"
    )
    (out / "part-a-report.md").write_text(markdown(doc), "utf-8", newline="\n")
    print(json.dumps({"records": len(rs), "doors_found": found}, indent=1))


def _pct(x: float | None) -> str:
    return "n/a" if x is None else f"{100 * x:.0f} %"


def markdown(doc: dict) -> str:
    out = [
        "# v0.5.6 part A: exploratory report",
        "",
        f"**Exploratory.** Limits label: '{doc['limits_label']}'. `method_status: "
        "not_validated`. The numbers describe the drawn sample (120 + 120 TOIs of the exploration "
        "half), never the TOI population. Nothing here is a verdict on any TOI or a candidate in a "
        "public claim; the battery's outcomes are its own, and agreement with any catalogue is "
        "not independence.",
        "",
        f"Records: {doc['records']}; CPU: {doc['cpu_hours']:.2f} CPU-h; data: "
        f"{doc['bytes'] / 1e9:.2f} GB. Generated by `part_a_report.py` (SHA-256 "
        f"`{doc['report_code_sha256'][:16]}...`) from the draw `{doc['draw_sha256'][:16]}...`.",
        "",
        "## Outcomes per arm",
        "",
        "| Arm | Records | Status | Coverage losses | Nonzero coverage | SURVIVED | WEAKENED | "
        "REFUTED | INCONCLUSIVE | Signal matched the TOI |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for arm, a in doc["arms"].items():
        w = a["with_nonzero_coverage"]
        cells = " | ".join(f"{w['counts'][o]} ({_pct(w['rates'][o])})" for o in OUTCOMES)
        status = ", ".join(f"{k} {v}" for k, v in sorted(a["status"].items()))
        out.append(
            f"| {arm} | {a['records']} | {status} | {a['coverage_losses']} | {w['n']} | {cells} "
            f"| {a['identity']['matched']} of {a['identity']['ok_records']} |"
        )
    out += ["", "Most frequent outcome reasons (numbers replaced by `#`):", ""]
    for arm, a in doc["arms"].items():
        out.append(
            f"- **{arm}:** " + "; ".join(f"{k} ({v})" for k, v in a["outcome_reasons"].items())
        )
    d = doc["doors"]
    out += [
        "",
        "## Doors (planet arm, records with nonzero coverage)",
        "",
        f"- **Door 1, a subgroup:** {'FOUND' if d['1_subgroup']['found'] else 'not found'}.",
    ]
    for r in d["1_subgroup"]["rows"]:
        s, o = r["subgroup"], r["rest"]
        out.append(
            f"  - {r['property']}, {r['cut']}: n {s['n']}, SURVIVED {_pct(s['rates']['SURVIVED'])} "
            f"vs rest {_pct(o['rates']['SURVIVED'])}, INCONCLUSIVE "
            f"{_pct(s['rates']['INCONCLUSIVE'])} vs rest {_pct(o['rates']['INCONCLUSIVE'])}"
            f"{' (qualifies)' if r['qualifies'] else ''}"
        )
    d2 = d["2_systematic_disagreement"]
    out += [
        f"- **Door 2, a systematic disagreement:** {'FOUND' if d2['found'] else 'not found'}. "
        f"REFUTED: {d2['refuted']}; first decisive fatal FAIL: "
        + ("; ".join(f"{k} {v}" for k, v in d2["first_fatal_fail"].items()) or "none")
        + ("; a tie for the largest count" if d2["tie"] else ""),
    ]
    d3 = d["3_dominant_cause"]
    out.append(f"- **Door 3, a dominant cause:** {'FOUND' if d3['found'] else 'not found'}.")
    for r in d3["tests"]:
        out.append(
            f"  - {r['test']}: {r['inconclusive']} INCONCLUSIVE; largest cause "
            f'{r["largest_count"]}: "{r["largest_cause"]}"'
            f"{' (tie)' if r['tie'] else ''}{' (qualifies)' if r['qualifies'] else ''}"
        )
    out += [
        "",
        f"**Doors found:** {', '.join(d['found']) or 'none'}. "
        + (
            f"Door {d['proceeds_to_part_b']} is the first in the plan's order; part B (its "
            "claim, lock and drand round) is the maintainer's stop."
            if d["proceeds_to_part_b"]
            else "With no door, the phase closes with declared limits (exit criterion 3b)."
        ),
        "",
        "## The open arm, described by the TOI table's disposition (descriptive only)",
        "",
        "Never a label, a score or a verdict; the disposition is the TFOPWG's, read from the "
        "NASA Exoplanet Archive's TOI table, used as NExScI's answer of 2026-11-22 allows.",
        "",
        "| Disposition | Records | SURVIVED | WEAKENED | REFUTED | INCONCLUSIVE |",
        "|---|---|---|---|---|---|",
    ]
    for k, v in doc["open_arm_by_disposition_descriptive"].items():
        c = v["with_nonzero_coverage"]
        out.append(f"| {k} | {v['records']} | " + " | ".join(str(c[o]) for o in OUTCOMES) + " |")
    out += [
        "",
        "## Limits",
        "",
        "- The battery is v0.5's, closed with declared limits: it does not meet D1, D2, D4 and "
        "T2a. Every outcome above carries that label.",
        "- The battery searches for its own signal; where it did not match the TOI, its outcome "
        "is about another signal.",
        "- The prior-exposure flag of the frame is a superset (catalogue snapshots in the "
        "repository name nearly every TOI); part B fixes which evidence counts.",
        "- Signals, periods and dispositions come from the NASA Exoplanet Archive and MAST, read "
        "on 2026-11-21 and 2026-11-22 (sources records in `docs/plans/sources/`).",
        "",
        "## Acknowledgment",
        "",
        doc["acknowledgment"],
        "",
    ]
    return "\n".join(out)


if __name__ == "__main__":
    main()
