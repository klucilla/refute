"""Claim inventories and the claim draw (WP5 W5.9, W5.10; plan section 5.2).

**Inventory** (format ``refute-ml-inventory-1``): every candidate claim of one paper, in
the paper's reading order, with its approved transcription, its type and, for a
comparison, its reference method and whether it is an eligible comparison. Its
SHA-256 is computed over the canonical JSON form (``refute.core.canonical``).

**Claim draw**: ``random.Random(int.from_bytes(sha256(claim_seed_bytes ||
arxiv_id_utf8), "big"))`` shuffles the drawable candidates (value claims and eligible
comparisons, in reading order) and the first K = 3 are drawn. When the inventory has an
eligible comparison and none of the 3 is one, the 3rd is replaced by the first eligible
comparison in the shuffled order. With no eligible comparison, up to 3 value claims are
drawn and the record says that no comparison was evaluated. With 3 drawable candidates
or fewer, all are taken. The drawn order is the claim order of the budget and report.
"""

from __future__ import annotations

import hashlib
import random
import re
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from refute.core.canonical import canonical_sha256
from refute.selection.publication import PublicationProof

FORMAT = "refute-ml-inventory-1"
K = 3
ARXIV_ID = re.compile(r"^\d{4}\.\d{4,5}$")
TRANSCRIPTION_FIELDS = ("value", "location", "metric", "split", "command")


class InventoryError(Exception):
    """The inventory or a draw request is not valid."""


def validate_inventory(inv: dict[str, Any]) -> None:
    """Raises InventoryError when the inventory does not follow ``refute-ml-inventory-1``."""
    if inv.get("format") != FORMAT:
        raise InventoryError(f"format must be {FORMAT}")
    paper = inv.get("paper") or {}
    if not ARXIV_ID.match(str(paper.get("arxiv_id", ""))):
        raise InventoryError("paper.arxiv_id must be a new-style arXiv ID without version")
    if not isinstance(paper.get("version"), int) or paper["version"] < 1:
        raise InventoryError("paper.version must be an integer of at least 1")
    candidates = inv.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        raise InventoryError("an inventory lists at least one candidate")
    ids = [c.get("candidate_id") for c in candidates]
    if any(not isinstance(i, str) or not i.strip() for i in ids) or len(set(ids)) != len(ids):
        raise InventoryError("candidate_id must be non-empty and unique")
    if [c.get("reading_order") for c in candidates] != list(range(1, len(candidates) + 1)):
        raise InventoryError("reading_order must be 1, 2, ... in list order")
    for c in candidates:
        if c.get("type") not in ("value", "comparison"):
            raise InventoryError(f"{c['candidate_id']}: type must be value or comparison")
        t = c.get("transcription") or {}
        if sorted(t) != sorted(TRANSCRIPTION_FIELDS) or any(
            not isinstance(t[f], str) or not t[f].strip() for f in TRANSCRIPTION_FIELDS
        ):
            raise InventoryError(
                f"{c['candidate_id']}: transcription needs exactly {TRANSCRIPTION_FIELDS} as text"
            )
        if c["type"] == "comparison":
            if not isinstance(c.get("reference"), str) or not c["reference"].strip():
                raise InventoryError(f"{c['candidate_id']}: a comparison names its reference")
            if not isinstance(c.get("eligible_comparison"), bool):
                raise InventoryError(
                    f"{c['candidate_id']}: eligible_comparison must be true or false"
                )
        elif c.get("reference") is not None or "eligible_comparison" in c:
            raise InventoryError(f"{c['candidate_id']}: a value claim has no reference")
    approval = inv.get("approval") or {}
    for key in ("approved_by", "approved_utc", "approved_commit"):
        if not isinstance(approval.get(key), str) or not approval[key].strip():
            raise InventoryError(f"approval.{key} is required")
    if not re.fullmatch(r"[0-9a-f]{40}", approval["approved_commit"]):
        raise InventoryError("approval.approved_commit must be 40 lowercase hex digits")


def inventory_sha256(inv: dict[str, Any]) -> str:
    validate_inventory(inv)
    return canonical_sha256(inv)


def has_eligible_comparison(inv: dict[str, Any]) -> bool:
    return any(c["type"] == "comparison" and c["eligible_comparison"] for c in inv["candidates"])


