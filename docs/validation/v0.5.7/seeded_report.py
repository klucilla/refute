"""v0.5.7 (exploratory): the report of the TOI-seeded run against search mode, with the four doors
counted by the plan's rules (docs/plans/v0.5.7-plan.md, "The four doors"). It is committed before
any TOI-seeded result exists (exit criterion 1).

**Inputs:**
- the TOI-seeded records, from ``.cache/v057/run/records`` or, once bundled, from
  ``seeded-records.json``;
- the v0.5.6 search-mode records, from the bundles in git;
- the cohort from the frozen draws.

**Outputs:** ``seeded-report.json`` and ``seeded-report.md``.

**Exploratory:** never a verdict, a candidate or a disposition. The numbers describe these 540
TOIs, never the TOI population.

**The cohort** (Codex's design round, blocking item 4):
- Keys, parts and arms come from the draws: exactly 540 unique TICs.
- Before a door is marked, the TOI-seeded records must be exactly that cohort: no duplicate, no
  extra, the same part and arm. Every OK record must have a valid outcome and a status for every
  decisive test.
- Until then, every door's ``found`` is None (incomplete), and no qualifying name is shown.

**The groups:**
- planets: part A's planet arm (120) and part B's planet stratum (150), 270 in all;
- part B's FPs (150);
- part A's open arm (120). It enters door 3 only, through its TOIs outside the period domain.

**Every door is counted twice** (the design decision, item 2), both versions fixed before running:
- **total:** all 540;
- **stayed:** only the records that stayed on the TOI ephemeris (v0.5.6's matching rule, on the
  battery's final fit).

The thresholds are the same in both versions.

**A record that is not OK** (ERROR, MISSING_PRODUCTS, INPUTS_DIFFER):
- counts as INCONCLUSIVE in doors 3 and 4;
- is never an event in doors 1 and 2. Doors 1 and 2 also show these *unknown* planet rows and an
  upper bound: the observed count plus the unknown planets. A door that passes only because
  unknown rows were treated as zero is flagged.

Usage (from the project root): ``seeded_report.py [records-folder-or-bundle]``.
"""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
V056 = ROOT / "docs/validation/v0.5.6"
SEARCH_BUNDLES = {"A": V056 / "part-a-records.json", "B": V056 / "part-b-records.json"}
DRAWS = {"A": V056 / "part-a-draw.json", "B": ROOT / "calibration/v0.5.6/part-b-draw.json"}
ARMS = {"A": ("planet", "open"), "B": ("planet", "fp")}
DEFAULT_RECORDS = ROOT / ".cache/v057/run/records"
BUNDLE = HERE / "seeded-records.json"
OUT_JSON = HERE / "seeded-report.json"
OUT_MD = HERE / "seeded-report.md"
LABEL = "WEAKENED; does not meet D1, D2, D4, T2a"
OUTCOMES = ("SURVIVED", "WEAKENED", "REFUTED", "INCONCLUSIVE")
DOMAIN = (0.5, 20.0)


def _bundle_records(path: Path) -> list[dict]:
    return [item["content"] for item in json.loads(path.read_text("utf-8"))["records"]]


def load_records(source: Path) -> list[dict]:
    if source.is_dir():
        return [json.loads(p.read_text("utf-8")) for p in sorted(source.glob("TIC-*.json"))]
    return _bundle_records(source)


def cohort() -> dict[str, dict]:
    """The 540 TICs from the frozen draws: part, arm and TOI period."""
    out = {}
    for part, path in DRAWS.items():
        arms = json.loads(path.read_text("utf-8"))["arms"]
        for arm in ARMS[part]:
            for c in arms[arm]["chosen"]:
                key = f"TIC-{c['tic_id']}"
                if key in out:
                    raise SystemExit(f"{key} is drawn twice")
                out[key] = {"part": part, "arm": arm, "period_days": float(c["period_days"])}
    if len(out) != 540:
        raise SystemExit(f"the cohort has {len(out)} TICs, not 540")
    return out


