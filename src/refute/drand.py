"""drand randomness for pre-registered draws (shared module, WP5 W5.1).

The functions come from ``calibration/v0.2/select_targets.py`` (``round_time``,
``verify_beacon``, ``drand_seed``) with their behavior unchanged; that script keeps its
own copy for its recorded use (W5.2). The chain is drand mainnet, default chain
(pedersen-bls-chained), as in v0.2.

- ``round_time``: when a round is published.
- ``verify_beacon``: offline check of one beacon; returns ``seed = int(randomness, 16)``.
- ``drand_seed``: fetch and verify a round (network); refuses a round not yet published.
- ``shuffled``: the draw order of plan section 4.3: sort by a key, then shuffle with
  ``random.Random(seed)``.

If drand is unavailable or a signature fails, these functions raise; a caller never
switches the source of randomness (plan section 4.3, item 6).
"""

from __future__ import annotations

import hashlib
import json
import platform
import random
import urllib.request
from collections.abc import Callable, Iterable
from datetime import UTC, datetime
from importlib.metadata import version
from typing import Any

DRAND_URL = "https://api.drand.sh"
DRAND_CHAIN_HASH = "8990e7a9aaed2ffed73dbd7092123d6f289930540d7651336225dc172e51b2ce"
DRAND_PUBLIC_KEY = (
    "868f005eb8e6e4ca0a47c8a77ceaa5309a47978a7c71bc5cce96366b5d7a569937c529eeda66c7293784"
    "a9402801af31"
)
DRAND_GENESIS = 1595431050
DRAND_PERIOD = 30


def _download(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "refute-selection"})
    with urllib.request.urlopen(request, timeout=180) as response:  # noqa: S310 - fixed URLs
        return response.read()


def _utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def round_time(number: int) -> datetime:
    """UTC time at which round ``number`` of the chain is published."""
    return datetime.fromtimestamp(DRAND_GENESIS + (number - 1) * DRAND_PERIOD, UTC)


def round_after(created_at: str, margin_seconds: int = 3600) -> int:
    """The first round published at least ``margin_seconds`` after ``created_at``
    (``YYYY-MM-DDTHH:MM:SSZ``): the rule of the v0.3 protocols
    (``calibration/v0.3/pilot/select_pilot.py``), used for the v0.4 rounds (protocol section 8)."""
    created = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
    earliest = created.timestamp() + margin_seconds
    number = -(-(int(earliest) - DRAND_GENESIS) // DRAND_PERIOD) + 1
    while round_time(number).timestamp() < earliest:
        number += 1
    return number


def verify_beacon(number: int, beacon: dict[str, Any]) -> int:
    """Verify one drand beacon of the chain and return the seed (offline).

    Scheme pedersen-bls-chained: the signature is a BLS signature on G2 by the
    chain's public key over sha256(previous_signature || round as 8 big-endian
    bytes), checked with py_ecc's G2Basic ciphersuite, and the randomness must
    equal sha256(signature). The seed is the randomness read as one big-endian
    integer: seed = int(randomness_hex, 16). Raises RuntimeError on any mismatch.
    """
    from py_ecc.bls import G2Basic

    if int(beacon["round"]) != number:
        raise RuntimeError(f"drand returned round {beacon['round']}, expected {number}")
    signature = bytes.fromhex(beacon["signature"])
    message = hashlib.sha256(
        bytes.fromhex(beacon["previous_signature"]) + number.to_bytes(8, "big")
    ).digest()
    if not G2Basic.Verify(bytes.fromhex(DRAND_PUBLIC_KEY), message, signature):
        raise RuntimeError(f"drand round {number}: BLS signature does not verify")
    if hashlib.sha256(signature).hexdigest() != beacon["randomness"]:
        raise RuntimeError(f"drand round {number}: randomness != sha256(signature)")
    return int(beacon["randomness"], 16)


def drand_seed(
    number: int, download: Callable[[str], bytes] = _download
) -> tuple[int, dict[str, Any]]:
    """Fetch and verify a drand round of the chain. Raises on any problem.

    ``download`` is the HTTP GET used (a parameter so that tests run offline with
    recorded responses); the round must already be published.
    """
    if datetime.now(UTC) < round_time(number):
        raise RuntimeError(
            f"drand round {number} is published at {round_time(number).isoformat()}; "
            "it is not available yet"
        )
    info = json.loads(download(f"{DRAND_URL}/{DRAND_CHAIN_HASH}/info"))
    if info.get("hash") != DRAND_CHAIN_HASH or info.get("public_key") != DRAND_PUBLIC_KEY:
        raise RuntimeError(f"drand chain info does not match the protocol: {info}")
    url = f"{DRAND_URL}/{DRAND_CHAIN_HASH}/public/{number}"
    beacon = json.loads(download(url))
    seed = verify_beacon(number, beacon)
    record = {
        "chain_hash": DRAND_CHAIN_HASH,
        "scheme": info.get("schemeID"),
        "round": number,
        "round_time_utc": round_time(number).isoformat(),
        "url": url,
        "retrieved_utc": _utc_now(),
        "randomness": beacon["randomness"],
        "signature": beacon["signature"],
        "previous_signature": beacon["previous_signature"],
        "signature_verified": True,
        "verifier": f"py_ecc {version('py_ecc')} (G2Basic)",
    }
    return seed, record


def shuffled[T](items: Iterable[T], seed: int, key: Callable[[T], Any]) -> list[T]:
    """Sort by ``key`` (which must be unique per item), then shuffle with
    ``random.Random(seed)``: the order of plan section 4.3, items 3 and 4."""
    ordered = sorted(items, key=key)
    keys = [key(item) for item in ordered]
    if len(set(keys)) != len(keys):
        raise ValueError("the sort key is not unique, so the order would depend on the input")
    random.Random(seed).shuffle(ordered)
    return ordered


def interpreter_record() -> dict[str, str]:
    """The interpreter that ran a shuffle, for the selection log of every draw (the paper
    draw and each claim draw). Python guarantees the same ``random()`` sequence for a
    compatible seeder, not the same ``shuffle`` across versions
    (https://docs.python.org/3.13/library/random.html#notes-on-reproducibility, accessed
    2026-10-15), so a draw is replayed with the version it records (#59, Codex review of
    #78); the recorded orders of tests/test_selection_frame.py stay as regression checks."""
    return {
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
    }
