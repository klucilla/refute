# v0.5.3 consensus record

Codex's answers in round 3 of the correction line (v0.5.3, #217), each stored unchanged with its
model, effort, Codex CLI version and SHA-256. Codex is consulted read only (sandbox read-only,
processors 8 to 31, through `.cache/v04/tools/codex_affinity.ps1`). Its tokens do not count against
the review limit (the maintainer, 2026-11-09). After three rounds of divergence, the option more
conservative against a false conclusion wins, with both arguments recorded.

## The design questions

The maintainer's decision of 2026-11-11 (#217, item 2): the principled argument on both sides of
three design questions, written before stage A's numbers and validated by Codex, deciding nothing
([v0.5.3-design-questions.md](../v0.5.3-design-questions.md)). Codex CLI 0.167.0-alpha.3.2, a new
conversation.

| Round | File | Model, effort | Verdict | SHA-256 |
|---|---|---|---|---|
| 1 | [design-questions-round-1-answer.md](design-questions-round-1-answer.md) | gpt-6.1-sol, high | `WEAKENED` (7 findings) | `e3adb9b4d012ae4c8074b55604e05971fb87062ec91346f5ce34dce094efb6e4` |
| 2 | [design-questions-round-2-answer.md](design-questions-round-2-answer.md) | gpt-6.1-sol, high | `WEAKENED` (7 confirmed applied, 2 new) | `e60e2178a19f1a74f2c45218feac718c7c3226ca41bc308117664d9a793f2f02` |
| 3 | [design-questions-round-3-answer.md](design-questions-round-3-answer.md) | gpt-6.1-sol, high | `SURVIVED` | `1045e6d4a9ac2dcd3aa3ae45218b191c2f3eda750d14a9b90db24a06f1cebc77` |

Tokens: round 1, 445,574 input (372,224 cached) and 4,561 output; round 2, 706,321 (620,288) and
6,458; round 3, 893,027 (802,944) and 7,481. Every finding was applied as Codex wrote it: the
chronology stated as pending until this commit; the monotonicity argument conditioned on an
operational decision, with its counterargument; the background's alternative distinguished from
its FAIL thresholds, its simulation described, the power policy's exceptions (`period_alias` at
0.90, categorical checks), the self-fulfilling risk of a noise-scaled alternative, and the "scale"
argument replaced by an argument that constrains change; the sinusoid's FAIL guards, weights and
Fréchet assumptions; the confirmation sets: none drawn or used, pool metadata examined for T3b.
Round 3: each question keeps a genuine argument for changing, which justifies reconsidering or
deriving a convention, not a particular relaxation.

## The stage A design

The design of stage A ([v0.5.3-stageA-design.md](../v0.5.3-stageA-design.md)), its ledger shim
and item (a)'s script (`docs/validation/v0.5.3/stageA/`), reviewed before any run. Codex CLI
0.167.0-alpha.3.2, a new conversation.

| Round | File | Model, effort | Verdict | SHA-256 |
|---|---|---|---|---|
| 1 | [stageA-design-round-1-answer.md](stageA-design-round-1-answer.md) | gpt-6.1-sol, high | `REFUTED` (10 findings) | `b0eb17f2f041265f00556a1aeaf14989bdde7cc1934f2d258238d406a4d2db0d` |
| 2 | [stageA-design-round-2-answer.md](stageA-design-round-2-answer.md) | gpt-6.1-sol, high | `REFUTED` (10 points) | `a1a0157ede13e9f2ff1d3ab434ac9d927c3646b8be7a78ebd0c5d98b72049475` |
| 3 | [stageA-design-round-3-answer.md](stageA-design-round-3-answer.md) | gpt-6.1-sol, high | `WEAKENED` for item (a) and for the design | `456c554062408673f6e216a1ad045cf03e5e5bf93dad7054fdfb6d4149863f8a` |

Tokens: round 1, 1,432,503 input (1,292,160 cached) and 9,466 output; round 2, 2,603,762
(2,435,456) and 17,116; round 3, 3,604,326 (3,414,272) and 27,278. Every finding was applied as Codex
wrote it: kept retention kept apart from the evidence-qualified PASS, so a warning blocker counts as
recoverable (a warning FAIL gives WEAKENED) and only fatal blockers can be bounded as lost; the
sinusoid's oracle GLS standard error with the flag's power at 1; the background's scatter as an
audit, not a bound; the joint Fisher information for `odd_even` with per-sector level columns and
the contrast `(1, -1, 0, ...)`; unbounded blockers recoverable; sampling uncertainty apart from the
bounds' validity, and T2a's plug-in as a conditional scenario; item (a)'s traces of the group
variance, the empirical events (each dropped event and its reason) and D2's A0 depths, with replays
excluded and any trace failure quarantined; the strict cap, prospective transfers, the token and
day checks before each step, the earlier ledger checked in a `finally`; no child process, and (c3)
on hold until a batch deadline enforced during the run is designed and reviewed. **One finding was
answered rather than applied:** round 3 read `caps.json`'s zero review tokens as an omission of
Codex's tokens; by the maintainer's decision of 2026-11-09 Codex's tokens do not count against the
review limit, so `caps.json` now states that rule and counts independent review sessions only (none
yet).

