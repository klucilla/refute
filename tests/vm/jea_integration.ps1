# Integration test of a real JEA endpoint, in Windows PowerShell 5.1 on a GitHub-hosted
# Windows runner only (it runs as Administrator there, on a machine discarded after the
# job). It refuses to run anywhere else: it enables WinRM and registers session
# configurations, which a developer machine must never get from a test. The variables it
# checks guard against an accidental run; they do not authenticate the machine.
#
# It installs probe modules and registers disposable endpoints shaped like RefuteVm
# (RestrictedRemoteServer, RunAsVirtualAccount, AccessMode Local), then opens real
# sessions to localhost, to check the three causes the maintainer found on 2026-10-16:
#   1. with AccessMode Local, a localhost session needs -EnableNetworkAccess (without it
#      the connection is a network logon, which the endpoint denies);
#   2. JEA finds <module path>\<module>\RoleCapabilities\<name>.psrc only, never in a
#      version subfolder (a twin at the top of its module is the positive control);
#   3. RequiredVersion or GUID in ModulesToImport makes PowerShell call Get-Module in the
#      restricted session (it fails); by the manifest path, or by name, it imports.
# It also records the module path seen inside a JEA session (the roots the service
# searches). Prints one JSON object; tests/test_vm_jea_integration.py holds the
# assertions. It never deletes anything (the runner is discarded).
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2.0

$out = [ordered]@{ Ran = $false; Reason = ''; Sessions = [ordered]@{}; Roots = [ordered]@{} }
function Write-Result { $out | ConvertTo-Json -Depth 6 -Compress; exit 0 }

$isAdmin = ([System.Security.Principal.WindowsPrincipal][System.Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([System.Security.Principal.WindowsBuiltInRole]::Administrator)
if ($env:GITHUB_ACTIONS -ne 'true' -or $env:REFUTE_JEA_INTEGRATION -ne '1' -or $env:RUNNER_ENVIRONMENT -ne 'github-hosted') {
    $out.Reason = 'not a GitHub-hosted Actions run with REFUTE_JEA_INTEGRATION=1'; Write-Result
}
if ($PSVersionTable.PSEdition -ne 'Desktop' -or $PSVersionTable.PSVersion.Major -ne 5) { $out.Reason = 'not Windows PowerShell 5.1'; Write-Result }
if (-not $isAdmin) { $out.Reason = 'not Administrator'; Write-Result }
$out.Ran = $true

# WinRM on the runner (an ephemeral machine)
Enable-PSRemoting -Force -SkipNetworkProfileCheck | Out-Null

$modules = Join-Path $env:ProgramFiles 'WindowsPowerShell\Modules'
$account = "$env:COMPUTERNAME\$env:USERNAME"
$utf8 = New-Object System.Text.UTF8Encoding($false)
$guid = 'c3d6a0f1-8e2b-4a57-9f30-1b2c3d4e5f60'
$visible = "VisibleFunctions = @('Get-RefuteJeaProbe', 'Get-RefuteJeaModulePath')"

function New-ProbeModule([string]$Folder, [string]$Name, [hashtable]$RoleFiles) {
    # A module exporting Get-RefuteJeaProbe and Get-RefuteJeaModulePath (the module path
    # of the session process), with role capability files in $Folder.
    [void][System.IO.Directory]::CreateDirectory((Join-Path $Folder 'RoleCapabilities'))
    $code = "function Get-RefuteJeaProbe { 'probe-ok' }`r`nfunction Get-RefuteJeaModulePath { [Environment]::GetEnvironmentVariable('PSModulePath') }`r`nExport-ModuleMember -Function Get-RefuteJeaProbe, Get-RefuteJeaModulePath`r`n"
    [System.IO.File]::WriteAllText((Join-Path $Folder "$Name.psm1"), $code, $utf8)
    [System.IO.File]::WriteAllText((Join-Path $Folder "$Name.psd1"), "@{ RootModule = '$Name.psm1'; ModuleVersion = '0.1.0'; GUID = '$guid'; FunctionsToExport = @('Get-RefuteJeaProbe', 'Get-RefuteJeaModulePath') }`r`n", $utf8)
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
    $result = [ordered]@{ Opened = $false; Error = ''; ErrorId = ''; Commands = @(); Probe = ''; ModulePath = '' }
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
            $result.ModulePath = [string](Invoke-Command -Session $s -ScriptBlock ([scriptblock]::Create('Get-RefuteJeaModulePath')))
        } finally { Remove-PSSession -Session $s }
    } catch {
        $result.Error = (($_.Exception.Message -split "`r?`n") | Where-Object { $_ }) -join ' | '
        $result.ErrorId = [string]$_.FullyQualifiedErrorId
    }
    return $result
}

