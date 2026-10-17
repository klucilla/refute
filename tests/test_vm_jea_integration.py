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


def _session_roots(text: str) -> tuple[str, list[dict]]:
    """The lines of Get-RefuteJeaModuleRoots (tests/vm/JeaProbe.psm1): first the session's
    current folder, then per entry its state (present, absent or error), the entry as
    written, its normalised root, the full path the session resolves it to (the folder
    inspected), error, psrc files."""
    lines = text.split("\n")
    head, cwd = lines[0].split("\t")
    assert head == "cwd", lines[0]
    roots = []
    for line in lines[1:]:
        state, entry, path, full, error, files = line.split("\t")
        assert state in ("present", "absent", "error"), line
        roots.append(
            {
                "Entry": entry,
                "Path": path,
                "Full": full,
                "State": state,
                "Error": error,
                "RoleCapabilities": [f for f in files.split("|") if f],
            }
        )
    return cwd, roots


def test_the_roots_the_session_searches_are_known_to_the_registration(result, sessions):
    """The module path seen inside a JEA session, read by its virtual account while the
    session is open, each entry inspected at the full path the session resolves it to. Every
    folder is one the registration searches (the registration's own function,
    Get-RefuteRegistrationModuleRoots), or, folder by folder, is confirmed absent, or was
    read without error and holds no role capability at all in that session: JEA can select
    nothing there. A folder that could not be read is never taken as absent, and no folder
    is exempted by its name (Codex review of #99 and #102). This is evidence for the GitHub
    runner only.

    A relative entry (on the runner, the virtual account's user module folder, whose
    Documents path is empty: ``WindowsPowerShell\\Modules``) depends on the session's
    current folder: it is reported, and held to the same rule at the folder it resolves to.
    The registration itself refuses relative entries in the paths it reads."""
    known = {p.lower() for p in result["Roots"]["Registration"]}
    cwd, session = _session_roots(sessions["PathWithNetworkAccess"]["Roots"])
    assert session, "the session reported no module path"
    relative = [r for r in session if not FULLY_QUALIFIED.match(r["Entry"])]
    print("session current folder:", cwd)
    print("relative entries of the session's module path:", json.dumps(relative, indent=1))
    assert all(FULLY_QUALIFIED.match(r["Full"]) for r in session if r["Full"]), session
    unknown = [r for r in session if r["State"] != "absent" and r["Full"].lower() not in known]
    print("session folders outside the registration's set:", json.dumps(unknown, indent=1))
    selectable = [
        r for r in unknown if r["State"] == "error" or not r["Full"] or r["RoleCapabilities"]
    ]
    assert selectable == [], (selectable, result["Roots"]["Registration"])
    # the probe's own role capabilities are seen from inside the session, so the listing works
    listed = [f for r in session for f in r["RoleCapabilities"]]
    assert any(
        f.lower().endswith("\\refutejeaprobe\\rolecapabilities\\probebypath.psrc") for f in listed
    )


def test_a_relative_entry_is_searched_where_the_session_resolves_it(result, request):
    """Codex review of #99: the probe reads the module path after the session opened, so
    it does not show by itself that JEA's search (made when the session is created) resolves
    a relative entry the same way. A role capability with its own name, placed only where
    the session resolves the first relative entry, must be found by a real session
    (positive control); one placed in a folder on no module path must not (negative
    control). The positive control counts only in a folder no absolute entry reaches (the
    session's, the machine's or the host's module path), and its evidence is recorded in
    the JUnit file, which the CI prints (scripts/junit_counts.py --show): the entry, the
    resolved folder, whether it is exclusive, whether the control ran and opened. With no
    relative entry the positive control is recorded as not applicable, never as run."""
    relative = result["Relative"]
    nowhere = relative["Nowhere"]
    absolute = relative["Absolute"]
    absolute = [absolute] if isinstance(absolute, str) else list(absolute)
    control = relative["Control"]
    evidence = {
        "entry": relative["Entry"],
        "resolved": relative["Resolved"],
        "exclusive": relative["Exclusive"],
        "positive_control": relative["Applicable"],
        "positive_opened": None if control is None else control["Opened"],
        "negative_opened": nowhere["Opened"],
        "absolute_entries": absolute,
    }
    request.node.user_properties.append(("relative_entry_control", json.dumps(evidence)))
    print("relative entry control:", json.dumps(evidence, indent=1))
    assert not nowhere["Opened"] and "ProbeNowhere" in nowhere["Error"], nowhere
    if not relative["Entry"]:
        # this runner's session has no relative entry: the positive control does not apply
        assert relative["Applicable"] == "no relative entry" and control is None, relative
        return
    assert relative["Applicable"] == "ran", relative
    folder = relative["Resolved"].rstrip("\\").lower()
    assert relative["Exclusive"] is True
    assert folder not in {a.rstrip("\\").lower() for a in absolute}, relative
    _opened(control)


