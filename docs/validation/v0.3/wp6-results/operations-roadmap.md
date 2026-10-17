# WP6: roadmap of operations 3 to 16 (prepared 2026-10-17, nothing run)

Preparation for the next VM operations through the JEA endpoint
([scripts/vm/README.md](../../../../scripts/vm/README.md), step 7;
[jea-registration.md](jea-registration.md)). **Nothing here was run:** no VM operation,
no endpoint session, no Administrator step. The maintainer runs each operation, one at a
time: first `-Simulate`, then the real call with the `PlanSha256` the simulation printed,
after checking the plan. Everything about the ACL of `C:\Hyper-V` in this document is a
hypothesis, not tested (section 9.2 of the record): each operation shows it when it runs.

The expected changes are read from `scripts/vm/RefuteVm/RefuteVm.Core.ps1` (`New-RefuteVmPlan`)
and the actions from `RefuteVm.HyperV.ps1` (`Invoke-RefuteVmMutation`), with the
configuration of a base disk of 100 GiB (`BaseDiskSizeBytes` 107374182400,
`ConfigSha256` `e41ee75a41e63b2314efca5d0c62a96b814564293218307d36d114a0f71e0f6e`). That
configuration is in pull request #134, **not merged** when this roadmap was written: its
estimate does not establish the margin of every case, and the size waits for the
maintainer. If another size is chosen, operations 3 and 11 and the `ConfigSha256` change
accordingly; nothing else here depends on the size.

## 1. Before operation 3

