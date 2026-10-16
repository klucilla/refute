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

Without -Apply nothing is changed: the script reads the ACL of C:\Hyper-V and of the
folders below it, prints the entries now and the entries it would set, and a PreviewSha256
of that list. With -Apply -PreviewSha256 <hash> it recomputes the list, refuses if it
differs from the preview, and then, stopping at the first problem:

  1. sets the ACL of C:\Hyper-V to version 2 (owner Administrators, inheritance from C:\
     removed); the folders below inherit it;
  2. checks that C:\Hyper-V holds exactly version 2, and that every folder below holds no
     explicit entry and inherits the new entries;
  3. writes C:\ProgramData\RefuteVm\Log\vmtree-acl-evidence.json.

It refuses when C:\Hyper-V holds anything but version 1 (or version 2: then there is
nothing to do), when a folder below has explicit entries or is a link, when a file exists
anywhere under C:\Hyper-V, or when a folder other than the three of the registration
exists there: the maintainer decides those cases. It never deletes anything, and it does
not touch the Hyper-V host settings.
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
$Below = @('C:\Hyper-V\Virtual Hard Disks', 'C:\Hyper-V\refute-vm', 'C:\Hyper-V\refute-vm\media')
$EvidencePath = 'C:\ProgramData\RefuteVm\Log\vmtree-acl-evidence.json'

. (Join-Path $PSScriptRoot 'RefuteRegistration.Core.ps1')

