# WP6 evidence: JEA endpoint registration and first validation (W6.4)

Record of the registration of the local JEA endpoint `RefuteVm`
([scripts/vm/README.md](../../../../scripts/vm/README.md),
[wp6-acceptance.md](../wp6-acceptance.md), W6.4) and of the first read-only validation
from the operator account. Technical fields only: no user name, host name,
account-specific SID or address of the machine. What remains is generic: well-known
SIDs (named in section 3.4), the loopback addresses, the wildcard socket, and the
address ranges of the firewall rule, which express the loopback exception documented
in the README.

## 1. Source of the scripts

- Exported from `main` at commit `627842d239106d8800583025c33d28a2d55ea5d6`
  (16 files under `scripts/vm/`, each checked against its git blob).
- The maintainer copied them to a folder writable only by administrators, checked the
  16 SHA-256 hashes on the copy and also against an independent download from GitHub,
  and deleted that folder afterwards.

## 2. Removal of the WinRM listener `*+HTTP` (step 5a)

Run by the maintainer as Administrator on 2026-10-15 with
`Remove-RefuteWinRmListener.ps1`.

| Item | Value |
|---|---|
| PreviewSha256 applied | `0c98630287e9512da4c17b90337880f6661c6274f4d6912f86d5541c87387bc1` |
| Backup | `.reg` export in `C:\ProgramData\RefuteVm-backup` |
| Backup SHA-256 | `2d4f8ac8cd5e01ef27d63dd8bcbea9251a41d0026e65680adfc7b562f285a875` |
| Result | key `*+HTTP` removed; WinRM stopped at that moment |

## 3. Registration of the endpoint (step 6)

Run by the maintainer as Administrator on 2026-10-15 with
`Register-RefuteVmEndpoint.ps1`. PreviewSha256 applied:
`ecf96548dd2e9701db7de88b3c61dc98e08a9cb4057303197317036843cc5888`.

The fields below are extracted from `C:\ProgramData\RefuteVm\Log\registration-evidence.json`
(5600 bytes, SHA-256 `ff32581edf114b69dc0ea96d973de52e4b05b1feb2b5ee454af52cd3e74f2454`,
written 2026-10-15T23:54:10Z). The raw file is not copied, because it holds the account
name and the account SID.

### 3.1 Installed module

`C:\Program Files\WindowsPowerShell\Modules\RefuteVm\0.1.0`. The hashes are equal to
the blobs of commit `627842d`:

| File | SHA-256 |
|---|---|
| `RefuteVm.Config.psd1` | `2559b7348a98430f9f61ebd85f8dfcf456292fadc32e6c3ea608e8db872c6a1e` |
| `RefuteVm.Core.ps1` | `5b717a3355ec0919717524fe9937a37d544a75ae413ca49bb7397a18b409bf4e` |
| `RefuteVm.HyperV.ps1` | `316183ad1ce0aae0eb28c9e2dfa31fc83fa4819eaecc112540a08e332c4e6d0e` |
| `RefuteVm.psd1` | `fcbb3416bca125295d2c979567eb7c8cc07a173e0397da4967ed82c17c22d188` |
| `RefuteVm.psm1` | `19a9c777c9baac18e933663f8a1739eb62ddc05869f62c089c7e675f86d714d2` |
| `RoleCapabilities/RefuteVmOperator.psrc` | `1303b08422e7a875a94a6b094d1f2733685c3c4837989606086f51887c6f1b08` |

Role capability copies named `RefuteVmOperator` on the module path: exactly one, the
one above.

### 3.2 Endpoint

| Field | Value |
|---|---|
| Name | `RefuteVm` |
| SessionType | `RestrictedRemoteServer` |
| RunAsVirtualAccount | `True` |
| RunAsVirtualAccountGroups | Hyper-V Administrators only (the localized name of the built-in group) |
| Permission | `NT AUTHORITY\NETWORK` AccessDenied; the operator account AccessAllowed; no other entry |
| TranscriptDirectory | `C:\ProgramData\RefuteVm\Transcripts` |

### 3.3 WinRM and firewall

| Field | Value |
|---|---|
| WinRM service | `Running`, start type `Automatic` |
| Listeners | `IP:127.0.0.1` HTTP 5985 enabled; `IP:::1` HTTP 5985 enabled; no other |
| Listening sockets on 5985 | `:::5985` (see the note below) |
| Firewall profiles | Domain, Private and Public enabled |
| Rule `Refute-JEA-Block-WinRM-Inbound` | Enabled, Inbound, Block, profile Any, local ports 5985 and 5986, remote addresses `0.0.0.0-126.255.255.255`, `128.0.0.0-255.255.255.255`, `::`, `::2-ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff` (every address except 127.0.0.0/8 and `::1`) |