def load_search() -> dict[str, dict]:
    out = {}
    for part, path in SEARCH_BUNDLES.items():
        for r in _bundle_records(path):
            out[r["target_key"]] = {**r, "part": part}
    return out


def group_of(c: dict) -> str:
    if c["arm"] == "planet":
        return "planet"
    return "fp_B" if c["part"] == "B" else "open_A"


def is_ok(r: dict | None) -> bool:
    return r is not None and r.get("status") == "OK"


def outcome(r: dict | None) -> str:
    if r is None:
        return "NO RECORD"
    return r.get("outcome") if is_ok(r) else r.get("status", "UNKNOWN")


def as_inconclusive(r: dict | None) -> bool:
    return not is_ok(r) or r.get("outcome") == "INCONCLUSIVE"


def stayed(r: dict | None) -> bool:
    return is_ok(r) and bool((r.get("ephemeris") or {}).get("stayed_on_toi_ephemeris"))


def fatal_fail(r: dict | None, name: str) -> bool:
    """A fatal FAIL of ``name`` in an OK record (the severity is read on that record)."""
    if not is_ok(r):
        return False
    t = (r.get("tests") or {}).get(name) or {}
    return t.get("status") == "FAIL" and t.get("severity") == "fatal"


def status_of(r: dict | None, name: str) -> str | None:
    if not is_ok(r):
        return None
    return ((r.get("tests") or {}).get(name) or {}).get("status")


def validate(records: list[dict], coh: dict[str, dict]) -> list[str]:
    """The problems that keep the doors from being marked."""
    problems = []
    keys = [r.get("target_key") for r in records]
    dup = sorted(k for k, n in Counter(keys).items() if n > 1)
    if dup:
        problems.append(f"duplicate records: {dup[:5]}")
    extra = sorted(set(keys) - set(coh))
    if extra:
        problems.append(f"records outside the cohort: {extra[:5]}")
    missing = sorted(set(coh) - set(keys))
    if missing:
        problems.append(f"{len(missing)} cohort TICs have no record")
    for r in records:
        c = coh.get(r.get("target_key"))
        if c is None:
            continue
        if r.get("part") != c["part"] or r.get("arm") != c["arm"]:
            problems.append(f"{r['target_key']}: part or arm differs from the draw")
        if is_ok(r):
            if r.get("outcome") not in OUTCOMES:
                problems.append(f"{r['target_key']}: an OK record with an invalid outcome")
            for name in r.get("decisive") or []:
                if name not in (r.get("tests") or {}):
                    problems.append(f"{r['target_key']}: no status for decisive test {name}")
    return problems