VISIBLE = [
    "Clear-Host",
    "Exit-PSSession",
    "Get-Command",
    "Get-FormatData",
    "Get-Help",
    "Get-RefuteVmStatus",
    "Invoke-RefuteVmOperation",
    "Measure-Object",
    "Out-Default",
    "Select-Object",
]
HYPERV_ABSENT = "Hyper-V is not available on this host"


def test_the_refutevm_endpoint_shows_exactly_its_ten_commands(result):
    """The real module and role capability (the maintainer's H.5 of 2026-10-16): the session
    opens with -EnableNetworkAccess and Get-Command shows exactly the two functions and the
    eight helper commands of RestrictedRemoteServer. The modules ModulesToImport adds for the
    functions (Microsoft.PowerShell.Utility, Hyper-V) stay invisible to the connecting
    account."""
    refute = result["RefuteVm"]
    assert refute["Opened"], refute
    assert sorted(refute["Commands"], key=str.lower) == sorted(VISIBLE, key=str.lower)


def _summary(c: dict) -> str:
    """A short line for the CI log (record_property): the outcome, and the top-level keys of
    the JSON output or the error."""
    if c["Ok"]:
        keys = sorted(json.loads(c["Output"]))
        return f"ok keys={','.join(keys)} bytes={len(c['Output'])}"
    return f"error {c['Exception']} {c['ErrorId']}: {c['Error'][:300]}"


@pytest.mark.parametrize("call", ["Status", "Simulate"])
def test_the_refutevm_calls_run_until_only_hyper_v_is_missing(result, call, record_property):
    """Get-RefuteVmStatus and Invoke-RefuteVmOperation -Operation SetHostPaths -Simulate run
    end to end on the runner, through the real endpoint. A command that is not recognized
    fails this test, whatever comes after it. On a host without the vmms service each call
    stops at the module's first Hyper-V call with the module's own message; on a host with
    it (the windows-2025 runner, since run 38934817010 of 2026-10-16) each call runs to its
    end: the status holds the observed state, the simulation its plan."""
    refute = result["RefuteVm"]
    assert refute["Opened"], refute
    c = refute[call]
    record_property("vmms", str(refute["Vmms"]))
    record_property("result", _summary(c))
    print(call, json.dumps(c, indent=1))
    text = c["Error"] + c["Output"]
    assert "is not recognized" not in text and "CommandNotFound" not in c["ErrorId"], c
    if refute["Vmms"]:
        # any failure on a host with the service keeps its own error and fails here
        assert c["Ok"], c
        out = json.loads(c["Output"])
        if call == "Status":
            assert {"Caller", "Config", "ConfigSha256", "Module", "Observed"} <= set(out), out
            assert out["Config"]["VmName"] == "refute-ci-vm"
        else:
            assert out["Mode"] == "simulated" and len(out["PlanSha256"]) == 64, out
    else:
        assert not c["Ok"] and HYPERV_ABSENT in c["Error"], c


def test_the_simulation_writes_its_record_as_the_virtual_account(result, record_property):
    """The simulated call writes one record to the operation log, as the session's virtual
    account (the caller is the connecting account, run as a WinRM virtual account), with
    the module hashes and the plan hash the call returned. Only where the runner has the
    vmms service; without it the call stops before any record."""
    refute = result["RefuteVm"]
    if not refute["Vmms"]:
        assert refute["LogRecords"] == [], refute["LogRecords"]
        pytest.skip("no vmms service on this runner: the call stops before any record")
    records = [json.loads(line) for line in refute["LogRecords"]]
    assert len(records) == 1, records
    record = records[0]
    caller = record["Caller"]
    record_property("caller", json.dumps(caller, sort_keys=True))
    record_property("module_files", ",".join(sorted(record["Module"])))
    assert record["Mode"] == "simulated" and record["Operation"] == "SetHostPaths"
    assert record["PlanSha256"] == json.loads(refute["Simulate"]["Output"])["PlanSha256"]
    assert caller["ConnectedUser"].lower() == refute["Account"].lower(), caller
    # a JEA virtual account is named "WinRM VA_<n>_<computer>_<user>"
    assert "\\winrm va_" in caller["RunAsUser"].lower(), caller
    files = {"RefuteVm.psm1", "RefuteVm.Config.psd1", "RoleCapabilities/RefuteVmOperator.psrc"}
    assert files <= set(record["Module"]), record["Module"]


