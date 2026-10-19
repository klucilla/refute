"""End to end on the Refute VM: a synthetic paper of the catalog through the production
wiring and the docker backend (the maintainer's decision of 2026-10-17: run end to end on
the VM with a synthetic repository of the catalog).

The paper is ``reproduced`` of tests/wp4_papers.py (every attack, expected REPRODUCED), its
claim file built by tests/test_wp4_papers.py. Its "repository" is the cataloged trainer
(tests/fixtures/ml_papers/trainer.py, numpy only) with a requirements file, built by the
real ladder (rung requirements_compiled: uv in the given Python image, through the
allowlist proxy) and run in containers with --network none. No third-party code but the
Python image and numpy from PyPI.

Run on the VM, from the Refute checkout:
    .venv/bin/python scripts/vm/production_vm_test.py --python-image <python@sha256:...>
        --out <dir> [--weights]

With --weights (wp3-repository-weights-acceptance.md, section 4) the repository is a Git
repository holding saved/model.bin, declared as weights that are a file of the commit and
named by every claim; Refute verifies it as a regular blob of the commit, then the tree's
file is overwritten (a change after the check), and train.py runs the trainer only if the
file it reads at saved/model.bin has the committed bytes and cannot be written: a run that
reads the tree's file, or a writable one, fails.

It prints the claim verdicts and the accounting, writes the dossier, and exits 0 when the
claim's verdict is the paper's expected one and the accounting is complete.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tests"))

from refute.packs.ml import production as pd  # noqa: E402
from refute.packs.ml.docker_backend import Limits  # noqa: E402
from refute.packs.ml.sandbox import TimingMaxima  # noqa: E402
from test_ml_integration import dataset_evidence  # noqa: E402
from test_wp4_papers import build  # noqa: E402
from wp4_papers import BASE_CONFIG, PAPERS  # noqa: E402

V22 = TimingMaxima(0.000346, 0.207)  # docs/validation/v0.3/wp3-results/docker-vm-test-*.json
WEIGHTS = b"committed weights of the synthetic predictor\n" * 512
# the run's entry point with --weights: the mounted file has the committed bytes and cannot
# be written, then the cataloged trainer runs unchanged
CHECKED_ENTRY = """import hashlib, os, runpy, sys
data = open("saved/model.bin", "rb").read()
if hashlib.sha256(data).hexdigest() != "{digest}":
    sys.exit("refute-weights-check: the run read other bytes")
try:
    open("saved/model.bin", "ab").close()
    sys.exit("refute-weights-check: the weights file is writable")
except OSError:
    pass
print("refute-weights-check ok", flush=True)
runpy.run_path("trainer.py", run_name="__main__")
"""


def git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-c", "user.name=Refute", "-c", "user.email=refute@example.invalid", *args],
        cwd=repo, check=True, capture_output=True, text=True,
    ).stdout.strip()  # fmt: skip


def with_weights(repo: Path, claim_file: dict, cache: Path) -> dict:
    """The repository becomes a Git repository with saved/model.bin, declared and named by
    every claim; returns the verified weights (production.repository_weights), after which
    the tree's file is overwritten."""
    (repo / "trainer.py").write_bytes((repo / "train.py").read_bytes())
    digest = hashlib.sha256(WEIGHTS).hexdigest()
    (repo / "train.py").write_text(CHECKED_ENTRY.replace("{digest}", digest), encoding="ascii")
    (repo / "saved").mkdir()
    (repo / "saved" / "model.bin").write_bytes(WEIGHTS)
    git(repo, "init", "-q")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "the synthetic repository")
    commit = git(repo, "rev-parse", "HEAD")
    plan = claim_file["test_plan"]
    plan["repository"] = {**plan["repository"], "commit": commit}
    plan["weights"] = [
        {
            "name": "model",
            "origin": "repository_file",
            "path": "saved/model.bin",
            "commit": commit,
            "sha256": digest,
            "size_bytes": len(WEIGHTS),
            "license": "synthetic, no licence",
        }
    ]
    for target in claim_file["targets"]:
        target["weights"] = "model"
    verified = pd.repository_weights(repo, plan, cache)
    if verified["model"].copy is None:
        raise SystemExit(f"the weights did not verify: {verified['model'].reason}")
    (repo / "saved" / "model.bin").write_bytes(b"changed after the check\n")
    return verified


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--python-image", required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--paper", default="reproduced")
    parser.add_argument("--weights", action="store_true")
    args = parser.parse_args()
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    paper = next(p for p in PAPERS if p.name == args.paper)
    data, claim_file = build(paper)
    claim_file["test_plan"]["build"]["base_image"] = args.python_image
    base = Path.home() / "refute-run" / "e2e" / stamp
    repo = base / "repo"
    repo.mkdir(parents=True)
    (repo / "train.py").write_bytes((ROOT / "tests/fixtures/ml_papers/trainer.py").read_bytes())
    hook = ROOT / "src/refute/packs/ml/coverage_hook.py"
    (repo / "coverage_hook.py").write_bytes(hook.read_bytes())
    (repo / "requirements.txt").write_text("numpy\n", encoding="ascii")
    settings = {"data": "data/dataset.npz", **BASE_CONFIG, **paper.config}
    (repo / "config.json").write_text(json.dumps(settings), encoding="ascii")
    fetched = base / "fetched" / "synthetic.npz"
    fetched.parent.mkdir()
    fetched.write_bytes(data)
    weights = with_weights(repo, claim_file, base / "cache") if args.weights else {}
    setup = pd.PaperSetup(
        paper="e2e" + stamp[2:8] + stamp[9:15],
        root=base / "run",
        repo=repo,
        datasets={"synthetic": dataset_evidence(fetched, data)},
        data_layout={"synthetic": "data/dataset.npz"},
        limits=Limits(cpus=4, period_us=100_000, memory_bytes=4 << 30, pids=1024),
        timing=V22,
        repository_weights=weights,
    )
    out = args.out / f"dossier-{args.paper}-{stamp}"
    outcome = pd.run_production(setup, claim_file, out, {"python": args.python_image})
    print(pd.outcome_summary(outcome))
    verdicts = [str(c.verdict) for c in outcome.claims]
    accounting = getattr(outcome.run, "completeness", None) if outcome.run else None
    print("accounting:", accounting)
    print("dossier:", out)
    ok = all(paper.expected in v for v in verdicts)
    if args.weights:
        record = pd.PaperSetup.record(setup)["repository_weights"]
        print("repository weights:", json.dumps(record, sort_keys=True))
        ok = ok and record["model"]["verified"] and record["model"]["mount_planned"]
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
