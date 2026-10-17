# WP6 phase 2: design of the VM's network (proposal, 2026-10-17, nothing run)

A design proposal for the maintainer's decision. **Nothing here was run, and nothing here
authorizes a step or changes an acceptance criterion.** The change of W6.5 proposed in
section 8, and the changes of V2 and V4 that section 9 shows to be needed, go into
`wp6-acceptance.md` only after the maintainer's OK. Facts about Hyper-V, Ubuntu, netplan
and Squid come from the sources of section 10, read on 2026-10-17. Where no source settles a
point, the text says it is a hypothesis to be observed on the host.

For each point the document gives the options, Claude's recommendation and Codex's. Codex
gave its recommendations independently (a read-only session that was shown the options but
not Claude's choices, 2026-10-17), before this document was written, and then reviewed the
document; where it does not agree with a sentence, the text says so.

**Context.** Phase 1 is the VM with no network ([after-operation-16.md](after-operation-16.md)).
Phase 2 is everything that needs a network path: the host-side ACLs, the egress allowlist,
SSH from the host, Docker and most acceptance tests (`wp6-acceptance.md` V2 to V9, V11,
V12, V22). The plan (`docs/plans/v0.3-plan.md` section 6.1) requires blocks to the Windows
host, the LAN and private or special ranges, enforced by ACLs on the VM's adapter port, and
build egress only through a forwarding proxy with an allowlist.

## 0. Decisions for the maintainer (summary)

| # | Decision | Claude | Codex | When |
|---|---|---|---|---|
| N1 | The guest's first network configuration | static, in the seed's `network` section, before operation 13 | the same | **before operation 13** (`ImportSeedIso`); operations 5 to 12 do not depend on it |
| N2 | How the revised seed replaces the current one | same name, after the current seed is archived and removed from `.cache` | keep the current seed; a new name, with `SeedIsoName` changed in the installed configuration | before operation 13 |
| N3 | Switch type | a dedicated internal switch, no NAT on it | the same | before phase 2 |
| N4 | Address plan | IPv4 /29 (host, VM, proxy), no gateway, no DNS; no automatic IPv6 configuration in the guest, and IPv6 denied at the port | the same | with N1 |
| N5 | Where the proxy runs | a second small VM (Squid), two adapters, no forwarding | the same | before phase 2 |
| N6 | ACL kind | extended ACLs only; no automatic fallback to the basic ones | the same | after the check on the host (section 5.3) |
| N7 | Network profiles of the VM | `build` (SSH from the host, proxy), `run` (disconnected), `pull` (SSH from the host only) | the same three profiles | before the new operations |
| N8 | Who creates the switch, the host's address, the NAT and the proxy VM | the maintainer, as Administrator, with reviewed scripts | the same | before phase 2 |
| N9 | Change of W6.5 | the text of section 8 | agrees that W6.5 must change; not yet with the whole text (N12 and section 8) | before the new operations |
| N10 | V2 and V4 without a gateway | a change of V2 and V4 is needed; the controls of section 9 are proposals | the same need; the controls of section 9 are additional, not a replacement of the LAN machine | before the V2 and V4 tests |
| N11 | The proxy's DNS resolvers | two public resolvers by address, chosen by the maintainer | not discussed | with N5 |
| N12 | Granularity of the ACL changes | one call sets a whole profile, only while the adapter is disconnected | one approved rule per call | with N9 |

## 1. Switch type (N3)

**Options:**

- **(a) a dedicated internal switch, with no NAT on it.** An internal switch "connects to a
  network that can be used only by the virtual machines running on the host that has the
  virtual switch, and between the host and the virtual machines" (Microsoft, section 10).
- **(b) a private switch**: the same without the host ("doesn't provide networking between
  the host and the virtual machines").
- **(c) the Default Switch** (the NAT switch Windows creates).
- **(d) an external switch**: "connects to a wired, physical network". The plan excludes it
  unless the maintainer decides otherwise.

**Claude: (a).** The host needs a path to the guest for SSH (V11), so (b) would need
another administration path (for example a jump through the proxy VM). (c) is shared with
whatever else uses it and is outside the reviewed configuration. The absence of NAT alone
does not make the switch a dead end: the guest also has no gateway (section 2), the proxy
VM does not forward or bridge (section 4), and **whether the host forwards between its
interfaces is to be checked on the host** (read only) before the first connection. **Risk:**
an internal switch also connects the host; the isolation from the host comes from the port
ACLs, not from the switch type.

**Codex: (a)**, for the same reasons, with the same risk: "the isolation depends on the
ACLs, not on the type of switch"; and the absence of a route depends on the routes and on
the absence of forwarding or a bridge, not on the absence of NAT.

## 2. Address plan (N4)

**Options:** (a) static IPv4 in a little-used RFC 1918 /29, no gateway, no automatic IPv6
configuration in the guest and every IPv6 packet denied at the port; (b) DHCP from a server
on the VM's network; (c) IPv6 configured as well.

**Claude: (a).** A /29 with three fixed addresses: the host's virtual adapter, the Refute VM
and the proxy's inner adapter. The prefix is chosen by the maintainer **after a read-only
check that it overlaps no network of the host** (LAN, VPN, Docker Desktop, WSL, the Default
Switch); the check's result is recorded as "no overlap", without the host's addresses. The
guest has no gateway and no DNS server: the proxy is reached by address, and the proxy
resolves the names. In the guest, netplan's `link-local: []` (which disables "IPv6
link-local addresses ... as well as IPv4 link-local addresses"), `accept-ra: false` and no
`dhcp6`. DHCP (b) would add a service to the network and an address that can change; IPv6
(c) adds a second family of rules to test with nothing gained.

**Codex: (a)**, with a precision both adopt: these netplan settings stop automatic
configuration but **do not disable the IPv6 stack**; the barrier is the denial of IPv6 at
the port, and the tests must not mistake "no address or route in the guest" for "blocked
outside the guest". **Risk** (both): confusing the absence of a route with a block.

## 3. The guest's first network configuration (N1, N2)

The seed built on 2026-10-15 has `network: ethernets: {}`, so connecting the adapter would
give the guest no address. The autoinstall `network` section, in netplan format, "is
applied during installation as well as in the installed system" (autoinstall reference,
section 10).

**Options:** (a) rebuild the seed **before operation 13** with the static configuration of
section 2 in its `network` section; (b) a second seed after the installation, with a new
instance-id (not confirmed by a source: the autoinstall reference does not say whether
cloud-init's network configuration stays enabled in the installed system; to observe);
(c) Hyper-V's key/value exchange (needs a daemon in the guest); (d) a console login (the
seed gives no password).

**Claude: (a).** It changes nothing in the module: the seed's hash is passed to
`ImportSeedIso` by `-MediaSha256`, not fixed in the configuration. The adapter stays
disconnected during the whole installation (operation 9, `DisconnectNetwork`, and the
checks of every later operation); a static address on a disconnected adapter gives no
path. The interface would be matched by its kernel driver (`match: driver:`, supported
"only with networkd", the default renderer), so that its name does not matter. **That the
driver is `hv_netvsc` in this installer is a hypothesis**, to be confirmed before the seed
is built (for example from the installer's documentation or a log of an earlier step), not
assumed. Whether the installer waits for the network at boot with a static address and no
carrier is **to observe** at operation 16. **Risk:** an interface matched wrongly leaves the
guest with no usable SSH after the installation; what to do then is the maintainer's
decision, outside this design.

**Codex: (a)**, and: "do not import the current seed while this choice is pending";
operations 5 to 12 do not depend on it.

**How the revised seed replaces the current one (N2).** `New-RefuteSeedIso.ps1` refuses an
existing destination, and `ImportSeedIso` copies `MediaSource\SeedIsoName`
(`refute-vm-seed.iso`).

- **Claude:** keep the name, so the installed configuration does not change. The current
  seed ISO and its content folder in `.cache\vm\media` are regenerable; under the project's
  folder hygiene they are archived to the Drive with a checked manifest (their hash
  `476754b8…60f9` stays recorded in [operations-roadmap.md](operations-roadmap.md)), then
  removed by their literal paths, and the new seed is built under the same name.
- **Codex:** keep the current seed as it is, build the revision under its own name, and
  change `SeedIsoName` in the installed configuration (an Administrator step with
  `Update-RefuteVmConfig.ps1`); the hash still enters by `-MediaSha256`. Codex does not
  recommend the removal in Claude's option (its review rules exclude proposing deletions),
  and treats its own option as a preference, not a technical need.

Either way the template change is a reviewed PR, and the new hash is recorded in
`operations-roadmap.md` before operation 13.

## 4. Where the allowlist proxy runs (N5, N11)

**Options:**

- **(a) a second small VM** (Ubuntu Server with Squid), one adapter on the Refute VM's
  internal switch and one on an egress network, with no bridge and no IP forwarding between
  them, and ACLs on both ports;
- **(b) a process on the Windows host**, listening only on the host's address on the
  internal switch;
- **(c) a container on the host's Docker Desktop**;
- **(d) inside the Refute VM**: excluded, since the guest would control it.

**Claude: (a).** The proxy receives requests from a guest that may run hostile code. In (b)
a flaw in the proxy reaches the maintainer's Windows session; in (c) it reaches Docker
Desktop's VM, which is close to the host's files and network. In (a) it reaches a VM that
holds nothing else, whose own ports are filtered. Its egress: a second internal switch with
Windows NAT (`New-NetNat`; "you're limited to one NAT network per host", so the host's
existing NAT networks are checked first, read only), the proxy configured statically. DNS
for the proxy: two public resolvers by address (N11, the maintainer's choice).

**The Squid configuration** is written explicitly, not left to the package's defaults:

- the Squid version is the one of the Ubuntu release installed on the proxy VM, recorded,
  and every directive used is checked against that version's documentation;
- `http_access` rules in order, the first match deciding, with a final `deny all`
  (section 10);
- ports: plain HTTP to port 80 and `CONNECT` to port 443 only;
- destinations: `dstdomain` with the allowlist; for `dstdomain` "a reverse lookup is tried
  if a IP based URL is used and no match is found" (section 10), so requests to a literal IP address
  are denied by an explicit rule before the allowlist, and the lookup option is decided
  with the version check;
- no TLS interception; the access log is kept as the record of build egress.

That a `CONNECT` target is matched as configured is checked by V4's negative cases.

**Codex: (a)**, "with two interfaces, no bridge and no IP forwarding between them"; the
inner interface carries the proxy service only. **Risk** (both): a compromised proxy, or a
tunnel to an allowed destination; a domain allowlist does not inspect what is carried.

**What the allowlist holds** is a separate decision (after-operation-16.md, section 5,
step 4): the package registries and the declared data hosts, plus what the VM itself needs
(Ubuntu's archive, Docker's apt repository), hashed and recorded.

## 5. How the list is applied on the host side (N6, N7, N12)

### 5.1 The Refute VM's port

Extended ACLs (`Add-VMNetworkAdapterExtendedAcl`): "Larger weight values apply first, and
once an ACL entry applies to a packet, other entries are no longer relevant for that
packet"; `-Stateful $True` "applies to a return packet even though that packet has the
opposite direction" (section 10). A proposed list (the weights are illustrative, the order
is what matters):

| Profile | Direction | Rule | Weight |
|---|---|---|---|
| `build`, `pull` | inbound | allow TCP to local port 22 from the host's address, stateful (its replies return) | 100 |
| `build` | outbound | allow TCP to the proxy's address, port 3128, stateful (its replies return) | 90 |
| all | inbound | deny `ANY` (IPv4 and IPv6) | 1 |
| all | outbound | deny `ANY` (IPv4 and IPv6) | 1 |

The guest can then start no connection to the host (only answer SSH), none to the LAN or
any other address, and only one to the proxy in `build`.

**Neighbor discovery.** ARP is not an IP packet, and IPv6 neighbor discovery is ICMPv6; the
sources of section 10 do not say whether extended ACLs filter ARP. A guest can still send
ARP and neighbor messages on the switch (for example to claim another address), which can
affect how the host or the proxy resolve their neighbors. **This is a security question
open for the implementation PR**: what Hyper-V offers against it on this host (port
protections of the network adapter) is to be sourced and tested there, not assumed here.

### 5.2 The profiles (N7)

**Claude:** three profiles, each a fixed list in the reviewed configuration:

- **`build`**: SSH from the host and the proxy. The repository's build and the declared
  inputs are fetched in this profile.
- **`run`**: the adapter disconnected (plan 6.1, V6); no ACL is needed while there is no
  link.
- **`pull`**: SSH from the host only, after the run, to copy the results; the proxy is not
  reachable, so code left running in the guest cannot reach an allowed destination during
  the pull.

**From `build` to `pull`:** the source does not say that disconnecting and reconnecting the
adapter ends the stateful sessions the ACLs track. The change of profile therefore needs
**evidence**: after it, a connection to the proxy opened in `build` and kept open no longer
carries data (a test of the implementation PR).

**Codex:** the same three profiles ("build", "run", "collection"), and: the observed state
and the plan must hold the adapter's and the switch's identity, the complete ACL list with
weights and options, in the preconditions and in the check after the call. **Risk:** merely
loosening today's refusal, so that operations run with an unknown or changed policy.

### 5.3 Extended or basic ACLs (N6)

`wp6-acceptance.md` note A: the extended ACL pages are published for Windows Server;
whether the cmdlet works under Hyper-V on Windows 11 is verified on the machine first.

- **Claude:** extended only. The basic ACLs (`Add-VMNetworkAdapterAcl`) filter by address,
  without ports or sessions ("the longest match rule decides"); allowing the host's address
  for SSH would let the guest reach every service of the host on that address. If the
  extended ACLs do not work on the host, the design goes back to the maintainer.
- **Codex:** the same: "I do not recommend an automatic fallback to the basic ACL."

The check on the host (a step for the maintainer, as Administrator, before any
connection): the cmdlet exists, an entry can be added and read back with
`Get-VMNetworkAdapterExtendedAcl`, and then V2 shows that it blocks.

### 5.4 Granularity of the ACL changes (N12)

- **Claude:** one call sets a whole profile, **only while the adapter is disconnected**, and
  reads it back; a partially applied list therefore never carries traffic. If the call
  fails midway, the adapter stays disconnected, the next simulation shows the partial list,
  and connecting is refused until the port's list equals a profile.
- **Codex:** one approved rule per call, closer to W6.5's "one administrative action per
  call"; it does not yet agree with treating a whole policy as one action.

### 5.5 The proxy VM's ports

A complete, versioned list belongs to the implementation PR; its shape:

- **Inner adapter:** inbound TCP 3128 from the Refute VM's address, stateful; inbound TCP 22
  from the host's address, stateful (its administration); deny the rest, IPv4 and IPv6.
- **Egress adapter:**
  - deny, at the highest weights, every special-purpose range of the IANA registries (IPv4
    and IPv6), the host's own addresses, and **every prefix of the maintainer's LAN**,
    including any that is not RFC 1918 (the LAN prefixes are recorded on the host, not
    published);
  - allow outbound TCP 80 and 443 to any other **IPv4** address (`0.0.0.0/0`, never `ANY`),
    stateful (the replies return);
  - allow outbound TCP and UDP 53 to the two resolvers' IPv4 addresses only, stateful;
  - deny every IPv6 packet (`::/0`) in both directions, at a weight above the allows; an
    egress network set up with an IPv4 prefix only does not replace this rule;
  - deny the rest.

## 6. What changes in the current operations

Today every operation that checks the target VM (those with a required VM state in the
operation table of `RefuteVm.Core.ps1`) refuses a connected adapter, except
`DisconnectNetwork` (`Resolve-RefuteVmTarget`), and `DisconnectNetwork` needs the VM off.
The operations that check no VM, among them the media imports `ImportInstallIso` and
`ImportSeedIso`, check files and hashes only, not the adapter (Codex review of the
package). The observed state holds only each adapter's name and switch name
(`RefuteVm.HyperV.ps1`).

| Item | Today | Proposed |
|---|---|---|
| Observed state and plan | adapter name and switch name | the adapter's stable identity (its Id), the switch's identity (its Id) and type, the number of adapters, and the port's complete extended ACL list (direction, addresses, protocol, ports, weight, stateful), in the preconditions and in the check after each call |
| Target check | any connected adapter is refused | an adapter is accepted connected only to the configured switch (by Id and type), with one adapter only, and with the port's ACLs equal, entry by entry, to the profile in force; anything else is refused |
| `DisconnectNetwork` | VM off | **always available** for the recorded VM's identified adapter, also with the VM running and also when the switch or the ACLs diverge, so that a divergence can be contained; whether Hyper-V disconnects a running VM's adapter without a stop is **to observe** |
| Installation operations that check the VM (attaching media, boot order, base disk, `StartVm` for the installation) | adapter disconnected | unchanged: they keep requiring the adapter disconnected |
| Media imports (`ImportInstallIso`, `ImportSeedIso`) | no adapter check (they act on files, not on the VM) | unchanged; whether they should also require the adapter disconnected is a **new** requirement, for the maintainer to decide, not a current protection |
| Capacity control (W6.2, V12: `SetProcessorMaximum`, `SuspendVm`, `ResumeVm`, `SaveVm`) | adapter disconnected | accepted in `run` (disconnected, as today) and in `build` or `pull` with the profile verified |
| Logging | every simulation, intent, refusal and result | unchanged; the ACL list is part of the plan, so its hash covers it |

The synthetic tests (W6.6) gain one refusal per divergence: another switch, another switch
type, a second adapter, an ACL entry missing, added or with another weight, an IPv6 entry
missing, and a `DisconnectNetwork` that still runs in each of these states.
`tests/test_vm_scripts.py` lists `Connect-VMNetworkAdapter` among the forbidden commands and
allows a fixed list of Hyper-V cmdlets; both lists change with the new operations, in the
same reviewed PR.

## 7. New operations

**In the endpoint** (each simulated, approved and logged, with fixed values from the
protected configuration; no free address, switch or rule as a parameter):

- setting the port's ACLs: one call per profile or one call per rule (N12), only with the
  adapter disconnected, read back after the change;
- `ConnectNetwork`: connects the adapter to the configured switch, only when the port's
  ACLs equal a profile;
- `DisconnectNetwork`: extended as in section 6;
- `-Status`: shows the switch, the profile in force and the ACL list.

**As Administrator, by the maintainer** (Claude writes reviewed scripts with a preview, a
hash of the preview and evidence, like the registration): the internal switch, the host's
address on it, the egress switch and its NAT, the proxy VM (its disk, seed, adapters and
ACLs) and the installation of the new module version (`Update-RefuteVmConfig.ps1` and the
registration). **Claude and Codex agree:** the endpoint stays limited to the Refute VM; the
proxy VM needs its own administrative scope. **Risk** (Codex): turning the network extension
into generic administration of the host, or grouping several administrative actions into one
call.

V10 (a differencing disk per paper) also needs new operations and a change of W6.5 ("No
operation deletes ... a disk"); it is a separate decision and is not part of this proposal.

## 8. Proposed change of W6.5 (N9; not applied)

**Current text** (`wp6-acceptance.md`, section 4a):

> - **W6.5 Operations.** One administrative action per call. A simulation computes the
>   plan (target, the observed preconditions, every change with its value before and
>   after, refusal) and its SHA-256 without changing the managed state; the real call
>   needs that hash, holds an exclusive lock from its observation to its final check,
>   and refuses if the plan changed. Media are copied only through a verified copy
>   (source read without write sharing, hashed while copied, moved into place only if
>   the hash matches, never overwriting). Every simulation, intent, refusal and result is logged.
>   Every operation checks the VM's identity (the VMId recorded at creation, its name,
>   its paths, its disks and media) and refuses any divergence. No operation deletes a
>   VM or a disk, turns a VM off without a guest shutdown, connects a network adapter,
>   enables an integration service or turns Secure Boot off.

**Proposed text** (Claude's; the bracketed sentence depends on N12):

> - **W6.5 Operations.** One administrative action per call. A simulation computes the
>   plan (target, the observed preconditions, every change with its value before and
>   after, refusal) and its SHA-256 without changing the managed state; the real call
>   needs that hash, holds an exclusive lock from its observation to its final check,
>   and refuses if the plan changed. Media are copied only through a verified copy
>   (source read without write sharing, hashed while copied, moved into place only if
>   the hash matches, never overwriting). Every simulation, intent, refusal and result is logged.
>   Every operation checks the VM's identity (the VMId recorded at creation, its name,
>   its paths, its disks and media) and refuses any divergence. **Network (phase 2):** the
>   VM has one network adapter, identified by its Id. It is connected only to the internal
>   switch of the configuration, identified by its Id and type, and only while the port's
>   extended ACLs equal, entry by entry (IPv4 and IPv6, with their weights and stateful
>   flags), one of the reviewed profiles of the configuration (`build`, `pull`). The ACLs
>   are changed only while the adapter is disconnected and are read back after each change
>   [by one call that sets a whole profile | by one call per rule]; a run starts only with
>   the adapter disconnected. Every operation except `DisconnectNetwork` refuses an adapter
>   connected to another switch, a second adapter, or a port whose ACLs differ from the
>   profile in force; `DisconnectNetwork` stays available in every such state. **Exception
>   for validation:** the positive controls of V2 and V4 need a port with fewer ACLs than a
>   profile. That state is set and undone only by the maintainer as Administrator,
>   following a written procedure approved for each test, before any paper code runs;
>   while it lasts the endpoint admits only `-Status` and `DisconnectNetwork`, and the
>   test ends with the adapter disconnected and the port back to a profile, read back. The
>   switches, the host's addresses on them, the NAT and the proxy VM are set up by the
>   maintainer as Administrator, not by the endpoint. No operation deletes a VM or a disk,
>   turns a VM off without a guest shutdown, enables an integration service or turns
>   Secure Boot off.

**What changes:**

- "connects a network adapter" leaves the list of forbidden actions, replaced by the
  conditions under which a connection is allowed;
- the ACL changes become operations, with a granularity still to decide (N12), including
  the behavior when a change fails midway (section 5.4);
- `DisconnectNetwork` stays available whatever the state, for containment;
- a test state with fewer ACLs is an explicit exception: set and undone by the maintainer as
  Administrator under a procedure approved for each test, with only `-Status` and
  `DisconnectNetwork` admitted by the endpoint meanwhile.

Codex agrees that W6.5 must change and that the change needs the maintainer; it does not
yet agree with the whole text (the granularity of N12). The proposal takes effect only with
the maintainer's OK, in its own PR.

## 9. Acceptance tests affected (N10)

These need decisions before the tests run; Codex raised them, and Claude agrees:

- **V2, the LAN's positive control.** With no gateway and no NAT on the Refute VM's switch,
  a LAN machine is unreachable even with the ACLs removed, so the positive control V2
  requires shows nothing about the ACLs. **V2 needs a change**, for the maintainer.
  Claude's proposal, as an **additional** control (Codex: it does not replace the LAN machine
  of the current criterion): for the test only, the host's virtual adapter gets a temporary
  second address in a lab range that overlaps no LAN or VPN prefix of the host, the guest a
  specific route to it, and a listener bound to that address only; with the ACLs removed the
  guest reaches it, with the ACLs applied it does not. The procedure must fix the addresses,
  the routes, the source address the host uses and the listener's interface, so that the
  host's own routing is not disturbed; the temporary address and route are removed after the
  test, and the record shows both states.
- **V4.** The test of a direct connection to the internet that bypasses the proxy fails
  already for lack of a route, so it shows nothing about the ACLs; and V4 requires an allowed
  registry to work through the proxy over IPv6, which the IPv4-only egress cannot give. **V4
  needs a change**, for the maintainer.
- **V11 and V4.** The proxy's outbound path and the SSH replies to the host are different
  rules (section 5.1); the tests distinguish them: a connection started by the guest to the
  host's port 22 fails, while the host's SSH session works.
- **IPv6.** The guest has no IPv6 address in normal use, so there is no IPv6 positive
  control. Claude's proposal: for the test only, the guest enables an IPv6 link-local
  address and the host listens on its own link-local address on the switch, with the
  address, the interface scope, the listener and the host firewall the same in both
  measurements; with the ACLs removed the guest reaches it, with them applied it does not.
  Codex: a useful control, but it covers only link-local, not unique-local or the other
  special ranges, and not V4's IPv6 positive control.

Every test state with fewer protections stays isolated and comes before any paper code
runs.

## 10. Sources (read 2026-10-17)

- Plan for Hyper-V networking in Windows Server (switch types: external "connects to a
  wired, physical network"; internal "can be used only by the virtual machines running on
  the host ... and between the host and the virtual machines"; private "doesn't provide
  networking between the host and the virtual machines"):
  https://learn.microsoft.com/en-us/windows-server/virtualization/hyper-v/plan/plan-hyper-v-networking-in-windows-server
- New-VMSwitch (`-SwitchType` Internal or Private):
  https://learn.microsoft.com/en-us/powershell/module/hyper-v/new-vmswitch
- Add-VMNetworkAdapterExtendedAcl (weights, `-Stateful`, IPv4 and IPv6, `ANY`; the page is
  published for Windows Server):
  https://learn.microsoft.com/en-us/powershell/module/hyper-v/add-vmnetworkadapterextendedacl
- Add-VMNetworkAdapterAcl (address-based, "the longest match rule decides"):
  https://learn.microsoft.com/en-us/powershell/module/hyper-v/add-vmnetworkadapteracl
- Set up a NAT network ("you're limited to one NAT network per host"; the guest is set
  statically):
  https://learn.microsoft.com/en-us/windows-server/virtualization/hyper-v/setup-nat-network
- Autoinstall configuration reference, `network` ("applied during installation as well as
  in the installed system"):
  https://canonical-subiquity.readthedocs-hosted.com/en/latest/reference/autoinstall-reference.html
- Netplan YAML configuration (`link-local`, `accept-ra`, `dhcp6`, `match: driver`):
  https://netplan.readthedocs.io/en/stable/netplan-yaml/
- Squid `http_access` (rules in order, a final `deny all`; the default denies `CONNECT` to
  ports other than SSL) and `acl` (`dstdomain`, and its reverse lookup for an IP based URL):
  https://www.squid-cache.org/Doc/config/http_access/ and
  https://www.squid-cache.org/Doc/config/acl/
- IANA IPv6 special-purpose address registry (as cited in the plan):
  https://www.iana.org/assignments/iana-ipv6-special-registry/
- The project's own: `docs/plans/v0.3-plan.md` sections 6.1 and 7.1,
  [../wp6-acceptance.md](../wp6-acceptance.md), [after-operation-16.md](after-operation-16.md),
  [operations-roadmap.md](operations-roadmap.md), `scripts/vm/README.md`,
  `scripts/vm/RefuteVm/RefuteVm.Core.ps1`, `scripts/vm/RefuteVm/RefuteVm.HyperV.ps1`,
  `scripts/vm/New-RefuteSeedIso.ps1`, `scripts/vm/seed/user-data.template`.
