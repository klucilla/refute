<#
.SYNOPSIS
Replaces RefuteVm.Config.psd1 of the installed RefuteVm module, and nothing else (WP6). Run
by the maintainer, in Windows PowerShell 5.1 started as Administrator, with
PSModuleAnalysisCachePath=nul in its environment (scripts/vm/README.md).

.DESCRIPTION
The procedure reviewed with Codex in pull request #134 (steps 0 to 3), as a script.

Step 0: the checker of the registration, RefuteRegistration.Core.ps1, is read once as bytes,
its SHA-256 is checked, and only those bytes are loaded. Get-RefuteTargetProblems (the
Assert-RefuteTarget of the procedure, returning every finding instead of the first) then
checks, with its tested functions:
  - the discovery set of the JEA session (Get-RefuteDiscoveryProblems): owners, writers,
    every ancestor up to the volume root, no reparse point;
  - the installed configuration file itself: not a reparse point, an allowed owner
    (Test-RefuteAllowedOwner), and no other account that can write it
    (Get-RefuteAceWriters: generic rights mapped, CREATOR OWNER only inherit-only);
  - exactly 6 files in the module;
  - no open remoting session (wsmprovhost.exe) at that moment.
Step 1 (the preview, without -Apply): step 0, then the SHA-256 of the installed file must be
-InstalledSha256 and that of the source -SourceSha256. Nothing is changed. It prints both
hashes and "Preconditions hold", or the problems.
Step 2 (with -Apply): step 0 again, the installed hash again, then the source is read once as
bytes, hashed in memory, and written from that same buffer over the installed file, in
place (its ACL stays).
Step 3: the installed file must now have -SourceSha256, the ACL of the file and of the
module folder must equal what they were before the write, and step 0 must pass again.

Limits:
  - the session check is a snapshot; it does not stop a call that starts during the write;
  - the write is not atomic. If it is interrupted, the file can be left incomplete; the
    module then fails closed (Import-PowerShellDataFile or Test-RefuteVmConfig throws, and
    every call refuses). Recovery: run -Apply again with -InstalledSha256 set to the hash
    of the incomplete file, as the preview prints it.

It prints no security descriptor and no path of its own (the files are named by their role).
Error messages pass through Format-RefuteReason, which masks every path under a user
profile folder (X:\Users\<name>, in any case) and the current account name (in any case);
a name that appears elsewhere in a message from Windows is not detected. It never deletes
anything, and changes no file but the installed RefuteVm.Config.psd1.

Reversal: -SourcePath <the previous RefuteVm.Config.psd1, saved in a folder only
administrators can write>, -InstalledSha256 <the new hash>, -SourceSha256 <the previous hash>.

The tests dot-source this file (tests/vm/config_update_cases.ps1): it then only defines its
functions and runs nothing.

.EXAMPLE
  scripts\vm\Update-RefuteVmConfig.ps1
  scripts\vm\Update-RefuteVmConfig.ps1 -Apply
