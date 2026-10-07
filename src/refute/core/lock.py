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


_ENTRY_RE = re.compile(r"^## (?P<when>\S+) \| (?P<claim>.+)$")
_FIELD_RE = re.compile(r"^- (?P<key>[a-z0-9_]+): (?P<value>.*)$")


def read_history(path: Path | str) -> list[dict[str, str]]:
    history = Path(path)
    if not history.is_file():
        return []
    entries: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    for line in history.read_text(encoding="utf-8").splitlines():
        header = _ENTRY_RE.match(line)
        if header:
            current = {"locked_at_utc": header["when"], "claim": header["claim"].strip()}
            entries.append(current)
            continue
        item = _FIELD_RE.match(line)
        if item and current is not None:
            current[item["key"]] = item["value"].strip()
    return entries


def _single_line(text: str) -> str:
    return " ".join(text.split())


def _history_entry(lock: dict[str, Any], *, action: str, previous: str | None, reason: str) -> str:
    attachments = ", ".join(f"{a['path']}={a['sha256']}" for a in lock["attachments"]) or "none"
    lines = [
        "",
        f"## {lock['locked_at_utc']} | {lock['claim_path']}",
        "",
        f"- action: {action}",
        f"- claim_id: {lock['claim_id']}",
        f"- claim_sha256: {lock['claim_sha256']}",
        f"- previous_claim_sha256: {previous or 'none'}",
        f"- attachments: {attachments}",
        f"- code_sha256: {lock['code']['sha256']}",
        f"- git_commit: {lock['git_commit'] or 'none'}",
        f"- git_dirty: {str(lock['git_dirty']).lower()}",
        f"- refute_version: {lock['refute_version']}",
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
        result.tampered.append("claim")
        result.messages.append(
            f"claim hash mismatch: locked {lock['claim_sha256']}, now {current_claim}"
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

    history = [
        e for e in read_history(history_path_for(claim_file)) if e["claim"] == lock["claim_path"]
    ]
    if not history:
        failures.append(f"lock is not recorded in {HISTORY_FILENAME}")
    else:
        latest = history[-1]
        if (
            latest.get("claim_sha256") != lock["claim_sha256"]
            or latest.get("code_sha256") != lock["code"]["sha256"]
            or latest.get("locked_at_utc") != lock["locked_at_utc"]
        ):
            failures.append(
                f"the lock file does not match the latest {HISTORY_FILENAME} entry for "
                f"{lock['claim_path']}"
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