1. The installed `RefuteVm.Config.psd1` is the version with the chosen size (the update
   procedure is in pull request #134).
2. `-Status` shows that `ConfigSha256`, `BaseDiskSizeBytes` 107374182400, the two host
   paths in `C:\Hyper-V`, `EnableEnhancedSessionMode` false, no VM and no base disk.

Every command runs from the main folder, in a normal window (the operator account):

```
scripts\vm\Invoke-RefuteVm.ps1 -Status
scripts\vm\Invoke-RefuteVm.ps1 -Status -IncludeMedia
scripts\vm\Invoke-RefuteVm.ps1 -Operation <name> -Simulate
scripts\vm\Invoke-RefuteVm.ps1 -Operation <name> -PlanSha256 <the simulated hash>
```

`-IncludeMedia` adds the SHA-256 of the media in `MediaRoot` and `MediaSource`; without it
those fields are empty. The three media operations observe the media themselves.

## 2. Order

The order is the one of the README (step 7), which this roadmap follows: operations 9
and 10 are `DisconnectNetwork`, then `DisableGuestServiceInterface`. The operation table of
the code (`RefuteVm.Core.ps1`, `$script:RefuteVmOperationTable`) lists them the other way
round. Both need the VM off and neither depends on the other, so the order does not change
their plans.

## 3. Rules common to every operation

- **What the plan holds.** The plan holds the observed preconditions: the host, the files,
  the recorded state and, for an operation on the VM, the whole record of the VM. Any change
  between the simulation and the call changes the `PlanSha256`, and the call is refused:
  "the plan differs from the simulated one".
- **Refusals for an operation on the VM** (operations 5 to 11 and 14 to 16), from
  `Resolve-RefuteVmTarget`:
  - no VM named `refute-vm`, or more than one;
  - no recorded VMId, or a VMId different from the recorded one;
  - the VM stored outside `C:\Hyper-V\refute-vm`;
  - not generation 2;
  - a disk other than the base disk attached;
  - DVD media other than the two ISOs;
  - a network adapter connected to a switch (except for `DisconnectNetwork`);
  - the VM not in the state the operation needs.
- **Other common refusals:** an invalid configuration, and an argument the operation does
  not take or that is malformed.
- **Failures:** a junction or link on the paths (`Assert-RefuteNoReparsePoint`) makes the call
  fail (`Outcome` failed), not a refusal. So does an error of the Hyper-V cmdlet.
- **Reversal.** No endpoint operation undoes operations 3 to 14, except
  `DetachInstallMedia` (for 14 and 15) and `StopVm` (for 16). Undoing anything else is a
  step of the maintainer, as Administrator, outside the endpoint, with a preview. It is
  listed per operation as a hint, not as a procedure.

## 4. The operations

### 3. CreateBaseDisk
- **Simulate:** `scripts\vm\Invoke-RefuteVm.ps1 -Operation CreateBaseDisk -Simulate`
- **Expected change:** `BaseDisk` from `absent` to `dynamic VHDX of 107374182400 bytes at C:\Hyper-V\Virtual Hard Disks\refute-vm-base.vhdx`.
- **Preconditions:** no file at that path; `ConfigSha256` `e41ee75a…`.
- **Refusal:** a file at the path that is not the configured disk (another format, type or size): "never overwritten". If the configured disk is already there, `AlreadyDone` true.
- **Action:** `New-VHD -Path <base> -SizeBytes 107374182400 -Dynamic`.
- **Then `-Status`:** `Files.BaseDisk` exists, `VHDX`, `Dynamic`, `SizeBytes` 107374182400.
- **Writes in `C:\Hyper-V`:** yes, a new file in `C:\Hyper-V\Virtual Hard Disks`. Hypothesis: the folder's inherited version 2 entries (Hyper-V Administrators modify) let it be created, and the file inherits them.
- **Reversal:** the maintainer deletes the file, as Administrator, while no VM uses it.

### 4. CreateVm
- **Simulate:** `scripts\vm\Invoke-RefuteVm.ps1 -Operation CreateVm -Simulate`
- **Expected change:** `VM` from `absent` to `generation 2, stored in C:\Hyper-V\refute-vm, no disk, network adapter not connected`.
- **Refusals:** a VM named `refute-vm` already exists; a VMId is already recorded.
- **Action:** `New-VM -Name refute-vm -Generation 2 -Path C:\Hyper-V\refute-vm -MemoryStartupBytes 51539607552 -NoVHD`. The new VMId is written to `C:\ProgramData\RefuteVm\State\vm.json`.
- **Then `-Status`:** one VM `refute-vm`, `Off`, generation 2, `Path` `C:\Hyper-V\refute-vm`, no hard disk, adapters with no switch; the recorded VMId equals the VM's.
- **Writes in `C:\Hyper-V`:** yes, the VM's configuration files under `C:\Hyper-V\refute-vm`. Hypothesis: the service also gives the VM's own account access to its files, and it needs the right to change permissions there, which version 2 gives (as for SetHostPaths). Section 9 saw the service add broader entries when it adopted a folder without version 2.
- **Reversal:** the maintainer removes the VM and the state file, as Administrator.

### 5. SetMemory
- **Simulate:** `scripts\vm\Invoke-RefuteVm.ps1 -Operation SetMemory -Simulate`
- **Expected change**, for each value that differs:
  - `Memory.DynamicMemoryEnabled` to false;
  - `Memory.StartupBytes` to 51539607552 (48 GiB). `New-VM` already set the startup memory, so only dynamic memory may remain.
- **Needs:** the VM `Off`.
- **Action:** `Set-VMMemory -DynamicMemoryEnabled $false -StartupBytes 51539607552`.
- **Then `-Status`:** `DynamicMemoryEnabled` false, `MemoryStartup` 51539607552.
- **Writes in `C:\Hyper-V`:** the VM's configuration, through the service. No new ACL question is expected.
- **Reversal:** the maintainer sets the previous values (the `Before` of the plan).

### 6. SetProcessor
- **Simulate:** `scripts\vm\Invoke-RefuteVm.ps1 -Operation SetProcessor -Simulate`
- **Expected change:** `Processor.Count` from the value `New-VM` set to 24.
- **Needs:** the VM `Off`.
- **Then `-Status`:** `ProcessorCount` 24.
- **Writes in `C:\Hyper-V`:** the configuration only.
- **Reversal:** the previous count, by the maintainer.

### 7. SetSecureBoot
- **Simulate:** `scripts\vm\Invoke-RefuteVm.ps1 -Operation SetSecureBoot -Simulate`
- **Expected change**, for each value that differs:
  - `Firmware.SecureBoot` to `On`;
  - `Firmware.SecureBootTemplate` to `MicrosoftUEFICertificateAuthority`, the template that boots Linux.
- **Needs:** the VM `Off`.
- **Then `-Status`:** `SecureBoot` `On`, `SecureBootTemplate` `MicrosoftUEFICertificateAuthority`.
- **Writes in `C:\Hyper-V`:** the configuration only.
- **Reversal:** the previous template, by the maintainer. Secure Boot is never turned off without the maintainer's decision.

### 8. DisableCheckpoints
- **Simulate:** `scripts\vm\Invoke-RefuteVm.ps1 -Operation DisableCheckpoints -Simulate`
- **Expected change:** `AutomaticCheckpointsEnabled` to false and `CheckpointType` to `Disabled`, for each that differs.
- **Needs:** the VM `Off`.
- **Then `-Status`:** `AutomaticCheckpointsEnabled` false, `CheckpointType` `Disabled`.
- **Writes in `C:\Hyper-V`:** the configuration only.
- **Reversal:** the previous values, by the maintainer.

### 9. DisconnectNetwork
- **Simulate:** `scripts\vm\Invoke-RefuteVm.ps1 -Operation DisconnectNetwork -Simulate`
- **Expected change:** none if `New-VM` left the adapter unconnected (it was called with no switch), so `AlreadyDone` true. Otherwise each connected adapter goes to no switch.
- **Needs:** the VM `Off`. This is the only operation on the VM that accepts a connected adapter.
- **Then `-Status`:** every adapter with an empty `SwitchName`.
- **Writes in `C:\Hyper-V`:** at most the configuration.
- **Reversal:** none. Connecting the VM is outside phase 1.

### 10. DisableGuestServiceInterface
- **First:** read the `Id` of the Guest Service Interface in `-Status` (`Observed.Vms[0].IntegrationServices`). The service's name depends on the Windows language, and its GUID is the last segment of the `Id`, in lowercase.
- **Simulate:** `scripts\vm\Invoke-RefuteVm.ps1 -Operation DisableGuestServiceInterface -ServiceGuid <guid> -Simulate`
- **Expected change:** `IntegrationService.<guid> (<name as the host reports it>)` from true to false. The plan shows the name, so the approval shows which service the GUID designates. If the service is already off, `AlreadyDone` true.
- **Refusals:**
  - `ServiceGuid` not a lowercase GUID;
  - not exactly one integration service whose `Id` ends with it.
- **Needs:** the VM `Off`.
- **Then `-Status`:** that service `Enabled` false.
- **Writes in `C:\Hyper-V`:** the configuration only.
- **Reversal:** the maintainer enables the service again.

### 11. AttachBaseDisk
- **Simulate:** `scripts\vm\Invoke-RefuteVm.ps1 -Operation AttachBaseDisk -Simulate`
- **Expected change:** `HardDisk` from `none` to `C:\Hyper-V\Virtual Hard Disks\refute-vm-base.vhdx`.
- **Refusals:**
  - the base disk does not exist ("CreateBaseDisk first");
  - it is not the configured disk (format, type or size; after a resize the configuration must change too).
- **Needs:** the VM `Off`.
- **Action:** `Add-VMHardDiskDrive -Path <base>`.
- **Then `-Status`:** `HardDisks` holds the base disk only.
- **Writes in `C:\Hyper-V`:** the configuration. Hypothesis: the service gives the VM's account access to the disk file by adding an entry to its ACL, which needs the right to change permissions on the file; version 2 gives it to Hyper-V Administrators, inherited by files. This was named an open question in section 9.2.
- **Reversal:** the maintainer removes the drive.

### 12. ImportInstallIso
- **Simulate:** `scripts\vm\Invoke-RefuteVm.ps1 -Operation ImportInstallIso -MediaSha256 cc8a95cde20f6ced61a322420de00f10cc3c90ced545daa46cb9c1a117f1d927 -Simulate`
- **Expected change:** `Media.InstallIso` from `absent` to `cc8a95…d927`.
- **Refusals:**
  - `InstallIsoSha256` not configured;
  - `MediaSha256` different from it;
  - a different install ISO already in `MediaRoot` (never overwritten);
  - the ISO in `MediaSource` missing or with another SHA-256.
  
  If the same ISO is already in `MediaRoot`, `AlreadyDone` true.
- **Needs:** no VM state.
- **Action:** the endpoint's virtual account copies `C:\Projetos\refute\.cache\vm\media\ubuntu-26.04.1-live-server-amd64.iso` to `C:\Hyper-V\refute-vm\media\`, hashing the bytes as it copies; a copy that does not match stays as `.partial`.
- **Then `-Status -IncludeMedia`:** `InstallIsoMediaSha256` `cc8a95…d927`.
- **Writes in `C:\Hyper-V`:** yes, a 2.9 GB file in `C:\Hyper-V\refute-vm\media`, written by the virtual account itself (Hyper-V Administrators modify, inherited). It also reads the project folder; see section 6.
- **Reversal:** the maintainer deletes the copy.

### 13. ImportSeedIso
- **Simulate:** `scripts\vm\Invoke-RefuteVm.ps1 -Operation ImportSeedIso -MediaSha256 476754b824ba267c14993fb864b798bd1140eeac8cd69ea97ab38645743160f9 -Simulate`
- **Expected change:** `Media.SeedIso` from `absent` to `476754b8…60f9`. The real call also records that hash in `vm.json`.
- **Refusals:**
  - a different seed ISO already in `MediaRoot`;
  - the seed in `MediaSource` missing or with another SHA-256;
  - the seed in `MediaRoot` without its hash in the state ("the maintainer inspects").
- **Note:** nothing in the configuration fixes the seed's hash, so the approval of this plan is what binds it. Section 5 says what is known about it.
- **Then `-Status -IncludeMedia`:** `SeedIsoMediaSha256` and `RecordedSeedIsoSha256` both `476754b8…60f9`.
- **Writes in `C:\Hyper-V`:** yes, the seed in `C:\Hyper-V\refute-vm\media`, and the state file in `C:\ProgramData\RefuteVm\State`.
- **Reversal:** the maintainer deletes the copy and the seed hash from the state.

### 14. AttachInstallMedia
- **Simulate:** `scripts\vm\Invoke-RefuteVm.ps1 -Operation AttachInstallMedia -Simulate`
- **Expected change:** `DvdDrive` from `none` to each of the two copies in `C:\Hyper-V\refute-vm\media` (the install ISO, then the seed), for each not yet attached.
- **Refusals:**
  - the install ISO in `MediaRoot` missing or not the configured one;
  - the seed in `MediaRoot` missing or not the imported one.
- **Needs:** the VM `Off`.
- **Then `-Status`:** `DvdDrives` holds the two paths.
- **Writes in `C:\Hyper-V`:** the configuration. Hypothesis: as for the disk, the service gives the VM's account read access to each ISO by changing its ACL.
- **Reversal:** `DetachInstallMedia`, an endpoint operation. It needs the base disk attached, removes every DVD drive and sets the first boot device to the base disk.

### 15. SetBootFromInstallMedia
- **Simulate:** `scripts\vm\Invoke-RefuteVm.ps1 -Operation SetBootFromInstallMedia -Simulate`
- **Expected change:** `Firmware.FirstBootDevice` from its current value to the install ISO's path.
- **Refusals:**
  - the install ISO is not attached ("AttachInstallMedia first");
  - Secure Boot is off ("SetSecureBoot first").
- **Needs:** the VM `Off`.
- **Then `-Status`:** `FirstBootDevice` the install ISO.
- **Writes in `C:\Hyper-V`:** the configuration only.
- **Reversal:** `DetachInstallMedia`.

### 16. StartVm
- **Simulate:** `scripts\vm\Invoke-RefuteVm.ps1 -Operation StartVm -Simulate`
- **Expected change:** `State` from `Off` to `Running`.
- **Refusal:** Secure Boot not on with the configured template.
- **Needs:** the VM `Off` or `Saved`.
- **Then `-Status`:** `State` `Running`. Then the maintainer opens the console, as Administrator, and answers "Continue with autoinstall?" (README, step 8); the installer powers the VM off at the end.
- **Writes in `C:\Hyper-V`:** yes. The VM's worker process, running as the VM's own account, opens the disk for writing and the ISOs for reading, and creates its runtime files in the VM's folder.
  - Hypothesis: the entries the service added at the attach operations, and the Virtual Machines group's create rights of version 2 on folders, are what this needs.
  - Not a disk question, but the start reserves 48 GiB of static memory on a host with 63.9 GB (plan 7.1), so it can fail when not enough memory is free.
- **Reversal:** `StopVm`, an endpoint operation: a clean shutdown through the guest, never forced.

## 5. The media (checked read only, 2026-10-17)

| File in `C:\Projetos\refute\.cache\vm\media` | Bytes | SHA-256 | Checked against |
|---|---|---|---|
| `ubuntu-26.04.1-live-server-amd64.iso` | 2,927,861,760 | `cc8a95cde20f6ced61a322420de00f10cc3c90ced545daa46cb9c1a117f1d927` | `InstallIsoSha256` of the configuration: **equal** |
| `refute-vm-seed.iso` | 55,296 | `476754b824ba267c14993fb864b798bd1140eeac8cd69ea97ab38645743160f9` | no record in the repository (see below) |

- **The install ISO is present and equal to the configuration.** The configuration's value was itself verified against `SHA256SUMS` and its signature on 2026-10-15 (`media-verification.json`).
- **The seed is present, but its hash is recorded nowhere in the repository.** `New-RefuteSeedIso.ps1` printed it on 2026-10-15. The ISO's content folder next to it, `refute-vm-seed.iso.content`, holds a `user-data` equal to `scripts/vm/seed/user-data.template` with the VM's SSH public key in place of `{{SSH_PUBLIC_KEY}}`, and a `meta-data` with `instance-id: refute-vm-1` and `local-hostname: refute-vm`. That folder is what the script wrote the ISO from, not a read of the ISO.
- **Nothing is missing.** If a medium had to be made again, `Get-RefuteMedia.ps1` downloads and verifies the ISO, and `New-RefuteSeedIso.ps1` builds the seed (README, steps 3 and 5). Neither was run.

## 6. Can the endpoint's virtual account read the media in the project folder?

The question of section 9.2: `ImportInstallIso` and `ImportSeedIso` read the media in
`C:\Projetos\refute\.cache\vm\media` as the endpoint's virtual account. That account is a
member of Hyper-V Administrators only, not of Administrators.

**What the ACLs show** (`Get-Acl`, read only, on 2026-10-17; no security descriptor or
account SID is published):

| Path | Entries |
|---|---|
| `C:\Projetos`, `C:\Projetos\refute`, `.cache`, `.cache\vm`, `.cache\vm\media` | inherited, not protected: Administrators and SYSTEM full control; **Users read and execute** (folders and files); **Authenticated Users modify** (the folder itself) and an inherit-only entry for its children; owner the maintainer's account |
| the two ISOs | inherited: Administrators and SYSTEM full control, **Users read and execute**, Authenticated Users modify |

No path is a junction or link.

**Conclusion: yes, very likely, though not tested.**
- **The ACL side is certain.** Both files can be read by any account in the token group
  Users or Authenticated Users, and every folder on the path can be traversed and read by
  Users.
- **That the virtual account holds those groups is shown indirectly.**
  - Authenticated Users: "Any user who accesses the system through a sign-in process has
    the Authenticated Users identity"
    (https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/manage/understand-special-identities-groups,
    read 2026-10-17).
  - Users: the installed module and its files grant read access only to TrustedInstaller,
    SYSTEM, Administrators, Users and the application package groups (sections 3.4 and 7.1
    of the record). Since 2026-10-16 the virtual account loads that module, and `-Status`
    completes (section 8). It is not TrustedInstaller, SYSTEM or an Administrator, and the
    application package entries apply only to app containers, so its token matches
    Users.
- **The direct test is the operation itself.** `ImportInstallIso` is simulated first; its
  plan already reads both hashes in `MediaSource` (`Files.InstallIsoSourceSha256`). If the
  account could not read the file, either the field would come back empty and the plan
  would refuse ("missing or has another SHA-256"), or the simulation would stop with the
  read error; in both cases nothing is copied.

**No correction is proposed.** If that simulation refused for this reason, the smallest
correction would be a read-only entry for Hyper-V Administrators on `.cache\vm\media`, set
by the maintainer. It is prepared only if needed.

**A note, not a change:** the same ACL lets every authenticated account modify the
media in the project folder. That does not reach the VM, because the endpoint copies a medium
only when the bytes it reads have the approved SHA-256 (`Copy-RefuteVerifiedFile`).

## 7. The commands of operation 3, in plain text

After the update of the installed configuration and its `-Status` check:

```
scripts\vm\Invoke-RefuteVm.ps1 -Status
scripts\vm\Invoke-RefuteVm.ps1 -Operation CreateBaseDisk -Simulate
scripts\vm\Invoke-RefuteVm.ps1 -Operation CreateBaseDisk -PlanSha256 <the PlanSha256 of the simulation>
scripts\vm\Invoke-RefuteVm.ps1 -Status
scripts\vm\Invoke-RefuteVm.ps1 -Operation CreateBaseDisk -Simulate
```

- **Check in the simulation:** `ConfigSha256` `e41ee75a…`, one change to a dynamic VHDX of
  107374182400 bytes, and `Refusal` null.
- **The last simulation** must give `AlreadyDone` true.
