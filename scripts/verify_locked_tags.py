"""Verify each lock at the code it froze, in that code's own environment (option C of
docs/validation/v0.3/lock-compat-acceptance.md, L8; the v0.3 locks by the maintainer's decision
of 2026-10-20).

Two lists, checked apart:

- ``LOCKED_TAGS``, the **historical** locks of v0.1 and v0.2: their claims match the lock by the
  projection of ``refute.core.lock_compat``, so a worktree is trusted only when its lock has a
  historical identity of that table (``HISTORICAL_LOCKS``).
- ``DIRECT_LOCKS``, the five locks of the v0.3 main sample: never in ``HISTORICAL_LOCKS`` (that
  table only projects old claims). Each entry gives the tag, the full commit the tag must point
  to, the claim path and the expected identity of the lock (``lock_compat.lock_identity``). The
  worktree must be at that commit with no tracked change and no untracked file, the lock must
  have exactly that identity, and ``refute verify`` must return ``PASS`` directly: no projection.

For each tag the script:

1. checks out the tag in a detached git worktree under `.cache/lock-compat/` (the main checkout
   is not touched);
2. runs `uv sync --frozen` there (the tag's own `uv.lock`);
3. for each claim of that tag, runs `uv run --frozen refute verify <claim> --json` there and
   saves the output to `<out>/<tag>__<claim path, "/" written "__">.json`, one file per claim;
4. writes `<out>/summary.json`, which lists every expected (tag, claim) and passes only when all
   of them are present and PASS; prints one line per claim and the joint result.

A tag that does not exist is a failure. With ``--allow-missing-tags`` a direct lock whose tag is
not created yet is checked at its full commit instead, and the summary records the tag as absent
(for the check before the tag is created); a tag that exists must point to its commit.

It runs by hand, never in the test suite: `uv sync` may need the network. With
`--remove-worktrees` it removes its own worktrees afterwards (`git worktree remove`), only below
`.cache/lock-compat/`. Exit code 0 only when the joint result is PASS.

Usage (project root):
    .venv/Scripts/python.exe scripts/verify_locked_tags.py [--python PATH] [--out DIR]
        [--allow-missing-tags] [--remove-worktrees]
"""

# No ``from __future__ import annotations``: the tests load this file with
# importlib.util.spec_from_file_location, without a sys.modules entry, and the dataclasses
# below would then fail to resolve string annotations.
import argparse
import hashlib
import json
import subprocess
import sys
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / ".cache" / "lock-compat"
LOCKED_TAGS = (
    ("v0.1.0", "calibration/self_claim.yaml"),
    ("v0.2.0-calibration-lock", "calibration/v0.2/self_claim.yaml"),
)

V03_TAG = "v0.3.0-main-lock"
V03_COMMIT = "b6f5346cbf2d6c5398b3da2ec37d91a6ae1c87bc"
V03_CODE_SHA256 = "3165e1417ebe1f9474145076000f14f3b561b2cdd55f8c2b6b36ffde26e17322"


@dataclass(frozen=True)
class DirectLock:
    """A lock checked by a direct PASS at its frozen code (never projected)."""

    tag: str
    commit: str
    claim: str
    identity: Mapping[str, Any] = field(default_factory=dict)


def _v03(paper: str, claim_sha256: str, git_commit: str, locked_at_utc: str) -> DirectLock:
    claim = f"calibration/v0.3/main/claims/{paper}/claim/claim.yaml"
    return DirectLock(
        tag=V03_TAG,
        commit=V03_COMMIT,
        claim=claim,
        identity={
            "lock_version": 1,
            "canonicalization": "refute-cjson-1",
            "claim_id": f"v0.3-main-{paper}",
            "claim_kind": "replicate",
            "claim_path_in_repo": claim,
            "claim_sha256": claim_sha256,
            "code_sha256": V03_CODE_SHA256,
            "git_commit": git_commit,
            "locked_at_utc": locked_at_utc,
        },
    )


