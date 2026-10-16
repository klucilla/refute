"""The VM scripts of WP6 phase 1 (scripts/vm), checked with no Hyper-V and no network.

tests/vm/vm_cases.ps1 parses every script, reads the data files, lists the commands
each script calls and runs the pure logic of RefuteVm.Core.ps1 on synthetic observed
states. The seed ISO is built and read back where Windows' IMAPI2FS is available.
Skipped when no PowerShell is installed.
"""

from __future__ import annotations

import base64
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
VM = ROOT / "scripts" / "vm"


def _powershell() -> str | None:
    if sys.platform == "win32":
        return shutil.which("powershell.exe") or shutil.which("pwsh")
    return shutil.which("pwsh")


POWERSHELL = _powershell()
pytestmark = pytest.mark.skipif(POWERSHELL is None, reason="PowerShell is not installed")


def _run(script: Path, *args: str) -> subprocess.CompletedProcess:
    cmd = [POWERSHELL, "-NoProfile", "-NonInteractive"]
    if sys.platform == "win32":
        cmd += ["-ExecutionPolicy", "Bypass"]
    return subprocess.run(
        [*cmd, "-File", str(script), *args], cwd=ROOT, capture_output=True, text=True, timeout=300
    )


@pytest.fixture(scope="module")
def cases(tmp_path_factory) -> dict:
    work = tmp_path_factory.mktemp("vm_cases")
    out = _run(ROOT / "tests" / "vm" / "vm_cases.ps1", "-Root", str(ROOT), "-WorkDir", str(work))
    assert out.returncode == 0, out.stderr
    return json.loads(out.stdout)


def test_every_script_parses(cases):
    assert cases["Parse"], "no script found"
    assert {name: errors for name, errors in cases["Parse"].items() if errors} == {}


def test_every_data_file_loads(cases):
    names = set(cases["Data"])
    assert {"RefuteVm/RefuteVm.Config.psd1", "RefuteVm/RefuteVm.psd1"} <= names
    assert "RefuteVm/RoleCapabilities/RefuteVmOperator.psrc" in names
    assert {name: r for name, r in cases["Data"].items() if r != "ok"} == {}


def test_synthetic_cases(cases):
    assert len(cases["Cases"]) >= 40
    failed = [f"{c['Name']}: {c['Detail']}" for c in cases["Cases"] if not c["Ok"]]
    assert failed == []


INSTALLED_MANIFEST = r"C:\Program Files\WindowsPowerShell\Modules\RefuteVm\RefuteVm.psd1"
UTILITY_MANIFEST = (
    r"C:\Windows\System32\WindowsPowerShell\v1.0\Modules"
    r"\Microsoft.PowerShell.Utility\Microsoft.PowerShell.Utility.psd1"
)
HYPERV_MANIFEST = r"C:\Windows\System32\WindowsPowerShell\v1.0\Modules\Hyper-V\2.0.0.0\Hyper-V.psd1"
VERSION_KEYS = {"requiredversion", "moduleversion", "maximumversion", "guid"}


def _version_keys(entries: list[dict]) -> list[str]:
    return sorted(
        key
        for entry in entries
        if entry["Kind"] == "table"
        for key in entry["Names"]
        if key.lower() in VERSION_KEYS
    )


def test_no_role_capability_imports_a_module_by_version(cases):
    """With RequiredVersion, ModuleVersion, MaximumVersion or GUID in ModulesToImport,
    PowerShell resolves the module by calling Get-Module inside the restricted session,
    which has no Get-Module: the session cannot open (the maintainer, 2026-10-16). Every
    .psrc of the repository imports by name or path only; the probe shows the detector
    sees every refused key."""
    imports = cases["RoleCapabilityImports"]
    assert "scripts/vm/RefuteVm/RoleCapabilities/RefuteVmOperator.psrc" in imports
    assert {name: _version_keys(e) for name, e in imports.items() if _version_keys(e)} == {}
    assert _version_keys(cases["RoleCapabilityProbe"]) == [
        "GUID",
        "MaximumVersion",
        "ModuleVersion",
        "RequiredVersion",
    ]


def test_the_role_capability_imports_the_installed_manifest_by_path(cases):
    """The module is pinned by the absolute path of its manifest in the folder the
    registration installs it to (no version subfolder), writable by administrators only.
    Before it, the two modules its functions need in a restricted session (the maintainer's
    H.5 of 2026-10-16), each by the absolute path of its manifest in System32, so that no
    name is resolved through the module path (Codex review of #118):
    Microsoft.PowerShell.Utility in $PSHOME (by name its functions do not come) and
    Hyper-V in its version subfolder."""
    entries = cases["RoleCapabilityImports"][
        "scripts/vm/RefuteVm/RoleCapabilities/RefuteVmOperator.psrc"
    ]
    assert entries == [
        {"Kind": "string", "Value": UTILITY_MANIFEST},
        {"Kind": "string", "Value": HYPERV_MANIFEST},
        {"Kind": "string", "Value": INSTALLED_MANIFEST},
    ]


