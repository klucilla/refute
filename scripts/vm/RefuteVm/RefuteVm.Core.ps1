# Pure logic of the RefuteVm module: the operation table, the checks of the
# configuration and of the paths, and the plan of one operation computed from the
# configuration and an observed state. Nothing here calls Hyper-V or writes a file, so
# it is tested in CI with synthetic observed states (tests/test_vm_scripts.py).
# Windows PowerShell 5.1 and PowerShell 7 compatible.

Set-StrictMode -Version 2.0

# One administrative action per operation. VmState: the states the VM must be in
# (empty: the operation does not need the VM). Argument: none, MediaSha256, Percent,
# ServiceGuid or Profile; no operation takes a path, a VM name, an address or a rule.
# Network: whether the operation may run with the adapter connected (to the configured
# switch, with the port's ACLs equal to a profile; phase 2, wp6-acceptance.md W6.5).
$script:RefuteVmConnectedOperations = @('StartVm', 'StopVm', 'SetProcessorMaximum', 'SuspendVm', 'ResumeVm', 'SaveVm', 'ConnectNetwork')
$script:RefuteVmProfiles = @('build', 'pull')
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
    DisconnectNetwork            = @{ VmState = @('Off', 'Running');    Argument = 'none' }
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
    SetPortProfile               = @{ VmState = @('Off', 'Running');    Argument = 'Profile' }
    ConnectNetwork               = @{ VmState = @('Off', 'Running');    Argument = 'none' }
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
        'SecureBootTemplate', 'StateFile', 'OperationLog',
        'NetworkSwitchName', 'NetworkSwitchId', 'HostAddress', 'VmAddress', 'ProxyAddress', 'ProxyPort'
    foreach ($key in $required) {
        if (-not $Config.Contains($key)) { $problems.Add("missing key: $key") }
    }
    foreach ($key in @($Config.Keys)) {
        if ($required -notcontains $key) { $problems.Add("unknown key: $key") }
    }
    if ($problems.Count) { return , $problems.ToArray() }

    if ($Config.ConfigVersion -ne 2) { $problems.Add('ConfigVersion must be 2') }
    # phase 2 network (the maintainer's decisions of 2026-10-17): the internal switch, by
    # name and by the Id the host gave it ('' until it exists), and the fixed /29
    if ($Config.NetworkSwitchName -cnotmatch '^[a-z][a-z0-9-]{2,30}$') { $problems.Add('NetworkSwitchName must be lowercase letters, digits and hyphens') }
    if ($Config.NetworkSwitchId -cnotmatch '^([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})?$') { $problems.Add('NetworkSwitchId must be empty or a lowercase GUID') }
    foreach ($key in 'HostAddress', 'VmAddress', 'ProxyAddress') {
        if ($Config[$key] -cnotmatch '^10\.231\.71\.[1-6]$') { $problems.Add("$key must be an address of 10.231.71.0/29") }
    }
    if (@($Config.HostAddress, $Config.VmAddress, $Config.ProxyAddress | Select-Object -Unique).Count -ne 3) { $problems.Add('HostAddress, VmAddress and ProxyAddress must differ') }
    if ($Config.ProxyPort -isnot [int] -or $Config.ProxyPort -lt 1 -or $Config.ProxyPort -gt 65535) { $problems.Add('ProxyPort must be an integer from 1 to 65535') }
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

function Get-RefuteMember {
    # A member of an observed record, or $Default when the record has none (StrictMode:
    # records observed before phase 2, and synthetic ones, have no switch or ACL fields).
    param($Object, [string]$Name, $Default = $null)
    if ($null -eq $Object) { return $Default }
    if ($Object -is [System.Collections.IDictionary]) {
        if ($Object.Contains($Name)) { return $Object[$Name] }
        return $Default
    }
    if ($Object.PSObject.Properties.Name -contains $Name) { return $Object.$Name }
    return $Default
}

