"""Record the outputs of the code of the v0.5.0 calibration lock (b6249b5) for the TESS plans of
the earlier claims, as the byte fixtures of v0.5.1 WP5 row 5.2 (a).

Usage (from the project root, with the project's environment; the worktree is only read, and no
bytecode is written into it):

    .venv/Scripts/python.exe -B tests/fixtures/v051_wp5/make_fixtures.py <worktree at b6249b5> \
        tests/fixtures/v051_wp5

The plans: the v0.1 and v0.2 calibration claims (their canonical locked forms,
tests/fixtures/locked_canonical), the v0.4 claim (calibration/v0.4/claim.yaml) and the v0.5 claim
(calibration/v0.5/claim.yaml), each on the synthetic scenario ``planet_three_years``; and the
paired chain of the v0.5 calibration (the v0.4 and v0.5 plans on one candidate). The v0.3 claims
are paper claims of the ML pack, whose code v0.5.1 does not change.
"""

import json
import sys

sys.dont_write_bytecode = True

from pathlib import Path  # noqa: E402

worktree, out = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
repo = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(worktree / "src"))

import yaml  # noqa: E402

import refute  # noqa: E402

assert Path(refute.__file__).resolve().is_relative_to(worktree), refute.__file__

from refute.core.io import dumps_json  # noqa: E402
from refute.packs.tess.discover.paired import paired_chain  # noqa: E402
from refute.packs.tess.params import TessTestPlan  # noqa: E402
from refute.packs.tess.pipeline import TessAnalyzer, analyze_data, build_result  # noqa: E402
from refute.packs.tess.report import render_report  # noqa: E402
from refute.packs.tess.synthetic import scenario_data  # noqa: E402

TARGET = {"key": "TIC-1", "tic_id": 1, "kind": "exploration", "name": "synthetic", "published": {}}


def plans() -> dict:
    canon = repo / "tests" / "fixtures" / "locked_canonical"
    out = {}
    for label, name in (
        ("v01", "tess-calibration-v0.1.json"),
        ("v02", "tess-calibration-v0.2.json"),
    ):
        out[label] = json.loads((canon / name).read_text(encoding="utf-8"))["canonical"][
            "test_plan"
        ]
    for label, path in (
        ("v04", "calibration/v0.4/claim.yaml"),
        ("v05", "calibration/v0.5/claim.yaml"),
    ):
        out[label] = yaml.safe_load((repo / path).read_text(encoding="utf-8"))["test_plan"]
    return out


def write(name: str, text: str) -> None:
    (out / name).write_text(text, encoding="utf-8", newline="\n")


def main() -> None:
    out.mkdir(parents=True, exist_ok=True)
    every = plans()
    for label, plan_dict in every.items():
        plan = TessTestPlan.model_validate(plan_dict)
        discover = plan.discovery is not None
        context = {
            "claim_id": f"synthetic-{label}",
            "claim_kind": "discover" if discover else "calibration",
            "hypothesis": "h",
        }
        data = scenario_data("planet_three_years")
        analysis = analyze_data(data, plan, stage=2 if discover else None)
        result = build_result(TARGET, data, plan, analysis, context)
        write(f"verdict-{label}.json", dumps_json(result))
        write(f"report-{label}.md", render_report(result, context))
        error = TessAnalyzer().error_result(TARGET, "boom", context)
        write(f"error-{label}.json", dumps_json(error))
    p04 = TessTestPlan.model_validate(every["v04"])
    p05 = TessTestPlan.model_validate(every["v05"])
    chain = paired_chain(scenario_data("planet_three_years"), p04, p05, stage=2)
    write("paired-v04-v05.json", dumps_json(chain))
    print("written", sorted(p.name for p in out.iterdir() if p.suffix in (".json", ".md")))


if __name__ == "__main__":
    main()