def doors_for(rec: dict[str, dict], keys: dict[str, list[str]], periods: dict[str, float]) -> dict:
    """The four doors over the given keys (all, or only those that stayed)."""
    planets, fps = keys["planet"], keys["fp_B"]
    unknown_pl = sum(1 for k in planets if not is_ok(rec.get(k)))
    d1 = sum(
        1
        for k in planets
        if outcome(rec.get(k)) == "REFUTED" and status_of(rec.get(k), "snr") == "PASS"
    )
    names = sorted({n for k in planets + fps if is_ok(rec.get(k))
                    for n, t in (rec[k].get("tests") or {}).items()
                    if t.get("severity") == "fatal"})  # fmt: skip
    per_test = {}
    for name in names:
        fp_fail = sum(fatal_fail(rec.get(k), name) for k in fps)
        pl_fail = sum(fatal_fail(rec.get(k), name) for k in planets)
        per_test[name] = {
            "fp_B_fatal_fail": fp_fail,
            "planet_fatal_fail": pl_fail,
            "planet_fatal_fail_upper_bound": pl_fail + unknown_pl,
            "qualifies": fp_fail >= 10 and pl_fail <= 1,
            "qualifies_only_if_unknown_planets_are_zero": fp_fail >= 10
            and pl_fail <= 1 < pl_fail + unknown_pl,
        }
    out_dom = [k for k in keys["all"] if not DOMAIN[0] <= periods[k] <= DOMAIN[1]]
    d3 = sum(1 for k in out_dom if not as_inconclusive(rec.get(k)))
    d4 = sum(1 for k in planets if as_inconclusive(rec.get(k)))
    n_pl, n_out = len(planets), len(out_dom)
    return {
        "door_1": {
            "planets": n_pl,
            "refuted_snr_pass": d1,
            "unknown_planets": unknown_pl,
            "upper_bound": d1 + unknown_pl,
            "found": d1 <= 4,
            "passes_only_if_unknown_are_zero": d1 <= 4 < d1 + unknown_pl,
        },
        "door_2": {
            "fps": len(fps),
            "planets": n_pl,
            "unknown_planets": unknown_pl,
            "per_test": per_test,
            "qualifying": sorted(n for n, v in per_test.items() if v["qualifies"]),
            "found": any(v["qualifies"] for v in per_test.values()),
        },
        "door_3": {
            "tois": n_out,
            "decided": d3,
            "fraction": d3 / n_out if n_out else None,
            "found": bool(n_out) and d3 / n_out >= 0.20,
        },
        "door_4": {
            "planets": n_pl,
            "inconclusive": d4,
            "fraction": d4 / n_pl if n_pl else None,
            "found": bool(n_pl) and d4 / n_pl <= 0.50,
        },
    }


DOOR_TEXT = {
    "door_1": "In fixed mode, among confirmed planets with the SNR gate passed, REFUTED falls from "
    "22 (9 in A, 13 in B) to at most 4 of 270.",
    "door_2": "Some fatal test fails in at least 10 FPs and in at most 1 planet (the FPs come only "
    "from part B).",
    "door_3": "Among the 60 TOIs with a period outside 0.5 to 20 d, at least 20 % end with an "
    "outcome other than INCONCLUSIVE.",
    "door_4": "INCONCLUSIVE in planets falls to 50 % or less (expected not to be found).",
}


