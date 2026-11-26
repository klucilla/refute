"""Amendment 1 (item 6b), the power of the full AND rule recalculated with the frozen calculator.

It imports the functions of docs/plans/v0.5.13-charter-prep/power_v2.py unchanged (the frozen
script; no threshold is changed and X is not raised) and evaluates the AND rule of the charter's
section 5 under the same planning model (0.85 assessed, 0.90 planet retention), for:
- **A. the approved population:** all 307 FPs (bands 153 and 154), at a pooled FP survival that is
  the mixture of the measured population's survival and an assumed SB1-like survival (a planning
  assumption, not a result: no battery result on a KELT-FP target exists);
- **B. the amendment's measured population:** the 124 FPs of the photometrically refutable types
  (NEB 49, SB2 27, EB1 17, BEB 17, EB2 8, Giant 6; bands 62 and 62), at FP survival 0.10, 0.15
  and 0.20.
Output: power-a1.json next to this file.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
FROZEN = HERE.parent / "v0.5.13-charter-prep" / "power_v2.py"
_spec = importlib.util.spec_from_file_location("power_v2", FROZEN)
pv = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pv)

PL = (85, 86)


def joint(fp_bands: tuple[int, int], p_survive: float) -> dict:
    n_pl, n_fp = sum(PL), sum(fp_bands)
    pl = pv.arm_distribution(PL, pv.P_RETAIN, planets=True)
    fp = pv.arm_distribution(fp_bands, p_survive, planets=False)
    j = sum(
        qp * qf
        for ap, qp in pl.items()
        for af, qf in fp.items()
        if pv.symmetry_ok(n_pl - ap, n_pl, n_fp - af, n_fp)
    )
    return {
        "fp_bands": list(fp_bands),
        "p_survive": p_survive,
        "planet_arm_pass": round(sum(pl.values()), 6),
        "fp_arm_pass": round(sum(fp.values()), 6),
        "joint_pass": round(j, 6),
    }


def main() -> int:
    measured, sb1_like = 124, 183  # 307 = 124 + SB1 172 + RV0 5 + Variable 6
    rows_a = []
    for p_meas in (0.15,):
        for p_sb1 in (0.15, 0.30, 0.50, 0.70):
            mix = (measured * p_meas + sb1_like * p_sb1) / (measured + sb1_like)
            r = joint((153, 154), round(mix, 6))
            r.update({"assumed_measured_survival": p_meas, "assumed_sb1_like_survival": p_sb1})
            rows_a.append(r)
    rows_b = [joint((62, 62), p) for p in (0.10, 0.15, 0.20)]
    doc = {
        "schema": "refute-v0513-amendment1-power-1",
        "mode": "exploratory",
        "method_status": "not_validated",
        "frozen_calculator": "docs/plans/v0.5.13-charter-prep/power_v2.py (imported unchanged)",
        "rules": {
            "X": pv.X,
            "Y": pv.Y,
            "Z": pv.Z,
            "D": pv.D,
            "band_X": pv.XB,
            "band_Y": pv.YB,
            "band_Z": pv.ZB,
        },  # fmt: skip
        "planning_model": {"p_assess": pv.P_ASSESS, "p_retain": pv.P_RETAIN, "planet_bands": PL},
        "A_all_307_mixture": rows_a,
        "B_measured_124": rows_b,
    }
    (HERE / "power-a1.json").write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8")
    a = [(r["assumed_sb1_like_survival"], r["p_survive"], r["joint_pass"]) for r in rows_a]
    b = [(r["p_survive"], r["joint_pass"]) for r in rows_b]
    print(json.dumps({"A": a, "B": b}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