def draw_seed(claim_seed_bytes: bytes, arxiv_id: str) -> int:
    """``int.from_bytes(sha256(claim_seed_bytes || arxiv_id_utf8), "big")`` (plan line 297)."""
    if len(claim_seed_bytes) != 32:
        raise InventoryError("claim_seed_bytes are the 32 bytes of the drand randomness")
    if not ARXIV_ID.match(arxiv_id):
        raise InventoryError("the arXiv ID is new-style, without version")
    return int.from_bytes(
        hashlib.sha256(claim_seed_bytes + arxiv_id.encode("utf-8")).digest(), "big"
    )


@dataclass
class ClaimDraw:
    arxiv_id: str
    inventory_sha256: str
    shuffled: list[str]  # drawable candidate IDs in shuffled order
    drawn: list[str]  # the drawn claims, in claim order
    comparison_required: bool
    comparison_substituted: str | None  # the candidate the comparison replaced, if any
    replacements: list[dict[str, str]] = field(default_factory=list)

    @property
    def no_comparison_evaluated(self) -> bool:
        return not self.comparison_required


def draw_published_claims(
    inv: dict[str, Any], claim_seed_bytes: bytes, proof: PublicationProof
) -> ClaimDraw:
    """The claim draw of the WP7 flow: only after ``check_publication`` has given its
    proof, and only for an inventory whose SHA-256 is one the proof covers (#59, Codex
    review of #82). The inventory files are stored in canonical JSON, so the hash of the
    file in the commit is ``inventory_sha256``."""
    if not isinstance(proof, PublicationProof):
        raise InventoryError("the claim draw needs the publication proof of check_publication")
    digest = inventory_sha256(inv)
    if digest not in {d for _, d in proof.inventory_hashes}:
        raise InventoryError("this inventory is not one the publication proof covers")
    return draw_claims(inv, claim_seed_bytes)


def draw_claims(inv: dict[str, Any], claim_seed_bytes: bytes) -> ClaimDraw:
    """The claim draw of plan section 5.2, item 4. The WP7 flow calls it only through
    ``draw_published_claims``, after the publication proof."""
    digest = inventory_sha256(inv)
    arxiv_id = inv["paper"]["arxiv_id"]
    by_id = {c["candidate_id"]: c for c in inv["candidates"]}
    required = has_eligible_comparison(inv)
    drawable = [
        c["candidate_id"]
        for c in inv["candidates"]
        if c["type"] == "value" or (required and c["eligible_comparison"])
    ]
    order = list(drawable)
    random.Random(draw_seed(claim_seed_bytes, arxiv_id)).shuffle(order)
    drawn = order[:K]
    substituted = None
    if required and len(drawn) == K and not any(_is_comparison(by_id[i]) for i in drawn):
        first = next(i for i in order if _is_comparison(by_id[i]))
        substituted = drawn[K - 1]
        drawn = [*drawn[: K - 1], first]
    return ClaimDraw(arxiv_id, digest, order, drawn, required, substituted)


DRAW_FORMAT = "refute-ml-claim-draw-1"
_DRAW_KEYS = (
    "format",
    "arxiv_id",
    "inventory_sha256",
    "shuffled",
    "drawn",
    "comparison_required",
    "comparison_substituted",
    "replacements",
)


def draw_record(draw: ClaimDraw) -> dict[str, Any]:
    """The claim draw as a record (format ``refute-ml-claim-draw-1``), stored in canonical
    JSON as the ``claim-draw`` attachment of the paper's claim file."""
    return {
        "format": DRAW_FORMAT,
        "arxiv_id": draw.arxiv_id,
        "inventory_sha256": draw.inventory_sha256,
        "shuffled": list(draw.shuffled),
        "drawn": list(draw.drawn),
        "comparison_required": draw.comparison_required,
        "comparison_substituted": draw.comparison_substituted,
        "replacements": [dict(r) for r in draw.replacements],
    }


