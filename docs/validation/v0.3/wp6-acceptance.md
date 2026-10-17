# WP6 acceptance: VM build and hardening, isolation tests, capacity control

Line numbers refer to docs/plans/v0.3-plan.md at commit 8456780.

Work package WP6 of [docs/plans/v0.3-plan.md](../../plans/v0.3-plan.md) (section 11,
line 885). Issue #49. Committed **before** the VM is built and before any test or code
of the package (plan lines 871-875). The requirements are in
[docs/sandbox.md](../../sandbox.md) and in plan section 6.1 (lines 345-408).

**Who builds and changes the VM** (revised on 2026-10-15 by decision of the
maintainer; plan section 7.1). The VM is built by versioned scripts in `scripts/vm/`
run by Claude Code through a local JEA endpoint, each mutating operation approved by
the maintainer; the maintainer's account is not a member of Hyper-V Administrators.
The maintainer registers the endpoint and performs every step that needs
administrator rights. No other Windows or Hyper-V setting is changed by an agent. No
third-party code runs until every test of section 3 passes and the maintainer records
the result.

## 1. Operating system of the VM

**Ubuntu Server 26.04.1 LTS (Resolute Raccoon), amd64**, installed from
`ubuntu-26.04.1-live-server-amd64.iso`.

- **Docker support.** The official Docker Engine installation page lists Ubuntu
  Resolute 26.04 (LTS), Noble 24.04 (LTS) and Jammy 22.04 (LTS) as supported. The
  latest LTS is therefore used. Source:
  https://docs.docker.com/engine/install/ubuntu/ (accessed 2026-10-14).
- **ISO.** The 26.04.1 point release, with the files `SHA256SUMS` and
  `SHA256SUMS.gpg`. Source: https://releases.ubuntu.com/26.04/ (accessed 2026-10-14).
  The maintainer checks the ISO's SHA-256 against `SHA256SUMS`, and the signature of
  `SHA256SUMS` against the Ubuntu key, and records both results.
- **Docker Engine.** Installed from Docker's official apt repository. Its version is
  recorded in every dossier, and the 7-day cooldown applies by hand (plan lines
  866-867).

## 2. VM configuration (plan 7.1, lines 496-522)

- **Hardware:** generation 2; Secure Boot with the "Microsoft UEFI Certificate
  Authority" template; 24 virtual processors; 16 GiB of static memory (the maintainer's
  decision of 2026-10-17; it was 48 GB, plan 7.1).
- **Disks:** one VHDX for the system, images and cache, and a differencing disk per
  paper on a clean base.
- **Host integration:** no shared folders; Enhanced Session off; Guest Service
  Interface off.
- **Results:** pulled by the host over SSH, with a key used only for this VM.

## 3. Validation of each requirement of section 6.1

Each test has a procedure, an expected result and the evidence kept: the command
output, a hash, and the date. A requirement is validated only when its test passes
on the built VM. The evidence goes to `docs/validation/v0.3/wp6-results/`, with no
host name, user name, address or credential beyond what the plan already states.

