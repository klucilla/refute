<#
.SYNOPSIS
Registers the local JEA endpoint "RefuteVm" (WP6, phase 1). Run by the maintainer, in
Windows PowerShell 5.1 started as Administrator.

.DESCRIPTION
Without -Apply nothing is changed: the script checks the preconditions and prints every
change the registration would make. With -Apply it makes exactly those changes, in the
printed order, stops at the first problem, and writes the evidence (scripts/vm/README.md).

Changes made with -Apply:
  1. copies the RefuteVm module (with its configuration and role capability) to
     %ProgramFiles%\WindowsPowerShell\Modules\RefuteVm\<version>, and checks the hashes;
  2. creates C:\ProgramData\RefuteVm\{Transcripts,Log,State} with explicit ACLs;
  3. creates C:\Hyper-V, C:\Hyper-V\Virtual Hard Disks, C:\Hyper-V\refute-vm and
     C:\Hyper-V\refute-vm\media with an explicit ACL;
  4. sets the WinRM service to start automatically and starts it;
  5. adds WinRM HTTP listeners on 127.0.0.1 and ::1 only (it refuses if any other
     listener exists);
  6. adds a Windows Firewall rule that blocks inbound TCP 5985 and 5986 from every
     address except loopback, on every profile;
  7. writes the session configuration file C:\ProgramData\RefuteVm\RefuteVm.pssc and
     registers the endpoint with Register-PSSessionConfiguration -AccessMode Local,
     which restarts the WinRM service.
It never deletes or overwrites anything: an existing target stops the script.

.PARAMETER OperatorAccount
The local account allowed to use the endpoint, as COMPUTERNAME\name. It must not be a
member of Hyper-V Administrators.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$OperatorAccount,
    [switch]$Apply
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2.0

