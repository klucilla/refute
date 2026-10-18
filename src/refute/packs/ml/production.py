"""The production wiring of the ML pack: from a resolved claim file to a dossier, on the
Refute VM with the docker backend (the maintainer's decision of 2026-10-17; the design
decided with Codex: the whole engine runs on the VM).

What this module does, in order (``run_production``):

1. **Workspaces** (WP3 integration requirement 10): one fresh folder per container of the
   plan (``integration.plan_container_ids``), each a copy of the repository at the pinned
   commit (``.git`` left out). A run container's folder also gets each declared dataset
   at the path the setup names, as a **hard link to the fetched file made read-only**: a
   run, which is a user that does not own it (``RUN_UID``), can neither change nor replace
   its bytes, and every run reads the same file Refute fetched and hashed.
2. **The build ladder** (plan 6.1, WP3 W3.9), with images fixed by Refute's code and
   pinned by digest, never chosen by the repository:
   - ``own_environment``: an ``environment.yml`` / ``environment.yaml`` is created as is
     with micromamba (``MICROMAMBA_IMAGE``) into ``/opt/conda/envs/env``; when the file
     names no channel, ``conda-forge`` is used, and this is recorded. A repository whose
     own environment is a Dockerfile only is not built by version 1 (decided by the
     maintainer on 2026-10-17): that rung ends as a Refute error (``EXIT_NOT_SUPPORTED``),
     the ladder stops and the gate is ``INCONCLUSIVE``, never the artifact's failure;
   - ``requirements_compiled`` and ``..._next_python``: in the claim's ``build.base_image``,
     ``uv`` (pinned) creates ``/opt/venv`` with the rung's Python and installs the
     requirements compiled with ``--exclude-newer`` of the claim; the lock file is kept
     in the build's folder for the dossier.
   A build reaches the internet only through the allowlist proxy and is committed as the
   paper's image when it exits 0 (docker backend).
3. **Classification of a build** (``classify_build``): exit 0 built; the threshold and the
   guards keep their causes; a refusal of the proxy or a network error is a cause on
   Refute's side (``transient_network``), never the artifact's; any other non-zero exit
   is an error of the procedure itself (``artifact_build_ladder``), which the WP2 core
   counts only when all three rungs ran and failed.
4. **The harness** (``integration.Harness``): the docker backend, the workspaces, the
   logs, the command (a claim's ``python`` is the built environment's), the dataset
   evidence, the ladder, the margin M (1.4a, from the V22 maxima), the parent cgroup's
   usage and the tolerance T, and the **base environment** of every run (``BASE_ENV``):
   fixed by Refute, the same for every paper, covered by the code hash and recorded in
   the dossier. It turns off, without any account or network, the experiment trackers
   and hubs a repository may call (``WANDB_MODE=disabled``: "If you set this to disabled
   wandb will turn off completely", https://docs.wandb.ai/guides/track/environment-variables/,
   read 2026-10-17).
5. **The run and the dossier** (``integration.run_paper``, then ``write_dossier``): the
   claim file, the setup, the images, every container record, the ladder, the gates, the
   attacks and the claim profile, as canonical JSON, with the logs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import shutil
import signal
import stat
import subprocess
import sys
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path, PurePosixPath
from typing import Any

from refute.core.canonical import canonical_bytes
from refute.core.paper import FailureCause
from refute.packs.ml import integration as ig
from refute.packs.ml import ladder as ld
from refute.packs.ml import orchestrate as orc
from refute.packs.ml import readers as rd
from refute.packs.ml import repository
from refute.packs.ml.docker_backend import ContainerPlan, DockerBackend, Limits
from refute.packs.ml.fetch import ArtifactSpec, fetch_artifact
from refute.packs.ml.sandbox import (
    STOP_ACTIVE_TIME,
    STOP_NO_PROGRESS,
    STOP_THRESHOLD,
    RunResult,
    TimingMaxima,
)

DOSSIER_FORMAT = "refute-ml-dossier-1"
UV_VERSION = "0.12.24"
# micromamba's official image, pinned by digest (the maintainer's approval of V4,
# 2026-10-17); its digest is filled when the image is first pulled on the VM, recorded
# with the pull, and never changed after a lock
MICROMAMBA_IMAGE_DEFAULT = ""
EXIT_NOT_SUPPORTED = 97
RUN_UID = 10001
# the V22 maxima measured on the VM on 2026-10-17 (docs/validation/v0.3/wp3-results/
# docker-vm-test-20261017T214010Z.json): detection delay D and stop latency S, in seconds
V22_MAXIMA = TimingMaxima(0.000346, 0.207)
# the file the engine waits for after the setup, before the first base run (the VM's port
# goes from the profile build to pull meanwhile, from the host: .cache/vm/switch-to-run-phase.ps1)
RUN_PHASE_FLAG = "run-phase-approved"
RUN_PHASE_WAIT_S = 12 * 3600
VENV = "/opt/venv"
CONDA_ENV = "/opt/conda/envs/env"
ENV_FILES = ("environment.yml", "environment.yaml")
REQUIREMENTS_FILES = ("requirements.txt",)
BASE_ENV = {
    # experiment trackers and model hubs: off, no account, no network (runs have none)
    "WANDB_MODE": "disabled",
    "WANDB_SILENT": "true",
    "HF_HUB_OFFLINE": "1",
    "HF_DATASETS_OFFLINE": "1",
    "TRANSFORMERS_OFFLINE": "1",
    "MLFLOW_TRACKING_URI": "file:/tmp/mlruns",
    # the environment the build made comes first
    "PATH": f"{VENV}/bin:{CONDA_ENV}/bin:/opt/conda/bin:"
    "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
    "HOME": "/tmp",
    "PYTHONDONTWRITEBYTECODE": "1",
    "PYTHONUNBUFFERED": "1",
}  # fmt: skip
# a build's log line that means the network or the proxy, not the artifact
_NETWORK = re.compile(
    r"(Tunnel connection failed|403 Forbidden|CONNECT tunnel failed|Could not resolve host|"
    r"Temporary failure in name resolution|Connection (?:reset|refused|timed out)|"
    r"Read timed out|ConnectTimeoutError|NewConnectionError|Network is unreachable|"
    r"CERTIFICATE_VERIFY_FAILED|SSLError|SSL: |certificate verify failed|"
    r"Failed to fetch|failed to download|HTTP error 5\d\d)",
    re.IGNORECASE,
)
# the only build failures counted as an error of the procedure itself (an artifact cause,
# plan 8.2): the declared environment cannot be resolved (Codex review of 3dd85e2: reserve
# artifact_build_ladder for a failure positively identified as the procedure's)
_PROCEDURE = re.compile(
    r"(No solution found when resolving|Because .+ we can conclude that .+ unsatisfiable|"
    r"ResolutionImpossible|Could not find a version that satisfies the requirement|"
    r"No matching distribution found for|Could not solve for environment specs|"
    r"LibMambaUnsatisfiableError|nothing provides .+ needed by|"
    r"does not exist \(os error 2\)|No such file or directory: '/work/)",
)


class ProductionError(RuntimeError):
    """The setup of a paper cannot be prepared (before any container runs)."""


@dataclass(frozen=True)
class PaperSetup:
    """Everything the run of one paper needs besides the claim file. Fixed before the run
    and written whole into the dossier."""

    paper: str  # the paper's slice id: lowercase letters and digits
    root: Path  # an empty folder of this run on the VM
    repo: Path  # the repository at the claim's commit, prepared by Refute (read only)
    datasets: Mapping[str, ig.DatasetEvidence]  # by dataset name
    data_layout: Mapping[str, str]  # dataset name -> relative path in a run's folder
    limits: Limits
    timing: TimingMaxima
    micromamba_image: str = MICROMAMBA_IMAGE_DEFAULT
    exclude_newer: str = ""  # filled from the claim when empty
    extra_env: Mapping[str, str] = field(default_factory=dict)  # e.g. a data folder variable

    def record(self) -> dict[str, Any]:
        return {
            "paper": self.paper,
            "data_layout": dict(self.data_layout),
            "limits": asdict(self.limits),
            "timing_maxima": asdict(self.timing),
            "micromamba_image": self.micromamba_image,
            "base_env": dict(BASE_ENV),
            "extra_env": dict(self.extra_env),
            "run_uid": RUN_UID,
            "uv_version": UV_VERSION,
        }


# ---- the margin and the tolerance (1.4a) --------------------------------------------------


def margin_usec(limits: Limits, timing: TimingMaxima, n_cpu: int = 24, slice_us: int = 5000) -> int:
    """M = 2 x C x (P + delta + D + S) + N x sigma, in integer microseconds, rounded up."""
    period_s = limits.period_us / 1_000_000
    m = 2 * limits.cpus * (period_s + 1.0 + timing.detection_delay_s + timing.stop_latency_s)
    m += n_cpu * slice_us / 1_000_000
    return math.ceil(m * 1_000_000)


def tolerance_usec(n_containers: int) -> int:
    """T = 1 CPU-s x (n + 1), in microseconds (1.4a)."""
    return 1_000_000 * (n_containers + 1)


# ---- the ladder's inputs and commands ------------------------------------------------------


def ladder_inputs(repo: Path) -> tuple[str | None, str | None, str | None]:
    """The own environment file, the requirements file, and a Dockerfile, found at the
    repository's root (the plan's ladder reads the root only)."""
    env = next((n for n in ENV_FILES if (repo / n).is_file()), None)
    dockerfile = "Dockerfile" if (repo / "Dockerfile").is_file() else None
    req = next((n for n in REQUIREMENTS_FILES if (repo / n).is_file()), None)
    return env, req, dockerfile


def env_file_channels(path: Path) -> list[str]:
    """The channels an environment file names (a plain reading of the ``channels:`` list)."""
    channels, inside = [], False
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if re.match(r"^channels\s*:", line):
            inside = True
            continue
        if inside:
            m = re.match(r"^\s*-\s*(\S+)", line)
            if m:
                channels.append(m.group(1))
            elif line.strip() and not line.startswith((" ", "\t")):
                inside = False
    return channels


def build_script(rung: ld.Rung, repo: Path, exclude_newer: str) -> list[str]:
    """The command of one rung's build container, run in /work (a copy of the repository)."""
    env, req, dockerfile = ladder_inputs(repo)
    if rung.name == ld.RUNGS[0]:
        if env is None:
            # a Dockerfile only: not built by version 1 (decided by the maintainer)
            assert dockerfile is not None
            message = "refute: version 1 does not build a Dockerfile"
            return ["sh", "-c", f"echo '{message}' >&2; exit {EXIT_NOT_SUPPORTED}"]
        channels = env_file_channels(repo / env)
        extra = "" if channels else " -c conda-forge"
        script = f"set -eu; micromamba create -y -p {CONDA_ENV} -f /work/{env}{extra}; "
        script += "micromamba clean -a -y"
        return ["sh", "-c", script]
    if req is None or rung.python is None:
        raise ProductionError(f"rung {rung.name} has no input")
    script = (
        "set -eu; mkdir -p /work/.refute; "
        f"python -m pip install --no-cache-dir uv=={UV_VERSION}; "
        "export UV_PYTHON_INSTALL_DIR=/opt/uv-python UV_NO_CACHE=1; "
        f"uv venv --python {rung.python} {VENV}; "
        f"uv pip compile --python {VENV}/bin/python --exclude-newer {exclude_newer} "
        f"/work/{req} -o /work/.refute/requirements.lock; "
        f"uv pip install --python {VENV}/bin/python -r /work/.refute/requirements.lock"
    )  # fmt: skip
    return ["sh", "-c", script]


