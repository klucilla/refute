"""The VM proof of the container readers (docs/validation/v0.3/wp3-data-sources-acceptance.md,
section 4.2): each reader of the closed list, on a synthetic file of its format, through the
production pieces and the docker backend, before any reader is used on a paper.

For each reader it builds an image with the real ladder rung ``requirements_compiled``
(uv in the given Python image, through the allowlist proxy, a requirements file of the
format's library only), then runs the reader exactly as production does
(``production.reader_argv``: ``/usr/bin/env -i`` with the thread variables, the built
interpreter with -I -S, in a fresh folder holding only Refute's script, the file mounted
read only), reads its answer with ``readers.read_answer``, and runs a probe with the same
command prefix that records what the reader saw: its working folder and files, its
environment, its ``sys.path`` after the reader's own library-path step, where the format's
library was imported from, and the mounts under /work. No third-party code runs but the
Python image and the libraries from PyPI; the DGL graph file is written in the built image
by this script's own code.

Run on the VM, from the Refute checkout:
    .venv/bin/python scripts/vm/reader_vm_test.py --python-image <python@sha256:...>
        --out <file.json> [--reader cifar_python --reader excel --reader dgl]

It writes one JSON record and exits 0 when every reader's count equals the expected one.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import pickle
import shutil
import subprocess
import sys
import tarfile
import zipfile
from datetime import UTC, datetime
from pathlib import Path

from refute.packs.ml import ladder as ld
from refute.packs.ml import production as pd
from refute.packs.ml import readers as rd
from refute.packs.ml.docker_backend import ContainerPlan, DockerBackend, Limits
from refute.packs.ml.sandbox import RunSpec

THREADS = {
    "OMP_NUM_THREADS": "2",
    "MKL_NUM_THREADS": "2",
    "OPENBLAS_NUM_THREADS": "2",
    "NUMEXPR_NUM_THREADS": "2",
}
HOUR_USEC = 3600 * 1_000_000
N_CIFAR, N_EXCEL, N_DGL = 4000, 123, 57
LIBRARY_STEP = "exec(open('reader.py', encoding='utf-8').read().split('READERS =')[0])\n"
PROBE = (
    "import json, os, sys\n" + LIBRARY_STEP + "_library_paths()\n"
    "module = __import__(sys.argv[1])\n"
    "files = sorted(os.path.join(d, f) for d, _, fs in os.walk('.') for f in fs)\n"
    # root, mount point and the mount's own options (ro or rw) of every mount under /work
    "mounts = [l.split(' ')[3:6] for l in open('/proc/self/mountinfo') if ' /work' in l]\n"
    "print('PROBE ' + json.dumps({'cwd': os.getcwd(), 'files': files, 'env': dict(os.environ),"
    " 'executable': sys.executable, 'prefix': sys.prefix, 'path': sys.path,"
    " 'flags': {'isolated': sys.flags.isolated, 'no_site': sys.flags.no_site},"
    " 'library': getattr(module, '__file__', None), 'mounts': mounts}))\n"
)
DGL_GENERATOR = (
    "import sys\n" + LIBRARY_STEP + "_library_paths()\n"
    "import dgl, torch\n"
    "n = int(sys.argv[1])\n"
    "g = dgl.heterograph({('a', 'b', 'c'): (torch.arange(n), torch.arange(n) % 5)})\n"
    "dgl.save_graphs('out/graph.bin', [g])\n"
)


def cifar_file() -> bytes:
    import numpy as np

    batch = {
        b"batch_label": b"testing batch 1 of 1",
        b"labels": [i % 10 for i in range(N_CIFAR)],
        b"data": np.zeros((N_CIFAR, 3072), dtype=np.uint8),
        b"filenames": [b"x.png"] * N_CIFAR,
    }
    data = pickle.dumps(batch, 2)
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
        info = tarfile.TarInfo("cifar-10-batches-py/test_batch")
        info.size = len(data)
        archive.addfile(info, io.BytesIO(data))
    return buffer.getvalue()


def excel_file() -> bytes:
    """A minimal .xlsx written by hand (OOXML parts): a header row and N_EXCEL data rows."""
    rows = ['<row r="1"><c r="A1" t="inlineStr"><is><t>x</t></is></c></row>']
    rows += [f'<row r="{i}"><c r="A{i}"><v>{i}</v></c></row>' for i in range(2, N_EXCEL + 2)]
    ns = 'xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"'
    rel = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
    parts = {
        "[Content_Types].xml": (
            '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats'
            '.org/package/2006/content-types"><Default Extension="rels" ContentType="application/'
            'vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType='
            '"application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/'
            'vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName='
            '"/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-'
            'officedocument.spreadsheetml.worksheet+xml"/></Types>'
        ),
        "_rels/.rels": (
            '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.'
            'openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="'
            f'{rel}/officeDocument" Target="xl/workbook.xml"/></Relationships>'
        ),
        "xl/workbook.xml": (
            f'<?xml version="1.0" encoding="UTF-8"?><workbook {ns} xmlns:r="{rel}"><sheets>'
            '<sheet name="Sheet1" sheetId="1" r:id="rId1"/></sheets></workbook>'
        ),
        "xl/_rels/workbook.xml.rels": (
            '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.'
            'openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="'
            f'{rel}/worksheet" Target="worksheets/sheet1.xml"/></Relationships>'
        ),
        "xl/worksheets/sheet1.xml": (
            f'<?xml version="1.0" encoding="UTF-8"?><worksheet {ns}><sheetData>'
            + "".join(rows)
            + "</sheetData></worksheet>"
        ),
    }
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, text in parts.items():
            archive.writestr(name, text)
    return buffer.getvalue()


CASES = {
    "cifar_python": {
        "requirements": "numpy\n",
        "module": "numpy",
        "file": "cifar-10-python.tar.gz",
        "source": "reader:container:cifar_python:cifar-10-batches-py/test_batch",
        "expected": N_CIFAR,
    },
    "excel": {
        "requirements": "pandas\nopenpyxl\n",
        "module": "pandas",
        "file": "table.xlsx",
        "source": "reader:container:excel:#0",
        "expected": N_EXCEL,
    },
    "dgl": {
        # dgl 2.1.0 is the last release with Linux wheels on PyPI (2.2.1 has Windows ones
        # only); its backend is torch
        # runs of 2026-10-18: dgl 2.x on Python 3.12 needs torchdata.datapipes, whose only
        # Python 3.12 wheel (0.8.0) needs the system's libcurl; dgl 1.1.3 has neither
        # graphbolt nor torchdata, and Linux wheels for Python 3.11 on PyPI. dgl imports
        # setuptools.extern.packaging and packaging without declaring them; torch 2.1 is
        # built for numpy 1
        "python": "3.11",
        "requirements": (
            "dgl==1.1.3\ntorch==2.1.2\nnumpy==1.26.4\nsetuptools==69.5.1\npackaging==24.0\n"
        ),
        "module": "dgl",
        "file": "graph.bin",
        "source": "reader:container:dgl:#a,b,c",
        "expected": N_DGL,
    },
}


def folder(path: Path, mode: int = 0o1777) -> Path:
    path.mkdir(parents=True)
    path.chmod(mode)
    return path


def run(backend: DockerBackend, work: Path, argv: list[str], logs: Path, name: str):
    spec = RunSpec(
        argv=argv,
        workdir=work,
        env=dict(THREADS),
        log_path=logs / f"{name}.log",
        threshold_usec=4 * HOUR_USEC,
        active_time_limit_s=3 * 3600,
        no_progress_s=3600,
    )
    result = backend.run(spec)
    text = spec.log_path.read_text(encoding="utf-8", errors="replace")
    return result, text


def image_id(image: str) -> str:
    done = subprocess.run(
        ["docker", "image", "inspect", "--format", "{{.Id}}", image],
        capture_output=True,
        text=True,
        check=True,
    )
    return done.stdout.strip()


def prove(name: str, case: dict, base_image: str, root: Path, stamp: str) -> dict:
    paper = f"rdr{name[:3]}{stamp[9:15]}"
    logs = root / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    repo = folder(root / "build", 0o777)
    (repo / "requirements.txt").write_text(case["requirements"], encoding="ascii")
    (repo / "requirements.txt").chmod(0o666)
    rungs = ld.ladder_rungs(None, "requirements.txt", [case.get("python", "3.12")])
    rung = next(r for r in rungs if r.name == "requirements_compiled")
    image = f"refute-local/{paper}/env"
    reader = folder(root / "reader")
    (reader / pd.READER_SCRIPT).write_bytes(pd.READER_SOURCE.read_bytes())
    (reader / pd.READER_SCRIPT).chmod(0o444)
    folder(reader / "data")
    probe = folder(root / "probe")
    (probe / pd.READER_SCRIPT).write_bytes(pd.READER_SOURCE.read_bytes())
    folder(probe / "data")
    fetched = root / "fetched"
    fetched.mkdir()
    data_file = fetched / case["file"]
    target = f"data/{case['file']}"
    generator = folder(root / "generator")
    (generator / pd.READER_SCRIPT).write_bytes(pd.READER_SOURCE.read_bytes())
    folder(generator / "out")
    if name == "cifar_python":
        data_file.write_bytes(cifar_file())
    elif name == "excel":
        data_file.write_bytes(excel_file())
    limits = Limits(cpus=4, period_us=100_000, memory_bytes=8 << 30, pids=2048)
    plans = {
        repo: ContainerPlan(base_image, network="proxy", commit_as=image, read_only=False),
        generator: ContainerPlan(image),
    }
    backend = DockerBackend(paper, limits, plans)
    record: dict = {"reader": name, "requirements": case["requirements"], "base_image": base_image}
    build, log = run(backend, repo, pd.build_script(rung, repo, "2026-10-01"), logs, "build")
    record["build"] = {"exit_code": build.exit_code, "stopped": build.stopped}
    if build.exit_code != 0:
        record["build"]["log_tail"] = log[-2000:]
        return record
    record["image_id"] = image_id(image)
    python = f"{pd.VENV}/bin/python"
    if name == "dgl":
        argv = [*pd.reader_argv(rung.name, "", THREADS)[:-2], "-c", DGL_GENERATOR, str(N_DGL)]
        made, log = run(backend, generator, argv, logs, "generator")
        record["generator"] = {"exit_code": made.exit_code, "log_tail": log[-1500:]}
        if made.exit_code != 0:
            return record
        shutil.copyfile(generator / "out" / "graph.bin", data_file)
    data_file.chmod(0o444)
    record["file"] = {
        "name": case["file"],
        "sha256": hashlib.sha256(data_file.read_bytes()).hexdigest(),
        "size": data_file.stat().st_size,
    }
    mounts = ((str(data_file.resolve()), target),)
    backend = DockerBackend(
        paper + "r",
        limits,
        {
            reader: ContainerPlan(image, data_mounts=mounts),
            probe: ContainerPlan(image, data_mounts=mounts),
        },
    )
    request = rd.container_request(target, {"test": {"source": case["source"]}})
    argv = pd.reader_argv(rung.name, request, THREADS)
    result, log = run(backend, reader, argv, logs, "reader")
    answer = rd.read_answer(reader / rd.ANSWER, {"test"})
    record["reader_run"] = {
        "argv": argv,
        "exit_code": result.exit_code,
        "stopped": result.stopped,
        "log_tail": log[-1500:],
        "answer": answer,
        "expected": {"test": case["expected"]},
    }
    probe_argv = [*argv[: argv.index(python) + 1], "-I", "-S", "-c", PROBE, case["module"]]
    result, log = run(backend, probe, probe_argv, logs, "probe")
    seen = [line for line in log.splitlines() if line.startswith("PROBE ")]
    record["probe"] = {
        "argv_prefix": probe_argv[: probe_argv.index("-c")],
        "exit_code": result.exit_code,
        "seen": json.loads(seen[-1][len("PROBE ") :]) if seen else None,
        "log_tail": None if seen else log[-1500:],
    }
    seen_record = record["probe"]["seen"] or {}
    data_mount = [m for m in seen_record.get("mounts", []) if m[1] == f"/work/{target}"]
    checks = {
        "count": answer == {"test": case["expected"]},
        "reader_exit_0": record["reader_run"]["exit_code"] == 0
        and not record["reader_run"]["stopped"],
        "probe_ran": result.exit_code == 0 and bool(seen),
        "isolated_no_site": seen_record.get("flags") == {"isolated": 1, "no_site": 1},
        "data_mount_read_only": len(data_mount) == 1 and "ro" in data_mount[0][2].split(","),
    }
    record["checks"] = checks
    record["passed"] = all(checks.values())
    return record


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--python-image", required=True)
    parser.add_argument("--python-image-311", help="for the readers whose case needs 3.11")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--reader", action="append", choices=sorted(CASES))
    args = parser.parse_args()
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    base = Path.home() / "refute-run" / "readers" / stamp
    records = []
    for name in args.reader or sorted(CASES):
        print(f"== {name}", flush=True)
        case = CASES[name]
        image = args.python_image_311 if case.get("python") == "3.11" else args.python_image
        if image is None:
            raise SystemExit(f"{name} needs --python-image-311")
        record = prove(name, case, image, base / name, stamp)
        records.append(record)
        print(json.dumps({k: record.get(k) for k in ("reader", "passed", "build")}), flush=True)
    out = {
        "format": "refute-reader-vm-test-1",
        "started_utc": stamp,
        "finished_utc": datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ"),
        "reader_sha256": hashlib.sha256(pd.READER_SOURCE.read_bytes()).hexdigest(),
        "records": records,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print("record:", args.out)
    return 0 if all(r.get("passed") for r in records) else 1


if __name__ == "__main__":
    sys.exit(main())