def read_draw_record(record: dict[str, Any]) -> ClaimDraw:
    """The inverse of ``draw_record``; raises InventoryError for a malformed record."""
    if not isinstance(record, dict) or sorted(record) != sorted(_DRAW_KEYS):
        raise InventoryError(f"a claim draw record has exactly the keys {_DRAW_KEYS}")
    if record["format"] != DRAW_FORMAT:
        raise InventoryError(f"format must be {DRAW_FORMAT}")
    if not ARXIV_ID.match(str(record["arxiv_id"])):
        raise InventoryError("arxiv_id must be a new-style arXiv ID without version")
    if not re.fullmatch(r"[0-9a-f]{64}", str(record["inventory_sha256"])):
        raise InventoryError("inventory_sha256 must be 64 lowercase hex digits")
    for key in ("shuffled", "drawn"):
        ids = record[key]
        if not isinstance(ids, list) or any(not isinstance(i, str) for i in ids):
            raise InventoryError(f"{key} must be a list of candidate IDs")
        if len(set(ids)) != len(ids):
            raise InventoryError(f"{key} repeats a candidate")
    if not record["drawn"] or not set(record["drawn"]) <= set(record["shuffled"]):
        raise InventoryError("drawn must be a non-empty subset of shuffled")
    if not isinstance(record["comparison_required"], bool):
        raise InventoryError("comparison_required must be true or false")
    if record["comparison_substituted"] is not None and not isinstance(
        record["comparison_substituted"], str
    ):
        raise InventoryError("comparison_substituted must be a candidate ID or null")
    replacements = record["replacements"]
    if not isinstance(replacements, list) or any(
        not isinstance(r, dict)
        or sorted(r) != ["invalidated", "reason", "replacement"]
        or any(not isinstance(v, str) for v in r.values())
        for r in replacements
    ):
        raise InventoryError("replacements are records {invalidated, reason, replacement}")
    return ClaimDraw(
        record["arxiv_id"],
        record["inventory_sha256"],
        list(record["shuffled"]),
        list(record["drawn"]),
        record["comparison_required"],
        record["comparison_substituted"],
        [dict(r) for r in replacements],
    )


class ReplacementExhaustedError(InventoryError):
    """No candidate can replace an invalidated claim; the maintainer decides."""

    def __init__(self, message: str, record: dict[str, str]):
        super().__init__(message)
        self.record = record


# Words that name a result, a cost or a verdict: never a reason to replace a claim.
_FORBIDDEN_WORDS = (
    "result",
    "cost",
    "budget",
    "verdict",
    "inconclusive",
    "fragile",
    "reproduc",
    "outcome",
    "runtime",
)


def _forbidden_reason(reason: str) -> bool:
    text = str(reason).lower()
    return any(word in text for word in _FORBIDDEN_WORDS)


def _is_comparison(candidate: dict[str, Any]) -> bool:
    return candidate["type"] == "comparison" and bool(candidate.get("eligible_comparison"))


def replace_claim(
    draw: ClaimDraw,
    inv: dict[str, Any],
    invalid_id: str,
    reason: str,
    allowed_reasons: Sequence[str],
) -> ClaimDraw:
    """Replaces one drawn claim invalidated for a reason of the protocol's closed list.

    The replacement is the next candidate in the shuffled order that was never drawn;
    when the invalidated claim is the only comparison and a comparison is required, it
    is the next eligible comparison. The original record is kept in ``replacements``.
    A candidate is never replaced because of a result, a cost or an INCONCLUSIVE
    verdict (plan section 5.2, item 5): a reason or a closed list that names one of
    those is refused, whatever the protocol says. When no candidate can replace it,
    ``ReplacementExhaustedError`` stops the draw for the maintainer: the claim set is
    never reduced, and a required comparison is never dropped, silently.
    """
    forbidden = [r for r in [reason, *allowed_reasons] if _forbidden_reason(r)]
    if forbidden:
        raise InventoryError(
            f"a result, cost or verdict is never a replacement reason: {forbidden}"
        )
    if reason not in allowed_reasons:
        raise InventoryError(f"reason not in the protocol's closed list: {reason!r}")
    if invalid_id not in draw.drawn:
        raise InventoryError(f"{invalid_id} is not a drawn claim")
    if inventory_sha256(inv) != draw.inventory_sha256:
        raise InventoryError("the inventory differs from the one the draw used")
    by_id = {c["candidate_id"]: c for c in inv["candidates"]}
    used = set(draw.drawn) | {r["invalidated"] for r in draw.replacements}
    others = [i for i in draw.drawn if i != invalid_id]
    keep_comparison = (
        draw.comparison_required
        and _is_comparison(by_id[invalid_id])
        and not any(_is_comparison(by_id[i]) for i in others)
    )
    candidates = [i for i in draw.shuffled if i not in used]
    if keep_comparison:
        candidates = [i for i in candidates if _is_comparison(by_id[i])]
    record = {"invalidated": invalid_id, "reason": reason, "replacement": ""}
    if not candidates:
        what = "eligible comparison" if keep_comparison else "candidate"
        raise ReplacementExhaustedError(f"no {what} left to replace {invalid_id}", record)
    new_drawn = list(draw.drawn)
    new_drawn[new_drawn.index(invalid_id)] = candidates[0]
    record["replacement"] = candidates[0]
    return ClaimDraw(
        draw.arxiv_id,
        draw.inventory_sha256,
        draw.shuffled,
        new_drawn,
        draw.comparison_required,
        draw.comparison_substituted,
        [*draw.replacements, record],
    )