def classify_build(rung: ld.Rung, result: RunResult | None) -> ld.RungResult:
    if result is None:
        return ld.RungResult(orc.Outcome.REFUTE_ERROR, None, "the build container did not run")
    if result.stopped == STOP_THRESHOLD:
        return ld.RungResult(orc.Outcome.BUDGET_EXHAUSTED, None, "stopped at its threshold")
    if result.stopped in (STOP_ACTIVE_TIME, STOP_NO_PROGRESS):
        return ld.RungResult(orc.Outcome.OPERATIONAL_GUARD, None, f"stopped: {result.stopped}")
    if result.exit_code == 0:
        return ld.RungResult(orc.Outcome.COMPLETED)
    text = result.log_path.read_text(encoding="utf-8", errors="replace")
    if result.exit_code == EXIT_NOT_SUPPORTED and "version 1 does not build" in text:
        return ld.RungResult(orc.Outcome.REFUTE_ERROR, None, "a Dockerfile: not built by version 1")
    if result.exit_code in (137, -9):
        # killed: out of memory or a signal, never the artifact's (Codex review of 3dd85e2)
        return ld.RungResult(orc.Outcome.OPERATIONAL_GUARD, None, "the build was killed (137)")
    network = _NETWORK.search(text)
    if network:
        return ld.RungResult(
            orc.Outcome.FAILED, FailureCause.TRANSIENT_NETWORK, f"network: {network.group(0)}"
        )
    procedure = _PROCEDURE.search(text)
    if procedure:
        # an error of the procedure itself, positively identified: the declared
        # environment cannot be resolved
        return ld.RungResult(
            orc.Outcome.FAILED, FailureCause.BUILD_LADDER, f"procedure: {procedure.group(0)}"
        )
    # anything else is undetermined: it stops the ladder and is never the artifact's cause
    return ld.RungResult(
        orc.Outcome.FAILED, FailureCause.UNDETERMINED, f"exit code {result.exit_code}"
    )


