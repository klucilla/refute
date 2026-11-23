"""v0.5.7 (exploratory): the report of fixed mode against search mode, with the four doors
counted by the plan's rules (docs/plans/v0.5.7-plan.md, "The four doors"). Committed before any
fixed-mode result exists (exit criterion 1).

Inputs:
- the fixed-mode records, from ``.cache/v057/run/records`` or, once bundled, from
  ``fixed-records.json``;
- the v0.5.6 search-mode records, from the bundles in git.

Outputs: ``fixed-report.json`` and ``fixed-report.md``. Everything is exploratory: never a
verdict, a candidate or a disposition. The numbers describe these 540 TOIs, never the TOI
population.

The groups:
- planets: part A's planet arm (120) and part B's planet stratum (150), 270 in all;
- part B's FPs (150);
- part A's open arm (120), reported apart and outside every door.

A record that is not OK counts as INCONCLUSIVE in doors 3 and 4, and never as an event.

Usage (from the project root): ``fixed_report.py [records-folder-or-bundle]``.
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
DEFAULT_RECORDS = ROOT / ".cache/v057/run/records"
BUNDLE = HERE / "fixed-records.json"
OUT_JSON = HERE / "fixed-report.json"
OUT_MD = HERE / "fixed-report.md"
LABEL = "WEAKENED; does not meet D1, D2, D4, T2a"
OUTCOMES = ("SURVIVED", "WEAKENED", "REFUTED", "INCONCLUSIVE")
DOMAIN = (0.5, 20.0)


def _bundle_records(path: Path) -> list[dict]:
    doc = json.loads(path.read_text("utf-8"))
    return [item["content"] for item in doc["records"]]


def load_fixed(source: Path) -> list[dict]:
    if source.is_dir():
        return [json.loads(p.read_text("utf-8")) for p in sorted(source.glob("TIC-*.json"))]
    return _bundle_records(source)


def load_search() -> dict[str, dict]:
    out = {}
    for part, path in SEARCH_BUNDLES.items():
        for r in _bundle_records(path):
            out[r["target_key"]] = {**r, "part": part}
    return out


def toi_periods() -> dict[str, float]:
    """The TOI period of every drawn TIC, from the draws (the frozen frame's values)."""
    out = {}
    for path in DRAWS.values():
        for arm in json.loads(path.read_text("utf-8"))["arms"].values():
            for c in arm["chosen"]:
                out[f"TIC-{c['tic_id']}"] = float(c["period_days"])
    return out


def group_of(r: dict) -> str:
    if r["arm"] == "planet":
        return "planet"
    return "fp_B" if r["part"] == "B" else "open_A"


def outcome(r: dict | None) -> str:
    """A record's outcome; anything not OK is shown by its status."""
    if r is None:
        return "NO RECORD"
    return r.get("outcome") if r.get("status") == "OK" else r.get("status", "UNKNOWN")


def as_inconclusive(r: dict | None) -> bool:
    """Doors 3 and 4: a record that is not OK counts as INCONCLUSIVE."""
    return r is None or r.get("status") != "OK" or r.get("outcome") == "INCONCLUSIVE"


def test_status(r: dict | None, name: str) -> str | None:
    if r is None or r.get("status") != "OK":
        return None
    return (r.get("tests", {}).get(name) or {}).get("status")


def fatal_tests(records: list[dict]) -> list[str]:
    names = set()
    for r in records:
        for name, t in (r.get("tests") or {}).items():
            if t.get("severity") == "fatal":
                names.add(name)
    return sorted(names)


def doors(fixed: dict[str, dict], search: dict[str, dict], keys: dict[str, list[str]]) -> dict:
    """The four doors. A door is marked only when every one of the 540 TOIs has a fixed-mode
    record; until then ``found`` is None (incomplete), so a door can never pass for lack of data."""
    marked = doors_counted(fixed, search, keys)
    complete = set(search) <= set(fixed)
    for d in marked.values():
        d["complete"] = complete
        if not complete:
            d["found"] = None
    return marked


def doors_counted(
    fixed: dict[str, dict], search: dict[str, dict], keys: dict[str, list[str]]
) -> dict:
    planets, fps = keys["planet"], keys["fp_B"]

    def refuted_snr_pass(rec: dict[str, dict], ks: list[str]) -> int:
        return sum(
            1
            for k in ks
            if outcome(rec.get(k)) == "REFUTED" and test_status(rec.get(k), "snr") == "PASS"
        )

    d1_fixed, d1_search = refuted_snr_pass(fixed, planets), refuted_snr_pass(search, planets)
    all_fixed = [r for r in fixed.values() if r.get("status") == "OK"]
    per_test = {}
    for name in fatal_tests(all_fixed):
        fp_fail = sum(1 for k in fps if test_status(fixed.get(k), name) == "FAIL")
        pl_fail = sum(1 for k in planets if test_status(fixed.get(k), name) == "FAIL")
        per_test[name] = {"fp_B_fail": fp_fail, "planet_fail": pl_fail,
                          "qualifies": fp_fail >= 10 and pl_fail <= 1}  # fmt: skip
    periods = toi_periods()
    out_of_domain = sorted(k for k in search if not DOMAIN[0] <= periods[k] <= DOMAIN[1])
    d3_decided = sum(1 for k in out_of_domain if not as_inconclusive(fixed.get(k)))
    d3_search = sum(1 for k in out_of_domain if not as_inconclusive(search.get(k)))
    d4_fixed = sum(1 for k in planets if as_inconclusive(fixed.get(k)))
    d4_search = sum(1 for k in planets if as_inconclusive(search.get(k)))
    n_pl, n_out = len(planets), len(out_of_domain)
    return {
        "door_1": {
            "text": "In fixed mode, among confirmed planets with the SNR gate passed, REFUTED "
            "falls from 22 (9 in A, 13 in B) to at most 4 of 270.",
            "rule": "fixed-mode planet records with outcome REFUTED and snr PASS; found if at "
            "most 4",
            "planets": n_pl,
            "search_mode": d1_search,
            "fixed_mode": d1_fixed,
            "found": d1_fixed <= 4,
        },
        "door_2": {
            "text": "Some fatal test fails in at least 10 FPs and in at most 1 planet (the FPs "
            "come only from part B).",
            "rule": "per fatal test: FAIL among part B's 150 FPs and among the 270 planets; "
            "found if some test has at least 10 and at most 1",
            "per_test": per_test,
            "qualifying": sorted(n for n, v in per_test.items() if v["qualifies"]),
            "found": any(v["qualifies"] for v in per_test.values()),
        },
        "door_3": {
            "text": "Among the 60 TOIs with a period outside 0.5 to 20 d, at least 20 % end with "
            "an outcome other than INCONCLUSIVE.",
            "rule": "TOI period below 0.5 d or above 20 d; a record that is not OK counts as "
            "INCONCLUSIVE; found if the fraction is at least 0.20",
            "tois": n_out,
            "search_mode_decided": d3_search,
            "fixed_mode_decided": d3_decided,
            "fraction": d3_decided / n_out if n_out else None,
            "found": bool(n_out) and d3_decided / n_out >= 0.20,
        },
        "door_4": {
            "text": "INCONCLUSIVE in planets falls to 50 % or less (expected not to be found).",
            "rule": "among the 270 planets, a record that is not OK counts as INCONCLUSIVE; "
            "found if the fraction is at most 0.50",
            "planets": n_pl,
            "search_mode_inconclusive": d4_search,
            "fixed_mode_inconclusive": d4_fixed,
            "fraction": d4_fixed / n_pl if n_pl else None,
            "found": bool(n_pl) and d4_fixed / n_pl <= 0.50,
        },
    }


def build(source: Path) -> dict:
    try:
        label = source.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        label = source.name
    return build_from(load_fixed(source), label)


def build_from(fixed_list: list[dict], source_label: str) -> dict:
    """The report from fixed-mode records already read (the tests call it directly)."""
    fixed = {r["target_key"]: r for r in fixed_list}
    search = load_search()
    keys: dict[str, list[str]] = {"planet": [], "fp_B": [], "open_A": []}
    for k, r in sorted(search.items()):
        keys[group_of(r)].append(k)
    groups = {}
    for g, ks in keys.items():
        f_out = Counter(outcome(fixed.get(k)) for k in ks)
        s_out = Counter(outcome(search.get(k)) for k in ks)
        paired = Counter(f"{outcome(search.get(k))} -> {outcome(fixed.get(k))}" for k in ks)
        ok = [fixed[k] for k in ks if k in fixed and fixed[k].get("status") == "OK"]
        groups[g] = {
            "tois": len(ks),
            "fixed_records": sum(k in fixed for k in ks),
            "search_outcomes": dict(s_out),
            "fixed_outcomes": dict(f_out),
            "paired": dict(sorted(paired.items())),
            "search_matched": sum(
                bool((search[k].get("identity") or {}).get("matched")) for k in ks
            ),  # fmt: skip
            "fixed_matched": sum(bool((r.get("identity") or {}).get("matched")) for r in ok),
            "window_found": sum(bool((r.get("window") or {}).get("found")) for r in ok),
            "left_window": sum(bool((r.get("identity") or {}).get("left_window")) for r in ok),
        }
    transitions: dict[str, Counter] = {}
    for k, s in search.items():
        f = fixed.get(k)
        if f is None or f.get("status") != "OK" or s.get("status") != "OK":
            continue
        for name in set(s.get("tests", {})) | set(f.get("tests", {})):
            a, b = test_status(s, name), test_status(f, name)
            if a != b:
                transitions.setdefault(name, Counter())[f"{a} -> {b}"] += 1
    return {
        "schema": "refute-v057-fixed-report-1",
        "mode": "exploratory",
        "limits_label": LABEL,
        "method_status": "not_validated",
        "note": "Exploratory: never a verdict, a candidate or a disposition; the numbers describe "
        "these 540 TOIs, never the TOI population.",
        "source": {
            "fixed_records": source_label,
            "fixed_count": len(fixed),
            "search_bundles": {
                p: v.relative_to(ROOT).as_posix() for p, v in SEARCH_BUNDLES.items()
            },
        },
        "code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "groups": groups,
        "test_status_changes": {n: dict(c) for n, c in sorted(transitions.items())},
        "doors": doors(fixed, search, keys),
    }


def mark(door: dict) -> str:
    if door["found"] is None:
        return "incomplete (not every TOI has a fixed-mode record)"
    return "FOUND" if door["found"] else "not found"


def markdown(rep: dict) -> str:
    names = {"planet": "Planets (A + B)", "fp_B": "FPs (part B)", "open_A": "Open arm (part A)"}
    lines = [
        "# v0.5.7: the TOI's own signal, fixed mode against search mode (exploratory)",
        "",
        f"**Exploratory.** Limits label: '{rep['limits_label']}'. `method_status: not_validated`. "
        + rep["note"],
        "",
        f"Fixed-mode records: {rep['source']['fixed_count']}. Generated by `fixed_report.py` "
        f"(SHA-256 `{rep['code_sha256'][:16]}...`).",
        "",
        "## Outcomes, search mode against fixed mode",
        "",
        "| Group | TOIs | Mode | " + " | ".join(OUTCOMES) + " | Other | Matched |",
        "|---|---|---|" + "---|" * (len(OUTCOMES) + 2),
    ]
    for g, v in rep["groups"].items():
        for mode, key, matched in (("search", "search_outcomes", v["search_matched"]),
                                   ("fixed", "fixed_outcomes", v["fixed_matched"])):  # fmt: skip
            c = v[key]
            other = sum(n for o, n in c.items() if o not in OUTCOMES)
            lines.append(f"| {names[g]} | {v['tois']} | {mode} | "
                         + " | ".join(str(c.get(o, 0)) for o in OUTCOMES)
                         + f" | {other} | {matched} |")  # fmt: skip
    lines += ["", "Window (fixed mode): an offset was found in the window, and the final epoch "
              "left it.", ""]  # fmt: skip
    for g, v in rep["groups"].items():
        lines.append(f"- {names[g]}: window found {v['window_found']}, left the window "
                     f"{v['left_window']}.")  # fmt: skip
    lines += ["", "## Paired outcomes (search -> fixed)", ""]
    for g, v in rep["groups"].items():
        pairs = "; ".join(f"{p} {n}" for p, n in v["paired"].items())
        lines.append(f"- {names[g]}: {pairs}")
    lines += ["", "## Test status changes (search -> fixed, records OK in both)", ""]
    for name, c in rep["test_status_changes"].items():
        lines.append(f"- `{name}`: " + "; ".join(f"{p} {n}" for p, n in sorted(c.items())))
    d = rep["doors"]
    lines += [
        "",
        "## The four doors (counted by the plan's rules, fixed before any result)",
        "",
        f"1. **Identity resolved:** {mark(d['door_1'])}. "
        f"REFUTED with SNR PASS among the {d['door_1']['planets']} planets: search "
        f"{d['door_1']['search_mode']}, fixed {d['door_1']['fixed_mode']} (at most 4 needed).",
        f"2. **A discriminating test:** {mark(d['door_2'])}"
        + (f" ({', '.join(d['door_2']['qualifying'])})" if d["door_2"]["qualifying"] else "")
        + ". FAIL per fatal test (FPs of part B / planets): "
        + "; ".join(
            f"`{n}` {v['fp_B_fail']}/{v['planet_fail']}" for n, v in d["door_2"]["per_test"].items()
        )
        + ".",  # fmt: skip
        f"3. **Outside the search's domain:** {mark(d['door_3'])}. "
        f"Decided (not INCONCLUSIVE) among {d['door_3']['tois']} TOIs: search "
        f"{d['door_3']['search_mode_decided']}, fixed {d['door_3']['fixed_mode_decided']} "
        f"(at least 20 % needed).",
        f"4. **Decidability:** {mark(d['door_4'])}. INCONCLUSIVE "
        f"among the {d['door_4']['planets']} planets: search "
        f"{d['door_4']['search_mode_inconclusive']}, fixed {d['door_4']['fixed_mode_inconclusive']}"
        f" (at most 50 % needed).",
        "",
        "## Limits",
        "",
        "- The battery is v0.5's, with its limits label; nothing in it changed.",
        "- Fixed mode attacks the TOI's ephemeris; the battery's own finalization may still move "
        "the epoch, and every record says whether it left the window.",
        "- Agreement with any catalogue is not independence. No output is about a single TOI.",
        "",
    ]
    return "\n".join(lines)


def main(argv: list[str]) -> None:
    source = Path(argv[0]).resolve() if argv else (BUNDLE if BUNDLE.exists() else DEFAULT_RECORDS)
    rep = build(source)
    OUT_JSON.write_text(json.dumps(rep, indent=1) + "\n", "utf-8", newline="\n")
    OUT_MD.write_text(markdown(rep), "utf-8", newline="\n")
    print(json.dumps({k: v["found"] for k, v in rep["doors"].items()}))


if __name__ == "__main__":
    main(sys.argv[1:])
