"""v0.5.4: a candidate launcher for long runs that should survive a restart of the desktop app
(#217; the maintainer's decision of 2026-11-12, 15:46, item 4). **A proposal; not used by any run
until the maintainer approves it.** ``scripts/launch_affinity.ps1`` stays the launcher of record.

**The finding.** Commands started from the app's tools run inside a chain of Windows job objects.
When the app exited on 2026-11-12 at about 15:40, I4's run (launched through
``launch_affinity.ps1``) ended with it. A probe on the same day showed two things:
- a PowerShell started by the tools is in a job whose limits allow a breakaway
  (``JOB_OBJECT_LIMIT_BREAKAWAY_OK``);
- a child created with ``CREATE_BREAKAWAY_FROM_JOB`` starts, so the chain allows it.

Sources (read 2026-11-12): Microsoft, "Job Objects",
https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects ;
"JOBOBJECT_BASIC_LIMIT_INFORMATION",
https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_basic_limit_information
;
"Nested Jobs", https://learn.microsoft.com/en-us/windows/win32/procthread/nested-jobs (a breakaway
from a nested job must be allowed by every job of the chain).

**What this does:**
- it reserves the log's prefix exclusively (``<log>.claim``, created with ``O_EXCL`` and kept)
  before it opens a log or starts anything, and opens the logs with exclusive creation: two
  launchers with the same ``--log`` cannot both proceed, and a prefix is never reused;
- it pins itself to the processors of ``--threads`` (8 to 31 by default) before starting
  anything, so the child inherits the mask;
- it starts the project's venv Python on the script with ``CREATE_BREAKAWAY_FROM_JOB``,
  ``DETACHED_PROCESS``, ``CREATE_NEW_PROCESS_GROUP`` and ``CREATE_SUSPENDED``, its output to
  ``<log>.out.txt`` and ``<log>.err.txt``;
- while the child is suspended (it has run nothing), it reads the child's creation time and writes
  its PID and creation time to ``<log>.pid.json`` atomically (a temporary file, flushed, then
  renamed);
- only then does it resume the child's one thread. If the creation time cannot be read, the record
  cannot be written, or the thread cannot be resumed, it ends that child, by the handle of the
  process it created, and exits with an error: **the work never runs without its identity on
  file**;
- it returns at once.

The venv's ``python.exe`` is a launcher that starts the real interpreter as its child and waits for
it (CPython's ``PC/venvlauncher.c``); the record names the launcher. A script that must be found
after a restart records its own interpreter's PID and creation time (the restart probe does).

**It refuses** if the breakaway is denied, and never falls back to an attached child. The driver
sets the run's own BelowNormal priority, as it does under ``launch_affinity.ps1``. Nothing is ever
ended by name.

**Not confirmed:** that such a run survives an actual restart of the app. That needs a restart to
observe, which is the maintainer's to schedule.
"""

from __future__ import annotations

import argparse
import ctypes
import json
import os
import subprocess
import sys
import time
from collections.abc import Callable
from ctypes import wintypes
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BREAKAWAY, DETACHED, NEW_GROUP, SUSPENDED = 0x01000000, 0x00000008, 0x00000200, 0x00000004
FLAGS = BREAKAWAY | DETACHED | NEW_GROUP | SUSPENDED
QUERY_LIMITED = 0x1000
THREAD_SUSPEND_RESUME = 0x0002
SNAPTHREAD = 0x00000004
INVALID_HANDLE = wintypes.HANDLE(-1).value


class THREADENTRY32(ctypes.Structure):
    _fields_ = [
        ("dwSize", wintypes.DWORD),
        ("cntUsage", wintypes.DWORD),
        ("th32ThreadID", wintypes.DWORD),
        ("th32OwnerProcessID", wintypes.DWORD),
        ("tpBasePri", wintypes.LONG),
        ("tpDeltaPri", wintypes.LONG),
        ("dwFlags", wintypes.DWORD),
    ]


def _kernel32():
    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    h, b, d = wintypes.HANDLE, wintypes.BOOL, wintypes.DWORD
    pft = ctypes.POINTER(wintypes.FILETIME)
    k32.GetCurrentProcess.argtypes, k32.GetCurrentProcess.restype = [], h
    k32.SetProcessAffinityMask.argtypes = [h, ctypes.c_size_t]
    k32.SetProcessAffinityMask.restype = b
    k32.OpenProcess.argtypes, k32.OpenProcess.restype = [d, b, d], h
    k32.GetProcessTimes.argtypes, k32.GetProcessTimes.restype = [h, pft, pft, pft, pft], b
    k32.CloseHandle.argtypes, k32.CloseHandle.restype = [h], b
    k32.CreateToolhelp32Snapshot.argtypes = [d, d]
    k32.CreateToolhelp32Snapshot.restype = h
    pte = ctypes.POINTER(THREADENTRY32)
    k32.Thread32First.argtypes, k32.Thread32First.restype = [h, pte], b
    k32.Thread32Next.argtypes, k32.Thread32Next.restype = [h, pte], b
    k32.OpenThread.argtypes, k32.OpenThread.restype = [d, b, d], h
    k32.ResumeThread.argtypes, k32.ResumeThread.restype = [h], d
    return k32


def _mask(threads: str) -> int:
    first, last = (int(x) for x in threads.split("-"))
    if not 0 <= first <= last < 64:
        raise SystemExit(f"--threads {threads}: not a range within 0-63")
    return sum(1 << i for i in range(first, last + 1))


