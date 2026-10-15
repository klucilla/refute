# Refute VM scripts (WP6, phase 1)

These scripts build the Hyper-V VM in which third-party paper code will run
([plan section 7.1](../../docs/plans/v0.3-plan.md),
[wp6-acceptance.md](../../docs/validation/v0.3/wp6-acceptance.md)). **Building the VM
does not validate its isolation**: no paper code runs until every WP6 acceptance test
passes. In phase 1 the VM has no network.

**Not validated in operation yet.** The JEA endpoint and the scripts are tested only
with synthetic inputs, without Windows administrator rights and without Hyper-V
(tests/test_vm_scripts.py). Nothing here has been run on the machine: the
registration, the endpoint's restrictions (NoLanguage, the virtual account's groups,
the loopback-only WinRM, the transcripts) and every Hyper-V operation remain
unvalidated until they are tested on Windows and Hyper-V, with the evidence recorded
(wp6-acceptance.md, W6.4 to W6.6).

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
  mode: literal arguments only, no script block or expression. The module is pinned
  by name, version and GUID in the role capability. No parameter takes a path or a VM
  name: they come from
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
6. The maintainer, in Windows PowerShell started as Administrator:
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

Capacity control (plan section 7.5): `SetProcessorMaximum -Percent <1-100>`
(a percentage, not a number of CPUs), `SuspendVm`, `ResumeVm`, `SaveVm`, `StartVm`.

## What the registration changes

`Register-RefuteVmEndpoint.ps1` runs as Administrator. Without `-Apply` it prints the
list below for the actual machine (with the module's file hashes and the current WinRM
state) and its `PreviewSha256`. With `-Apply -PreviewSha256 <hash>`, only if the list
is unchanged and every target is absent (it never deletes or overwrites), in this
order:

1. copies the module to `%ProgramFiles%\WindowsPowerShell\Modules\RefuteVm\<version>`,
   checks the copied hashes, that only SYSTEM, Administrators, TrustedInstaller and
   CREATOR OWNER can write there, and that exactly one role capability named
   `RefuteVmOperator` exists on the module path (machine `PSModulePath`, Program Files
   and System32);
2. creates `C:\ProgramData\RefuteVm\{Transcripts,Log,State}` and the `C:\Hyper-V`
   tree, owner Administrators, explicit ACLs (Transcripts: SYSTEM and Administrators
   only; Log and State: also Hyper-V Administrators modify, Users read; `C:\Hyper-V`:
   SYSTEM and Administrators full control, Hyper-V Administrators modify);
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
7. writes the evidence (module hashes, role capability copies, endpoint settings,
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
