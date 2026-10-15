"""Verify each historical lock at its tag, in that tag's own environment (option C of
docs/validation/v0.3/lock-compat-acceptance.md, L8).

For each (tag, claim) below the script:

1. checks out the tag in a detached git worktree under `.cache/lock-compat/`
   (the main checkout is not touched);
2. runs `uv sync --frozen` there (the tag's own `uv.lock`);
3. runs `uv run --frozen refute verify <claim> --json` there and saves the output to
   `<out>/<tag>.json`;
4. prints the status, the locked and current hashes and the SHA-256 of the saved file.

It runs by hand, never in the test suite: `uv sync` may need the network. With
`--remove-worktrees` it removes its own worktrees afterwards (`git worktree remove`),
only below `.cache/lock-compat/`.

Usage (project root):
    .venv/Scripts/python.exe scripts/verify_locked_tags.py [--python PATH] [--remove-worktrees]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / ".cache" / "lock-compat"
LOCKED_TAGS = (
    ("v0.1.0", "calibration/self_claim.yaml"),
    ("v0.2.0-calibration-lock", "calibration/v0.2/self_claim.yaml"),
)


def run(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=str(cwd), capture_output=True, text=True)


def inside_work(path: Path) -> bool:
    return path.resolve().is_relative_to(WORK.resolve())


def worktree_problems(worktree: Path, claim: str, expected_commit: str) -> list[str]:
    """Reasons not to trust a worktree for the historical check (empty when it is fine).

    The worktree must be at the tag's commit, with no change to any tracked file, and
    the lock of the claim must have the identity recorded in the frozen table of
    ``refute.core.lock_compat`` (read from this checkout's ``src/``)."""
    sys.path.insert(0, str(ROOT / "src"))
    from refute.core.lock_compat import HISTORICAL_LOCKS, lock_identity

    problems = []
    head = run(["git", "rev-parse", "HEAD"], worktree).stdout.strip()
    if head != expected_commit:
        problems.append(f"worktree is at {head or 'nothing'}, expected {expected_commit}")
    status = run(["git", "status", "--porcelain", "--untracked-files=no"], worktree)
    if status.returncode != 0 or status.stdout.strip():
        problems.append("tracked files differ from the commit: " + status.stdout.strip()[:300])
    lock_file = worktree / Path(claim).with_suffix(".lock.json")
    try:
        identity = lock_identity(json.loads(lock_file.read_text(encoding="utf-8")))
    except (OSError, ValueError) as exc:
        problems.append(f"lock unreadable: {exc}")
    else:
        if not any(dict(e.identity) == identity for e in HISTORICAL_LOCKS):
            problems.append("the lock does not have a historical identity of the table")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--python", help="interpreter for uv (default: uv's choice)")
    parser.add_argument("--out", type=Path, default=WORK / "tag-verify")
    parser.add_argument("--remove-worktrees", action="store_true")
    args = parser.parse_args()
    python = ["--python", args.python] if args.python else []
    args.out.mkdir(parents=True, exist_ok=True)
    failures = 0
    for tag, claim in LOCKED_TAGS:
        worktree = WORK / f"wt-{tag}"
        if not inside_work(worktree):
            raise SystemExit(f"refusing a worktree outside {WORK}: {worktree}")
        expected = run(["git", "rev-parse", f"{tag}^{{commit}}"], ROOT).stdout.strip()
        if not worktree.is_dir():
            added = run(["git", "worktree", "add", "--detach", str(worktree), tag], ROOT)
            if added.returncode != 0:
                print(f"{tag}: git worktree add failed: {added.stderr.strip()}")
                failures += 1
                continue
        problems = worktree_problems(worktree, claim, expected)
        if problems:
            print(f"{tag}: worktree refused: " + "; ".join(problems))
            failures += 1
            continue
        head = expected
        sync = run(["uv", "sync", "--frozen", *python], worktree)
        if sync.returncode != 0:
            print(f"{tag}: uv sync --frozen failed: {sync.stderr.strip()[-500:]}")
            failures += 1
            continue
        verify = run(
            ["uv", "run", "--frozen", *python, "refute", "verify", claim, "--json"], worktree
        )
        out_file = args.out / f"{tag}.json"
        out_file.write_text(verify.stdout, encoding="utf-8", newline="\n")
        digest = hashlib.sha256(out_file.read_bytes()).hexdigest()
        try:
            result = json.loads(verify.stdout)
        except json.JSONDecodeError:
            print(f"{tag}: verify did not return JSON (exit {verify.returncode})")
            failures += 1
            continue
        print(
            f"{tag} {head[:12]} {claim}: {result['status']} (exit {verify.returncode}); "
            f"claim locked {result['locked_claim_sha256']} now {result['current_claim_sha256']}; "
            f"code locked {result['locked_code_sha256']} now {result['current_code_sha256']}; "
            f"output {out_file.relative_to(ROOT).as_posix()} sha256 {digest}"
        )
        if result["status"] != "PASS" or verify.returncode != 0:
            failures += 1
        elif worktree_problems(worktree, claim, expected):  # nothing changed during the run
            print(f"{tag}: tracked files changed during the run")
            failures += 1
    if args.remove_worktrees:
        for tag, _ in LOCKED_TAGS:
            worktree = WORK / f"wt-{tag}"
            if worktree.is_dir() and inside_work(worktree):
                removed = run(["git", "worktree", "remove", "--force", str(worktree)], ROOT)
                print(
                    f"removed worktree {worktree.relative_to(ROOT).as_posix()}: "
                    f"exit {removed.returncode}"
                )
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
