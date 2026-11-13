# v0.5.4 consensus record

Codex's answers in v0.5.4 Information checks (#217), stored unchanged, with the model, the effort and
the Codex CLI's version. Codex is consulted read only (sandbox read-only, processors 8 to 31). The
token count is the maintainer's rule: each conversation's last turn, `input_tokens -
cached_input_tokens + output_tokens`. Divergence after three rounds goes to the more conservative
option, recorded.

## The first half's design, ledger and code (`docs/plans/v0.5.4-h1-design.md`, `ledger_i.py`, `i1_diagnose.py`, `i4_bound.py`)

Codex's review of I1's and I4's design with their frozen rules, the phase's ledger, and then the code, before any run (the maintainer's decision of 2026-11-12, 14:00, item 3). Codex CLI 0.167.0-alpha.3.2 answered in Portuguese, and the answers are stored unchanged.

| Round | File | Model, effort | Verdict | SHA-256 |
|---|---|---|---|---|
| 1 | [h1-design-round-1-answer.md](h1-design-round-1-answer.md) | gpt-6.1-sol, high | `WEAKENED` (I1's enforcement order and identity checks, I4's derivatives and validity, the ledger's binding, review tokens and disk, the Fisher cost) | `fe940998cb2b8b3c2c0f9516fe14f1bf9928eec7d0c600228304b5b4d8f5fbed` |
| 2 | [h1-design-round-2-answer.md](h1-design-round-2-answer.md) | gpt-6.1-sol, high | `WEAKENED` (binding stops, block validation, retained diagnostics, disk bounds, I4's isolation) | `daddc29642ae39ea1b4dd303757e42e9961cf8c8c618554a9e62ec04d0f2eb06` |
| 3 | [h1-design-round-3-answer.md](h1-design-round-3-answer.md) | gpt-6.1-sol, high | `WEAKENED` (I4's stops, I1's provenance, a report when assembly is refused: the conservative options) | `4655f5cb0f490d62854ba2e329f6268ca7dfdb8fa3d3eadc2f678226c408099d` |

The tokens are cumulative over the conversation `h1-design`:

- round 1: 1,147,893 input (1,044,608 cached) and 7,165 output;
- round 2: 2,550,830 input (2,386,560 cached) and 13,650 output;
- round 3: 3,815,627 input (3,611,008 cached) and 17,451 output;

The conversation now counts **222,070** against v0.5.4's caps.

Applied as Codex wrote them. Round 1: the full pipeline replayed (coverage, sensitivity, deferral); every supplied block validated; `dumps` categorical; T2a's identity (v0.4's C2 compatibility, the candidate, decisive and deferred lists, inputs in the fingerprint); L over all 178; I4's mean model frozen, analytic derivatives with a baseline-aware convergence check, E extended, the condition number after column scaling, k² Fisher calls and a 4-8 CPU-h price; the ledger's `assert_bound`, independent-review tokens counted (a separate final allowance), and a disk reservation. Round 2: binding stops by a stop file with later shards skipped and a failing summary; absent versus malformed sensitivity and undeclared blocks; the decisive tests' raw and enforced messages and the report's distributions, estimators and unresolved cases; bounded records; I4's sinusoid isolated and non-finite convergence rejected; `_atomic_save` bound. Round 3 (the last) left three stop defects; by the tie-break, its conservative options were applied and recorded: in I4 an unexpected error or an oversized record is a binding stop, not part of E; I4 verifies I1's provenance (its current fingerprint, the completed and verified part, 206 cases, none skipped, no stop anywhere) before scheduling; and a summary writes its report from the verified shards when the assembly is refused, exiting with a failure.

## I2's and I3's paper designs (`docs/plans/v0.5.4-I2-I3-designs.md`)

Codex's review of the paper designs of I2 (T2a's per-host background bound) and I3 (D1's joint test with the planet side), written in the first half and frozen only after I1's result, with neither run (the maintainer's decision of 2026-11-12, 14:00, item 3). Round 2 was interrupted by the desktop app's restart and rerun from the same prompt; only the completed answer is stored. Codex CLI 0.167.0-alpha.3.2 answered in Portuguese, and the answers are stored unchanged.

| Round | File | Model, effort | Verdict | SHA-256 |
|---|---|---|---|---|
| 1 | [h1-i2i3-round-1-answer.md](h1-i2i3-round-1-answer.md) | gpt-6.1-sol, high | `WEAKENED` (I2's measurement correspondence and unknowns, I3's joint definition, Monte Carlo uncertainty, the price) | `4a5731c12bddadcb3e2317a95666783b60979355acfbe167a1f1a3ef380031aa` |
| 2 | [h1-i2i3-round-2-answer.md](h1-i2i3-round-2-answer.md) | gpt-6.1-sol, high | `WEAKENED` (I3's quantile and fatal precedence, I2's nuisances, numerical freeze and price) | `295e30f765fe001a8daa234a7d22152244f29468e236c4d586ea8f74b398dea9` |
| 3 | [h1-i2i3-round-3-answer.md](h1-i2i3-round-3-answer.md) | gpt-6.1-sol, high | `WEAKENED` (I2's internal detrending, open numerical starts, I3's joint envelope and quantile claim: the conservative options) | `039b36fe7e8dbb755e7016664bb99461710f952b887d57fdb63763dc2b9a67e7` |

The tokens are cumulative over the conversation `h1-i2i3`:

- round 1: 1,491,314 input (1,364,352 cached) and 10,263 output;
- round 2: 2,143,294 input (1,993,984 cached) and 14,373 output;
- round 3: 2,502,745 input (2,344,192 cached) and 19,231 output;

The conversation now counts **177,784** against v0.5.4's caps.

Applied as Codex wrote them. Round 1: I2 rebuilds each injection to read the sub-check's own measurement and the SAP depth's error, keeps σ_op (the sub-check's contrast) apart from σ_GLS (the information bound), counts unknowns so they cannot make a route, and the 56 above 20 a conditional scenario; I3's statistic defined with aliases and penalized priors as a new test, its calibration frozen, its uncertainty propagated, the joint distribution as a conditional scenario, the warning and INCONCLUSIVE paths to the maintainer, its price about 860 CPU-h. Round 2: I3's threshold is the lower α quantile with strict rejection, and a new fatal FAIL makes any gate-passed verdict REFUTED; I2's nuisances are E4's quadratic terms, its numerics filled in, its price 95-380 CPU-h, a smoke only with authorization. Round 3 (the last): by the tie-break, the conservative options were applied and the designs frozen as paper designs only: E4's internal detrending must enter I2's contrast with unit response shown, or the injection is unknown; the remaining starts are impediments; I3 needs a joint-coverage envelope (route only with its lower bound at least 0.95, a finding only with its upper bound below 0.05, unresolved otherwise) and no population guarantee for the quantile. Neither runs before the maintainer's decision.

## I4's completion after the interruption (`docs/validation/v0.5.4/i4_rest.py`)

Codex's review of the script that reconciles I4's interruption (the desktop app's restart at 10 of 290 planets) and runs the 280 remaining planets as part h1_i4_rest with the same code, fingerprint and rows (the maintainer's decision of 2026-11-12, 15:46, items 1 to 3), before its run. Codex CLI 0.167.0-alpha.3.2 answered in Portuguese, and the answers are stored unchanged.

| Round | File | Model, effort | Verdict | SHA-256 |
|---|---|---|---|---|
| 1 | [h1-i4rest-round-1-answer.md](h1-i4rest-round-1-answer.md) | gpt-6.1-sol, high | `WEAKENED` (finish's stop, a resumable reconciliation, an atomic transfer, another interruption, the reader's guards, the stale lock) | `339902ad657bc5928631e57ad009abb4cf5b341802363cb1944ed3ec501725b4` |
| 2 | [h1-i4rest-round-2-answer.md](h1-i4rest-round-2-answer.md) | gpt-6.1-sol, high | `WEAKENED` (a durable record of each run, the PID check, pending stops whatever the history) | `f8713bc7d30b54b53fd8ea195e751a708a4773b71e9b1e4ed9db58754120431f` |
| 3 | [h1-i4rest-round-3-answer.md](h1-i4rest-round-3-answer.md) | gpt-6.1-sol, high | `SURVIVED` | `708e0bbb3d00f2224a1fe6e8b221dc311143b5ca70c65c5bb02d2c17a257bfca` |

The tokens are cumulative over the conversation `h1-i4rest`:

- round 1: 633,746 input (566,656 cached) and 9,650 output;
- round 2: 1,017,642 input (941,440 cached) and 14,699 output;
- round 3: 1,348,172 input (1,262,208 cached) and 18,534 output;

The conversation now counts **104,498** against v0.5.4's caps.

Applied as Codex wrote them. Round 1 confirmed the crash charge (5.082674 CPU-h), the 280 rows, the drain at 19:30 through the driver, and the faithful reuse of the frozen summary with planet 3129 excluded from L and disclosed; its corrections: keep finish's stop, resume only this step's own intermediate stop, write the transfer's debit, credit and history in one save (ledger_i.py stays unedited, inside I1's and I4's fingerprints), refuse an open batch of the rest, guard the reader (stops, gates, unique keys, 290 records), and release the stale lock only as a kept file. Round 2: a durable start and end per run (a start without an end is a STOP), a failed PID query treated as alive, and a pending main stop checked whatever the history. Round 3 found no new defect; its conservative note: a crash after a start, even before any dispatch, is a STOP for the maintainer, never a manual completion of the journal or a repeat.

## I4's second completion step (`docs/validation/v0.5.4/i4_rest2.py`), reviewed as a diff against `i4_rest.py`

Codex's review of the script that reconciles h1_i4_rest's cap stop as a fact and runs the 266 remaining planets as h1_i4_rest2 with 6 workers, and of its one pre-approved reserve (h1_i4_rest3 with the first half's sub-cap raised to 30), before its run (the maintainer's decision of 2026-11-12, 18:05). Codex CLI 0.167.0-alpha.3.2 answered in Portuguese, and the answers are stored unchanged.

| Round | File | Model, effort | Verdict | SHA-256 |
|---|---|---|---|---|
| 1 | [h1-i4rest2-round-1-answer.md](h1-i4rest2-round-1-answer.md) | gpt-6.1-sol, high | `WEAKENED` (the total projection at the transfer, run 3's accepted stops and zero debits, the science checks) | `e8917bdd0fd69e2e8327a583b6ebb96248e50bbd8696ec8558fa2a5fa63d1484` |
| 2 | [h1-i4rest2-round-2-answer.md](h1-i4rest2-round-2-answer.md) | gpt-6.1-sol, high | `WEAKENED` (a closed part counted twice in run 3) | `0e4b440667c27c88b62795201fa5a6a09d1442a5f7084d2a08b20825688a974c` |
| 3 | [h1-i4rest2-round-3-answer.md](h1-i4rest2-round-3-answer.md) | gpt-6.1-sol, high | `WEAKENED` (rounding of a debit, a closed part as a target: the conservative options) | `e4041d4b90d09fd674306a1bef68f00bce5b8388285486a29b9283c994114b83` |

The tokens are cumulative over the conversation `h1-i4rest2`:

- round 1: 715,607 input (654,464 cached) and 8,886 output;
- round 2: 1,516,362 input (1,436,288 cached) and 16,208 output;
- round 3: 2,099,658 input (2,009,728 cached) and 24,426 output;

The conversation now counts **114,356** against v0.5.4's caps.

Applied as Codex wrote them. Round 1 confirmed the 290 rows, the 10 and 14 verified shards, the 266 left, the fingerprint, the atomic transfer and the drain; its corrections: the stopped part's frozen projection would push the total projection above 50 at the transfer, so it is accounted by its consumption; run 3 accepts the cause's own cap stop in the driver's folder when it agrees with the ledger, and skips a donor with nothing left; I4's binding stop and L so far (below 23) are checked before any change. Round 2 found the archived consumption counted twice in run 3; archiving, and reducing the allocation, both double count through the unallocated-line term, so a closed part now keeps its identity, consumption and allocation and its projection becomes its consumption, the frozen projection kept as `projection_at_stop` and in `allocation_closures` (totals 48.26 for run 2 and 48.36 in the run-3 scenario). Round 3 (the last): by the tie-break, the conservative options were applied and recorded: a donor's debit is rounded down, and a closed part is never a target again; any failure in the transition to run 3 is a STOP for the maintainer, never resumed by run 2.

## The driver correction for future parts (`docs/validation/v0.5.4/budgeted_v3.py`) and the candidate detached launcher (`launch_detached.py`)

Codex's review of the projection correction for future parts and of a candidate launcher for runs that should survive a restart of the desktop app, with their tests (`tests/test_v054_budgeted_v3.py`, `tests/test_v054_launch_detached.py`), after I4 (the maintainer's decisions of 2026-11-12, 15:46, item 4, and 18:05, item 3). Codex CLI 0.167.0-alpha.3.2 answered in Portuguese, and the answers are stored unchanged.

| Round | File | Model, effort | Verdict | SHA-256 |
|---|---|---|---|---|
| 1 | [h1-driverv3-round-1-answer.md](h1-driverv3-round-1-answer.md) | gpt-6.1-sol, high | `WEAKENED` (the refusal of a driver stop before the reconciliation; the tests; the launcher's identity before the work runs) | `a92ac3af10b28b87026e43037b8b125cf957e018560488b8288cffa9b48749e4` |
| 2 | [h1-driverv3-round-2-answer.md](h1-driverv3-round-2-answer.md) | gpt-6.1-sol, high | `WEAKENED` (a larger projection raises the part's cap; a race on the launcher's record) | `4427a12bf591efa31f9ed28eb0fec38219c9268fff436eda77479db4ae371fa5` |
| 3 | [h1-driverv3-round-3-answer.md](h1-driverv3-round-3-answer.md) | gpt-6.1-sol, high | `WEAKENED` (the restart check's test of life and its full protocol; the driver and the launcher pass) | `94a7c975f7b054e624aec20c1699131459155ef8b19e8accde809466bdf3b85f` |

The tokens are cumulative over the conversation `h1-driverv3`:

- round 1: 657,219 input (562,560 cached) and 6,694 output;
- round 2: 1,197,513 input (1,084,160 cached) and 12,023 output;
- round 3: 1,857,617 input (1,725,056 cached) and 16,572 output;

The conversation now counts **149,133** against v0.5.4's caps.

Applied as Codex wrote them. Round 1: `budgeted_v3.execute` refuses a driver `stop.json` before it reconciles anything, in the driver's own order; the tests were rewritten (a real interruption of the real driver with a real pool, a deterministic batch comparing v0.5.2 and v3 to the last digit, the crash charge against the caller's hard cap and the total, the three kinds of batch, the refusals, no live worker left); the launcher starts its child suspended and resumes it only after its PID and creation time are written atomically, ending it by its own handle on any failure, with complete ctypes prototypes. In the same round the measure became the larger of the charges less the crash charges and the shards' sidecar CPU (never below round 1's). Round 2: a larger projection also raises the part's own cap after the checkpoint (1.5 times the projection), so that is documented in the module and tested with Codex's example and the exact caps each driver run was given; the launcher reserves its log's prefix with `O_EXCL` before anything is opened or started, and its start sequence is tested offline with a fake process (the record before the resume, each failure ending the child, a refused breakaway, a reused log, two concurrent launchers). Round 3 (the last) found the driver's and the launcher's points resolved, and asked, as the conservative options, that the restart check test a process's life by its termination state (a zero-timeout wait on its handle, any query failure 'unknown'), and that the restart test's decision require: criteria and the watched processes persisted before the launch and alive at the first beat, the probe's two processes alive before and after the restart with the same identities, the app's exit and its new instance inside the observed window, the planned duration and cadence with positive intervals of at most 30 s on both clocks, the final line and both processes ended. These were applied to the probe and its check (under `.cache`, not committed), and the docstring's comparison was made exact. `scripts/launch_affinity.ps1` stays the launcher of record until the maintainer approves the restart test's result; neither module was used by I4.

## The check of Fable 5.2's audit (`docs/plans/v0.5.4-fable-audit.md`): its 18 points and its section-5 plan

Codex's check of each of the audit's 18 points and of its section-5 plan, steps 1 to 7 with the maintainer's adjustments, against the files at `9742a96` (the maintainer's decision of 2026-11-12, night, item 3). The short record is [`v0.5.4-audit-check.md`](../v0.5.4-audit-check.md). Codex CLI 0.167.0-alpha.3.2 answered in Portuguese, and the answers are stored unchanged.

| Round | File | Model, effort | Verdict | SHA-256 |
|---|---|---|---|---|
| 1 | [h2-audit-round-1-answer.md](h2-audit-round-1-answer.md) | gpt-6.1-sol, high | `WEAKENED` (3 points accepted, 14 accepted with a reservation, 1 rejected; steps 1 to 7 all accepted, six with a reservation; the frozen rules each step must fix; the budget; corrections to sections 2, 3 and 6) | `4b6296683faa27da6777295e2a62be729f86f2db04832f90a1342ba48b841b21` |

The tokens are cumulative over the conversation `h2-audit`:

- round 1: 1,597,330 input (1,460,992 cached) and 12,320 output;

The conversation now counts **148,658** against v0.5.4's caps.

One round. Claude agreed with every row, so no second round was needed; the check is the record, and its corrections are carried into the second half's step designs. Point 14 is rejected and stays recorded with its reason.

## T3b's eligibility count (`docs/plans/v0.5.4-t3b-eligibility-count.md`, `docs/validation/v0.5.4/t3b_count.py`) and the record defects (`docs/validation/v0.5.4/record-defects.md`)

Codex's review of the design and script of T3b's eligibility count of the approved frame's 22 remaining stars (the maintainer's decision of 2026-11-12, night, item 6) and of the four record defects (item 7d), before the count runs. Codex CLI 0.167.0-alpha.3.2 answered in Portuguese, and the answers are stored unchanged.

| Round | File | Model, effort | Verdict | SHA-256 |
|---|---|---|---|---|
| 1 | [h2-t3b-round-1-answer.md](h2-t3b-round-1-answer.md) | gpt-6.1-sol, high | `WEAKENED` (metadata only and a count, not a selection; retries, provenance, per-query records, the price; records 2 to 4 overstated) | `2dc0acffafa0703d8eb6253687850a0018e3e2f31c91b6ba0cac755cfea67bec` |
| 2 | [h2-t3b-round-2-answer.md](h2-t3b-round-2-answer.md) | gpt-6.1-sol, high | `WEAKENED` (a listing's partial searches lost; `inputs.json` not bound to the freeze commit) | `451e496b2a56b785ba5ed1436243cace3e845871f14696e04546fbc29005e673` |
| 3 | [h2-t3b-round-3-answer.md](h2-t3b-round-3-answer.md) | gpt-6.1-sol, high | `WEAKENED` (the attempt history lost when a permanent failure follows a transient one) | `005f33298b8068391a03c0caa663b60df0714280f937b6b0e42c6259b7b231a7` |

The tokens are cumulative over the conversation `h2-t3b`:

- round 1: 841,391 input (757,248 cached) and 6,863 output;
- round 2: 1,453,568 input (1,352,704 cached) and 11,781 output;
- round 3: 2,012,376 input (1,901,312 cached) and 15,919 output;

The conversation now counts **126,983** against v0.5.4's caps.

Applied as Codex wrote them. Round 1: it is metadata only, reads nothing new from ExoFOP, and is a count, not a selection of real targets; the triage is v0.5's, so k is comparable at that step, while 11 + k joins two query dates. Corrected: `with_retries` (5 attempts, 120 s), provenance bound to v0.5's freeze and selection commits with the frame checked at {63, 41, 11} and 22 left, per-query records, the price (up to 330 calls and 2h56 of backoff), the ExoFOP wording; record 2 is not a defect, record 3 prescribes no fix (analytic derivatives already exist), record 4 names the extrapolation from B0b. Round 2: each search is now logged on its own through `sel.transient`, with its hash or error, and `inputs.json` is compared with its bytes at the freeze commit before it is read. Round 3 (the last): by the tie-break, the conservative option was applied: every triage attempt is accumulated with its number, time and result or error, and persisted in any outcome. The question whether the TOI table's disposition column is ExoFOP user data stays not confirmed.

## Step 1: D2's joint floor and T2a's losses no procedure fixes (`docs/plans/v0.5.4-h2-step1-floor.md`, `docs/validation/v0.5.4/step1_floor.py`)

Codex's review of step 1's frozen design and script before any per-case overlap was read (the maintainer's decision of 2026-11-12, night, item 4a); Codex was told not to open the per-case records, and did not. Codex CLI 0.167.0-alpha.3.2 answered in Portuguese, and the answers are stored unchanged.

| Round | File | Model, effort | Verdict | SHA-256 |
|---|---|---|---|---|
| 1 | [h2-step1-round-1-answer.md](h2-step1-round-1-answer.md) | gpt-6.1-sol, high | `WEAKENED` (disclosures of predictable outcomes; one category per test; F_upper's meaning; a missing import, wrong fields, the T2a refusal, hidden tests, the REFUTED scenario, integrity) | `707011b35254c0319b8e535af53f2224089a807c333a16ed846b913e549b8d64` |
| 2 | [h2-step1-round-2-answer.md](h2-step1-round-2-answer.md) | gpt-6.1-sol, high | `WEAKENED` (T2a's class field; INFO independent of I1's class; the 24 non-grid cases) | `b88ffef8ac962d617c8377b09457c91429cd79bdc73037a4ed8a313e8b921d41` |
| 3 | [h2-step1-round-3-answer.md](h2-step1-round-3-answer.md) | gpt-6.1-sol, high | `WEAKENED` (invalid probabilities in `_below_bound`) | `43f9e91aa0e11fe3ebfde43116b39b8c61e8d0d5c024c9c072cad015d36da211` |

The tokens are cumulative over the conversation `h2-step1`:

- round 1: 1,189,793 input (1,090,176 cached) and 8,310 output;
- round 2: 1,878,523 input (1,748,096 cached) and 13,029 output;
- round 3: 2,366,464 input (2,219,904 cached) and 15,507 output;

The conversation now counts **162,067** against v0.5.4's caps.

Applied as Codex wrote them. Round 1: the design discloses that T2a under B is exhausted under DATA by its 20 not-enough-data blockers alone and that D2 cannot reach F_strict > 22 from the marginals; each test gets the set of its categories; F_upper is not a demonstrated bound, so a margin read from it assumes every REC and PROC loss recovered; the script reads I1 and I4 through their own reviewed readers, compares the reproduced blockers with the published ones, counts unknown T2a records as UNK losses, compares only the floors outside the REFUTED with 2, and runs with `python -B`. Round 2: T2a's `inconclusive_class`; INFO from an INCONCLUSIVE test and a valid bound whatever I1's class, REC only for class (i); the non-grid class-(ii) tally checked at exactly 24. Round 3 (the last): by the tie-break, the conservative option: an absent, non-finite or out-of-range probability is no bound, so class (i) stays UNK.

## The end-of-step review of step 1 and T3b, and steps 7 and 5 before their runs (`v0.5.4-h2-step7-sinusoid.md`, `step7_sinusoid.py`, `v0.5.4-h2-step5-gap.md`, `step5_gap.py`)

Codex's end-of-step review of step 1's floors and T3b's count, and its review of steps 7 (`sinusoid`'s joint limit) and 5 (E2's gap decomposition) before their runs (the maintainer's decisions of 2026-11-12, night, items 4a, 4d, 4f and 6). Codex CLI 0.167.0-alpha.3.2 answered in Portuguese, and the answers are stored unchanged.

| Round | File | Model, effort | Verdict | SHA-256 |
|---|---|---|---|---|
| 1 | [h2-step7-round-1-answer.md](h2-step7-round-1-answer.md) | gpt-6.1-sol, high | A: `SURVIVED` (step 1 and T3b follow their designs; no stop). Step 7: `WEAKENED` (not a universal impossibility; sensitivity apart from retention; Monte Carlo precision and validity; explicit stops; caps for the phase) | `8be49e5fcfbc55622f4c74237cf7673d614e1d9a2c789afde2cd44d688abde76` |
| 2 | [h2-step7-round-2-answer.md](h2-step7-round-2-answer.md) | gpt-6.1-sol, high | Step 7: `WEAKENED` (the residual Gram matrix; stops against the outcome). Step 5: `WEAKENED` (the multiplicative trend; a common amplitude with E2; approximations; unknowns and denominators; V0 and divergence) | `6c3f01385d4a8da9489745a1ddfce525fe4ad4b95987541c6cdb103529dfdcf9` |
| 3 | [h2-step7-round-3-answer.md](h2-step7-round-3-answer.md) | gpt-6.1-sol, high | Step 7: `SURVIVED`. Step 5: `WEAKENED` (E2's effective response not shown; collinearity; V0's completeness) | `336066e327c83191f29b11a500d16939f666556ca1f149ff543a854cea4e7fae` |

The tokens are cumulative over the conversation `h2-step7`:

- round 1: 1,469,996 input (1,359,232 cached) and 10,532 output;
- round 2: 2,543,312 input (2,398,464 cached) and 18,424 output;
- round 3: 3,280,734 input (3,116,416 cached) and 23,355 output;

The conversation now counts **187,673** against v0.5.4's caps.

Applied as Codex wrote them. In round 2 Codex agreed that corrections found in a review before any run are not the stop list's 'defect', which concerns defects found in runs or records. Step 7 survived after round 3; its last documentary cleanups were applied. Step 5: by the tie-break after round 3, the conservative option was applied: E2's effective response is unknown, so no comparison with E2's error, no explained share and no decision from them are drawn; the gap's outcome is INCONCLUSIVE by design, and the step reports the Fisher inflations of its variants (and, for the trapezoid variants only, the crossings of D2's odd_even REC losses); V_all is a partial combination; V0 must be compared on every planet.

## Step 4: B0's oracle at stellar errors of 1, 2 and 3 % (`v0.5.4-h2-step4-b0-errors.md`, `step4_b0_errors.py`)

Codex's review of step 4 before its run (the maintainer's decision of 2026-11-12, night, item 4c). Codex CLI 0.167.0-alpha.3.2 answered in Portuguese, and the answers are stored unchanged.

| Round | File | Model, effort | Verdict | SHA-256 |
|---|---|---|---|---|
| 1 | [h2-step4-round-1-answer.md](h2-step4-round-1-answer.md) | gpt-6.1-sol, high | `WEAKENED` (stops' coverage; NaN in the 5 % check; the summary's CPU) | `8bc3ddc54f0107748bbc6f30669a2e3b0dc6366eedd8c3d712c3f13226a8417c` |
| 2 | [h2-step4-round-2-answer.md](h2-step4-round-2-answer.md) | gpt-6.1-sol, high | `WEAKENED` (reserve the charge and charge before publishing; a unique charge name; stops' wording) | `781a6b15546d8ec0d11f1cf529527787e0b6d4e655172e959ceb1c2dba06f356` |
| 3 | [h2-step4-round-3-answer.md](h2-step4-round-3-answer.md) | gpt-6.1-sol, high | `WEAKENED` (a UUID in the charge's name) | `13b568335f3529883ac3a3c5fb16100ad05197d4a1ddfb9e614b620e56312454` |

The tokens are cumulative over the conversation `h2-step4`:

- round 1: 767,001 input (682,880 cached) and 5,327 output;
- round 2: 1,111,666 input (1,006,208 cached) and 7,627 output;
- round 3: 1,512,568 input (1,392,256 cached) and 9,788 output;

The conversation now counts **130,100** against v0.5.4's caps.

Applied as Codex wrote them. Round 1 confirmed that the script reproduces B0's oracle and reading at the new errors and that reading B0's shards by the fingerprint its committed record states is sound (recomputing it hashes today's code). Corrections: stops before any record against stops in the record, no aggregate under a stop, the 5 % check requiring finite positive distances, the summary's own CPU charged. Round 2: the charges' room checked for the summary's reserve before reading, the record written only after the charge succeeds, a unique name per invocation, every distance checked before any aggregate. Round 3 (the last): by the tie-break, the conservative option: a UUID added to the charge's name.
