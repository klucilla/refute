"""v0.5.11 (battery version 5), proof (i) of the charter's section 2.3: versions 1 to 4 must give
the same bytes after the `src/` change as at its parent.

Byte fixtures do not travel between machines (tests/baseline_code.py says why), so the golden
snapshot is differential, on the machine that runs the test:
- ``outputs()`` computes every output with the ``refute`` this process imports;
- the test runs it once with the current code, and once in a subprocess with the source of
  ``BASELINE``, the charter's commit, whose ``src/`` is the parent of the `src/` change;
- the two must be equal byte for byte.

**The outputs.** The synthetic plans of discovery versions 1 to 4 on the scenario
``planet_three_years``, plus version 2 on ``eb_odd_even``. Each goes through the four entry
points of the specification (docs/plans/v0.5.11-spec.md, section 2):
- ``analyze_data``, then ``build_result``: ``verdict.json``;
- ``discover.measure.chain``, at stage 1;
- ``TessAnalyzer.error_result``, with the plan;
- the rendered report.

An exception is recorded as its type and message, so failure behavior is compared too.

As a script (the subprocess): ``python -B baseline_code_v0511.py <folder holding src> <out>``.
"""

from __future__ import annotations

import os
import subprocess
import sys
import zipfile
from pathlib import Path

BASELINE = "eb70c13e04e910bb9cbd547c85c488a58ef9f0a4"  # the v0.5.11 charter (src as at the parent)
REPO = Path(__file__).resolve().parents[1]
TARGET = {"key": "TIC-1", "tic_id": 1, "kind": "exploration", "name": "synthetic", "published": {}}


def _guard(fn):
    try:
        return fn()
    except Exception as exc:  # noqa: BLE001 - the failure itself is an output to compare
        return f"ERROR {type(exc).__name__}: {exc}\n"


def outputs() -> dict[str, str]:
    """Every output, computed with the current source in a fresh subprocess, like the baseline's.

    CI run 45514526728 (2026-11-25) showed version 3's floats differing in their last digits
    between an in-process computation after thousands of other tests and a fresh subprocess, on
    the same machine and code. So both sides are computed in fresh subprocesses, in the same
    environment."""
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        return _subprocess_outputs(REPO, Path(tmp) / "outputs")


def _compute() -> dict[str, str]:
    """Every output, by name, computed with the ``refute`` this process imports."""
    from refute.core.io import dumps_json
    from refute.packs.tess.discover.measure import chain
    from refute.packs.tess.params import TessTestPlan
    from refute.packs.tess.pipeline import TessAnalyzer, analyze_data, build_result
    from refute.packs.tess.report import render_report
    from refute.packs.tess.synthetic import (
        discovery_plan_dict,
        discovery_v05_plan_dict,
        discovery_v051_plan_dict,
        discovery_v052_plan_dict,
        scenario_data,
    )

    cases = [
        ("v1", discovery_plan_dict(), "planet_three_years"),
        ("v2", discovery_v05_plan_dict(), "planet_three_years"),
        ("v3", discovery_v051_plan_dict(), "planet_three_years"),
        ("v4", discovery_v052_plan_dict(), "planet_three_years"),
        ("v2-eb", discovery_v05_plan_dict(), "eb_odd_even"),
    ]
    out: dict[str, str] = {}
    for label, plan_dict, scenario in cases:
        context = {"claim_id": f"synthetic-{label}", "claim_kind": "discover", "hypothesis": "h"}

        def verdict(plan_dict=plan_dict, scenario=scenario, context=context):
            plan = TessTestPlan.model_validate(plan_dict)
            data = scenario_data(scenario)
            analysis = analyze_data(data, plan, stage=2)
            result = build_result(TARGET, data, plan, analysis, context)
            return dumps_json(result) + "\n---report---\n" + render_report(result, context)

        def measured(plan_dict=plan_dict, scenario=scenario):
            plan = TessTestPlan.model_validate(plan_dict)
            return dumps_json(chain(scenario_data(scenario), plan, 1))

        def error(plan_dict=plan_dict, context=context):
            return dumps_json(
                TessAnalyzer().error_result(TARGET, "boom", context, test_plan=plan_dict)
            )

        def dumped(plan_dict=plan_dict):
            return dumps_json(TessTestPlan.model_validate(plan_dict).model_dump(mode="json"))

        out[f"verdict-{label}.txt"] = _guard(verdict)
        out[f"chain-{label}.json"] = _guard(measured)
        out[f"error-{label}.json"] = _guard(error)
        out[f"plan-{label}.json"] = _guard(dumped)
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
    return _subprocess_outputs(tree, work / "outputs")


def _subprocess_outputs(tree: Path, out: Path) -> dict[str, str]:
    """``_compute()`` in a fresh subprocess with the source under ``tree``."""
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
    for name, text in _compute().items():
        (out / name).write_text(text, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main(sys.argv[1:])
