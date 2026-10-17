# Refute VM scripts (WP6, phase 1)

These scripts build the Hyper-V VM in which third-party paper code will run
([plan section 7.1](../../docs/plans/v0.3-plan.md),
[wp6-acceptance.md](../../docs/validation/v0.3/wp6-acceptance.md)). **Building the VM
does not validate its isolation**: no paper code runs until every WP6 acceptance test
passes. In phase 1 the VM has no network.

**Operation 1 validated on the host; every other operation not validated in operation yet.** What has been checked so far, and where:

- **Synthetic tests:** the scripts are tested with synthetic inputs, without Windows administrator rights and without Hyper-V (tests/test_vm_scripts.py).
- **CI integration:** a real JEA endpoint is registered on the GitHub Windows runner, and its sessions and module discovery are checked there (tests/test_vm_jea_integration.py). Where the runner has the Hyper-V management service, `SetHostPaths` also runs for real through it, under each version of the `C:\Hyper-V` ACL; the runner is Windows Server, not the maintainer's host.
  - **The test's remoting is wider than the real installation's.** On the runner the test runs `Enable-PSRemoting -Force -SkipNetworkProfileCheck`, which configures a listener on every address and a firewall exception, while the real installation keeps WinRM on loopback only, behind a block rule. That is acceptable only because the runner is discarded after the job; whether the runner was reachable from outside during the job was not measured. **The CI does not validate the network isolation of the real installation.**
  - **The CI builds the ACLs itself** and checks the applier's preview only: it does not run a complete apply of `Set-RefuteVmTreeAcl.ps1`, nor the writing of its protected evidence.
