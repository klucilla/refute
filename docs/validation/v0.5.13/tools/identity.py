"""The protected-identity records of v0.5.13 (charter: step 0 "ID-BEFORE", step 1 "NR-A1", step 5
"ID-AFTER"). New file; the procedures are those of v0.5.12's golden_local.py and claim_hashes.py
(identity verification, not a rerun), with this phase's paths, and the BLAS record of step 1.

    unit id-golden:  {python} -I -B docs/validation/v0.5.13/tools/identity.py golden <label>
    unit id-claims:  {python} -I -B docs/validation/v0.5.13/tools/identity.py claims <label>

- ``golden <label>``: the outputs of versions 1 to 4 on the synthetic fixtures
  (``tests/baseline_code_v0511.py``, ``outputs()``, which computes them in a fresh subprocess that
  inherits this process's environment). Each output goes under ``.cache/v0513/golden/<label>/``;
  the record ``golden-<label>.json`` (payload: each file's SHA-256 and the error outputs;
  provenance: HEAD, versions, the thread environment and the BLAS record) goes to the run's out
  folder.
- ``claims <label>``: the resolved hash of every committed claim (``claim-hashes-<label>.json``).
- **The BLAS record** (step 1): the thread variables (``OMP_NUM_THREADS``,
  ``OPENBLAS_NUM_THREADS``, ``MKL_NUM_THREADS``) as set before any numerical import, and, from a
  fresh child process with the same environment (the process kind that computes the outputs), the
  loaded BLAS libraries and their effective thread counts, read with ``threadpoolctl`` (already
  installed; no dependency is added).

Labels allowed: ``before``, ``after`` (ID-BEFORE / ID-AFTER) and ``nr-a1-default``, ``nr-a1-t1``,
``nr-a1-t4`` (NR-A1). A label's folder must be empty: each runs once.
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
LABELS = ("before", "after", "nr-a1-default", "nr-a1-t1", "nr-a1-t4")
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
        "payload": {"claims": hashes},
        "provenance": {
            "head": head(),
            "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        },
    }


def main() -> int:
    kind, label = sys.argv[1], sys.argv[2]
    if label not in LABELS:
        raise SystemExit(f"label must be one of {LABELS}")
    doc = golden(label) if kind == "golden" else claims(label) if kind == "claims" else None
    if doc is None:
        raise SystemExit("kind must be golden or claims")
    name = f"golden-{label}.json" if kind == "golden" else f"claim-hashes-{label}.json"
    out = Path(os.environ["REFUTE_RUN_OUT"])
    (out / name).write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8", newline="\n")
    count = len(next(iter(doc["payload"].values())))
    (out / "case-outputs.json").write_text(json.dumps({"case_outputs": count}), encoding="utf-8")
    print(json.dumps({"record": name, "items": len(next(iter(doc["payload"].values())))}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
