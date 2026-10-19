"""The time of the maintainer's approval of the transcriptions of the main sample, as the claim
files state it (the maintainer's decision 2b of 2026-10-19).

The frozen inventories carry ``approval.approved_utc = 2026-10-18T17:05:00Z``: the agent
derived that value from the local time stated in the maintainer's message. The approval
comment of issue #158 was posted at 2026-10-18T16:52:05Z (its ``created_at``, read with the
GitHub API on 2026-10-19), and a correction comment, posted at 2026-10-18T16:54:23Z, records
the difference. The claim schema does not require a claim's transcription approval time to
equal its inventory's, so the claim files carry the comment's time and cite both comments
in their definitions; the frozen inventories are never edited.
"""

from __future__ import annotations

APPROVAL_RECORD = "https://github.com/klucilla/refute/issues/158#issuecomment-6252536898"
CORRECTION_RECORD = "https://github.com/klucilla/refute/issues/158#issuecomment-6252562691"
INVENTORY_UTC = "2026-10-18T17:05:00Z"
COMMENT_UTC = "2026-10-18T16:52:05Z"
DEFINITION = (
    "approvals.transcription.approved_utc is 2026-10-18T16:52:05Z, the time of the "
    f"maintainer's approval comment ({APPROVAL_RECORD}). The frozen inventory attached carries "
    "2026-10-18T17:05:00Z, a value derived from the local time stated in the maintainer's "
    f"message; the correction is recorded in {CORRECTION_RECORD}, and the inventory is not "
    "edited (the maintainer's decision of 2026-10-19)."
)


def approved_utc(inventory_approval: dict) -> str:
    """The claim's transcription approval time for an inventory approved by that comment."""
    if (
        inventory_approval.get("approved_utc") != INVENTORY_UTC
        or inventory_approval.get("approval_record") != APPROVAL_RECORD
    ):
        raise SystemExit("the inventory's approval is not the one this correction is about")
    return COMMENT_UTC
