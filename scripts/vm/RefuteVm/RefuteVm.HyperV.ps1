# Hyper-V side of the RefuteVm module: it reads the observed state and performs the
# one mutation of an approved plan. Every call goes through the JEA endpoint
# (scripts/vm/README.md); nothing here is run by the maintainer's own account.
# Windows PowerShell 5.1.

Set-StrictMode -Version 2.0

# The text of the last failure this module raised itself (Stop-RefuteVmOperation), for the
# log (Get-RefuteVmFailureText); RefuteVm.psm1 clears it before each mutation.
$script:RefuteVmFailureReason = ''

function Stop-RefuteVmOperation {
    # Fails the operation with a text of this module. The text is recorded in the module's
    # own scope before it is thrown, so the log can tell it from an error of Hyper-V or of
    # the system, which is reported by type and HRESULT only (Codex review of #142). Every
    # text given here quotes configured values, operation names and hashes only.
    param([string]$Reason)
    $script:RefuteVmFailureReason = $Reason
    throw $Reason
}

function Read-RefuteVmState {
    param([System.Collections.IDictionary]$Config)
    $state = @{ RecordedVmId = ''; RecordedSeedIsoSha256 = '' }
    if (Test-Path -LiteralPath $Config.StateFile -PathType Leaf) {
        $data = [System.IO.File]::ReadAllText($Config.StateFile) | ConvertFrom-Json
        if ($data.PSObject.Properties.Name -contains 'VmId') { $state.RecordedVmId = [string]$data.VmId }
        if ($data.PSObject.Properties.Name -contains 'SeedIsoSha256') { $state.RecordedSeedIsoSha256 = [string]$data.SeedIsoSha256 }
    }
    return $state
}

function Write-RefuteVmState {
    # Written to a new file, then moved over the state file in one step, so a reader
    # never sees a half-written state.
    param([System.Collections.IDictionary]$Config, [string]$VmId, [string]$SeedIsoSha256)
    $map = [ordered]@{ VmId = $VmId; SeedIsoSha256 = $SeedIsoSha256 }
    $utf8 = New-Object System.Text.UTF8Encoding($false)
    $next = $Config.StateFile + '.next'
    [System.IO.File]::WriteAllText($next, (ConvertTo-RefuteCanonicalJson $map), $utf8)
    if (Test-Path -LiteralPath $Config.StateFile -PathType Leaf) {
        [System.IO.File]::Replace($next, $Config.StateFile, [NullString]::Value)
    } else {
        [System.IO.File]::Move($next, $Config.StateFile)
    }
}

function Enter-RefuteVmLock {
    # One operation at a time on this host: the lock file is opened with no sharing and
    # kept open until the operation ends; a second session is refused at once.
    param([System.Collections.IDictionary]$Config)
    $path = Join-Path (Split-Path -Parent $Config.StateFile) 'operation.lock'
    try {
        return [System.IO.File]::Open($path, [System.IO.FileMode]::OpenOrCreate, [System.IO.FileAccess]::ReadWrite, [System.IO.FileShare]::None)
    } catch {
        throw 'another RefuteVm operation is in progress; try again when it ends'
    }
}

function Copy-RefuteVerifiedFile {
    # Copies Source to Destination only if its bytes have the given SHA-256. The source
    # is opened with no write sharing (it cannot change while it is read), the bytes are
    # hashed as they are copied into Destination.partial (created new, never
    # overwritten), and only a matching copy is moved to Destination (which must not
    # exist). A copy that does not match stays as .partial for the maintainer to inspect.
    param([string]$Source, [string]$Destination, [string]$Sha256)
    foreach ($p in $Source, $Destination) {
        $item = Get-Item -LiteralPath $p -Force -ErrorAction SilentlyContinue
        if ($item -and ($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint)) { Stop-RefuteVmOperation "reparse point refused: $p" }
    }
    if (Test-Path -LiteralPath $Destination) { Stop-RefuteVmOperation "the destination already exists: $Destination" }
    $partial = $Destination + '.partial'
    $sha = [System.Security.Cryptography.SHA256]::Create()
    $in = [System.IO.File]::Open($Source, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::Read)
    try {
        $out = [System.IO.File]::Open($partial, [System.IO.FileMode]::CreateNew, [System.IO.FileAccess]::Write, [System.IO.FileShare]::None)
        try {
            $buffer = New-Object byte[] 1048576
            while (($read = $in.Read($buffer, 0, $buffer.Length)) -gt 0) {
                [void]$sha.TransformBlock($buffer, 0, $read, $null, 0)
                $out.Write($buffer, 0, $read)
            }
            [void]$sha.TransformFinalBlock((New-Object byte[] 0), 0, 0)
        } finally { $out.Dispose() }
    } finally { $in.Dispose() }
    $actual = -join ($sha.Hash | ForEach-Object { $_.ToString('x2') })
    $sha.Dispose()
    if ($actual -cne $Sha256) { Stop-RefuteVmOperation "the copied bytes have SHA-256 $actual, not $Sha256; left at $partial" }
    [System.IO.File]::Move($partial, $Destination)
}

