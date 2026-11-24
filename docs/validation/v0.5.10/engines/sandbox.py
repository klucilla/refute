"""The launcher of part (f): run one worker in a Windows AppContainer (Codex's blocking items 3, 5).

The worker runs as a process whose token is an AppContainer token with **no capability**, so the
operating system denies it every network connection (the Windows Filtering Platform blocks an
AppContainer without the internetClient, internetClientServer or privateNetworkClientServer
capabilities), and it can open only files whose ACL grants its AppContainer SID. ACL entries are
added only to folders under ``.cache/v0510/``.

**The one change outside the project** (the maintainer's decision of 2026-11-24, #218 comment
7140572901): Windows needs an AppContainer profile to start such a process, so ``ensure_profile``
creates the profile ``refute.v0510.engines`` with no capability. Windows records it as a key
``Mappings/<SID>`` under HKCU's ``Software/Classes/Local Settings/Software/Microsoft/Windows/
CurrentVersion/AppContainer`` (backslashes in the registry) and a folder ``Packages/
refute.v0510.engines`` under the local application-data folder. The session never deletes it:
the removal is the maintainer's, with ``delete_profile.py``.

Each worker:
- is created suspended inside a Job object that kills it with the job, holds every child process
  to processors 8 to 31 and to BelowNormal priority, and accounts the CPU of all of them;
- gets a fresh private home, temp and cache folders (HOME, USERPROFILE, the two
  application-data variables, TEMP, TMP, XDG_*, MPLCONFIGDIR, NUMBA_CACHE_DIR), and runs Python
  with ``-I`` (isolated mode:
  no PYTHON* variables, no user site, no script folder on the path);
- exchanges only file names and plain JSON with the launcher.

Standard library only (ctypes); runs in the project's environment.
"""

# ruff: noqa: N801  (the structures keep their Win32 names)
from __future__ import annotations

import ctypes
import os
import subprocess
import time
from ctypes import wintypes
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[4]
CACHE_ROOT = (PROJECT / ".cache" / "v0510").resolve()
CONTAINER_NAME = "refute.v0510.engines"
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
HRESULT_ALREADY_EXISTS = -2147024713  # HRESULT_FROM_WIN32(ERROR_ALREADY_EXISTS), 0x800700B7
advapi32.ConvertSidToStringSidW.argtypes = [_V, ctypes.POINTER(ctypes.c_wchar_p)]

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
JobObjectBasicAccountingInformation = 1
JobObjectExtendedLimitInformation = 9
WAIT_TIMEOUT = 0x00000102
INFINITE = 0xFFFFFFFF


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
    _fields_ = [(n, ctypes.c_ulonglong) for n in ("r", "w", "o", "rb", "wb", "ob")]


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


def _check(ok, what: str):
    if not ok:
        raise OSError(ctypes.get_last_error(), f"{what} failed")
    return ok


def ensure_profile() -> str:
    """Create the AppContainer profile with no capability, once; return 'created' or 'existed'."""
    psid = ctypes.c_void_p()
    hr = userenv.CreateAppContainerProfile(
        CONTAINER_NAME,
        "Refute v0.5.10 engines",
        "Refute v0.5.10 part (f): engine workers with no network capability",
        None,
        0,
        ctypes.byref(psid),
    )
    if hr == 0:
        advapi32.FreeSid(psid.value)
        return "created"
    if hr == HRESULT_ALREADY_EXISTS:
        return "existed"
    raise OSError(hr, f"CreateAppContainerProfile failed, HRESULT {hr & 0xFFFFFFFF:#010x}")


def container_sid() -> tuple[ctypes.c_void_p, str]:
    """The AppContainer SID derived from the container's name (no profile is created)."""
    psid = ctypes.c_void_p()
    hr = userenv.DeriveAppContainerSidFromAppContainerName(CONTAINER_NAME, ctypes.byref(psid))
    if hr != 0:
        raise OSError(hr, "DeriveAppContainerSidFromAppContainerName failed")
    s = ctypes.c_wchar_p()
    _check(advapi32.ConvertSidToStringSidW(psid.value, ctypes.byref(s)), "ConvertSidToStringSidW")
    text = s.value
    kernel32.LocalFree(ctypes.cast(s, ctypes.c_void_p).value)
    return psid, text


def _inside_cache(path: Path) -> Path:
    p = Path(path).resolve()
    if p != CACHE_ROOT and CACHE_ROOT not in p.parents:
        raise ValueError(f"refused: {p} is not under {CACHE_ROOT}")
    for q in [p, *p.parents]:
        if q == CACHE_ROOT.parent:
            break
        if q.is_symlink() or (q.exists() and os.path.isjunction(q)):
            raise ValueError(f"refused: {q} is a link or a junction")
    return p


def grant(path: Path, write: bool = False) -> None:
    """Grant the container SID read (or modify) on a folder under .cache/v0510, inherited."""
    p = _inside_cache(path)
    _, sid = container_sid()
    right = "(OI)(CI)(M)" if write else "(OI)(CI)(RX)"
    subprocess.run(
        ["icacls", str(p), "/grant", f"*{sid}:{right}", "/T", "/C", "/Q"],
        check=True,
        capture_output=True,
    )