# Read from the five lock files at b6f5346 (2026-10-20); a literal, never read from the tree
# being checked.
DIRECT_LOCKS: tuple[DirectLock, ...] = (
    _v03(
        "2302.12465",
        "cb7720a2fd3dc4d95315bc2ea04829c10060992f1f3c6739d30ce24e614cd6c6",
        "408a1d724ed7332ed78079eaa1a765449b4d3f68",
        "2026-10-19T13:31:04Z",
    ),
    _v03(
        "2305.19518",
        "ff1ac0933507882c63178a9fa7e7d5b0c82279a7ee758b9ac6bdbec9e8403424",
        "abdc9031f565aa445e912603dbb24b33a9e64c80",
        "2026-10-19T13:49:28Z",
    ),
    _v03(
        "2309.15704",
        "598543893374b9c4742d44f25bbaf7fa89cbc3f2faf7f4e857c2359a91b34957",
        "4b35d35232725063c0a611851ba3561a4a6e19c2",
        "2026-10-19T14:07:09Z",
    ),
    _v03(
        "2407.11735",
        "dcea7ed105a99f336a124db706d1683d058b12fb8b1a2979bc838ede9a25a34f",
        "8a8c586b12c0cc799ee08197e3758fdfb2901e50",
        "2026-10-19T14:24:53Z",
    ),
    _v03(
        "2502.16782",
        "3e59b8353da037e57d03b68817c7b01c947e06ef113555c8b79f4ec842b857ab",
        "a27fd3c50dd647594858a8e9547194a6c3334b55",
        "2026-10-19T14:42:38Z",
    ),
)


@dataclass(frozen=True)
class Check:
    """One expected (tag, claim) of the joint verification."""

    kind: str  # "historical" or "direct"
    tag: str
    claim: str
    commit: str | None = None  # direct locks only: the full commit the tag must point to
    identity: Mapping[str, Any] | None = None  # direct locks only

    @property
    def key(self) -> str:
        return f"{self.tag}::{self.claim}"


def expected_checks() -> list[Check]:
    checks = [Check("historical", tag, claim) for tag, claim in LOCKED_TAGS]
    checks += [
        Check("direct", d.tag, d.claim, commit=d.commit, identity=dict(d.identity))
        for d in DIRECT_LOCKS
    ]
    return checks


def output_name(tag: str, claim: str) -> str:
    """One unambiguous file name per (tag, claim): no two checks can share it."""
    return f"{tag}__{claim.replace('/', '__')}.json"


def run(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=str(cwd), capture_output=True, text=True)


def inside_work(path: Path) -> bool:
    return path.resolve().is_relative_to(WORK.resolve())


def _lock_of(worktree: Path, claim: str) -> tuple[dict | None, str | None]:
    lock_file = worktree / Path(claim).with_suffix(".lock.json")
    try:
        return json.loads(lock_file.read_text(encoding="utf-8")), None
    except (OSError, ValueError) as exc:
        return None, f"lock unreadable: {exc}"


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
    lock, error = _lock_of(worktree, claim)
    if error:
        problems.append(error)
    elif not any(dict(e.identity) == lock_identity(lock) for e in HISTORICAL_LOCKS):
        problems.append("the lock does not have a historical identity of the table")
    return problems


def direct_worktree_problems(
    worktree: Path, claim: str, expected_commit: str, identity: Mapping[str, Any]
) -> list[str]:
    """Reasons not to trust a worktree for a direct lock (empty when it is fine): the worktree
    at exactly ``expected_commit``, clean (no tracked change and no untracked file, since an
    untracked file under ``src/`` would enter the code hash), and the lock with exactly the
    expected identity."""
    sys.path.insert(0, str(ROOT / "src"))
    from refute.core.lock_compat import lock_identity

    problems = []
    head = run(["git", "rev-parse", "HEAD"], worktree).stdout.strip()
    if head != expected_commit:
        problems.append(f"worktree is at {head or 'nothing'}, expected {expected_commit}")
    status = run(["git", "status", "--porcelain", "--untracked-files=all"], worktree)
    if status.returncode != 0 or status.stdout.strip():
        problems.append("the worktree is not clean: " + status.stdout.strip()[:300])
    lock, error = _lock_of(worktree, claim)
    if error:
        problems.append(error)
    else:
        found = lock_identity(lock)
        if found != dict(identity):
            differ = sorted(
                k for k in set(found) | set(identity) if found.get(k) != identity.get(k)
            )
            problems.append("the lock does not have the expected identity: " + ", ".join(differ))
    return problems


