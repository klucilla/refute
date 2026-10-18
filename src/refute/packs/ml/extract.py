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
  and the value is its ``group`` (number or name);
- ``tensorboard`` (``from: file`` only): the one scalar of a ``tag`` at a ``step`` (or the
  ``"last"``, greatest, step) of a TensorBoard event file (``tbevents``, W3.11b); the
  token is the exact expansion of the binary float, marked ``binary``.

A JSON object with a repeated key, and a CSV header with a repeated column, are refused:
the value would depend on which copy a parser keeps. The result is the **token as
text**, exactly as written (for a JSON number, its source text: ``1e-2`` stays
``1e-2``), because ``metric_recompute`` derives the printed interval from it
(section 1.7). Any failure (no file, no match, more than one match, a value that is not
a finite decimal number) raises ``ExtractionError``: the gate ``metric_extracted`` does
not pass (W3.12). No LLM reads outputs; nothing is guessed.
"""

from __future__ import annotations

import contextlib
import contextvars
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
_TEXT_WAYS = ("json_path", "csv", "regex")
DIGIT_BUDGET = 4096
BUDGET_REASON = "the exact-arithmetic budget of Refute (a limitation of Refute)"


class ExtractionError(Exception):
    """The metric could not be extracted: ``metric_extracted`` does not pass."""


@dataclass(frozen=True)
class Extracted:
    token: str  # the number as written
    value: Decimal
    source: str  # "file:<path>" or "log"
    # "float32" or "float64" when the token is the exact expansion of a binary float read
    # from an event file (W3.11b): such a token has no printed interval
    binary: str | None = None


def within_budget(value: Decimal) -> bool:
    """Whether exact arithmetic on ``value`` stays bounded: at most ``DIGIT_BUDGET``
    significant digits and decimal exponents within ``±DIGIT_BUDGET`` (a token such as
    ``1e999999999`` would make the exact predicates expand millions of digits). The exact
    expansion of any float64 fits (at most 767 digits, exponent -1074)."""
    _, digits, exponent = value.as_tuple()
    return (
        len(digits) <= DIGIT_BUDGET
        and -DIGIT_BUDGET <= int(exponent)
        and value.adjusted() <= DIGIT_BUDGET
    )


def _number(token: str, where: str) -> Extracted:
    text = token.strip()
    if not _NUMBER.match(text):
        raise ExtractionError(f"{where}: {token!r} is not a finite decimal number")
    value = Decimal(text)
    if not within_budget(value):
        raise ExtractionError(f"{where}: {token!r} is outside {BUDGET_REASON}")
    return Extracted(text, value, where)


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


_SESSION: contextvars.ContextVar[dict | None] = contextvars.ContextVar("reads", default=None)


@contextlib.contextmanager
def read_session():
    """Within one evaluation, every reader of one file spec of one run (the metric, the
    coverage counts) shares a single resolution and a single read: the same resolved path
    and the same bytes (wp3-extraction-pattern-acceptance.md, "One resolution for every
    reader"). A failure is shared too."""
    token = _SESSION.set({})
    try:
        yield
    finally:
        _SESSION.reset(token)


def read_output_bytes(
    workdir: Path, spec: str, seed: int | None, *, pattern: bool = True
) -> tuple[bytes, str, Path]:
    """The bytes of the one file a run wrote that ``spec`` names, the ``where`` recorded with
    a value read from it (``file:<the resolved path>``), and its path. Exactly one match
    (counted before any content is read); every component a real folder or file, no
    symbolic link; a regular file with a single link, checked again on the open handle.
    With ``pattern=False`` (the predictions file) the final path may hold no pattern, even
    after its placeholders are filled. Anything else is an ExtractionError."""
    if not pattern and any(c in str(spec) for c in "*?[]"):
        raise ExtractionError(f"the file holds no pattern: {spec!r}")
    reads = _SESSION.get()
    key = (os.path.realpath(workdir), str(spec), seed, pattern)
    if reads is not None and key in reads:
        cached = reads[key]
        if isinstance(cached, ExtractionError):
            raise cached
        return cached
    try:
        result = _read_bytes(workdir, spec, seed)
    except ExtractionError as exc:
        if reads is not None:
            reads[key] = exc
        raise
    if reads is not None:
        reads[key] = result
    return result


def _read_bytes(workdir: Path, spec: str, seed: int | None) -> tuple[bytes, str, Path]:
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
    try:
        with os.fdopen(fd, "rb") as handle:
            st = os.fstat(handle.fileno())
            if not stat.S_ISREG(st.st_mode) or st.st_nlink != 1:
                raise ExtractionError(f"{where}: not a regular file with a single link")
            if st.st_size > MAX_BYTES:
                raise ExtractionError(f"{where}: larger than {MAX_BYTES} bytes")
            data = handle.read(MAX_BYTES + 1)
    except OSError as exc:  # a failure of fstat or of the read is no value, never a crash
        raise ExtractionError(f"{where}: cannot read: {exc}") from None
    if len(data) > MAX_BYTES:
        raise ExtractionError(f"{where}: larger than {MAX_BYTES} bytes")
    return data, where, current


def read_output(workdir: Path, spec: str, seed: int | None) -> tuple[str, str, Path]:
    """``read_output_bytes``, decoded as UTF-8."""
    data, where, current = read_output_bytes(workdir, spec, seed)
    try:
        return data.decode("utf-8"), where, current
    except UnicodeDecodeError as exc:
        raise ExtractionError(f"{where}: cannot read: {exc}") from None


def extract(
    extraction: dict[str, Any], workdir: Path, log_text: str, seed: int | None
) -> Extracted:
    """The metric of one run, by the claim's resolved ``metric_extraction`` block."""
    origin = extraction.get("from")
    board = extraction.get("tensorboard")
    if board is not None:
        from refute.packs.ml import tbevents  # noqa: PLC0415 - tbevents imports this module

        if origin != "file" or any(extraction.get(k) is not None for k in _TEXT_WAYS):
            raise ExtractionError("tensorboard is read from a file, and alone")
        data, where, _ = read_output_bytes(workdir, str(extraction["file"]), seed)
        found = tbevents.select(data, str(board["tag"]), board["step"], where)
        token = tbevents.token(found.value, where)
        if not within_budget(Decimal(token)):  # never for a float32 or float64
            raise ExtractionError(f"{where}: the value is outside {BUDGET_REASON}")
        return Extracted(token, Decimal(token), where, found.width)
    if origin == "file":
        text, where, _ = read_output(workdir, str(extraction["file"]), seed)
    elif origin == "log":
        where, text = "log", log_text
    else:
        raise ExtractionError(f"metric_extraction.from must be file or log, got {origin!r}")
    return parse(extraction, text, where)


def parse(extraction: dict[str, Any], text: str, where: str) -> Extracted:
    """The value a selector names in a text already read (one file or the log)."""
    if extraction.get("tensorboard") is not None:
        raise ExtractionError("tensorboard reads the bytes of an event file, not a text")
    ways = [k for k in _TEXT_WAYS if extraction.get(k) is not None]
    if len(ways) != 1:
        raise ExtractionError("metric_extraction takes exactly one of json_path, csv, regex")
    if ways == ["json_path"]:
        return _from_json(text, extraction["json_path"], where)
    if ways == ["csv"]:
        spec = extraction["csv"]
        return _from_csv(text, spec["column"], spec["row"], where)
    spec = extraction["regex"]
    return _from_regex(text, spec["pattern"], spec["group"], where)
