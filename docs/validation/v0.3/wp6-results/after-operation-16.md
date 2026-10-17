# WP6: what comes after operation 16 (prepared 2026-10-17, nothing run)

Preparation only. **Nothing here was run, and nothing here authorizes a step:** every VM
operation goes through the JEA endpoint, simulated first and approved by the maintainer
(`scripts/vm/README.md`; [operations-roadmap.md](operations-roadmap.md)); every step as
Administrator is the maintainer's. Facts about Ubuntu and Hyper-V come from the sources of
section 7, read on 2026-10-17. Where no source settles a point, the text says it is to be
observed on the host.

**Phase 1** is the VM with no network (`scripts/vm/README.md`: "In phase 1 the VM has no
network"). **Phase 2** is everything that needs a network path: the host-side ACLs, the
egress allowlist, Docker and most acceptance tests. No third-party paper code runs until
every acceptance test of `wp6-acceptance.md` passes and the maintainer records the result.

## 1. Operation 16, StartVm, and the automatic installation

**What is on the VM when operation 16 runs** (operations 4 to 15 of the roadmap): generation
2, Secure Boot with `MicrosoftUEFICertificateAuthority`, 24 processors, 48 GiB of static
memory, no checkpoints, adapter not connected, Guest Service Interface off, the empty base
disk, two DVD drives (the Ubuntu 26.04.1 live server ISO and the CIDATA seed) and the
install ISO as first boot device.

**What the seed asks for** (`scripts/vm/seed/user-data.template`, autoinstall version 1):

| Key | Value | Effect (autoinstall reference) |
|---|---|---|
| `interactive-sections` | `[]` | no section is asked on the console |
| `refresh-installer` | `update: false` | the installer does not try to update itself (it has no network) |
| `network` | no interface configured | the installed system has no network configuration |
| `apt` `fallback` | `offline-install` | what the installer does "when no primary mirror is usable": install from the ISO |
| `storage` | `layout: direct` | the whole base disk, no LVM |
| `ssh` | server installed, no password login | |
| `updates` | `security` | "updates that will be downloaded and installed after the system installation"; with no network nothing can be downloaded (to observe: whether the installer skips this step or reports it) |
| `shutdown` | `poweroff` | "Request the system to power off ... automatically after the installation has finished" (the default is `reboot`) |
| `user-data` | hostname `refute-vm`; root disabled; user `refute` with a locked password, passwordless sudo, and the VM's SSH public key | applied by cloud-init on the first boot of the installed system |

**Step by step:**

1. The maintainer runs operation 16 (`StartVm`), simulated and then approved. `-Status`
   shows `State` `Running`. Starting reserves 48 GiB of static memory on a host with
   63.9 GB (plan 7.1): it can fail if that much is not free.
2. The maintainer opens the console (Hyper-V Manager or `vmconnect`), **as Administrator**,
   because the maintainer's own account has no Hyper-V rights. The installer stops at
   "Continue with autoinstall? (yes|no)", because the seed was found but `autoinstall` is
   not on the kernel command line (zero-touch page, section 7). The maintainer answers
   `yes`. This answer is what lets the installer write the disk.
3. The installer partitions the base disk, installs from the ISO, configures the user and
   the SSH server, and powers the VM off (`shutdown: poweroff`).
4. **How long:** not measured, and no source gives a duration for this machine. It is
   recorded when it happens: the time of the `StartVm` result in `operations.jsonl` and the
   time the VM is seen `Off`.
5. **How to confirm that it finished and that the VM is off:**
   - `scripts\vm\Invoke-RefuteVm.ps1 -Status` shows `State` `Off` after `Running`, with no
     `StopVm` called (the endpoint never turns a VM off without a guest shutdown);
   - the console showed the end of the installation before the power-off (a screenshot or
     a note by the maintainer is the evidence, without host or user names);
   - if the VM is still `Running` long after the console is idle, or the console shows an
     error, the maintainer stops there and nothing else runs.
6. **Network:** none during the whole installation (the adapter has no switch since
   operation 4; operation 9 checks it). The installer cannot reach any mirror; this is why
   `fallback: offline-install` is set.

## 2. Removing the install media and the first boot from the disk

1. **`DetachInstallMedia`** (an endpoint operation that already exists): it needs the VM
   `Off` and the base disk attached. It removes every DVD drive (the install ISO and the
   seed) and sets the first boot device to the base disk (`RefuteVm.Core.ps1`, the plan of
   `DetachInstallMedia`). Simulated, then approved by the maintainer.
2. **`StartVm`** again: the first boot from the disk. cloud-init applies the `user-data` of
   the seed it saw during the installation (user `refute`, the SSH key, hostname). Still no
   network.
3. **What can be checked in phase 1:** the console shows the boot and a login prompt with
   the hostname `refute-vm`. **No login is possible in phase 1, by design:** the only user
   has a locked password and SSH needs a network path. So no command runs inside the guest
   until phase 2; the first access to a shell is the first SSH session of phase 2.
4. **Stopping it:** `StopVm`, a guest shutdown "through the guest operating system"
   (Stop-VM, section 7), never a power cut. Ubuntu's Linux Integration Services are built
   in (Microsoft's support page, section 7); that page lists Ubuntu up to 24.04 LTS, so
   whether the shutdown integration answers on 26.04 is **to observe** at this step. If it
   does not, the maintainer decides; no endpoint operation can force it.
5. **After this,** the downloaded ISO in `.cache\vm\media` becomes regenerable and is
   deleted by its literal path (`scripts/vm/README.md`, "Install media after the
   installation"), keeping its hash and the verification evidence. The copies in
   `C:\Hyper-V\refute-vm\media` are outside the project: their removal is the
   maintainer's decision (issue #135).

## 3. How the host talks to the VM

**Phase 1 (no network):**

- Hyper-V state through the endpoint: `-Status` (state, settings, disks, integration
  services) and the operations of the roadmap.
- The console (`vmconnect`), by the maintainer as Administrator: read-only in practice,
  since no account can log in.
- Nothing else: no shared folder, Enhanced Session off, Guest Service Interface off (no
  file copy from the host), no network. Hyper-V sockets and the key/value pair exchange
  are integration features the support page lists; Refute does not use them, and no
  operation of the module reads them.

**Phase 2 (results over SSH, plan 7.1 and `wp6-acceptance.md` V11):**

- **The key already exists.** It was made in step 2 of `scripts/vm/README.md`
  (`ssh-keygen -t ed25519 -C refute-vm -f C:\Projetos\refute\.cache\vm\ssh\refute_vm_ed25519`,
  used only for this VM), before the seed was built on 2026-10-15; its public half is in
  the seed (`{{SSH_PUBLIC_KEY}}` of the template), so the guest receives it at the first
  boot. **No new key is made.** The private key stays in `.cache\vm\ssh` (git-ignored), is
  never archived by the generic cleanup and is never deleted automatically.
- **When it is used:** only once phase 2 gives the VM a network path that lets the host
  reach port 22 of the guest. Until then the key is inert.
- **How (to be designed and approved in phase 2):** the host connects with that key to
  user `refute`. The host-side ACLs must allow exactly that path (host to guest, TCP 22,
  and its replies) while blocking every connection the guest starts toward the host and
  the LAN (V2). The run phase keeps the adapter disconnected (plan 6.1), so results are
  pulled after a run, in a separate step with the adapter connected to the restricted
  switch. The exact sequence (connect for the build, disconnect for the run, connect for
  the pull) is a phase 2 design item for the maintainer.

## 4. The WP6 acceptance tests: what each needs and when it runs

From `wp6-acceptance.md` (sections 3 and 4). "Endpoint" means a new or existing operation
of the module, simulated and approved; "maintainer" means a step as Administrator or a
setup outside the VM.

| Test | What it needs | Phase | Owner of the steps |
|---|---|---|---|
| W6.4 Endpoint | registration evidence, NoLanguage, groups, loopback WinRM, transcripts | 1 (in progress: registered and used, restrictions in operation not all validated yet) | maintainer (records), Claude (record PRs) |
| W6.5 Operations | every operation simulated, approved and logged | 1 (operations 1 to 3 validated; 4 created the VM; 5 to 16 pending) | maintainer (approves and runs), Claude (prepares) |
| W6.6 Synthetic tests | CI | done in CI, kept green | Claude |
| W6.1 `refute throttle`/`pause`/`resume`/`status` inside the VM | Docker in the VM, the event log | 2 | Claude (code), maintainer (runs on the VM) |
| W6.2 VM-level control script | endpoint operations `SetProcessorMaximum`, `SuspendVm`, `ResumeVm`, `SaveVm`, `StartVm` (they exist) | 1 for the operations; 2 for a running job | maintainer approves each call |
| W6.3 Synthetic tests of the event log and heartbeat | CI | any time (no VM) | Claude |
| V1 third-party code only in the VM | runner configuration review | 2 | Claude, Codex |
| V2 host, LAN and special ranges blocked outside the guest | vSwitch, port ACLs (new endpoint operations), listeners on the host and on a LAN machine, positive controls | 2 | maintainer (switch, listeners, approval of each ACL), Claude (scripts) |
| V3 guest firewall only a second layer | V2 and V4 with the guest firewall off | 2 | maintainer approves, Claude runs over SSH |
| V4 build egress only through the allowlist proxy | the proxy, its allowlist, ACLs allowing only the proxy | 2 | maintainer (where the proxy runs, the allowlist), Claude (config, tests) |
| V5 declared inputs fetched and hashed first | a synthetic repository | 2 (on the VM) | Claude |
| V6 run phase without network | a run container with `--network none`, adapter disconnected | 2 | Claude, maintainer approves |
| V7 container limits in run and build | Docker, synthetic fork bomb, memory hog, disk filler | 2 | Claude |
| V8 no mounts, no credentials, sentinels | Docker, BuildKit | 2 | Claude |
| V9 BuildKit entitlements forbidden | builder configuration file | 2 | Claude |
| V10 differencing disk per paper | new endpoint operations to create, attach and discard a child disk | 1 or 2 (host side; the marker is written from inside the guest, so it needs SSH) | maintainer approves, Claude (operations) |
| V11 results only over SSH with the VM's key | settings recorded (phase 1) and a pull with the key (phase 2) | 1 + 2 | maintainer approves |
| V12 capacity control | Docker and the VM-level operations on a running synthetic job | 2 | maintainer approves each VM-level call |
| V13 pre-run memory check | the runner on the VM | 2 | Claude |
| V14, V16 to V20 | WP3/WP2 tests (CI), plus a VM run where the row says so | CI now; VM part in 2 | Claude |
| V15 builder configuration in every dossier | a synthetic paper on the VM | 2 | Claude |
| V21 no privileged builder | Docker, BuildKit, cgroup paths | 2 | Claude |
| V22 budget control during a run | measure first the quota period, the reading delay and the stop latency on the VM, then the stopping margin M | 2 | Claude (measurements and tests), maintainer approves |

## 5. Phase 2, step by step (a plan to be approved; nothing is decided here)

Each step names its owner and the kind of approval. "PR" means a reviewed change (Codex
until agreement); "maintainer OK" means an explicit decision in chat before it runs;
"Administrator" means the maintainer runs it.

1. **Design document of the network** (owner: Claude; approval: maintainer OK on the
   document). It decides, with sources:
   - the switch type for the VM (an internal or private switch; an external switch is
     excluded unless the maintainer decides otherwise) and its address plan, IPv4 and
     IPv6;
   - where the forwarding proxy runs and what it is (the plan names "a controlled
     intermediary (a forwarding proxy) with an allowlist"; it does not choose the
     software or its place);
   - the exact ACL list: extended ACLs if `Add-VMNetworkAdapterExtendedAcl` works under
     Hyper-V on Windows 11, checked on the machine first (note A of `wp6-acceptance.md`),
     otherwise the basic ACLs; how SSH from the host to the guest is allowed while every
     connection the guest starts toward the host and the LAN is blocked;
   - the connect, disconnect and pull sequence of section 3.
2. **Changes to the acceptance criteria that phase 2 needs** (owner: Claude; approval:
   maintainer OK, since they change merged criteria): W6.5 says today that no operation
   "connects a network adapter". Phase 2 needs operations that create or select the
   switch, set and read the ACLs, and connect or disconnect the adapter.
3. **New endpoint operations** (owner: Claude, PR with synthetic tests; approval: the
   maintainer's OK to install them, Administrator for the module update with
   `Update-RefuteVmConfig.ps1`, and each call approved). Creating a virtual switch
   changes the host's network configuration: whether that is an endpoint operation or an
   Administrator step is a decision for the maintainer.
4. **The allowlist** (owner: Claude proposes from the plan: the package registries and the
   declared data hosts, plus what the VM itself needs, for example Ubuntu's archive and
   Docker's apt repository; approval: maintainer OK on the list, hashed and recorded).
5. **Listeners for V2** (owner: the maintainer, on the host's virtual-switch address and
   on one LAN machine; Claude writes the procedure). First with the ACLs removed (positive
   control), then with them applied.
6. **First SSH session** (owner: the maintainer approves; Claude connects with the VM's
   key): record the guest's identity (host key fingerprint, OS release) as the first
   evidence of phase 2.
7. **Docker Engine in the VM** (owner: Claude, over SSH, through the proxy; approval:
   maintainer OK): from Docker's official apt repository for Ubuntu 26.04 (listed as
   supported, `wp6-acceptance.md` section 1), with the 7-day cooldown applied by hand and
   the version recorded in every dossier. The builder configuration file with the three
   forbidden entitlements (V9) is written and hashed.
8. **Measurements for V22** (owner: Claude; approval: maintainer OK on the procedure):
   the CPU quota period in effect, the delay of a cgroup reading and the stop latency,
   measured on the VM, before the stopping margin M is fixed (WP3 revision). These are
   measurements, not CI assertions on a real clock (the timing rule of 2026-10-16).
9. **The acceptance tests V1 to V22 and W6.1 to W6.3** in the order of their needs
   (section 4), each with its evidence in `docs/validation/v0.3/wp6-results/`, no host
   name, user name or address beyond what the plan already states.
10. **The maintainer records the WP6 result.** Only then can third-party code run.

## 6. What depends on the maintainer

- Operations 4 to 16: each simulation checked and each call approved; the console answer
  "Continue with autoinstall?" (as Administrator).
- After the installation: the record that the VM powered off; `DetachInstallMedia` and the
  first boot from the disk; the stop.
- Phase 2: the network design (switch type, address plan, where the proxy runs), the
  change of W6.5, the installation of the new operations, the switch creation if it is an
  Administrator step, the allowlist, the V2 listeners, the first SSH session, Docker's
  installation, and the final WP6 record.

## 7. Sources (read 2026-10-17)

- Autoinstall configuration reference, `shutdown` ("Request the system to power off or
  reboot automatically after the installation has finished"), `updates` ("The type of
  updates that will be downloaded and installed after the system installation"), `apt`
  `fallback` ("controls what Subiquity does when no primary mirror is usable"):
  https://canonical-subiquity.readthedocs-hosted.com/en/latest/reference/autoinstall-reference.html
- Zero-touch deployment with autoinstall ("Confirmation is required to continue. Add
  'autoinstall' to your kernel command line to avoid this"):
  https://canonical-subiquity.readthedocs-hosted.com/en/latest/explanation/zero-touch-autoinstall.html
- Supported Ubuntu virtual machines on Hyper-V ("Linux Integration Services (LIS) is
  included as part of this Linux distribution"; the table lists Ubuntu up to 24.04 LTS):
  https://learn.microsoft.com/en-us/windows-server/virtualization/hyper-v/supported-ubuntu-virtual-machines-on-hyper-v
- Stop-VM ("Shuts down virtual machine TestVM through the guest operating system"):
  https://learn.microsoft.com/en-us/powershell/module/hyper-v/stop-vm
- The project's own: `scripts/vm/README.md`, `scripts/vm/seed/user-data.template`,
  `scripts/vm/RefuteVm/RefuteVm.Core.ps1`, [operations-roadmap.md](operations-roadmap.md),
  [../wp6-acceptance.md](../wp6-acceptance.md), [../../../plans/v0.3-plan.md](../../../plans/v0.3-plan.md)
  sections 6.1 and 7.
