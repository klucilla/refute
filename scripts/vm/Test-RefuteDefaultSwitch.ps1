# Checks, with no administrator rights, whether the host's IPv4 address on
# "vEthernet (Default Switch)" is still the DHCP server the proxy VM's egress ACL allows
# (admin/Set-RefuteProxyAcls.ps1 -DhcpServer). Windows can give the Default Switch another
# prefix after a restart; the proxy VM then gets no address and nothing can be built (seen on
# 2026-10-19: the ACL allowed the old server only). The value recorded when the ACL was last
# set is kept in the project's git-ignored .cache, so no host address enters the repository.
#   powershell -NoProfile -ExecutionPolicy Bypass -File scripts/vm/Test-RefuteDefaultSwitch.ps1 [-Record]
# Exit 0: the address equals the recorded one (or -Record wrote it); 1: it changed (the
# maintainer sets the ACL again with the new server, then this script runs with -Record);
# 2: nothing recorded yet, or the adapter has no single IPv4 address.
# -Observed replaces the reading of the adapter (tests only).
param(
    [switch]$Record,
    [string]$StatePath = '',
    [string]$Observed = ''
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2.0
$Alias = 'vEthernet (Default Switch)'
if (-not $StatePath) { $StatePath = Join-Path $PSScriptRoot '..\..\.cache\vm\default-switch.json' }

if ($Observed) { $now = @($Observed) }
else {
    $now = @(Get-NetIPAddress -InterfaceAlias $Alias -AddressFamily IPv4 -ErrorAction SilentlyContinue |
            ForEach-Object { $_.IPAddress })
}
if ($now.Count -ne 1 -or $now[0] -notmatch '^\d{1,3}(\.\d{1,3}){3}$') {
    Write-Output "The adapter '$Alias' has not exactly one IPv4 address ($($now.Count)): is Hyper-V's Default Switch up?"
    exit 2
}
$address = $now[0]

if ($Record) {
    $folder = Split-Path -Parent $StatePath
    if (-not (Test-Path -LiteralPath $folder)) { New-Item -ItemType Directory -Path $folder | Out-Null }
    $state = [ordered]@{ dhcp_server = $address; recorded_utc = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ') }
    [System.IO.File]::WriteAllText($StatePath, ((New-Object psobject -Property $state) | ConvertTo-Json) + "`n")
    Write-Output "Recorded: the proxy's egress ACL allows the DHCP server $address."
    exit 0
}

if (-not (Test-Path -LiteralPath $StatePath)) {
    Write-Output "Nothing recorded yet. After the proxy's ACL is set with -DhcpServer $address, run this script with -Record."
    exit 2
}
$recorded = (Get-Content -LiteralPath $StatePath -Raw | ConvertFrom-Json).dhcp_server
if ($recorded -eq $address) {
    Write-Output "Unchanged: the Default Switch's address is the recorded DHCP server ($address)."
    exit 0
}
Write-Output "CHANGED: the Default Switch's address is $address; the proxy's egress ACL allows $recorded."
Write-Output 'The proxy VM will get no address. The maintainer, as Administrator:'
Write-Output '  Stop-VM -Name refute-proxy'
Write-Output "  scripts/vm/admin/Set-RefuteProxyAcls.ps1 -DhcpServer $address -Apply"
Write-Output '  Start-VM -Name refute-proxy'
Write-Output 'Check: each adapter reads back the entries expected; then this script with -Record.'
exit 1
