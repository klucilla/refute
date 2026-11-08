"""Read which logical processors share a physical core on this machine (Windows), for the driver's
``pin`` (Codex's round 1: verify the topology, do not assume it). Writes ``topology.json``.

Usage (from the project root): ``.venv/Scripts/python.exe <this file>``.
"""

from __future__ import annotations

import ctypes
import json
from ctypes import wintypes
from pathlib import Path

HERE = Path(__file__).resolve().parent
RELATION_PROCESSOR_CORE = 0


class _Union(ctypes.Union):
    _fields_ = [("flags", ctypes.c_byte), ("reserved", ctypes.c_ulonglong * 2)]


class _Info(ctypes.Structure):
    _fields_ = [("mask", ctypes.c_size_t), ("relationship", ctypes.c_int), ("u", _Union)]


def cores() -> list[list[int]]:
    k32 = ctypes.windll.kernel32
    length = wintypes.DWORD(0)
    k32.GetLogicalProcessorInformation(None, ctypes.byref(length))
    count = length.value // ctypes.sizeof(_Info)
    buffer = (_Info * count)()
    if not k32.GetLogicalProcessorInformation(buffer, ctypes.byref(length)):
        raise OSError("GetLogicalProcessorInformation failed")
    out = []
    for item in buffer:
        if item.relationship == RELATION_PROCESSOR_CORE:
            out.append([b for b in range(64) if item.mask >> b & 1])
    return sorted(out)


def main() -> None:
    table = cores()
    allowed = [c for c in table if all(8 <= p <= 31 for p in c)]
    doc = {
        "physical_cores": len(table),
        "cores": table,
        "cores_entirely_in_8_to_31": len(allowed),
        "one_logical_processor_per_core_in_8_to_31": [c[0] for c in allowed],
    }
    (HERE / "topology.json").write_text(json.dumps(doc, indent=1) + "\n", "utf-8")
    print(doc["physical_cores"], doc["cores_entirely_in_8_to_31"], allowed)


if __name__ == "__main__":
    main()
