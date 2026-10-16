"""The observation hook of coverage route (b) (docs/validation/v0.3/wp3-acceptance.md, 1.5a,
W3.12c).

The hook is observation only. ``observe(function, sink)`` returns a wrapper that:

- calls ``function`` with exactly the arguments it received, the same objects, unchanged,
  and returns exactly the object ``function`` returned (or lets exactly the exception it
  raised propagate);
- only after the call, reads its first argument (``y_true`` in scikit-learn's metric
  functions) to record one event: the function's name, the call site, the number of
  examples, the SHA-256 of the labels in Refute's canonical JSON form, and the returned
  value's text;
- never consumes an iterator: an argument that is its own iterator (a generator, for
  example) is not read, and a hook failure is recorded instead;
- turns any failure of its own (an argument it cannot read, a sink that fails) into a
  failure record, or into no record at all when the sink itself fails. Neither ever
  changes the call. The gate counts a hook failure, or a missing or extra event, as
  ``INCONCLUSIVE``.

This module uses the standard library only, because it runs in the paper's container,
where Refute is not installed. Its labels hash is computed in the canonical form of
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


def _canonical_labels(labels: list[Any]) -> bytes:
    """The canonical JSON of a list of labels (refute.core.canonical, for int and str)."""
    values = []
    for label in labels:
        if isinstance(label, bool) or not isinstance(label, (int, str)):
            raise TypeError(f"label of type {type(label).__name__} is not an int or a str")
        values.append(unicodedata.normalize("NFC", label) if isinstance(label, str) else label)
    text = json.dumps(
        values, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    )
    return text.encode("utf-8")


def _labels(y_true: Any) -> list[Any]:
    if iter(y_true) is y_true:
        raise TypeError("the labels are an iterator: reading them would consume them")
    values = y_true.tolist() if hasattr(y_true, "tolist") else list(y_true)
    return [v.item() if hasattr(v, "item") else v for v in values]


def _event(function: Callable[..., Any], frame: Any, args: tuple, result: Any) -> dict[str, Any]:
    labels = _labels(args[0])
    module = getattr(function, "__module__", "?")
    name = getattr(function, "__qualname__", "?")
    return {
        "function": f"{module}.{name}",
        "call_site": {"file": frame.f_code.co_filename, "line": frame.f_lineno},
        "n_examples": len(labels),
        "labels_sha256": hashlib.sha256(_canonical_labels(labels)).hexdigest(),
        "result": repr(result),
    }


def observe(
    function: Callable[..., Any], sink: Callable[[dict[str, Any]], None]
) -> Callable[..., Any]:
    """The observation-only wrapper of ``function``; ``sink`` receives one event per call."""

    @functools.wraps(function)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        frame = sys._getframe(1)
        result = function(*args, **kwargs)
        try:
            try:
                record = _event(function, frame, args, result)
            except Exception as exc:  # noqa: BLE001 - any failure of the hook is recorded
                record = {HOOK_FAILURE: f"{type(exc).__name__}: {exc}"}
            sink(record)
        except Exception:  # noqa: BLE001,S110 - a failing sink leaves no event: INCONCLUSIVE
            pass
        return result

    return wrapper
