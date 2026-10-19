"""The count of a population before the lock (W3.12f, wp3-population-count-acceptance.md,
section 1), on the VM: Refute's count script runs in the claim's production container
(the clone at the claim's commit plus its allowed patches, applied by the engine; the image
the ladder's rung builds; 22 CPUs, 12 GiB, no network), twice, in independent containers,
and the two counts must agree. Only the line ``refute-population-count <K>`` is kept from
each run's log (a failed run keeps its error lines only); the raw logs and the run folders
are deleted. The output is the count record, canonical JSON, committed before the lock.

Two phases, run on the VM from the Refute checkout (the same profiles as measure_paper.py):

    # the endpoint's profile build (the allowlist proxy)
    .venv/bin/python scripts/vm/count_population.py build --spec <spec.json> --root <new folder>
    # the endpoint's profile pull (no proxy), the containers' network none
    .venv/bin/python scripts/vm/count_population.py count --spec <spec.json> --root <same folder>

The spec (JSON) is measure_paper.py's (name, repo_url, commit, python, base_image,
exclude_newer, patches, data) plus: dataset and split (the derived split counted), script
({path, sha256} of the count script on the VM), configuration (a list of {path, sha256} of
the files the selection reads, checked in the patched tree; empty when it reads none) and
active_minutes (a cap per run).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path, PurePosixPath

sys.path.insert(0, str(Path(__file__).resolve().parent))

import measure_paper as mp  # noqa: E402 - the same build, isolation and timing helpers

from refute.core.canonical import canonical_bytes  # noqa: E402
from refute.packs.ml import production as pd  # noqa: E402
from refute.packs.ml import schema as sch  # noqa: E402
from refute.packs.ml.docker_backend import ContainerPlan, DockerBackend  # noqa: E402

RUNG = "requirements_compiled"  # the rung measure_paper.build builds
SCRIPT_NAME = "refute_population_count.py"  # at the root: the repository's modules import
COUNT_LINE = re.compile(r"^refute-population-count (\d+)$")
REPEATS = 2


def file_sha256(path: Path) -> str | None:
    return mp.sha256(path) if path.is_file() and not path.is_symlink() else None


def build(spec: dict, root: Path) -> dict:
    record = mp.build(spec, root)
    built = root / "build" / ".refute"
    record["rung"] = RUNG
    record["lock_sha256"] = file_sha256(built / "requirements.lock")
    record["pyvenv_sha256"] = file_sha256(built / "pyvenv.cfg")
    record["pyvenv"] = (
        (built / "pyvenv.cfg").read_text(encoding="utf-8") if record["pyvenv_sha256"] else None
    )
    return record


def count_once(spec: dict, root: Path, image: str, script: bytes, n: int) -> dict:
    work = root / f"count-{n}"
    source = root / "patched" if (root / "patched").is_dir() else root / "clone"
    pd._copy_repo(source, work)  # noqa: SLF001 - production's own copy
    target = work / SCRIPT_NAME
    if target.exists() or target.is_symlink():
        raise SystemExit(f"{SCRIPT_NAME} exists in the repository")
    target.write_bytes(script)
    target.chmod(0o444)
    for item in spec["configuration"]:
        path = work / PurePosixPath(item["path"])
        if file_sha256(path) != item["sha256"]:
            raise SystemExit(f"{item['path']}: SHA-256 differs from the spec in the patched tree")
    work.chmod(0o1777)
    mounts = tuple((str(Path(s["path"]).resolve()), t) for t, s in spec["data"].items())
    backend = DockerBackend(
        mp.run_paper_id({**spec, "run_id": f"count{n}"}),
        mp.LIMITS,
        {work: ContainerPlan(image, data_mounts=mounts)},
    )
    log = root / "logs" / f"count-{n}.log"
    started = mp.now()
    result, _ = mp.run(backend, work, ["python", SCRIPT_NAME], log, spec["active_minutes"])
    raw = log.read_text(encoding="utf-8", errors="replace")
    lines = [m.group(1) for m in map(COUNT_LINE.match, raw.splitlines()) if m]
    errors = mp.keep_timing(raw, mp.ERROR_PATTERNS)[-60:] if result.exit_code != 0 else []
    log.unlink()  # only the count line is kept (section 1)
    shutil.rmtree(work, ignore_errors=True)
    if work.exists():  # files the run's uid wrote: emptied from a container, then removed
        clean = ["docker", "run", "--rm", "--network", "none", "-v", f"{work}:/w",
                 image, "find", "/w", "-mindepth", "1", "-delete"]  # fmt: skip
        subprocess.run(clean, check=False)
        shutil.rmtree(work, ignore_errors=True)
    return {
        "started_utc": started,
        "finished_utc": mp.now(),
        "exit_code": result.exit_code,
        "stopped": result.stopped,
        "usage_usec": result.usage_usec,
        "count_lines": lines,
        "error_lines": errors,
    }


def count(spec: dict, root: Path) -> tuple[dict, bool]:
    built = json.loads((root / "build.json").read_text(encoding="utf-8"))
    if built["exit_code"] != 0 or not built.get("lock_sha256") or not built.get("pyvenv_sha256"):
        raise SystemExit("the build did not succeed, or wrote no lock or pyvenv.cfg")
    script = Path(spec["script"]["path"]).read_bytes()
    if hashlib.sha256(script).hexdigest() != spec["script"]["sha256"]:
        raise SystemExit("the count script's SHA-256 differs from the spec")
    for source in spec["data"].values():
        if mp.sha256(Path(source["path"])) != source["sha256"]:
            raise SystemExit(f"{source['path']}: SHA-256 differs from the spec")
    runs = [count_once(spec, root, built["image"], script, n) for n in range(1, REPEATS + 1)]
    counts = [r["count_lines"][0] if len(r["count_lines"]) == 1 else None for r in runs]
    ok = all(r["exit_code"] == 0 and r["stopped"] is None for r in runs)
    ok = ok and counts[0] is not None and len(set(counts)) == 1
    refute_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True,
        cwd=Path(__file__).resolve().parents[2],
    ).stdout.strip()  # fmt: skip
    record = {
        "format": sch.POPULATION_RECORD_FORMAT,
        "dataset": spec["dataset"],
        "split": spec["split"],
        "count": int(counts[0]) if ok else None,
        "script_sha256": spec["script"]["sha256"],
        "commit": built["commit"],
        "patches": [p["sha256"] for p in spec.get("patches", [])],
        "configuration": spec["configuration"],
        "environment": {
            "base_image": spec["base_image"],
            "rung": built["rung"],
            "lock_sha256": built["lock_sha256"],
            "pyvenv_sha256": built["pyvenv_sha256"],
        },
        "exit_code": 0 if ok else 1,
        "runs": runs,
        "refute_commit": refute_commit,
    }
    return record, ok


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=("build", "count"))
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    if args.phase == "build":
        record = build(spec, args.root)
        record["spec"] = spec
        ok = record["exit_code"] == 0
        out = args.root / "build.json"
        out.write_text(json.dumps(record, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    else:
        record, ok = count(spec, args.root)
        out = args.root / "count-record.json"
        out.write_bytes(canonical_bytes(record))
    print("record:", out, "ok" if ok else "NOT OK")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
