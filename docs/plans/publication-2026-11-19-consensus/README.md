# Consensus record: the preparation of 2026-11-16 (publication of 2026-11-19, the advance-rule options, the TOI-7930 scope)

Codex's reviews under the maintainer's decision of 2026-11-16 (#217), items 1f, 2 and 3. Codex ran
read only (sandbox read-only), through `.cache/v04/tools/codex_affinity.ps1` on processors 8 to 31.
Every answer is stored here unchanged, with the model, the effort and the Codex CLI version.
Agents propose; nothing here is a verdict on a claim.

## The advance-rule options page (`docs/plans/advance-rule-options.md`)

Codex's review of the options page for balance and fidelity to the records (the maintainer's decision of 2026-11-16, item 2: up to 3 rounds). Codex CLI 0.167.0-alpha.3.2 answered in Portuguese, and the answers are stored unchanged.

| Round | File | Model, effort | Verdict | SHA-256 |
|---|---|---|---|---|
| 1 | [pub-options-round-1-answer.md](pub-options-round-1-answer.md) | gpt-6.1-sol, high | `WEAKENED` (pause and advance confused; "the only route back"; T3b; the release named as published; an over-general ban on changing rules; eight tilting sentences; C's scientific risk; the single-case variant) | `e82ab3cfd2f5ebdcbac367769eb9316e4696bd997e79a6dc0494a579f89bec05` |
| 2 | [pub-options-round-2-answer.md](pub-options-round-2-answer.md) | gpt-6.1-sol, high | `SURVIVED` (one editorial precision, applied) | `5fe9aa68be775ad617fa91cb303d944ad4b3f9f8b97579d35b6c9e379aabc311` |

The tokens are cumulative over the conversation `pub-options`:

- round 1: 290,714 input (228,224 cached) and 4,897 output;
- round 2: 553,691 input (478,976 cached) and 7,057 output;

The conversation counts **81,772** review tokens (the last round's uncached input plus output).

Applied as Codex wrote them:
- The rule conditions the advance, not the end of the pause.
- The pause record's items are evidence for reconsidering, never the only route and never an authorization.
- T3b is stated as passed in v0.5, with a further sample short by 9.
- Option A's public text refers to the release's drafts.
- The scientific rules, which the roadmap protects, are distinguished from the advance rule as a governance rule.
- The eight sentences that tilted towards an option were removed or rewritten.
- C carries B's scientific risk and the lower evidentiary bar of its records.
- The single-case variant names any exception as a question for the maintainer.
- After round 2, "the advance no longer waits on them" became "B replaces the rule's requirement ... the advance does not depend on that evidence".

## The TOI-7930 check of future sectors (`docs/plans/toi-7930-sector-check.md`)

Codex's review of the TOI-7930 page (the maintainer's decision of 2026-11-16, item 3). Round 1 reviewed the page under its first name, `toi-7930-prediction-scope.md`. Codex CLI 0.167.0-alpha.3.2 answered in Portuguese, and the answers are stored unchanged.

| Round | File | Model, effort | Verdict | SHA-256 |
|---|---|---|---|---|
| 1 | [pub-toi-round-1-answer.md](pub-toi-round-1-answer.md) | gpt-6.1-sol, high | `WEAKENED` (the stop of item 3a not respected; the tool's range; the deadlines by mid-time; the power and availability statements) | `320dd52728e7242ebdeaf54c7cf913f2dca5850d13c30ca5f2f53f9079a488ca` |
| 2 | [pub-toi-round-2-answer.md](pub-toi-round-2-answer.md) | gpt-6.1-sol, high | `SURVIVED` (one optional editorial tweak, applied) | `3bca1e455b35eacb46d87e6d3fe7bd1011b10978d625c419a3f9ae02ea142fe6` |

The tokens are cumulative over the conversation `pub-toi`:

- round 1: 626,775 input (553,600 cached) and 8,070 output;
- round 2: 883,265 input (803,456 cached) and 10,304 output;

The conversation counts **90,113** review tokens (the last round's uncached input plus output).

Codex recomputed the mid-times, both uncertainties and the segments, and they agree. The conservative reading of item 3a was applied:
- The page records the check and stops. The evaluation rule, the lock list, the calendar and the price were removed, and the page was renamed, since no scope is written before the maintainer answers.
- The tool's own note on its range (sectors 108 to 121) is quoted, and nothing is excluded for sectors 122 to 134.
- "One of the four segments is public" replaced a fraction of images.
- The release delay is one observed case.
- The power paragraph was removed.
- #25's positive controls are quoted as predictions for known planets.
- The BJD's time scale is stated as an assumption.

## The drafts of the publication of 2026-11-19 and the day's script (`docs/plans/publication-2026-11-19.md`)

Codex's review of the release drafts, the v0.3 drafts, the site's draft and the day's script (the maintainer's decision of 2026-11-16, item 1f: up to 3 rounds). The drafts stay outside `main`, in `.cache/v05/release/` and `.cache/pub1119/`; only the script and the new `sources/` record are committed. Codex CLI 0.167.0-alpha.3.2 answered in Portuguese, and the answers are stored unchanged.

| Round | File | Model, effort | Verdict | SHA-256 |
|---|---|---|---|---|
| 1 | [pub-drafts-round-1-answer.md](pub-drafts-round-1-answer.md) | gpt-6.1-sol, high | `WEAKENED` (the #158 comment announced annexes before they exist; T2c's denominator; missing public links; acknowledgment requests without a `sources/` record; no check for addresses; steps of the script not yet executable) | `530f297ba189beaabed51977561c8a8cb83d4cc64d73da3f836f7a26e5a9a6db` |
| 2 | [pub-drafts-round-2-answer.md](pub-drafts-round-2-answer.md) | gpt-6.1-sol, high | `WEAKENED` (the address check accepted a partial match; the site's sequence; the DOI tool could write one file only; the CI wait returned success on failure or timeout) | `4e3ae91049dd0311d66df2e4c23bdd5dcbf942c572ebe76384f7c4408d2265d3` |
| 3 | [pub-drafts-round-3-answer.md](pub-drafts-round-3-answer.md) | gpt-6.1-sol, high | `WEAKENED` (one correction: the script omitted `approved.site_commit` of the site's approval record) | `c42852fe9526e1b342f554ab9784fa1a9f4b63bbf50ec02a0cbf594a76f78457` |

The tokens are cumulative over the conversation `pub-drafts`:

- round 1: 2,897,601 input (2,753,536 cached) and 13,587 output;
- round 2: 5,157,621 input (4,986,368 cached) and 21,907 output;
- round 3: 6,626,203 input (6,443,136 cached) and 27,386 output;

The conversation counts **210,453** review tokens (the last round's uncached input plus output).

Round 1's first attempt ended after its turn started, with no answer (a Codex CLI execution failure). Its events are kept as `.cache/pub1119/codex/pub-drafts-r1-attempt1-events.jsonl`, and the round was run again unchanged.

Codex confirmed in every round:
- the states match the ROADMAP and the closing records;
- the README's two tables no longer show v0.5 in progress;
- no target is relaxed or declared infeasible;
- the three withheld hashes and the three rehearsed `ANNEX.json` hashes are right;
- the append leaves the record's first 5,644 bytes unchanged and is parsed by `annex_record`;
- the cause analysis agrees with `run.py` at the tested commit;
- `calibration/v0.3/` is unchanged.

Every correction was applied as written:
- The state comment of #158 says only that the period ended; a second comment follows the push.
- T2c is "2 to 0 among the 97 stars outside the three development stars (4 to 0 among all 100)".
- The notes and the Zenodo description link the closings and the pause record.
- `docs/sources/acknowledgments-2026-11-16.md` records every acknowledgment request.
- `address_check.py` matches the allowed forms whole and reads every staged path.
- The [M] go-ahead to annex is its own step.
- The release targets the checked SHA.
- `apply_version_doi.py` validates both files before writing.
- `wait_ci_strict.py` fails on a failed, missing or incomplete run.
- The site's part registers the release before the fetch, commits before the acceptance, and asks for the launch gate's READY before the deploy.

Round 3 was the last. Its one correction was applied: the approval record's `approved.site_commit` is updated and checked. No divergence remained.

## Items 1a and 1b of the decision of 2026-11-16, 21:40 (the 4-of-100 count; the README's closing sentence)

Codex's review of the two corrections to the release drafts asked by the maintainer's decision of 2026-11-16, 21:40 (#217), item 5: one round, up to three if not SURVIVED. Codex CLI 0.167.0-alpha.3.2 answered in Portuguese, and the answers are stored unchanged.

| Round | File | Model, effort | Verdict | SHA-256 |
|---|---|---|---|---|
| 1 | [pub-fix-round-1-answer.md](pub-fix-round-1-answer.md) | gpt-6.1-sol, high | `SURVIVED` | `a289f00ac2c5de57d829020975d6c61f48aa754f4dcbe90a9ead6ba3ff118dba` |

The tokens are cumulative over the conversation `pub-fix`:

- round 1: 266,485 input (220,544 cached) and 2,926 output;

The conversation counts **48,867** review tokens (the last round's uncached input plus output).

The first attempt ended after its turn started, with no answer (a Codex CLI execution failure). Its events are kept as `.cache/pub1119/codex/pub-fix-r1-attempt1-events.jsonl`, and the round was run again unchanged.

Codex confirmed:
- The "4 to 0 among all 100" has a registered source: `calibration/v0.5/runs/c2/report.json`, `originals_all`, identical to the file committed in `a9ec11a`. It counts SURVIVED only, on the original curves, with the same stage verdicts as T2c's "2 to 0 among the 97". The parenthesis stays, as a descriptive count, not a target.
- The README draft's sentence is now the text of `README.md` on main, unchanged.
- The paragraph of `metadata-changes.md` is accurate.

No correction was needed.