# ---- the workspaces -------------------------------------------------------------------------


def _safe(cid: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]", "_", cid)


def _inside(root: Path, path: Path) -> bool:
    r = os.path.realpath(root)
    return os.path.commonpath([r, os.path.realpath(path)]) == r


def _copy_repo(repo: Path, dest: Path) -> None:
    """A copy of the repository (no .git). A symbolic link of the repository that resolves
    outside it is refused before any run (Codex review of 3dd85e2): the paper cannot run,
    on Refute's side."""
    shutil.copytree(repo, dest, ignore=shutil.ignore_patterns(".git"), symlinks=True)
    for p in [dest, *dest.rglob("*")]:
        if p.is_symlink():
            if not _inside(dest, p):
                raise ProductionError(
                    f"the repository has a link that leaves it: {p.relative_to(dest)}"
                )
            continue
        mode = p.stat().st_mode
        # a run (another uid) may write its outputs anywhere in its own copy
        p.chmod(mode | stat.S_IRWXO if p.is_dir() else mode | stat.S_IROTH | stat.S_IWOTH)


def check_data_layout(layout: Mapping[str, str]) -> None:
    """Each dataset's path in a run's folder: relative, no '..', not under .refute."""
    for name, rel in layout.items():
        posix = PurePosixPath(rel)
        if posix.is_absolute() or not posix.parts or ".." in posix.parts or "\\" in rel:
            raise ProductionError(f"data path of {name} must be relative, without '..': {rel!r}")
        if posix.parts[0] == ".refute":
            raise ProductionError(f"data path of {name} is under .refute: {rel!r}")


