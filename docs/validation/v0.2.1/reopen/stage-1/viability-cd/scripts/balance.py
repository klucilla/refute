"""The ceiling's balance on 2026-10-27, before the comparative viability package (read only).

The 4000 LP-h and 200 h ceilings of plan B (plan-b/budget-b.json, its snapshot of plan B's
adoption), less what ran since that snapshot, item by item:

- the snapshot's consumption, as budget-b.json records it (the lots and the kept suites);
- the suites since: every JUnit file under .cache/ written from the snapshot's time on (the
  budget's commit, 2026-10-23 15:38 local), its suite time, in LP-h by budget_b.py's proxy (24
  processors times the wall time); a file written in the snapshot's minute is counted again (a
  possible double count, on the side of a smaller balance);
- the lots since, measured where a record holds the time: the two X2 subsets of the dependency
  update (their run reports: elapsed hours times workers); the acceptance population generated again
  on 2026-10-27 (from the full suite's JUnit file to the manifest's write time, 22 workers);
- what ran without a recorded time, **estimated**: gate 1's three generations of the acceptance
  population (each at the measured cost of the 2026-10-27 generation; wall at their worker counts
  22, 13 and 7) and gate 1's sabotages (an allowance, not a measurement);
- the real controls' check (queries only: 0 LP-h, its wall time from result.json).

Codex's reviews and the interactive work are outside these ceilings, as in budget_b.py.

python balance.py <out.json>
"""

from __future__ import annotations

import json
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[7]
STAGE = ROOT / "docs/validation/v0.2.1/reopen/stage-1"
CACHE = ROOT / ".cache"
SNAPSHOT_LOCAL = "2026-10-23T15:38:00-03:00"
LP_MAX, WALL_MAX = 4000.0, 200.0
SUITE_LP = 24
GEN_WORKERS = (22, 13, 7)
SABOTAGE_ALLOWANCE = {"lp_h": 12.0, "wall_h": 1.0}


def junit_since(after: float) -> list[dict]:
    out = []
    for p in sorted(CACHE.rglob("*.xml")):
        if p.stat().st_mtime < after or "tmp" in p.parts:
            continue
        try:
            r = ET.parse(p).getroot()
        except ET.ParseError:
            continue
        suites = [r] if r.tag == "testsuite" else [s for s in r if s.tag == "testsuite"]
        if r.tag not in ("testsuite", "testsuites") or not suites:
            continue
        seconds = sum(float(s.get("time", 0)) for s in suites)
        out.append({"file": p.relative_to(ROOT).as_posix(), "seconds": round(seconds, 3)})
    return out


def main(argv: list[str]) -> int:
    budget = json.loads((STAGE / "plan-b/budget-b.json").read_text(encoding="utf-8"))
    c = budget["consumed"]
    snap_lp = c["lots_lp_h"] + c["suites_kept_lp_h_proxy"]
    snap_wall = c["lots_wall_h"] + c["suites_kept_wall_h"]
    after = datetime.fromisoformat(SNAPSHOT_LOCAL).timestamp()
    suites = junit_since(after)
    suite_h = sum(s["seconds"] for s in suites) / 3600
    deps = CACHE / "deps-1027"
    subsets = []
    for name in ("x2-subset-updated", "x2-subset-frozen"):
        report = json.loads(next((deps / name).glob("run-report-*.json")).read_text("utf-8"))
        subsets.append(
            {
                "run": name,
                "elapsed_h": report["elapsed_hours"],
                "workers": report["workers"],
                "lp_h": report["elapsed_hours"] * report["workers"],
            }
        )
    start = (deps / "suite.xml").stat().st_mtime
    end = (deps / "acceptance/manifest-after-update.json").stat().st_mtime
    gen_wall = (end - start) / 3600
    gen_lp = gen_wall * 22
    gate1 = {
        "lp_h": len(GEN_WORKERS) * gen_lp,
        "wall_h": sum(gen_lp / w for w in GEN_WORKERS),
        "note": "estimated: three generations at the 2026-10-27 generation's measured LP-h",
    }
    rc = json.loads((STAGE / "real-controls/result.json").read_text(encoding="utf-8"))
    rc_wall = (
        datetime.fromisoformat(rc["finished_utc"]) - datetime.fromisoformat(rc["started_utc"])
    ).total_seconds() / 3600
    since = {
        "suites": {"lp_h": suite_h * SUITE_LP, "wall_h": suite_h, "files": suites},
        "x2_subsets_2026_10_27": {
            "lp_h": sum(s["lp_h"] for s in subsets),
            "wall_h": sum(s["elapsed_h"] for s in subsets),
            "runs": subsets,
        },
        "acceptance_regeneration_2026_10_27": {
            "lp_h": gen_lp,
            "wall_h": gen_wall,
            "note": "from suite.xml's to the manifest's write time, 22 workers (an upper bound)",
        },
        "gate1_generations_estimated": gate1,
        "gate1_sabotages_allowance": {**SABOTAGE_ALLOWANCE, "note": "not recorded; an allowance"},
        "real_controls_check": {"lp_h": 0.0, "wall_h": rc_wall},
    }
    since_lp = sum(v["lp_h"] for v in since.values())
    since_wall = sum(v["wall_h"] for v in since.values())
    out = {
        "format": "refute-v0.2.1-balance/1",
        "computed_utc": datetime.now().astimezone().isoformat(timespec="seconds"),
        "snapshot": {"source": "plan-b/budget-b.json", "lp_h": snap_lp, "wall_h": snap_wall},
        "since_snapshot": since,
        "consumed_lp_h": snap_lp + since_lp,
        "consumed_wall_h": snap_wall + since_wall,
        "unspent_lp_h": LP_MAX - snap_lp - since_lp,
        "unspent_wall_h": WALL_MAX - snap_wall - since_wall,
        "plan_b_reserved_steps_now_void": "plan B ended on 2026-10-27; its reserved steps no "
        "longer hold a claim on the ceiling",
    }
    Path(argv[1]).write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8", newline="\n")
    for k, v in since.items():
        print(f"{k}: {v['lp_h']:.2f} LP-h, {v['wall_h']:.2f} h")
    print(f"snapshot {snap_lp:.1f} LP-h {snap_wall:.1f} h;",
          f"consumed {out['consumed_lp_h']:.1f} LP-h, {out['consumed_wall_h']:.1f} h;",
          f"unspent {out['unspent_lp_h']:.1f} LP-h, {out['unspent_wall_h']:.1f} h")  # fmt: skip
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