function Write-RefuteVmLog {
    # One JSON line per record, appended, UTF-8 without BOM.
    param([System.Collections.IDictionary]$Config, [System.Collections.IDictionary]$Record)
    $utf8 = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::AppendAllText($Config.OperationLog, (ConvertTo-RefuteCanonicalJson $Record) + "`n", $utf8)
}

function Get-RefuteFileSha256 {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return '' }
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Test-RefuteVmmsInstalled {
    # True when the Virtual Machine Management service (vmms) is installed: its service key
    # exists. A key that cannot be read counts as installed, so that only a host where the
    # service is certainly absent gets the message of Get-RefuteVmHostChecked.
    try {
        $key = [Microsoft.Win32.Registry]::LocalMachine.OpenSubKey('SYSTEM\CurrentControlSet\Services\vmms')
    } catch {
        return $true
    }
    if ($null -eq $key) { return $false }
    $key.Close()
    return $true
}

function Get-RefuteVmHostChecked {
    # The first Hyper-V call. A host without the Hyper-V service (with the PowerShell module
    # only) stops here with a message of its own. Every other
    # failure keeps its own error: a command that is not recognized (a missing import, a
    # defect; tests/test_vm_jea_integration.py fails on it), and any failure on a host where
    # the service is installed (access denied, for example).
    try {
        return Get-VMHost -ErrorAction Stop
    } catch [System.Management.Automation.CommandNotFoundException] {
        throw
    } catch {
        $failure = $_
        if (-not (Test-RefuteVmmsInstalled)) {
            # the error by type and HRESULT, never by its message (Get-RefuteVmFailureText)
            Stop-RefuteVmOperation ('Hyper-V is not available on this host (the vmms service is not installed): {0} (HRESULT 0x{1:X8})' -f $failure.Exception.GetType().Name, $failure.Exception.HResult)
        }
        throw $failure
    }
}