| # | Requirement | Test | Expected |
|---|---|---|---|
| V1 | Third-party code only in the VM | Review of the runner configuration: the docker backend refuses any context other than the VM's Docker Engine | refused outside the VM |
| V2 | Blocks to the Windows host, the LAN and private or special ranges, enforced outside the guest (IPv4 and IPv6) | Port ACLs on the VM's adapter (see note A). **Controlled targets with positive controls.** Listeners are set up by the maintainer on the host's virtual-switch address and on one LAN machine (TCP port, and ICMP echo allowed by the target). First, **with the ACLs removed**, the VM reaches each listener (positive control: the targets answer). Then, with the ACLs applied and nothing else changed, the same connections fail. The VM also tries each RFC 1918 range, 169.254.0.0/16, fc00::/7, fe80::/10 and the other IANA IPv6 special-purpose ranges in the list fixed by the test. The effective rules and their order are read with `Get-VMNetworkAdapterExtendedAcl` (or the basic ACL equivalent) and recorded | listeners reachable without ACLs and unreachable with them; the recorded rules and weights explain each block |
| V3 | The guest firewall is only a second layer | V2 and V4 repeated with the guest firewall disabled | the blocks still hold, so they come from the host-side ACLs |
| V4 | Build egress only through the allowlist intermediary, for the whole VM | The host-side ACLs allow outbound traffic only to the proxy endpoint. Tests run **from the guest shell, outside any container**, and from a build container, over IPv4 and IPv6: an allowed registry through the proxy works (positive control); a non-allowed host through the proxy fails; a direct connection to the internet that bypasses the proxy fails. They are repeated with the guest firewall disabled (V3) | allowed host works; the others fail, from the guest and from the container |
| V5 | Declared inputs fetched by Refute and hashed before repository code runs | Run on a synthetic repository: the fetch log and the hashes come before the first repository command | order and hashes recorded |
| V6 | Run phase without network | In a run container (`--network none`, adapter disconnected): DNS, TCP and ICMP to any destination | every attempt fails |
| V7 | Container limits, at run time **and during the build** | Inspect the run container (`docker inspect`): CPU, memory, PIDs, read-only root, `CapDrop: ALL`, `no-new-privileges`, non-root user. Inspect the builder container's limits. A fork bomb and a memory hog in a synthetic repository hit the limits, both in a run and in a `RUN` step of a synthetic Dockerfile. The active-time limit stops a synthetic job that sleeps; the disk quota stops a synthetic job that fills its volume | limits present and enforced in run and build |
| V8 | No mounts and no credentials, at run time and during the build | `docker inspect` of the run container: only the output mount; no Docker socket, no devices, not privileged; no SSH agent socket; the environment holds only the allowed variables. **Build:** the runner's build invocations contain no `--secret`, `--ssh` or build arguments with credentials, which a unit test checks on the generated command lines. **Sentinels:** fake credential values placed in the guest's environment, in a fake SSH agent socket and in a fake secret file must not be visible from any `RUN` step of a synthetic build, nor from a run (BuildKit secrets and SSH mounts: https://docs.docker.com/build/building/secrets/, accessed 2026-10-14) | no sentinel visible; invocations clean |
| V9 | BuildKit entitlements forbidden | The builder configuration file forbids `network.host`, `security.insecure` and `device`. A build that requests each one is refused. Source of the entitlement names: https://docs.docker.com/build/buildkit/toml-configuration/ (cited in the plan) | all three refused; the configuration file is hashed |
| V10 | Differencing disk per paper | Create a child disk, write a marker, discard it; a new child disk does not have the marker | clean state |
| V11 | Results only over SSH with the VM's key | No shared folder or Guest Service Interface (Hyper-V settings recorded); the host pulls a test file with the VM's key | settings off; pull works |
| V12 | Capacity control | `docker update --cpus` changes only the quota; `docker pause` and `unpause`; `Set-VMProcessor -Maximum` while running (the plan leaves this to verify, lines 590-591); `Suspend-VM` and `Resume-VM`, `Save-VM` and `Start-VM` on a running synthetic job | each control works, and CPU-hours do not grow during a pause |
| V13 | Pre-run memory check | Start a run with limits above the free memory | refused, with a clear message and no budget charged |
| V14 | A new container per run; base image pinned by digest; Python from the repository or the fixed ladder (plan line 370) | WP3 runner tests (subprocess backend in CI); on the VM, two runs of a synthetic repository create two containers with different IDs from the same image digest, recorded in the dossier | new container each run; digest recorded |
| V15 | The builder configuration file is recorded in every dossier (plan line 382) | Run a synthetic paper on the VM and check that the dossier holds the configuration file and its hash, equal to the hashed file of V9 | present and equal |
| V16 | Repository version rules (plan lines 383-388) | WP3 adapter tests: the commit named in the paper or README is used; without one, the latest on the draw date; tags resolve to commits; the three commits are recorded | as stated |
| V17 | Provenance and license of datasets and weights (plan lines 389-391) | WP3 adapter tests: reference, version, license, retrieval date and hashes recorded; no local copy when the license does not allow it | as stated |
| V18 | Build ladder and allowed patches fixed before the lock (plan lines 392-402) | WP3 runner tests: rungs tried in order, every attempt logged; a patch not in the hashed list is refused; a source edit after the lock is refused | as stated |
| V19 | Every run started by the maintainer or with the maintainer's approval for that paper (plan lines 403-405) | The runner refuses to start a paper without an approval record for that paper, checked by a test; on the VM, an attempt without the record is refused | refused without approval |
| V20 | CI tests only the subprocess backend (plan lines 406-408) | The CI suite contains the subprocess-backend tests and no test that pulls images | as stated |
| V21 | No privileged builder (plan lines 375-379; WP3 W3.10b) | `docker inspect` of every container that takes part in a build, including any builder container: `HostConfig.Privileged` is `false`, with no added devices or capabilities beyond the sandbox's. The `RUN` steps of a synthetic build run under the paper's parent cgroup, shown by their cgroup path | not privileged; build steps in the paper's cgroup |
| V22 | Budget control during a run (WP2 W2.10a) | On the VM, **measure first**: the quota period in effect, the reading delay and the stop latency, to derive the stopping margin M (WP3 revision). Then synthetic jobs that keep consuming CPU, including two concurrent containers in one claim and a bursty job, are stopped before their account passes its authorized balance. The recorded usage matches the parent cgroup within the tolerance | no account past its authorized balance; reserves intact; accounting complete |

V14 and V16 to V20 are covered by WP3 or WP2 tests where the code lives. This table
names them so that every requirement of plan 6.1 has a test and an evidence record.
For those rows the evidence is the name of the test, the commit, and the CI run (or
the local run, for docker tests) where it passed, plus the VM run where the row says
so.

**Note A, Hyper-V port ACLs.** `Add-VMNetworkAdapterExtendedAcl` filters by direction,
local and remote IP address (IPv4 and IPv6, host, subnet or wildcard), protocol and
ports, with a weight. Larger weights apply first, and the first matching entry decides.
Source: https://learn.microsoft.com/en-us/powershell/module/hyper-v/add-vmnetworkadapterextendedacl
(accessed 2026-10-14). That page is published for Windows Server; **whether the cmdlet
works under Hyper-V on Windows 11 is verified on the machine first**. Only extended ACLs
are used, with no fallback (the maintainer's decision of 2026-10-17, which replaced the
earlier fallback to the basic `Add-VMNetworkAdapterAcl`): if they do not work, phase 2
stops for the maintainer's decision. The same page distinguishes `0.0.0.0/0` (all IPv4),
`::/0` (all IPv6) and `ANY` (both); the module keeps them distinct, and compares the
`IsolationID` of each entry (0, no isolation).

**Note B, Docker and the guest firewall.** Docker Engine creates its rules with
iptables by default and also supports nftables, selected with the daemon option
`firewall-backend`. Source: https://docs.docker.com/engine/network/packet-filtering-firewalls/
(accessed 2026-10-14). The installation page also warns that ports exposed by Docker
bypass ufw and firewalld rules. Source:
https://docs.docker.com/engine/install/ubuntu/ (accessed 2026-10-14). The guest layer
(V3) is therefore written for Docker's chains, and it is never the only protection.

## 4. Capacity-control commands (plan 7.5, lines 580-603)

- **W6.1** `refute throttle --cpus N`, `refute throttle --reset`, `refute pause`,
  `refute resume` and `refute status`, inside the VM. Each command records an event
  with a UTC timestamp in `run/events.jsonl`, and a heartbeat every 10 s records
  gaps longer than 30 s as pauses.
- **W6.2** A small documented PowerShell script for the VM-level controls, run
  through the JEA endpoint of section 4a, each call approved by the maintainer.
- **W6.3** Synthetic tests in CI for the event log and the heartbeat logic, with no
  Docker and no VM. The Docker and VM parts are tested by V12 on the built VM.

## 4a. Phase 1 scripts and the JEA endpoint (scripts/vm/README.md)

- **W6.4 Endpoint.** One local JEA endpoint, `RefuteVm`: `SessionType
  RestrictedRemoteServer` (NoLanguage); a virtual account in Hyper-V Administrators
  only; one role capability exposing only `Get-RefuteVmStatus` and
  `Invoke-RefuteVmOperation`, for the maintainer's account only; no parameter takes a
  path or a VM name; the module and its configuration installed where only
  administrators can write; `-AccessMode Local`; WinRM listeners on `127.0.0.1` and
  `::1` only and a firewall rule that blocks inbound TCP 5985 and 5986 from every
  address except loopback, on every profile; transcripts of every session in
  `C:\ProgramData\RefuteVm\Transcripts`. The registration script shows every change
  and a hash of the list before it applies it, applies only with that hash, adds the
  firewall rule and checks the active policy and the listeners before WinRM is
  started, registers the endpoint last after its post-conditions hold, never deletes
  or overwrites, and writes the evidence.
- **W6.5 Operations.** One administrative action per call. A simulation computes the
  plan (target, the observed preconditions, every change with its value before and
  after, refusal) and its SHA-256 without changing the managed state; the real call
  needs that hash, holds an exclusive lock from its observation to its final check,
  and refuses if the plan changed. Media are copied only through a verified copy
  (source read without write sharing, hashed while copied, moved into place only if
  the hash matches, never overwriting). Every simulation, intent, refusal and result is logged.
  Every operation checks the VM's identity (the VMId recorded at creation, its name,
  its paths, its disks and media) and refuses any divergence. **Network (phase 2;
  changed by the maintainer's decision of 2026-10-17, wp6-results/
  phase2-network-design.md):** the VM has one network adapter, identified by its Id.
  It is connected only to the internal switch of the configuration, identified by its Id
  and type, and only while the port's extended ACLs equal, entry by entry (IPv4 and
  IPv6, with their weights and stateful flags), one of the reviewed profiles of the
  configuration (`build`, `pull`). The ACLs are changed only while the adapter is
  disconnected and are read back after each change, by one call that sets a whole
  profile; a run starts only with the adapter disconnected. Every operation except
  `DisconnectNetwork` refuses an adapter connected to another switch, a second adapter,
  or a port whose ACLs differ from the profile in force; `DisconnectNetwork` stays
  available in every such state. The media imports also need the adapter disconnected.
  The switches, the host's addresses on them and the proxy VM are set up by the
  maintainer as Administrator, not by the endpoint. No operation deletes a VM or a
  disk, turns a VM off without a guest shutdown, enables an integration service or
  turns Secure Boot off.