#>
[CmdletBinding()]
param(
    [switch]$Apply,
    [string]$SourcePath = '',
    [ValidatePattern('^[0-9A-Fa-f]{64}$')][string]$InstalledSha256 = '2559B7348A98430F9F61EBD85F8DFCF456292FADC32E6C3EA608E8DB872C6A1E',
    [ValidatePattern('^[0-9A-Fa-f]{64}$')][string]$SourceSha256 = 'FE46F573C0BF49E1D6EED819CD7F8EB4C220F50B5BE1BF34BEA9E7D11AC11F46'
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2.0

# the SHA-256 of RefuteRegistration.Core.ps1 whose functions this script uses (the file the
# maintainer checked on 2026-10-16, jea-registration.md section 10.1); a changed checker
# needs a reviewed change of this value
$CoreSha256 = 'E22A61A96FC88EDE07697CD6D0A6B3221DCCF8FA31770BEC7DAA6012170AE2E0'
$script:RefuteExitCode = 1

function Get-RefuteBytesSha256([byte[]]$Bytes) {
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try { return [System.BitConverter]::ToString($sha.ComputeHash($Bytes)).Replace('-', '') } finally { $sha.Dispose() }
}

function Get-RefuteFileSha256Upper([string]$Path) {
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToUpperInvariant()
}

function Format-RefuteReason([string]$Text) {
    # an error message with every user profile folder (any drive, any account, any case)
    # and the current account name masked, case-insensitively
    $ignore = [System.Text.RegularExpressions.RegexOptions]::IgnoreCase
    $out = [regex]::Replace($Text, '[A-Za-z]:\\Users\\[^\\/:*?"<>|\r\n]+', '%USERPROFILE%', $ignore)
    if ($env:USERNAME) { $out = [regex]::Replace($out, [regex]::Escape($env:USERNAME), '<account>', $ignore) }
    return $out
}

function Write-Problems([string]$Heading, [string[]]$Problems) {
    Write-Output $Heading
    foreach ($p in $Problems) { Write-Output ('  - ' + (Format-RefuteReason $p)) }
}

function Get-RefuteTargetProblems([string]$ModuleDir, [string]$InstalledPath) {
    # Assert-RefuteTarget of the reviewed procedure, returning every finding (none: an empty
    # result) instead of throwing at the first; a read that fails is a finding too.
    $found = New-Object System.Collections.Generic.List[string]
    try {
        foreach ($p in @(Get-RefuteDiscoveryProblems -Roots @(Get-RefuteJeaDiscoveryRoots))) { $found.Add("discovery set: $p") }
        if ((Get-Item -LiteralPath $InstalledPath -Force).Attributes -band [System.IO.FileAttributes]::ReparsePoint) { $found.Add('the configuration is a reparse point') }
        $acl = Get-Acl -LiteralPath $InstalledPath
        if (-not (Test-RefuteAllowedOwner $acl.GetOwner([System.Security.Principal.SecurityIdentifier]).Value)) { $found.Add('the configuration has another owner') }
        $entries = @(foreach ($e in $acl.GetAccessRules($true, $true, [System.Security.Principal.SecurityIdentifier])) {
                [pscustomobject]@{ Sid = $e.IdentityReference.Value; Rights = [int]$e.FileSystemRights; Type = [string]$e.AccessControlType
                    InheritOnly = [bool]($e.PropagationFlags -band [System.Security.AccessControl.PropagationFlags]::InheritOnly) } })
        $writers = @(Get-RefuteAceWriters -Entries $entries)
        if ($writers.Count) { $found.Add('another account can write the configuration: ' + ($writers -join ', ')) }
        if (@(Get-ChildItem -LiteralPath $ModuleDir -Recurse -File -Force).Count -ne 6) { $found.Add('the module does not hold exactly 6 files') }
        # a failed query throws; an empty list means no open session at this moment
        if (@(Get-CimInstance -ClassName Win32_Process -Filter "Name = 'wsmprovhost.exe'").Count) { $found.Add('a remoting session is open') }
    } catch {
        $found.Add("a check could not read: $($_.Exception.Message)")
    }
    # enumerated, so that no finding gives an empty result for @(...) at the caller
    return $found.ToArray()
}

function Invoke-RefuteConfigUpdate {
    # Steps 1 to 3 (step 0, the checker, is loaded by the caller). Writes its report to the
    # output and leaves the exit code in $script:RefuteExitCode.
    param([string]$ModuleDir, [string]$InstalledPath, [string]$Source, [string]$Old, [string]$New, [switch]$DoApply)
    $script:RefuteExitCode = 1
    $Old = $Old.ToUpperInvariant()
    $New = $New.ToUpperInvariant()
    Write-Output ('Mode: ' + $(if ($DoApply) { 'apply' } else { 'preview (no change)' }))

    # ---- step 1: the preview
    $problems = New-Object System.Collections.Generic.List[string]
    foreach ($p in @(Get-RefuteTargetProblems $ModuleDir $InstalledPath)) { $problems.Add($p) }
    $installedNow = ''
    $sourceNow = ''
    try { $installedNow = Get-RefuteFileSha256Upper $InstalledPath } catch { $problems.Add("the installed configuration cannot be hashed: $($_.Exception.Message)") }
    try { $sourceNow = Get-RefuteFileSha256Upper $Source } catch { $problems.Add("the source cannot be hashed: $($_.Exception.Message)") }
    Write-Output "Installed configuration SHA-256: $installedNow (expected $Old)"
    Write-Output "Source SHA-256:                  $sourceNow (expected $New)"
    if ($installedNow -and $installedNow -ne $Old) { $problems.Add('the installed configuration is not the expected one') }
    if ($sourceNow -and $sourceNow -ne $New) { $problems.Add('the source is not the expected one') }
    if ($problems.Count) { Write-Problems 'Problems (nothing was changed):' $problems.ToArray(); return }
    Write-Output 'Preconditions hold'
    if (-not $DoApply) { $script:RefuteExitCode = 0; return }

    # ---- apply
    # step 2: the ACLs before (kept in memory only, never printed), the checks again, then
    # one write from one checked buffer
    $problems = New-Object System.Collections.Generic.List[string]
    $bytes = $null
    $aclFileBefore = ''
    $aclDirBefore = ''
    try {
        $aclFileBefore = (Get-Acl -LiteralPath $InstalledPath).Sddl
        $aclDirBefore = (Get-Acl -LiteralPath $ModuleDir).Sddl
        foreach ($p in @(Get-RefuteTargetProblems $ModuleDir $InstalledPath)) { $problems.Add($p) }
        if (-not $problems.Count -and (Get-RefuteFileSha256Upper $InstalledPath) -ne $Old) { $problems.Add('the installed configuration changed since the preview') }
        if (-not $problems.Count) {
            $bytes = [System.IO.File]::ReadAllBytes($Source)
            if ((Get-RefuteBytesSha256 $bytes) -ne $New) { $problems.Add('the source changed since the preview') }
        }
    } catch {
        $problems.Add("a check before the write could not read: $($_.Exception.Message)")
    }
    if ($problems.Count) { Write-Problems 'Problems (nothing was changed):' $problems.ToArray(); return }
    try {
        [System.IO.File]::WriteAllBytes($InstalledPath, $bytes)
    } catch {
        Write-Problems 'Stopped during the write (the installed configuration may be incomplete; the module then refuses every call):' @(
            $_.Exception.Message,
            'recovery: run the preview, then -Apply with -InstalledSha256 set to the hash it prints')
        return
    }
    Write-Output 'Written: the installed configuration was replaced in place'

    # step 3: the checks after the write
    $problems = New-Object System.Collections.Generic.List[string]
    $after = ''
    try {
        $after = Get-RefuteFileSha256Upper $InstalledPath
        if ($after -ne $New) { $problems.Add("the installed configuration has SHA-256 $after, not $New") }
        if ((Get-Acl -LiteralPath $InstalledPath).Sddl -ne $aclFileBefore) { $problems.Add('the ACL of the installed configuration changed') }
        if ((Get-Acl -LiteralPath $ModuleDir).Sddl -ne $aclDirBefore) { $problems.Add('the ACL of the module folder changed') }
        foreach ($p in @(Get-RefuteTargetProblems $ModuleDir $InstalledPath)) { $problems.Add($p) }
    } catch {
        $problems.Add("a check after the write could not read: $($_.Exception.Message)")
    }
    if ($problems.Count) {
        Write-Problems 'Problems after the write (the installed configuration WAS replaced; stop and inspect, no automatic correction):' $problems.ToArray()
        return
    }
    Write-Output "Done: installed configuration SHA-256 $after; the ACLs are unchanged; checks passed"
    Write-Output 'Next, from a normal window: scripts\vm\Invoke-RefuteVm.ps1 -Status'
    $script:RefuteExitCode = 0
}

# ---- main (not run when the tests dot-source this file)
if ($MyInvocation.InvocationName -eq '.') { return }

# Only a value present when powershell.exe starts disables the module analysis cache
# (about_Windows_PowerShell_5.1, "Module analysis cache"); refuse before reading anything.
if ($env:PSModuleAnalysisCachePath -ne 'nul') {
    Write-Output 'Problems (nothing was changed):'
    Write-Output '  - start powershell.exe with PSModuleAnalysisCachePath=nul in its environment (see scripts/vm/README.md), so no module analysis cache is written'
    exit 1
}

# step 0: who runs, and the checker loaded from checked bytes
$problems = New-Object System.Collections.Generic.List[string]
$isAdmin = ([System.Security.Principal.WindowsPrincipal][System.Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([System.Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) { $problems.Add('run in Windows PowerShell started as Administrator') }
if ($PSVersionTable.PSEdition -ne 'Desktop' -or $PSVersionTable.PSVersion.Major -ne 5) { $problems.Add('run in Windows PowerShell 5.1 (powershell.exe)') }
if ($problems.Count) { Write-Problems 'Problems (nothing was changed):' $problems.ToArray(); exit 1 }

try {
    $coreBytes = [System.IO.File]::ReadAllBytes((Join-Path $PSScriptRoot 'RefuteRegistration.Core.ps1'))
} catch {
    Write-Problems 'Problems (nothing was changed):' @("RefuteRegistration.Core.ps1 cannot be read: $($_.Exception.Message)")
    exit 1
}
$coreActual = Get-RefuteBytesSha256 $coreBytes
if ($coreActual -ne $CoreSha256) {
    Write-Problems 'Problems (nothing was changed):' @("RefuteRegistration.Core.ps1 has SHA-256 $coreActual, not the checked $CoreSha256")
    exit 1
}
. ([scriptblock]::Create([System.Text.Encoding]::ASCII.GetString($coreBytes)))

$dir = Join-Path $env:ProgramFiles 'WindowsPowerShell\Modules\RefuteVm'
$source = $SourcePath
if (-not $source) { $source = Join-Path $PSScriptRoot 'RefuteVm\RefuteVm.Config.psd1' }
Invoke-RefuteConfigUpdate -ModuleDir $dir -InstalledPath (Join-Path $dir 'RefuteVm.Config.psd1') -Source $source -Old $InstalledSha256 -New $SourceSha256 -DoApply:$Apply
exit $script:RefuteExitCode