def build_from(records: list[dict], source_label: str) -> dict:
    """The report from TOI-seeded records already read (the tests call it directly)."""
    coh = cohort()
    search = load_search()
    problems = validate(records, coh)
    complete = not problems
    seeded = {r["target_key"]: r for r in records if r.get("target_key") in coh}
    periods = {k: c["period_days"] for k, c in coh.items()}
    keys_all: dict[str, list[str]] = {"planet": [], "fp_B": [], "open_A": [], "all": sorted(coh)}
    for k, c in sorted(coh.items()):
        keys_all[group_of(c)].append(k)
    keys_stayed = {g: [k for k in ks if stayed(seeded.get(k))] for g, ks in keys_all.items()}
    doors = {"total": doors_for(seeded, keys_all, periods),
             "stayed": doors_for(seeded, keys_stayed, periods),
             "search_mode_baseline": doors_for(search, keys_all, periods)}  # fmt: skip
    for version in ("total", "stayed"):
        for door in doors[version].values():
            door["complete"] = complete
            if not complete:
                door["found"] = None
                if "qualifying" in door:
                    door["qualifying"] = []
    groups = {}
    for g in ("planet", "fp_B", "open_A"):
        ks = keys_all[g]
        groups[g] = {
            "tois": len(ks),
            "seeded_records": sum(k in seeded for k in ks),
            "search_outcomes": dict(Counter(outcome(search.get(k)) for k in ks)),
            "seeded_outcomes": dict(Counter(outcome(seeded.get(k)) for k in ks)),
            "paired": dict(
                sorted(
                    Counter(
                        f"{outcome(search.get(k))} -> {outcome(seeded.get(k))}" for k in ks
                    ).items()
                )
            ),  # fmt: skip
            "search_matched": sum(
                bool((search.get(k, {}).get("identity") or {}).get("matched")) for k in ks
            ),  # fmt: skip
            "stayed_on_toi_ephemeris": sum(stayed(seeded.get(k)) for k in ks),
            "window_found": sum(
                bool((seeded.get(k, {}).get("window") or {}).get("found")) for k in ks
            ),  # fmt: skip
            "no_toi_event_covered": sum(
                is_ok(seeded.get(k))
                and not (seeded[k].get("ephemeris") or {}).get("any_toi_event_covered")
                for k in ks
            ),
            "provenance": dict(
                Counter(
                    ((seeded.get(k) or {}).get("provenance") or {}).get("overall", "none")
                    for k in ks
                )
            ),  # fmt: skip
        }
    transitions: dict[str, Counter] = {}
    for k in coh:
        s, f = search.get(k), seeded.get(k)
        if not (is_ok(s) and is_ok(f)):
            continue
        for name in set(s.get("tests", {})) | set(f.get("tests", {})):
            a, b = status_of(s, name), status_of(f, name)
            if a != b:
                transitions.setdefault(name, Counter())[f"{a} -> {b}"] += 1
    return {
        "schema": "refute-v057-seeded-report-1",
        "mode": "exploratory",
        "limits_label": LABEL,
        "method_status": "not_validated",
        "candidate_mode": "TOI-seeded: the TOI's ephemeris seeds the unchanged battery, which "
        "refits period, epoch, duration, depth and SNR before any test",
        "note": "Exploratory: never a verdict, a candidate or a disposition; the numbers describe "
        "these 540 TOIs, never the TOI population.",
        "source": {
            "seeded_records": source_label,
            "records": len(records),
            "search_bundles": {
                p: v.relative_to(ROOT).as_posix() for p, v in SEARCH_BUNDLES.items()
            },
        },  # fmt: skip
        "code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "cohort_problems": problems,
        "complete": complete,
        "groups": groups,
        "test_status_changes": {n: dict(c) for n, c in sorted(transitions.items())},
        "door_text": DOOR_TEXT,
        "doors": doors,
    }


def build(source: Path) -> dict:
    try:
        label = source.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        label = source.name
    return build_from(load_records(source), label)


def mark(door: dict) -> str:
    if door["found"] is None:
        return "incomplete"
    return "FOUND" if door["found"] else "not found"


