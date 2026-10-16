"""A real JEA endpoint on the Windows CI runner (tests/vm/jea_integration.ps1).

Runs only on GitHub-hosted Actions Windows jobs, where the CI sets REFUTE_JEA_INTEGRATION=1
and the runner is an ephemeral machine with Administrator rights; it is skipped everywhere
else, and the PowerShell script refuses to run outside that environment too, because it
enables WinRM and registers session configurations. These variables guard against an
accidental run; they do not authenticate the machine. It checks, with disposable
endpoints shaped like RefuteVm (RestrictedRemoteServer, RunAsVirtualAccount, AccessMode
Local), the three causes the maintainer found when the RefuteVm session would not open
(2026-10-16), each with the failure it predicts and a positive control.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tests" / "vm" / "jea_integration.ps1"
FULLY_QUALIFIED = re.compile(r"^([A-Za-z]:\\|\\\\[^\\]+\\[^\\]+)")
PINS = (
    "RequiredVersion",
    "ModuleVersion",
    "MaximumVersion",
    "ModuleVersionGuid",
    "RequiredVersionGuid",
)

ON_RUNNER = (
    sys.platform == "win32"
    and os.environ.get("GITHUB_ACTIONS") == "true"
    and os.environ.get("RUNNER_ENVIRONMENT") == "github-hosted"
    and os.environ.get("REFUTE_JEA_INTEGRATION") == "1"
)


@pytest.fixture(scope="module")
def result() -> dict:
    # every test that needs the endpoint uses this fixture, so it is skipped with it; the
    # check of the entries below needs no endpoint and runs everywhere
    if not ON_RUNNER:
        pytest.skip("runs only on GitHub-hosted Windows runners (REFUTE_JEA_INTEGRATION=1)")
    exe = shutil.which("powershell.exe")
    assert exe, "Windows PowerShell 5.1 is part of Windows"
    out = subprocess.run(
        [exe, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", str(SCRIPT)],
        capture_output=True,
        text=True,
        timeout=900,
    )
    assert out.returncode == 0, out.stdout + out.stderr
    data = json.loads(out.stdout.strip().splitlines()[-1])
    assert data["Ran"], data["Reason"]
    print(json.dumps(data, indent=1))  # the evidence, in the CI log
    return data


@pytest.fixture(scope="module")
def sessions(result) -> dict:
    return result["Sessions"]


def _opened(s: dict) -> None:
    assert s["Opened"], s
    assert "Get-RefuteJeaProbe" in s["Commands"] and "Get-Command" in s["Commands"]
    assert "Get-Module" not in s["Commands"]
    assert s["Probe"] == "probe-ok"


def test_a_session_by_manifest_path_opens_with_network_access(sessions):
    """The fix of the role capability (import by the manifest path) and of
    Invoke-RefuteVm.ps1 (-EnableNetworkAccess, no -Credential): the session opens, shows
    the visible functions and the helper commands, and runs the function."""
    _opened(sessions["PathWithNetworkAccess"])


def test_a_session_by_name_opens_too(sessions):
    """The alternative the maintainer named: ModulesToImport by name only."""
    _opened(sessions["NameWithNetworkAccess"])


def test_without_network_access_a_local_endpoint_denies_access(sessions):
    """Cause 1: with AccessMode Local, localhost without -EnableNetworkAccess is a network
    logon, which the endpoint denies: an access-denied error, not any other failure."""
    s = sessions["PathWithoutNetworkAccess"]
    assert not s["Opened"]
    assert "AccessDenied" in s["ErrorId"] or "Access is denied" in s["Error"], s


@pytest.mark.parametrize("pin", PINS)
def test_each_version_pin_cannot_open_the_restricted_session(sessions, pin):
    """Cause 3: any of RequiredVersion, ModuleVersion, MaximumVersion (and GUID, which needs
    a version key) makes PowerShell call Get-Module in the restricted session."""
    s = sessions[f"Pin{pin}"]
    assert not s["Opened"] and "Get-Module" in s["Error"], s


def test_a_role_capability_in_a_version_subfolder_is_not_found(sessions):
    """Cause 2: the same role capability is found at the top of its module (the positive
    control) and not in a version subfolder, where the error names the role capability."""
    _opened(sessions["FlatTwinWithNetworkAccess"])
    s = sessions["SubfolderWithNetworkAccess"]
    assert not s["Opened"] and "ProbeVersioned" in s["Error"], s


def _session_roots(text: str) -> list[dict]:
    """The lines of Get-RefuteJeaModuleRoots (tests/vm/JeaProbe.psm1): state (present,
    absent or error), the entry as written, its normalised root, error, psrc files."""
    roots = []
    for line in text.split("\n"):
        state, entry, path, error, files = line.split("\t")
        assert state in ("present", "absent", "error"), line
        roots.append(
            {
                "Entry": entry,
                "Path": path,
                "State": state,
                "Error": error,
                "RoleCapabilities": [f for f in files.split("|") if f],
            }
        )
    return roots


def test_the_roots_the_session_searches_are_known_to_the_registration(result, sessions):
    """The module path seen inside a JEA session, read by its virtual account while the
    session is open. Every root is one the registration searches (the registration's own
    function, Get-RefuteRegistrationModuleRoots), or, root by root, is confirmed absent, or
    was read without error and holds no role capability at all in that session: JEA can
    select nothing there. A root that could not be read is never taken as absent (Codex
    review of #99). No folder is exempted by its name (Codex review of #99 and #102). This
    is evidence for the GitHub runner only."""
    known = {p.lower() for p in result["Roots"]["Registration"]}
    session = _session_roots(sessions["PathWithNetworkAccess"]["Roots"])
    assert session, "the session reported no module path"
    # every entry, as written and before any normalisation, is fully qualified (a drive and
    # '\', or UNC), as the registration requires: a relative entry ('C:', 'Modules') would
    # depend on the session's current folder (Codex review of #99, round 5)
    relative = [r["Entry"] for r in session if not FULLY_QUALIFIED.match(r["Entry"])]
    assert relative == [], relative
    unknown = [r for r in session if r["State"] != "absent" and r["Path"].lower() not in known]
    print("session roots outside the registration's set:", json.dumps(unknown, indent=1))
    selectable = [r for r in unknown if r["State"] == "error" or r["RoleCapabilities"]]
    assert selectable == [], (selectable, result["Roots"]["Registration"])
    # the probe's own role capabilities are seen from inside the session, so the listing works
    listed = [f for r in session for f in r["RoleCapabilities"]]
    assert any(
        f.lower().endswith("\\refutejeaprobe\\rolecapabilities\\probebypath.psrc") for f in listed
    )


@pytest.mark.parametrize(
    ("entry", "qualified"),
    [
        ("C:\\Program Files\\WindowsPowerShell\\Modules", True),
        ("C:\\", True),
        ("C:\\\\", True),
        ("\\\\srv\\share\\Modules", True),
        ("C:", False),
        ("C:Modules", False),
        ("Modules", False),
        (".\\Modules", False),
        ("\\Modules", False),
    ],
)
def test_the_entry_check_refuses_relative_entries(entry, qualified):
    """The check the roots test applies to each entry as written (it runs everywhere: it
    needs no endpoint)."""
    assert bool(FULLY_QUALIFIED.match(entry)) is qualified
