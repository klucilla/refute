"""v0.2.1 synthetic population study harness, version 3: the frozen version 2 measuring a
configuration of the M4 corrections (docs/validation/v0.2.1/reopen/m4-implementation-map.md,
Amendment 17; the maintainer's decision of 2026-10-18 on the explicit activation).

Version 2 (``population_v2.py``, SHA-256 pinned below) is never edited: it builds its plan with
``_plan()`` from ``FAST_PLAN`` (the fast search only), so it measures the M3 path. This file loads
version 2 as a module, checks its bytes, and replaces in it only:

- ``_plan()``: ``FAST_PLAN`` plus the corrections block of the **configuration file** named by the
  environment variable ``REFUTE_M4_CONFIGURATION`` (``refute-m4-configuration/1``: a name and a
  ``corrections`` block with ``version`` 2 and ``enabled`` true, checked when loaded);
- ``analyze_task``: the same function, defined in this module, so that the spawned workers import
  this module (and so apply the same replacement, with the same configuration, which they inherit
  through the environment) before analyzing; each analysis checks that its plan carries the
  configuration's block;
- the harness identity: ``HARNESS_PATH`` and ``HARNESS_SHA256`` become this file's, so a campaign
  declaration names version 3, and the records' ``origin.harness_sha256`` is this file;
- R2 (``harness_problems``): this file, version 2 and the configuration file must each be the file
  of HEAD, and unchanged since the process started.

The configuration of a case is in its scientific record (``test_plan.gauntlet.corrections``) and
the parts of M4 that ran are in its ``corrections`` marker. Run as version 2 is run, with this file
in its place: ``.venv/Scripts/python.exe docs/validation/v0.2.1/population/population_v3.py <mode>
...``.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
V3_PATH = Path(__file__).resolve()
V3_BYTES = V3_PATH.read_bytes()
V3_SHA256 = hashlib.sha256(V3_BYTES).hexdigest()
V2_PATH = HERE / "population_v2.py"
# The frozen version 2 (its last commit 37c92c9617fb4077b7ec6f3c31c0972193ff0702).
V2_SHA256 = "8b3b6ad6aca6e713636b04e40db5a7d253c05458c8b143c38d984100072c1f82"
CONFIGURATION_ENV = "REFUTE_M4_CONFIGURATION"
CONFIGURATION_FORMAT = "refute-m4-configuration/1"


def _load_v2():
    if hashlib.sha256(V2_PATH.read_bytes()).hexdigest() != V2_SHA256:
        raise SystemExit("population_v2.py is not the frozen version 2 (SHA-256)")
    if "population_v2" in sys.modules:
        return sys.modules["population_v2"]
    spec = importlib.util.spec_from_file_location("population_v2", V2_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules["population_v2"] = module
    spec.loader.exec_module(module)
    return module


pv2 = _load_v2()


def load_configuration(path: str | os.PathLike | None = None) -> tuple[dict, str, Path]:
    """The configuration file (its content, its SHA-256 and its path); refused unless it is
    ``refute-m4-configuration/1`` with a corrections block of version 2 and enabled true."""
    path = Path(path or os.environ.get(CONFIGURATION_ENV) or "")
    if not path.is_file():
        raise SystemExit(f"{CONFIGURATION_ENV} must name an M4 configuration file")
    data = path.read_bytes()
    config = json.loads(data)
    block = config.get("corrections") or {}
    if config.get("format") != CONFIGURATION_FORMAT or not config.get("name"):
        raise SystemExit(f"{path}: not a {CONFIGURATION_FORMAT} file with a name")
    if block.get("version") != 2 or block.get("enabled") is not True:
        raise SystemExit(f"{path}: the corrections block must have version 2 and enabled true")
    return config, hashlib.sha256(data).hexdigest(), path.resolve()


CONFIGURATION, CONFIGURATION_SHA256, CONFIGURATION_PATH = load_configuration()
CONFIGURATION_AT_START = CONFIGURATION_PATH.read_bytes()


def _plan():
    from refute.packs.tess.params import TessTestPlan

    plan = json.loads(json.dumps(pv2.FAST_PLAN))
    plan.setdefault("gauntlet", {})["corrections"] = dict(CONFIGURATION["corrections"])
    resolved = TessTestPlan.model_validate(plan)
    if not resolved.gauntlet.corrections.active:
        raise RuntimeError("the configuration does not activate M4")
    return resolved


_V2_ANALYZE_TASK = pv2.analyze_task


def analyze_task(task):
    """Version 2's ``analyze_task``, defined here so that a spawned worker imports this module
    (and its replacements) first; the plan is checked against the configuration's block."""
    want = dict(CONFIGURATION["corrections"])
    got = pv2._plan().gauntlet.corrections.model_dump(mode="json")
    if {k: got.get(k) for k in want} != want:
        raise RuntimeError("the plan of this process does not carry the configuration's block")
    return _V2_ANALYZE_TASK(task)


def harness_problems() -> tuple[str, list[str]]:
    """R2 for version 3: this file, version 2 and the configuration file are each the file of
    HEAD and unchanged since the process started; then version 2's own checks of the comparator."""
    head = pv2.git(V3_PATH.parent, "rev-parse", "HEAD")
    problems = pv2.committed_problems(V3_PATH, V3_SHA256)
    problems += pv2.committed_problems(V2_PATH, V2_SHA256)
    problems += pv2.committed_problems(CONFIGURATION_PATH, CONFIGURATION_SHA256)
    if pv2.file_sha256(V3_PATH) != V3_SHA256:
        problems.append("the harness (version 3) changed on disk after this process started")
    if pv2.file_sha256(V2_PATH) != V2_SHA256:
        problems.append("population_v2.py changed on disk after this process started")
    if CONFIGURATION_PATH.read_bytes() != CONFIGURATION_AT_START:
        problems.append("the configuration file changed on disk after this process started")
    problems += pv2.committed_problems(pv2.COMPARATOR_PATH, pv2.COMPARATOR_SHA256_AT_START)
    if pv2.file_sha256(pv2.COMPARATOR_PATH) != pv2.COMPARATOR_SHA256_AT_START:
        problems.append("the comparator file changed on disk after this process started")
    if pv2.CMP.COMPARATOR_SHA256 != pv2.COMPARATOR_SHA256_AT_START:
        problems.append("the comparator module loaded is not the file read at start")
    return head, problems


def install() -> None:
    """Apply the replacements to the loaded version 2 (idempotent)."""
    pv2._plan = _plan
    pv2.analyze_task = analyze_task
    pv2.harness_problems = harness_problems
    pv2.HARNESS_PATH = V3_PATH
    pv2.HARNESS_SHA256 = V3_SHA256


install()


def main(argv: list[str] | None = None) -> int:
    return pv2.main(argv)


if __name__ == "__main__":
    # Run through the importable module, so that pickled functions name ``population_v3``.
    sys.path.insert(0, str(HERE))
    import population_v3

    raise SystemExit(population_v3.main())
