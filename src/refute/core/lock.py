"""Pre-registration lock: ``refute lock`` and ``refute verify``.

A lock is a sidecar JSON file next to the claim (``<claim stem>.lock.json``). It
records the SHA-256 of the resolved, canonicalized claim, of every attachment, of
the source tree (code hash) and the git commit. Every lock and re-lock is also
appended to ``LOCK_HISTORY.md`` in the claim's directory.

``verify`` exit codes: 0 PASS, 1 FAIL, 2 TAMPERED. See ``docs/lock-format.md``.
"""

from __future__ import annotations

import enum
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import refute
from refute.core.canonical import CANONICALIZATION
from refute.core.claim import ClaimError, LoadedClaim, load_claim
from refute.core.codehash import (
    CodeHashError,
    compute_code_hash,
    diff_code_files,
    git_state,
    relative_to_toplevel,
)
from refute.core.hashing import sha256_text_normalized
from refute.core.io import append_text, write_json
from refute.core.lock_compat import LIMIT as PROJECTION_LIMIT
from refute.core.lock_compat import project

LOCK_VERSION = 1
HISTORY_FILENAME = "LOCK_HISTORY.md"
HISTORY_HEADER = """# Lock history

Append-only record of every `refute lock` performed on the claims in this
directory, including forced re-locks. Entries are written by `refute lock`.
Never edit or delete an entry: `refute verify` checks that a claim's lock is the
latest entry recorded here, and the git history of this file is the evidence of
when each lock happened.
"""