# module at the top of its folder: role capabilities by the manifest path, by name, and
# pinned by RequiredVersion, by GUID, and by both
$flat = Join-Path $modules 'RefuteJeaProbe'
$manifest = Join-Path $flat 'RefuteJeaProbe.psd1'
New-ProbeModule $flat 'RefuteJeaProbe' @{
    ProbeByPath     = "@{ ModulesToImport = @('$manifest'); $visible }"
    ProbeByName     = "@{ ModulesToImport = @('RefuteJeaProbe'); $visible }"
    # each version key alone (a GUID is only accepted next to a version key)
    ProbeByRequiredVersion = "@{ ModulesToImport = @(@{ ModuleName = 'RefuteJeaProbe'; RequiredVersion = '0.1.0' }); $visible }"
    ProbeByModuleVersion   = "@{ ModulesToImport = @(@{ ModuleName = 'RefuteJeaProbe'; ModuleVersion = '0.1.0' }); $visible }"
    ProbeByMaximumVersion  = "@{ ModulesToImport = @(@{ ModuleName = 'RefuteJeaProbe'; MaximumVersion = '0.1.0' }); $visible }"
    ProbeByModuleVersionGuid = "@{ ModulesToImport = @(@{ ModuleName = 'RefuteJeaProbe'; ModuleVersion = '0.1.0'; GUID = '$guid' }); $visible }"
    ProbeByRequiredVersionGuid = "@{ ModulesToImport = @(@{ ModuleName = 'RefuteJeaProbe'; RequiredVersion = '0.1.0'; GUID = '$guid' }); $visible }"
}
# the same role capability content in a version subfolder of one module, and at the top
# of another (the positive control of cause 2)
$sameRole = "@{ ModulesToImport = @('RefuteJeaProbe'); $visible }"
New-ProbeModule (Join-Path $modules 'RefuteJeaVersioned\0.1.0') 'RefuteJeaVersioned' @{ ProbeVersioned = $sameRole }
New-ProbeModule (Join-Path $modules 'RefuteJeaFlatTwin') 'RefuteJeaFlatTwin' @{ ProbeFlatTwin = $sameRole }

Register-Probe 'RefuteProbePath' 'ProbeByPath'
Register-Probe 'RefuteProbeName' 'ProbeByName'
foreach ($pin in 'RequiredVersion', 'ModuleVersion', 'MaximumVersion', 'ModuleVersionGuid', 'RequiredVersionGuid') {
    Register-Probe "RefuteProbe$pin" "ProbeBy$pin"
}
Register-Probe 'RefuteProbeSubfolder' 'ProbeVersioned'
Register-Probe 'RefuteProbeFlatTwin' 'ProbeFlatTwin'

$out.Sessions.PathWithNetworkAccess = Test-Session 'RefuteProbePath' $true
$out.Sessions.PathWithoutNetworkAccess = Test-Session 'RefuteProbePath' $false
$out.Sessions.NameWithNetworkAccess = Test-Session 'RefuteProbeName' $true
foreach ($pin in 'RequiredVersion', 'ModuleVersion', 'MaximumVersion', 'ModuleVersionGuid', 'RequiredVersionGuid') {
    $out.Sessions["Pin$pin"] = Test-Session "RefuteProbe$pin" $true
}
$out.Sessions.SubfolderWithNetworkAccess = Test-Session 'RefuteProbeSubfolder' $true
$out.Sessions.FlatTwinWithNetworkAccess = Test-Session 'RefuteProbeFlatTwin' $true

# the module roots of this machine, computed like Get-ModulePathRoots of the registration
# (machine PSModulePath, this process's PSModulePath, Program Files, System32, PSHOME)
$roots = @([Environment]::GetEnvironmentVariable('PSModulePath', 'Machine').Split(';')) +
    @([Environment]::GetEnvironmentVariable('PSModulePath', 'Process').Split(';')) +
    @($modules, (Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\Modules'), (Join-Path $PSHOME 'Modules'))
$out.Roots.Registration = @($roots | Where-Object { $_ } | ForEach-Object { $_.TrimEnd('\') } | Sort-Object -Unique)
$out.Roots.Session = @($out.Sessions.PathWithNetworkAccess.ModulePath.Split(';') | Where-Object { $_ } | ForEach-Object {
        [ordered]@{ Path = $_.TrimEnd('\'); Exists = (Test-Path -LiteralPath $_ -PathType Container) }
    })
Write-Result