@pytest.mark.skipif(sys.platform != "win32", reason="Windows PowerShell 5.1 and Hyper-V module")
def test_every_command_the_module_calls_exists_in_the_restricted_session():
    """The maintainer's H.5 of 2026-10-16: in the real session 'Import-PowerShellDataFile'
    was not recognized, a fourth layer found on the machine. A RestrictedRemoteServer state
    plus the role capability's ModulesToImport (with the repository's copy of RefuteVm)
    must hold every command the module's three files call, also on paths a host without
    Hyper-V never runs (tests/vm/jea_commands.ps1; no administrator rights needed). It
    shows that the commands exist in that state; what the connecting account sees is
    checked on the real endpoint (tests/test_vm_jea_integration.py)."""
    data = _windows_powershell_json("jea_commands.ps1")
    if not data["Ran"]:
        pytest.skip(data["Reason"])
    print(json.dumps(data, indent=1))
    assert data["Imports"][:2] == [UTILITY_MANIFEST, HYPERV_MANIFEST]
    assert data["Checked"] >= 40 and data["Defined"] >= 20  # 44 and 27 on 2026-10-16
    assert data["Missing"] == []
    # every call without a command name, by its form (Codex review of #118): the local
    # refusal script block, and the dot-sourcing of the module's two files. A new dynamic
    # call fails here until it is reviewed.
    assert data["Dynamic"] == {
        "Ampersand $refuse": 28,
        "Dot (Join-Path $PSScriptRoot 'RefuteVm.Core.ps1')": 1,
        "Dot (Join-Path $PSScriptRoot 'RefuteVm.HyperV.ps1')": 1,
    }
    # the Hyper-V cmdlets come from the manifest the role capability names, and their
    # assembly from the global assembly cache, not from a folder of the module path
    hyperv = data["HyperV"]
    assert hyperv["ModulePath"].lower() == HYPERV_MANIFEST.lower(), hyperv
    assert hyperv["GlobalAssemblyCache"] is True, hyperv
    assert (
        hyperv["AssemblyLocation"]
        .lower()
        .startswith(
            "c:\\windows\\microsoft.net\\assembly\\gac_msil\\microsoft.hyperv.powershell.cmdlets\\"
        )
    ), hyperv


