<#
.SYNOPSIS
Sets the extended port ACLs of the two adapters of the proxy VM "refute-proxy" (WP6 phase
2; the maintainer's decisions of 2026-10-17, docs/validation/v0.3/wp6-results/
phase2-network-design.md, section 5.5). Run by the maintainer as Administrator, with the
proxy VM off. Without -Apply it only prints the entries it would set.

.DESCRIPTION
"inner" (on the internal switch refute-internal): TCP 3128 in from the Refute VM
(10.231.71.2) and TCP 22 in from the host (10.231.71.1), both stateful; everything else
denied both ways, IPv4 and IPv6.

"egress" (on the Windows Default Switch):
- every IPv6 packet denied, both ways, above every allow;
- DHCP with the Default Switch's DHCP server only (-DhcpServer, the host's address on
  "vEthernet (Default Switch)"): out UDP to port 67 of the broadcast address and of the
  server, in UDP from the server's port 67 to port 68 (Codex, 2026-10-17: the minimal
  rules; RFC 2131 sections 4.1 and 4.4). If Windows changes the Default Switch's prefix
  (it can, after a restart), the rules are set again with the new server;
- DNS, TCP and UDP 53, to 1.1.1.1 and 9.9.9.9 only, stateful;
- every IPv4 special-purpose range of the IANA registry, and each -LanPrefix (prefixes of
  the maintainer's LAN that are not RFC 1918), denied out;
- TCP 80 and 443 out to any other IPv4 address, stateful;
- everything else denied both ways.
Larger weights apply first, and the first entry that applies decides
(https://learn.microsoft.com/en-us/powershell/module/hyper-v/add-vmnetworkadapterextendedacl,
read 2026-10-17). The weights are unique per adapter.
IANA IPv4 special-purpose registry:
https://www.iana.org/assignments/iana-ipv4-special-registry/ (read 2026-10-17).
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][ValidatePattern('^\d{1,3}(\.\d{1,3}){3}$')][string]$DhcpServer,
    [ValidatePattern('^\d{1,3}(\.\d{1,3}){3}/\d{1,2}$')][string[]]$LanPrefix = @(),
    [switch]$Apply
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2.0
$VmName = 'refute-proxy'

function Rule($Direction, $Action, $Remote, $Weight, $Protocol = '', $LocalPort = '', $RemotePort = '', [bool]$Stateful = $false) {
    return [ordered]@{ Direction = $Direction; Action = $Action; RemoteIPAddress = $Remote; Protocol = $Protocol; LocalPort = $LocalPort; RemotePort = $RemotePort; Weight = $Weight; Stateful = $Stateful }
}

$inner = @(
    (Rule 'Inbound' 'Allow' '10.231.71.2' 100 'TCP' '3128' '' $true),
    (Rule 'Inbound' 'Allow' '10.231.71.1' 99 'TCP' '22' '' $true),
    (Rule 'Inbound' 'Deny' 'ANY' 2),
    (Rule 'Outbound' 'Deny' 'ANY' 1)
)

$special = @('0.0.0.0/8', '10.0.0.0/8', '100.64.0.0/10', '127.0.0.0/8', '169.254.0.0/16', '172.16.0.0/12',
    '192.0.0.0/24', '192.0.2.0/24', '192.31.196.0/24', '192.52.193.0/24', '192.88.99.0/24', '192.168.0.0/16',
    '192.175.48.0/24', '198.18.0.0/15', '198.51.100.0/24', '203.0.113.0/24', '224.0.0.0/4', '240.0.0.0/4') + $LanPrefix