- **W6.6 Synthetic tests (CI, no Hyper-V).** Every script parses; every data file
  loads; the pure logic refuses each divergence above and plans each change; the plan
  hash is deterministic and changes with the observed state; the operation lists of
  the module and of the caller are the same; no script calls a forbidden command; the
  scripts are ASCII; the seed ISO is a CIDATA volume with the rendered `user-data` and
  `meta-data` (where IMAPI2FS exists). On the machine, the evidence of W6.4 is
  recorded before the first operation, and the first operation is shown simulated to
  the maintainer before it runs.

## 5. Synthetic cases, metrics and regression

- **Synthetic cases (W6.3, CI, no Docker, no VM).**
  - **Must pass:** each command records its event with a UTC timestamp; a heartbeat
    gap of 31 s is recorded as a pause; a reset restores the CPU limit written in the
    claim.
  - **Must fail:** a malformed or out-of-order event is refused; a gap of 30 s or less
    is not recorded as a pause; a throttle with a non-positive value is refused.
- **Metrics:** every row V1 to V22 has a pass or fail result with its evidence and
  date. Test counts of W6.3 come from a JUnit XML file.
- **Regression:**
  - the existing suite passes;
  - after any later change to the VM's network, Docker Engine, the builder or the
    host-side ACLs, rows V2 to V9, V21 and V22 are run again before any third-party
    code runs, with the new results recorded.

