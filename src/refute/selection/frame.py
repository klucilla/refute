"""The sampling frame (WP5 W5.3; plan section 4.1).

The frame is the Parquet file of the Papers with Code archive on Hugging Face,
``pwc-archive/links-between-paper-and-code``. Its URL, revision and SHA-256 are
recorded in the protocol before any draw; ``load_frame`` refuses a file whose SHA-256
differs, and reads only the columns the selection uses.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

FRAME_COLUMNS = ("paper_arxiv_id", "repo_url", "is_official", "mentioned_in_paper", "framework")


class FrameError(Exception):
    """The frame snapshot cannot be used."""


@dataclass(frozen=True)
class FrameSnapshot:
    """A recorded snapshot of the frame: where it came from and its hash."""

    url: str
    revision: str
    sha256: str
    path: Path

    def record(self) -> dict[str, str]:
        """The fields that go into the protocol (no local path)."""
        return {"url": self.url, "revision": self.revision, "sha256": self.sha256}


def file_sha256(path: Path | str) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def load_frame(snapshot: FrameSnapshot) -> list[dict[str, Any]]:
    """The rows of the frame, with only ``FRAME_COLUMNS``, after checking the hash."""
    import pyarrow.parquet as pq

    if len(snapshot.sha256) != 64 or any(c not in "0123456789abcdef" for c in snapshot.sha256):
        raise FrameError("the recorded SHA-256 must be 64 lowercase hexadecimal digits")
    actual = file_sha256(snapshot.path)
    if actual != snapshot.sha256:
        raise FrameError(f"the frame file has SHA-256 {actual}, not the recorded {snapshot.sha256}")
    schema = pq.read_schema(snapshot.path)
    missing = [c for c in FRAME_COLUMNS if c not in schema.names]
    if missing:
        raise FrameError("the frame lacks the columns: " + ", ".join(missing))
    return pq.read_table(snapshot.path, columns=list(FRAME_COLUMNS)).to_pylist()
