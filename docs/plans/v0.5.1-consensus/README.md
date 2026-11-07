# v0.5.1 scope consensus: Codex's answers

The maintainer delegated, on 2026-11-06, the scope of v0.5.1 Battery corrections to a consensus
between Claude and Codex, within one direction: correct the targets that failed in v0.5 without
losing the ones that passed. Codex ran read-only (sandbox `read-only`, logical processors 8 to 31,
through `.cache/v04/tools/codex_affinity.ps1`) on the drafts of
[../v0.5.1-plan.md](../v0.5.1-plan.md) in three rounds of one conversation on 2026-11-06. Its
answers are kept here unchanged; the prompts stay local because they name a private folder the
session was told not to open.

| Round | Time (UTC) | What Codex reviewed | Verdict | File | SHA-256 |
|---|---|---|---|---|---|
| 1 | 13:15 to 13:24 | the first draft | `WEAKENED` (8 objections) | [round-1-answer.md](round-1-answer.md) | `e2a5d6a02a501a6c85e716c1a000b1d01521bcbb2577aef1462afc27eea501b4` |
| 2 | 13:27 to 13:33 | the plan with the round-1 changes | `WEAKENED` (6 objections) | [round-2-answer.md](round-2-answer.md) | `0eaea60624c2653e36bee63d109442e24162dfc225ca5c994cd690584cad8c7e` |
| 3 | 13:35 to 13:39 | the plan with the round-2 changes | `SURVIVED`; scope adopted | [round-3-answer.md](round-3-answer.md) | `c1de4c984fa16b915fc47663a134ad6333a7786063b2198e9e4a619954f96a39` |

How each objection was handled: the consensus record at the end of the plan. No disagreement
remained, so nothing went to the maintainer.

The numbers of the plan's section 2 come from
[../v0.5.1-wp0/diagnose_v05_records.py](../v0.5.1-wp0/diagnose_v05_records.py) (its output:
[../v0.5.1-wp0/diagnosis.json](../v0.5.1-wp0/diagnosis.json)), run on the v0.5 records, which this
phase uses for development only.

## The acceptance documents

Codex's one review of [../v0.5.1-acceptance.md](../v0.5.1-acceptance.md) and of the plan's
amendment 1 (2026-11-06, 14:14 to 14:20 UTC, a new conversation): `WEAKENED`, 7 objections (2
critical), all applied as the acceptance documents' revision 1 (the one revision before code the
plan's stop rule allows): [acceptance-review-1.md](acceptance-review-1.md) (SHA-256
`67fc49966e5410cdb5c8667afea4629b97f92443f753f552dbf85bd8d1aefe4d`).

Codex's review of the proposed revision 2 of A0 (2026-11-06, a recorded deviation from the plan's
stop rule 1): `WEAKENED`, 3 critical and 1 important objection; it requires the maintainer's
disposition before any A0 code: [acceptance-review-2.md](acceptance-review-2.md) (SHA-256
`0c49b83772b77f8a728277c6d8fe77557347d84f93be5e0a466f8ea43b8597eb`).

## A0, the corrected revision 2 (the maintainer's conditions, amendment 2)

Three rounds in one conversation on 2026-11-06; not adopted (no `SURVIVED`); the remaining
objection goes to the maintainer.

| Round | File | Verdict | SHA-256 |
|---|---|---|---|
| 1 | [a0-round-1-answer.md](a0-round-1-answer.md) | `WEAKENED` | `6b5374b37f34e226d1f1de5c5e9a50f6859a605be3fc3fd8daf99256b5dd4e70` |
| 2 | [a0-round-2-answer.md](a0-round-2-answer.md) | `WEAKENED` | `b480733cd0a3737735a757cdf5ee172b3a7c471caeae1dcf735d4b9e61204a46` |
| 3 | [a0-round-3-answer.md](a0-round-3-answer.md) | `WEAKENED` | `8337c14f2fa07fad9adcdb761cd233b2c544a029ecf6f74a7979ee86c82e76d8` |

## A0 under amendment 3 (the maintainer's decision on the cross-coverage correlation)

Three rounds in one conversation on 2026-11-06; **adopted** with `SURVIVED` in the third.

| Round | File | Verdict | SHA-256 |
|---|---|---|---|
| 1 | [a0-amendment3-round-1-answer.md](a0-amendment3-round-1-answer.md) | `WEAKENED` | `d994e244655e04dcdb45701707ed8cfcb53a8f658dffdc19a301903118964205` |
| 2 | [a0-amendment3-round-2-answer.md](a0-amendment3-round-2-answer.md) | `WEAKENED` | `a8bff73fb2423d99c05717ed223722ae39d213db35021c0d565263d2997ae4a3` |
| 3 | [a0-amendment3-round-3-answer.md](a0-amendment3-round-3-answer.md) | `SURVIVED` | `e4008c6466bbff4761b27b078ea2ee806fe7976049b932316e33c1bbd62efcdd` |

