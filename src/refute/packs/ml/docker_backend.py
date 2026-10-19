"""Sandbox runner of the ML pack: the ``docker`` backend (WP3 W3.8 to W3.10b, 1.4a).

It runs on the Refute VM, next to the engine (the design decided with Codex on
2026-10-17: the whole engine runs on the VM, the host starts it and checks the dossier it
brings back). Same interface as the ``subprocess`` backend (``orchestrate.Backend``):
``run(RunSpec) -> RunResult``.

For each run the backend:

- refuses a run whose working folder has no plan (``ContainerPlan``): the image, pinned by
  digest, the network (``none``, or ``proxy`` for a build), the user and whether the
  result is committed as an image. A claim or a repository gives only the command; the
  mounts, namespaces and security options are the backend's own;
- creates the container under a **systemd slice of its own**, inside the paper's slice
  (``--cgroup-parent``): ``refute-<paper>.slice`` holds every container of the paper,
  builds and failed attempts included, and ``refute-<paper>-cNNNN.slice`` exactly one
  container. A slice outlives its container and keeps its cumulative ``usage_usec``
  (observed on the VM on 2026-10-17, jea-registration.md section 23), so the final
  reading of each container and the paper's total (W2.10) are exact;
- runs with ``--cap-drop ALL``, ``--security-opt no-new-privileges``, a CPU quota with
  no burst, a memory limit equal to its swap limit (no swap), a process limit, and with
  ``--network none`` except a build, which reaches the internet only through the
  allowlist proxy (``HTTP_PROXY`` and ``HTTPS_PROXY``); a run container also has a
  read-only root filesystem, a non-root user and a ``/tmp`` in memory. The only mount is
  the run's own working folder, at ``/work``;
- checks, once the container started, that its quota is not ``max`` and its burst is 0
  (1.4a), and stops it otherwise;
- reads the slice's ``cpu.stat`` every Δ = 1 s and stops the container when a reading
  reaches F, its threshold (W2.10a), when the stage's active time limit is reached, or
  when neither the usage nor the log grew for ``no_progress`` seconds; it measures D and
  S as the ``subprocess`` backend does (1.4a), S until the slice holds no process;
- reads the final usage once the slice holds no process, commits the container as an
  image when its plan asks and it exited 0, and removes it.

**Known limit (recorded in wp3-acceptance.md):** no disk quota per container: the storage
driver of the VM (overlayfs on ext4) does not support ``--storage-opt size``
(https://docs.docker.com/reference/cli/docker/container/run/#set-storage-driver-options-per-container---storage-opt,
read 2026-10-17); the paper's slice is bounded in CPU and memory, the disk is not.

Only containers this backend created are ever stopped, by their id.
"""

from __future__ import annotations

import json
import os
import re
import stat
import subprocess
import threading
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

from refute.packs.ml.sandbox import (
    STOP_ACTIVE_TIME,
    STOP_NO_PROGRESS,
    STOP_OUT_OF_MEMORY,
    STOP_THRESHOLD,
    RunResult,
    RunSpec,
)

DELTA_S = 1.0  # the reading interval of 1.4a
PROXY_URL = "http://10.231.71.3:3128"
WORK = "/work"
# a run is a user that owns nothing of the engine's (the engine is uid 1000 on the VM):
# the read-only data files hard-linked into its folder cannot be changed by it
RUN_USER = "10001:10001"
BUILD_USER = "0:0"  # a build installs into the image as root, with no capability
KILL_WAIT_S = 60.0  # the longest wait for a stopped container's slice to empty
PAPER_ID = re.compile(r"^[a-z0-9]{1,40}$")
IMAGE_BY_DIGEST = re.compile(r"^[a-z0-9./_-]+(:[A-Za-z0-9._-]+)?@sha256:[0-9a-f]{64}$")
LOCAL_IMAGE = re.compile(r"^refute-local/[a-z0-9]{1,40}/[a-z0-9_-]{1,60}$")
ENV_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class DockerRefusedError(Exception):
    """A run the backend does not start: no plan, an image not pinned, a bad limit."""


