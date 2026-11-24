"""Recounts asked by Codex's round on the report (docs/plans/v0.5.10-consensus/), from the cached
census tables only: no new query, no new target looked at, no recorded value re-scored.

- **Exposure, repository-wide** (blocking item 3). Two sets of TIC ids from the git-tracked files
  outside docs/validation/v0.5.10/:
  - "in run records": the files of docs/validation/ and calibration/ that hold run outputs or
    selection draws (records, draws, candidates, ledgers);
  - "mentioned anywhere": any tracked file. TIC ids are read in the forms TIC-123, TIC 123,
    TIC123, "tic_id": 123 and "tic": 123.
  The usable arms of (d1) and the Kepler field are counted again without each set.
- **Units** (important items 9 to 11). Rows against distinct TICs for (d1), Kepler and route (e).
  The (d1) ground subset is also counted without the ambiguous facility labels "Multiple
  Observatories" and "Multiple Facilities".
- **Route (e), per target** (blocking item 2). route-e-targets.csv: one row per list and target,
  with the on-silicon state per sector, the predicted transits on silicon, the 2-minute history and
  the expected product. The expected product is "not determined", because the sectors' 2-minute
  target lists were not found.

Writes recheck-after-codex.json and route-e-targets.csv.
"""

from __future__ import annotations

import csv
import json
import re
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CACHE = ROOT / ".cache/v0510"
FORMS = [
    re.compile(r"TIC[-_ ]?(\d{4,10})\b"),
    re.compile(r'"tic_id"\s*:\s*"?(\d{4,10})'),
    re.compile(r'"tic"\s*:\s*"?(\d{4,10})'),
]
RECORD_HINTS = ("record", "draw", "candidate", "ledger", "units", "set", "selection", "frame")
AMBIGUOUS = {"Multiple Observatories", "Multiple Facilities"}


def tracked() -> list[str]:
    out = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, check=True)
    return [p for p in out.stdout.decode("utf-8").split("\0") if p]


def tic_sets() -> tuple[set[int], set[int]]:
    anywhere, records = set(), set()
    for rel in tracked():
        if rel.startswith("docs/validation/v0.5.10/"):
            continue
        p = ROOT / rel
        try:
            data = p.read_bytes()
        except OSError:
            continue
        if b"\0" in data[:4096]:
            continue
        text = data.decode("utf-8", errors="replace")
        found = {int(m.group(1)) for f in FORMS for m in f.finditer(text)}
        anywhere |= found
        name = rel.lower()
        if (name.startswith(("docs/validation/", "calibration/"))) and any(
            h in name for h in RECORD_HINTS
        ):
            records |= found
    return anywhere, records