## 5a. Isolation test (V3), replacing the battery V1 to V22 (2026-10-17)

By the maintainer's decision of 2026-10-17, the battery of section 3 (V1 to V22) and
W6.1 to W6.6 are replaced by **one isolation test**, run once at the end of phase 2:
`scripts/vm/isolation/run_isolation.py` (host side, from a saved `-Status`) and
`scripts/vm/isolation/guest_checks.sh` (guest side, through SSH with the checked host key).
**Its approval is the condition for running third-party code.** It needs no state with
fewer ACLs than a profile: an allowed port and a listening port outside the list on the
same target show that the block comes from the port ACLs.

| Check | What it shows | Old items it covers |
|---|---|---|
| `proxy_port_open`, `proxy_ssh_blocked` | on the proxy, port 3128 answers and its listening SSH is blocked | V2 (blocks enforced outside the guest, with a positive control on the same target), V4 |
| `host_<port>_blocked` (22, 80, 135, 139, 443, 445, 3389, 5985, 5986) | nothing the guest starts reaches the Windows host | V2 |
| `private_<address>_blocked` | private and link-local targets are not reached | V2 (LAN and special ranges) |
| `direct_tcp_*_blocked`, `no_dns` | no direct path to the internet, no name resolution in the guest | V4 (no bypass of the proxy) |
| `proxy_allows_pypi`, `proxy_refuses_example_com`, `proxy_refuses_ip_literal`, `proxy_refuses_other_port` | the proxy passes the allowlist only | V4 |
| `no_ipv6_address`, `ipv6_blocked` | no IPv6 address, and with a temporary link-local address no other node answers | V2 and V4 (IPv6) |
| `container_network_none` | a container with `--network none` has only `lo` and reaches neither the proxy nor the internet (the image needs only bash: the Ubuntu image, pinned by digest) | V6 |
| host: `one_adapter`, `adapter_on_configured_switch`, `switch_internal`, `port_acls_equal_build` | the network as W6.5 requires, the ACLs read back equal to the profile | V2 (recorded rules), W6.5 |
| host: `guest_service_interface_off`, `enhanced_session_off`, `no_dvd_drive` | no host integration channel | V11 (settings), section 2 (no shared folders, Enhanced Session off, Guest Service Interface off) |

