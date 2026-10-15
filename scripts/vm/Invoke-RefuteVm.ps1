<#
.SYNOPSIS
Calls the local JEA endpoint "RefuteVm" (scripts/vm/README.md). This is the only way the
Refute scripts act on Hyper-V: the account that runs this script has no Hyper-V rights
of its own.

.EXAMPLE
  scripts/vm/Invoke-RefuteVm.ps1 -Status
  scripts/vm/Invoke-RefuteVm.ps1 -Operation CreateVm -Simulate
  scripts/vm/Invoke-RefuteVm.ps1 -Operation CreateVm -PlanSha256 <the simulated plan's hash>

Every value is validated here and again inside the endpoint; the command sent to the
endpoint is built only from these validated values, as literals (the endpoint runs in
NoLanguage mode).
#>
[CmdletBinding(DefaultParameterSetName = 'Operation')]
param(
    [Parameter(Mandatory = $true, ParameterSetName = 'Operation')]
    [ValidateSet('SetHostPaths', 'DisableEnhancedSessionHost', 'CreateBaseDisk', 'CreateVm',
        'SetMemory', 'SetProcessor', 'SetSecureBoot', 'DisableCheckpoints',
        'DisableGuestServiceInterface', 'DisconnectNetwork', 'AttachBaseDisk',
        'ImportInstallIso', 'ImportSeedIso', 'AttachInstallMedia', 'SetBootFromInstallMedia',
        'StartVm', 'StopVm', 'DetachInstallMedia', 'SetProcessorMaximum', 'SuspendVm',
        'ResumeVm', 'SaveVm')]
    [string]$Operation,
    [Parameter(ParameterSetName = 'Operation')][switch]$Simulate,
    [Parameter(ParameterSetName = 'Operation')][ValidatePattern('^[0-9a-f]{64}$')][string]$PlanSha256 = '',
    [Parameter(ParameterSetName = 'Operation')][ValidatePattern('^[0-9a-f]{64}$')][string]$MediaSha256 = '',
    [Parameter(ParameterSetName = 'Operation')][ValidateRange(1, 100)][int]$Percent = 0,
    [Parameter(ParameterSetName = 'Operation')][ValidatePattern('^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')][string]$ServiceGuid = '',
    [Parameter(Mandatory = $true, ParameterSetName = 'Status')][switch]$Status,
    [Parameter(ParameterSetName = 'Status')][switch]$IncludeMedia
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2.0

function Get-RefuteVmCommandText {
    # The command line sent to the endpoint, from validated values only.
    param([hashtable]$Bound, [string]$Set)
    if ($Set -eq 'Status') {
        $text = 'Get-RefuteVmStatus'
        if ($Bound.ContainsKey('IncludeMedia') -and $Bound.IncludeMedia) { $text += ' -IncludeMedia' }
        return $text
    }
    $text = "Invoke-RefuteVmOperation -Operation '$($Bound.Operation)'"
    if ($Bound.ContainsKey('Simulate') -and $Bound.Simulate) { $text += ' -Simulate' }
    foreach ($name in 'PlanSha256', 'MediaSha256', 'ServiceGuid') {
        if ($Bound.ContainsKey($name) -and $Bound[$name]) {
            if ($Bound[$name] -notmatch '^[0-9a-f-]+$') { throw "invalid $name" }
            $text += " -$name '$($Bound[$name])'"
        }
    }
    if ($Bound.ContainsKey('Percent') -and $Bound.Percent) { $text += ' -Percent ' + [int]$Bound.Percent }
    return $text
}

$commandText = Get-RefuteVmCommandText -Bound $PSBoundParameters -Set $PSCmdlet.ParameterSetName
$session = New-PSSession -ComputerName localhost -ConfigurationName RefuteVm
try {
    Invoke-Command -Session $session -ScriptBlock ([scriptblock]::Create($commandText))
} finally {
    Remove-PSSession -Session $session
}