def _env_block(env: dict[str, str]) -> ctypes.Array:
    text = "".join(f"{k}={v}\0" for k, v in sorted(env.items(), key=lambda kv: kv[0].upper()))
    return ctypes.create_unicode_buffer(text + "\0")


def private_env(run_dir: Path, workers: int) -> dict[str, str]:
    """A minimal environment whose home, temp and caches are fresh folders of this run."""
    run_dir = _inside_cache(run_dir)
    dirs = {}
    names = ("home", "ad", "lad", "tmp", "xdg_config", "xdg_cache", "mpl", "numba")
    for name in names:
        d = run_dir / "private" / name
        d.mkdir(parents=True, exist_ok=True)
        dirs[name] = str(d)
    for sub in ("xdg_config", "xdg_cache"):
        (Path(dirs[sub]) / "astropy").mkdir(exist_ok=True)
    sysroot = os.environ.get("SystemRoot", r"C:\Windows")
    return {
        "SystemRoot": sysroot,
        "windir": sysroot,
        "PATH": rf"{sysroot}\System32;{sysroot}",
        "HOME": dirs["home"],
        "USERPROFILE": dirs["home"],
        "APP" + "DATA": dirs["ad"],
        "LOCAL" + "APP" + "DATA": dirs["lad"],
        "TEMP": dirs["tmp"],
        "TMP": dirs["tmp"],
        "XDG_CONFIG_HOME": dirs["xdg_config"],
        "XDG_CACHE_HOME": dirs["xdg_cache"],
        "MPLCONFIGDIR": dirs["mpl"],
        "MPLBACKEND": "Agg",
        "NUMBA_CACHE_DIR": dirs["numba"],
        "NUMBA_NUM_THREADS": str(workers),
        "OMP_NUM_THREADS": "1",
        "OPENBLAS_NUM_THREADS": "1",
        "MKL_NUM_THREADS": "1",
        "PYTHONHASHSEED": "0",
        "NUMBER_OF_PROCESSORS": str(workers),
    }


def run(
    argv: list[str],
    cwd: Path,
    run_dir: Path,
    workers: int = 1,
    timeout_s: float = 1800.0,
) -> dict:
    """Run argv in the AppContainer; stdout and stderr go to run_dir. Returns a plain record."""
    run_dir = _inside_cache(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    env = private_env(run_dir, workers)
    ensure_profile()
    psid, sid_text = container_sid()
    _keep = psid  # the SID must outlive CreateProcessW
    caps = SECURITY_CAPABILITIES(psid.value, None, 0, 0)

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

    out = open(run_dir / "stdout.txt", "wb")
    err = open(run_dir / "stderr.txt", "wb")
    import msvcrt

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
    si.lpAttributeList = ctypes.addressof(attr)
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
    envb = _env_block(env)
    flags = (
        EXTENDED_STARTUPINFO_PRESENT
        | CREATE_SUSPENDED
        | CREATE_UNICODE_ENVIRONMENT
        | CREATE_NO_WINDOW
        | BELOW_NORMAL_PRIORITY_CLASS
    )
    started = time.time()
    ok = kernel32.CreateProcessW(
        None,
        cmdline,
        None,
        None,
        True,
        flags,
        ctypes.addressof(envb),
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
        raise OSError(e, "CreateProcessW failed")
    try:
        _check(kernel32.AssignProcessToJobObject(job, pi.hProcess), "AssignProcessToJobObject")
        kernel32.ResumeThread(pi.hThread)
        wait = kernel32.WaitForSingleObject(pi.hProcess, int(timeout_s * 1000))
        timed_out = wait == WAIT_TIMEOUT
        if timed_out:
            kernel32.TerminateJobObject(job, 1)
            kernel32.WaitForSingleObject(pi.hProcess, 30000)
        code = wintypes.DWORD()
        kernel32.GetExitCodeProcess(pi.hProcess, ctypes.byref(code))
        # Children may outlive the main process; give them a moment, then end the job.
        acct = JOBOBJECT_BASIC_ACCOUNTING_INFORMATION()
        for _ in range(50):
            kernel32.QueryInformationJobObject(
                job,
                JobObjectBasicAccountingInformation,
                ctypes.addressof(acct),
                ctypes.sizeof(acct),
                None,
            )
            if acct.ActiveProcesses == 0:
                break
            time.sleep(0.2)
        leftover = acct.ActiveProcesses
        if leftover:
            kernel32.TerminateJobObject(job, 1)
            time.sleep(0.5)
        kernel32.QueryInformationJobObject(
            job,
            JobObjectBasicAccountingInformation,
            ctypes.addressof(acct),
            ctypes.sizeof(acct),
            None,
        )
        return {
            "pid": pi.dwProcessId,
            "exit_code": code.value,
            "timed_out": timed_out,
            "leftover_processes_ended": leftover,
            "cpu_seconds": (acct.TotalUserTime + acct.TotalKernelTime) / 1e7,
            "processes": acct.TotalProcesses,
            "wall_seconds": round(time.time() - started, 3),
            "container_sid": sid_text,
        }
    finally:
        kernel32.CloseHandle(pi.hThread)
        kernel32.CloseHandle(pi.hProcess)
        kernel32.CloseHandle(job)
        out.close()
        err.close()