def prepare_workspaces(setup: PaperSetup, claim_file: Mapping[str, Any]) -> dict[str, Path]:
    """One copy of the repository per container. The datasets are not copied: a run gets
    them as read-only bind mounts (``data_mounts``), so it can neither change nor replace
    them (Codex review of 3dd85e2)."""
    check_data_layout(setup.data_layout)
    ws_root = setup.root / "ws"
    ws_root.mkdir(parents=True)
    workspaces = {}
    for cid in ig.plan_container_ids(claim_file):
        folder = ws_root / _safe(cid)
        _copy_repo(setup.repo, folder)
        if not cid.startswith("setup/"):
            for rel in setup.data_layout.values():
                target = folder / PurePosixPath(rel)
                if target.exists() or target.is_symlink():
                    raise ProductionError(f"{rel} exists in the repository: the data path collides")
                if not _inside(folder, target.parent):
                    raise ProductionError(f"the data path {rel} leaves the run's folder")
        workspaces[cid] = folder
    return workspaces


def data_mounts(setup: PaperSetup) -> tuple[tuple[str, str], ...]:
    mounts = []
    for name, rel in setup.data_layout.items():
        path = setup.datasets[name].fetch.path
        if path is None:
            continue  # absent: the data_present gate records it
        Path(path).chmod(0o444)  # the canonical file: read only for everyone
        mounts.append((str(Path(path).resolve()), rel))
    return tuple(mounts)


