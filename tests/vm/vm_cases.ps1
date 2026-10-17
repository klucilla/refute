# Synthetic checks of scripts/vm (WP6 phase 1), with no Hyper-V: parse every script,
# read the data files, list the commands each script calls, and run the pure logic of
# RefuteVm.Core.ps1 on synthetic observed states. Prints one JSON object; the
# assertions are in tests/test_vm_scripts.py. Windows PowerShell 5.1 and PowerShell 7.
param([Parameter(Mandatory = $true)][string]$Root, [Parameter(Mandatory = $true)][string]$WorkDir)
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
# The registration preview: every command and every .NET method called before the apply
# section of Register-RefuteVmEndpoint.ps1, and everywhere in the core it dot-sources
# (tests/test_vm_scripts.py checks them against an allowlist).
$register = Join-Path $vmDir 'Register-RefuteVmEndpoint.ps1'
$coreAst = [System.Management.Automation.Language.Parser]::ParseFile((Join-Path $vmDir 'RefuteRegistration.Core.ps1'), [ref]$null, [ref]$null)

function Get-PreviewSurface([object[]]$Nodes) {
    # Named commands, .NET methods, and the two forms a name list cannot see (Codex review):
    # a command whose name is not static (& $x, . $x), except the reviewed dot-source of
    # the core, and any redirection to a file.
    $commands = @($Nodes | Where-Object { $_ -is [System.Management.Automation.Language.CommandAst] })
    [ordered]@{
        Commands     = @($commands | ForEach-Object { $_.GetCommandName() } | Where-Object { $_ } | Sort-Object -Unique)
        Methods      = @($Nodes | Where-Object { $_ -is [System.Management.Automation.Language.InvokeMemberExpressionAst] } |
                ForEach-Object { [string]$_.Member } | Sort-Object -Unique)
        Unnamed      = @($commands | Where-Object { -not $_.GetCommandName() } |
                Where-Object { $_.Extent.Text -ne ". (Join-Path `$PSScriptRoot 'RefuteRegistration.Core.ps1')" } |
                ForEach-Object { $_.Extent.Text })
        Redirections = @($Nodes | Where-Object { $_ -is [System.Management.Automation.Language.FileRedirectionAst] } |
                ForEach-Object { $_.Extent.Text })
    }
}

function Get-ScriptPreview([string]$Path) {
    # The preview surface of one script: everything before its "# ---- apply" comment, and
    # the whole core it dot-sources.
    $scriptTokens = $null
    $scriptAst = [System.Management.Automation.Language.Parser]::ParseFile($Path, [ref]$scriptTokens, [ref]$null)
    $applyMarker = @($scriptTokens | Where-Object { $_.Kind -eq 'Comment' -and $_.Text.StartsWith('# ---- apply') })
    $at = if ($applyMarker.Count -eq 1) { $applyMarker[0].Extent.StartOffset } else { -1 }
    $nodes = @($scriptAst.FindAll({ param($n) $true }, $true) | Where-Object { $_.Extent.StartOffset -lt $at }) + @($coreAst.FindAll({ param($n) $true }, $true))
    $surface = Get-PreviewSurface $nodes
    $surface['ApplyMarkerFound'] = ($at -ge 0)
    return $surface
}

$out['Preview'] = Get-ScriptPreview $register
$out['PreviewListener'] = Get-ScriptPreview (Join-Path $vmDir 'Remove-RefuteWinRmListener.ps1')
$out['PreviewVmTree'] = Get-ScriptPreview (Join-Path $vmDir 'Set-RefuteVmTreeAcl.ps1')
# negative checks: the collector sees a dynamic command and a file redirection
$probe = [System.Management.Automation.Language.Parser]::ParseInput("& `$someCommand`nWrite-Output 'probe' > `$somewhere", [ref]$null, [ref]$null)
$probeSurface = Get-PreviewSurface @($probe.FindAll({ param($n) $true }, $true))
$out['PreviewProbe'] = [ordered]@{ Unnamed = $probeSurface.Unnamed.Count; Redirections = $probeSurface.Redirections.Count }

