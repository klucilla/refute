"""The observation hook of coverage route (b) (docs/validation/v0.3/wp3-acceptance.md, 1.5a,
W3.12c).

The hook is observation only. ``Observer(sink).wrap(function, name)`` returns a wrapper
that calls ``function`` with exactly the arguments it received (the same objects,
untouched before the call) and returns exactly the object ``function`` returned, or lets
exactly the exception it raised propagate. Only after the call it records one event, and
only through operations whose code is Python's own or numpy's compiled code:

- **Types are compared with ``is`` only,** never with ``==`` or ``in``, so no
  ``__eq__`` of a class or metaclass runs.
- **The labels** (the first argument, ``y_true`` in scikit-learn's metric functions) are
  read only when their type is exactly ``list`` or ``tuple`` with every element exactly
  ``int`` or ``str``, or exactly numpy's own ``ndarray``.
- **A numpy type is trusted only when it is the compiled type** held by the numpy module
  the program already imported. That module must be an exact ``ModuleType``; its type is
  read from the module's ``__dict__``, its metaclass must be exactly ``type``, and it
  must not be a heap type (a class written in Python is one). So a class that merely
  calls itself ``numpy.ndarray`` is never trusted, and none of its methods run. The hook
  never imports numpy, since importing it early could change the program.
- **The result** is recorded only when its type is exactly ``int`` or ``float``, or a
  trusted numpy number. Otherwise nothing of it is read.
- **Failures** are recorded with fixed messages; the hook never formats an unknown
  object or exception.

**Records.**
- Each call gets a unique sequence number (allocated under a lock) and writes an event,
  or a failure record, and then a commit record.
- ``Observer.finish()`` (registered with ``atexit`` by the installation) waits until no
  call is in progress, then writes a final record. It holds the number of calls, whether
  any failure happened (a sink that raised included), and the SHA-256 of every record
  written before it (``record_line``; the digest and the write happen in one locked
  step).
- **The log is judged by its content, not by whether the sink returned.** A sink that
  raises after writing the final record leaves a complete log that matches its digest. A
  log written in part, reordered or edited does not match it.
- ``committed_events``, used by the gate, accepts the events only when:
  - every record has exactly the form and the types the hook writes;
  - the sequence numbers are 1 to n, without repeats;
  - each event comes before its commit record, and there is no failure record;
  - the final record is the last one, says ``failed: false``, counts the calls and
    matches the digest of the records before it.

  Anything else, an absent or malformed final record included, is a failure, and the
  gate is then ``INCONCLUSIVE``.

**Interrupts.** A ``BaseException`` that is not an ``Exception`` (``KeyboardInterrupt``,
``SystemExit``) raised while the hook does its own work is not swallowed: it is an
interruption of the run, not a fault of the hook. The observed call has already
returned, and nothing it returned is changed. Without the final record, the gate is
``INCONCLUSIVE``.

This module uses the standard library only, because it runs in the paper's container,
where Refute is not installed. Its labels hash is the canonical form of
``refute.core.canonical`` for lists of integers and strings, which tests check. A claim
installs it through an allowed patch, fixed and hashed before the lock (W3.12b).
"""

from __future__ import annotations

import functools
import hashlib
import json
import sys
import threading
import types
import unicodedata
from collections.abc import Callable
from typing import Any

HOOK_FAILURE = "hook_failure"
COMMITTED = "committed"
FINAL = "final"
_HEAPTYPE = 1 << 9  # Py_TPFLAGS_HEAPTYPE: a class created at run time, in Python
_EVENT_FIELDS = {"seq", "function", "call_site", "n_examples", "labels_sha256"}


class _RefusedError(Exception):
    """A failure of the hook's own reading, with a fixed message."""


def _trusted_numpy(*names: str) -> tuple[type, ...]:
    """numpy's compiled types of these names, from the numpy module the program already
    imported; none when numpy is absent or does not look like the real module."""
    module = sys.modules.get("numpy")
    if type(module) is not types.ModuleType:
        return ()
    found = []
    for name in names:
        kind = module.__dict__.get(name)
        if type(kind) is type and not (kind.__flags__ & _HEAPTYPE):
            found.append(kind)
    return tuple(found)


def _exact(value: Any, kinds: tuple[type, ...]) -> bool:
    kind = type(value)
    return any(kind is k for k in kinds)


