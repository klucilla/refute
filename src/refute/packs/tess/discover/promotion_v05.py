"""A promotion checked without the stage-1 dossiers (docs/plans/v0.5-acceptance.md, case 8.3;
issues #189 and #195, item 4).

The v0.4 ``verify_promotion`` recomputes the stage-1 entries from the stage-1 dossiers, which a
clone does not have. A v0.5 promotion is checked against the committed records alone: the
results commit's ``entries.json`` and the stage-1 seals file, each identified by its SHA-256
in the promotion record. A missing file is named; a tampered entry or seal fails. The v0.4
function is unchanged.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from typing import Any


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def verify_promotion_records(
    record: dict[str, Any],
    entries_bytes: bytes | None,
    seals_bytes: bytes | None,
    run_set: Sequence[str],
) -> list[str]:
    """Problems of a promotion record against the committed stage-1 records (empty when it
    agrees). ``record["stage1_records"]`` holds ``entries_sha256`` and ``seals_sha256``; the
    entries file holds a list of entries (each with ``target_key``); the seals file maps each
    funnel star's key to its core SHA-256 under ``core_sha256``."""
    problems: list[str] = []
    declared = record.get("stage1_records") or {}
    for name, data, key in (
        ("entries.json", entries_bytes, "entries_sha256"),
        ("seals.json", seals_bytes, "seals_sha256"),
    ):
        if data is None:
            problems.append(f"missing input: {name}")
        elif declared.get(key) != _sha(data):
            problems.append(f"{name}: its SHA-256 is not the one the promotion record declares")
    if problems:
        return problems
    entries = json.loads(entries_bytes.decode("utf-8"))
    seals = (json.loads(seals_bytes.decode("utf-8")) or {}).get("core_sha256") or {}
    if isinstance(entries, dict):
        entries = entries.get("entries") or []
    keys = [e.get("target_key") for e in entries]
    if keys != list(run_set):
        problems.append("the committed entries are not exactly the run set, in order")
    if sorted(seals) != sorted(run_set):
        problems.append("the seals are not exactly the run set")
    if list(record.get("entries") or []) != list(entries):
        problems.append("the record's entries differ from the committed entries")
    eligible = [e["target_key"] for e in entries if e.get("eligible")]
    if record.get("eligible") != eligible:
        problems.append("the eligible list does not follow from the committed entries")
    return problems
