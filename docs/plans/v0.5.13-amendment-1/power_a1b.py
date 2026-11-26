"""Amendment 1 (item 6b), a second planning run: the measured population with RV0 and Variable
kept in it (135 FPs = 124 + RV0 5 + Variable 6; bands 67 and 68), the more conservative choice
than leaving them apart. Same frozen calculator (power_v2.py, imported unchanged through
power_a1.py's helper), same planning model, X not raised. Output: power-a1b.json.
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
    rows = [pa.joint((67, 68), p) for p in (0.10, 0.15, 0.20)]
    doc = {
        "schema": "refute-v0513-amendment1-power-1b",
        "mode": "exploratory",
        "method_status": "not_validated",
        "measured_population": "135 = NEB 49 + SB2 27 + EB1 17 + BEB 17 + EB2 8 + Giant 6 + "
        "RV0 5 + Variable 6",
        "rows": rows,
    }
    (HERE / "power-a1b.json").write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8")
    print(json.dumps([(r["p_survive"], r["fp_arm_pass"], r["joint_pass"]) for r in rows]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
