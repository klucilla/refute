"""Remove the AppContainer profile of part (f). For the maintainer to run; the session never does.

The maintainer's decision of 2026-11-24 (#218, comment 7140572901): the session created the
profile ``refute.v0510.engines`` (no capability) and does not delete it; the removal is the
maintainer's. This script calls ``DeleteAppContainerProfile`` for that name and then checks that
both things Windows created are gone:
- the registry key ``Mappings/<SID>`` under HKCU's
  ``Software/Classes/Local Settings/Software/Microsoft/Windows/CurrentVersion/AppContainer``;
- the folder ``Packages/refute.v0510.engines`` under the local application-data folder.

It touches nothing else. Run it from the project folder with the project's Python:

    .venv/Scripts/python.exe docs/validation/v0.5.10/engines/delete_profile.py

It prints "removed" and exits 0 only when both are gone.
"""

from __future__ import annotations

import ctypes
import os
import winreg
from pathlib import Path

NAME = "refute.v0510.engines"
MAPPINGS = (
    r"Software\Classes\Local Settings\Software\Microsoft\Windows\CurrentVersion"
    r"\AppContainer\Mappings"
)


def sid_of(name: str) -> str:
    userenv = ctypes.WinDLL("userenv")
    advapi32 = ctypes.WinDLL("advapi32")
    kernel32 = ctypes.WinDLL("kernel32")
    userenv.DeriveAppContainerSidFromAppContainerName.argtypes = [
        ctypes.c_wchar_p,
        ctypes.POINTER(ctypes.c_void_p),
    ]
    userenv.DeriveAppContainerSidFromAppContainerName.restype = ctypes.c_long
    advapi32.ConvertSidToStringSidW.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_wchar_p)]
    kernel32.LocalFree.argtypes = [ctypes.c_void_p]
    psid = ctypes.c_void_p()
    hr = userenv.DeriveAppContainerSidFromAppContainerName(name, ctypes.byref(psid))
    if hr != 0:
        raise OSError(hr, "DeriveAppContainerSidFromAppContainerName failed")
    text = ctypes.c_wchar_p()
    if not advapi32.ConvertSidToStringSidW(psid.value, ctypes.byref(text)):
        raise OSError("ConvertSidToStringSidW failed")
    return text.value


def key_exists(sid: str) -> bool:
    try:
        winreg.CloseKey(winreg.OpenKey(winreg.HKEY_CURRENT_USER, MAPPINGS + "\\" + sid))
        return True
    except FileNotFoundError:
        return False


def main() -> int:
    sid = sid_of(NAME)
    folder = Path(os.environ["LOCAL" + "APP" + "DATA"]) / "Packages" / NAME
    print("before: key present", key_exists(sid), "; folder present", folder.exists())
    userenv = ctypes.WinDLL("userenv")
    userenv.DeleteAppContainerProfile.argtypes = [ctypes.c_wchar_p]
    userenv.DeleteAppContainerProfile.restype = ctypes.c_long
    hr = userenv.DeleteAppContainerProfile(NAME)
    print(f"DeleteAppContainerProfile: HRESULT {hr & 0xFFFFFFFF:#010x}")
    gone_key = not key_exists(sid)
    gone_folder = not folder.exists()
    print("after: key gone", gone_key, "; folder gone", gone_folder)
    if gone_key and gone_folder:
        print("removed")
        return 0
    print("NOT fully removed")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
