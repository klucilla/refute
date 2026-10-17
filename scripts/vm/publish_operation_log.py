"""The publishable copy of the endpoint's operation log (#59, item 5).

The endpoint appends one JSON line per simulation, intent, refusal and result to
``C:\\ProgramData\\RefuteVm\\Log\\operations.jsonl`` on the host. That file stays whole and
local: this script only reads it. What is published (for example next to
``docs/validation/v0.3/wp6-results/jea-registration.md``) is a new file made here, and only
after the checker below has passed on it.

The copy (``anonymize``):

- ``Caller.ConnectedUser`` becomes ``<operator-account>`` (``""`` stays ``""``);
- ``Caller.RunAsUser`` becomes ``<virtual-account> VA <n>``, with the number of the WinRM
  virtual account read from its name (``WinRM VA_<n>_...``), or ``<account>`` for a call
  outside a remote session;
- in every other text, each host identifier becomes ``<host-identifier>``, compared without
  regard to case. The identifiers are those given with ``--identifier``, the computer, user
  and domain names of the environment that runs the script, and the names read from the
  ``Caller`` fields of the whole log (the account, its domain and the part of a virtual
  account's name after its number). A text that is a hash, a GUID or a time is left as it
  is: a name inside one is a coincidence of its digits.

Everything else is kept as it is, including ``PlanSha256``: the hash of the plan in the
local log, which the anonymized plan of the copy no longer has when a text in it changed.

The checker (``check``), which the copy must pass before it is written:

- the copy has the same records as the source, in the same order, with the same keys and
  the same numbers, booleans and nulls; a text differs only in a ``Caller`` field, or where
  it now holds ``<host-identifier>``;
- every ``Caller`` field is one of the placeholders above;
- no text (keys included; a hash, a GUID or a time aside, for the identifiers) holds a
  host identifier, a user profile path, a UNC path, an IPv4
  or IPv6 address, a MAC address, an e-mail address or a machine or domain account SID.

A pattern can refuse a text that is not a host value (a four-part version number reads as
an IPv4 address): the checker then refuses the copy, and the record is published by hand,
never by loosening the checker.

Usage (Python from the project's virtual environment)::

    .venv/Scripts/python.exe scripts/vm/publish_operation_log.py
        --source C:/ProgramData/RefuteVm/Log/operations.jsonl
        --output <new file> [--from-utc <time>] [--to-utc <time>] [--identifier <name> ...]

``--output`` must not exist (the copy never overwrites) and must not be the source. The
script prints the SHA-256 of the source and of the copy, and the number of records.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from collections.abc import Iterable
from pathlib import Path
from typing import Any

OPERATOR = "<operator-account>"
VIRTUAL = "<virtual-account>"
# the account a call outside a remote session runs as (no virtual account)
ACCOUNT = "<account>"
IDENTIFIER = "<host-identifier>"
# the shortest identifier the copy replaces: a shorter one would match inside ordinary words
MIN_IDENTIFIER = 3

UTC = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$")
HASH = re.compile(r"^[0-9a-fA-F]{32,}$")
GUID = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")
VA_NUMBER = re.compile(r"WinRM VA_(\d+)_(.+)$")
RUN_AS_PLACEHOLDER = re.compile(r"^(<virtual-account> VA \d+|<account>)$")

LEAKS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("a user profile path", re.compile(r"(?i)\b[a-z]:[\\/]+users[\\/]")),
    ("a UNC path", re.compile(r"\\\\[^\\\s]+\\")),
    (
        "an IPv4 address",
        re.compile(
            r"(?<![\d.])(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)(?![\d.])"
        ),
    ),
    (
        "an IPv6 address",
        re.compile(r"(?i)(?<![0-9a-f:])(?:[0-9a-f]{1,4}:){3,7}[0-9a-f]{1,4}(?![0-9a-f:])"),
    ),
    (
        "an IPv6 address",
        re.compile(r"(?i)(?<![0-9a-z])[0-9a-f]{1,4}::|::[0-9a-f]{1,4}(?![0-9a-z])"),
    ),
    (
        "a MAC address",
        re.compile(r"(?i)(?<![0-9a-f])(?:[0-9a-f]{2}[:-]){5}[0-9a-f]{2}(?![0-9a-f])"),
    ),
    ("an e-mail address", re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")),
    ("an account SID", re.compile(r"(?i)\bS-1-5-21-\d+-\d+-\d+")),
)


class LogError(Exception):
    """The source cannot be read as an operation log, or the copy is refused."""


# ---- reading ----------------------------------------------------------------------------


def read_records(data: bytes) -> list[dict[str, Any]]:
    """The records of the log: one JSON object per non-empty line, each with a ``Utc``
    time of the endpoint's format."""
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        raise LogError("the log is not UTF-8") from None
    records = []
    for number, line in enumerate(text.split("\n"), start=1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            raise LogError(f"line {number} is not JSON") from None
        if not isinstance(record, dict):
            raise LogError(f"line {number} is not a JSON object")
        if not isinstance(record.get("Utc"), str) or not UTC.match(record["Utc"]):
            raise LogError(f"line {number} has no Utc time of the endpoint's format")
        records.append(record)
    return records


def select(
    records: Iterable[dict[str, Any]], from_utc: str | None = None, to_utc: str | None = None
) -> list[dict[str, Any]]:
    """The records whose ``Utc`` is inside the inclusive window (the endpoint's format sorts
    as text)."""
    for bound in (from_utc, to_utc):
        if bound is not None and not UTC.match(bound):
            raise LogError(
                f"not a time of the endpoint's format (yyyy-MM-ddTHH:mm:ss.fffZ): {bound!r}"
            )
    return [
        r
        for r in records
        if (from_utc is None or r["Utc"] >= from_utc) and (to_utc is None or r["Utc"] <= to_utc)
    ]


# ---- identifiers ------------------------------------------------------------------------


def caller_identifiers(records: Iterable[dict[str, Any]]) -> set[str]:
    """The names the log itself holds in its ``Caller`` fields: each part of
    ``DOMAIN\\user``, and the part of a virtual account's name after its number."""
    found: set[str] = set()
    for record in records:
        caller = record.get("Caller")
        if not isinstance(caller, dict):
            continue
        for key in ("ConnectedUser", "RunAsUser"):
            value = caller.get(key)
            if not isinstance(value, str) or not value:
                continue
            for part in re.split(r"[\\/]", value):
                match = VA_NUMBER.match(part)
                if match:
                    found.add(match.group(2))
                elif part != "WinRM Virtual Users":
                    found.add(part)
    return found


def environment_identifiers(environ: dict[str, str] | None = None) -> set[str]:
    """The computer, user and domain names of the environment that runs the script."""
    environ = os.environ if environ is None else environ
    names = (
        environ.get(k, "") for k in ("COMPUTERNAME", "USERNAME", "USERDOMAIN", "HOSTNAME", "USER")
    )
    return {n for n in names if n}


def usable_identifiers(identifiers: Iterable[str]) -> list[str]:
    """The identifiers, longest first (so a name is replaced before a part of it); an
    identifier too short to replace safely is refused, never skipped."""
    result = set()
    for identifier in identifiers:
        name = identifier.strip()
        if not name:
            continue
        if len(name) < MIN_IDENTIFIER:
            raise LogError(
                f"an identifier shorter than {MIN_IDENTIFIER} characters cannot be replaced safely"
            )
        result.add(name)
    return sorted(result, key=lambda n: (-len(n), n.casefold()))


# ---- the copy ---------------------------------------------------------------------------


def _structural(text: str) -> bool:
    # a hash, a GUID or a time: a host name inside one of them is a coincidence of its
    # digits, so it is neither replaced (the hash would change) nor reported
    return bool(HASH.match(text) or GUID.match(text) or UTC.match(text))


def _replace(text: str, identifiers: list[str]) -> str:
    if _structural(text):
        return text
    for name in identifiers:
        text = re.sub(re.escape(name), IDENTIFIER, text, flags=re.IGNORECASE)
    return text


def _run_as(value: str) -> str:
    match = VA_NUMBER.search(value)
    return f"{VIRTUAL} VA {match.group(1)}" if match else ACCOUNT


def _anonymize_value(value: Any, identifiers: list[str]) -> Any:
    if isinstance(value, str):
        return _replace(value, identifiers)
    if isinstance(value, list):
        return [_anonymize_value(v, identifiers) for v in value]
    if isinstance(value, dict):
        return {
            _replace(k, identifiers): _anonymize_value(v, identifiers) for k, v in value.items()
        }
    return value


def anonymize(
    records: Iterable[dict[str, Any]], identifiers: Iterable[str]
) -> list[dict[str, Any]]:
    """The publishable copy of the records (see the module docstring)."""
    names = usable_identifiers(identifiers)
    copy = []
    for record in records:
        out = _anonymize_value(record, names)
        caller = record.get("Caller")
        if isinstance(caller, dict):
            out["Caller"] = {
                k: (
                    (OPERATOR if v else "")
                    if k == "ConnectedUser"
                    else (_run_as(v) if v else "")
                    if k == "RunAsUser"
                    else _anonymize_value(v, names)
                )
                for k, v in caller.items()
            }
        copy.append(out)
    return copy


# ---- the checker ------------------------------------------------------------------------


def _strings(value: Any, path: str = "") -> Iterable[tuple[str, str]]:
    if isinstance(value, str):
        yield path, value
    elif isinstance(value, list):
        for i, v in enumerate(value):
            yield from _strings(v, f"{path}[{i}]")
    elif isinstance(value, dict):
        for k, v in value.items():
            yield f"{path}.{k} (key)", k
            yield from _strings(v, f"{path}.{k}")


def _compare(source: Any, copy: Any, path: str, problems: list[str]) -> None:
    if isinstance(source, dict):
        if not isinstance(copy, dict) or len(copy) != len(source):
            problems.append(f"{path}: not the same object as the source")
            return
        for (sk, sv), (ck, cv) in zip(source.items(), copy.items(), strict=True):
            if sk != ck and IDENTIFIER not in ck:
                problems.append(f"{path}: key {ck!r} is not the source's key")
            _compare(sv, cv, f"{path}.{ck}", problems)
    elif isinstance(source, list):
        if not isinstance(copy, list) or len(copy) != len(source):
            problems.append(f"{path}: not the same list as the source")
            return
        for i, (s, c) in enumerate(zip(source, copy, strict=True)):
            _compare(s, c, f"{path}[{i}]", problems)
    elif isinstance(source, str):
        if not isinstance(copy, str):
            problems.append(f"{path}: not a text, as in the source")
        elif copy != source and IDENTIFIER not in copy and not path.startswith(".Caller."):
            problems.append(f"{path}: differs from the source")
    elif type(copy) is not type(source) or copy != source:
        problems.append(f"{path}: differs from the source")


def check(
    source: list[dict[str, Any]], copy: list[dict[str, Any]], identifiers: Iterable[str]
) -> list[str]:
    """The reasons to refuse the copy; an empty list means it may be published."""
    names = usable_identifiers(identifiers)
    problems: list[str] = []
    if len(copy) != len(source):
        return [f"the copy has {len(copy)} records, the source {len(source)}"]
    for number, (s, c) in enumerate(zip(source, copy, strict=True), start=1):
        record_problems: list[str] = []
        _compare(s, c, "", record_problems)
        caller = c.get("Caller") if isinstance(c, dict) else None
        if isinstance(caller, dict):
            connected = caller.get("ConnectedUser")
            if connected not in ("", OPERATOR):
                record_problems.append(".Caller.ConnectedUser: not a placeholder")
            run_as = caller.get("RunAsUser")
            if run_as != "" and not (isinstance(run_as, str) and RUN_AS_PLACEHOLDER.match(run_as)):
                record_problems.append(".Caller.RunAsUser: not a placeholder")
        for path, text in _strings(c):
            folded = text.casefold()
            if not _structural(text):
                for name in names:
                    if name.casefold() in folded:
                        record_problems.append(f"{path}: holds a host identifier")
            for what, pattern in LEAKS:
                if pattern.search(text):
                    record_problems.append(f"{path}: holds {what}")
        problems.extend(f"record {number}{p}" for p in record_problems)
    return problems


# ---- the command ------------------------------------------------------------------------


def dump(records: Iterable[dict[str, Any]]) -> bytes:
    return b"".join(
        json.dumps(r, ensure_ascii=False, separators=(",", ":")).encode("utf-8") + b"\n"
        for r in records
    )


def publish(
    source: Path,
    output: Path,
    identifiers: Iterable[str],
    from_utc: str | None = None,
    to_utc: str | None = None,
) -> dict[str, Any]:
    """Reads the source, makes the copy, checks it, and only then writes it to a new file."""
    if output.exists():
        raise LogError(f"{output} exists: the copy never overwrites")
    if output.resolve() == source.resolve():
        raise LogError("the copy cannot be the source")
    data = source.read_bytes()
    every = read_records(data)
    records = select(every, from_utc, to_utc)
    # the names the whole log holds, not only the selected records
    names = set(identifiers) | caller_identifiers(every)
    copy = anonymize(records, names)
    problems = check(records, copy, names)
    if problems:
        raise LogError("the copy is refused:\n" + "\n".join(problems))
    out = dump(copy)
    with output.open("xb") as handle:
        handle.write(out)
    return {
        "source_sha256": hashlib.sha256(data).hexdigest(),
        "records": len(copy),
        "copy_sha256": hashlib.sha256(out).hexdigest(),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--from-utc")
    parser.add_argument("--to-utc")
    parser.add_argument("--identifier", action="append", default=[])
    args = parser.parse_args(argv)
    try:
        result = publish(
            args.source,
            args.output,
            set(args.identifier) | environment_identifiers(),
            args.from_utc,
            args.to_utc,
        )
    except (LogError, OSError) as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 1
    print(f"source SHA-256 {result['source_sha256']}")
    print(f"records {result['records']}")
    print(f"copy SHA-256 {result['copy_sha256']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
