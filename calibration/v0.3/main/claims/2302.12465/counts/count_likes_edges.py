"""N of 2302.12465: the edges of the canonical type user,likes,item in datasets/synthetic,
counted by the engine's dgl container reader (src/refute/packs/ml/container_reader.py) in
the count's image, as a production reader runs: a fresh folder holding Refute's reader only,
the dataset's checked copy mounted read only, no network, the production limits.

Run on the VM from the Refute checkout:
    .venv/bin/python <this> <count root> <new work folder>
"""

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, "scripts/vm")
import measure_paper as mp  # noqa: E402

from refute.packs.ml import production as pd  # noqa: E402
from refute.packs.ml import readers as rd  # noqa: E402
from refute.packs.ml.docker_backend import ContainerPlan, DockerBackend  # noqa: E402

PATH = "datasets/synthetic"
SHA256 = "a368d8f68a6bbfd7ea5cf844fe217872c79ac1f3c160f4f46823bbbb7798df9f"
SIZE = 93724
SPLITS = {
    "likes_edges": {"expected_examples": 1, "source": "reader:container:dgl:#user,likes,item"}
}

root, work = Path(sys.argv[1]), Path(sys.argv[2])
work.mkdir()
built = json.loads((root / "build.json").read_text(encoding="utf-8"))
source = root / "clone" / PATH
if source.is_symlink() or not source.is_file():
    raise SystemExit("the dataset is not a regular file of the clone")
data = source.read_bytes()
if hashlib.sha256(data).hexdigest() != SHA256 or len(data) != SIZE:
    raise SystemExit("the dataset's bytes differ from the declared ones")
copy = work / "verified" / SHA256
copy.parent.mkdir()
copy.write_bytes(data)
copy.chmod(0o444)

folder = work / "reader"
folder.mkdir()
(folder / pd.READER_SCRIPT).write_bytes(pd.READER_SOURCE.read_bytes())
(folder / pd.READER_SCRIPT).chmod(0o444)
(folder / "datasets").mkdir()
(folder / "datasets").chmod(0o1777)
folder.chmod(0o1777)
request = rd.container_request(PATH, SPLITS)
env = {k: "22" for k in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS",
                         "NUMEXPR_NUM_THREADS")}  # fmt: skip
argv = pd.reader_argv(built["rung"], request, env)
plan = ContainerPlan(built["image"], data_mounts=((str(copy.resolve()), PATH),))
backend = DockerBackend(mp.run_paper_id({"name": "pgcn", "run_id": "n"}), mp.LIMITS, {folder: plan})
log = work / "reader.log"
result, seconds = mp.run(backend, folder, argv, log, 30)
counts = rd.read_answer(folder / rd.ANSWER, {"likes_edges"})
out = {
    "reader": "container_reader.py dgl, user,likes,item",
    "reader_sha256": hashlib.sha256(pd.READER_SOURCE.read_bytes()).hexdigest(),
    "image": built["image"],
    "rung": built["rung"],
    "dataset": {"path": PATH, "sha256": SHA256, "size_bytes": SIZE},
    "exit_code": result.exit_code,
    "stopped": result.stopped,
    "seconds": round(seconds, 1),
    "counts": counts,
    "finished_utc": mp.now(),
    "refute_commit": subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True
    ).stdout.strip(),
}
(work / "likes_edges_record.json").write_text(json.dumps(out, indent=1, sort_keys=True) + "\n",
                                    encoding="utf-8")  # fmt: skip
print(json.dumps(out, sort_keys=True))
if result.exit_code != 0:
    print(log.read_text(encoding="utf-8", errors="replace")[-3000:])
shutil.rmtree(folder, ignore_errors=True)