## The duration warning (amendment 3, item 2)

Codex's check of the development measurement and its recommendation (item (d), the same as
Claude's): [duration-recommendation.md](duration-recommendation.md) (SHA-256 `f782e82edf17875f05dbab095512f0056112fa3df7ccc171b60345010b17f9f1`).

## A0 window availability (amendment 5)

Codex's two answers on the finding that A0 kept no window for short periods, both unchanged:
[a0-availability-answer-1.md](a0-availability-answer-1.md) (SHA-256 `ee88efa1c53bb46106e5ceb9ea933a1ddd027ae62c028a0f6cb2ae9c5f6dca4d`) recommended keeping A0's
rule and accepting the loss (it read Claude's option (d) as amendment 4, which is about
`duration_excess`); after the measurement of option (a),
[a0-availability-answer-2.md](a0-availability-answer-2.md) (SHA-256 `64e0b25b51bb9acc2be3bba72487b2b12436a3a4b71e64d46943170b30af6507`) recommended option (a),
with the caveat that a phase-0.5 signal can bias the variance and the correlations in either
direction. The maintainer approved option (a) with a conditional exclusion (amendment 5).

Codex's three rounds on amendment 5's text (the conditional exclusion, A0.8, A0.9, the sabotage):
**adopted** with `SURVIVED` in the third.

| Round | File | Verdict | SHA-256 |
|---|---|---|---|
| 1 | [amendment5-round-1-answer.md](amendment5-round-1-answer.md) | `WEAKENED` | `5920c65bb4de507e372f9b211f9e80960a0d4e4e3edf18749c33ea871abdb526` |
| 2 | [amendment5-round-2-answer.md](amendment5-round-2-answer.md) | `WEAKENED` | `e1b40169fac9e7d2cb913df630bce6eeca708fb2a37eac093939c6a890aae4fa` |
| 3 | [amendment5-round-3-answer.md](amendment5-round-3-answer.md) | `SURVIVED` | `e5e85665791969c877b74806ea31075183d29c92f33566e49e7864e4ecc2ac5a` |

## End-of-round reviews and the WP3 (c) review

Codex's review of WP3 (c)'s revision 1 (cited by the acceptance, WP3 (c)):
[wp3c-review.md](wp3c-review.md) (SHA-256 `8b00804907c1a6537b93ff16b22dabf91b476d5bb3b753052bac6676edbd179c`).

| Round | Commits | File | Verdict | SHA-256 |
|---|---|---|---|---|
| 2 | round 2's commits | [round-2-end-review.md](round-2-end-review.md) | `WEAKENED` | `b916abebf64b6e6c505f564a1da9490df15902d5b31b1076667dfc127bac6040` |
| 3 | 86e0a1d to 2cd5a5f | [round-3-end-review.md](round-3-end-review.md) | `REFUTED` (4 objections) | `7f2989d624253da6f02a2af35da13611ca2e0536224a9f9ec1361ecf41ab68c1` |
| 4 | a188254 to 2f0a48e | [round-4-end-review.md](round-4-end-review.md) | `WEAKENED` (3 objections) | `1fbdc3d65e634baffa79d027e19ae145b2759ad729134eaa6b2ff09c5b51b7f2` |

Round 4's three objections were all applied in the commit that adds its review: amendment 6's
sabotage is checked against row 3a.7's own "must" on three curves, with its preconditions (the
affine sectors meet the cutoffs and are treated as applicable, a rule block detectable on at least
one curve) and the row failing on that block; a version-3 error record carries the condition
`analysis_error` or `data_fetch_failed` (in `verdict.json`, `report.md`, `case.json` and the
tallies), the analyzer receiving the claim's plan; row 4.2 compares bytes with fixtures recorded by
the code before WP4 (6f8d805) for a v0.4 and a v0.5 claim and an error record
(`tests/fixtures/v051_wp4/`, with the script that wrote them).

Round 3's four objections were all applied in the commit that adds its review: A0's per-stratum
`n_eff` uses every available within-segment pair (the 20-pair minimum stays only for the group
rule's correlations); WP3 (d)'s matched amplitude is weighted least squares with the cadence
weights, in the real events and the pseudo-events, and its model error is the inverse root of the
same weighted information; WP3 (d)'s two INCONCLUSIVE messages carry the reason "phase-0.5 windows
excluded: a secondary detected" when the exclusion applies; the shortcut requires all 200
bootstrap replicates of each term.

## WP3 (a): the SAP applicability rule

Codex's review of the WP3 (a) draft code and of Claude's proposal to read the acceptance's "SAP
and PDCSAP identical up to a constant factor" as "an exact affine function" (the synthetic
generator's `SAP = 1 + CROWDSAP x (PDCSAP - 1)`): `WEAKENED`
([wp3a-sap-review.md](wp3a-sap-review.md), SHA-256
`f35626272200b96486517f72771f0d27ccce901643d99ea52df6f9862ff63490`). The affine reading fits the
acceptance's intent but changes its written criterion, so it needs an amendment (the maintainer's
decision); until then the code applies the written rule. Its objection 3 (each sector's own
CROWDSAP in the expected SAP depth and its sensitivity simulation) was applied in the WP3 (a)
commit.