**No longer tested by WP6, and why** (the maintainer's decision: test the essential once,
before third-party code):
- **V1, V5, V7, V8, V9, V13 to V21:** properties of Refute's runner and builder, covered by
  the synthetic tests of WP2 and WP3 in CI; the container limits, mounts, entitlements and
  the builder configuration of each real run are recorded in its dossier.
- **V3** (the guest firewall only a second layer): no guest firewall is configured; every
  block of the test is on the host side by construction (port ACLs).
- **V2's LAN machine as a positive control:** the guest has no route to the LAN; the port
  ACLs deny every address but the two allowed ones, and the same-target check shows that
  they block.
- **V10** (a differencing disk per paper): not built; the development papers run on the
  base disk, and the maintainer decides before the main sample.
- **V12** (capacity control on a running job) and **W6.1 to W6.3** (`refute throttle`,
  `pause`, `resume`): the endpoint's `SetProcessorMaximum`, `SuspendVm`, `ResumeVm`,
  `SaveVm` and `StopVm` are available and tested when used; the guest-side commands are
  not built.
- **V22** (the stopping margin of the budget): measured on the first real run, not before.
- **W6.4 and W6.6:** recorded in `wp6-results/jea-registration.md` and kept green in CI.

## 6. Acceptance of the package

**Since 2026-10-17:** WP6 is accepted when the isolation test of section 5a passes, with
its report recorded in `wp6-results/`, and the maintainer records the result. Until then
[docs/sandbox.md](../../sandbox.md) keeps saying "not yet validated", and no
third-party code runs. (Before 2026-10-17 the condition was every row V1 to V22 and W6.1
to W6.3.)

## 7. Closing task: decommission the VM (issue #135)

Decided by the maintainer on 2026-10-16: the Refute VM is removed when the v0.3 tests end,
as a closing task of WP6. This is a task, not an acceptance criterion; the list of what
goes and the rules are in issue #135. In short: nothing is deleted automatically; the
maintainer does the removal as Administrator, with a preview; the records in
`C:\ProgramData\RefuteVm` are archived, with a checked SHA-256 manifest, before any
deletion there. No removal script is written before that task.
