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
import gzip
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
from datetime import UTC, datetime, timedelta
from enum import Enum
from pathlib import Path, PurePosixPath
from typing import Any

from refute.core.canonical import canonical_bytes
from refute.core.dossier import write_manifest
from refute.core.paper import FailureCause, GateFailure
from refute.packs.ml import extract as ex
from refute.packs.ml import integration as ig
from refute.packs.ml import ladder as ld
from refute.packs.ml import orchestrate as orc
from refute.packs.ml import patches as pt
from refute.packs.ml import readers as rd
from refute.packs.ml import repository
from refute.packs.ml import schema as sch
from refute.packs.ml.docker_backend import ContainerPlan, DockerBackend, Limits
from refute.packs.ml.fetch import ArtifactSpec, FetchResult, fetch_artifact
from refute.packs.ml.sandbox import (
    STOP_ACTIVE_TIME,
    STOP_NO_PROGRESS,
    STOP_OUT_OF_MEMORY,
    STOP_THRESHOLD,
    RunResult,
    TimingMaxima,
)

# format 2 adds the provenance (wp3-dossier-provenance-acceptance.md); the dev dossier of
# 2304.14390 keeps format 1
DOSSIER_FORMAT = "refute-ml-dossier-2"
# the host's record of the VM port's network profile (wp3-dossier-provenance-acceptance.md)
PROFILE_FORMAT = "refute-vm-profile-1"
PROFILE_FIELDS = ("format", "execution_id", "paper", "claim_sha256", "phase", "profile",
                  "read_utc", "checks", "script_sha256")  # fmt: skip
