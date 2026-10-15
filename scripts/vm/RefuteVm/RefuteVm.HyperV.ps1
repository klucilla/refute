# Hyper-V side of the RefuteVm module: it reads the observed state and performs the
# one mutation of an approved plan. Every call goes through the JEA endpoint
# (scripts/vm/README.md); nothing here is run by the maintainer's own account.
# Windows PowerShell 5.1.

Set-StrictMode -Version 2.0

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
    param([System.Collections.IDictionary]$Config, [string]$VmId, [string]$SeedIsoSha256)
    $map = [ordered]@{ VmId = $VmId; SeedIsoSha256 = $SeedIsoSha256 }
    $utf8 = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Config.StateFile, (ConvertTo-RefuteCanonicalJson $map), $utf8)
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

function Get-RefuteVmObserved {
    # The state the plan is computed from. Names are compared exactly in Core: Get-VM is
    # called without -Name, so no wildcard is ever interpreted.
    param([System.Collections.IDictionary]$Config, [switch]$IncludeMedia)
    $vmHost = Get-VMHost -ErrorAction Stop
    $recorded = Read-RefuteVmState -Config $Config
    $vms = foreach ($vm in @(Get-VM -ErrorAction Stop)) {
        $memory = Get-VMMemory -VM $vm -ErrorAction Stop
        $processor = Get-VMProcessor -VM $vm -ErrorAction Stop
        $firmware = $null
        if ($vm.Generation -eq 2) { $firmware = Get-VMFirmware -VM $vm -ErrorAction Stop }
        $firstBoot = 'none'
        if ($firmware -and $firmware.BootOrder.Count) {
            $device = $firmware.BootOrder[0].Device
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
            NetworkAdapters             = @(Get-VMNetworkAdapter -VM $vm -ErrorAction Stop | ForEach-Object {
                    [ordered]@{ Name = [string]$_.Name; SwitchName = [string]$_.SwitchName } })
            HardDisks                   = @(Get-VMHardDiskDrive -VM $vm -ErrorAction Stop | ForEach-Object { [string]$_.Path })
            DvdDrives                   = @(Get-VMDvdDrive -VM $vm -ErrorAction Stop | Where-Object { $_.Path } | ForEach-Object { [string]$_.Path })
        }
    }
    $files = [ordered]@{
        BaseDiskExists         = (Test-Path -LiteralPath $Config.BaseDiskPath -PathType Leaf)
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
            if ($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) { throw "reparse point refused: $current" }
        }
        $current = Split-Path -Parent $current
    }
}