def result_problems(
    check: Check, result: Mapping[str, Any] | None, exit_code: int | None
) -> list[str]:
    """Why one verify result does not count as a PASS of its check (empty when it does)."""
    if result is None:
        return ["no verify result"]
    problems = []
    if result.get("status") != "PASS" or exit_code != 0:
        problems.append(f"verify {result.get('status')} (exit {exit_code})")
    if check.kind == "direct":
        if result.get("claim_projection") is not None:
            problems.append(f"a projection was applied: {result.get('claim_projection')}")
        identity = check.identity or {}
        if result.get("locked_claim_sha256") != identity.get("claim_sha256"):
            problems.append("the locked claim hash is not the expected one")
        if result.get("current_claim_sha256") != identity.get("claim_sha256"):
            problems.append("the current claim hash is not the locked one")
        if result.get("locked_code_sha256") != identity.get("code_sha256"):
            problems.append("the locked code hash is not the expected one")
        if result.get("current_code_sha256") != identity.get("code_sha256"):
            problems.append("the current code hash is not the locked one")
    return problems


def summarize(checks: Sequence[Check], outcomes: Mapping[str, Mapping[str, Any]]) -> dict:
    """The joint result: PASS only when every expected check has an outcome with no problem.

    A missing outcome, an outcome with problems, or an outcome for a check that is not
    expected each makes the joint result FAIL."""
    rows = []
    for check in checks:
        outcome = outcomes.get(check.key)
        problems = list(outcome.get("problems", [])) if outcome else ["no outcome"]
        rows.append(
            {
                "kind": check.kind,
                "tag": check.tag,
                "claim": check.claim,
                "status": outcome.get("status") if outcome else None,
                "output": outcome.get("output") if outcome else None,
                "output_sha256": outcome.get("output_sha256") if outcome else None,
                "tag_state": outcome.get("tag_state") if outcome else None,
                "problems": problems,
                "pass": not problems,
            }
        )
    unexpected = sorted(set(outcomes) - {c.key for c in checks})
    joint = "PASS" if rows and all(r["pass"] for r in rows) and not unexpected else "FAIL"
    absent = sorted({r["tag"] for r in rows if str(r["tag_state"] or "").startswith("absent")})
    return {
        "joint": joint,
        "expected": len(checks),
        "passed": sum(r["pass"] for r in rows),
        "unexpected": unexpected,
        # tags checked at their full commit because they are not created yet
        # (--allow-missing-tags); a PASS here is a PASS at the commit, not at the tag
        "tags_absent": absent,
        "checks": rows,
    }


@dataclass(frozen=True)
class Prepared:
    """A tag's worktree, ready for verify, or the reasons it is not."""

    worktree: Path | None
    tag_state: str
    commit: str  # the commit the worktree must be at ("" when unknown)
    problems: tuple[str, ...] = ()


Prepare = Callable[[str, str | None], Prepared]
Verify = Callable[[Path, str], tuple[str, int]]


def _trust_problems(check: Check, worktree: Path, commit: str) -> list[str]:
    if check.kind == "direct":
        return direct_worktree_problems(worktree, check.claim, commit, check.identity or {})
    return worktree_problems(worktree, check.claim, commit)


