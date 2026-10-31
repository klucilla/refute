"""The affinity mask of scripts/launch_affinity.ps1 is built in 64 bits (the slip of 2026-10-30:
[IntPtr]0xFFFFFF00 is the int32 -256, which Windows refuses). Windows only; no network."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
POWERSHELL = shutil.which("powershell") if sys.platform == "win32" else None
pytestmark = pytest.mark.skipif(POWERSHELL is None, reason="Windows PowerShell only")


def _mask(threads: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [
            POWERSHELL,
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(ROOT / "scripts" / "launch_affinity.ps1"),
            "-Threads",
            threads,
            "-MaskOnly",
        ],
        capture_output=True,
        text=True,
        timeout=120,
    )


@pytest.mark.parametrize(
    ("threads", "mask"),
    [
        ("8-31", "0xFFFFFF00"),  # above the int32 range: the case that failed
        ("31-31", "0x80000000"),  # the int32 sign bit alone
        ("0-31", "0xFFFFFFFF"),
        ("0-0", "0x1"),
        ("0-7", "0xFF"),
        ("32-33", "0x300000000"),
    ],
)
def test_the_mask_is_built_in_64_bits(threads, mask):
    out = _mask(threads)
    assert out.returncode == 0, out.stderr
    assert out.stdout.strip() == mask


@pytest.mark.parametrize("threads", ["31-8", "8", "0-64"])
def test_an_invalid_range_is_refused(threads):
    assert _mask(threads).returncode != 0


PROBE = """import ctypes, sys
from ctypes import wintypes
k = ctypes.WinDLL("kernel32", use_last_error=True)
k.GetCurrentProcess.restype = wintypes.HANDLE
k.GetProcessAffinityMask.argtypes = [
    wintypes.HANDLE,
    ctypes.POINTER(ctypes.c_size_t),
    ctypes.POINTER(ctypes.c_size_t),
]
process, system = ctypes.c_size_t(), ctypes.c_size_t()
k.GetProcessAffinityMask(k.GetCurrentProcess(), ctypes.byref(process), ctypes.byref(system))
print(hex(process.value), sys.argv[1:])
"""


def test_the_launched_process_has_the_mask_from_its_start(tmp_path):
    """The child reads its own mask with GetProcessAffinityMask: 0x1 for 0-0 (a CPU every
    machine has), and its arguments arrive intact. The launcher's line reports the mask it set
    on itself, not one read from the child, which may already have exited."""
    probe = tmp_path / "probe.py"
    probe.write_text(PROBE)
    log = tmp_path / "run"
    out = subprocess.run(
        [
            POWERSHELL,
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(ROOT / "scripts" / "launch_affinity.ps1"),
            "-Script",
            str(probe),
            "-Arguments",
            "a,b c",
            "-Log",
            str(log),
            "-Threads",
            "0-0",
        ],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert out.returncode == 0, out.stderr
    assert "affinity=0x1" in out.stdout and "exit=0" in out.stdout
    assert (tmp_path / "run.out.txt").read_text().strip() == "0x1 ['a', 'b c']"
    assert (tmp_path / "run.pid").read_text().strip().isdigit()


def test_the_launcher_returns_the_exit_code_of_the_script(tmp_path):
    probe = tmp_path / "fail.py"
    probe.write_text("raise SystemExit(3)\n")
    out = subprocess.run(
        [
            POWERSHELL,
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(ROOT / "scripts" / "launch_affinity.ps1"),
            "-Script",
            str(probe),
            "-Log",
            str(tmp_path / "run"),
            "-Threads",
            "0-0",
        ],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert out.returncode == 3 and "exit=3" in out.stdout
