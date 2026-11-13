"""A harmless restart probe (#217; the maintainer's decision of 2026-11-12, 18:05, item 3): no data,
no write outside .cache. Started by docs/validation/v0.5.4/launch_detached.py, it records its own
interpreter's identity (PID, creation time, parent PID and the parent's creation time), its
affinity mask and priority class (after setting BelowNormal, as the driver does), then a heartbeat
with a sequence number every --every seconds for --minutes minutes, then a final line, and exits.

Usage: .venv/Scripts/python.exe .cache/v054/tools/restart_probe.py <dir> [--minutes 60] [--every 10]
"""

from __future__ import annotations

import argparse
import ctypes
import datetime as dt
import json
import os
import sys
import time
from ctypes import wintypes
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BELOW_NORMAL = 0x00004000
QUERY_LIMITED = 0x1000


def _k32():
    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    h, b, d = wintypes.HANDLE, wintypes.BOOL, wintypes.DWORD
    pft = ctypes.POINTER(wintypes.FILETIME)
    psz = ctypes.POINTER(ctypes.c_size_t)
    k32.GetCurrentProcess.argtypes, k32.GetCurrentProcess.restype = [], h
    k32.OpenProcess.argtypes, k32.OpenProcess.restype = [d, b, d], h
    k32.GetProcessTimes.argtypes, k32.GetProcessTimes.restype = [h, pft, pft, pft, pft], b
    k32.CloseHandle.argtypes, k32.CloseHandle.restype = [h], b
    k32.GetProcessAffinityMask.argtypes = [h, psz, psz]
    k32.GetProcessAffinityMask.restype = b
    k32.SetPriorityClass.argtypes, k32.SetPriorityClass.restype = [h, d], b
    k32.GetPriorityClass.argtypes, k32.GetPriorityClass.restype = [h], d
    k32.WaitForSingleObject.argtypes, k32.WaitForSingleObject.restype = [h, d], d
    return k32


def created(k32, pid: int) -> int | None:
    handle = k32.OpenProcess(QUERY_LIMITED, False, pid)
    if not handle:
        return None
    try:
        c, e, k, u = (wintypes.FILETIME() for _ in range(4))
        if not k32.GetProcessTimes(handle, *(ctypes.byref(x) for x in (c, e, k, u))):
            return None
        return (c.dwHighDateTime << 32) | c.dwLowDateTime
    finally:
        k32.CloseHandle(handle)


SYNCHRONIZE = 0x00100000
WAIT_OBJECT_0, WAIT_TIMEOUT = 0x0, 0x102
ERROR_INVALID_PARAMETER = 87


def status(k32, pid: int, expected: int) -> str:
    """'alive' only if the PID opens, has the expected creation time and has not terminated (a
    zero-timeout wait on its handle times out); 'ended' if no such process exists or its handle is
    signaled; 'reused' if another process holds the PID; 'unknown' on any other failure."""
    handle = k32.OpenProcess(QUERY_LIMITED | SYNCHRONIZE, False, pid)
    if not handle:
        err = ctypes.get_last_error()
        return "ended" if err == ERROR_INVALID_PARAMETER else f"unknown (error {err})"
    try:
        c, e, k, u = (wintypes.FILETIME() for _ in range(4))
        if not k32.GetProcessTimes(handle, *(ctypes.byref(x) for x in (c, e, k, u))):
            return f"unknown (error {ctypes.get_last_error()})"
        if ((c.dwHighDateTime << 32) | c.dwLowDateTime) != expected:
            return "reused"
        wait = k32.WaitForSingleObject(handle, 0)
        if wait == WAIT_TIMEOUT:
            return "alive"
        if wait == WAIT_OBJECT_0:
            return "ended"
        return f"unknown (wait {wait:#x})"
    finally:
        k32.CloseHandle(handle)


def utc() -> str:
    return dt.datetime.now(dt.UTC).isoformat(timespec="milliseconds")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("dir")
    ap.add_argument("--minutes", type=float, default=60.0)
    ap.add_argument("--every", type=float, default=10.0)
    a = ap.parse_args()
    folder = (ROOT / a.dir).resolve()
    if (ROOT / ".cache").resolve() not in folder.parents:
        raise SystemExit("the probe writes only under .cache: refused")
    if not 1.0 <= a.every <= 60.0 or not 0.0 < a.minutes <= 120.0:
        raise SystemExit("--every 1 to 60 s, --minutes up to 120")
    folder.mkdir(parents=True, exist_ok=True)
    k32 = _k32()
    me = k32.GetCurrentProcess()
    if not k32.SetPriorityClass(me, BELOW_NORMAL):
        raise SystemExit(f"BelowNormal could not be set: error {ctypes.get_last_error()}")
    proc, system = ctypes.c_size_t(), ctypes.c_size_t()
    if not k32.GetProcessAffinityMask(me, ctypes.byref(proc), ctypes.byref(system)):
        raise SystemExit("the affinity could not be read")
    pid, ppid = os.getpid(), os.getppid()
    identity = {
        "pid": pid,
        "created": created(k32, pid),
        "ppid": ppid,
        "parent_created": created(k32, ppid),
        "affinity_mask": hex(proc.value),
        "priority_class": hex(k32.GetPriorityClass(me)),
        "python": sys.version.split()[0],
        "started_utc": utc(),
        "minutes": a.minutes,
        "every_seconds": a.every,
    }
    tmp = folder / "identity.json.tmp"
    tmp.write_text(json.dumps(identity, sort_keys=True) + "\n", "utf-8")
    os.replace(tmp, folder / "identity.json")
    # the app's processes to watch (PID and creation time, written before the launch): each beat
    # records whether each is still the same process, which dates the app's exit
    watch = json.loads((folder / "watch.json").read_text("utf-8"))["pids"]  # required
    if not watch:
        raise SystemExit("watch.json lists no process")
    beats = folder / "heartbeat.jsonl"
    start = time.monotonic()
    seq = 0
    with beats.open("a", encoding="utf-8", newline="\n") as fh:
        while time.monotonic() - start < a.minutes * 60.0:
            alive = {p: status(k32, int(p), c) for p, c in watch.items()}
            line = {"seq": seq, "utc": utc(), "mono": time.monotonic(), "watch": alive}
            fh.write(json.dumps(line, sort_keys=True) + "\n")
            fh.flush()
            os.fsync(fh.fileno())
            seq += 1
            time.sleep(a.every)
        fh.write(json.dumps({"seq": seq, "utc": utc(), "final": "complete"}) + "\n")
        fh.flush()
        os.fsync(fh.fileno())


if __name__ == "__main__":
    main()
