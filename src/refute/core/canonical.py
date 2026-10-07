"""Canonical JSON serialization (``refute-cjson-1``) and its SHA-256.

The canonical form of a value is:

1. every string (keys and values) normalized to Unicode NFC;
2. serialized with ``json.dumps(sort_keys=True, separators=(",", ":"),
   ensure_ascii=False, allow_nan=False)``;
3. encoded as UTF-8.

Key order, YAML comments and whitespace therefore never affect the hash, while any
change of a value does. Non-finite floats are rejected.
"""

from __future__ import annotations

import json
import math
import unicodedata
from typing import Any

from refute.core.hashing import sha256_bytes

CANONICALIZATION = "refute-cjson-1"


def _normalize(value: Any) -> Any:
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value)
    if isinstance(value, bool) or value is None:
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("non-finite floats cannot be canonicalized")
        return value
    if isinstance(value, dict):
        out: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError(f"canonical JSON keys must be strings, got {type(key).__name__}")
            out[unicodedata.normalize("NFC", key)] = _normalize(item)
        return out
    if isinstance(value, list | tuple):
        return [_normalize(item) for item in value]
    raise TypeError(f"value of type {type(value).__name__} cannot be canonicalized")


def canonical_bytes(value: Any) -> bytes:
    """Return the canonical UTF-8 JSON encoding of ``value``."""
    text = json.dumps(
        _normalize(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )
    return text.encode("utf-8")


def canonical_sha256(value: Any) -> str:
    """SHA-256 (hex) of the canonical encoding of ``value``."""
    return sha256_bytes(canonical_bytes(value))
