# Pure logic of the RefuteVm module: the operation table, the checks of the
# configuration and of the paths, and the plan of one operation computed from the
# configuration and an observed state. Nothing here calls Hyper-V or writes a file, so
# it is tested in CI with synthetic observed states (tests/test_vm_scripts.py).
# Windows PowerShell 5.1 and PowerShell 7 compatible.

Set-StrictMode -Version 2.0

# One administrative action per operation. VmState: the states the VM must be in
# (empty: the operation does not need the VM). Argument: none, MediaSha256, Percent or
# ServiceGuid; no operation takes a path or a VM name.
$script:RefuteVmOperationTable = [ordered]@{
    SetHostPaths                 = @{ VmState = @();                    Argument = 'none' }
    DisableEnhancedSessionHost   = @{ VmState = @();                    Argument = 'none' }
    CreateBaseDisk               = @{ VmState = @();                    Argument = 'none' }
    CreateVm                     = @{ VmState = @();                    Argument = 'none' }
    SetMemory                    = @{ VmState = @('Off');               Argument = 'none' }
    SetProcessor                 = @{ VmState = @('Off');               Argument = 'none' }
    SetSecureBoot                = @{ VmState = @('Off');               Argument = 'none' }
    DisableCheckpoints           = @{ VmState = @('Off');               Argument = 'none' }
    DisableGuestServiceInterface = @{ VmState = @('Off');               Argument = 'ServiceGuid' }
    DisconnectNetwork            = @{ VmState = @('Off');               Argument = 'none' }
    AttachBaseDisk               = @{ VmState = @('Off');               Argument = 'none' }
    ImportInstallIso             = @{ VmState = @();                    Argument = 'MediaSha256' }
    ImportSeedIso                = @{ VmState = @();                    Argument = 'MediaSha256' }
    AttachInstallMedia           = @{ VmState = @('Off');               Argument = 'none' }
    SetBootFromInstallMedia      = @{ VmState = @('Off');               Argument = 'none' }
    StartVm                      = @{ VmState = @('Off', 'Saved');      Argument = 'none' }
    StopVm                       = @{ VmState = @('Running');           Argument = 'none' }
    DetachInstallMedia           = @{ VmState = @('Off');               Argument = 'none' }
    SetProcessorMaximum          = @{ VmState = @('Off', 'Running');    Argument = 'Percent' }
    SuspendVm                    = @{ VmState = @('Running');           Argument = 'none' }
    ResumeVm                     = @{ VmState = @('Paused');            Argument = 'none' }
    SaveVm                       = @{ VmState = @('Running');           Argument = 'none' }
}

function Get-RefuteVmOperationNames {
    return @($script:RefuteVmOperationTable.Keys)
}

