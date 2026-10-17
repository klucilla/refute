<#
.SYNOPSIS
Replaces the ACL of the VM tree (C:\Hyper-V) set by the registration of 2026-10-15
(version 1 of Get-RefuteVmTreeAclSpec) with version 2 (WP6). Run by the maintainer, in
Windows PowerShell 5.1 started as Administrator, with PSModuleAnalysisCachePath=nul in its
environment (scripts/vm/README.md).

.DESCRIPTION
Why: through the JEA endpoint the first VM operation, SetHostPaths, failed on 2026-10-16
with "access denied" (0x80070005). Each session runs as a new virtual account, a member of
Hyper-V Administrators only, which version 1 gives Modify on the tree but not the right to
change permissions; the Hyper-V management service changes permissions with the identity
of its caller (docs/validation/v0.3/wp6-results/jea-registration.md, section 9). Version 2
adds ChangePermissions for Hyper-V Administrators and the entries of NT VIRTUAL
MACHINE\Virtual Machines that the default folder of Windows has.

Without -Apply nothing is changed: the script reads the VM tree and the folders of the
evidence, and prints their state (paths, creation times, attributes, owners, protection and
every access entry), the change list, and a PreviewSha256 of both. With -Apply
-PreviewSha256 <hash> it reads that state again and refuses if the hash differs, and then,
stopping at the first problem:

  1. creates the evidence file, a new file (never an existing one) that only SYSTEM and
     Administrators can change; if it cannot be created, nothing has changed;
  2. reads the state once more and refuses if it differs from the preview;
  3. sets the ACL of C:\Hyper-V to version 2 (owner Administrators, inheritance from C:\
     removed); the folders below inherit it;
  4. checks that C:\Hyper-V holds exactly version 2, and that every folder below holds no
     explicit entry and inherits exactly what version 2 passes down (compared by effect:
     who gets which rights on the folder, its subfolders and its files);
  5. writes the evidence (also when a step stops it, with what was done).

It refuses when C:\Hyper-V holds anything but version 1 (or version 2: then there is
nothing to do), when a folder below is a link, has explicit entries or inherits anything
other than what C:\Hyper-V passes down, when a file exists anywhere under C:\Hyper-V, when a
folder other than the three of the registration exists there, when C:\, C:\ProgramData or
C:\ProgramData\RefuteVm lets another account delete, change permissions or take ownership,
when the Log folder does not hold exactly the ACL of the registration, when Hyper-V
Administrators has any member, or when a PowerShell remoting session is open
(wsmprovhost.exe; a session of the endpoint has the group in its token without being
listed as a member): the maintainer decides those cases. That group can delete C:\Hyper-V
(Modify), so no session of the endpoint and no other writer may run during the whole
apply: a premise the maintainer accepts. The checks support it but do not prove it, and
they do not close the short window between the last read and the change. It never deletes
anything, and it does not touch the Hyper-V host settings.

