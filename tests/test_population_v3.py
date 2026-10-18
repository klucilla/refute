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


def test_the_harness_v3_runs_m4_in_a_spawned_worker():
    # the harness writes only inside the project, so the work folder is under .cache/
    import uuid

    work = ROOT / ".cache" / "test-population-v3" / uuid.uuid4().hex
    res = _probe("v3", work)
    assert res.returncode == 0, res.stderr[-2000:]
    out = json.loads(res.stdout.strip().splitlines()[-1])
    assert out["error"] is None and out["status"] == "analyzed"
    assert out["worker_pid"] != out["main_pid"]  # the analysis ran in a spawned worker
    assert out["block"]["version"] == 2 and out["block"]["enabled"] is True
    assert {"a1_noise", "bls_beta_gate", "trapezoid_timing"} <= set(out["marker"]["executed"])
    assert out["harness_sha256"] == out["v3_sha256"]  # the campaign names version 3


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
