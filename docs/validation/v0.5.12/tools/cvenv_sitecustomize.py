"""The container virtual environment's sitecustomize (v0.5.12, step 0; the maintainer's decision of
#218 comment 7190662570, item 1). Installed ONLY as ``.cache/v0512/cvenv/Lib/site-packages/
sitecustomize.py`` by ``sitecustomize_install.py``; the project's ``.venv`` does not change.

**The cause it addresses.** Since Python 3.12.4, ``os.mkdir(path, 0o700)`` on Windows creates the
folder with a restricted, protected ACL, and ``tempfile.mkdtemp`` uses that mode (the mitigation of
CVE-2024-4030; https://mail-archive.com/python-checkins@python.org/msg03194.html, read by the
maintainer on 2026-11-26). The ACL that this interpreter's ``python313.dll`` applies was read
from the DLL itself (the inspect unit labelled sddl-from-dll-2; quoted in
``step0/golden-before-findings.md``):
``D:P(A;OICI;FA;;;SY)(A;OICI;FA;;;BA)(A;OICI;FA;;;OW)``. An AppContainer process also needs its
container's SID in the list, so a folder made that way is closed to the container that made it.

**What it does, and only that.** In a process whose own token is in the AppContainer
``refute.v0512.offline`` (any other process: nothing happens), a call ``os.mkdir(path, 0o700)``
(no ``dir_fd``, a text path) creates the folder with that same ACL plus one entry,
``(A;OICI;FA;;;<the container's SID>)``. Every other call goes to the original ``os.mkdir``
unchanged. It widens access for no other user or SID, and it changes nothing but the permissions
of folders the contained process creates with mode ``0o700``.
"""

import os
import sys

CONTAINER = "refute.v0512.offline"
BASE_SDDL = "D:P(A;OICI;FA;;;SY)(A;OICI;FA;;;BA)(A;OICI;FA;;;OW)"


def _own_container_sid():
    import ctypes
    from ctypes import wintypes

    advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    userenv = ctypes.WinDLL("userenv", use_last_error=True)
    kernel32.GetCurrentProcess.restype = wintypes.HANDLE
    advapi32.OpenProcessToken.argtypes = [wintypes.HANDLE, wintypes.DWORD, ctypes.c_void_p]
    advapi32.GetTokenInformation.argtypes = [
        wintypes.HANDLE,
        ctypes.c_int,
        ctypes.c_void_p,
        wintypes.DWORD,
        ctypes.c_void_p,
    ]
    advapi32.ConvertSidToStringSidW.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
    userenv.DeriveAppContainerSidFromAppContainerName.argtypes = [ctypes.c_wchar_p, ctypes.c_void_p]
    kernel32.LocalFree.argtypes = [ctypes.c_void_p]
    advapi32.FreeSid.argtypes = [ctypes.c_void_p]

    def text(psid) -> str | None:
        s = ctypes.c_wchar_p()
        if not advapi32.ConvertSidToStringSidW(psid, ctypes.byref(s)):
            return None
        value = s.value
        kernel32.LocalFree(ctypes.cast(s, ctypes.c_void_p))
        return value

    token = wintypes.HANDLE()
    if not advapi32.OpenProcessToken(kernel32.GetCurrentProcess(), 0x0008, ctypes.byref(token)):
        return None
    buf = ctypes.create_string_buffer(512)
    size = wintypes.DWORD()
    ok = advapi32.GetTokenInformation(token, 31, buf, 512, ctypes.byref(size))
    kernel32.CloseHandle(token)
    if not ok:
        return None
    psid = ctypes.cast(buf, ctypes.POINTER(ctypes.c_void_p))[0]
    if not psid:
        return None  # not in an AppContainer
    mine = text(psid)
    named = ctypes.c_void_p()
    if userenv.DeriveAppContainerSidFromAppContainerName(CONTAINER, ctypes.byref(named)) != 0:
        return None
    expected = text(named)
    advapi32.FreeSid(named)
    return mine if mine and mine == expected else None


def _install() -> None:
    if sys.platform != "win32":
        return
    sid = _own_container_sid()
    if sid is None:
        return
    import ctypes
    from ctypes import wintypes

    advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    advapi32.ConvertStringSecurityDescriptorToSecurityDescriptorW.argtypes = [
        ctypes.c_wchar_p,
        wintypes.DWORD,
        ctypes.c_void_p,
        ctypes.c_void_p,
    ]
    kernel32.CreateDirectoryW.argtypes = [ctypes.c_wchar_p, ctypes.c_void_p]
    kernel32.LocalFree.argtypes = [ctypes.c_void_p]

    class SECURITY_ATTRIBUTES(ctypes.Structure):  # noqa: N801
        _fields_ = [
            ("nLength", wintypes.DWORD),
            ("lpSecurityDescriptor", ctypes.c_void_p),
            ("bInheritHandle", wintypes.BOOL),
        ]

    sddl = BASE_SDDL + f"(A;OICI;FA;;;{sid})"
    original = os.mkdir

    def mkdir(path, mode=0o777, *, dir_fd=None):
        target = os.fspath(path)
        if mode != 0o700 or dir_fd is not None or not isinstance(target, str):
            return original(path, mode, dir_fd=dir_fd)
        psd = ctypes.c_void_p()
        if not advapi32.ConvertStringSecurityDescriptorToSecurityDescriptorW(
            sddl, 1, ctypes.byref(psd), None
        ):
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            sa = SECURITY_ATTRIBUTES(ctypes.sizeof(SECURITY_ATTRIBUTES), psd, False)
            if not kernel32.CreateDirectoryW(target, ctypes.byref(sa)):
                err = ctypes.get_last_error()
                raise OSError(None, ctypes.FormatError(err), target, err)
        finally:
            kernel32.LocalFree(psd)

    mkdir.__wrapped__ = original
    mkdir.__doc__ = "os.mkdir, with the container's SID added for mode 0o700 (v0.5.12)."
    os.mkdir = mkdir
    os.refute_v0512_container_sid = sid


_install()