function Get-SidName([string]$Sid) {
    # The account name of a SID for the listing, or the SID itself when it does not map.
    try {
        return (New-Object System.Security.Principal.SecurityIdentifier $Sid).Translate([System.Security.Principal.NTAccount]).Value
    } catch [System.Security.Principal.IdentityNotMappedException] {
        return $Sid
    }
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
foreach ($folder in $Below) {
    try {
        $item = Get-Item -LiteralPath $folder -Force -ErrorAction Stop
        if (([int]$item.Attributes -band [int][System.IO.FileAttributes]::ReparsePoint) -ne 0) { $problems.Add("$folder is a reparse point (a link or junction)") }
        $acl = Get-Acl -LiteralPath $folder -ErrorAction Stop
        if ($acl.AreAccessRulesProtected) { $problems.Add("$folder does not inherit from its parent") }
        $explicit = @(ConvertTo-RefuteAclRules $acl -IncludeInherited $false)
        if ($explicit.Count) { $problems.Add("$folder has explicit entries: $($explicit -join '; ')") }
        $owner = [string]$acl.GetOwner([System.Security.Principal.SecurityIdentifier]).Value
        if (-not (Test-RefuteAllowedOwner $owner)) { $problems.Add("$folder is owned by $owner") }
    } catch { $problems.Add("$folder cannot be read: $($_.Exception.Message)") }
}
try {
    $files = @(Get-ChildItem -LiteralPath $TreeRoot -Recurse -Force -File -ErrorAction Stop | ForEach-Object { $_.FullName })
    if ($files.Count) { $problems.Add("files exist under $TreeRoot (the maintainer decides): $($files -join ', ')") }
    $folders = @(Get-ChildItem -LiteralPath $TreeRoot -Recurse -Force -Directory -ErrorAction Stop | ForEach-Object { $_.FullName })
    $extra = @($folders | Where-Object { $Below -notcontains $_ })
    if ($extra.Count) { $problems.Add("folders other than the registration's exist under $TreeRoot (the maintainer decides): $($extra -join ', ')") }
} catch { $problems.Add("$TreeRoot cannot be listed: $($_.Exception.Message)") }

# ---- the change list (preview) ---------------------------------------------------------
$lines = New-Object System.Collections.Generic.List[string]
$lines.Add("ACL of $TreeRoot now ($state):")
foreach ($rule in $current) { $lines.Add("  $rule") }
$lines.Add("1. Set the ACL of $TreeRoot to version 2 (owner Administrators, inheritance from C:\ removed):")
foreach ($e in $version2) { $lines.Add(("     {0} {1} ({2}; {3})" -f (Get-SidName $e.Sid), $e.Rights, $e.Inheritance, $e.Propagation)) }
$lines.Add("2. Check $TreeRoot holds exactly version 2, and that $($Below -join ', ') hold no explicit entry and inherit it")
$lines.Add("3. Write the evidence to $EvidencePath")
$sha = [System.Security.Cryptography.SHA256]::Create()
$previewHash = -join ($sha.ComputeHash([System.Text.Encoding]::UTF8.GetBytes(($lines -join "`n"))) | ForEach-Object { $_.ToString('x2') })
$sha.Dispose()

Write-Output '== ACL of the VM tree =='
Write-Output ('Mode: ' + $(if ($Apply) { 'APPLY' } else { 'preview (no change)' }))
foreach ($line in $lines) { Write-Output $line }
Write-Output "PreviewSha256: $previewHash"
if ($state -eq 'version 2' -and -not $problems.Count) { Write-Output "Nothing to do: $TreeRoot already holds version 2."; exit 0 }
if ($Apply -and $PreviewSha256 -and $PreviewSha256 -cne $previewHash) { $problems.Add('the change list differs from the previewed one; run the preview again') }
if ($problems.Count) {
    Write-Output 'Problems (nothing was changed):'
    foreach ($p in $problems) { Write-Output "  - $p" }
    exit 1
}
if (-not $Apply) { Write-Output "Preconditions hold. To apply: -Apply -PreviewSha256 $previewHash"; exit 0 }

# ---- apply ------------------------------------------------------------------------------
$done = New-Object System.Collections.Generic.List[string]
try {
    # 1. the new ACL; the folders below inherit it
    Set-Acl -LiteralPath $TreeRoot -AclObject (New-RefuteFolderAcl $version2)
    $done.Add("ACL of $TreeRoot set to version 2")
    # 2. checks
    $after = Get-Acl -LiteralPath $TreeRoot
    $left = @(Compare-RefuteVmTreeAcl -Acl $after -Spec $version2)
    if ($left.Count) { throw ("$TreeRoot does not hold version 2: " + ($left -join '; ')) }
    $inheritedWanted = @(ConvertTo-RefuteAclRules (New-RefuteFolderAcl $version2) | ForEach-Object { $_ })
    $belowEvidence = [ordered]@{}
    foreach ($folder in $Below) {
        $acl = Get-Acl -LiteralPath $folder
        $explicit = @(ConvertTo-RefuteAclRules $acl -IncludeInherited $false)
        if ($explicit.Count) { throw "$folder has explicit entries after the change: $($explicit -join '; ')" }
        $inherited = @(ConvertTo-RefuteAclRules $acl)
        $hyperV = @($inherited | Where-Object { $_ -like 'Allow S-1-5-32-578 *' })
        if ($hyperV.Count -eq 0) { throw "$folder does not inherit the entry of Hyper-V Administrators" }
        $belowEvidence[$folder] = $inherited
    }
    # 3. evidence (entries by SID; no account name)
    $evidence = [ordered]@{
        Utc           = [DateTime]::UtcNow.ToString('yyyy-MM-ddTHH:mm:ssZ')
        PreviewSha256 = $previewHash
        Before        = $current
        Root          = @(ConvertTo-RefuteAclRules $after)
        Below         = $belowEvidence
        Spec          = $inheritedWanted
    }
    $utf8 = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($EvidencePath, (ConvertTo-Json $evidence -Depth 5), $utf8)
    $done.Add("evidence written to $EvidencePath")
} catch {
    Write-Output "STOPPED: $($_.Exception.Message)"
    Write-Output ('Already done: ' + $(if ($done.Count) { $done -join '; ' } else { 'nothing' }))
    exit 2
}
Write-Output ('Done: ' + ($done -join '; '))
Write-Output "Evidence: $EvidencePath (SHA-256 $((Get-FileHash -LiteralPath $EvidencePath -Algorithm SHA256).Hash.ToLowerInvariant()))"
