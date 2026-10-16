"""A real JEA endpoint on the Windows CI runner (tests/vm/jea_integration.ps1).

Runs only on GitHub Actions Windows jobs, where the CI sets REFUTE_JEA_INTEGRATION=1 and
the runner is an ephemeral machine with Administrator rights; it is skipped everywhere
else, and the PowerShell script refuses to run outside that environment too, because it
enables WinRM and registers session configurations. It checks, with disposable endpoints
shaped like RefuteVm (RestrictedRemoteServer, RunAsVirtualAccount, AccessMode Local), the
three causes the maintainer found when the RefuteVm session would not open (2026-10-16).
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tests" / "vm" / "jea_integration.ps1"

pytestmark = pytest.mark.skipif(
    not (
        sys.platform == "win32"
        and os.environ.get("GITHUB_ACTIONS") == "true"
        and os.environ.get("REFUTE_JEA_INTEGRATION") == "1"
    ),
    reason="runs only on the GitHub Actions Windows runners (REFUTE_JEA_INTEGRATION=1)",
)


@pytest.fixture(scope="module")
def sessions() -> dict:
    exe = shutil.which("powershell.exe")
    assert exe, "Windows PowerShell 5.1 is part of Windows"
    out = subprocess.run(
        [exe, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", str(SCRIPT)],
        capture_output=True,
        text=True,
        timeout=900,
    )
    assert out.returncode == 0, out.stdout + out.stderr
    result = json.loads(out.stdout.strip().splitlines()[-1])
    assert result["Ran"], result["Reason"]
    return result["Sessions"]


def test_a_session_by_manifest_path_opens_with_network_access(sessions):
    """The fix of the role capability (import by the manifest path) and of
    Invoke-RefuteVm.ps1 (-EnableNetworkAccess, no -Credential): the session opens, shows
    the visible function and the helper commands, and runs the function."""
    s = sessions["PathWithNetworkAccess"]
    assert s["Opened"], s["Error"]
    assert "Get-RefuteJeaProbe" in s["Commands"] and "Get-Command" in s["Commands"]
    assert "Get-Module" not in s["Commands"]
    assert s["Probe"] == "probe-ok"


def test_a_session_by_name_opens_too(sessions):
    """The alternative the maintainer named: ModulesToImport by name only."""
    s = sessions["NameWithNetworkAccess"]
    assert s["Opened"] and s["Probe"] == "probe-ok", s["Error"]


def test_without_network_access_a_local_endpoint_refuses(sessions):
    """Cause 1: with AccessMode Local, localhost without -EnableNetworkAccess is a network
    logon, which the endpoint denies."""
    s = sessions["PathWithoutNetworkAccess"]
    assert not s["Opened"] and s["Error"]


def test_a_version_pin_cannot_open_the_restricted_session(sessions):
    """Cause 3: RequiredVersion and GUID make PowerShell call Get-Module in the restricted
    session, which does not have it."""
    s = sessions["VersionWithNetworkAccess"]
    assert not s["Opened"] and "Get-Module" in s["Error"], s


def test_a_role_capability_in_a_version_subfolder_is_not_found(sessions):
    """Cause 2: JEA looks for <module path>\\<module>\\RoleCapabilities\\<name>.psrc only."""
    s = sessions["SubfolderWithNetworkAccess"]
    assert not s["Opened"] and s["Error"], s
