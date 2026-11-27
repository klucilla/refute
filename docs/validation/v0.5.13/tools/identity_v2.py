"""The identity records of NR-A2 (v0.5.13; amendment 2, revision 8, section 3; the maintainer's
decision S3, option A, #218 comment 7227283917). A new file: ``identity.py`` stays byte for byte,
for ID-BEFORE, NR-A1 and ID-AFTER.

    unit nr-a2-t2-golden:  {python} -I -B <this file> golden nr-a2-t2
    unit nr-a2-t2-claims:  {python} -I -B <this file> claims nr-a2-t2

**The code check (decision T2(4), #218 comment 7227882370).** Before and after the run, the
script records HEAD, whether the code paths (``src``, ``tests``, ``pyproject.toml``,
``uv.lock``) at HEAD are byte for byte those of the authorized commit that NR-A2's committed
manifest names, ``git status --porcelain`` of those paths and of this script, and the code digest
at HEAD (the ``src`` tree, and the SHA-256 of the fixture code, ``pyproject.toml``, ``uv.lock`` and
this script). It refuses to run, or to write its record, unless the code is the authorized code,
the porcelain status is empty, the digest is the one the freeze list holds, and HEAD did not move.
The two checks go into the record (``provenance.code_check``), and the comparator requires them.

The procedures are those of ``identity.py``, unchanged, with three differences:
- the only label allowed is ``nr-a2-t2``, and a label's folder must be empty (it runs once);
- each record names its label (``label``), so that the comparator can bind it to NR-A2;
- the record is written at the end, after every output, with the SHA-256 of each output
  (decision S3(b)); it is committed before the comparator reads any file.

- ``golden nr-a2-t2``: the outputs of versions 1 to 4 on the synthetic fixtures
  (``tests/baseline_code_v0511.py``, ``outputs()``, computed in a fresh subprocess that inherits
  this process's environment) go under ``.cache/v0513/golden/nr-a2-t2/``; the record
  ``golden-nr-a2-t2.json`` (payload: each file's SHA-256 and the error outputs; provenance: HEAD,
  versions, the script's SHA-256, the thread environment and the BLAS record) goes to the run's
  out folder.
- ``claims nr-a2-t2``: the resolved hash of every committed claim (``claim-hashes-nr-a2-t2.json``).
- **The BLAS record:** the thread variables (``OMP_NUM_THREADS``, ``OPENBLAS_NUM_THREADS``,
  ``MKL_NUM_THREADS``) as set before any numerical import, and, from a fresh child process with the
  same environment, the loaded BLAS libraries and their effective thread counts (``threadpoolctl``,
  already installed; no dependency is added).
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
LABELS = ("nr-a2-t2",)
MANIFEST = "docs/validation/v0.5.13/manifests/nr-a2.json"
SCRIPT = "docs/validation/v0.5.13/tools/identity_v2.py"
FIXTURE_CODE = "tests/baseline_code_v0511.py"
CODE_PATHS = ("src", "tests", "pyproject.toml", "uv.lock")


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, check=True,
                          text=True).stdout  # fmt: skip


def git_bytes(*args: str) -> bytes:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, check=True).stdout


def authorization() -> tuple[str, dict]:
    """The authorized code commit named by NR-A2's committed manifest, and the frozen code digest
    of the freeze list it names (decision T2(4))."""
    data = (ROOT / MANIFEST).read_bytes()
    if git_bytes("show", f"@:{MANIFEST}") != data:
        raise SystemExit(f"refused: {MANIFEST} is not committed with these bytes")
    manifest = json.loads(data)
    freeze_raw = (ROOT / manifest["freeze"]).read_bytes()
    if git_bytes("show", f"@:{manifest['freeze']}") != freeze_raw:
        raise SystemExit(f"refused: {manifest['freeze']} is not committed with these bytes")
    freeze = json.loads(freeze_raw)
    entry = freeze["prospective"]["nr-a2-t2"]
    if entry["authorized_code_commit"] != manifest["authorized_code_commit"]:
        raise SystemExit("refused: the manifest and the freeze name different authorized commits")
    return manifest["authorized_code_commit"], entry["code_digest"]


def code_check(authorized: str) -> dict:
    """T2(4): HEAD, whether the code paths at HEAD are those of the authorized commit, the
    porcelain status of the code paths and this script, and the code digest at HEAD."""
    head = git("rev-parse", "HEAD").strip()
    same = subprocess.run(["git", "diff", "--quiet", authorized, head, "--", *CODE_PATHS],
                          cwd=ROOT, capture_output=True).returncode == 0  # fmt: skip
    porcelain = git("status", "--porcelain", "--", *CODE_PATHS, SCRIPT)
    digest = {
        "src_tree": git("rev-parse", f"{head}:src").strip(),
        "fixture_code_sha256": hashlib.sha256(
            git_bytes("show", f"{head}:{FIXTURE_CODE}")
        ).hexdigest(),
        "pyproject_sha256": hashlib.sha256(git_bytes("show", f"{head}:pyproject.toml")).hexdigest(),
        "uv_lock_sha256": hashlib.sha256(git_bytes("show", f"{head}:uv.lock")).hexdigest(),
        "script_sha256": hashlib.sha256(git_bytes("show", f"{head}:{SCRIPT}")).hexdigest(),
    }
    return {"head": head, "authorized_commit": authorized, "same_code_as_authorized": same,
            "porcelain": porcelain, "digest": digest}  # fmt: skip


def require(check: dict, frozen: dict, when: str) -> None:
    if not (check["same_code_as_authorized"] and check["porcelain"] == ""
            and check["digest"] == frozen):  # fmt: skip
        raise SystemExit(f"refused: the code {when} the run is not the authorized code: {check}")


THREAD_VARS = ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")
CHILD = (
    "import json, numpy, scipy.linalg, threadpoolctl; "
    "info = threadpoolctl.threadpool_info(); "
    "print(json.dumps([{k: d.get(k) for k in ('user_api', 'internal_api', 'prefix', 'version', "
    "'num_threads', 'threading_layer')} for d in info]))"
)


def head() -> str:
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, check=True,
                          text=True).stdout.strip()  # fmt: skip


def blas_record() -> dict:
    env_seen = {v: os.environ.get(v) for v in THREAD_VARS}
    out = subprocess.run([sys.executable, "-I", "-B", "-c", CHILD], capture_output=True,
                         text=True, check=True).stdout  # fmt: skip
    return {"thread_env": env_seen, "child_threadpool_info": json.loads(out)}


def golden(label: str) -> dict:
    sys.path.insert(0, str(ROOT / "tests"))
    import numpy
    import scipy

    import baseline_code_v0511 as bc

    folder = ROOT / ".cache" / "v0513" / "golden" / label
    if folder.exists() and any(folder.iterdir()):
        raise SystemExit(f"refused: {folder} is not empty")
    folder.mkdir(parents=True, exist_ok=True)
    files, errors = {}, []
    for name, text in sorted(bc.outputs().items()):
        data = text.encode("utf-8")
        (folder / name).write_bytes(data)
        files[name] = hashlib.sha256(data).hexdigest()
        if text.startswith("ERROR"):
            errors.append(name)
    return {
        "labels": ["exploratory", "method_status: not_validated"],
        "label": label,
        "payload": {"files_sha256": files, "error_outputs": errors},
        "provenance": {
            "head": head(),
            "python": platform.python_version(),
            "numpy": numpy.__version__,
            "scipy": scipy.__version__,
            "system": platform.system(),
            "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "blas": blas_record(),
        },
    }


def claims(label: str) -> dict:
    import yaml

    from refute.core.claim import load_claim

    listed = subprocess.run(["git", "ls-files", "*.yaml", "*.yml"], cwd=ROOT, capture_output=True,
                            check=True, text=True).stdout.splitlines()  # fmt: skip
    found = []
    for rel in listed:
        try:
            data = yaml.safe_load((ROOT / rel).read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001 - not a claim if it is not readable YAML
            continue
        if isinstance(data, dict) and "pack" in data and "kind" in data:
            found.append(rel)
    hashes = {}
    for rel in sorted(found):
        try:
            hashes[rel] = load_claim(ROOT / rel).sha256()
        except Exception as exc:  # noqa: BLE001 - the failure is recorded and compared too
            hashes[rel] = f"ERROR {type(exc).__name__}: {exc}"
    return {
        "labels": ["exploratory", "method_status: not_validated"],
        "label": label,
        "payload": {"claims": hashes},
        "provenance": {
            "head": head(),
            "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "blas": {"thread_env": {v: os.environ.get(v) for v in THREAD_VARS}},
        },
    }


def main() -> int:
    kind, label = sys.argv[1], sys.argv[2]
    if label not in LABELS:
        raise SystemExit(f"label must be one of {LABELS}")
    if kind not in ("golden", "claims"):
        raise SystemExit("kind must be golden or claims")
    authorized, frozen = authorization()
    before = code_check(authorized)
    require(before, frozen, "before")  # nothing runs on other code
    doc = golden(label) if kind == "golden" else claims(label)
    after = code_check(authorized)
    require(after, frozen, "after")  # no record is written if the code changed during the run
    if after["head"] != before["head"]:
        raise SystemExit("refused: HEAD moved during the run")
    doc["provenance"]["code_check"] = {"before": before, "after": after}
    name = f"golden-{label}.json" if kind == "golden" else f"claim-hashes-{label}.json"
    out = Path(os.environ["REFUTE_RUN_OUT"])
    (out / name).write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8", newline="\n")
    count = len(next(iter(doc["payload"].values())))
    (out / "case-outputs.json").write_text(json.dumps({"case_outputs": count}), encoding="utf-8")
    print(json.dumps({"record": name, "items": count}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