def run_checks(checks: Sequence[Check], out: Path, prepare: Prepare, verify: Verify) -> dict:
    """Run every check, write one file per claim and ``summary.json``; return the summary.

    ``prepare(tag, commit)`` gives the tag's ``Prepared`` worktree (``commit`` is the full
    commit a direct lock's tag must point to, None for a historical tag);
    ``verify(worktree, claim)`` gives (stdout, exit code) of ``refute verify --json``."""
    out.mkdir(parents=True, exist_ok=True)
    names = [output_name(c.tag, c.claim) for c in checks]
    if len(set(names)) != len(names):
        raise SystemExit("two checks would write the same output file")
    prepared: dict[str, Prepared] = {}
    outcomes: dict[str, dict] = {}
    for check, name in zip(checks, names, strict=True):
        if check.tag not in prepared:
            prepared[check.tag] = prepare(check.tag, check.commit)
        ready = prepared[check.tag]
        worktree, problems = ready.worktree, list(ready.problems)
        if check.kind == "direct" and ready.commit != check.commit:
            problems.append(f"the tag's worktree is for {ready.commit}, expected {check.commit}")
        outcome: dict[str, Any] = {"tag_state": ready.tag_state, "status": None, "output": None}
        if worktree is not None and not problems:
            problems += _trust_problems(check, worktree, ready.commit)
        if worktree is not None and not problems:
            stdout, code = verify(worktree, check.claim)
            out_file = out / name
            out_file.write_text(stdout, encoding="utf-8", newline="\n")
            outcome["output"] = name
            outcome["output_sha256"] = hashlib.sha256(out_file.read_bytes()).hexdigest()
            try:
                result = json.loads(stdout)
            except json.JSONDecodeError:
                result = None
                problems.append(f"verify did not return JSON (exit {code})")
            if result is not None:
                outcome["status"] = result.get("status")
                problems += result_problems(check, result, code)
            # nothing changed during the run
            after = _trust_problems(check, worktree, ready.commit)
            problems += [f"after the run: {p}" for p in after]
        outcome["problems"] = problems
        outcomes[check.key] = outcome
    summary = summarize(checks, outcomes)
    (out / "summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    return summary


def make_prepare(python: list[str], allow_missing_tags: bool) -> Prepare:
    def prepare(tag: str, commit: str | None) -> Prepared:
        resolved = run(["git", "rev-parse", "--verify", "--quiet", f"{tag}^{{commit}}"], ROOT)
        found = resolved.stdout.strip() if resolved.returncode == 0 else ""
        if found:
            state = "present"
            if commit is not None and found != commit:
                return Prepared(None, state, found, (f"tag {tag} points to {found}, not {commit}",))
            target, expected = tag, found
        elif commit is not None and allow_missing_tags:
            state = "absent (checked at its commit)"
            target, expected = commit, commit
        else:
            return Prepared(None, "absent", commit or "", (f"tag {tag} does not exist",))
        worktree = WORK / f"wt-{tag}"
        if not inside_work(worktree):
            raise SystemExit(f"refusing a worktree outside {WORK}: {worktree}")
        if not worktree.is_dir():
            added = run(["git", "worktree", "add", "--detach", str(worktree), target], ROOT)
            if added.returncode != 0:
                why = f"git worktree add failed: {added.stderr.strip()}"
                return Prepared(None, state, expected, (why,))
        head = run(["git", "rev-parse", "HEAD"], worktree).stdout.strip()
        if head != expected:
            why = f"worktree is at {head or 'nothing'}, expected {expected}"
            return Prepared(None, state, expected, (why,))
        sync = run(["uv", "sync", "--frozen", *python], worktree)
        if sync.returncode != 0:
            why = f"uv sync --frozen failed: {sync.stderr.strip()[-500:]}"
            return Prepared(None, state, expected, (why,))
        return Prepared(worktree, state, expected)

    return prepare


def make_verify(python: list[str]) -> Verify:
    def verify(worktree: Path, claim: str) -> tuple[str, int]:
        done = run(
            ["uv", "run", "--frozen", *python, "refute", "verify", claim, "--json"], worktree
        )
        return done.stdout, done.returncode

    return verify


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--python", help="interpreter for uv (default: uv's choice)")
    parser.add_argument("--out", type=Path, default=WORK / "tag-verify")
    parser.add_argument("--allow-missing-tags", action="store_true")
    parser.add_argument("--remove-worktrees", action="store_true")
    args = parser.parse_args()
    python = ["--python", args.python] if args.python else []
    checks = expected_checks()
    summary = run_checks(
        checks, args.out, make_prepare(python, args.allow_missing_tags), make_verify(python)
    )
    for row in summary["checks"]:
        state = "PASS" if row["pass"] else "FAIL"
        detail = "" if row["pass"] else ": " + "; ".join(row["problems"])
        print(f"{row['tag']} {row['claim']}: {state} (verify {row['status']}){detail}")
    print(f"joint: {summary['joint']} ({summary['passed']} of {summary['expected']})")
    if summary["tags_absent"]:
        print("checked at the commit, tag not created: " + ", ".join(summary["tags_absent"]))
    if args.remove_worktrees:
        for tag in dict.fromkeys(c.tag for c in checks):
            worktree = WORK / f"wt-{tag}"
            if worktree.is_dir() and inside_work(worktree):
                removed = run(["git", "worktree", "remove", "--force", str(worktree)], ROOT)
                print(
                    f"removed worktree {worktree.relative_to(ROOT).as_posix()}: "
                    f"exit {removed.returncode}"
                )
    return 0 if summary["joint"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
