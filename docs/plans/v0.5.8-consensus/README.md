# Consensus record: v0.5.8 Output stability

Every answer and attachment here is stored unchanged, with its SHA-256. Codex's answers carry the
model, the effort and the Codex CLI version.

## The independent recommendation (the phase's basis)

The maintainer's decision of 2026-11-23 (received at 13:27 local, #218, comment 7107165120), item
0. It is one read-only session of Claude Fable 5.2, launched by the maintainer's adviser with the
maintainer's approval, on `4b57f7c`. It used 188,722 tokens, outside Codex's lines. It is written
in Brazilian Portuguese, as asked. Its recounts are exploratory and were not reviewed by Codex.

The file is the maintainer's attachment, stored unchanged. Its SHA-256 was checked against the
attachment before the commit.

| File | SHA-256 |
|---|---|
| [independent-recommendation.md](independent-recommendation.md) | `2f7c89d71b4a701d3304f5d7493f7bbe16945a10a2394771e680e47a2e02018d` |

## The CI timing margin (item 6), one round

The maintainer's decision, item 6: investigate whether the v0.5.4 timing test's failures come from the CI runner or from the v0.5.7 tests. Only if they come from the runner, give margin to the wall-time limit, with the evidence on #59 and one Codex round.
- **The evidence:** [ci-margin-evidence.md](ci-margin-evidence.md):
  - the job times before and after;
  - the order of the tests in the `rest` shard;
  - the rerun that passed with the same code.
- **The change:** `MAX_SHARD = 10.0` in `tests/test_v054_budgeted_v3.py`, a harness limit, not a scientific one.

The round ran in conversation `v058ci` (thread `01a20943-bf1f-7de0-b5e6-a5531a75f789`). Codex CLI 0.167.0-alpha.3.2, model gpt-6.2-sol, effort high. The answer is stored unchanged.

| Round | File | Verdicts | SHA-256 |
|---|---|---|---|
| 1 | [ci-margin-round-1-answer.md](ci-margin-round-1-answer.md) | cause SURVIVED (the runner); change SURVIVED; what the test proves WEAKENED; no blocking item; **OVERALL: WEAKENED** | `f3bbc4832f0afc8339c295ff2dee38a68ac12a680b87cad21d716a9d6b6c2ab5` |

The round used 851,331 input tokens (764,928 cached) and 8,238 output tokens: **94,641** review tokens.

**Applied** (the conservative option): the deterministic interruption case now runs at both shard limits, 1 s and `MAX_SHARD`. The v3 projection is the same exact value at each, so a partial leak of the crash charge would show. 15 tests pass (JUnit).