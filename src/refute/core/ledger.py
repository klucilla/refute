"""The public case ledger (v0.4, issue #25 extended): an append-only JSON Lines file whose
events are chained by hash.

Each line is one event in canonical JSON (``refute-cjson-1``):

- ``schema`` (``refute-ledger-1``), ``seq`` (1, 2, ...), ``case_id``, ``type`` (one of
  ``EVENT_TYPES``), ``utc``, ``data`` (the event's content), ``corrects`` (the ``seq`` of the
  event it corrects, or null), ``hashes`` (of the dossier, seal, annexes and commit it refers to),
  ``prev_hash`` (the ``hash`` of the previous event; 64 zeros for the first) and ``hash`` (the
  SHA-256 of the canonical encoding of every other field).

Nothing is deleted or rewritten: a correction is a new event that points to the old one. The
chain shows continuity against a known anchor (a published commit); it does not prove that a
copy holds every later event.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

from refute.core.canonical import canonical_bytes, canonical_sha256

LEDGER_SCHEMA = "refute-ledger-1"
GENESIS = "0" * 64
EVENT_TYPES = (
    "opened",
    "locked",
    "ran",
    "promoted",
    "reviewed",
    "corrected",
    "concluded",
    "embargoed",
    "released",
)
FIELDS = ("schema", "seq", "case_id", "type", "utc", "data", "corrects", "hashes", "prev_hash")


class LedgerError(Exception):
    """An event cannot be appended (it would break the ledger's rules)."""


def event_hash(event: dict[str, Any]) -> str:
    return canonical_sha256({k: event[k] for k in FIELDS})


def read_events(path: Path) -> list[dict[str, Any]]:
    import json

    if not Path(path).is_file():
        return []
    lines = Path(path).read_bytes().decode("utf-8").splitlines()
    return [json.loads(line) for line in lines if line.strip()]


def make_event(
    previous: dict[str, Any] | None,
    case_id: str,
    event_type: str,
    utc: str,
    data: dict[str, Any],
    corrects: int | None = None,
    hashes: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """The next event after ``previous`` (None for the first)."""
    if event_type not in EVENT_TYPES:
        raise LedgerError(f"unknown event type {event_type!r}")
    if event_type == "corrected" and corrects is None:
        raise LedgerError("a correction names the event it corrects")
    event = {
        "schema": LEDGER_SCHEMA,
        "seq": 1 if previous is None else int(previous["seq"]) + 1,
        "case_id": case_id,
        "type": event_type,
        "utc": utc,
        "data": data,
        "corrects": corrects,
        "hashes": hashes or {},
        "prev_hash": GENESIS if previous is None else previous["hash"],
    }
    event["hash"] = event_hash(event)
    return event


def append_event(path: Path, event: dict[str, Any]) -> None:
    """Append one event; the file is only ever extended, never rewritten."""
    events = read_events(path)
    problems = verify_events([*events, event])
    if problems:
        raise LedgerError("; ".join(problems))
    with Path(path).open("ab") as handle:
        handle.write(canonical_bytes(event) + b"\n")


def verify_events(
    events: Sequence[dict[str, Any]],
    check: Callable[[dict[str, Any]], list[str]] | None = None,
) -> list[str]:
    """Every rule of the ledger; an empty list means the chain is intact. ``check`` adds the
    content rules of a pack for each event (for example the fields of a light entry)."""
    problems = []
    previous_hash = GENESIS
    seen: dict[int, dict[str, Any]] = {}
    for position, event in enumerate(events, start=1):
        where = f"event {position}"
        missing = [k for k in (*FIELDS, "hash") if k not in event]
        if missing:
            problems.append(f"{where}: missing field(s) {', '.join(missing)}")
            break
        if event["schema"] != LEDGER_SCHEMA:
            problems.append(f"{where}: schema {event['schema']!r}")
        if event["seq"] != position:
            problems.append(f"{where}: seq {event['seq']} (expected {position})")
        if event["type"] not in EVENT_TYPES:
            problems.append(f"{where}: unknown type {event['type']!r}")
        if event["prev_hash"] != previous_hash:
            problems.append(f"{where}: prev_hash does not match the previous event")
        if event_hash(event) != event["hash"]:
            problems.append(f"{where}: hash does not match its content")
        corrects = event["corrects"]
        if corrects is not None and (corrects not in seen or corrects >= event["seq"]):
            problems.append(f"{where}: corrects an event that does not precede it ({corrects})")
        if event["type"] == "corrected" and corrects is None:
            problems.append(f"{where}: a correction names no event")
        if check is not None:
            problems.extend(f"{where}: {p}" for p in check(event))
        seen[event["seq"]] = event
        previous_hash = event["hash"]
    return problems


def verify_file(
    path: Path, anchor_hash: str | None = None, check: Callable | None = None
) -> list[str]:
    """Verify a ledger file; with ``anchor_hash`` (the last hash at a published commit), the
    chain must pass through it."""
    events = read_events(path)
    problems = verify_events(events, check)
    if anchor_hash is not None and anchor_hash not in {e.get("hash") for e in events}:
        problems.append("the anchor hash is not in the chain")
    return problems