The maintainer approved the affine rule on 2026-11-06 (plan, amendment 6). Codex's three rounds
on the amendment's text: `WEAKENED` in each, every objection applied, no disagreement; no
`SURVIVED`, so the code has not changed and the text went to the maintainer.

| Round | File | Verdict | SHA-256 |
|---|---|---|---|
| 1 | [amendment6-round-1-answer.md](amendment6-round-1-answer.md) | `WEAKENED` | `56607ddfef2267df8e51ee2bd6dfa93c54d1474c8fe8aed5747340038ac5f11c` |
| 2 | [amendment6-round-2-answer.md](amendment6-round-2-answer.md) | `WEAKENED` | `970373f6935d572c4827cf54742abd6c6466952cfc9d559bcd694424cfe0293d` |
| 3 | [amendment6-round-3-answer.md](amendment6-round-3-answer.md) | `WEAKENED` (wording only) | `37b82fbbe9f4b2ff214cf5515856106fc73cc4539e2b92f61b4e2edd0a2ffeda` |
| 4 | [amendment6-round-4-answer.md](amendment6-round-4-answer.md) | `WEAKENED` (wording only) | `de710b1dd977e78f055d2a76a03e4b9276a1c817b71b4896e52f658a76d0a314` |

The maintainer authorized, on 2026-11-07, a fourth round as a confirmation only (plan, amendment
6, item 6), with its outcome fixed in advance: `WEAKENED` for wording only means the correction is
applied and recorded and the code starts with no fifth round. Round 4 found the seven earlier
objections resolved and one wording objection (the registry comment in `power.py`), applied in the
commit that implements the rule; amendment 6 is adopted.

## WP4: the design of the INCONCLUSIVE classes

Claude's design (a version-3-only pass over the test results; the class set by the test, the
engine's coverage and sensitivity refusals, a table of the shared v0.4 and v0.5 functions'
messages, a counted fallback; the verdict's class; the reporting in `verdict.json`, `report.md`
and `case.json`) went to Codex before code, two rounds on 2026-11-07:

| Round | File | Verdict | SHA-256 |
|---|---|---|---|
| 1 | [wp4-design-round-1-answer.md](wp4-design-round-1-answer.md) | `WEAKENED` (4 objections) | `c513be0114afe7c3be40ea79ae0256c2c1b49f51536e131fdde669a3cf8b0090` |
| 2 | [wp4-design-round-2-answer.md](wp4-design-round-2-answer.md) | `SURVIVED` | `9de60237ec8fbbc881a6b2a972ce64f7622a4532a9c6c284c616e829e75e9b70` |

The four objections of round 1, all applied: a test not run at this stage is `not_enough_data`
(source `stage`), never `outside_domain`; the classification runs after the stage deferral, which
builds new results; the verdict's class comes only from its decisive INCONCLUSIVE tests, and a gate
not passed or a missing expected test is recorded apart as a condition; a version-3 record says
`discovery_version` 3.

## WP5: battery version 3 and the packaging rehearsal

Claude's design went to Codex before code, two rounds on 2026-11-07:

| Round | File | Verdict | SHA-256 |
|---|---|---|---|
| 1 | [wp5-design-round-1-answer.md](wp5-design-round-1-answer.md) | `WEAKENED` (3 objections) | `d9f21e13a707545871fbc559dccc65ba79bb52f534c95e6f6f843c8612fe1a55` |
| 2 | [wp5-design-round-2-answer.md](wp5-design-round-2-answer.md) | `SURVIVED` | `8f722b9fd77c658759968ac3b134667b2185dfffb6da6760c21c7e525261a4b6` |

The three objections of round 1, all applied: row 5.1's set is named explicitly (every test of
`V05_DECISIVE` and `V05_DIAGNOSTIC` keeps a role in a version-3 claim); row 5.2 needs the recorded
claims of v0.1 to v0.5 re-executed, not only synthetic fixtures, and that re-execution (with row
5.3's) waits for the maintainer's approval on an issue; the paired chain of the calibration
classifies a version-3 battery's INCONCLUSIVE results (WP4) itself. The rehearsal is a smoke test
(one minimal synthetic path per step), and the C1', C2', C3' sizes are the plan's fixed minimums.
