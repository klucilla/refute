<#
.SYNOPSIS
Removes the WinRM listener "*+HTTP" (every address, HTTP), with a backup, before the JEA
endpoint is registered (WP6). Decided by the maintainer on 2026-10-15. Run by the
maintainer, in Windows PowerShell 5.1 started as Administrator, with
PSModuleAnalysisCachePath=nul in its environment (scripts/vm/README.md).

.DESCRIPTION
Without -Apply nothing is changed: the script reads the WinRM service state and every
listener key under HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\WSMAN\Listener with all
its values (port, hostname, certificate thumbprint, enabled, URL prefix), prints what
the removal would do and a PreviewSha256 of that list. With -Apply -PreviewSha256 <hash>
it recomputes the list, refuses if it differs from the preview, and then, in this
order, stopping at the first problem:

  1. creates C:\ProgramData\RefuteVm-backup (owner Administrators; only SYSTEM and
     Administrators have access), unless it exists with that protection;
  2. exports the key "*+HTTP" with reg.exe to a .reg file there (the file must not exist)
     and checks that the export holds exactly that key;
  3. checks again that the WinRM service is stopped, and deletes only the key "*+HTTP";
  4. checks that the key is gone, that every remaining listener is HTTP on 127.0.0.1 or
     ::1, and that the WinRM service is still stopped.

The WinRM service is never started, stopped or reconfigured: the script refuses to run
unless it is already stopped. No other listener is touched: if a listener other than
"*+HTTP" is not loopback HTTP, the script refuses (the maintainer decides).
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

$ListenerRoot = 'SOFTWARE\Microsoft\Windows\CurrentVersion\WSMAN\Listener'
$Target = '*+HTTP'
$TargetRegPath = "HKEY_LOCAL_MACHINE\$ListenerRoot\$Target"
$BackupRoot = 'C:\ProgramData\RefuteVm-backup'
$BackupFile = Join-Path $BackupRoot 'WSMAN-Listener-star-HTTP.reg'
$SidAdmins = 'S-1-5-32-544'
$SidSystem = 'S-1-5-18'
$RegExe = Join-Path $env:SystemRoot 'System32\reg.exe'

. (Join-Path $PSScriptRoot 'RefuteRegistration.Core.ps1')

function Read-RefuteListeners {
    # Every listener key with its values, read-only; an unreadable key is an error.
    $root = [Microsoft.Win32.Registry]::LocalMachine.OpenSubKey($ListenerRoot)
    if (-not $root) { return [ordered]@{} }
    try {
        $out = [ordered]@{}
        foreach ($name in @($root.GetSubKeyNames() | Sort-Object)) {
            $key = $root.OpenSubKey($name)
            try {
                $values = [ordered]@{}
                foreach ($v in @($key.GetValueNames() | Sort-Object)) { $values[$v] = [string]$key.GetValue($v) }
                $out[$name] = $values
            } finally { $key.Close() }
        }
        return $out
    } finally { $root.Close() }
}

function Get-RefuteBackupProblems {
    # The backup folder, when it exists, must be owned by Administrators and give access to
    # SYSTEM and Administrators only, with inheritance removed.
    if (-not (Test-Path -LiteralPath $BackupRoot)) { return @() }
    $acl = Get-Acl -LiteralPath $BackupRoot
    $found = @()
    $owner = (New-Object System.Security.Principal.NTAccount $acl.Owner).Translate([System.Security.Principal.SecurityIdentifier]).Value
    if ($owner -ne $SidAdmins) { $found += "$BackupRoot is not owned by Administrators" }
    if (-not $acl.AreAccessRulesProtected) { $found += "$BackupRoot inherits permissions" }
    foreach ($rule in $acl.Access) {
        $sid = $rule.IdentityReference.Translate([System.Security.Principal.SecurityIdentifier]).Value
        if (@($SidAdmins, $SidSystem) -notcontains $sid) { $found += "$BackupRoot gives access to $($rule.IdentityReference)" }
    }
    return $found
}

