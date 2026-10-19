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
- ``lines:rows``: the number of non-empty lines (whitespace-separated text);
  ``lines:rows-1`` excludes one header line;
- ``arff:rows``: the number of non-empty, non-comment (``%``) lines after the ``@data``
  line (case insensitive); with no ``@data`` line the file gives no count;
- ``zip:<member>``: one of these formats inside a zip archive, as
  ``zip:<member>!<format>:<selector>``.

``lines`` and ``arff`` were added by docs/validation/v0.3/wp3-data-sources-acceptance.md
(section 4.1). Formats that need a library or run code (CIFAR python archives, Excel, DGL)
are counted in the paper's own container (section 4.2), never here.

A file that cannot be read gives no count (``None``), never a guess. Reading never runs
code from the file: ``numpy.load`` with ``allow_pickle=False``.
"""

from __future__ import annotations

import csv
import io
import json
import zipfile
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from refute.packs.ml import extract

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
    if fmt == "lines":
        if selector not in ("rows", "rows-1"):
            raise ValueError("lines counts rows or rows-1")
        rows = sum(1 for line in data.decode("utf-8-sig").splitlines() if line.strip())
        return max(rows - 1, 0) if selector == "rows-1" else rows
    if fmt == "arff":
        if selector != "rows":
            raise ValueError("arff counts rows")
        lines = data.decode("utf-8-sig").splitlines()
        start = next((i for i, line in enumerate(lines) if line.strip().lower() == "@data"), None)
        if start is None:
            raise ValueError("an ARFF file with no @data line")
        return sum(
            1 for line in lines[start + 1 :] if line.strip() and not line.lstrip().startswith("%")
        )
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
    """Every declared split's count, or None when any of them cannot be read. Splits counted
    in the paper's container (``container_place``) are left out: they are read after the
    build (``read_answer``)."""
    out = {}
    for name, split in splits.items():
        if is_container_source(str(split["source"])):
            continue
        n = count_split(path, str(split["source"]))
        if n is None:
            return None
        out[name] = n
    return out


# ---- readers in the paper's container (wp3-data-sources-acceptance.md, section 4.2) ----------

CONTAINER_PREFIX = PREFIX + "container:"
CONTAINER_READERS = ("cifar_python", "excel", "dgl")
# the reader's answer, in its own folder, and its largest size
ANSWER = "out/counts.json"
ANSWER_MAX_BYTES = 64 * 1024


def is_container_source(source: str) -> bool:
    return source.startswith(CONTAINER_PREFIX)


def container_place(source: str) -> dict[str, str]:
    """``reader:container:<reader>:<member>#<arg>`` as the request of one split: the reader
    (closed list), the member of an archive (exact name; empty for a bare file; members
    joined by ``+`` for ``cifar_python``) and the argument (a sheet for ``excel``, a canonical
    edge type ``src,etype,dst`` for ``dgl``). ValueError for anything else."""
    if not is_container_source(source):
        raise ValueError(f"not a container reader: {source!r}")
    reader, sep, selector = source[len(CONTAINER_PREFIX) :].partition(":")
    if not sep or reader not in CONTAINER_READERS:
        raise ValueError(f"unknown container reader in {source!r} (known: {CONTAINER_READERS})")
    member, _, arg = selector.partition("#")
    if "\\" in member or member.startswith("/") or ".." in member.split("/"):
        raise ValueError(f"a member is a plain relative name: {member!r}")
    if reader == "cifar_python" and (not member or arg or "" in member.split("+")):
        raise ValueError("cifar_python names one or more members joined by '+', no argument")
    if reader == "excel" and not arg:
        raise ValueError("excel names its sheet after '#'")
    if reader == "dgl" and (member or len(arg.split(",")) != 3 or "" in arg.split(",")):
        raise ValueError("dgl takes no member and a canonical edge type src,etype,dst")
    return {"reader": reader, "member": member, "arg": arg}


def container_request(path: str, splits: Mapping[str, Mapping[str, Any]]) -> str | None:
    """The request of a dataset's container reader (canonical JSON text), for the splits
    counted in the container, or None when there is none. ``path`` is where the dataset is
    mounted in the reader's folder."""
    places = {
        name: container_place(str(split["source"]))
        for name, split in splits.items()
        if is_container_source(str(split["source"]))
    }
    if not places:
        return None
    return json.dumps({"path": path, "splits": places}, sort_keys=True, separators=(",", ":"))


def _refuse_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    keys = [k for k, _ in pairs]
    if len(set(keys)) != len(keys):
        raise ValueError("a key appears twice")
    return dict(pairs)


def _refuse_constant(name: str) -> Any:
    raise ValueError(f"{name} is not a count")


def read_answer(path: Path, splits: set[str], workdir: Path | None = None) -> dict[str, int] | None:
    """The counts a container reader wrote, or None: a regular file (not a link) of at most
    ``ANSWER_MAX_BYTES``, holding one JSON object with exactly ``splits`` as keys, each a
    non-negative integer (no boolean, no float, no duplicate key, nothing after it). With
    ``workdir`` (the reader's folder), the bytes read are recorded before the parsing
    (``extract.record_reads``, the dossier's provenance)."""
    try:
        if path.is_symlink() or not path.is_file():
            return None
        with path.open("rb") as handle:  # never more than the limit in memory
            data = handle.read(ANSWER_MAX_BYTES + 1)
        if len(data) > ANSWER_MAX_BYTES:
            return None
        if workdir is not None:
            extract.record_file(workdir, path.relative_to(workdir).as_posix(), data)
        answer = json.loads(
            data.decode("utf-8"),
            object_pairs_hook=_refuse_duplicates,
            parse_float=lambda text: _refuse_constant(text),
            parse_constant=_refuse_constant,
        )
    except (OSError, UnicodeDecodeError, ValueError, RecursionError):
        return None
    if not isinstance(answer, dict) or set(answer) != set(splits):
        return None
    if any(type(v) is not int or v < 0 for v in answer.values()):
        return None
    return dict(answer)