# ---- the harness ----------------------------------------------------------------------------


def build_harness(
    setup: PaperSetup,
    claim_file: Mapping[str, Any],
    after_setup: Callable[[], None] | None = None,
) -> tuple[ig.Harness, DockerBackend]:
    plan = claim_file["test_plan"]
    if setup.root.exists() and any(setup.root.iterdir()):
        raise ProductionError(f"the run folder {setup.root} is not empty")
    setup.root.mkdir(parents=True, exist_ok=True)
    env_file, req, dockerfile = ladder_inputs(setup.repo)
    own = env_file or dockerfile
    exclude_newer = setup.exclude_newer or plan["build"]["exclude_newer"]
    workspaces = prepare_workspaces(setup, claim_file)
    image = f"refute-local/{setup.paper}/env"
    plans: dict[Path, ContainerPlan] = {}
    for cid, folder in workspaces.items():
        if cid.startswith("setup/build/"):
            rung = cid.rsplit("/", 1)[1]
            base = plan["build"]["base_image"]
            if rung == ld.RUNGS[0] and env_file is not None:
                if not setup.micromamba_image:
                    raise ProductionError("the micromamba image is not pinned")
                base = setup.micromamba_image
            plans[folder] = ContainerPlan(base, network="proxy", commit_as=image, read_only=False)
        else:
            plans[folder] = ContainerPlan(image, data_mounts=data_mounts(setup))
    backend = DockerBackend(setup.paper, setup.limits, plans)
    rung_by_name: dict[str, ld.Rung] = {}

    def build_command(rung: ld.Rung) -> list[str]:
        rung_by_name[rung.name] = rung
        return build_script(rung, setup.repo, exclude_newer)

    harness = ig.Harness(
        backend=backend,
        workspaces=workspaces,
        logs=setup.root / "logs",
        command=lambda argv: list(argv),
        datasets=dict(setup.datasets),
        ladder_inputs=(own, req),
        build_command=build_command,
        classify_build=classify_build,
        margin_usec=margin_usec(setup.limits, setup.timing),
        timing_maxima=setup.timing,
        base_env={**BASE_ENV, **setup.extra_env},
        parent_usage=backend.parent_usage,
        # T from the containers that actually started (Codex review of 3dd85e2)
        tolerance_usec=tolerance_usec,
        after_setup=after_setup,
    )
    return harness, backend


# ---- the dossier ----------------------------------------------------------------------------


def _plain(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return {k: _plain(v) for k, v in asdict(value).items()}
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, Mapping):
        return {str(k): _plain(v) for k, v in value.items()}
    if isinstance(value, list | tuple | set | frozenset):
        return [_plain(v) for v in value]
    if isinstance(value, float) and not math.isfinite(value):
        return str(value)
    if isinstance(value, int | float | str | bool) or value is None:
        return value
    return str(value)