def markdown(rep: dict) -> str:
    names = {"planet": "Planets (A + B)", "fp_B": "FPs (part B)", "open_A": "Open arm (part A)"}
    lines = [
        "# v0.5.7: the TOI's own signal, TOI-seeded against search mode (exploratory)",
        "",
        f"**Exploratory.** Limits label: '{rep['limits_label']}'. `method_status: not_validated`. "
        + rep["note"],
        "",
        f"**Mode.** {rep['candidate_mode']}.",
        "",
        f"Records: {rep['source']['records']}. Complete cohort: {rep['complete']}. Generated by "
        f"`seeded_report.py` (SHA-256 `{rep['code_sha256'][:16]}...`).",
    ]
    if rep["cohort_problems"]:
        lines += ["", "Cohort problems (the doors are not marked):", ""]
        lines += [f"- {p}" for p in rep["cohort_problems"]]
    lines += [
        "",
        "## Outcomes, search mode against TOI-seeded",
        "",
        "| Group | TOIs | Mode | " + " | ".join(OUTCOMES) + " | Other |",
        "|---|---|---|" + "---|" * (len(OUTCOMES) + 1),
    ]
    for g, v in rep["groups"].items():
        for mode, key in (("search", "search_outcomes"), ("seeded", "seeded_outcomes")):
            c = v[key]
            other = sum(n for o, n in c.items() if o not in OUTCOMES)
            cells = " | ".join(str(c.get(o, 0)) for o in OUTCOMES)
            lines.append(f"| {names[g]} | {v['tois']} | {mode} | {cells} | {other} |")
    lines += ["", "## The ephemeris (TOI-seeded)", ""]
    for g, v in rep["groups"].items():
        lines.append(
            f"- {names[g]}: matched in search mode {v['search_matched']}; stayed on the TOI "
            f"ephemeris {v['stayed_on_toi_ephemeris']}; window seed found {v['window_found']}; "
            f"no TOI event covered {v['no_toi_event_covered']}; provenance {v['provenance']}."
        )
    lines += ["", "## Paired outcomes (search -> seeded)", ""]
    for g, v in rep["groups"].items():
        lines.append(f"- {names[g]}: " + "; ".join(f"{p} {n}" for p, n in v["paired"].items()))
    lines += ["", "## Test status changes (search -> seeded, records OK in both)", ""]
    for name, c in rep["test_status_changes"].items():
        lines.append(f"- `{name}`: " + "; ".join(f"{p} {n}" for p, n in sorted(c.items())))
    lines += ["", "## The four doors (the plan's rules, fixed before any result)", ""]
    base = rep["doors"]["search_mode_baseline"]
    for version, title in (("total", "All 540"), ("stayed", "Only records that stayed on the TOI "
                                                            "ephemeris")):  # fmt: skip
        d = rep["doors"][version]
        lines += [f"### {title}", ""]
        lines.append(
            f"1. **Identity resolved:** {mark(d['door_1'])}. REFUTED with SNR PASS among "
            f"{d['door_1']['planets']} planets: {d['door_1']['refuted_snr_pass']} (search "
            f"{base['door_1']['refuted_snr_pass']}; at most 4 needed); unknown planet rows "
            f"{d['door_1']['unknown_planets']}, upper bound {d['door_1']['upper_bound']}"
            + (
                " (passes only if unknown rows are zero)"
                if d["door_1"]["passes_only_if_unknown_are_zero"]
                else ""
            )
            + "."  # fmt: skip
        )
        tests = "; ".join(f"`{n}` {v['fp_B_fatal_fail']}/{v['planet_fatal_fail']}"
                          for n, v in d["door_2"]["per_test"].items())  # fmt: skip
        lines.append(
            f"2. **A discriminating test:** {mark(d['door_2'])}"
            + (f" ({', '.join(d['door_2']['qualifying'])})" if d["door_2"]["qualifying"] else "")
            + f". Fatal FAIL per test, FPs of part B / planets: {tests}."
        )
        lines.append(
            f"3. **Outside the search's domain:** {mark(d['door_3'])}. Decided among "
            f"{d['door_3']['tois']} TOIs: {d['door_3']['decided']} (search "
            f"{base['door_3']['decided']} of {base['door_3']['tois']}; at least 20 % needed)."
        )
        lines.append(
            f"4. **Decidability:** {mark(d['door_4'])}. INCONCLUSIVE among "
            f"{d['door_4']['planets']} planets: {d['door_4']['inconclusive']} (search "
            f"{base['door_4']['inconclusive']} of {base['door_4']['planets']}; at most 50 % "
            "needed)."
        )
        lines.append("")
    lines += [
        "## Limits",
        "",
        "- The battery is v0.5's, with its limits label; nothing in it changed.",
        "- TOI-seeded: the TOI's ephemeris seeds the battery, which refits it before any test; "
        "each record says whether the fit stayed on the TOI ephemeris.",
        "- Agreement with any catalogue is not independence. No output is about a single TOI.",
        "",
    ]
    return "\n".join(lines)


def main(argv: list[str]) -> None:
    source = Path(argv[0]).resolve() if argv else (BUNDLE if BUNDLE.exists() else DEFAULT_RECORDS)
    rep = build(source)
    OUT_JSON.write_text(json.dumps(rep, indent=1) + "\n", "utf-8", newline="\n")
    OUT_MD.write_text(markdown(rep), "utf-8", newline="\n")
    print(json.dumps({v: {k: d["found"] for k, d in rep["doors"][v].items()}
                      for v in ("total", "stayed")}))  # fmt: skip


if __name__ == "__main__":
    main(sys.argv[1:])
