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

## WP5: issue #212 and row 5.2 after the v0.1 re-execution

After row 5.2 (b) stopped at v0.1 (not reproduced; `docs/validation/v0.5.1/wp5/README.md`), two
questions went to Codex on 2026-11-07: whether #212 (BLS peaks that differ between machines)
affects a v0.5.1 criterion, and Claude's reading of row 5.2 with a proposal for the maintainer
([wp5-reexec-answer.md](wp5-reexec-answer.md), SHA-256
`f381989d7ac92794bddc8bd09bd452ef32b91f024c6ab3f82e9679109a9762cb`).

- #212: `WEAKENED`. No criterion is shown to fail, but whether a dossier's reproduction is
  promised only in its recorded environment is not specified; and row 5.4's rehearsal, which runs
  in CI on four platforms, should assert the candidate, the verdict and the test statuses, not the
  search diagnostics.
- Row 5.2: `REFUTED` for Claude's reading. The cause of the v0.1 result (defaults of commit
  `deaa4eb`, v0.2) is supported, but row 5.2 does require the recorded claims' outputs, so (a)
  and the resolved claim hashes do not meet it; the v0.1 result combines the changed defaults with
  inputs fetched today (TIC records, pixel files), so it is "not reproduced under the fixed rule
  with current-code inputs"; and the script's predicate leaves out the byte identity that row 5.2
  names. Codex recommends running v0.2, v0.4 and v0.5 under the approved procedure and reporting
  each. Claude accepts every objection; the stop stays, because the maintainer's condition stops
  the re-executions at the first one not reproduced, so the decision is his.

## Amendment 7: row 5.2 and the v0.1 claims

The maintainer approved amendment 7 on 2026-11-07 (plan, "Amendment 7"); Codex reviewed its text
in three rounds, the first also classifying the v0.2 re-execution (question B) and assessing issue
#213 (question C):

| Round | File | Verdict | SHA-256 |
|---|---|---|---|
| 1 | [amendment7-round-1-answer.md](amendment7-round-1-answer.md) | A `WEAKENED`; B `SURVIVED`; C `WEAKENED` | `0920d923f75f1717d45db167e054d5e3e3a4adaeb578648d5074253d26d8aefd` |
| 2 | [amendment7-round-2-answer.md](amendment7-round-2-answer.md) | `WEAKENED` (one minor objection) | `eff815917b9b194e349c33a30678aa43f005671991c9544d21945e10e2405555` |
| 3 | [amendment7-round-3-answer.md](amendment7-round-3-answer.md) | `WEAKENED` (wording only) | `7c861975c635a1b150965d4fb7349b33e5f8cef51dbd3e7eff92194306a91642` |

Every objection was applied (the exception and the reported `check-dossier` result in row 5.2;
"locked tag, following its `REPRODUCE.md` procedure"; the amendment's opening in the past tense;
the overview and row 5.2 naming the v0.1 dossier); no disagreement remains. Question B: the v0.2
result is not byte-identical, its 13 code differences are a pre-existing default reinterpretation
(from v0.2.1), not a v0.5.1 change, and the stop applies. Question C: #213 now separates the v0.2
defaults that can change a status from the one that only adds bytes, and limits the v0.4 and v0.5
finding to what was checked.

## Amendment 8: row 5.2's two comparisons

The maintainer decided amendment 8 on 2026-11-07 (plan, "Amendment 8"); Codex reviewed its text
and the implementation of comparison (a) (`docs/validation/v0.5.1/wp5/reproduce_dossiers.py`,
steps `baseline` and `compare`) before it ran. Round 1 also answered the maintainer's question for
#213 (question B: an estimate, from the recorded outputs only, of the published v0.2 dossiers whose
verdict the later defaults would change).

| Round | File | Verdict | SHA-256 |
|---|---|---|---|
| 1 | [amendment8-round-1-answer.md](amendment8-round-1-answer.md) | A `WEAKENED` (7 objections); B an estimate | `abb0dd16edeb9d016d39e181a5707bdb0919ebb3377906c70085f13451215708` |
| 2 | [amendment8-round-2-answer.md](amendment8-round-2-answer.md) | `WEAKENED` (2 objections) | `553a1a127deb090f02dd1dabad23067bf6028627198287dbb81b19f44c3eeb23` |
| 3 | [amendment8-round-3-answer.md](amendment8-round-3-answer.md) | `SURVIVED` | `f59e03c62b224fab11945aefb6454a6318a6d173df59851d382b54eaad9b3aaa` |

Every objection was applied (plan, amendment 8, items 6 and 7). The estimate for #213: 3 of the 20
v0.2 calibration dossiers would change verdict (TIC-158561566 and TIC-317507345 by
`same_photometry_catalogs`, TIC-48506505 by the train-validity rule), 14 would not, 3 cannot be
told from the record; with the observation that TIC-194736418, one of the three, was re-run and
kept its verdict, round 2 accepts 3 changed, 15 unchanged (one observed), 2 undecidable
(TIC-118327550, TIC-315755496).

