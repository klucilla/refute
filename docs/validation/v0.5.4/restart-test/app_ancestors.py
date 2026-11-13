"""The chain of processes above a given PID (process snapshot; PID, parent, creation time, image
name), for the restart probe's watch list (#217). With --write <dir>, writes <dir>/watch.json with
the PID and creation time of every ancestor whose image name contains "claude" (names not stored).

Usage: .venv/Scripts/python.exe .cache/v054/tools/app_ancestors.py <pid> [--write <dir>]
"""

from __future__ import annotations

import ctypes
import json
import sys
from ctypes import wintypes
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import restart_probe  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]


class PROCESSENTRY32W(ctypes.Structure):
    _fields_ = [
        ("dwSize", wintypes.DWORD),
        ("cntUsage", wintypes.DWORD),
        ("th32ProcessID", wintypes.DWORD),
        ("th32DefaultHeapID", ctypes.c_size_t),
        ("th32ModuleID", wintypes.DWORD),
        ("cntThreads", wintypes.DWORD),
        ("th32ParentProcessID", wintypes.DWORD),
        ("pcPriClassBase", wintypes.LONG),
        ("dwFlags", wintypes.DWORD),
        ("szExeFile", wintypes.WCHAR * 260),
    ]


def snapshot() -> dict[int, tuple[int, str]]:
    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    k32.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
    k32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    pe = ctypes.POINTER(PROCESSENTRY32W)
    k32.Process32FirstW.argtypes, k32.Process32FirstW.restype = [wintypes.HANDLE, pe], wintypes.BOOL
    k32.Process32NextW.argtypes, k32.Process32NextW.restype = [wintypes.HANDLE, pe], wintypes.BOOL
    k32.CloseHandle.argtypes, k32.CloseHandle.restype = [wintypes.HANDLE], wintypes.BOOL
    snap = k32.CreateToolhelp32Snapshot(0x00000002, 0)
    table = {}
    try:
        e = PROCESSENTRY32W()
        e.dwSize = ctypes.sizeof(PROCESSENTRY32W)
        ok = k32.Process32FirstW(snap, ctypes.byref(e))
        while ok:
            table[e.th32ProcessID] = (e.th32ParentProcessID, e.szExeFile)
            ok = k32.Process32NextW(snap, ctypes.byref(e))
    finally:
        k32.CloseHandle(snap)
    return table


def main() -> None:
    pid = int(sys.argv[1])
    table = snapshot()
    k32 = restart_probe._k32()
    chain = []
    seen = set()
    while pid in table and pid not in seen and pid > 4:
        seen.add(pid)
        parent, name = table[pid]
        made = restart_probe.created(k32, pid)
        pmade = restart_probe.created(k32, parent)
        chain.append({"pid": pid, "name": name, "created": made})
        if pmade is None or made is None or pmade > made:  # the parent ended; its PID was reused
            break
        pid = parent
    print(json.dumps(chain, indent=1))
    for flag, name in (("--write", "watch.json"), ("--after", "after_restart.json")):
        if flag not in sys.argv:
            continue
        folder = (ROOT / sys.argv[sys.argv.index(flag) + 1]).resolve()
        if (ROOT / ".cache").resolve() not in folder.parents:
            raise SystemExit("only under .cache")
        folder.mkdir(parents=True, exist_ok=True)
        pids = {str(c["pid"]): c["created"] for c in chain if "claude" in c["name"].lower()}
        if not pids or any(v is None for v in pids.values()):
            raise SystemExit("no app process with a creation time in the chain")
        path = folder / name
        if path.exists():
            raise SystemExit(f"{name} exists: never overwritten")
        path.write_text(json.dumps({"pids": pids}) + "\n", "utf-8")


if __name__ == "__main__":
    main()