def _norm(path: str) -> str:
    return path.rstrip("\\").lower()


def _as_list(value) -> list:
    # ConvertTo-Json writes a one-item array as the item itself, and an empty one as []
    if value is None:
        return []
    return [value] if isinstance(value, str) else list(value)


def test_set_host_paths_through_the_endpoint_needs_version_2_of_the_tree_acl(
    result, record_property
):
    """The failure of 2026-10-16 (#126, Codex review): on the maintainer's host the first
    real VM operation, SetHostPaths, failed through the endpoint with access denied, while
    the simulation passed. The simulation cannot catch it, so the runner makes the real
    call, in a new session for each version of the C:\\Hyper-V ACL: under version 1 (the
    registration of 2026-10-15) it must fail with access denied and leave the host paths
    as they were; under version 2 it must succeed and set them. Only where the runner has
    the vmms service and no C:\\Hyper-V of its own. The runner is Windows Server, not the
    maintainer's Windows 11: what it shows is evidence for the diagnosis, not a check of
    the host. Between them, version 1 with ChangePermissions only (no Virtual Machines
    entries) is tried and recorded, not asserted: it tells whether the maintainer's
    preferred change is enough for this operation on the runner. Each attempt starts from
    the original host paths, and the whole tree is checked before each. It does not show
    the other operations."""
    host_paths = result["RefuteVm"]["HostPaths"]
    print(json.dumps(host_paths, indent=1))
    if not host_paths["Ran"]:
        pytest.skip(host_paths["Reason"])
    original = host_paths["Original"]
    attempts = host_paths["Attempts"]
    v1, v2 = attempts["Version1"], attempts["Version2"]
    for name, attempt in attempts.items():
        record_property(
            f"{name}_real",
            _summary(attempt["Real"]) if attempt["Real"] else attempt["Error"],
        )
        record_property(f"{name}_root_after", json.dumps(attempt["RootAfter"]))
        for way in ("Baseline", "Restored", "HostAfter", "HostAfterNewProcess", "HostAfterModule"):
            record_property(f"{name}_{way}", json.dumps(attempt[way]))
    before = set(_as_list(host_paths["MembersBefore"]))
    for attempt in attempts.values():
        # the whole tree held exactly this version before the call
        assert attempt["TreeProblems"] == [], attempt
        assert attempt["Error"] == "" and attempt["Simulate"]["Ok"], attempt
        assert attempt["Real"] is not None, attempt
        # the positive control of the open-session check of Set-RefuteVmTreeAcl.ps1: while
        # a session is open, at least one wsmprovhost.exe runs. The members of Hyper-V
        # Administrators are recorded only: in run 38982160054 the session's virtual
        # account was not listed there, so a member check cannot find a session.
        hosts_before = set(_as_list(attempt["SessionHostsBefore"]))
        hosts_during = set(_as_list(attempt["SessionHostsDuringSession"]))
        assert hosts_during - hosts_before, attempt
        record_property(
            f"{attempt['Tree']}_members",
            json.dumps([sorted(before), sorted(_as_list(attempt["MembersDuringSession"]))]),
        )
        # each attempt starts from the original host paths, both read through CIM
        for key in ("VirtualMachinePath", "VirtualHardDiskPath"):
            assert _norm(attempt["Baseline"][key]) == _norm(original[key]), attempt
    # version 1: the module's own failure of SetHostPaths, with the access denied of
    # 2026-10-16 (0x80070005), and nothing changed
    denied = v1["Real"]["Error"]
    assert not v1["Real"]["Ok"], v1
    assert "SetHostPaths failed:" in denied and "0x80070005" in denied, v1
    assert _norm(v1["HostAfter"]["VirtualMachinePath"]) == _norm(original["VirtualMachinePath"]), v1
    assert _norm(v1["HostAfter"]["VirtualHardDiskPath"]) == _norm(
        original["VirtualHardDiskPath"]
    ), v1
    # version 2: done, and the host paths are the tree
    assert v2["Real"]["Ok"], v2
    assert json.loads(v2["Real"]["Output"])["Outcome"] == "done", v2
    assert _norm(v2["HostAfter"]["VirtualMachinePath"]) == "c:\\hyper-v", v2
    assert _norm(v2["HostAfter"]["VirtualHardDiskPath"]) == "c:\\hyper-v\\virtual hard disks", v2
    # and the tree stays exactly version 2 after the call: the service adds nothing to the
    # root, and every folder below still inherits exactly what version 2 passes down (the
    # property that justifies version 2; Codex review of the WP6 package)
    assert _as_list(v2["RootAfter"]) == _as_list(v2["RootBefore"]), v2
    assert _as_list(v2["TreeProblemsAfter"]) == [], v2
    record_property(
        "ChangePermissionsOnly_tree_after",
        json.dumps(_as_list(attempts["ChangePermissionsOnly"]["TreeProblemsAfter"])),
    )


