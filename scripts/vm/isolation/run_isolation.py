"""The WP6 isolation test, run once at the end of phase 2 (wp6-acceptance.md, "Isolation
test (V3)"; the maintainer's decision of 2026-10-17). Its approval is the condition for
running third-party code.

Two halves:
- **host side**, from the output of ``scripts/vm/Invoke-RefuteVm.ps1 -Status`` saved by
  the maintainer to a file (the endpoint is his to call): one adapter, connected to the
  configured internal switch, the port's ACLs equal to the ``build`` profile, the Guest
  Service Interface disabled, Enhanced Session off on the host, no DVD drive;
- **guest side**, ``guest_checks.sh`` run inside the Refute VM through SSH with the VM's
  key and a known_hosts file that holds only the host key checked against the console.

It writes a Markdown report and the raw lines into the given folder (never overwriting),
and exits 0 only when every check passes.

Usage::

    .venv/Scripts/python.exe scripts/vm/isolation/run_isolation.py --status <status.json>
        --known-hosts <file> --image <image@sha256:...> --out <folder>
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
KEY = Path(r"C:\Projetos\refute\.cache\vm\ssh\refute_vm_ed25519")
VM = "refute@10.231.71.2"
GSI_NAMES = ("Guest Service Interface", "Interface de Servi\u00e7o de Convidado")
# The client options of every SSH of Refute to its VMs. The host's client
# (OpenSSH_for_Windows 9.5p2, LibreSSL 3.8.2) fails the default key exchange with the
# guests' OpenSSH 10.2p1 ("choose_kex: unsupported KEX method
# sntrup761x25519-sha512@openssh.com", observed by the maintainer on 2026-10-17); the key
# exchange is pinned to curve25519-sha256 (RFC 8731). That client offers neither SNTRUP
# nor ML-KEM (`ssh -Q kex`; PowerShell/Win32-OpenSSH issue 2140, read 2026-10-17), so the
# post-quantum risk is accepted, reduced (not removed) by a switch that only the host and
# the VMs share. Codex review of 2026-10-17: no user or system configuration (-F none), the
# checked known_hosts file only, the host key type pinned to ED25519 (the identity comes
# from that file), the given key file only, and no agent, X11 or port forwarding to a VM
# that runs third-party code.
SSH_OPTIONS = (
    "-F", "none",
    "-o", "KexAlgorithms=curve25519-sha256",
    "-o", "HostKeyAlgorithms=ssh-ed25519",
    "-o", "StrictHostKeyChecking=yes",
    "-o", "GlobalKnownHostsFile=none",
    "-o", "BatchMode=yes",
    "-o", "IdentitiesOnly=yes",
    "-o", "ForwardAgent=no",
    "-o", "ForwardX11=no",
    "-o", "ClearAllForwardings=yes",
)  # fmt: skip


def build_profile() -> list[dict]:
    """The build profile as the module writes it (RefuteVm.Core.ps1, Get-RefuteVmAclProfile),
    in the normalized form the status reports."""

    def rule(direction, action, remote, weight, protocol="ANY", local="", rport="", stateful=False):
        return {
            "Action": action, "Direction": direction, "LocalIPAddress": "ANY", "LocalPort": local,
            "Protocol": protocol, "RemoteIPAddress": remote, "RemotePort": rport,
            "Stateful": stateful, "Weight": weight, "IsolationID": 0,
        }  # fmt: skip

    return [
        rule("Inbound", "Allow", "10.231.71.1", 100, "TCP", "22", "", True),
        rule("Outbound", "Allow", "10.231.71.3", 90, "TCP", "", "3128", True),
        rule("Inbound", "Deny", "ANY", 2),
        rule("Outbound", "Deny", "ANY", 1),
    ]


def _canon(rules: list[dict]) -> list[str]:
    return sorted(json.dumps(r, sort_keys=True) for r in rules)


def host_checks(status: dict) -> list[tuple[str, bool, str]]:
    checks = []
    config = status["Config"]
    vms = [v for v in status["Observed"]["Vms"] if v["Name"] == config["VmName"]]
    if len(vms) != 1:
        return [("vm_found", False, f"{len(vms)} VMs named {config['VmName']}")]
    vm = vms[0]
    adapters = vm["NetworkAdapters"]
    checks.append(("one_adapter", len(adapters) == 1, f"{len(adapters)} adapters"))
    if adapters:
        a = adapters[0]
        checks.append(
            (
                "adapter_on_configured_switch",
                bool(config["NetworkSwitchId"]) and a.get("SwitchId") == config["NetworkSwitchId"],
                f"switch {a.get('SwitchName')!r}",
            )
        )
        switches = [
            s
            for s in status["Observed"].get("Switches", [])
            if s["Id"] == config["NetworkSwitchId"]
        ]
        checks.append(
            (
                "switch_internal",
                len(switches) == 1 and switches[0]["SwitchType"] == "Internal",
                str(switches),
            )
        )
        checks.append(
            (
                "port_acls_equal_build",
                _canon(a.get("Acls", [])) == _canon(build_profile()),
                f"{len(a.get('Acls', []))} entries",
            )
        )
    gsi = [s for s in vm["IntegrationServices"] if s["Name"] in GSI_NAMES]
    checks.append(
        ("guest_service_interface_off", len(gsi) == 1 and gsi[0]["Enabled"] is False, str(gsi))
    )
    checks.append(
        (
            "enhanced_session_off",
            status["Observed"]["Host"]["EnableEnhancedSessionMode"] is False,
            str(status["Observed"]["Host"]["EnableEnhancedSessionMode"]),
        )
    )
    checks.append(("no_dvd_drive", vm["DvdDrives"] == [], str(vm["DvdDrives"])))
    return checks


def guest_checks(known_hosts: Path, image: str) -> tuple[list[tuple[str, bool, str]], str]:
    script = (HERE / "guest_checks.sh").read_bytes()
    cmd = [
        "ssh", "-i", str(KEY), "-o", f"UserKnownHostsFile={known_hosts}", *SSH_OPTIONS, VM,
        f"ISOLATION_IMAGE='{image}' bash -s",
    ]  # fmt: skip
    out = subprocess.run(cmd, input=script, capture_output=True, timeout=900)
    text = out.stdout.decode("utf-8", "replace")
    checks = []
    for line in text.splitlines():
        if line.startswith("CHECK "):
            _, name, verdict, *detail = line.split(" ")
            checks.append((name, verdict == "PASS", " ".join(detail)))
    if "END" not in text.splitlines():
        checks.append(
            ("guest_script_completed", False, out.stderr.decode("utf-8", "replace")[-500:])
        )
    return checks, text


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--status", type=Path, required=True)
    parser.add_argument("--known-hosts", type=Path, required=True)
    parser.add_argument("--image", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if "@sha256:" not in args.image:
        raise SystemExit("the image must be pinned by digest")
    status = json.loads(args.status.read_text(encoding="utf-8-sig"))
    host = host_checks(status)
    guest, raw = guest_checks(args.known_hosts, args.image)
    when = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    args.out.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# Isolation test, {when}",
        "",
        "| Side | Check | Result | Detail |",
        "|---|---|---|---|",
    ]
    for side, checks in (("host", host), ("guest", guest)):
        for name, ok, detail in checks:
            lines.append(f"| {side} | `{name}` | {'PASS' if ok else 'FAIL'} | {detail} |")
    passed = all(ok for _, ok, _ in host + guest)
    lines += ["", f"Result: **{'every check passed' if passed else 'at least one check failed'}**."]
    with (args.out / f"isolation-{when[:10]}.md").open("x", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    with (args.out / f"isolation-{when[:10]}-guest.txt").open("x", encoding="utf-8") as f:
        f.write(raw)
    print("\n".join(lines))
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
