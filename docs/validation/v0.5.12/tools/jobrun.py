"""Run one command in a Windows job object, optionally inside an AppContainer with no capability
(v0.5.12, charter step 0; adapted from v0.5.10's docs/validation/v0.5.10/engines/sandbox.py).

**The job object** holds the command and every descendant from the first instruction (the process
is created suspended and assigned before it resumes):
- processors 8 to 31 and BelowNormal priority, for every process of the tree;
- kill on close, so nothing outlives the unit;
- **accounting of the whole tree, terminated processes included:** CPU (user + kernel) and the IO
  counters. ``write_bytes`` is the job's WriteTransferCount: every byte written by any process of
  the tree to any file, pipe or device, files deleted afterwards included.
- **limits, enforced while it runs:** the job is terminated before its CPU or its written bytes
  pass the unit's allowance (polled each second), or at the timeout; the reason is recorded.

**The AppContainer** (``container=``) has no capability, so Windows denies every network
connection of the process and of all its descendants (they inherit the token). It can open only
files whose ACL grants its SID (``container_setup.py`` grants them, inside the project only). Its
profile is the one change outside the project, authorized by the maintainer (#218, comment
7173638284, item 3); the session never removes it (``delete_profile`` is the maintainer's).

Standard library only (ctypes).
"""

# ruff: noqa: N801  (the structures keep their Win32 names)
from __future__ import annotations

import ctypes
import os
import subprocess
import time
from ctypes import wintypes
from pathlib import Path

AFFINITY_MASK = 0xFFFFFF00  # processors 8 to 31

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)
userenv = ctypes.WinDLL("userenv", use_last_error=True)

_H, _D, _V = wintypes.HANDLE, wintypes.DWORD, ctypes.c_void_p
kernel32.CreateJobObjectW.restype = _H
kernel32.CreateJobObjectW.argtypes = [_V, ctypes.c_wchar_p]
kernel32.SetInformationJobObject.argtypes = [_H, ctypes.c_int, _V, _D]
kernel32.AssignProcessToJobObject.argtypes = [_H, _H]
kernel32.QueryInformationJobObject.argtypes = [_H, ctypes.c_int, _V, _D, _V]
kernel32.TerminateJobObject.argtypes = [_H, wintypes.UINT]
kernel32.WaitForSingleObject.argtypes = [_H, _D]
kernel32.WaitForSingleObject.restype = _D
kernel32.GetExitCodeProcess.argtypes = [_H, ctypes.POINTER(_D)]
kernel32.CloseHandle.argtypes = [_H]
kernel32.ResumeThread.argtypes = [_H]
kernel32.ResumeThread.restype = _D
kernel32.LocalFree.argtypes = [_V]
kernel32.InitializeProcThreadAttributeList.argtypes = [_V, _D, _D, ctypes.POINTER(ctypes.c_size_t)]
kernel32.UpdateProcThreadAttribute.argtypes = [_V, _D, ctypes.c_size_t, _V, ctypes.c_size_t, _V, _V]
kernel32.DeleteProcThreadAttributeList.argtypes = [_V]
kernel32.CreateProcessW.argtypes = [
    ctypes.c_wchar_p,
    ctypes.c_wchar_p,
    _V,
    _V,
    wintypes.BOOL,
    _D,
    _V,
    ctypes.c_wchar_p,
    _V,
    _V,
]
userenv.DeriveAppContainerSidFromAppContainerName.argtypes = [ctypes.c_wchar_p, ctypes.POINTER(_V)]
userenv.DeriveAppContainerSidFromAppContainerName.restype = ctypes.c_long
userenv.CreateAppContainerProfile.argtypes = [
    ctypes.c_wchar_p,
    ctypes.c_wchar_p,
    ctypes.c_wchar_p,
    _V,
    _D,
    ctypes.POINTER(_V),
]
userenv.CreateAppContainerProfile.restype = ctypes.c_long
advapi32.FreeSid.argtypes = [_V]
advapi32.ConvertSidToStringSidW.argtypes = [_V, ctypes.POINTER(ctypes.c_wchar_p)]
HRESULT_ALREADY_EXISTS = -2147024713  # HRESULT_FROM_WIN32(ERROR_ALREADY_EXISTS)

