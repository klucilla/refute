# Switches the Refute VM's port to a network profile through the endpoint (each operation
# simulated, then run with the simulated plan), reads the profile back from the endpoint's
# status, checks it, and writes the host's record of the profile in force
# (refute-vm-profile-1, docs/validation/v0.3/wp3-dossier-provenance-acceptance.md):
#   {format, execution_id, paper, claim_sha256, phase, profile, read_utc, checks, script_sha256}
# The record holds no host value (no VM name, path, switch or address): only the profile,
# the bindings, the time it was read, the checks (each true) and this script's SHA-256.
# The operator copies it to the VM (the build record before the launch, given to the engine
# with --profile-status; the run record as the run-phase flag, written atomically).
# A normal, non-administrator window:
#   powershell -NoProfile -ExecutionPolicy Bypass -File scripts/vm/Switch-RefuteVmProfile.ps1 `
#       -Profile build|pull -Paper <id> -ExecutionId <32 hex> -ClaimSha256 <64 hex> -Record <file>
param(
    [Parameter(Mandatory)][ValidateSet('build', 'pull')][string]$Profile,
    [Parameter(Mandatory)][ValidatePattern('^[a-z0-9]+$')][string]$Paper,
    [Parameter(Mandatory)][ValidatePattern('^[0-9a-f]{32}$')][string]$ExecutionId,
    [Parameter(Mandatory)][ValidatePattern('^[0-9a-f]{64}$')][string]$ClaimSha256,
    [Parameter(Mandatory)][string]$Record
)
$ErrorActionPreference = 'Stop'
$endpoint = Join-Path $PSScriptRoot 'Invoke-RefuteVm.ps1'
if (Test-Path -LiteralPath $Record) { throw "refused: $Record exists" }

function Invoke-Endpoint([string[]]$Arguments) {
    $raw = & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $endpoint @Arguments 2>&1 | Out-String
    try { return $raw | ConvertFrom-Json -ErrorAction Stop } catch { throw "the endpoint's reply is not JSON: $raw" }
}

foreach ($op in @(@('DisconnectNetwork'), @('SetPortProfile', '-Profile', $Profile), @('ConnectNetwork'))) {
    $sim = Invoke-Endpoint (@('-Operation') + $op + @('-Simulate'))
    if ($sim.Plan.Refusal) { throw "the simulation of $($op[0]) was refused: $($sim.Plan.Refusal)" }
    if ($sim.Plan.AlreadyDone) { Write-Output "$($op[0]): already done"; continue }
    $run = Invoke-Endpoint (@('-Operation') + $op + @('-PlanSha256', $sim.PlanSha256))
    if ($run.Outcome -ne 'done') { throw "$($op[0]) did not end done: $($run.Outcome)" }
    Write-Output "$($op[0]): done"
}

# the profile in force, read back from the endpoint's status
$status = Invoke-Endpoint @('-Status')
$vm = @($status.Observed.Vms | Where-Object { $_.Name -eq $status.Config.VmName })
if ($vm.Count -ne 1) { throw 'the Refute VM is not in the status' }
$adapters = @($vm[0].NetworkAdapters)
if ($adapters.Count -ne 1) { throw 'the VM does not have exactly one adapter' }
$acls = @($adapters[0].Acls)
$proxy = @($acls | Where-Object { $_.RemoteIPAddress -eq $status.Config.ProxyAddress })
$onSwitch = ($adapters[0].SwitchId -eq $status.Config.NetworkSwitchId)
if ($Profile -eq 'pull') { $entries = ($acls.Count -eq 3 -and $proxy.Count -eq 0) } else { $entries = ($proxy.Count -gt 0) }
if (-not $onSwitch) { throw 'the adapter is not on the configured switch; no record written' }
if (-not $entries) { throw "the port's entries are not those of the profile $Profile; no record written" }

$phase = if ($Profile -eq 'build') { 'build' } else { 'run' }
# this script's SHA-256 as stored in the repository (LF line endings, whatever the checkout's)
$text = [System.IO.File]::ReadAllText($PSCommandPath) -replace "`r`n", "`n"
$sha = [System.Security.Cryptography.SHA256]::Create()
$digest = $sha.ComputeHash((New-Object System.Text.UTF8Encoding($false)).GetBytes($text))
$scriptSha256 = -join ($digest | ForEach-Object { $_.ToString('x2') })
$record = [ordered]@{
    format        = 'refute-vm-profile-1'
    execution_id  = $ExecutionId
    paper         = $Paper
    claim_sha256  = $ClaimSha256
    phase         = $phase
    profile       = $Profile
    read_utc      = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
    checks        = [ordered]@{ adapter_on_configured_switch = $true; entries_of_the_profile = $true }
    script_sha256 = $scriptSha256
}
$json = $record | ConvertTo-Json -Compress
[System.IO.File]::WriteAllText($Record, $json + "`n", (New-Object System.Text.UTF8Encoding($false)))
Write-Output "profile $Profile in force, read back from the status; record written: $Record"
