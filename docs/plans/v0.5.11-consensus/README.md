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

## Step 0: the two rounds on the specification (2026-11-24 and 25)

These rounds ran after the phase opened (#218, comment 7146858167), on the same thread. They
were stored by the metered unit `store-round`, with each SHA-256 checked on the copy.

| File | Bytes | SHA-256 |
|---|---|---|
| [step0-r1-codex-prompt.md](step0-r1-codex-prompt.md) | 3,540 | `133dfb862b1b3ae9872817cf7ffc4d7f12702426ed8cd7acfeb7b283639244a9` |
| [step0-r1-codex-answer.md](step0-r1-codex-answer.md) | 9,979 | `f0c35998277219a0e38006a9d09cbd2f07da5a65e4e6a57f0201d8af14c2dcf6` |
| [step0-r2-codex-prompt.md](step0-r2-codex-prompt.md) | 3,241 | `5fc0bbb6e188e5e1c518412da55ab211d2714536f9aa7711f9622f0979c8ffae` |
| [step0-r2-codex-answer.md](step0-r2-codex-answer.md) | 5,932 | `6c3e5c1b1a87107b5c68f7338c56c6c7f8afd8a7c7a93727959aa2d973dac8d4` |

- **Codex:** CLI 0.167.0-alpha.3.2, gpt-6.2-sol, effort high, thread
  `01a20fa7-804c-7150-aac0-6182fb57221b`.
- **Round 1: `REFUTED`,** with 5 blocking items, on `d0d2ba1`. Tokens, the real sum of its
  events: 5,176,274 input (4,929,792 cached) and 26,315 output, so **272,797**.
- **Round 2: `WEAKENED`,** with 3 blocking items, on `f2e977c`. Tokens: 6,790,500 input
  (6,503,424 cached) and 31,776 output, so **318,852**.
- **No third round.** Every blocking item of round 2 was applied in Codex's own wording, so the
  specification was frozen. The charter allowed up to three rounds.
- **Thread total so far:** 141,197 + 194,054 + 272,797 + 318,852 = **926,900** review tokens.

**What was done with each blocking item:**

| Round, item | What | Where |
|---|---|---|
| 1.1 | F1 by OE_box alone; the rest report-only | spec, section 4 |
| 1.2 | Frozen numerical choices; versions, hashes and literal equations | spec, section 5; the sources record |
| 1.3 | The handoff, the `entry` field, A5's entry points | spec, sections 1 to 3 |
| 1.4 | The recount's interpretation; the Markdown omission | spec, section 4; errata entry 1 |
| 1.5 | The launcher's accounting | `tools/launch_v2.py` (`f2e977c`); `meter-gaps.json`; errata entry 2 |
| 2.1 | An executable pre-source check (a test-only reference evaluator) | spec, sections 4 and 8, in Codex's wording |
| 2.2 | Report-only coverage; the grid bound; null flags | spec, sections 5 and 6, in Codex's wording |
| 2.3 | A meter that fails closed | `tools/launch_v3.py` (`ab828ce`) |

**The frozen specification:** `docs/plans/v0.5.11-spec.md` at commit `ab828ce`, SHA-256
`d498a82ada2e31a5b47768d58d6af2e19af0a3c5e35364693f04886068612f15`.

## Step 2: the three rounds on the src/ diff (2026-11-25)

These rounds ran on the same thread, on the working-tree diff before any `src/` commit (charter,
step 2). The files were stored unchanged by the metered unit `store-round` (launch_v6).

| File | Bytes | SHA-256 |
|---|---|---|
| [step2-r1-codex-prompt.md](step2-r1-codex-prompt.md) | 2,907 | `4855f2bf10776d7261c1241b411c2c3e252188d20e82a0088de4dfc50a3f1796` |
| [step2-r1-codex-answer.md](step2-r1-codex-answer.md) | 6,963 | `6ce947e5f7e4cc96a8d765cbbe6af834c7508723d5c297230263f6316d7fb9f9` |
| [step2-r2-codex-prompt.md](step2-r2-codex-prompt.md) | 3,020 | `4b07045dad14da208263bb88452c2604dc9d2edce976f4b988f01698ea8a6634` |
| [step2-r2-codex-answer.md](step2-r2-codex-answer.md) | 5,457 | `b2dfb00781643be86f4083701eaac5e3a2fd0cbcf26ec67f6667d32d1c233f18` |
| [step2-r3-codex-prompt.md](step2-r3-codex-prompt.md) | 2,159 | `217cd8db7e19533fd9ba286f5b59845e40be12587b5793f409dcaa6bfed509e4` |
| [step2-r3-codex-answer.md](step2-r3-codex-answer.md) | 2,477 | `b8b12c157323a944ab6b076db5364e34ebe274157bbbce17173fa3f567d576ce` |

The tokens are the real sum of each round's events:

| Round | Verdict | Blocking items | Input (cached) | Output | Tokens |
|---|---|---|---|---|---|
| 1 | `REFUTED` | 4 | 10,884,102 (10,544,512) | 41,937 | **381,527** |
| 2 | `WEAKENED` | 3 | 13,002,796 (12,629,120) | 48,454 | **422,130** |
| 3 | `SURVIVED` | none in the diff | 15,668,115 (15,273,216) | 53,167 | **448,066** |

- **Round 1:**
  1. contain numerical failures;
  2. refuse an authored `entry: null` for versions 1 to 4;
  3. attach the screen in `conclude_analysis` and serialize it only for version 5;
  4. the frozen availability and coverage rules.
- **Round 2:**
  1. the frozen input predicate with weights on a common scale, and index checks;
  2. a missing flattened curve;
  3. 64-bit transfer counters in the launcher (`tools/launch_v6.py`).
- **Round 3:** the reviewed diff may be committed once the approved repetition of the tests unit
  passes on it. It also notes that the ledger's `netstat` description is inherited and should
  name the source per version.
- **The reviewed diff** is
  [../../validation/v0.5.11/step2/src-change.diff](../../validation/v0.5.11/step2/src-change.diff):
  `git diff HEAD -- src tests` at `168a36f`, SHA-256
  `35102b10296f31d8d1cf80038295632bb8888588c0e3a42e81b22741221a7546`.
- **The thread's total over 7 rounds:** 141,197 + 194,054 + 272,797 + 318,852 + 381,527 + 422,130
  + 448,066 = **2,178,623** review tokens.

## A deviation: the weights adjustment after round 3 (2026-11-25)

By the maintainer's decision received on 2026-11-25 at 00:04 local (#218, comment 7151559282),
items 1 and 2.
- **Why there was an adjustment.** The approved tests unit on the reviewed diff (`35102b10…`)
  failed one of the 22 expected IDs: a relative difference of about 1.5e-9 against the reference
  evaluator, at OE_box ≈ 9.4e-4 (errata entry 8).
  - Option (A) was chosen. `screen_d5._weights` uses the unscaled 1/σ² whenever every weight of
    the valid set is finite and positive, and the common scale only when they cannot be
    represented.
  - The frozen step-1 test does not change.
- **The deviation.**
  - There is no fourth Codex round on the diff: the rule limits the rounds to three.
  - The first `src/` commit therefore carries round 3's `SURVIVED` on the diff `35102b10…`,
    plus this adjustment, which no Codex round has reviewed.
- **The adjustment's own diff:**
  [../../validation/v0.5.11/step2/weights-adjustment.diff](../../validation/v0.5.11/step2/weights-adjustment.diff),
  SHA-256 `04b3f048e1d47e19e61d1969fa677521f6e638d473967573f18716d66428bd57`, 1,403 bytes.
  - It is `git diff` of `screen_d5.py` between the reviewed content (staged) and the adjusted
    file.
  - The full adjusted diff is
    [../../validation/v0.5.11/step2/src-change-adjusted.diff](../../validation/v0.5.11/step2/src-change-adjusted.diff),
    SHA-256 `c24bc496a3afdc7d5d402dbbb1f1058adc4190271bde4d570aad677a139c6ba4`.
- **Its obligations:** it must be in Codex's review of all the phase's commits, before the gate,
  and in the independent gate. Its proof is the tests unit on the adjusted diff.
