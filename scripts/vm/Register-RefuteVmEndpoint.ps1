<#
.SYNOPSIS
Registers the local JEA endpoint "RefuteVm" (WP6, phase 1). Run by the maintainer, in
Windows PowerShell 5.1 started as Administrator.

.DESCRIPTION
Without -Apply nothing is changed: the script checks the preconditions, prints every
change the registration would make, and prints a PreviewSha256 of that list. With
-Apply -PreviewSha256 <hash> it recomputes the list, refuses if it differs from the
preview (the machine changed), and then makes exactly those changes in this order,
stopping at the first problem:

  1. copies the RefuteVm module (configuration and role capability included) to
     %ProgramFiles%\WindowsPowerShell\Modules\RefuteVm, with NO version subfolder (JEA
     looks for <module path>\<module>\RoleCapabilities\<name>.psrc only), and checks the
     hashes, that only administrators can write there, that the search JEA makes finds
     exactly that role capability, and that no other copy exists on the module path (in
     particular none in a version subfolder);
  2. creates C:\ProgramData\RefuteVm\{Transcripts,Log,State} and the C:\Hyper-V tree
     with explicit ACLs (owner: Administrators);
  3. adds the Windows Firewall rule that blocks inbound TCP 5985 and 5986 from every
     address except loopback, on every profile, and checks that it is in the active
     policy, that every profile is enabled and that no enabled inbound rule overrides
     block rules - all BEFORE the WinRM service is started;
  4. reads the WinRM listeners from the registry (the service may be stopped) and
     refuses any listener other than HTTP on 127.0.0.1 or ::1;
  5. sets WinRM to start automatically, starts it, checks the listeners again through
     WinRM, and adds the loopback listeners that are missing;
  6. writes C:\ProgramData\RefuteVm\RefuteVm.pssc and registers the endpoint with
     Register-PSSessionConfiguration -AccessMode Local (this restarts WinRM);
  7. checks the endpoint's settings and writes
     C:\ProgramData\RefuteVm\Log\registration-evidence.json.

It never deletes or overwrites anything: an existing target stops it before any change.
If it stops in the middle, the parts already made stay; the evidence and the output say
which, and the maintainer decides what to do (scripts/vm/README.md).

.PARAMETER OperatorAccount
The local account allowed to use the endpoint, as COMPUTERNAME\name. It must not be a
member of Hyper-V Administrators.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$OperatorAccount,
    [switch]$Apply,
    [ValidatePattern('^[0-9a-f]{64}$')][string]$PreviewSha256 = ''
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2.0
# Commands of Windows modules load them automatically, and Windows PowerShell 5.1 then
# writes its module analysis cache. Only a value set BEFORE powershell.exe starts
# disables it (about_Windows_PowerShell_5.1, "Module analysis cache"), so the script
# refuses to run unless it was started with PSModuleAnalysisCachePath=nul, before
# reading anything (scripts/vm/README.md).
if ($env:PSModuleAnalysisCachePath -ne 'nul') {
    Write-Output 'Problems (nothing was changed):'
    Write-Output '  - start powershell.exe with PSModuleAnalysisCachePath=nul in its environment (see scripts/vm/README.md), so no module analysis cache is written'
    exit 1
}

