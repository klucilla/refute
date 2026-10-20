"""The population harness version 3 (map Amendments 17 and 25): the frozen version 2 measuring an
M4 configuration. Each case runs ``tests/population_v3_probe.py`` in its own process.

From Amendment 25 the configuration is loaded without an exit at import (a loading problem is
kept and refuses the plan and every operational mode), and a configuration file must sit directly
inside ``m4-configurations/``, so the non-default case uses the test fixture
``probe-non-default.json`` there, and an incomplete or legacy block is checked by ``capture``."""

import json
import os
import subprocess
import sys
import uuid
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "tests" / "population_v3_probe.py"
CONFIGS = ROOT / "docs" / "validation" / "v0.2.1" / "population" / "m4-configurations"
CONFIG = CONFIGS / "m4-c1.json"
NON_DEFAULT = CONFIGS / "probe-non-default.json"


def _work():
    # the harness writes only inside the project, so the work folder is under .cache/
    return ROOT / ".cache" / "test-population-v3" / uuid.uuid4().hex


def _probe(mode, work, config=CONFIG, extra_env=None):
    env = dict(os.environ)
    env.pop("REFUTE_M4_CONFIGURATION", None)
    env.pop("REFUTE_M4_EXPECTED_IDENTITY", None)
    if config is not None:
        env["REFUTE_M4_CONFIGURATION"] = str(config)
    env.update(extra_env or {})
    return subprocess.run(
        [sys.executable, str(PROBE), mode, str(work)],
        capture_output=True,
        text=True,
        env=env,
        timeout=1200,
    )


def _last(res):
    return json.loads(res.stdout.strip().splitlines()[-1])


def _plain(block):
    """The record's typed floats ({"dec": ...}) back to plain values."""
    return {
        k: float(v["dec"]) if isinstance(v, dict) and "dec" in v else v for k, v in block.items()
    }


@pytest.mark.parametrize("config", [CONFIG, NON_DEFAULT], ids=["m4-c1", "non-default"])
def test_the_harness_v3_runs_m4_in_a_spawned_worker(config):
    res = _probe("v3", _work(), config=config)
    assert res.returncode == 0, res.stderr[-2000:]
    out = _last(res)
    assert out["error"] is None and out["status"] == "analyzed"
    assert out["worker_pid"] != out["main_pid"]  # the analysis ran in a spawned worker
    assert _plain(out["block"]) == out["configuration"]  # the whole block, in the worker's plan
    assert {"a1_noise", "bls_beta_gate", "trapezoid_timing"} <= set(out["marker"]["executed"])
    assert out["harness_sha256"] == out["v3_sha256"]  # the campaign names version 3
    assert out["record_origin"]["harness_sha256"] == out["v3_sha256"]
    assert out["schema_problems"] == []  # the record fits version 2's closed schema
    # Amendment 25: the worker's identity in the envelope, a confirmation, a clean resume
    assert out["seen_identity"] == out["expected"]
    kinds = [e["kind"] for e in out["journal"]]
    assert kinds == ["confirmation"] and out["journal"][0]["identity"] == out["expected"]
    assert out["resume_problems"] == []


@pytest.mark.parametrize(
    ("block", "words"),
    [
        ({"version": 2, "enabled": True}, "every setting"),  # the other settings left implicit
        ({"version": 1, "enabled": True}, "version 2"),  # the legacy block
    ],
)
def test_capture_refuses_an_incomplete_or_legacy_block(block, words):
    work = _work()
    work.mkdir(parents=True)
    doc = {"format": "refute-m4-configuration/1", "name": "x", "corrections": block}
    path = work / "bad.json"
    path.write_text(json.dumps(doc), encoding="utf-8")
    out = _last(_probe("capture", work, extra_env={"PROBE_CAPTURE": str(path)}))
    assert out["error"] is not None and words in out["error"], out


def test_version_2_alone_still_measures_m3(tmp_path):
    res = _probe("v2", tmp_path, config=None)
    assert res.returncode == 0, res.stderr[-2000:]
    assert _last(res) == {"active": False}


@pytest.mark.parametrize("bad", [None, "not_a_file.json", "outside"])
def test_without_an_authorized_configuration_the_plan_is_refused(bad):
    work = _work()
    work.mkdir(parents=True)
    config = None
    if bad == "outside":  # a valid file, but not inside m4-configurations/
        config = work / "c.json"
        config.write_bytes(CONFIG.read_bytes())
    elif bad is not None:
        config = work / bad
    imported = _probe("import", work, config=config)
    assert imported.returncode == 0, imported.stderr[-2000:]  # no exit at import
    state = _last(imported)
    assert state["state_ok"] is False and "M4 configuration not loaded" in state["problem"]
    assert _probe("plan", work, config=config).returncode != 0
