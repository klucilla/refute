"""The VM proof of the TensorBoard event-file reader (docs/validation/v0.3/
wp3-tensorboard-acceptance.md, section 4): event files written by real TensorFlow, read
offline by the reader's tests.

Approved by the maintainer on 2026-10-18, only to make these fixtures: TensorFlow 2.14.0,
the version 2407.11735 declares (`requirements.txt` at walline/prosub@8a28cf3d), in its
CPU-only variant `tensorflow-cpu`, on the pinned Python 3.11 image. The image with
TensorFlow serves only this proof; no run of a paper reuses it, and the engine never
imports TensorFlow.

Two phases, run on the VM from the Refute checkout:

    # the endpoint's build profile (PyPI through the allowlist proxy)
    .venv/bin/python scripts/vm/tensorboard_vm_fixtures.py build --python-image <3.11 image>
        --root <new folder>
    # the endpoint's run profile (no network; the container has none either)
    .venv/bin/python scripts/vm/tensorboard_vm_fixtures.py write --root <same folder>

`build` installs `tensorflow-cpu==2.14.0` with the engine's own build command (uv, the
lock written to the build folder, `--exclude-newer` 7 days before the run) and commits the
image. `write` runs, in a container of that image with no network, a generator that
writes the event files with TensorFlow 2 (`tf.summary.scalar`, a tensor) and with the
TensorFlow 1 compatible writer (`simple_value`), lists the installed distributions, and
copies the files to `<root>/fixtures`. Each phase writes `<root>/<phase>.json`.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

from refute.packs.ml import ladder as ld
from refute.packs.ml import production as pd
from refute.packs.ml.docker_backend import ContainerPlan, DockerBackend, Limits
from refute.packs.ml.sandbox import RunSpec

REQUIREMENTS = "tensorflow-cpu==2.14.0\n"
THREADS = {"OMP_NUM_THREADS": "2", "TF_NUM_INTEROP_THREADS": "1", "TF_NUM_INTRAOP_THREADS": "2"}
HOUR_USEC = 3600 * 1_000_000
LIMITS = Limits(cpus=4, period_us=100_000, memory_bytes=8 << 30, pids=2048)
TAG = "test/accuracy"
# values with no exact binary form, at steps 0 (omitted by the writer), 1 and 2
VALUES = {0: 0.1, 1: 0.7, 2: 0.9234}
# the reader's own library-path step (the venv's site-packages under -I -S), as the VM
# proof of the container readers uses it (reader_vm_test.py)
LIBRARY_STEP = "exec(open('reader.py', encoding='utf-8').read().split('READERS =')[0])\n"
GENERATOR = (
    LIBRARY_STEP
    + "_library_paths()\n"
    + r"""
import json, sys
mode = sys.argv[1]
values = {int(k): v for k, v in json.loads(sys.argv[2]).items()}
tag = sys.argv[3]
import tensorflow as tf
if mode == "tf2":
    writer = tf.summary.create_file_writer("out/tf2")
    with writer.as_default():
        for step, value in sorted(values.items()):
            tf.summary.scalar(tag, value, step=step)
            if step == 1:
                tf.summary.image("images/sample", tf.zeros([1, 4, 4, 1]), step=step)
    writer.flush()
    writer.close()
else:
    tf.compat.v1.disable_eager_execution()
    writer = tf.compat.v1.summary.FileWriter("out/tf1")
    for step, value in sorted(values.items()):
        summary = tf.compat.v1.Summary(
            value=[tf.compat.v1.Summary.Value(tag=tag, simple_value=value)]
        )
        writer.add_summary(summary, step)
    writer.flush()
    writer.close()
