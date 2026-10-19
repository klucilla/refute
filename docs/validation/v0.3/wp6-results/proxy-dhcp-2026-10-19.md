# The proxy VM without an address, 2026-10-18 to 2026-10-19

A record of an incident of the WP6 network (phase 2) and of the checks after its correction.
No host address, host name or account name is written here.

## What happened

After a restart of Windows on 2026-10-18, the proxy VM `refute-proxy` had no IPv4 address on
its adapter `egress` (`egress0` stayed "carrier (configuring)"), so it could not resolve or
reach any registry, and no build of the Refute VM could run (seen by the operator's read-only
checks during the night; still so at 2026-10-19T03:00Z).

**Cause (found by the maintainer).** The egress ACL allows DHCP with one server only, the
host's address on "vEthernet (Default Switch)" given to `admin/Set-RefuteProxyAcls.ps1
-DhcpServer`. After the restart Windows gave the Default Switch another prefix, so the server
moved and its replies were denied by the ACL.

**Correction (the maintainer, as Administrator, 2026-10-19).** `Stop-VM refute-proxy`;
`Set-RefuteProxyAcls.ps1 -DhcpServer <the new server> -Apply`, read back with every entry
expected on each adapter (inner 4 of 4, egress 31 of 31); `Start-VM refute-proxy`. Before
that, one `sudo -n networkctl renew egress0` on the proxy VM, with no change of
configuration.

## Checks after the correction

The proxy VM, by SSH from the host (read only), 2026-10-19T11:09Z: `egress0` routable, with
an address of the Default Switch's new prefix obtained by DHCP from the new server, its
default route through it; github.com resolved; a direct HTTPS request to github.com answered
200; Squid active.

The Refute VM through the proxy in the profile build (switched through the endpoint, each
operation simulated and then run, the profile read back from the status), 2026-10-19T11:10:35Z:

| Request | Result |
|---|---|
| `https://pypi.org/simple/pip/` through the proxy | 200 |
| `https://example.com/` through the proxy | refused by the proxy: `CONNECT tunnel failed, response 403` |
| `https://pypi.org/` with no proxy | no connection: the name does not resolve |

## Prevention

`scripts/vm/Test-RefuteDefaultSwitch.ps1` (no administrator rights) compares the Default
Switch's address with the one recorded when the ACL was last set, and prints the maintainer's
commands when it changed; the procedure after each restart of Windows is in
[scripts/vm/README.md](../../../../scripts/vm/README.md), "After a restart of Windows".
