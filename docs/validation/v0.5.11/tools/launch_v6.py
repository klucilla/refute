"""The metered launcher of v0.5.11, version 6: version 5 with 64-bit transfer counters, after
Codex's second review of the step-2 diff, item 3.

    .venv/Scripts/python.exe -I -B docs/validation/v0.5.11/tools/launch_v6.py <unit spec>
        [--label L] [--approval URL] [-- extra arguments]

**Why.** Version 5 unwrapped a ``netstat -e`` counter when it decreased from above 2^31. Codex
showed that this does not establish a 32-bit wrap: a reset after a reading above 2^32 was
accepted as a small increment, and a full wrap can look like an ordinary increase.

**What changed.**
- **The source:** the machine's transfer is read from Windows' 64-bit interface counters
  (``GetIfTable2`` of iphlpapi: ``InOctets`` and ``OutOctets`` of every interface), never from
  ``netstat``.
- **The layout is checked.** ``sizeof(MIB_IF_ROW2)`` must be 1352 bytes, the documented x64
  size. Otherwise the launcher refuses to start.
- **The interface set is stable.** The baseline records each interface's LUID. A reading with
  another set of interfaces is lost telemetry.
- **Any decrease is lost telemetry:** of an interface's ``InOctets`` or ``OutOctets``, or of
  their sum. No wrap is ever assumed.
- **The bound is still machine-wide,** an upper bound of the unit's own transfer, as in every
  earlier version.

Everything else is version 5's: its scan, which skips vanished files and follows no junction, and
versions 4 and 2 behind it. The SHA-256 of launch_v2.py, launch_v4.py, launch_v5.py and this file
are in every attempt's identity.
"""

from __future__ import annotations

import ctypes
import importlib.util
import sys
from ctypes import wintypes
from pathlib import Path

_HERE = Path(__file__).resolve().parent


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, _HERE / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


v5 = _load("launch_v5")
v4, base = v5.v4, v5.base
ROW2_SIZE_X64 = 1352


class MIB_IF_ROW2(ctypes.Structure):  # noqa: N801 (the Win32 name)
    _fields_ = [
        ("InterfaceLuid", ctypes.c_uint64),
        ("InterfaceIndex", ctypes.c_uint32),
        ("InterfaceGuid", ctypes.c_ubyte * 16),
        ("Alias", ctypes.c_wchar * 257),
        ("Description", ctypes.c_wchar * 257),
        ("PhysicalAddressLength", ctypes.c_uint32),
        ("PhysicalAddress", ctypes.c_ubyte * 32),
        ("PermanentPhysicalAddress", ctypes.c_ubyte * 32),
        ("Mtu", ctypes.c_uint32),
        ("Type", ctypes.c_uint32),
        ("TunnelType", ctypes.c_uint32),
        ("MediaType", ctypes.c_uint32),
        ("PhysicalMediumType", ctypes.c_uint32),
        ("AccessType", ctypes.c_uint32),
        ("DirectionType", ctypes.c_uint32),
        ("InterfaceAndOperStatusFlags", ctypes.c_ubyte),
        ("OperStatus", ctypes.c_uint32),
        ("AdminStatus", ctypes.c_uint32),
        ("MediaConnectState", ctypes.c_uint32),
        ("NetworkGuid", ctypes.c_ubyte * 16),
        ("ConnectionType", ctypes.c_uint32),
        ("TransmitLinkSpeed", ctypes.c_uint64),
        ("ReceiveLinkSpeed", ctypes.c_uint64),
        ("InOctets", ctypes.c_uint64),
        ("InUcastPkts", ctypes.c_uint64),
        ("InNUcastPkts", ctypes.c_uint64),
        ("InDiscards", ctypes.c_uint64),
        ("InErrors", ctypes.c_uint64),
        ("InUnknownProtos", ctypes.c_uint64),
        ("InUcastOctets", ctypes.c_uint64),
        ("InMulticastOctets", ctypes.c_uint64),
        ("InBroadcastOctets", ctypes.c_uint64),
        ("OutOctets", ctypes.c_uint64),
        ("OutUcastPkts", ctypes.c_uint64),
        ("OutNUcastPkts", ctypes.c_uint64),
        ("OutDiscards", ctypes.c_uint64),
        ("OutErrors", ctypes.c_uint64),
        ("OutUcastOctets", ctypes.c_uint64),
        ("OutMulticastOctets", ctypes.c_uint64),
        ("OutBroadcastOctets", ctypes.c_uint64),
        ("OutQLen", ctypes.c_uint64),
    ]


_iphlpapi = ctypes.WinDLL("iphlpapi")
_iphlpapi.GetIfTable2.argtypes = [ctypes.POINTER(ctypes.c_void_p)]
_iphlpapi.GetIfTable2.restype = wintypes.ULONG
_iphlpapi.FreeMibTable.argtypes = [ctypes.c_void_p]


def _rows() -> dict[int, tuple[int, int]] | None:
    """LUID -> (InOctets, OutOctets) for every interface, or None when the read fails."""
    table = ctypes.c_void_p()
    if _iphlpapi.GetIfTable2(ctypes.byref(table)) != 0 or not table.value:
        return None
    try:
        n = ctypes.c_uint32.from_address(table.value).value
        first = table.value + 8  # ULONG NumEntries, then the 8-byte aligned rows
        out = {}
        for i in range(n):
            row = MIB_IF_ROW2.from_address(first + i * ctypes.sizeof(MIB_IF_ROW2))
            out[int(row.InterfaceLuid)] = (int(row.InOctets), int(row.OutOctets))
        return out
    finally:
        _iphlpapi.FreeMibTable(table)


class _Counter64:
    """The machine's received plus sent octets from 64-bit counters; None on lost telemetry."""

    def __init__(self) -> None:
        self.base: dict[int, tuple[int, int]] | None = None
        self.last: dict[int, tuple[int, int]] | None = None

    def read(self) -> int | None:
        now = _rows()
        if now is None:
            return None
        if self.base is None:
            self.base = self.last = now
        if set(now) != set(self.base):
            return None
        for luid, (i, o) in now.items():
            li, lo = self.last[luid]
            if i < li or o < lo:
                return None
        self.last = now
        return sum(i + o for i, o in now.values())


def main() -> int:
    if ctypes.sizeof(MIB_IF_ROW2) != ROW2_SIZE_X64:
        raise SystemExit(
            f"refused: MIB_IF_ROW2 is {ctypes.sizeof(MIB_IF_ROW2)} bytes, not {ROW2_SIZE_X64}"
        )
    counter = _Counter64()
    if counter.read() is None:
        raise SystemExit("refused: the 64-bit interface counters cannot be read")
    v4.tree_bytes = v5.tree_bytes
    base.net_bytes = counter.read
    v6_rel = Path(__file__).resolve().relative_to(base.ROOT).as_posix()
    v5_rel = (_HERE / "launch_v5.py").relative_to(base.ROOT).as_posix()
    shas = {v6_rel: base.committed_sha256(v6_rel), v5_rel: base.committed_sha256(v5_rel)}
    original_append = base.append_log

    def append_log(entry: dict) -> None:
        if entry.get("event") == "before":
            entry = dict(entry, launcher="launch_v6.py")
            entry["identity_sha256"] = {**shas, **entry.get("identity_sha256", {})}
            entry["transfer_source"] = "GetIfTable2 64-bit InOctets + OutOctets, all interfaces"
        original_append(entry)

    base.append_log = append_log
    return v4.main()


if __name__ == "__main__":
    sys.exit(main())
