# v0.5.13 charter, amendment 2: review record

The proposal is [../v0.5.13-charter-amendment-2.md](../v0.5.13-charter-amendment-2.md)
(PROPOSED, not approved; the maintainer's decision D1b, #218 comment 7207651312). It is reviewed
by Codex in up to 3 rounds of one conversation, then by a fresh blind review that the
maintainer's adviser proposes.

Labels: `exploratory`, `method_status: not_validated`.

## Revision 3 (current proposal)

[../v0.5.13-charter-amendment-2-rev3.md](../v0.5.13-charter-amendment-2-rev3.md) is written under
the maintainer's decision E1 (#218, comment 7216128796). Its direction:
- no thread pin;
- no synthetic v5 verification in Step 1;
- decision identity as the reproducibility criterion.

What it drops and keeps:
- It removes the pinned worker, the `src/` patches and the `blas-pin` extra. The §12 exception was
  denied (E2).
- Revisions 1 and 2 and their patches below stay as the record.

Codex round 3, the last, returned `NOT_APPROVABLE` with four implementation items, none of which
reopens the direction.
- Their replacement texts are adopted as written in revision 3.
- Item 4 (the survey) is a correction comment on #231.
- **The text revised after round 3 has had no further Codex review.**

## Revisions 1 and 2 (the record)

**State of revision 2: superseded by revision 3.** Codex rounds 1 and 2 returned
`NOT_APPROVABLE`. The patches below are revision 2's, as round 2 reviewed them, and are not part
of revision 3.

## The current package (revision 2): exact patches, not applied

Written by the committed unit `make-patch` (`docs/validation/v0.5.13/tools/make_patch.py`) from
the committed files at `24bf505c41ece20d81705166f84d886e727c4251`; meant to apply at the
repository root (`git apply --check` has not been run). Applying any of them is a stop.

| File | SHA-256 |
| --- | --- |
| [r2-runner.patch](r2-runner.patch) | `10f56ce87d50f0fb5737a6c288cc58c1cfa493ff99038b1a56372f42a48c0a30` |
| [r2-pinned_worker.patch](r2-pinned_worker.patch) | `62b265005ea7685d1f3464a6a1de3f80d80291d820e56e23fc9851f6cd44eb88` |
| [r2-test_runner_blas_pin.patch](r2-test_runner_blas_pin.patch) | `006bfbf96d1537a3b435b73ba33f21406cc274721669f47c3f5ba0417b495dc6` |
| [r2-dependency.patch](r2-dependency.patch) | `03b24d6ffa8ba05d0cc4cc1716c2207c37944483c598dcad34eea3f3a7855386` |

- The dependency patch comes from `uv lock --offline` on a copy of `pyproject.toml` and `uv.lock`
  under `.cache/v0513/d1b2/lockcopy`; it resolved 108 packages and downloaded nothing.
- The proposed files passed `ruff check` and `ruff format --check` (metered units). The tests
  have not been run (amendment, section 4.4).

## Codex rounds

Codex ran read-only, sandbox read-only, through `.cache/v04/tools/codex_affinity.ps1`
(processors 8 to 31), in one conversation, thread `01a21afc-2d5a-7342-97b6-093ea3204ec7`. The
prompts and answers are stored byte for byte by the unit `store-file`.

| Round | Prompt | Answer | Verdict | Tokens (input / cached / output) |
| --- | --- | --- | --- | --- |
| 1 | [round-1-prompt.md](round-1-prompt.md) (`ab316a5e…93e8edb1`) | [round-1-answer.md](round-1-answer.md) (`5b6bbbb6…61dcc5a`) | `NOT_APPROVABLE`, 6 blocking items | 1,244,184 / 1,145,216 / 11,723 |
| 2 | [round-2-prompt.md](round-2-prompt.md) (`e722d18a…badf5689`) | [round-2-answer.md](round-2-answer.md) (`ee6d1e34…b31a0d90`) | `NOT_APPROVABLE`, 5 blocking items | 630,176 / 605,312 / 7,745 |
| 3 (revision 3) | [round-3-prompt.md](round-3-prompt.md) (`0c58d163…1b8d6e9b`) | [round-3-answer.md](round-3-answer.md) (`4c72836a…721e5671`) | `NOT_APPROVABLE`, 4 implementation items | 2,023,068 / 1,853,952 / 9,404 |

A resumed thread reports cumulative usage; each round's own usage is its cumulative figure minus
the previous round's. The total of the three rounds is round 3's cumulative figure: 3,897,428
input (3,604,480 cached) and 28,872 output.

**The package round 1 reviewed** (the first draft's design, kept as reviewed):
[round-1-runner.patch](round-1-runner.patch) (`257b77c87bce99b5527822e09143244410b962ec261f7eccba0665baad11536e`)
and [round-1-test_runner_blas_pin.diff](round-1-test_runner_blas_pin.diff)
(`2667f509859987d883ab365a349e409d179ef107bf33bdb3dfad5a1fb216edb8`). Its patch headers pointed at
`.cache` paths, one of round 1's findings. It is superseded by revision 2.

## How revision 2 answers round 1

| Item | Revision 2 |
| --- | --- |
| 1. Typed-field comparator, bound evidence | Section 3.1 quotes the replacement as written; section 1 the tag sentence. |
| 2. The tolerance's purpose | Section 3.2: the floating-point bound is withdrawn; `1e-6` is an engineering budget, declared post hoc. |
| 3. A complete margin manifest, failing closed | Section 3.3, with the consequence that missing operands need an approved measurement. |
| 4. Fresh interpreter per shard, checked startup | Section 4.1 and the new design of `r2-runner.patch` and `r2-pinned_worker.patch`. |
| 5. Dependency extra and tests | Sections 4.3 (the §12 exception requested) and 4.4; `r2-dependency.patch`; the test patch. |
| 6. Step 1 rule and exit criterion 1 | Section 5, with the sequencing conflict left to the maintainer. |

## Round 2's items in the text, and what remains

| Item | Text | Code |
| --- | --- | --- |
| 1. Bind results to the actual child; keep failure evidence | Section 4.2, quoted | Not revised (defects listed in 4.2) |
| 2. Verified installation; nonempty, bound inventory | Section 4.2, quoted | Not revised |
| 3. Tests through the launched child | Section 4.4, quoted | Not revised |
| 4. v5 entry point, evidence sink, fixture, harness; sequencing | Section 5, quoted | No diff; the maintainer's decision |
| 5. Bind supplemental operands to golden bytes | Section 3.3, quoted; section 5 item 2 | Not applicable |

Round 2's non-blocking items: the dependency diff was found correct as prepared; `1e-6` is now
attributed to the first amendment draft; the patch base commit is recorded above.
