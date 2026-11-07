"""Record the v0.4 and v0.5 outputs of the code before WP4 (a worktree at 6f8d805) as the byte
fixtures of WP4 row 4.2. Usage: python make_wp4_fixtures.py <worktree> <out dir>."""

import sys
from pathlib import Path

worktree, out = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
sys.path.insert(0, str(worktree / "src"))

import refute  # noqa: E402

assert Path(refute.__file__).resolve().is_relative_to(worktree), refute.__file__

from refute.core.io import dumps_json  # noqa: E402
from refute.packs.tess.discover.case import build_case  # noqa: E402
from refute.packs.tess.params import TessTestPlan  # noqa: E402
from refute.packs.tess.pipeline import TessAnalyzer, analyze_data, build_result  # noqa: E402
from refute.packs.tess.report import render_report  # noqa: E402
from refute.packs.tess.synthetic import (  # noqa: E402
    discovery_plan_dict,
    discovery_v05_plan_dict,
    scenario_data,
)

TARGET = {"key": "TIC-1", "tic_id": 1, "kind": "exploration", "name": "synthetic", "published": {}}
CONTEXT = {"claim_id": "synthetic", "claim_kind": "discover", "hypothesis": "h"}

out.mkdir(parents=True, exist_ok=True)
for label, plan_dict in (("v04", discovery_plan_dict()), ("v05", discovery_v05_plan_dict())):
    data = scenario_data("planet_three_years")
    plan = TessTestPlan.model_validate(plan_dict)
    analysis = analyze_data(data, plan, stage=2)
    result = build_result(TARGET, data, plan, analysis, CONTEXT)
    (out / f"verdict-{label}.json").write_text(dumps_json(result), encoding="utf-8", newline="\n")
    (out / f"report-{label}.md").write_text(
        render_report(result, CONTEXT), encoding="utf-8", newline="\n"
    )
    case = build_case(result, TARGET, None, None)
    (out / f"case-{label}.json").write_text(dumps_json(case), encoding="utf-8", newline="\n")
error = TessAnalyzer().error_result(TARGET, "boom", CONTEXT)
(out / "error-v05.json").write_text(dumps_json(error), encoding="utf-8", newline="\n")
print("written", sorted(p.name for p in out.iterdir()))