- **The maintainer's machine:**
  - the WinRM listener removal and the endpoint registration were run once, from `main` at `627842d`, with a first read-only check from the operator account. On 2026-10-16 the maintainer then:
    - repaired the installed module by hand: copied it to `RefuteVm\`, with no version subfolder, and removed `RefuteVm\0.1.0` (sections 5 and 6 of the record);
    - replaced the installed `RefuteVmOperator.psrc` with the one of `main` at `46fe0c2` (H.5). The session then opened from the operator account, ran as a virtual account and showed exactly the ten visible commands (section 7).
  - On 2026-10-16 the maintainer reinstalled the files changed by #118 (the role capability and two module files) from `main` at `57812ca`, with the hashes checked before and after, the same ACL and 6 files. The session then opened from the operator account with exactly the ten visible commands, and `Invoke-RefuteVm.ps1 -Status` completed: the configuration loaded, the six module hashes equal to `57812ca`, no VM, no base disk and no imported media (section 8 of the record).
  - The record is [jea-registration.md](../../docs/validation/v0.3/wp6-results/jea-registration.md).
  - the endpoint's restrictions in operation (NoLanguage, the virtual account's groups, the loopback-only WinRM, the transcripts) and every other Hyper-V operation remain unvalidated until they are tested on Windows and Hyper-V, with the evidence recorded (wp6-acceptance.md, W6.4 to W6.6).
  - **Operation 1, `SetHostPaths`, validated on the host on 2026-10-16:** tried twice under the first version of the `C:\Hyper-V` ACL, it failed with access denied, with no change (section 9 of the record). After the maintainer applied version 2 with `Set-RefuteVmTreeAcl.ps1`, it was done through the endpoint with the same plan, and the post-check of the tree gave the same result before and after the paths were adopted (section 10). Every other operation is not validated yet.

## Who can do what

- The maintainer's account is **not** a member of Hyper-V Administrators.
- Hyper-V operations go only through a local **JEA endpoint**, `RefuteVm`
  (Just Enough Administration). It runs each session as a temporary virtual account
  that is a member of Hyper-V Administrators only (not of Administrators), and it
  exposes two functions of the `RefuteVm` module: `Get-RefuteVmStatus` (read only)
  and `Invoke-RefuteVmOperation` (one administrative action per call), besides the
  default helper commands that a `RestrictedRemoteServer` session keeps
  (`Clear-Host`, `Exit-PSSession`, `Get-Command`, `Get-FormatData`, `Get-Help`,
  `Measure-Object`, `Out-Default`, `Select-Object`). The session is in NoLanguage
  mode: literal arguments only, no script block or expression. The role capability
  imports the module by the absolute path of its installed manifest,
  `C:\Program Files\WindowsPowerShell\Modules\RefuteVm\RefuteVm.psd1`, which pins that
  copy in a folder only administrators can write. It names no version and no GUID: with
  them PowerShell resolves the module by calling `Get-Module` inside the restricted
  session, which has no `Get-Module`, and the session cannot open (observed on
  2026-10-16).
  - **Two more imports, before the module.** The session holds the core cmdlets but not the functions of `Microsoft.PowerShell.Utility` (`Import-PowerShellDataFile`, `Get-FileHash`) nor the Hyper-V cmdlets, which the module's functions call ("`Import-PowerShellDataFile` is not recognized", observed on 2026-10-16). So the role capability also imports, each by the absolute path of its manifest in System32 (no name is resolved through the module path), `Microsoft.PowerShell.Utility` in `$PSHOME` (by name its functions do not come) and `Hyper-V` in `Hyper-V\2.0.0.0`.
  - **What the connecting account sees.** The commands these imports bring are private: the module's functions call them, but the connecting account does not see them. A CI test on a real endpoint checks the visible list, and another checks that every command the module calls exists in such a session.

  No parameter takes a path or a VM name: they come from
  `RefuteVm.Config.psd1`, installed with the module under `%ProgramFiles%`, where only
  administrators can write.
- Claude Code calls the endpoint through `Invoke-RefuteVm.ps1`; every call is a
  separate command on the maintainer's permission screen. Each operation runs twice:
  first with `-Simulate` (the plan and its `PlanSha256`; the managed state does not
  change), then with `-PlanSha256 <hash>`, which refuses if the plan is no longer the
  same. The plan holds the observed preconditions (host settings, files, the recorded
  state and the whole record of the target VM), so a change to any of them changes the
  hash. A real call holds an exclusive lock from its observation to its final check:
  one operation at a time, and a second session is refused. The endpoint does not
  require that a simulation was logged before a real call; the approval of the two
  commands on the permission screen is what binds them.
- **Limit.** The endpoint limits what can be done; it does not prove who approved a
  call. Any process that runs as the operator account can call it.
- The maintainer runs, as Administrator, the registration of the endpoint and any
  other step that needs administrator rights.

Sources (retrieved 2026-10-15): JEA session configurations,
https://learn.microsoft.com/en-us/powershell/scripting/security/remoting/jea/session-configurations;
registration (which restarts WinRM),
https://learn.microsoft.com/en-us/powershell/scripting/security/remoting/jea/register-jea;
Hyper-V Administrators ("complete and unrestricted access to all the features in
Hyper-V"),
https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/manage/understand-security-groups.

## Files

| File | Run by | Purpose |
|---|---|---|
| `RefuteVm/` | the endpoint | module: `RefuteVm.Core.ps1` (pure logic: configuration checks, plans, plan hash), `RefuteVm.HyperV.ps1` (observed state and the one mutation), `RefuteVm.psm1`, `RefuteVm.Config.psd1`, `RoleCapabilities/RefuteVmOperator.psrc` |
| `Register-RefuteVmEndpoint.ps1` | the maintainer, as Administrator | registers the endpoint; without `-Apply`, only shows what would change |
| `Remove-RefuteWinRmListener.ps1` | the maintainer, as Administrator | removes the WinRM listener `*+HTTP`, with a `.reg` backup in `C:\ProgramData\RefuteVm-backup`, with WinRM stopped; without `-Apply`, only shows the listener keys and what would change |
| `Set-RefuteVmTreeAcl.ps1` | the maintainer, as Administrator | replaces the ACL of `C:\Hyper-V` set by the registration of 2026-10-15 with version 2 (after the failure of SetHostPaths, [jea-registration.md](../../docs/validation/v0.3/wp6-results/jea-registration.md) section 9); without `-Apply`, only shows the state of the tree and of the evidence folders and the ACL it would set; the evidence goes to a new file in `C:\ProgramData\RefuteVm\Log` that only SYSTEM and Administrators can change |
| `Invoke-RefuteVm.ps1` | Claude Code (operator account) | calls the endpoint |
| `Get-RefuteMedia.ps1` | operator account, after approval | downloads and verifies the Ubuntu ISO |
| `New-RefuteSeedIso.ps1`, `seed/` | operator account | builds the CIDATA seed ISO (autoinstall) |

Data written by the endpoint, outside the project:
`C:\ProgramData\RefuteVm\Log\operations.jsonl` (one JSON line per simulation,
intent, refusal and result), `C:\ProgramData\RefuteVm\State\vm.json` (the VMId
recorded at creation and the seed ISO hash), and the JEA transcripts in
`C:\ProgramData\RefuteVm\Transcripts` (written by Local System, readable by
administrators only). Evidence copied to `docs/validation/v0.3/wp6-results/` holds no
user name, host name or address.

## Order of the steps

1. Review of this pull request.
2. SSH key of the VM, used only for it (Windows OpenSSH):
   `ssh-keygen -t ed25519 -C refute-vm -f C:\Projetos\refute\.cache\vm\ssh\refute_vm_ed25519`.
3. `Get-RefuteMedia.ps1` (preview), then `-Apply` after the maintainer approves the
   download (2.7 GB from releases.ubuntu.com).
4. A reviewed change sets `InstallIsoSha256` in `RefuteVm.Config.psd1`.
5. `New-RefuteSeedIso.ps1`; it prints the seed ISO's SHA-256.
5a. Only if WinRM has a listener on every address (`*+HTTP`; the registration refuses
   any listener that is not HTTP on loopback): the maintainer decided on 2026-10-15 to
   remove it with `Remove-RefuteWinRmListener.ps1`, started like the registration below
   (preview, the maintainer's OK, then `-Apply -PreviewSha256 <hash>`). The WinRM service
   must be stopped; the script never starts or stops it.
6. The maintainer, in Windows PowerShell started as Administrator, starts a new
   `powershell.exe -NoProfile` whose environment holds `PSModuleAnalysisCachePath=nul`
   (set in the parent shell first: only a value present when PowerShell starts disables
   the module analysis cache, and the script refuses to run without it), then runs
   `scripts\vm\Register-RefuteVmEndpoint.ps1 -OperatorAccount <COMPUTERNAME>\<account>`
   (preview; it prints a `PreviewSha256`), then the same with
   `-Apply -PreviewSha256 <hash>`, which refuses if the machine changed since the
   preview.
7. `Invoke-RefuteVm.ps1 -Status`, then each operation, simulated and then run:
   `SetHostPaths`, `DisableEnhancedSessionHost`, `CreateBaseDisk`, `CreateVm`,
   `SetMemory`, `SetProcessor`, `SetSecureBoot`, `DisableCheckpoints`,
   `DisconnectNetwork`, `DisableGuestServiceInterface -ServiceGuid <from -Status>`,
   `AttachBaseDisk`, `ImportInstallIso -MediaSha256 <hash>`,
   `ImportSeedIso -MediaSha256 <hash>`, `AttachInstallMedia`,
   `SetBootFromInstallMedia`, `StartVm`.
8. The maintainer opens the VM's console (Hyper-V Manager or `vmconnect`, as
   Administrator, since the maintainer's account has no Hyper-V rights) and answers
   "Continue with autoinstall?". The installer powers the VM off when it ends.
9. `DetachInstallMedia`, then `StartVm`. Secure Boot is never turned off without the
   maintainer's decision; no operation can do it.

### Install media after the installation

The downloaded ISO (`C:\Projetos\refute\.cache\vm\media\ubuntu-26.04.1-live-server-amd64.iso`,
2,927,861,760 bytes) is regenerable. After the VM is installed and the install media are
detached (step 9), it is deleted from the project folder by its literal path. What is
kept:

- its SHA-256, in `RefuteVm.Config.psd1`;
- the verification evidence: `media-verification.json`, copied to
  `docs/validation/v0.3/wp6-results/`;
- `SHA256SUMS` and `SHA256SUMS.gpg`, kept with the WP6 records under the project's
  cleanup rule.

The copy that the endpoint made in `C:\Hyper-V\refute-vm\media` is outside the project.
Removing it is the maintainer's decision (see "Reversal").

Capacity control (plan section 7.5): `SetProcessorMaximum -Percent <1-100>`
(a percentage, not a number of CPUs), `SuspendVm`, `ResumeVm`, `SaveVm`, `StartVm`.

## What the registration changes

`Register-RefuteVmEndpoint.ps1` runs as Administrator. Without `-Apply` it prints the
list below for the actual machine (with the module's file hashes and the current WinRM
state) and its `PreviewSha256`. With `-Apply -PreviewSha256 <hash>`, only if the list
is unchanged and every target is absent (it never deletes or overwrites), in this
order:

1. copies the module to `%ProgramFiles%\WindowsPowerShell\Modules\RefuteVm`, with **no
   version subfolder**: JEA looks for `<module path>\<module>\RoleCapabilities\<name>.psrc`
   only, one folder deep, and a copy in `RefuteVm\<version>` is never found (diagnosed
   by the maintainer on 2026-10-16; `GetRoleCapabilityPath` in
   https://github.com/PowerShell/PowerShell/blob/master/src/System.Management.Automation/engine/remoting/fanin/InitialSessionStateProvider.cs,
   accessed 2026-10-16). It checks the copied hashes, that only SYSTEM, Administrators,
   TrustedInstaller and CREATOR OWNER can write there, that a search with the structure
   of JEA's finds exactly one role capability,
   `RefuteVm\RoleCapabilities\RefuteVmOperator.psrc`, that no other copy exists (none in
   a version subfolder), and, already in the preview, that the role capability imports
   exactly, in this order, the `Microsoft.PowerShell.Utility` manifest in `$PSHOME`, the
   Hyper-V manifest `Hyper-V\2.0.0.0\Hyper-V.psd1` in System32 (it must be the one the host
   has) and `C:\Program Files\WindowsPowerShell\Modules\RefuteVm\RefuteVm.psd1`, and
   makes visible only the two functions; in the folders these imports load from (the two
   module folders in System32 and the Hyper-V cmdlets assembly in the global assembly
   cache), every file and folder and every ancestor gets the checks of the discovery set
   below (owners, writers with generic rights mapped, no reparse point). The
   search covers these module roots (`Get-RefuteRegistrationModuleRoots` in
   `RefuteRegistration.Core.ps1`): the machine and process `PSModulePath`, Program Files,
   System32, `$PSHOME\Modules`, and the Default profile's
   `Documents\WindowsPowerShell\Modules`. A virtual account's own user module folder
   does not exist at registration: its profile is created, from the Default profile,
   when its session starts. **Limit:** what the registration checks is this set on the
   machine at that moment. A CI test on a real endpoint (tests/test_vm_jea_integration.py)
   calls the same function and shows, for the GitHub runner only, that every existing
   root a JEA session reports is in the set or holds no role capability; it does not
   validate the maintainer's host. The registration also checks the **effective
   discovery set** of the session (`Get-RefuteJeaDiscoveryRoots`): the machine
   `PSModulePath`, Program Files, `$PSHOME\Modules`, and the virtual account's user
   entry, which is relative (`WindowsPowerShell\Modules`, its Documents path being
   empty) and resolves against the session's current folder, `%SystemRoot%\system32`
   (as the CI test observed on the runner). The checks on that set:
   - **Writers:** in every folder of the set, in every module folder under it, and in every `RoleCapabilities` folder and `.psrc` file, only SYSTEM, Administrators and TrustedInstaller may write. CREATOR OWNER is accepted only as an inherit-only entry. The generic rights `GENERIC_ALL` and `GENERIC_WRITE` count as the specific rights they grant, so an inherit-only entry that keeps them unmapped is caught too.
   - **Owners and links:** every one of these items has one of those three owners and is not a reparse point.
   - **Ancestors:** no ancestor, up to the volume root, can be deleted, have its permissions changed or be taken over by another account.
   - **A folder of the set that does not exist:** the same checks apply to its nearest existing ancestor, which decides who can create it, and the ancestors above that one are checked as ancestors.

   The preview and the apply both refuse otherwise. **Limit:** the set is computed from
   the machine's state at that moment and from the current folder observed on the CI
   runner;
2. creates `C:\ProgramData\RefuteVm\{Transcripts,Log,State}` and the `C:\Hyper-V`
   tree, owner Administrators, explicit ACLs (Transcripts: SYSTEM and Administrators
   only; Log and State: also Hyper-V Administrators modify, Users read; `C:\Hyper-V`:
   version 2 of `Get-RefuteVmTreeAclSpec`, that is SYSTEM and Administrators full
   control, Hyper-V Administrators modify and change permissions, and NT VIRTUAL
   MACHINE\Virtual Machines as on the default folder of Windows: list and create in
   folders, read files. The Hyper-V management service changes permissions with the
   identity of its caller, so modify alone made SetHostPaths fail; a host registered
   before this change gets version 2 with `Set-RefuteVmTreeAcl.ps1`);
3. adds the firewall rule `Refute-JEA-Block-WinRM-Inbound` (inbound TCP 5985 and 5986
   blocked from every address except loopback, on every profile) **before WinRM is
   started**, and checks that it is in the active policy, that every profile is
   enabled and that no enabled inbound rule overrides block rules;
4. reads the WinRM listeners from the registry (the service may be stopped) and stops
   if any is not HTTP on `127.0.0.1` or `::1`;
5. sets WinRM to start automatically, starts it, checks the listeners again through
   WinRM, adds the loopback listeners that are missing, and checks that every listener
   is HTTP, port 5985, enabled, on loopback;
6. writes `C:\ProgramData\RefuteVm\RefuteVm.pssc` and registers the endpoint with
   `Register-PSSessionConfiguration -AccessMode Local` (this restarts WinRM), then
   checks its virtual account, group and permission. JEA grants each virtual account
   the "Log on as a service" right for the length of its session;
7. writes the evidence (module hashes, role capability copies and the one JEA finds, endpoint settings,
   listeners, listening sockets, firewall profiles and rule, folder ACLs) to
   `C:\ProgramData\RefuteVm\Log\registration-evidence.json`.

**If it stops in the middle** (a check fails), it prints what was already done; the
parts already made stay as they are, and the endpoint is registered only by the last
step. The maintainer decides what to do; the script never removes anything, and a new
run refuses while any target exists.

## Reversal

The registration creates only the items listed above, all named in the evidence file.
Reverting any of them (the endpoint registration, the firewall rule, the loopback
listeners, the installed module, the data folders, the `C:\Hyper-V` tree and the VM) is
the maintainer's decision and action, as Administrator; no script of the project
removes them.
