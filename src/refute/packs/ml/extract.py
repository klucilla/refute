"""Deterministic metric extraction (WP3 W3.11, W3.12; design 1.0.3 ``run.metric_extraction``).

The value is read from a file the run wrote (``from: file``, the path may hold
``{seed}``) or from the run's log (``from: log``), by exactly one of:

- ``json_path``: a JSON document and a path in a small, fixed grammar:
  ``$`` followed by ``.name`` or ``[index]`` steps (``$.test.acc``, ``$.runs[0].acc``).
  No wildcards, filters or slices: one path names one value;
- ``csv``: the value of ``column`` in the single row whose ``row.column`` equals
  ``row.equals`` (both compared as text);
- ``regex``: a regular expression searched in the text; it must match exactly once,
  and the value is its ``group`` (number or name).

A JSON object with a repeated key, and a CSV header with a repeated column, are refused:
the value would depend on which copy a parser keeps. The result is the **token as
text**, exactly as written (for a JSON number, its source text: ``1e-2`` stays
``1e-2``), because ``metric_recompute`` derives the printed interval from it
(section 1.7). Any failure (no file, no match, more than one match, a value that is not
a finite decimal number) raises ``ExtractionError``: the gate ``metric_extracted`` does
not pass (W3.12). No LLM reads outputs; nothing is guessed.
"""

from __future__ import annotations

import csv
import io
import json
import re
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path, PurePosixPath
from typing import Any

_NUMBER = re.compile(r"^[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?$")
_STEP = re.compile(r"\.([A-Za-z_][A-Za-z0-9_-]*)|\[(\d+)\]")
MAX_BYTES = 64 * 1024 * 1024


class ExtractionError(Exception):
    """The metric could not be extracted: ``metric_extracted`` does not pass."""


@dataclass(frozen=True)
class Extracted:
    token: str  # the number as written
    value: Decimal
    source: str  # "file:<path>" or "log"


def _number(token: str, where: str) -> Extracted:
    text = token.strip()
    if not _NUMBER.match(text):
        raise ExtractionError(f"{where}: {token!r} is not a finite decimal number")
    return Extracted(text, Decimal(text), where)


def parse_json_path(path: str) -> list[str | int]:
    """``$.a.b[0]`` -> ["a", "b", 0]; anything else is refused."""
    if not path.startswith("$"):
        raise ExtractionError(f"json_path must start with '$': {path!r}")
    steps: list[str | int] = []
    position = 1
    while position < len(path):
        match = _STEP.match(path, position)
        if match is None:
            raise ExtractionError(f"json_path has an unsupported step at {position}: {path!r}")
        steps.append(match.group(1) if match.group(1) is not None else int(match.group(2)))
        position = match.end()
    if not steps:
        raise ExtractionError("json_path names the whole document, not a value")
    return steps


class _JsonNumber(str):
    """A JSON number kept as the exact text written in the document."""


def _unique_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """A JSON object whose keys are unique: a repeated key is ambiguous, and the
    standard parser would silently keep the last one (Codex review)."""
    out: dict[str, Any] = {}
    for key, value in pairs:
        if key in out:
            raise ValueError(f"the key {key!r} is repeated in one object")
        out[key] = value
    return out


def _from_json(text: str, path: str, where: str) -> Extracted:
    try:
        document = json.loads(
            text,
            parse_float=_JsonNumber,
            parse_int=_JsonNumber,
            parse_constant=_refuse_constant,
            object_pairs_hook=_unique_keys,
        )
    except (json.JSONDecodeError, ValueError) as exc:
        raise ExtractionError(f"{where}: not valid JSON: {exc}") from None
    node: Any = document
    for step in parse_json_path(path):
        if isinstance(step, int):
            if not isinstance(node, list) or step >= len(node):
                raise ExtractionError(f"{where}: {path} has no index {step}")
        elif not isinstance(node, dict) or step not in node:
            raise ExtractionError(f"{where}: {path} has no key {step!r}")
        node = node[step]
    if not isinstance(node, _JsonNumber):
        raise ExtractionError(f"{where}: {path} is not a number ({type(node).__name__})")
    return _number(str(node), where)


