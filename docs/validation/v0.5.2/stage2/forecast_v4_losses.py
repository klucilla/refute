"""v0.5.2 stage 2: where D2's kept fraction goes, in the forecast with version 4 (the maintainer's
decision of 2026-11-10, #216, item 1: how much of each loss comes from each rule). Reads the
forecast's records (``forecast_v4.py``; no curve is run again). For every eligible planet kept by
the v0.4 battery and not by version 4 (or by version 3), every decisive test that is not PASS is
listed with its INCONCLUSIVE class, the sector selection's refusal and the sinusoid's status: the
blockers overlap, so they are counted, not apportioned. It decides nothing.
``method_status: not_validated``.

Usage: ``.venv/Scripts/python.exe <this file>``; writes ``forecast-v4-losses.json``.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import budgeted  # noqa: E402
import forecast_v4 as f  # noqa: E402

KEPT = ("SURVIVED", "WEAKENED")


def main() -> None:
    from refute.packs.tess.pipeline import expected_by_role

    fp = f.fingerprint()
    data = budgeted.assembled(
        f.SECTION, f.PART, f.OUT / fp, f.shard, f.shards(), fp, f.WORKERS, pin=f.PIN,
        max_shard_seconds=f.MAX_SHARD_SECONDS,
    )  # fmt: skip
    recs = [json.loads(x) for x in data.decode().splitlines() if x.strip()]
    eligible = [r for r in recs if r.get("status") == "OK" and r["gate_passed"] and r["identity"]]
    _, p3, p4 = f.plans()
    out: dict = {
        "label": "where D2's kept fraction goes with version 4; it decides nothing",
        "method_status": "not_validated",
        "eligible": len(eligible),
    }
    for name, plan in (("v3", p3), ("v4", p4)):
        decisive, _ = expected_by_role(plan, False)
        blockers: Counter = Counter()
        sole: Counter = Counter()
        lost = 0
        for r in eligible:
            if r["v04"] not in KEPT or r[name] in KEPT:
                continue
            lost += 1
            tests = r[f"{name}_tests"]
            bad = []
            for t in sorted(decisive):
                row = tests.get(t, {})
                if row.get("status") in ("FAIL", "INCONCLUSIVE"):
                    label = f"{t} {row['status']}"
                    if row.get("class"):
                        label += f" ({row['class']})"
                    if row.get("refused"):
                        label += f" [refused: {row['refused']}]"
                    bad.append(label)
            for b in bad:
                blockers[b] += 1
            if len(bad) == 1:
                sole[bad[0]] += 1
        out[name] = {
            "verdict": r"kept by v0.4, not by this battery",
            "lost": lost,
            "blockers_overlapping": dict(blockers.most_common()),
            "sole_blocker": dict(sole.most_common()),
        }
    (HERE / "forecast-v4-losses.json").write_text(
        json.dumps(out, indent=1, sort_keys=True) + "\n", "utf-8"
    )
    print(json.dumps(out, indent=1, sort_keys=True))


if __name__ == "__main__":
    main()
