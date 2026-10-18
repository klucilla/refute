"""A short timing run of a paper's code on the VM, for the budget estimate of its claims
(the maintainer's decision 2 of 2026-10-18): production isolation (the docker backend,
22 CPUs, 12 GiB, no network in the run), a fixed small number of epochs declared in the
spec before the run, and ONLY timing kept: the run's log is filtered on the VM to the
lines that the spec's timing patterns match (progress bars and clocks), the raw log and
the run's folder are deleted, and no metric output (accuracy, AUROC, losses) is read or
recorded. Nothing measured here informs a tolerance, an attack or the choice of a claim.

Two phases, run on the VM from the Refute checkout:

    # the endpoint's profile build (the allowlist proxy)
    .venv/bin/python scripts/vm/measure_paper.py build --spec <spec.json> --root <new folder>
    # the endpoint's profile pull (no proxy), the container's network none
    .venv/bin/python scripts/vm/measure_paper.py run --spec <spec.json> --root <same folder>

The spec (JSON): name, repo_url, commit, python, base_image, exclude_newer, argv (the
documented command with the declared number of epochs), data ({target path in the run's
folder: absolute source file on the VM}, each with its sha256), timing_patterns (regular
expressions; a line is kept only if one matches, and only its matched text is kept),
active_minutes (a cap; the run is expected to end before it), run_id (the name of one
timing run; several runs share one build).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

from refute.packs.ml import ladder as ld
from refute.packs.ml import patches as pt
from refute.packs.ml import production as pd
from refute.packs.ml.docker_backend import ContainerPlan, DockerBackend, Limits
from refute.packs.ml.sandbox import RunSpec

LIMITS = Limits(cpus=22, period_us=100_000, memory_bytes=12 << 30, pids=4096)  # production
HOUR_USEC = 3600 * 1_000_000
PROXY = "http://10.231.71.3:3128"


def now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def run(backend: DockerBackend, work: Path, argv: list[str], log: Path, minutes: float):
    spec = RunSpec(
        argv=argv,
        workdir=work,
        env=dict(pd.BASE_ENV),
        log_path=log,
        threshold_usec=None,
        active_time_limit_s=minutes * 60,
        no_progress_s=minutes * 60,
    )
    started = datetime.now(UTC)
    result = backend.run(spec)
    return result, (datetime.now(UTC) - started).total_seconds()


def patched_source(spec: dict, clone: Path, root: Path) -> Path:
    """The clone, or the clone plus the claim's allowed patches applied by the engine's own
    applier (W3.9a): spec "patches" is a list of {attachment, path, sha256} on the VM."""
    if not spec.get("patches"):
        return clone
    given = []
    for p in spec["patches"]:
        data = Path(p["path"]).read_bytes()
        if hashlib.sha256(data).hexdigest() != p["sha256"]:
            raise SystemExit(f"{p['path']}: SHA-256 differs from the spec")
        given.append((p["attachment"], data))
    tree = subprocess.run(
        ["git", "-C", str(clone), "ls-tree", "-r", "-z", "--full-tree", spec["commit"]],
        capture_output=True, text=True, check=True,
    ).stdout  # fmt: skip
    record = pt.prepare(
        clone, root / "patched", given, sorted(spec.get("data", {})), pt.commit_entries(tree)
    )
    (root / "patch-record.json").write_text(json.dumps(record, indent=1), encoding="utf-8")
    return root / "patched"


def build(spec: dict, root: Path) -> dict:
    root.mkdir(parents=True)
    clone = root / "clone"
    env = {**os.environ, "http_proxy": PROXY, "https_proxy": PROXY}
    subprocess.run(["git", "clone", "--quiet", spec["repo_url"], str(clone)], env=env, check=True)
    subprocess.run(["git", "-C", str(clone), "checkout", "--quiet", spec["commit"]], check=True)
    head = subprocess.run(
        ["git", "-C", str(clone), "rev-parse", "HEAD"], capture_output=True, text=True, check=True
    ).stdout.strip()
    if head != spec["commit"]:
        raise SystemExit(f"checked out {head}, not {spec['commit']}")
    source = patched_source(spec, clone, root)
    repo = root / "build"
    pd._copy_repo(source, repo)  # noqa: SLF001 - production's own copy
    repo.chmod(0o1777)
    _, req, _ = pd.ladder_inputs(repo)
    rungs = ld.ladder_rungs(None, req, [spec["python"]])
    rung = next(r for r in rungs if r.name == "requirements_compiled")
    image = f"refute-local/meas{spec['name']}/env"  # [a-z0-9] only (LOCAL_IMAGE)
    backend = DockerBackend(
        f"meas{spec['name']}b",
        LIMITS,
        {
            repo: ContainerPlan(
                spec["base_image"], network="proxy", commit_as=image, read_only=False
            )
        },
    )
    (root / "logs").mkdir()
    argv = pd.build_script(rung, repo, spec["exclude_newer"])
    result, seconds = run(backend, repo, argv, root / "logs" / "build.log", 180)
    record = {
        "phase": "build",
        "finished_utc": now(),
        "commit": head,
        "image": image,
        "exit_code": result.exit_code,
        "stopped": result.stopped,
        "usage_usec": result.usage_usec,
        "wall_s": seconds,
    }
    lock = repo / ".refute" / "requirements.lock"
    record["lock"] = lock.read_text(encoding="utf-8") if lock.is_file() else None
    if result.exit_code != 0:
        text = (root / "logs" / "build.log").read_text(encoding="utf-8", errors="replace")
        record["log_tail"] = text[-4000:]
    return record


def keep_timing(raw: str, patterns: list[str]) -> list[str]:
    """Only the text the timing patterns match, line by line (a progress bar redraws with
    carriage returns: each redraw is a line here)."""
    compiled = [re.compile(p) for p in patterns]
    kept = []
    for line in re.split(r"[\r\n]+", raw):
        for c in compiled:
            m = c.search(line)
            if m:
                kept.append(m.group(0))
                break
    return kept


def measure(spec: dict, root: Path) -> dict:
    built = json.loads((root / "build.json").read_text(encoding="utf-8"))
    if built["exit_code"] != 0:
        raise SystemExit("the build did not succeed")
    for source in spec["data"].values():
        if sha256(Path(source["path"])) != source["sha256"]:
            raise SystemExit(f"{source['path']}: SHA-256 differs from the spec")
    work = root / f"run-{spec['run_id']}"
    source = root / "patched" if (root / "patched").is_dir() else root / "clone"
    pd._copy_repo(source, work)  # noqa: SLF001
    for target in spec["data"]:
        (work / target).parent.mkdir(parents=True, exist_ok=True)
    work.chmod(0o1777)
    mounts = tuple((str(Path(s["path"]).resolve()), t) for t, s in spec["data"].items())
    backend = DockerBackend(
        f"meas{spec['name']}r", LIMITS, {work: ContainerPlan(built["image"], data_mounts=mounts)}
    )
    argv = list(spec["argv"])  # as production runs it: PATH starts with the build's venv
    log = root / "logs" / f"run-{spec['run_id']}.log"
    started = now()
    result, seconds = run(backend, work, argv, log, spec["active_minutes"])
    raw = log.read_text(encoding="utf-8", errors="replace")
    timing = keep_timing(raw, spec["timing_patterns"])
    # the raw log and the run's folder may hold metric outputs: never kept (decision 2c)
    log.unlink()
    shutil.rmtree(work, ignore_errors=True)
    if work.exists():
        subprocess.run(["docker", "run", "--rm", "--network", "none", "-v", f"{work}:/w",
                        built["image"], "rm", "-rf", "/w"], check=False)  # fmt: skip
    return {
        "phase": "run",
        "started_utc": started,
        "finished_utc": now(),
        "argv": argv,
        "data": spec["data"],
        "exit_code": result.exit_code,
        "stopped": result.stopped,
        "usage_usec": result.usage_usec,
        "wall_s": seconds,
        "timing_lines": timing,
        "raw_log_and_outputs": "deleted on the VM; only the timing lines above were kept",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=("build", "run"))
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    if args.phase == "build":
        record = build(spec, args.root)
        ok = record["exit_code"] == 0
    else:
        record = measure(spec, args.root)
        ok = record["exit_code"] == 0
    record["spec"] = spec
    name = "build" if args.phase == "build" else f"run-{spec['run_id']}"
    out = args.root / f"{name}.json"
    out.write_text(json.dumps(record, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print("record:", out, "ok" if ok else "NOT OK")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