@dataclass(frozen=True)
class Limits:
    """The limits of every container of a paper, fixed before the lock."""

    cpus: float  # C of 1.4a, at most the VM's vCPUs
    period_us: int  # P of 1.4a, in microseconds
    memory_bytes: int
    pids: int

    def __post_init__(self) -> None:
        if not (0 < self.cpus <= 24):
            raise ValueError("cpus is above 0 and at most the 24 vCPUs of the VM")
        if not (1000 <= self.period_us <= 1_000_000):
            raise ValueError("the cpu.max period is from 1 ms to 1 s")
        if self.memory_bytes < 64 * 1024 * 1024 or self.pids < 16:
            raise ValueError("memory of at least 64 MiB and at least 16 processes")

    @property
    def quota_us(self) -> int:
        return round(self.cpus * self.period_us)


@dataclass(frozen=True)
class ContainerPlan:
    """How one working folder is run: chosen by Refute's code, never by the claim."""

    image: str  # pinned by digest, or an image this backend committed for the paper
    network: str = "none"  # "none", or "proxy" (a build: the allowlist proxy only)
    commit_as: str | None = None  # the image a build becomes when it exits 0
    read_only: bool = True  # a build writes its environment into the image: False
    # read-only bind mounts of fetched files: (absolute source on the VM, relative path in
    # /work); the run can neither change nor replace them (Codex review of 3dd85e2: a hard
    # link in a folder the run can write could be replaced by another file)
    data_mounts: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        if not (IMAGE_BY_DIGEST.match(self.image) or LOCAL_IMAGE.match(self.image)):
            raise ValueError(f"image not pinned by digest: {self.image!r}")
        for source, target in self.data_mounts:
            rel = PurePosixPath(target)
            if not PurePosixPath(source).is_absolute() or "," in source or "," in target:
                raise ValueError(f"a data mount source is an absolute path: {source!r}")
            if rel.is_absolute() or not rel.parts or ".." in rel.parts or rel.parts[0] == ".refute":
                raise ValueError(f"a data mount target is a relative path in /work: {target!r}")
        if self.network not in ("none", "proxy"):
            raise ValueError("network is none or proxy")
        if self.commit_as is not None and not LOCAL_IMAGE.match(self.commit_as):
            raise ValueError(
                f"a committed image is named refute-local/<paper>/<name>: {self.commit_as!r}"
            )
        if self.network == "none" and self.commit_as is not None:
            raise ValueError("only a build (network proxy) is committed")


def _read(path: Path) -> str:
    # a cgroup file is read whole; the retry only serves the tests' stand-in on Windows,
    # where a file being replaced cannot be opened for a moment
    for _ in range(100):
        try:
            return path.read_text(encoding="ascii")
        except PermissionError:
            time.sleep(0.005)
    return path.read_text(encoding="ascii")


