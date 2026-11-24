# v0.5.11 consensus record

## The draft charter and its review (2026-11-24)

Stored by the maintainer's decision received at 19:33 local (#218, comment 7146372481), item 0.
The four files below are stored **unchanged**, copied byte for byte from
`.cache/v0511/charter-review/`. Each SHA-256 was checked on the copy against the original. The
folder is excluded from line-ending normalization and from the pre-commit hooks, so its bytes stay
as they were.

| File | Bytes | SHA-256 |
|---|---|---|
| [charter-draft.md](charter-draft.md) | 34,690 | `4b6a8f72145735169461434c08827bb4cace6987788d2f08105174f05ff4dfe2` |
| [charter-cover.md](charter-cover.md) | 4,494 | `48e3c1c6df8ba2df4ae38c2ad6a52ff689223b5ce3da8a9ef1346d7b97220bbf` |
| [codex-prompt.md](codex-prompt.md) | 3,903 | `2ed0f2934e71c54fd72272077265a842351bcd574e4dc26a363f2b297d16abf5` |
| [codex-answer.md](codex-answer.md) | 12,767 | `73acd9545fedd9f10c1764b0d69923c0f6c79da4cf5328a99308e28b676239d4` |

**Origin.**
- **The draft and its cover** were written by a new, read-only Claude Fable 5.2 session on
  `main` at `411173ba`. The maintainer's adviser launched it, with the maintainer's approval.
  - It used 437,998 tokens. That figure is the maintainer's; this record did not recount it.
  - `charter-draft.md` is the draft charter of battery version 5, in English.
  - `charter-cover.md` is its cover for the adviser, **in Portuguese, kept as it is**.
- **Codex** reviewed the draft in one round, on a new thread, reading `main` at `602d14ed`
  (whose `src/` equals `411173ba`'s).
  - It ran read-only through `.cache/v04/tools/codex_affinity.ps1`, on processors 8 to 31.
  - **Codex CLI** 0.167.0-alpha.3.2 (`codex_affinity.ps1 -VersionOnly`).
  - **Model and effort:** gpt-6.2-sol, effort high. They are read from the Codex configuration
    in force when this record was written; the event file does not name them.
  - **Thread:** `01a20fa7-804c-7150-aac0-6182fb57221b`.
  - **Its tokens, the real sum of the events** (one `turn.completed`): 1,522,957 input (1,393,024
    cached) and 11,264 output, so **141,197** review tokens, input not cached plus output.
- **Verdict: `REFUTED` for approval as drafted,** with six blocking items. Codex recommended
  splitting the phase.

**What followed** (the same decision, items 1 to 3):
- **The split,** the most conservative option, recorded:
  - [v0.5.11](../v0.5.11-charter.md) keeps the specification, the synthetic tests and the `src/`
    change, with the gate.
  - [v0.5.12](../v0.5.12-proposal.md) is a proposal only.
- **The blocking items:** 1, 2 (its step-0 part), 4, 5 and 6 are quoted in the charter in
  Codex's own wording, where they fit v0.5.11. Item 3 and the pools go to the v0.5.12 proposal.
- **One Codex round on the charter,** resuming this thread, before the maintainer's approval. It
  is recorded below.

## The round on the v0.5.11 charter (2026-11-24)

By the same decision, item 3. It resumed the draft review's thread, and both files are stored
unchanged.

| File | Bytes | SHA-256 |
|---|---|---|
| [round2-codex-prompt.md](round2-codex-prompt.md) | 3,346 | `08969cfac5a1a5b9c7d95fe5c746b143b83c7d37261b7b091332f03dfd13e9fa` |
| [round2-codex-answer.md](round2-codex-answer.md) | 7,061 | `95bcb5cd0f02462b85a364337481833487549605c3392ca489bb1eeb1242b757` |

- **What it reviewed:** the charter as written before this round (SHA-256
  `9ca4f5048ea9b7f8ed785fc64fe99fa939d5d36c1111c0988a43998544cb5c99`) and the proposal (SHA-256
  `d0612d17792ee6532fa136b7b24d907a126b7cb0b16e71e1aed52b3301b35341`), uncommitted in the
  working tree, on `main` at `602d14ed`.
- **Codex:** the same CLI, model, effort and wrapper as round 1, on thread
  `01a20fa7-804c-7150-aac0-6182fb57221b`.
- **Its tokens, the real sum of the events** (one `turn.completed`): 2,795,734 input (2,618,752
  cached) and 18,072 output, so **194,054** review tokens.
- **Both rounds together:** 141,197 + 194,054 = **335,251** review tokens.
- **Verdict: `WEAKENED`,** with four blocking items. A second round was conditional on a new
  `REFUTED`, so none was run.

**What was done with each blocking item.** Each is applied in Codex's own wording, quoted in the
file named.

| # | Item | Where |
|---|---|---|
| 1 | A nonempty core, and limits on report-only execution | charter, sections 2.2 and 3 (step 0), and exit criteria 1 and 4 |
| 2 | Tests first, and evidence bound to the gated code | charter, section 3 (steps 1 and 2), section 7, and exit criteria 2, 3, 4 and 7 |
| 3 | The carried rules applied to every local unit, and caps enforced in flight | charter, sections 5 and 6, and exit criterion 6 |
| 4 | The safeguards deferred to v0.5.12 | proposal, "Safeguards the future charter must keep" |

**The non-blocking caps finding** is applied in section 6 of the charter. The warm tag
environments come first, any cold sync or full local suite is preflighted, and targeted local
tests come before full CI.
