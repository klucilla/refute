# Integration test of a real JEA endpoint, in Windows PowerShell 5.1 on a GitHub Actions
# Windows runner only (it runs as Administrator there, on a machine discarded after the
# job). It refuses to run anywhere else: it enables WinRM and registers session
# configurations, which a developer machine must never get from a test.
#
# It installs a probe module and registers disposable endpoints shaped like RefuteVm
# (RestrictedRemoteServer, RunAsVirtualAccount, AccessMode Local), then opens real
# sessions to localhost, to check the three causes the maintainer found on 2026-10-16:
#   1. with AccessMode Local, a localhost session needs -EnableNetworkAccess (without it
#      the connection is a network logon, which the endpoint denies);
#   2. JEA finds <module path>\<module>\RoleCapabilities\<name>.psrc only, never in a
#      version subfolder;
#   3. ModulesToImport with RequiredVersion and GUID makes PowerShell call Get-Module in
#      the restricted session (it fails); by the manifest path it imports.
# Prints one JSON object; tests/test_vm_jea_integration.py holds the assertions. It never
# deletes anything (the runner is discarded).
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2.0

$out = [ordered]@{ Ran = $false; Reason = ''; Sessions = [ordered]@{} }
function Write-Result { $out | ConvertTo-Json -Depth 6 -Compress; exit 0 }

$isAdmin = ([System.Security.Principal.WindowsPrincipal][System.Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([System.Security.Principal.WindowsBuiltInRole]::Administrator)
if ($env:GITHUB_ACTIONS -ne 'true' -or $env:REFUTE_JEA_INTEGRATION -ne '1') { $out.Reason = 'not a GitHub Actions run with REFUTE_JEA_INTEGRATION=1'; Write-Result }
if ($PSVersionTable.PSEdition -ne 'Desktop' -or $PSVersionTable.PSVersion.Major -ne 5) { $out.Reason = 'not Windows PowerShell 5.1'; Write-Result }
if (-not $isAdmin) { $out.Reason = 'not Administrator'; Write-Result }
$out.Ran = $true

# WinRM on the runner (an ephemeral machine)
Enable-PSRemoting -Force -SkipNetworkProfileCheck | Out-Null

$modules = Join-Path $env:ProgramFiles 'WindowsPowerShell\Modules'
$account = "$env:COMPUTERNAME\$env:USERNAME"
$utf8 = New-Object System.Text.UTF8Encoding($false)

function New-ProbeModule([string]$Folder, [string]$Name, [hashtable]$RoleFiles) {
    # A module exporting Get-RefuteJeaProbe, with role capability files in $Folder.
    [void][System.IO.Directory]::CreateDirectory((Join-Path $Folder 'RoleCapabilities'))
    [System.IO.File]::WriteAllText((Join-Path $Folder "$Name.psm1"), "function Get-RefuteJeaProbe { 'probe-ok' }`r`nExport-ModuleMember -Function Get-RefuteJeaProbe`r`n", $utf8)
    [System.IO.File]::WriteAllText((Join-Path $Folder "$Name.psd1"), "@{ RootModule = '$Name.psm1'; ModuleVersion = '0.1.0'; GUID = 'c3d6a0f1-8e2b-4a57-9f30-1b2c3d4e5f60'; FunctionsToExport = @('Get-RefuteJeaProbe') }`r`n", $utf8)
    foreach ($role in $RoleFiles.Keys) {
        [System.IO.File]::WriteAllText((Join-Path $Folder "RoleCapabilities\$role.psrc"), $RoleFiles[$role], $utf8)
    }
}

function Register-Probe([string]$Endpoint, [string]$Role) {
    $pssc = Join-Path $env:TEMP "$Endpoint.pssc"
    New-PSSessionConfigurationFile -Path $pssc -SessionType RestrictedRemoteServer -RunAsVirtualAccount `
        -RoleDefinitions @{ $account = @{ RoleCapabilities = $Role } }
    Register-PSSessionConfiguration -Name $Endpoint -Path $pssc -AccessMode Local -Force | Out-Null
}

function Test-Session([string]$Endpoint, [bool]$NetworkAccess) {
    $result = [ordered]@{ Opened = $false; Error = ''; Commands = @(); Probe = '' }
    try {
        if ($NetworkAccess) {
            $s = New-PSSession -ComputerName localhost -ConfigurationName $Endpoint -EnableNetworkAccess -ErrorAction Stop
        } else {
            $s = New-PSSession -ComputerName localhost -ConfigurationName $Endpoint -ErrorAction Stop
        }
        $result.Opened = $true
        try {
            $result.Commands = @(Invoke-Command -Session $s -ScriptBlock { Get-Command } | ForEach-Object { [string]$_.Name } | Sort-Object)
            # the call shape of Invoke-RefuteVm.ps1: a script block built from one literal command
            $result.Probe = [string](Invoke-Command -Session $s -ScriptBlock ([scriptblock]::Create('Get-RefuteJeaProbe')))
        } finally { Remove-PSSession -Session $s }
    } catch {
        $result.Error = (($_.Exception.Message -split "`r?`n") | Where-Object { $_ }) -join ' | '
    }
    return $result
}

# module at the top of its folder: one role capability by the manifest path, one pinned
# by RequiredVersion and GUID
$flat = Join-Path $modules 'RefuteJeaProbe'
$manifest = Join-Path $flat 'RefuteJeaProbe.psd1'
New-ProbeModule $flat 'RefuteJeaProbe' @{
    ProbeByPath    = "@{ ModulesToImport = @('$manifest'); VisibleFunctions = @('Get-RefuteJeaProbe') }"
    ProbeByVersion = "@{ ModulesToImport = @(@{ ModuleName = 'RefuteJeaProbe'; RequiredVersion = '0.1.0'; GUID = 'c3d6a0f1-8e2b-4a57-9f30-1b2c3d4e5f60' }); VisibleFunctions = @('Get-RefuteJeaProbe') }"
    ProbeByName    = "@{ ModulesToImport = @('RefuteJeaProbe'); VisibleFunctions = @('Get-RefuteJeaProbe') }"
}
# a second module with its role capability only in a version subfolder
$versioned = Join-Path $modules 'RefuteJeaVersioned\0.1.0'
New-ProbeModule $versioned 'RefuteJeaVersioned' @{
    ProbeVersioned = "@{ ModulesToImport = @('RefuteJeaProbe'); VisibleFunctions = @('Get-RefuteJeaProbe') }"
}

Register-Probe 'RefuteProbePath' 'ProbeByPath'
Register-Probe 'RefuteProbeVersion' 'ProbeByVersion'
Register-Probe 'RefuteProbeName' 'ProbeByName'
Register-Probe 'RefuteProbeSubfolder' 'ProbeVersioned'

$out.Sessions.PathWithNetworkAccess = Test-Session 'RefuteProbePath' $true
$out.Sessions.PathWithoutNetworkAccess = Test-Session 'RefuteProbePath' $false
$out.Sessions.VersionWithNetworkAccess = Test-Session 'RefuteProbeVersion' $true
$out.Sessions.NameWithNetworkAccess = Test-Session 'RefuteProbeName' $true
$out.Sessions.SubfolderWithNetworkAccess = Test-Session 'RefuteProbeSubfolder' $true
Write-Result
