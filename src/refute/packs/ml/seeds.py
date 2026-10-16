"""Seeds of an ML paper (WP3 design, sections 1.0.2 and 1.0.4).

**Run seed.** ``sha256(claim_seed_bytes || b"refute/v0.3/runs" || arxiv_id_utf8)``, where
``claim_seed_bytes`` are the 32 bytes of the drand randomness reserved for the claims and
the arXiv ID is canonical, without version. It differs from the seed that shuffled the
claim inventory, ``sha256(claim_seed_bytes || arxiv_id_utf8)`` (refute.selection.inventory),
because of its own domain string.

**Derived seeds.** For a domain ``D`` (``base``, ``seeds``, ``data_split``, ``holdout``) the
generator is ``random.Random(int.from_bytes(sha256(run_seed || D_utf8), "big"))``, where
``run_seed`` is the 32 bytes of the run seed, and the seeds are its successive
``randrange(2**31)`` values, skipping repeats and any value already used by the base run.
"""

from __future__ import annotations

import hashlib
import random
import re
from collections.abc import Iterable

RUN_SEED_DOMAIN = b"refute/v0.3/runs"
ARXIV_ID = re.compile(r"^\d{4}\.\d{4,5}$")
SEED_LIMIT = 2**31
DOMAINS = ("base", "seeds", "data_split", "holdout")
# The fixed lengths of the derived lists (plan lines 488-491).
ATTACK_SEEDS = 5
DATA_SPLIT_SEEDS = 3
HOLDOUT_SEEDS = 1


def run_seed(claim_seed_bytes: bytes, arxiv_id: str) -> str:
    """The per-paper run seed, as 64 lowercase hex digits."""
    if len(claim_seed_bytes) != 32:
        raise ValueError("claim_seed_bytes are the 32 bytes of the drand randomness")
    if not ARXIV_ID.match(arxiv_id):
        raise ValueError("the arXiv ID is new-style, without version")
    return hashlib.sha256(claim_seed_bytes + RUN_SEED_DOMAIN + arxiv_id.encode("utf-8")).hexdigest()


def derived_seeds(
    run_seed_sha256: str, domain: str, count: int, exclude: Iterable[int] = ()
) -> list[int]:
    """``count`` seeds of ``domain``, distinct and not in ``exclude``."""
    if not re.fullmatch(r"[0-9a-f]{64}", run_seed_sha256):
        raise ValueError("run_seed_sha256 must be 64 lowercase hex digits")
    if domain not in DOMAINS:
        raise ValueError(f"unknown seed domain {domain!r}")
    if count < 0:
        raise ValueError("count cannot be negative")
    digest = hashlib.sha256(bytes.fromhex(run_seed_sha256) + domain.encode("utf-8")).digest()
    rng = random.Random(int.from_bytes(digest, "big"))
    used = set(exclude)
    out: list[int] = []
    while len(out) < count:
        value = rng.randrange(SEED_LIMIT)
        if value in used:
            continue
        used.add(value)
        out.append(value)
    return out
