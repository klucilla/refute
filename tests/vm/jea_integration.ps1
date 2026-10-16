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
# It also records, from inside a JEA session, every root of the session's module path and
# the role capability files under each, next to the roots the registration searches
# (Get-RefuteRegistrationModuleRoots, the registration's own function). Prints one JSON
# object; tests/test_vm_jea_integration.py holds the assertions. It never deletes anything
# (the runner is discarded).
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
$visible = "VisibleFunctions = @('Get-RefuteJeaProbe', 'Get-RefuteJeaModuleRoots')"
# The probe functions (tests/vm/JeaProbe.psm1, checked on synthetic folders by
# tests/vm/vm_cases.ps1). Get-RefuteJeaModuleRoots runs inside the JEA session, as its
# virtual account, while the session is open, and reports each entry of the session's
# PSModulePath as written, its normalised root, whether it is present, absent or could not
# be read, and every <root>\<folder>\RoleCapabilities\*.psrc under it.
$probeCode = [System.IO.File]::ReadAllText((Join-Path $PSScriptRoot 'JeaProbe.psm1'))

function New-ProbeModule([string]$Folder, [string]$Name, [hashtable]$RoleFiles) {
    # A module exporting the probe functions, with role capability files in $Folder.
    [void][System.IO.Directory]::CreateDirectory((Join-Path $Folder 'RoleCapabilities'))
    [System.IO.File]::WriteAllText((Join-Path $Folder "$Name.psm1"), $probeCode, $utf8)
    [System.IO.File]::WriteAllText((Join-Path $Folder "$Name.psd1"), "@{ RootModule = '$Name.psm1'; ModuleVersion = '0.1.0'; GUID = '$guid'; FunctionsToExport = @('Get-RefuteJeaProbe', 'Get-RefuteJeaModuleRoots') }`r`n", $utf8)
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
    $result = [ordered]@{ Opened = $false; Error = ''; ErrorId = ''; Commands = @(); Probe = ''; Roots = '' }
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
            $result.Roots = [string](Invoke-Command -Session $s -ScriptBlock ([scriptblock]::Create('Get-RefuteJeaModuleRoots')))
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

# The relative entries of the session's module path (Codex review of #99): a role capability
# with a name of its own is placed only where the session resolves the first relative
# entry, and a real session to an endpoint that names it shows whether JEA's search finds
# it there (positive control); a capability placed in a folder on no module path must not
# be found (negative control). The positive control runs only when no absolute entry
# reaches that folder: neither an absolute entry of the session's module path nor one of
# the machine's or this host's module path (JEA finds <root>\<module>\RoleCapabilities, so
# only an entry equal to the folder could reach it). Applicable records why it ran or not.
$out.Relative = [ordered]@{
    Entry = ''; Resolved = ''; Absolute = @(); Exclusive = $null; Applicable = 'no relative entry'
    Control = $null; Nowhere = $null
}
$qualified = '^([A-Za-z]:\\|\\\\[^\\]+\\[^\\]+)'
function ConvertTo-ProbeFolder([string]$Path) {
    # the probe's normalisation (tests/vm/JeaProbe.psm1): full path, no trailing '\' except
    # on a drive root; '' for an entry that cannot be resolved
    try { $full = [System.IO.Path]::GetFullPath($Path).TrimEnd('\') } catch { return '' }
    if ($full -match '^[A-Za-z]:$') { $full = $full + '\' }
    return $full
}
$rootsText = [string]$out.Sessions.PathWithNetworkAccess.Roots
if ($rootsText) {
    $rows = @($rootsText.Split("`n"))
    $parsed = @($rows[1..($rows.Count - 1)] | ForEach-Object { , @($_.Split("`t")) })
    $absolute = [System.Collections.Generic.List[string]]::new()
    foreach ($row in $parsed) {
        if ($row[1] -match $qualified -and $row[3]) { $absolute.Add($row[3]) }
    }
    $hostPaths = @([Environment]::GetEnvironmentVariable('PSModulePath', 'Machine'), $env:PSModulePath)
    foreach ($entry in @($hostPaths | ForEach-Object { "$_".Split(';') } | Where-Object { $_ -match $qualified })) {
        $folder = ConvertTo-ProbeFolder $entry
        if ($folder) { $absolute.Add($folder) }
    }
    $out.Relative.Absolute = @($absolute | Sort-Object -Unique)
    $relative = @($parsed | Where-Object { $_[1] -notmatch $qualified })
    if ($relative.Count) {
        $out.Relative.Entry = $relative[0][1]
        $out.Relative.Resolved = $relative[0][3]
        if (-not $out.Relative.Resolved) {
            $out.Relative.Applicable = 'the relative entry cannot be resolved'
        } else {
            $same = @($absolute | Where-Object { $_ -ieq $out.Relative.Resolved })
            $out.Relative.Exclusive = ($same.Count -eq 0)
            if ($out.Relative.Exclusive) {
                New-ProbeModule (Join-Path $out.Relative.Resolved 'RefuteJeaRelative') 'RefuteJeaRelative' @{ ProbeRelative = $sameRole }
                Register-Probe 'RefuteProbeRelative' 'ProbeRelative'
                $out.Relative.Control = Test-Session 'RefuteProbeRelative' $true
                $out.Relative.Applicable = 'ran'
            } else {
                $out.Relative.Applicable = 'an absolute entry reaches the resolved folder'
            }
        }
    }
}
New-ProbeModule (Join-Path $env:TEMP 'refute-jea-nowhere\RefuteJeaNowhere') 'RefuteJeaNowhere' @{ ProbeNowhere = $sameRole }
Register-Probe 'RefuteProbeNowhere' 'ProbeNowhere'
$out.Relative.Nowhere = Test-Session 'RefuteProbeNowhere' $true

# The real RefuteVm endpoint, end to end (the maintainer's H.5 of 2026-10-16, after a fourth
# layer, 'Import-PowerShellDataFile' not recognized, was found on the machine): the module
# and its role capability from the repository, installed where the registration installs
# them (no version subfolder), with a test configuration (the repository's, with a VM name
# of its own; every path stays where Test-RefuteVmConfig requires it); an endpoint shaped
# like the real one (RestrictedRemoteServer, a virtual account in Hyper-V Administrators
# only, AccessMode Local); a session with -EnableNetworkAccess; Get-Command,
# Get-RefuteVmStatus and Invoke-RefuteVmOperation -Simulate, each as a literal command.
# The runner has the Hyper-V PowerShell module but not the service, so both calls stop at
# the module's first Hyper-V call, with the module's own message.
$out.RefuteVm = [ordered]@{ Opened = $false; Error = ''; Commands = @(); Status = $null; Simulate = $null }
$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$source = Join-Path $repoRoot 'scripts\vm\RefuteVm'
$target = Join-Path $modules 'RefuteVm'
[void][System.IO.Directory]::CreateDirectory((Join-Path $target 'RoleCapabilities'))
foreach ($file in 'RefuteVm.psd1', 'RefuteVm.psm1', 'RefuteVm.Core.ps1', 'RefuteVm.HyperV.ps1', 'RoleCapabilities\RefuteVmOperator.psrc') {
    Copy-Item -LiteralPath (Join-Path $source $file) -Destination (Join-Path $target $file)
}
$configText = [System.IO.File]::ReadAllText((Join-Path $source 'RefuteVm.Config.psd1'))
$testConfig = $configText.Replace("= 'refute-vm'", "= 'refute-ci-vm'")
if ($testConfig -eq $configText) { throw 'the test configuration was not written' }
[System.IO.File]::WriteAllText((Join-Path $target 'RefuteVm.Config.psd1'), $testConfig, $utf8)
$hyperVAdmins = (New-Object System.Security.Principal.SecurityIdentifier 'S-1-5-32-578').Translate([System.Security.Principal.NTAccount]).Value.Split('\')[-1]
$refutePssc = Join-Path $env:TEMP 'RefuteVmCi.pssc'
New-PSSessionConfigurationFile -Path $refutePssc -SessionType RestrictedRemoteServer -RunAsVirtualAccount `
    -RunAsVirtualAccountGroups $hyperVAdmins -RoleDefinitions @{ $account = @{ RoleCapabilities = 'RefuteVmOperator' } }
Register-PSSessionConfiguration -Name 'RefuteVmCi' -Path $refutePssc -AccessMode Local -Force | Out-Null

function Invoke-Literal($Session, [string]$Command) {
    # one literal command, the call shape of Invoke-RefuteVm.ps1
    $call = [ordered]@{ Ok = $false; Output = ''; Error = ''; ErrorId = ''; Exception = '' }
    try {
        $call.Output = [string](Invoke-Command -Session $Session -ScriptBlock ([scriptblock]::Create($Command)) -ErrorAction Stop)
        $call.Ok = $true
    } catch {
        $call.Error = (($_.Exception.Message -split "`r?`n") | Where-Object { $_ }) -join ' | '
        $call.ErrorId = [string]$_.FullyQualifiedErrorId
        $call.Exception = $_.Exception.GetType().FullName
    }
    return $call
}
try {
    $refuteSession = New-PSSession -ComputerName localhost -ConfigurationName 'RefuteVmCi' -EnableNetworkAccess -ErrorAction Stop
    $out.RefuteVm.Opened = $true
    try {
        $out.RefuteVm.Commands = @(Invoke-Command -Session $refuteSession -ScriptBlock { Get-Command } | ForEach-Object { [string]$_.Name } | Sort-Object)
        $out.RefuteVm.Status = Invoke-Literal $refuteSession 'Get-RefuteVmStatus'
        $out.RefuteVm.Simulate = Invoke-Literal $refuteSession 'Invoke-RefuteVmOperation -Operation SetHostPaths -Simulate'
    } finally { Remove-PSSession -Session $refuteSession }
} catch {
    $out.RefuteVm.Error = (($_.Exception.Message -split "`r?`n") | Where-Object { $_ }) -join ' | '
}

# the module roots the registration searches, from the function the registration itself
# calls (scripts/vm/RefuteRegistration.Core.ps1), not from a copy of its formula
$repo = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
. (Join-Path $repo 'scripts\vm\RefuteRegistration.Core.ps1')
$out.Roots.Registration = @(Get-RefuteRegistrationModuleRoots)
Write-Result
