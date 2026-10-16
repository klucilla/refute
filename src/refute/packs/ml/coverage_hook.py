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
- ``Observer.finish()`` (registered with ``atexit`` by the installation) writes a final
  record. It holds the number of calls and whether any failure happened, including a
  sink that raised after it had written.
- ``committed_events``, used by the gate, accepts the events only when:
  - every record is well formed;
  - no sequence number repeats;
  - every event has its commit record and no failure record;
  - the final record is the last one, says ``failed: false``, and counts the calls seen.

  Anything else is a failure, and the gate is then ``INCONCLUSIVE``.

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
        values = y_true.tolist()  # numpy's compiled method of its own ndarray
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


class Observer:
    """Observes calls of metric functions and writes their records to ``sink``."""

    def __init__(self, sink: Callable[[dict[str, Any]], None]) -> None:
        self._sink = sink
        self._lock = threading.Lock()
        self._next = 0
        self._failed = False

    def _seq(self) -> int:
        with self._lock:
            self._next += 1
            return self._next

    def _fail(self) -> None:
        with self._lock:
            self._failed = True

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
        try:
            frame = sys._getframe(2)
            labels = _labels(args[0] if args else kwargs.get("y_true"))
            record: dict[str, Any] = {
                "seq": seq,
                "function": name,
                "call_site": {"file": frame.f_code.co_filename, "line": frame.f_lineno},
                "n_examples": len(labels),
                "labels_sha256": hashlib.sha256(_canonical_labels(labels)).hexdigest(),
                **_result(result),
            }
        except _RefusedError as exc:
            self._fail()
            record = {"seq": seq, HOOK_FAILURE: exc.args[0]}
        except Exception:  # noqa: BLE001 - never formatted: its __str__ is unknown code
            self._fail()
            record = {"seq": seq, HOOK_FAILURE: "the hook could not read the call"}
        try:
            self._sink(record)
            self._sink({COMMITTED: seq})
        except Exception:  # noqa: BLE001 - recorded by the final record, never formatted
            self._fail()

    def finish(self) -> None:
        """The final record: how many calls were observed and whether anything failed."""
        with self._lock:
            final = {FINAL: {"calls": self._next, "failed": self._failed}}
        try:
            self._sink(final)
        except Exception:  # noqa: BLE001,S110 - no final record: the gate is INCONCLUSIVE
            pass


def committed_events(records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    """The events the gate may count, and every failure (the gate is INCONCLUSIVE when
    the failures are not empty)."""
    failures: list[str] = []
    events: dict[int, dict[str, Any]] = {}
    failed: set[int] = set()
    committed: set[int] = set()
    seen: set[int] = set()
    final: dict[str, Any] | None = None
    for i, record in enumerate(records):
        if final is not None:
            failures.append(f"record {i} after the final record")
            continue
        if not isinstance(record, dict):
            failures.append(f"record {i} is not an object")
            continue
        if set(record) == {FINAL}:
            final = record[FINAL]
            continue
        if set(record) == {COMMITTED}:
            seq = record[COMMITTED]
            if type(seq) is not int or seq in committed:
                failures.append(f"record {i}: a commit record repeated or malformed")
            else:
                committed.add(seq)
            continue
        seq = record.get("seq")
        if type(seq) is not int or seq in seen:
            failures.append(f"record {i}: a sequence number repeated or malformed")
            continue
        seen.add(seq)
        if HOOK_FAILURE in record:
            failed.add(seq)
            failures.append(f"hook failure {seq}: {record[HOOK_FAILURE]}")
        elif not _EVENT_FIELDS <= set(record):
            failures.append(f"event {seq} is incomplete")
        else:
            events[seq] = record
    for seq in sorted(set(events) - committed):
        failures.append(f"event {seq} without its commit record")
    for seq in sorted(committed - seen):
        failures.append(f"a commit record with no event: {seq}")
    if final is None:
        failures.append("no final record")
    elif final != {"calls": len(seen), "failed": False}:
        failures.append(f"the final record reports {final}")
    accepted = [events[s] for s in sorted(events) if s in committed and s not in failed]
    return (accepted if not failures else []), failures
