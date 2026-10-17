# Synthetic cases of scripts/vm/Update-RefuteVmConfig.ps1 (#134), with no Administrator and
# nothing installed: the script is dot-sourced (it then runs nothing), the real
# RefuteRegistration.Core.ps1 is loaded, and the reads of the machine (the discovery set,
# the owner and writers of the configuration, the remoting sessions) are replaced by fakes
# that pass unless a case sets them to fail. The module folder is a temporary folder with 6
# files. Prints one JSON document; tests/test_vm_scripts.py checks it.
param([Parameter(Mandatory = $true)][string]$Root, [Parameter(Mandatory = $true)][string]$WorkDir)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2.0

. (Join-Path $Root 'scripts\vm\RefuteRegistration.Core.ps1')
. (Join-Path $Root 'scripts\vm\Update-RefuteVmConfig.ps1')

$script:Fake = @{}
function Reset-Fake {
    $script:Fake = @{ Discovery = @(); FailDiscoveryOnCall = 0; DiscoveryCalls = 0; Owner = $true; RealOwner = $false; Writers = @(); Sessions = @() }
}
$realOwner = ${function:Test-RefuteAllowedOwner}
function Get-RefuteJeaDiscoveryRoots { return @('C:\fake-root') }
function Get-RefuteDiscoveryProblems([string[]]$Roots) {
    $script:Fake.DiscoveryCalls++
    if ($script:Fake.FailDiscoveryOnCall -and $script:Fake.DiscoveryCalls -eq $script:Fake.FailDiscoveryOnCall) { return @('S-1-5-21-0 278 (fake late finding)') }
    return $script:Fake.Discovery
}
function Test-RefuteAllowedOwner([string]$Sid) {
    if ($script:Fake.RealOwner) { return (& $realOwner $Sid) }
    return $script:Fake.Owner
}
function Get-RefuteAceWriters([object[]]$Entries) { return $script:Fake.Writers }
function Get-CimInstance { param($ClassName, $Filter) return $script:Fake.Sessions }

$utf8 = New-Object System.Text.UTF8Encoding($false)
$oldText = "@{ ConfigVersion = 1 } # old`n"
$newText = "@{ ConfigVersion = 1 } # new`n"
$dir = Join-Path $WorkDir 'RefuteVm'
[void][System.IO.Directory]::CreateDirectory((Join-Path $dir 'RoleCapabilities'))
$installed = Join-Path $dir 'RefuteVm.Config.psd1'
foreach ($name in 'RefuteVm.psd1', 'RefuteVm.psm1', 'RefuteVm.Core.ps1', 'RefuteVm.HyperV.ps1', 'RoleCapabilities\RefuteVmOperator.psrc') {
    [System.IO.File]::WriteAllText((Join-Path $dir $name), "# $name`n", $utf8)
}
$source = Join-Path $WorkDir 'new.psd1'
[System.IO.File]::WriteAllText($source, $newText, $utf8)
$old = Get-RefuteBytesSha256 $utf8.GetBytes($oldText)
$new = Get-RefuteBytesSha256 $utf8.GetBytes($newText)

$cases = New-Object System.Collections.Generic.List[object]
function Invoke-Case([string]$Name, [scriptblock]$Setup, [switch]$Apply, [string]$OldHash = $old, [string]$SourcePath = $source) {
    Reset-Fake
    [System.IO.File]::WriteAllText($installed, $oldText, $utf8)
    $extra = Join-Path $dir 'extra.txt'
    if (Test-Path -LiteralPath $extra) { [System.IO.File]::Delete($extra) }
    if ($Setup) { & $Setup }
    $lines = @(Invoke-RefuteConfigUpdate -ModuleDir $dir -InstalledPath $installed -Source $SourcePath -Old $OldHash -New $new -DoApply:$Apply)
    $cases.Add([ordered]@{
            Name      = $Name
            Exit      = $script:RefuteExitCode
            Lines     = @($lines | ForEach-Object { [string]$_ })
            Installed = (Get-RefuteFileSha256Upper $installed)
            Calls     = $script:Fake.DiscoveryCalls
        })
}

Invoke-Case 'preview passes' $null
Invoke-Case 'apply passes' $null -Apply
Invoke-Case 'installed hash differs' $null -Apply -OldHash ('0' * 64)
Invoke-Case 'source hash differs' { [System.IO.File]::WriteAllText($source, "changed`n", $utf8) } -Apply
[System.IO.File]::WriteAllText($source, $newText, $utf8)
Invoke-Case 'a discovery finding' { $script:Fake.Discovery = @('S-1-5-21-0 278') } -Apply
Invoke-Case 'a remoting session' { $script:Fake.Sessions = @([pscustomobject]@{ ProcessId = 1 }) } -Apply
Invoke-Case 'seven files' { [System.IO.File]::WriteAllText((Join-Path $dir 'extra.txt'), "x`n", $utf8) } -Apply
Invoke-Case 'another writer' { $script:Fake.Writers = @('S-1-5-21-0 278') } -Apply
Invoke-Case 'real owner check on a user-owned file' { $script:Fake.RealOwner = $true } -Apply
Invoke-Case 'a finding after the write' { $script:Fake.FailDiscoveryOnCall = 3 } -Apply
Invoke-Case 'missing source' $null -Apply -SourcePath (Join-Path $WorkDir 'absent.psd1')

Reset-Fake
$none = @(Get-RefuteTargetProblems $dir $installed)
$script:Fake.Discovery = @('a', 'b')
$two = @(Get-RefuteTargetProblems $dir $installed)
$masked = @(
    (Format-RefuteReason "denied: $env:USERPROFILE\x and $env:USERNAME"),
    (Format-RefuteReason ("denied: " + $env:USERPROFILE.ToUpperInvariant() + "\x and " + $env:USERNAME.ToUpperInvariant())),
    (Format-RefuteReason 'denied: d:\users\Some.Other\file.txt'))
# checked here, so the account name never reaches the test output
$noAccountLeft = -not @($masked | Where-Object { $_.IndexOf($env:USERNAME, [System.StringComparison]::OrdinalIgnoreCase) -ge 0 -or $_.IndexOf('\Users\', [System.StringComparison]::OrdinalIgnoreCase) -ge 0 }).Count
$maskedForOutput = @($masked | ForEach-Object { $_.Replace($env:USERNAME, '') })
# whether the real owner check accepts the temporary file (an elevated runner can make
# Administrators the owner of what it creates)
$ownerAllowed = [bool](& $realOwner (Get-Acl -LiteralPath $installed).GetOwner([System.Security.Principal.SecurityIdentifier]).Value)

[ordered]@{
    OwnerAllowed   = $ownerAllowed
    Old            = $old
    New            = $new
    Cases          = $cases.ToArray()
    NoFindingCount = $none.Count
    TwoFindings    = $two
    Masked         = $maskedForOutput
    NoAccountLeft  = [bool]$noAccountLeft
} | ConvertTo-Json -Depth 6
