"""Build the per-TOI, per-engine table of part (f) and answer G1 to G5 (exploratory, post hoc).

Reads only committed records: results/<engine>/<TIC>.json, settings.json (the thresholds fixed
before the runs), tfopwg.json, and v0.5.9's prototype-report.json (the E and S classes) and
prototype-units.json (each test's status). Applies the rules logged before the results were read
(log.jsonl, the 'crosswalk' note). Writes table.json and table.md. Nothing here is a verdict,
a candidate or a claim; v0.5.9's records are never re-scored.
"""

from __future__ import annotations

import json
import statistics
from pathlib import Path

HERE = Path(__file__).resolve().parent
V059 = HERE.parents[1] / "v0.5.9"
LABEL = "WEAKENED; does not meet D1, D2, D4, T2a"
ENGINES = ("tls", "exovetter", "leo", "triceratops")
FACTORS = (1 / 3, 1 / 2, 1.0, 2.0, 3.0)
TOL = 0.001


EMPTY = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"


def provenance_gaps() -> set[str]:
    """Runs whose 'before' entry logged the empty file's SHA-256 for the worker (Codex's round on
    the report, blocking item 1): the copy was hashed while another thread rewrote it, so what the
    process executed is not established by the log. Their outputs are 'unavailable' here."""
    out = set()
    for line in (HERE.parent / "log.jsonl").read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        if r.get("kind") == "before" and r.get("worker_sha256") == EMPTY:
            out.add(r["run"])
    return out


GAPS = provenance_gaps()


def load(engine: str, key: str) -> dict | None:
    p = HERE / "results" / engine / f"{key}.json"
    rec = json.loads(p.read_text(encoding="utf-8")) if p.exists() else None
    if rec is not None and f"{engine}:{key}" in GAPS:
        rec = {**rec, "status": "unavailable_provenance", "result": None}
    return rec


def tls_outcomes(rec: dict | None, period: float) -> dict:
    out = {"detection": "unavailable", "recovery": "unavailable"}
    if not rec or rec["status"] != "ok":
        return out
    m = rec["result"]["metrics"]
    if m.get("sde") is not None:
        out["detection"] = "threshold_met" if m["sde"] >= 9 else "threshold_not_met"
    if m.get("period_days"):
        hits = [f for f in FACTORS if abs(m["period_days"] / (period * f) - 1) <= TOL]
        out["recovery"] = "threshold_met" if hits else "threshold_not_met"
        out["recovery_factor"] = hits[0] if hits else None
    return out


def exo_outcomes(rec: dict | None) -> dict:
    names = ("ModShift", "OddEven", "TransitPhaseCoverage", "Sweet", "Lpp", "Centroid")
    out = {n: "unavailable" for n in names}
    if not rec or rec["status"] != "ok":
        return out
    v = rec["result"]["vetters"]
    for n in ("ModShift", "OddEven", "TransitPhaseCoverage"):
        out[n] = "no_published_threshold" if v.get(n, {}).get("status") == "ok" else "unavailable"
    sw = v.get("Sweet", {})
    if sw.get("status") == "ok":
        ratios = [
            sw["native"][k][2]
            for k in ("amp_half_period", "amp_period", "amp_twice_period")
            if sw["native"][k][2] is not None
        ]
        if ratios:
            out["Sweet"] = "threshold_met" if max(ratios) > 3 else "threshold_not_met"
    cents = [
        c["significance"]
        for c in v.get("Centroid", {}).get("sectors", [])
        if c.get("status") == "ok" and c.get("significance") is not None
    ]
    if cents:
        out["Centroid"] = "threshold_met" if min(cents) < 1e-3 else "threshold_not_met"
    return out


def leo_outcomes(rec: dict | None) -> dict:
    if not rec or rec["status"] != "ok":
        return {"class": "unavailable", "flags": {}}
    r = rec["result"]
    flags = {
        k: ("threshold_met" if v is True else "threshold_not_met" if v is False else "unavailable")
        for k, v in r.get("flags", {}).items()
    }
    return {"class": r.get("leo_class"), "flags": flags}


def tri_outcomes(rec: dict | None) -> dict:
    out = {"FPP<0.015 and NFPP<0.001": "unavailable", "NFPP>0.1": "unavailable"}
    if not rec or rec["status"] != "ok":
        return out
    m = rec["result"]["metrics"]
    fpp, nfpp = m.get("FPP"), m.get("NFPP")
    # Codex's blocking item 8: a degenerate FPP is unavailable coverage (here: outside [0, 1])
    if any(x is not None and not 0.0 <= x <= 1.0 for x in (fpp, nfpp)):
        return {k: "unavailable" for k in out}
    if fpp is not None and nfpp is not None:
        both = fpp < 0.015 and nfpp < 0.001
        out["FPP<0.015 and NFPP<0.001"] = "threshold_met" if both else "threshold_not_met"
    if nfpp is not None:
        out["NFPP>0.1"] = "threshold_met" if nfpp > 0.1 else "threshold_not_met"
    return out