function Invoke-RefuteVmMutation {
    # The single administrative action of the plan. No other action is taken here.
    param(
        [System.Collections.IDictionary]$Config,
        [System.Collections.IDictionary]$Observed,
        [System.Collections.IDictionary]$Plan,
        [string]$MediaSha256,
        [int]$Percent,
        [string]$ServiceGuid
    )
    $vm = $null
    if ($Plan.Target.VmId) { $vm = Get-VM -Id $Plan.Target.VmId -ErrorAction Stop }
    $installMedia = "$($Config.MediaRoot)\$($Config.InstallIsoName)"
    $seedMedia = "$($Config.MediaRoot)\$($Config.SeedIsoName)"
    foreach ($p in $Config.VmRoot, $Config.BaseDiskPath, $Config.MediaRoot, $Config.HostVirtualHardDiskPath) { Assert-RefuteNoReparsePoint $p }

    switch ($Plan.Operation) {
        'SetHostPaths' { Set-VMHost -VirtualMachinePath $Config.HostVirtualMachinePath -VirtualHardDiskPath $Config.HostVirtualHardDiskPath -ErrorAction Stop }
        'DisableEnhancedSessionHost' { Set-VMHost -EnableEnhancedSessionMode $false -ErrorAction Stop }
        'CreateBaseDisk' { New-VHD -Path $Config.BaseDiskPath -SizeBytes $Config.BaseDiskSizeBytes -Dynamic -ErrorAction Stop | Out-Null }
        'CreateVm' {
            $created = New-VM -Name $Config.VmName -Generation 2 -Path $Config.VmRoot -MemoryStartupBytes $Config.MemoryBytes -NoVHD -ErrorAction Stop
            Write-RefuteVmState -Config $Config -VmId ([string]$created.VMId).ToLowerInvariant() -SeedIsoSha256 $Observed.RecordedSeedIsoSha256
        }
        'SetMemory' { Set-VMMemory -VM $vm -DynamicMemoryEnabled $false -StartupBytes $Config.MemoryBytes -ErrorAction Stop }
        'SetProcessor' { Set-VMProcessor -VM $vm -Count $Config.ProcessorCount -ErrorAction Stop }
        'SetSecureBoot' { Set-VMFirmware -VM $vm -EnableSecureBoot On -SecureBootTemplate $Config.SecureBootTemplate -ErrorAction Stop }
        'DisableCheckpoints' { Set-VM -VM $vm -AutomaticCheckpointsEnabled $false -CheckpointType Disabled -ErrorAction Stop }
        'DisableGuestServiceInterface' {
            $service = @(Get-VMIntegrationService -VM $vm -ErrorAction Stop | Where-Object { ([string]$_.Id).Split('\')[-1] -ieq $ServiceGuid })
            if ($service.Count -ne 1) { throw 'the integration service changed since the plan' }
            Disable-VMIntegrationService -VMIntegrationService $service[0] -ErrorAction Stop
        }
        'DisconnectNetwork' { Get-VMNetworkAdapter -VM $vm -ErrorAction Stop | Disconnect-VMNetworkAdapter -ErrorAction Stop }
        'AttachBaseDisk' { Add-VMHardDiskDrive -VM $vm -Path $Config.BaseDiskPath -ErrorAction Stop }
        'ImportInstallIso' {
            Copy-Item -LiteralPath "$($Config.MediaSource)\$($Config.InstallIsoName)" -Destination $installMedia -ErrorAction Stop
            if ((Get-RefuteFileSha256 $installMedia) -cne $MediaSha256) { throw 'the copied install ISO has another SHA-256; it is left in place for the maintainer to inspect' }
        }
        'ImportSeedIso' {
            Copy-Item -LiteralPath "$($Config.MediaSource)\$($Config.SeedIsoName)" -Destination $seedMedia -ErrorAction Stop
            if ((Get-RefuteFileSha256 $seedMedia) -cne $MediaSha256) { throw 'the copied seed ISO has another SHA-256; it is left in place for the maintainer to inspect' }
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
            if ($dvd.Count -ne 1) { throw 'the install DVD drive changed since the plan' }
            Set-VMFirmware -VM $vm -FirstBootDevice $dvd[0] -ErrorAction Stop
        }
        'StartVm' { Start-VM -VM $vm -ErrorAction Stop }
        'StopVm' { Stop-VM -VM $vm -Force -ErrorAction Stop }
        'DetachInstallMedia' {
            $disk = @(Get-VMHardDiskDrive -VM $vm -ErrorAction Stop | Where-Object { [string]$_.Path -ieq $Config.BaseDiskPath })
            if ($disk.Count -ne 1) { throw 'the base disk changed since the plan' }
            Set-VMFirmware -VM $vm -FirstBootDevice $disk[0] -ErrorAction Stop
            Get-VMDvdDrive -VM $vm -ErrorAction Stop | Remove-VMDvdDrive -ErrorAction Stop
        }
        'SetProcessorMaximum' { Set-VMProcessor -VM $vm -Maximum $Percent -ErrorAction Stop }
        'SuspendVm' { Suspend-VM -VM $vm -ErrorAction Stop }
        'ResumeVm' { Resume-VM -VM $vm -ErrorAction Stop }
        'SaveVm' { Save-VM -VM $vm -ErrorAction Stop }
        default { throw "no mutation for operation $($Plan.Operation)" }
    }
}