def _refuse_constant(name: str) -> Any:
    raise ValueError(f"non-finite JSON constant {name}")


def _from_csv(text: str, column: str, row: dict[str, str], where: str) -> Extracted:
    reader = csv.reader(io.StringIO(text, newline=""))
    try:
        header = next(reader)
    except StopIteration:
        raise ExtractionError(f"{where}: the CSV is empty") from None
    except csv.Error as exc:
        raise ExtractionError(f"{where}: not valid CSV: {exc}") from None
    repeated = sorted({h for h in header if header.count(h) > 1})
    if repeated:
        # a repeated column is ambiguous (Codex review)
        raise ExtractionError(f"{where}: the header repeats the columns {repeated}")
    for name in (column, row["column"]):
        if name not in header:
            raise ExtractionError(f"{where}: no column {name!r}")
    value_at, key_at = header.index(column), header.index(row["column"])
    matches = []
    try:
        for number, fields in enumerate(reader, start=2):
            if len(fields) != len(header):
                raise ExtractionError(
                    f"{where}: line {number} has {len(fields)} fields, the header {len(header)}"
                )
            if fields[key_at] == row["equals"]:
                matches.append(fields[value_at])
    except csv.Error as exc:
        raise ExtractionError(f"{where}: not valid CSV: {exc}") from None
    if len(matches) != 1:
        raise ExtractionError(
            f"{where}: {len(matches)} rows have {row['column']} = {row['equals']!r}; "
            "exactly one is needed"
        )
    return _number(matches[0], where)


def _from_regex(text: str, pattern: str, group: int | str, where: str) -> Extracted:
    try:
        compiled = re.compile(pattern)
    except re.error as exc:
        raise ExtractionError(f"regex does not compile: {exc}") from None
    matches = list(compiled.finditer(text))
    if len(matches) != 1:
        raise ExtractionError(
            f"{where}: the regex matched {len(matches)} times; exactly once is needed"
        )
    try:
        token = matches[0].group(group)
    except IndexError as exc:  # also raised for an unknown group name
        raise ExtractionError(f"{where}: the regex has no group {group!r}: {exc}") from None
    if token is None:
        raise ExtractionError(f"{where}: group {group!r} did not take part in the match")
    return _number(token, where)


def _read(path: Path, where: str) -> str:
    try:
        if path.stat().st_size > MAX_BYTES:
            raise ExtractionError(f"{where}: larger than {MAX_BYTES} bytes")
        return path.read_text(encoding="utf-8")
    except ExtractionError:
        raise
    except (OSError, UnicodeDecodeError) as exc:
        raise ExtractionError(f"{where}: cannot read: {exc}") from None


def extract(
    extraction: dict[str, Any], workdir: Path, log_text: str, seed: int | None
) -> Extracted:
    """The metric of one run, by the claim's resolved ``metric_extraction`` block."""
    origin = extraction.get("from")
    if origin == "file":
        relative = str(extraction["file"])
        if "{seed}" in relative:
            if seed is None:
                raise ExtractionError("the extraction file names {seed} but the run has no seed")
            relative = relative.replace("{seed}", str(seed))
        posix = PurePosixPath(relative)
        if posix.is_absolute() or ".." in posix.parts or "\\" in relative:
            raise ExtractionError(f"extraction file must be relative, without '..': {relative!r}")
        where = f"file:{relative}"
        text = _read(workdir.joinpath(*posix.parts), where)
    elif origin == "log":
        where, text = "log", log_text
    else:
        raise ExtractionError(f"metric_extraction.from must be file or log, got {origin!r}")
    ways = [k for k in ("json_path", "csv", "regex") if extraction.get(k) is not None]
    if len(ways) != 1:
        raise ExtractionError("metric_extraction takes exactly one of json_path, csv, regex")
    if ways == ["json_path"]:
        return _from_json(text, extraction["json_path"], where)
    if ways == ["csv"]:
        spec = extraction["csv"]
        return _from_csv(text, spec["column"], spec["row"], where)
    spec = extraction["regex"]
    return _from_regex(text, spec["pattern"], spec["group"], where)