EXTENDED_STARTUPINFO_PRESENT = 0x00080000
CREATE_SUSPENDED = 0x00000004
CREATE_UNICODE_ENVIRONMENT = 0x00000400
CREATE_NO_WINDOW = 0x08000000
BELOW_NORMAL_PRIORITY_CLASS = 0x00004000
PROC_THREAD_ATTRIBUTE_SECURITY_CAPABILITIES = 0x00020009
STARTF_USESTDHANDLES = 0x00000100
JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000
JOB_OBJECT_LIMIT_AFFINITY = 0x00000010
JOB_OBJECT_LIMIT_PRIORITY_CLASS = 0x00000020
JobObjectBasicAndIoAccountingInformation = 8
JobObjectExtendedLimitInformation = 9
WAIT_TIMEOUT = 0x00000102


class SECURITY_CAPABILITIES(ctypes.Structure):
    _fields_ = [
        ("AppContainerSid", ctypes.c_void_p),
        ("Capabilities", ctypes.c_void_p),
        ("CapabilityCount", wintypes.DWORD),
        ("Reserved", wintypes.DWORD),
    ]


class STARTUPINFOW(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD),
        ("lpReserved", wintypes.LPWSTR),
        ("lpDesktop", wintypes.LPWSTR),
        ("lpTitle", wintypes.LPWSTR),
        ("dwX", wintypes.DWORD),
        ("dwY", wintypes.DWORD),
        ("dwXSize", wintypes.DWORD),
        ("dwYSize", wintypes.DWORD),
        ("dwXCountChars", wintypes.DWORD),
        ("dwYCountChars", wintypes.DWORD),
        ("dwFillAttribute", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("wShowWindow", wintypes.WORD),
        ("cbReserved2", wintypes.WORD),
        ("lpReserved2", ctypes.c_void_p),
        ("hStdInput", wintypes.HANDLE),
        ("hStdOutput", wintypes.HANDLE),
        ("hStdError", wintypes.HANDLE),
    ]


class STARTUPINFOEXW(ctypes.Structure):
    _fields_ = [("StartupInfo", STARTUPINFOW), ("lpAttributeList", ctypes.c_void_p)]


class PROCESS_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("hProcess", wintypes.HANDLE),
        ("hThread", wintypes.HANDLE),
        ("dwProcessId", wintypes.DWORD),
        ("dwThreadId", wintypes.DWORD),
    ]


class IO_COUNTERS(ctypes.Structure):
    _fields_ = [
        ("ReadOperationCount", ctypes.c_ulonglong),
        ("WriteOperationCount", ctypes.c_ulonglong),
        ("OtherOperationCount", ctypes.c_ulonglong),
        ("ReadTransferCount", ctypes.c_ulonglong),
        ("WriteTransferCount", ctypes.c_ulonglong),
        ("OtherTransferCount", ctypes.c_ulonglong),
    ]


class JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("PerProcessUserTimeLimit", ctypes.c_longlong),
        ("PerJobUserTimeLimit", ctypes.c_longlong),
        ("LimitFlags", wintypes.DWORD),
        ("MinimumWorkingSetSize", ctypes.c_size_t),
        ("MaximumWorkingSetSize", ctypes.c_size_t),
        ("ActiveProcessLimit", wintypes.DWORD),
        ("Affinity", ctypes.c_size_t),
        ("PriorityClass", wintypes.DWORD),
        ("SchedulingClass", wintypes.DWORD),
    ]


class JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("BasicLimitInformation", JOBOBJECT_BASIC_LIMIT_INFORMATION),
        ("IoInfo", IO_COUNTERS),
        ("ProcessMemoryLimit", ctypes.c_size_t),
        ("JobMemoryLimit", ctypes.c_size_t),
        ("PeakProcessMemoryUsed", ctypes.c_size_t),
        ("PeakJobMemoryUsed", ctypes.c_size_t),
    ]


class JOBOBJECT_BASIC_ACCOUNTING_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("TotalUserTime", ctypes.c_longlong),
        ("TotalKernelTime", ctypes.c_longlong),
        ("ThisPeriodTotalUserTime", ctypes.c_longlong),
        ("ThisPeriodTotalKernelTime", ctypes.c_longlong),
        ("TotalPageFaultCount", wintypes.DWORD),
        ("TotalProcesses", wintypes.DWORD),
        ("ActiveProcesses", wintypes.DWORD),
        ("TotalTerminatedProcesses", wintypes.DWORD),
    ]


