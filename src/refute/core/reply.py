"""Reply draft to the authors of a paper (plan section 9.1, item 4).

Implements docs/validation/v0.3/wp2-acceptance.md, criteria W2.13, W2.13a and W2.14.
``refute reply-draft <dossier> --contact <file> --out <file>`` writes an email draft in
English. It never sends anything and opens no network connection; the maintainer
reviews the draft and sends it from their own account (CLAUDE.md, plan 9.1 item 5).

Inputs:

- **Scientific content: the sealed core only.** The dossier must be sealed and intact
  (``refute.core.seal``). The draft quotes:
  - ``SEAL.json``: the core hash;
  - ``verdict.json``: the claim verdict, with its meaning from ``VERDICT_MEANING``;
  - ``REPRODUCE.md``: the reproduction commands, as they are;
  - the locked ``claim.yaml``: ``key``, ``statement``, ``source.arxiv_id``,
    ``source.version``, ``source.location``, ``source.repository_url`` and
    ``source.repository_commit``.
- **Contact: the only outside input.** A JSON file under a ``private/`` folder (ignored
  by git) with ``arxiv_id``, ``version``, ``email`` (the corresponding-author address
  as printed in the paper), ``printed_at`` (its coordinates in the paper, never a
  transcription) and ``retrieved_utc``. No other source of personal data is searched.

Output: the draft, written under a ``private/`` folder and never into a dossier. The
command prints only the SHA-256 of the draft and of the address (plain SHA-256,
decided by the maintainer on 2026-10-15). Its messages, on success and on every
refusal, never contain the address, the contact file content or the draft text.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from refute.core.hashing import sha256_bytes
from refute.core.verdict import PaperVerdict

REPLY_PERIOD_DAYS = 30  # D-15: 30 days from sending
PRIVATE_DIR = "private"
CLAIM_FIELDS = (
    ("key",),
    ("statement",),
    ("source", "arxiv_id"),
    ("source", "version"),
    ("source", "location"),
    ("source", "repository_url"),
    ("source", "repository_commit"),
)
CONTACT_FIELDS = ("arxiv_id", "version", "email", "printed_at", "retrieved_utc")

# The meaning of each claim verdict, as in docs/verdicts.md (paper verdicts).
VERDICT_MEANING = {
    PaperVerdict.REPRODUCED: (
        "the claim was reproduced within the tolerance fixed before the run, and it "
        "held under every robustness check that was run"
    ),
    PaperVerdict.FRAGILE: (
        "the base result was reproduced, but at least one robustness check fixed before "
        "the run (for example other seeds or another data split) did not hold"
    ),
    PaperVerdict.NOT_REPRODUCED: (
        "the documented procedure ran to its end, and the result it produced is outside "
        "the tolerance fixed before the run"
    ),
    PaperVerdict.NOT_REPRODUCIBLE: (
        "the documented procedure could not be completed in our environment after the "
        "attempts fixed before the run (for example the build, the documented command, "
        "or an artifact that answered as absent)"
    ),
    PaperVerdict.INCONCLUSIVE: (
        "our run could not decide, for reasons on our side (for example an exhausted "
        "budget or an interrupted stage); this says nothing about the paper"
    ),
}

# W2.14: the template addresses the authors and otherwise speaks only about the claim.
FORBIDDEN_WORDS = (
    "misconduct",
    "error by the authors",
    "fraud",
    "fraudulent",
    "sloppy",
    "careless",
    "dishonest",
    "fabricated",
    "falsified",
    "incompetent",
    "negligent",
    "mistake by the authors",
    "the authors failed",
    "you failed",
)


class ReplyDraftError(Exception):
    """The draft was refused. The message never contains personal data."""


@dataclass(frozen=True)
class ReplyDraft:
    path: Path
    draft_sha256: str
    address_sha256: str


def _get(tree: Any, path: tuple[str, ...]) -> Any:
    node = tree
    for key in path:
        if not isinstance(node, dict) or key not in node:
            return None
        node = node[key]
    return node


def address_sha256(email: str) -> str:
    """Plain SHA-256 of the address as printed (surrounding blanks removed)."""
    return sha256_bytes(email.strip().encode("utf-8"))


def _read_contact(path: Path) -> dict[str, str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raise ReplyDraftError("the contact file cannot be read as JSON") from None
    if not isinstance(data, dict):
        raise ReplyDraftError("the contact file must hold a JSON object")
    contact = {}
    for name in CONTACT_FIELDS:
        value = data.get(name)
        if not isinstance(value, str | int) or not str(value).strip():
            raise ReplyDraftError(f"the contact file has no {name}")
        contact[name] = str(value).strip()
    email = contact["email"]
    if "@" not in email or any(ch.isspace() for ch in email):
        raise ReplyDraftError("the contact email is not an address")
    if "@" in contact["printed_at"]:
        raise ReplyDraftError("printed_at must hold coordinates in the paper, never the address")
    return contact


def _inside(path: Path, folder: Path) -> bool:
    try:
        path.resolve().relative_to(folder.resolve())
    except ValueError:
        return False
    return True


def render(
    claim: dict[str, str], verdict: PaperVerdict, core_sha256: str, reproduce: str, email: str
) -> str:
    """The draft text. Only the To line holds the address."""
    meaning = VERDICT_MEANING[verdict]
    return (
        f"To: {email}\n"
        f"Subject: Reproduction of a claim in arXiv:{claim['arxiv_id']}v{claim['version']}\n"
        "\n"
        "Dear authors,\n"
        "\n"
        "We are writing about one claim of your paper, which we tried to reproduce with "
        "Refute, an open-source tool that re-runs published results with a procedure fixed "
        "before the run.\n"
        "\n"
        f"Paper: arXiv:{claim['arxiv_id']}, version {claim['version']}\n"
        f"Claim ({claim['key']}): {claim['statement']}\n"
        f"Location in the paper: {claim['location']}\n"
        f"Code tested: {claim['repository_url']} at commit {claim['repository_commit']}\n"
        "\n"
        f"Verdict for this claim: {verdict.value}. It means that {meaning}. A verdict is "
        "about the claim as we ran it, never about the people who made it.\n"
        "\n"
        "The full evidence (the locked claim, the outputs, the logs and the verdict) is in "
        f"a sealed dossier whose core has the SHA-256 {core_sha256}. These commands "
        "reproduce it:\n"
        "\n"
        f"{reproduce.strip()}\n"
        "\n"
        f"We would be glad to hear from you within {REPLY_PERIOD_DAYS} days of this "
        "message, before anything about this result is published. If you reply, we offer "
        "to publish your reply next to the verdict, as you write it. If something in our "
        "run does not match your procedure, we would like to know.\n"
        "\n"
        "Kind regards,\n"
    )


def write_reply_draft(dossier: Path | str, contact_path: Path | str, out: Path | str) -> ReplyDraft:
    """Check the inputs, write the draft and return its hashes (W2.13, W2.13a)."""
    from refute.core.seal import check_sealed

    dossier, contact_path, out = Path(dossier), Path(contact_path), Path(out)
    sealed = check_sealed(dossier)
    if not sealed.ok:
        raise ReplyDraftError("the dossier must be sealed and intact (refute check-dossier)")
    try:
        seal_record = json.loads((dossier / "SEAL.json").read_text(encoding="utf-8"))
        verdict_data = json.loads((dossier / "verdict.json").read_text(encoding="utf-8"))
        claim_data = yaml.safe_load((dossier / "claim.yaml").read_text(encoding="utf-8"))
        reproduce = (dossier / "REPRODUCE.md").read_text(encoding="utf-8")
    except (OSError, ValueError, yaml.YAMLError) as exc:
        raise ReplyDraftError(
            f"a file of the sealed core cannot be read: {type(exc).__name__}"
        ) from None
    try:
        verdict = PaperVerdict(verdict_data.get("verdict"))
    except (ValueError, AttributeError):
        raise ReplyDraftError("verdict.json holds no paper claim verdict") from None
    claim = {}
    for path in CLAIM_FIELDS:
        value = _get(claim_data, path)
        if value is None or not str(value).strip():
            raise ReplyDraftError(f"the locked claim has no {'.'.join(path)}")
        claim[path[-1]] = str(value).strip()
    contact = _read_contact(contact_path)
    if (contact["arxiv_id"], contact["version"]) != (claim["arxiv_id"], claim["version"]):
        raise ReplyDraftError("the contact file belongs to another paper or version")
    if PRIVATE_DIR not in out.resolve().parent.parts or _inside(out, dossier):
        raise ReplyDraftError(
            f"the draft holds the address: write it under a {PRIVATE_DIR}/ folder, never "
            "into a dossier"
        )
    text = render(claim, verdict, seal_record["core_sha256"], reproduce, contact["email"])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8", newline="\n")
    return ReplyDraft(out, sha256_bytes(out.read_bytes()), address_sha256(contact["email"]))
