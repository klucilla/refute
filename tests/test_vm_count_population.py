"""scripts/vm/count_population.py, offline: the count phase is bound to the spec its build
used (end-of-round review of 2026-10-18); a spec changed between the two phases is refused
before any container runs. The real run is on the VM."""

from __future__ import annotations

import hashlib
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


# ---- weights that are a file of the commit (wp3-repository-weights-acceptance.md) -------------

CKPT = b"a frozen predictor" * 32


def _clone(tmp_path):
    from conftest import git

    clone = tmp_path / "clone"
    (clone / "saved").mkdir(parents=True)
    git(clone, "init", "-q")
    (clone / "saved" / "m.pth").write_bytes(CKPT)
    (clone / "train.py").write_text("print(1)\n", encoding="utf-8")
    git(clone, "add", "-A")
    git(clone, "commit", "-q", "-m", "c")
    return git(clone, "rev-parse", "HEAD").strip()


def _weights_spec(commit, listed=True, data=CKPT):
    digest = hashlib.sha256(data).hexdigest()
    entry = {"path": "saved/m.pth", "sha256": digest}
    return {
        **SPEC,
        "commit": commit,
        "configuration": [entry] if listed else [],
        "weights": [{**entry, "size_bytes": len(data)}],
    }


@pytest.mark.skipif(sys.platform == "win32", reason="a container plan takes the VM's POSIX paths")
def test_the_count_reads_the_verified_weights_mounted_read_only(tmp_path, monkeypatch):
    module = load()
    commit = _clone(tmp_path)
    weights = module.verified_weights(_weights_spec(commit), tmp_path)
    ((copy, rel),) = weights
    assert rel == "saved/m.pth" and copy.read_bytes() == CKPT
    assert copy.parent == tmp_path / "verified" / "repository-files"
    seen = {}

    class Result:
        exit_code, stopped, usage_usec = 0, None, 1

    def run(backend, work, argv, log, minutes):
        # the container is not started: its plan and its folder are read
        seen["mounts"] = next(iter(backend.plans.values())).data_mounts
        seen["tree"] = (work / "saved" / "m.pth").exists()
        log.parent.mkdir(parents=True, exist_ok=True)
        log.write_text("noise\nrefute-population-count 7\n", encoding="utf-8")
        return Result(), 0.0

    monkeypatch.setattr(module.mp, "run", run)
    out = module.count_once(
        _weights_spec(commit), tmp_path, "python@sha256:" + "b" * 64, b"print(7)\n", 1, weights
    )
    assert out["count_lines"] == ["7"] and out["exit_code"] == 0
    assert seen["mounts"] == ((str(copy.resolve()), "saved/m.pth"),)
    assert seen["tree"] is False  # the tree's copy left for the mount


@pytest.mark.skipif(sys.platform == "win32", reason="a container plan takes the VM's POSIX paths")
def test_the_count_record_names_the_weights_it_mounted(tmp_path, monkeypatch):
    """The record's weights field names the weights the two containers read from Refute's
    verified copy (Codex review, round 2): a claim binds only with it."""
    module = load()
    commit = _clone(tmp_path)
    script = b"print('refute-population-count 7')\n"
    (tmp_path / "count.py").write_bytes(script)
    spec = _weights_spec(commit)
    spec["script"] = {
        "path": str(tmp_path / "count.py"),
        "sha256": hashlib.sha256(script).hexdigest(),
    }
    built = {"exit_code": 0, "lock_sha256": "1" * 64, "pyvenv_sha256": "2" * 64, "spec": spec,
             "image": "python@sha256:" + "b" * 64, "commit": commit,
             "rung": "requirements_compiled"}  # fmt: skip
    (tmp_path / "build.json").write_text(json.dumps(built), encoding="utf-8")

    class Result:
        exit_code, stopped, usage_usec = 0, None, 1

    def run(backend, work, argv, log, minutes):
        log.parent.mkdir(parents=True, exist_ok=True)
        log.write_text("refute-population-count 7\n", encoding="utf-8")
        return Result(), 0.0

    monkeypatch.setattr(module.mp, "run", run)
    record, ok = module.count(spec, tmp_path)
    assert ok and record["count"] == 7
    digest = hashlib.sha256(CKPT).hexdigest()
    assert record["weights"] == [{"path": "saved/m.pth", "sha256": digest}]


@pytest.mark.parametrize(
    ("case", "match"),
    [("unlisted", "not listed in configuration"), ("other bytes", "not verified")],
)
def test_weights_not_listed_or_not_verified_stop_the_count(tmp_path, case, match):
    module = load()
    commit = _clone(tmp_path)
    if case == "unlisted":
        spec = _weights_spec(commit, listed=False)
    else:
        spec = _weights_spec(commit, data=CKPT + b"x")
    with pytest.raises(SystemExit, match=match):
        module.verified_weights(spec, tmp_path)