$EndpointName = 'RefuteVm'
$RoleName = 'RefuteVmOperator'
$SidHyperVAdmins = 'S-1-5-32-578'
$SidAdmins = 'S-1-5-32-544'
$SidUsers = 'S-1-5-32-545'
$SidSystem = 'S-1-5-18'
$SidTrustedInstaller = 'S-1-5-80-956008885-3418522649-1831038044-1853292631-2271478464'
$SidCreatorOwner = 'S-1-3-0'
$DataRoot = 'C:\ProgramData\RefuteVm'
$VmFolders = @('C:\Hyper-V', 'C:\Hyper-V\Virtual Hard Disks', 'C:\Hyper-V\refute-vm', 'C:\Hyper-V\refute-vm\media')
$FirewallRuleName = 'Refute-JEA-Block-WinRM-Inbound'
$LoopbackListeners = @('IP:127.0.0.1', 'IP:::1')
$NotLoopback = @('0.0.0.0-126.255.255.255', '128.0.0.0-255.255.255.255', '::', '::2-ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff')
$ListenerKey = 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\WSMAN\Listener'
$ModuleSource = Join-Path $PSScriptRoot 'RefuteVm'
$ModuleManifest = Import-PowerShellDataFile -LiteralPath (Join-Path $ModuleSource 'RefuteVm.psd1')
$ModuleBase = Join-Path $env:ProgramFiles 'WindowsPowerShell\Modules\RefuteVm'
# No version subfolder: JEA finds a role capability only at
# <module path>\<module>\RoleCapabilities\<name>.psrc (maintainer's diagnosis, 2026-10-16),
# and the role capability imports the manifest by this exact path.
$ModuleDestination = $ModuleBase
$InstalledManifest = Join-Path $ModuleBase 'RefuteVm.psd1'
$PsscPath = Join-Path $DataRoot 'RefuteVm.pssc'
$EvidencePath = Join-Path $DataRoot 'Log\registration-evidence.json'

function Get-SidAccount([string]$Sid) {
    # The account name of a SID, or the SID itself when this host has no such account
    # (for example Hyper-V Administrators on a host without Hyper-V): the preview lists it
    # as a problem instead of stopping.
    try {
        return (New-Object System.Security.Principal.SecurityIdentifier $Sid).Translate([System.Security.Principal.NTAccount]).Value
    } catch [System.Security.Principal.IdentityNotMappedException] {
        return "$Sid (no account on this host)"
    }
}