function New-RefuteVmAclRule {
    # One extended ACL entry, every field present and normalized, so that a profile and the
    # list read back from the host compare as text (ConvertTo-RefuteAclRule).
    param([string]$Direction, [string]$Action, [string]$RemoteIPAddress, [string]$Protocol = 'ANY',
        [string]$LocalPort = '', [string]$RemotePort = '', [int]$Weight, [bool]$Stateful = $false)
    return [ordered]@{
        Direction = $Direction; Action = $Action; LocalIPAddress = 'ANY'; RemoteIPAddress = $RemoteIPAddress
        Protocol = $Protocol; LocalPort = $LocalPort; RemotePort = $RemotePort; Weight = $Weight; Stateful = $Stateful
    }
}

function Get-RefuteVmAclProfile {
    # The reviewed port ACLs of the Refute VM's adapter (phase2-network-design.md section
    # 5.1; the maintainer's decisions of 2026-10-17). build: SSH from the host and the
    # proxy; pull: SSH from the host only. Everything else is denied, IPv4 and IPv6 (ANY).
    # Larger weights apply first; stateful entries let the replies of their session return.
    param([System.Collections.IDictionary]$Config, [string]$Profile)
    if ($script:RefuteVmProfiles -notcontains $Profile) { throw "unknown profile: $Profile" }
    $rules = New-Object System.Collections.Generic.List[object]
    $rules.Add((New-RefuteVmAclRule -Direction 'Inbound' -Action 'Allow' -RemoteIPAddress $Config.HostAddress -Protocol 'TCP' -LocalPort '22' -Weight 100 -Stateful $true))
    if ($Profile -eq 'build') {
        $rules.Add((New-RefuteVmAclRule -Direction 'Outbound' -Action 'Allow' -RemoteIPAddress $Config.ProxyAddress -Protocol 'TCP' -RemotePort ([string]$Config.ProxyPort) -Weight 90 -Stateful $true))
    }
    $rules.Add((New-RefuteVmAclRule -Direction 'Inbound' -Action 'Deny' -RemoteIPAddress 'ANY' -Weight 1))
    $rules.Add((New-RefuteVmAclRule -Direction 'Outbound' -Action 'Deny' -RemoteIPAddress 'ANY' -Weight 1))
    return , $rules.ToArray()
}

function ConvertTo-RefuteAclRule {
    # An entry read from the host (Get-VMNetworkAdapterExtendedAcl), in the form of
    # New-RefuteVmAclRule. Wildcards (empty, '*', 0.0.0.0/0, ::/0, ANY) become 'ANY' for
    # addresses and protocols and '' for ports; a host address loses '/32'; protocol numbers
    # 6 and 17 become TCP and UDP. How the host spells an entry is to be observed on it, so
    # the comparison is tolerant of spelling and strict on meaning.
    param($Entry)
    function Norm-Address($a) {
        $t = [string]$a
        if ([string]::IsNullOrWhiteSpace($t) -or @('*', 'ANY', '0.0.0.0/0', '::/0') -icontains $t.Trim()) { return 'ANY' }
        $t = $t.Trim()
        if ($t.EndsWith('/32')) { $t = $t.Substring(0, $t.Length - 3) }
        return $t
    }
    function Norm-Port($p) {
        $t = [string]$p
        if ([string]::IsNullOrWhiteSpace($t) -or @('*', 'ANY') -icontains $t.Trim()) { return '' }
        return $t.Trim()
    }
    $protocol = [string]$Entry.Protocol
    if ([string]::IsNullOrWhiteSpace($protocol) -or @('*', 'ANY') -icontains $protocol.Trim()) { $protocol = 'ANY' }
    elseif ($protocol.Trim() -eq '6') { $protocol = 'TCP' }
    elseif ($protocol.Trim() -eq '17') { $protocol = 'UDP' }
    else { $protocol = $protocol.Trim().ToUpperInvariant() }
    return [ordered]@{
        Direction = [string]$Entry.Direction; Action = [string]$Entry.Action
        LocalIPAddress = Norm-Address $Entry.LocalIPAddress; RemoteIPAddress = Norm-Address $Entry.RemoteIPAddress
        Protocol = $protocol; LocalPort = Norm-Port $Entry.LocalPort; RemotePort = Norm-Port $Entry.RemotePort
        Weight = [int]$Entry.Weight; Stateful = [bool]$Entry.Stateful
    }
}

