"""Build the provenance fixtures of the historical lock projections (L7 of
docs/validation/v0.3/lock-compat-acceptance.md).

For each historical lock this script:

1. extracts `src/` of the lock's own commit (`git archive`) into
   `.cache/lock-compat/<commit>/` and resolves the claim with that code in a child
   process of the project interpreter;
2. checks that the resulting canonical form hashes to the locked `claim_sha256`, and
   writes it to `tests/fixtures/locked_canonical/<claim_id>.json`;
3. resolves the claim with the current code and prints, for the table in
   `src/refute/core/lock_compat.py`, the key paths added since the lock (at their
   highest new level) with their current values.

It changes no lock, claim or history file. The child process uses the current
environment's dependencies with the old source; the fixture is valid only because its
hash equals the locked hash, which the script and the tests check.

Usage (from the project root, project interpreter):
    .venv/Scripts/python.exe scripts/lock_compat_snapshot.py
"""

from __future__ import annotations

import io
import json
import subprocess
import sys
import tarfile
from pathlib import Path
from pprint import pformat

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / ".cache" / "lock-compat"
FIXTURES = ROOT / "tests" / "fixtures" / "locked_canonical"
CLAIMS = ("calibration/self_claim.yaml", "calibration/v0.2/self_claim.yaml")

CHILD = """
import json, sys
sys.path.insert(0, sys.argv[1])
from refute.core.claim import load_claim
print(json.dumps(load_claim(sys.argv[2]).canonical()))
"""

sys.path.insert(0, str(ROOT / "src"))
from refute.core.canonical import canonical_sha256  # noqa: E402
from refute.core.claim import load_claim  # noqa: E402
from refute.core.lock import lock_path_for, read_lock  # noqa: E402


def extract_src(commit: str) -> Path:
    target = WORK / commit[:12]
    if not (target / "src").is_dir():
        target.mkdir(parents=True, exist_ok=True)
        data = subprocess.run(
            ["git", "-C", str(ROOT), "archive", "--format=tar", commit, "src"],
            capture_output=True,
            check=True,
        ).stdout
        with tarfile.open(fileobj=io.BytesIO(data)) as archive:
            archive.extractall(target, filter="data")
    return target / "src"


def added_paths(current, old, prefix=()):
    """Key paths of ``current`` absent from ``old``, at their highest new level."""
    out = {}
    for key, value in current.items():
        path = (*prefix, key)
        if key not in old:
            out[path] = value
        elif isinstance(value, dict) and isinstance(old[key], dict):
            out.update(added_paths(value, old[key], path))
    return out


def main() -> int:
    FIXTURES.mkdir(parents=True, exist_ok=True)
    status = 0
    for claim_rel in CLAIMS:
        claim = ROOT / claim_rel
        lock = read_lock(lock_path_for(claim))
        src = extract_src(lock["git_commit"])
        child = subprocess.run(
            [sys.executable, "-c", CHILD, str(src), str(claim)],
            capture_output=True,
            text=True,
            check=True,
            cwd=str(WORK),
        )
        at_lock = json.loads(child.stdout)
        digest = canonical_sha256(at_lock)
        if digest != lock["claim_sha256"]:
            print(f"{claim_rel}: lock-time form hashes to {digest}, not the locked hash")
            status = 1
            continue
        fixture = {
            "claim_id": lock["claim_id"],
            "claim_path_in_repo": lock["claim_path_in_repo"],
            "lock_commit": lock["git_commit"],
            "locked_claim_sha256": lock["claim_sha256"],
            "generated_by": "scripts/lock_compat_snapshot.py",
            "canonical": at_lock,
        }
        out = FIXTURES / f"{lock['claim_id']}.json"
        out.write_text(
            json.dumps(fixture, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        current = load_claim(claim).canonical()
        added = added_paths(current, at_lock)
        print(f"# {lock['claim_id']}: fixture {out.relative_to(ROOT).as_posix()}")
        print(f"# full current hash {canonical_sha256(current)}")
        print(pformat(added, width=88, sort_dicts=True))
    return status


if __name__ == "__main__":
    sys.exit(main())