def main() -> int:
    anywhere, records = tic_sets()
    d1 = json.loads((CACHE / "census/census-d1-targets.json").read_text(encoding="utf-8"))
    kep = json.loads((CACHE / "census/census-kepler-targets.json").read_text(encoding="utf-8"))
    out: dict = {
        "schema": "refute-v0510-recheck-1",
        "mode": "exploratory",
        "method_status": "not_validated",
        "tic_ids_in_run_records_outside_v0510": len(records),
        "tic_ids_mentioned_anywhere_outside_v0510": len(anywhere),
        "promoted_v04_in_run_records": sorted(
            t for t in (88096786, 286480954, 406413408) if t in records
        ),
    }

    def usable(rows, extra=None):
        return {
            r["tic"]
            for r in rows
            if r.get("spoc_2min") and not r.get("exposed") and (extra is None or extra(r))
        }

    arms = {}
    for arm in ("kelt_fp", "planets_not_tess"):
        rows = [r for r in d1 if r["arm"] == arm]
        u = usable(rows)
        arms[arm] = {
            "rows": len(rows),
            "distinct_tics": len({r["tic"] for r in rows}),
            "usable_distinct_tics": len(u),
            "usable_without_run_records": len(u - records),
            "usable_without_any_mention": len(u - anywhere),
        }
    planets = [r for r in d1 if r["arm"] == "planets_not_tess"]
    space = ("Kepler", "K2", "CoRoT", "Spitzer", "Hubble", "James Webb", "CHEOPS", "Gaia")

    def ground(r, strict=False):
        f = r.get("facility") or ""
        if any(s in f for s in space):
            return False
        return not (strict and f in AMBIGUOUS)

    g = usable(planets, ground)
    gs = usable(planets, lambda r: ground(r, True))
    arms["planets_ground"] = {
        "usable_distinct_tics": len(g),
        "usable_without_ambiguous_facilities": len(gs),
        "usable_without_run_records": len(g - records),
        "usable_without_ambiguous_and_run_records": len(gs - records),
        "usable_without_any_mention": len(g - anywhere),
    }
    fac_rows: dict[str, int] = {}
    fac_tics: dict[str, set] = {}
    for r in planets:
        if r.get("spoc_2min") and not r.get("exposed"):
            f = r.get("facility") or ""
            fac_rows[f] = fac_rows.get(f, 0) + 1
            fac_tics.setdefault(f, set()).add(r["tic"])
    arms["planets_usable_by_facility"] = {
        f: {"rows": fac_rows[f], "distinct_tics": len(fac_tics[f])}
        for f in sorted(fac_rows, key=lambda x: -fac_rows[x])[:6]
    }
    out["d1"] = arms
    kout = {}
    for arm in ("certified_fp", "kepler_planets"):
        rows = [r for r in kep if r["arm"] == arm]
        two = [r for r in rows if r.get("spoc_2min")]
        t2 = {r["tic"] for r in two if r.get("tic")}
        kout[arm] = {
            "rows": len(rows),
            "spoc_2min_rows": len(two),
            "spoc_2min_distinct_tics": len(t2),
            "spoc_2min_without_run_records": len(t2 - records),
            "tglc": "not determined (the lookup returned none under a TIC target name)",
        }
    out["kepler"] = kout
    rt = json.loads((CACHE / "route-e/route-e-targets.json").read_text(encoding="utf-8"))
    sectors = sorted(rt[0]["sectors"], key=int)
    rout = {}
    for lst in ("eumemic", "ctoi", "refute_own"):
        rows = [r for r in rt if r["list"] == lst]
        hit = [r for r in rows if r["transits"] > 0]
        rout[lst] = {
            "entries": len(rows),
            "distinct_tics": len({r["tic"] for r in rows}),
            "entries_with_transit_on_silicon": len(hit),
            "distinct_tics_with_transit_on_silicon": len({r["tic"] for r in hit}),
            "distinct_tics_with_transit_and_2min_history": len(
                {r["tic"] for r in hit if r["two_min_history"]}
            ),
        }
    out["route_e"] = rout
    out["route_e_limits"] = [
        "adjacent sector windows share their boundary day, so an event on that day counts in two "
        "sectors; not corrected here",
        "a missing uncertainty term was treated as zero by route_e.py; not corrected here",
        "sector 110 began on 2026-10-31, before the census; its events are not prospective",
        "the 2-minute history is a proxy from earlier sectors, not the expected product",
    ]
    (HERE / "recheck-after-codex.json").write_text(json.dumps(out, indent=1) + "\n", "utf-8")
    with open(HERE / "route-e-targets.csv", "w", encoding="utf-8", newline="\n") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(
            [
                "list",
                "tic",
                *[f"s{s}" for s in sectors],
                "transits_on_silicon",
                "two_min_history",
                "expected_product",
            ]  # fmt: skip
        )
        for r in sorted(rt, key=lambda r: (r["list"], r["tic"])):
            w.writerow(
                [
                    r["list"],
                    r["tic"],
                    *[r["sectors"][s] for s in sectors],
                    r["transits"],
                    r["two_min_history"],
                    "not determined",
                ]  # fmt: skip
            )
    print(json.dumps({k: out[k] for k in ("d1", "kepler", "route_e")}, indent=1)[:4000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