## Item (b)'s implementation

`docs/validation/v0.5.3/stageA/d2_bounds.py`, reviewed before its run. Codex CLI 0.167.0-alpha.3.2,
a new conversation.

| Round | File | Model, effort | Verdict | SHA-256 |
|---|---|---|---|---|
| 1 | [d2-bounds-round-1-answer.md](d2-bounds-round-1-answer.md) | gpt-6.1-sol, high | `REFUTED` (3 findings) | `1cef8f94ac65dceb47c4f176b278011560826f2cf414d0d187c64b8b9b2825a6` |
| 2 | [d2-bounds-round-2-answer.md](d2-bounds-round-2-answer.md) | gpt-6.1-sol, high | `REFUTED` (3 corrections) | `9f73ba3b0c6eaf0b373226125c5078c0a27ecd4c51f652d499386fd6c03d2707` |
| 3 | [d2-bounds-round-3-answer.md](d2-bounds-round-3-answer.md) | gpt-6.1-sol, high | `SURVIVED` | `bdd5a39094e9f1ee3c372f97ed7e9420fb389c242351140665a2000defd4c5a3` |

Tokens: round 1, 773,957 input (698,240 cached) and 8,439 output; round 2, 1,465,182 (1,364,864)
and 13,663; round 3, 1,998,102 (1,885,184) and 16,387. Applied as Codex wrote them: item (a)'s
refusals read and bound into the fingerprint, an absent or failed (a) diagnosis counted
optimistically; the generator's known multiplicative trend on the odd and even template columns
only; the sinusoid's residual box in normalized coordinates (a fixed-normalizer oracle assumption),
the odd/even columns raw. Codex checked the polarization against a dense covariance (relative error
1.3e-16) and seven counting scenarios.

## Items (c1) and (c2)'s implementation

`docs/validation/v0.5.3/stageA/t2a_bounds.py`, reviewed before its run. Codex CLI
0.167.0-alpha.3.2, a new conversation.

| Round | File | Model, effort | Verdict | SHA-256 |
|---|---|---|---|---|
| 1 | [t2a-bounds-round-1-answer.md](t2a-bounds-round-1-answer.md) | gpt-6.1-sol, high | `REFUTED` (5 corrections) | `1ac509290c1258c22309852eacaed284ca21d027834b9aab7dcd5c112a161faa` |
| 2 | [t2a-bounds-round-2-answer.md](t2a-bounds-round-2-answer.md) | gpt-6.1-sol, high | `SURVIVED` | `1b22edc3b3217126d06c9daf0f2b07a75bfb1db4c24c2af4cf77df264b93fc09` |

Tokens: round 1, 952,471 input (750,080 cached) and 7,556 output; round 2, 1,303,349 (1,091,968)
and 10,201. Round 1 confirmed the method's reading (under the design's rules every blocker of T2a's
51 losses is recoverable, so kept retention's upper bound is 1 on the measured strata, and the
informative outputs are the background audit and conditional scenarios, labelled as not bounds) and
asked for five corrections, applied as written: the background not normalized twice; the odd/even
columns with the host's multiplicative response and a fixed normalizer; the 23-loss background
cohort for the primary summaries, with the per-sector ratio; the qualifications in the output; the
fingerprint's coverage.

## Item (c3)'s controller (cut by the tie-break)

`docs/validation/v0.5.3/stageA/above20.py`, the controller of the sample above 20 sectors, reviewed
before any run. Codex CLI 0.167.0-alpha.3.2, one conversation.

| Round | File | Model, effort | Verdict | SHA-256 |
|---|---|---|---|---|
| 1 | [above20-round-1-answer.md](above20-round-1-answer.md) | gpt-6.1-sol, high | `REFUTED` (10 findings) | `68fd373839ce4cd5b74c5befa629b672550c912f11ee122d035ba63ae688001b` |
| 2 | [above20-round-2-answer.md](above20-round-2-answer.md) | gpt-6.1-sol, high | `REFUTED` (remaining blockers) | `d8fb74942edc1cdcc835d83f60ab6251781858417f8f5f7512c5c6caf157a08e` |
| 3 | [above20-round-3-answer.md](above20-round-3-answer.md) | gpt-6.1-sol, high | `REFUTED` (3 remaining blockers) | `9d4dbfcd4f5b526e365b5b099b51b355747976c7b75f44aa9c2caa7d6c10dae5` |

Tokens: round 1, 962,046 input (872,192 cached) and 9,792 output; round 2, 1,620,974 (1,512,576)
and 17,731; round 3, 2,461,328 (2,330,112) and 23,606. After three rounds of divergence the more
conservative option holds: (c3) does not run, nothing of it was executed, and the stratum above 20
sectors stays bounded both ways (T2a's kept fraction 0.909 to 1.0 under (c2)'s rules). The
controller is kept as written, never run. The tie-break is recorded in the stage A design.

## Item (d)'s implementation

`docs/validation/v0.5.3/stageA/d1_geometry.py`, D1's geometric route, reviewed before its run.
Codex CLI 0.167.0-alpha.3.2, one conversation.