def write_dossier(
    out: Path, setup: PaperSetup, claim_file: Mapping[str, Any], outcome: ig.PaperOutcome,
    images: Mapping[str, str], started_utc: str,
) -> Path:  # fmt: skip
    """The dossier of one paper run: canonical JSON plus the logs, written into a new
    folder (never over an existing one)."""
    out.mkdir(parents=True)
    record = {
        "format": DOSSIER_FORMAT,
        "started_utc": started_utc,
        "finished_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "claim_file_sha256": hashlib.sha256(canonical_bytes(_plain(claim_file))).hexdigest(),
        "setup": setup.record(),
        "images": dict(images),
        "outcome": _plain(outcome),
    }
    (out / "claim_file.json").write_bytes(canonical_bytes(_plain(claim_file)))
    (out / "dossier.json").write_bytes(canonical_bytes(record))
    logs = setup.root / "logs"
    if logs.is_dir():
        shutil.copytree(logs, out / "logs")
    lock = next(iter(setup.root.glob("ws/setup_build_*/.refute/requirements.lock")), None)
    if lock is not None:
        shutil.copy2(lock, out / "requirements.lock")
    return out


def run_production(
    setup: PaperSetup, claim_file: Mapping[str, Any], out: Path,
    image_digests: Mapping[str, str], after_setup: Callable[[], None] | None = None,
    stop_on_sigterm: bool = False,
) -> ig.PaperOutcome:  # fmt: skip
    started = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    harness, backend = build_harness(setup, claim_file, after_setup)
    if stop_on_sigterm:
        # systemctl stop sends SIGTERM to the engine: its own containers (by id) are killed
        # first, so stopping the paper's unit stops every container of the paper (Codex
        # review of 3dd85e2: the containers live in another slice than the unit)
        def stop(signum: int, frame: Any) -> None:
            killed = backend.kill_active()
            print(f"SIGTERM: killed {len(killed)} container(s); the paper stops", flush=True)
            raise SystemExit(143)

        signal.signal(signal.SIGTERM, stop)
    outcome = ig.run_paper(claim_file, harness)
    write_dossier(out, setup, claim_file, outcome, image_digests, started)
    return outcome


def outcome_summary(outcome: ig.PaperOutcome) -> str:
    """One line per claim, for the console and the watcher."""
    lines = [f"ladder: built with {outcome.ladder.built_with}"]
    for c in outcome.claims:
        lines.append(f"{c.key}: {c.verdict}")
    return "\n".join(lines)


def dump(value: Any) -> str:
    return json.dumps(_plain(value), indent=2, sort_keys=True)


# ---- the inputs: the repository and the declared datasets (W3.6, W3.7) ----------------------


def prepare_inputs(
    claim_file: Mapping[str, Any], root: Path, cache: Path
) -> tuple[Path, dict[str, ig.DatasetEvidence]]:
    """Clones the repository at the claim's commit and fetches every declared dataset with
    Refute's fetcher (with the build, the only network access of a paper run, through the
    allowlist proxy). The splits are counted by ``readers``; an unreadable split gives no
    count, so ``data_present`` is ``INCONCLUSIVE``, never a pass."""
    plan = claim_file["test_plan"]
    repo = repository.clone(plan["repository"]["url"], root / "source")
    repository.checkout(repo, plan["repository"]["commit"])
    absent = plan["absent_artifact"]
    datasets: dict[str, ig.DatasetEvidence] = {}
    for d in plan["datasets"]:
        spec = ArtifactSpec(d["name"], d["url"], d["sha256"], int(d["size_bytes"]))
        result = fetch_artifact(
            spec,
            cache,
            attempts=int(absent["attempts"]),
            interval_s=float(absent["interval_minutes"]) * 60,
        )
        counts = rd.split_counts(result.path, d["splits"]) if result.path is not None else None
        datasets[d["name"]] = ig.DatasetEvidence(result, counts)
    return repo, datasets


# ---- the paper's slice and the run phase ----------------------------------------------------