def _windows_powershell_json(script: str) -> dict:
    exe = shutil.which("powershell.exe")
    assert exe, "Windows PowerShell 5.1 is part of Windows"
    out = subprocess.run(
        [
            exe,
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(ROOT / "tests" / "vm" / script),
            "-Root",
            str(ROOT),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert out.returncode == 0, out.stdout + out.stderr
    return json.loads(out.stdout.strip().splitlines()[-1])


@pytest.mark.skipif(sys.platform != "win32", reason="Windows PowerShell 5.1")
def test_the_status_and_the_simulation_record_the_caller_and_the_module():
    """Codex review of #118: the caller and the module hashes are computed before the
    Hyper-V step; this checks the records on any Windows machine, with or without Hyper-V
    (the real endpoint test reads the record on the runner). With the
    observation and the log writer replaced inside the module (tests/vm/module_records.ps1),
    the status output and the simulated record hold the caller, the module hashes and the
    configuration hash the module's own functions give."""
    data = _windows_powershell_json("module_records.ps1")
    if not data["Ran"]:
        pytest.skip(data["Reason"])
    expected = data["Expected"]
    caller = json.loads(expected["Caller"])
    module = json.loads(expected["Module"])
    assert module and caller
    status = json.loads(data["Status"])
    assert status["Caller"] == caller and status["Module"] == module
    assert status["ConfigSha256"] == expected["ConfigSha256"]
    assert status["Observed"]["Vms"] == []
    simulate = json.loads(data["Simulate"])
    assert simulate["Mode"] == "simulated" and len(data["Records"]) == 1
    record = json.loads(data["Records"][0])
    assert record["Mode"] == "simulated" and record["Operation"] == "SetHostPaths"
    assert record["Caller"] == caller and record["Module"] == module
    assert record["PlanSha256"] == simulate["PlanSha256"]


def test_the_registration_installs_without_a_version_subfolder():
    """JEA finds <module path>\\<module>\\RoleCapabilities\\<name>.psrc only (the maintainer's
    diagnosis of 2026-10-16): the module goes to RefuteVm itself, the apply checks the JEA
    search and refuses a copy in a version subfolder, and the preview checks that the role
    capability imports the installed manifest."""
    text = (VM / "Register-RefuteVmEndpoint.ps1").read_text(encoding="utf-8")
    assert "$ModuleDestination = $ModuleBase\n" in text.replace("\r\n", "\n")
    assert "ModuleManifest.ModuleVersion" not in text
    apply = text[text.index("# ---- apply") :]
    assert "Find-RefuteJeaRoleCapability -ModuleRoots $moduleRoots -RoleName $RoleName" in apply
    assert (
        "Find-RefuteVersionedRoleCapability -ModuleRoots $moduleRoots -RoleName $RoleName" in apply
    )
    preview = text[: text.index("# ---- apply")]
    assert (
        "$ExpectedImports = @($UtilityManifest, $HyperVManifestPath, $InstalledManifest)" in preview
    )
    assert f"$HyperVManifestPath = '{HYPERV_MANIFEST}'" in preview
    assert "$hyperVManifest -ne $HyperVManifestPath" in preview
    assert "@(Get-RefuteTreeProblems -Roots $ImportTrees)" in preview
    assert "the role capability must import exactly $($ExpectedImports -join ', ')" in preview
    assert "the role capability must make visible exactly Get-RefuteVmStatus" in preview
    assert "$InstalledManifest = Join-Path $ModuleBase 'RefuteVm.psd1'" in text


def test_the_endpoint_is_called_as_a_loopback_session(cases):
    """The endpoint is registered with AccessMode Local: a session to localhost is a
    loopback session only with implicit credentials and -EnableNetworkAccess
    (https://learn.microsoft.com/powershell/module/microsoft.powershell.core/disable-psremoting,
    accessed 2026-10-16); without it the maintainer's session was refused (2026-10-16).
    From the AST of Invoke-RefuteVm.ps1, read by Windows PowerShell 5.1 on Windows."""
    calls = cases["InvokeRemoting"]
    sessions = [c for c in calls if c["Command"] == "New-PSSession"]
    assert len(sessions) == 1, calls
    params = {p.lower() for p in sessions[0]["Parameters"]}
    assert {"computername", "configurationname", "enablenetworkaccess"} <= params
    assert "credential" not in params
    values = {k.lower(): v for k, v in sessions[0]["Values"].items()}
    assert values["computername"] == "localhost" and values["configurationname"] == "RefuteVm"
    others = [c for c in calls if c["Command"] != "New-PSSession"]
    assert {c["Command"] for c in others} <= {"Invoke-Command"}
    assert all({p.lower() for p in c["Parameters"]} == {"scriptblock", "session"} for c in others)


def test_operation_lists_agree(cases):
    table = cases["OperationTable"]
    assert cases["ValidateSets"]["RefuteVm/RefuteVm.psm1"] == table
    assert cases["ValidateSets"]["Invoke-RefuteVm.ps1"] == table


FORBIDDEN = {
    "Remove-Item",
    "Remove-VM",
    "Remove-VHD",
    "Remove-VMHardDiskDrive",
    "Remove-VMNetworkAdapter",
    "Connect-VMNetworkAdapter",
    "Enable-VMIntegrationService",
    "Invoke-Expression",
    "iex",
    "Unregister-PSSessionConfiguration",
    "Set-ExecutionPolicy",
    "Enable-PSRemoting",
    "Set-WSManQuickConfig",
    "Disable-NetFirewallRule",
    "Remove-NetFirewallRule",
    "Start-Process",
    "Set-VMNetworkAdapter",
    "Add-VMNetworkAdapter",
    "New-VMSwitch",
    "Mount-VHD",
}

HYPERV_ALLOWED = {
    "Get-VMHost",
    "Get-VM",
    "Get-VMMemory",
    "Get-VMProcessor",
    "Get-VMFirmware",
    "Get-VMIntegrationService",
    "Get-VMNetworkAdapter",
    "Get-VMHardDiskDrive",
    "Get-VMDvdDrive",
    "Get-VHD",
    "Set-VMHost",
    "New-VHD",
    "New-VM",
    "Set-VMMemory",
    "Set-VMProcessor",
    "Set-VMFirmware",
    "Set-VM",
    "Disable-VMIntegrationService",
    "Disconnect-VMNetworkAdapter",
    "Add-VMHardDiskDrive",
    "Add-VMDvdDrive",
    "Remove-VMDvdDrive",
    "Start-VM",
    "Stop-VM",
    "Suspend-VM",
    "Resume-VM",
    "Save-VM",
}


def test_no_script_calls_a_forbidden_command(cases):
    used = {name: sorted(set(cmds) & FORBIDDEN) for name, cmds in cases["Commands"].items()}
    assert {name: cmds for name, cmds in used.items() if cmds} == {}


def test_the_module_calls_only_the_listed_hyperv_cmdlets(cases):
    module = set()
    for name, cmds in cases["Commands"].items():
        if name.startswith("RefuteVm/"):
            module |= {c for c in cmds if "-VM" in c or c.endswith("-VHD")}
    assert module <= HYPERV_ALLOWED, sorted(module - HYPERV_ALLOWED)


def test_scripts_are_ascii():
    # Windows PowerShell 5.1 reads a file without BOM in the ANSI code page.
    for path in [*VM.rglob("*"), ROOT / "tests" / "vm" / "vm_cases.ps1"]:
        if path.is_file():
            assert path.read_bytes().isascii(), path


def test_no_turn_off_and_no_secure_boot_off():
    for path in VM.rglob("*.ps*1"):
        text = path.read_text(encoding="utf-8")
        assert "-TurnOff" not in text, path
        assert "EnableSecureBoot Off" not in text, path
        for line in text.splitlines():
            if "Stop-VM" in line:
                assert "-Force" not in line, (path, line)


def test_registration_blocks_winrm_before_starting_it():
    text = (VM / "Register-RefuteVmEndpoint.ps1").read_text(encoding="utf-8")
    apply = text[text.index("# ---- apply") :]
    rule = apply.index("New-NetFirewallRule")
    active = apply.index("Get-NetFirewallRule -PolicyStore ActiveStore -Name")
    registry = apply.index("Test-ListenersLoopbackOnly @(Get-RegistryListeners)")
    start = apply.index("Start-Service -Name WinRM")
    register = apply.index("Register-PSSessionConfiguration")
    assert rule < active < registry < start < register
    assert "-AccessMode Local" in apply
    # the bypass check reads each rule's security filter (Codex review round 2)
    assert "Get-NetFirewallSecurityFilter -AssociatedNetFirewallRule" in apply
    assert apply.index("Get-NetFirewallSecurityFilter") < start
    assert "Test-RefuteRightsWrite" in text
    assert "-PreviewSha256" in text and "the change list differs from the previewed one" in text


# Commands that change the machine, or may (the WSMan provider can offer to start WinRM;
# module discovery can write the module analysis cache). None may run in the preview.
PREVIEW_FORBIDDEN = (
    "Get-PSSessionConfiguration",
    "Get-Module",
    "Import-Module",
    "WSMan:",
    "Get-WSManInstance",
    "Set-Service",
    "Start-Service",
    "Set-Acl",
    "Copy-Item",
    "New-Item",
    "New-NetFirewallRule",
    "Set-NetFirewall",
    "New-PSSessionConfigurationFile",
    "Register-PSSessionConfiguration",
    "CreateDirectory",
    "WriteAllText",
    "Out-File",
    "Set-Content",
    "Add-Content",
    "Set-ItemProperty",
    "New-ItemProperty",
    "Add-LocalGroupMember",
)


# Every command and .NET method the preview may call (before the apply section of
# Register-RefuteVmEndpoint.ps1, and in the core it dot-sources), from the PowerShell
# AST: reads, in-memory work and output only. A new command fails this test until it is
# reviewed. The ACL methods (SetOwner, SetAccessRuleProtection, AddAccessRule) act on an
# in-memory DirectorySecurity that only Set-Acl, in the apply section, writes.
PREVIEW_COMMANDS = {
    "find-refutehypervmanifest",
    "find-rolecapabilitycopies",
    "convertto-refutemoduleroot",
    "convertto-refuteaclentries",
    # the ACL of the VM tree, built in memory (version 2, after the failure of SetHostPaths),
    # and the effect of ACL rules, computed in memory
    "convertto-refuteaclrules",
    "convertto-refuteacleffect",
    "get-refutechildrules",
    "get-refutevmtreeaclspec",
    "new-refutefolderacl",
    "convertto-refutespecificrights",
    "convertto-refutewindowsfullpath",
    "foreach-object",
    "get-acl",
    "get-childitem",
    "get-filehash",
    "get-itemproperty",
    "get-localgroupmember",
    "get-modulepathroots",
    "get-netfirewallrule",
    "get-item",
    "get-refuteacewriters",
    "get-refuteancestorwriters",
    "get-refutediscoveryproblems",
    "get-refuteitemproblems",
    "get-refutejeadiscoveryroots",
    "get-refuteregistrationmoduleroots",
    "get-refutetreeproblems",
    "get-refutewriterightsmask",
    "get-registrylisteners",
    "get-service",
    "get-sidaccount",
    "get-treehashes",
    "import-powershelldatafile",
    "join-path",
    "join-refutediscoveryroots",
    "join-refutemoduleroots",
    "new-object",
    "resolve-path",
    "resolve-refutesessionentry",
    "set-strictmode",
    "sort-object",
    "split-path",
    "test-listenersloopbackonly",
    "test-path",
    "test-refuteallowedowner",
    "test-refuteallowedwriter",
    "test-refuterightswrite",
    "test-targetexists",
    "where-object",
    "write-output",
}
PREVIEW_METHODS = {
    "add",
    "addaccessrule",
    "close",
    "computehash",
    "containskey",
    "create",
    "dispose",
    "endswith",
    "expandenvironmentvariables",
    "getbytes",
    "getaccessrules",
    "getcurrent",
    "getenvironmentvariable",
    "getowner",
    "isinrole",
    "lastindexof",
    "max",
    "opensubkey",
    "replace",
    "setaccessruleprotection",
    "setowner",
    "split",
    "startswith",
    "substring",
    "tolowerinvariant",
    "tostring",
    "translate",
    "trimend",
    "tryparse",
}

# The preview of Remove-RefuteWinRmListener.ps1 (and the core): reads of the registry,
# the service state and the backup folder ACL, in-memory work and output.
LISTENER_PREVIEW_COMMANDS = {
    "convertto-refutemoduleroot",
    "convertto-refuteaclentries",
    # in the core it dot-sources: the ACL of the VM tree, built in memory only, and the
    # effect of ACL rules, computed in memory
    "convertto-refuteaclrules",
    "convertto-refuteacleffect",
    "get-refutechildrules",
    "new-refutefolderacl",
    "convertto-refutespecificrights",
    "convertto-refutewindowsfullpath",
    "foreach-object",
    "get-acl",
    "get-childitem",
    "get-item",
    "get-itemproperty",
    "get-refuteacewriters",
    "get-refuteancestorwriters",
    "get-refutebackupproblems",
    "get-refutediscoveryproblems",
    "get-refuteitemproblems",
    "get-refutejeadiscoveryroots",
    "get-refutelistenerremoval",
    "get-refutetreeproblems",
    "get-refutewriterightsmask",
    "get-service",
    "join-path",
    "join-refutediscoveryroots",
    "join-refutemoduleroots",
    "new-object",
    "read-refutelisteners",
    "resolve-refutesessionentry",
    "set-strictmode",
    "sort-object",
    "split-path",
    "test-path",
    "test-refuteallowedowner",
    "test-refuteallowedwriter",
    "test-refuterightswrite",
    "where-object",
    "write-output",
}
LISTENER_PREVIEW_METHODS = {
    "add",
    # the core's New-RefuteFolderAcl acts on an in-memory DirectorySecurity; this script
    # never calls it, and never calls Set-Acl
    "addaccessrule",
    "setaccessruleprotection",
    "setowner",
    "close",
    "computehash",
    "containskey",
    "create",
    "dispose",
    "endswith",
    "expandenvironmentvariables",
    "getbytes",
    "getaccessrules",
    "getcurrent",
    "getenvironmentvariable",
    "getowner",
    "getsubkeynames",
    "getvalue",
    "getvaluenames",
    "isinrole",
    "lastindexof",
    "max",
    "opensubkey",
    "replace",
    "split",
    "startswith",
    "substring",
    "tolowerinvariant",
    "tostring",
    "translate",
    "trimend",
    "tryparse",
}


def test_the_listener_removal_preview_only_reads(cases):
    """The preview of the listener removal: allowlisted commands and methods only, no
    dynamic command, no redirection; the registry keys are opened read-only; the WinRM
    service is never started, stopped or set anywhere in the script."""
    preview = cases["PreviewListener"]
    assert preview["ApplyMarkerFound"]
    assert {c.lower() for c in preview["Commands"]} - LISTENER_PREVIEW_COMMANDS == set()
    assert {m.lower() for m in preview["Methods"]} - LISTENER_PREVIEW_METHODS == set()
    assert preview["Unnamed"] == [] and preview["Redirections"] == []
    text = (VM / "Remove-RefuteWinRmListener.ps1").read_text(encoding="utf-8")
    before = text[: text.index("# ---- apply")]
    assert (
        ".OpenSubKey($ListenerRoot)" in before and ".OpenSubKey($ListenerRoot, $true)" not in before
    )
    for command in ("Start-Service", "Stop-Service", "Restart-Service", "Set-Service", "WSMan:"):
        assert command.lower() not in text.lower(), command
    # the apply opens the listener root writable once, to delete exactly the target key
    apply = text[text.index("# ---- apply") :]
    assert apply.count(".OpenSubKey($ListenerRoot, $true)") == 1
    assert "DeleteSubKeyTree($Target)" in apply


# The preview of Set-RefuteVmTreeAcl.ps1 (and the core): reads of the VM tree's folders and
# ACLs, in-memory ACL objects, and output. Set-Acl appears only after its apply marker.
VMTREE_PREVIEW_COMMANDS = (
    LISTENER_PREVIEW_COMMANDS
    - {
        "get-refutebackupproblems",
        "get-refutelistenerremoval",
        "read-refutelisteners",
        "get-service",
    }
) | {
    "compare-refutevmtreeacl",
    "compare-refutevmtreebelow",
    "get-refutevmtreeaclspec",
    "get-sidname",
    "get-statehash",
    "get-treestate",
}
VMTREE_PREVIEW_METHODS = (
    LISTENER_PREVIEW_METHODS
    - {
        "getsubkeynames",
        "getvalue",
        "getvaluenames",
        "opensubkey",
    }
) | {"getowner"}


def test_the_vm_tree_acl_preview_only_reads(cases):
    """The preview of Set-RefuteVmTreeAcl.ps1: allowlisted commands and methods only, no
    dynamic command, no redirection; Set-Acl and the evidence file only after the apply
    marker. In the apply (Codex review of #126): the evidence file is created first, as a
    new file with its ACL set at creation, and the state is read and compared with the
    preview again, both before the one Set-Acl; the evidence is written in a finally block,
    so also when a step stops."""
    preview = cases["PreviewVmTree"]
    assert preview["ApplyMarkerFound"]
    assert {c.lower() for c in preview["Commands"]} - VMTREE_PREVIEW_COMMANDS == set()
    assert {m.lower() for m in preview["Methods"]} - VMTREE_PREVIEW_METHODS == set()
    assert preview["Unnamed"] == [] and preview["Redirections"] == []
    text = (VM / "Set-RefuteVmTreeAcl.ps1").read_text(encoding="utf-8")
    before = text[: text.index("# ---- apply")]
    for writer in ("Set-Acl", "WriteAllText", "FileStream", "CreateNew"):
        assert writer not in before, writer
    apply = text[text.index("# ---- apply") :]
    assert apply.count("Set-Acl -LiteralPath $TreeRoot") == 1
    set_acl = apply.index("Set-Acl -LiteralPath $TreeRoot")
    create = apply.index("[System.IO.FileMode]::CreateNew")
    assert create < set_acl
    assert "[System.IO.FileShare]::Read, 4096, [System.IO.FileOptions]::None, $fileAcl)" in apply
    assert apply.index("(Get-StateHash $again) -cne $previewHash") < set_acl
    assert "WriteAllText" not in apply and "FileMode]::Create," not in apply
    assert apply.index("} finally {") > set_acl and "$stream.Write(" in apply


@pytest.mark.skipif(sys.platform != "win32", reason="the script runs in Windows PowerShell 5.1")
def test_the_vm_tree_acl_preview_runs_and_never_applies_without_its_hash(tmp_path):
    """The preview of Set-RefuteVmTreeAcl.ps1 in powershell.exe: it refuses without
    PSModuleAnalysisCachePath=nul, otherwise lists the ACL it would set (with the
    ChangePermissions of Hyper-V Administrators) and a PreviewSha256 and changes nothing;
    -Apply without -PreviewSha256 is refused before the apply section."""
    import os

    exe = shutil.which("powershell.exe")
    assert exe
    argv = [
        exe,
        "-NoProfile",
        "-NonInteractive",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(VM / "Set-RefuteVmTreeAcl.ps1"),
    ]
    plain = {k: v for k, v in os.environ.items() if k.upper() != "PSMODULEANALYSISCACHEPATH"}
    env = {**plain, "PSModuleAnalysisCachePath": "nul"}

    def run(*extra, environment=env):
        return subprocess.run(
            [*argv, *extra],
            cwd=tmp_path,
            env=environment,
            capture_output=True,
            text=True,
            timeout=300,
        )

    refused = run(environment=plain)
    assert refused.returncode == 1 and "PSModuleAnalysisCachePath=nul" in refused.stdout
    out = run()
    text = out.stdout + out.stderr
    assert "PropertyNotFoundStrict" not in text, text
    assert "Mode: preview (no change)" in out.stdout and "PreviewSha256: " in out.stdout, text
    assert "Modify, ChangePermissions" in out.stdout, text
    assert out.returncode in (0, 1), text
    if out.returncode == 1:
        assert "Problems (nothing was changed):" in out.stdout, text
    no_hash = run("-Apply")
    assert no_hash.returncode in (0, 1), no_hash.stdout + no_hash.stderr
    assert "Done:" not in no_hash.stdout
    if no_hash.returncode == 1:
        assert "-Apply needs -PreviewSha256 from a preview run" in no_hash.stdout or (
            "Problems (nothing was changed):" in no_hash.stdout
        )


def test_the_registration_preview_only_reads(cases):
    """Codex review of the preview: everything the preview can run is on the allowlist
    (case-insensitive, from the AST, comments excluded, core included); no command that
    changes the machine, or may, appears in it."""
    preview = cases["Preview"]
    assert preview["ApplyMarkerFound"]
    commands = {c.lower() for c in preview["Commands"]}
    methods = {m.lower() for m in preview["Methods"]}
    assert commands - PREVIEW_COMMANDS == set()
    assert methods - PREVIEW_METHODS == set()
    # nothing a name list cannot see: no dynamic command (the dot-source of the reviewed
    # core is the only exception) and no redirection to a file
    assert preview["Unnamed"] == [] and preview["Redirections"] == []
    # the collector does see both forms (synthetic probe)
    assert cases["PreviewProbe"] == {"Unnamed": 1, "Redirections": 1}
    assert not {c.lower() for c in PREVIEW_FORBIDDEN} & commands
    text = (VM / "Register-RefuteVmEndpoint.ps1").read_text(encoding="utf-8")
    before = text[: text.index("# ---- apply")]
    # the registry key is opened read-only (one argument), and every path without -Apply
    # ends before the apply section: problems exit 1, a clean preview exits 0
    assert (
        '.OpenSubKey("SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\WSMAN\\Plugin\\$EndpointName")'
        in before
    )
    tail = [line.strip() for line in before.strip().splitlines()[-8:]]
    assert any(line.startswith("if ($problems.Count)") for line in tail)
    assert "exit 1" in "\n".join(tail)
    assert tail[-1].startswith("if (-not $Apply)") and tail[-1].endswith("exit 0 }")


def test_no_command_output_is_counted_or_indexed_without_an_array(cases):
    """Windows PowerShell 5.1 under StrictMode: `$x = f` with an empty output leaves $null,
    so `$x.Count` or `$x[0]` fails (the maintainer's first preview run). Every script must
    wrap such output in @(...); the detector is checked on a synthetic snippet."""
    found = {
        (name, use)
        for name, uses in cases["UnsafeListUse"].items()
        for use in uses
        if (name, use) not in REVIEWED_SINGLE_OBJECTS
    }
    assert found == set()
    assert sorted(cases["UnsafeListProbe"]) == ["$x.Count", "$x[0]"]


# Uses the detector lists that are not lists at all, reviewed one by one: the command
# always returns exactly one object, and .Count or [k] is that object's own member.
REVIEWED_SINGLE_OBJECTS = {
    # Get-VMProcessor returns one VMProcessor; Count is its number of virtual processors
    ("RefuteVm/RefuteVm.HyperV.ps1", "$processor.Count"),
    # Get-TreeHashes returns one ordered dictionary; [$k] reads a key
    ("Register-RefuteVmEndpoint.ps1", "$sourceHashes[$k]"),
    # Test-RefuteVmConfig returns its array with the comma operator (", $x.ToArray()"),
    # so an empty list arrives as one empty array, never $null; @(...) around it would
    # instead give an array holding that empty array (Count 1)
    ("RefuteVm/RefuteVm.Core.ps1", "$problems.Count"),
    ("RefuteVm/RefuteVm.psm1", "$problems.Count"),
    # Read-RefuteListeners returns one ordered dictionary (empty or not); a dictionary is
    # never unrolled by the pipeline, so .Count and [$name] are its own members
    ("Remove-RefuteWinRmListener.ps1", "$listeners.Count"),
    ("Remove-RefuteWinRmListener.ps1", "$listeners[$name]"),
}


def test_the_config_check_returns_an_array_even_when_empty(cases):
    """The reviewed exception above, checked: a valid configuration gives an empty array
    (the first synthetic case), not $null."""
    first = cases["Cases"][0]
    assert first["Name"] == "config of the repository is valid" and first["Ok"], first


@pytest.mark.skipif(
    sys.platform != "win32", reason="the registration runs in Windows PowerShell 5.1"
)
def test_the_registration_preview_runs_to_its_end_in_windows_powershell(tmp_path):
    """The preview itself, in powershell.exe (Windows PowerShell 5.1, StrictMode 2.0), on
    a machine with no RefuteVmOperator role capability anywhere (the maintainer's first
    run stopped there: a function returning an empty list gives $null, and .Count on
    $null is an error under StrictMode). Without -Apply nothing changes; as a normal
    user, or on a host without Hyper-V, the preview lists its problems and exits 1."""
    import os

    exe = shutil.which("powershell.exe")
    assert exe, "Windows PowerShell 5.1 is part of Windows"
    account = f"{os.environ['COMPUTERNAME']}\\{os.environ['USERNAME']}"
    argv = [
        exe,
        "-NoProfile",
        "-NonInteractive",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(VM / "Register-RefuteVmEndpoint.ps1"),
        "-OperatorAccount",
        account,
    ]
    # the module analysis cache is disabled only by the environment the process starts
    # with (Codex review); without it the script refuses before reading anything
    plain = {k: v for k, v in os.environ.items() if k.upper() != "PSMODULEANALYSISCACHEPATH"}
    refused = subprocess.run(
        argv, cwd=tmp_path, env=plain, capture_output=True, text=True, timeout=600
    )
    assert refused.returncode == 1 and "PSModuleAnalysisCachePath=nul" in refused.stdout
    assert "Mode:" not in refused.stdout
    out = subprocess.run(
        argv,
        cwd=tmp_path,
        env={**plain, "PSModuleAnalysisCachePath": "nul"},
        capture_output=True,
        text=True,
        timeout=600,
    )
    text = out.stdout + out.stderr
    assert "PropertyNotFoundStrict" not in text and "Count" not in out.stderr, text
    assert "Mode: preview (no change)" in out.stdout, text
    assert "PreviewSha256: " in out.stdout, text
    # on a CI runner no role capability exists, so none is reported (a host where the
    # endpoint is registered reports its copy, which is correct there)
    if os.environ.get("CI"):
        assert "a role capability named RefuteVmOperator already exists" not in out.stdout
    # exit 0 only on a ready host as Administrator; otherwise 1 with the problems listed
    assert out.returncode in (0, 1), text
    if out.returncode == 1:
        assert "Problems (nothing was changed):" in out.stdout, text


@pytest.mark.skipif(
    sys.platform != "win32", reason="the listener removal runs in Windows PowerShell 5.1"
)
def test_the_listener_removal_preview_runs_and_never_applies_without_its_hash(tmp_path):
    """The preview of Remove-RefuteWinRmListener.ps1 in powershell.exe: it refuses without
    PSModuleAnalysisCachePath=nul in its launch environment, otherwise prints the listener
    keys and a PreviewSha256 and changes nothing; -Apply without -PreviewSha256 is refused
    before the apply section."""
    import os

    exe = shutil.which("powershell.exe")
    assert exe
    argv = [
        exe,
        "-NoProfile",
        "-NonInteractive",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(VM / "Remove-RefuteWinRmListener.ps1"),
    ]
    plain = {k: v for k, v in os.environ.items() if k.upper() != "PSMODULEANALYSISCACHEPATH"}
    env = {**plain, "PSModuleAnalysisCachePath": "nul"}

    def run(*extra, environment=env):
        return subprocess.run(
            [*argv, *extra],
            cwd=tmp_path,
            env=environment,
            capture_output=True,
            text=True,
            timeout=300,
        )

    refused = run(environment=plain)
    assert refused.returncode == 1 and "PSModuleAnalysisCachePath=nul" in refused.stdout
    assert "Mode:" not in refused.stdout
    out = run()
    text = out.stdout + out.stderr
    assert "PropertyNotFoundStrict" not in text, text
    assert "Mode: preview (no change)" in out.stdout and "PreviewSha256: " in out.stdout, text
    assert "Listener keys under HKLM" in out.stdout, text
    assert out.returncode in (0, 1), text
    if out.returncode == 1:
        assert "Problems (nothing was changed):" in out.stdout, text
    no_hash = run("-Apply")
    assert no_hash.returncode == 1, no_hash.stdout + no_hash.stderr
    assert "-Apply needs -PreviewSha256 from a preview run" in no_hash.stdout
    assert "Already done" not in no_hash.stdout and "Done:" not in no_hash.stdout


def _iso_files(data: bytes) -> tuple[str, str, dict[str, bytes]]:
    """Volume labels (ISO 9660 and Joliet) and the files of the Joliet root."""
    sec = 2048
    pvd = data[16 * sec : 17 * sec]
    assert pvd[0] == 1 and pvd[1:6] == b"CD001"
    label = pvd[40:72].decode("ascii").strip()
    index = 17
    while True:
        desc = data[index * sec : (index + 1) * sec]
        assert desc[1:6] == b"CD001" and desc[0] != 255, "no Joliet descriptor"
        if desc[0] == 2 and desc[88:91] in (b"%/@", b"%/C", b"%/E"):
            break
        index += 1
    joliet_label = desc[40:72].decode("utf-16-be").strip()
    root = desc[156 : 156 + 34]
    lba, size = int.from_bytes(root[2:6], "little"), int.from_bytes(root[10:14], "little")
    table = data[lba * sec : lba * sec + size]
    files, pos = {}, 0
    while pos < len(table):
        length = table[pos]
        if length == 0:
            pos = (pos // sec + 1) * sec
            continue
        rec = table[pos : pos + length]
        name = rec[33 : 33 + rec[32]]
        if name not in (b"\x00", b"\x01"):
            start, n = int.from_bytes(rec[2:6], "little"), int.from_bytes(rec[10:14], "little")
            files[name.decode("utf-16-be").split(";")[0]] = data[start * sec : start * sec + n]
        pos += length
    return label, joliet_label, files


@pytest.mark.skipif(sys.platform != "win32", reason="IMAPI2FS is a Windows component")
def test_seed_iso_is_a_cidata_volume_with_the_rendered_files(tmp_path):
    key = tmp_path / "vm.pub"
    # RFC 8709 wire format: string "ssh-ed25519", then a 32-byte key (synthetic bytes)
    raw = b"\x00\x00\x00\x0bssh-ed25519" + b"\x00\x00\x00\x20" + bytes(range(32))
    blob = base64.b64encode(raw).decode("ascii")
    key.write_text(f"ssh-ed25519 {blob} somebody@somehost\n", encoding="ascii")
    iso = tmp_path / "seed.iso"
    out = _run(VM / "New-RefuteSeedIso.ps1", "-PublicKeyPath", str(key), "-OutputPath", str(iso))
    if out.returncode != 0 and "IMAPI2FS" in out.stderr:
        pytest.skip("IMAPI2FS is not registered on this machine")
    assert out.returncode == 0, out.stderr
    label, joliet_label, files = _iso_files(iso.read_bytes())
    assert label == "CIDATA" and joliet_label == "CIDATA"
    assert set(files) == {"user-data", "meta-data"}
    user_data = files["user-data"].decode("utf-8")
    assert user_data.startswith("#cloud-config\n")
    assert f"ssh-ed25519 {blob} refute-vm" in user_data
    assert "somebody" not in user_data and "{{" not in user_data and "\r" not in user_data
    assert (
        files["meta-data"].decode("utf-8")
        == "instance-id: refute-vm-1\nlocal-hostname: refute-vm\n"
    )
    # nothing is overwritten
    again = _run(VM / "New-RefuteSeedIso.ps1", "-PublicKeyPath", str(key), "-OutputPath", str(iso))
    assert again.returncode != 0 and "already exists" in again.stderr


def test_seed_iso_refuses_a_key_that_is_not_ed25519(tmp_path):
    if sys.platform != "win32":
        pytest.skip("the seed script runs on the Windows host")
    key = tmp_path / "vm.pub"
    key.write_text("ssh-rsa AAAAB3NzaC1yc2E user@host\n", encoding="ascii")
    out = _run(
        VM / "New-RefuteSeedIso.ps1",
        "-PublicKeyPath",
        str(key),
        "-OutputPath",
        str(tmp_path / "s.iso"),
    )
    assert out.returncode != 0 and "ssh-ed25519" in out.stderr