function Get-RefuteVmObserved {
    # The state the plan is computed from. Names are compared exactly in Core: Get-VM is
    # called without -Name, so no wildcard is ever interpreted.
    param([System.Collections.IDictionary]$Config, [switch]$IncludeMedia)
    $vmHost = Get-RefuteVmHostChecked
    $recorded = Read-RefuteVmState -Config $Config
    $vms = foreach ($vm in @(Get-VM -ErrorAction Stop)) {
        $memory = Get-VMMemory -VM $vm -ErrorAction Stop
        $processor = Get-VMProcessor -VM $vm -ErrorAction Stop
        $firmware = $null
        if ($vm.Generation -eq 2) { $firmware = Get-VMFirmware -VM $vm -ErrorAction Stop }
        $firstBoot = 'none'
        # @(...): a missing or single boot entry is still a list (StrictMode, PowerShell 5.1)
        $bootOrder = @(if ($firmware) { $firmware.BootOrder | Where-Object { $null -ne $_ } })
        if ($bootOrder.Count) {
            $device = $bootOrder[0].Device
            if ($device -and $device.PSObject.Properties.Name -contains 'Path' -and $device.Path) { $firstBoot = [string]$device.Path }
        }
        [ordered]@{
            Name                        = [string]$vm.Name
            VmId                        = ([string]$vm.VMId).ToLowerInvariant()
            State                       = [string]$vm.State
            Generation                  = [int]$vm.Generation
            Path                        = [string]$vm.Path
            MemoryStartup               = [long]$memory.Startup
            DynamicMemoryEnabled        = [bool]$memory.DynamicMemoryEnabled
            ProcessorCount              = [int]$processor.Count
            ProcessorMaximum            = [int]$processor.Maximum
            SecureBoot                  = $(if ($firmware) { [string]$firmware.SecureBoot } else { 'n/a' })
            SecureBootTemplate          = $(if ($firmware) { [string]$firmware.SecureBootTemplate } else { 'n/a' })
            FirstBootDevice             = $firstBoot
            AutomaticCheckpointsEnabled = [bool]$vm.AutomaticCheckpointsEnabled
            CheckpointType              = [string]$vm.CheckpointType
            IntegrationServices         = @(Get-VMIntegrationService -VM $vm -ErrorAction Stop | ForEach-Object {
                    [ordered]@{ Id = [string]$_.Id; Name = [string]$_.Name; Enabled = [bool]$_.Enabled } })
            # each adapter with its Id, its switch (by name and Id) and the port's extended
            # ACLs, normalized (phase 2, W6.5)
            NetworkAdapters             = @(Get-VMNetworkAdapter -VM $vm -ErrorAction Stop | ForEach-Object {
                    $adapter = $_
                    [ordered]@{
                        Name       = [string]$adapter.Name
                        Id         = [string]$adapter.Id
                        SwitchName = [string]$adapter.SwitchName
                        SwitchId   = $(if ($adapter.SwitchId) { ([string]$adapter.SwitchId).ToLowerInvariant() } else { '' })
                        Acls       = @(Get-VMNetworkAdapterExtendedAcl -VMNetworkAdapter $adapter -ErrorAction Stop | ForEach-Object { ConvertTo-RefuteAclRule $_ })
                    } })
            HardDisks                   = @(Get-VMHardDiskDrive -VM $vm -ErrorAction Stop | ForEach-Object { [string]$_.Path })
            DvdDrives                   = @(Get-VMDvdDrive -VM $vm -ErrorAction Stop | ForEach-Object { [string]$_.Path })
        }
    }
    $baseDisk = [ordered]@{ Exists = $false; Format = ''; Type = ''; SizeBytes = 0 }
    if (Test-Path -LiteralPath $Config.BaseDiskPath -PathType Leaf) {
        $vhd = Get-VHD -Path $Config.BaseDiskPath -ErrorAction Stop
        $baseDisk = [ordered]@{ Exists = $true; Format = [string]$vhd.VhdFormat; Type = [string]$vhd.VhdType; SizeBytes = [long]$vhd.Size }
    }
    $files = [ordered]@{
        BaseDisk               = $baseDisk
        InstallIsoMediaSha256  = ''
        InstallIsoSourceSha256 = ''
        SeedIsoMediaSha256     = ''
        SeedIsoSourceSha256    = ''
    }
    if ($IncludeMedia) {
        $files.InstallIsoMediaSha256 = Get-RefuteFileSha256 "$($Config.MediaRoot)\$($Config.InstallIsoName)"
        $files.InstallIsoSourceSha256 = Get-RefuteFileSha256 "$($Config.MediaSource)\$($Config.InstallIsoName)"
        $files.SeedIsoMediaSha256 = Get-RefuteFileSha256 "$($Config.MediaRoot)\$($Config.SeedIsoName)"
        $files.SeedIsoSourceSha256 = Get-RefuteFileSha256 "$($Config.MediaSource)\$($Config.SeedIsoName)"
    }
    return [ordered]@{
        Host                  = [ordered]@{
            VirtualMachinePath        = [string]$vmHost.VirtualMachinePath
            VirtualHardDiskPath       = [string]$vmHost.VirtualHardDiskPath
            EnableEnhancedSessionMode = [bool]$vmHost.EnableEnhancedSessionMode
        }
        Vms                   = @($vms)
        # every virtual switch of the host, by Id, name and type (Get-VMSwitch without -Name,
        # so no wildcard is interpreted)
        Switches              = @(Get-VMSwitch -ErrorAction Stop | ForEach-Object {
                [ordered]@{ Id = ([string]$_.Id).ToLowerInvariant(); Name = [string]$_.Name; SwitchType = [string]$_.SwitchType } })
        Files                 = $files
        RecordedVmId          = $recorded.RecordedVmId
        RecordedSeedIsoSha256 = $recorded.RecordedSeedIsoSha256
    }
}

