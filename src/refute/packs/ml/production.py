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

import hashlib
import json
import math
import os
import re
import shutil
import stat
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

from refute.core.canonical import canonical_bytes
from refute.core.paper import FailureCause
from refute.packs.ml import integration as ig
from refute.packs.ml import ladder as ld
from refute.packs.ml import orchestrate as orc
from refute.packs.ml.docker_backend import ContainerPlan, DockerBackend, Limits
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
    r"Read timed out|ConnectTimeoutError|NewConnectionError|Network is unreachable)",
    re.IGNORECASE,
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
    text = result.log_path.read_text(encoding="utf-8", errors="replace")[-200_000:]
    if result.exit_code == EXIT_NOT_SUPPORTED and "version 1 does not build" in text:
        return ld.RungResult(orc.Outcome.REFUTE_ERROR, None, "a Dockerfile: not built by version 1")
    match = _NETWORK.search(text)
    if match:
        return ld.RungResult(
            orc.Outcome.FAILED, FailureCause.TRANSIENT_NETWORK, f"network: {match.group(0)}"
        )
    return ld.RungResult(
        orc.Outcome.FAILED, FailureCause.BUILD_LADDER, f"exit code {result.exit_code}"
    )


# ---- the workspaces -------------------------------------------------------------------------


def _safe(cid: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]", "_", cid)


def _copy_repo(repo: Path, dest: Path) -> None:
    shutil.copytree(repo, dest, ignore=shutil.ignore_patterns(".git"), symlinks=True)
    for p in [dest, *dest.rglob("*")]:
        if p.is_symlink():
            continue
        mode = p.stat().st_mode
        # a run (another uid) may write its outputs anywhere in its own copy
        p.chmod(mode | stat.S_IRWXO if p.is_dir() else mode | stat.S_IROTH | stat.S_IWOTH)


def _link_data(fetched: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    fetched.chmod(0o444)  # the canonical file: read only for everyone, owned by the engine
    if target.exists() or target.is_symlink():
        raise ProductionError(f"{target} exists in the repository copy: the data path collides")
    os.link(fetched, target)


def prepare_workspaces(setup: PaperSetup, claim_file: Mapping[str, Any]) -> dict[str, Path]:
    ws_root = setup.root / "ws"
    ws_root.mkdir(parents=True)
    workspaces = {}
    for cid in ig.plan_container_ids(claim_file):
        folder = ws_root / _safe(cid)
        _copy_repo(setup.repo, folder)
        if not cid.startswith("setup/"):
            for name, rel in setup.data_layout.items():
                evidence = setup.datasets[name]
                if evidence.fetch.path is None:
                    continue  # absent: the data_present gate records it
                _link_data(Path(evidence.fetch.path), folder / rel)
        workspaces[cid] = folder
    return workspaces


# ---- the harness ----------------------------------------------------------------------------


def build_harness(
    setup: PaperSetup, claim_file: Mapping[str, Any]
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
            plans[folder] = ContainerPlan(image)
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
        tolerance_usec=tolerance_usec(len(workspaces)),
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
    image_digests: Mapping[str, str],
) -> ig.PaperOutcome:  # fmt: skip
    started = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    harness, _backend = build_harness(setup, claim_file)
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


__all__: Sequence[str] = (
    "BASE_ENV",
    "PaperSetup",
    "ProductionError",
    "build_harness",
    "build_script",
    "classify_build",
    "ladder_inputs",
    "margin_usec",
    "run_production",
    "tolerance_usec",
    "write_dossier",
)
