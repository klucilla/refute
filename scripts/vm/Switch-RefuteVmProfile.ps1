# Switches the Refute VM's port to a network profile through the endpoint (each operation
# simulated, then run with the simulated plan), reads the profile back from the endpoint's
# status, checks it, and writes the host's record of the profile in force
# (refute-vm-profile-1, docs/validation/v0.3/wp3-dossier-provenance-acceptance.md):
#   {format, execution_id, paper, claim_sha256, phase, profile, read_utc, checks, script_sha256}
# The record holds no host value (no VM name, path, switch or address): only the profile,
# the bindings, the time it was read, the checks (each true) and this script's SHA-256.
# The profile in force is the one whose whole normalized entry list equals the adapter's
# (Get-RefuteVmProfileInForce of RefuteVm.Core.ps1, the endpoint's own comparison).
# The operator copies the record to the VM (the build record before the launch, given to the
# engine with --profile-status; the run record as the run-phase flag, written atomically).
# A normal, non-administrator window:
#   powershell -NoProfile -ExecutionPolicy Bypass -File scripts/vm/Switch-RefuteVmProfile.ps1 `
#       -Profile build|pull -Paper <id> -ExecutionId <32 hex> -ClaimSha256 <64 hex> -RecordPath <file>
# With -CheckOnly: no operation and no record; it prints the profile in force (read only).
param(
    [Parameter(Mandatory)][ValidateSet('build', 'pull')][string]$Profile,
    [ValidatePattern('^[a-z0-9]+$')][string]$Paper,
    [ValidatePattern('^[0-9a-f]{32}$')][string]$ExecutionId,
    [ValidatePattern('^[0-9a-f]{64}$')][string]$ClaimSha256,
    [string]$RecordPath,
    [switch]$CheckOnly
)
$ErrorActionPreference = 'Stop'
$endpoint = Join-Path $PSScriptRoot 'Invoke-RefuteVm.ps1'
. (Join-Path $PSScriptRoot 'RefuteVm\RefuteVm.Core.ps1')
if (-not $CheckOnly) {
    if (-not ($Paper -and $ExecutionId -and $ClaimSha256 -and $RecordPath)) {
        throw 'a switch needs -Paper, -ExecutionId, -ClaimSha256 and -RecordPath'
    }
    if (Test-Path -LiteralPath $RecordPath) { throw "refused: $RecordPath exists" }
}

function Invoke-Endpoint([string[]]$Arguments) {
    $raw = & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $endpoint @Arguments 2>&1 | Out-String
    try { return $raw | ConvertFrom-Json -ErrorAction Stop } catch { throw "the endpoint's reply is not JSON: $raw" }
}

function Get-ProfileInForce($Status) {
    # the endpoint's comparison of the whole entry list, on the status read back
    $vm = @($Status.Observed.Vms | Where-Object { $_.Name -eq $Status.Config.VmName })
    if ($vm.Count -ne 1) { throw 'the Refute VM is not in the status' }
    $adapters = @($vm[0].NetworkAdapters)
    if ($adapters.Count -ne 1) { throw 'the VM does not have exactly one adapter' }
    $config = @{}
    foreach ($p in $Status.Config.PSObject.Properties) { $config[$p.Name] = $p.Value }
    $rules = @(@($adapters[0].Acls) | ForEach-Object {
            [ordered]@{
                Direction = [string]$_.Direction; Action = [string]$_.Action
                LocalIPAddress = [string]$_.LocalIPAddress; RemoteIPAddress = [string]$_.RemoteIPAddress
                Protocol = [string]$_.Protocol; LocalPort = [string]$_.LocalPort; RemotePort = [string]$_.RemotePort
                Weight = [int]$_.Weight; Stateful = [bool]$_.Stateful; IsolationID = [int]$_.IsolationID
            }
        })
    return [pscustomobject]@{
        OnSwitch = ([string]$adapters[0].SwitchId -ieq [string]$config.NetworkSwitchId -and $config.NetworkSwitchId)
        Profile  = (Get-RefuteVmProfileInForce -Config $config -Adapter @{ Acls = $rules })
    }
}

if ($CheckOnly) {
    $seen = Get-ProfileInForce (Invoke-Endpoint @('-Status'))
    Write-Output "on the configured switch: $([bool]$seen.OnSwitch); profile in force: '$($seen.Profile)'"
    exit 0
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
$seen = Get-ProfileInForce (Invoke-Endpoint @('-Status'))
if (-not $seen.OnSwitch) { throw 'the adapter is not on the configured switch; no record written' }
if ($seen.Profile -cne $Profile) { throw "the port's entries are those of '$($seen.Profile)', not $Profile; no record written" }

$phase = if ($Profile -eq 'build') { 'build' } else { 'run' }
# this script's SHA-256 as stored in the repository (LF line endings, whatever the checkout's)
$text = [System.IO.File]::ReadAllText($PSCommandPath) -replace "`r`n", "`n"
$sha = [System.Security.Cryptography.SHA256]::Create()
$digest = $sha.ComputeHash((New-Object System.Text.UTF8Encoding($false)).GetBytes($text))
$scriptSha256 = -join ($digest | ForEach-Object { $_.ToString('x2') })
$profileRecord = [ordered]@{
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
$json = $profileRecord | ConvertTo-Json -Compress
[System.IO.File]::WriteAllText($RecordPath, $json + "`n", (New-Object System.Text.UTF8Encoding($false)))
Write-Output "profile $Profile in force, read back from the status; record written: $RecordPath"
