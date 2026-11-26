"""Remove v0.5.12's AppContainer profile. For the maintainer to run; the session never does.

The maintainer's decision recorded in #218, comment 7202383280, item 6: the session created the
profile ``refute.v0512.offline`` (no capability; recorded in
``docs/validation/v0.5.12/container.json``) and does not remove it. This script follows v0.5.10's
``engines/delete_profile.py``.
- It derives the profile's SID and refuses to go on if it differs from the SID recorded in
  ``container.json``.
- It calls ``DeleteAppContainerProfile`` for that name.
- It checks that both things Windows created are gone: the registry key ``Mappings/<SID>`` under
  HKCU's ``Software/Classes/Local Settings/Software/Microsoft/Windows/CurrentVersion/AppContainer``,
  and the folder ``Packages/refute.v0512.offline`` under the local application-data folder.

It touches nothing else; the ACL grants inside the project are removed by separate icacls
commands (``close/appcontainer-commands.md``). Run it from the project folder with the project's
Python:

    .venv/Scripts/python.exe docs/validation/v0.5.12/close/delete_profile.py

It prints "removed" and exits 0 only when both are gone.
"""

from __future__ import annotations

import ctypes
import json
import os
import winreg
from pathlib import Path

NAME = "refute.v0512.offline"
RECORD = Path(__file__).resolve().parents[1] / "container.json"
MAPPINGS = (
    r"Software\Classes\Local Settings\Software\Microsoft\Windows\CurrentVersion"
    r"\AppContainer\Mappings"
)


def sid_of(name: str) -> str:
    userenv = ctypes.WinDLL("userenv")
    advapi32 = ctypes.WinDLL("advapi32")
    userenv.DeriveAppContainerSidFromAppContainerName.argtypes = [
        ctypes.c_wchar_p,
        ctypes.POINTER(ctypes.c_void_p),
    ]
    userenv.DeriveAppContainerSidFromAppContainerName.restype = ctypes.c_long
    advapi32.ConvertSidToStringSidW.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_wchar_p)]
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
    recorded = json.loads(RECORD.read_text(encoding="utf-8"))["appcontainer"]["sid"]
    if sid != recorded:
        print(f"refused: derived SID {sid} differs from the recorded {recorded}")
        return 2
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