function Get-TreeHashes([string]$Root) {
    $map = [ordered]@{}
    foreach ($file in @(Get-ChildItem -LiteralPath $Root -Recurse -File | Sort-Object FullName)) {
        $relative = $file.FullName.Substring($Root.Length + 1).Replace('\', '/')
        $map[$relative] = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    }
    return $map
}

function Get-ModulePathRoots {
    # A superset of the folders Windows PowerShell searches for modules for a service
    # session: the machine PSModulePath, this process's PSModulePath, Program Files,
    # System32 and $PSHOME\Modules. The integration test on a real endpoint (#99) checks
    # that every existing root a JEA session reports, outside the user profiles, is in this
    # set. Enumeration errors stop the script.
    $roots = @([Environment]::GetEnvironmentVariable('PSModulePath', 'Machine').Split(';')) +
        @([Environment]::GetEnvironmentVariable('PSModulePath', 'Process').Split(';')) +
        @((Join-Path $env:ProgramFiles 'WindowsPowerShell\Modules'), (Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\Modules'), (Join-Path $PSHOME 'Modules'))
    return @($roots | Where-Object { $_ } | ForEach-Object { $_.TrimEnd('\') } | Sort-Object -Unique | Where-Object { Test-Path -LiteralPath $_ })
}

function Find-RoleCapabilityCopies {
    $found = @()
    foreach ($root in Get-ModulePathRoots) {
        $found += @(Get-ChildItem -LiteralPath $root -Recurse -Filter "$RoleName.psrc" -File -ErrorAction Stop | ForEach-Object { $_.FullName })
    }
    return @($found | Sort-Object -Unique)
}

function Get-RegistryListeners {
    # The configured WinRM listeners, read from the registry, so the service need not run.
    if (-not (Test-Path -LiteralPath $ListenerKey)) { return @() }
    return @(Get-ChildItem -LiteralPath $ListenerKey | ForEach-Object {
            $name = $_.PSChildName
            $cut = $name.LastIndexOf('+')
            [ordered]@{ Name = $name; Address = $name.Substring(0, [Math]::Max($cut, 0)); Transport = $name.Substring($cut + 1) }
        })
}

function Test-ListenersLoopbackOnly([object[]]$Listeners) {
    return @($Listeners | Where-Object { $LoopbackListeners -notcontains $_.Address -or $_.Transport -ne 'HTTP' })
}

function New-FolderAcl {
    # Entries: @(Sid, Rights, Inherit): Inherit $true = this folder, subfolders and files;
    # $false = this folder only. Inherited entries are removed; owner Administrators.
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

. (Join-Path $PSScriptRoot 'RefuteRegistration.Core.ps1')

function Get-NonAdminWriters([string]$Path) {
    # Accounts other than SYSTEM, Administrators, TrustedInstaller and CREATOR OWNER whose
    # allow entry on Path grants any change (read and execute entries do not count).
    $allowed = @($SidSystem, $SidAdmins, $SidTrustedInstaller, $SidCreatorOwner)
    return @((Get-Acl -LiteralPath $Path).Access | Where-Object {
            $_.AccessControlType -eq 'Allow' -and (Test-RefuteRightsWrite ([int]$_.FileSystemRights)) -and
            $allowed -notcontains $_.IdentityReference.Translate([System.Security.Principal.SecurityIdentifier]).Value
        } | ForEach-Object { [string]$_.IdentityReference })
}

$FolderAcls = [ordered]@{
    $DataRoot                           = @(@($SidSystem, 'FullControl', $true), @($SidAdmins, 'FullControl', $true),
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
if (-not $isAdmin) { $problems.Add('run in a PowerShell started as Administrator (also for the preview: the checks read protected settings)') }
if ($Apply -and -not $PreviewSha256) { $problems.Add('-Apply needs -PreviewSha256 from a preview run') }
# The preview only reads: no WSMan provider access (it may offer to start WinRM) and no
# module discovery (it may write the module analysis cache). The Hyper-V module is found
# by its manifest file, directly in the module folder or in a version subfolder
# (Windows 10 and 11: Hyper-V\2.0.0.0\Hyper-V.psd1); see Find-RefuteHyperVManifest.
$hyperVManifest = Find-RefuteHyperVManifest -ModuleFolder (Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\Modules\Hyper-V')
if (-not $hyperVManifest) { $problems.Add('the Hyper-V PowerShell module is not available') }

$operatorSid = $null
try {
    $operatorSid = (New-Object System.Security.Principal.NTAccount $OperatorAccount).Translate([System.Security.Principal.SecurityIdentifier]).Value
    $OperatorAccount = Get-SidAccount $operatorSid
} catch { $problems.Add("OperatorAccount '$OperatorAccount' does not resolve to an account") }
if ($operatorSid) {
    try {
        $members = @(Get-LocalGroupMember -SID $SidHyperVAdmins | ForEach-Object { $_.SID.Value })
        if ($members -contains $operatorSid) { $problems.Add('the operator account is a member of Hyper-V Administrators; remove it first (it would bypass the endpoint)') }
    } catch { $problems.Add("cannot read the members of Hyper-V Administrators: $($_.Exception.Message)") }
}
function Test-TargetExists([string]$Path) {
    # True when Path exists, or when it cannot be read (a folder only administrators can
    # read, met by a preview run as a normal user on a registered host): then the problem
    # is listed instead of stopping the preview.
    try {
        return (Test-Path -LiteralPath $Path -ErrorAction Stop)
    } catch {
        $problems.Add("$Path cannot be read: $($_.Exception.Message)")
        return $false
    }
}
if (Test-TargetExists $ModuleBase) { $problems.Add("$ModuleBase already exists") }
if (Test-TargetExists $DataRoot) { $problems.Add("$DataRoot already exists") }
foreach ($folder in $VmFolders) { if (Test-TargetExists $folder) { $problems.Add("$folder already exists") } }
# The role capability imports the module by the path of its installed manifest (no
# version, no GUID: those make PowerShell call Get-Module in the restricted session).
$roleData = Import-PowerShellDataFile -LiteralPath (Join-Path $ModuleSource "RoleCapabilities\$RoleName.psrc")
$imports = @($roleData.ModulesToImport)
if ($imports.Count -ne 1 -or $imports[0] -isnot [string] -or $imports[0] -ne $InstalledManifest) {
    $problems.Add("the role capability must import exactly $InstalledManifest (it imports: " + (($imports | ForEach-Object { [string]$_ }) -join ', ') + ')')
}
$psrcCopies = @()
# @(...): a function that returns an empty list gives $null to its caller, and .Count on
# $null is an error under StrictMode in Windows PowerShell 5.1
try { $psrcCopies = @(Find-RoleCapabilityCopies) } catch { $problems.Add("the module path cannot be searched completely: $($_.Exception.Message)") }
if ($psrcCopies.Count) { $problems.Add("a role capability named $RoleName already exists: " + ($psrcCopies -join ', ')) }
if ($isAdmin) {
    if (Get-NetFirewallRule -Name $FirewallRuleName -ErrorAction SilentlyContinue) { $problems.Add("the firewall rule $FirewallRuleName already exists") }
    # The endpoint is a WSMan plugin: read its registry key, never the WSMan provider.
    try {
        $plugin = [Microsoft.Win32.Registry]::LocalMachine.OpenSubKey("SOFTWARE\Microsoft\Windows\CurrentVersion\WSMAN\Plugin\$EndpointName")
        if ($plugin) { $plugin.Close(); $problems.Add("the endpoint $EndpointName is already registered") }
    } catch { $problems.Add("cannot read the WSMan plugin key: $($_.Exception.Message)") }
}
$listeners = @()
try { $listeners = @(Get-RegistryListeners) } catch { $problems.Add("cannot read the WinRM listeners from the registry: $($_.Exception.Message)") }
$foreign = @(Test-ListenersLoopbackOnly $listeners)
if ($foreign.Count) { $problems.Add('WinRM has listeners other than HTTP on loopback: ' + (($foreign | ForEach-Object { $_.Name }) -join ', ') + ' (the maintainer decides; this script never removes them)') }
$winrm = Get-Service -Name WinRM
$config = Import-PowerShellDataFile -LiteralPath (Join-Path $ModuleSource 'RefuteVm.Config.psd1')
$groupAccount = Get-SidAccount $SidHyperVAdmins
if ($groupAccount.EndsWith('(no account on this host)')) { $problems.Add("the group Hyper-V Administrators ($SidHyperVAdmins) does not exist on this host") }
$groupName = $groupAccount.Split('\')[-1]

# ---- the change list (preview) ---------------------------------------------------------
$sourceRoot = (Resolve-Path -LiteralPath $ModuleSource).Path
$sourceHashes = Get-TreeHashes $sourceRoot
$lines = New-Object System.Collections.Generic.List[string]
$lines.Add("Operator account: $OperatorAccount ($operatorSid)")
$lines.Add("Virtual account group: $groupAccount ($SidHyperVAdmins)")
$lines.Add("Hyper-V module manifest: $(if ($hyperVManifest) { $hyperVManifest } else { 'not found' })")
$lines.Add("1. Copy the module to $ModuleDestination, no version subfolder (owner and ACL inherited from Program Files; checked: only SYSTEM, Administrators, TrustedInstaller and CREATOR OWNER can write; the JEA search finds exactly its RoleCapabilities\$RoleName.psrc, and no other copy exists); the role capability imports ${InstalledManifest}:")
foreach ($k in $sourceHashes.Keys) { $lines.Add("     $($sourceHashes[$k])  $k") }
$lines.Add("2. Create these folders, owner Administrators, inheritance removed:")
foreach ($folder in $FolderAcls.Keys) {
    $lines.Add("     $folder")
    foreach ($e in $FolderAcls[$folder]) { $lines.Add(("       {0} {1}{2}" -f (Get-SidAccount $e[0]), $e[1], $(if ($e[2]) { '' } else { ' (this folder only)' }))) }
}
$lines.Add("     $($VmFolders -join ', ') (ACL on C:\Hyper-V, inherited below):")
foreach ($e in $VmTreeAcl) { $lines.Add(("       {0} {1}" -f (Get-SidAccount $e[0]), $e[1])) }
$lines.Add("3. Firewall rule $FirewallRuleName : inbound, block, TCP 5985 and 5986, all profiles, remote addresses $($NotLoopback -join ', ') (before WinRM starts)")
$lines.Add("4. WinRM listeners in the registry now: " + $(if ($listeners.Count) { ($listeners | ForEach-Object { $_.Name }) -join ', ' } else { 'none' }))
$lines.Add("5. WinRM service: startup $($winrm.StartType) -> Automatic; status $($winrm.Status) -> Running; add HTTP listeners (if missing): $($LoopbackListeners -join ', ')")
$lines.Add("6. Write $PsscPath and register endpoint $EndpointName (restarts WinRM): SessionType RestrictedRemoteServer; RunAsVirtualAccount; RunAsVirtualAccountGroups $groupName; RoleDefinitions $OperatorAccount -> $RoleName; TranscriptDirectory $DataRoot\Transcripts; AccessMode Local")
$lines.Add('     JEA grants each virtual account the "Log on as a service" right for the length of its session.')
$lines.Add("7. Write the evidence to $EvidencePath")
if (-not $config.InstallIsoSha256) { $lines.Add('Note: InstallIsoSha256 is empty in the configuration; ImportInstallIso will refuse until a new reviewed version is registered.') }
$sha = [System.Security.Cryptography.SHA256]::Create()
$previewHash = -join ($sha.ComputeHash([System.Text.Encoding]::UTF8.GetBytes(($lines -join "`n"))) | ForEach-Object { $_.ToString('x2') })
$sha.Dispose()

Write-Output '== RefuteVm endpoint registration =='
Write-Output ("Mode: " + $(if ($Apply) { 'APPLY' } else { 'preview (no change)' }))
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
    # 1. module
    foreach ($file in @(Get-ChildItem -LiteralPath $sourceRoot -Recurse -File)) {
        $target = Join-Path $ModuleDestination $file.FullName.Substring($sourceRoot.Length + 1)
        [void][System.IO.Directory]::CreateDirectory((Split-Path -Parent $target))
        Copy-Item -LiteralPath $file.FullName -Destination $target
    }
    $done.Add("module copied to $ModuleDestination")
    if ((ConvertTo-Json (Get-TreeHashes $ModuleDestination) -Compress) -ne (ConvertTo-Json $sourceHashes -Compress)) { throw 'the installed module differs from the source' }
    $writers = @(Get-ChildItem -LiteralPath $ModuleBase -Recurse -Force | ForEach-Object { $_.FullName }) + @($ModuleBase) | ForEach-Object { Get-NonAdminWriters $_ } | Sort-Object -Unique
    if (@($writers).Count) { throw ('accounts other than administrators can write to the module: ' + ($writers -join ', ')) }
    $expected = Join-Path $ModuleDestination "RoleCapabilities\$RoleName.psrc"
    # the search JEA makes (first match wins), then any other copy, in a version subfolder
    # or deeper: exactly one role capability, the one JEA loads
    $moduleRoots = @(Get-ModulePathRoots)
    $jeaFinds = @(Find-RefuteJeaRoleCapability -ModuleRoots $moduleRoots -RoleName $RoleName)
    if ($jeaFinds.Count -ne 1 -or $jeaFinds[0] -ne $expected) { throw ("the JEA search must find exactly $expected, found: " + ($jeaFinds -join ', ')) }
    $versioned = @(Find-RefuteVersionedRoleCapability -ModuleRoots $moduleRoots -RoleName $RoleName)
    if ($versioned.Count) { throw ('copies of the role capability in a version subfolder: ' + ($versioned -join ', ')) }
    $copies = @(Find-RoleCapabilityCopies)
    if ($copies.Count -ne 1 -or $copies[0] -ne $expected) { throw ("expected exactly one role capability at $expected, found: " + ($copies -join ', ')) }
    if (-not (Test-Path -LiteralPath $InstalledManifest -PathType Leaf)) { throw "the manifest the role capability imports is missing: $InstalledManifest" }
    # 2. folders
    foreach ($folder in $FolderAcls.Keys) {
        [void][System.IO.Directory]::CreateDirectory($folder)
        Set-Acl -LiteralPath $folder -AclObject (New-FolderAcl $FolderAcls[$folder])
    }
    [void][System.IO.Directory]::CreateDirectory($VmFolders[0])
    Set-Acl -LiteralPath $VmFolders[0] -AclObject (New-FolderAcl $VmTreeAcl)
    foreach ($folder in $VmFolders[1..($VmFolders.Count - 1)]) { [void][System.IO.Directory]::CreateDirectory($folder) }
    $done.Add('folders created')
    # 3. firewall, before WinRM starts
    New-NetFirewallRule -Name $FirewallRuleName -DisplayName 'Refute JEA: block WinRM from the network' `
        -Description 'Blocks inbound WinRM (TCP 5985, 5986) from every address except loopback (scripts/vm/README.md).' `
        -Direction Inbound -Action Block -Protocol TCP -LocalPort 5985, 5986 -RemoteAddress $NotLoopback -Profile Any -Enabled True | Out-Null
    $done.Add("firewall rule $FirewallRuleName added")
    $active = Get-NetFirewallRule -PolicyStore ActiveStore -Name $FirewallRuleName -ErrorAction SilentlyContinue
    if (-not $active -or [string]$active.Enabled -ne 'True' -or [string]$active.Action -ne 'Block') { throw 'the block rule is not in the active firewall policy' }
    $profilesOff = @(Get-NetFirewallProfile -PolicyStore ActiveStore | Where-Object { [string]$_.Enabled -ne 'True' } | ForEach-Object { $_.Name })
    if ($profilesOff.Count) { throw ('firewall profiles not enabled: ' + ($profilesOff -join ', ')) }
    # OverrideBlockRules belongs to each rule's security filter, not to the rule.
    $inbound = foreach ($r in @(Get-NetFirewallRule -PolicyStore ActiveStore | Where-Object { [string]$_.Enabled -eq 'True' -and [string]$_.Direction -eq 'Inbound' })) {
        $filter = Get-NetFirewallSecurityFilter -AssociatedNetFirewallRule $r
        [ordered]@{ Name = $r.Name; Enabled = [string]$r.Enabled; Direction = [string]$r.Direction; OverrideBlockRules = [bool]$filter.OverrideBlockRules }
    }
    $overrides = @(Find-RefuteBlockOverrides @($inbound))
    if ($overrides.Count) { throw ('enabled inbound rules override block rules: ' + ($overrides -join ', ')) }
    # 4. listeners from the registry, before the service starts
    $foreign = @(Test-ListenersLoopbackOnly @(Get-RegistryListeners))
    if ($foreign.Count) { throw ('WinRM has listeners other than HTTP on loopback: ' + (($foreign | ForEach-Object { $_.Name }) -join ', ')) }
    # 5. WinRM service and loopback listeners
    Set-Service -Name WinRM -StartupType Automatic
    if ((Get-Service -Name WinRM).Status -ne 'Running') { Start-Service -Name WinRM }
    $done.Add('WinRM set to automatic and running')
    $live = @(Get-WSManInstance -ResourceURI winrm/config/Listener -Enumerate | ForEach-Object { [ordered]@{ Name = "$($_.Address)+$($_.Transport)"; Address = [string]$_.Address; Transport = [string]$_.Transport } })
    $foreign = @(Test-ListenersLoopbackOnly $live)
    if ($foreign.Count) { throw ('WinRM reports listeners other than HTTP on loopback: ' + (($foreign | ForEach-Object { $_.Name }) -join ', ')) }
    foreach ($address in $LoopbackListeners) {
        if (@($live | Where-Object { $_.Address -eq $address }).Count -eq 0) {
            New-Item -Path WSMan:\localhost\Listener -Address $address -Transport HTTP -Force | Out-Null
            $done.Add("listener $address+HTTP added")
        }
    }
    $live = @(Get-WSManInstance -ResourceURI winrm/config/Listener -Enumerate)
    foreach ($l in $live) {
        if ($LoopbackListeners -notcontains [string]$l.Address -or [string]$l.Transport -ne 'HTTP' -or [string]$l.Port -ne '5985' -or [string]$l.Enabled -ne 'true') {
            throw "unexpected listener after the change: $($l.Address) $($l.Transport) port $($l.Port) enabled $($l.Enabled)"
        }
    }
    # 6. session configuration
    New-PSSessionConfigurationFile -Path $PsscPath -SessionType RestrictedRemoteServer -RunAsVirtualAccount `
        -RunAsVirtualAccountGroups $groupName -TranscriptDirectory (Join-Path $DataRoot 'Transcripts') `
        -RoleDefinitions @{ $OperatorAccount = @{ RoleCapabilities = $RoleName } } `
        -Description 'Refute VM operations (WP6 phase 1)'
    if (-not (Test-PSSessionConfigurationFile -Path $PsscPath)) { throw "the session configuration file is not valid: $PsscPath" }
    Register-PSSessionConfiguration -Name $EndpointName -Path $PsscPath -AccessMode Local -Force | Out-Null
    $done.Add("endpoint $EndpointName registered")
    $endpoint = Get-PSSessionConfiguration -Name $EndpointName
    if ([string]$endpoint.RunAsVirtualAccount -ne 'True') { throw 'the endpoint does not run as a virtual account' }
    if ([string]$endpoint.RunAsVirtualAccountGroups -notmatch [regex]::Escape($groupName)) { throw 'the virtual account group is not the expected one' }
    if ([string]$endpoint.Permission -notmatch [regex]::Escape($OperatorAccount)) { throw 'the operator account is not in the endpoint permission' }
} catch {
    Write-Output "STOPPED: $($_.Exception.Message)"
    Write-Output ('Already done: ' + $(if ($done.Count) { $done -join '; ' } else { 'nothing' }))
    exit 2
}

# ---- evidence ---------------------------------------------------------------------------
$rule = Get-NetFirewallRule -Name $FirewallRuleName
$evidence = [ordered]@{
    Utc              = [DateTime]::UtcNow.ToString('yyyy-MM-ddTHH:mm:ssZ')
    PreviewSha256    = $previewHash
    Module           = [ordered]@{ Path = $ModuleDestination; Files = Get-TreeHashes $ModuleDestination }
    RoleCapabilities = @(Find-RoleCapabilityCopies)
    JeaRoleCapability = @(Find-RefuteJeaRoleCapability -ModuleRoots @(Get-ModulePathRoots) -RoleName $RoleName)
    Endpoint         = [ordered]@{
        Name                      = $endpoint.Name
        Permission                = [string]$endpoint.Permission
        RunAsVirtualAccount       = [string]$endpoint.RunAsVirtualAccount
        RunAsVirtualAccountGroups = [string]$endpoint.RunAsVirtualAccountGroups
        TranscriptDirectory       = [string]$endpoint.TranscriptDirectory
        SessionType               = [string]$endpoint.SessionType
    }
    WinRmService     = [ordered]@{ StartType = [string](Get-Service WinRM).StartType; Status = [string](Get-Service WinRM).Status }
    Listeners        = @(Get-WSManInstance -ResourceURI winrm/config/Listener -Enumerate | ForEach-Object { [ordered]@{ Address = [string]$_.Address; Transport = [string]$_.Transport; Port = [string]$_.Port; Enabled = [string]$_.Enabled } })
    ListeningSockets = @(Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Where-Object { $_.LocalPort -in 5985, 5986 } | ForEach-Object { "$($_.LocalAddress):$($_.LocalPort)" })
    FirewallProfiles = @(Get-NetFirewallProfile -PolicyStore ActiveStore | ForEach-Object { [ordered]@{ Name = $_.Name; Enabled = [string]$_.Enabled } })
    FirewallRule     = [ordered]@{
        Name          = $rule.Name
        Enabled       = [string]$rule.Enabled
        Direction     = [string]$rule.Direction
        Action        = [string]$rule.Action
        Profile       = [string]$rule.Profile
        LocalPorts    = [string](($rule | Get-NetFirewallPortFilter).LocalPort -join ',')
        RemoteAddress = [string](($rule | Get-NetFirewallAddressFilter).RemoteAddress -join ',')
    }
    FolderAcls       = [ordered]@{}
}
foreach ($folder in @($FolderAcls.Keys) + $VmFolders + @($ModuleDestination)) { $evidence.FolderAcls[$folder] = (Get-Acl -LiteralPath $folder).Sddl }
$utf8 = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($EvidencePath, (ConvertTo-Json $evidence -Depth 6), $utf8)
Write-Output "Done. Evidence: $EvidencePath"
Write-Output (ConvertTo-Json $evidence -Depth 6)
