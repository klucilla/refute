<#
.SYNOPSIS
Replaces ONE file of the installed RefuteVm module (-File; by default RefuteVm.Config.psd1),
and nothing else (WP6). Run by the maintainer, in Windows PowerShell 5.1 started as
Administrator, with PSModuleAnalysisCachePath=nul in its environment (scripts/vm/README.md).
-File is one of the six files of the module; for any file but RefuteVm.Config.psd1,
-InstalledSha256 and -SourceSha256 must be given (their defaults are the configuration's).
The source is that file under scripts\vm\RefuteVm of this checkout, unless -SourcePath is
given. Several files are replaced by running the script once per file.

.DESCRIPTION
The procedure reviewed with Codex in pull request #134 (steps 0 to 3), as a script.

Step 0: the checker of the registration, RefuteRegistration.Core.ps1, is read once as bytes,
its SHA-256 is checked, and only those bytes are loaded. Get-RefuteTargetProblems (the
Assert-RefuteTarget of the procedure, returning every finding instead of the first) then
checks, with its tested functions:
  - the discovery set of the JEA session (Get-RefuteDiscoveryProblems): owners, writers,
    every ancestor up to the volume root, no reparse point;
  - the installed file file itself: not a reparse point, an allowed owner
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

It prints no security descriptor and no path of its own: the files are named by their role,
and an error is reported by the step, the role of the file, the exception's type and its
HRESULT (Format-RefuteError), never by the exception's message. A finding of the checker is
printed as a category (Format-RefuteFinding), without its path, SID or Windows message; the
registration's own checks list the details. As a last guard, every printed problem passes
through Format-RefuteReason, which masks every path under a user profile folder
(X:\Users\<name>, in any case) and the current account name. The hash arguments are checked
in the body, so a wrong value is never echoed. Messages PowerShell itself prints before the
script runs (an unknown parameter name, for example) are outside this guarantee.
It never deletes anything, and changes no file but the one installed file named by -File.

Reversal: -File <the file> -SourcePath <its previous version, saved in a folder only
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
    # one of $ModuleFiles, checked in the body (never echoed)
    [string]$File = 'RefuteVm.Config.psd1',
    [string]$SourcePath = '',
    # checked in the body, with a controlled message: a ValidatePattern error would echo the
    # value given (Codex review of #134)
    [string]$InstalledSha256 = '2559B7348A98430F9F61EBD85F8DFCF456292FADC32E6C3EA608E8DB872C6A1E',
    [string]$SourceSha256 = 'FE46F573C0BF49E1D6EED819CD7F8EB4C220F50B5BE1BF34BEA9E7D11AC11F46'
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2.0

# the SHA-256 of RefuteRegistration.Core.ps1 whose functions this script uses (the file the
# maintainer checked on 2026-10-16, jea-registration.md section 10.1); a changed checker
# needs a reviewed change of this value
$CoreSha256 = 'E22A61A96FC88EDE07697CD6D0A6B3221DCCF8FA31770BEC7DAA6012170AE2E0'
$script:RefuteExitCode = 1
# the six files of the installed module (the registration installs exactly these)
$ModuleFiles = @('RefuteVm.Config.psd1', 'RefuteVm.Core.ps1', 'RefuteVm.HyperV.ps1', 'RefuteVm.psd1', 'RefuteVm.psm1', 'RoleCapabilities\RefuteVmOperator.psrc')

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

function Format-RefuteError($ErrorRecord) {
    # a controlled diagnostic of an error: the exception's type and HRESULT, never its
    # message, which can hold a path or an account name (Codex review of #134)
    $e = $ErrorRecord.Exception
    return ('{0} (HRESULT 0x{1:X8})' -f $e.GetType().Name, $e.HResult)
}

function Format-RefuteFinding([string]$Finding) {
    # A finding of the checker as a controlled category, without its path, SID or Windows
    # message (Codex review of #134). The registration's own checks list the details.
    if ($Finding.Contains(' cannot be read')) { return 'an item cannot be read' }
    if ($Finding.Contains(' is a reparse point')) { return 'an item is a reparse point (a link or junction)' }
    if ($Finding.Contains(' is owned by ')) { return 'an item has an owner other than SYSTEM, Administrators or TrustedInstaller' }
    if ($Finding.Contains('(an ancestor) can be changed by ')) { return 'an ancestor can be changed by another account' }
    if ($Finding.Contains(' can be written by ')) { return 'an item can be written by another account' }
    if ($Finding.Contains(' does not exist')) { return 'a folder of the discovery set does not exist' }
    return 'another finding'
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
        foreach ($p in @(Get-RefuteDiscoveryProblems -Roots @(Get-RefuteJeaDiscoveryRoots))) { $found.Add('discovery set: ' + (Format-RefuteFinding $p)) }
        if ((Get-Item -LiteralPath $InstalledPath -Force).Attributes -band [System.IO.FileAttributes]::ReparsePoint) { $found.Add('the installed file is a reparse point') }
        $acl = Get-Acl -LiteralPath $InstalledPath
        if (-not (Test-RefuteAllowedOwner $acl.GetOwner([System.Security.Principal.SecurityIdentifier]).Value)) { $found.Add('the installed file has another owner') }
        $entries = @(foreach ($e in $acl.GetAccessRules($true, $true, [System.Security.Principal.SecurityIdentifier])) {
                [pscustomobject]@{ Sid = $e.IdentityReference.Value; Rights = [int]$e.FileSystemRights; Type = [string]$e.AccessControlType
                    InheritOnly = [bool]($e.PropagationFlags -band [System.Security.AccessControl.PropagationFlags]::InheritOnly) } })
        $writers = @(Get-RefuteAceWriters -Entries $entries)
        if ($writers.Count) { $found.Add("another account can write the installed file ($($writers.Count) access entries)") }
        if (@(Get-ChildItem -LiteralPath $ModuleDir -Recurse -File -Force).Count -ne 6) { $found.Add('the module does not hold exactly 6 files') }
        # a failed query throws; an empty list means no open session at this moment
        if (@(Get-CimInstance -ClassName Win32_Process -Filter "Name = 'wsmprovhost.exe'").Count) { $found.Add('a remoting session is open') }
    } catch {
        $found.Add("a check could not read: $(Format-RefuteError $_)")
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
    try { $installedNow = Get-RefuteFileSha256Upper $InstalledPath } catch { $problems.Add("the installed file cannot be hashed: $(Format-RefuteError $_)") }
    try { $sourceNow = Get-RefuteFileSha256Upper $Source } catch { $problems.Add("the source cannot be hashed: $(Format-RefuteError $_)") }
    Write-Output "Installed file SHA-256: $installedNow (expected $Old)"
    Write-Output "Source SHA-256:         $sourceNow (expected $New)"
    if ($installedNow -and $installedNow -ne $Old) { $problems.Add('the installed file is not the expected one') }
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
        if (-not $problems.Count -and (Get-RefuteFileSha256Upper $InstalledPath) -ne $Old) { $problems.Add('the installed file changed since the preview') }
        if (-not $problems.Count) {
            $bytes = [System.IO.File]::ReadAllBytes($Source)
            if ((Get-RefuteBytesSha256 $bytes) -ne $New) { $problems.Add('the source changed since the preview') }
        }
    } catch {
        $problems.Add("a check before the write could not read: $(Format-RefuteError $_)")
    }
    if ($problems.Count) { Write-Problems 'Problems (nothing was changed):' $problems.ToArray(); return }
    try {
        [System.IO.File]::WriteAllBytes($InstalledPath, $bytes)
    } catch {
        Write-Problems 'Stopped during the write (the installed file may be incomplete; the module then refuses every call):' @(
            ('the write failed: ' + (Format-RefuteError $_)),
            'recovery: run the preview, then -Apply with -InstalledSha256 set to the hash it prints')
        return
    }
    Write-Output 'Written: the installed file was replaced in place'

    # step 3: the checks after the write
    $problems = New-Object System.Collections.Generic.List[string]
    $after = ''
    try {
        $after = Get-RefuteFileSha256Upper $InstalledPath
        if ($after -ne $New) { $problems.Add("the installed file has SHA-256 $after, not $New") }
        if ((Get-Acl -LiteralPath $InstalledPath).Sddl -ne $aclFileBefore) { $problems.Add('the ACL of the installed file changed') }
        if ((Get-Acl -LiteralPath $ModuleDir).Sddl -ne $aclDirBefore) { $problems.Add('the ACL of the module folder changed') }
        foreach ($p in @(Get-RefuteTargetProblems $ModuleDir $InstalledPath)) { $problems.Add($p) }
    } catch {
        $problems.Add("a check after the write could not read: $(Format-RefuteError $_)")
    }
    if ($problems.Count) {
        Write-Problems 'Problems after the write (the installed file WAS replaced; stop and inspect, no automatic correction):' $problems.ToArray()
        return
    }
    Write-Output "Done: installed file SHA-256 $after; the ACLs are unchanged; checks passed"
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

# step 0: the arguments, who runs, and the checker loaded from checked bytes
$problems = New-Object System.Collections.Generic.List[string]
$fileName = @($ModuleFiles | Where-Object { $_ -ieq $File })
if ($fileName.Count -ne 1) {
    $problems.Add('-File must be one of the six files of the module: ' + ($ModuleFiles -join ', '))
} elseif ($fileName[0] -ne 'RefuteVm.Config.psd1' -and -not ($PSBoundParameters.ContainsKey('InstalledSha256') -and $PSBoundParameters.ContainsKey('SourceSha256'))) {
    $problems.Add("-InstalledSha256 and -SourceSha256 are required for $($fileName[0])")
}
foreach ($pair in @(@('-InstalledSha256', $InstalledSha256), @('-SourceSha256', $SourceSha256))) {
    if ($pair[1] -notmatch '^[0-9A-Fa-f]{64}$') { $problems.Add("$($pair[0]) must be 64 hexadecimal digits") }
}
$isAdmin = ([System.Security.Principal.WindowsPrincipal][System.Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([System.Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) { $problems.Add('run in Windows PowerShell started as Administrator') }
if ($PSVersionTable.PSEdition -ne 'Desktop' -or $PSVersionTable.PSVersion.Major -ne 5) { $problems.Add('run in Windows PowerShell 5.1 (powershell.exe)') }
if ($problems.Count) { Write-Problems 'Problems (nothing was changed):' $problems.ToArray(); exit 1 }

try {
    $coreBytes = [System.IO.File]::ReadAllBytes((Join-Path $PSScriptRoot 'RefuteRegistration.Core.ps1'))
} catch {
    Write-Problems 'Problems (nothing was changed):' @("RefuteRegistration.Core.ps1 cannot be read: $(Format-RefuteError $_)")
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
if (-not $source) { $source = Join-Path (Join-Path $PSScriptRoot 'RefuteVm') $fileName[0] }
Write-Output "File: $($fileName[0])"
Invoke-RefuteConfigUpdate -ModuleDir $dir -InstalledPath (Join-Path $dir $fileName[0]) -Source $source -Old $InstalledSha256 -New $SourceSha256 -DoApply:$Apply
exit $script:RefuteExitCode
