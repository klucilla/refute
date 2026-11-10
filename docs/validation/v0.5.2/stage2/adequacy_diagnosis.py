"""v0.5.2 stage 2: a read-only diagnosis of the failed adequacy check (design, section 1).

The frozen check failed with no member and no aggregate outside its tolerances, and every one of
the 200 datasets with members not measured. This script compares, member by member, the number
of curves that carry the member (G) under version 3 (the sizing reference) and version 4 (the
rebuilt reference). The draw scales each run by ``target / min_g`` with version 3's ``min_g``
(the schedule kept frozen from version 3, as the design says), so a member whose version 4 G is
below ``0.95 * min_g`` falls below ``G_min`` in every dataset. It decides nothing, changes no
result and certifies nothing. ``method_status: not_validated``.

Usage: ``.venv/Scripts/python.exe docs/validation/v0.5.2/stage2/adequacy_diagnosis.py``; writes
``adequacy-diagnosis.json``.
"""

from __future__ import annotations

import json
import pickle
from collections import Counter
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
V3 = ROOT / ".cache/v052/s2/plasmode/components.pkl"
V4 = ROOT / ".cache/v052/s2/adequacy/components-v4.pkl"
EVAL = ROOT / ".cache/v052/s2/adequacy/evaluate"
FRACTION = 0.95  # G_min = 0.95 T


def g_of(comp) -> np.ndarray:
    return sum((r["n"] > 0).sum(axis=0) for r in comp["runs"])


def main() -> None:
    v3 = pickle.loads(V3.read_bytes())  # noqa: S301 - local cache, written by plasmode.py
    v4 = pickle.loads(V4.read_bytes())  # noqa: S301 - local cache, written by adequacy.py
    rows = []
    for c3, c4 in zip(v3, v4, strict=True):
        if c3["members"] != c4["members"]:
            raise SystemExit("the two references do not share the family")
        g3, g4 = g_of(c3), g_of(c4)
        for j, m in enumerate(c4["members"]):
            rows.append(
                {
                    "member": repr(m),
                    "section": m[0],
                    "g3": int(g3[j]),
                    "g4": int(g4[j]),
                    "min_g": int(c4["min_g"]),
                    "ratio_v4": float(g4[j] / c4["min_g"]),
                }
            )
    below = [r for r in rows if r["ratio_v4"] < FRACTION]
    near = [r for r in rows if FRACTION <= r["ratio_v4"] < FRACTION + 0.02]
    lost = [r for r in rows if r["g4"] < r["g3"]]
    per_dataset = []
    for path in sorted(EVAL.rglob("*.bin")):
        per_dataset.append(json.loads(path.read_bytes().decode().strip())["not_measured"])
    ratios = np.array([r["ratio_v4"] for r in rows])
    doc = {
        "label": "why the adequacy check found members not measured; it decides nothing",
        "method_status": "not_validated",
        "members": len(rows),
        "members_with_fewer_curves_in_version_4": len(lost),
        "members_with_fewer_curves_by_section": dict(
            sorted(Counter(r["section"] for r in lost).items())
        ),
        "members_below_g_min_in_every_dataset": len(below),
        "members_below_by_section": dict(sorted(Counter(r["section"] for r in below).items())),
        "members_within_0_02_above_the_fraction": len(near),
        "smallest_ratio_v4": float(ratios.min()),
        "factor_on_the_schedule_that_reaches_the_fraction_for_every_member": float(
            FRACTION / ratios.min()
        ),
        "worst_25": sorted(below, key=lambda r: r["ratio_v4"])[:25],
        "not_measured_per_dataset": {
            "datasets": len(per_dataset),
            "min": min(per_dataset),
            "max": max(per_dataset),
        },
    }
    (HERE / "adequacy-diagnosis.json").write_text(
        json.dumps(doc, indent=1, sort_keys=True) + "\n", "utf-8"
    )
    print(json.dumps({k: v for k, v in doc.items() if k != "worst_25"}, indent=1), flush=True)


if __name__ == "__main__":
    main()