PROFILE_OF_PHASE = {"build": "build", "run": "pull"}
PROFILE_LIMITS = (
    "declared by the operator's scripts from the endpoint's status, not signed by the endpoint;"
    " each tells the profile when it was read, not that it stayed in force"
)
PROFILE_MAX_BYTES = 4096
# the checks a profile record must report, each true (Switch-RefuteVmProfile.ps1)
PROFILE_CHECKS = ("adapter_on_configured_switch", "entries_of_the_profile")
# the largest difference accepted between the host's clock and the VM's (section 1)
CLOCK_SKEW_S = 300
# an execution id: 32 lowercase hex digits, generated by the host's launcher
EXECUTION_ID = re.compile(r"[0-9a-f]{32}")
# a log above this size is stored compressed, losslessly (section 2)
LOG_STORE_LIMIT = 50_000_000
# the engine's store of the bytes read, by SHA-256, in the run folder (section 1)
READ_STORE = "read-store"
UTC_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
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
# the container reader (wp3-data-sources-acceptance.md, section 4.2): Refute's script,
# written into the reader's own folder, run by the image's interpreter with -I -S
READER_SOURCE = Path(__file__).with_name("container_reader.py")
READER_SCRIPT = "reader.py"
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
    r"(Retrying \(Retry\(|too many \d{3} error responses|50\d (?:Server Error|Service Unavailable)|"
    r"status code 5\d\d|Tunnel connection failed|403 Forbidden|CONNECT tunnel failed|"
    r"Could not resolve host|"
    r"Temporary failure in name resolution|Connection (?:reset|refused|timed out)|"
    r"Read timed out|ConnectTimeoutError|NewConnectionError|Network is unreachable|"
    r"CERTIFICATE_VERIFY_FAILED|SSLError|SSL: |certificate verify failed|"
    r"Failed to fetch|failed to download|HTTP error 5\d\d)",
    re.IGNORECASE,
)
# a resolver failure that names the platform: the engine's base image (glibc 2.36) has no
# matching wheel, a limitation of Refute, never the procedure's
# (wp3-run-resources-acceptance.md, section 3)
_PLATFORM = re.compile(
    r"(no wheels with a matching platform tag|"
    r"Wheels are available for .+ on the following platform)",
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
    # the declared weights from outside the repository, recorded as not fetched, checked or
    # mounted by version 1 (wp3-declared-weights-acceptance.md)
    weights: tuple[str, ...] = ()
    # the allowed patches applied to the clone (patches.prepare, W3.9a): their bytes'
    # SHA-256, the touched files and the manifests of the clone and of ``repo``
    patch_record: Mapping[str, Any] = field(default_factory=dict)
    # the weights that are files of the repository, verified after the checkout and
    # mounted read only in every run container (wp3-repository-weights-acceptance.md)
    repository_weights: Mapping[str, ig.WeightsEvidence] = field(default_factory=dict)

    def record(self) -> dict[str, Any]:
        return {
            "weights": {
                "declared": list(self.weights),
                "fetched": False,
                "checked": False,
                "mounted": False,
                "reason": "declared weights from outside the repository are not fetched, "
                "checked or mounted by version 1 (an unsupported capability)",
            }
            if self.weights
            else None,
            "repository_weights": {
                name: {
                    "path": e.rel,
                    "sha256": e.sha256,
                    "verified": e.copy is not None,
                    # planned for every run container; the containers created are in the
                    # run's records
                    "mount_planned": e.copy is not None,
                    "reason": e.reason,
                }
                for name, e in sorted(self.repository_weights.items())
            }
            or None,
            "patches": dict(self.patch_record),
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
        f"uv pip install --python {VENV}/bin/python -r /work/.refute/requirements.lock; "
        # the interpreter's identity (implementation, full version, uv): the environment
        # a count before the lock is bound to (wp3-population-count-acceptance.md, 1)
        f"cp {VENV}/pyvenv.cfg /work/.refute/pyvenv.cfg"
    )  # fmt: skip
    return ["sh", "-c", script]


def reader_argv(rung: str | None, request: str, env: Mapping[str, str]) -> list[str]:
    """The command of a container reader (wp3-data-sources-acceptance.md, section 4.2):
    ``env -i`` with the given variables only (the image's other variables do not reach the
    reader), then the interpreter of the environment the ladder built, by its path, with
    -I -S, so no PYTHONPATH, user site, .pth file or sitecustomize is used, and the request
    as one argument."""
    python = f"{CONDA_ENV}/bin/python" if rung == ld.RUNGS[0] else f"{VENV}/bin/python"
    variables = [f"{k}={v}" for k, v in sorted(env.items())]
    return ["/usr/bin/env", "-i", *variables, python, "-I", "-S", READER_SCRIPT, request]


def classify_build(rung: ld.Rung, result: RunResult | None) -> ld.RungResult:
    if result is None:
        return ld.RungResult(orc.Outcome.REFUTE_ERROR, None, "the build container did not run")
    if result.stopped == STOP_THRESHOLD:
        return ld.RungResult(orc.Outcome.BUDGET_EXHAUSTED, None, "stopped at its threshold")
    if result.stopped in (STOP_ACTIVE_TIME, STOP_NO_PROGRESS, STOP_OUT_OF_MEMORY):
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
    platform = _PLATFORM.search(text)
    if platform:
        return ld.RungResult(
            orc.Outcome.REFUTE_ERROR, None, f"the engine's platform: {platform.group(0)}"
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


def check_copy(folder: Path, expected: Mapping[str, Mapping[str, Any]]) -> None:
    """A repository copy, before any data path is prepared in it, against the patched
    tree's manifest: the same entries, types and bytes, and the modes ``_copy_repo``
    projects (a file gains o+rw, a folder o+rwx; W3.9a, section 3)."""
    got = pt.manifest(folder)
    if set(got) != set(expected):
        extra, missing = sorted(set(got) - set(expected)), sorted(set(expected) - set(got))
        raise ProductionError(f"the copy is not the patched tree: extra {extra}, missing {missing}")
    for rel, want in expected.items():
        have = dict(got[rel])
        want = dict(want)
        if want["type"] == "file":
            want["mode"] = want["mode"] | stat.S_IROTH | stat.S_IWOTH
        elif want["type"] == "dir":
            want["mode"] = want["mode"] | stat.S_IRWXO
        if have != want:
            raise ProductionError(f"the copy differs from the patched tree at {rel}")


def refuse_hook_routes(claim_file: Mapping[str, Any]) -> None:
    """A claim with a ``hook`` coverage route, anywhere, is not supported by this version
    of production (its installation contract is not written: #59): refused before the
    preparation, a limitation of Refute (wp3-allowed-patches-acceptance.md, section 4)."""
    for target in claim_file.get("targets", []):
        for role, evidence in (target.get("coverage_evidence") or {}).items():
            routes = [r.get("route") for r in (evidence or {}).get("routes", [])]
            if "hook" in routes:
                raise ProductionError(
                    f"{target.get('key')}: the {role}'s hook route is not supported by this "
                    "version of production"
                )


def patch_tree(
    claim_file: Mapping[str, Any],
    clone: Path,
    dest: Path,
    patch_bytes: Mapping[str, bytes],
    data_layout: Mapping[str, str],
) -> tuple[Path, dict[str, Any]]:
    """The tree every build and run copies: the clone at the claim's commit, anchored on
    the commit's tree, plus the claim's allowed patches in their listed order (W3.9a). The
    patches given must be exactly the listed ones."""
    plan = claim_file["test_plan"]
    listed = [p["attachment"] for p in plan["build"]["allowed_patches"]]
    if sorted(patch_bytes) != sorted(listed):
        raise ProductionError(
            f"the patches given {sorted(patch_bytes)} are not the listed {listed}"
        )
    commit = plan["repository"]["commit"]
    entries = pt.commit_entries(repository.ls_tree(clone, commit))
    # no patch may touch a data path or a file of the repository Refute verified (datasets,
    # weights: wp3-repository-weights-acceptance.md)
    data_paths = sorted(
        {*data_layout.values()}
        | {d["path"] for d in plan["datasets"] if sch.dataset_origin(d) == sch.REPOSITORY_FILE}
        | {
            w["path"]
            for w in plan.get("weights", [])
            if sch.weights_origin(w) == sch.REPOSITORY_FILE
        }
    )
    try:
        record = pt.prepare(clone, dest, [(n, patch_bytes[n]) for n in listed], data_paths, entries)
    except pt.PatchError as exc:
        raise ProductionError(f"the allowed patches: {exc}") from None
    return dest, record


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
    # the files of the repository that are datasets: each run and reader mounts the copy
    # Refute verified before the build in their place (wp3-data-sources-acceptance.md, 1)
    # every path compared normalized: a/b, a//b and a/./b are one mount target (Codex
    # review); a path two dataset entries share is prepared once (round 2)
    repository_files, unverified = set(), set()
    for d in (claim_file.get("test_plan") or {}).get("datasets", []):
        if sch.dataset_origin(d) == sch.REPOSITORY_FILE:
            if setup.data_layout.get(d["name"]) != d["path"]:
                # mounted anywhere else, the runs would read the clone's unverified copy
                raise ProductionError(
                    f"dataset {d['name']} is the repository file {d['path']}: its data path "
                    "must be that path"
                )
            evidence = setup.datasets.get(d["name"])
            if evidence is not None and evidence.fetch.ok:
                repository_files.add(_norm(d["path"]))  # a verified copy replaces the clone's
            else:
                # no verified copy: nothing is mounted there, the runs see the clone as it
                # is, and data_present is not a pass (section 1)
                unverified.add(_norm(d["path"]))
    both = sorted(repository_files & unverified)
    if both:
        raise ProductionError(f"two datasets name {both}: one verified, one not")
    # the weights that are files of the repository, verified: in the runs' containers only
    # (not the builds, not the readers), the clone's copy leaves and the verified copy is
    # mounted there (wp3-repository-weights-acceptance.md); unverified, nothing is mounted
    # and the claims that name them are not run
    weights = [_norm(e.rel) for e in setup.repository_weights.values() if e.copy is not None]
    data_paths = list(dict.fromkeys(_norm(r) for r in setup.data_layout.values()))
    collide = sorted(set(weights) & set(data_paths))
    if collide:
        raise ProductionError(f"a weights file is also a data path: {collide}")
    repository_files.update(weights)
    for cid in ig.plan_container_ids(claim_file):
        folder = ws_root / _safe(cid)
        if cid.startswith(ig.READER_PREFIX):
            # a container reader runs in a fresh folder of its own, never in the clone,
            # with only Refute's reader script (section 4.2)
            folder.mkdir()
            (folder / READER_SCRIPT).write_bytes(READER_SOURCE.read_bytes())
            (folder / READER_SCRIPT).chmod(0o444)
        else:
            _copy_repo(setup.repo, folder)
            if setup.patch_record:
                # the copy is the patched tree, byte for byte (W3.9a, section 3)
                check_copy(folder, setup.patch_record["patched_manifest"])
        if not cid.startswith("setup/build/"):
            mounted = list(data_paths)
            if not cid.startswith(ig.READER_PREFIX):
                mounted += weights
            for rel in mounted:
                if rel in unverified:
                    continue
                target = folder / PurePosixPath(rel)
                # no component of a data path may be a link: the sticky folders below are
                # then the real ancestors of the mount (Codex review of 6289608)
                component = folder
                for part in PurePosixPath(rel).parts[:-1]:
                    component = component / part
                    if component.is_symlink():
                        raise ProductionError(f"the data path {rel} goes through a link: {part}")
                if rel in repository_files and not cid.startswith(ig.READER_PREFIX):
                    # the clone's own copy leaves; the verified copy is mounted there
                    if target.is_symlink() or not target.is_file():
                        raise ProductionError(f"{rel} is not a regular file of the repository")
                    target.unlink()
                if target.exists() or target.is_symlink():
                    raise ProductionError(f"{rel} exists in the repository: the data path collides")
                target.parent.mkdir(parents=True, exist_ok=True)
                if not _inside(folder, target.parent):
                    raise ProductionError(f"the data path {rel} leaves the run's folder")
                # the run's folder and every folder above a data path are sticky: the run
                # (another uid) may add files there but can neither rename nor remove what
                # the engine owns, so the mounted file cannot be swapped by renaming one of
                # its folders (Codex review of 6755d61)
                for d in [target.parent, *target.parent.parents]:
                    if not _inside(folder, d):
                        break
                    d.chmod(0o1777)
            folder.chmod(0o1777)
        workspaces[cid] = folder
    return workspaces


def _norm(rel: str) -> str:
    """A relative path in a run's folder, normalized (a//b and a/./b are a/b)."""
    return str(PurePosixPath(rel))


def data_mounts(setup: PaperSetup, weights: bool = True) -> tuple[tuple[str, str], ...]:
    """The read-only mounts of a container: every dataset Refute holds, and (``weights``:
    a run's container) every verified weights file of the repository; one mount per
    normalized path, so two dataset entries naming one file mount it once, and two
    different sources for one path are refused (Codex review, round 2)."""
    by_target: dict[str, str] = {}

    def add(path: Path | str, rel: str) -> None:
        Path(path).chmod(0o444)  # the canonical file: read only for everyone
        source, target = str(Path(path).resolve()), _norm(rel)
        if by_target.setdefault(target, source) != source:
            raise ProductionError(f"two different files are mounted at {target}")

    for name, rel in setup.data_layout.items():
        evidence = setup.datasets.get(name)
        path = evidence.fetch.path if evidence is not None else None
        if path is None:
            continue  # absent: the data_present gate records it
        add(path, rel)
    if weights:
        for _, e in sorted(setup.repository_weights.items()):
            if e.copy is None:
                continue  # not verified: the claims naming it are not run
            add(e.copy, e.rel)
    return tuple((source, target) for target, source in by_target.items())


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
            run = not cid.startswith(ig.READER_PREFIX)
            plans[folder] = ContainerPlan(image, data_mounts=data_mounts(setup, weights=run))
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
        reader_command=reader_argv,
        data_paths=dict(setup.data_layout),
        weights=dict(setup.repository_weights),
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


def now_utc() -> str:
    return datetime.now(UTC).strftime(UTC_FORMAT)


def refute_checkout(root: Path | None = None) -> tuple[dict[str, Any], bytes | None]:
    """The Refute checkout that holds the imported package: its commit, whether its tracked
    files are unchanged and, when not, the changed paths and the SHA-256 of the diff; and
    the diff's bytes (kept in the dossier as ``refute.diff``), read at this event."""
    root = root or Path(__file__).resolve().parents[4]

    def git(*args: str) -> bytes:
        return subprocess.run(
            ["git", "-C", str(root), *args], capture_output=True, check=True, timeout=60
        ).stdout

    try:
        commit = git("rev-parse", "HEAD").decode().strip()
        status = git("status", "--porcelain", "--untracked-files=no").decode()
        record: dict[str, Any] = {"commit": commit, "tracked_files_unchanged": status == ""}
        diff = None
        if status:
            diff = git("diff", "HEAD", "--binary")
            record["changed"] = sorted(line[3:] for line in status.splitlines())
            record["diff_sha256"] = hashlib.sha256(diff).hexdigest()
            record["diff"] = "refute.diff"
        return record, diff
    except (OSError, subprocess.SubprocessError, UnicodeDecodeError) as exc:
        return {"commit": None, "reason": f"{type(exc).__name__}: {exc}"}, None


def systemd_unit(
    cgroup: str | None = None, env: Mapping[str, str] | None = None
) -> dict[str, Any] | None:
    """The systemd unit the engine runs in (the last ``.service`` of /proc/self/cgroup) and
    its INVOCATION_ID; None outside a unit."""
    if cgroup is None:
        try:
            cgroup = Path("/proc/self/cgroup").read_text(encoding="utf-8")
        except OSError:
            return None
    env = os.environ if env is None else env
    names = [
        part
        for line in cgroup.splitlines()
        for part in line.split(":", 2)[-1].split("/")
        if part.endswith(".service")
    ]
    if not names:
        return None
    return {"name": names[-1], "invocation_id": env.get("INVOCATION_ID")}


def _utc(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.strptime(value, UTC_FORMAT).replace(tzinfo=UTC)
    except ValueError:
        return None
    return parsed if parsed.strftime(UTC_FORMAT) == value else None


def read_profile(
    data: bytes, *, execution_id: str, paper: str, claim_sha256: str, phase: str,
    consumed_utc: str, not_before: str | None = None,
) -> dict[str, Any]:  # fmt: skip
    """The host's record of the network profile in force at ``phase`` (``build``: given at
    the start; ``run``: the run-phase flag), checked: the exact fields with their types,
    this execution (the id the host's launcher generated and gave the engine), this paper,
    this claim file, the phase's profile, every check passed, and its time no later than its
    consumption and no earlier than ``not_before``, each within CLOCK_SKEW_S; ASCII only and
    no key twice. The caller keeps the bytes consumed as a file of the dossier. Anything
    else is a ProductionError."""
    where = f"the profile record of the phase {phase}"
    if len(data) > PROFILE_MAX_BYTES:
        raise ProductionError(f"{where} is larger than {PROFILE_MAX_BYTES} bytes")
    if not data.isascii():
        raise ProductionError(f"{where} is not ASCII")
    try:
        record = json.loads(data.decode("ascii"), object_pairs_hook=_no_duplicates)
    except ValueError as exc:
        raise ProductionError(f"{where} is not JSON (an empty flag included): {exc}") from None
    if not _ascii_only(record):
        raise ProductionError(f"{where} holds a string that is not ASCII")
    if not isinstance(record, dict) or tuple(sorted(record)) != tuple(sorted(PROFILE_FIELDS)):
        raise ProductionError(f"{where} must have exactly the fields {list(PROFILE_FIELDS)}")
    hex64 = re.compile(r"[0-9a-f]{64}")
    passed = record["checks"]
    checks = (
        (record["format"] == PROFILE_FORMAT, "format"),
        (record["execution_id"] == execution_id, "this execution"),
        (record["paper"] == paper, "this paper"),
        (record["claim_sha256"] == claim_sha256, "this claim file"),
        (record["phase"] == phase, "the phase"),
        (record["profile"] == PROFILE_OF_PHASE.get(phase), f"the profile of {phase}"),
        (isinstance(passed, dict) and sorted(passed) == sorted(PROFILE_CHECKS)
         and all(v is True for v in passed.values()),
         f"the checks {list(PROFILE_CHECKS)}, each true"),
        (isinstance(record["script_sha256"], str)
         and hex64.fullmatch(record["script_sha256"]) is not None, "script_sha256"),
    )  # fmt: skip
    for ok, what in checks:
        if not ok:
            raise ProductionError(f"{where}: {what} does not hold")
    read = _utc(record["read_utc"])
    if read is None:
        raise ProductionError(f"{where}: read_utc is not a UTC time {UTC_FORMAT}")
    skew = timedelta(seconds=CLOCK_SKEW_S)
    if read > _utc(consumed_utc) + skew:
        raise ProductionError(f"{where} was read after its consumption at {consumed_utc}")
    if not_before is not None and read < _utc(not_before) - skew:
        raise ProductionError(f"{where} was read before {not_before}")
    return {"record": record, "sha256": hashlib.sha256(data).hexdigest()}


def _no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    keys = [k for k, _ in pairs]
    if len(set(keys)) != len(keys):
        raise ValueError("a key appears twice")
    return dict(pairs)


def _ascii_only(value: Any) -> bool:
    if isinstance(value, str):
        return value.isascii()
    if isinstance(value, dict):
        return all(_ascii_only(k) and _ascii_only(v) for k, v in value.items())
    if isinstance(value, list):
        return all(_ascii_only(v) for v in value)
    return True


def _hash_file(path: Path) -> tuple[str, int]:
    h, size = hashlib.sha256(), 0
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
            size += len(block)
    return h.hexdigest(), size


def copy_logs(src: Path, dest: Path) -> list[dict[str, Any]]:
    """Every log of ``src`` copied under ``dest`` (``logs/``), with its manifest: the path in
    the dossier, the SHA-256 and size as written and, for a log above LOG_STORE_LIMIT, the
    compressed copy (gzip level 9, no name, time 0) and its SHA-256 (section 2)."""
    manifest: list[dict[str, Any]] = []
    if not src.is_dir():
        return manifest
    for path in sorted(src.rglob("*")):
        if path.is_symlink() or (not path.is_file() and not path.is_dir()):
            raise ProductionError(f"a log that is not a regular file: {path.name}")
        if path.is_dir():
            continue
        rel = path.relative_to(src).as_posix()
        digest, size = _hash_file(path)
        entry: dict[str, Any] = {"path": f"logs/{rel}", "sha256": digest, "size": size}
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if size > LOG_STORE_LIMIT:
            stored = target.with_name(target.name + ".gz")
            with path.open("rb") as raw, stored.open("wb") as out:
                with gzip.GzipFile(filename="", mode="wb", compresslevel=9, fileobj=out,
                                   mtime=0) as packed:  # fmt: skip
                    shutil.copyfileobj(raw, packed, 1 << 20)
            with gzip.open(stored, "rb") as check:
                h = hashlib.sha256()
                for block in iter(lambda: check.read(1 << 20), b""):
                    h.update(block)
            if h.hexdigest() != digest:
                raise ProductionError(f"the compressed copy of {rel} differs from the log")
            entry["stored"] = {"path": f"logs/{rel}.gz", "sha256": _hash_file(stored)[0]}
        else:
            shutil.copyfile(path, target)
            if _hash_file(target)[0] != digest:
                raise ProductionError(f"the copy of {rel} differs from the log")
        manifest.append(entry)
    return manifest


def _container_of(workspaces: Mapping[str, Path]) -> dict[str, str]:
    return {os.path.realpath(folder): cid for cid, folder in workspaces.items()}


def copy_sources(
    reads: Sequence[Mapping[str, Any]], workspaces: Mapping[str, Path], store: Path, dest: Path
) -> list[dict[str, Any]]:
    """The provenance of the reads (section 1): each read with its container, a mark when one
    path was read with two SHA-256, and its bytes, kept in the engine's store at the read,
    copied to ``dest`` (``sources/<sha256>``) and checked there on the bytes stored."""
    by_folder = _container_of(workspaces)
    out = []
    for read in reads:
        entry: dict[str, Any] = {
            "container": by_folder.get(read["workdir"]),
            "path": read["path"],
            "sha256": read["sha256"],
            "size": read["size"],
        }
        key = (read["workdir"], read["path"])
        if sum(1 for r in reads if (r["workdir"], r["path"]) == key) > 1:
            entry["divergent"] = True
        kept = store / read["sha256"]
        target = dest / read["sha256"]
        if not read.get("stored") or kept.is_symlink() or not kept.is_file():
            entry["source"] = None
            entry["reason"] = "not kept at the read"
        else:
            if not target.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(kept, target)
            if _hash_file(target)[0] != read["sha256"]:
                raise ProductionError(f"the stored bytes of {read['path']} differ from the read")
            entry["source"] = f"sources/{read['sha256']}"
        out.append(entry)
    return out


def built_environment(
    setup: PaperSetup, outcome: ig.PaperOutcome, dest: Path, image_id: str | None
) -> dict[str, Any]:
    """The rung that built the image, the image's ID, and that rung's resolved lock and
    ``pyvenv.cfg`` copied from its own folder (section 1)."""
    rung = getattr(getattr(outcome, "ladder", None), "built_with", None)
    if rung is None:
        # no rung built: no image of this run (a local image of an earlier run is never
        # attributed to it)
        return {"rung": None, "image_id": None, "reason": "no rung built the environment"}
    record: dict[str, Any] = {"rung": rung, "image_id": image_id}
    built = setup.root / "ws" / _safe(f"setup/build/{rung}") / ".refute"
    for name in ("requirements.lock", "pyvenv.cfg"):
        source = built / name
        if rung == ld.RUNGS[0]:
            record[name] = None
            record[f"{name} reason"] = f"not produced by the rung {rung}"
        elif source.is_file() and not source.is_symlink():
            shutil.copyfile(source, dest / name)
            record[name] = _hash_file(dest / name)[0]
        else:
            record[name] = None
            record[f"{name} reason"] = "absent from the rung's folder"
    record["complete"] = rung == ld.RUNGS[0] or all(
        record[n] is not None for n in ("requirements.lock", "pyvenv.cfg")
    )
    if not record["complete"]:
        record["incomplete"] = "a rung that resolves a lock left no lock or pyvenv.cfg"
    return record


def bind_logs_read(
    reads: Sequence[Mapping[str, Any]], manifest: Sequence[Mapping[str, Any]], logs: Path,
    workspaces: Mapping[str, Path],
) -> list[dict[str, Any]]:  # fmt: skip
    """Each log read, bound to its entry of the logs manifest by path, SHA-256 and size, with
    its container; a read with no entry, or whose bytes differ from the copy, is recorded
    as unbound with the reason (section 1)."""
    root = os.path.realpath(logs)
    by_path = {os.path.join(root, *PurePosixPath(e["path"]).parts[1:]): e for e in manifest}
    by_log = {f"logs/{_safe(cid)}.log": cid for cid in workspaces}
    out = []
    for read in reads:
        entry = by_path.get(read["path"])
        bound: dict[str, Any] = {
            "log": entry["path"] if entry else None,
            "container": by_log.get(entry["path"]) if entry else None,
            "sha256": read["sha256"],
            "size": read["size"],
        }
        if entry is None:
            bound["bound"], bound["reason"] = False, "no log of the dossier at this path"
        elif (entry["sha256"], entry["size"]) != (read["sha256"], read["size"]):
            bound["bound"], bound["reason"] = False, "the log copied differs from the log read"
        else:
            bound["bound"] = True
        out.append(bound)
    return out


def write_dossier(
    out: Path, setup: PaperSetup, claim_file: Mapping[str, Any], outcome: ig.PaperOutcome,
    images: Mapping[str, str], provenance: Mapping[str, Any] | None = None,
    recorded: Mapping[str, Sequence[Mapping[str, Any]]] | None = None,
    workspaces: Mapping[str, Path] | None = None,
) -> Path:  # fmt: skip
    """The dossier of one paper run, written into a new folder (never over an existing
    one), in the order of wp3-dossier-provenance-acceptance.md: the logs, the sources, the
    lock and pyvenv.cfg copied and checked; then dossier.json with the provenance; then
    MANIFEST.sha256 over every file."""
    out.mkdir(parents=True)
    prov = dict(provenance or {})
    recorded = recorded or {"reads": [], "logs": []}
    workspaces = workspaces or {}
    logs = copy_logs(setup.root / "logs", out / "logs")
    prov["logs"] = logs
    prov["logs_read"] = bind_logs_read(recorded["logs"], logs, setup.root / "logs", workspaces)
    for phase, data in sorted((prov.pop("profile_bytes", None) or {}).items()):
        (out / "profiles").mkdir(exist_ok=True)
        (out / "profiles" / f"{phase}.json").write_bytes(data)
        prov.setdefault("profiles", {})[f"{phase} file"] = {
            "path": f"profiles/{phase}.json",
            "sha256": hashlib.sha256(data).hexdigest(),
        }
    claim_input = prov.pop("claim_input", None)
    if claim_input is not None:
        (out / "claim_input.json").write_bytes(claim_input)
        prov["claim_input"] = {
            "path": "claim_input.json",
            "sha256": hashlib.sha256(claim_input).hexdigest(),
        }
    prov["reads"] = copy_sources(
        recorded["reads"], workspaces, setup.root / READ_STORE, out / "sources"
    )
    diff = prov.pop("refute_diff", None)
    if diff is not None:
        (out / "refute.diff").write_bytes(diff)
    prov["datasets"] = [
        {
            "name": name,
            "sha256": evidence.fetch.spec.sha256 if evidence.fetch.ok else None,
            "size": evidence.fetch.spec.size_bytes if evidence.fetch.ok else None,
            "counts": dict(evidence.split_counts) if evidence.split_counts is not None else None,
        }
        for name, evidence in sorted(setup.datasets.items())
    ]
    prov["environment"] = built_environment(setup, outcome, out, prov.pop("image_id", None))
    prov.setdefault("times", {})["dossier_written_utc"] = now_utc()
    record = {
        "format": DOSSIER_FORMAT,
        "claim_file_sha256": hashlib.sha256(canonical_bytes(_plain(claim_file))).hexdigest(),
        "setup": setup.record(),
        "images": dict(images),
        "outcome": _plain(outcome),
        "provenance": _plain(prov),
    }
    (out / "claim_file.json").write_bytes(canonical_bytes(_plain(claim_file)))
    (out / "dossier.json").write_bytes(canonical_bytes(record))
    write_manifest(out)
    return out


def image_id(image: str) -> str | None:
    """The ID of a local image (``docker image inspect``), or None."""
    try:
        done = subprocess.run(
            ["docker", "image", "inspect", "--format", "{{.Id}}", image],
            capture_output=True, text=True, timeout=60, check=False,
        )  # fmt: skip
    except (OSError, subprocess.SubprocessError):
        return None
    found = done.stdout.strip()
    return found if done.returncode == 0 and found.startswith("sha256:") else None


def run_production(
    setup: PaperSetup, claim_file: Mapping[str, Any], out: Path,
    image_digests: Mapping[str, str], after_setup: Callable[[], None] | None = None,
    stop_on_sigterm: bool = False, provenance: dict[str, Any] | None = None,
) -> ig.PaperOutcome:  # fmt: skip
    """One paper run and its dossier. ``provenance`` is filled along the way (the hook adds
    the run's profile record and the image ID after the setup)."""
    prov = provenance if provenance is not None else {}
    times = prov.setdefault("times", {})
    times["run_started_utc"] = now_utc()
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
    with ex.record_reads(setup.root / READ_STORE) as recorded:
        outcome = ig.run_paper(claim_file, harness)
    times["runs_finished_utc"] = now_utc()
    write_dossier(
        out, setup, claim_file, outcome, image_digests, prov, recorded, harness.workspaces
    )
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


@dataclass(frozen=True)
class RepositoryFileSpec(ArtifactSpec):
    """The identity of a repository file read by Refute (never fetched): its ``url`` is
    ``repository:<path>``, so the fetcher's https rule does not apply to it."""

    def __post_init__(self) -> None:
        if not self.url.startswith(sch.REPOSITORY_URL_PREFIX):
            raise ValueError(f"{self.name}: a repository file is named repository:<path>")
        if len(self.sha256) != 64 or any(c not in "0123456789abcdef" for c in self.sha256):
            raise ValueError(f"{self.name}: sha256 is 64 lowercase hex digits")
        if type(self.size_bytes) is not int or self.size_bytes < 1:
            raise ValueError(f"{self.name}: size_bytes is a positive integer")


def repository_file(
    repo: Path, dataset: Mapping[str, Any], cache: Path
) -> ig.DatasetEvidence | None:
    """A dataset that is a file of the repository (wp3-data-sources-acceptance.md, section
    1), read once after the checkout and before any build or code of the repository runs:
    a regular file inside the clone, reached through no link, copied into Refute's cache
    where its SHA-256 and size are checked. Every count and every run reads that copy. A
    missing file, a link or a path that leaves the clone gives no evidence (data_present
    INCONCLUSIVE); other bytes give a failed result with no cause of the artifact (data_present
    FAIL, the claim INCONCLUSIVE)."""
    name, url, sha256, size = sch.artifact_identity(dict(dataset))
    spec = RepositoryFileSpec(name, url, sha256, size)
    copy, why = verified_copy(repo, dataset["path"], sha256, size, cache)
    if copy is None:
        if why != OTHER_BYTES:
            return None  # no file: data_present INCONCLUSIVE (section 1)
        failure = GateFailure(FailureCause.UNDETERMINED)
        return ig.DatasetEvidence(FetchResult(spec, None, False, (), failure), None)
    counts = rd.split_counts(copy, dataset["splits"])
    return ig.DatasetEvidence(FetchResult(spec, copy, True, (), None), counts)


OTHER_BYTES = "other bytes than declared"


def verified_copy(
    repo: Path,
    rel_path: str,
    sha256: str,
    size: int,
    cache: Path,
    entries: Mapping[str, tuple[str, str]] | None = None,
) -> tuple[Path | None, str]:
    """A file of the repository read once after the checkout, before any build or code of
    the repository runs (a dataset, wp3-data-sources-acceptance.md section 1; weights,
    wp3-repository-weights-acceptance.md): a regular file inside the clone, reached through
    no link in any component of its path, copied into Refute's cache (no link there either),
    made read only and hashed again. With ``entries`` (the commit's tree,
    ``patches.commit_entries``) the path must also be a regular blob of the commit with
    these bytes, so a file the commit does not hold (under ``.git``, untracked) is refused.
    Returns the copy and "", or None and why not."""
    current = repo
    for part in PurePosixPath(rel_path).parts:
        current = current / part
        if current.is_symlink():
            return None, "reached through a link"
    if not _inside(repo, current):
        return None, "outside the clone"
    entry = None
    if entries is not None:
        entry = entries.get(str(PurePosixPath(rel_path)))
        if entry is None or entry[0] not in ("100644", "100755"):
            return None, "not a regular file of the commit's tree"
    if not current.exists():
        return None, "missing"
    if not current.is_file():
        return None, "not a regular file"
    data = current.read_bytes()
    if hashlib.sha256(data).hexdigest() != sha256 or len(data) != size:
        return None, OTHER_BYTES
    if entry is not None and pt.blob_sha1(data) != entry[1]:
        return None, "not the commit's bytes"
    folder = cache / "repository-files"
    if _through_link(folder):
        return None, LINKED_CACHE
    folder.mkdir(parents=True, exist_ok=True)
    copy = folder / sha256
    if _through_link(folder) or copy.is_symlink():
        return None, LINKED_CACHE
    if not copy.exists():
        # a new temporary file, created exclusively without following a link (Codex review,
        # round 2): an existing one, a link included, is refused rather than written through
        partial = folder / f".{sha256}.partial"
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
        try:
            fd = os.open(partial, flags | getattr(os, "O_BINARY", 0), 0o600)
        except FileExistsError:
            return None, LINKED_CACHE if partial.is_symlink() else "a partial copy is in the cache"
        with os.fdopen(fd, "wb") as out:
            out.write(data)
        partial.replace(copy)
    copy.chmod(0o444)
    if copy.is_symlink() or hashlib.sha256(copy.read_bytes()).hexdigest() != sha256:
        return None, OTHER_BYTES
    return copy, ""


LINKED_CACHE = "Refute's cache is reached through a link or '..'"


def _through_link(path: Path) -> bool:
    """Whether the path has a '..' component (normalizing it would hide a link before it,
    Codex review, round 3), or the absolute path or a folder above it is a symbolic link."""
    if ".." in Path(path).parts:
        return True
    absolute = Path(os.path.abspath(path))
    return any(p.is_symlink() for p in (absolute, *absolute.parents))


def repository_weights(
    repo: Path, plan: Mapping[str, Any], cache: Path
) -> dict[str, ig.WeightsEvidence]:
    """The weights entries that are files of the repository, each verified as a regular
    blob of the commit's tree (``verified_copy`` with the tree), by entry name; the
    downloaded ones are not read by version 1 (wp3-repository-weights-acceptance.md,
    section 1)."""
    wanted = [w for w in plan.get("weights", []) if sch.weights_origin(w) == sch.REPOSITORY_FILE]
    if not wanted:
        return {}
    entries = pt.commit_entries(repository.ls_tree(repo, plan["repository"]["commit"]))
    out = {}
    for w in wanted:
        copy, why = verified_copy(
            repo, w["path"], w["sha256"], int(w["size_bytes"]), cache, entries=entries
        )
        out[w["name"]] = ig.WeightsEvidence(w["path"], w["sha256"], copy, why or None)
    return out


def prepare_inputs(
    claim_file: Mapping[str, Any], root: Path, cache: Path
) -> tuple[Path, dict[str, ig.DatasetEvidence], dict[str, ig.WeightsEvidence]]:
    """Clones the repository at the claim's commit, verifies the weights that are files of
    the repository, and fetches every declared dataset with Refute's fetcher (with the
    build, the only network access of a paper run, through the allowlist proxy). The splits
    are counted by ``readers``; an unreadable split gives no count, so ``data_present`` is
    ``INCONCLUSIVE``, never a pass."""
    plan = claim_file["test_plan"]
    repo = repository.clone(plan["repository"]["url"], root / "source")
    repository.checkout(repo, plan["repository"]["commit"])
    # the weights that are files of the repository: verified right after the checkout,
    # before the patches, the build or any code of the paper; weights from outside are not
    # fetched, checked or mounted by version 1, and the claims that need them are not run
    # (integration.not_run_reason; wp3-repository-weights-acceptance.md)
    weights = repository_weights(repo, plan, cache)
    absent = plan["absent_artifact"]
    datasets: dict[str, ig.DatasetEvidence] = {}
    for d in plan["datasets"]:
        origin = sch.dataset_origin(d)
        if origin == sch.GENERATED:
            continue  # nothing to fetch or count: data_present does not apply
        if origin == sch.REPOSITORY_FILE:
            evidence = repository_file(repo, d, cache)
            if evidence is not None:
                datasets[d["name"]] = evidence
            continue
        spec = ArtifactSpec(d["name"], d["url"], d["sha256"], int(d["size_bytes"]))
        result = fetch_artifact(
            spec,
            cache,
            attempts=int(absent["attempts"]),
            interval_s=float(absent["interval_minutes"]) * 60,
        )
        counts = rd.split_counts(result.path, d["splits"]) if result.path is not None else None
        datasets[d["name"]] = ig.DatasetEvidence(result, counts)
    return repo, datasets, weights


# ---- a population counted before the lock (W3.12f) ------------------------------------------


def counted_records(
    claim_file: Mapping[str, Any], record_bytes: Mapping[str, bytes]
) -> list[dict[str, Any]]:
    """The records of the claim's populations counted before the lock, each given once
    (``--count-record attachment=file``) and equal to its attachment's sha256
    (wp3-population-count-acceptance.md, section 1)."""
    by_path = {a["path"]: a for a in claim_file.get("attachments") or []}
    wanted = [
        split["counted_before_lock"]["record"]
        for d in claim_file["test_plan"]["datasets"]
        for split in (d.get("derived_splits") or {}).values()
        if split.get("counted_before_lock")
    ]
    if sorted(record_bytes) != sorted(wanted):
        raise ProductionError(f"the count records given {sorted(record_bytes)} are not {wanted}")
    records = []
    for path in wanted:
        data = record_bytes[path]
        if path not in by_path or hashlib.sha256(data).hexdigest() != by_path[path].get("sha256"):
            raise ProductionError(f"the count record {path} differs from its attachment")
        records.append(json.loads(data.decode("utf-8")))
    return records


def _file_sha256(path: Path) -> str | None:
    if path.is_symlink() or not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_counted_environment(setup: PaperSetup, records: Sequence[Mapping[str, Any]]) -> None:
    """After the build and before the first base run, each count's environment must be this
    run's: the rung the record names built the image (its resolved lock and its venv's
    ``pyvenv.cfg``, the interpreter's identity, have the record's sha256, and no later rung
    ran), and the configuration files the selection reads have the record's sha256 in the
    patched tree. Otherwise the count does not apply: a Refute error, the paper stops before
    its runs, never an adjusted K (wp3-population-count-acceptance.md, section 1)."""
    ws = setup.root / "ws"
    for record in records:
        where = f"the count of {record.get('dataset')}/{record.get('split')}"
        env = record.get("environment") or {}
        rung = env.get("rung")
        if rung not in ld.RUNGS[1:]:
            raise ProductionError(f"{where}: the rung {rung!r} is not a rung with a resolved lock")
        built = ws / _safe(f"setup/build/{rung}") / ".refute"
        for name, key in (("requirements.lock", "lock_sha256"), ("pyvenv.cfg", "pyvenv_sha256")):
            if _file_sha256(built / name) != env.get(key):
                raise ProductionError(f"{where} does not apply: {name} of {rung} differs")
        for later in ld.RUNGS[ld.RUNGS.index(rung) + 1 :]:
            if (ws / _safe(f"setup/build/{later}") / ".refute" / "requirements.lock").exists():
                raise ProductionError(f"{where} does not apply: the rung {later} ran after {rung}")
        mounted = {
            str(PurePosixPath(e.rel)): e.copy
            for e in setup.repository_weights.values()
            if e.copy is not None
        }
        for item in record.get("configuration") or []:
            path = setup.repo / PurePosixPath(item["path"])
            if not _inside(setup.repo, path) or _file_sha256(path) != item.get("sha256"):
                raise ProductionError(f"{where} does not apply: {item['path']} differs")
            # a weights file the runs read from Refute's verified copy: the copy mounted is
            # the one counted (wp3-repository-weights-acceptance.md)
            copy = mounted.get(str(PurePosixPath(item["path"])))
            if copy is not None and _file_sha256(Path(copy)) != item.get("sha256"):
                raise ProductionError(f"{where} does not apply: the mounted {item['path']} differs")


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
    flag: Path, timeout_s: float = RUN_PHASE_WAIT_S, sleep: Callable[[float], None] = time.sleep,
    check: Callable[[bytes, str], None] | None = None,
) -> Callable[[], None]:  # fmt: skip
    """The hook between the setup and the first base run: it writes that the setup ended and
    waits for ``flag`` (the host creates it after the VM's port is in the profile pull). No
    flag within the time limit stops the paper (a Refute error, INCONCLUSIVE). With
    ``check``, the flag's bytes and the time the setup ended are checked when it appears
    (the host's record of the profile pull, wp3-dossier-provenance-acceptance.md)."""

    def hook() -> None:
        setup_ended = now_utc()
        status = flag.with_name("status.txt")
        status.write_text("setup done; waiting for the run phase\n", encoding="utf-8")
        print("setup done; waiting for the run phase", flush=True)
        waited = 0.0
        while not flag.exists():
            if waited >= timeout_s:
                raise ProductionError(f"the run phase was not approved within {timeout_s:.0f} s")
            sleep(10)
            waited += 10
        if check is not None:
            check(flag.read_bytes(), setup_ended)
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
    parser.add_argument(
        "--execution-id", default="", help="the id the host's launcher generated (32 hex)"
    )
    parser.add_argument(
        "--profile-status", type=Path, help="the host's record of the profile build"
    )
    parser.add_argument(
        "--patch", action="append", default=[], help="attachment=file of an allowed patch"
    )
    parser.add_argument(
        "--count-record", action="append", default=[],
        help="attachment=file of a population counted before the lock",
    )  # fmt: skip
    args = parser.parse_args(argv)
    engine_started = now_utc()
    claim_bytes = args.claim.read_bytes()
    claim_file = json.loads(claim_bytes.decode("utf-8"))
    claim_sha256 = hashlib.sha256(claim_bytes).hexdigest()
    if args.execution_id and not EXECUTION_ID.fullmatch(args.execution_id):
        raise ProductionError("--execution-id: 32 lowercase hex digits")
    if (args.run_phase_flag or args.profile_status) and not args.execution_id:
        raise ProductionError("the profile records need the host's --execution-id")
    checkout, diff = refute_checkout()
    prov: dict[str, Any] = {
        "execution_id": args.execution_id or None,
        "refute": checkout,
        "refute_diff": diff,
        "unit": systemd_unit(),
        "times": {"engine_started_utc": engine_started},
        "profiles": {"build": None, "run": None},
        "profile_bytes": {},
        "claim_input": claim_bytes,
        "profile_limits": PROFILE_LIMITS,
    }
    if args.profile_status:
        build_bytes = args.profile_status.read_bytes()
        prov["profile_bytes"]["build"] = build_bytes
        prov["profiles"]["build"] = read_profile(
            build_bytes, execution_id=args.execution_id,
            paper=args.paper, claim_sha256=claim_sha256, phase="build",
            consumed_utc=now_utc(),
        )  # fmt: skip
    else:
        prov["profiles"]["build reason"] = "not given"
    refuse_hook_routes(claim_file)
    patch_bytes = {}
    for item in args.patch:
        name, _, path = item.partition("=")
        if name in patch_bytes or not path:
            raise ProductionError(f"--patch {item!r}: attachment=file, each attachment once")
        patch_bytes[name] = Path(path).read_bytes()
    count_bytes = {}
    for item in args.count_record:
        name, _, path = item.partition("=")
        if name in count_bytes or not path:
            raise ProductionError(f"--count-record {item!r}: attachment=file, each once")
        count_bytes[name] = Path(path).read_bytes()
    records = counted_records(claim_file, count_bytes)
    if shutil.disk_usage(Path.home()).free < args.min_free_gb * 1e9:
        print(f"refused: less than {args.min_free_gb:g} GB free on the VM", flush=True)
        return 2
    args.root.mkdir(parents=True)
    repo, datasets, weights = prepare_inputs(claim_file, args.root, args.cache)
    layout = dict(item.split("=", 1) for item in args.data)
    patched, patch_record = patch_tree(claim_file, repo, args.root / "patched", patch_bytes, layout)
    limits = Limits(cpus=22, period_us=100_000, memory_bytes=12 << 30, pids=4096)
    limit_paper_slice(args.paper, 13 << 30, 22)
    setup = PaperSetup(
        paper=args.paper,
        root=args.root / "run",
        repo=patched,
        datasets=datasets,
        data_layout=layout,
        limits=limits,
        timing=V22_MAXIMA,
        micromamba_image=args.micromamba_image,
        patch_record=patch_record,
        weights=tuple(
            w["name"]
            for w in claim_file["test_plan"].get("weights", [])
            if sch.weights_origin(w) != sch.REPOSITORY_FILE
        ),
        repository_weights=weights,
    )

    def check_run(data: bytes, setup_ended: str) -> None:
        prov["profile_bytes"]["run"] = data  # kept before the check, a refusal included
        try:
            prov["profiles"]["run"] = read_profile(
                data, execution_id=args.execution_id, paper=args.paper,
                claim_sha256=claim_sha256, phase="run", consumed_utc=now_utc(),
                not_before=setup_ended,
            )  # fmt: skip
        except ProductionError as exc:
            prov["profiles"]["run refused"] = str(exc)
            raise

    wait = wait_for_run_phase(args.run_phase_flag, check=check_run) if args.run_phase_flag else None

    def hook() -> None:
        # the image built is identified first, so a stop below keeps it
        prov["image_id"] = image_id(f"refute-local/{args.paper}/env")
        # then the count's environment: a mismatch stops the paper before its runs
        check_counted_environment(setup, records)
        if wait is not None:
            wait()

    images = {
        "micromamba": args.micromamba_image,
        "base": claim_file["test_plan"]["build"]["base_image"],
    }
    outcome = run_production(
        setup, claim_file, args.out, images, hook, stop_on_sigterm=True, provenance=prov
    )
    print(outcome_summary(outcome), flush=True)
    return 0


__all__: Sequence[str] = (
    "BASE_ENV",
    "PaperSetup",
    "ProductionError",
    "build_harness",
    "build_script",
    "check_counted_environment",
    "classify_build",
    "counted_records",
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