def _inside(root: Path, path: str) -> Path:
    """The log's path, resolved; refused outside the project."""
    log = (root / path).resolve()
    if root.resolve() not in log.parents:
        raise SystemExit("the log must be inside the project: refused")
    return log


def _creation_time(k32, pid: int) -> int:
    """The process's creation time (FILETIME, 100 ns since 1601); never zero."""
    handle = k32.OpenProcess(QUERY_LIMITED, False, pid)
    if not handle:
        raise OSError(f"OpenProcess failed: error {ctypes.get_last_error()}")
    try:
        c, e, k, u = (wintypes.FILETIME() for _ in range(4))
        if not k32.GetProcessTimes(handle, *(ctypes.byref(x) for x in (c, e, k, u))):
            raise OSError(f"GetProcessTimes failed: error {ctypes.get_last_error()}")
        value = (c.dwHighDateTime << 32) | c.dwLowDateTime
        if value <= 0:
            raise OSError("a creation time of zero")
        return value
    finally:
        k32.CloseHandle(handle)


def _resume_only_thread(k32, pid: int) -> None:
    """Resume the one thread of a process created suspended; anything else is an error."""
    snap = k32.CreateToolhelp32Snapshot(SNAPTHREAD, 0)
    if not snap or snap == INVALID_HANDLE:
        raise OSError(f"CreateToolhelp32Snapshot failed: error {ctypes.get_last_error()}")
    threads = []
    try:
        entry = THREADENTRY32()
        entry.dwSize = ctypes.sizeof(THREADENTRY32)
        ok = k32.Thread32First(snap, ctypes.byref(entry))
        while ok:
            if entry.th32OwnerProcessID == pid:
                threads.append(entry.th32ThreadID)
            ok = k32.Thread32Next(snap, ctypes.byref(entry))
    finally:
        k32.CloseHandle(snap)
    if len(threads) != 1:
        raise OSError(f"the suspended child has {len(threads)} threads, not one")
    handle = k32.OpenThread(THREAD_SUSPEND_RESUME, False, threads[0])
    if not handle:
        raise OSError(f"OpenThread failed: error {ctypes.get_last_error()}")
    try:
        previous = k32.ResumeThread(handle)
    finally:
        k32.CloseHandle(handle)
    if previous != 1:
        raise OSError(f"ResumeThread returned {previous}, not a suspend count of one")


def _write_atomic(path: Path, text: str) -> None:
    tmp = path.with_name(path.name + ".tmp")
    with tmp.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


def _claim(log: Path) -> None:
    """Reserve the log's prefix exclusively before anything is opened or started: the claim file
    is created with ``O_CREAT | O_EXCL`` (atomic: of two launchers with the same ``--log``, one
    fails) and is kept, so a prefix is never reused."""
    claim = log.with_name(log.name + ".claim")
    try:
        fd = os.open(claim, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        raise SystemExit(f"{claim.name} exists: a log is never reused") from None
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(f"{os.getpid()} {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}\n")


def start(
    log: Path,
    argv: list[str],
    meta: dict,
    *,
    popen: Callable = subprocess.Popen,
    creation_time: Callable[[int], int],
    resume: Callable[[int], None],
    write: Callable[[Path, str], None] = _write_atomic,
) -> dict:
    """Claim the prefix, start the child suspended, record its identity, then resume it; on any
    failure after the start, end that child by its own handle. ``popen``, ``creation_time``,
    ``resume`` and ``write`` are injected so that the sequence can be tested offline."""
    _claim(log)
    with (
        log.with_name(log.name + ".out.txt").open("xb") as out,
        log.with_name(log.name + ".err.txt").open("xb") as err,
    ):
        try:
            child = popen(
                argv, cwd=ROOT, stdout=out, stderr=err, stdin=subprocess.DEVNULL,
                creationflags=FLAGS,
            )  # fmt: skip
        except OSError as exc:
            raise SystemExit(f"the breakaway was refused ({exc!r}): nothing started") from None
    try:
        record = {
            "pid": child.pid,
            "created": creation_time(child.pid),
            **meta,
            "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        write(log.with_name(log.name + ".pid.json"), json.dumps(record, sort_keys=True) + "\n")
        resume(child.pid)
    except BaseException as exc:
        child.kill()  # the handle of the process this launcher created, still suspended
        child.wait(timeout=30)
        raise SystemExit(f"the child's identity could not be secured ({exc!r}): ended") from None
    return record


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--script", required=True)
    ap.add_argument("--log", required=True)
    ap.add_argument("--threads", default="8-31")
    ap.add_argument("args", nargs="*")
    a = ap.parse_args()
    if sys.platform != "win32":
        raise SystemExit("Windows only")
    k32 = _kernel32()
    if not k32.SetProcessAffinityMask(k32.GetCurrentProcess(), _mask(a.threads)):
        raise SystemExit(f"the affinity could not be set: error {ctypes.get_last_error()}")
    log = _inside(ROOT, a.log)
    log.parent.mkdir(parents=True, exist_ok=True)
    record = start(
        log,
        [str(ROOT / ".venv/Scripts/python.exe"), a.script, *a.args],
        {"script": a.script, "args": a.args, "threads": a.threads},
        creation_time=lambda pid: _creation_time(k32, pid),
        resume=lambda pid: _resume_only_thread(k32, pid),
    )
    print(json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