function Test-RefuteSafePath {
    # True when Path is an absolute local path equal to Root or inside it, with no
    # relative segment, wildcard, alternate stream or UNC form. Root itself must be a
    # plain drive path such as 'C:\Hyper-V'.
    param([string]$Path, [string]$Root)
    if ([string]::IsNullOrEmpty($Path) -or [string]::IsNullOrEmpty($Root)) { return $false }
    foreach ($p in @($Path, $Root)) {
        if ($p -notmatch '^[A-Za-z]:\\') { return $false }
        if ($p.Contains('/') -or $p.Contains('\\\\')) { return $false }
        if ($p.IndexOfAny([char[]]'*?[]~"<>|') -ge 0) { return $false }
        if ($p.Substring(2).Contains(':')) { return $false }
        foreach ($segment in $p.Substring(3).Split('\')) {
            if ($segment -eq '.' -or $segment -eq '..') { return $false }
            if ($segment -ne $segment.TrimEnd(' ', '.')) { return $false }
        }
        if ($p.EndsWith('\')) { return $false }
    }
    if ($Path -ieq $Root) { return $true }
    return $Path.StartsWith($Root + '\', [System.StringComparison]::OrdinalIgnoreCase)
}

function Test-RefuteVmConfig {
    # The list of problems of a configuration; empty when it is valid.
    param([System.Collections.IDictionary]$Config)
    $problems = New-Object System.Collections.Generic.List[string]
    $required = 'ConfigVersion', 'VmName', 'HostVirtualMachinePath', 'HostVirtualHardDiskPath',
        'VmRoot', 'BaseDiskPath', 'BaseDiskSizeBytes', 'MediaRoot', 'MediaSource',
        'InstallIsoName', 'InstallIsoSha256', 'SeedIsoName', 'ProcessorCount', 'MemoryBytes',
        'SecureBootTemplate', 'StateFile', 'OperationLog'
    foreach ($key in $required) {
        if (-not $Config.Contains($key)) { $problems.Add("missing key: $key") }
    }
    foreach ($key in @($Config.Keys)) {
        if ($required -notcontains $key) { $problems.Add("unknown key: $key") }
    }
    if ($problems.Count) { return , $problems.ToArray() }

    if ($Config.ConfigVersion -ne 1) { $problems.Add('ConfigVersion must be 1') }
    if ($Config.VmName -cnotmatch '^[a-z][a-z0-9-]{2,30}$') { $problems.Add('VmName must be lowercase letters, digits and hyphens') }
    $hyperV = 'C:\Hyper-V'
    foreach ($key in 'HostVirtualMachinePath', 'HostVirtualHardDiskPath', 'VmRoot', 'BaseDiskPath', 'MediaRoot') {
        if (-not (Test-RefuteSafePath -Path $Config[$key] -Root $hyperV)) { $problems.Add("$key must be inside $hyperV") }
    }
    if ($Config.HostVirtualMachinePath -ine $hyperV) { $problems.Add("HostVirtualMachinePath must be $hyperV") }
    if ($Config.HostVirtualHardDiskPath -ine "$hyperV\Virtual Hard Disks") { $problems.Add("HostVirtualHardDiskPath must be $hyperV\Virtual Hard Disks") }
    if (-not (Test-RefuteSafePath -Path $Config.MediaRoot -Root $Config.VmRoot)) { $problems.Add('MediaRoot must be inside VmRoot') }
    if (-not (Test-RefuteSafePath -Path $Config.BaseDiskPath -Root $Config.HostVirtualHardDiskPath)) { $problems.Add('BaseDiskPath must be inside HostVirtualHardDiskPath') }
    if ($Config.BaseDiskPath -inotmatch '\.vhdx$') { $problems.Add('BaseDiskPath must be a .vhdx file') }
    if (-not (Test-RefuteSafePath -Path $Config.MediaSource -Root 'C:\Projetos\refute\.cache\vm')) { $problems.Add('MediaSource must be inside C:\Projetos\refute\.cache\vm') }
    foreach ($key in 'StateFile', 'OperationLog') {
        if (-not (Test-RefuteSafePath -Path $Config[$key] -Root 'C:\ProgramData\RefuteVm')) { $problems.Add("$key must be inside C:\ProgramData\RefuteVm") }
    }
    foreach ($key in 'InstallIsoName', 'SeedIsoName') {
        if ($Config[$key] -cnotmatch '^[a-z0-9][a-z0-9.-]*\.iso$') { $problems.Add("$key must be a plain lowercase .iso file name") }
    }
    if ($Config.InstallIsoSha256 -cnotmatch '^([0-9a-f]{64})?$') { $problems.Add('InstallIsoSha256 must be empty or 64 lowercase hex digits') }
    if ($Config.ProcessorCount -isnot [int] -or $Config.ProcessorCount -lt 1 -or $Config.ProcessorCount -gt 24) { $problems.Add('ProcessorCount must be an integer from 1 to 24 (plan 7.1)') }
    if (($Config.MemoryBytes -isnot [long] -and $Config.MemoryBytes -isnot [int]) -or $Config.MemoryBytes -le 0 -or $Config.MemoryBytes % 1048576 -ne 0) { $problems.Add('MemoryBytes must be a positive multiple of 1 MB') }
    if (($Config.BaseDiskSizeBytes -isnot [long] -and $Config.BaseDiskSizeBytes -isnot [int]) -or $Config.BaseDiskSizeBytes -le 0 -or $Config.BaseDiskSizeBytes % 1048576 -ne 0) { $problems.Add('BaseDiskSizeBytes must be a positive multiple of 1 MB') }
    if ($Config.SecureBootTemplate -cne 'MicrosoftUEFICertificateAuthority') { $problems.Add('SecureBootTemplate must be MicrosoftUEFICertificateAuthority') }
    return , $problems.ToArray()
}

function ConvertTo-RefuteCanonicalJson {
    # JSON with object keys sorted by ordinal comparison, no spaces, and every character
    # outside printable ASCII escaped, so equal values always give equal text.
    param($Value)
    if ($null -eq $Value) { return 'null' }
    if ($Value -is [bool]) { if ($Value) { return 'true' } else { return 'false' } }
    if ($Value -is [string] -or $Value -is [char] -or $Value -is [enum] -or $Value -is [guid]) {
        $text = [string]$Value
        $sb = New-Object System.Text.StringBuilder
        [void]$sb.Append('"')
        foreach ($ch in $text.ToCharArray()) {
            $code = [int]$ch
            if ($ch -eq '"') { [void]$sb.Append('\"') }
            elseif ($ch -eq '\') { [void]$sb.Append('\\') }
            elseif ($code -lt 0x20 -or $code -gt 0x7E) { [void]$sb.Append(('\u{0:x4}' -f $code)) }
            else { [void]$sb.Append($ch) }
        }
        [void]$sb.Append('"')
        return $sb.ToString()
    }
    if ($Value -is [double] -or $Value -is [single]) {
        if ([double]::IsNaN($Value) -or [double]::IsInfinity($Value)) { throw 'non-finite number' }
        return ([double]$Value).ToString('R', [System.Globalization.CultureInfo]::InvariantCulture)
    }
    if ($Value -is [int] -or $Value -is [long] -or $Value -is [uint32] -or $Value -is [uint64] -or
        $Value -is [int16] -or $Value -is [uint16] -or $Value -is [byte] -or $Value -is [decimal]) {
        return ([decimal]$Value).ToString([System.Globalization.CultureInfo]::InvariantCulture)
    }
    if ($Value -is [System.Collections.IDictionary]) {
        $keys = @($Value.Keys | ForEach-Object { [string]$_ })
        [Array]::Sort($keys, [System.StringComparer]::Ordinal)
        $parts = foreach ($k in $keys) { (ConvertTo-RefuteCanonicalJson $k) + ':' + (ConvertTo-RefuteCanonicalJson $Value[$k]) }
        return '{' + (@($parts) -join ',') + '}'
    }
    if ($Value -is [System.Management.Automation.PSCustomObject]) {
        $map = [ordered]@{}
        foreach ($p in $Value.PSObject.Properties) { $map[$p.Name] = $p.Value }
        return ConvertTo-RefuteCanonicalJson $map
    }
    if ($Value -is [System.Collections.IEnumerable]) {
        $parts = foreach ($item in $Value) { ConvertTo-RefuteCanonicalJson $item }
        return '[' + (@($parts) -join ',') + ']'
    }
    throw "cannot serialize a value of type $($Value.GetType().FullName)"
}

function Get-RefuteSha256Text {
    param([string]$Text)
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try {
        $bytes = $sha.ComputeHash([System.Text.Encoding]::UTF8.GetBytes($Text))
    } finally { $sha.Dispose() }
    return -join ($bytes | ForEach-Object { $_.ToString('x2') })
}

function Get-RefuteVmPlanSha256 {
    param([System.Collections.IDictionary]$Plan)
    return Get-RefuteSha256Text (ConvertTo-RefuteCanonicalJson $Plan)
}

function Get-RefuteVmCallerRecord {
    # The connecting account (PSSenderInfo.UserInfo.Identity.Name; empty outside a
    # remote session) and the account the session runs as (the JEA virtual account).
    param($SenderInfo, [string]$RunAsUser)
    $connected = ''
    if ($null -ne $SenderInfo -and $null -ne $SenderInfo.UserInfo -and $null -ne $SenderInfo.UserInfo.Identity) {
        $connected = [string]$SenderInfo.UserInfo.Identity.Name
    }
    return [ordered]@{ ConnectedUser = $connected; RunAsUser = $RunAsUser }
}

function New-RefuteVmChange {
    param([string]$Item, $Before, $After)
    return [ordered]@{ Item = $Item; Before = $Before; After = $After }
}

function Get-RefuteVmStoragePath {
    # Where Hyper-V stores the VM. New-VM -Path <VmRoot> keeps the VM's files in
    # <VmRoot>\<VmName>, and Get-VM reports that folder as its Path: observed on the
    # maintainer's host on 2026-10-17 (jea-registration.md, the incident of operation 4); the
    # reference page of New-VM only says -Path "specifies the directory to store the files".
    # VmName is lowercase letters, digits and hyphens (Test-RefuteVmConfig), so the folder
    # stays inside VmRoot.
    param([System.Collections.IDictionary]$Config)
    return "$($Config.VmRoot)\$($Config.VmName)"
}

function Resolve-RefuteVmTarget {
    # The VM these scripts own, or the reason it cannot be used. Divergence from what the
    # scripts set up stops the operation; nothing is corrected silently. Refusal may quote
    # values read from the host (a path, a switch name); Category is a fixed text that
    # quotes none, for the reason of a result that is not reached.
    param([System.Collections.IDictionary]$Config, [System.Collections.IDictionary]$Observed, [string]$Operation)
    $named = @($Observed.Vms | Where-Object { $_.Name -ieq $Config.VmName })
    if ($named.Count -eq 0) { return @{ Vm = $null; Refusal = "no VM named '$($Config.VmName)'"; Category = 'no VM of that name' } }
    if ($named.Count -gt 1) { return @{ Vm = $null; Refusal = "more than one VM named '$($Config.VmName)'"; Category = 'more than one VM of that name' } }
    $vm = $named[0]
    if ([string]::IsNullOrEmpty($Observed.RecordedVmId)) {
        return @{ Vm = $null; Refusal = 'the VM was not created by these scripts (no recorded VMId)'; Category = 'no recorded VMId' }
    }
    if ($vm.VmId -ine $Observed.RecordedVmId) {
        return @{ Vm = $null; Refusal = "VMId $($vm.VmId) differs from the recorded $($Observed.RecordedVmId)"; Category = 'the VMId differs from the recorded one' }
    }
    $storage = Get-RefuteVmStoragePath $Config
    if ($vm.Path -ine $storage) {
        return @{ Vm = $null; Refusal = "the VM is stored in '$($vm.Path)', not in '$storage'"; Category = "the VM is not stored in '$storage'" }
    }
    if ($vm.Generation -ne 2) { return @{ Vm = $null; Refusal = 'the VM is not generation 2'; Category = 'the VM is not generation 2' } }
    $allowedDisks = @($Config.BaseDiskPath)
    foreach ($disk in @($vm.HardDisks)) {
        if ($allowedDisks -inotcontains $disk) { return @{ Vm = $null; Refusal = "unexpected disk attached: $disk"; Category = 'an unexpected disk is attached' } }
    }
    $allowedMedia = @("$($Config.MediaRoot)\$($Config.InstallIsoName)", "$($Config.MediaRoot)\$($Config.SeedIsoName)")
    foreach ($dvd in @($vm.DvdDrives)) {
        # an empty drive ('') is allowed; it is listed, and DetachInstallMedia removes it
        if ($dvd -and $allowedMedia -inotcontains $dvd) { return @{ Vm = $null; Refusal = "unexpected DVD media: $dvd"; Category = 'unexpected DVD media' } }
    }
    if ($Operation -ne 'DisconnectNetwork') {
        foreach ($adapter in @($vm.NetworkAdapters)) {
            if (-not [string]::IsNullOrEmpty($adapter.SwitchName)) {
                return @{ Vm = $null; Refusal = "network adapter '$($adapter.Name)' is connected to '$($adapter.SwitchName)' (phase 1: no network)"; Category = 'a network adapter is connected (phase 1: no network)' }
            }
        }
    }
    return @{ Vm = $vm; Refusal = $null; Category = $null }
}

function New-RefuteVmPlan {
    # The plan of one operation: its target, the changes it would make (each with the
    # value observed before and the value after), whether it is already done, or why it
    # is refused. It also holds the observed preconditions (host settings, files, the
    # recorded state and the whole record of the target VM), so a change to any of them
    # between the simulation and the real call changes the PlanSha256. The plan holds no
    # time and no identity: the same configuration and observed state give the same hash.
    param(
        [string]$Operation,
        [System.Collections.IDictionary]$Config,
        [System.Collections.IDictionary]$Observed,
        [string]$MediaSha256 = '',
        [int]$Percent = 0,
        [string]$ServiceGuid = ''
    )
    if (-not $script:RefuteVmOperationTable.Contains($Operation)) { throw "unknown operation: $Operation" }
    $spec = $script:RefuteVmOperationTable[$Operation]
    $argument = $null
    if ($spec.Argument -eq 'MediaSha256') { $argument = [ordered]@{ MediaSha256 = $MediaSha256 } }
    if ($spec.Argument -eq 'Percent') { $argument = [ordered]@{ Percent = $Percent } }
    if ($spec.Argument -eq 'ServiceGuid') { $argument = [ordered]@{ ServiceGuid = $ServiceGuid } }
    $plan = [ordered]@{
        Operation    = $Operation
        Argument     = $argument
        ConfigSha256 = Get-RefuteSha256Text (ConvertTo-RefuteCanonicalJson $Config)
        Target       = [ordered]@{ VmName = $Config.VmName; VmId = $null }
        Preconditions = [ordered]@{
            Host                  = $Observed.Host
            Files                 = $Observed.Files
            RecordedVmId          = $Observed.RecordedVmId
            RecordedSeedIsoSha256 = $Observed.RecordedSeedIsoSha256
            TargetVm              = $null
        }
        Changes      = @()
        AlreadyDone  = $false
        Refusal      = $null
    }
    $refuse = { param($why) $plan.Refusal = $why; return $plan }

    $problems = Test-RefuteVmConfig $Config
    if ($problems.Count) { return (& $refuse ('invalid configuration: ' + ($problems -join '; '))) }
    if ($spec.Argument -ne 'MediaSha256' -and $MediaSha256) { return (& $refuse 'this operation takes no MediaSha256') }
    if ($spec.Argument -ne 'Percent' -and $Percent -ne 0) { return (& $refuse 'this operation takes no Percent') }
    if ($spec.Argument -ne 'ServiceGuid' -and $ServiceGuid) { return (& $refuse 'this operation takes no ServiceGuid') }
    if ($spec.Argument -eq 'ServiceGuid' -and $ServiceGuid -cnotmatch '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$') { return (& $refuse 'ServiceGuid must be a lowercase GUID') }
    if ($spec.Argument -eq 'MediaSha256' -and $MediaSha256 -cnotmatch '^[0-9a-f]{64}$') { return (& $refuse 'MediaSha256 must be 64 lowercase hex digits') }
    if ($spec.Argument -eq 'Percent' -and ($Percent -lt 1 -or $Percent -gt 100)) { return (& $refuse 'Percent must be from 1 to 100') }

    $vm = $null
    if ($spec.VmState.Count) {
        $target = Resolve-RefuteVmTarget -Config $Config -Observed $Observed -Operation $Operation
        if ($target.Refusal) { return (& $refuse $target.Refusal) }
        $vm = $target.Vm
        $plan.Target.VmId = $vm.VmId
        $plan.Preconditions.TargetVm = $vm
        if ($spec.VmState -notcontains $vm.State) {
            return (& $refuse "the VM is $($vm.State); this operation needs: $($spec.VmState -join ' or ')")
        }
    }
    $changes = New-Object System.Collections.Generic.List[object]
    $installMedia = "$($Config.MediaRoot)\$($Config.InstallIsoName)"
    $seedMedia = "$($Config.MediaRoot)\$($Config.SeedIsoName)"

    switch ($Operation) {
        'SetHostPaths' {
            if ($Observed.Host.VirtualMachinePath -ine $Config.HostVirtualMachinePath) {
                $changes.Add((New-RefuteVmChange 'Host.VirtualMachinePath' $Observed.Host.VirtualMachinePath $Config.HostVirtualMachinePath))
            }
            if ($Observed.Host.VirtualHardDiskPath -ine $Config.HostVirtualHardDiskPath) {
                $changes.Add((New-RefuteVmChange 'Host.VirtualHardDiskPath' $Observed.Host.VirtualHardDiskPath $Config.HostVirtualHardDiskPath))
            }
        }
        'DisableEnhancedSessionHost' {
            if ($Observed.Host.EnableEnhancedSessionMode -ne $false) {
                $changes.Add((New-RefuteVmChange 'Host.EnableEnhancedSessionMode' $Observed.Host.EnableEnhancedSessionMode $false))
            }
        }
        'CreateBaseDisk' {
            $disk = $Observed.Files.BaseDisk
            if (-not $disk.Exists) {
                $changes.Add((New-RefuteVmChange 'BaseDisk' 'absent' ("dynamic VHDX of $($Config.BaseDiskSizeBytes) bytes at $($Config.BaseDiskPath)")))
            } elseif ($disk.Format -cne 'VHDX' -or $disk.Type -cne 'Dynamic' -or $disk.SizeBytes -ne $Config.BaseDiskSizeBytes) {
                return (& $refuse "a file at the base disk path is not the configured disk ($($disk.Format), $($disk.Type), $($disk.SizeBytes) bytes); never overwritten")
            }
        }
        'CreateVm' {
            if (@($Observed.Vms | Where-Object { $_.Name -ieq $Config.VmName }).Count) {
                # Already done only for exactly the VM these scripts created: the recorded
                # VMId, stored where Hyper-V puts it, and every other check of
                # Resolve-RefuteVmTarget. Any other VM of that name is refused, never adopted.
                $existing = Resolve-RefuteVmTarget -Config $Config -Observed $Observed -Operation $Operation
                if ($existing.Refusal) { return (& $refuse "a VM named '$($Config.VmName)' already exists and is not the one these scripts created: $($existing.Refusal)") }
                $plan.Target.VmId = $existing.Vm.VmId
                $plan.Preconditions.TargetVm = $existing.Vm
                break
            }
            if (-not [string]::IsNullOrEmpty($Observed.RecordedVmId)) { return (& $refuse "a VMId is already recorded: $($Observed.RecordedVmId)") }
            $changes.Add((New-RefuteVmChange 'VM' 'absent' ("generation 2, stored in $(Get-RefuteVmStoragePath $Config), no disk, network adapter not connected")))
        }
        'SetMemory' {
            if ($vm.DynamicMemoryEnabled -ne $false) { $changes.Add((New-RefuteVmChange 'Memory.DynamicMemoryEnabled' $vm.DynamicMemoryEnabled $false)) }
            if ($vm.MemoryStartup -ne $Config.MemoryBytes) { $changes.Add((New-RefuteVmChange 'Memory.StartupBytes' $vm.MemoryStartup $Config.MemoryBytes)) }
        }
        'SetProcessor' {
            if ($vm.ProcessorCount -ne $Config.ProcessorCount) { $changes.Add((New-RefuteVmChange 'Processor.Count' $vm.ProcessorCount $Config.ProcessorCount)) }
        }
        'SetSecureBoot' {
            if ($vm.SecureBoot -cne 'On') { $changes.Add((New-RefuteVmChange 'Firmware.SecureBoot' $vm.SecureBoot 'On')) }
            if ($vm.SecureBootTemplate -cne $Config.SecureBootTemplate) { $changes.Add((New-RefuteVmChange 'Firmware.SecureBootTemplate' $vm.SecureBootTemplate $Config.SecureBootTemplate)) }
        }
        'DisableCheckpoints' {
            if ($vm.AutomaticCheckpointsEnabled -ne $false) { $changes.Add((New-RefuteVmChange 'AutomaticCheckpointsEnabled' $vm.AutomaticCheckpointsEnabled $false)) }
            if ($vm.CheckpointType -cne 'Disabled') { $changes.Add((New-RefuteVmChange 'CheckpointType' $vm.CheckpointType 'Disabled')) }
        }
        'DisableGuestServiceInterface' {
            # The plan names the service as the host reports it, so the approval shows
            # which service the GUID designates.
            $found = @($vm.IntegrationServices | Where-Object { $_.Id.Split('\')[-1] -ieq $ServiceGuid })
            if ($found.Count -ne 1) { return (& $refuse "expected one integration service with Id ending in $ServiceGuid, found $($found.Count)") }
            if ($found[0].Enabled -ne $false) { $changes.Add((New-RefuteVmChange ("IntegrationService.$ServiceGuid ($($found[0].Name))") $found[0].Enabled $false)) }
        }
        'DisconnectNetwork' {
            foreach ($adapter in @($vm.NetworkAdapters)) {
                if (-not [string]::IsNullOrEmpty($adapter.SwitchName)) {
                    $changes.Add((New-RefuteVmChange ('NetworkAdapter.' + $adapter.Name) $adapter.SwitchName ''))
                }
            }
        }
        'AttachBaseDisk' {
            $disk = $Observed.Files.BaseDisk
            if (-not $disk.Exists) { return (& $refuse 'the base disk does not exist (CreateBaseDisk first)') }
            if ($disk.Format -cne 'VHDX' -or $disk.Type -cne 'Dynamic' -or $disk.SizeBytes -ne $Config.BaseDiskSizeBytes) { return (& $refuse 'the base disk is not the configured disk') }
            if (@($vm.HardDisks) -inotcontains $Config.BaseDiskPath) { $changes.Add((New-RefuteVmChange 'HardDisk' 'none' $Config.BaseDiskPath)) }
        }
        'ImportInstallIso' {
            if ([string]::IsNullOrEmpty($Config.InstallIsoSha256)) { return (& $refuse 'InstallIsoSha256 is not configured yet') }
            if ($MediaSha256 -cne $Config.InstallIsoSha256) { return (& $refuse 'MediaSha256 differs from the configured InstallIsoSha256') }
            if ($Observed.Files.InstallIsoMediaSha256 -ceq $MediaSha256) { break }
            if ($Observed.Files.InstallIsoMediaSha256) { return (& $refuse 'a different install ISO is already in MediaRoot (never overwritten)') }
            if ($Observed.Files.InstallIsoSourceSha256 -cne $MediaSha256) { return (& $refuse 'the install ISO in MediaSource is missing or has another SHA-256') }
            $changes.Add((New-RefuteVmChange 'Media.InstallIso' 'absent' $MediaSha256))
        }
        'ImportSeedIso' {
            if ($Observed.Files.SeedIsoMediaSha256 -ceq $MediaSha256) {
                if ($Observed.RecordedSeedIsoSha256 -cne $MediaSha256) { return (& $refuse 'the seed ISO is in MediaRoot but its hash is not recorded in the state; the maintainer inspects') }
                break
            }
            if ($Observed.Files.SeedIsoMediaSha256) { return (& $refuse 'a different seed ISO is already in MediaRoot (never overwritten)') }
            if ($Observed.Files.SeedIsoSourceSha256 -cne $MediaSha256) { return (& $refuse 'the seed ISO in MediaSource is missing or has another SHA-256') }
            $changes.Add((New-RefuteVmChange 'Media.SeedIso' 'absent' $MediaSha256))
        }
        'AttachInstallMedia' {
            if ($Observed.Files.InstallIsoMediaSha256 -cne $Config.InstallIsoSha256 -or [string]::IsNullOrEmpty($Config.InstallIsoSha256)) { return (& $refuse 'the install ISO in MediaRoot is missing or not the configured one') }
            if ([string]::IsNullOrEmpty($Observed.RecordedSeedIsoSha256) -or $Observed.Files.SeedIsoMediaSha256 -cne $Observed.RecordedSeedIsoSha256) { return (& $refuse 'the seed ISO in MediaRoot is missing or not the imported one') }
            foreach ($media in $installMedia, $seedMedia) {
                if (@($vm.DvdDrives) -inotcontains $media) { $changes.Add((New-RefuteVmChange 'DvdDrive' 'none' $media)) }
            }
        }
        'SetBootFromInstallMedia' {
            if (@($vm.DvdDrives) -inotcontains $installMedia) { return (& $refuse 'the install ISO is not attached (AttachInstallMedia first)') }
            if ($vm.SecureBoot -cne 'On') { return (& $refuse 'Secure Boot is off (SetSecureBoot first)') }
            if ($vm.FirstBootDevice -ine $installMedia) { $changes.Add((New-RefuteVmChange 'Firmware.FirstBootDevice' $vm.FirstBootDevice $installMedia)) }
        }
        'StartVm' {
            if ($vm.SecureBoot -cne 'On' -or $vm.SecureBootTemplate -cne $Config.SecureBootTemplate) { return (& $refuse 'Secure Boot is not on with the configured template') }
            $changes.Add((New-RefuteVmChange 'State' $vm.State 'Running'))
        }
        'StopVm' { $changes.Add((New-RefuteVmChange 'State' $vm.State 'Off')) }
        'DetachInstallMedia' {
            if (@($vm.HardDisks) -inotcontains $Config.BaseDiskPath) { return (& $refuse 'the base disk is not attached') }
            foreach ($dvd in @($vm.DvdDrives)) {
                $shown = $dvd
                if (-not $dvd) { $shown = 'empty drive' }
                $changes.Add((New-RefuteVmChange 'DvdDrive' $shown 'removed'))
            }
            if ($vm.FirstBootDevice -ine $Config.BaseDiskPath) { $changes.Add((New-RefuteVmChange 'Firmware.FirstBootDevice' $vm.FirstBootDevice $Config.BaseDiskPath)) }
        }
        'SetProcessorMaximum' {
            if ($vm.ProcessorMaximum -ne $Percent) { $changes.Add((New-RefuteVmChange 'Processor.Maximum' $vm.ProcessorMaximum $Percent)) }
        }
        'SuspendVm' { $changes.Add((New-RefuteVmChange 'State' $vm.State 'Paused')) }
        'ResumeVm' { $changes.Add((New-RefuteVmChange 'State' $vm.State 'Running')) }
        'SaveVm' { $changes.Add((New-RefuteVmChange 'State' $vm.State 'Saved')) }
    }
    $plan.Changes = $changes.ToArray()
    $plan.AlreadyDone = ($changes.Count -eq 0)
    return $plan
}

function Get-RefuteVmPlanReachedProblem {
    # After the mutation: why the state the plan asked for is not observed, or '' when it
    # is. State changes compare the VM's state; CreateVm needs one VM of that name that
    # passes every check of Resolve-RefuteVmTarget (recorded VMId, stored where Hyper-V puts
    # it, generation 2, no foreign disk, media or network); every other operation must now
    # plan as already done. The reason is always given, so a "not reached" result is never
    # empty (the incident of operation 4, 2026-10-17). It is built from fixed texts,
    # configured values, VMIds, VM states, counts and change item names only: it never
    # quotes a path, a name or a message read from the host (Codex review of #142); the
    # simulation of the operation shows the full refusal.
    param(
        [System.Collections.IDictionary]$Plan,
        [System.Collections.IDictionary]$Config,
        [System.Collections.IDictionary]$ObservedAfter,
        [string]$MediaSha256 = '',
        [int]$Percent = 0,
        [string]$ServiceGuid = ''
    )
    $targetStates = @{ StartVm = 'Running'; StopVm = 'Off'; SuspendVm = 'Paused'; ResumeVm = 'Running'; SaveVm = 'Saved' }
    if ($targetStates.ContainsKey($Plan.Operation)) {
        $vm = @($ObservedAfter.Vms | Where-Object { $_.VmId -ieq $Plan.Target.VmId })
        if ($vm.Count -ne 1) { return "expected one VM with VMId $($Plan.Target.VmId) after the operation, found $($vm.Count)" }
        $wanted = $targetStates[$Plan.Operation]
        if ($vm[0].State -ne $wanted) { return "the VM is $($vm[0].State), not $wanted" }
        return ''
    }
    if ($Plan.Operation -eq 'CreateVm') {
        $vm = @($ObservedAfter.Vms | Where-Object { $_.Name -ieq $Config.VmName })
        if ($vm.Count -ne 1) { return "expected one VM named '$($Config.VmName)' after New-VM, found $($vm.Count)" }
        $target = Resolve-RefuteVmTarget -Config $Config -Observed $ObservedAfter -Operation 'CreateVm'
        if ($null -ne $target.Refusal) { return "the VM after New-VM is not the one these scripts set up: $($target.Category)" }
        return ''
    }
    $again = New-RefuteVmPlan -Operation $Plan.Operation -Config $Config -Observed $ObservedAfter -MediaSha256 $MediaSha256 -Percent $Percent -ServiceGuid $ServiceGuid
    if ($null -ne $again.Refusal) { return 'the plan after the operation is refused (simulate the operation to see the reason)' }
    if (-not $again.AlreadyDone) {
        # the items of an integration service or a network adapter carry a name read from
        # the host; only their kind is named here
        $items = @($again.Changes) | ForEach-Object { [string]$_.Item -replace '^(IntegrationService|NetworkAdapter)\..*$', '$1' }
        return "the plan after the operation still has $(@($again.Changes).Count) change(s): " + ($items -join ', ')
    }
    return ''
}

function Get-RefuteVmFailureText {
    # The reason of a failed operation, for the log and the caller. A text this module
    # throws (throw '<text>': a RuntimeException whose error id is the text itself) is kept:
    # it quotes configured values only. Any other error, from Hyper-V or the system, is
    # reported by type and HRESULT, never by its message, which can quote host paths or
    # account names (as in Update-RefuteVmConfig.ps1; Codex review of #142).
    param([System.Management.Automation.ErrorRecord]$ErrorRecord)
    $e = $ErrorRecord.Exception
    if ($e.GetType() -eq [System.Management.Automation.RuntimeException] -and $ErrorRecord.FullyQualifiedErrorId -ceq $e.Message) {
        return $e.Message
    }
    return ('{0} (HRESULT 0x{1:X8})' -f $e.GetType().Name, $e.HResult)
}

function Test-RefuteVmPlanReached {
    # Whether the state the plan asked for is observed (Get-RefuteVmPlanReachedProblem).
    param(
        [System.Collections.IDictionary]$Plan,
        [System.Collections.IDictionary]$Config,
        [System.Collections.IDictionary]$ObservedAfter,
        [string]$MediaSha256 = '',
        [int]$Percent = 0,
        [string]$ServiceGuid = ''
    )
    return ((Get-RefuteVmPlanReachedProblem -Plan $Plan -Config $Config -ObservedAfter $ObservedAfter -MediaSha256 $MediaSha256 -Percent $Percent -ServiceGuid $ServiceGuid) -eq '')
}