$EndpointName = 'RefuteVm'
$RoleName = 'RefuteVmOperator'
$SidHyperVAdmins = 'S-1-5-32-578'
$SidAdmins = 'S-1-5-32-544'
$SidUsers = 'S-1-5-32-545'
$SidSystem = 'S-1-5-18'
$DataRoot = 'C:\ProgramData\RefuteVm'
$VmFolders = @('C:\Hyper-V', 'C:\Hyper-V\Virtual Hard Disks', 'C:\Hyper-V\refute-vm', 'C:\Hyper-V\refute-vm\media')
$FirewallRuleName = 'Refute-JEA-Block-WinRM-Inbound'
$LoopbackListeners = @('IP:127.0.0.1', 'IP:::1')
$NotLoopback = @('0.0.0.0-126.255.255.255', '128.0.0.0-255.255.255.255', '::', '::2-ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff')
$ModuleSource = Join-Path $PSScriptRoot 'RefuteVm'
$ModuleManifest = Import-PowerShellDataFile -LiteralPath (Join-Path $ModuleSource 'RefuteVm.psd1')
$ModuleDestination = Join-Path $env:ProgramFiles ('WindowsPowerShell\Modules\RefuteVm\' + $ModuleManifest.ModuleVersion)
$PsscPath = Join-Path $DataRoot 'RefuteVm.pssc'
$EvidencePath = Join-Path $DataRoot 'Log\registration-evidence.json'

function Get-SidAccount([string]$Sid) {
    return (New-Object System.Security.Principal.SecurityIdentifier $Sid).Translate([System.Security.Principal.NTAccount]).Value
}

function Get-TreeHashes([string]$Root) {
    $map = [ordered]@{}
    foreach ($file in @(Get-ChildItem -LiteralPath $Root -Recurse -File | Sort-Object FullName)) {
        $relative = $file.FullName.Substring($Root.Length + 1).Replace('\', '/')
        $map[$relative] = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    }
    return $map
}

function New-FolderAcl {
    # Entries: @(Sid, Rights, Inherit) where Inherit is $true for this folder, its
    # subfolders and files, $false for this folder only. Inherited entries are removed.
    param([object[]]$Entries)
    $acl = New-Object System.Security.AccessControl.DirectorySecurity
    $acl.SetAccessRuleProtection($true, $false)
    $acl.SetOwner((New-Object System.Security.Principal.SecurityIdentifier $SidAdmins))
    foreach ($entry in $Entries) {
        $inherit = [System.Security.AccessControl.InheritanceFlags]::None
        if ($entry[2]) { $inherit = [System.Security.AccessControl.InheritanceFlags]'ContainerInherit, ObjectInherit' }
        $rule = New-Object System.Security.AccessControl.FileSystemAccessRule(
            (New-Object System.Security.Principal.SecurityIdentifier $entry[0]),
            [System.Security.AccessControl.FileSystemRights]$entry[1], $inherit,
            [System.Security.AccessControl.PropagationFlags]::None,
            [System.Security.AccessControl.AccessControlType]::Allow)
        $acl.AddAccessRule($rule)
    }
    return $acl
}

$FolderAcls = [ordered]@{
    $DataRoot                          = @(@($SidSystem, 'FullControl', $true), @($SidAdmins, 'FullControl', $true),
                                           @($SidHyperVAdmins, 'ReadAndExecute', $false), @($SidUsers, 'ReadAndExecute', $false))
    (Join-Path $DataRoot 'Transcripts') = @(@($SidSystem, 'FullControl', $true), @($SidAdmins, 'FullControl', $true))
    (Join-Path $DataRoot 'Log')         = @(@($SidSystem, 'FullControl', $true), @($SidAdmins, 'FullControl', $true),
                                           @($SidHyperVAdmins, 'Modify', $true), @($SidUsers, 'ReadAndExecute', $true))
    (Join-Path $DataRoot 'State')       = @(@($SidSystem, 'FullControl', $true), @($SidAdmins, 'FullControl', $true),
                                           @($SidHyperVAdmins, 'Modify', $true), @($SidUsers, 'ReadAndExecute', $true))
}
$VmTreeAcl = @(@($SidSystem, 'FullControl', $true), @($SidAdmins, 'FullControl', $true), @($SidHyperVAdmins, 'Modify', $true))

# ---- preconditions ------------------------------------------------------------------
$problems = New-Object System.Collections.Generic.List[string]
$isAdmin = ([System.Security.Principal.WindowsPrincipal][System.Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([System.Security.Principal.WindowsBuiltInRole]::Administrator)
if ($PSVersionTable.PSEdition -ne 'Desktop' -or $PSVersionTable.PSVersion.Major -ne 5) { $problems.Add('run in Windows PowerShell 5.1 (powershell.exe)') }
if ($Apply -and -not $isAdmin) { $problems.Add('-Apply needs a PowerShell started as Administrator') }
if (-not (Get-Module -ListAvailable -Name Hyper-V)) { $problems.Add('the Hyper-V PowerShell module is not available') }

$operatorSid = $null
try {
    $operatorSid = (New-Object System.Security.Principal.NTAccount $OperatorAccount).Translate([System.Security.Principal.SecurityIdentifier]).Value
    $OperatorAccount = Get-SidAccount $operatorSid
} catch { $problems.Add("OperatorAccount '$OperatorAccount' does not resolve to a local account") }
if ($operatorSid) {
    $members = @()
    try { $members = @(Get-LocalGroupMember -SID $SidHyperVAdmins | ForEach-Object { $_.SID.Value }) } catch { $problems.Add("cannot read the members of Hyper-V Administrators: $($_.Exception.Message)") }
    if ($members -contains $operatorSid) { $problems.Add('the operator account is a member of Hyper-V Administrators; remove it first (it would bypass the endpoint)') }
}
if (Test-Path -LiteralPath $ModuleDestination) { $problems.Add("the module destination already exists: $ModuleDestination") }
if (Test-Path -LiteralPath $DataRoot) { $problems.Add("$DataRoot already exists") }
foreach ($folder in $VmFolders) { if (Test-Path -LiteralPath $folder) { $problems.Add("$folder already exists") } }
if (Get-NetFirewallRule -Name $FirewallRuleName -ErrorAction SilentlyContinue) { $problems.Add("the firewall rule $FirewallRuleName already exists") }
$psrcCopies = @(foreach ($dir in $env:PSModulePath.Split(';') | Where-Object { $_ -and (Test-Path -LiteralPath $_) }) {
        Get-ChildItem -LiteralPath $dir -Recurse -Filter "$RoleName.psrc" -File -ErrorAction SilentlyContinue })
if ($psrcCopies.Count) { $problems.Add("a role capability named $RoleName is already on PSModulePath: " + ($psrcCopies.FullName -join ', ')) }
$config = Import-PowerShellDataFile -LiteralPath (Join-Path $ModuleSource 'RefuteVm.Config.psd1')
$listeners = $null
$winrm = Get-Service -Name WinRM
if ($isAdmin) {
    if (Get-PSSessionConfiguration -Name $EndpointName -ErrorAction SilentlyContinue) { $problems.Add("the endpoint $EndpointName is already registered") }
    if ($winrm.Status -eq 'Running') {
        $listeners = @(Get-WSManInstance -ResourceURI winrm/config/Listener -Enumerate | ForEach-Object { [string]$_.Address })
        $foreign = @($listeners | Where-Object { $LoopbackListeners -notcontains $_ })
        if ($foreign.Count) { $problems.Add('WinRM has listeners other than loopback: ' + ($foreign -join ', ') + ' (the maintainer decides; this script does not remove them)') }
    }
}

# ---- what would change ------------------------------------------------------------------
$sourceHashes = Get-TreeHashes (Resolve-Path -LiteralPath $ModuleSource).Path
Write-Output '== RefuteVm endpoint registration =='
Write-Output ("Mode: " + $(if ($Apply) { 'APPLY' } else { 'preview (no change)' }))
Write-Output "Operator account: $OperatorAccount ($operatorSid)"
Write-Output "Virtual account group: $(Get-SidAccount $SidHyperVAdmins) ($SidHyperVAdmins)"
Write-Output ''
Write-Output "1. Copy the module to $ModuleDestination :"
foreach ($k in $sourceHashes.Keys) { Write-Output "     $($sourceHashes[$k])  $k" }
Write-Output "2. Create $DataRoot and its folders, with these ACLs (inheritance removed):"
foreach ($folder in $FolderAcls.Keys) {
    Write-Output "     $folder"
    foreach ($e in $FolderAcls[$folder]) { Write-Output ("       {0} {1}{2}" -f (Get-SidAccount $e[0]), $e[1], $(if ($e[2]) { '' } else { ' (this folder only)' })) }
}
Write-Output "3. Create $($VmFolders -join ', '); ACL on C:\Hyper-V, inherited below:"
foreach ($e in $VmTreeAcl) { Write-Output ("       {0} {1}" -f (Get-SidAccount $e[0]), $e[1]) }
Write-Output "4. WinRM service: startup $($winrm.StartType) -> Automatic; status $($winrm.Status) -> Running"
Write-Output ("5. WinRM listeners now: " + $(if ($null -eq $listeners) { 'not read (service stopped or not Administrator)' } else { ($listeners -join ', ') }) + "; add (HTTP): $($LoopbackListeners -join ', ')")
Write-Output "6. Firewall rule $FirewallRuleName : inbound, block, TCP 5985 and 5986, all profiles, remote addresses $($NotLoopback -join ', ')"
Write-Output "7. Session configuration $PsscPath and Register-PSSessionConfiguration -Name $EndpointName -AccessMode Local (restarts WinRM):"
Write-Output "     SessionType RestrictedRemoteServer (NoLanguage); RunAsVirtualAccount; RunAsVirtualAccountGroups $(Get-SidAccount $SidHyperVAdmins)"
Write-Output "     RoleDefinitions: $OperatorAccount -> $RoleName; TranscriptDirectory $DataRoot\Transcripts"
Write-Output '     JEA grants each virtual account the "Log on as a service" right for the length of its session.'
if (-not $config.InstallIsoSha256) { Write-Output 'Note: InstallIsoSha256 is empty in the configuration; ImportInstallIso will refuse until a new reviewed version is registered.' }
Write-Output ''
if ($problems.Count) {
    Write-Output 'Problems (nothing was changed):'
    foreach ($p in $problems) { Write-Output "  - $p" }
    exit 1
}
if (-not $Apply) { Write-Output 'Preconditions hold. Run again with -Apply to make these changes.'; exit 0 }

# ---- apply ------------------------------------------------------------------------------
Write-Output 'Applying...'
# 1. module
$sourceRoot = (Resolve-Path -LiteralPath $ModuleSource).Path
foreach ($file in @(Get-ChildItem -LiteralPath $sourceRoot -Recurse -File)) {
    $target = Join-Path $ModuleDestination $file.FullName.Substring($sourceRoot.Length + 1)
    [void][System.IO.Directory]::CreateDirectory((Split-Path -Parent $target))
    Copy-Item -LiteralPath $file.FullName -Destination $target
}
$installed = Get-TreeHashes $ModuleDestination
if ((ConvertTo-Json $installed -Compress) -ne (ConvertTo-Json $sourceHashes -Compress)) { throw 'the installed module differs from the source; stopped' }
# 2. data folders
foreach ($folder in $FolderAcls.Keys) {
    [void][System.IO.Directory]::CreateDirectory($folder)
    Set-Acl -LiteralPath $folder -AclObject (New-FolderAcl $FolderAcls[$folder])
}
# 3. VM folders
[void][System.IO.Directory]::CreateDirectory($VmFolders[0])
Set-Acl -LiteralPath $VmFolders[0] -AclObject (New-FolderAcl $VmTreeAcl)
foreach ($folder in $VmFolders[1..($VmFolders.Count - 1)]) { [void][System.IO.Directory]::CreateDirectory($folder) }
# 4. WinRM service
Set-Service -Name WinRM -StartupType Automatic
if ((Get-Service -Name WinRM).Status -ne 'Running') { Start-Service -Name WinRM }
# 5. listeners
$listeners = @(Get-WSManInstance -ResourceURI winrm/config/Listener -Enumerate | ForEach-Object { [string]$_.Address })
$foreign = @($listeners | Where-Object { $LoopbackListeners -notcontains $_ })
if ($foreign.Count) { throw ('WinRM has listeners other than loopback: ' + ($foreign -join ', ') + '; stopped before the endpoint is registered') }
foreach ($address in $LoopbackListeners) {
    if ($listeners -notcontains $address) { New-Item -Path WSMan:\localhost\Listener -Address $address -Transport HTTP -Force | Out-Null }
}
# 6. firewall
New-NetFirewallRule -Name $FirewallRuleName -DisplayName 'Refute JEA: block WinRM from the network' `
    -Description 'Blocks inbound WinRM (TCP 5985, 5986) from every address except loopback (scripts/vm/README.md).' `
    -Direction Inbound -Action Block -Protocol TCP -LocalPort 5985, 5986 -RemoteAddress $NotLoopback -Profile Any -Enabled True | Out-Null
# 7. session configuration
$groupName = (Get-SidAccount $SidHyperVAdmins).Split('\')[-1]
New-PSSessionConfigurationFile -Path $PsscPath -SessionType RestrictedRemoteServer -RunAsVirtualAccount `
    -RunAsVirtualAccountGroups $groupName -TranscriptDirectory (Join-Path $DataRoot 'Transcripts') `
    -RoleDefinitions @{ $OperatorAccount = @{ RoleCapabilities = $RoleName } } `
    -Description 'Refute VM operations (WP6 phase 1)'
if (-not (Test-PSSessionConfigurationFile -Path $PsscPath)) { throw "the session configuration file is not valid: $PsscPath" }
Register-PSSessionConfiguration -Name $EndpointName -Path $PsscPath -AccessMode Local -Force | Out-Null

# ---- evidence ---------------------------------------------------------------------------
$endpoint = Get-PSSessionConfiguration -Name $EndpointName
$rule = Get-NetFirewallRule -Name $FirewallRuleName
$evidence = [ordered]@{
    Utc                = [DateTime]::UtcNow.ToString('yyyy-MM-ddTHH:mm:ssZ')
    Module             = [ordered]@{ Path = $ModuleDestination; Files = Get-TreeHashes $ModuleDestination }
    RoleCapabilities   = @(foreach ($dir in $env:PSModulePath.Split(';') | Where-Object { $_ -and (Test-Path -LiteralPath $_) }) {
            Get-ChildItem -LiteralPath $dir -Recurse -Filter "$RoleName.psrc" -File -ErrorAction SilentlyContinue | ForEach-Object { $_.FullName } })
    Endpoint           = [ordered]@{
        Name                      = $endpoint.Name
        Permission                = [string]$endpoint.Permission
        RunAsVirtualAccount       = [string]$endpoint.RunAsVirtualAccount
        RunAsVirtualAccountGroups = [string]$endpoint.RunAsVirtualAccountGroups
        TranscriptDirectory       = [string]$endpoint.TranscriptDirectory
        SessionType               = [string]$endpoint.SessionType
    }
    WinRmService       = [ordered]@{ StartType = [string](Get-Service WinRM).StartType; Status = [string](Get-Service WinRM).Status }
    Listeners          = @(Get-WSManInstance -ResourceURI winrm/config/Listener -Enumerate | ForEach-Object { [ordered]@{ Address = [string]$_.Address; Transport = [string]$_.Transport; Port = [string]$_.Port } })
    ListeningSockets   = @(Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Where-Object { $_.LocalPort -in 5985, 5986 } | ForEach-Object { "$($_.LocalAddress):$($_.LocalPort)" })
    FirewallRule       = [ordered]@{
        Name          = $rule.Name
        Enabled       = [string]$rule.Enabled
        Direction     = [string]$rule.Direction
        Action        = [string]$rule.Action
        Profile       = [string]$rule.Profile
        LocalPorts    = [string](($rule | Get-NetFirewallPortFilter).LocalPort -join ',')
        RemoteAddress = [string](($rule | Get-NetFirewallAddressFilter).RemoteAddress -join ',')
    }
    FolderAcls         = [ordered]@{}
}
foreach ($folder in @($FolderAcls.Keys) + $VmFolders) { $evidence.FolderAcls[$folder] = (Get-Acl -LiteralPath $folder).Sddl }
$utf8 = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($EvidencePath, (ConvertTo-Json $evidence -Depth 6), $utf8)
Write-Output "Done. Evidence: $EvidencePath"
Write-Output (ConvertTo-Json $evidence -Depth 6)