def test_create_vm_through_the_endpoint_stores_the_vm_where_the_module_expects(
    result, record_property
):
    """The incident of operation 4 on the maintainer's host (2026-10-17): New-VM -Path
    <VmRoot> stored the VM in <VmRoot>\\<VmName>, the module's check expected <VmRoot>, and
    the call ended "not reached" with an empty reason. On the runner, after the version 2
    attempt, CreateVm runs for real through the endpoint with the test configuration
    (VmName refute-ci-vm): it must be done, Get-VM must report the VM in
    C:\\Hyper-V\\refute-vm\\refute-ci-vm; then, in a new session (the retake on the host;
    Codex review of #142), a CreateVm simulation must be already done and a SetMemory
    simulation must plan without a refusal. Only where SetHostPaths ran for real."""
    host_paths = result["RefuteVm"]["HostPaths"]
    if not host_paths["Ran"]:
        pytest.skip(host_paths["Reason"])
    create = result["RefuteVm"]["CreateVm"]
    print(json.dumps(create, indent=1))
    record_property("create_vm", json.dumps(create))
    assert create["Error"] == "", create
    assert create["Simulate"]["Ok"], create
    assert create["Real"]["Ok"], create
    assert json.loads(create["Real"]["Output"])["Outcome"] == "done", create
    assert create["Count"] == 1, create
    assert _norm(create["Path"]) == "c:\\hyper-v\\refute-vm\\refute-ci-vm", create
    assert create["Again"]["Ok"], create
    again = json.loads(create["Again"]["Output"])
    assert again["Plan"]["AlreadyDone"] is True and again["Plan"]["Refusal"] is None, create
    assert create["SetMemory"]["Ok"], create
    set_memory = json.loads(create["SetMemory"]["Output"])
    assert set_memory["Mode"] == "simulated", create
    assert set_memory["Plan"]["Refusal"] is None, create


PRIVATE = [
    "Get-FileHash",
    "Import-PowerShellDataFile",
    "Get-VMHost",
    "Microsoft.PowerShell.Utility\\Get-FileHash",
    "Microsoft.PowerShell.Utility\\Import-PowerShellDataFile",
    "Hyper-V\\Get-VMHost",
    "Get-Module",
    "RefuteVm\\Get-RefuteVmModuleFiles",
]


@pytest.mark.parametrize("name", PRIVATE)
def test_the_imported_commands_cannot_be_called_from_the_session(result, name):
    """Negative controls (Codex review of #118): the commands the role capability imports
    for the module's functions, and an internal function of the module, cannot be called by
    the connecting account, by name or module-qualified. Each is read-only."""
    refute = result["RefuteVm"]
    assert refute["Opened"], refute
    c = refute["Private"][name]
    assert not c["Ok"], c
    assert "CommandNotFound" in c["ErrorId"] or "is not recognized" in c["Error"], c


def test_the_discovery_set_is_exactly_the_folders_the_session_searches(result, sessions, request):
    """Codex review of #114: the effective discovery set the registration computes
    (Get-RefuteJeaDiscoveryRoots: machine PSModulePath, Program Files, $PSHOME\\Modules and
    the relative user entry resolved against %SystemRoot%\\system32) must be EQUAL to the
    folders a real RefuteVm-shaped session searches (every entry of its module path,
    resolved where the session resolves it), existing or not. The difference is recorded
    in the JUnit file. This is evidence for the GitHub runner only."""
    _, session = _session_roots(sessions["PathWithNetworkAccess"]["Roots"])
    observed = {r["Full"].rstrip("\\").lower() for r in session if r["Full"]}
    discovery = result["Roots"]["Discovery"]
    discovery = [discovery] if isinstance(discovery, str) else list(discovery)
    computed = {p.rstrip("\\").lower() for p in discovery}
    evidence = {
        "session": sorted(observed),
        "computed": sorted(computed),
        "missing_from_computed": sorted(observed - computed),
        "not_searched_by_the_session": sorted(computed - observed),
    }
    request.node.user_properties.append(("discovery_set", json.dumps(evidence)))
    assert observed == computed, evidence


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