@dataclass
class _Cgroups:
    root: Path

    def slice_dir(self, paper: str, container: str | None = None) -> Path:
        # systemd encodes the hierarchy in the slice name: refute-<paper>-<c>.slice lives
        # in refute-<paper>.slice, which lives in refute.slice
        base = self.root / "refute.slice" / f"refute-{paper}.slice"
        return base if container is None else base / f"refute-{paper}-{container}.slice"

    @staticmethod
    def usage_usec(directory: Path) -> int | None:
        try:
            text = _read(directory / "cpu.stat")
        except FileNotFoundError:
            return None
        for line in text.splitlines():
            key, _, value = line.partition(" ")
            if key == "usage_usec":
                return int(value)
        raise RuntimeError(f"no usage_usec in {directory / 'cpu.stat'}")

    @staticmethod
    def oom_kills(directory: Path) -> int:
        """``oom_kill`` of the slice's ``memory.events`` (which aggregates its descendants:
        the container's scope). Unreadable, missing or invalid is a Refute error, never 0
        (wp3-run-resources-acceptance.md, section 2)."""
        try:
            text = _read(directory / "memory.events")
        except OSError as exc:
            raise RuntimeError(f"cannot read {directory / 'memory.events'}: {exc}") from None
        for line in text.splitlines():
            key, _, value = line.partition(" ")
            if key == "oom_kill":
                if not value.isdigit():
                    raise RuntimeError(f"invalid oom_kill {value!r} in {directory}")
                return int(value)
        raise RuntimeError(f"no oom_kill in {directory / 'memory.events'}")

    @staticmethod
    def check_aggregated_events(mounts: Path, root: Path) -> None:
        """The cgroup v2 hierarchy at ``root`` must be mounted without ``memory_localevents``,
        so a slice's ``memory.events`` aggregates its descendants (the container's scope);
        otherwise, or when no cgroup2 mount is at ``root``, a Refute error before any run
        (wp3-run-resources-acceptance.md, section 2)."""
        try:
            text = _read(mounts)
        except OSError as exc:
            raise DockerRefusedError(f"cannot read {mounts}: {exc}") from None
        found = []
        for line in text.splitlines():
            fields = line.split()
            if len(fields) >= 4 and fields[2] == "cgroup2":
                point = re.sub(r"\\([0-7]{3})", lambda m: chr(int(m.group(1), 8)), fields[1])
                if point == str(root):
                    found.append(fields[3].split(","))
        if len(found) != 1:
            raise DockerRefusedError(
                f"{len(found)} cgroup2 mounts at {root}; exactly one is needed"
            )
        if "memory_localevents" in found[0]:
            raise DockerRefusedError(
                "cgroup2 is mounted with memory_localevents: a slice's memory.events would not "
                "count its descendants' kills for memory"
            )

    @staticmethod
    def populated(directory: Path) -> bool:
        try:
            text = _read(directory / "cgroup.events")
        except FileNotFoundError:
            return False
        return any(line == "populated 1" for line in text.splitlines())