def limit_paper_slice(paper: str, memory_bytes: int, cpus: float) -> None:
    """The paper's slice's memory (no swap) and CPU limits, set before Docker creates it, so
    the containers of one step together stay inside them (V4 terms; observed on the VM on
    2026-10-17: the properties apply to the slice Docker creates afterwards)."""
    subprocess.run(
        ["sudo", "-n", "systemctl", "set-property", "--runtime", f"refute-{paper}.slice",
         f"MemoryMax={memory_bytes}", "MemorySwapMax=0", f"CPUQuota={round(cpus * 100)}%"],
        check=True, capture_output=True, text=True, timeout=60,
    )  # fmt: skip


def wait_for_run_phase(
    flag: Path, timeout_s: float = RUN_PHASE_WAIT_S, sleep: Callable[[float], None] = time.sleep
) -> Callable[[], None]:
    """The hook between the setup and the first base run: it writes that the setup ended and
    waits for ``flag`` (the host creates it after the VM's port is in the profile pull). No
    flag within the time limit stops the paper (a Refute error, INCONCLUSIVE)."""

    def hook() -> None:
        status = flag.with_name("status.txt")
        status.write_text("setup done; waiting for the run phase\n", encoding="utf-8")
        print("setup done; waiting for the run phase", flush=True)
        waited = 0.0
        while not flag.exists():
            if waited >= timeout_s:
                raise ProductionError(f"the run phase was not approved within {timeout_s:.0f} s")
            sleep(10)
            waited += 10
        status.write_text("run phase\n", encoding="utf-8")
        print("run phase approved", flush=True)

    return hook


# ---- the entry point of the paper's systemd unit (scripts/vm/launch-paper.sh) ---------------


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run one ML paper on the Refute VM.")
    parser.add_argument("--claim", type=Path, required=True, help="resolved claim file (JSON)")
    parser.add_argument("--paper", required=True, help="the paper's slice id")
    parser.add_argument("--root", type=Path, required=True, help="a new folder for this run")
    parser.add_argument("--out", type=Path, required=True, help="the dossier folder (new)")
    parser.add_argument("--cache", type=Path, required=True, help="the dataset cache")
    parser.add_argument("--data", action="append", default=[], help="dataset=relative path")
    parser.add_argument("--micromamba-image", default="")
    parser.add_argument("--run-phase-flag", type=Path, help="wait for this file after the setup")
    parser.add_argument("--min-free-gb", type=float, default=15.0)
    args = parser.parse_args(argv)
    claim_file = json.loads(args.claim.read_text(encoding="utf-8"))
    if shutil.disk_usage(Path.home()).free < args.min_free_gb * 1e9:
        print(f"refused: less than {args.min_free_gb:g} GB free on the VM", flush=True)
        return 2
    args.root.mkdir(parents=True)
    repo, datasets = prepare_inputs(claim_file, args.root, args.cache)
    layout = dict(item.split("=", 1) for item in args.data)
    limits = Limits(cpus=22, period_us=100_000, memory_bytes=12 << 30, pids=4096)
    limit_paper_slice(args.paper, 13 << 30, 22)
    setup = PaperSetup(
        paper=args.paper,
        root=args.root / "run",
        repo=repo,
        datasets=datasets,
        data_layout=layout,
        limits=limits,
        timing=V22_MAXIMA,
        micromamba_image=args.micromamba_image,
    )
    hook = wait_for_run_phase(args.run_phase_flag) if args.run_phase_flag else None
    images = {
        "micromamba": args.micromamba_image,
        "base": claim_file["test_plan"]["build"]["base_image"],
    }
    outcome = run_production(setup, claim_file, args.out, images, hook, stop_on_sigterm=True)
    print(outcome_summary(outcome), flush=True)
    return 0


__all__: Sequence[str] = (
    "BASE_ENV",
    "PaperSetup",
    "ProductionError",
    "build_harness",
    "build_script",
    "classify_build",
    "ladder_inputs",
    "margin_usec",
    "prepare_inputs",
    "run_production",
    "tolerance_usec",
    "wait_for_run_phase",
    "write_dossier",
)


if __name__ == "__main__":
    sys.exit(main())
