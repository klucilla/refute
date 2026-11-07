"""The outputs of earlier claims' code paths, compared with the code of the v0.5.0 calibration
lock (v0.5.1 WP4 row 4.2, WP5 row 5.2 (a)).

Byte fixtures recorded on one machine do not travel: CI runs 42353283742 and 42356576130
(2026-11-07) showed floats differing in their last bits on Linux and on Python 3.12, and on other
machines the BLS search picking other refined peaks (periods differing in the fourth digit, a tie
broken at another event), even on windows-2025 / Python 3.13. So the comparison is differential,
on the machine that runs the test: ``outputs()`` computes every output with the ``refute`` it
imports; the test runs it once with the current code and once, in a subprocess, with the source of
the v0.5.0 calibration lock (``BASELINE``, extracted from git by ``git archive`` into a temporary
folder, no network), and the two must be equal byte for byte.

``outputs()``: the TESS plans of the v0.1 and v0.2 calibration claims (their canonical locked
forms), of the v0.4 and v0.5 claims (``calibration/v0.4/claim.yaml``,
``calibration/v0.5/claim.yaml``) and the synthetic v0.4 and v0.5 discover plans, each on the
synthetic scenario ``planet_three_years`` (``verdict.json``, ``report.md``, the error record,
``case.json`` for the discover claims); and the paired chain of the v0.5 calibration. The v0.3
claims are paper claims of the ML pack, which v0.5.1 does not change.

As a script (the subprocess): ``python -B baseline_code.py <folder holding src> <out folder>``.
"""

from __future__ import annotations

import inspect
import json
import os
import subprocess
import sys
import zipfile
from pathlib import Path

BASELINE = "b6249b500d8d7b98a6246dbe0d99a4c55363f1cb"  # v0.5: commit B, the lock of the C3 claim
REPO = Path(__file__).resolve().parents[1]
TARGET = {"key": "TIC-1", "tic_id": 1, "kind": "exploration", "name": "synthetic", "published": {}}


def _claim_plans() -> dict:
    import yaml

    canon = REPO / "tests" / "fixtures" / "locked_canonical"
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
        out[label] = yaml.safe_load((REPO / path).read_text(encoding="utf-8"))["test_plan"]
    return out


def outputs() -> dict[str, str]:
    """Every output, by file name, computed with the ``refute`` this process imports."""
    from refute.core.io import dumps_json
    from refute.packs.tess.discover.case import build_case
    from refute.packs.tess.discover.paired import paired_chain
    from refute.packs.tess.params import TessTestPlan
    from refute.packs.tess.pipeline import TessAnalyzer, analyze_data, build_result
    from refute.packs.tess.report import render_report
    from refute.packs.tess.synthetic import (
        discovery_plan_dict,
        discovery_v05_plan_dict,
        scenario_data,
    )

    takes_plan = "test_plan" in inspect.signature(TessAnalyzer.error_result).parameters
    plans = {
        **_claim_plans(),
        "syn-v04": discovery_plan_dict(),
        "syn-v05": discovery_v05_plan_dict(),
    }
    out: dict[str, str] = {}
    for label, plan_dict in plans.items():
        plan = TessTestPlan.model_validate(plan_dict)
        discover = plan.discovery is not None
        kind = "discover" if discover else "calibration"
        context = {"claim_id": f"synthetic-{label}", "claim_kind": kind, "hypothesis": "h"}
        data = scenario_data("planet_three_years")
        analysis = analyze_data(data, plan, stage=2 if discover else None)
        result = build_result(TARGET, data, plan, analysis, context)
        out[f"verdict-{label}.json"] = dumps_json(result)
        out[f"report-{label}.md"] = render_report(result, context)
        if discover:
            out[f"case-{label}.json"] = dumps_json(build_case(result, TARGET, None, None))
        extra = {"test_plan": plan_dict} if takes_plan else {}
        out[f"error-{label}.json"] = dumps_json(
            TessAnalyzer().error_result(TARGET, "boom", context, **extra)
        )
    p04 = TessTestPlan.model_validate(plans["v04"])
    p05 = TessTestPlan.model_validate(plans["v05"])
    chain = paired_chain(scenario_data("planet_three_years"), p04, p05, stage=2)
    out["paired-v04-v05.json"] = dumps_json(chain)
    return out


def baseline_available() -> bool:
    found = subprocess.run(
        ["git", "cat-file", "-e", f"{BASELINE}^{{commit}}"], cwd=REPO, capture_output=True
    )
    return found.returncode == 0


def baseline_outputs(work: Path) -> dict[str, str]:
    """``outputs()`` computed with the baseline's source, in a subprocess."""
    archive = work / "baseline-src.zip"
    subprocess.run(
        ["git", "archive", "--format=zip", "-o", str(archive), BASELINE, "src"],
        cwd=REPO,
        check=True,
    )
    tree = work / "baseline"
    with zipfile.ZipFile(archive) as z:
        z.extractall(tree)
    out = work / "outputs"
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    subprocess.run(
        [sys.executable, "-B", str(Path(__file__).resolve()), str(tree), str(out)],
        cwd=REPO,
        env=env,
        check=True,
    )
    return {p.name: p.read_bytes().decode("utf-8") for p in sorted(out.iterdir())}


def main(argv: list[str]) -> None:
    sys.dont_write_bytecode = True
    tree, out = Path(argv[0]).resolve(), Path(argv[1]).resolve()
    sys.path.insert(0, str(tree / "src"))
    import refute

    if not Path(refute.__file__).resolve().is_relative_to(tree):
        raise SystemExit(f"not the baseline's refute: {refute.__file__}")
    out.mkdir(parents=True, exist_ok=True)
    for name, text in outputs().items():
        (out / name).write_text(text, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main(sys.argv[1:])
