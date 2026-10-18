"""Readers of the ML pack: how many examples each declared split of a fetched dataset holds
(the ``data_present`` gate, WP3 integration requirement 5; #15). Without a reading, the
gate is ``INCONCLUSIVE`` (``integration.data_present``), never a pass.

A split's ``source`` names how it is counted, fixed in the claim before the lock, in the
form ``reader:<format>:<selector>``; any other text is not read by Refute (the gate stays
``INCONCLUSIVE``). Formats (no new dependency):

- ``npz:<array>``: the length of the first axis of that array of a NumPy ``.npz`` file;
- ``npy``: the length of the first axis of a ``.npy`` file (selector empty);
- ``csv:<rows>`` and ``tsv:<rows>``: the number of data rows (the header excluded);
- ``jsonl:<rows>``: the number of non-empty lines;
- ``parquet:<rows>``: the row count of a Parquet file (pyarrow, already a dependency of
  the selection);
- ``zip:<member>``: one of these formats inside a zip archive, as
  ``zip:<member>!<format>:<selector>``.

A file that cannot be read gives no count (``None``), never a guess. Reading never runs
code from the file: ``numpy.load`` with ``allow_pickle=False``.
"""

from __future__ import annotations

import csv
import io
import zipfile
from collections.abc import Mapping
from pathlib import Path
from typing import Any

PREFIX = "reader:"


def _count(data: bytes, fmt: str, selector: str) -> int:
    if fmt == "npz":
        import numpy as np

        with np.load(io.BytesIO(data), allow_pickle=False) as archive:
            return int(archive[selector].shape[0])
    if fmt == "npy":
        import numpy as np

        return int(np.load(io.BytesIO(data), allow_pickle=False).shape[0])
    if fmt in ("csv", "tsv"):
        if selector != "rows":
            raise ValueError("csv and tsv count rows")
        text = data.decode("utf-8-sig")
        rows = list(csv.reader(io.StringIO(text), delimiter="," if fmt == "csv" else "\t"))
        return max(len([r for r in rows if r]) - 1, 0)
    if fmt == "jsonl":
        if selector != "rows":
            raise ValueError("jsonl counts rows")
        return sum(1 for line in data.decode("utf-8").splitlines() if line.strip())
    if fmt == "parquet":
        if selector != "rows":
            raise ValueError("parquet counts rows")
        import pyarrow.parquet as pq

        return int(pq.ParquetFile(io.BytesIO(data)).metadata.num_rows)
    raise ValueError(f"unknown format {fmt!r}")


def count_split(path: Path, source: str) -> int | None:
    """The examples of one split, or None when the source names no reader or the file
    cannot be read."""
    if not source.startswith(PREFIX):
        return None
    spec = source[len(PREFIX) :]
    try:
        if spec.startswith("zip:"):
            member, _, inner = spec[len("zip:") :].partition("!")
            fmt, _, selector = inner.partition(":")
            with zipfile.ZipFile(path) as archive:
                return _count(archive.read(member), fmt, selector)
        fmt, _, selector = spec.partition(":")
        return _count(path.read_bytes(), fmt, selector)
    except Exception:  # an unreadable file gives no count, never a guess
        return None


def split_counts(path: Path, splits: Mapping[str, Mapping[str, Any]]) -> dict[str, int] | None:
    """Every declared split's count, or None when any of them cannot be read."""
    out = {}
    for name, split in splits.items():
        n = count_split(path, str(split["source"]))
        if n is None:
            return None
        out[name] = n
    return out