There is NO automatic rollback. If a step stops after the ACL was set, or the post-check
fails, the script reports what was done and writes the evidence; the maintainer then STOPS
and presents the effective state of the ACL, with no automatic correction.
#>
[CmdletBinding()]
param(
    [switch]$Apply,
    [ValidatePattern('^[0-9a-f]{64}$')][string]$PreviewSha256 = ''
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2.0
# Only a value present when powershell.exe starts disables the module analysis cache
# (about_Windows_PowerShell_5.1, "Module analysis cache"); refuse before reading anything.
if ($env:PSModuleAnalysisCachePath -ne 'nul') {
    Write-Output 'Problems (nothing was changed):'
    Write-Output '  - start powershell.exe with PSModuleAnalysisCachePath=nul in its environment (see scripts/vm/README.md), so no module analysis cache is written'
    exit 1
}

$TreeRoot = 'C:\Hyper-V'
# the folders the registration creates below C:\Hyper-V, with their depth
$Below = [ordered]@{ 'C:\Hyper-V\Virtual Hard Disks' = 1; 'C:\Hyper-V\refute-vm' = 1; 'C:\Hyper-V\refute-vm\media' = 2 }
# the evidence folder and its parents, each checked (no link) and bound to the preview hash
$EvidenceChain = @('C:\ProgramData', 'C:\ProgramData\RefuteVm', 'C:\ProgramData\RefuteVm\Log')
$EvidenceFolder = $EvidenceChain[-1]
# the ACL Register-RefuteVmEndpoint.ps1 gives the Log folder (its $FolderAcls): owner
# Administrators, protected; SYSTEM and Administrators full control, Hyper-V Administrators
# modify (no DeleteSubdirectoriesAndFiles, so no deletion of a file it cannot delete), Users
# read and execute; all inherited by folders and files
$all = 'ContainerInherit, ObjectInherit'
$LogAclSpec = @(
    [ordered]@{ Sid = 'S-1-5-18'; Rights = 'FullControl'; Inheritance = $all; Propagation = 'None' },
    [ordered]@{ Sid = 'S-1-5-32-544'; Rights = 'FullControl'; Inheritance = $all; Propagation = 'None' },
    [ordered]@{ Sid = 'S-1-5-32-578'; Rights = 'Modify'; Inheritance = $all; Propagation = 'None' },
    [ordered]@{ Sid = 'S-1-5-32-545'; Rights = 'ReadAndExecute'; Inheritance = $all; Propagation = 'None' }
)

. (Join-Path $PSScriptRoot 'RefuteRegistration.Core.ps1')

function Get-OpenRemotingSessions {
    # The process IDs of wsmprovhost.exe, the process that hosts every open PowerShell
    # remoting session, a session of the endpoint included. A JEA session's virtual account
    # does not show among the members of Hyper-V Administrators (CI run 38982160054), so
    # open sessions are found by their host process; the CI test checks that a session of
    # its endpoint shows here while it is open.
    return @(Get-Process -Name 'wsmprovhost' -ErrorAction SilentlyContinue | ForEach-Object { [string]$_.Id } | Sort-Object)
}

function Get-HyperVAdminMembers {
    # The SIDs of the members of Hyper-V Administrators (S-1-5-32-578), by SID (never by a
    # localized name). If the group cannot be read, that is reported as a member, so the
    # check refuses rather than passes.
    try {
        return @(Get-LocalGroupMember -SID 'S-1-5-32-578' -ErrorAction Stop | ForEach-Object { [string]$_.SID.Value } | Sort-Object)
    } catch { return @("(the group cannot be read: $($_.Exception.Message))") }
}

function Get-SidName([string]$Sid) {
    # The account name of a SID for the listing, or the SID itself when it does not map.
    try {
        return (New-Object System.Security.Principal.SecurityIdentifier $Sid).Translate([System.Security.Principal.NTAccount]).Value
    } catch [System.Security.Principal.IdentityNotMappedException] {
        return $Sid
    }
}

function Get-TreeState([string[]]$Members, [string[]]$Sessions) {
    # The state the change depends on, as lines: for C:\Hyper-V, every item below it, and
    # the evidence folders: the path, creation time, attributes, owner, protection and every
    # access entry (explicit and inherited, by SID); then the members of Hyper-V
    # Administrators and the open remoting sessions, the one sample of each the caller read
    # and checked for this state. Unreadable items give a line saying so.
    $paths = New-Object System.Collections.Generic.List[string]
    $paths.Add($TreeRoot)
    try {
        foreach ($item in @(Get-ChildItem -LiteralPath $TreeRoot -Recurse -Force -ErrorAction Stop | Sort-Object FullName)) { $paths.Add($item.FullName) }
    } catch { $paths.Add("$TreeRoot\* (cannot be listed: $($_.Exception.Message))") }
    foreach ($p in $EvidenceChain) { $paths.Add($p) }
    $state = New-Object System.Collections.Generic.List[string]
    foreach ($p in $paths) {
        if ($p.EndsWith(')')) { $state.Add($p); continue }
        try {
            $item = Get-Item -LiteralPath $p -Force -ErrorAction Stop
            $acl = Get-Acl -LiteralPath $p -ErrorAction Stop
            $state.Add(('{0} | created {1} | attributes {2} | owner {3} | protected {4}' -f $p, $item.CreationTimeUtc.Ticks, [int]$item.Attributes,
                    [string]$acl.GetOwner([System.Security.Principal.SecurityIdentifier]).Value, $acl.AreAccessRulesProtected))
            foreach ($rule in @(ConvertTo-RefuteAclRules $acl)) { $state.Add("    $rule") }
        } catch { $state.Add("$p | cannot be read: $($_.Exception.Message)") }
    }
    $state.Add('Hyper-V Administrators members: ' + $(if (@($Members).Count) { @($Members) -join ', ' } else { 'none' }))
    $state.Add('Open remoting sessions (wsmprovhost.exe): ' + $(if (@($Sessions).Count) { @($Sessions) -join ', ' } else { 'none' }))
    return $state
}

function Get-StateHash([string[]]$Lines) {
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try { return -join ($sha.ComputeHash([System.Text.Encoding]::UTF8.GetBytes(($Lines -join "`n"))) | ForEach-Object { $_.ToString('x2') }) }
    finally { $sha.Dispose() }
}

# ---- preconditions ------------------------------------------------------------------
$problems = New-Object System.Collections.Generic.List[string]
$isAdmin = ([System.Security.Principal.WindowsPrincipal][System.Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([System.Security.Principal.WindowsBuiltInRole]::Administrator)
if ($PSVersionTable.PSEdition -ne 'Desktop' -or $PSVersionTable.PSVersion.Major -ne 5) { $problems.Add('run in Windows PowerShell 5.1 (powershell.exe)') }
if (-not $isAdmin) { $problems.Add('run in a PowerShell started as Administrator') }
if ($Apply -and -not $PreviewSha256) { $problems.Add('-Apply needs -PreviewSha256 from a preview run') }
$version1 = @(Get-RefuteVmTreeAclSpec -Version 1)
$version2 = @(Get-RefuteVmTreeAclSpec -Version 2)
$current = @()
$state = 'unknown'
try {
    $rootItem = Get-Item -LiteralPath $TreeRoot -Force -ErrorAction Stop
    if (-not $rootItem.PSIsContainer) { $problems.Add("$TreeRoot is not a folder") }
    if (([int]$rootItem.Attributes -band [int][System.IO.FileAttributes]::ReparsePoint) -ne 0) { $problems.Add("$TreeRoot is a reparse point (a link or junction)") }
    $rootAcl = Get-Acl -LiteralPath $TreeRoot -ErrorAction Stop
    $current = @(ConvertTo-RefuteAclRules $rootAcl)
    if (@(Compare-RefuteVmTreeAcl -Acl $rootAcl -Spec $version2).Count -eq 0) { $state = 'version 2' }
    elseif (@(Compare-RefuteVmTreeAcl -Acl $rootAcl -Spec $version1).Count -eq 0) { $state = 'version 1' }
    else {
        $state = 'other'
        foreach ($p in @(Compare-RefuteVmTreeAcl -Acl $rootAcl -Spec $version1)) { $problems.Add("$TreeRoot is neither version 1 nor version 2: $p") }
    }
} catch { $problems.Add("$TreeRoot cannot be read: $($_.Exception.Message)") }
# the folders below must inherit exactly what C:\Hyper-V passes down now
$rootSpec = $(if ($state -eq 'version 2') { $version2 } else { $version1 })
foreach ($folder in $Below.Keys) {
    try {
        $item = Get-Item -LiteralPath $folder -Force -ErrorAction Stop
        if (([int]$item.Attributes -band [int][System.IO.FileAttributes]::ReparsePoint) -ne 0) { $problems.Add("$folder is a reparse point (a link or junction)") }
        $acl = Get-Acl -LiteralPath $folder -ErrorAction Stop
        foreach ($p in @(Compare-RefuteVmTreeBelow -Acl $acl -Spec $rootSpec -Depth $Below[$folder])) { $problems.Add("${folder}: $p") }
        $owner = [string]$acl.GetOwner([System.Security.Principal.SecurityIdentifier]).Value
        if (-not (Test-RefuteAllowedOwner $owner)) { $problems.Add("$folder is owned by $owner") }
    } catch { $problems.Add("$folder cannot be read: $($_.Exception.Message)") }
}
try {
    $files = @(Get-ChildItem -LiteralPath $TreeRoot -Recurse -Force -File -ErrorAction Stop | ForEach-Object { $_.FullName })
    if ($files.Count) { $problems.Add("files exist under $TreeRoot (the maintainer decides): $($files -join ', ')") }
    $folders = @(Get-ChildItem -LiteralPath $TreeRoot -Recurse -Force -Directory -ErrorAction Stop | ForEach-Object { $_.FullName })
    $extra = @($folders | Where-Object { @($Below.Keys) -notcontains $_ })
    if ($extra.Count) { $problems.Add("folders other than the registration's exist under $TreeRoot (the maintainer decides): $($extra -join ', ')") }
} catch { $problems.Add("$TreeRoot cannot be listed: $($_.Exception.Message)") }
# the evidence folders and C:\ (Codex review of #126, round 2): C:\, C:\ProgramData and
# C:\ProgramData\RefuteVm get the ancestor check of the registration (no link, an allowed
# owner, no other account allowed to delete, change permissions or take ownership), and the
# Log folder must hold exactly the ACL the registration gives it, so no other account can
# delete the evidence file or change the folder's permissions
foreach ($folder in @('C:\') + $EvidenceChain[0..($EvidenceChain.Count - 2)]) {
    foreach ($p in @(Get-RefuteItemProblems -Item $folder -IsAncestor $true)) { $problems.Add($p) }
}
try {
    $item = Get-Item -LiteralPath $EvidenceFolder -Force -ErrorAction Stop
    if (-not $item.PSIsContainer) { $problems.Add("$EvidenceFolder is not a folder") }
    if (([int]$item.Attributes -band [int][System.IO.FileAttributes]::ReparsePoint) -ne 0) { $problems.Add("$EvidenceFolder is a reparse point (a link or junction)") }
    $logAcl = Get-Acl -LiteralPath $EvidenceFolder -ErrorAction Stop
    $owner = [string]$logAcl.GetOwner([System.Security.Principal.SecurityIdentifier]).Value
    if ($owner -ne 'S-1-5-32-544') { $problems.Add("$EvidenceFolder is owned by $owner, not Administrators") }
    if (-not $logAcl.AreAccessRulesProtected) { $problems.Add("$EvidenceFolder inherits from its parent") }
    $logWanted = @(ConvertTo-RefuteAclRules (New-RefuteFolderAcl $LogAclSpec))
    $logActual = @(ConvertTo-RefuteAclRules $logAcl)
    foreach ($rule in $logActual) { if ($logWanted -notcontains $rule) { $problems.Add("$EvidenceFolder has an unexpected entry: $rule") } }
    foreach ($rule in $logWanted) { if ($logActual -notcontains $rule) { $problems.Add("$EvidenceFolder misses the entry: $rule") } }
} catch { $problems.Add("$EvidenceFolder cannot be read: $($_.Exception.Message)") }
# Hyper-V Administrators: Modify includes Delete, so a member, or a session of the endpoint
# (whose virtual account has the group in its token without being listed as a member, CI run
# 38982160054), could rename C:\Hyper-V and put something else in its place between the last
# read and the change. The maintainer's account is not a member. For each state one sample
# of the group's members and one of the open remoting sessions (wsmprovhost.exe) are read,
# and the state is accepted only when both are empty: here and when the state is read again
# before the change. That no session and no other writer runs during the whole apply stays
# a premise the maintainer accepts; these checks support it.
$hyperVMembers = @(Get-HyperVAdminMembers)
if ($hyperVMembers.Count) { $problems.Add("Hyper-V Administrators has members (the maintainer decides): $($hyperVMembers -join ', ')") }
$openSessions = @(Get-OpenRemotingSessions)
if ($openSessions.Count) { $problems.Add("PowerShell remoting sessions are open (wsmprovhost.exe, process IDs $($openSessions -join ', ')); close every session of the endpoint first") }

# ---- the state and the change list (preview) --------------------------------------------
$lines = New-Object System.Collections.Generic.List[string]
$lines.Add("State now (C:\Hyper-V is $state):")
$treeState = @(Get-TreeState -Members $hyperVMembers -Sessions $openSessions)
foreach ($line in $treeState) { $lines.Add("  $line") }
$lines.Add("1. Create the evidence file $EvidenceFolder\vmtree-acl-evidence-<UTC time>.json, a new file only SYSTEM and Administrators can change (Users read)")
$lines.Add('2. Read the state again; stop if it differs from this preview')
$lines.Add("3. Set the ACL of $TreeRoot to version 2 (owner Administrators, inheritance from C:\ removed):")
foreach ($e in $version2) { $lines.Add(("     {0} {1} ({2}; {3})" -f (Get-SidName $e.Sid), $e.Rights, $e.Inheritance, $e.Propagation)) }
$lines.Add("4. Check $TreeRoot holds exactly version 2, and that $(@($Below.Keys) -join ', ') hold no explicit entry and inherit exactly what version 2 passes down")
$lines.Add('5. Write the evidence to the file of step 1')
$previewHash = Get-StateHash $lines

Write-Output '== ACL of the VM tree =='
Write-Output ('Mode: ' + $(if ($Apply) { 'APPLY' } else { 'preview (no change)' }))
foreach ($line in $lines) { Write-Output $line }
Write-Output "PreviewSha256: $previewHash"
if ($state -eq 'version 2' -and -not $problems.Count) { Write-Output "Nothing to do: $TreeRoot already holds version 2."; exit 0 }
if ($Apply -and $PreviewSha256 -and $PreviewSha256 -cne $previewHash) { $problems.Add('the state or the change list differs from the previewed one; run the preview again') }
if ($problems.Count) {
    Write-Output 'Problems (nothing was changed):'
    foreach ($p in $problems) { Write-Output "  - $p" }
    exit 1
}
if (-not $Apply) { Write-Output "Preconditions hold. To apply: -Apply -PreviewSha256 $previewHash"; exit 0 }

# ---- apply ------------------------------------------------------------------------------
$done = New-Object System.Collections.Generic.List[string]
$evidencePath = Join-Path $EvidenceFolder ('vmtree-acl-evidence-' + [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ') + '.json')
$evidence = [ordered]@{
    Utc           = [DateTime]::UtcNow.ToString('yyyy-MM-ddTHH:mm:ssZ')
    PreviewSha256 = $previewHash
    Before        = $treeState
    Outcome       = 'stopped'
    Done          = $done
    Error         = $null
    Root          = @()
    Below         = [ordered]@{}
}
$stream = $null
$failed = $false
try {
    # 1. the evidence file: CreateNew never opens an existing file; its ACL is set at creation
    # (owner Administrators, protected: SYSTEM and Administrators full control, Users read),
    # so no other account can change it, and the handle stays open until the end
    $fileAcl = New-Object System.Security.AccessControl.FileSecurity
    $fileAcl.SetAccessRuleProtection($true, $false)
    $fileAcl.SetOwner((New-Object System.Security.Principal.SecurityIdentifier 'S-1-5-32-544'))
    foreach ($entry in @(@('S-1-5-18', 'FullControl'), @('S-1-5-32-544', 'FullControl'), @('S-1-5-32-545', 'Read'))) {
        $fileAcl.AddAccessRule((New-Object System.Security.AccessControl.FileSystemAccessRule(
                    (New-Object System.Security.Principal.SecurityIdentifier $entry[0]), [System.Security.AccessControl.FileSystemRights]$entry[1],
                    [System.Security.AccessControl.AccessControlType]::Allow)))
    }
    $stream = New-Object System.IO.FileStream($evidencePath, [System.IO.FileMode]::CreateNew, [System.Security.AccessControl.FileSystemRights]::Write,
        [System.IO.FileShare]::Read, 4096, [System.IO.FileOptions]::None, $fileAcl)
    $fileCheck = Get-Acl -LiteralPath $evidencePath
    $fileRules = @(ConvertTo-RefuteAclRules $fileCheck)
    $fileWanted = @(ConvertTo-RefuteAclRules $fileAcl)
    if (-not $fileCheck.AreAccessRulesProtected -or [string]$fileCheck.GetOwner([System.Security.Principal.SecurityIdentifier]).Value -ne 'S-1-5-32-544' -or
        ($fileRules -join '|') -cne ($fileWanted -join '|')) { throw "the evidence file $evidencePath does not hold the ACL it was created with" }
    $done.Add("evidence file created: $evidencePath")
    # 2. the state again, just before the change
    $membersAgain = @(Get-HyperVAdminMembers)
    if ($membersAgain.Count) { throw "Hyper-V Administrators has members now: $($membersAgain -join ', '); nothing on the tree was changed" }
    $sessionsAgain = @(Get-OpenRemotingSessions)
    if ($sessionsAgain.Count) { throw "remoting sessions are open now (wsmprovhost.exe, process IDs $($sessionsAgain -join ', ')); nothing on the tree was changed" }
    $again = New-Object System.Collections.Generic.List[string]
    $again.Add("State now (C:\Hyper-V is $state):")
    foreach ($line in @(Get-TreeState -Members $membersAgain -Sessions $sessionsAgain)) { $again.Add("  $line") }
    foreach ($line in @($lines | Select-Object -Skip ($treeState.Count + 1))) { $again.Add($line) }
    if ((Get-StateHash $again) -cne $previewHash) { throw 'the state changed after the preview; nothing on the tree was changed' }
    # 3. the new ACL; the folders below inherit it
    Set-Acl -LiteralPath $TreeRoot -AclObject (New-RefuteFolderAcl $version2)
    $done.Add("ACL of $TreeRoot set to version 2")
    # 4. checks
    $after = Get-Acl -LiteralPath $TreeRoot
    $evidence.Root = @(ConvertTo-RefuteAclRules $after)
    $left = @(Compare-RefuteVmTreeAcl -Acl $after -Spec $version2)
    if ($left.Count) { throw ("$TreeRoot does not hold version 2: " + ($left -join '; ')) }
    foreach ($folder in $Below.Keys) {
        $acl = Get-Acl -LiteralPath $folder
        $evidence.Below[$folder] = [ordered]@{
            Owner  = [string]$acl.GetOwner([System.Security.Principal.SecurityIdentifier]).Value
            Rules  = @(ConvertTo-RefuteAclRules $acl)
            Effect = @(ConvertTo-RefuteAclEffect @($acl.GetAccessRules($true, $true, [System.Security.Principal.SecurityIdentifier])))
        }
        $differences = @(Compare-RefuteVmTreeBelow -Acl $acl -Spec $version2 -Depth $Below[$folder])
        if ($differences.Count) { throw ("$folder does not inherit version 2: " + ($differences -join '; ')) }
        if (-not (Test-RefuteAllowedOwner $evidence.Below[$folder].Owner)) { throw "$folder is owned by $($evidence.Below[$folder].Owner)" }
    }
    $done.Add('checks passed')
    $evidence.Outcome = 'done'
} catch {
    $failed = $true
    $evidence.Error = $_.Exception.Message
    Write-Output "STOPPED: $($_.Exception.Message)"
} finally {
    # 5. the evidence (entries by SID; no account name), also when a step stopped; the
    # stream is closed even if the write fails, and that failure is reported after the
    # first one
    if ($stream) {
        try {
            $bytes = (New-Object System.Text.UTF8Encoding($false)).GetBytes((ConvertTo-Json $evidence -Depth 6))
            $stream.Write($bytes, 0, $bytes.Length)
        } catch {
            $failed = $true
            Write-Output "STOPPED: the evidence could not be written: $($_.Exception.Message)"
        } finally { $stream.Dispose() }
    }
}
if ($failed) {
    Write-Output ('Already done: ' + $(if ($done.Count) { $done -join '; ' } else { 'nothing' }))
    if ($stream) { Write-Output "Evidence: $evidencePath" }
    exit 2
}
Write-Output ('Done: ' + ($done -join '; '))
Write-Output "Evidence: $evidencePath (SHA-256 $((Get-FileHash -LiteralPath $evidencePath -Algorithm SHA256).Hash.ToLowerInvariant()))"
