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

function Resolve-RefuteVmTarget {
    # The VM these scripts own, or the reason it cannot be used. Divergence from what the
    # scripts set up stops the operation; nothing is corrected silently.
    param([System.Collections.IDictionary]$Config, [System.Collections.IDictionary]$Observed, [string]$Operation)
    $named = @($Observed.Vms | Where-Object { $_.Name -ieq $Config.VmName })
    if ($named.Count -eq 0) { return @{ Vm = $null; Refusal = "no VM named '$($Config.VmName)'" } }
    if ($named.Count -gt 1) { return @{ Vm = $null; Refusal = "more than one VM named '$($Config.VmName)'" } }
    $vm = $named[0]
    if ([string]::IsNullOrEmpty($Observed.RecordedVmId)) {
        return @{ Vm = $null; Refusal = 'the VM was not created by these scripts (no recorded VMId)' }
    }
    if ($vm.VmId -ine $Observed.RecordedVmId) {
        return @{ Vm = $null; Refusal = "VMId $($vm.VmId) differs from the recorded $($Observed.RecordedVmId)" }
    }
    if ($vm.Path -ine $Config.VmRoot) { return @{ Vm = $null; Refusal = "the VM is stored in '$($vm.Path)', not in '$($Config.VmRoot)'" } }
    if ($vm.Generation -ne 2) { return @{ Vm = $null; Refusal = 'the VM is not generation 2' } }
    $allowedDisks = @($Config.BaseDiskPath)
    foreach ($disk in @($vm.HardDisks)) {
        if ($allowedDisks -inotcontains $disk) { return @{ Vm = $null; Refusal = "unexpected disk attached: $disk" } }
    }
    $allowedMedia = @("$($Config.MediaRoot)\$($Config.InstallIsoName)", "$($Config.MediaRoot)\$($Config.SeedIsoName)")
    foreach ($dvd in @($vm.DvdDrives)) {
        # an empty drive ('') is allowed; it is listed, and DetachInstallMedia removes it
        if ($dvd -and $allowedMedia -inotcontains $dvd) { return @{ Vm = $null; Refusal = "unexpected DVD media: $dvd" } }
    }
    if ($Operation -ne 'DisconnectNetwork') {
        foreach ($adapter in @($vm.NetworkAdapters)) {
            if (-not [string]::IsNullOrEmpty($adapter.SwitchName)) {
                return @{ Vm = $null; Refusal = "network adapter '$($adapter.Name)' is connected to '$($adapter.SwitchName)' (phase 1: no network)" }
            }
        }
    }
    return @{ Vm = $vm; Refusal = $null }
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
            if (@($Observed.Vms | Where-Object { $_.Name -ieq $Config.VmName }).Count) { return (& $refuse "a VM named '$($Config.VmName)' already exists") }
            if (-not [string]::IsNullOrEmpty($Observed.RecordedVmId)) { return (& $refuse "a VMId is already recorded: $($Observed.RecordedVmId)") }
            $changes.Add((New-RefuteVmChange 'VM' 'absent' ("generation 2, stored in $($Config.VmRoot), no disk, network adapter not connected")))
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

function Test-RefuteVmPlanReached {
    # After the mutation: whether the state the plan asked for is observed. State
    # changes compare the VM's state; CreateVm needs the VM and its recorded VMId; every
    # other operation must now plan as already done.
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
        return ($vm.Count -eq 1 -and $vm[0].State -eq $targetStates[$Plan.Operation])
    }
    if ($Plan.Operation -eq 'CreateVm') {
        $vm = @($ObservedAfter.Vms | Where-Object { $_.Name -ieq $Config.VmName })
        return ($vm.Count -eq 1 -and $vm[0].VmId -ieq $ObservedAfter.RecordedVmId -and $vm[0].Path -ieq $Config.VmRoot)
    }
    $again = New-RefuteVmPlan -Operation $Plan.Operation -Config $Config -Observed $ObservedAfter -MediaSha256 $MediaSha256 -Percent $Percent -ServiceGuid $ServiceGuid
    return ($null -eq $again.Refusal -and $again.AlreadyDone)
}