$egress = New-Object System.Collections.Generic.List[object]
$egress.Add((Rule 'Inbound' 'Deny' '::/0' 301))
$egress.Add((Rule 'Outbound' 'Deny' '::/0' 300))
$egress.Add((Rule 'Outbound' 'Allow' '255.255.255.255' 290 'UDP' '68' '67'))
$egress.Add((Rule 'Outbound' 'Allow' $DhcpServer 289 'UDP' '68' '67'))
$egress.Add((Rule 'Inbound' 'Allow' $DhcpServer 288 'UDP' '68' '67'))
$w = 280
foreach ($resolver in '1.1.1.1', '9.9.9.9') {
    foreach ($proto in 'UDP', 'TCP') { $egress.Add((Rule 'Outbound' 'Allow' $resolver $w $proto '' '53' $true)); $w-- }
}
$w = 200
foreach ($prefix in $special) { $egress.Add((Rule 'Outbound' 'Deny' $prefix $w)); $w-- }
$egress.Add((Rule 'Outbound' 'Allow' '0.0.0.0/0' 100 'TCP' '' '80' $true))
$egress.Add((Rule 'Outbound' 'Allow' '0.0.0.0/0' 99 'TCP' '' '443' $true))
$egress.Add((Rule 'Inbound' 'Deny' 'ANY' 2))
$egress.Add((Rule 'Outbound' 'Deny' 'ANY' 1))
$weights = @($inner | ForEach-Object { $_.Weight }), @($egress | ForEach-Object { $_.Weight })
foreach ($list in $weights) { if (@($list | Sort-Object -Unique).Count -ne @($list).Count) { throw 'two entries of one adapter share a weight' } }

foreach ($pair in @(@{ Name = 'inner'; Rules = $inner }, @{ Name = 'egress'; Rules = $egress.ToArray() })) {
    Write-Output "Adapter $($pair.Name):"
    foreach ($r in $pair.Rules) {
        Write-Output ('  {0,-8} {1,-5} {2,-18} {3,-4} local {4,-5} remote {5,-5} weight {6,3} stateful {7}' -f $r.Direction, $r.Action, $r.RemoteIPAddress, $r.Protocol, $r.LocalPort, $r.RemotePort, $r.Weight, $r.Stateful)
    }
}
if (-not $Apply) { Write-Output 'Preview only. Run with -Apply (as Administrator, the proxy VM off).'; exit 0 }

$vm = Get-VM -Name $VmName
if ($vm.State -ne 'Off') { throw "the proxy VM is $($vm.State); stop it first" }
foreach ($pair in @(@{ Name = 'inner'; Rules = $inner }, @{ Name = 'egress'; Rules = $egress.ToArray() })) {
    $adapter = @(Get-VMNetworkAdapter -VM $vm | Where-Object { $_.Name -ceq $pair.Name })
    if ($adapter.Count -ne 1) { throw "expected one adapter named $($pair.Name)" }
    Get-VMNetworkAdapterExtendedAcl -VMNetworkAdapter $adapter[0] | Remove-VMNetworkAdapterExtendedAcl
    foreach ($r in $pair.Rules) {
        $add = @{ VMNetworkAdapter = $adapter[0]; Direction = $r.Direction; Action = $r.Action; RemoteIPAddress = $r.RemoteIPAddress; Weight = $r.Weight; Stateful = $r.Stateful }
        if ($r.Protocol) { $add.Protocol = $r.Protocol }
        if ($r.LocalPort) { $add.LocalPort = $r.LocalPort }
        if ($r.RemotePort) { $add.RemotePort = $r.RemotePort }
        Add-VMNetworkAdapterExtendedAcl @add | Out-Null
    }
    $read = @(Get-VMNetworkAdapterExtendedAcl -VMNetworkAdapter $adapter[0])
    Write-Output "Adapter $($pair.Name): $($read.Count) entries read back (expected $(@($pair.Rules).Count))"
    $read | Sort-Object Direction, Weight -Descending | Format-Table Direction, Action, RemoteIPAddress, Protocol, LocalPort, RemotePort, Weight, Stateful -AutoSize | Out-String -Width 200
    # every field as the host spells it, one JSON line per entry: the first observation of
    # the read-back form, which the module's comparison (ConvertTo-RefuteAclRule) relies on
    foreach ($e in $read) {
        $fields = [ordered]@{}
        foreach ($n in 'Direction', 'Action', 'LocalIPAddress', 'RemoteIPAddress', 'Protocol', 'LocalPort', 'RemotePort', 'Weight', 'Stateful', 'IsolationID', 'IdleSessionTimeout') {
            $fields[$n] = $(if ($e.PSObject.Properties.Name -contains $n) { [string]$e.$n } else { '<absent>' })
        }
        Write-Output ("  " + (New-Object psobject -Property $fields | ConvertTo-Json -Compress))
    }
}
