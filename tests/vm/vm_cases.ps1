# Synthetic checks of scripts/vm (WP6 phase 1), with no Hyper-V: parse every script,
# read the data files, list the commands each script calls, and run the pure logic of
# RefuteVm.Core.ps1 on synthetic observed states. Prints one JSON object; the
# assertions are in tests/test_vm_scripts.py. Windows PowerShell 5.1 and PowerShell 7.
param([Parameter(Mandatory = $true)][string]$Root)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2.0

$vmDir = Join-Path $Root 'scripts/vm'
$moduleDir = Join-Path $vmDir 'RefuteVm'
$out = [ordered]@{ Parse = [ordered]@{}; Data = [ordered]@{}; Commands = [ordered]@{}; ValidateSets = [ordered]@{}; Cases = @() }

# ---- parse, data files, commands --------------------------------------------------------
$scripts = @(Get-ChildItem -LiteralPath $vmDir -Recurse -File | Where-Object { $_.Extension -in '.ps1', '.psm1' } | Sort-Object FullName)
foreach ($file in $scripts) {
    $tokens = $null; $errors = $null
    $ast = [System.Management.Automation.Language.Parser]::ParseFile($file.FullName, [ref]$tokens, [ref]$errors)
    $name = $file.FullName.Substring($vmDir.Length + 1).Replace('\', '/')
    $out.Parse[$name] = @($errors | ForEach-Object { $_.Message })
    $out.Commands[$name] = @($ast.FindAll({ param($n) $n -is [System.Management.Automation.Language.CommandAst] }, $true) |
            ForEach-Object { $_.GetCommandName() } | Where-Object { $_ } | Sort-Object -Unique)
    foreach ($param in $ast.FindAll({ param($n) $n -is [System.Management.Automation.Language.ParameterAst] }, $true)) {
        if ($param.Name.VariablePath.UserPath -ne 'Operation') { continue }
        foreach ($attr in $param.Attributes) {
            if ($attr.TypeName.Name -eq 'ValidateSet') {
                $out.ValidateSets[$name] = @($attr.PositionalArguments | ForEach-Object { $_.Value })
            }
        }
    }
}
foreach ($file in @(Get-ChildItem -LiteralPath $vmDir -Recurse -File | Where-Object { $_.Extension -in '.psd1', '.psrc' } | Sort-Object FullName)) {
    $name = $file.FullName.Substring($vmDir.Length + 1).Replace('\', '/')
    try { Import-PowerShellDataFile -LiteralPath $file.FullName | Out-Null; $out.Data[$name] = 'ok' } catch { $out.Data[$name] = $_.Exception.Message }
}

# ---- pure logic ------------------------------------------------------------------------------
. (Join-Path $moduleDir 'RefuteVm.Core.ps1')
$out['OperationTable'] = @(Get-RefuteVmOperationNames)
$cases = New-Object System.Collections.Generic.List[object]
function Add-Case([string]$Name, [bool]$Ok, $Detail = $null) { $cases.Add([ordered]@{ Name = $Name; Ok = $Ok; Detail = [string]$Detail }) }

$config = Import-PowerShellDataFile -LiteralPath (Join-Path $moduleDir 'RefuteVm.Config.psd1')
$problems = Test-RefuteVmConfig $config
Add-Case 'config of the repository is valid' ($problems.Count -eq 0) ($problems -join '; ')

function Copy-Config([hashtable]$Changes) {
    $c = @{}; foreach ($k in $config.Keys) { $c[$k] = $config[$k] }
    foreach ($k in $Changes.Keys) { $c[$k] = $Changes[$k] }
    return $c
}
foreach ($bad in @(
        @{ BaseDiskPath = 'K:\refute.vhdx' }, @{ VmRoot = 'C:\Hyper-V\..\Windows' }, @{ MediaSource = 'C:\Users\Public' },
        @{ ProcessorCount = 32 }, @{ MemoryBytes = 1000 }, @{ SecureBootTemplate = 'MicrosoftWindows' },
        @{ InstallIsoSha256 = 'ABC' }, @{ StateFile = 'C:\Temp\vm.json' }, @{ VmName = 'Refute VM' },
        @{ HostVirtualMachinePath = 'C:\Hyper-V\Other' }, @{ Extra = 1 })) {
    $p = Test-RefuteVmConfig (Copy-Config $bad)
    Add-Case ("config refused: " + (($bad.Keys | ForEach-Object { $_ }) -join ',')) ($p.Count -gt 0) ($p -join '; ')
}
$missing = Copy-Config @{}; $missing.Remove('OperationLog')
Add-Case 'config refused: missing key' ((Test-RefuteVmConfig $missing).Count -gt 0)

foreach ($pathCase in @(
        @('C:\Hyper-V\x', $true), @('C:\Hyper-V', $true), @('C:\Hyper-Vx', $false), @('C:\Hyper-V\..\Windows', $false),
        @('C:\Hyper-V\.\x', $false), @('\\server\share\x', $false), @('C:\Hyper-V\a*', $false), @('C:\Hyper-V\a:b', $false),
        @('C:\Hyper-V\x.', $false), @('C:\Hyper-V\x\', $false), @('C:/Hyper-V/x', $false), @('K:\Hyper-V\x', $false))) {
    $got = Test-RefuteSafePath -Path $pathCase[0] -Root 'C:\Hyper-V'
    Add-Case ("safe path $($pathCase[0]) = $($pathCase[1])") ($got -eq $pathCase[1]) $got
}

# The script itself stays ASCII (Windows PowerShell reads a file without BOM as ANSI).
$json = ConvertTo-RefuteCanonicalJson ([ordered]@{ b = 1; a = @('x', $true, $null); c = ([string][char]0x00E7) + '"\'; d = 0.1 })
Add-Case 'canonical JSON' ($json -ceq '{"a":["x",true,null],"b":1,"c":"\u00e7\"\\","d":0.1}') $json

function New-Observed {
    return [ordered]@{
        Host                  = [ordered]@{ VirtualMachinePath = 'C:\ProgramData\Microsoft\Windows\Hyper-V'; VirtualHardDiskPath = 'C:\Users\Public\Documents\Hyper-V\Virtual Hard Disks'; EnableEnhancedSessionMode = $true }
        Vms                   = @()
        Files                 = [ordered]@{ BaseDiskExists = $false; InstallIsoMediaSha256 = ''; InstallIsoSourceSha256 = ''; SeedIsoMediaSha256 = ''; SeedIsoSourceSha256 = '' }
        RecordedVmId          = ''
        RecordedSeedIsoSha256 = ''
    }
}
$vmId = '0b1c2d3e-4f50-6172-8394-a5b6c7d8e9f0'
$gsi = '0a1b2c3d-1111-2222-3333-444455556666'
function New-Vm {
    return [ordered]@{
        Name = 'refute-vm'; VmId = $vmId; State = 'Off'; Generation = 2; Path = 'C:\Hyper-V\refute-vm'
        MemoryStartup = [long]1073741824; DynamicMemoryEnabled = $true; ProcessorCount = 1; ProcessorMaximum = 100
        SecureBoot = 'On'; SecureBootTemplate = 'MicrosoftWindows'; FirstBootDevice = 'none'
        AutomaticCheckpointsEnabled = $true; CheckpointType = 'Standard'
        IntegrationServices = @([ordered]@{ Id = "Microsoft:$vmId\$gsi"; Name = 'Guest Service Interface'; Enabled = $true })
        NetworkAdapters = @([ordered]@{ Name = 'Network Adapter'; SwitchName = '' })
        HardDisks = @(); DvdDrives = @()
    }
}
function Plan([string]$Op, $Obs, $Cfg = $config, [string]$Media = '', [int]$Pct = 0, [string]$Guid = '') {
    return New-RefuteVmPlan -Operation $Op -Config $Cfg -Observed $Obs -MediaSha256 $Media -Percent $Pct -ServiceGuid $Guid
}

$obs = New-Observed
$p = Plan 'SetHostPaths' $obs
Add-Case 'SetHostPaths plans two changes' ($null -eq $p.Refusal -and $p.Changes.Count -eq 2 -and -not $p.AlreadyDone)
$h1 = Get-RefuteVmPlanSha256 $p; $h2 = Get-RefuteVmPlanSha256 (Plan 'SetHostPaths' (New-Observed))
Add-Case 'plan hash is deterministic' ($h1 -ceq $h2 -and $h1 -cmatch '^[0-9a-f]{64}$')
$obs2 = New-Observed; $obs2.Host.VirtualHardDiskPath = 'D:\other'
Add-Case 'plan hash changes with the observed state' ($h1 -cne (Get-RefuteVmPlanSha256 (Plan 'SetHostPaths' $obs2)))
$done = New-Observed; $done.Host.VirtualMachinePath = 'C:\Hyper-V'; $done.Host.VirtualHardDiskPath = 'C:\Hyper-V\Virtual Hard Disks'
Add-Case 'SetHostPaths already done' ((Plan 'SetHostPaths' $done).AlreadyDone)

Add-Case 'CreateVm on an empty host' ($null -eq (Plan 'CreateVm' (New-Observed)).Refusal)
$o = New-Observed; $v = New-Vm; $v.Name = 'REFUTE-VM'; $o.Vms = @($v)
Add-Case 'CreateVm refused: a VM with that name exists (any case)' ($null -ne (Plan 'CreateVm' $o).Refusal)
$o = New-Observed; $o.RecordedVmId = $vmId
Add-Case 'CreateVm refused: a VMId is recorded' ($null -ne (Plan 'CreateVm' $o).Refusal)

Add-Case 'SetMemory refused: no VM' ($null -ne (Plan 'SetMemory' (New-Observed)).Refusal)
$o = New-Observed; $o.Vms = @(New-Vm)
Add-Case 'SetMemory refused: VM not created by the scripts' ((Plan 'SetMemory' $o).Refusal -like '*not created by these scripts*')
$o.RecordedVmId = 'ffffffff-ffff-ffff-ffff-ffffffffffff'
Add-Case 'SetMemory refused: other VMId' ((Plan 'SetMemory' $o).Refusal -like '*differs from the recorded*')
$o.RecordedVmId = $vmId
$p = Plan 'SetMemory' $o
Add-Case 'SetMemory plans two changes' ($null -eq $p.Refusal -and $p.Changes.Count -eq 2 -and $p.Target.VmId -eq $vmId)
$o.Vms[0].State = 'Running'
Add-Case 'SetMemory refused: VM running' ((Plan 'SetMemory' $o).Refusal -like '*needs: Off*')
$o.Vms[0].State = 'Off'; $o.Vms[0].DynamicMemoryEnabled = $false; $o.Vms[0].MemoryStartup = [long]$config.MemoryBytes
Add-Case 'SetMemory already done' ((Plan 'SetMemory' $o).AlreadyDone)
$o2 = New-Observed; $o2.RecordedVmId = $vmId; $v = New-Vm; $v.HardDisks = @('C:\Hyper-V\other.vhdx'); $o2.Vms = @($v)
Add-Case 'refused: unexpected disk' ((Plan 'SetProcessor' $o2).Refusal -like '*unexpected disk*')
$o2 = New-Observed; $o2.RecordedVmId = $vmId; $v = New-Vm; $v.DvdDrives = @('C:\Hyper-V\refute-vm\media\other.iso'); $o2.Vms = @($v)
Add-Case 'refused: unexpected DVD media' ((Plan 'SetProcessor' $o2).Refusal -like '*unexpected DVD*')
$o2 = New-Observed; $o2.RecordedVmId = $vmId; $v = New-Vm; $v.Path = 'C:\Elsewhere'; $o2.Vms = @($v)
Add-Case 'refused: VM stored elsewhere' ((Plan 'SetProcessor' $o2).Refusal -like '*stored in*')
$o2 = New-Observed; $o2.RecordedVmId = $vmId; $v = New-Vm; $v.NetworkAdapters = @([ordered]@{ Name = 'Network Adapter'; SwitchName = 'Default Switch' }); $o2.Vms = @($v)
Add-Case 'refused: connected network (phase 1)' ((Plan 'SetProcessor' $o2).Refusal -like '*no network*')
$p = Plan 'DisconnectNetwork' $o2
Add-Case 'DisconnectNetwork plans the disconnection' ($null -eq $p.Refusal -and $p.Changes.Count -eq 1)

$o = New-Observed; $o.RecordedVmId = $vmId; $o.Vms = @(New-Vm)
Add-Case 'DisableGuestServiceInterface refused: no ServiceGuid' ($null -ne (Plan 'DisableGuestServiceInterface' $o).Refusal)
Add-Case 'DisableGuestServiceInterface refused: uppercase GUID' ($null -ne (Plan 'DisableGuestServiceInterface' $o -Guid $gsi.ToUpper()).Refusal)
Add-Case 'DisableGuestServiceInterface refused: unknown GUID' ($null -ne (Plan 'DisableGuestServiceInterface' $o -Guid '99999999-1111-2222-3333-444455556666').Refusal)
$p = Plan 'DisableGuestServiceInterface' $o -Guid $gsi
Add-Case 'DisableGuestServiceInterface names the service' ($null -eq $p.Refusal -and $p.Changes[0].Item -like '*Guest Service Interface*')
Add-Case 'refused: a ServiceGuid for another operation' ($null -ne (Plan 'SetProcessor' $o -Guid $gsi).Refusal)
Add-Case 'refused: Percent 0 for SetProcessorMaximum' ($null -ne (Plan 'SetProcessorMaximum' $o).Refusal)
Add-Case 'refused: Percent for another operation' ($null -ne (Plan 'SetProcessor' $o -Pct 50).Refusal)
$p = Plan 'SetProcessorMaximum' $o -Pct 50
Add-Case 'SetProcessorMaximum plans the change' ($null -eq $p.Refusal -and $p.Changes[0].After -eq 50)
$o.Vms[0].SecureBoot = 'Off'
Add-Case 'StartVm refused: Secure Boot off' ($null -ne (Plan 'StartVm' $o).Refusal)

$sha = 'a' * 64; $other = 'b' * 64
Add-Case 'ImportInstallIso refused: hash not configured' ((Plan 'ImportInstallIso' (New-Observed) -Media $sha).Refusal -like '*not configured*')
$cfg = Copy-Config @{ InstallIsoSha256 = $sha }
Add-Case 'ImportInstallIso refused: another hash' ($null -ne (Plan 'ImportInstallIso' (New-Observed) $cfg $other).Refusal)
$o = New-Observed; $o.Files.InstallIsoSourceSha256 = $other
Add-Case 'ImportInstallIso refused: source differs' ($null -ne (Plan 'ImportInstallIso' $o $cfg $sha).Refusal)
$o = New-Observed; $o.Files.InstallIsoSourceSha256 = $sha; $o.Files.InstallIsoMediaSha256 = $other
Add-Case 'ImportInstallIso refused: never overwrites' ((Plan 'ImportInstallIso' $o $cfg $sha).Refusal -like '*never overwritten*')
$o = New-Observed; $o.Files.InstallIsoSourceSha256 = $sha
Add-Case 'ImportInstallIso plans the copy' ((Plan 'ImportInstallIso' $o $cfg $sha).Changes.Count -eq 1)
$o.Files.InstallIsoMediaSha256 = $sha
Add-Case 'ImportInstallIso already done' ((Plan 'ImportInstallIso' $o $cfg $sha).AlreadyDone)
Add-Case 'refused: MediaSha256 not lowercase hex' ($null -ne (Plan 'ImportSeedIso' (New-Observed) -Media ('A' * 64)).Refusal)
Add-Case 'refused: MediaSha256 for another operation' ($null -ne (Plan 'CreateVm' (New-Observed) -Media $sha).Refusal)

$o = New-Observed; $o.RecordedVmId = $vmId; $v = New-Vm; $v.State = 'Running'; $o.Vms = @($v)
$p = Plan 'StopVm' $o
$after = New-Observed; $after.RecordedVmId = $vmId; $v2 = New-Vm; $v2.State = 'Off'; $after.Vms = @($v2)
Add-Case 'StopVm reached when Off' (Test-RefuteVmPlanReached -Plan $p -Config $config -ObservedAfter $after)
Add-Case 'StopVm not reached when Running' (-not (Test-RefuteVmPlanReached -Plan $p -Config $config -ObservedAfter $o))

$out.Cases = $cases.ToArray()
ConvertTo-RefuteCanonicalJson $out