class JOBOBJECT_BASIC_AND_IO_ACCOUNTING_INFORMATION(ctypes.Structure):
    _fields_ = [("BasicInfo", JOBOBJECT_BASIC_ACCOUNTING_INFORMATION), ("IoInfo", IO_COUNTERS)]


def _check(ok, what: str):
    if not ok:
        raise OSError(ctypes.get_last_error(), f"{what} failed")
    return ok


# ---- the AppContainer -------------------------------------------------------------------------


def ensure_profile(name: str, display: str, description: str) -> str:
    """Create the AppContainer profile with no capability, once; 'created' or 'existed'."""
    psid = ctypes.c_void_p()
    hr = userenv.CreateAppContainerProfile(name, display, description, None, 0, ctypes.byref(psid))
    if hr == 0:
        advapi32.FreeSid(psid.value)
        return "created"
    if hr == HRESULT_ALREADY_EXISTS:
        return "existed"
    raise OSError(hr, f"CreateAppContainerProfile failed, HRESULT {hr & 0xFFFFFFFF:#010x}")


def container_sid(name: str) -> tuple[ctypes.c_void_p, str]:
    """The AppContainer SID derived from its name (creates nothing)."""
    psid = ctypes.c_void_p()
    hr = userenv.DeriveAppContainerSidFromAppContainerName(name, ctypes.byref(psid))
    if hr != 0:
        raise OSError(hr, "DeriveAppContainerSidFromAppContainerName failed")
    s = ctypes.c_wchar_p()
    _check(advapi32.ConvertSidToStringSidW(psid.value, ctypes.byref(s)), "ConvertSidToStringSidW")
    text = s.value
    kernel32.LocalFree(ctypes.cast(s, ctypes.c_void_p).value)
    return psid, text


# ---- the job ----------------------------------------------------------------------------------


def _env_block(env: dict[str, str]) -> ctypes.Array:
    text = "".join(f"{k}={v}\0" for k, v in sorted(env.items(), key=lambda kv: kv[0].upper()))
    return ctypes.create_unicode_buffer(text + "\0")


def _account(job) -> dict:
    a = JOBOBJECT_BASIC_AND_IO_ACCOUNTING_INFORMATION()
    kernel32.QueryInformationJobObject(
        job,
        JobObjectBasicAndIoAccountingInformation,
        ctypes.addressof(a),
        ctypes.sizeof(a),
        None,
    )
    b, io = a.BasicInfo, a.IoInfo
    return {
        "cpu_s": (b.TotalUserTime + b.TotalKernelTime) / 1e7,
        "processes": b.TotalProcesses,
        "active": b.ActiveProcesses,
        "write_bytes": io.WriteTransferCount,
        "read_bytes": io.ReadTransferCount,
        "other_bytes": io.OtherTransferCount,
        "write_ops": io.WriteOperationCount,
    }