## WP5 row 5.4: the packaging rehearsal

Claude's concrete design (the `calib051` package with what the plan fixes before the protocol;
the selection walks, draws and protocol steps after the protocol, rehearsed again before the
freeze; the rehearsal in a temporary repository with the CLI path) went to Codex before code on
2026-11-07: `SURVIVED`, no objection
([wp5-row-5-4-design-answer.md](wp5-row-5-4-design-answer.md), SHA-256
`a1036eeb5e34005f0ffcda4c67feccce4a44996168258ebed3626e3695f64399`). Its two implementation
conditions are kept: the synthetic substitution only at the network boundary (the production
adapter reads the cache through its manifest; the claim is validated, its attachments resolved),
and across platforms only the candidate, the verdict and the test statuses (#212).

## Round 5: the end-of-round review

Codex's review of every commit of round 5 (`911c9a5..9ce92a7`: WP5 rows 5.1 to 5.4, the
re-executions and their records, amendments 7 and 8), 2026-11-07: `SURVIVED`, no objection
([round-5-end-review.md](round-5-end-review.md), SHA-256
`4cd3d3cfe49593204ac55d0b0586d8f862a7c85717d9baffe14435653a3994d3`).

## `duration_excess`: the measurement after A0 revision 2 (a proposal for the maintainer)

The acceptance section of `duration_excess` defines `sigma_T` on "A0's shifted ephemerides", which
A0's revision 2 removed, and requires the maintainer's decision on a proposal agreed with Codex
before any code. Claude's proposal went through three Codex rounds on 2026-11-07; every objection
was applied, no disagreement remains, and the text goes to the maintainer
([duration-sigma-proposal.md](duration-sigma-proposal.md), SHA-256
`a953c974075909222a21242137ded156b3071f7054ffbdf1f2dcbe73c524f42a`):

| Round | File | Verdict | SHA-256 |
|---|---|---|---|
| 1 | [duration-sigma-round-1-answer.md](duration-sigma-round-1-answer.md) | `WEAKENED` (7 objections) | `9d421ba1ed761b32b3a15f2ba97323568af35f8d656d6c4a1ee4d43c705a8dbe` |
| 2 | [duration-sigma-round-2-answer.md](duration-sigma-round-2-answer.md) | `WEAKENED` (3 objections) | `8864f9a1d7a6ff42b4c96c84a0bb0cfb4e55c39bba492ffe8df5b787d7e0dfe6` |
| 3 | [duration-sigma-round-3-answer.md](duration-sigma-round-3-answer.md) | `WEAKENED` (1 objection, applied after it) | `a570a7fd48a3e83d9c1ac998a4f0e02c620888a1f0bcf98b05c92e1b3ff10dd9` |

Round 3's objection (D.1's denominator) is applied with a rule marked as Claude's choice for the
maintainer to confirm (at least 380 of 400 usable pulls per noise model, else NOT DECIDABLE).

## The D1 route search (amendment 10, item 3)

Codex reviewed the search plan and its results, 2026-11-07
(`docs/validation/v0.5.1/feasibility/README.md`, "The D1 route search"):

| Round | File | Verdict | SHA-256 |
|---|---|---|---|
| 1 | [d1-routes-round-1-answer.md](d1-routes-round-1-answer.md) | `WEAKENED` (4 objections) | `156b0bab6697c25b687769ed716fc4f61c3c0ff94fba54c186b78fb8f32d2b50` |
| 2 | [d1-routes-round-2-answer.md](d1-routes-round-2-answer.md) | `WEAKENED` (5 objections, wording and caution) | `f7be5c9592964382e9bb5f4542730f985b260522837b9dd4e1c2f12b95c78b4c` |

Every objection was applied (thresholds exploratory; a covariance-scored statistic; the joint
radius and mass decomposition; routes unavailable on C1 recorded; the oracle as a proxy forecast;
per-group flag fractions; the grazing tail unexplained; the cost overrun recorded). Both agree: no
new decisive test in v0.5.1. They differ on one point, for the maintainer: Codex would keep the
geometry consistency as a non-fatal diagnostic pending calibration; Claude would record it only,
since a new diagnostic needs the maintainer's approval.

**A disagreement resolved by the maintainer (2026-11-07).** Codex's argument: keep the transit-
geometry consistency as a weakened, non-fatal diagnostic in v0.5.1 pending its calibration and
tail work, so that its evidence accumulates. Claude's argument: record it only; it moves no
target in this round, its thresholds are uncalibrated, and a new diagnostic outside the plan needs
the maintainer's approval. **The maintainer's decision:** recorded only, neither decisive nor
diagnostic, because it moves no target and its unexplained tail (about 30 % of the grazing PG
planets flagged in white noise) could mislead a reader of a dossier (plan, amendment 10, item 7;
#215).
