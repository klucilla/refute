# Consensus record: v0.5.9 Ephemeris entry (exploratory prototype)

Every answer and attachment here is stored unchanged, with its SHA-256. Codex's answers carry the
model, the effort and the Codex CLI version.

## The origin of the phase

The maintainer's decision of 2026-11-23 (received at 19:28 local, #218, comment 7115813315),
item 0.
- **The proposal.** With the maintainer's approval, the maintainer's adviser launched a new,
  read-only Claude Fable 5.2 session on `4a704f0f`. It used 350,977 tokens, outside Codex's lines.
  It proposed a full v0.5.9: battery version 5 in `src/`, part A on 108 TOIs, and a claim under a
  lock on 600 PCs. The plan is in Brazilian Portuguese and is stored as it is, like v0.5.8's
  attachments. Its recounts are its own, and exploratory.
- **The review.** One Codex round reviewed that design in conversation `v059plan` (thread
  `01a20a4f-3ec2-7cb2-8a0a-5990041bd6d7`). It returned `REFUTED`, with 7 blocking items, and proposed
  a smaller alternative.
- **The decision.** By the rule of the most conservative option, the maintainer opened v0.5.9 as an
  **exploratory prototype**: [the plan](../v0.5.9-plan.md).

The three files are those of `.cache/v059/plan-review/`, copied unchanged. Each SHA-256 was checked
against its source before the commit. The plan's SHA-256 is also the one the Codex prompt cites.

| File | What it is | SHA-256 |
|---|---|---|
| [fable-plan.md](fable-plan.md) | The Fable 5.2 session's plan (Portuguese) | `dc5756a4169cebe47441e6dea75122f90670727bfe59615536eef5985fc71386` |
| [codex-prompt.md](codex-prompt.md) | The prompt of Codex's round | `5e2b501ce27cd6cd8d75c0fc1a3782b779a07423c0a514a1304477d1aa503415` |
| [codex-answer.md](codex-answer.md) | Codex's answer: **OVERALL: REFUTED**, 7 blocking items | `06f2ee531d04c52b184b3687be4a8f0ece8eb78fa2d5289807fb071797e432d2` |

- **The round:** Codex CLI 0.167.0-alpha.3.2 (`codex_affinity.ps1 -VersionOnly`), model
  gpt-6.2-sol, effort high.
- **Its tokens:** 1,576,727 input (1,436,032 cached) and 13,921 output, so **154,616** review
  tokens.

**What the answer settled, as the decision took it:**
- **Blocking items 1 to 3** (the execution path, the fixed evaluation with the probe grid, the
  centroid's numerical failures) are handled at prototype level by the phase's script.
- **Blocking items 4 to 7** (the paired claim, the thresholds and power, the freeze and the lock,
  the process and sampling gaps) go to the version-5 specification draft, a deliverable of the
  phase.
- **The fact table's row on the v0.5.8 report** (12 lower SNRs) was checked against the committed
  records and gave correction 2:
  [docs/reports/v0.5.8-report-correction-2-2026-11-23.md](../../reports/v0.5.8-report-correction-2-2026-11-23.md).