import importlib.metadata as md
dists = sorted(f"{d.metadata['Name']}=={d.version}" for d in md.distributions())
print("GENERATED " + json.dumps({"mode": mode, "tf": tf.__version__, "distributions": dists}))
"""
)


def folder(path: Path, mode: int = 0o1777) -> Path:
    path.mkdir(parents=True)
    path.chmod(mode)
    return path


def run(backend: DockerBackend, work: Path, argv: list[str], log: Path):
    spec = RunSpec(
        argv=argv,
        workdir=work,
        env=dict(THREADS),
        log_path=log,
        threshold_usec=4 * HOUR_USEC,
        active_time_limit_s=3 * 3600,
        no_progress_s=3600,
    )
    result = backend.run(spec)
    return result, log.read_text(encoding="utf-8", errors="replace")


def image_id(image: str) -> str:
    done = subprocess.run(
        ["docker", "image", "inspect", "--format", "{{.Id}}", image],
        capture_output=True,
        text=True,
        check=True,
    )
    return done.stdout.strip()


def build(root: Path, base_image: str, stamp: str) -> dict:
    repo = folder(root / "build", 0o777)
    (repo / "requirements.txt").write_text(REQUIREMENTS, encoding="ascii")
    (repo / "requirements.txt").chmod(0o666)
    rungs = ld.ladder_rungs(None, "requirements.txt", ["3.11"])
    rung = next(r for r in rungs if r.name == "requirements_compiled")
    image = f"refute-local/tbfix{stamp[9:15]}/env"
    exclude_newer = (datetime.now(UTC) - timedelta(days=7)).strftime("%Y-%m-%d")
    backend = DockerBackend(
        f"tbfix{stamp[9:15]}",
        LIMITS,
        {repo: ContainerPlan(base_image, network="proxy", commit_as=image, read_only=False)},
    )
    (root / "logs").mkdir()
    argv = pd.build_script(rung, repo, exclude_newer)
    result, log = run(backend, repo, argv, root / "logs" / "build.log")
    lock = repo / ".refute" / "requirements.lock"
    record = {
        "phase": "build",
        "started_utc": stamp,
        "base_image": base_image,
        "requirements": REQUIREMENTS,
        "exclude_newer": exclude_newer,
        "image": image,
        "exit_code": result.exit_code,
        "stopped": result.stopped,
        "lock": lock.read_text(encoding="utf-8") if lock.is_file() else None,
    }
    if result.exit_code == 0:
        record["image_id"] = image_id(image)
    else:
        record["log_tail"] = log[-3000:]
    return record


def write(root: Path, stamp: str) -> dict:
    built = json.loads((root / "build.json").read_text(encoding="utf-8"))
    if built.get("exit_code") != 0:
        raise SystemExit("the build did not succeed")
    image = built["image"]
    if image_id(image) != built["image_id"]:
        raise SystemExit("the image changed since the build")
    record: dict = {"phase": "write", "started_utc": stamp, "image_id": built["image_id"]}
    fixtures = root / "fixtures"
    fixtures.mkdir()
    for mode in ("tf2", "tf1"):
        work = folder(root / f"gen-{mode}")
        (work / pd.READER_SCRIPT).write_bytes(pd.READER_SOURCE.read_bytes())
        folder(work / "out")
        backend = DockerBackend(f"tbw{mode}{stamp[9:15]}", LIMITS, {work: ContainerPlan(image)})
        argv = [
            *pd.reader_argv("requirements_compiled", "", THREADS)[:-2],
            "-c",
            GENERATOR,
            mode,
            json.dumps(VALUES),
            TAG,
        ]
        result, log = run(backend, work, argv, root / "logs" / f"write-{mode}.log")
        seen = [line for line in log.splitlines() if line.startswith("GENERATED ")]
        files = sorted(p for p in (work / "out").rglob("*") if p.is_file())
        entry: dict = {
            "argv": argv,
            "exit_code": result.exit_code,
            "stopped": result.stopped,
            "generated": json.loads(seen[-1][len("GENERATED ") :]) if seen else None,
            "files": [],
        }
        if not seen:
            entry["log_tail"] = log[-3000:]
        for path in files:
            target = fixtures / mode / path.name
            target.parent.mkdir(exist_ok=True)
            shutil.copyfile(path, target)
            data = target.read_bytes()
            entry["files"].append(
                {
                    "name": f"{mode}/{path.name}",
                    "size": len(data),
                    "sha256": hashlib.sha256(data).hexdigest(),
                }
            )
        record[mode] = entry
    record["tag"] = TAG
    record["values"] = {str(k): v for k, v in VALUES.items()}
    record["passed"] = all(
        record[m]["exit_code"] == 0 and record[m]["generated"] and len(record[m]["files"]) == 1
        for m in ("tf2", "tf1")
    )
    return record


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=("build", "write"))
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--python-image")
    args = parser.parse_args()
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    if args.phase == "build":
        if not args.python_image:
            raise SystemExit("build needs --python-image")
        args.root.mkdir(parents=True, exist_ok=False)
        record = build(args.root, args.python_image, stamp)
        ok = record["exit_code"] == 0
    else:
        record = write(args.root, stamp)
        ok = record["passed"]
    record["finished_utc"] = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    out = args.root / f"{args.phase}.json"
    out.write_text(json.dumps(record, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print("record:", out, "ok" if ok else "FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
