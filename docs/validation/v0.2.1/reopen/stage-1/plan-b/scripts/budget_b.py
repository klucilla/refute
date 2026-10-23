"""The consolidated plan's budget up to X7 (plan-b/README.md; the maintainer's decisions of
2026-10-23 on proposal B): logical-processor hours (LP-h) and wall time on 22 workers, cumulative,
the earlier consumption included, every step at its ceiling (1.5 times its estimate) and at its
planning (minimum) size, the new generator's development and validation, the real controls'
availability check, the local suites and the mandatory checks included. It is **not** the budget
of the complete phase: the real calibration of gate 13 has its own budget, and the statistically
necessary sizes may exceed these floors. Planning arithmetic only: every unit cost is a
measurement of another run, named, and the highest one is used where the final configuration's is
unknown.

  python budget_b.py <out.json>
"""

import glob
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

CEIL = 1.5
WORKERS = 22
LP_MAX = 4000.0
WALL_MAX = 200.0
UNIT_DIAG = 61.578  # LP-s per curve, X2's variability cells (the calibration measurement)
UNIT_FULL_OLD = 30766.3 * 24 / 41600  # development campaign 1: the whole analysis, pre-M4
GEN_LP_H_PER_5200 = 335.3 * 24 / 3600  # one generation of the 5200-case dev population
SUITE_WALL_H = 2453.391 / 3600  # one full suite (JUnit, 2026-10-22), processors 8 to 31
SUITE_LP = 24
ROUNDS_AHEAD = 20  # planned rounds to X7, one full suite each before its push (section 6)

# B2, per noise model: planets 3 bands x 360; false positives 100 + 100 + 250; no transit
B2 = {"white": 3 * 360 + 450 + 2200, "correlated": 3 * 360 + 450 + 600}
B2_CURVES = sum(B2.values())


def suites_so_far(root: Path) -> float:
    total = 0.0
    for path in glob.glob(str(root / ".cache" / "**" / "junit*.xml"), recursive=True):
        try:
            r = ET.parse(path).getroot()
        except ET.ParseError:
            continue
        s = r if r.tag == "testsuite" else next(iter(r), None)
        if s is not None and s.get("time"):
            total += float(s.get("time"))
    return total / 3600


def step(name: str, curves: float, unit: float, note: str) -> dict:
    est = curves * unit / 3600
    return {
        "step": name,
        "curves": curves,
        "unit_lp_s": unit,
        "estimate_lp_h": est,
        "ceiling_lp_h": est * CEIL,
        "ceiling_wall_h": est * CEIL / WORKERS,
        "note": note,
    }


def main() -> int:
    root = Path(__file__).resolve().parents[7]
    suites_h = suites_so_far(root)
    consumed = {
        "lots_lp_h": 386.2,
        "lots_wall_h": 51.2,
        "suites_kept_wall_h": suites_h,
        "suites_kept_lp_h_proxy": suites_h * SUITE_LP,
    }
    gen_cases = 4 * B2_CURVES  # the pilot, the main study, the reserve, the confirmation lot
    gen_lp = 3 * gen_cases / 5200 * GEN_LP_H_PER_5200  # three generations each (determinism)
    steps = [
        {
            "step": "new generator: development and validation",
            "ceiling_lp_h": CEIL * (gen_lp + 20.0),
            "ceiling_wall_h": CEIL * (gen_lp + 20.0) / 24,
            "note": (
                "3 generations of 4 populations at the dev population's measured cost; "
                "20 LP-h of self-tests, an allowance"
            ),
        },
        {
            "step": "the real controls' availability check (catalogues and metadata only)",
            "ceiling_lp_h": 0.0,
            "ceiling_wall_h": 2.0,
            "note": "queries only, no light curve analysed; a wall-time allowance",
        },
        {
            "step": "X2f S1 + S2 (declared ceilings 3.25 + 10.50 h)",
            "ceiling_lp_h": (3.25 + 10.50) * WORKERS,
            "ceiling_wall_h": 3.25 + 10.50,
            "note": "x2f-declaration.md, S3 removed",
        },
        {
            "step": "spec C's confirmation (as S1 + S2, on the new population)",
            "ceiling_lp_h": (3.25 + 10.50) * WORKERS,
            "ceiling_wall_h": 3.25 + 10.50,
            "note": "the same sizes and cost as the choice",
        },
        step(
            "X3 on three-year curves",
            1300,
            UNIT_DIAG,
            "a planning assumption; its declaration sizes it",
        ),
        step(
            "X5 pilot (the complete engine; the development population)",
            1500,
            UNIT_DIAG,
            "a planning size; its declaration sizes it",
        ),
        step(
            "before-and-after comparisons of each change on X5's development inputs (2)",
            2 * 1500,
            UNIT_DIAG,
            "the ROADMAP's measurement before and after each change (spec C's model, X3's b, s)",
        ),
        step(
            "X6 main study, B2 floor (the complete engine)",
            B2_CURVES,
            UNIT_DIAG,
            "the holdout criteria's sizes come from X5",
        ),
        step(
            "X7 reserve, as X6's floor",
            B2_CURVES,
            UNIT_DIAG,
            "the same composition and sizes as X6",
        ),
        {
            "step": f"local full suites and mandatory checks ahead ({ROUNDS_AHEAD} rounds)",
            "ceiling_lp_h": CEIL * ROUNDS_AHEAD * SUITE_WALL_H * SUITE_LP,
            "ceiling_wall_h": CEIL * ROUNDS_AHEAD * SUITE_WALL_H,
            "note": "24 processors x the suite's wall time (a proxy, not measured CPU), 1.5 times",
        },
    ]
    lp = (
        consumed["lots_lp_h"]
        + consumed["suites_kept_lp_h_proxy"]
        + sum(s["ceiling_lp_h"] for s in steps)
    )
    wall = (
        consumed["lots_wall_h"]
        + consumed["suites_kept_wall_h"]
        + sum(s["ceiling_wall_h"] for s in steps)
    )
    out = {
        "note": __doc__.split("\n\n")[0],
        "unit_costs_lp_s_per_curve": {
            "x2_diagnostic": UNIT_DIAG,
            "dev_campaign_1_complete_analysis_pre_m4": UNIT_FULL_OLD,
        },
        "b2_curves_per_study": B2,
        "consumed": consumed,
        "steps": steps,
        "total_lp_h_at_ceilings": lp,
        "total_wall_h_at_ceilings": wall,
        "left_of_4000_lp_h": LP_MAX - lp,
        "left_of_200_h": WALL_MAX - wall,
        "left_for_x6_beyond_its_floor_wall_h": WALL_MAX - wall,
    }
    Path(sys.argv[1]).write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8", newline="\n")
    for s in steps:
        print(f"{s['step']}: {s['ceiling_lp_h']:.1f} LP-h, {s['ceiling_wall_h']:.2f} h")
    print("consumed", {k: round(v, 2) for k, v in consumed.items()})
    print(f"total at ceilings {lp:.1f} LP-h, {wall:.1f} h")
    print(f"left {LP_MAX - lp:.1f} LP-h, {WALL_MAX - wall:.1f} h")
    print("unit costs", out["unit_costs_lp_s_per_curve"], "B2", B2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
