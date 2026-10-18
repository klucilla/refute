"""The docker backend (WP3 W3.8 to W3.10b, 1.4a) against a stand-in docker CLI and a
stand-in cgroup tree (tests/fake_docker.py): CI has no Docker. The real test is on the VM
(scripts/vm/docker_backend_vm_test.py)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from refute.packs.ml.docker_backend import (
    ContainerPlan,
    DockerBackend,
    DockerRefusedError,
    Limits,
)
from refute.packs.ml.sandbox import STOP_ACTIVE_TIME, STOP_THRESHOLD, RunSpec

FAKE = Path(__file__).with_name("fake_docker.py")
IMAGE = "ubuntu@sha256:" + "c" * 64
LIMITS = Limits(cpus=2, period_us=100_000, memory_bytes=1 << 30, pids=256)


def backend(tmp_path: Path, plans: dict[Path, ContainerPlan], **kw) -> DockerBackend:
    state, root = tmp_path / "state", tmp_path / "cgroup"
    return DockerBackend(
        "p1",
        kw.pop("limits", LIMITS),
        plans,
        docker=(sys.executable, str(FAKE), str(state), str(root)),
        cgroup_root=root,
        poll_s=0.05,
        **kw,
    )


def spec(tmp_path: Path, work: Path, argv: list[str], threshold: int | None = None, active=30.0):
    return RunSpec(
        argv=argv,
        workdir=work,
        env={"OMP_NUM_THREADS": "1"},
        log_path=tmp_path / "logs" / f"{work.name}.log",
        threshold_usec=threshold,
        active_time_limit_s=active,
        no_progress_s=30.0,
    )


def records(tmp_path: Path) -> list[dict]:
    return [json.loads(p.read_text()) for p in sorted((tmp_path / "state").glob("*.json"))]


def test_a_run_counts_its_slice_and_exits(tmp_path):
    work = tmp_path / "w1"
    work.mkdir()
    b = backend(tmp_path, {work: ContainerPlan(IMAGE)})
    result = b.run(spec(tmp_path, work, ["work", "0.3", "0"]))
    assert result.exit_code == 0 and result.stopped is None
    assert 300_000 <= result.usage_usec < 400_000
    assert b.parent_usage() == result.usage_usec
    (rec,) = records(tmp_path)
    args = rec["args"]
    # the backend's own options, never the claim's
    for flag in ("--cap-drop", "--security-opt", "--read-only", "--user", "--pids-limit"):
        assert flag in args
    assert args[args.index("--network") + 1] == "none"
    assert args[args.index("--cgroup-parent") + 1] == "refute-p1-c0001.slice"
    assert args[args.index("--memory-swap") + 1] == args[args.index("--memory") + 1]
    # the image's own entry point, health check and user never apply (Codex review)
    assert args[args.index("--entrypoint") + 1] == "" and "--no-healthcheck" in args
    assert args[args.index("--user") + 1] == "10001:10001"
    assert "HTTPS_PROXY=" in args  # a committed build's proxy variables are cleared
    assert rec["cmd"] == ["work", "0.3", "0"]
    assert "started" in result.log_path.read_text()
    assert b.kill_active() == []  # nothing left running


def test_data_mounts_are_read_only(tmp_path):
    work = tmp_path / "w1"
    work.mkdir()
    # the source is a path on the VM; the stand-in does not open it
    plan = ContainerPlan(IMAGE, data_mounts=(("/home/refute/cache/fetched.npz", "data/d.npz"),))
    b = backend(tmp_path, {work: plan})
    b.run(spec(tmp_path, work, ["work", "0.1", "0"]))
    (rec,) = records(tmp_path)
    mounts = [rec["args"][i + 1] for i, a in enumerate(rec["args"]) if a == "--mount"]
    assert any(m.endswith("target=/work/data/d.npz,readonly") for m in mounts)
    with pytest.raises(ValueError, match="relative path in /work"):
        ContainerPlan(IMAGE, data_mounts=(("/abs/f", "../escape"),))
    with pytest.raises(ValueError, match="relative path in /work"):
        ContainerPlan(IMAGE, data_mounts=(("/abs/f", "/etc/passwd"),))


def test_an_image_with_a_volume_is_refused(tmp_path):
    work = tmp_path / "w1"
    work.mkdir()
    b = backend(tmp_path, {work: ContainerPlan("volumeimg@sha256:" + "d" * 64)})
    with pytest.raises(DockerRefusedError, match="declares volumes"):
        b.run(spec(tmp_path, work, ["work", "0.1", "0"]))


def test_no_container_starts_after_a_stop(tmp_path):
    work = tmp_path / "w1"
    work.mkdir()
    b = backend(tmp_path, {work: ContainerPlan(IMAGE)})
    assert b.kill_active() == []
    with pytest.raises(DockerRefusedError, match="stopping"):
        b.run(spec(tmp_path, work, ["work", "0.1", "0"]))
    assert not list((tmp_path / "state").glob("*.json"))  # nothing was even created


def test_a_stop_during_a_run_kills_it_as_a_refute_error(tmp_path):
    """The stop is sent once the container has started (its log says so), not after a fixed
    delay: under load a fixed 0.3 s could fall before the start, and the run would then be
    refused instead of stopped (#59)."""
    import threading
    import time

    work = tmp_path / "w1"
    work.mkdir()
    b = backend(tmp_path, {work: ContainerPlan(IMAGE)})
    run = spec(tmp_path, work, ["work", "60", "0"])
    started = threading.Event()

    def stop_once_started():
        deadline = time.monotonic() + 50  # far below the run's 60 s
        while time.monotonic() < deadline:
            try:
                if "started" in run.log_path.read_text():
                    started.set()
                    break
            except OSError:
                pass  # the log does not exist yet
            time.sleep(0.05)
        b.kill_active()

    stopper = threading.Thread(target=stop_once_started)
    stopper.start()
    with pytest.raises(RuntimeError, match="the paper was stopped"):
        b.run(run)
    stopper.join()
    assert started.is_set()


@pytest.mark.skipif(sys.platform == "win32", reason="modes as on the VM (Linux)")
def test_an_unlistable_folder_stops_the_reading(tmp_path):
    work = tmp_path / "w1"
    hidden = work / "out"
    hidden.mkdir(parents=True)
    (hidden / "metric.json").write_text("{}")
    hidden.chmod(0o111)
    log = tmp_path / "r.log"
    try:
        with pytest.raises(RuntimeError, match="cannot be checked"):
            DockerBackend._sanitize(work, log)
    finally:
        hidden.chmod(0o755)


def test_a_missing_parent_slice_is_an_error_not_zero(tmp_path):
    b = backend(tmp_path, {})
    with pytest.raises(RuntimeError, match="no cpu.stat"):
        b.parent_usage()


@pytest.mark.skipif(sys.platform == "win32", reason="symbolic links as on the VM (Linux)")
def test_links_leaving_the_folder_are_removed_after_a_run(tmp_path):
    work = tmp_path / "w1"
    (work / "out").mkdir(parents=True)
    (work / "out" / "metric.json").symlink_to("/etc/hostname")
    (work / "out" / "inside.json").write_text("{}")
    (work / "out" / "alias.json").symlink_to(work / "out" / "inside.json")
    log = tmp_path / "logs" / "r.log"
    log.parent.mkdir()
    log.write_text("")
    removed = DockerBackend._sanitize(work, log)
    assert removed == [str(Path("out") / "metric.json")]
    assert (work / "out" / "alias.json").is_symlink()  # a link inside the folder stays
    assert json.loads((tmp_path / "logs" / "r.log.sanitized.json").read_text()) == removed


def test_threshold_stops_the_container_and_measures_d_and_s(tmp_path):
    work = tmp_path / "w1"
    work.mkdir()
    b = backend(tmp_path, {work: ContainerPlan(IMAGE)})
    result = b.run(spec(tmp_path, work, ["work", "60", "0", "2"], threshold=500_000))
    assert result.stopped == STOP_THRESHOLD and result.exit_code is None
    assert result.usage_usec >= 500_000
    assert result.detection_delay_s is not None and result.stop_latency_s is not None
    assert (tmp_path / "state").glob("*.killed")


def test_active_time_guard(tmp_path):
    work = tmp_path / "w1"
    work.mkdir()
    b = backend(tmp_path, {work: ContainerPlan(IMAGE)})
    result = b.run(spec(tmp_path, work, ["work", "60", "0"], active=0.3))
    assert result.stopped == STOP_ACTIVE_TIME


def test_parent_sums_every_container(tmp_path):
    w1, w2 = tmp_path / "w1", tmp_path / "w2"
    w1.mkdir()
    w2.mkdir()
    b = backend(tmp_path, {w1: ContainerPlan(IMAGE), w2: ContainerPlan(IMAGE)})
    r1 = b.run(spec(tmp_path, w1, ["work", "0.2", "0"]))
    r2 = b.run(spec(tmp_path, w2, ["work", "0.2", "3"]))
    assert r2.exit_code == 3
    # the stand-in writes only the container slices; the paper's total is their sum on the
    # VM (the kernel's), so here the parent is read from the slices themselves
    total = sum(
        int(p.read_text().split()[1])
        for p in (tmp_path / "cgroup" / "refute.slice" / "refute-p1.slice").glob("*/cpu.stat")
    )
    assert total == r1.usage_usec + r2.usage_usec


def test_build_has_the_proxy_and_is_committed(tmp_path):
    work = tmp_path / "build"
    work.mkdir()
    plan = ContainerPlan(IMAGE, network="proxy", commit_as="refute-local/p1/env", read_only=False)
    b = backend(tmp_path, {work: plan})
    result = b.run(spec(tmp_path, work, ["work", "0.1", "0"]))
    assert result.exit_code == 0
    (rec,) = records(tmp_path)
    assert "--network" not in rec["args"] and "--read-only" not in rec["args"]
    assert "HTTPS_PROXY=http://10.231.71.3:3128" in rec["args"]
    (committed,) = (tmp_path / "state").glob("*.committed")
    assert committed.read_text() == "refute-local/p1/env"


def test_a_failed_build_is_not_committed(tmp_path):
    work = tmp_path / "build"
    work.mkdir()
    plan = ContainerPlan(IMAGE, network="proxy", commit_as="refute-local/p1/env", read_only=False)
    b = backend(tmp_path, {work: plan})
    assert b.run(spec(tmp_path, work, ["work", "0.1", "1"])).exit_code == 1
    assert not list((tmp_path / "state").glob("*.committed"))


def test_a_quota_of_max_is_refused(tmp_path):
    work = tmp_path / "w1"
    work.mkdir()
    b = backend(tmp_path, {work: ContainerPlan(IMAGE)})
    b._create_args_orig = b._create_args

    def no_quota(*a):
        args = b._create_args_orig(*a)
        args[args.index("--cpu-quota") + 1] = "0"
        return args

    b._create_args = no_quota
    with pytest.raises(RuntimeError, match="refused by 1.4a"):
        b.run(spec(tmp_path, work, ["work", "5", "0"]))


def test_the_quota_is_checked_as_a_ratio(tmp_path):
    work = tmp_path / "w1"
    work.mkdir()
    b = backend(tmp_path, {work: ContainerPlan(IMAGE)}, limits=LIMITS)
    b._create_args_orig = b._create_args

    def tiny_period(*a):  # 200000/1000 passes both separate checks and is 200 CPUs
        args = b._create_args_orig(*a)
        args[args.index("--cpu-period") + 1] = "1000"
        return args

    b._create_args = tiny_period
    with pytest.raises(RuntimeError, match="refused by 1.4a"):
        b.run(spec(tmp_path, work, ["work", "5", "0"]))


def test_refusals(tmp_path):
    work = tmp_path / "w1"
    work.mkdir()
    b = backend(tmp_path, {work: ContainerPlan(IMAGE)})
    with pytest.raises(DockerRefusedError, match="no container plan"):
        b.run(spec(tmp_path, tmp_path, ["work", "1", "0"]))
    with pytest.raises(ValueError, match="pinned by digest"):
        ContainerPlan("ubuntu:latest")
    with pytest.raises(ValueError, match="only a build"):
        ContainerPlan(IMAGE, commit_as="refute-local/p1/env")
    with pytest.raises(ValueError, match="slice name"):
        DockerBackend("P-1", LIMITS, {})
    with pytest.raises(ValueError):
        Limits(cpus=25, period_us=100_000, memory_bytes=1 << 30, pids=256)
    bad = RunSpec(["work", "1", "0"], work, {"BAD NAME": "x"}, tmp_path / "l.log", None, 5, 5)
    with pytest.raises(DockerRefusedError, match="environment variable"):
        b.run(bad)
