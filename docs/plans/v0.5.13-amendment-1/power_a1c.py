"""Amendment 1, the corrected all-307 sensitivity check (Codex's round 1 on the amendment, blocking
item 2). The earlier runs (power_a1.py, power_a1b.py) are preserved unchanged.

The non-SB1 subgroup (135: NEB, BEB, EB1, EB2, SB2, Giant, Variable, RV0) at assumed conditional
survival 0.15, and the SB1 subgroup (172) at an assumed survival q; the common probability
(135 x 0.15 + 172 x q) / 307, at full precision, is passed to the unchanged frozen functions of
power_v2.py (through power_a1.joint) for both FP bands (153 and 154). A homogeneous planning
approximation with hypothetical band sizes; it establishes neither expected battery performance nor
infeasibility. Output: power-a1c.json.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("power_a1", HERE / "power_a1.py")
pa = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pa)


def main() -> int:
    rows = []
    for q in (0.15, 0.30, 0.50, 0.70):
        p = (135 * 0.15 + 172 * q) / 307
        r = pa.joint((153, 154), p)
        r.update({"assumed_non_sb1_survival": 0.15, "assumed_sb1_survival": q})
        rows.append(r)
    doc = {
        "schema": "refute-v0513-amendment1-power-1c",
        "mode": "exploratory",
        "method_status": "not_validated",
        "model": "135 non-SB1 at 0.15 and 172 SB1 at q; common probability at full precision; "
        "frozen power_v2 functions; FP bands 153/154; planet bands 85/86",
        "rows": rows,
    }
    (HERE / "power-a1c.json").write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8")
    print(json.dumps([(r["assumed_sb1_survival"], r["joint_pass"]) for r in rows]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