class VerifyStatus(enum.StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    TAMPERED = "TAMPERED"


EXIT_CODES = {VerifyStatus.PASS: 0, VerifyStatus.FAIL: 1, VerifyStatus.TAMPERED: 2}


class LockError(Exception):
    """A lock could not be created (refused or invalid input)."""


def lock_path_for(claim_path: Path | str) -> Path:
    path = Path(claim_path)
    return path.with_name(f"{path.stem}.lock.json")


def history_path_for(claim_path: Path | str) -> Path:
    return Path(claim_path).parent / HISTORY_FILENAME


def utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def hash_attachments(loaded: LoadedClaim) -> list[dict[str, Any]]:
    records = []
    for attachment in loaded.claim.attachments:
        path = loaded.attachment_path(attachment)
        if not path.is_file():
            raise LockError(f"attachment not found: {attachment.path}")
        digest = sha256_text_normalized(path)
        if attachment.sha256 is not None and attachment.sha256.lower() != digest:
            raise LockError(
                f"attachment {attachment.path} has sha256 {digest}, "
                f"but the claim expects {attachment.sha256}"
            )
        records.append({"path": attachment.path, "role": attachment.role, "sha256": digest})
    return records


def read_lock(path: Path | str) -> dict[str, Any]:
    lock_file = Path(path)
    try:
        data = json.loads(lock_file.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise LockError(f"cannot read lock file {lock_file}: {exc}") from exc
    if not isinstance(data, dict) or data.get("lock_version") != LOCK_VERSION:
        raise LockError(f"unsupported lock file format in {lock_file}")
    for key in ("claim_sha256", "attachments", "code", "locked_at_utc", "canonicalization"):
        if key not in data:
            raise LockError(f"lock file {lock_file} is missing '{key}'")
    if data["canonicalization"] != CANONICALIZATION:
        raise LockError(f"unsupported canonicalization '{data['canonicalization']}'")
    return data


def _verify_structure_problems(lock: dict[str, Any]) -> list[str]:
    """The fields ``verify`` reads directly that a lock file lacks (issue #65, Codex
    review): such a lock is FAIL with the field named, never a KeyError. Kept out of
    :func:`read_lock`, so ``create_lock`` reads an existing lock as before."""
    problems = []
    if not isinstance(lock.get("claim_path"), str):
        problems.append("the lock file has no string 'claim_path'")
    code = lock.get("code")
    if not isinstance(code, dict) or not isinstance(code.get("sha256"), str):
        problems.append("the lock file has no string 'code.sha256'")
    elif "files" in code and not (
        isinstance(code["files"], list)
        and all(
            isinstance(f, dict)
            and isinstance(f.get("path"), str)
            and isinstance(f.get("sha256"), str)
            for f in code["files"]
        )
    ):
        # an absent list stays allowed (read as no files, as before)
        problems.append(
            "the lock file's 'code.files' is not a list of objects with a string 'path' and "
            "'sha256'"
        )
    records = lock.get("attachments")
    if not isinstance(records, list) or not all(
        isinstance(a, dict) and isinstance(a.get("path"), str) and isinstance(a.get("sha256"), str)
        for a in records
    ):
        problems.append(
            "the lock file's 'attachments' is not a list of objects with a string 'path' "
            "and 'sha256'"
        )
    return problems


_ENTRY_RE = re.compile(r"^## (?P<when>\S+) \| (?P<claim>.+)$")
_FIELD_RE = re.compile(r"^- (?P<key>[a-z0-9_]+): (?P<value>.*)$")
# In a literal read, the names of the fields an entry writes more than once (a bullet that
# repeats the heading's locked_at_utc or claim included), comma-joined. The key holds a
# space, so it never matches a field name.
REPEATED_FIELDS = "repeated fields"


def read_history(path: Path | str, *, literal: bool = False) -> list[dict[str, str]]:
    """The entries of a LOCK_HISTORY.md file, in order.

    By default values are stripped of surrounding whitespace and a repeated field keeps
    its last value. With ``literal=True`` (what ``verify`` uses, issue #65) values are
    kept exactly as written, and every field written twice in an entry is listed under
    :data:`REPEATED_FIELDS` instead of being silently replaced.
    """
    history = Path(path)
    if not history.is_file():
        return []
    entries: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    for line in history.read_text(encoding="utf-8").splitlines():
        header = _ENTRY_RE.match(line)
        if header:
            claim = header["claim"] if literal else header["claim"].strip()
            current = {"locked_at_utc": header["when"], "claim": claim}
            entries.append(current)
            continue
        item = _FIELD_RE.match(line)
        if item and current is not None:
            key, value = item["key"], item["value"]
            if literal and key in current:
                repeated = [k for k in current.get(REPEATED_FIELDS, "").split(",") if k]
                current[REPEATED_FIELDS] = ",".join([*repeated, key])
                continue
            current[key] = value if literal else value.strip()
    return entries


def _single_line(text: str) -> str:
    return " ".join(text.split())


# The fields a LOCK_HISTORY.md entry shares with its lock file (issue #65), in the order
# the entry writes them. ``action``, ``previous_claim_sha256`` and ``reason`` have no
# counterpart in the lock file; ``claim_path`` selects the entries and is not compared.
HISTORY_SHARED_FIELDS = (
    "locked_at_utc",
    "claim_id",
    "claim_sha256",
    "attachments",
    "code_sha256",
    "git_commit",
    "git_dirty",
    "refute_version",
)


class _FieldError(Exception):
    """A shared field of a lock file is missing or has a type its rule does not accept."""


def _string_field(lock: dict[str, Any], key: str) -> str:
    if key not in lock:
        raise _FieldError(f"the lock file has no '{key}'")
    value = lock[key]
    if not isinstance(value, str):
        raise _FieldError(f"'{key}' in the lock file is a {type(value).__name__}, not a string")
    return value


def _history_value(lock: dict[str, Any], key: str) -> str:
    """The text the history entry holds for one shared field, by that field's rule.

    The rules (docs/lock-format.md, "What verify compares"): no normalization of case,
    whitespace, Unicode or paths; the lock's value is turned into text exactly as
    ``refute lock`` writes it, and the two texts must be equal.

    - ``locked_at_utc``, ``claim_id``, ``claim_sha256``, ``refute_version``: a string,
      written as is.
    - ``code_sha256``: ``code.sha256`` of the lock, a string, written as is.
    - ``attachments``: a list of objects with string ``path`` and ``sha256``, written as
      ``path=sha256`` joined by ``", "`` in the lock's order, or ``none`` when empty.
    - ``git_commit``: a string, or null; null or an empty string is written ``none``.
    - ``git_dirty``: true, false or null, written ``true``, ``false`` or ``none``.

    Raises :class:`_FieldError` when the lock has no such field or a value of
    another type.
    """
    if key == "code_sha256":
        code = lock.get("code")
        if not isinstance(code, dict) or "sha256" not in code:
            raise _FieldError("the lock file has no 'code.sha256'")
        if not isinstance(code["sha256"], str):
            raise _FieldError("'code.sha256' in the lock file is not a string")
        return code["sha256"]
    if key == "attachments":
        if key not in lock:
            raise _FieldError("the lock file has no 'attachments'")
        records = lock[key]
        if not isinstance(records, list) or not all(
            isinstance(a, dict)
            and isinstance(a.get("path"), str)
            and isinstance(a.get("sha256"), str)
            for a in records
        ):
            raise _FieldError(
                "'attachments' in the lock file is not a list of objects with a string "
                "'path' and 'sha256'"
            )
        return ", ".join(f"{a['path']}={a['sha256']}" for a in records) or "none"
    if key == "git_commit":
        if key not in lock:
            raise _FieldError("the lock file has no 'git_commit'")
        value = lock[key]
        if value is not None and not isinstance(value, str):
            raise _FieldError(
                f"'git_commit' in the lock file is a {type(value).__name__}, not a string or null"
            )
        return value or "none"
    if key == "git_dirty":
        if key not in lock:
            raise _FieldError("the lock file has no 'git_dirty'")
        value = lock[key]
        if value is not None and not isinstance(value, bool):
            raise _FieldError(
                f"'git_dirty' in the lock file is a {type(value).__name__}, not true, false or null"
            )
        return "none" if value is None else str(value).lower()
    return _string_field(lock, key)


def compare_history_entry(lock: dict[str, Any], entry: dict[str, str]) -> list[str]:
    """Every difference between a lock file and its history entry, one line per field.

    Each field of :data:`HISTORY_SHARED_FIELDS` is compared by its rule
    (:func:`_history_value`). A field missing on either side is a difference, never
    skipped: missing in the lock, in the entry, or in both gives one line per missing
    side. A field the entry writes twice is a difference (a literal read records it,
    :func:`read_history`). The attachments text is ambiguous when a path holds ``", "``,
    ``"="`` or a line break (two different lists could then give the same text), so such a
    lock is a difference too; ``refute lock`` still writes it as before. An empty list
    means the entry records exactly this lock.
    """
    problems: list[str] = []
    repeated = {k for k in entry.get(REPEATED_FIELDS, "").split(",") if k}
    # any field written twice, shared or not (claim, reason, action included)
    for key in sorted(repeated - set(HISTORY_SHARED_FIELDS)):
        problems.append(f"the history entry writes '{key}' more than once")
    for key in HISTORY_SHARED_FIELDS:
        expected: str | None
        try:
            expected = _history_value(lock, key)
        except _FieldError as exc:
            problems.append(str(exc))
            expected = None
        if key == "attachments" and expected is not None:
            ambiguous = [
                a["path"]
                for a in lock["attachments"]
                if ", " in a["path"] or "=" in a["path"] or "\n" in a["path"] or "\r" in a["path"]
            ]
            if ambiguous:
                problems.append(
                    "attachments: a path in the lock file holds ', ', '=' or a line break, so "
                    f"its history text is ambiguous: {ambiguous!r}"
                )
                expected = None
        if key not in entry:
            problems.append(f"the history entry has no '{key}'")
            continue
        if key in repeated:
            problems.append(f"the history entry writes '{key}' more than once")
            continue
        if expected is not None and entry[key] != expected:
            problems.append(
                f"{key}: the lock file has {expected!r}, the history entry {entry[key]!r}"
            )
    return problems


def _history_entry(lock: dict[str, Any], *, action: str, previous: str | None, reason: str) -> str:
    value = {key: _history_value(lock, key) for key in HISTORY_SHARED_FIELDS}
    lines = [
        "",
        f"## {value['locked_at_utc']} | {lock['claim_path']}",
        "",
        f"- action: {action}",
        f"- claim_id: {value['claim_id']}",
        f"- claim_sha256: {value['claim_sha256']}",
        f"- previous_claim_sha256: {previous or 'none'}",
        f"- attachments: {value['attachments']}",
        f"- code_sha256: {value['code_sha256']}",
        f"- git_commit: {value['git_commit']}",
        f"- git_dirty: {value['git_dirty']}",
        f"- refute_version: {value['refute_version']}",
        f"- reason: {_single_line(reason)}",
        "",
    ]
    return "\n".join(lines)


def create_lock(
    claim_path: Path | str,
    *,
    force: bool = False,
    reason: str | None = None,
    code_root: Path | None = None,
    now: str | None = None,
) -> dict[str, Any]:
    """Lock a claim. Returns the lock record. Raises :class:`LockError` when refused."""
    claim_file = Path(claim_path).resolve()
    try:
        loaded = load_claim(claim_file)
    except ClaimError as exc:
        raise LockError(str(exc)) from exc

    lock_file = lock_path_for(claim_file)
    history_file = history_path_for(claim_file)
    previous: dict[str, Any] | None = None
    if lock_file.exists():
        try:
            previous = read_lock(lock_file)
        except LockError:
            previous = None
        if not force:
            existing = previous["claim_sha256"] if previous else "unreadable"
            raise LockError(
                f"{claim_file.name} is already locked (claim_sha256={existing}). "
                "Re-locking requires --force with a --reason, and is recorded in "
                f"{HISTORY_FILENAME}."
            )
    if force and not (reason and reason.strip()):
        raise LockError("--force requires a non-empty --reason")

    # Git state is computed BEFORE anything is written. Only the two files that the
    # lock itself writes are ignored when deciding whether the tree is clean.
    state = git_state(claim_file.parent)
    ignored = {
        relative_to_toplevel(state, lock_file),
        relative_to_toplevel(state, history_file),
    }
    dirty_paths = [p for p in state.dirty_paths if p not in ignored]
    if loaded.claim.kind == "calibration":
        if not state.is_repo or state.commit is None:
            raise LockError(
                "calibration claims can only be locked inside a git repository with at "
                "least one commit; commit the code, protocol and targets first"
            )
        if dirty_paths:
            shown = ", ".join(dirty_paths[:20])
            more = f" (+{len(dirty_paths) - 20} more)" if len(dirty_paths) > 20 else ""
            raise LockError(
                "refusing to lock a calibration claim: the working tree is dirty. "
                f"Commit or remove these paths first: {shown}{more}"
            )

    try:
        attachments = hash_attachments(loaded)
        code = compute_code_hash(code_root)
    except CodeHashError as exc:
        raise LockError(str(exc)) from exc

    lock: dict[str, Any] = {
        "lock_version": LOCK_VERSION,
        "canonicalization": CANONICALIZATION,
        "claim_path": claim_file.name,
        "claim_id": loaded.claim.id,
        "claim_kind": loaded.claim.kind,
        "claim_sha256": loaded.sha256(),
        "attachments": attachments,
        "code": code.to_dict(),
        "git_commit": state.commit,
        "git_dirty": (bool(dirty_paths) if state.is_repo else None),
        "git_dirty_paths": dirty_paths,
        "claim_path_in_repo": relative_to_toplevel(state, claim_file),
        "locked_at_utc": now or utc_now(),
        "refute_version": refute.__version__,
        "python_version": sys.version.split()[0],
    }
    if loaded.claim.kind != "calibration" and dirty_paths:
        lock["warning"] = "locked from a dirty working tree"

    if not history_file.exists():
        append_text(history_file, HISTORY_HEADER)
    action = "relock" if previous is not None or lock_file.exists() else "lock"
    entry_reason = reason.strip() if reason and reason.strip() else "initial lock"
    previous_sha = previous["claim_sha256"] if previous else None
    write_json(lock_file, lock)
    append_text(
        history_file,
        _history_entry(lock, action=action, previous=previous_sha, reason=entry_reason),
    )
    return lock


@dataclass
class VerifyResult:
    status: VerifyStatus
    claim_path: str
    messages: list[str] = field(default_factory=list)
    tampered: list[str] = field(default_factory=list)
    changed_files: list[str] = field(default_factory=list)
    lock: dict[str, Any] | None = None
    current_claim_sha256: str | None = None
    current_code_sha256: str | None = None
    claim_projection: str | None = None
    projected_claim_sha256: str | None = None
    verified_at_utc: str = field(default_factory=utc_now)

    @property
    def exit_code(self) -> int:
        return EXIT_CODES[self.status]

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "exit_code": self.exit_code,
            "claim_path": self.claim_path,
            "messages": self.messages,
            "tampered_components": self.tampered,
            "changed_files": self.changed_files,
            "locked_claim_sha256": self.lock.get("claim_sha256") if self.lock else None,
            "locked_code_sha256": self.lock.get("code", {}).get("sha256") if self.lock else None,
            "current_claim_sha256": self.current_claim_sha256,
            "current_code_sha256": self.current_code_sha256,
            "claim_projection": self.claim_projection,
            "projected_claim_sha256": self.projected_claim_sha256,
            "verified_at_utc": self.verified_at_utc,
        }


def verify_claim(claim_path: Path | str, *, code_root: Path | None = None) -> VerifyResult:
    """Recompute every hash covered by the lock and compare."""
    claim_file = Path(claim_path).resolve()
    result = VerifyResult(status=VerifyStatus.PASS, claim_path=claim_file.name)
    failures: list[str] = []

    lock_file = lock_path_for(claim_file)
    if not lock_file.is_file():
        result.status = VerifyStatus.FAIL
        result.messages.append(f"no lock file: {lock_file.name} (run `refute lock` first)")
        return result
    try:
        lock = read_lock(lock_file)
    except LockError as exc:
        result.status = VerifyStatus.FAIL
        result.messages.append(str(exc))
        return result
    structure = _verify_structure_problems(lock)
    if structure:
        result.status = VerifyStatus.FAIL
        result.messages.extend(f"{lock_file.name}: {p}" for p in structure)
        return result
    result.lock = lock

    try:
        loaded = load_claim(claim_file)
    except ClaimError as exc:
        result.status = VerifyStatus.FAIL
        result.messages.append(str(exc))
        return result

    current_claim = loaded.sha256()
    result.current_claim_sha256 = current_claim
    if current_claim != lock["claim_sha256"]:
        # Historical locks only: remove the exact fields added since the lock
        # (refute.core.lock_compat); every safeguard must hold, or the claim is TAMPERED.
        projection = project(loaded.canonical(), loaded.raw, lock)
        if projection.applied and projection.sha256 == lock["claim_sha256"]:
            result.claim_projection = projection.entry
            result.projected_claim_sha256 = projection.sha256
            result.messages.append(
                f"claim matches its lock by historical projection {projection.entry}: "
                f"locked {lock['claim_sha256']}, full resolved hash now {current_claim}; "
                f"{PROJECTION_LIMIT}"
            )
        else:
            result.tampered.append("claim")
            why = (
                f"; historical projection {projection.entry} not applied: {projection.reason}"
                if projection.entry and not projection.applied
                else (
                    f"; historical projection {projection.entry} gives {projection.sha256}"
                    if projection.entry
                    else ""
                )
            )
            result.messages.append(
                f"claim hash mismatch: locked {lock['claim_sha256']}, now {current_claim}{why}"
            )

    for record in lock["attachments"]:
        path = claim_file.parent / record["path"]
        if not path.is_file():
            failures.append(f"attachment missing: {record['path']}")
            continue
        digest = sha256_text_normalized(path)
        if digest != record["sha256"]:
            result.tampered.append(f"attachment:{record['path']}")
            result.messages.append(
                f"attachment {record['path']} hash mismatch: locked {record['sha256']}, "
                f"now {digest}"
            )

    try:
        code = compute_code_hash(code_root)
    except CodeHashError as exc:
        failures.append(str(exc))
        code = None
    if code is not None:
        result.current_code_sha256 = code.sha256
        if code.sha256 != lock["code"]["sha256"]:
            result.tampered.append("code")
            result.changed_files = diff_code_files(lock["code"].get("files", []), code)
            result.messages.append(
                f"code hash mismatch: locked {lock['code']['sha256']}, now {code.sha256}; "
                + ("; ".join(result.changed_files) or "file list unchanged")
            )

    try:
        entries = read_history(history_path_for(claim_file), literal=True)
        readable = True
    except (OSError, UnicodeDecodeError) as exc:
        # an unreadable history is FAIL with the reason, never an exception
        failures.append(f"cannot read {HISTORY_FILENAME}: {exc}")
        entries, readable = [], False
    history = [e for e in entries if e["claim"] == lock["claim_path"]]
    if readable and not history:
        failures.append(f"lock is not recorded in {HISTORY_FILENAME}")
    elif history:
        # every field the entry shares with the lock, each by its rule (issue #65)
        differences = compare_history_entry(lock, history[-1])
        if differences:
            failures.append(
                f"the lock file does not match the latest {HISTORY_FILENAME} entry for "
                f"{lock['claim_path']}: " + "; ".join(differences)
            )

    result.messages.extend(failures)
    if result.tampered:
        result.status = VerifyStatus.TAMPERED
    elif failures:
        result.status = VerifyStatus.FAIL
    else:
        result.messages.append(
            f"claim {lock['claim_sha256']}, code {lock['code']['sha256']}, "
            f"{len(lock['attachments'])} attachment(s): all hashes match the lock"
        )
    return result
