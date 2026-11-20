"""v0.5.5: T2a-E's geometry count, before it runs (#218; the maintainer's decision of 2026-11-20,
night, item 4b). ``method_status: not_validated``. Development records only; nothing is replayed.

For each of T2a-E's 102 injections, from its **recorded** final candidate's period (B1's record,
carried by step 6's schedule as ``expected_candidate``, which holds no duration), the **injected
duration** recorded in C2's references (``c2.references``: ``duration_hours``; a declared proxy
for the final candidate's duration, which no record holds) and its recorded ``secondary_eclipse``
status: how
many of T2a-E's 24 shift phases have the geometry to be usable (``t2ae_census.shift_phases``'s
rule: E4's outer half-width is ``duration/2 + 1.5 duration``, so a phase is kept when it stays
more than ``4 duration / period`` from phase 0, and from phase 0.5 when E4 excludes it). E4
excludes phase 0.5 when the secondary-eclipse test FAILed (``pipeline_v52``); a missing status is
counted as excluded (the side with fewer phases).

**The frozen rule (item 4b):** an injection with fewer than 12 geometric phases will be UNK. If
more than 20 of the 102 would be UNK on geometry alone, T2a-E does not run (futility), and this
record says so. Geometry is necessary, not sufficient: E4 may still return no value at a usable
phase.

Usage: ``.venv/Scripts/python.exe -B .cache/v054/tools/pin.py "import runpy;
runpy.run_path('docs/validation/v0.5.5/t2ae_geometry.py', run_name='__main__')"``
"""

from __future__ import annotations

import json
import sys
import time
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import t2ae_census as tc  # noqa: E402,I001  (it imports the earlier stages, then ledger_v055)
import ledger_v055 as lv  # noqa: E402

OUT_FILE = HERE / "t2ae-geometry.json"
OUTER_DURATIONS = 1.5  # calibration/v0.4/claim.yaml:150, baseline_outer_durations


def geometric_phases(period: float, duration: float, exclude_half: bool) -> int:
    cand = types.SimpleNamespace(period=period, duration=duration)
    plan = types.SimpleNamespace(
        gauntlet=types.SimpleNamespace(
            events=types.SimpleNamespace(baseline_outer_durations=OUTER_DURATIONS)
        )
    )
    return len(tc.shift_phases(cand, plan, exclude_half))


def _get(c: dict, *names):
    for n in names:
        if c.get(n) is not None:
            return float(c[n])
    raise KeyError(f"none of {names} in the recorded candidate")


def main() -> None:
    if OUT_FILE.exists():
        raise SystemExit(f"{OUT_FILE.name} exists: the record is written once")
    started = time.process_time()
    from refute.packs.tess.calib05 import c2

    rows = tc.population()
    _, refs = c2.references(tc.ROOT)
    per = []
    for _, arg in rows:
        c = arg["expected_candidate"]
        period = _get(c, "period_days", "period")
        injected = refs[f"{arg['row']['key']}/injection/{arg['row']['slot']}"]["injection"]
        duration = float(injected["duration_hours"]) / 24.0
        status = (arg.get("expected_tests") or {}).get("secondary_eclipse")
        excl = True if status is None else status == "FAIL"
        n = geometric_phases(period, duration, excl)
        per.append({"key": arg["row"]["key"], "slot": arg["row"]["slot"],
                    "duration_over_period": duration / period, "secondary_eclipse": status,
                    "excludes_phase_half": excl, "geometric_phases": n})  # fmt: skip
    unk = sum(r["geometric_phases"] < tc.MIN_SHIFTS for r in per)
    runs = unk <= 20
    used = time.process_time() - started
    doc = {
        "label": "v0.5.5: T2a-E's geometry count from the recorded candidates' periods and the "
        "injected durations (a proxy), before it runs (development records; geometry is "
        "necessary, not sufficient)",
        "method_status": "not_validated",
        "decision": "the maintainer's decision of 2026-11-20 (night), item 4b (#218)",
        "injections": len(per),
        "unk_on_geometry": unk,
        "rule": "T2a-E does not run if more than 20 of the 102 would be UNK on geometry alone",
        "t2ae_runs": runs,
        "outcome_if_not_run": None if runs else "INCONCLUSIVE (futility: too many unknown)",
        "per_injection": per,
        "cpu_hours": round(used / 3600.0, 4),
    }
    OUT_FILE.write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n", "utf-8", newline="\n")
    lv.bind()
    lv.declare()
    lv.charge(f"t2ae_geometry_{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}", used / 3600.0,
              f"t2ae_geometry.py: process time {used:.1f} s")  # fmt: skip
    print(json.dumps({k: doc[k] for k in ("injections", "unk_on_geometry", "t2ae_runs")}))


if __name__ == "__main__":
    main()