def reached(x: str) -> bool:
    return x in ("threshold_met", "threshold_not_met")


def main() -> int:
    s = json.loads((V059 / "prototype-set.json").read_text(encoding="utf-8"))
    rep = json.loads((V059 / "prototype-report.json").read_text(encoding="utf-8"))
    base = rep["describe"]["all_24"]["base"]["per_toi"]
    cons = rep["describe"]["all_24"]["consensus"]["per_toi"]
    units = json.loads((V059 / "prototype-units.json").read_text(encoding="utf-8"))["units"]
    tests = {}
    for u in units:
        c = u["content"]
        if c["kind"] == "base" and c.get("tests"):
            tests[(c["target_key"], c["entry_mode"])] = {
                k: v["status"] for k, v in c["tests"].items()
            }
    tf = json.loads((HERE / "tfopwg.json").read_text(encoding="utf-8"))["targets"]
    import run_engines

    cat = run_engines.catalog()
    rows = []
    for key in s["order"]:
        recs = {e: load(e, key) for e in ENGINES}
        row = {
            "target": key,
            "toi": s["tois"][key],
            "tfopwg_disp": tf[key]["tfopwg_disp"],
            "v059": {
                "E": base[key]["E"],
                "S": base[key]["S"],
                "E_consensus": cons[key]["E"],
                "S_consensus": cons[key]["S"],
                "E_inconclusive_tests": sorted(
                    k for k, v in tests.get((key, "E"), {}).items() if v == "INCONCLUSIVE"
                ),
            },
            "tls": tls_outcomes(recs["tls"], cat[key]["period_days"]),
            "exovetter": exo_outcomes(recs["exovetter"]),
            "leo": leo_outcomes(recs["leo"]),
            "triceratops": tri_outcomes(recs["triceratops"]),
            "status": {e: (recs[e] or {}).get("status", "not_run") for e in ENGINES},
            "cpu_seconds": {e: (recs[e] or {}).get("cpu_seconds") for e in ENGINES},
            "native": {
                "tls": ((recs["tls"] or {}).get("result") or {}).get("metrics")
                if recs["tls"]
                else None,
                "triceratops": ((recs["triceratops"] or {}).get("result") or {}).get("metrics")
                if recs["triceratops"]
                else None,
            },
        }
        rows.append(row)

    def engine_outputs(r: dict) -> dict[str, str]:
        out = {f"tls:{k}": v for k, v in r["tls"].items() if k != "recovery_factor"}
        out.update({f"exovetter:{k}": v for k, v in r["exovetter"].items()})
        out.update({f"leo:{k}": v for k, v in r["leo"]["flags"].items()})
        out["leo:class"] = (
            "threshold_met" if r["leo"]["class"] in ("FA", "FP", "PC") else "unavailable"
        )
        out.update({f"triceratops:{k}": v for k, v in r["triceratops"].items()})
        return out

    g1 = {}
    for which in ("E", "E_consensus", "S", "S_consensus"):
        inc = [r for r in rows if r["v059"][which] == "INCONCLUSIVE"]
        per = {}
        for r in inc:
            for k, v in engine_outputs(r).items():
                d = per.setdefault(k, {"n": 0, "reached": 0})
                d["n"] += 1
                d["reached"] += reached(v)
        g1[which] = {"inconclusive_tois": len(inc), "outputs": per}
    crosswalk = {}
    for line in (HERE.parent / "log.jsonl").read_text(encoding="utf-8").splitlines():
        e = json.loads(line)
        if e.get("run") == "crosswalk":
            crosswalk = e["crosswalk"]
    output_of = {
        "tls: SDE >= 9": lambda r: r["tls"]["detection"],
        "tls: recovery factor": lambda r: r["tls"]["recovery"],
        "exovetter: OddEven (no published threshold)": lambda r: r["exovetter"]["OddEven"],
        "exovetter: ModShift (no published threshold)": lambda r: r["exovetter"]["ModShift"],
        "exovetter: Centroid significance < 1e-3": lambda r: r["exovetter"]["Centroid"],
        "exovetter: Sweet": lambda r: r["exovetter"]["Sweet"],
        "triceratops: NFPP > 0.1": lambda r: r["triceratops"]["NFPP>0.1"],
        "leo: FA weak": lambda r: r["leo"]["flags"].get("FA:weak", "unavailable"),
        "leo: FP odd_even": lambda r: r["leo"]["flags"].get("FP:odd_even", "unavailable"),
        "leo: FP secondary": lambda r: r["leo"]["flags"].get("FP:secondary", "unavailable"),
        "leo: FA sinusoidal": lambda r: r["leo"]["flags"].get("FA:sinusoidal", "unavailable"),
        "leo: FA unphysical_duration": lambda r: r["leo"]["flags"].get(
            "FA:unphysical_duration", "unavailable"
        ),
        "leo: FP large, vshaped": lambda r: r["leo"]["flags"].get("FP:large", "unavailable"),
        "leo: FA chases, dmm, bad_fit, chi": lambda r: r["leo"]["flags"].get(
            "FA:chases", "unavailable"
        ),
    }
    g1_tests = {}
    for test, outs in crosswalk.items():
        rows_inc = [r for r in rows if test in r["v059"]["E_inconclusive_tests"]]
        per = {}
        for o in outs:
            fn = output_of.get(o)
            if fn is None:
                continue
            per[o] = {"n": len(rows_inc), "reached": sum(reached(fn(r)) for r in rows_inc)}
        g1_tests[test] = {"tois_with_test_inconclusive_in_E": len(rows_inc), "outputs": per}
    g1["per_test_E"] = g1_tests
    g2 = {}
    pairs = {
        "centroid: exovetter Centroid vs TRICERATOPS NFPP>0.1": (
            lambda r: r["exovetter"]["Centroid"],
            lambda r: r["triceratops"]["NFPP>0.1"],
        ),
        "variability: exovetter Sweet vs LEO FA:sinusoidal": (
            lambda r: r["exovetter"]["Sweet"],
            lambda r: r["leo"]["flags"].get("FA:sinusoidal", "unavailable"),
        ),
        "detection: TLS SDE>=9 vs LEO FA:weak (inverted; not in the logged note)": (
            lambda r: r["tls"]["detection"],
            lambda r: {
                "threshold_met": "threshold_not_met",
                "threshold_not_met": "threshold_met",
            }.get(r["leo"]["flags"].get("FA:weak", "unavailable"), "unavailable"),
        ),
    }
    for name, (a, b) in pairs.items():
        both = [(a(r), b(r)) for r in rows if reached(a(r)) and reached(b(r))]
        g2[name] = {"both_reached": len(both), "agree": sum(x == y for x, y in both)}
    g3 = {}
    for r in rows:
        d = g3.setdefault(
            r["tfopwg_disp"] or "none", {"n": 0, "leo_class": {}, "triceratops_both": {}}
        )
        d["n"] += 1
        lc = r["leo"]["class"]
        d["leo_class"][lc] = d["leo_class"].get(lc, 0) + 1
        tb = r["triceratops"]["FPP<0.015 and NFPP<0.001"]
        d["triceratops_both"][tb] = d["triceratops_both"].get(tb, 0) + 1
    g4 = {}
    for e in ENGINES:
        cpus = [r["cpu_seconds"][e] for r in rows if r["cpu_seconds"][e] is not None]
        g4[e] = {
            "runs": len(cpus),
            "cpu_seconds_total": round(sum(cpus), 1),
            "median": round(statistics.median(cpus), 1) if cpus else None,
            "max": round(max(cpus), 1) if cpus else None,
        }
    g5 = {}
    for r in rows:
        for k, v in engine_outputs(r).items():
            d = g5.setdefault(k, {})
            d[v] = d.get(v, 0) + 1
    doc = {
        "schema": "refute-v0510-engine-table-1",
        "mode": "exploratory",
        "method_status": "not_validated",
        "limits_label": LABEL,
        "post_hoc": "comparisons are exploratory and post hoc; v0.5.9's classes are shown beside, "
        "never replaced or re-scored; no replacement class and no vote",
        "provenance_gaps": sorted(GAPS),
        "aggregation_post_hoc": "Centroid: the minimum significance over the sectors; "
        "TRICERATOPS: FPP or NFPP outside [0, 1] is unavailable; both chosen after the runs",
        "rows": rows,
        "G1": g1,
        "G2": g2,
        "G3": g3,
        "G4": g4,
        "G5": g5,
    }
    (HERE / "table.json").write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8")
    lines = [
        "# v0.5.10 part (f): engines beside v0.5.9 (exploratory, post hoc)",
        "",
        f"Limits label: '{LABEL}'. `method_status: not_validated`. Outcomes: `met`/`not met` "
        "against each tool's published threshold (settings.json), `n/p` no published threshold, "
        "`—` unavailable. Never a verdict, a candidate or a claim.",
        "",
        "| TOI | TFOPWG | E | S | E cons. | TLS SDE>=9 | TLS recov. | exoV Sweet | exoV Centroid "
        "| LEO class | TRIC. FPP&NFPP | TRIC. NFPP>0.1 |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]

    def short(x: str) -> str:
        return {
            "threshold_met": "met",
            "threshold_not_met": "not met",
            "no_published_threshold": "n/p",
            "unavailable": "—",
        }.get(x, str(x))

    for r in rows:
        lines.append(
            f"| {r['toi']} | {r['tfopwg_disp']} | {r['v059']['E']} | {r['v059']['S']} "
            f"| {r['v059']['E_consensus']} | {short(r['tls']['detection'])} "
            f"| {short(r['tls']['recovery'])} | {short(r['exovetter']['Sweet'])} "
            f"| {short(r['exovetter']['Centroid'])} | {r['leo']['class'] or '—'} "
            f"| {short(r['triceratops']['FPP<0.015 and NFPP<0.001'])} "
            f"| {short(r['triceratops']['NFPP>0.1'])} |"
        )
    (HERE / "table.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"G2": g2, "G4": g4}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
