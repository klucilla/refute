"""The VM scripts of WP6 phase 1 (scripts/vm), checked with no Hyper-V and no network.

tests/vm/vm_cases.ps1 parses every script, reads the data files, lists the commands
each script calls and runs the pure logic of RefuteVm.Core.ps1 on synthetic observed
states. The seed ISO is built and read back where Windows' IMAPI2FS is available.
Skipped when no PowerShell is installed.
"""

from __future__ import annotations

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
def cases() -> dict:
    out = _run(ROOT / "tests" / "vm" / "vm_cases.ps1", "-Root", str(ROOT))
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
    blob = "AAAAC3NzaC1lZDI1NTE5AAAAIGq8Zx0k4lYtV2b1x7oQ4yYzW9xg0m3v5u6r8s9t0u1v"
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