# Windows PowerShell 5.1 pattern (the maintainer's first preview run): a variable that
# receives the output of a command or function without @(...) is $null when the output
# is empty, so .Count or [i] on it fails under StrictMode. Every such use is listed.
function Get-UnsafeListUse($Ast) {
    $bare = @{}
    foreach ($a in $Ast.FindAll({ param($n) $n -is [System.Management.Automation.Language.AssignmentStatementAst] }, $true)) {
        $isVariable = $a.Left -is [System.Management.Automation.Language.VariableExpressionAst]
        $isCommand = $a.Right -is [System.Management.Automation.Language.PipelineAst] -and
            $a.Right.PipelineElements[0] -is [System.Management.Automation.Language.CommandAst]
        # New-Object writes exactly one object (a constructor), never an empty output
        $isConstructor = $isCommand -and $a.Right.PipelineElements[0].GetCommandName() -eq 'New-Object'
        if ($isVariable -and $isCommand -and -not $isConstructor) { $bare[$a.Left.VariablePath.UserPath.ToLowerInvariant()] = $true }
    }
    $uses = @()
    foreach ($n in $Ast.FindAll({ param($n) $n -is [System.Management.Automation.Language.MemberExpressionAst] -or $n -is [System.Management.Automation.Language.IndexExpressionAst] }, $true)) {
        $target = if ($n -is [System.Management.Automation.Language.IndexExpressionAst]) { $n.Target } else { $n.Expression }
        if (-not ($target -is [System.Management.Automation.Language.VariableExpressionAst])) { continue }
        if (-not $bare.ContainsKey($target.VariablePath.UserPath.ToLowerInvariant())) { continue }
        $isCount = $n -is [System.Management.Automation.Language.MemberExpressionAst] -and [string]$n.Member -eq 'Count'
        if ($isCount -or $n -is [System.Management.Automation.Language.IndexExpressionAst]) { $uses += $n.Extent.Text }
    }
    return , @($uses | Sort-Object -Unique)
}
$out['UnsafeListUse'] = [ordered]@{}
foreach ($file in $scripts) {
    $fileAst = [System.Management.Automation.Language.Parser]::ParseFile($file.FullName, [ref]$null, [ref]$null)
    $name = $file.FullName.Substring($vmDir.Length + 1).Replace('\', '/')
    $out.UnsafeListUse[$name] = Get-UnsafeListUse $fileAst
}
# negative check: the detector sees the pattern in a synthetic snippet
$probeAst = [System.Management.Automation.Language.Parser]::ParseInput("function f { @() }`n`$x = f`nif (`$x.Count) { `$x[0] }", [ref]$null, [ref]$null)
$out['UnsafeListProbe'] = Get-UnsafeListUse $probeAst

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
        Files                 = [ordered]@{ BaseDisk = [ordered]@{ Exists = $false; Format = ''; Type = ''; SizeBytes = 0 }; InstallIsoMediaSha256 = ''; InstallIsoSourceSha256 = ''; SeedIsoMediaSha256 = ''; SeedIsoSourceSha256 = '' }
        RecordedVmId          = ''
        RecordedSeedIsoSha256 = ''
    }
}
$vmId = '0b1c2d3e-4f50-6172-8394-a5b6c7d8e9f0'
$gsi = '0a1b2c3d-1111-2222-3333-444455556666'
function New-Vm {
    return [ordered]@{
        # where Hyper-V stores the VM: New-VM -Path <VmRoot> keeps it in <VmRoot>\<VmName>
        # (the host, 2026-10-17)
        Name = 'refute-vm'; VmId = $vmId; State = 'Off'; Generation = 2; Path = 'C:\Hyper-V\refute-vm\refute-vm'
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

# ---- the incident of operation 4 (2026-10-17): New-VM -Path <VmRoot> stores the VM in
# <VmRoot>\<VmName>; the module now expects it there
$storage = Get-RefuteVmStoragePath $config
Add-Case 'the VM is stored in VmRoot\VmName' ($storage -ceq 'C:\Hyper-V\refute-vm\refute-vm') $storage
$p = Plan 'CreateVm' (New-Observed)
Add-Case 'CreateVm plans the VM where Hyper-V stores it' ($p.Changes.Count -eq 1 -and $p.Changes[0].After -like "*stored in $storage,*") ([string]$p.Changes[0].After)
$o = New-Observed; $o.RecordedVmId = $vmId; $o.Vms = @(New-Vm)
$p = Plan 'CreateVm' $o
Add-Case 'CreateVm already done for the VM it created (recorded VMId, nested folder)' ($null -eq $p.Refusal -and $p.AlreadyDone -and $p.Target.VmId -eq $vmId) ([string]$p.Refusal)
$o = New-Observed; $o.Vms = @(New-Vm)
Add-Case 'CreateVm refused: a VM of that name with no recorded VMId is never adopted' ((Plan 'CreateVm' $o).Refusal -like '*not the one these scripts created*not created by these scripts*')
$o = New-Observed; $o.RecordedVmId = $vmId; $v = New-Vm; $v.Path = 'C:\Hyper-V\refute-vm'; $o.Vms = @($v)
Add-Case 'CreateVm refused: the VM in VmRoot itself (the old expectation) is not where Hyper-V stores it' ((Plan 'CreateVm' $o).Refusal -like "*stored in 'C:\Hyper-V\refute-vm', not in '$storage'*")
Add-Case 'SetMemory refused: the VM in VmRoot itself' ((Plan 'SetMemory' $o).Refusal -like '*stored in*')
$o = New-Observed; $o.RecordedVmId = 'ffffffff-ffff-ffff-ffff-ffffffffffff'; $o.Vms = @(New-Vm)
Add-Case 'CreateVm refused: a VM of that name with another VMId' ((Plan 'CreateVm' $o).Refusal -like '*differs from the recorded*')
$o = New-Observed; $o.RecordedVmId = $vmId; $o.Vms = @(New-Vm)
Add-Case 'SetMemory plans for the VM in the nested folder (the retake of operation 5)' ($null -eq (Plan 'SetMemory' $o).Refusal)

# the reason of a result that is not reached is never empty
$p = Plan 'CreateVm' (New-Observed)
$after = New-Observed; $after.RecordedVmId = $vmId; $after.Vms = @(New-Vm)
$why = Get-RefuteVmPlanReachedProblem -Plan $p -Config $config -ObservedAfter $after
Add-Case 'CreateVm reached for the VM in the nested folder' ($why -eq '' -and (Test-RefuteVmPlanReached -Plan $p -Config $config -ObservedAfter $after)) $why
$v = New-Vm; $v.Path = 'C:\Hyper-V\refute-vm'; $after.Vms = @($v)
$why = Get-RefuteVmPlanReachedProblem -Plan $p -Config $config -ObservedAfter $after
Add-Case 'CreateVm not reached names the expected folder only' ($why -ceq "the VM after New-VM is not the one these scripts set up: the VM is not stored in '$storage'") $why
$after.Vms = @()
$why = Get-RefuteVmPlanReachedProblem -Plan $p -Config $config -ObservedAfter $after
Add-Case 'CreateVm not reached names a missing VM' ($why -like "expected one VM named 'refute-vm' after New-VM, found 0") $why
$after.Vms = @(New-Vm); $after.RecordedVmId = ''
$why = Get-RefuteVmPlanReachedProblem -Plan $p -Config $config -ObservedAfter $after
Add-Case 'CreateVm not reached names a VMId that was not recorded' ($why -like '*: no recorded VMId') $why
# review round 1 of #142 (Codex): the check after New-VM is the whole check of the target
$after.RecordedVmId = $vmId; $v = New-Vm; $v.Generation = 1; $after.Vms = @($v)
$why = Get-RefuteVmPlanReachedProblem -Plan $p -Config $config -ObservedAfter $after
Add-Case 'CreateVm not reached for a generation 1 VM' ($why -like '*: the VM is not generation 2') $why
# a reason that is not reached never quotes a value read from the host
$v = New-Vm; $v.HardDisks = @('C:\Users\SomeAccount\disk.vhdx'); $after.Vms = @($v)
$why = Get-RefuteVmPlanReachedProblem -Plan $p -Config $config -ObservedAfter $after
Add-Case 'CreateVm not reached for a foreign disk names no path' ($why -like '*: an unexpected disk is attached' -and $why -notlike '*Users*') $why
$v = New-Vm; $v.NetworkAdapters = @([ordered]@{ Name = 'Adapter of SomeAccount'; SwitchName = 'Switch of SomeAccount' }); $after.Vms = @($v)
$why = Get-RefuteVmPlanReachedProblem -Plan $p -Config $config -ObservedAfter $after
Add-Case 'CreateVm not reached for a connected adapter names no switch' ($why -like '*: a network adapter is connected*' -and $why -notlike '*SomeAccount*') $why
$o = New-Observed; $o.RecordedVmId = $vmId; $o.Vms = @(New-Vm)
$p = Plan 'SetMemory' $o
$why = Get-RefuteVmPlanReachedProblem -Plan $p -Config $config -ObservedAfter $o
Add-Case 'SetMemory not reached names the changes left' ($why -like '*still has 2 change(s): Memory.DynamicMemoryEnabled, Memory.StartupBytes') $why
$o2 = New-Observed; $o2.RecordedVmId = $vmId; $v = New-Vm; $v.DvdDrives = @('C:\Users\SomeAccount\other.iso'); $o2.Vms = @($v)
$why = Get-RefuteVmPlanReachedProblem -Plan $p -Config $config -ObservedAfter $o2
Add-Case 'SetMemory not reached for a refused plan names no path' ($why -ceq 'the plan after the operation is refused (simulate the operation to see the reason)') $why
$p = Plan 'DisableGuestServiceInterface' $o -Guid $gsi
$why = Get-RefuteVmPlanReachedProblem -Plan $p -Config $config -ObservedAfter $o -ServiceGuid $gsi
Add-Case 'DisableGuestServiceInterface not reached names the kind of item only' ($why -like '*still has 1 change(s): IntegrationService' -and $why -notlike '*Guest Service*') $why
$o3 = New-Observed; $o3.RecordedVmId = $vmId; $v = New-Vm; $v.NetworkAdapters = @([ordered]@{ Name = 'Adapter of SomeAccount'; SwitchName = 'Switch of SomeAccount' }); $o3.Vms = @($v)
$why = Get-RefuteVmPlanReachedProblem -Plan (Plan 'DisconnectNetwork' $o3) -Config $config -ObservedAfter $o3
Add-Case 'DisconnectNetwork not reached names the kind of item only' ($why -like '*still has 1 change(s): NetworkAdapter' -and $why -notlike '*SomeAccount*') $why
# review round 2 of #142 (Codex): a name with a line break is still named by kind only
foreach ($kind in 'NetworkAdapter', 'IntegrationService') {
    $name = "Adapter`nSomeAccount"
    $o3 = New-Observed; $o3.RecordedVmId = $vmId; $v = New-Vm
    if ($kind -eq 'NetworkAdapter') {
        $v.NetworkAdapters = @([ordered]@{ Name = $name; SwitchName = "Switch`r`nSomeAccount" }); $o3.Vms = @($v)
        $why = Get-RefuteVmPlanReachedProblem -Plan (Plan 'DisconnectNetwork' $o3) -Config $config -ObservedAfter $o3
    } else {
        $v.IntegrationServices = @([ordered]@{ Id = "Microsoft:$vmId\$gsi"; Name = $name; Enabled = $true }); $o3.Vms = @($v)
        $why = Get-RefuteVmPlanReachedProblem -Plan (Plan 'DisableGuestServiceInterface' $o3 -Guid $gsi) -Config $config -ObservedAfter $o3 -ServiceGuid $gsi
    }
    Add-Case "$kind not reached with a line break in a name names the kind only" ($why -ceq "the plan after the operation still has 1 change(s): $kind") $why
}
# the reason of a failure: the text the module recorded and threw is kept; any other error,
# even one shaped like it (a RuntimeException whose error id is its message), by type and
# HRESULT
$records = @{}
try { throw 'reparse point refused: C:\Hyper-V\refute-vm' } catch { $records['module'] = $_ }
try { Write-Error -Message 'C:\Users\SomeAccount\x' -ErrorId 'Probe' -ErrorAction Stop } catch { $records['cmdlet'] = $_ }
try { throw [System.IO.IOException]::new('C:\Users\SomeAccount\x') } catch { $records['exception'] = $_ }
try {
    Write-Error -Exception ([System.Management.Automation.RuntimeException]::new('C:\Users\SomeAccount\x')) -ErrorId 'C:\Users\SomeAccount\x' -ErrorAction Stop
} catch { $records['shaped'] = $_ }
$text = Get-RefuteVmFailureText -ErrorRecord $records['module'] -ModuleReason 'reparse point refused: C:\Hyper-V\refute-vm'
Add-Case 'failure text: the text the module recorded is kept' ($text -ceq 'reparse point refused: C:\Hyper-V\refute-vm') $text
$text = Get-RefuteVmFailureText -ErrorRecord $records['module']
Add-Case 'failure text: a thrown text the module did not record by type and HRESULT' ($text -cmatch '^RuntimeException \(HRESULT 0x[0-9A-F]{8}\)$') $text
$text = Get-RefuteVmFailureText -ErrorRecord $records['cmdlet'] -ModuleReason 'reparse point refused: C:\Hyper-V\refute-vm'
Add-Case 'failure text: a cmdlet error after a recorded text by type and HRESULT' ($text -cmatch '^WriteErrorException \(HRESULT 0x[0-9A-F]{8}\)$') $text
$text = Get-RefuteVmFailureText -ErrorRecord $records['exception']
Add-Case 'failure text: a thrown exception by type and HRESULT' ($text -cmatch '^IOException \(HRESULT 0x[0-9A-F]{8}\)$') $text
$text = Get-RefuteVmFailureText -ErrorRecord $records['shaped']
Add-Case 'failure text: an error shaped like a module text by type and HRESULT' ($text -cmatch '^RuntimeException \(HRESULT 0x[0-9A-F]{8}\)$' -and $text -notlike '*SomeAccount*') $text

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
$unset = Copy-Config @{ InstallIsoSha256 = '' }
Add-Case 'ImportInstallIso refused: hash not configured' ((Plan 'ImportInstallIso' (New-Observed) $unset $sha).Refusal -like '*not configured*')
Add-Case 'repository config: install ISO hash set (64 lowercase hex)' ($config.InstallIsoSha256 -cmatch '^[0-9a-f]{64}$')
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
$why = Get-RefuteVmPlanReachedProblem -Plan $p -Config $config -ObservedAfter $o
Add-Case 'StopVm not reached names the state' ($why -eq 'the VM is Running, not Off') $why

# ---- review round 1 (Codex): preconditions, state, disks, media, lock, caller --------------
$o = New-Observed; $o.RecordedVmId = $vmId; $v = New-Vm; $v.SecureBootTemplate = 'MicrosoftUEFICertificateAuthority'; $o.Vms = @($v)
$h1 = Get-RefuteVmPlanSha256 (Plan 'StartVm' $o)
$o.Vms[0].FirstBootDevice = 'C:\Hyper-V\refute-vm\media\ubuntu-26.04.1-live-server-amd64.iso'
Add-Case 'plan hash changes when a precondition changes (boot device)' ($h1 -cne (Get-RefuteVmPlanSha256 (Plan 'StartVm' $o)))
Add-Case 'plan holds the target VM record' ((Plan 'StartVm' $o).Preconditions.TargetVm.VmId -eq $vmId)

$o = New-Observed; $o.Files.SeedIsoMediaSha256 = $sha
Add-Case 'ImportSeedIso refused: seed in MediaRoot but not recorded' ((Plan 'ImportSeedIso' $o -Media $sha).Refusal -like '*not recorded*')
$o.RecordedSeedIsoSha256 = $sha
Add-Case 'ImportSeedIso already done when file and state agree' ((Plan 'ImportSeedIso' $o -Media $sha).AlreadyDone)

$o = New-Observed; $o.Files.BaseDisk = [ordered]@{ Exists = $true; Format = 'VHD'; Type = 'Fixed'; SizeBytes = 10 }
Add-Case 'CreateBaseDisk refused: another file at the path' ((Plan 'CreateBaseDisk' $o).Refusal -like '*never overwritten*')
$o.Files.BaseDisk = [ordered]@{ Exists = $true; Format = 'VHDX'; Type = 'Dynamic'; SizeBytes = [long]$config.BaseDiskSizeBytes }
Add-Case 'CreateBaseDisk already done for the configured disk' ((Plan 'CreateBaseDisk' $o).AlreadyDone)

$o = New-Observed; $o.RecordedVmId = $vmId; $v = New-Vm; $v.HardDisks = @($config.BaseDiskPath); $v.DvdDrives = @(''); $o.Vms = @($v)
$o.Files.BaseDisk = [ordered]@{ Exists = $true; Format = 'VHDX'; Type = 'Dynamic'; SizeBytes = [long]$config.BaseDiskSizeBytes }
Add-Case 'an empty DVD drive is not a divergence' ($null -eq (Plan 'SetProcessor' $o).Refusal)
$p = Plan 'DetachInstallMedia' $o
Add-Case 'DetachInstallMedia lists the empty drive' (@($p.Changes | Where-Object { $_.Before -eq 'empty drive' }).Count -eq 1)

$sender = [pscustomobject]@{ UserInfo = [pscustomobject]@{ Identity = [pscustomobject]@{ Name = 'PC\operator' } } }
$c = Get-RefuteVmCallerRecord -SenderInfo $sender -RunAsUser 'WinRM Virtual Users\WinRM VA_1'
Add-Case 'caller from PSSenderInfo.UserInfo.Identity.Name' ($c.ConnectedUser -eq 'PC\operator' -and $c.RunAsUser -like 'WinRM*')
Add-Case 'caller outside a remote session' ((Get-RefuteVmCallerRecord -SenderInfo $null -RunAsUser 'x').ConnectedUser -eq '')

. (Join-Path $moduleDir 'RefuteVm.HyperV.ps1')
$src = Join-Path $WorkDir 'source.iso'; $dst = Join-Path $WorkDir 'dest.iso'
[System.IO.File]::WriteAllBytes($src, [byte[]](1..200))
$srcSha = (Get-FileHash -LiteralPath $src -Algorithm SHA256).Hash.ToLowerInvariant()
$failed = $null
try { Copy-RefuteVerifiedFile -Source $src -Destination $dst -Sha256 ('0' * 64) } catch { $failed = $_.Exception.Message }
Add-Case 'verified copy refuses other bytes and keeps only the .partial' ($failed -like '*not*' -and -not (Test-Path -LiteralPath $dst) -and (Test-Path -LiteralPath "$dst.partial"))
$dst2 = Join-Path $WorkDir 'dest2.iso'
Copy-RefuteVerifiedFile -Source $src -Destination $dst2 -Sha256 $srcSha
Add-Case 'verified copy of the right bytes' ((Get-FileHash -LiteralPath $dst2 -Algorithm SHA256).Hash.ToLowerInvariant() -eq $srcSha -and -not (Test-Path -LiteralPath "$dst2.partial"))
$failed = $null
$script:RefuteVmFailureReason = ''
try { Copy-RefuteVerifiedFile -Source $src -Destination $dst2 -Sha256 $srcSha } catch { $failed = $_ }
Add-Case 'verified copy never overwrites' ($failed.Exception.Message -like '*already exists*')
# the module records the text it throws (Stop-RefuteVmOperation), and the log keeps it
$text = Get-RefuteVmFailureText -ErrorRecord $failed -ModuleReason $script:RefuteVmFailureReason
Add-Case 'a failure of the module records its own text' ($script:RefuteVmFailureReason -ceq "the destination already exists: $dst2" -and $text -ceq $script:RefuteVmFailureReason) $text

# The first Hyper-V call (Codex review of #118): only a host without the vmms service gets
# the module's own message; a command that is not recognized and any failure on a host
# with the service keep their own error. Get-VMHost and the service probe are replaced by
# functions here (a function wins over a cmdlet of the same name).
function Get-HostCheckFailure([scriptblock]$VmHost, [bool]$Installed) {
    Set-Item -Path function:Get-VMHost -Value $VmHost
    Set-Item -Path function:Test-RefuteVmmsInstalled -Value ([scriptblock]::Create("return `$$Installed"))
    try {
        $got = Get-RefuteVmHostChecked
        return [ordered]@{ Value = $got; Type = ''; Message = '' }
    } catch {
        return [ordered]@{ Value = $null; Type = $_.Exception.GetType().FullName; Message = $_.Exception.Message }
    } finally {
        Remove-Item -Path function:Get-VMHost
    }
}
$denied = { throw (New-Object System.UnauthorizedAccessException 'synthetic: access denied') }
$noService = { throw (New-Object System.InvalidOperationException 'synthetic: no virtualization service') }
$notFound = { throw (New-Object System.Management.Automation.CommandNotFoundException 'synthetic: Get-VMHost is not recognized') }
$r = Get-HostCheckFailure $noService $false
Add-Case 'Hyper-V check: no vmms service gives the own message, with the error by type and HRESULT' ($r.Message -cmatch '^Hyper-V is not available on this host \(the vmms service is not installed\): InvalidOperationException \(HRESULT 0x[0-9A-F]{8}\)$' -and $r.Message -notlike '*synthetic*') ($r.Type + ': ' + $r.Message)
$r = Get-HostCheckFailure $denied $true
Add-Case 'Hyper-V check: access denied with the service installed keeps its error' ($r.Type -eq 'System.UnauthorizedAccessException' -and $r.Message -eq 'synthetic: access denied') ($r.Type + ': ' + $r.Message)
$r = Get-HostCheckFailure $notFound $false
Add-Case 'Hyper-V check: a command not recognized is never the own message' ($r.Type -eq 'System.Management.Automation.CommandNotFoundException' -and $r.Message -notlike '*not available*') ($r.Type + ': ' + $r.Message)
$r = Get-HostCheckFailure $notFound $true
Add-Case 'Hyper-V check: a command not recognized keeps its error with the service installed' ($r.Type -eq 'System.Management.Automation.CommandNotFoundException') ($r.Type + ': ' + $r.Message)
$r = Get-HostCheckFailure { 'synthetic host' } $false
Add-Case 'Hyper-V check: a host that answers is returned' ($r.Value -eq 'synthetic host' -and $r.Type -eq '') ($r.Type + ': ' + $r.Message)
Remove-Item -Path function:Test-RefuteVmmsInstalled
. (Join-Path $moduleDir 'RefuteVm.HyperV.ps1')

$onWindows = ($PSVersionTable.PSEdition -eq 'Desktop') -or ((Get-Variable -Name IsWindows -ErrorAction SilentlyContinue) -and $IsWindows)
if ($onWindows) {
    # FileShare.None is enforced by Windows; the endpoint runs only there.
    $lockConfig = @{ StateFile = (Join-Path $WorkDir 'vm.json') }
    $first = Enter-RefuteVmLock -Config $lockConfig
    $failed = $null
    try { $second = Enter-RefuteVmLock -Config $lockConfig; $second.Dispose() } catch { $failed = $_.Exception.Message }
    $first.Dispose()
    Add-Case 'a second operation is refused while one holds the lock' ($failed -like '*in progress*')
    $again = Enter-RefuteVmLock -Config $lockConfig; $again.Dispose()
    Add-Case 'the lock is free after the operation' $true
}

$stateConfig = @{ StateFile = (Join-Path $WorkDir 'state.json') }
Write-RefuteVmState -Config $stateConfig -VmId $vmId -SeedIsoSha256 ''
Write-RefuteVmState -Config $stateConfig -VmId $vmId -SeedIsoSha256 $sha
$state = Read-RefuteVmState -Config $stateConfig
Add-Case 'state is replaced whole' ($state.RecordedVmId -eq $vmId -and $state.RecordedSeedIsoSha256 -eq $sha -and -not (Test-Path -LiteralPath "$($stateConfig.StateFile).next"))

# ---- media and key decisions ---------------------------------------------------------------
. (Join-Path $vmDir 'RefuteMedia.Core.ps1')
$fpr = '843938DF228D22F7B3742BC0D94AA3F0EFE21092'
$good = @("[GNUPG:] NEWSIG", "[GNUPG:] GOODSIG D94AA3F0EFE21092 Ubuntu CD Image Automatic Signing Key (2012)",
    "[GNUPG:] VALIDSIG $fpr 2026-08-27 1756334580 0 4 0 1 10 00 $fpr")
Add-Case 'gpg: signature by the primary key' ((Test-RefuteGpgStatus -Lines $good -Fingerprint $fpr) -like '*VALIDSIG*')
$subkey = @($good[0], $good[1], "[GNUPG:] VALIDSIG 0123456789ABCDEF0123456789ABCDEF01234567 2026-08-27 1 0 4 0 1 10 00 $fpr")
Add-Case 'gpg: signature by a subkey of the primary key' ((Test-RefuteGpgStatus -Lines $subkey -Fingerprint $fpr) -like '*VALIDSIG*')
foreach ($bad in @(
        @{ Name = 'another primary key'; Lines = @($good[0], $good[1], "[GNUPG:] VALIDSIG $fpr 2026 1 0 4 0 1 10 00 FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF") },
        @{ Name = 'no VALIDSIG'; Lines = @($good[0], $good[1]) },
        @{ Name = 'two VALIDSIG'; Lines = @($good + $good[2]) },
        @{ Name = 'no GOODSIG'; Lines = @($good[0], $good[2]) },
        @{ Name = 'BADSIG present'; Lines = @($good + '[GNUPG:] BADSIG D94AA3F0EFE21092 x') })) {
    $failed = $null
    try { Test-RefuteGpgStatus -Lines $bad.Lines -Fingerprint $fpr | Out-Null } catch { $failed = $_.Exception.Message }
    Add-Case "gpg refused: $($bad.Name)" ($null -ne $failed) $failed
}
$iso = 'ubuntu-26.04.1-live-server-amd64.iso'
$sums = @("$('a' * 64) *$iso", "$('b' * 64) *$iso.zsync", "$('c' * 64)  ubuntu-26.04.1-desktop-amd64.iso")
Add-Case 'SHA256SUMS: the exact line' ((Get-RefuteSumsHash -Lines $sums -Name $iso) -eq ('a' * 64))
foreach ($bad in @(@{ Name = 'missing'; Lines = @($sums[1]) }, @{ Name = 'twice'; Lines = @($sums[0], $sums[0]) }, @{ Name = 'uppercase hash'; Lines = @("$('A' * 64) *$iso") })) {
    $failed = $null
    try { Get-RefuteSumsHash -Lines $bad.Lines -Name $iso | Out-Null } catch { $failed = $_.Exception.Message }
    Add-Case "SHA256SUMS refused: $($bad.Name)" ($null -ne $failed) $failed
}
$typeBytes = [System.Text.Encoding]::ASCII.GetBytes('ssh-ed25519')
$blob = [byte[]](@(0, 0, 0, 11) + $typeBytes + @(0, 0, 0, 32) + (1..32))
$b64 = [System.Convert]::ToBase64String($blob)
Add-Case 'key: a valid ed25519 key, comment replaced' ((ConvertTo-RefuteVmPublicKey "ssh-ed25519 $b64 someone@somehost") -ceq "ssh-ed25519 $b64 refute-vm")
foreach ($bad in @("ssh-rsa $b64", "ssh-ed25519 notbase64!", "ssh-ed25519 $([System.Convert]::ToBase64String([byte[]](1..51)))")) {
    $failed = $null
    try { ConvertTo-RefuteVmPublicKey $bad | Out-Null } catch { $failed = $_.Exception.Message }
    Add-Case "key refused: $($bad.Substring(0, 12))" ($null -ne $failed) $failed
}
# The gpg of Git for Windows is an MSYS program: started from PowerShell it reads
# "C:/a/b" as a relative path, so every path it gets is in the "/c/a/b" form.
Add-Case 'msys path: key ring folder' ((ConvertTo-RefuteMsysPath 'C:\Projetos\refute\.cache\vm\gnupg') -ceq '/c/Projetos/refute/.cache/vm/gnupg')
Add-Case 'msys path: file, lowercase drive' ((ConvertTo-RefuteMsysPath 'K:\Meu Drive\SHA256SUMS') -ceq '/k/Meu Drive/SHA256SUMS')
Add-Case 'msys path: trailing separator and drive root' ((ConvertTo-RefuteMsysPath 'C:\a\') -ceq '/c/a' -and (ConvertTo-RefuteMsysPath 'C:\') -ceq '/c')
foreach ($bad in @('relative\path', '\\server\share\x', 'C:/Projetos/refute', 'C:\Projetos\..\Windows', '/c/Projetos')) {
    $failed = $null
    try { ConvertTo-RefuteMsysPath $bad | Out-Null } catch { $failed = $_.Exception.Message }
    Add-Case "msys path refused: $bad" ($null -ne $failed) $failed
}

# ---- registration decisions (Codex review round 2) ----------------------------------------
. (Join-Path $vmDir 'RefuteRegistration.Core.ps1')
$r = [System.Security.AccessControl.FileSystemRights]
foreach ($readOnly in @($r::ReadAndExecute, $r::Read, $r::ListDirectory, $r::ReadPermissions, $r::Synchronize)) {
    Add-Case "read-only rights are not a writer: $readOnly" (-not (Test-RefuteRightsWrite ([int]$readOnly)))
}
foreach ($writer in @($r::Modify, $r::FullControl, $r::Write, $r::WriteData, $r::AppendData, $r::Delete, $r::ChangePermissions, $r::TakeOwnership, $r::DeleteSubdirectoriesAndFiles, $r::WriteAttributes)) {
    Add-Case "change rights are a writer: $writer" (Test-RefuteRightsWrite ([int]$writer))
}
$fw = @(
    [ordered]@{ Name = 'plain-allow'; Enabled = 'True'; Direction = 'Inbound'; OverrideBlockRules = $false },
    [ordered]@{ Name = 'bypass-in'; Enabled = 'True'; Direction = 'Inbound'; OverrideBlockRules = $true },
    [ordered]@{ Name = 'bypass-disabled'; Enabled = 'False'; Direction = 'Inbound'; OverrideBlockRules = $true },
    [ordered]@{ Name = 'bypass-out'; Enabled = 'True'; Direction = 'Outbound'; OverrideBlockRules = $true })
$found = @(Find-RefuteBlockOverrides $fw)
Add-Case 'only enabled inbound bypass rules are found' ($found.Count -eq 1 -and $found[0] -eq 'bypass-in') ($found -join ',')
Add-Case 'no bypass rule, nothing found' (@(Find-RefuteBlockOverrides @($fw[0], $fw[2], $fw[3])).Count -eq 0)

# The ACL of the VM tree: SetHostPaths failed through the endpoint with version 1 on
# 2026-10-16 (access denied); version 2 lets Hyper-V Administrators change permissions and
# gives the Virtual Machines group the entries of the default folder of Windows. Windows
# only: PowerShell on Linux has no DirectorySecurity (the Windows jobs run these cases).
if ([System.Environment]::OSVersion.Platform -eq 'Win32NT') {
$tree1 = @(Get-RefuteVmTreeAclSpec -Version 1)
$tree2 = @(Get-RefuteVmTreeAclSpec -Version 2)
$acl1 = New-RefuteFolderAcl $tree1
$acl2 = New-RefuteFolderAcl $tree2
Add-Case 'VM tree ACL: version 2 matches its spec' (@(Compare-RefuteVmTreeAcl -Acl $acl2 -Spec $tree2).Count -eq 0) (@(Compare-RefuteVmTreeAcl -Acl $acl2 -Spec $tree2) -join '; ')
Add-Case 'VM tree ACL: version 1 matches its spec' (@(Compare-RefuteVmTreeAcl -Acl $acl1 -Spec $tree1).Count -eq 0)
Add-Case 'VM tree ACL: version 1 is not version 2' (@(Compare-RefuteVmTreeAcl -Acl $acl1 -Spec $tree2).Count -gt 0)
$fsr = [System.Security.AccessControl.FileSystemRights]
$changePermissions = [int]$fsr::ChangePermissions
$takeOwnership = [int]$fsr::TakeOwnership
function Get-RuleRights([string]$Rule) { return [int]($Rule.Split(' ')[2]) }
$hv1 = @(ConvertTo-RefuteAclRules $acl1 | Where-Object { $_ -like 'Allow S-1-5-32-578 *' })
$hv2 = @(ConvertTo-RefuteAclRules $acl2 | Where-Object { $_ -like 'Allow S-1-5-32-578 *' })
Add-Case 'VM tree ACL: version 1 gives Hyper-V Administrators no ChangePermissions (the cause)' ($hv1.Count -eq 1 -and ((Get-RuleRights $hv1[0]) -band $changePermissions) -eq 0) ($hv1 -join '; ')
Add-Case 'VM tree ACL: version 2 gives Hyper-V Administrators ChangePermissions, inherited by folders and files, and no TakeOwnership' (
    $hv2.Count -eq 1 -and ((Get-RuleRights $hv2[0]) -band $changePermissions) -ne 0 -and ((Get-RuleRights $hv2[0]) -band $takeOwnership) -eq 0 -and
    $hv2[0].EndsWith(' ContainerInherit, ObjectInherit None explicit')) ($hv2 -join '; ')
$vmGroup = @(ConvertTo-RefuteAclRules $acl2 | Where-Object { $_ -like 'Allow S-1-5-83-0 *' })
$replace = [int]($fsr::Delete -bor $fsr::DeleteSubdirectoriesAndFiles -bor $fsr::ChangePermissions -bor $fsr::TakeOwnership -bor $fsr::WriteAttributes -bor $fsr::WriteExtendedAttributes)
# .NET merges the entry of the folder and the one inherited by the folders below (same
# rights) into one entry that applies to both: two entries in all, the same effect
Add-Case 'VM tree ACL: the Virtual Machines group lists and creates in folders, reads files, and can never delete, rewrite attributes or change permissions' (
    $vmGroup.Count -eq 2 -and @($vmGroup | Where-Object { ((Get-RuleRights $_) -band $replace) -ne 0 }).Count -eq 0 -and
    @($vmGroup | Where-Object { $_.EndsWith(' ContainerInherit None explicit') -and ((Get-RuleRights $_) -band [int]$fsr::CreateFiles) -ne 0 }).Count -eq 1 -and
    @($vmGroup | Where-Object { $_.EndsWith(' ObjectInherit InheritOnly explicit') -and ((Get-RuleRights $_) -band [int]($fsr::CreateFiles -bor $fsr::AppendData)) -eq 0 }).Count -eq 1) ($vmGroup -join '; ')
Add-Case 'VM tree ACL: only SYSTEM, Administrators, Hyper-V Administrators and Virtual Machines' (
    @(ConvertTo-RefuteAclRules $acl2 | Where-Object { @('S-1-5-18', 'S-1-5-32-544', 'S-1-5-32-578', 'S-1-5-83-0') -notcontains $_.Split(' ')[1] }).Count -eq 0)
$otherOwner = New-RefuteFolderAcl $tree2
$otherOwner.SetOwner((New-Object System.Security.Principal.SecurityIdentifier 'S-1-5-32-545'))
Add-Case 'VM tree ACL: another owner is a difference' (@(@(Compare-RefuteVmTreeAcl -Acl $otherOwner -Spec $tree2) -like '*owner*').Count -eq 1)
$unprotected = New-RefuteFolderAcl $tree2
$unprotected.SetAccessRuleProtection($false, $false)
Add-Case 'VM tree ACL: an inheriting DACL is a difference' (@(@(Compare-RefuteVmTreeAcl -Acl $unprotected -Spec $tree2) -like '*inherits*').Count -eq 1)
$widened = New-RefuteFolderAcl $tree2
$widened.AddAccessRule((New-Object System.Security.AccessControl.FileSystemAccessRule(
            (New-Object System.Security.Principal.SecurityIdentifier 'S-1-5-32-545'), 'Modify',
            [System.Security.AccessControl.InheritanceFlags]'ContainerInherit, ObjectInherit',
            [System.Security.AccessControl.PropagationFlags]::None, [System.Security.AccessControl.AccessControlType]::Allow)))
Add-Case 'VM tree ACL: an extra entry is a difference' (@(@(Compare-RefuteVmTreeAcl -Acl $widened -Spec $tree2) -like 'unexpected entry: Allow S-1-5-32-545 *').Count -eq 1)

# The folders below C:\Hyper-V (Codex review of #126): each must inherit exactly what the
# tree's ACL passes down, compared by effect. The synthetic ACLs are written as Windows
# writes inherited entries (the ID flag): SYSTEM and Administrators full control; Hyper-V
# Administrators Modify (0x1301bf), or Modify and ChangePermissions (0x1701bf); the Virtual
# Machines group list and create on folders (0x12008f) and read on files (0x120089).
function New-BelowAcl([string]$Aces, [bool]$Protected = $false) {
    $acl = New-Object System.Security.AccessControl.DirectorySecurity
    $acl.SetSecurityDescriptorSddlForm('O:BAD:' + $(if ($Protected) { 'P' } else { 'AI' }) + $Aces)
    return $acl
}
$below1 = '(A;OICIID;FA;;;SY)(A;OICIID;FA;;;BA)(A;OICIID;0x1301bf;;;S-1-5-32-578)'
$below2 = '(A;OICIID;FA;;;SY)(A;OICIID;FA;;;BA)(A;OICIID;0x1701bf;;;S-1-5-32-578)(A;CIID;0x12008f;;;S-1-5-83-0)(A;OIIOID;0x120089;;;S-1-5-83-0)'
foreach ($depth in 1, 2) {
    $d1 = @(Compare-RefuteVmTreeBelow -Acl (New-BelowAcl $below1) -Spec $tree1 -Depth $depth)
    Add-Case "VM tree below: a folder inheriting version 1 matches version 1 at depth $depth" ($d1.Count -eq 0) ($d1 -join '; ')
    $d2 = @(Compare-RefuteVmTreeBelow -Acl (New-BelowAcl $below2) -Spec $tree2 -Depth $depth)
    Add-Case "VM tree below: a folder inheriting version 2 matches version 2 at depth $depth" ($d2.Count -eq 0) ($d2 -join '; ')
}
$old = @(Compare-RefuteVmTreeBelow -Acl (New-BelowAcl $below1) -Spec $tree2 -Depth 1)
Add-Case 'VM tree below: a folder still inheriting version 1 is not version 2 (the post-check fails)' (
    @($old -like 'missing effect: Allow S-1-5-32-578 *').Count -gt 0 -and @($old -like 'missing effect: Allow S-1-5-83-0 *').Count -gt 0) ($old -join '; ')
$wider = @(Compare-RefuteVmTreeBelow -Acl (New-BelowAcl ($below1 + '(A;OICIID;0x1301bf;;;BU)')) -Spec $tree1 -Depth 1)
Add-Case 'VM tree below: an extra inherited entry is a difference (the pre-check fails)' (@($wider -like 'unexpected effect: Allow S-1-5-32-545 *').Count -eq 3) ($wider -join '; ')
$own = @(Compare-RefuteVmTreeBelow -Acl (New-BelowAcl ('(A;OICI;0x1301bf;;;BU)' + $below1)) -Spec $tree1 -Depth 1)
Add-Case 'VM tree below: an explicit entry is a difference' (@($own -like 'explicit entry: Allow S-1-5-32-545 *').Count -eq 1) ($own -join '; ')
$cut = @(Compare-RefuteVmTreeBelow -Acl (New-BelowAcl '(A;OICI;FA;;;SY)(A;OICI;FA;;;BA)(A;OICI;0x1301bf;;;S-1-5-32-578)' $true) -Spec $tree1 -Depth 1)
Add-Case 'VM tree below: a folder that does not inherit is a difference' (@($cut -like '*does not inherit*').Count -eq 1 -and @($cut -like 'explicit entry: *').Count -eq 3) ($cut -join '; ')
$narrower = @(Compare-RefuteVmTreeBelow -Acl (New-BelowAcl '(A;OICIID;FA;;;SY)(A;OICIID;FA;;;BA)(A;CIID;0x1301bf;;;S-1-5-32-578)') -Spec $tree1 -Depth 1)
Add-Case 'VM tree below: an entry that no longer reaches the files is a difference' (@($narrower -like 'missing effect: Allow S-1-5-32-578 files *').Count -eq 1) ($narrower -join '; ')
# the effect does not depend on how the entries are split
$split = @(ConvertTo-RefuteAclEffect @((New-BelowAcl '(A;;0x12008f;;;S-1-5-83-0)(A;CIIO;0x12008f;;;S-1-5-83-0)').GetAccessRules($true, $true, [System.Security.Principal.SecurityIdentifier])))
$merged = @(ConvertTo-RefuteAclEffect @((New-BelowAcl '(A;CI;0x12008f;;;S-1-5-83-0)').GetAccessRules($true, $true, [System.Security.Principal.SecurityIdentifier])))
Add-Case 'ACL effect: split and merged entries with the same rights have the same effect' (($split -join '|') -ceq ($merged -join '|') -and $split.Count -eq 2) (($split -join '; ') + ' / ' + ($merged -join '; '))
# NoPropagateInherit: the entry reaches the first level only
$sid578 = New-Object System.Security.Principal.SecurityIdentifier 'S-1-5-32-578'
$np = [pscustomobject]@{ AccessControlType = 'Allow'; IdentityReference = $sid578; FileSystemRights = 0x1301bf
    InheritanceFlags = [System.Security.AccessControl.InheritanceFlags]'ContainerInherit, ObjectInherit'; PropagationFlags = [System.Security.AccessControl.PropagationFlags]::NoPropagateInherit }
$npEffect = @(ConvertTo-RefuteAclEffect @($np))
Add-Case 'ACL effect: NoPropagateInherit is shown as the first level only' (($npEffect -join '|') -ceq 'Allow S-1-5-32-578 child-files 1245631|Allow S-1-5-32-578 child-folders 1245631|Allow S-1-5-32-578 folder 1245631') ($npEffect -join '; ')
$npChild = @(ConvertTo-RefuteAclEffect @(Get-RefuteChildRules @($np)))
Add-Case 'ACL effect: a child of a NoPropagateInherit entry gets it on itself only' (($npChild -join '|') -ceq 'Allow S-1-5-32-578 folder 1245631') ($npChild -join '; ')
$oiOnly = [pscustomobject]@{ AccessControlType = 'Allow'; IdentityReference = $sid578; FileSystemRights = 0x120089
    InheritanceFlags = [System.Security.AccessControl.InheritanceFlags]::ObjectInherit; PropagationFlags = [System.Security.AccessControl.PropagationFlags]::None }
$oiChild = @(ConvertTo-RefuteAclEffect @(Get-RefuteChildRules @($oiOnly)))
Add-Case 'ACL effect: a files-only entry passes to a child folder for its files only' (($oiChild -join '|') -ceq 'Allow S-1-5-32-578 files 1179785') ($oiChild -join '; ')
}

# Hyper-V module manifest: both layouts (the maintainer's first preview did not find the
# version subfolder of Windows 10 and 11)
$hv = Join-Path $WorkDir 'hyperv'
foreach ($layout in 'flat', 'versioned', 'two', 'none', 'noversion') {
    [void][System.IO.Directory]::CreateDirectory((Join-Path $hv $layout))
}
[System.IO.File]::WriteAllText((Join-Path $hv 'flat\Hyper-V.psd1'), '@{}')
[void][System.IO.Directory]::CreateDirectory((Join-Path $hv 'versioned\2.0.0.0'))
[System.IO.File]::WriteAllText((Join-Path $hv 'versioned\2.0.0.0\Hyper-V.psd1'), '@{}')
foreach ($v in '1.1', '2.0.0.0') {
    [void][System.IO.Directory]::CreateDirectory((Join-Path $hv "two\$v"))
    [System.IO.File]::WriteAllText((Join-Path $hv "two\$v\Hyper-V.psd1"), '@{}')
}
[void][System.IO.Directory]::CreateDirectory((Join-Path $hv 'noversion\latest'))
[System.IO.File]::WriteAllText((Join-Path $hv 'noversion\latest\Hyper-V.psd1'), '@{}')
Add-Case 'Hyper-V manifest: flat layout' ((Find-RefuteHyperVManifest (Join-Path $hv 'flat')) -eq (Join-Path $hv 'flat\Hyper-V.psd1'))
Add-Case 'Hyper-V manifest: version subfolder' ((Find-RefuteHyperVManifest (Join-Path $hv 'versioned')) -eq (Join-Path $hv 'versioned\2.0.0.0\Hyper-V.psd1'))
Add-Case 'Hyper-V manifest: the highest version wins' ((Find-RefuteHyperVManifest (Join-Path $hv 'two')) -eq (Join-Path $hv 'two\2.0.0.0\Hyper-V.psd1'))
Add-Case 'Hyper-V manifest: none' ($null -eq (Find-RefuteHyperVManifest (Join-Path $hv 'none')))
Add-Case 'Hyper-V manifest: a folder that is not a version is ignored' ($null -eq (Find-RefuteHyperVManifest (Join-Path $hv 'noversion')))
Add-Case 'Hyper-V manifest: missing module folder' ($null -eq (Find-RefuteHyperVManifest (Join-Path $hv 'absent')))

# The role capability search of JEA: <root>\<module>\RoleCapabilities\<name>.psrc only
# (the maintainer's diagnosis of 2026-10-16); a copy in a version subfolder is not found
function New-RoleFile([string[]]$Parts) {
    $dir = $WorkDir
    foreach ($p in $Parts) { $dir = Join-Path $dir $p }
    $dir = Join-Path $dir 'RoleCapabilities'
    [void][System.IO.Directory]::CreateDirectory($dir)
    $file = Join-Path $dir 'Op.psrc'
    [System.IO.File]::WriteAllText($file, '@{}')
    return $file
}
$flatRole = New-RoleFile @('jea', 'flat', 'M')
$verRole = New-RoleFile @('jea', 'versioned', 'M', '0.1.0')
$bothFlat = New-RoleFile @('jea', 'both', 'M')
$bothVer = New-RoleFile @('jea', 'both', 'M', '0.1.0')
$firstRoot = New-RoleFile @('jea', 'first', 'A')
$secondRoot = New-RoleFile @('jea', 'second', 'B')
[void](New-RoleFile @('jea', 'other', 'M'))
$jea = Join-Path $WorkDir 'jea'
$jf = @(Find-RefuteJeaRoleCapability -ModuleRoots @(Join-Path $jea 'flat') -RoleName 'Op')
$vf = @(Find-RefuteVersionedRoleCapability -ModuleRoots @(Join-Path $jea 'flat') -RoleName 'Op')
Add-Case 'JEA search: a role capability at the module top is found' ($jf.Count -eq 1 -and $jf[0] -eq $flatRole -and $vf.Count -eq 0) (($jf + $vf) -join ', ')
$jv = @(Find-RefuteJeaRoleCapability -ModuleRoots @(Join-Path $jea 'versioned') -RoleName 'Op')
$vv = @(Find-RefuteVersionedRoleCapability -ModuleRoots @(Join-Path $jea 'versioned') -RoleName 'Op')
Add-Case 'JEA search: a version subfolder is never found, and is reported' ($jv.Count -eq 0 -and $vv.Count -eq 1 -and $vv[0] -eq $verRole) (($jv + $vv) -join ', ')
$jb = @(Find-RefuteJeaRoleCapability -ModuleRoots @(Join-Path $jea 'both') -RoleName 'Op')
$vb = @(Find-RefuteVersionedRoleCapability -ModuleRoots @(Join-Path $jea 'both') -RoleName 'Op')
Add-Case 'JEA search: a stale copy in a version subfolder is reported next to the found one' ($jb.Count -eq 1 -and $jb[0] -eq $bothFlat -and $vb.Count -eq 1 -and $vb[0] -eq $bothVer)
$jo = @(Find-RefuteJeaRoleCapability -ModuleRoots @((Join-Path $jea 'second'), (Join-Path $jea 'first')) -RoleName 'Op')
Add-Case 'JEA search: module roots are searched in order (the first found is the one loaded)' ($jo.Count -eq 2 -and $jo[0] -eq $secondRoot -and $jo[1] -eq $firstRoot)
Add-Case 'JEA search: another role name is not found' (@(Find-RefuteJeaRoleCapability -ModuleRoots @(Join-Path $jea 'flat') -RoleName 'Other').Count -eq 0)
Add-Case 'JEA search: a missing root is skipped' (@(Find-RefuteJeaRoleCapability -ModuleRoots @(Join-Path $jea 'absent') -RoleName 'Op').Count -eq 0)

# The module roots the registration searches: PSModulePath values and extra folders,
# trimmed, without empty entries or repeats (compared without case), sorted
$joined = @(Join-RefuteModuleRoots -PathValues @('C:\B\;C:\A;;c:\a\', $null, '') -Extra @('C:\C', 'C:\B'))
Add-Case 'module roots: entries split, trimmed, deduplicated without case, sorted' ($joined.Count -eq 3 -and $joined[0] -eq 'C:\A' -and $joined[1] -eq 'C:\B' -and $joined[2] -eq 'C:\C') ($joined -join ', ')
Add-Case 'module roots: nothing given gives nothing' (@(Join-RefuteModuleRoots -PathValues @() -Extra @()).Count -eq 0)
# a volume root keeps its '\' ('C:' would be the current folder of drive C); UNC paths are
# trimmed; relative and drive-relative entries are refused (Codex review of #102)
$volume = @(Join-RefuteModuleRoots -PathValues @('C:\;D:\Mods\;\\srv\share\Mods\;E:\\;F:\Mods\\') -Extra @())
Add-Case 'module roots: a volume root keeps one backslash, also after repeated ones' ($volume.Count -eq 5 -and $volume -ccontains 'C:\' -and $volume -ccontains 'D:\Mods' -and $volume -ccontains '\\srv\share\Mods' -and $volume -ccontains 'E:\' -and $volume -ccontains 'F:\Mods') ($volume -join ', ')
foreach ($relative in 'Modules', 'C:Modules', '.\Modules', '\Modules') {
    $refused = $false
    try { [void](Join-RefuteModuleRoots -PathValues @("C:\A;$relative") -Extra @()) } catch { $refused = $true }
    Add-Case "module roots: the relative entry '$relative' is refused" $refused
}

# The effective discovery set of the session (item 9 of the maintainer's message of
# 2026-10-16): a relative entry resolves against the session's current folder; a
# drive-relative or root-relative entry, and a relative current folder, are refused
$sys32 = 'C:\Windows\system32'
Add-Case 'session entry: a relative entry resolves against the current folder' ((Resolve-RefuteSessionEntry -Entry 'WindowsPowerShell\Modules' -CurrentFolder $sys32) -ceq 'C:\Windows\system32\WindowsPowerShell\Modules')
Add-Case 'session entry: dot and dot-dot segments are resolved' ((Resolve-RefuteSessionEntry -Entry '.\a\..\Mods\' -CurrentFolder 'C:\X') -ceq 'C:\X\Mods')
Add-Case 'session entry: dot-dot stops at the volume root' ((Resolve-RefuteSessionEntry -Entry '..\..\..\M' -CurrentFolder 'C:\X') -ceq 'C:\M')
Add-Case 'session entry: a fully qualified entry is kept as a root' ((Resolve-RefuteSessionEntry -Entry 'D:\Mods\' -CurrentFolder $sys32) -ceq 'D:\Mods')
# Windows rules on every OS (Codex review of #114): a UNC share stays the root, '/' is a
# separator, '.' and '..' are resolved in absolute entries too. The expected values are
# written out; on Windows they are also compared with .NET's own resolution.
$onWindows = [System.Environment]::OSVersion.Platform -eq 'Win32NT'
foreach ($pair in @(@('..\..\Mods', '\\srv\share\X', '\\srv\share\Mods'), @('C:/Mods', $sys32, 'C:\Mods'), @('C:\A\..\Mods', $sys32, 'C:\Mods'),
        @('a/./b/../c', 'C:\X', 'C:\X\a\c'), @('WindowsPowerShell\Modules', $sys32, 'C:\Windows\system32\WindowsPowerShell\Modules'))) {
    $ours = Resolve-RefuteSessionEntry -Entry $pair[0] -CurrentFolder $pair[1]
    Add-Case "session entry: '$($pair[0])' against '$($pair[1])' gives '$($pair[2])'" ($ours -ceq $pair[2]) $ours
    if ($onWindows) {
        $dotnet = [System.IO.Path]::GetFullPath([System.IO.Path]::Combine($pair[1], $pair[0].Replace('/', '\'))).TrimEnd('\')
        Add-Case "session entry: '$($pair[0])' against '$($pair[1])' as .NET resolves it on Windows" ($ours -ceq $dotnet) "$ours / $dotnet"
    }
}
Add-Case 'full path: a volume root keeps its backslash' ((ConvertTo-RefuteWindowsFullPath 'C:\a\..') -ceq 'C:\')
Add-Case 'full path: a UNC share root' ((ConvertTo-RefuteWindowsFullPath '\\srv\share\..\x\') -ceq '\\srv\share\x')
foreach ($bad in '\\?\C:\Mods', '\\.\C:\Mods', 'C:\Mods.\x', 'C:\Mods \x', 'Mods', 'C:Mods',
    'C:\Modules|audit', 'C:\Modules:stream', 'C:\a<b', 'C:\a>b', 'C:\a"b', 'C:\a*b', 'C:\a?b', "C:\a`tb", '\\srv\sh:are\x') {
    $refused = $false
    try { [void](ConvertTo-RefuteWindowsFullPath $bad) } catch { $refused = $true }
    Add-Case "full path refused: '$bad'" $refused
}
Add-Case 'session entry: a UNC share is kept under dot-dot' ((Resolve-RefuteSessionEntry -Entry '..\..\Mods' -CurrentFolder '\\srv\share\X') -ceq '\\srv\share\Mods')
foreach ($bad in @(@('C:Modules', $sys32), @('\Modules', $sys32), @('/Modules', $sys32), @('Modules', 'system32'))) {
    $refused = $false
    try { [void](Resolve-RefuteSessionEntry -Entry $bad[0] -CurrentFolder $bad[1]) } catch { $refused = $true }
    Add-Case "session entry refused: '$($bad[0])' against '$($bad[1])'" $refused
}
$disc = @(Join-RefuteDiscoveryRoots -PathValues @('C:\Program Files\WindowsPowerShell\Modules;C:\Windows\system32\WindowsPowerShell\v1.0\Modules') `
        -Extra @('C:\Program Files\WindowsPowerShell\Modules\') -RelativeEntries @('WindowsPowerShell\Modules', 'windowspowershell\modules') -CurrentFolder $sys32)
Add-Case 'discovery set: absolute entries, extras and resolved relative entries, without repeats' ($disc.Count -eq 3 -and
    $disc -ccontains 'C:\Program Files\WindowsPowerShell\Modules' -and $disc -ccontains 'C:\Windows\system32\WindowsPowerShell\v1.0\Modules' -and
    $disc -ccontains 'C:\Windows\system32\WindowsPowerShell\Modules') ($disc -join ', ')

# Who may write in the discovery set: SYSTEM, Administrators, TrustedInstaller; CREATOR
# OWNER only as an inherit-only entry; a deny entry or a read-only entry never counts
function New-Ace([string]$Sid, $Rights, [string]$Type, [bool]$InheritOnly) { [ordered]@{ Sid = $Sid; Rights = [int]$Rights; Type = $Type; InheritOnly = $InheritOnly } }
$ti = 'S-1-5-80-956008885-3418522649-1831038044-1853292631-2271478464'
$okAces = @((New-Ace 'S-1-5-18' $r::FullControl 'Allow' $false), (New-Ace 'S-1-5-32-544' $r::Modify 'Allow' $false), (New-Ace $ti $r::FullControl 'Allow' $false),
    (New-Ace 'S-1-3-0' $r::FullControl 'Allow' $true), (New-Ace 'S-1-5-32-545' $r::ReadAndExecute 'Allow' $false), (New-Ace 'S-1-5-32-545' $r::Modify 'Deny' $false))
Add-Case 'discovery writers: SYSTEM, Administrators, TrustedInstaller, inherit-only CREATOR OWNER, read-only and deny entries are accepted' (@(Get-RefuteAceWriters $okAces).Count -eq 0)
foreach ($badAce in @((New-Ace 'S-1-5-32-545' $r::Modify 'Allow' $false), (New-Ace 'S-1-5-11' $r::AppendData 'Allow' $false),
        (New-Ace 'S-1-3-0' $r::FullControl 'Allow' $false), (New-Ace 'S-1-1-0' $r::WriteData 'Allow' $true))) {
    Add-Case "discovery writers: $($badAce.Sid) with rights $($badAce.Rights) (inherit-only $($badAce.InheritOnly)) is a writer" (@(Get-RefuteAceWriters @($badAce)).Count -eq 1)
}
# Owners and ancestors (Codex review of #114): an owner outside SYSTEM, Administrators and
# TrustedInstaller is refused; an ancestor counts only the rights that replace what is
# below it, never creating a new child nor an inherit-only entry
Add-Case 'owner: SYSTEM, Administrators, TrustedInstaller are allowed' ((Test-RefuteAllowedOwner 'S-1-5-18') -and (Test-RefuteAllowedOwner 'S-1-5-32-544') -and (Test-RefuteAllowedOwner $ti))
Add-Case 'owner: Users, Authenticated Users and CREATOR OWNER are refused' (-not (Test-RefuteAllowedOwner 'S-1-5-32-545') -and -not (Test-RefuteAllowedOwner 'S-1-5-11') -and -not (Test-RefuteAllowedOwner 'S-1-3-0'))
$ancOk = @((New-Ace 'S-1-5-11' $r::AppendData 'Allow' $false), (New-Ace 'S-1-5-11' $r::WriteData 'Allow' $false), (New-Ace 'S-1-5-11' $r::Modify 'Allow' $true), (New-Ace 'S-1-5-32-544' $r::FullControl 'Allow' $false))
Add-Case 'ancestor: creating a child, an inherit-only entry and Administrators are accepted' (@(Get-RefuteAncestorWriters $ancOk).Count -eq 0)
foreach ($ancBad in @((New-Ace 'S-1-5-11' $r::DeleteSubdirectoriesAndFiles 'Allow' $false), (New-Ace 'S-1-5-32-545' $r::ChangePermissions 'Allow' $false), (New-Ace 'S-1-1-0' $r::TakeOwnership 'Allow' $false), (New-Ace 'S-1-5-32-545' $r::Delete 'Allow' $false))) {
    Add-Case "ancestor: $($ancBad.Sid) with rights $($ancBad.Rights) can replace what is below" (@(Get-RefuteAncestorWriters @($ancBad)).Count -eq 1)
}

# Generic rights (Codex review of the integrated JEA package): GENERIC_ALL (0x10000000) and
# GENERIC_WRITE (0x40000000), which Windows can keep unmapped on an inherit-only entry,
# count as the specific rights they grant; GENERIC_READ (0x80000000) and GENERIC_EXECUTE
# (0x20000000) never count as writing
$ga, $gx, $gw, $gr = 0x10000000, 0x20000000, 0x40000000, 0x80000000
Add-Case 'generic rights: GENERIC_ALL maps to every right' ((ConvertTo-RefuteSpecificRights $ga) -eq [int]$r::FullControl)
Add-Case 'generic rights: GENERIC_WRITE maps to FILE_GENERIC_WRITE' ((ConvertTo-RefuteSpecificRights $gw) -eq [int]($r::WriteData -bor $r::AppendData -bor $r::WriteAttributes -bor $r::WriteExtendedAttributes -bor $r::ReadPermissions -bor $r::Synchronize))
foreach ($gBad in @((New-Ace 'S-1-5-32-545' $ga 'Allow' $true), (New-Ace 'S-1-5-32-545' $gw 'Allow' $true), (New-Ace 'S-1-5-11' $ga 'Allow' $false), (New-Ace 'S-1-5-11' $gw 'Allow' $false))) {
    Add-Case "generic rights: $($gBad.Sid) with $('0x{0:X8}' -f $gBad.Rights) (inherit-only $($gBad.InheritOnly)) is a writer" (@(Get-RefuteAceWriters @($gBad)).Count -eq 1)
}
foreach ($gOk in @((New-Ace 'S-1-5-32-545' $gr 'Allow' $true), (New-Ace 'S-1-5-32-545' $gx 'Allow' $false), (New-Ace 'S-1-5-32-545' ($gr -bor $gx) 'Allow' $false))) {
    Add-Case "generic rights: $($gOk.Sid) with $('0x{0:X8}' -f $gOk.Rights) only reads" (@(Get-RefuteAceWriters @($gOk)).Count -eq 0)
}
Add-Case 'generic rights: GENERIC_ALL on an ancestor can replace what is below' (@(Get-RefuteAncestorWriters @(New-Ace 'S-1-5-32-545' $ga 'Allow' $false)).Count -eq 1)
Add-Case 'generic rights: GENERIC_WRITE on an ancestor only creates children' (@(Get-RefuteAncestorWriters @(New-Ace 'S-1-5-32-545' $gw 'Allow' $false)).Count -eq 0)

# Owner and access entries by SID, never by translated names (the maintainer's decision of
# 2026-10-16, after 'ALL APPLICATION PACKAGES' could not be translated on a Portuguese
# Windows). A synthetic security object: its rules by SID are S-1-15-2-1 (ALL APPLICATION
# PACKAGES, read, an INHERITED entry) and S-1-15-2-2 (ALL RESTRICTED APPLICATION PACKAGES,
# GENERIC_WRITE, inherit-only, an EXPLICIT entry); read by name it would give the Portuguese
# names, and reading it by name (Access, Owner, or rules of the NTAccount type) is counted
# as a failure; so is leaving out the explicit or the inherited entries (Codex review).
# Windows only: the access control types of .NET are not supported elsewhere.
if ($onWindows) {
    $ptNames = @('AUTORIDADE DE PACOTE DE APLICATIVOS\TODOS OS PACOTES DE APLICATIVOS',
        'AUTORIDADE DE PACOTE DE APLICATIVOS\TODOS OS PACOTES DE APLICATIVOS RESTRITOS')
    $script:byName = 0
    $script:partial = 0
    # the rules come from a real in-memory descriptor (SDDL keeps GW unmapped, as Windows
    # can on an inherit-only entry; ID marks an inherited entry); the synthetic object only
    # wraps it, and returns the explicit and the inherited entries as asked
    $sddlAcl = New-Object System.Security.AccessControl.DirectorySecurity
    $sddlAcl.SetSecurityDescriptorSddlForm('O:BAD:(A;OICIIO;GW;;;S-1-15-2-2)(A;ID;0x1200a9;;;S-1-15-2-1)')
    $sidRules = @($sddlAcl.GetAccessRules($true, $true, [System.Security.Principal.SecurityIdentifier]))
    $fakeAcl = New-Object PSObject
    Add-Member -InputObject $fakeAcl -MemberType ScriptProperty -Name Access -Value { $script:byName++; @($ptNames | ForEach-Object { [ordered]@{ IdentityReference = $_ } }) }
    Add-Member -InputObject $fakeAcl -MemberType ScriptProperty -Name Owner -Value { $script:byName++; $ptNames[0] }
    Add-Member -InputObject $fakeAcl -MemberType ScriptMethod -Name GetOwner -Value {
        param($type)
        if ($type -ne [System.Security.Principal.SecurityIdentifier]) { $script:byName++ }
        New-Object System.Security.Principal.SecurityIdentifier 'S-1-5-32-544'
    }
    Add-Member -InputObject $fakeAcl -MemberType ScriptMethod -Name GetAccessRules -Value {
        param($explicit, $inherited, $type)
        if ($type -ne [System.Security.Principal.SecurityIdentifier]) { $script:byName++ }
        if (-not ($explicit -and $inherited)) { $script:partial++ }
        @($sidRules | Where-Object { ($_.IsInherited -and $inherited) -or (-not $_.IsInherited -and $explicit) })
    }
    $converted = ConvertTo-RefuteAclEntries $fakeAcl
    $convertedSids = @($converted.Entries | ForEach-Object { $_.Sid } | Sort-Object)
    Add-Case 'ACL by SID: the owner and the explicit and inherited entries come by SID, the Portuguese names are never read' (
        $script:byName -eq 0 -and $script:partial -eq 0 -and $converted.Owner -eq 'S-1-5-32-544' -and ($convertedSids -join ',') -eq 'S-1-15-2-1,S-1-15-2-2'
    ) "byName=$($script:byName) partial=$($script:partial) owner=$($converted.Owner) sids=$($convertedSids -join ',')"
    $restricted = @($converted.Entries | Where-Object { $_.Sid -eq 'S-1-15-2-2' })
    Add-Case 'ACL by SID: GENERIC_WRITE inherit-only for S-1-15-2-2 is a writer, read-only S-1-15-2-1 is not' (
        @(Get-RefuteAceWriters $converted.Entries).Count -eq 1 -and $restricted[0].InheritOnly -and $restricted[0].Rights -eq $gw) ((@(Get-RefuteAceWriters $converted.Entries)) -join ' | ')
    # a real folder that holds ALL APPLICATION PACKAGES entries: the check reads it (the
    # names translation used to make it "cannot be read" on a Portuguese Windows)
    $pshomeModules = Join-Path $PSHOME 'Modules'
    $pshomeProblems = @(Get-RefuteItemProblems -Item $pshomeModules -IsAncestor $false)
    $pshomeSids = @((ConvertTo-RefuteAclEntries (Get-Acl -LiteralPath $pshomeModules)).Entries | ForEach-Object { $_.Sid })
    Add-Case 'ACL by SID: $PSHOME\Modules is read, with its S-1-15-2-1 entry, and reports no problem' (
        $pshomeProblems.Count -eq 0 -and $pshomeSids -contains 'S-1-15-2-1') (($pshomeProblems + $pshomeSids) -join ' | ')
}

# on real folders: a folder the current account can write (the test's work folder) is
# reported at every level (the root, a module folder, its RoleCapabilities, a .psrc, and a
# module folder with no RoleCapabilities), its owner too; an absent folder is checked
# through its nearest existing ancestor
$discRoot = Join-Path $WorkDir 'discovery'
[void][System.IO.Directory]::CreateDirectory((Join-Path $discRoot 'SomeModule\RoleCapabilities'))
[void][System.IO.Directory]::CreateDirectory((Join-Path $discRoot 'NoRoles'))
[System.IO.File]::WriteAllText((Join-Path $discRoot 'SomeModule\RoleCapabilities\Op.psrc'), '@{}')
$discProblems = @(Get-RefuteDiscoveryProblems -Roots @($discRoot))
if ($onWindows) {
    foreach ($level in @($discRoot, (Join-Path $discRoot 'SomeModule'), (Join-Path $discRoot 'SomeModule\RoleCapabilities'),
            (Join-Path $discRoot 'SomeModule\RoleCapabilities\Op.psrc'), (Join-Path $discRoot 'NoRoles'))) {
        Add-Case "discovery problems: '$($level.Substring($WorkDir.Length + 1))' writable by the current account is reported" (
            @($discProblems | Where-Object { $_.StartsWith("$level can be written by") }).Count -ge 1) ($discProblems -join ' | ')
    }
    Add-Case 'discovery problems: a root owned by the current account is reported' (@($discProblems | Where-Object { $_.StartsWith("$discRoot is owned by") }).Count -eq 1) ($discProblems -join ' | ')
    $absentProblems = @(Get-RefuteDiscoveryProblems -Roots @(Join-Path $discRoot 'absent\deeper'))
    Add-Case 'discovery problems: an absent folder is checked through its nearest existing ancestor' (
        @($absentProblems | Where-Object { $_.StartsWith("$discRoot can be written by") }).Count -ge 1) ($absentProblems -join ' | ')
    # the folders above that ancestor are checked as ancestors (Codex review of #114, round
    # 2): the work folder, owned by the current account, is reported
    Add-Case 'discovery problems: the ancestors above the nearest existing one are checked too' (
        @($absentProblems | Where-Object { $_.StartsWith("$WorkDir is owned by") }).Count -eq 1) ($absentProblems -join ' | ')
} else {
    # Windows ACLs cannot be read here (no Get-Acl): every folder is reported as unreadable,
    # never accepted (the registration itself runs only on Windows)
    Add-Case 'discovery problems: without Windows ACLs every level is reported, never accepted' (
        @($discProblems | Where-Object { $_.StartsWith("$discRoot cannot be read") }).Count -ge 1) ($discProblems -join ' | ')
}

# The folders the role capability's imports load from (Get-RefuteTreeProblems, Codex review
# of #118): every file and folder below the root gets the full check, every ancestor the
# ancestor check; a reparse point and a missing root are problems
$treeRoot = Join-Path $WorkDir 'imports'
[void][System.IO.Directory]::CreateDirectory((Join-Path $treeRoot 'deep\deeper'))
[System.IO.File]::WriteAllText((Join-Path $treeRoot 'deep\deeper\Some.dll'), 'x')
$treeProblems = @(Get-RefuteTreeProblems -Roots @($treeRoot))
if ($onWindows) {
    foreach ($level in @($treeRoot, (Join-Path $treeRoot 'deep'), (Join-Path $treeRoot 'deep\deeper'), (Join-Path $treeRoot 'deep\deeper\Some.dll'))) {
        Add-Case "import trees: '$($level.Substring($WorkDir.Length + 1))' writable and owned by the current account is reported" (
            @($treeProblems | Where-Object { $_.StartsWith("$level can be written by") }).Count -ge 1 -and
            @($treeProblems | Where-Object { $_.StartsWith("$level is owned by") }).Count -eq 1) ($treeProblems -join ' | ')
    }
    Add-Case 'import trees: the ancestors are checked as ancestors' (
        @($treeProblems | Where-Object { $_.StartsWith("$WorkDir is owned by") }).Count -eq 1) ($treeProblems -join ' | ')
    # a junction (no administrator right needed) inside the tree is refused
    $junction = Join-Path $treeRoot 'link'
    New-Item -ItemType Junction -Path $junction -Value (Join-Path $treeRoot 'deep') | Out-Null
    $linkProblems = @(Get-RefuteTreeProblems -Roots @($treeRoot))
    Add-Case 'import trees: a junction inside the tree is a problem' (
        @($linkProblems | Where-Object { $_ -eq "$junction is a reparse point (a link or junction)" }).Count -eq 1) ($linkProblems -join ' | ')
    # the real folders of the role capability's imports on this machine: none of them may
    # report a problem (the registration refuses otherwise); only where they exist
    $systemTrees = @(
        (Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\Modules\Microsoft.PowerShell.Utility'),
        (Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\Modules\Hyper-V'),
        (Join-Path $env:SystemRoot 'Microsoft.NET\assembly\GAC_MSIL\Microsoft.HyperV.PowerShell.Cmdlets'))
    if (@($systemTrees | Where-Object { -not (Test-Path -LiteralPath $_ -PathType Container) }).Count -eq 0) {
        $systemProblems = @(Get-RefuteTreeProblems -Roots $systemTrees)
        Add-Case 'import trees: the folders of this Windows machine report no problem' ($systemProblems.Count -eq 0) ($systemProblems -join ' | ')
    }
}
$missingTree = @(Get-RefuteTreeProblems -Roots @(Join-Path $treeRoot 'absent'))
Add-Case 'import trees: a missing folder is a problem' ($missingTree.Count -eq 1 -and $missingTree[0] -eq "$(Join-Path $treeRoot 'absent') does not exist") ($missingTree -join ' | ')

# The JEA session probe (tests/vm/JeaProbe.psm1) on synthetic roots: a root holding a role
# capability, an absent root, and a root that cannot be read as a folder (a file). A root
# that cannot be read is never reported as absent (Codex review of #99).
$probeRole = New-RoleFile @('probe-roots', 'present', 'Mod')
$present = Join-Path (Join-Path $WorkDir 'probe-roots') 'present'
$absent = Join-Path (Join-Path $WorkDir 'probe-roots') 'absent'
$fileRoot = Join-Path (Join-Path $WorkDir 'probe-roots') 'a-file'
[System.IO.File]::WriteAllText($fileRoot, 'x')
Import-Module (Join-Path (Join-Path (Join-Path $Root 'tests') 'vm') 'JeaProbe.psm1') -Force
$savedModulePath = [Environment]::GetEnvironmentVariable('PSModulePath', 'Process')
$savedCwd = [System.IO.Directory]::GetCurrentDirectory()
try {
    # a relative entry ('present') resolves against the process's current folder
    [System.IO.Directory]::SetCurrentDirectory((Join-Path $WorkDir 'probe-roots'))
    [Environment]::SetEnvironmentVariable('PSModulePath', "$present;$absent;$fileRoot;present", 'Process')
    $probeText = Get-RefuteJeaModuleRoots
} finally {
    [System.IO.Directory]::SetCurrentDirectory($savedCwd)
    [Environment]::SetEnvironmentVariable('PSModulePath', $savedModulePath, 'Process')
    Remove-Module JeaProbe
}
$probeLines = @($probeText.Split("`n"))
$probeRows = @($probeLines[1..($probeLines.Count - 1)] | ForEach-Object { , @($_.Split("`t")) })
Add-Case 'JEA probe: the current folder first, then one line of six fields per entry' ($probeLines[0].StartsWith("cwd`t") -and $probeRows.Count -eq 4 -and @($probeRows | Where-Object { $_.Count -ne 6 }).Count -eq 0) $probeText
Add-Case 'JEA probe: a present root lists its role capability' ($probeRows[0][0] -eq 'present' -and $probeRows[0][1] -eq $present -and $probeRows[0][5] -eq $probeRole) ($probeRows[0] -join ' | ')
Add-Case 'JEA probe: an absent root is confirmed absent' ($probeRows[1][0] -eq 'absent' -and $probeRows[1][4] -eq '') ($probeRows[1] -join ' | ')
$onWindows = [System.Environment]::OSVersion.Platform -eq [System.PlatformID]::Win32NT
if ($onWindows) {
    # on Windows a file read as a folder is an IOException, never DirectoryNotFound
    Add-Case 'JEA probe: a root that cannot be read is an error, never absent' ($probeRows[2][0] -eq 'error' -and $probeRows[2][4]) ($probeRows[2] -join ' | ')
} else {
    Add-Case 'JEA probe: a root that cannot be read is never present' ($probeRows[2][0] -ne 'present') ($probeRows[2] -join ' | ')
}
Add-Case 'JEA probe: a relative entry is inspected where the process resolves it' ($probeRows[3][1] -eq 'present' -and $probeRows[3][3] -eq $present -and $probeRows[3][0] -eq 'present' -and $probeRows[3][5] -eq $probeRole) ($probeRows[3] -join ' | ')
if ($onWindows) {
    # a drive-relative entry ('C:') is the current folder of that drive, never its root
    $drive = (Join-Path $WorkDir 'probe-roots').Substring(0, 2)
    Import-Module (Join-Path (Join-Path (Join-Path $Root 'tests') 'vm') 'JeaProbe.psm1') -Force
    try {
        [System.IO.Directory]::SetCurrentDirectory($present)
        [Environment]::SetEnvironmentVariable('PSModulePath', $drive, 'Process')
        $driveText = Get-RefuteJeaModuleRoots
    } finally {
        [System.IO.Directory]::SetCurrentDirectory($savedCwd)
        [Environment]::SetEnvironmentVariable('PSModulePath', $savedModulePath, 'Process')
        Remove-Module JeaProbe
    }
    $driveRow = @($driveText.Split("`n"))[1].Split("`t")
    Add-Case "JEA probe: '$drive' resolves to the current folder of the drive, not '$drive\'" ($driveRow[1] -eq $drive -and $driveRow[3] -eq $present -and $driveRow[0] -eq 'present') ($driveRow -join ' | ')
}

# WinRM listener removal plan
$plan1 = Get-RefuteListenerRemoval -Names @('*+HTTP') -Target '*+HTTP'
Add-Case 'listener: *+HTTP alone, nothing remains' ($plan1.TargetPresent -and @($plan1.Remaining).Count -eq 0 -and @($plan1.ForeignRemaining).Count -eq 0)
$plan2 = Get-RefuteListenerRemoval -Names @('*+HTTP', 'IP:127.0.0.1+HTTP', 'IP:::1+HTTP') -Target '*+HTTP'
Add-Case 'listener: loopback HTTP may remain' ($plan2.TargetPresent -and @($plan2.Remaining).Count -eq 2 -and @($plan2.ForeignRemaining).Count -eq 0)
$plan3 = Get-RefuteListenerRemoval -Names @('*+HTTP', '*+HTTPS', 'IP:10.0.0.5+HTTP', 'IP:127.0.0.1+HTTPS') -Target '*+HTTP'
Add-Case 'listener: other non-loopback or HTTPS listeners are reported' (@($plan3.ForeignRemaining).Count -eq 3)
$plan4 = Get-RefuteListenerRemoval -Names @('IP:127.0.0.1+HTTP') -Target '*+HTTP'
Add-Case 'listener: target absent' (-not $plan4.TargetPresent)
$plan5 = Get-RefuteListenerRemoval -Names @() -Target '*+HTTP'
Add-Case 'listener: no listener at all' (-not $plan5.TargetPresent -and @($plan5.ForeignRemaining).Count -eq 0)

# .reg export check
$key = 'HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\WSMAN\Listener\*+HTTP'
$good = "Windows Registry Editor Version 5.00`r`n`r`n[$key]`r`n`"Port`"=dword:00001761`r`n"
Add-Case 'reg export: exactly the key' (Test-RefuteRegExport -Text $good -KeyPath $key)
Add-Case 'reg export: a subkey of the key is allowed' (Test-RefuteRegExport -Text ($good + "[$key\sub]`r`n") -KeyPath $key)
Add-Case 'reg export: another key is refused' (-not (Test-RefuteRegExport -Text ($good + "[HKEY_LOCAL_MACHINE\SOFTWARE\Other]`r`n") -KeyPath $key))
Add-Case 'reg export: a sibling key is refused' (-not (Test-RefuteRegExport -Text ($good + "[$key" + "S]`r`n") -KeyPath $key))
Add-Case 'reg export: the key missing is refused' (-not (Test-RefuteRegExport -Text "Windows Registry Editor Version 5.00`r`n" -KeyPath $key))

function Get-PsrcImports([string]$Path) {
    # The ModulesToImport entries of one role capability file: a string (a name or a
    # path) as it is, a hashtable as its sorted key names (tests/test_vm_scripts.py refuses
    # version and GUID keys, which make PowerShell call Get-Module in the restricted session).
    $data = Import-PowerShellDataFile -LiteralPath $Path
    $entries = @()
    if ($data.ContainsKey('ModulesToImport')) { $entries = @($data.ModulesToImport) }
    return @($entries | ForEach-Object {
            if ($_ -is [System.Collections.IDictionary]) {
                # "Names", not "Keys": a key named Keys would hide the dictionary's own .Keys
                [ordered]@{ Kind = 'table'; Names = @($_.Keys | ForEach-Object { [string]$_ } | Sort-Object) }
            } else {
                [ordered]@{ Kind = 'string'; Value = [string]$_ }
            }
        })
}

# every .psrc of the repository (top-level folders starting with '.' are skipped: .git,
# .venv, .cache), and a synthetic file with the refused keys (the detector sees them)
$out.RoleCapabilityImports = [ordered]@{}
$tops = @(Get-ChildItem -LiteralPath $Root -Force | Where-Object { -not $_.Name.StartsWith('.') })
foreach ($top in $tops) {
    $found = if ($top.PSIsContainer) { @(Get-ChildItem -LiteralPath $top.FullName -Recurse -File -Filter '*.psrc') } elseif ($top.Extension -eq '.psrc') { @($top) } else { @() }
    foreach ($file in $found) {
        $out.RoleCapabilityImports[$file.FullName.Substring($Root.Length + 1).Replace('\', '/')] = @(Get-PsrcImports $file.FullName)
    }
}
$probe = Join-Path $WorkDir 'probe.psrc'
[System.IO.File]::WriteAllText($probe, "@{ ModulesToImport = @('Plain', @{ ModuleName = 'X'; RequiredVersion = '1.0'; GUID = 'b2713b52-46f8-4c00-a4bf-2b940708587a' }, @{ ModuleName = 'Y'; ModuleVersion = '1.0'; MaximumVersion = '2.0' }) }")
$out.RoleCapabilityProbe = @(Get-PsrcImports $probe)

# The remoting calls of Invoke-RefuteVm.ps1 and their parameter names, from the AST: the
# endpoint (AccessMode Local) needs -EnableNetworkAccess and implicit credentials.
$invokeAst = [System.Management.Automation.Language.Parser]::ParseFile((Join-Path $vmDir 'Invoke-RefuteVm.ps1'), [ref]$null, [ref]$null)
$out.InvokeRemoting = @($invokeAst.FindAll({ param($n) $n -is [System.Management.Automation.Language.CommandAst] }, $true) |
        Where-Object { @('New-PSSession', 'Enter-PSSession', 'Invoke-Command', 'New-CimSession') -contains $_.GetCommandName() } |
        ForEach-Object {
            # the literal value that follows a parameter, when it is a constant
            $values = [ordered]@{}
            $elements = @($_.CommandElements)
            for ($i = 0; $i -lt $elements.Count - 1; $i++) {
                if ($elements[$i] -is [System.Management.Automation.Language.CommandParameterAst] -and
                    $elements[$i + 1] -is [System.Management.Automation.Language.StringConstantExpressionAst]) {
                    $values[$elements[$i].ParameterName] = $elements[$i + 1].Value
                }
            }
            [ordered]@{
                Command    = $_.GetCommandName()
                Parameters = @($_.CommandElements | Where-Object { $_ -is [System.Management.Automation.Language.CommandParameterAst] } |
                        ForEach-Object { $_.ParameterName } | Sort-Object)
                Values     = $values
            }
        })

$out.Cases = $cases.ToArray()
ConvertTo-RefuteCanonicalJson $out
