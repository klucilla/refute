"""v0.5.8 stage 1 (exploratory): the report of output stability, with the four doors counted by
the plan's rules (docs/plans/v0.5.8-plan.md, "The four doors"). Committed before any stage-1
result, with the corrections of Codex's design round (blocking item 3).

**Inputs:**
- the TOI-seeded records (``.cache/v058/run/records``, or once bundled ``stability-records.json``);
- the v0.5.6 records, from the bundles in git;
- the set, ``stage1-set.json``.

**Outputs:** ``stability-report.json`` and ``stability-report.md``. Everything is exploratory:
never a verdict, a candidate or a disposition. The numbers describe these TOIs only.

**Rules fixed before any result:**
- **Pairing.** Every rate compares a TOI's reseeded record with its v0.5.6 record, and is given with
  its Wilson 95 % interval.
- **Completeness.** The doors are marked only when there is exactly one record per key of the set,
  and every record carries a ``status`` (no duplicate, no extra). Until then:
  - the doors are ``incomplete``;
  - flips are summarized over the observed pairs only, labelled ``partial``.
- **A reseeded record that is not OK** changes class (door 1), and its test statuses all count as
  changed (door 2).
- **Two versions of every door,** with the same rules: in total, and only over the records whose
  provenance is ``same``. An empty ``same`` panel is shown as "no data".
- **Door 2, "near"** (decimal arithmetic, inclusive bounds). In the v0.5.6 record of that test:
  - some sensitivity block has |probability − required_probability| ≤ 0.02;
  - or the message's statistic is within 0.5 of its threshold, by the pattern
    ``<value> sigma (<= | > <threshold>)``.
- **Door 3:**
  - *Differs* when both SNRs exist, the v0.5.6 one is positive, and 10 × |SNR new − SNR v0.5.6| >
    SNR v0.5.6, compared in decimal arithmetic.
  - A missing SNR (a record that is not OK, or no candidate) is not "differs", and is counted
    apart.
  - *Found when:* at least ``ceil(0.05 × n)``, so 9 for the 167.

Usage (from the project root): ``stability_report.py``
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections import Counter
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
BUNDLES = {"A": ROOT / "docs/validation/v0.5.6/part-a-records.json",
           "B": ROOT / "docs/validation/v0.5.6/part-b-records.json"}  # fmt: skip
SET_FILE = HERE / "stage1-set.json"
BUNDLE = HERE / "stability-records.json"
FOLDER = ROOT / ".cache/v058/run/records"
OUT_JSON = HERE / "stability-report.json"
OUT_MD = HERE / "stability-report.md"
LABEL = "WEAKENED; does not meet D1, D2, D4, T2a"
STAT = re.compile(r"(-?\d+(?:\.\d+)?) sigma \((?:<=|>) (\d+(?:\.\d+)?)\)")
POWER_MARGIN, SIGMA_MARGIN = Decimal("0.02"), Decimal("0.5")


def wilson(k: int, n: int, z: float = 1.959963984540054) -> list[float] | None:
    if n == 0:
        return None
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return [max(0.0, centre - half), min(1.0, centre + half)]


def rate(k: int, n: int) -> dict:
    return {"k": k, "n": n, "rate": None if n == 0 else k / n, "wilson95": wilson(k, n)}


def load() -> list[dict]:
    if BUNDLE.exists():
        return [i["content"] for i in json.loads(BUNDLE.read_text("utf-8"))["records"]]
    if FOLDER.exists():
        return [json.loads(p.read_text("utf-8")) for p in sorted(FOLDER.glob("TIC-*.json"))]
    return []


def v056() -> dict[str, dict]:
    out = {}
    for part, path in BUNDLES.items():
        for item in json.loads(path.read_text("utf-8"))["records"]:
            out[item["content"]["target_key"]] = {**item["content"], "_part": part}
    return out


def ok(r: dict | None) -> bool:
    return r is not None and r.get("status") == "OK"


def outcome(r: dict | None) -> str:
    if r is None:
        return "NO RECORD"
    return r["outcome"] if ok(r) else r.get("status", "UNKNOWN")


def status(r: dict | None, name: str) -> str:
    if not ok(r):
        return "NOT OK"
    return ((r.get("tests") or {}).get(name) or {}).get("status") or "ABSENT"


def _dec(x) -> Decimal:
    return Decimal(str(x))


def near(base: dict, name: str) -> bool:
    """Door 2: was this test near its threshold in the v0.5.6 record? (decimal, inclusive)"""
    t = (base.get("tests") or {}).get(name) or {}
    s = t.get("sensitivity")
    if isinstance(s, dict):
        for b in s.values():
            if isinstance(b, dict) and "probability" in b and "required_probability" in b:
                if abs(_dec(b["probability"]) - _dec(b["required_probability"])) <= POWER_MARGIN:
                    return True
    m = STAT.search(t.get("message") or "")
    return m is not None and abs(_dec(m.group(1)) - _dec(m.group(2))) <= SIGMA_MARGIN


def snr_of(r: dict | None) -> Decimal | None:
    if not ok(r):
        return None
    value = (r.get("candidate") or {}).get("snr")
    if value is None:
        return None
    d = _dec(value)
    return d if d.is_finite() else None


def snr_differs(new: dict | None, base: dict) -> bool | None:
    """True or False when both SNRs exist and the v0.5.6 one is positive; None otherwise."""
    a, b = snr_of(new), snr_of(base)
    if a is None or b is None or b <= 0:
        return None
    return 10 * abs(a - b) > b


def complete_set(records: list[dict], keys: list[str]) -> tuple[bool, list[str]]:
    problems = []
    found = [r.get("target_key") for r in records]
    dup = sorted(k for k, n in Counter(found).items() if n > 1)
    if dup:
        problems.append(f"duplicate records: {dup[:5]}")
    extra = sorted(set(found) - set(keys))
    if extra:
        problems.append(f"records outside the set: {extra[:5]}")
    missing = sorted(set(keys) - set(found))
    if missing:
        problems.append(f"{len(missing)} keys have no record")
    if any("status" not in r for r in records):
        problems.append("a record has no status")
    return not problems, problems


def doors(new: dict[str, dict], base: dict[str, dict], keys: list[str], decided: list[str],
          fps: list[str], planets_b: list[str], complete: bool) -> dict:  # fmt: skip
    if not keys:
        return {d: {"found": None, "no_data": True} for d in ("door_1", "door_2", "door_3",
                                                             "door_4")}  # fmt: skip
    changed_class = [k for k in decided if outcome(new.get(k)) != outcome(base[k])]
    changes, near_changes = 0, 0
    for k in keys:
        names = set(base[k].get("tests") or {}) | set((new.get(k) or {}).get("tests") or {})
        for name in names:
            if status(new.get(k), name) != status(base[k], name):
                changes += 1
                near_changes += near(base[k], name)
    snr = [snr_differs(new.get(k), base[k]) for k in keys]
    differs, missing_snr = sum(1 for x in snr if x is True), sum(1 for x in snr if x is None)
    need3 = math.ceil(Decimal("0.05") * len(keys))
    fp_stay = sum(outcome(new.get(k)) == "REFUTED" for k in fps)
    pl_ref = sum(outcome(new.get(k)) == "REFUTED" for k in planets_b)
    d = {
        "door_1": {"decided": len(decided), "changed_class": len(changed_class),
                   "rate": rate(len(changed_class), len(decided)),
                   "found": len(changed_class) <= 5},
        "door_2": {"status_changes": changes, "near": near_changes,
                   "rate": rate(near_changes, changes),
                   "found": changes > 0 and Decimal(near_changes) / changes >= Decimal("0.80")},
        "door_3": {"tois": len(keys), "snr_differs": differs, "snr_missing": missing_snr,
                   "needed": need3, "rate": rate(differs, len(keys)),
                   "found": differs >= need3},
        "door_4": {"fp_events": len(fps), "fp_stay_refuted": fp_stay,
                   "planets_b": len(planets_b), "planets_refuted": pl_ref,
                   "found": fp_stay >= 15 and pl_ref <= 2},
    }  # fmt: skip
    for door in d.values():
        door["complete"] = complete
        if not complete:
            door["found"] = None
    return d


def flips(new: dict[str, dict], base: dict[str, dict], keys: list[str], partial: bool) -> dict:
    per_output = Counter(f"{outcome(base[k])} -> {outcome(new.get(k))}" for k in keys)
    per_test: dict[str, Counter] = {}
    tested: Counter = Counter()
    for k in keys:
        names = set(base[k].get("tests") or {}) | set((new.get(k) or {}).get("tests") or {})
        for name in names:
            tested[name] += 1
            a, b = status(base[k], name), status(new.get(k), name)
            if a != b:
                per_test.setdefault(name, Counter())[f"{a} -> {b}"] += 1
    changed = sum(n for p, n in per_output.items() if p.split(" -> ")[0] != p.split(" -> ")[1])
    return {
        "partial": partial,
        "pairs": len(keys),
        "per_output": dict(sorted(per_output.items())),
        "outputs_changed": rate(changed, len(keys)),
        "per_test": {
            name: {"changes": dict(c), "rate": rate(sum(c.values()), tested[name])}
            for name, c in sorted(per_test.items())
        },  # fmt: skip
        "tests_never_changed": sorted(n for n in tested if n not in per_test),
    }


def build() -> dict:
    s = json.loads(SET_FILE.read_text("utf-8"))
    base = v056()
    keys = [*s["decided"], *s["inconclusive_drawn"]]
    records = load()
    complete, problems = complete_set(records, keys)
    new = {r["target_key"]: r for r in records if r.get("target_key") in set(keys)}
    observed = keys if complete else [k for k in keys if k in new]
    fps = [k for k in s["decided"] if base[k]["_part"] == "B" and base[k]["arm"] == "fp"
           and base[k]["outcome"] == "REFUTED"]  # fmt: skip
    planets_b = [k for k in keys if base[k]["_part"] == "B" and base[k]["arm"] == "planet"]
    same = [k for k in keys if ((new.get(k) or {}).get("provenance") or {}).get("overall")
            == "same"]  # fmt: skip
    prov = Counter(((r.get("provenance") or {}).get("overall") or "none") for r in records)
    return {
        "schema": "refute-v058-stability-report-1",
        "mode": "exploratory",
        "limits_label": LABEL,
        "method_status": "not_validated",
        "code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "set_sha256": hashlib.sha256(SET_FILE.read_bytes()).hexdigest(),
        "records": len(records),
        "complete": complete,
        "completeness_problems": problems,
        "provenance": dict(prov),
        "flips_total": flips(new, base, observed, not complete),
        "flips_same": flips(new, base, [k for k in same if k in observed], not complete),
        "doors_total": doors(new, base, keys, s["decided"], fps, planets_b, complete),
        "doors_same": doors(
            new,
            base,
            same,
            [k for k in s["decided"] if k in same],
            [k for k in fps if k in same],
            [k for k in planets_b if k in same],
            complete,
        ),  # fmt: skip
    }


def mark(d: dict) -> str:
    if d.get("no_data"):
        return "no data"
    return "incomplete" if d["found"] is None else ("FOUND" if d["found"] else "not found")


def fmt(r: dict) -> str:
    if r["n"] == 0:
        return "0 of 0"
    lo, hi = r["wilson95"]
    return f"{r['k']} of {r['n']} ({r['rate']:.3f}; Wilson 95 % {lo:.3f} to {hi:.3f})"


def markdown(rep: dict) -> str:
    lines = [
        "# v0.5.8: output stability of the v0.5 battery (exploratory)",
        "",
        f"**Exploratory.** Limits label: '{rep['limits_label']}'. `method_status: "
        "not_validated`. Never a verdict, a candidate or a disposition; the numbers describe "
        "these TOIs only. Each TOI-seeded record is compared with its v0.5.6 record.",
        "",
        f"Records: {rep['records']}; complete: {rep['complete']}; provenance: {rep['provenance']}.",
    ]
    if rep["completeness_problems"]:
        lines += ["", "Not complete (the doors are not marked; flips are partial):", ""]
        lines += [f"- {p}" for p in rep["completeness_problems"]]
    for version in ("total", "same"):
        f, d = rep[f"flips_{version}"], rep[f"doors_{version}"]
        lines += ["", f"## {version}" + (" (partial)" if f["partial"] else ""), ""]
        if d["door_1"].get("no_data"):
            lines += ["No data: no record has provenance `same`.", ""]
            continue
        lines += [f"- Outputs that changed: {fmt(f['outputs_changed'])}.",
                  "- Per output: " + "; ".join(f"{p} {n}" for p, n in f["per_output"].items())
                  + ".", "- Status changes per test:"]  # fmt: skip
        lines += [f"  - `{n}`: {fmt(v['rate'])}; "
                  + "; ".join(f"{p} {c}" for p, c in v["changes"].items())
                  for n, v in f["per_test"].items()]  # fmt: skip
        lines += [
            f"- Tests that never changed: {', '.join(f['tests_never_changed']) or 'none'}.",
            "",
            f"1. **Stable output:** {mark(d['door_1'])}: changed class "
            f"{fmt(d['door_1']['rate'])} (at most 5 needed).",
            f"2. **Flip predictable from the records:** {mark(d['door_2'])}: near "
            f"{fmt(d['door_2']['rate'])} (at least 80 % needed).",
            f"3. **More than one optimum:** {mark(d['door_3'])}: SNR differs by more than 10 % "
            f"in {fmt(d['door_3']['rate'])}; SNR missing {d['door_3']['snr_missing']} (at least "
            f"{d['door_3']['needed']} needed).",
            f"4. **The claim's events:** {mark(d['door_4'])}: FPs still REFUTED "
            f"{d['door_4']['fp_stay_refuted']} of {d['door_4']['fp_events']} (at least 15); "
            f"part B planets REFUTED {d['door_4']['planets_refuted']} of "
            f"{d['door_4']['planets_b']} (at most 2).",
        ]
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    rep = build()
    OUT_JSON.write_text(json.dumps(rep, indent=1) + "\n", "utf-8", newline="\n")
    OUT_MD.write_text(markdown(rep), "utf-8", newline="\n")
    print(json.dumps({v: {k: d["found"] for k, d in rep[f"doors_{v}"].items()}
                      for v in ("total", "same")}))  # fmt: skip


if __name__ == "__main__":
    main()
