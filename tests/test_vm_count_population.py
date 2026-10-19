"""scripts/vm/count_population.py, offline: the count phase is bound to the spec its build
used (end-of-round review of 2026-10-18); a spec changed between the two phases is refused
before any container runs. The real run is on the VM."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

VM = Path(__file__).resolve().parents[1] / "scripts" / "vm"


def load():
    # no bytecode written under scripts/vm (tests/test_vm_scripts.py keeps that folder to
    # its ASCII sources): neither for this module nor for measure_paper, which it imports
    sys.path.insert(0, str(VM))
    writes = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec = importlib.util.spec_from_file_location(
            "count_population", VM / "count_population.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        sys.dont_write_bytecode = writes
        sys.path.remove(str(VM))
        sys.modules.pop("measure_paper", None)


SPEC = {
    "name": "pgc",
    "repo_url": "https://example.invalid/r.git",
    "commit": "a" * 40,
    "python": "3.10",
    "base_image": "python@sha256:" + "b" * 64,
    "exclude_newer": "2023-07-25",
    "patches": [{"attachment": "p.patch", "path": "/x/p.patch", "sha256": "c" * 64}],
    "data": {},
    "dataset": "d",
    "split": "s",
    "script": {"path": "/x/count.py", "sha256": "d" * 64},
    "configuration": [],
    "active_minutes": 1,
}


@pytest.mark.parametrize(
    "change",
    [
        {"commit": "f" * 40},
        {"base_image": "python@sha256:" + "e" * 64},
        {"patches": []},
        {"python": "3.11"},
        {"exclude_newer": "2023-07-26"},
    ],
)
def test_a_spec_changed_after_the_build_is_refused(tmp_path, change):
    module = load()
    built = {"exit_code": 0, "lock_sha256": "1" * 64, "pyvenv_sha256": "2" * 64, "spec": SPEC}
    (tmp_path / "build.json").write_text(json.dumps(built), encoding="utf-8")
    with pytest.raises(SystemExit, match="differs from the build"):
        module.count({**SPEC, **change}, tmp_path)
