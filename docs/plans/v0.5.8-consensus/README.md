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
## The design round of stage 1 (one round)

The decision, item 3: one Codex round on the design before stage 1 runs. It reviewed `stability_run.py`, `stability_report.py`, `stage1-set.json` and `tests/v058` in the working tree, uncommitted, with no stage-1 result. It ran in conversation `v058design` (thread `01a20946-8fae-7620-9213-17bc995453fc`). Codex CLI 0.167.0-alpha.3.2, model gpt-6.2-sol, effort high. The answer is stored unchanged.

| Round | File | Verdicts | SHA-256 |
|---|---|---|---|
| 1 | [design-round-1-answer.md](design-round-1-answer.md) | 1 REFUTED, 2 SURVIVED, 3 REFUTED, 4 REFUTED, 5 REFUTED, 6 SURVIVED; five blocking items; **OVERALL: REFUTED** | `db85d190ae00397c513a3327b5a3e6dcb6e81ce006b6bcf4551ca6e2d53ba7d5` |

The round used 1,234,791 input tokens (1,150,592 cached) and 12,957 output tokens: **97,156** review tokens.

**Applied as Codex wrote them** (one round, so there is no second round; the run follows the decision's order):
1. **Disk and fingerprints:** disk accounting now reads `.cache/v058`, and the fingerprints are v0.5.8's own.
2. **The shifted second seed is removed.** It changes the mode, so by the decision it does not run.
3. **The report:**
   - door 2 uses decimal arithmetic with inclusive bounds (the 0.92 against 0.90 cases);
   - door 3 uses a strict decimal comparison and tells a missing SNR from zero;
   - the doors require exactly one record per key;
   - flips are labelled partial until the set is complete;
   - an empty `same` panel is "no data".
4. **Caps during the work:** a download reservation per target in flight (1.25 times its v0.5.6 bytes, at least 1 GB) within 65 GB. The set downloaded 52.8 GB in v0.5.6, and its largest target 1.98 GB, so the 5 GB margin covers one file overrun.
5. **Resume and cleanup:**
   - an OS-held lock;
   - atomic writes with unique temporary names;
   - provenance defaults to `unknown` with a reason;
   - `clean` also deletes light curves of the set left without a manifest, logged with their SHA-256.

**Not fully applied, and stated:** CPU and the deadline govern admission, not the work already running. A running target finishes. The CPU estimate is about 4 CPU-h against the cap of 8.