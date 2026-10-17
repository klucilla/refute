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
- in every other text and key, each host identifier becomes ``<host-identifier>``,
  compared without regard to case, in one pass (longest name first). The identifiers are
  those given with ``--identifier``, the computer, user and domain names of the
  environment that runs the script, and the names read from the ``Caller`` fields of the
  whole log: each part of ``DOMAIN\\user``, the part of a virtual account's name after its
  number, that part without the connecting user's name at its end, and its parts between
  underscores. A text shaped as a hash, a GUID or a time is never changed.

Everything else is kept as it is, including ``PlanSha256``: the hash of the plan in the
local log, which the anonymized plan of the copy no longer has when a text in it changed.

The checker (``check``) must pass before the copy is written. Its reasons are its own: it
does not trust the copy to have been made by ``anonymize``.

- **Same records.** The copy has the source's records, in order, with the same keys, list
  lengths, numbers, booleans and nulls. A text (or a key) of the copy differs from the
  source's only where the source held a host identifier: with each ``<host-identifier>`` of
  the copy put back as one of the identifiers, the source's text must match exactly. The
  two ``Caller`` fields are the exception, checked next.
- **Placeholders.** Each ``Caller`` field is the placeholder its source value calls for:
  the operator for a connecting account, the virtual account with the same number, the
  account of a call outside a remote session, or ``""`` for an empty value.
- **Module.** ``Module`` maps file names of the module to SHA-256 hashes, nothing else.
- **Nothing of the host.** With the placeholders masked, no text or key holds a host
  identifier (except a typed field: a ``...Sha256`` hash, a GUID of ``OperationId``,
  ``VmId``, ``RecordedVmId``, ``ServiceGuid`` or ``Id``, the ``Utc`` time, or a ``Module``
  hash, where a name would be a coincidence of digits), a Windows path outside the allowed
  roots (``C:\\Hyper-V``, ``C:\\ProgramData\\RefuteVm`` and the project folder, unless
  others are given; with either separator, every drive path in a text must start with a
  root, and no ``..`` step is accepted), a user profile or UNC path, an IPv4 or IPv6
  address, a MAC address, an e-mail address, a local host name (``.internal``,
  ``.local``, ``.lan``, ``.home``, ``.corp``, ``.localdomain``, ``.intranet``) or an
  account SID with three or more sub-authorities.

**What it cannot see:** a name it does not know and that matches no pattern (for example a
switch name chosen on the host). The maintainer still reads the copy before it is
published. A pattern can also refuse a text that is no host value (a four-part version
number reads as an IPv4 address): the copy is then refused, and the record is published by
hand, never by loosening the checker.