function Get-RefuteAclListText {
    # A list of rules as one canonical text, independent of the order the host lists them.
    param([object[]]$Rules)
    $texts = @(@($Rules) | ForEach-Object { ConvertTo-RefuteCanonicalJson $_ })
    [Array]::Sort($texts, [System.StringComparer]::Ordinal)
    return '[' + ($texts -join ',') + ']'
}

function Get-RefuteVmProfileInForce {
    # The profile whose list equals the adapter's ACLs, or '' when none does.
    param([System.Collections.IDictionary]$Config, $Adapter)
    $observed = Get-RefuteAclListText @(Get-RefuteMember $Adapter 'Acls' @())
    foreach ($profile in $script:RefuteVmProfiles) {
        if ($observed -ceq (Get-RefuteAclListText (Get-RefuteVmAclProfile -Config $Config -Profile $profile))) { return $profile }
    }
    return ''
}

function Get-RefuteVmNetworkProblem {
    # Why the VM's network is not in a state an operation may meet ('' when it is). Every
    # operation needs one adapter; it may be connected only for the operations allowed
    # connected, to the configured switch (by Id, internal), with the port's ACLs equal to
    # a profile. DisconnectNetwork accepts any state, for containment.
    param([System.Collections.IDictionary]$Config, [System.Collections.IDictionary]$Observed, $Vm, [string]$Operation)
    if ($Operation -eq 'DisconnectNetwork') { return '' }
    $adapters = @($Vm.NetworkAdapters)
    if ($adapters.Count -ne 1) { return "the VM has $($adapters.Count) network adapters, not 1" }
    $adapter = $adapters[0]
    if ([string]::IsNullOrEmpty($adapter.SwitchName) -and [string]::IsNullOrEmpty((Get-RefuteMember $adapter 'SwitchId'))) { return '' }
    if ($script:RefuteVmConnectedOperations -notcontains $Operation) { return 'the network adapter is connected; this operation needs it disconnected (DisconnectNetwork first)' }
    if ([string]::IsNullOrEmpty($Config.NetworkSwitchId) -or (Get-RefuteMember $adapter 'SwitchId') -ine $Config.NetworkSwitchId) { return 'the network adapter is connected to a switch that is not the configured one' }
    $switch = @(Get-RefuteMember $Observed 'Switches' @() | Where-Object { $_.Id -ieq $Config.NetworkSwitchId })
    if ($switch.Count -ne 1 -or $switch[0].SwitchType -cne 'Internal') { return 'the configured switch is missing or not internal' }
    if (-not (Get-RefuteVmProfileInForce -Config $Config -Adapter $adapter)) { return "the port's ACLs equal no profile" }
    return ''
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
    # phase 2 (W6.5): one adapter; connected only to the configured internal switch, with
    # the port's ACLs equal to a profile, and only for the operations allowed connected
    $network = Get-RefuteVmNetworkProblem -Config $Config -Observed $Observed -Vm $vm -Operation $Operation
    if ($network) { return @{ Vm = $null; Refusal = $network; Category = $network } }
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
        [string]$ServiceGuid = '',
        [string]$Profile = ''
    )
    if (-not $script:RefuteVmOperationTable.Contains($Operation)) { throw "unknown operation: $Operation" }
    $spec = $script:RefuteVmOperationTable[$Operation]
    $argument = $null
    if ($spec.Argument -eq 'MediaSha256') { $argument = [ordered]@{ MediaSha256 = $MediaSha256 } }
    if ($spec.Argument -eq 'Percent') { $argument = [ordered]@{ Percent = $Percent } }
    if ($spec.Argument -eq 'ServiceGuid') { $argument = [ordered]@{ ServiceGuid = $ServiceGuid } }
    if ($spec.Argument -eq 'Profile') { $argument = [ordered]@{ Profile = $Profile } }
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
            # the configured switch as the host reports it (Id, name, type), so a change of
            # it between the simulation and the call changes the plan
            Switch                = @(Get-RefuteMember $Observed 'Switches' @() | Where-Object { $Config.NetworkSwitchId -and $_.Id -ieq $Config.NetworkSwitchId })
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
    if ($spec.Argument -ne 'Profile' -and $Profile) { return (& $refuse 'this operation takes no Profile') }
    if ($spec.Argument -eq 'Profile' -and $script:RefuteVmProfiles -cnotcontains $Profile) { return (& $refuse "Profile must be one of: $($script:RefuteVmProfiles -join ', ')") }
    # the media imports act on files, but also need the recorded VM's adapter disconnected
    # (the maintainer's decision of 2026-10-17)
    if (@('ImportInstallIso', 'ImportSeedIso') -contains $Operation -and $Observed.RecordedVmId) {
        foreach ($recorded in @($Observed.Vms | Where-Object { $_.VmId -ieq $Observed.RecordedVmId })) {
            foreach ($adapter in @($recorded.NetworkAdapters)) {
                if (-not [string]::IsNullOrEmpty($adapter.SwitchName) -or -not [string]::IsNullOrEmpty((Get-RefuteMember $adapter 'SwitchId'))) {
                    return (& $refuse 'the network adapter is connected; this operation needs it disconnected (DisconnectNetwork first)')
                }
            }
        }
    }

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
                if (-not [string]::IsNullOrEmpty($adapter.SwitchName) -or -not [string]::IsNullOrEmpty((Get-RefuteMember $adapter 'SwitchId'))) {
                    $changes.Add((New-RefuteVmChange ('NetworkAdapter.' + $adapter.Name) $adapter.SwitchName ''))
                }
            }
        }
        'SetPortProfile' {
            # the whole profile in one call, only with the adapter disconnected (N12)
            $adapters = @($vm.NetworkAdapters)
            if ($adapters.Count -ne 1) { return (& $refuse "the VM has $($adapters.Count) network adapters, not 1") }
            if (-not [string]::IsNullOrEmpty($adapters[0].SwitchName) -or -not [string]::IsNullOrEmpty((Get-RefuteMember $adapters[0] 'SwitchId'))) { return (& $refuse 'the network adapter is connected; the ACLs change only while it is disconnected') }
            $wanted = Get-RefuteVmAclProfile -Config $Config -Profile $Profile
            $before = Get-RefuteAclListText @(Get-RefuteMember $adapters[0] 'Acls' @())
            $after = Get-RefuteAclListText $wanted
            if ($before -cne $after) { $changes.Add((New-RefuteVmChange 'PortAcl' @(Get-RefuteMember $adapters[0] 'Acls' @()) $wanted)) }
        }
        'ConnectNetwork' {
            $adapters = @($vm.NetworkAdapters)
            if ($adapters.Count -ne 1) { return (& $refuse "the VM has $($adapters.Count) network adapters, not 1") }
            if ([string]::IsNullOrEmpty($Config.NetworkSwitchId)) { return (& $refuse 'NetworkSwitchId is not configured yet') }
            $switch = @(Get-RefuteMember $Observed 'Switches' @() | Where-Object { $_.Id -ieq $Config.NetworkSwitchId })
            if ($switch.Count -ne 1) { return (& $refuse 'the configured switch does not exist') }
            if ($switch[0].SwitchType -cne 'Internal' -or $switch[0].Name -cne $Config.NetworkSwitchName) { return (& $refuse 'the configured switch is not internal or has another name') }
            if (-not (Get-RefuteVmProfileInForce -Config $Config -Adapter $adapters[0])) { return (& $refuse "the port's ACLs equal no profile (SetPortProfile first)") }
            if ((Get-RefuteMember $adapters[0] 'SwitchId') -ine $Config.NetworkSwitchId) { $changes.Add((New-RefuteVmChange ('NetworkAdapter.' + $adapters[0].Name) $adapters[0].SwitchName $Config.NetworkSwitchName)) }
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
        [string]$ServiceGuid = '',
        [string]$Profile = ''
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
    $again = New-RefuteVmPlan -Operation $Plan.Operation -Config $Config -Observed $ObservedAfter -MediaSha256 $MediaSha256 -Percent $Percent -ServiceGuid $ServiceGuid -Profile $Profile
    if ($null -ne $again.Refusal) { return 'the plan after the operation is refused (simulate the operation to see the reason)' }
    if (-not $again.AlreadyDone) {
        # the items of an integration service or a network adapter carry a name read from
        # the host (which may hold any character, a line break included); only their kind
        # is named here
        $items = @($again.Changes) | ForEach-Object {
            $item = [string]$_.Item
            if ($item.StartsWith('IntegrationService.', [System.StringComparison]::Ordinal)) { 'IntegrationService' }
            elseif ($item.StartsWith('NetworkAdapter.', [System.StringComparison]::Ordinal)) { 'NetworkAdapter' }
            else { $item }
        }
        return "the plan after the operation still has $(@($again.Changes).Count) change(s): " + ($items -join ', ')
    }
    return ''
}

