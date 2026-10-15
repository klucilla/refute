"""Sandbox runner of the ML pack: the ``subprocess`` backend (WP3 W3.8 to W3.10).

One interface, two backends (W3.8): ``docker`` runs on the VM (WP6); ``subprocess``,
here, runs a command of a synthetic repository directly, for CI and local tests. It is
**not** an isolation boundary: it never runs third-party code (CLAUDE.md, standing
approval: running third-party code needs the maintainer and the VM).

For each run the backend:

- starts ``argv`` (a list, never a shell) in ``workdir`` with the given environment,
  stdout and stderr to one log file;
- accounts the CPU time of **every process of the run**, children included (W3.10):
  on Windows through a Job Object to which the process is assigned while still
  suspended, so no child can escape before the assignment; on Linux through the
  process's own session (``/proc`` while it runs, ``wait4`` rusage at the end);
- stops the run, and every process in it, when one of the guards fires:
  - ``threshold``: the CPU time reached F, the threshold of the WP2 grant;
  - ``active_time_limit``: the stage's active time limit;
  - ``no_progress``: neither the CPU time nor the log grew for ``no_progress`` seconds
    (progress signal ``cpu_or_output``, design 1.0.2);
- returns the exit code, the CPU time in microseconds (an int, for the WP2 accountant)
  and the reason it was stopped, if it was.

Only processes this backend started are ever stopped: the Job Object (Windows) or the
process group of the run (Linux), never anything found by name.
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

STOP_THRESHOLD = "threshold"
STOP_ACTIVE_TIME = "active_time_limit"
STOP_NO_PROGRESS = "no_progress"


@dataclass(frozen=True)
class RunSpec:
    argv: list[str]
    workdir: Path
    env: dict[str, str]
    log_path: Path
    threshold_usec: int | None  # F of the grant; None only in tests that need no budget
    active_time_limit_s: float
    no_progress_s: float
    poll_s: float = 0.2

    def __post_init__(self) -> None:
        if (
            not isinstance(self.argv, list)
            or not self.argv
            or any(not isinstance(a, str) for a in self.argv)
        ):
            raise ValueError("argv is a non-empty list of strings")
        if self.threshold_usec is not None and (
            type(self.threshold_usec) is not int or self.threshold_usec <= 0
        ):
            raise ValueError("threshold_usec is a positive int")
        if not (self.active_time_limit_s > 0 and self.no_progress_s > 0 and self.poll_s > 0):
            raise ValueError("time limits and the poll interval are positive")


@dataclass(frozen=True)
class RunResult:
    exit_code: int | None  # None when the run was stopped
    usage_usec: int
    stopped: str | None
    elapsed_s: float
    log_path: Path


class SubprocessBackend:
    name = "subprocess"

    def run(self, spec: RunSpec) -> RunResult:
        spec.log_path.parent.mkdir(parents=True, exist_ok=True)
        with spec.log_path.open("wb") as log:
            if sys.platform == "win32":
                tracker = _WindowsJob(spec, log)
            else:
                tracker = _PosixSession(spec, log)
            return _supervise(spec, tracker)


def _supervise(spec: RunSpec, tracker: _Tracker) -> RunResult:
    start = time.monotonic()
    last_usage, last_size, last_progress = -1, -1, start
    seen = 0  # the largest usage observed while running
    stopped = None
    try:
        while True:
            exit_code = tracker.poll()
            usage = tracker.usage_usec()
            seen = max(seen, usage)
            now = time.monotonic()
            if exit_code is not None:
                break
            size = spec.log_path.stat().st_size if spec.log_path.exists() else 0
            if usage > last_usage or size > last_size:
                last_usage, last_size, last_progress = usage, size, now
            if spec.threshold_usec is not None and usage >= spec.threshold_usec:
                stopped = STOP_THRESHOLD
            elif now - start >= spec.active_time_limit_s:
                stopped = STOP_ACTIVE_TIME
            elif now - last_progress >= spec.no_progress_s:
                stopped = STOP_NO_PROGRESS
            if stopped:
                tracker.stop()
                exit_code = None
                break
            time.sleep(spec.poll_s)
        # a descendant stopped before its parent waited for it is in the observed usage
        # but not in the parent's final rusage: never report less than what was seen
        final = max(tracker.final_usage_usec(), seen)
    finally:
        tracker.close()
    return RunResult(exit_code, final, stopped, time.monotonic() - start, spec.log_path)


class _Tracker:
    def poll(self) -> int | None: ...
    def usage_usec(self) -> int: ...
    def final_usage_usec(self) -> int: ...
    def stop(self) -> None: ...
    def close(self) -> None: ...


# ---- Windows: a Job Object, the process assigned while suspended ---------------------------

if sys.platform == "win32":
    import ctypes
    from ctypes import wintypes

    _k32 = ctypes.WinDLL("kernel32", use_last_error=True)

    class _IoCounters(ctypes.Structure):
        _fields_ = [
            (name, ctypes.c_ulonglong)
            for name in (
                "ReadOperationCount",
                "WriteOperationCount",
                "OtherOperationCount",
                "ReadTransferCount",
                "WriteTransferCount",
                "OtherTransferCount",
            )
        ]

    class _BasicLimit(ctypes.Structure):
        _fields_ = [
            ("PerProcessUserTimeLimit", ctypes.c_int64),
            ("PerJobUserTimeLimit", ctypes.c_int64),
            ("LimitFlags", wintypes.DWORD),
            ("MinimumWorkingSetSize", ctypes.c_size_t),
            ("MaximumWorkingSetSize", ctypes.c_size_t),
            ("ActiveProcessLimit", wintypes.DWORD),
            ("Affinity", ctypes.c_size_t),
            ("PriorityClass", wintypes.DWORD),
            ("SchedulingClass", wintypes.DWORD),
        ]

    class _ExtendedLimit(ctypes.Structure):
        _fields_ = [
            ("BasicLimitInformation", _BasicLimit),
            ("IoInfo", _IoCounters),
            ("ProcessMemoryLimit", ctypes.c_size_t),
            ("JobMemoryLimit", ctypes.c_size_t),
            ("PeakProcessMemoryUsed", ctypes.c_size_t),
            ("PeakJobMemoryUsed", ctypes.c_size_t),
        ]

    class _Accounting(ctypes.Structure):
        _fields_ = [
            ("TotalUserTime", ctypes.c_int64),
            ("TotalKernelTime", ctypes.c_int64),
            ("ThisPeriodTotalUserTime", ctypes.c_int64),
            ("ThisPeriodTotalKernelTime", ctypes.c_int64),
            ("TotalPageFaultCount", wintypes.DWORD),
            ("TotalProcesses", wintypes.DWORD),
            ("ActiveProcesses", wintypes.DWORD),
            ("TotalTerminatedProcesses", wintypes.DWORD),
        ]

    class _ThreadEntry(ctypes.Structure):
        _fields_ = [
            ("dwSize", wintypes.DWORD),
            ("cntUsage", wintypes.DWORD),
            ("th32ThreadID", wintypes.DWORD),
            ("th32OwnerProcessID", wintypes.DWORD),
            ("tpBasePri", wintypes.LONG),
            ("tpDeltaPri", wintypes.LONG),
            ("dwFlags", wintypes.DWORD),
        ]

    _k32.CreateJobObjectW.restype = wintypes.HANDLE
    _k32.CreateJobObjectW.argtypes = [wintypes.LPVOID, wintypes.LPCWSTR]
    _k32.SetInformationJobObject.argtypes = [
        wintypes.HANDLE,
        ctypes.c_int,
        wintypes.LPVOID,
        wintypes.DWORD,
    ]
    _k32.QueryInformationJobObject.argtypes = [
        wintypes.HANDLE,
        ctypes.c_int,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.LPVOID,
    ]
    _k32.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
    _k32.TerminateJobObject.argtypes = [wintypes.HANDLE, wintypes.UINT]
    _k32.CloseHandle.argtypes = [wintypes.HANDLE]
    _k32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    _k32.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
    _k32.Thread32First.argtypes = [wintypes.HANDLE, ctypes.POINTER(_ThreadEntry)]
    _k32.Thread32Next.argtypes = [wintypes.HANDLE, ctypes.POINTER(_ThreadEntry)]
    _k32.OpenThread.restype = wintypes.HANDLE
    _k32.OpenThread.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    _k32.ResumeThread.argtypes = [wintypes.HANDLE]
    _k32.ResumeThread.restype = wintypes.DWORD

    _ACCOUNTING = 1
    _EXTENDED_LIMIT = 9
    _KILL_ON_JOB_CLOSE = 0x2000
    _CREATE_SUSPENDED = 0x00000004
    _TH32CS_SNAPTHREAD = 0x00000004
    _THREAD_SUSPEND_RESUME = 0x0002
    _INVALID_HANDLE = wintypes.HANDLE(-1).value


def _win_check(ok: object, what: str) -> None:
    if not ok:
        raise OSError(ctypes.get_last_error(), f"{what} failed")


class _WindowsJob(_Tracker):
    def __init__(self, spec: RunSpec, log) -> None:
        self.job = _k32.CreateJobObjectW(None, None)
        _win_check(self.job, "CreateJobObjectW")
        limit = _ExtendedLimit()
        limit.BasicLimitInformation.LimitFlags = _KILL_ON_JOB_CLOSE
        _win_check(
            _k32.SetInformationJobObject(
                self.job, _EXTENDED_LIMIT, ctypes.byref(limit), ctypes.sizeof(limit)
            ),
            "SetInformationJobObject",
        )
        self.proc = subprocess.Popen(
            spec.argv,
            cwd=spec.workdir,
            env=spec.env,
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=subprocess.STDOUT,
            creationflags=_CREATE_SUSPENDED,
        )
        try:
            _win_check(
                _k32.AssignProcessToJobObject(self.job, int(self.proc._handle)),
                "AssignProcessToJobObject",
            )
            self._resume(self.proc.pid)
        except BaseException:
            _k32.TerminateJobObject(self.job, 1)
            self.proc.wait()
            raise

    @staticmethod
    def _resume(pid: int) -> None:
        snapshot = _k32.CreateToolhelp32Snapshot(_TH32CS_SNAPTHREAD, 0)
        if snapshot in (None, _INVALID_HANDLE):
            raise OSError(ctypes.get_last_error(), "CreateToolhelp32Snapshot failed")
        resumed = 0
        try:
            entry = _ThreadEntry()
            entry.dwSize = ctypes.sizeof(entry)
            more = _k32.Thread32First(snapshot, ctypes.byref(entry))
            while more:
                if entry.th32OwnerProcessID == pid:
                    thread = _k32.OpenThread(_THREAD_SUSPEND_RESUME, False, entry.th32ThreadID)
                    _win_check(thread, "OpenThread")
                    try:
                        if _k32.ResumeThread(thread) == 0xFFFFFFFF:
                            raise OSError(ctypes.get_last_error(), "ResumeThread failed")
                        resumed += 1
                    finally:
                        _k32.CloseHandle(thread)
                more = _k32.Thread32Next(snapshot, ctypes.byref(entry))
        finally:
            _k32.CloseHandle(snapshot)
        if resumed == 0:
            raise OSError("the suspended process has no thread to resume")

    def poll(self) -> int | None:
        return self.proc.poll()

    def usage_usec(self) -> int:
        info = _Accounting()
        _win_check(
            _k32.QueryInformationJobObject(
                self.job, _ACCOUNTING, ctypes.byref(info), ctypes.sizeof(info), None
            ),
            "QueryInformationJobObject",
        )
        # 100-nanosecond units -> microseconds
        return int((info.TotalUserTime + info.TotalKernelTime) // 10)

    def final_usage_usec(self) -> int:
        # children may outlive the first process: end them (they belong to this job)
        _k32.TerminateJobObject(self.job, 1)
        self.proc.wait()
        return self.usage_usec()

    def stop(self) -> None:
        _k32.TerminateJobObject(self.job, 1)
        self.proc.wait()

    def close(self) -> None:
        if self.job:
            _k32.CloseHandle(self.job)
            self.job = None


# ---- Linux: the run's own session ------------------------------------------------------------


class _PosixSession(_Tracker):
    def __init__(self, spec: RunSpec, log) -> None:
        self.proc = subprocess.Popen(
            spec.argv,
            cwd=spec.workdir,
            env=spec.env,
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        self.sid = self.proc.pid
        self.exit_code: int | None = None
        self.rusage_usec: int | None = None
        self.ticks = os.sysconf("SC_CLK_TCK")

    def poll(self) -> int | None:
        if self.exit_code is None:
            pid, status, rusage = os.wait4(self.proc.pid, os.WNOHANG)
            if pid:
                self._record(status, rusage)
        return self.exit_code

    def _record(self, status: int, rusage) -> None:
        self.exit_code = os.waitstatus_to_exitcode(status)
        self.proc.returncode = self.exit_code
        self.rusage_usec = int(round((rusage.ru_utime + rusage.ru_stime) * 1_000_000))

    def usage_usec(self) -> int:
        """While running: user and system time of every live process of the session, and
        of the children they already waited for (cutime, cstime), from /proc."""
        if self.rusage_usec is not None:
            return self.rusage_usec
        total = 0
        for entry in os.listdir("/proc"):
            if not entry.isdigit():
                continue
            try:
                with open(f"/proc/{entry}/stat", encoding="ascii") as handle:
                    stat = handle.read()
            except OSError:
                continue
            fields = stat[stat.rindex(")") + 2 :].split()
            if int(fields[3]) != self.sid:  # field 6 of stat: the session id
                continue
            total += sum(int(fields[i]) for i in (11, 12, 13, 14))  # utime stime cutime cstime
        return total * 1_000_000 // self.ticks

    def final_usage_usec(self) -> int:
        if self.exit_code is None:
            _, status, rusage = os.wait4(self.proc.pid, 0)
            self._record(status, rusage)
        self._kill_group()  # descendants left behind belong to the run's group
        return self.rusage_usec or 0

    def _kill_group(self) -> None:
        import signal

        try:
            os.killpg(self.sid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass

    def stop(self) -> None:
        self._kill_group()
        if self.exit_code is None:
            _, status, rusage = os.wait4(self.proc.pid, 0)
            self._record(status, rusage)

    def close(self) -> None:
        pass
