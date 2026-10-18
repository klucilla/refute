"""The population harness version 3 (map Amendment 17): the frozen version 2 measuring an M4
configuration. Each case runs ``tests/population_v3_probe.py`` in its own process."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "tests" / "population_v3_probe.py"
CONFIG = ROOT / "docs" / "validation" / "v0.2.1" / "population" / "m4-configurations" / "m4-c1.json"


def _probe(mode, work, config=CONFIG):
    env = dict(os.environ)
    env.pop("REFUTE_M4_CONFIGURATION", None)
    if config is not None:
        env["REFUTE_M4_CONFIGURATION"] = str(config)
    res = subprocess.run(
        [sys.executable, str(PROBE), mode, str(work)],
        capture_output=True,
        text=True,
        env=env,
        timeout=1200,
    )
    return res


def _plain(block):
    """The record's typed floats ({"dec": ...}) back to plain values."""
    return {
        k: float(v["dec"]) if isinstance(v, dict) and "dec" in v else v for k, v in block.items()
    }


@pytest.mark.parametrize("which", ["m4-c1", "non-default"])
def test_the_harness_v3_runs_m4_in_a_spawned_worker(which):
    # the harness writes only inside the project, so the work folder is under .cache/
    import uuid

    work = ROOT / ".cache" / "test-population-v3" / uuid.uuid4().hex
    config = CONFIG
    if which == "non-default":  # added after the Codex stage review: every setting reaches the plan
        work.mkdir(parents=True)
        doc = json.loads(CONFIG.read_text(encoding="utf-8"))
        doc["name"] = "probe-non-default"
        doc["corrections"].update(r_min=15, m_beta=1.3, b_min=25)
        config = work / "non-default.json"
        config.write_text(json.dumps(doc), encoding="utf-8")
    res = _probe("v3", work / "run", config=config)
    assert res.returncode == 0, res.stderr[-2000:]
    out = json.loads(res.stdout.strip().splitlines()[-1])
    assert out["error"] is None and out["status"] == "analyzed"
    assert out["worker_pid"] != out["main_pid"]  # the analysis ran in a spawned worker
    assert _plain(out["block"]) == out["configuration"]  # the whole block, in the worker's plan
    assert {"a1_noise", "bls_beta_gate", "trapezoid_timing"} <= set(out["marker"]["executed"])
    assert out["harness_sha256"] == out["v3_sha256"]  # the campaign names version 3
    assert out["record_origin"]["harness_sha256"] == out["v3_sha256"]
    assert out["schema_problems"] == []  # the record fits version 2's closed schema


def test_the_harness_v3_refuses_an_incomplete_block(tmp_path):
    doc = json.loads(CONFIG.read_text(encoding="utf-8"))
    doc["corrections"] = {"version": 2, "enabled": True}  # the other settings left implicit
    config = tmp_path / "incomplete.json"
    config.write_text(json.dumps(doc), encoding="utf-8")
    assert _probe("import", tmp_path, config=config).returncode != 0


def test_version_2_alone_still_measures_m3(tmp_path):
    res = _probe("v2", tmp_path, config=None)
    assert res.returncode == 0, res.stderr[-2000:]
    assert json.loads(res.stdout.strip().splitlines()[-1]) == {"active": False}


@pytest.mark.parametrize("bad", [None, "not_a_file.json", "legacy"])
def test_the_harness_v3_refuses_without_an_m4_configuration(tmp_path, bad):
    config = bad
    if bad == "legacy":
        config = tmp_path / "legacy.json"
        block = {"version": 1, "enabled": True}
        doc = {"format": "refute-m4-configuration/1", "name": "x", "corrections": block}
        config.write_text(json.dumps(doc), encoding="utf-8")
    elif bad is not None:
        config = tmp_path / bad
    res = _probe("import", tmp_path, config=config)
    assert res.returncode != 0