function Get-RefuteVmFailureText {
    # The reason of a failed operation, for the log and the caller. ModuleReason is the
    # text this module raised itself (Stop-RefuteVmOperation records it in the module's own
    # scope before it throws it; it quotes configured values and hashes only): it is kept
    # when the error carries exactly that text. Any other error, from Hyper-V or the system,
    # is reported by type and HRESULT, never by its message, which can quote host paths or
    # account names (as in Update-RefuteVmConfig.ps1; Codex review of #142, rounds 1 and 2:
    # the type or the error id of an error does not prove where its message comes from).
    # Hyper-V often throws a VirtualizationException with the generic HRESULT 0x80131500 and
    # the real code only in its message (access denied, 0x80070005: the CI run 39039117173 of
    # #142), so the reason also gives the error's category (a fixed enum), the HRESULTs of
    # the inner exceptions, and the codes of a closed, reviewed list (below) found in the
    # message of any of them. Any other number in a message is left out: a path can hold a
    # folder named like a code (Codex review of #142, round 4). A code found in the text is
    # named, not taken as the proven cause.
    param([System.Management.Automation.ErrorRecord]$ErrorRecord, [string]$ModuleReason = '')
    # the reviewed Win32 errors as HRESULTs: access denied, file not found, path not found,
    # sharing violation, file exists, invalid parameter, already exists, disk full, invalid data
    $known = @('0x80070005', '0x80070002', '0x80070003', '0x80070020', '0x80070050', '0x80070057', '0x800700B7', '0x80070070', '0x8007000D')
    $e = $ErrorRecord.Exception
    if ($ModuleReason -and $e.Message -ceq $ModuleReason) { return $ModuleReason }
    $main = '0x{0:X8}' -f $e.HResult
    $codes = New-Object System.Collections.Generic.List[string]
    $x = $e
    while ($null -ne $x) {
        $found = @(('0x{0:X8}' -f $x.HResult))
        $message = [string]$x.Message
        foreach ($code in $known) {
            if ($message.IndexOf($code, [System.StringComparison]::OrdinalIgnoreCase) -ge 0) { $found += $code }
        }
        foreach ($code in $found) {
            if ($code -cne $main -and -not $codes.Contains($code)) { $codes.Add($code) }
        }
        $x = $x.InnerException
    }
    $text = '{0} (HRESULT {1}; category {2}' -f $e.GetType().Name, $main, [string]$ErrorRecord.CategoryInfo.Category
    if ($codes.Count) { $text += '; codes ' + ($codes -join ', ') }
    return $text + ')'
}

function Test-RefuteVmPlanReached {
    # Whether the state the plan asked for is observed (Get-RefuteVmPlanReachedProblem).
    param(
        [System.Collections.IDictionary]$Plan,
        [System.Collections.IDictionary]$Config,
        [System.Collections.IDictionary]$ObservedAfter,
        [string]$MediaSha256 = '',
        [int]$Percent = 0,
        [string]$ServiceGuid = '',
        [string]$Profile = ''
    )
    return ((Get-RefuteVmPlanReachedProblem -Plan $Plan -Config $Config -ObservedAfter $ObservedAfter -MediaSha256 $MediaSha256 -Percent $Percent -ServiceGuid $ServiceGuid -Profile $Profile) -eq '')
}