Usage (Python from the project's virtual environment)::

    .venv/Scripts/python.exe scripts/vm/publish_operation_log.py
        --source C:/ProgramData/RefuteVm/Log/operations.jsonl
        --output <new file> [--from-utc <time>] [--to-utc <time>] [--identifier <name> ...]
        [--allowed-root <folder> ...]

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
PLACEHOLDERS = (OPERATOR, VIRTUAL, ACCOUNT, IDENTIFIER)
# the shortest identifier the copy replaces: a shorter one would match inside ordinary words
MIN_IDENTIFIER = 3
ALLOWED_ROOTS = ("C:\\Hyper-V", "C:\\ProgramData\\RefuteVm", "C:\\Projetos\\refute")

UTC = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$")
HASH = re.compile(r"^[0-9a-f]{64}$")
GUID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
# a text of this shape is never changed by the copy
SHAPED = re.compile(r"(?i)^(?:[0-9a-f]{32,}|[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12})$")
GUID_KEYS = frozenset({"OperationId", "VmId", "RecordedVmId", "ServiceGuid", "Id"})
MODULE_FILE = re.compile(
    r"^[A-Za-z][A-Za-z0-9.]*(?:/[A-Za-z][A-Za-z0-9.]*)*\.(?:ps1|psm1|psd1|psrc)$"
)
VA_NUMBER = re.compile(r"WinRM VA_(\d+)_(.+)$")
RUN_AS_PLACEHOLDER = re.compile(r"^(?:<virtual-account> VA \d+|<account>)$")
# where a drive path starts, and a ".." step in a path (in a text whose "/" became "\")
DRIVE = re.compile(r"(?i)\b[a-z]:\\")
DOTDOT = re.compile(r"(?:^|\\|(?<=[\s'\"]))\.\.(?=$|[\\\s'\"])")
# what may follow an allowed root: a separator, or a character no folder name can hold
# (a space, a comma, a parenthesis or a single quote can be part of a sibling folder's
# name, Codex review of #154; the masked placeholder is "\0")
PATH_END = '\\"<>|\0'

LEAKS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("a user profile path", re.compile(r"(?i)\b[a-z]:[\\/]+users[\\/]")),
    # \\host\share, //host/share and their mixtures (Codex review of #154); a URL's "//host/"
    # is refused as well, since it names a host
    ("a UNC path or a URL", re.compile(r"[\\/]{2}[^\\/\s]+[\\/]")),
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
    (
        "a local host name",
        re.compile(
            r"(?i)\b[a-z0-9-]+(?:\.[a-z0-9-]+)*\.(?:internal|local|lan|home|corp|localdomain|intranet)\b"
        ),
    ),
    ("an account SID", re.compile(r"(?i)\bS-1-\d+(?:-\d+){3,}")),
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
    """The names the log itself holds in its ``Caller`` fields (see the module docstring)."""
    found: set[str] = set()
    for record in records:
        caller = record.get("Caller")
        if not isinstance(caller, dict):
            continue
        users: list[str] = []
        rests: list[str] = []
        for key in ("ConnectedUser", "RunAsUser"):
            value = caller.get(key)
            if not isinstance(value, str) or not value:
                continue
            parts = [p for p in re.split(r"[\\/]", value) if p]
            for part in parts:
                match = VA_NUMBER.match(part)
                if match:
                    rests.append(match.group(2))
                elif part != "WinRM Virtual Users":
                    found.add(part)
            if key == "ConnectedUser" and parts:
                users.append(parts[-1])
        for rest in rests:
            found.add(rest)
            for user in users:
                # "<host or domain>_<user>": the host or domain alone, too
                if rest.casefold().endswith("_" + user.casefold()):
                    found.add(rest[: -len(user) - 1])
            found.update(p for p in rest.split("_") if len(p) >= MIN_IDENTIFIER)
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


def _alternation(names: list[str]) -> str:
    return "|".join(re.escape(n) for n in names)


# ---- the copy ---------------------------------------------------------------------------


def _replacer(names: list[str]):
    if not names:
        return lambda text: text
    pattern = re.compile(_alternation(names), re.IGNORECASE)

    def replace(text: str) -> str:
        if SHAPED.match(text) or UTC.match(text):
            return text
        return pattern.sub(IDENTIFIER, text)

    return replace


def _run_as(value: str) -> str:
    match = VA_NUMBER.search(value)
    return f"{VIRTUAL} VA {match.group(1)}" if match else ACCOUNT


def _anonymize_value(value: Any, replace) -> Any:
    if isinstance(value, str):
        return replace(value)
    if isinstance(value, list):
        return [_anonymize_value(v, replace) for v in value]
    if isinstance(value, dict):
        return {replace(k): _anonymize_value(v, replace) for k, v in value.items()}
    return value


def anonymize(
    records: Iterable[dict[str, Any]], identifiers: Iterable[str]
) -> list[dict[str, Any]]:
    """The publishable copy of the records (see the module docstring)."""
    replace = _replacer(usable_identifiers(identifiers))
    copy = []
    for record in records:
        out = _anonymize_value(record, replace)
        caller = record.get("Caller")
        if isinstance(caller, dict):
            fields = dict(out["Caller"])
            if isinstance(caller.get("ConnectedUser"), str):
                fields["ConnectedUser"] = OPERATOR if caller["ConnectedUser"] else ""
            if isinstance(caller.get("RunAsUser"), str):
                fields["RunAsUser"] = _run_as(caller["RunAsUser"]) if caller["RunAsUser"] else ""
            out["Caller"] = fields
        copy.append(out)
    return copy


# ---- the checker ------------------------------------------------------------------------


def _typed(path: tuple, text: str) -> bool:
    """A text whose key says it is a hash, a GUID or a time, and which has that shape."""
    key = path[-1] if path else None
    if path[:1] == ("Module",) and len(path) == 2:
        return bool(HASH.match(text))
    if isinstance(key, str) and key.endswith("Sha256"):
        return bool(HASH.match(text))
    if key in GUID_KEYS:
        return bool(GUID.match(text))
    if key == "Utc":
        return bool(UTC.match(text))
    return False


def _render(path: tuple) -> str:
    return "".join(f"[{p}]" if isinstance(p, int) else f".{p}" for p in path)


def _strings(value: Any, path: tuple = ()) -> Iterable[tuple[tuple, str, bool]]:
    """Every text of a record with its path, and whether it is a key."""
    if isinstance(value, str):
        yield path, value, False
    elif isinstance(value, list):
        for i, v in enumerate(value):
            yield from _strings(v, (*path, i))
    elif isinstance(value, dict):
        for k, v in value.items():
            yield (*path, k), k, True
            yield from _strings(v, (*path, k))


def _substituted(source: str, copy: str, alternation: str) -> bool:
    """Whether copy is source with some host identifiers replaced, and nothing else."""
    segments = copy.split(IDENTIFIER)
    if len(segments) == 1 or not alternation:
        return False
    pattern = f"(?i:{alternation})".join(re.escape(s) for s in segments)
    return re.fullmatch(pattern, source) is not None


def _compare(source: Any, copy: Any, path: tuple, alternation: str, problems: list[str]) -> None:
    where = _render(path) or "the record"
    if isinstance(source, dict):
        if not isinstance(copy, dict) or len(copy) != len(source):
            problems.append(f"{where}: not the same object as the source")
            return
        for (sk, sv), (ck, cv) in zip(source.items(), copy.items(), strict=True):
            if sk != ck and not _substituted(sk, ck, alternation):
                problems.append(f"{where}: key {ck!r} is not the source's key")
            _compare(sv, cv, (*path, sk), alternation, problems)
    elif isinstance(source, list):
        if not isinstance(copy, list) or len(copy) != len(source):
            problems.append(f"{where}: not the same list as the source")
            return
        for i, (s, c) in enumerate(zip(source, copy, strict=True)):
            _compare(s, c, (*path, i), alternation, problems)
    elif isinstance(source, str):
        if not isinstance(copy, str):
            problems.append(f"{where}: not a text, as in the source")
        elif copy == source or path in (("Caller", "ConnectedUser"), ("Caller", "RunAsUser")):
            return
        elif not _substituted(source, copy, alternation):
            problems.append(f"{where}: differs from the source beyond the replaced names")
    elif type(copy) is not type(source) or copy != source:
        problems.append(f"{where}: differs from the source")


def _outside_roots(text: str, roots: tuple[str, ...]) -> list[str]:
    """Why the paths of a text are not below an allowed root, conservatively (Codex review of
    #154): where a path ends in free text is ambiguous (names hold spaces), so no path is cut
    out of the text. Instead, wherever a drive path starts (``X:\\`` or ``X:/``), the text
    from there must start with an allowed root, followed by a separator or by a character
    that ends a path; and no text may hold a ``..`` step in a path, which could leave a root
    whatever follows it."""
    allowed = [r.replace("/", "\\").rstrip("\\").casefold() for r in roots]
    norm = text.replace("/", "\\").casefold()
    found = []
    if DOTDOT.search(norm):
        found.append("a '..' step")
    for match in DRIVE.finditer(norm):
        rest = norm[match.start() :]
        inside = False
        for root in allowed:
            if rest.startswith(root):
                after = rest[len(root) :]
                inside = inside or not after or after[0] in PATH_END
        if not inside:
            found.append("a drive path")
    return found


def _caller_problems(source: Any, copy: Any) -> list[str]:
    """Each Caller field of the copy is the placeholder its source value calls for: the
    operator for a connecting account, the virtual account with the same number, or the
    account of a call outside a remote session; an empty value stays empty (Codex review of
    #154: the format alone let VA 31 become VA 999)."""
    problems = []
    if not isinstance(copy, dict):
        return problems
    if "ConnectedUser" in copy:
        value = source.get("ConnectedUser") if isinstance(source, dict) else None
        expected = (OPERATOR if value else "") if isinstance(value, str) else None
        if copy["ConnectedUser"] != expected:
            problems.append(".Caller.ConnectedUser: not the placeholder of the source's value")
    if "RunAsUser" in copy:
        value = source.get("RunAsUser") if isinstance(source, dict) else None
        expected = None
        if isinstance(value, str):
            number = VA_NUMBER.search(value)
            expected = "" if not value else f"{VIRTUAL} VA {number.group(1)}" if number else ACCOUNT
        if copy["RunAsUser"] != expected:
            problems.append(".Caller.RunAsUser: not the placeholder of the source's value")
    return problems


def _mask(text: str) -> str:
    for placeholder in PLACEHOLDERS:
        text = text.replace(placeholder, "\0")
    return text


def check(
    source: list[dict[str, Any]],
    copy: list[dict[str, Any]],
    identifiers: Iterable[str],
    roots: Iterable[str] = ALLOWED_ROOTS,
) -> list[str]:
    """The reasons to refuse the copy; an empty list means it may be published."""
    names = usable_identifiers(identifiers)
    alternation = _alternation(names)
    allowed = tuple(roots)
    if len(copy) != len(source):
        return [f"the copy has {len(copy)} records, the source {len(source)}"]
    problems: list[str] = []
    for number, (s, c) in enumerate(zip(source, copy, strict=True), start=1):
        found: list[str] = []
        _compare(s, c, (), alternation, found)
        caller = c.get("Caller") if isinstance(c, dict) else None
        if isinstance(caller, dict):
            if caller.get("ConnectedUser") not in ("", OPERATOR):
                found.append(".Caller.ConnectedUser: not a placeholder")
            run_as = caller.get("RunAsUser")
            if run_as != "" and not (isinstance(run_as, str) and RUN_AS_PLACEHOLDER.match(run_as)):
                found.append(".Caller.RunAsUser: not a placeholder")
            found.extend(_caller_problems(s.get("Caller") if isinstance(s, dict) else None, caller))
        module = c.get("Module") if isinstance(c, dict) else None
        if module is not None and not (
            isinstance(module, dict)
            and all(
                isinstance(k, str) and MODULE_FILE.match(k) and isinstance(v, str) and HASH.match(v)
                for k, v in module.items()
            )
        ):
            found.append(".Module: not file names of the module with their SHA-256")
        for path, text, is_key in _strings(c):
            where = _render(path) + (" (key)" if is_key else "")
            masked = _mask(text)
            if is_key or not _typed(path, text):
                folded = masked.casefold()
                if any(name.casefold() in folded for name in names):
                    found.append(f"{where}: holds a host identifier")
            for outside in _outside_roots(masked, allowed):
                found.append(f"{where}: holds a path outside the allowed roots ({outside})")
            for what, pattern in LEAKS:
                if pattern.search(masked):
                    found.append(f"{where}: holds {what}")
        problems.extend(
            f"record {number}{p}" if p.startswith(".") else f"record {number}: {p}" for p in found
        )
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
    roots: Iterable[str] = ALLOWED_ROOTS,
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
    problems = check(records, copy, names, roots)
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
    parser.add_argument("--allowed-root", action="append", default=[])
    args = parser.parse_args(argv)
    try:
        result = publish(
            args.source,
            args.output,
            set(args.identifier) | environment_identifiers(),
            args.from_utc,
            args.to_utc,
            tuple(args.allowed_root) or ALLOWED_ROOTS,
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