def _labels(y_true: Any) -> list[int | str]:
    kind = type(y_true)
    if kind is list or kind is tuple:
        values = list(y_true)  # the interpreter's own iteration of an exact list or tuple
    elif _exact(y_true, _trusted_numpy("ndarray")):
        # numpy's compiled attribute and method of its own ndarray; only a 1-D array gives
        # a list (a 0-d array of dtype object would give back the object it holds)
        if y_true.ndim != 1:
            raise _RefusedError("labels in an array that is not one-dimensional")
        values = y_true.tolist()
        if type(values) is not list:
            raise _RefusedError("labels that numpy did not return as a list")
    else:
        raise _RefusedError("labels of an unread type")
    for v in values:
        vk = type(v)
        if not (vk is int or vk is str):
            raise _RefusedError("a label that is not an int or a str")
    return values


def _canonical_labels(labels: list[int | str]) -> bytes:
    """The canonical JSON of a list of labels (refute.core.canonical, for int and str)."""
    values = [unicodedata.normalize("NFC", v) if type(v) is str else v for v in labels]
    text = json.dumps(
        values, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    )
    return text.encode("utf-8")


_NUMPY_NUMBERS = (
    "float16", "float32", "float64", "longdouble",
    "int8", "int16", "int32", "int64", "uint8", "uint16", "uint32", "uint64",
)  # fmt: skip


def _result(result: Any) -> dict[str, str]:
    if _exact(result, _trusted_numpy(*_NUMPY_NUMBERS)):
        result = result.item()  # numpy's compiled method of its own scalar
    kind = type(result)
    if kind is int:
        return {"result": int.__repr__(result)}
    if kind is float:
        return {"result": float.__repr__(result)}
    return {"result": "unread"}


def record_line(record: dict[str, Any]) -> bytes:
    """The bytes of one record in the running digest: compact JSON with sorted keys, then
    a newline. The gate recomputes it from the records it parsed back."""
    text = json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return text.encode("utf-8") + b"\n"


class Observer:
    """Observes calls of metric functions and writes their records to ``sink``."""

    def __init__(self, sink: Callable[[dict[str, Any]], None]) -> None:
        self._sink = sink
        self._lock = threading.Condition()
        self._next = 0
        self._failed = False
        self._active = 0
        self._digest = hashlib.sha256()

    def _seq(self) -> int:
        with self._lock:
            self._next += 1
            self._active += 1
            return self._next

    def _done(self, failed: bool) -> None:
        with self._lock:
            self._failed = self._failed or failed
            self._active -= 1
            self._lock.notify_all()

    def _write(self, record: dict[str, Any]) -> None:
        # the digest and the sink in one locked step, so the digest follows the order of
        # the log; a record the sink failed to write is in the digest, not in the log,
        # and the final record then does not match
        with self._lock:
            self._digest.update(record_line(record))
            self._sink(record)

    def wrap(self, function: Callable[..., Any], name: str) -> Callable[..., Any]:
        """The observation-only wrapper of ``function``, recorded under its declared
        public ``name``, which the gate compares with the claim's function."""

        def wrapper(*args: Any, **kwargs: Any) -> Any:
            result = function(*args, **kwargs)
            self._observe(name, args, kwargs, result)
            return result

        try:
            return functools.wraps(function)(wrapper)
        except Exception:  # noqa: BLE001 - metadata that cannot be copied never stops it
            return wrapper

    def _observe(self, name: str, args: tuple, kwargs: dict, result: Any) -> None:
        seq = self._seq()
        failed = True
        try:
            try:
                frame = sys._getframe(2)
                labels = _labels(args[0] if args else kwargs.get("y_true"))
                record: dict[str, Any] = {
                    "seq": seq,
                    "function": name,
                    "call_site": {"file": frame.f_code.co_filename, "line": frame.f_lineno},
                    "n_examples": len(labels),  # an exact list, checked above
                    "labels_sha256": hashlib.sha256(_canonical_labels(labels)).hexdigest(),
                    **_result(result),
                }
                failed = False
            except _RefusedError as exc:
                record = {"seq": seq, HOOK_FAILURE: exc.args[0]}
            except Exception:  # noqa: BLE001 - never formatted: its __str__ is unknown code
                record = {"seq": seq, HOOK_FAILURE: "the hook could not read the call"}
            try:
                self._write(record)
                self._write({COMMITTED: seq})
            except Exception:  # noqa: BLE001 - recorded by the final record, never formatted
                failed = True
        finally:
            self._done(failed)

    def finish(self) -> None:
        """The final record, written once every call in progress has ended: the number of
        calls, whether anything failed, and the SHA-256 of every record written before it
        (``record_line``), so the gate checks the log by its content. A sink failure after
        the final record was written leaves a complete, verifiable log; a log the sink
        wrote only in part does not match the digest."""
        with self._lock:
            while self._active:
                self._lock.wait()
            final = {
                FINAL: {
                    "calls": self._next,
                    "failed": self._failed,
                    "records_sha256": self._digest.hexdigest(),
                }
            }
        try:
            self._sink(final)
        except Exception:  # noqa: BLE001,S110 - judged by content: no or bad final, INCONCLUSIVE
            pass


