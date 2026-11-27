"""The order-proof check of v0.5.13 (charter, section 8, Codex r1, item 6, with Codex r2, item 3).

    unit order-proof:  {python} -I -B docs/validation/v0.5.13/tools/order_proof.py <manifest>

Before a draw, probe or measurement batch, its manifest is pushed alone in a single non-merge,
fast-forward evidence commit with the trailer ``CI: order-proof``. This check, a GitHub network
unit, writes a receipt ``docs/validation/v0.5.13/order-proofs/<manifest blob SHA-256>.json``; the
launcher refuses the batch without a passing receipt. It passes only if:
1. the manifest is committed at HEAD, and the commit that last changed it (the evidence commit)
   has one parent and a message with the trailer line ``CI: order-proof``;
2. the evidence commit touches only files under ``docs/validation/v0.5.13/manifests/``;
3. it is an ancestor of ``origin/main`` (it was pushed);
4. GitHub has a run of ``ci.yml`` with ``event=push`` and ``head_sha`` = the evidence commit, whose
   ``created_at`` is earlier than this check, and whose jobs other than ``plan`` were all skipped
   (the ``record-only`` plan: no test job ran).
The receipt records the run ID, its ``created_at`` and the checks.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
RECEIPTS = ROOT / "docs" / "validation" / "v0.5.13" / "order-proofs"
MANIFESTS = "docs/validation/v0.5.13/manifests/"
REPO = "klucilla/refute"


def run(*args: str) -> str:
    return subprocess.run(args, cwd=ROOT, capture_output=True, check=True, text=True).stdout


def main() -> int:
    manifest = Path(sys.argv[1]).as_posix()
    blob = subprocess.run(["git", "show", f"HEAD:{manifest}"], cwd=ROOT, capture_output=True,
                          check=True).stdout  # fmt: skip
    blob_sha = hashlib.sha256(blob).hexdigest()
    commit = run("git", "log", "-1", "--format=%H", "--", manifest).strip()
    parents = run("git", "show", "-s", "--format=%P", commit).split()
    message = run("git", "show", "-s", "--format=%B", commit)
    files = [f for f in run("git", "show", "--format=", "--name-only", commit).splitlines() if f]
    try:
        subprocess.run(["git", "merge-base", "--is-ancestor", commit, "origin/main"], cwd=ROOT,
                       check=True)  # fmt: skip
        pushed = True
    except subprocess.CalledProcessError:
        pushed = False
    url = f"repos/{REPO}/actions/workflows/ci.yml/runs?head_sha={commit}&event=push"
    jq = "[.workflow_runs[] | {id, created_at, head_sha, event, status}]"
    runs = json.loads(run("gh", "api", url, "--jq", jq))
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    run_ok, jobs_ok, chosen, jobs = False, False, None, []
    for r in runs:
        if r["head_sha"] == commit and r["event"] == "push" and r["created_at"] < now:
            chosen = r
            jobs = json.loads(run("gh", "api", f"repos/{REPO}/actions/runs/{r['id']}/jobs",
                                  "--jq", "[.jobs[] | {name, conclusion, status}]"))  # fmt: skip
            others = [j for j in jobs if j["name"] != "plan"]
            jobs_ok = all(j["conclusion"] == "skipped" for j in others)
            run_ok = True
            break
    checks = {
        "one_parent": len(parents) == 1,
        "trailer": any(line.strip() == "CI: order-proof" for line in message.splitlines()),
        "only_manifests": bool(files) and all(f.startswith(MANIFESTS) for f in files),
        "pushed_to_origin_main": pushed,
        "ci_push_run_found_before_now": run_ok,
        "record_only_no_test_job": jobs_ok,
    }
    receipt = {
        "schema": "refute-v0513-order-proof-1",
        "utc": now,
        "manifest": manifest,
        "manifest_sha256": blob_sha,
        "evidence_commit": commit,
        "evidence_files": files,
        "ci_run_id": chosen["id"] if chosen else None,
        "ci_run_created_at": chosen["created_at"] if chosen else None,
        "ci_jobs": jobs,
        "checks": checks,
        "passed": all(checks.values()),
    }
    RECEIPTS.mkdir(parents=True, exist_ok=True)
    (RECEIPTS / f"{blob_sha}.json").write_text(json.dumps(receipt, indent=1) + "\n",
                                               encoding="utf-8", newline="\n")  # fmt: skip
    out = Path(os.environ.get("REFUTE_RUN_OUT", ROOT / ".cache" / "v0513"))
    body = json.dumps(receipt).encode("utf-8")
    (out / "transfer.json").write_text(json.dumps({"inbound_bytes": 2 * len(body) + 65536,
        "basis": "an upper estimate: twice the receipt's size plus 64 KiB for the gh calls"}),
        encoding="utf-8", newline="\n")  # fmt: skip
    print(json.dumps({"passed": receipt["passed"], "checks": checks, "run": receipt["ci_run_id"]}))
    return 0 if receipt["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
