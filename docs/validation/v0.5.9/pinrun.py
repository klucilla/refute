"""Run a command pinned to processors 8-31 at BelowNormal priority (the machine rule); the child
inherits the affinity and the priority class.
Usage: .venv/Scripts/python.exe -B .cache/v055/tools/pinrun.py <program> <args...>"""

import ctypes
import subprocess
import sys
from pathlib import Path

k32 = ctypes.WinDLL("kernel32", use_last_error=True)
k32.GetCurrentProcess.restype = ctypes.c_void_p
k32.SetProcessAffinityMask.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
k32.SetPriorityClass.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
me = k32.GetCurrentProcess()
if not k32.SetProcessAffinityMask(me, 0xFFFFFF00) or not k32.SetPriorityClass(me, 0x4000):
    raise SystemExit("could not pin the process")
args = sys.argv[1:]
if Path(args[0]).exists():  # CreateProcess does not resolve a relative path with slashes
    args[0] = str(Path(args[0]).resolve())
sys.exit(subprocess.call(args))
