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
try { Copy-RefuteVerifiedFile -Source $src -Destination $dst2 -Sha256 $srcSha } catch { $failed = $_.Exception.Message }
Add-Case 'verified copy never overwrites' ($failed -like '*already exists*')

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
$volume = @(Join-RefuteModuleRoots -PathValues @('C:\;D:\Mods\;\\srv\share\Mods\') -Extra @())
Add-Case 'module roots: a volume root keeps its backslash' ($volume.Count -eq 3 -and $volume -ccontains 'C:\' -and $volume -ccontains 'D:\Mods' -and $volume -ccontains '\\srv\share\Mods') ($volume -join ', ')
foreach ($relative in 'Modules', 'C:Modules', '.\Modules', '\Modules') {
    $refused = $false
    try { [void](Join-RefuteModuleRoots -PathValues @("C:\A;$relative") -Extra @()) } catch { $refused = $true }
    Add-Case "module roots: the relative entry '$relative' is refused" $refused
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

$out.Cases = $cases.ToArray()
ConvertTo-RefuteCanonicalJson $out
