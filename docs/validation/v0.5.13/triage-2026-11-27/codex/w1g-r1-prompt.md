# Codex review, one round: the VM decommissioning checklist (block W, item W1(g)3)

You are a read-only reviewer. You must not edit any file and must not run anything that writes or
changes the machine; do not run any Hyper-V, WinRM, firewall or service command. Do not open
`K:\Meu Drive\Pessoal\Segurança`.

## Context

The maintainer decided (W1(g), #218 comment 7229841832) that the Refute VM is decommissioned. The
agent archives first, without administrator rights; then it posts on #135 a removal checklist that
only the maintainer runs, as Administrator. The checklist has one command per line, a preview
before each removal (`-WhatIf` or a listing), and a check after each line. An earlier version
(2026-11-20) was reviewed by you then. Your findings of that day are in
`C:\Projetos\refute\docs\plans\maintenance-2026-11-20-consensus\maint-round-1-answer.md`,
section "5 — WEAKENED". That version is archived at
`K:\Meu Drive\Pessoal\Projetos\refute\cache-archive-2026-11-24b\maint1120\vm-decommission-commands.md`.

## Files to read

- **The checklist to post:** `C:\Projetos\refute\.cache\v0513\w\c135.md`. The placeholders
  `MANIFEST_SHA`, `COMMIT_SHA` and `CODEX_LINE` are filled before posting.
- **The archive's record:** `C:\Projetos\refute\docs\validation\v0.5.13\vm-archive\summary.json`
  and `manifest.tsv`, made by `C:\Projetos\refute\docs\validation\v0.5.13\tools\vm_archive.py`.
- **What the endpoint's registration created and how it is reverted:**
  `C:\Projetos\refute\scripts\vm\README.md`, `C:\ProgramData\RefuteVm\Log\registration-evidence.json`
  and the configuration `C:\Projetos\refute\scripts\vm\RefuteVm\RefuteVm.Config.psd1`.
- **The proxy VM and its ACLs:** `C:\Projetos\refute\scripts\vm\admin\Set-RefuteProxyAcls.ps1`, and
  `C:\Projetos\refute\docs\validation\v0.3\wp6-results\`.
- **The operation log** (the host values before the endpoint changed them):
  `C:\ProgramData\RefuteVm\Log\operations.jsonl`.

## Questions

1. **Completeness:** does the checklist remove everything the project created on the host, and only
   that? Consider the VMs and their disks, the media copies, the switch, the host paths, the
   endpoint, the listeners, the firewall rule, the module, and the data folders. Is anything the
   project created missing? This includes the proxy VM's own items: port ACLs, any NAT, host
   addresses, a scheduled task, a local account. Does any line touch what the project did not
   create?
2. **Order and safety:**
   - Is every removal preceded by a preview that would show a wrong target?
   - Is the order safe (archive before deletion; both VMs Off before removal; the switch's
     exclusivity checked; the firewall rule after WinRM stops; part D only after A5)?
   - Are your four corrections of 2026-11-20 applied?
3. **Each command:** does each one do what its check says on Windows PowerShell 5.1 with the
   Hyper-V module? For example: `Stop-VM` on an already stopped VM; `-WhatIf` support on each
   cmdlet used; `Remove-WSManInstance`; the quoting of B2c on one line. Name any line that would
   fail or mislead, with the exact correction.
4. **The archive:** is the archive step adequate? Consider its handling of unreadable sources, the
   exclusion of the private key and keyring, and the manifest. Is A5's condition enough to protect
   part D?
5. **Privacy in a public post:** does the text expose a user name, a host name, an address or a
   profile path?

## Answer format

- One verdict: `SURVIVED`, `WEAKENED` or `REFUTED`.
- Then the findings, numbered, each with the line (for example B3), the evidence and the exact
  correction.
- Short; no preamble.