| Round | File | Model, effort | Verdict | SHA-256 |
|---|---|---|---|---|
| 1 | [d1-geometry-round-1-answer.md](d1-geometry-round-1-answer.md) | gpt-6.1-sol, high | do not run yet (5 corrections) | `95c21acc13da4e41f0c60ef6bf6006149a0b9117168cfe073966529d8f3f9aec` |
| 2 | [d1-geometry-round-2-answer.md](d1-geometry-round-2-answer.md) | gpt-6.1-sol, high | do not run yet (checkpoint coverage) | `97856426ec333cf1c2ac19edadeac456809d73aa14eaf47f03acc7a18b32ea43` |
| 3 | [d1-geometry-round-3-answer.md](d1-geometry-round-3-answer.md) | gpt-6.1-sol, high | acceptable to run | `f8bcfec5e02d116a4b9094c396c4686e9199b847762cc6cf50ae071581ea168c` |

Tokens: round 1, 879,042 input (781,952 cached) and 8,662 output; round 2, 1,268,115 (1,154,560)
and 11,576; round 3, 1,840,785 (1,718,400) and 13,514. Applied as Codex wrote them: the cost
revised to about 7.7 CPU-h; the threshold the larger of the P and PG 99.73 % quantiles; the
fingerprint covering both wrappers, the historical route log and the v0.4 claim; the checkpoint's
projection in curves, its shards covering all four families; strict exceedances per family. Round 3
computed an 8.182 CPU-h hard cap from the ledger, above the 7.71 CPU-h estimate.

## Stage A's end-of-round review

Every commit from `7896ba7` to `35c07cb` and the stop report
(`docs/validation/v0.5.3/stageA/README.md`). Codex CLI 0.167.0-alpha.3.2, one conversation.

| Round | File | Model, effort | Verdict | SHA-256 |
|---|---|---|---|---|
| 1 | [stageA-end-round-1-answer.md](stageA-end-round-1-answer.md) | gpt-6.1-sol, high | `WEAKENED` (5 corrections) | `91de8737214bb56373ffd43fbf857f8ef1a74de221ffdab8fe801adedf4b93f9` |
| 2 | [stageA-end-round-2-answer.md](stageA-end-round-2-answer.md) | gpt-6.1-sol, high | `SURVIVED` | `1c0114a6740ce5ef8b1161bdeb92252f66cf3e3baa94bd2e7c30225d5bd94438` |

Tokens: round 1, 2,562,343 input (2,375,936 cached) and 12,728 output; round 2, 3,149,019
(2,945,152) and 13,855. Applied as Codex wrote them: round 3's closing criterion states each
target's frozen rule in its own direction; the fingerprint promise qualified (a change to `src/`
changes the code hash T2a's v0.5.2 fingerprint covers); the A0-only and whole-schedule acceptance
costs told apart; the smoke exception disclosed; planet 1075 excluded from `odd_even`'s 0.97 to 1.0.
Round 1 reconciled every number of the report with its records (7.7830877 CPU-h) and found no
protected file, earlier record or v0.5.2 ledger changed in the range.

