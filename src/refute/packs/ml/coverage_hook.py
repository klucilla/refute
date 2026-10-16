"""The observation hook of coverage route (b) (docs/validation/v0.3/wp3-acceptance.md, 1.5a,
W3.12c).

The hook is observation only. ``observe(function, sink, name)`` returns a wrapper that
calls ``function`` with exactly the arguments it received (the same objects, untouched
before the call) and returns exactly the object ``function`` returned, or lets exactly
the exception it raised propagate. Only after the call, and only through operations
whose code is known, it records one event:

- **what it reads:** the first argument (``y_true`` in scikit-learn's metric functions)
  is read only when its type is exactly ``list`` or ``tuple`` of ``int`` or ``str``, or
  exactly ``numpy.ndarray`` (read by numpy's own ``tolist``). The type is tested with
  ``type()`` alone, so no attribute, ``__iter__`` or ``__len__`` of an unknown object
  runs. Any other argument gives a failure record and is not touched;
- **the result:** its value is recorded only when its type is exactly ``int``,
  ``float``, or a numpy floating or integer scalar. Otherwise only its type name is
  recorded, and its ``__repr__`` never runs;
- **the event:** the public name declared at installation (``name``, for example
  ``sklearn.metrics.accuracy_score``, which the gate compares with the claim), the call
  site, the number of examples, and the SHA-256 of the labels in Refute's canonical JSON
  form.

**Commit protocol.** Each event carries a sequence number. After the sink has accepted
the event, a second record ``{"committed": n}`` follows it. ``committed_events``, which the
gate uses, keeps only events whose commit record follows them, and reports every other
record (an event the sink wrote but failed on, a failure record) as a failure. A failure
of the hook's own work is recorded when it can be, and never changes the call. The gate
counts any failure, or a missing or extra event, as ``INCONCLUSIVE``.

**Interrupts.** A ``BaseException`` that is not an ``Exception`` (``KeyboardInterrupt``,
``SystemExit``) raised while the hook does its own work is not swallowed: it is an
interruption of the run, not a fault of the hook. The run then ends as interrupted. The
observed call has already returned, and nothing it returned is changed.

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
import unicodedata
from collections.abc import Callable
from typing import Any

HOOK_FAILURE = "hook_failure"
COMMITTED = "committed"


def _numpy_type(value: Any, names: tuple[str, ...]) -> bool:
    """Whether the exact type of ``value`` is one of numpy's named types (no import of
    numpy, no attribute of ``value`` read)."""
    kind = type(value)
    return kind.__module__ == "numpy" and kind.__name__ in names


def _labels(y_true: Any) -> list[int | str]:
    """The labels, read only from exact known types; any other argument is refused
    without running any of its code."""
    if type(y_true) in (list, tuple):
        values = list(y_true)  # list and tuple iteration is the interpreter's own code
    elif _numpy_type(y_true, ("ndarray",)):
        values = y_true.tolist()  # numpy's own method; the exact type is ndarray
    else:
        raise TypeError(f"labels of type {type(y_true).__qualname__} are not read")
    for v in values:
        if type(v) not in (int, str):
            raise TypeError(f"a label of type {type(v).__qualname__} is not an int or a str")
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


def _result(result: Any) -> dict[str, Any]:
    """The returned value when its exact type is a known number; its type name otherwise."""
    if _numpy_type(result, _NUMPY_NUMBERS):
        result = result.item()  # numpy's own method; the exact type is a numpy scalar
    if type(result) is int:
        return {"result": int.__repr__(result)}
    if type(result) is float:
        return {"result": float.__repr__(result)}
    return {"result_type": type(result).__qualname__}


def observe(
    function: Callable[..., Any], sink: Callable[[dict[str, Any]], None], name: str
) -> Callable[..., Any]:
    """The observation-only wrapper of ``function``, recorded under its declared public
    ``name``; ``sink`` receives one event and its commit record per call."""
    state = {"seq": 0}

    def wrapper(*args: Any, **kwargs: Any) -> Any:
        result = function(*args, **kwargs)
        try:
            state["seq"] += 1
            seq = state["seq"]
            try:
                frame = sys._getframe(1)
                labels = _labels(args[0] if args else kwargs.get("y_true"))
                record: dict[str, Any] = {
                    "seq": seq,
                    "function": name,
                    "call_site": {"file": frame.f_code.co_filename, "line": frame.f_lineno},
                    "n_examples": len(labels),
                    "labels_sha256": hashlib.sha256(_canonical_labels(labels)).hexdigest(),
                    **_result(result),
                }
            except Exception as exc:  # noqa: BLE001 - the hook's own failure is recorded
                record = {"seq": seq, HOOK_FAILURE: f"{type(exc).__name__}: {exc}"}
            sink(record)
            sink({COMMITTED: seq})
        except Exception:  # noqa: BLE001,S110 - a failing sink: no commit record, INCONCLUSIVE
            pass
        return result

    try:
        return functools.wraps(function)(wrapper)
    except Exception:  # noqa: BLE001 - metadata that cannot be copied never stops the call
        return wrapper


def committed_events(records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    """The events whose commit record follows them, and every failure: an event without
    its commit, a failure record, or a commit with no event. The gate is INCONCLUSIVE
    when the failures are not empty."""
    events: list[dict[str, Any]] = []
    failures: list[str] = []
    pending: dict[int, dict[str, Any]] = {}
    for record in records:
        if COMMITTED in record:
            seq = record[COMMITTED]
            event = pending.pop(seq, None)
            if event is None:
                failures.append(f"a commit record with no event: {seq}")
            elif HOOK_FAILURE in event:
                failures.append(f"hook failure: {event[HOOK_FAILURE]}")
            else:
                events.append(event)
        else:
            pending[record.get("seq", -1)] = record
    for seq in pending:
        failures.append(f"event {seq} without its commit record")
    return events, failures
