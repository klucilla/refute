"""SHA-256 helpers used by locks, code hashes, data manifests and dossiers."""

from __future__ import annotations

import hashlib
from pathlib import Path

_CHUNK = 1 << 20


def sha256_bytes(data: bytes) -> str:
    """Hex SHA-256 of raw bytes."""
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path | str) -> str:
    """Hex SHA-256 of a file's raw bytes (used for binary data such as FITS files)."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(_CHUNK), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_newlines(data: bytes) -> bytes:
    """Convert CRLF line endings to LF."""
    return data.replace(b"\r\n", b"\n")


def is_text(data: bytes) -> bool:
    """True when the bytes decode as UTF-8 and contain no NUL byte."""
    if b"\x00" in data:
        return False
    try:
        data.decode("utf-8")
    except UnicodeDecodeError:
        return False
    return True


def sha256_text_normalized(path: Path | str) -> str:
    """SHA-256 of a file, with CRLF normalized to LF when the file is text.

    Git may convert line endings on checkout (``core.autocrlf``). Normalizing makes
    the hash of a text file identical on Windows and Linux checkouts. Binary files
    (not valid UTF-8, or containing NUL) are hashed as raw bytes.
    """
    data = Path(path).read_bytes()
    if is_text(data):
        data = normalize_newlines(data)
    return sha256_bytes(data)