_HEX64 = frozenset("0123456789abcdef")


def _hex64(value: Any) -> bool:
    return type(value) is str and len(value) == 64 and set(value) <= _HEX64


def _valid_event(record: dict[str, Any]) -> bool:
    """An event exactly as the hook writes it: the fixed fields, of the right types."""
    if set(record) != _EVENT_FIELDS | {"result"}:
        return False
    site = record["call_site"]
    return (
        type(record["function"]) is str
        and record["function"] != ""
        and type(site) is dict
        and set(site) == {"file", "line"}
        and type(site["file"]) is str
        and type(site["line"]) is int
        and site["line"] >= 0
        and type(record["n_examples"]) is int
        and record["n_examples"] >= 0
        and _hex64(record["labels_sha256"])
        and type(record["result"]) is str
    )


def committed_events(records: list[Any]) -> tuple[list[dict[str, Any]], list[str]]:
    """The events the gate may count, and every failure (the gate is INCONCLUSIVE when
    the failures are not empty). Accepted only when: every record has exactly the form
    the hook writes; sequence numbers are 1, 2, 3, ... with no repeat; each event or
    failure record comes before its commit record; no failure record; and the last
    record is a final record that counts the calls, says no failure and holds the SHA-256
    of every record before it."""
    failures: list[str] = []
    events: dict[int, dict[str, Any]] = {}
    pending: set[int] = set()
    seen: set[int] = set()
    committed: set[int] = set()
    digest = hashlib.sha256()
    final_index = None
    for i, record in enumerate(records):
        if final_index is not None:
            failures.append(f"record {i} after the final record")
            continue
        if type(record) is not dict:
            failures.append(f"record {i} is not an object")
            continue
        if set(record) == {FINAL}:
            final_index = i
            continue
        digest.update(record_line(record))
        if set(record) == {COMMITTED}:
            seq = record[COMMITTED]
            if type(seq) is not int or seq not in pending:
                failures.append(f"record {i}: a commit record without its event before it")
            else:
                pending.discard(seq)
                committed.add(seq)
            continue
        seq = record.get("seq")
        if type(seq) is not int or seq < 1 or seq in seen:
            failures.append(f"record {i}: a sequence number repeated or malformed")
            continue
        seen.add(seq)
        if set(record) == {"seq", HOOK_FAILURE} and type(record[HOOK_FAILURE]) is str:
            failures.append(f"hook failure {seq}: {record[HOOK_FAILURE]}")
            pending.add(seq)
        elif _valid_event(record):
            events[seq] = record
            pending.add(seq)
        else:
            failures.append(f"record {i}: not an event as the hook writes it")
    for seq in sorted(pending):
        failures.append(f"event {seq} without its commit record")
    if seen and seen != set(range(1, max(seen) + 1)):
        failures.append("the sequence numbers are not 1 to n")
    if final_index is None:
        failures.append("no final record")
    else:
        final = records[final_index][FINAL]
        want = {"calls": len(seen), "failed": False, "records_sha256": digest.hexdigest()}
        if type(final) is not dict or set(final) != set(want):
            failures.append("the final record is malformed")
        elif not (
            type(final["calls"]) is int
            and type(final["failed"]) is bool
            and _hex64(final["records_sha256"])
        ):
            failures.append("the final record is malformed")
        elif final != want:
            same = final["records_sha256"] == want["records_sha256"]
            failures.append(
                "the final record does not match the log: "
                f"calls {final['calls']}, failed {final['failed']}, "
                f"digest {'equal' if same else 'different'}"
            )
    if failures:
        return [], failures
    return [events[s] for s in sorted(events)], failures