function Assert-RefuteNoReparsePoint {
    # Refuses a path whose existing part goes through a junction or a symbolic link.
    param([string]$Path)
    $current = $Path
    while ($current -and $current.Length -gt 3) {
        if (Test-Path -LiteralPath $current) {
            $item = Get-Item -LiteralPath $current -Force
            if ($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) { Stop-RefuteVmOperation "reparse point refused: $current" }
        }
        $current = Split-Path -Parent $current
    }
}

function Get-RefuteVmPlannedAdapter {
    # The VM's one network adapter, read again: the one the plan observed (by Id) and still
    # disconnected, or the operation fails without a change.
    param($Vm, [System.Collections.IDictionary]$Plan)
    $planned = @(Get-RefuteMember $Plan.Preconditions.TargetVm 'NetworkAdapters' @())
    $nowAdapters = @(Get-VMNetworkAdapter -VM $Vm -ErrorAction Stop)
    if ($planned.Count -ne 1 -or $nowAdapters.Count -ne 1) { Stop-RefuteVmOperation 'the VM does not have the one network adapter of the plan' }
    $plannedId = [string](Get-RefuteMember $planned[0] 'Id' '')
    if ([string]::IsNullOrEmpty($plannedId) -or ([string]$nowAdapters[0].Id) -ine $plannedId) { Stop-RefuteVmOperation 'the network adapter is not the one of the plan' }
    if (-not [string]::IsNullOrEmpty([string]$nowAdapters[0].SwitchName) -or $nowAdapters[0].SwitchId) { Stop-RefuteVmOperation 'the network adapter is connected; it must be disconnected' }
    return $nowAdapters[0]
}

function Get-RefuteVmConfiguredSwitch {
    # The configured switch, read again by Id: it must exist once, be internal and have the
    # configured name.
    param([System.Collections.IDictionary]$Config)
    if ([string]::IsNullOrEmpty($Config.NetworkSwitchId)) { Stop-RefuteVmOperation 'NetworkSwitchId is not configured' }
    $found = @(Get-VMSwitch -ErrorAction Stop | Where-Object { ([string]$_.Id) -ieq $Config.NetworkSwitchId })
    if ($found.Count -ne 1) { Stop-RefuteVmOperation 'the configured switch does not exist' }
    if ([string]$found[0].SwitchType -cne 'Internal' -or [string]$found[0].Name -cne $Config.NetworkSwitchName) { Stop-RefuteVmOperation 'the configured switch is not internal or has another name' }
    return $found[0]
}

function Test-RefuteVmAdapterProfile {
    # True when the adapter's extended ACLs, read now, equal one of the profiles.
    param([System.Collections.IDictionary]$Config, $Adapter)
    $acls = @(Get-VMNetworkAdapterExtendedAcl -VMNetworkAdapter $Adapter -ErrorAction Stop | ForEach-Object { ConvertTo-RefuteAclRule $_ })
    return [bool](Get-RefuteVmProfileInForce -Config $Config -Adapter @{ Acls = $acls })
}