def run(
    argv: list[str],
    cwd: Path,
    stdout_path: Path,
    stderr_path: Path,
    *,
    env: dict[str, str] | None = None,
    container: str | None = None,
    cpu_limit_s: float = float("inf"),
    write_limit_bytes: float = float("inf"),
    timeout_s: float = 1800.0,
) -> dict:
    """Run argv in a job (and the named AppContainer if given). Returns a plain record."""
    attr = None
    keep = []
    if container is not None:
        psid, _ = container_sid(container)
        keep.append(psid)  # the SID must outlive CreateProcessW
        caps = SECURITY_CAPABILITIES(psid.value, None, 0, 0)
        keep.append(caps)
        size = ctypes.c_size_t()
        kernel32.InitializeProcThreadAttributeList(None, 1, 0, ctypes.byref(size))
        attr = ctypes.create_string_buffer(size.value)
        _check(
            kernel32.InitializeProcThreadAttributeList(
                ctypes.addressof(attr), 1, 0, ctypes.byref(size)
            ),
            "InitializeProcThreadAttributeList",
        )
        _check(
            kernel32.UpdateProcThreadAttribute(
                ctypes.addressof(attr),
                0,
                PROC_THREAD_ATTRIBUTE_SECURITY_CAPABILITIES,
                ctypes.addressof(caps),
                ctypes.sizeof(caps),
                None,
                None,
            ),
            "UpdateProcThreadAttribute",
        )

    import msvcrt

    out = open(stdout_path, "wb")
    err = open(stderr_path, "wb")
    h_out = msvcrt.get_osfhandle(out.fileno())
    h_err = msvcrt.get_osfhandle(err.fileno())
    os.set_handle_inheritable(h_out, True)
    os.set_handle_inheritable(h_err, True)
    si = STARTUPINFOEXW()
    si.StartupInfo.cb = ctypes.sizeof(si)
    si.StartupInfo.dwFlags = STARTF_USESTDHANDLES
    si.StartupInfo.hStdInput = None
    si.StartupInfo.hStdOutput = h_out
    si.StartupInfo.hStdError = h_err
    si.lpAttributeList = ctypes.addressof(attr) if attr is not None else None
    pi = PROCESS_INFORMATION()

    job = kernel32.CreateJobObjectW(None, None)
    _check(job, "CreateJobObjectW")
    lim = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
    lim.BasicLimitInformation.LimitFlags = (
        JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        | JOB_OBJECT_LIMIT_AFFINITY
        | JOB_OBJECT_LIMIT_PRIORITY_CLASS
    )
    lim.BasicLimitInformation.Affinity = AFFINITY_MASK
    lim.BasicLimitInformation.PriorityClass = BELOW_NORMAL_PRIORITY_CLASS
    _check(
        kernel32.SetInformationJobObject(
            job, JobObjectExtendedLimitInformation, ctypes.addressof(lim), ctypes.sizeof(lim)
        ),
        "SetInformationJobObject",
    )
    cmdline = ctypes.create_unicode_buffer(subprocess.list2cmdline(argv))
    envb = _env_block(env) if env is not None else None
    flags = CREATE_SUSPENDED | CREATE_NO_WINDOW | BELOW_NORMAL_PRIORITY_CLASS
    flags |= CREATE_UNICODE_ENVIRONMENT
    if attr is not None:
        flags |= EXTENDED_STARTUPINFO_PRESENT
    started = time.time()
    ok = kernel32.CreateProcessW(
        None,
        cmdline,
        None,
        None,
        True,
        flags,
        ctypes.addressof(envb) if envb is not None else None,
        str(cwd),
        ctypes.addressof(si),
        ctypes.addressof(pi),
    )
    os.set_handle_inheritable(h_out, False)
    os.set_handle_inheritable(h_err, False)
    if not ok:
        e = ctypes.get_last_error()
        out.close()
        err.close()
        kernel32.CloseHandle(job)
        raise OSError(e, f"CreateProcessW failed for {argv[0]}")
    stopped = None
    try:
        _check(kernel32.AssignProcessToJobObject(job, pi.hProcess), "AssignProcessToJobObject")
        kernel32.ResumeThread(pi.hThread)
        while True:
            wait = kernel32.WaitForSingleObject(pi.hProcess, 1000)
            acct = _account(job)
            if acct["cpu_s"] > cpu_limit_s:
                stopped = "cpu allowance"
            elif acct["write_bytes"] > write_limit_bytes:
                stopped = "disk allowance"
            elif time.time() - started > timeout_s:
                stopped = "timeout"
            if stopped:
                kernel32.TerminateJobObject(job, 1)
                kernel32.WaitForSingleObject(pi.hProcess, 30000)
                break
            if wait != WAIT_TIMEOUT:
                break
        code = wintypes.DWORD()
        kernel32.GetExitCodeProcess(pi.hProcess, ctypes.byref(code))
        for _ in range(50):  # descendants may outlive the main process
            if _account(job)["active"] == 0:
                break
            time.sleep(0.2)
        leftover = _account(job)["active"]
        if leftover:
            kernel32.TerminateJobObject(job, 1)
            time.sleep(0.5)
        acct = _account(job)
        acct.pop("active")
        return {
            "pid": pi.dwProcessId,
            "exit_code": code.value,
            "stopped": stopped,
            "leftover_processes_ended": leftover,
            "wall_s": round(time.time() - started, 3),
            "container": container,
            **acct,
        }
    finally:
        kernel32.CloseHandle(pi.hThread)
        kernel32.CloseHandle(pi.hProcess)
        kernel32.CloseHandle(job)
        if attr is not None:
            kernel32.DeleteProcThreadAttributeList(ctypes.addressof(attr))
        out.close()
        err.close()
