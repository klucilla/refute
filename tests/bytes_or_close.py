"""Comparing an output with a byte fixture recorded on one platform (v0.5.1 WP4 row 4.2, WP5 row
5.2 (a)).

The fixtures of an analysis were written on the recording platform below. CI run 42353283742
(2026-11-07) showed that the same code gives floats that differ in their last bits on Linux and on
Python 3.12 (BLAS and the CPU's floating point), so byte identity is a claim about one platform:

- on the recording platform the output must equal the fixture byte for byte;
- elsewhere it must have the same structure, the same keys, strings, integers, booleans and nulls,
  and every float within a relative 1e-9 of the fixture's (the tolerance of the v0.5 C2
  compatibility, ``calib05.values.C2Values.float_rel_tolerance``); a Markdown report the same text
  with every number compared at that tolerance.
"""

from __future__ import annotations

import json
import math
import platform
import re
import sys

RECORDING_PLATFORM = ("win32", "3.13")
REL_TOL = 1e-9
_NUMBER = re.compile(r"-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?")


def on_recording_platform() -> bool:
    return (sys.platform, ".".join(platform.python_version_tuple()[:2])) == RECORDING_PLATFORM


def _close(a, b, path: str) -> list[str]:
    if isinstance(a, bool) or isinstance(b, bool) or a is None or b is None:
        return [] if a == b else [f"{path}: {a!r} != {b!r}"]
    if isinstance(a, float) or isinstance(b, float):
        if isinstance(a, (int, float)) and isinstance(b, (int, float)):
            ok = math.isclose(a, b, rel_tol=REL_TOL, abs_tol=0.0) or a == b
            return [] if ok else [f"{path}: {a!r} != {b!r}"]
        return [f"{path}: {a!r} != {b!r}"]
    if isinstance(a, dict) and isinstance(b, dict):
        if list(a) != list(b):
            return [f"{path}: keys {list(a)} != {list(b)}"]
        return [p for k in a for p in _close(a[k], b[k], f"{path}.{k}")]
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            return [f"{path}: length {len(a)} != {len(b)}"]
        return [
            p
            for i, (x, y) in enumerate(zip(a, b, strict=True))
            for p in _close(x, y, f"{path}[{i}]")
        ]
    return [] if a == b else [f"{path}: {a!r} != {b!r}"]


def json_problems(actual: str, fixture: str) -> list[str]:
    """Empty when ``actual`` matches the JSON ``fixture`` by the rule of this module."""
    if actual == fixture:
        return []
    if on_recording_platform():
        return ["not byte-identical on the recording platform"]
    return _close(json.loads(actual), json.loads(fixture), "$")


def text_problems(actual: str, fixture: str) -> list[str]:
    """Empty when the Markdown ``actual`` matches ``fixture`` by the rule of this module."""
    if actual == fixture:
        return []
    if on_recording_platform():
        return ["not byte-identical on the recording platform"]
    if _NUMBER.sub("#", actual) != _NUMBER.sub("#", fixture):
        return ["the text differs beyond its numbers"]
    pairs = zip(_NUMBER.findall(actual), _NUMBER.findall(fixture), strict=True)
    return [
        f"number {x} != {y}"
        for x, y in pairs
        if not (x == y or math.isclose(float(x), float(y), rel_tol=REL_TOL, abs_tol=0.0))
    ]