function Invoke-RefuteVmMutation {
    # The single administrative action of the plan. No other action is taken here.
    param(
        [System.Collections.IDictionary]$Config,
        [System.Collections.IDictionary]$Observed,
        [System.Collections.IDictionary]$Plan,
        [string]$MediaSha256,
        [int]$Percent,
        [string]$ServiceGuid,
        [string]$Profile = ''
    )
    $vm = $null
    if ($Plan.Target.VmId) { $vm = Get-VM -Id $Plan.Target.VmId -ErrorAction Stop }
    $installMedia = "$($Config.MediaRoot)\$($Config.InstallIsoName)"
    $seedMedia = "$($Config.MediaRoot)\$($Config.SeedIsoName)"
    foreach ($p in $Config.VmRoot, (Get-RefuteVmStoragePath $Config), $Config.BaseDiskPath, $Config.MediaRoot, $Config.HostVirtualHardDiskPath) { Assert-RefuteNoReparsePoint $p }

    switch ($Plan.Operation) {
        'SetHostPaths' { Set-VMHost -VirtualMachinePath $Config.HostVirtualMachinePath -VirtualHardDiskPath $Config.HostVirtualHardDiskPath -ErrorAction Stop }
        'DisableEnhancedSessionHost' { Set-VMHost -EnableEnhancedSessionMode $false -ErrorAction Stop }
        'CreateBaseDisk' { New-VHD -Path $Config.BaseDiskPath -SizeBytes $Config.BaseDiskSizeBytes -Dynamic -ErrorAction Stop | Out-Null }
        'CreateVm' {
            # -Path is VmRoot: Hyper-V stores the VM in VmRoot\VmName (Get-RefuteVmStoragePath)
            $created = New-VM -Name $Config.VmName -Generation 2 -Path $Config.VmRoot -MemoryStartupBytes $Config.MemoryBytes -NoVHD -ErrorAction Stop
            Write-RefuteVmState -Config $Config -VmId ([string]$created.VMId).ToLowerInvariant() -SeedIsoSha256 $Observed.RecordedSeedIsoSha256
        }
        'SetMemory' { Set-VMMemory -VM $vm -DynamicMemoryEnabled $false -StartupBytes $Config.MemoryBytes -ErrorAction Stop }
        'SetProcessor' { Set-VMProcessor -VM $vm -Count $Config.ProcessorCount -ErrorAction Stop }
        'SetSecureBoot' { Set-VMFirmware -VM $vm -EnableSecureBoot On -SecureBootTemplate $Config.SecureBootTemplate -ErrorAction Stop }
        'DisableCheckpoints' { Set-VM -VM $vm -AutomaticCheckpointsEnabled $false -CheckpointType Disabled -ErrorAction Stop }
        'DisableGuestServiceInterface' {
            $service = @(Get-VMIntegrationService -VM $vm -ErrorAction Stop | Where-Object { ([string]$_.Id).Split('\')[-1] -ieq $ServiceGuid })
            if ($service.Count -ne 1) { Stop-RefuteVmOperation 'the integration service changed since the plan' }
            Disable-VMIntegrationService -VMIntegrationService $service[0] -ErrorAction Stop
        }
        'DisconnectNetwork' { Get-VMNetworkAdapter -VM $vm -ErrorAction Stop | Disconnect-VMNetworkAdapter -ErrorAction Stop }
        'AttachBaseDisk' { Add-VMHardDiskDrive -VM $vm -Path $Config.BaseDiskPath -ErrorAction Stop }
        'ImportInstallIso' {
            Assert-RefuteNoReparsePoint $Config.MediaSource
            Copy-RefuteVerifiedFile -Source "$($Config.MediaSource)\$($Config.InstallIsoName)" -Destination $installMedia -Sha256 $MediaSha256
        }
        'ImportSeedIso' {
            Assert-RefuteNoReparsePoint $Config.MediaSource
            Copy-RefuteVerifiedFile -Source "$($Config.MediaSource)\$($Config.SeedIsoName)" -Destination $seedMedia -Sha256 $MediaSha256
            Write-RefuteVmState -Config $Config -VmId $Observed.RecordedVmId -SeedIsoSha256 $MediaSha256
        }
        'AttachInstallMedia' {
            $attached = @(Get-VMDvdDrive -VM $vm -ErrorAction Stop | ForEach-Object { [string]$_.Path })
            foreach ($media in $installMedia, $seedMedia) {
                if ($attached -inotcontains $media) { Add-VMDvdDrive -VM $vm -Path $media -ErrorAction Stop }
            }
        }
        'SetBootFromInstallMedia' {
            $dvd = @(Get-VMDvdDrive -VM $vm -ErrorAction Stop | Where-Object { [string]$_.Path -ieq $installMedia })
            if ($dvd.Count -ne 1) { Stop-RefuteVmOperation 'the install DVD drive changed since the plan' }
            Set-VMFirmware -VM $vm -FirstBootDevice $dvd[0] -ErrorAction Stop
        }
        'StartVm' { Start-VM -VM $vm -ErrorAction Stop }
        # A guest shutdown through the integration service, never forced and never a
        # power cut: if the guest does not shut down cleanly the operation fails.
        'StopVm' { Stop-VM -VM $vm -Confirm:$false -ErrorAction Stop }
        'DetachInstallMedia' {
            $disk = @(Get-VMHardDiskDrive -VM $vm -ErrorAction Stop | Where-Object { [string]$_.Path -ieq $Config.BaseDiskPath })
            if ($disk.Count -ne 1) { Stop-RefuteVmOperation 'the base disk changed since the plan' }
            Set-VMFirmware -VM $vm -FirstBootDevice $disk[0] -ErrorAction Stop
            Get-VMDvdDrive -VM $vm -ErrorAction Stop | Remove-VMDvdDrive -ErrorAction Stop
        }
        'SetProcessorMaximum' { Set-VMProcessor -VM $vm -Maximum $Percent -ErrorAction Stop }
        'SuspendVm' { Suspend-VM -VM $vm -ErrorAction Stop }
        'ResumeVm' { Resume-VM -VM $vm -ErrorAction Stop }
        'SaveVm' { Save-VM -VM $vm -ErrorAction Stop }
        'SetPortProfile' {
            # with the adapter disconnected (checked by the plan, and again here): every entry
            # removed, then the profile's entries added; the check after reads the list back
            $adapter = Get-RefuteVmPlannedAdapter -Vm $vm -Plan $Plan
            Get-VMNetworkAdapterExtendedAcl -VMNetworkAdapter $adapter -ErrorAction Stop | Remove-VMNetworkAdapterExtendedAcl -ErrorAction Stop
            foreach ($rule in (Get-RefuteVmAclProfile -Config $Config -Profile $Profile)) {
                # IsolationID 0 (no isolation) is the default and is not passed
                $add = @{
                    VMNetworkAdapter = $adapter; Action = $rule.Action; Direction = $rule.Direction
                    RemoteIPAddress = $rule.RemoteIPAddress; Weight = $rule.Weight; Stateful = $rule.Stateful
                    ErrorAction = 'Stop'
                }
                if ($rule.Protocol -ne 'ANY') { $add.Protocol = $rule.Protocol }
                if ($rule.LocalPort) { $add.LocalPort = $rule.LocalPort }
                if ($rule.RemotePort) { $add.RemotePort = $rule.RemotePort }
                Add-VMNetworkAdapterExtendedAcl @add | Out-Null
            }
        }
        'ConnectNetwork' {
            # Everything the plan checked is read again right before the connection (Codex
            # review of c3c06db: the module's lock does not stop a change made outside it): the
            # same adapter, still disconnected, its ACLs equal to a profile, and the configured
            # switch by Id, internal, with the configured name. A failure here leaves the
            # adapter disconnected. After the connection the ACLs and the switch are read once
            # more; if they no longer hold, the adapter is disconnected again before failing.
            $adapter = Get-RefuteVmPlannedAdapter -Vm $vm -Plan $Plan
            $switch = Get-RefuteVmConfiguredSwitch -Config $Config
            if (-not (Test-RefuteVmAdapterProfile -Config $Config -Adapter $adapter)) { Stop-RefuteVmOperation "the port's ACLs equal no profile; the adapter stays disconnected" }
            Connect-VMNetworkAdapter -VMNetworkAdapter $adapter -VMSwitch $switch -ErrorAction Stop
            $connected = @(Get-VMNetworkAdapter -VM $vm -ErrorAction Stop | Where-Object { ([string]$_.Id) -ieq ([string]$adapter.Id) })
            $held = ($connected.Count -eq 1 -and ([string]$connected[0].SwitchId) -ieq $Config.NetworkSwitchId -and (Test-RefuteVmAdapterProfile -Config $Config -Adapter $connected[0]))
            if (-not $held) {
                Get-VMNetworkAdapter -VM $vm -ErrorAction Stop | Disconnect-VMNetworkAdapter -ErrorAction Stop
                Stop-RefuteVmOperation 'after the connection the adapter, its switch or its ACLs were not the planned ones; the adapter was disconnected again'
            }
        }
        default { Stop-RefuteVmOperation "no mutation for operation $($Plan.Operation)" }
    }
}
