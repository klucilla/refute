"""Deterministic metric extraction (WP3 W3.11, W3.12; design 1.0.3 ``run.metric_extraction``).

The value is read from a file the run wrote (``from: file``, the path may hold
``{seed}`` and one component that is exactly ``*``, resolved to exactly one path the run
created: ``read_output``, wp3-extraction-pattern-acceptance.md) or from the run's log
(``from: log``), by exactly one of:

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
import os
import re
import stat
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


# ---- the file a run wrote (W3.11; wp3-extraction-pattern-acceptance.md, W3.11a) -----------

WILDCARD = "*"


def check_pattern(path: str) -> None:
    """A file path may hold one component that is exactly ``*`` and no other pattern:
    ValueError otherwise."""
    parts = PurePosixPath(path).parts
    if any(c in part for part in parts for c in "?[]"):
        raise ValueError(f"a file path holds no '?', '[' or ']': {path!r}")
    stars = [part for part in parts if "*" in part]
    if any(part != WILDCARD for part in stars) or len(stars) > 1:
        raise ValueError(f"a file path holds at most one component that is exactly '*': {path!r}")


def _relative(spec: str, seed: int | None) -> PurePosixPath:
    relative = str(spec)
    if "{seed}" in relative:
        if seed is None:
            raise ExtractionError("the file names {seed} but the run has no seed")
        relative = relative.replace("{seed}", str(seed))
    posix = PurePosixPath(relative)
    if posix.is_absolute() or ".." in posix.parts or "\\" in relative or not posix.parts:
        raise ExtractionError(f"a file must be relative, without '..': {relative!r}")
    try:
        check_pattern(relative)
    except ValueError as exc:
        raise ExtractionError(str(exc)) from None
    return posix


def _is_link(path: Path, st: os.stat_result) -> bool:
    return stat.S_ISLNK(st.st_mode) or (hasattr(path, "is_junction") and path.is_junction())


def _lexists(workdir: Path, parts: tuple[str, ...]) -> bool:
    """Whether the path exists, without following any link; an error while inspecting a
    component is an ExtractionError, never read as absence."""
    try:
        os.lstat(workdir.joinpath(*parts))
    except FileNotFoundError:
        return False
    except OSError as exc:
        raise ExtractionError(f"cannot inspect {'/'.join(parts)}: {exc}") from None
    return True


def _matches(workdir: Path, posix: PurePosixPath) -> list[tuple[str, ...]]:
    """Every existing path the file names: itself, or with a name in place of ``*``. Only
    names are listed and compared; no content is read."""
    parts = posix.parts
    if WILDCARD not in parts:
        return [parts] if _lexists(workdir, parts) else []
    at = parts.index(WILDCARD)
    parent = workdir.joinpath(*parts[:at])
    try:
        names = sorted(os.listdir(parent))
    except FileNotFoundError:
        return []
    except OSError as exc:
        raise ExtractionError(f"cannot list {'/'.join(parts[:at]) or '.'}: {exc}") from None
    out = []
    for name in names:
        candidate = (*parts[:at], name, *parts[at + 1 :])
        if _lexists(workdir, candidate):
            out.append(candidate)
    return out


def output_present(workdir: Path, spec: str, seed: int | None = None) -> bool:
    """Whether anything the file names (a fixed path, or a match of its ``*``) exists:
    the check that a run's outputs are absent before it starts."""
    return bool(_matches(workdir, _relative(spec, seed)))


def checked_path(workdir: Path, spec: str, seed: int | None) -> Path:
    """The path of the one file ``spec`` names, with every check of ``read_output`` but the
    read itself (for the predictions file, which its own reader opens)."""
    posix = _relative(spec, seed)
    found = _matches(workdir, posix)
    if len(found) != 1:
        raise ExtractionError(
            f"{posix.as_posix()}: {len(found)} paths match; exactly one is needed"
        )
    current = workdir
    for part in found[0]:
        current = current / part
        try:
            st = os.lstat(current)
        except OSError as exc:
            raise ExtractionError(f"{posix.as_posix()}: cannot inspect: {exc}") from None
        if _is_link(current, st):
            raise ExtractionError(f"{posix.as_posix()}: a symbolic link on the path: {part}")
    if not stat.S_ISREG(st.st_mode) or st.st_nlink != 1:
        raise ExtractionError(f"{posix.as_posix()}: not a regular file with a single link")
    return current


def read_output(workdir: Path, spec: str, seed: int | None) -> tuple[str, str, Path]:
    """The text of the one file a run wrote that ``spec`` names, the ``where`` recorded with
    a value read from it (``file:<the resolved path>``), and its path. Exactly one match
    (counted before any content is read); every component a real folder or file, no
    symbolic link; a regular file with a single link, checked again on the open handle.
    Anything else is an ExtractionError."""
    posix = _relative(spec, seed)
    found = _matches(workdir, posix)
    if not found and WILDCARD not in posix.parts:
        raise ExtractionError(f"file:{posix.as_posix()}: cannot read: no such file")
    if len(found) != 1:
        raise ExtractionError(
            f"{posix.as_posix()}: {len(found)} paths match; exactly one is needed"
        )
    parts = found[0]
    where = "file:" + "/".join(parts)
    current = workdir
    for part in parts:
        current = current / part
        try:
            st = os.lstat(current)
        except OSError as exc:
            raise ExtractionError(f"{where}: cannot inspect: {exc}") from None
        if _is_link(current, st):
            raise ExtractionError(f"{where}: a symbolic link on the path: {part}")
    if not stat.S_ISREG(st.st_mode) or st.st_nlink != 1:
        raise ExtractionError(f"{where}: not a regular file with a single link")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_BINARY", 0)
    try:
        fd = os.open(current, flags)
    except OSError as exc:
        raise ExtractionError(f"{where}: cannot open: {exc}") from None
    with os.fdopen(fd, "rb") as handle:
        st = os.fstat(handle.fileno())
        if not stat.S_ISREG(st.st_mode) or st.st_nlink != 1:
            raise ExtractionError(f"{where}: not a regular file with a single link")
        if st.st_size > MAX_BYTES:
            raise ExtractionError(f"{where}: larger than {MAX_BYTES} bytes")
        data = handle.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ExtractionError(f"{where}: larger than {MAX_BYTES} bytes")
    try:
        return data.decode("utf-8"), where, current
    except UnicodeDecodeError as exc:
        raise ExtractionError(f"{where}: cannot read: {exc}") from None


def extract(
    extraction: dict[str, Any], workdir: Path, log_text: str, seed: int | None
) -> Extracted:
    """The metric of one run, by the claim's resolved ``metric_extraction`` block."""
    origin = extraction.get("from")
    if origin == "file":
        text, where, _ = read_output(workdir, str(extraction["file"]), seed)
    elif origin == "log":
        where, text = "log", log_text
    else:
        raise ExtractionError(f"metric_extraction.from must be file or log, got {origin!r}")
    return parse(extraction, text, where)


def parse(extraction: dict[str, Any], text: str, where: str) -> Extracted:
    """The value a selector names in a text already read (one file or the log)."""
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
