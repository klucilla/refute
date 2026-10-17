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
function Write-Result { $out | ConvertTo-Json -Depth 8 -Compress; exit 0 }

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
# The data folders (Log, State) are created with the ACL the registration gives them. On a
# host without the Hyper-V service both calls stop at the module's first Hyper-V call, with
# the module's own message; the windows-2025 runner has the service (run 38934817010 of
# 2026-10-16 got past the observation), so both calls run to their end there and the
# simulation writes its record, which is read back. Afterwards the module folder is moved
# out of the module path (never deleted), so that later tests on the runner find no
# RefuteVmOperator role capability.
$out.RefuteVm = [ordered]@{ Opened = $false; Error = ''; Commands = @(); Status = $null; Simulate = $null; Private = [ordered]@{}; Vmms = $false; LogRecords = @(); Account = $account }
# whether this host has the Virtual Machine Management service (the module's own message
# for a host without Hyper-V depends on it)
$vmmsKey = [Microsoft.Win32.Registry]::LocalMachine.OpenSubKey('SYSTEM\CurrentControlSet\Services\vmms')
if ($vmmsKey) { $out.RefuteVm.Vmms = $true; $vmmsKey.Close() }
$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$source = Join-Path $repoRoot 'scripts\vm\RefuteVm'
$target = Join-Path $modules 'RefuteVm'
# everything from the copy of the module to the reading of the log runs inside this try:
# its finally moves the module out of the module path, also when a step fails (Codex
# review of #118, round 2)
try {
    [void][System.IO.Directory]::CreateDirectory((Join-Path $target 'RoleCapabilities'))
    foreach ($file in 'RefuteVm.psd1', 'RefuteVm.psm1', 'RefuteVm.Core.ps1', 'RefuteVm.HyperV.ps1', 'RoleCapabilities\RefuteVmOperator.psrc') {
        Copy-Item -LiteralPath (Join-Path $source $file) -Destination (Join-Path $target $file)
    }
    $configText = [System.IO.File]::ReadAllText((Join-Path $source 'RefuteVm.Config.psd1'))
    $testConfig = $configText.Replace("= 'refute-vm'", "= 'refute-ci-vm'")
    if ($testConfig -eq $configText) { throw 'the test configuration was not written' }
    [System.IO.File]::WriteAllText((Join-Path $target 'RefuteVm.Config.psd1'), $testConfig, $utf8)
    $hyperVAdmins = (New-Object System.Security.Principal.SecurityIdentifier 'S-1-5-32-578').Translate([System.Security.Principal.NTAccount]).Value.Split('\')[-1]
    # the data folders, as Register-RefuteVmEndpoint.ps1 creates them: owner Administrators,
    # inheritance removed; SYSTEM and Administrators full control, Hyper-V Administrators
    # modify, Users read
    $operationLog = 'C:\ProgramData\RefuteVm\Log\operations.jsonl'
    foreach ($folder in 'C:\ProgramData\RefuteVm\Log', 'C:\ProgramData\RefuteVm\State') {
        [void][System.IO.Directory]::CreateDirectory($folder)
        $acl = New-Object System.Security.AccessControl.DirectorySecurity
        $acl.SetOwner((New-Object System.Security.Principal.SecurityIdentifier 'S-1-5-32-544'))
        $acl.SetAccessRuleProtection($true, $false)
        $inherit = [System.Security.AccessControl.InheritanceFlags]'ContainerInherit, ObjectInherit'
        foreach ($entry in @(@('S-1-5-18', 'FullControl'), @('S-1-5-32-544', 'FullControl'), @('S-1-5-32-578', 'Modify'), @('S-1-5-32-545', 'ReadAndExecute'))) {
            $acl.AddAccessRule((New-Object System.Security.AccessControl.FileSystemAccessRule (
                        (New-Object System.Security.Principal.SecurityIdentifier $entry[0]), [System.Security.AccessControl.FileSystemRights]$entry[1], $inherit,
                        [System.Security.AccessControl.PropagationFlags]::None, [System.Security.AccessControl.AccessControlType]::Allow)))
        }
        Set-Acl -LiteralPath $folder -AclObject $acl
    }
    $refutePssc = Join-Path $env:TEMP 'RefuteVmCi.pssc'
    $refuteTranscripts = Join-Path $env:TEMP 'RefuteVmCi-transcripts'
    [void][System.IO.Directory]::CreateDirectory($refuteTranscripts)
    New-PSSessionConfigurationFile -Path $refutePssc -SessionType RestrictedRemoteServer -RunAsVirtualAccount `
        -RunAsVirtualAccountGroups $hyperVAdmins -TranscriptDirectory $refuteTranscripts `
        -RoleDefinitions @{ $account = @{ RoleCapabilities = 'RefuteVmOperator' } }
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
            # negative controls (Codex review of #118): the commands the imports bring for the
            # module's functions cannot be called by the connecting account, by name or by a
            # module-qualified name; all are read-only, so a failure here changes nothing
            foreach ($private in 'Get-FileHash', 'Import-PowerShellDataFile', 'Get-VMHost', 'Microsoft.PowerShell.Utility\Get-FileHash',
                'Microsoft.PowerShell.Utility\Import-PowerShellDataFile', 'Hyper-V\Get-VMHost', 'Get-Module', 'RefuteVm\Get-RefuteVmModuleFiles') {
                $out.RefuteVm.Private[$private] = Invoke-Literal $refuteSession $private
            }
        } finally { Remove-PSSession -Session $refuteSession }
    } catch {
        $out.RefuteVm.Error = (($_.Exception.Message -split "`r?`n") | Where-Object { $_ }) -join ' | '
    }
    if (Test-Path -LiteralPath $operationLog -PathType Leaf) {
        $out.RefuteVm.LogRecords = @([System.IO.File]::ReadAllLines($operationLog) | Where-Object { $_ })
    }

    # SetHostPaths for real, through the endpoint, under each version of the VM tree ACL
    # (Codex review of #126: the simulation above cannot show whether the virtual account
    # may change the host paths; on 2026-10-16 the real call failed on the maintainer's host
    # with access denied under version 1). Only where the runner has the vmms service, and
    # only when C:\Hyper-V does not exist before the test. The tree is created as the
    # registration creates it; version 1 is tried first, then version 1 with ChangePermissions
    # only, then version 2, each from the original host paths and in a new session (a new
    # virtual account, as on the host): the simulation, then the real call with its
    # PlanSha256. Afterwards the host paths stay as the last call left them: the runner is
    # discarded after the job, and nothing is deleted.
    $out.RefuteVm.HostPaths = [ordered]@{ Ran = $false; Reason = ''; Original = $null; MembersBefore = @(); Attempts = [ordered]@{} }
    if (-not $out.RefuteVm.Vmms) { $out.RefuteVm.HostPaths.Reason = 'the runner has no vmms service' }
    elseif (Test-Path -LiteralPath 'C:\Hyper-V') { $out.RefuteVm.HostPaths.Reason = 'C:\Hyper-V exists before the test' }
    else {
        $out.RefuteVm.HostPaths.Ran = $true
        . (Join-Path $repoRoot 'scripts\vm\RefuteRegistration.Core.ps1')
        Import-Module Hyper-V
        function Get-HostPathsCim {
            # The host paths read from the service's settings through CIM, on every call:
            # the Hyper-V module of this process can keep the VMHost object it read first
            # (run 38978769925: Get-VMHost here still showed the old paths after the session
            # had set and observed the new ones)
            $settings = @(Get-CimInstance -Namespace 'root\virtualization\v2' -ClassName 'Msvm_VirtualSystemManagementServiceSettingData' -ErrorAction Stop)
            if ($settings.Count -ne 1) { throw "expected one instance of the service settings, found $($settings.Count)" }
            $read = [ordered]@{ Utc = [DateTime]::UtcNow.ToString('yyyy-MM-ddTHH:mm:ss.fffZ'); VirtualMachinePath = [string]$settings[0].DefaultExternalDataRoot; VirtualHardDiskPath = [string]$settings[0].DefaultVirtualHardDiskPath }
            if (-not $read.VirtualMachinePath -or -not $read.VirtualHardDiskPath) { throw 'the service settings hold an empty default path' }
            return $read
        }
        function Get-HostPathsNewProcess {
            # Get-VMHost in a new powershell.exe, which has no object read before
            $text = & powershell.exe -NoProfile -NonInteractive -Command '$h = Hyper-V\Get-VMHost; $h.VirtualMachinePath + [char]124 + $h.VirtualHardDiskPath'
            $parts = ([string]($text | Select-Object -Last 1)).Split([char]124)
            return [ordered]@{ Utc = [DateTime]::UtcNow.ToString('yyyy-MM-ddTHH:mm:ss.fffZ'); VirtualMachinePath = $parts[0]; VirtualHardDiskPath = $(if ($parts.Count -gt 1) { $parts[1] } else { '' }) }
        }
        function Get-HyperVAdminSids {
            return @(Get-LocalGroupMember -SID 'S-1-5-32-578' -ErrorAction Stop | ForEach-Object { [string]$_.SID.Value } | Sort-Object)
        }
        $out.RefuteVm.HostPaths.MembersBefore = @(Get-HyperVAdminSids)
        $out.RefuteVm.HostPaths.Original = Get-HostPathsCim
        $vmTree = 'C:\Hyper-V'
        [void][System.IO.Directory]::CreateDirectory($vmTree)
        Set-Acl -LiteralPath $vmTree -AclObject (New-RefuteFolderAcl @(Get-RefuteVmTreeAclSpec -Version 1))
        foreach ($folder in 'C:\Hyper-V\Virtual Hard Disks', 'C:\Hyper-V\refute-vm', 'C:\Hyper-V\refute-vm\media') { [void][System.IO.Directory]::CreateDirectory($folder) }
        # three trees: version 1; version 1 with ChangePermissions for Hyper-V Administrators and
        # no Virtual Machines entries (the maintainer's preference, if it is enough); version 2
        $changePermissionsOnly = @(Get-RefuteVmTreeAclSpec -Version 1 | ForEach-Object {
                $entry = [ordered]@{}; foreach ($k in $_.Keys) { $entry[$k] = $_[$k] }
                if ($entry.Sid -eq 'S-1-5-32-578') { $entry.Rights = 'Modify, ChangePermissions' }
                $entry
            })
        $trees = [ordered]@{
            Version1              = @(Get-RefuteVmTreeAclSpec -Version 1)
            ChangePermissionsOnly = $changePermissionsOnly
            Version2              = @(Get-RefuteVmTreeAclSpec -Version 2)
        }
        foreach ($name in @($trees.Keys)) {
            $attempt = [ordered]@{ Tree = $name; Restored = $null; Baseline = $null; RootBefore = @(); TreeProblems = @(); Simulate = $null; Real = $null; Error = ''; MembersDuringSession = @(); SessionHostsBefore = @(); SessionHostsDuringSession = @(); HostAfter = $null; HostAfterNewProcess = $null; HostAfterModule = $null; RootAfter = @(); TreeProblemsAfter = @() }
            $spec = $trees[$name]
            # each attempt starts from the original host paths: the harness, as Administrator,
            # puts them back if an earlier attempt changed them, and checks it through CIM
            $original = $out.RefuteVm.HostPaths.Original
            $now = Get-HostPathsCim
            if ($now.VirtualMachinePath -ne $original.VirtualMachinePath -or $now.VirtualHardDiskPath -ne $original.VirtualHardDiskPath) {
                Set-VMHost -VirtualMachinePath $original.VirtualMachinePath -VirtualHardDiskPath $original.VirtualHardDiskPath -ErrorAction Stop
                $now = Get-HostPathsCim
                $attempt.Restored = $now
            }
            # the baseline of this attempt, read through CIM: both paths must be the original ones
            $attempt.Baseline = $now
            if ($now.VirtualMachinePath -ne $original.VirtualMachinePath -or $now.VirtualHardDiskPath -ne $original.VirtualHardDiskPath) {
                throw "the host paths could not be put back before the attempt $name"
            }
            Set-Acl -LiteralPath $vmTree -AclObject (New-RefuteFolderAcl $spec)
            $attempt.RootBefore = @(ConvertTo-RefuteAclRules (Get-Acl -LiteralPath $vmTree))
            # the whole tree before the call (Codex review of #126, round 2): the root holds
            # exactly this version and every folder below inherits exactly what it passes
            # down, so nothing an earlier attempt left on the tree takes part in this one
            $attempt.TreeProblems = @(Compare-RefuteVmTreeAcl -Acl (Get-Acl -LiteralPath $vmTree) -Spec $spec)
            foreach ($below in @(@('C:\Hyper-V\Virtual Hard Disks', 1), @('C:\Hyper-V\refute-vm', 1), @('C:\Hyper-V\refute-vm\media', 2))) {
                $attempt.TreeProblems += @(Compare-RefuteVmTreeBelow -Acl (Get-Acl -LiteralPath $below[0]) -Spec $spec -Depth $below[1] | ForEach-Object { "$($below[0]): $_" })
            }
            # the wsmprovhost.exe processes before this attempt's session (earlier sessions may
            # still be closing): the session must add one
            $attempt.SessionHostsBefore = @(Get-Process -Name 'wsmprovhost' -ErrorAction SilentlyContinue | ForEach-Object { [string]$_.Id })
            try {
                $hostSession = New-PSSession -ComputerName localhost -ConfigurationName 'RefuteVmCi' -EnableNetworkAccess -ErrorAction Stop
                try {
                    # while this session is open: the members of Hyper-V Administrators
                    # (recorded; run 38982160054 showed the virtual account is not listed),
                    # and the wsmprovhost.exe processes, the positive control of the
                    # open-session check of Set-RefuteVmTreeAcl.ps1 (a failure to read either
                    # goes to the attempt's Error, never into a list)
                    $attempt.MembersDuringSession = @(Get-HyperVAdminSids)
                    $attempt.SessionHostsDuringSession = @(Get-Process -Name 'wsmprovhost' -ErrorAction Stop | ForEach-Object { [string]$_.Id })
                    $attempt.Simulate = Invoke-Literal $hostSession 'Invoke-RefuteVmOperation -Operation SetHostPaths -Simulate'
                    if ($attempt.Simulate.Ok) {
                        $planSha = [string](ConvertFrom-Json $attempt.Simulate.Output).PlanSha256
                        if ($planSha -cnotmatch '^[0-9a-f]{64}$') { throw "no PlanSha256 in the simulation: $planSha" }
                        $attempt.Real = Invoke-Literal $hostSession "Invoke-RefuteVmOperation -Operation SetHostPaths -PlanSha256 $planSha"
                    }
                } finally { Remove-PSSession -Session $hostSession }
            } catch {
                $attempt.Error = (($_.Exception.Message -split "`r?`n") | Where-Object { $_ }) -join ' | '
            }
            # the host paths after the call, three ways: CIM (decides), Get-VMHost in a new
            # process, and Get-VMHost in this process, which read the host before
            $attempt.HostAfter = Get-HostPathsCim
            $attempt.HostAfterNewProcess = Get-HostPathsNewProcess
            $vmHost = Get-VMHost
            $attempt.HostAfterModule = [ordered]@{ Utc = [DateTime]::UtcNow.ToString('yyyy-MM-ddTHH:mm:ss.fffZ'); VirtualMachinePath = [string]$vmHost.VirtualMachinePath; VirtualHardDiskPath = [string]$vmHost.VirtualHardDiskPath }
            # what the Hyper-V management service left on the tree (entries by SID), and
            # whether the root still holds exactly this tree and every folder below still
            # inherits exactly what it passes down (Codex review of the WP6 package)
            $attempt.RootAfter = @(ConvertTo-RefuteAclRules (Get-Acl -LiteralPath $vmTree))
            $attempt.TreeProblemsAfter = @(Compare-RefuteVmTreeAcl -Acl (Get-Acl -LiteralPath $vmTree) -Spec $spec)
            foreach ($below in @(@('C:\Hyper-V\Virtual Hard Disks', 1), @('C:\Hyper-V\refute-vm', 1), @('C:\Hyper-V\refute-vm\media', 2))) {
                $attempt.TreeProblemsAfter += @(Compare-RefuteVmTreeBelow -Acl (Get-Acl -LiteralPath $below[0]) -Spec $spec -Depth $below[1] | ForEach-Object { "$($below[0]): $_" })
            }
            $out.RefuteVm.HostPaths.Attempts[$name] = $attempt
        }
    }
} finally {
    # out of the module path, kept on the runner (nothing is deleted)
    if (Test-Path -LiteralPath $target) { Move-Item -LiteralPath $target -Destination (Join-Path $env:TEMP 'RefuteVm-installed-by-jea-test') }
}

# the module roots the registration searches, from the function the registration itself
# calls (scripts/vm/RefuteRegistration.Core.ps1), not from a copy of its formula
$repo = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
. (Join-Path $repo 'scripts\vm\RefuteRegistration.Core.ps1')
$out.Roots.Registration = @(Get-RefuteRegistrationModuleRoots)
# the effective discovery set the registration computes (Get-RefuteJeaDiscoveryRoots),
# existing folders or not, compared with what a real session searches (Codex review of #114)
$out.Roots.Discovery = @(Get-RefuteJeaDiscoveryRoots)
Write-Result
