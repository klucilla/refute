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
  suspended, so no child can escape before the assignment, and the final reading waits
  until the job has no active process; on Linux through a supervisor process
  (``_reaper.py``) that is a child subreaper and waits for every process of the run.
  On Linux the total is the sum of their rusage, and never below the largest live
  reading. **Known limit:** the time of descendants reaped automatically by a parent that
  ignores SIGCHLD is lost and can add up, so the total can be below the real usage. Only
  a cgroup closes that: it is the docker backend's job on the VM, and this backend never
  runs a real paper;
- stops the run, and every process in it, when one of the guards fires:
  - ``threshold``: the CPU time reached F, the threshold of the WP2 grant;
  - ``active_time_limit``: the stage's active time limit;
  - ``no_progress``: neither the CPU time nor the log grew for ``no_progress`` seconds
    (progress signal ``cpu_or_output``, design 1.0.2);
- returns the exit code, the CPU time in microseconds (an int, for the WP2 accountant)
  and the reason it was stopped, if it was.

Only processes this backend started are ever stopped: the Job Object (Windows) or the
supervisor's own descendants (Linux), never anything found by name. Any error while
supervising stops the run before it propagates.
"""

from __future__ import annotations

import json
import math
import signal
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
        times = (self.active_time_limit_s, self.no_progress_s, self.poll_s)
        if not all(isinstance(t, int | float) and math.isfinite(t) and t > 0 for t in times):
            raise ValueError("time limits and the poll interval are positive and finite")


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
                tracker: _Tracker = _WindowsJob(spec, log)
            else:
                tracker = _Reaped(spec)
            return _supervise(spec, tracker)


def _supervise(spec: RunSpec, tracker: _Tracker) -> RunResult:
    start = time.monotonic()
    last_usage, last_size, last_progress = -1, -1, start
    stopped = None
    try:
        while True:
            exit_code = tracker.poll()
            usage = tracker.usage_usec()
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
        # exact on both platforms: the job's total after its last process ended, or the
        # supervisor's sum over every waited process
        final = tracker.final_usage_usec()
    finally:
        tracker.close()  # stops whatever is left of the run, also after an error
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
            # the process may still be suspended and outside the job: end it by its own
            # handle (the process this backend started), with a deadline
            _k32.TerminateJobObject(self.job, 1)
            self.proc.kill()
            self.proc.wait(timeout=_END_TIMEOUT_S)
            self.close()
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

    def _accounting(self) -> _Accounting:
        info = _Accounting()
        _win_check(
            _k32.QueryInformationJobObject(
                self.job, _ACCOUNTING, ctypes.byref(info), ctypes.sizeof(info), None
            ),
            "QueryInformationJobObject",
        )
        return info

    def usage_usec(self) -> int:
        info = self._accounting()
        # 100-nanosecond units -> microseconds; the job keeps the time of ended processes
        return int((info.TotalUserTime + info.TotalKernelTime) // 10)

    def _end_all(self) -> None:
        """Ends every process of the job and waits until none is active: process
        termination is asynchronous, so the final reading waits for it."""
        _win_check(_k32.TerminateJobObject(self.job, 1), "TerminateJobObject")
        self.proc.wait(timeout=_END_TIMEOUT_S)
        deadline = time.monotonic() + _END_TIMEOUT_S
        while self._accounting().ActiveProcesses:
            if time.monotonic() > deadline:
                raise OSError("processes of the job are still active after termination")
            time.sleep(0.02)

    def final_usage_usec(self) -> int:
        # children may outlive the first process: end them (they belong to this job)
        self._end_all()
        return self.usage_usec()

    def stop(self) -> None:
        self._end_all()

    def close(self) -> None:
        if self.job:
            _k32.TerminateJobObject(self.job, 1)  # nothing of the run outlives it
            _k32.CloseHandle(self.job)
            self.job = None


# ---- Linux: a subreaper supervisor ----------------------------------------------------------

_END_TIMEOUT_S = 30.0
_REAPER = Path(__file__).with_name("_reaper.py")


class _Reaped(_Tracker):
    """The run under ``_reaper.py``, which waits for every process of the run and writes
    its status (live estimate, then the exact final total) to a JSON file."""

    def __init__(self, spec: RunSpec) -> None:
        self.status_path = spec.log_path.with_name(spec.log_path.name + ".status.json")
        self.status_path.unlink(missing_ok=True)
        self.proc = subprocess.Popen(
            [
                sys.executable,
                "-I",
                str(_REAPER),
                str(self.status_path),
                str(spec.workdir),
                str(spec.log_path),
                "--",
                *spec.argv,
            ],
            env=spec.env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        self.status: dict = {"final": False, "usage_usec": 0}

    def _read(self) -> dict:
        try:
            self.status = json.loads(self.status_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            pass  # not written yet, or being replaced: keep the last reading
        return self.status

    def poll(self) -> int | None:
        ended = self.proc.poll() is not None  # read before the status: no race
        status = self._read()
        if status.get("final"):
            self._check(status)
            self.proc.wait(timeout=_END_TIMEOUT_S)
            return status["exit_code"]
        if ended:
            raise OSError(
                f"the run supervisor ended without a final status ({self.proc.returncode})"
            )
        return None

    def usage_usec(self) -> int:
        return int(self._read()["usage_usec"])

    @staticmethod
    def _check(status: dict) -> None:
        if status.get("error"):
            raise OSError(f"the run supervisor failed: {status['error']}")

    def _wait_final(self) -> dict:
        self.proc.wait(timeout=_END_TIMEOUT_S)
        status = self._read()
        if not status.get("final"):
            raise OSError("the run supervisor wrote no final status")
        self._check(status)
        return status

    def final_usage_usec(self) -> int:
        return int(self._wait_final()["usage_usec"])

    def stop(self) -> None:
        if self.proc.poll() is None:
            self.proc.send_signal(signal.SIGTERM)  # the supervisor this backend started
        self._wait_final()

    def close(self) -> None:
        if self.proc.poll() is None:
            self.proc.send_signal(signal.SIGTERM)
            try:
                self.proc.wait(timeout=_END_TIMEOUT_S)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait()
