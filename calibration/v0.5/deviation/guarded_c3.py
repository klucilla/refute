"""``c3-fetch`` and ``c3-run`` behind the checks of the deviation approved on 2026-11-04 (#199;
calibration/v0.5/deviation/README.md).

The frozen C3 steps check the freeze and the budget decision, but read ``claim.yaml`` without
checking it against its lock. This wrapper runs, in order, and stops at the first failure
(exit 1, the frozen step is never started):

1. ``refute verify calibration/v0.5/claim.yaml`` (``refute.core.lock.verify_claim``): PASS only
   (the claim, every attachment and the code hash as locked);
2. the lock covers the C3 inputs the steps read: ``claim-targets.yaml``,
   ``selection/targets.yaml``, ``eb_catalog.csv`` and ``eb_catalog_scan.json``;
3. ``claim-targets.yaml`` is still exactly the projection of ``selection/targets.yaml`` (the
   C3 steps read the original; the dossiers read the projection);
4. the claim's test plan equals the plan ``c3-run`` rebuilds (``c3run.v05_plan`` of
   ``c3run.v04_plan_for``), so the dossiers and the paired runs analyse with the same parameters;
5. the TESS-EB edition is in the step's cache and the claim's catalog resolves from it, as
   ``c3-run`` loads it (``prepare_tess_eb.resolves``; place it first with ``prepare_tess_eb.py``).

Then the frozen step runs unchanged: ``run_calibration.py`` with the same arguments, in this
Python. Nothing here changes analysis code, a threshold, a test role, the selection or a frozen
input.

Run from the repository root:
``.venv/Scripts/python.exe calibration/v0.5/deviation/guarded_c3.py c3-fetch --cache <dir>``
``.venv/Scripts/python.exe calibration/v0.5/deviation/guarded_c3.py c3-run [--workers N]``
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import prepare_tess_eb  # noqa: E402 - the sibling script, by its path
import project_targets  # noqa: E402

STEP = Path("calibration/v0.5")
CLAIM = STEP / "claim.yaml"
LOCK = STEP / "claim.lock.json"
COVERED = ("claim-targets.yaml", "selection/targets.yaml", "eb_catalog.csv", "eb_catalog_scan.json")
FETCH_REPORT = Path(".cache/v05/calibration/c3-fetch.json")


class GuardError(Exception):
    """A check failed: the frozen step is not started."""


def check_lock(root: Path) -> list[str]:
    from refute.core.lock import verify_claim

    result = verify_claim(root / CLAIM)
    lines = [f"refute verify: {result.status.value}", *(f"  {m}" for m in result.messages)]
    if result.status.value != "PASS" or result.exit_code != 0:
        raise GuardError("\n".join(lines))
    lock = json.loads((root / LOCK).read_text(encoding="utf-8"))
    paths = {a["path"] for a in lock["attachments"]}
    missing = [p for p in COVERED if p not in paths]
    if missing:
        raise GuardError("the lock does not cover: " + ", ".join(missing))
    return lines


def check_projection(root: Path) -> None:
    original = (root / project_targets.SOURCE_TARGETS).read_text(encoding="utf-8")
    projected, _ = project_targets.project_targets(original)
    if (root / project_targets.OUT_TARGETS).read_text(encoding="utf-8") != projected:
        raise GuardError("claim-targets.yaml is not the projection of selection/targets.yaml")


def check_plan(root: Path) -> None:
    import yaml

    from refute.packs.tess.calib05 import c3run
    from refute.packs.tess.calib05.plans import v05_plan

    step = root / STEP
    claim = yaml.safe_load((root / CLAIM).read_text(encoding="utf-8"))
    inputs = json.loads((step / "inputs.json").read_text(encoding="utf-8"))
    rebuilt = v05_plan(c3run.v04_plan_for(root, inputs, step))
    if claim["test_plan"] != rebuilt:
        raise GuardError("the claim's test plan is not the plan c3-run rebuilds")


def check_catalog(root: Path, cache: Path) -> int:
    want = prepare_tess_eb.expected(root)
    dest = (root / cache).joinpath(*want["cache_path"].split("/"))
    if not dest.is_file() or prepare_tess_eb.sha256_file(dest) != want["sha256"]:
        raise GuardError(f"the TESS-EB edition is not in {dest}: run prepare_tess_eb.py first")
    return prepare_tess_eb.resolves(root, cache)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="step", required=True)
    fetch = sub.add_parser("c3-fetch")
    fetch.add_argument("--cache", required=True)
    run = sub.add_parser("c3-run")
    run.add_argument("--workers", type=int)
    args = parser.parse_args(argv)
    root = Path.cwd()
    for line in check_lock(root):
        print(line)
    check_projection(root)
    check_plan(root)
    if args.step == "c3-fetch":
        cache = Path(args.cache)
    else:
        cache = Path(json.loads((root / FETCH_REPORT).read_text(encoding="utf-8"))["cache"])
    rows = check_catalog(root, cache)
    print(f"checks passed; TESS-EB reference rows resolved: {rows}; running {args.step}")
    frozen = [sys.executable, str(root / STEP / "run_calibration.py"), *argv]
    return subprocess.run(frozen, cwd=root, check=False).returncode


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except (GuardError, prepare_tess_eb.PlacementError, project_targets.ProjectionError) as error:
        print(f"STOP: {error}", file=sys.stderr)
        sys.exit(1)