# ---- preconditions ------------------------------------------------------------------
$problems = New-Object System.Collections.Generic.List[string]
$isAdmin = ([System.Security.Principal.WindowsPrincipal][System.Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([System.Security.Principal.WindowsBuiltInRole]::Administrator)
if ($PSVersionTable.PSEdition -ne 'Desktop' -or $PSVersionTable.PSVersion.Major -ne 5) { $problems.Add('run in Windows PowerShell 5.1 (powershell.exe)') }
if (-not $isAdmin) { $problems.Add('run in a PowerShell started as Administrator (also for the preview: the listener keys are protected)') }
if ($Apply -and -not $PreviewSha256) { $problems.Add('-Apply needs -PreviewSha256 from a preview run') }
$winrm = Get-Service -Name WinRM
if ([string]$winrm.Status -ne 'Stopped') { $problems.Add("the WinRM service is $($winrm.Status); it must be stopped (this script never starts or stops it)") }
$listeners = [ordered]@{}
try { $listeners = Read-RefuteListeners } catch { $problems.Add("cannot read the WinRM listener keys: $($_.Exception.Message)") }
$removal = Get-RefuteListenerRemoval -Names @($listeners.Keys) -Target $Target
if (-not $removal.TargetPresent) { $problems.Add("there is no listener key $Target") }
if (@($removal.ForeignRemaining).Count) { $problems.Add('other listeners are not HTTP on loopback and would remain: ' + ($removal.ForeignRemaining -join ', ') + ' (the maintainer decides; this script removes only ' + $Target + ')') }
# a backup folder that only administrators can read, met by a preview run as a normal
# user, is a listed problem instead of an error that stops the preview
try {
    if (Test-Path -LiteralPath $BackupFile -ErrorAction Stop) { $problems.Add("$BackupFile already exists (never overwritten)") }
} catch { $problems.Add("$BackupFile cannot be read: $($_.Exception.Message)") }
$backupProblems = @()
try { $backupProblems = @(Get-RefuteBackupProblems) } catch { $problems.Add("cannot read the ACL of $BackupRoot : $($_.Exception.Message)") }
foreach ($p in $backupProblems) { $problems.Add($p) }

# ---- the change list (preview) ---------------------------------------------------------
$lines = New-Object System.Collections.Generic.List[string]
$lines.Add("WinRM service: $($winrm.Status), startup $($winrm.StartType) (never changed by this script)")
$lines.Add("Listener keys under HKLM\$ListenerRoot :")
if ($listeners.Count) {
    foreach ($name in $listeners.Keys) {
        $lines.Add("  $name")
        foreach ($v in $listeners[$name].Keys) { $lines.Add("      $v = $($listeners[$name][$v])") }
    }
} else { $lines.Add('  none') }
$lines.Add("1. Backup folder $BackupRoot : " + $(if (Test-Path -LiteralPath $BackupRoot) { 'exists, protected (checked)' } else { 'create, owner Administrators, access SYSTEM and Administrators only, inheritance removed' }))
$lines.Add("2. Export $TargetRegPath with reg.exe to $BackupFile (must not exist) and check the export holds exactly that key")
$lines.Add("3. Check the WinRM service is stopped, then delete only the key $Target")
$lines.Add('4. Check the key is gone, every remaining listener is HTTP on 127.0.0.1 or ::1 (remaining: ' + $(if (@($removal.Remaining).Count) { $removal.Remaining -join ', ' } else { 'none' }) + '), and WinRM is still stopped')
$sha = [System.Security.Cryptography.SHA256]::Create()
$previewHash = -join ($sha.ComputeHash([System.Text.Encoding]::UTF8.GetBytes(($lines -join "`n"))) | ForEach-Object { $_.ToString('x2') })
$sha.Dispose()

Write-Output '== Removal of the WinRM listener *+HTTP =='
Write-Output ('Mode: ' + $(if ($Apply) { 'APPLY' } else { 'preview (no change)' }))
foreach ($line in $lines) { Write-Output $line }
Write-Output "PreviewSha256: $previewHash"
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
    # 1. backup folder
    if (-not (Test-Path -LiteralPath $BackupRoot)) {
        $acl = New-Object System.Security.AccessControl.DirectorySecurity
        $acl.SetAccessRuleProtection($true, $false)
        $acl.SetOwner((New-Object System.Security.Principal.SecurityIdentifier $SidAdmins))
        foreach ($sid in $SidSystem, $SidAdmins) {
            $acl.AddAccessRule((New-Object System.Security.AccessControl.FileSystemAccessRule(
                        (New-Object System.Security.Principal.SecurityIdentifier $sid), 'FullControl',
                        [System.Security.AccessControl.InheritanceFlags]'ContainerInherit, ObjectInherit',
                        [System.Security.AccessControl.PropagationFlags]::None,
                        [System.Security.AccessControl.AccessControlType]::Allow)))
        }
        [void][System.IO.Directory]::CreateDirectory($BackupRoot, $acl)
        $done.Add("backup folder $BackupRoot created")
    }
    $check = @(Get-RefuteBackupProblems)
    if ($check.Count) { throw ('the backup folder is not protected: ' + ($check -join '; ')) }
    # 2. export
    $exportOutput = & $RegExe export $TargetRegPath $BackupFile 2>&1
    if ($LASTEXITCODE -ne 0) { throw "reg.exe export failed with exit code $LASTEXITCODE : $exportOutput" }
    $done.Add("key exported to $BackupFile")
    $exported = [System.IO.File]::ReadAllText($BackupFile)
    if (-not (Test-RefuteRegExport -Text $exported -KeyPath $TargetRegPath)) { throw "the export $BackupFile does not hold exactly the key $TargetRegPath" }
    # 3. delete only the target key, with WinRM stopped
    if ([string](Get-Service -Name WinRM).Status -ne 'Stopped') { throw 'the WinRM service is no longer stopped' }
    $root = [Microsoft.Win32.Registry]::LocalMachine.OpenSubKey($ListenerRoot, $true)
    try { $root.DeleteSubKeyTree($Target) } finally { $root.Close() }
    $done.Add("key $Target deleted")
    # 4. checks
    $after = Read-RefuteListeners
    $left = Get-RefuteListenerRemoval -Names @($after.Keys) -Target $Target
    if ($left.TargetPresent) { throw "the key $Target is still present" }
    if (@($left.ForeignRemaining).Count) { throw ('listeners other than HTTP on loopback remain: ' + ($left.ForeignRemaining -join ', ')) }
    if ([string](Get-Service -Name WinRM).Status -ne 'Stopped') { throw 'the WinRM service is no longer stopped' }
} catch {
    Write-Output "STOPPED: $($_.Exception.Message)"
    Write-Output ('Already done: ' + $(if ($done.Count) { $done -join '; ' } else { 'nothing' }))
    exit 2
}
Write-Output ('Done: ' + ($done -join '; '))
Write-Output ('Remaining listener keys: ' + $(if (@($left.Remaining).Count) { $left.Remaining -join ', ' } else { 'none' }))
Write-Output "Backup: $BackupFile (SHA-256 $((Get-FileHash -LiteralPath $BackupFile -Algorithm SHA256).Hash.ToLowerInvariant()))"