**A note on the token figures (2026-11-11).** The Codex CLI's usage at the end of a turn
(`turn.completed`) is cumulative over the conversation (#217, comment 6799452280). The per-round
"Tokens" lines above are the CLI's figures as reported, so a conversation's total is its last round's
figure, not the sum of its rounds. Across stage A's 7 conversations, uncached input plus output
comes to 1.17 M.

## Stage B, B0: the design of D1's gate

The design of B0 ([v0.5.3-stageB0-design.md](../v0.5.3-stageB0-design.md)), the bound's script
and stage B's ledger (`docs/validation/v0.5.3/stageB/`), reviewed before any run. Codex CLI
0.167.0-alpha.3.2, one conversation. From stage B on, Codex's tokens count against the review cap
(the maintainer's rule of 2026-11-11, #217): uncached input plus output, cumulative.

| Round | File | Model, effort | Verdict | SHA-256 |
|---|---|---|---|---|
| 1 | [b0-design-round-1-answer.md](b0-design-round-1-answer.md) | gpt-6.1-sol, high | `WEAKENED` | `96328c1570f0b6ce622682c91fba661e8e94fe90040eb10ec4c152d64b6282e6` |
| 2 | [b0-design-round-2-answer.md](b0-design-round-2-answer.md) | gpt-6.1-sol, high | `WEAKENED` (the charges' room) | `c7fa4348fc3e480ff868536b5db3b0873c6a711c797702091b7282049f794cb0` |
| 3 | [b0-design-round-3-answer.md](b0-design-round-3-answer.md) | gpt-6.1-sol, high | `SURVIVED` | `09778d88a67962e9b5f3427c16ce2c4a9a8b575751b6bff34564a794a77333fd` |

Tokens, cumulative: round 1, 1,237,919 input (1,106,048 cached) and 11,360 output; round 2,
2,123,977 (1,962,240) and 17,451; round 3, 2,705,121 (2,537,472) and 19,234. The conversation
counts **186,883** against B0's cap. Codex answered these three rounds in Portuguese. The
answers are stored unchanged, as the record requires.

Every correction was applied as Codex wrote it. Round 1 made these:

- the depth row and the candidate-size route (LEO-Vetter IV.1);
- the bound kept a diagnostic, with "non-rejection" in place of "survival";
- the per-planet level, the selection and the star's null stated as requirements, not shown;
- the star's known trend applied to the residual;
- D1's second condition stated as outside the bound;
- the outcomes A, B and C reworded, and D added (errors, too few eligible, a non-finite distance);
- the projection over every attempted curve;
- `>=` for the stops;
- the ledger line 149.9, with 0.1 CPU-h outside it for the charges;
- `summarize` checks the caps and charges its own time;
- the design in the fingerprint.

Round 2 made two more: a charge always recorded, with a STOP past the room, and `summarize`
charging its own time in a `finally` after checking that room is left; and `declare` keeping the
allocations after a transfer. Claude's own fix after round 1: the token parser reads each event's
type, because a command output that quoted `turn.completed` had broken it.

## Stage B, B0: the end-of-B0 review

The stop report (`docs/validation/v0.5.3/stageB/README.md`), with the bound's output
(`d1-bound.json`), the ledger and the caps, reviewed before it went to the maintainer. Codex CLI
0.167.0-alpha.3.2, one conversation, answered in Portuguese and stored unchanged.

| Round | File | Model, effort | Verdict | SHA-256 |
|---|---|---|---|---|
| 1 | [b0-end-round-1-answer.md](b0-end-round-1-answer.md) | gpt-6.1-sol, high | `WEAKENED` (2 corrections) | `8da98fb215ae8a87aa4b71ad8d2499559e7f92d7fc286d8e63084c7bd48847a9` |
| 2 | [b0-end-round-2-answer.md](b0-end-round-2-answer.md) | gpt-6.1-sol, high | `SURVIVED` | `97e28605bbfc1c18e3f33efc346f61c896be361f298b8923f2f67545828e8f3c` |

Tokens, cumulative: round 1, 699,907 input (630,784 cached) and 7,391 output; round 2, 990,558
(911,488) and 8,239. The conversation counts **87,309**, so **B0 in all counts 274,192** of its
1.5 M cap (18.3 %). Applied as Codex wrote them: EB1's folded fraction rounded to 0.217; the
assumptions listed in full (the per-planet level over the whole ±3-sigma box; a selection that
leaves the noise along the binary-to-planet difference unchanged; the eligibility approximation).
Round 1 reproduced the fingerprint `cc407aecdd294028` from `b00a78d` and checked the 80 shards, the
800 seeds, 0 errors and the denominator with the 5 generation failures.

## Stage B, B0b: the design of D1's infeasibility test

After B0's stop, the maintainer decided on 2026-11-11 (#217, comment 6804003610) on a
pre-registered infeasibility test of D1 on C1's information. Its design
([v0.5.3-stageB0b-design.md](../v0.5.3-stageB0b-design.md)) and script
(`docs/validation/v0.5.3/stageB/d1_infeasibility.py`), with the ledger's changes, were reviewed
before any B0b measurement. Codex CLI 0.167.0-alpha.3.2, one conversation, answered in
Portuguese and stored unchanged.

| Round | File | Model, effort | Verdict | SHA-256 |
|---|---|---|---|---|
| 1 | [b0b-design-round-1-answer.md](b0b-design-round-1-answer.md) | gpt-6.1-sol, high | `WEAKENED` (2 corrections) | `07e71a23051e8f12643713e0ca11368e8b36338bea166211641ef42670864db0` |
| 2 | [b0b-design-round-2-answer.md](b0b-design-round-2-answer.md) | gpt-6.1-sol, high | `SURVIVED` | `f7d3b69d2f5b4bcf5f59035abfc197e61c4e81bea9c4d92c55e84b3c5a0f6945` |

Tokens, cumulative:

- round 1: 595,997 input (526,592 cached) and 7,580 output;
- round 2: 1,031,542 input (933,888 cached) and 11,918 output.

The conversation counts **109,572**, so B0's total is **383,764** of its 1.5 M cap.

Round 1 found the criterion faithful to the maintainer's example and found no tuning to B0's
figures. It checked the 800 seeds against B0's and found no overlap. It made two corrections to
the ledger, both applied as written:

- One writer at a time. B0b and B1 run in parallel, and a run saves the whole ledger, so writers
  are serialized by an exclusive lock file held for the whole run.
- The part's cap is counted over every attempt, and a run under a new identity is refused.

Round 2 confirmed both.

## Stage B, B0b: the end-of-B0b review

The record [`b0b-record.md`](../../validation/v0.5.3/stageB/b0b-record.md), with the output
(`d1-infeasibility.json`), the ledger and the caps, was reviewed before it was committed. Codex CLI
0.167.0-alpha.3.2 ran one conversation. It answered in Portuguese, and the answers are stored
unchanged.

| Round | File | Model, effort | Verdict | SHA-256 |
|---|---|---|---|---|
| 1 | [b0b-end-round-1-answer.md](b0b-end-round-1-answer.md) | gpt-6.1-sol, high | `WEAKENED` (4 corrections) | `0e56f280fe373204ce937ec67ad8d8f45af11bd23f00f07d2c1cd10d30ee6b2c` |
| 2 | [b0b-end-round-2-answer.md](b0b-end-round-2-answer.md) | gpt-6.1-sol, high | `SURVIVED` | `2175f55ee16545449b47d17dca8c4f37107e0362350f1129e3bd311ac88890ba` |

The tokens are cumulative:

- round 1: 878,707 input (797,312 cached) and 6,899 output;
- round 2: 1,330,063 input (1,232,640 cached) and 8,322 output.

The conversation counts **105,745**, so B0 in all, B0b included, counts **489,509** of its 1.5 M.

Codex's corrections, all applied as written:

- EB2's star-known figures, 12.9 and 0.077;
- the extremely small medians at 0.0027 stated, with the tables' 0.000 marked as rounding;
- the figures at 0.05 named the oracle's optimistic bounds, conditional on B0's assumptions;
- the comparison with B0 reworded as an illustration of the sensitivity to the seed set.

Round 1 recomputed the fingerprint `584a56d8f50283fe` from the files of `98fa3c7`. It also checked
the 80 shards, the 800 seeds against B0's, the 0 errors and the released lock.

## Stage B, B1: the design of the estimators, recalibration and forecast

The design [v0.5.3-stageB1-design.md](../v0.5.3-stageB1-design.md), reviewed before any B1 code.
Codex CLI 0.167.0-alpha.3.2 ran one conversation. It answered in Portuguese, and the answers are
stored unchanged.

| Round | File | Model, effort | Verdict | SHA-256 |
|---|---|---|---|---|
| 1 | [b1-design-round-1-answer.md](b1-design-round-1-answer.md) | gpt-6.1-sol, high | `REFUTED` | `758aaf826b069d4505616961778dbec2e535c63be9c99fb912b120f997a5d114` |
| 2 | [b1-design-round-2-answer.md](b1-design-round-2-answer.md) | gpt-6.1-sol, high | `REFUTED` | `b7d0f64f547b19e991de3266f38d4d0cc1f4b42e3270b558a77eee8ceb1f77ff` |
| 3 | [b1-design-round-3-answer.md](b1-design-round-3-answer.md) | gpt-6.1-sol, high | `WEAKENED` (conservative options named) | `c24407cf08057617b9cfe7a0a6f3256e7dfac8d73e59f365cbc1d00670558983` |

The tokens are cumulative:

- round 1: 2,627,260 input (2,464,640 cached) and 14,842 output;
- round 2: 4,392,117 input (4,184,448 cached) and 34,271 output;
- round 3: 5,756,147 input (5,514,880 cached) and 44,845 output;

The conversation counts **286,112** against stage B's cap.

Each round's corrections are mapped in the design's section 6. Round 3 named a conservative option
for each remaining point, and all were adopted. Round 3 was the last before the tie-break, which
would have chosen the same options. The main changes were these:

- **Round 1:**
  - pooling and the matrix repair in A0's domain replaced by a Cauchy-Schwarz completion;
  - the joint GLS contrast for `odd_even`;
  - an ARMA(1,1) GLS for the sinusoid's residual;
  - a window-local quadratic baseline for the background;
  - T2a measured as a census of 559 injections, because 80 + 80 could never reach a PASS.
- **Round 2:**
  - numerical conditions for every inversion;
  - the state-space treatment of gaps and masks;
  - the protected alternative kept for the background;
  - 450 recalibration curves;
  - the T2a conclusions and the overrun as a stop.
- **Round 3:**
  - availability that never erases a FAIL;
  - intervals as conditional diagnostics;
  - a degenerate bootstrap as UNRESOLVED;
  - a disk quota before every write.

## Stage B, B1.1: the code of the candidate version 5, before the smoke

The code was reviewed against the design before any B1 run:

- `docs/validation/v0.5.3/stageB/battery_b1.py`;
- `b1_forecast.py`;
- `tests/v053/`.

Codex CLI 0.167.0-alpha.3.2 ran one conversation. It answered in Portuguese, and the answers are
stored unchanged.

| Round | File | Model, effort | Verdict | SHA-256 |
|---|---|---|---|---|
| 1 | [b1-code-round-1-answer.md](b1-code-round-1-answer.md) | gpt-6.1-sol, high | `WEAKENED` (4 corrections) | `5994194998d717c0062b3b901cca6d5f59650d98717837a116ab57bd40f0a619` |
| 2 | [b1-code-round-2-answer.md](b1-code-round-2-answer.md) | gpt-6.1-sol, high | `REFUTED` (the smoke's validator) | `5101cebb77096beb26ffc2328a328e1743542f6736479611dfeda372c77abbfc` |
| 3 | [b1-code-round-3-answer.md](b1-code-round-3-answer.md) | gpt-6.1-sol, high | `SURVIVED` | `90b9ad3460175424321a775e2db25516f08852493e8fc8a87b7258d30180e917` |

The tokens are cumulative:

- round 1: 1,491,949 input (1,383,168 cached) and 9,657 output;
- round 2: 2,214,788 input (2,088,576 cached) and 13,836 output;
- round 3: 2,854,191 input (2,714,112 cached) and 16,750 output;

The conversation counts **156,829** against stage B's cap.

Round 1 found no error in the estimators' formulas. It asked for four corrections:

- the smoke validated on its records, not only on the driver's state;
- the record bound counted with the newline, a bound for the driver's other files, and the disk
  checked after the run;
- the rows in the fingerprint;
- a test of real calls through version 4, then version 5, then version 4.

Round 2 found that the new validator would reject the selector's legitimate refusal in
configuration A, and that it still accepted incomplete evidence. Two changes followed:

- the validator became a pure function with exact checks;
- the required counters now respect the structural refusals, with tests of their own (20 tests
  pass).

## Stage B, B1.1: the smoke split (rounds 4 and 5 of the code review)

The maintainer's decision on the smoke's stop (#217, comment 6807681986) split the smoke into three homogeneous parts and added the part above 20 sectors. The change to `b1_forecast.py` was reviewed before the runs, in the conversation of the B1.1 code review. Codex CLI 0.167.0-alpha.3.2 answered in Portuguese, and the answers are stored unchanged.

| Round | File | Model, effort | Verdict | SHA-256 |
|---|---|---|---|---|
| 4 | [b1-code-round-4-answer.md](b1-code-round-4-answer.md) | gpt-6.1-sol, high | `WEAKENED` (the overrun report) | `fd87ae65b3feec2f6a9d94dd10b9d6454246868e56e9518e97f3cdc8c1bc432d` |
| 5 | [b1-code-round-5-answer.md](b1-code-round-5-answer.md) | gpt-6.1-sol, high | `SURVIVED` | `7cfc0cdb37cae0062c8c5875558413d7ca741fcdcd77acc7eba2dfcadbf7e720` |

The tokens are cumulative over the conversation `b1-code`:

- round 4: 4,339,919 input (4,177,920 cached) and 24,022 output;
- round 5: 5,138,051 input (4,968,704 cached) and 27,371 output;

The conversation now counts **196,718** against stage B's cap.

Round 4 found the split correct. It asked for a report of an overrun above 20 sectors, read from the driver's own files, with C above 20 unknown and the stop kept. That report was added with a test, and round 5 confirmed it.

## Stage B, B1.2: the screening code

The screening (`screen`, `screen_summarize` in `b1_forecast.py`) was reviewed before its run. Codex CLI 0.167.0-alpha.3.2 answered in Portuguese, and the answers are stored unchanged.

| Round | File | Model, effort | Verdict | SHA-256 |
|---|---|---|---|---|
| 1 | [b1-screen-round-1-answer.md](b1-screen-round-1-answer.md) | gpt-6.1-sol, high | `REFUTED` | `5552c17fb7c51909ea3d96a6dffbd2ed621f9262f542cff655aaf1aefbad0db4` |
| 2 | [b1-screen-round-2-answer.md](b1-screen-round-2-answer.md) | gpt-6.1-sol, high | `WEAKENED` (2 corrections) | `abf85eeb334ec6ce312102bb0d31e9f43c34acbc8f8f066954e81ac762c5c733` |
| 3 | [b1-screen-round-3-answer.md](b1-screen-round-3-answer.md) | gpt-6.1-sol, high | `WEAKENED` (the conservative option, adopted) | `bff93d441f69c0f91fe36ebf62f08d789740a89cf73073bda7a8b6f000cb02e7` |

The tokens are cumulative over the conversation `b1-screen`:

- round 1: 1,000,618 input (892,288 cached) and 8,627 output;
- round 2: 1,506,504 input (1,379,456 cached) and 12,083 output;
- round 3: 2,255,479 input (2,110,336 cached) and 15,923 output;

The conversation now counts **161,066** against stage B's cap.

The corrections were these:

- **Round 1:**
  - the eligible set fixed from v0.5.2's records, with a STOP for any missing, failed or duplicated record;
  - E1's population taken from version 4's own `group_variance` refusals, counted by a probe in a version-4 rerun on each curve;
  - v0.5.2's records sealed by their sidecars, and in the fingerprint;
  - both versions' sensitivity details reported.
- **Round 2:**
  - an E1 use counted only as a completion that is not still undefined;
  - the error ratios computed against stage A's raw bounds (`sigma_bound_ppm`, `sigma_box_bound_ppm`), sealed;
  - `aperture_depth` added to the details.
- **Round 3:** exactly the 31 stage A records required, each OK with finite positive bounds. Round 3 was the last round, and its conservative option was adopted.

## Stage B, B1.3: the recalibration screen's code

`b1_recal.py` and `b1_data.py` were reviewed before any B1.3 run. Codex CLI 0.167.0-alpha.3.2 answered in Portuguese, and the answers are stored unchanged.

| Round | File | Model, effort | Verdict | SHA-256 |
|---|---|---|---|---|
| 1 | [b1-recal-round-1-answer.md](b1-recal-round-1-answer.md) | gpt-6.1-sol, high | `REFUTED` | `eb946d459934cfbae21e0c23be274a6a4726e130737c11a3e5737ecc96a7ef28` |
| 2 | [b1-recal-round-2-answer.md](b1-recal-round-2-answer.md) | gpt-6.1-sol, high | `REFUTED` | `8f39c4010ca16e946a3f56e4386dae4bbbe52bd6575a525236c2ae053e190ee3` |
| 3 | [b1-recal-round-3-answer.md](b1-recal-round-3-answer.md) | gpt-6.1-sol, high | `WEAKENED` (the conservative options, adopted) | `8891e68620adc9db1f2f7548ad948f9b3f4bc50658ecf88ffe2135ad4712ed64` |

The tokens are cumulative over the conversation `b1-recal`:

- round 1: 1,466,301 input (1,355,648 cached) and 12,435 output;
- round 2: 2,412,548 input (2,264,320 cached) and 18,573 output;
- round 3: 3,155,254 input (2,992,384 cached) and 23,561 output;

The conversation now counts **186,431** against stage B's cap.

The corrections were these:

- **Round 1:**
  - equal host weights in E4's bootstrap;
  - safeguards that hold whatever the outcome;
  - E1's population taken from the contrast variance's own refusal, with every branch's population counted;
  - a fetch under the ledger's lock, bounded by c2-fetch.json's recorded sizes;
  - the fingerprint extended with E4's inputs;
  - the activation stored per contrast.
- **Round 2:**
  - degeneracy detected with a numerical tolerance;
  - each estimator's errors kept apart, an unknown eligibility counted against a PASS;
  - the fetch's metadata reserved before any write.
- **Round 3:** the manifest's exact bytes checked and written, and existing files checked before any write, with a mismatch a STOP. Round 3 was the last round, and its conservative options were adopted.

The facts disclosed:

- E4 has 13 gate-passing hosts with an OK original record, not the design's 16.
- scipy is not used, because it is not a declared dependency.

## Stage B, B1.4: the forecast's code

`b1_b14.py` was reviewed before any B1.4 run. Codex CLI 0.167.0-alpha.3.2 answered in Portuguese, and the answers are stored unchanged.

| Round | File | Model, effort | Verdict | SHA-256 |
|---|---|---|---|---|
| 1 | [b1-b14-round-1-answer.md](b1-b14-round-1-answer.md) | gpt-6.1-sol, high | `WEAKENED` (3 corrections) | `eceacaa5aef54aabe16ca5fecca8878d87f60a10ce2b8d2953f9b44be104507a` |
| 2 | [b1-b14-round-2-answer.md](b1-b14-round-2-answer.md) | gpt-6.1-sol, high | `WEAKENED` (2 corrections) | `955a90625c80e88260d481ac73bd9d2821d6fa1c3395aafbe0005030b6cf0b26` |
| 3 | [b1-b14-round-3-answer.md](b1-b14-round-3-answer.md) | gpt-6.1-sol, high | `WEAKENED` (the conservative option, adopted) | `ea3a9cfa24c445f4bc013d9e84210e41ac6db68a76d61f21cc515ce064b7dd0d` |

The tokens are cumulative over the conversation `b1-b14`:

- round 1: 944,724 input (836,096 cached) and 7,744 output;
- round 2: 1,503,257 input (1,379,328 cached) and 11,957 output;
- round 3: 2,147,650 input (2,006,400 cached) and 15,047 output;

The conversation now counts **156,297** against stage B's cap.

The corrections were these:

- **Round 1:**
  - a checked partial read for a stopped part;
  - the frozen interval 3000 to 3199 kept, with the smoke's index 3000 disclosed and the overlaps with other development indices refused;
  - v0.4's inputs in the fingerprint.
- **Round 2:**
  - an incomplete D2/D4 part is never decided;
  - integrity refusals stand.
- **Round 3:** the partial read decided by the persisted ledger state, with a failed gate always propagated. Round 3 was the last round, and its conservative option was adopted.

## The end-of-B1 review (the stop report, `b1-stop-report.md`)

Codex's one review at B1's end (the maintainer's rule: one review at the end of each step), of the stop report and its records (`67a2107`): every number against its record, the claims' limits, the pricing, T3b, D1 and round 3's closing reading. Codex CLI 0.167.0-alpha.3.2 answered in Portuguese, and the answers are stored unchanged.

| Round | File | Model, effort | Verdict | SHA-256 |
|---|---|---|---|---|
| 1 | [b1-end-round-1-answer.md](b1-end-round-1-answer.md) | gpt-6.1-sol, high | `WEAKENED` (pricing, confirmation, calendar and cap coverage) | `e5e4e038165cd3fa17d97c920cf6df10decc472b8a6bd536539be7d16a9bb62d` |
| 2 | [b1-end-round-2-answer.md](b1-end-round-2-answer.md) | gpt-6.1-sol, high | `WEAKENED` (one duplicated table header) | `fa213c8e64c61520777cb3993a714f768f34e69cbe4e722dacae80f9c9fa10da` |

The tokens are cumulative over the conversation `b1-end`:

- round 1: 2,375,126 input (2,239,744 cached) and 17,601 output;
- round 2: 3,088,811 input (2,932,352 cached) and 21,712 output;

The conversation now counts **178,171** against stage B's cap.

Applied as Codex wrote them. Round 1 reproduced the forecast, the census, the blockers and the consumption in memory, checked the shards against their sidecars, and confirmed that the D2/D4 stop's reading and the new blocker diagnostic are faithful (`K_B`, `U_B` and the answer do not depend on the defective counter). Its corrections: the A0 line called a provisional inherited reference, and version 3's failed schedule (2,956) left out of the low end; the estimators' 1,000 contrasts an illustration, not a sizing, with E3's 15 % availability a design problem; the confirmation re-extrapolated per stratum and called not priced in full; the totals called provisional subtotals, with the cumulative total against 3,100; the calendar conditioned (no acceptance authorized, the release a hypothesis); E3's lower end 1.045; T3b a planning preference with the union's safeguards before any result; the consumption completed with sub-caps, a per-part table and the first smoke's cap stop. Round 2 confirmed every correction against the records and asked only to remove a duplicated table header, which was removed as written; no third round was needed, since no point remained in divergence.

## B1.4's D2/D4 completion (`b1_d2d4_rest.py`), before its run

Codex's review of the script that reconciles the cap stop of `b1_forecast_d2d4` and runs its 19 missing curves with the same code, fingerprint and rows, within 1.5 CPU-h more (the maintainer's decision of 2026-11-12, item 1, #217), before the run and before its record on #217. Codex CLI 0.167.0-alpha.3.2 answered in Portuguese, and the answers are stored unchanged.

| Round | File | Model, effort | Verdict | SHA-256 |
|---|---|---|---|---|
| 1 | [b1-rest-round-1-answer.md](b1-rest-round-1-answer.md) | gpt-6.1-sol, high | `WEAKENED` (the attempt argument, recoverability, the closing checks, the cap margin) | `b3d74668a32331eb05e54ad1837dd88d4540edf17367a26b245142e5d95c84c4` |
| 2 | [b1-rest-round-2-answer.md](b1-rest-round-2-answer.md) | gpt-6.1-sol, high | `WEAKENED` (the rerun's preparation not resumable) | `84729a2a39812075eb4a2d0314e0d476018e223886c47d48046c7565e8511c10` |
| 3 | [b1-rest-round-3-answer.md](b1-rest-round-3-answer.md) | gpt-6.1-sol, high | `SURVIVED` | `f34bfc1eca5988786df91190ffba5606c4a2e1e5601e3d359897fdfdd9bc82ea` |

The tokens are cumulative over the conversation `b1-rest`:

- round 1: 999,689 input (924,672 cached) and 9,898 output;
- round 2: 1,425,954 input (1,338,368 cached) and 15,381 output;
- round 3: 1,902,221 input (1,806,848 cached) and 18,757 output;

The conversation now counts **114,130** against stage B's cap.

Applied as Codex wrote them. Round 1 confirmed the fingerprint, the 181 sidecars, the 19 missing rows, the reconciliation keeping the stop on file and the cap's algebra. Its corrections: accept only attempts 1 and 2; run every check before any reconciliation and resume a started part under its identity; reconcile the driver's own stop file and refuse at the closing on a driver stop, a failed gate or a summed consumption above 1.5 CPU-h; a cap margin for the watchdog's polling (`MARGIN` 1.2). It also confirmed that no parameter can widen a one-shard checkpoint without changing `budgeted`, so the re-stop risk stays disclosed. Round 2 confirmed those and found that a failure between the ledger's reconciliation and the rerun part's creation left the rerun blocked; the persisted reconciliation now authorizes the resume (never another attempt), and the foreseeable refusals (allocation, gates) run before any change. Round 3 reproduced the failure cases with mocks and found no new defect.

## The decisive blockers and the stop report's addendum (`b1_blockers_decisive.py`, `b1-stop-report-addendum.md`)

Codex's review of the new read-only record of B1.4's decisive blockers, its output and the addendum to the B1 stop report (the maintainer's decision of 2026-11-12, item 2, with the D2/D4 completion of item 1). Codex CLI 0.167.0-alpha.3.2 answered in Portuguese, and the answers are stored unchanged.

| Round | File | Model, effort | Verdict | SHA-256 |
|---|---|---|---|---|
| 1 | [b1-blockers-round-1-answer.md](b1-blockers-round-1-answer.md) | gpt-6.1-sol, high | `WEAKENED` (E4's states, the systematics claim, E2 on D2, one table missing) | `8884b708237b025047dafdb0cb4b897fd163151702eae3c83924e32e8a198581` |
| 2 | [b1-blockers-round-2-answer.md](b1-blockers-round-2-answer.md) | gpt-6.1-sol, high | `SURVIVED` | `58c5af35ea90f40e0567660cabdf5006d2f09360e919ddd912622673dc8ae571` |

The tokens are cumulative over the conversation `b1-blockers`:

- round 1: 1,604,497 input (1,480,448 cached) and 10,733 output;
- round 2: 2,076,304 input (1,936,512 cached) and 13,011 output;

The conversation now counts **152,803** against stage B's cap.

Applied as Codex wrote them. Round 1 recomputed the T2a and D2 sections through the verifying readers and found them equal to the JSON, independently re-aggregated T2a, and confirmed K_B 331, U_B 0, C 373, the corrected lists, the what-ifs (72/124/211/228 and 9/8/33/34), D2 FAIL and D4 PASS on the 200 curves, and that only B1's two lists counted diagnostics. Its corrections: E4 without a measurement is "called, no measurement completed", not a fallback to version 4 (the script rerun, read only); the addendum no longer attributes `systematics`' INCONCLUSIVE to the background sub-check's power; on D2, 21 INCONCLUSIVE and 1 FAIL where E2 operated; `forecast-paths.md` added to item 2(c); "single blocker" defined against `aggregate`'s branch. Round 2 confirmed every correction and reproduced the updated JSON exactly.
