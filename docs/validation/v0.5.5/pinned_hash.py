"""v0.5.5: locate the earlier stages' records under the code hash they were written with (#218).

The earlier stages' readers (``b1_b14._records``, ``b1_d2d4_rest.complete_records``, called by
``i1_diagnose.schedule`` and ``step6_i2.schedule``) recompute their parts' fingerprints from
``src/``'s code hash (``refute.core.codehash.compute_code_hash``), which covers ``uv.lock``. The
dependency update of 2026-11-20 (commit ``5e5f40a``: soupsieve 4.1, tornado 6.6.1; #59) changed
``uv.lock`` and so the code hash, and those readers would no longer find their records.

**The pinned hash authenticates historical record lookup. The replay runs in the current
environment; matching recorded outputs establishes agreement only for the quantities and
tolerances checked** (Codex, r0r1 round 2). ``pinned()`` is used only around those lookups (T2a-E's
schedule), never around the replay or the identification of the current run.

``pinned_code_hash()`` returns the code hash of commit ``8653911`` (the last before the update).
It refuses unless, at the moment it is used, the files the code hash covers are exactly that
commit's, file for file (the same paths, each with the same normalized SHA-256, ignored files
included), except ``uv.lock``, which must be either that commit's or the approved one of
``5e5f40a``. Any other difference is refused.
"""

from __future__ import annotations

import contextlib
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PINNED_COMMIT = "8653911011c59f9eccba9158b5bb2f57eaa67293"
APPROVED_LOCK_COMMIT = "5e5f40a7864c84d0ecf4eb2ef3ce8242c1357503"  # #59, the maintainer's 4a


def _git(*args: str) -> bytes:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, check=True).stdout


def _normalized_sha(data: bytes) -> str:
    from refute.core.hashing import is_text, normalize_newlines, sha256_bytes

    return sha256_bytes(normalize_newlines(data) if is_text(data) else data)


def check_manifest(
    current: dict[str, str], expected: dict[str, str], approved_locks: set[str]
) -> str | None:
    """Pure: the reason to refuse, or None. ``current`` and ``expected`` map each covered path
    to its normalized SHA-256; ``uv.lock`` may differ from ``expected`` only to one of
    ``approved_locks``."""
    cur = {k: v for k, v in current.items() if k != "uv.lock"}
    exp = {k: v for k, v in expected.items() if k != "uv.lock"}
    if set(cur) != set(exp):
        extra, missing = sorted(set(cur) - set(exp)), sorted(set(exp) - set(cur))
        return f"the covered files differ (added {extra[:3]}, missing {missing[:3]})"
    changed = sorted(k for k in cur if cur[k] != exp[k])
    if changed:
        return f"covered files changed since the pinned commit: {changed[:3]}"
    if current.get("uv.lock") not in approved_locks:
        return "uv.lock is neither the pinned commit's nor the approved update's"
    return None


def ls_tree_paths(out: bytes) -> list[str]:
    """``git ls-tree -z --name-only`` output: NUL-separated and unquoted, so a path with a space
    (or any byte git would quote) stays one path (the maintainer's decision of 2026-11-20,
    night, 4c)."""
    return [p.decode("utf-8") for p in out.split(b"\0") if p]


def pinned_code_hash():
    """The code hash of ``PINNED_COMMIT``, after the manifest check of the module's docstring."""
    from refute.core import codehash
    from refute.core.hashing import sha256_bytes

    current = dict(codehash.compute_code_hash(ROOT).files)
    paths = ls_tree_paths(_git("ls-tree", "-r", "-z", "--name-only", PINNED_COMMIT, "--", "src"))
    expected = {}
    for p in paths:
        rel = Path(p)
        if codehash._is_excluded(rel):
            continue
        expected[rel.as_posix()] = _normalized_sha(_git("show", f"{PINNED_COMMIT}:{p}"))
    for name in ("pyproject.toml", "uv.lock"):
        expected[name] = _normalized_sha(_git("show", f"{PINNED_COMMIT}:{name}"))
    approved = {
        expected["uv.lock"],
        _normalized_sha(_git("show", f"{APPROVED_LOCK_COMMIT}:uv.lock")),
    }
    why = check_manifest(current, expected, approved)
    if why:
        raise SystemExit(f"the pinned code hash is refused: {why}")
    entries = tuple(sorted(expected.items()))
    text = "".join(f"{digest}  {rel}\n" for rel, digest in entries)
    return codehash.CodeHash(codehash.CODE_ALGORITHM, sha256_bytes(text.encode("utf-8")), entries)


@contextlib.contextmanager
def pinned(value=None):
    """``compute_code_hash`` returns the pinned hash inside the block (the readers import it at
    call time from the module), and is restored on exit, also on an error. Serial use within one
    process only. ``value`` is for tests."""
    from refute.core import codehash

    value = pinned_code_hash() if value is None else value
    original = codehash.compute_code_hash

    def compute_code_hash(root=None):
        return value

    codehash.compute_code_hash = compute_code_hash
    try:
        yield value
    finally:
        codehash.compute_code_hash = original
