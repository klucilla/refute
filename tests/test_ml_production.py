"""The production wiring of the ML pack (src/refute/packs/ml/production.py), offline: the
ladder's inputs and commands, the classification of a build, the workspaces with the
read-only data links, the harness's container plans, the margin and the tolerance, and
the dossier. The end-to-end run with Docker is on the VM
(scripts/vm/production_vm_test.py)."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

from refute.core.paper import FailureCause
from refute.packs.ml import ladder as ld
from refute.packs.ml import orchestrate as orc
from refute.packs.ml import production as pd
from refute.packs.ml.docker_backend import Limits
from refute.packs.ml.sandbox import RunResult, TimingMaxima

LIMITS = Limits(cpus=22, period_us=100_000, memory_bytes=12 << 30, pids=4096)
TIMING = TimingMaxima(0.000346, 0.207)


def repo(tmp_path: Path, files: dict[str, str]) -> Path:
    r = tmp_path / "repo"
    for name, text in files.items():
        (r / name).parent.mkdir(parents=True, exist_ok=True)
        (r / name).write_text(text)
    (r / ".git").mkdir()
    (r / ".git" / "HEAD").write_text("ref")
    return r


def result(tmp_path, code, stopped=None, log="") -> RunResult:
    path = tmp_path / "build.log"
    path.write_text(log)
    return RunResult(code, 1000, stopped, 1.0, path)


def test_ladder_inputs_and_channels(tmp_path):
    r = repo(
        tmp_path,
        {
            "environment.yml": "name: x\ndependencies:\n- python=3.8\n",
            "requirements.txt": "numpy\n",
        },
    )
    assert pd.ladder_inputs(r) == ("environment.yml", "requirements.txt", None)
    assert pd.env_file_channels(r / "environment.yml") == []
    (r / "environment.yml").write_text(
        "name: x\nchannels:\n  - pytorch\n  - conda-forge\ndependencies:\n- numpy\n"
    )
    assert pd.env_file_channels(r / "environment.yml") == ["pytorch", "conda-forge"]


def test_build_scripts(tmp_path):
    r = repo(
        tmp_path,
        {
            "environment.yaml": "name: x\ndependencies:\n- python=3.8\n",
            "requirements.txt": "numpy\n",
        },
    )
    own = ld.Rung("own_environment", True, "found environment.yaml")
    script = pd.build_script(own, r, "2024-01-01")[2]
    assert (
        "micromamba create" in script
        and "-c conda-forge" in script
        and "/work/environment.yaml" in script
    )
    req = ld.Rung("requirements_compiled", True, "found requirements.txt", "3.10")
    script = pd.build_script(req, r, "2024-01-01")[2]
    assert "--exclude-newer 2024-01-01" in script and "uv venv --python 3.10 /opt/venv" in script
    assert f"uv=={pd.UV_VERSION}" in script


def test_a_dockerfile_only_is_not_built_by_version_1(tmp_path):
    r = repo(tmp_path, {"Dockerfile": "FROM scratch\n"})
    own = ld.Rung("own_environment", True, "found Dockerfile")
    argv = pd.build_script(own, r, "2024-01-01")
    res = result(
        tmp_path, pd.EXIT_NOT_SUPPORTED, log="refute: version 1 does not build a Dockerfile\n"
    )
    assert str(pd.EXIT_NOT_SUPPORTED) in argv[2]
    assert pd.classify_build(own, res).outcome is orc.Outcome.REFUTE_ERROR


def test_classify_build(tmp_path):
    rung = ld.Rung("requirements_compiled", True, "x", "3.10")
    assert pd.classify_build(rung, result(tmp_path, 0)).outcome is orc.Outcome.COMPLETED
    assert (
        pd.classify_build(rung, result(tmp_path, None, "threshold")).outcome
        is orc.Outcome.BUDGET_EXHAUSTED
    )
    assert (
        pd.classify_build(rung, result(tmp_path, None, "no_progress")).outcome
        is orc.Outcome.OPERATIONAL_GUARD
    )
    net = pd.classify_build(
        rung, result(tmp_path, 1, log="ProxyError: Tunnel connection failed: 403 Forbidden")
    )
    assert net.outcome is orc.Outcome.FAILED and net.cause is FailureCause.TRANSIENT_NETWORK
    proc = pd.classify_build(
        rung, result(tmp_path, 1, log="ERROR: No matching distribution found for x")
    )
    assert proc.cause is FailureCause.BUILD_LADDER
    assert pd.classify_build(rung, None).outcome is orc.Outcome.REFUTE_ERROR
    # Codex review of 3dd85e2: only a positively identified procedure error is the artifact's
    killed = pd.classify_build(rung, result(tmp_path, 137, log="Killed\n"))
    assert killed.outcome is orc.Outcome.OPERATIONAL_GUARD
    tls = pd.classify_build(rung, result(tmp_path, 1, log="SSL: CERTIFICATE_VERIFY_FAILED"))
    assert tls.cause is FailureCause.TRANSIENT_NETWORK
    other = pd.classify_build(rung, result(tmp_path, 1, log="gcc: command not found\n"))
    assert other.outcome is orc.Outcome.FAILED and other.cause is FailureCause.UNDETERMINED


def test_margin_and_tolerance():
    # 2 x 22 x (0.1 + 1 + 0.000346 + 0.207) + 24 x 0.005 = 57.64 CPU-s
    assert pd.margin_usec(LIMITS, TIMING) == 57_643_224
    assert pd.tolerance_usec(12) == 13_000_000


def test_base_env_turns_trackers_off():
    assert pd.BASE_ENV["WANDB_MODE"] == "disabled"
    assert pd.BASE_ENV["HF_HUB_OFFLINE"] == "1"


def _setup(tmp_path, files, layout):
    from refute.packs.ml import integration as ig
    from refute.packs.ml.fetch import ArtifactSpec, FetchResult

    r = repo(tmp_path, files)
    data = tmp_path / "fetched.npz"
    data.write_bytes(b"data")
    spec = ArtifactSpec("d", "https://example.org/d", "0" * 64, 4)
    evidence = ig.DatasetEvidence(FetchResult(spec, data, False, (), None), {"test": 1})
    return pd.PaperSetup("p1", tmp_path / "run", r, {"d": evidence}, layout, LIMITS, TIMING), data


def test_datasets_are_mounted_read_only_not_copied(tmp_path, monkeypatch):
    from refute.packs.ml import integration as ig

    setup, data = _setup(tmp_path, {"train.py": "print(1)\n"}, {"d": "data/dataset.npz"})
    monkeypatch.setattr(
        ig, "plan_container_ids", lambda cf: ["setup/build/requirements_compiled", "k1/base/s0"]
    )
    ws = pd.prepare_workspaces(setup, {})
    assert not (ws["k1/base/s0"] / ".git").exists()
    assert not (ws["k1/base/s0"] / "data" / "dataset.npz").exists()  # a mount, not a file
    mounts = pd.data_mounts(setup)
    assert mounts == ((str(data.resolve()), "data/dataset.npz"),)
    if sys.platform != "win32":
        assert oct(os.stat(data).st_mode & 0o777) == "0o444"


def test_data_layout_must_stay_in_the_folder(tmp_path, monkeypatch):
    from refute.packs.ml import integration as ig

    monkeypatch.setattr(ig, "plan_container_ids", lambda cf: ["k1/base/s0"])
    for bad in ("../x.npz", "/etc/x", ".refute/x", "a\\b"):
        setup, _ = _setup(
            tmp_path / bad.replace("/", "_").replace("\\", "_"), {"t.py": ""}, {"d": bad}
        )
        with pytest.raises(pd.ProductionError):
            pd.prepare_workspaces(setup, {})


@pytest.mark.skipif(sys.platform == "win32", reason="symbolic links as on the VM (Linux)")
def test_a_repository_link_that_leaves_it_is_refused(tmp_path, monkeypatch):
    from refute.packs.ml import integration as ig

    monkeypatch.setattr(ig, "plan_container_ids", lambda cf: ["k1/base/s0"])
    setup, _ = _setup(tmp_path, {"train.py": "print(1)\n"}, {})
    (setup.repo / "secrets").symlink_to("/etc")
    with pytest.raises(pd.ProductionError, match="leaves it"):
        pd.prepare_workspaces(setup, {})


def test_wait_for_run_phase(tmp_path):
    flag = tmp_path / "run-phase-approved"
    sleeps = []

    def sleep(s):
        sleeps.append(s)
        if len(sleeps) == 2:
            flag.write_text("")

    pd.wait_for_run_phase(flag, timeout_s=100, sleep=sleep)()
    assert len(sleeps) == 2 and (tmp_path / "status.txt").read_text() == "run phase\n"
    other = tmp_path / "never"
    with pytest.raises(pd.ProductionError, match="not approved"):
        pd.wait_for_run_phase(other, timeout_s=20, sleep=lambda s: None)()


def test_dossier_record(tmp_path):
    setup = pd.PaperSetup("p1", tmp_path / "run", tmp_path, {}, {}, LIMITS, TIMING)
    (setup.root / "logs").mkdir(parents=True)
    (setup.root / "logs" / "a.log").write_text("x")

    class Outcome:  # the dossier serializes whatever the integration returns
        pass

    out = pd.write_dossier(
        tmp_path / "dossier", setup, {"test_plan": {}}, Outcome(), {"env": "sha256:1"}, "t"
    )
    record = json.loads((out / "dossier.json").read_text())
    assert (
        record["format"] == pd.DOSSIER_FORMAT
        and record["setup"]["base_env"]["WANDB_MODE"] == "disabled"
    )
    assert (out / "logs" / "a.log").exists() and (out / "claim_file.json").exists()
    with pytest.raises(FileExistsError):
        pd.write_dossier(tmp_path / "dossier", setup, {}, Outcome(), {}, "t")