@dataclass
class DockerBackend:
    """One paper's containers. ``plans`` maps each working folder (as given in the
    ``RunSpec``) to its ``ContainerPlan``."""

    paper: str
    limits: Limits
    plans: Mapping[Path, ContainerPlan]
    docker: Sequence[str] = ("docker",)
    cgroup_root: Path = Path("/sys/fs/cgroup")
    mounts: Path = Path("/proc/self/mounts")  # where the cgroup2 mount is checked
    poll_s: float = DELTA_S
    clock_ns: Callable[[], int] = time.perf_counter_ns
    sleep: Callable[[float], None] = time.sleep
    name: str = field(default="docker", init=False)
    _count: int = field(default=0, init=False)

    def __post_init__(self) -> None:
        if not PAPER_ID.match(self.paper):
            raise ValueError("the paper id is lowercase letters and digits (a slice name)")
        self._cgroups = _Cgroups(Path(self.cgroup_root))
        self._plans = {Path(k).resolve(): v for k, v in self.plans.items()}
        self._active: set[str] = set()  # containers created and not yet removed
        self._stopping = False  # set by kill_active: no container starts afterwards
        self._lock = threading.Lock()
        self._mount_checked = False

    # -- the paper's total, for the completeness check of W2.10

    def parent_usage(self) -> int:
        """The paper's slice's cumulative usage. A missing slice is an error, never zero
        (Codex review of 3dd85e2: a missing meter must invalidate the accounting)."""
        value = _Cgroups.usage_usec(self._cgroups.slice_dir(self.paper))
        if value is None:
            raise RuntimeError(f"the slice refute-{self.paper}.slice has no cpu.stat")
        return value

    def kill_active(self) -> list[str]:
        """Kills every container of this backend still running (the paper's unit is
        stopped): by their ids only."""
        with self._lock:
            self._stopping = True  # under the lock: no container is registered after this
            active = sorted(self._active)
        for cid in active:
            self._kill(cid)
        return active

    def _check_image(self, image: str) -> None:
        """An image's own configuration must not change the container: a VOLUME would add a
        mount the backend did not choose (Codex review of 3dd85e2). ENTRYPOINT and
        HEALTHCHECK are neutralized at creation, the user is always given."""
        volumes = self._docker("image", "inspect", "--format", "{{json .Config.Volumes}}", image)
        if volumes not in ("null", "{}", ""):
            raise DockerRefusedError(f"the image {image} declares volumes {volumes}: refused")

    # -- one run

    def _docker(self, *args: str, timeout: float = 120) -> str:
        done = subprocess.run(
            [*self.docker, *args], capture_output=True, text=True, timeout=timeout, check=False
        )
        if done.returncode != 0:
            raise RuntimeError(
                f"docker {args[0]} failed ({done.returncode}): {done.stderr.strip()[-400:]}"
            )
        return done.stdout.strip()

    def _create_args(
        self, spec: RunSpec, plan: ContainerPlan, slice_name: str, label: str
    ) -> list[str]:
        args = [
            "create",
            "--name", label,
            "--cgroup-parent", slice_name,
            "--cpu-period", str(self.limits.period_us),
            "--cpu-quota", str(self.limits.quota_us),
            "--memory", str(self.limits.memory_bytes),
            "--memory-swap", str(self.limits.memory_bytes),
            # /dev/shm of a quarter of the memory limit: Docker's 64 MiB default kills the
            # data-loader workers of PyTorch (bus error; 2305.19518's measurement run of
            # 2026-10-18); shm pages count in the memory limit, which stays the bound
            "--shm-size", str(self.limits.memory_bytes // 4),
            "--pids-limit", str(self.limits.pids),
            "--cap-drop", "ALL",
            "--security-opt", "no-new-privileges",
            "--mount", f"type=bind,source={Path(spec.workdir).resolve()},target={WORK}",
            "--workdir", WORK,
            # the image's own entry point and health check never run (Codex review)
            "--entrypoint", "",
            "--no-healthcheck",
        ]  # fmt: skip
        for source, target in plan.data_mounts:
            args += ["--mount", f"type=bind,source={source},target={WORK}/{target},readonly"]
        proxy_names = ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy")
        if plan.network == "none":
            args += ["--network", "none"]
            # a committed build keeps its proxy variables in the image: cleared in a run
            for key in proxy_names:
                args += ["--env", f"{key}="]
        else:
            for key in proxy_names:
                args += ["--env", f"{key}={PROXY_URL}"]
        if plan.read_only:
            args += ["--read-only", "--tmpfs", "/tmp:rw,nosuid,nodev,size=1g", "--user", RUN_USER]
        else:
            args += ["--user", BUILD_USER]  # never the image's own USER
        for key, value in spec.env.items():
            if not ENV_NAME.match(key) or "\x00" in value:
                raise DockerRefusedError(f"environment variable refused: {key!r}")
            args += ["--env", f"{key}={value}"]
        return [*args, plan.image, *spec.argv]

    def run(self, spec: RunSpec) -> RunResult:
        workdir = Path(spec.workdir).resolve()
        plan = self._plans.get(workdir)
        if plan is None:
            raise DockerRefusedError(f"no container plan for {workdir}")
        if not workdir.is_dir():
            raise DockerRefusedError(f"the working folder does not exist: {workdir}")
        self._count += 1
        tag = f"c{self._count:04d}"
        slice_name = f"refute-{self.paper}-{tag}.slice"
        label = f"refute-{self.paper}-{tag}"
        own = self._cgroups.slice_dir(self.paper, tag)
        if not self._mount_checked:
            _Cgroups.check_aggregated_events(Path(self.mounts), Path(self.cgroup_root))
            self._mount_checked = True
        if _Cgroups.usage_usec(own) is not None:
            raise DockerRefusedError(f"the slice {slice_name} already exists")
        self._check_image(plan.image)
        with self._lock:
            if self._stopping:
                raise DockerRefusedError("the paper is stopping: no container starts")
        cid = self._docker(*self._create_args(spec, plan, slice_name, label))
        spec.log_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with spec.log_path.open("wb") as log:
                with self._lock:
                    # registered and started under the lock: a stop either comes before
                    # (nothing starts) or sees this container (Codex review of 6755d61); the
                    # supervision also checks the stop at every reading
                    if self._stopping:
                        raise DockerRefusedError("the paper is stopping: no container starts")
                    self._active.add(cid)
                    attached = subprocess.Popen(
                        [*self.docker, "start", "--attach", cid],
                        stdout=log,
                        stderr=subprocess.STDOUT,
                    )
                try:
                    result = self._supervise(spec, cid, own, attached)
                finally:
                    if attached.poll() is None:
                        self._kill(cid)
                        attached.wait(timeout=60)
            if plan.commit_as is not None and result.exit_code == 0:
                self._docker("commit", cid, plan.commit_as, timeout=1800)
            self._sanitize(workdir, spec.log_path)
            return result
        finally:
            subprocess.run([*self.docker, "rm", "--force", cid], capture_output=True, check=False)
            with self._lock:
                self._active.discard(cid)

    @staticmethod
    def _sanitize(workdir: Path, log_path: Path) -> list[str]:
        """After a run, before the engine reads anything it wrote: every symbolic link that
        resolves outside the run's folder and every special file (FIFO, socket, device) is
        removed, and the removals are recorded next to the log, outside the folder (Codex
        review of 3dd85e2: the engine must never read through a link a run planted). A
        value that a removed file carried is then simply missing (the run's own doing)."""
        root = os.path.realpath(workdir)
        removed = []

        def unreadable(error: OSError) -> None:
            # a folder the run made unlistable could hide a link: the run's outputs are not
            # read at all (Codex review of 6755d61)
            raise RuntimeError(f"the run's folder cannot be checked: {error}") from error

        for dirpath, dirnames, filenames in os.walk(workdir, followlinks=False, onerror=unreadable):
            for name in [*dirnames, *filenames]:
                p = os.path.join(dirpath, name)
                st = os.lstat(p)
                if stat.S_ISLNK(st.st_mode):
                    target = os.path.realpath(p)
                    if os.path.commonpath([root, target]) != root:
                        os.unlink(p)
                        removed.append(os.path.relpath(p, workdir))
                elif not (stat.S_ISREG(st.st_mode) or stat.S_ISDIR(st.st_mode)):
                    os.unlink(p)
                    removed.append(os.path.relpath(p, workdir))
        if removed:
            note = log_path.with_name(log_path.name + ".sanitized.json")
            note.write_text(json.dumps(sorted(removed)) + "\n", encoding="utf-8")
        return removed

    def _kill(self, cid: str) -> None:
        subprocess.run([*self.docker, "kill", cid], capture_output=True, check=False, timeout=60)

    def _check_quota(self, cid: str) -> None:
        scope = next(iter(self._cgroups.slice_dir(self.paper).rglob(f"docker-{cid}.scope")), None)
        if scope is None:
            return  # not started yet, or already ended: checked on the next reading
        quota, period = _read(scope / "cpu.max").split()
        burst_file = scope / "cpu.max.burst"
        burst = _read(burst_file).strip() if burst_file.exists() else "0"
        # the limit C is quota / period: compared as a ratio too (Codex review: 2200000/1000
        # passes both separate checks and is 2200 CPUs)
        if (
            quota == "max"
            or burst != "0"
            or int(quota) > self.limits.quota_us
            or int(period) > self.limits.period_us
            or int(quota) * self.limits.period_us > self.limits.quota_us * int(period)
        ):
            raise RuntimeError(f"cpu.max {quota} {period}, burst {burst}: refused by 1.4a")

    def _supervise(
        self, spec: RunSpec, cid: str, own: Path, attached: subprocess.Popen
    ) -> RunResult:
        start = time.monotonic()
        last_usage, last_size, last_progress = -1, -1, start
        stopped = None
        detection = latency = None
        quota_checked = False
        poll_ns = round(self.poll_s * 1_000_000_000)
        planned_ns = self.clock_ns()
        while True:
            if self._stopping:
                # the paper is stopping (SIGTERM): this container is killed and the run fails
                # as a Refute error; it never ends as the artifact's result
                self._kill(cid)
                deadline = time.monotonic() + KILL_WAIT_S
                while _Cgroups.populated(own) and time.monotonic() < deadline:
                    self.sleep(0.01)
                raise RuntimeError(f"the paper was stopped while {cid} ran")
            code = attached.poll()
            usage = _Cgroups.usage_usec(own) or 0
            now = time.monotonic()
            if code is not None:
                break
            if not quota_checked and _Cgroups.populated(own):
                self._check_quota(cid)
                quota_checked = True
            size = spec.log_path.stat().st_size if spec.log_path.exists() else 0
            if usage > last_usage or size > last_size:
                last_usage, last_size, last_progress = usage, size, now
            if spec.threshold_usec is not None and usage >= spec.threshold_usec:
                stopped = STOP_THRESHOLD
            elif now - start >= spec.active_time_limit_s:
                stopped = STOP_ACTIVE_TIME
            elif now - last_progress >= spec.no_progress_s:
                stopped = STOP_NO_PROGRESS
            if stopped:
                requested_ns = self.clock_ns()
                detection = (requested_ns - planned_ns) / 1_000_000_000
                self._kill(cid)
                stop_deadline = time.monotonic() + KILL_WAIT_S
                while _Cgroups.populated(own):
                    if time.monotonic() > stop_deadline:
                        raise RuntimeError(f"{cid} did not stop within {KILL_WAIT_S:.0f} s")
                    self.sleep(0.01)
                latency = (self.clock_ns() - requested_ns) / 1_000_000_000
                attached.wait(timeout=60)
                break
            planned_ns = self.clock_ns() + poll_ns
            self.sleep(self.poll_s)
        # the final reading once the slice holds no process: exact, the slice keeps it
        deadline = time.monotonic() + 60
        while _Cgroups.populated(own):
            if time.monotonic() > deadline:
                raise RuntimeError(f"the slice of {cid} still holds processes after the run")
            self.sleep(0.01)
        final = _Cgroups.usage_usec(own)
        if final is None:
            raise RuntimeError(f"no final reading for {cid}: its slice is gone")
        exit_code = (
            None
            if stopped
            else int(self._docker("inspect", "--format", "{{.State.ExitCode}}", cid))
        )
        try:
            oom_kills: int | None = _Cgroups.oom_kills(own)
        except RuntimeError:
            if exit_code not in (None, 0):
                raise  # after a non-zero exit, never read as 0
            oom_kills = None
        if exit_code not in (None, 0) and oom_kills:
            # killed for memory inside the container's own limit: Refute's guard, the exit
            # code kept, no D or S (the stop was not Refute's request)
            stopped = STOP_OUT_OF_MEMORY
        return RunResult(
            exit_code,
            final,
            stopped,
            time.monotonic() - start,
            spec.log_path,
            detection,
            latency,
            "perf_counter",
            None,
            oom_kills,
        )


def container_workdir(path: PurePosixPath | str) -> str:
    """Where a run sees its working folder."""
    del path
    return WORK


def environment_for_build() -> dict[str, str]:
    """The variables a build adds (the allowlist proxy); for the record."""
    return {"HTTP_PROXY": PROXY_URL, "HTTPS_PROXY": PROXY_URL}


def is_vm() -> bool:
    """True on the Refute VM (a Linux host with cgroup v2 and the docker CLI)."""
    return os.name == "posix" and Path("/sys/fs/cgroup/cgroup.controllers").exists()