**Note on the socket `:::5985`** (the maintainer, 2026-10-15). HTTP.sys opens the port on
every address, but WinRM answers only on its loopback listeners, and the block rule
covers every other address on the three profiles. Nothing is changed for this; it is
recorded in the follow-ups issue (#59) only as a record.

This table records configuration: the wildcard socket, the listeners configured on
loopback and the block rule. Reachability from another machine was not measured.

### 3.4 Folder ACLs (DACL; owner `BA`, from the `O:` field, on every folder)

Aliases: SY = Local System, BA = Administrators, BU = Users, HA = Hyper-V
Administrators, CO = Creator Owner, AC = All Application Packages, S-1-15-2-2 = All
Restricted Application Packages, S-1-5-80-956008885-3418522649-1831038044-1853292631-2271478464
= TrustedInstaller. `0x1200a9` is read and execute (with synchronize); `0x1301bf` is
modify (with synchronize). `P` = the DACL is protected from inheritance from its parent;
the protected DACLs below hold no inherited (`ID`) entry. The group field of each
security descriptor is left out (it is the account SID).

| Folder | DACL |
|---|---|
| `C:\ProgramData\RefuteVm` | `PAI(A;OICI;FA;;;SY)(A;OICI;FA;;;BA)(A;;0x1200a9;;;BU)(A;;0x1200a9;;;HA)` |
| `C:\ProgramData\RefuteVm\Transcripts` | `PAI(A;OICI;FA;;;SY)(A;OICI;FA;;;BA)` |
| `C:\ProgramData\RefuteVm\Log` | `PAI(A;OICI;FA;;;SY)(A;OICI;FA;;;BA)(A;OICI;0x1200a9;;;BU)(A;OICI;0x1301bf;;;HA)` |
| `C:\ProgramData\RefuteVm\State` | `PAI(A;OICI;FA;;;SY)(A;OICI;FA;;;BA)(A;OICI;0x1200a9;;;BU)(A;OICI;0x1301bf;;;HA)` |
| `C:\Hyper-V` | `PAI(A;OICI;FA;;;SY)(A;OICI;FA;;;BA)(A;OICI;0x1301bf;;;HA)` |
| `C:\Hyper-V\Virtual Hard Disks`, `C:\Hyper-V\refute-vm`, `C:\Hyper-V\refute-vm\media` | inherited from `C:\Hyper-V` |
| module folder `...\RefuteVm\0.1.0` | `AI(A;ID;FA;;;TI)(A;CIIOID;GA;;;TI)(A;ID;FA;;;SY)(A;OICIIOID;GA;;;SY)(A;ID;FA;;;BA)(A;OICIIOID;GA;;;BA)(A;ID;0x1200a9;;;BU)(A;OICIIOID;GXGR;;;BU)(A;OICIIOID;GA;;;CO)(A;ID;0x1200a9;;;AC)(A;OICIIOID;GXGR;;;AC)(A;ID;0x1200a9;;;S-1-15-2-2)(A;OICIIOID;GXGR;;;S-1-15-2-2)`, where `TI` stands for the TrustedInstaller SID above; every entry is inherited from Program Files |

In the module folder only TrustedInstaller, SY and BA have write rights on the folder
itself; CO has full control only on the files and folders created inside it
(inherit-only, `IO`), as W6.4 and the README allow.

### 3.5 Checks done by the maintainer after the registration

WinRM `Running`/`Automatic`; listeners only on `127.0.0.1` and `::1`; the block rule
`True`/`Inbound`/`Block`; endpoint `RefuteVm` with `RunAsVirtualAccount` `True` and
`RestrictedRemoteServer`; network denied and only the operator account allowed.

## 4. First validation from the operator account (read-only)

Run by Claude Code under the operator account (not an administrator), on 2026-10-16
between 00:01 and 00:20 UTC. Nothing was changed.

| Step | Result |
|---|---|
| Open a session on `RefuteVm` (`New-PSSession -ComputerName localhost -ConfigurationName RefuteVm`) and list the commands | **failed**: the session is not created. WinRM error `0x8009030e` during Negotiate authentication, "a specified logon session does not exist"; WinRM operational log event 142 (CreateShell failed, error 1312) and event 161 |
| The same with `-ComputerName 127.0.0.1` | the same error |
| The default endpoint (`New-PSSession -ComputerName localhost`, expected to be refused for lack of rights) | the same error, so the failure is not specific to `RefuteVm` |
| `Test-WSMan -ComputerName localhost`, anonymous and with `-Authentication Negotiate` | both succeed (with Negotiate the server reports its OS version): WinRM answers on loopback, and Negotiate succeeds for this identification request |
| Status (`Invoke-RefuteVm.ps1 -Status`) | **not run**: it needs the same session |
| Transcripts in `C:\ProgramData\RefuteVm\Transcripts` | the operator account cannot list the folder (access denied), as designed; no session was created, so no transcript is expected |
| Logon session of the calling process | the same logon session as the desktop shell (`explorer.exe`), interactive (logon type 2) |

These calls were made without `-EnableNetworkAccess` (cause 1 of section 5). A
hypothesis about the sign-in method of the account, considered in the first version of
this record, was ruled out by the maintainer and is not part of the evidence.

## 5. Diagnosis by the maintainer (2026-10-16)

The endpoint, WinRM, the firewall rule and the ACLs of section 3 are correct and are not
redone. Three causes were found:

1. **Loopback session.** With `-AccessMode Local`, a connection to localhost is a
   loopback connection only with implicit credentials (no `-Credential`) and
   `-EnableNetworkAccess`; otherwise it goes through the network stack and is denied.
   Source: https://learn.microsoft.com/powershell/module/microsoft.powershell.core/disable-psremoting
   (accessed 2026-10-16): "For loopback connections you must use implicit credentials
   along the EnableNetworkAccess parameter."
2. **Role capability location.** JEA looks for
   `<module path>\<module>\RoleCapabilities\<name>.psrc`, with no version subfolder
   (`GetRoleCapabilityPath` in
   https://github.com/PowerShell/PowerShell/blob/master/src/System.Management.Automation/engine/remoting/fanin/InitialSessionStateProvider.cs,
   accessed 2026-10-16; PowerShell 7 code, the behaviour of 5.1 inferred from the error
   observed). The registration had installed the module in `RefuteVm\0.1.0`, and the
   check of the script accepted the version subfolder. `Get-RefuteVmModuleFiles` hashes
   everything below the module folder, so an old subfolder would also disturb that check.
3. **Module import in the restricted session** (found after the repair below).
   `New-PSSession -ComputerName localhost -ConfigurationName RefuteVm -EnableNetworkAccess`
   failed with "The term 'Get-Module' is not recognized". The role capability imported
   the module with `RequiredVersion` and `GUID`; with that form PowerShell resolves the
   module by calling `Get-Module` inside the already restricted runspace, and a
   `RestrictedRemoteServer` session has no `Get-Module`. With a name only it imports
   without that call (`ProcessModulesToImport` in
   https://github.com/PowerShell/PowerShell/blob/master/src/System.Management.Automation/engine/InitialSessionState.cs
   and `GetModuleIfAvailable` in
   https://github.com/PowerShell/PowerShell/blob/master/src/System.Management.Automation/engine/Modules/ModuleCmdletBase.cs,
   accessed 2026-10-16).

**Manual repair by the maintainer, as Administrator, on 2026-10-16 at about 00:10 (local
time):** the hashes of the 6 files in `Modules\RefuteVm\0.1.0` were checked (6 of 6), the
files were copied to `C:\Program Files\WindowsPowerShell\Modules\RefuteVm\`
(`RoleCapabilities\` included), the 6 hashes were checked at the destination, and the
folder `RefuteVm\0.1.0` was removed by its literal path with a guard (`Test-Path`
returned False afterwards; exactly the 6 files remained).

The local `registration-evidence.json` (section 3) still names the old path
`Modules\RefuteVm\0.1.0` (module path, role capability copy and folder ACL key); it is a
record of the registration as it ran and is not rewritten.

## 6. Read-only check after the repair (2026-10-16, 03:13 UTC)

Run once by Claude Code under the operator account, authorized by the maintainer for this
check only (`.cache` script, nothing changed):

| Check | Result |
|---|---|
| Files under `C:\Program Files\WindowsPowerShell\Modules\RefuteVm\` | exactly 6; the only subfolder is `RoleCapabilities`; no version subfolder |
| Their SHA-256 | 6 of 6 equal to the export of `627842d` (section 3.1) |
| `New-PSSession -ComputerName localhost -ConfigurationName RefuteVm -EnableNetworkAccess` | **fails**: "The term 'Get-Module' is not recognized as the name of a cmdlet, function, script file, or operable program" (translated from the localized message; `PSSessionOpenFailed`), cause 3 |

**Status of W6.4:** the registration evidence matches W6.4; the endpoint's use by the
operator account is **not validated** until the role capability imports the module by
the path of its manifest and `Invoke-RefuteVm.ps1` opens a loopback session (pull
requests of 2026-10-16), the installed role capability is replaced by the maintainer, and
the session and `Invoke-RefuteVm.ps1 -Status` work. No VM operation is attempted before.

## 7. H.5: the role capability of main installed, and a fourth cause (2026-10-16)

Run by the maintainer on 2026-10-16. Account names are replaced by `<operator-account>`
(the maintainer's account) and `<virtual-account>` (the session's virtual account). The
raw security descriptor is not published: its group field holds the account SID.

### 7.1 Replacing the installed role capability

| Step | Result |
|---|---|
| 1. Source | `RefuteVmOperator.psrc` downloaded raw from GitHub at the merge of #100 (`46fe0c218d0082a8314931d5aa3044481dbbee04`), SHA-256 `d6ec0bf7f5bfdae982dc4c7653a6a74cb63c8287dd85459e24ac40a25614a103` (1766 bytes), equal to the blob in git |
| 2. Copy, as Administrator | installed before: `1303b08422e7a875a94a6b094d1f2733685c3c4837989606086f51887c6f1b08` (the role capability of `627842d`); copied; installed after: equal to the new hash (True); the same ACL before and after (True): owner Administrators, inherited entries only, SYSTEM and Administrators full control, Users, All Application Packages and All Restricted Application Packages read and execute only; 6 files in the module |

### 7.2 Session from the operator account (not an administrator)

| Check | Result |
|---|---|
| `New-PSSession -ComputerName localhost -ConfigurationName RefuteVm -EnableNetworkAccess` | **opens** (causes 1 to 3 of section 5 are resolved) |
| `Get-Command` in the session | exactly: `Clear-Host`, `Exit-PSSession`, `Get-Command`, `Get-FormatData`, `Get-Help`, `Get-RefuteVmStatus`, `Invoke-RefuteVmOperation`, `Measure-Object`, `Out-Default`, `Select-Object` (no `Get-Module`) |
| Identity of the session | connected user `<operator-account>`; run as `<virtual-account>`, a WinRM virtual account (`VA_5_...`) |
| `Invoke-RefuteVm.ps1 -Status`, from a worktree at main `6a8fe5c` | **fails** in the module: "The term 'Import-PowerShellDataFile' is not recognized" (reported at `Invoke-RefuteVm.ps1:65`). The output held the caller record and `ConfigSha256` `74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b`, with `Config` null, `Module` empty and `Observed` null |

### 7.3 The fourth cause

4. **Commands the module needs in the restricted session.**
   - **What the session holds:** a `RestrictedRemoteServer` session holds the core cmdlets as private commands, which a module's functions can call. It does not hold the script functions of `Microsoft.PowerShell.Utility` (`Import-PowerShellDataFile`, `Get-FileHash`) nor the Hyper-V cmdlets.
   - **What is missing:** with the role capability of `46fe0c2`, 29 of the 44 commands the module calls are missing: the two functions and 27 Hyper-V cmdlets. The analysis and the fix are in PR #118.
   - **The fix in #118:** it imports `Microsoft.PowerShell.Utility` and `Hyper-V`, each by the absolute path of its manifest in System32 (by name the functions of Utility do not come), with no change to the visible commands.
   - **The test in #118:** it checks this end to end on a real endpoint in CI.

**Status of W6.4 after H.5:**
- **Validated:** the session opens from the operator account and shows exactly the ten commands.
- **Not validated yet:** the status and the operations. They wait for #118 and for the maintainer's replacement of the installed role capability and module, with the same hash and ACL checks as in 7.1. No VM operation is attempted before.

## 8. Reinstallation of #118 and the first complete status (2026-10-16)

Run by the maintainer on 2026-10-16, with commands the maintainer checked. Account names
are replaced by `<operator-account>` and `<virtual-account>`, as in section 7; the raw
security descriptor is not published.

### 8.1 Replacing the three files changed by #118

Source: the merge of #118, `main` at `57812ca314b99289e701d07fa5c000979df3be27`.

| File | Installed before (expected) | New (`57812ca`) |
|---|---|---|
| `RoleCapabilities/RefuteVmOperator.psrc` | `d6ec0bf7f5bfdae982dc4c7653a6a74cb63c8287dd85459e24ac40a25614a103` | `4f82875330f13e52193829c2251923207bab9e316131eda52e3f44d6633e132c` |
| `RefuteVm.psm1` | `19a9c777c9baac18e933663f8a1739eb62ddc05869f62c089c7e675f86d714d2` | `9633d81d9d1e672316c89494704dbee837f368b16d1c26f6848b872b6085c8df` |
| `RefuteVm.HyperV.ps1` | `316183ad1ce0aae0eb28c9e2dfa31fc83fa4819eaecc112540a08e332c4e6d0e` | `32de95348c7d9d2a4da3b3648c69b955bf8d11983ceef05c7b2ba592a97d69ac` |

| Step | Result |
|---|---|
| 1. Source | the three files downloaded raw from GitHub at `57812ca`; their SHA-256 equal to the blobs in git (3 of 3) |
| 2. Copy, as Administrator | the three installed files before: equal to the expected hashes above (3 of 3); copied; the three after: equal to the new hashes (3 of 3); the same ACL before and after on the three (compared without printing the security descriptor); 6 files in the module |

The other three installed files (`RefuteVm.Config.psd1`, `RefuteVm.Core.ps1`,
`RefuteVm.psd1`) did not change in #118.

### 8.2 Session and status from the operator account (not an administrator)

| Check | Result |
|---|---|
| `New-PSSession -ComputerName localhost -ConfigurationName RefuteVm -EnableNetworkAccess` | **opens** |
| `Get-Command` in the session | exactly the ten commands of section 7.2 |
| `Invoke-RefuteVm.ps1 -Status`, from a worktree at `57812ca` | **completes** |
| Caller | connected user `<operator-account>`; run as `<virtual-account>`, a WinRM virtual account (`VA_7_...`) |
| Config | loaded; `ConfigSha256` `fa27a08622297aa2615cf48d09d584fed6b4ab25b1862ce2f5d0d91c728208ff` |
| Module | the six hashes equal to the blobs of `57812ca`: the three new ones above, `RefuteVm.Config.psd1` `2559b7348a98430f9f61ebd85f8dfcf456292fadc32e6c3ea608e8db872c6a1e`, `RefuteVm.Core.ps1` `5b717a3355ec0919717524fe9937a37d544a75ae413ca49bb7397a18b409bf4e`, `RefuteVm.psd1` `fcbb3416bca125295d2c979567eb7c8cc07a173e0397da4967ed82c17c22d188` |
| Observed | no VM; the base disk absent; no imported media; on the host, `EnableEnhancedSessionMode` true and the default Hyper-V paths for virtual hard disks and virtual machines, under `C:\ProgramData\Microsoft\Windows` |

**Correction to section 7.2.** The `ConfigSha256` recorded there,
`74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b`, is the SHA-256 of
the four bytes `null`: the configuration did not load in that attempt, so it is not the
hash of a configuration.

**Status of W6.4 after the reinstallation:**
- **Validated:** the session opens from the operator account, shows exactly the ten
  commands, and `-Status` runs read-only to the end with the module of `main` at
  `57812ca`.
- **Not validated yet:** every operation. The first, `SetHostPaths`, is simulated first
  (`-Simulate`), and runs only with the maintainer's OK, one operation at a time.

## 9. Operation 1, SetHostPaths: failed, with no change to the host (2026-10-16)

Run by the maintainer through the endpoint, from the operator account. Account names are
replaced by `<operator-account>` and `<virtual-account>`; no security descriptor is
published.

### 9.1 What was run and what the log holds

| Step | Result |
|---|---|
| `-Operation SetHostPaths -Simulate` | `Mode` simulated, `AlreadyDone` false, `Refusal` null, `ConfigSha256` `fa27a08622297aa2615cf48d09d584fed6b4ab25b1862ce2f5d0d91c728208ff`; exactly two changes: `Host.VirtualMachinePath` from `C:\ProgramData\Microsoft\Windows\Hyper-V` to `C:\Hyper-V`, and `Host.VirtualHardDiskPath` from `C:\ProgramData\Microsoft\Windows\Virtual Hard Disks` to `C:\Hyper-V\Virtual Hard Disks`; `PlanSha256` `3976d96a09c23d1a6ca1cd858a16087810c4ecb814af3384a219b6041cffd304` |
| `-Operation SetHostPaths -PlanSha256 <that hash>`, twice (22:08:38 and 22:09:30 UTC; the first from an Administrator terminal by mistake, the second from a normal one) | both failed: "Failed to modify service settings. The default virtual machine configuration store cannot be changed to 'C:\Hyper-V': Access denied. (0x80070005)" (translated from the localized message) |
| `C:\ProgramData\RefuteVm\Log\operations.jsonl`, read on 2026-10-16 | for each attempt, an `intent` record and a `result` record with `Outcome` failed, both with that `PlanSha256`; each session ran as its own `<virtual-account>`, a different WinRM virtual account (VA numbers 9 and 12 in the log) |
| `-Status` and a new `-Simulate` afterwards | nothing changed: the same two planned changes and the same `PlanSha256` |
| Log Microsoft-Windows-Hyper-V-VMMS-Admin | a pair of events 15110 ("Failed to modify service settings") and 18170 (the access denied) at each attempt, with no account name and no right named |

### 9.2 Diagnosis

**The ACL the maintainer read (as Administrator, read-only):**
- `C:\Hyper-V`, as the registration set it:
  - owner Administrators, protected DACL;
  - SYSTEM and Administrators full control;
  - Hyper-V Administrators modify;
  - all entries inherited by folders and files.

  The folders below inherit it.
- The default folder of Windows, `C:\ProgramData\Microsoft\Windows\Hyper-V`, has:
  - entries for CREATOR OWNER, SYSTEM and Administrators;
  - entries for NT VIRTUAL MACHINE\Virtual Machines: read on the files below, list and create in the folder and the folders below;
  - no entry for Hyper-V Administrators.

**What the sources say** (accessed 2026-10-16):
- **A JEA virtual account exists for one session only, under a new name each time.** "Virtual accounts are one-time, temporary local accounts that are created for the connecting user to use during the duration of their JEA session", and "each JEA user session has a unique virtual account": https://learn.microsoft.com/en-us/powershell/scripting/security/remoting/jea/security-considerations.
- **The Hyper-V management service acts with the identity of its caller when it changes permissions.** It runs as SYSTEM, "but impersonates during this operation the current user" when it gives a VM access to an attached virtual disk: https://decoder.cloud/2020/01/20/from-hyper-v-admin-to-system/ (a security research article, not Microsoft documentation).
- **A VM needs its own SID on its files.** Microsoft's fix for a VM that does not start is to grant `NT VIRTUAL MACHINE\<VM ID>` access to the disk and to the configuration file: https://learn.microsoft.com/en-us/troubleshoot/windows-server/virtualization/hyper-v-virtual-machine-not-start-0x80070005.
- **The Virtual Machines group is maintained by Hyper-V.** NT VIRTUAL MACHINE\Virtual Machines is S-1-5-83-0, "created when the Hyper-V role is installed", with its membership maintained by the Hyper-V management service: https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/manage/understand-security-identifiers.

**The cause: demonstrated on the CI runner `windows-2025` (runs 38978769925 to 38983528864, below); on the maintainer's Windows 11 it stays pending confirmation until the new attempt.**
- **What it says:** to adopt a folder as a default, and to attach a disk or an ISO to a VM, the Hyper-V management service changes permissions with the caller's identity. The caller is the session's virtual account, a member of Hyper-V Administrators only. It has Modify on the tree but neither ChangePermissions nor ownership, so the change is denied.
- **What supports it:** the error, the impersonation described above, and the default folder of Windows, which holds the Virtual Machines entries.
- **What the runner showed for SetHostPaths:** under version 1 the call is denied with the host's message; with ChangePermissions alone, and with version 2, it succeeds.
- **What is still pending:** no source states which right `Set-VMHost` needs, and the runner is not the maintainer's host. Only the new attempt on the host, after the corrected ACL, confirms the cause there. The evidence covers SetHostPaths only.
- **Each session is a new account.** A file created in one session is not owned by the account of the next one.

**The other operations with the ACL of the registration: hypotheses, not tested.** Only SetHostPaths was observed (denied on the host and on the runner). For the others, what follows is what the diagnosis predicts, not evidence:
- **Expected to meet the same denial:**
  - **AttachBaseDisk:** it gives the VM's SID access to the base disk created in another session.
  - **AttachInstallMedia:** it gives the VM's SID access to the two ISOs copied in another session.
- **Possibly at risk:**
  - **CreateVm:** it gives the VM's SID access to its configuration, in a folder created in the same session.
  - **SaveVm:** the saved state is written in the VM's folder, where the Virtual Machines group has no entry.
- **Not expected to meet this problem:** the operations that change only VM or host settings (memory, processors, Secure Boot, checkpoints, integration services, network, boot order, start, stop, suspend, resume, the processor maximum, enhanced session mode). This is a prediction too.
- **Another question, for ImportInstallIso and ImportSeedIso:** they read the media in the project folder, which the virtual account may not be allowed to read. That is a separate check, for the operations themselves.

Each of these is known only when it runs, one operation at a time with the maintainer's OK.

**The correction, not applied: version 2 of the tree ACL** (`Get-RefuteVmTreeAclSpec` in `scripts/vm/RefuteRegistration.Core.ps1`). Its design was approved by the maintainer on 2026-10-16 **as an explicit security concession**; applying it on the host is a separate decision of the maintainer.
- **Hyper-V Administrators:** Modify plus ChangePermissions, inherited.
- **NT VIRTUAL MACHINE\Virtual Machines:** the entries of the default folder of Windows.
- **The concessions of version 2:**
  - Hyper-V Administrators can change permissions on the whole tree.
  - NT VIRTUAL MACHINE\Virtual Machines gets read **and the creation of files and subfolders** (CreateFiles and AppendData on the root, inherited by the folders below), besides read on the files.
  - These rights apply to the VM identities of the host. The tests do **not** show that a guest system can reach the disks of the tree directly.
- **The limit of the evidence:** it covers SetHostPaths only; it does not show the other operations.
- **Nothing else changes.** The maintainer applies it with the new `scripts/vm/Set-RefuteVmTreeAcl.ps1`, as Administrator: a preview, then `-Apply -PreviewSha256`.
  - **No automatic rollback:** the script does not promise one. If the post-check fails, the maintainer STOPS and presents the effective state of the ACL, with no automatic correction.
  - The `PreviewSha256` covers the state the change depends on: every item of the tree and the evidence folders, with creation time, attributes, owner, protection and every access entry.
  - The script reads that state again just before the change.
  - Each folder below must inherit exactly what the tree passes down, before and after; the check compares who gets which rights on the folder, its subfolders and its files.
  - The evidence goes to a new file, created before the change, that only SYSTEM and Administrators can change. The Log folder must hold exactly the registration's ACL, and `C:\`, `C:\ProgramData` and `C:\ProgramData\RefuteVm` must let no other account delete, change permissions or take ownership.
  - **A premise, not a check:** Hyper-V Administrators has Delete on the tree (Modify), so a member could rename `C:\Hyper-V` and put something else in its place. That no session of the endpoint and no other writer runs during the whole apply is a premise the maintainer accepts.
    - **What supports it:** for each state the script reads one sample of the group's members and one of the open PowerShell remoting sessions (`wsmprovhost.exe`, the process that hosts every session), and accepts the state only when both are empty, at the preview and again just before the change.
    - **Why the sessions are found by their process:** on the CI runner (run 38982160054) a session's virtual account was not listed among the group's members while the session was open: it has the group in its token only. The CI test checks that a session of its endpoint adds a `wsmprovhost.exe` while it is open.
    - **What it does not cover:** the short window between the last read and the change.
- **What version 2 is not:**
  - **Not the smallest change that worked:** ChangePermissions alone also worked for SetHostPaths on the runner (third run, below). The observed advantage of version 2 is a predictable final ACL: with ChangePermissions alone the service wrote broader entries on the root (Virtual Machines, CREATOR OWNER with full control, and a capability SID).
  - **Not a bound on Hyper-V Administrators:** with ChangePermissions they can widen the tree's ACL. What they can do in practice stays limited by the commands the endpoint exposes.
  - **Not limited to the Refute VM:** the Virtual Machines entries (read, and the creation of files and subfolders) apply to the VM identities of the whole host, since the group is not the Refute VM alone. Direct access from a guest system is not shown.

**Could the CI have caught it? Yes, with a real call.**
- **What the test did:** since run 38934817010 the CI endpoint test runs on a `windows-2025` runner that has the Hyper-V management service. It called only `-Status` and `SetHostPaths -Simulate`, and a simulation cannot show whether the virtual account may change the host paths.
- **What it does now:** it makes the real call on the runner, under each version of the tree ACL, each in a new session:
  - under version 1 the call must fail with access denied and leave the host paths unchanged;
  - under version 2 it must succeed.
- **First run, 38978769925 (head `3adc0a5`, 2026-10-16):**
  - **Version 1:** the call failed with the host's message: "The default virtual machine configuration store cannot be changed to 'C:\Hyper-V': Access is denied. (0x80070005)". The host paths did not change.
  - **Version 2:** the module reported `done`, and its own observation after the call showed the new paths. The test's `Get-VMHost`, in a process that had read the host before the attempts, still showed the old ones, so the test failed. It now reads the host paths through CIM.
- **Second run, 38980778326 (head `5799d85`, 2026-10-16), all green:**
  - version 1 failed again with the host's message;
  - under version 2 the call was `done` and the host paths read through CIM were `C:\Hyper-V` and `C:\Hyper-V\Virtual Hard Disks`;
  - the service added no entry to the root of the tree in either attempt.

  So on the runner, version 2 is enough for SetHostPaths and version 1 is not. The test then also recorded `Get-VMHost` in a new process, and a third tree between the two: version 1 with ChangePermissions only, without the Virtual Machines entries.
- **Third run, 38982160054 (head `4ce1bd2`, 2026-10-16):**
  - **Version 1:** denied again, with the host's message.
  - **ChangePermissions only:** the call was `done`, and CIM and a new process showed the new host paths. So for SetHostPaths on the runner, ChangePermissions is the right that was missing. The service then **added entries to the root itself**:
    - NT VIRTUAL MACHINE\Virtual Machines, as on the default folder;
    - CREATOR OWNER, full control, inherit-only;
    - a capability SID, `S-1-15-3-1024-2268835264-3721307629-241982045-173645152-1490879176-104643441-2915960892-1612460704`, full control on the folder and inherit-only (its name was not resolved).
  - **Version 2:** `done`, the new host paths through CIM and in a new process, and the service added nothing to the root.
  - **The first run's puzzle, explained:** `Get-VMHost` in the test's own process, which had read the host before, still showed the old paths after each successful call, while CIM and a new process showed the new ones. That is a cache of the Hyper-V module in that process.
  - **The test failed on its positive control:** while a session was open, Hyper-V Administrators listed no member, so the empty-group check of `Set-RefuteVmTreeAcl.ps1` could not find a session. The script now also refuses open remoting sessions (`wsmprovhost.exe`), and the test checks that instead.
- **What this means for the choice of the ACL:**
  - With ChangePermissions alone the service writes its own entries on the first default change, broader than version 2 (full control for CREATOR OWNER and for the capability SID), and the tree then no longer matches what Refute set.
  - With version 2 the tree stays as Refute set it.
  - Whether other operations (attaching disks and media, creating and saving the VM) need more is not known; each is tested when it runs.
- **What the test now requires of version 2** (the WP6 package review): after the call the root still holds exactly version 2, with nothing added by the service, and every folder below still inherits exactly what it passes down.
- **What the CI does not show:**
  - a complete apply of `Set-RefuteVmTreeAcl.ps1` and the writing of its protected evidence (the CI builds the ACLs itself and checks the applier's preview only);
  - the network isolation of the real installation: the test enables PowerShell remoting on the runner with `Enable-PSRemoting` (a listener on every address and a firewall exception), which the real installation never does; this is acceptable only on a runner discarded after the job.
- **The limits:** the runner is Windows Server 2025, not the maintainer's Windows 11. It demonstrates the cause there; it does not replace the attempt on the host. It covers SetHostPaths only, not the other operations. The attempts share one tree, so the whole tree is checked against each version before its call.

**Status of W6.4 at the end of this section:** no operation had succeeded; operation 1 was pending the corrected ACL and the maintainer's new attempt (section 10).

## 10. Version 2 applied, and operation 1 done on the host (2026-10-16)

Run by the maintainer on 2026-10-16 (Brasília time; UTC below). As the maintainer reports,
the main folder was at `ca91f9103c1e7e6eef3ea44bf8abd18af0f63dcd` (the merge of #126) the
whole time, and the agent was idle meanwhile. Account names are replaced by `<operator-account>`
and `<virtual-account>`; no security descriptor is published.

### 10.1 Version 2 of the tree ACL (`scripts/vm/Set-RefuteVmTreeAcl.ps1`, as Administrator)

| Step | Result |
|---|---|
| a) The hashes, before running | `Set-RefuteVmTreeAcl.ps1` `AD0C5D0CF87EE93C8D115F31AEDA25E52D04B6BE174409B1B45115EDFAF7430F`, `RefuteRegistration.Core.ps1` `E22A61A96FC88EDE07697CD6D0A6B3221DCCF8FA31770BEC7DAA6012170AE2E0`, equal to the blobs of `ca91f91` |
| b) The preview, with `PSModuleAnalysisCachePath=nul` | `State now (C:\Hyper-V is version 1)`; `C:\Hyper-V` owned by Administrators, protected, exactly the three entries of version 1; the three folders below with inherited entries only, and no other file or folder; the evidence folders with the registration's ACL; `Hyper-V Administrators members: none`; `Open remoting sessions (wsmprovhost.exe): none`; `Preconditions hold`; `PreviewSha256` `f71782d0876fc7aa4f93c2b896bd840fad20be5d8bac6e1ebe573d608e78a776` |
| c) The apply, with that `PreviewSha256` | `Done: evidence file created: C:\ProgramData\RefuteVm\Log\vmtree-acl-evidence-20261017T015022354Z.json; ACL of C:\Hyper-V set to version 2; checks passed`. The evidence file `vmtree-acl-evidence-20261017T015022354Z.json` (created at 01:50:22.354 UTC) has SHA-256 `8b1b3a62c2e4c04b9b4b4a69db1a29fdd91bba84737169accb5c60ea5a723845` |
| d) The post-check, the same script without `-Apply` | `State now (C:\Hyper-V is version 2)`; on the root exactly SYSTEM (2032127), Administrators (2032127), Hyper-V Administrators (1507775, inherited by folders and files), and the Virtual Machines group with two entries (1179785 inherit-only on files, 1179791 on the folder and the folders below); the three folders with those entries inherited only; `Nothing to do: C:\Hyper-V already holds version 2.`; `PreviewSha256` `4f2a777f60e59d2ef13e4ba67d076b449d8dac433efe5c10b2039a8ec5cbba18` |

### 10.2 Operation 1, SetHostPaths, through the endpoint (a normal window)

From `C:\ProgramData\RefuteVm\Log\operations.jsonl`, read on 2026-10-16 (read only). The two
failed attempts of section 9 are still recorded before these lines: `intent` at
22:08:38.514 UTC and `result` failed at 22:08:38.651 UTC (VA 9), `intent` at
22:09:29.935 UTC and `result` failed at 22:09:30.029 UTC (VA 12), both with the
`PlanSha256` below.

| Step | Log record (UTC, 2026-10-17) | Result |
|---|---|---|
| e) `-Operation SetHostPaths -Simulate` | `simulated` at 01:51:43.946, `<virtual-account>` VA 15 | the same as before the ACL change: `AlreadyDone` false, the same two changes, `ConfigSha256` `fa27a08622297aa2615cf48d09d584fed6b4ab25b1862ce2f5d0d91c728208ff`, `PlanSha256` `3976d96a09c23d1a6ca1cd858a16087810c4ecb814af3384a219b6041cffd304` |
| e) `-Operation SetHostPaths -PlanSha256 <that hash>` | `intent` at 01:52:13.830 and `result` at 01:52:13.920, VA 16 | `Mode` result, `Outcome` done, `Error` null |
| f) A new `-Simulate` | `simulated` at 01:52:18.029, VA 18 | `AlreadyDone` true, no change, the host paths `C:\Hyper-V` and `C:\Hyper-V\Virtual Hard Disks` (`PlanSha256` `173d31a354123dea75a715d791968a6032b887f4e8ce7fed295fc735cd31da6c`) |
| f) `-Status` | (read only, no record) | `VirtualMachinePath` `C:\Hyper-V`, `VirtualHardDiskPath` `C:\Hyper-V\Virtual Hard Disks`, `EnableEnhancedSessionMode` true, no VM |
| f) The post-check of the ACL again, as Administrator | (no record) | version 2, `Nothing to do`, and the **same** `PreviewSha256` `4f2a777f…cbba18` as in d) |

### 10.3 Conclusion

- **The cause is confirmed on the maintainer's Windows 11, for SetHostPaths.** On the same
  host, with the same plan (`PlanSha256` `3976d96a…d304`), the operation was denied twice
  under version 1 and done under version 2. With the CI runner (section 9), the cause is
  now shown on both.
- **The tree was the same after the paths were adopted.** The `PreviewSha256` of the
  post-check is the same before and after SetHostPaths. It covers the list of items under
  `C:\Hyper-V` and, for each item and for the evidence folders, its creation time,
  attributes, owner, protection and every access entry. So no difference in what the
  preview covers was left between the two checks: the service left no entry and no item
  in `C:\Hyper-V` when it adopted the folder as its default. Two observations of the state
  cannot exclude a change made and undone between them.
- **The other operations remain hypotheses, not tested** (section 9.2): each is known only
  when it runs, one operation at a time with the maintainer's OK.

**Status of W6.4 at the end of this section:** operation 1, `SetHostPaths`, is validated on
the host. Every other operation is not validated yet.

## 11. Operation 2, DisableEnhancedSessionHost, done on the host (2026-10-16)

Run by the maintainer on 2026-10-16 (Brasília time; UTC below), through the endpoint from a
normal window, after operation 1 (section 10). Account names are replaced by
`<operator-account>` and `<virtual-account>`; no security descriptor is published. The ACL of
`C:\Hyper-V` was not changed: it is still version 2 (section 10.1).

### 11.1 What was run and what the log holds

From `C:\ProgramData\RefuteVm\Log\operations.jsonl`, read on 2026-10-17 (read only). The four
records of this operation follow the records of section 10, and every record carries the
same module hashes as those of section 10.

| Step | Log record (UTC, 2026-10-17) | Result |
|---|---|---|
| a) `-Operation DisableEnhancedSessionHost -Simulate` | `simulated` at 01:54:37.475, `<virtual-account>` VA 19 | `AlreadyDone` false, `Refusal` null, one change: `Host.EnableEnhancedSessionMode` from true to false; `ConfigSha256` `fa27a08622297aa2615cf48d09d584fed6b4ab25b1862ce2f5d0d91c728208ff`; preconditions: the host paths already `C:\Hyper-V` and `C:\Hyper-V\Virtual Hard Disks`, no VM, no base disk, no media; `PlanSha256` `93dffecbcce12bd78b7fea03c4c65c5cd7fa38de0b93017b084cea796b9c17d4` |
| b) `-Operation DisableEnhancedSessionHost -PlanSha256 <that hash>` | `intent` at 01:55:25.512 and `result` at 01:55:25.613, VA 20 | `Mode` result, `Outcome` done, `Error` null, on the first attempt |
| c) `-Status` | (read only, no record) | `EnableEnhancedSessionMode` false, `VirtualMachinePath` `C:\Hyper-V`, `VirtualHardDiskPath` `C:\Hyper-V\Virtual Hard Disks`, no VM |
| d) A new `-Simulate` | `simulated` at 01:55:29.426, VA 22 | `AlreadyDone` true, no change (`PlanSha256` `ef6b1fd0de9294791c6ee235a438030c98c56c5ba951f1fb31860d74f52e8535`) |

### 11.2 Conclusion

- **Operation 2 was done with the simulated plan, on the first attempt.** The execution used
  the `PlanSha256` of the simulation, and the new simulation found nothing left to do.
- **It changes a host setting, not a file Refute creates.** The module calls
  `Set-VMHost -EnableEnhancedSessionMode $false` (`RefuteVm.HyperV.ps1`); the ACL of
  `C:\Hyper-V` was not checked after it. Its success says nothing about the ACL questions of
  the later operations, which create disks, VMs and media under `C:\Hyper-V`; those remain
  hypotheses, not tested (section 9.2).
- **Not done:** operation 3, `CreateBaseDisk`, was neither simulated nor run; it waits for the
  change of the base disk size and the update of the installed configuration.

**Status of W6.4:** operations 1, `SetHostPaths`, and 2, `DisableEnhancedSessionHost`, are
validated on the host. Every other operation is not validated yet.
