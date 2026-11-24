# Consensus record: v0.5.9 Ephemeris entry (exploratory prototype)

Every answer and attachment here is stored unchanged, with its SHA-256. Codex's answers carry the
model, the effort and the Codex CLI version.

## The origin of the phase

The maintainer's decision of 2026-11-23 (received at 19:28 local, #218, comment 7115813315),
item 0.
- **The proposal.** With the maintainer's approval, the maintainer's adviser launched a new,
  read-only Claude Fable 5.2 session on `4a704f0f`. It used 350,977 tokens, outside Codex's lines.
  It proposed a full v0.5.9: battery version 5 in `src/`, part A on 108 TOIs, and a claim under a
  lock on 600 PCs. The plan is in Brazilian Portuguese and is stored as it is, like v0.5.8's
  attachments. Its recounts are its own, and exploratory.
- **The review.** One Codex round reviewed that design in conversation `v059plan` (thread
  `01a20a4f-3ec2-7cb2-8a0a-5990041bd6d7`). It returned `REFUTED`, with 7 blocking items, and proposed
  a smaller alternative.
- **The decision.** By the rule of the most conservative option, the maintainer opened v0.5.9 as an
  **exploratory prototype**: [the plan](../v0.5.9-plan.md).

The three files are those of `.cache/v059/plan-review/`, copied unchanged. Each SHA-256 was checked
against its source before the commit. The plan's SHA-256 is also the one the Codex prompt cites.

| File | What it is | SHA-256 |
|---|---|---|
| [fable-plan.md](fable-plan.md) | The Fable 5.2 session's plan (Portuguese) | `dc5756a4169cebe47441e6dea75122f90670727bfe59615536eef5985fc71386` |
| [codex-prompt.md](codex-prompt.md) | The prompt of Codex's round | `5e2b501ce27cd6cd8d75c0fc1a3782b779a07423c0a514a1304477d1aa503415` |
| [codex-answer.md](codex-answer.md) | Codex's answer: **OVERALL: REFUTED**, 7 blocking items | `06f2ee531d04c52b184b3687be4a8f0ece8eb78fa2d5289807fb071797e432d2` |

- **The round:** Codex CLI 0.167.0-alpha.3.2 (`codex_affinity.ps1 -VersionOnly`), model
  gpt-6.2-sol, effort high.
- **Its tokens:** 1,576,727 input (1,436,032 cached) and 13,921 output, so **154,616** review
  tokens.

**What the answer settled, as the decision took it:**
- **Blocking items 1 to 3** (the execution path, the fixed evaluation with the probe grid, the
  centroid's numerical failures) are handled at prototype level by the phase's script.
- **Blocking items 4 to 7** (the paired claim, the thresholds and power, the freeze and the lock,
  the process and sampling gaps) go to the version-5 specification draft, a deliverable of the
  phase.
- **The fact table's row on the v0.5.8 report** (12 lower SNRs) was checked against the committed
  records and gave correction 2:
  [docs/reports/v0.5.8-report-correction-2-2026-11-23.md](../../reports/v0.5.8-report-correction-2-2026-11-23.md).

## The prototype, before the run: round 1

The decision, item 3: one round on the plan, the set, the control rule and the scripts, before
running, resuming the same conversation (thread `01a20a4f-3ec2-7cb2-8a0a-5990041bd6d7`). It
reviewed `e581d078` (the plan, the scripts and the seed in `d70adc3`, the drawn set in `e581d07`).
Codex CLI 0.167.0-alpha.3.2, model gpt-6.2-sol, effort high. The answer is stored unchanged.

| Round | File | Verdicts | SHA-256 |
|---|---|---|---|
| 1 | [prototype-round-1-answer.md](prototype-round-1-answer.md) | checks 1, 2, 7, 8 PASS; 3, 4, 5, 6 FAIL; six blocking items; **OVERALL: REFUTED** | `3a61f90cd36d6a0e7e6bd26c2cf1ffd73805ccb3236440899001b05880245025` |

The round used 4,780,683 input tokens (4,433,152 cached) and 25,472 output tokens: **373,003**
review tokens (the turn's own usage, as the CLI reports it for a resumed thread).

**What Codex confirmed:** the set reproduces from its rule (all 24, their order, the four source
hashes); the seed commit was pushed before the set commit; the explicit path holds; nothing needs
a change in `src/`; correction 2's arithmetic.

**Applied, all six blocking items, in the prototype only:**
1. **The window and the probes.** The period window's ends are exact trials and no trial lies
   outside it (n equal steps per side, the step at most the battery's fine step). The probe
   offsets are declared as formulas of the final fit, and E's own grid steps are recorded apart.
   Transits are counted from the same membership as the depth (finite, positive noise, half-open
   box). New tests: an injection near the window's end, exact ends, the transit count.
2. **The centroid guard.** Covariances are checked symmetric as well as finite and positive
   definite; in `sky_power`'s simulations both quadratic forms of every draw are checked before
   the rule reads them. Only a guard's own failure becomes INCONCLUSIVE; unrelated exceptions
   propagate; the patches are restored in `finally`. New tests on the real simulation path and on
   propagation.
3. **Completeness and Q3.** The bundle records the run's terminal state; the report marks nothing
   without one, and marks a question only if its TOIs are complete (no row without a record, no
   required unit missing, no `INCOMPLETE` consensus). A probe never recorded is `INCOMPLETE`, apart
   from a recorded failure. Q3 needs a reason, reports evaluated and skipped apart, and keeps the
   guard's reason.
4. **The caps, enforced.** Downloads: a metered byte allowance per download unit, refused at the
   allowance, interrupted units charged their whole allowance, `NoProductsError` attempts
   recorded; the 15 GB cap is now used. CPU and disk: a live halt event from the monitor stops
   every running unit with its record at the cap.
5. **Recovery.** The runner's own batch loop replaces `seeded_run.run_batch`: one serialized marker
   writer, the monitor stopped in `finally`, interruptions charged before any redispatch, the
   run's fingerprints pinned by the first batch (a resume or a bundle with changed files is
   refused), and the adapter's manifest hashed and checked with the FITS files.
6. **Cleanup and the archive.** `clean` runs only on a complete run or one the maintainer ended
   with `abandon` (which `run` then refuses to resume); cache roots that are links are refused at
   the start and before each download; `verify-archive` checks the Drive copy of staged unit
   records against its SHA-256, with a manifest, before anything local is retired.

**Non-blocking items, applied:** Q1's headline is the same *decided* class, with joint
abstentions and identity-matched pairs beside it (also over all 24); Q5 prints the fetch's CPU and
separates the whole probe unit's CPU from its evaluation's; the plan states that the seed confound
is acceptable for this question and that S's base class is a prototype output. In correction 2,
the origin of the report's 12 is now labelled an inference (a wording change in the same round,
before the correction was cited by SHA-256; its numbers are unchanged).

**Stated, not removed:** the CPU estimate. With the runner's conservative estimates, all possible
probes could pass the 8 CPU-h cap; the run would then stop at the cap, with the changes admitted
first and each question marked only if complete. The cap is not raised.

Because the round returned REFUTED, a second round in the same conversation reviews these
changes (the decision, item 3).

## The prototype, before the run: round 2

The same conversation (thread `01a20a4f-3ec2-7cb2-8a0a-5990041bd6d7`) reviewed `97be424f`. Codex CLI
0.167.0-alpha.3.2, model gpt-6.2-sol, effort high. The answer is stored unchanged.

| Round | File | Verdicts | SHA-256 |
|---|---|---|---|
| 2 | [prototype-round-2-answer.md](prototype-round-2-answer.md) | round 1's item 1 RESOLVED; items 2, 3, 5, 6 PARTLY; item 4 NOT RESOLVED; six blocking items; **OVERALL: REFUTED** | `234ef454d69aee8746ef925ec28255828e6a4814b20cfbff51c7c5b4da5e7864` |

The round used 7,030,085 input tokens (6,633,856 cached) and 34,224 output tokens: **430,453**
review tokens. The two rounds on the prototype together: **803,456** review tokens.

**What Codex confirmed:** the refit window, the shared box membership and the declared probe
offsets; that Windows `spawn` initializes the worker and returns a record; that the fixes can stay
in the prototype; the disclosure of the CPU risk; correction 2's inference label.

**Applied, all six blocking items, in the prototype only (commit D):**
1. **Downloads during the transfer.** The supervisor reads the TOI's new bytes on disk every
   second (cache hits excluded, vanished partial files at their largest size) and ends the worker
   at its allowance; the worker's own meter no longer counts cache hits; a charge over 15 GB ends
   every worker. Tested offline (an oversized product, a cache hit, a vanished partial file).
2. **A parent-owned supervisor.** The interrupt watchdog is gone. Each unit is its own process,
   one thread, with a CPU allowance enforced by the supervisor and by the worker itself (it ends
   its own process past it). One charge serves admission, supervision and settlement; an
   unreadable reading is bounded by the wall time; a supervisor failure ends and settles every
   worker and stops the run; the caps are checked again after every drain. Tested with real
   worker processes (`selftest` units): normal settlement, a unit past its CPU allowance, and
   every worker stopped at the CPU cap.
3. **Durable settlement.** Every dispatch is journaled before its process starts; the record,
   then the charge, are written before it leaves the journal; recovery is idempotent, refuses a
   worker of an earlier batch still alive (PID and creation time), adopts a result file, or
   charges the whole allowances. The fingerprints (now with every file under `src/`,
   `pyproject.toml` and `uv.lock`) are pinned before the first dispatch; the manifest is parsed
   from the exact bytes whose SHA-256 was checked.
4. **Resource stops out of the scientific counts.** The report has its own structural-validity
   field; a unit ended by a resource stop makes its TOI incomplete (its questions are not marked)
   and makes a consensus `INCOMPLETE`, never a demotion; its cost stays in Q5. The plan's
   counting rule was updated before any result.
5. **The symmetry tolerance** is relative to the matrix itself, checked before Cholesky, and
   tested at both scales.
6. **The destinations.** Every configured cache root (including the cache folders the runner
   sets) is refused if it is a link, before any folder is created; `verify-archive` needs a
   distinct copy under the approved archive root and records the destination and both hashes;
   `clean` refuses while staged records lack a matching receipt.

**Not reviewed by a third round.** The decision authorizes a second round when the first returns
REFUTED; it does not authorize a third. Codex's last verdict on record is therefore **REFUTED**, on
the code before commit D. By the rule of the most conservative option, the run is not proposed as
reviewed: whether a third round reviews commit D before the run is the maintainer's decision.

## The prototype, before the run: round 3 (short)

The maintainer's decision of 2026-11-24 (#218, comment 7122240195), item 1: one short round in the
same conversation on `521fcff`, limited to (a) whether each of round 2's six blocking items was
resolved as asked and (b) whether the fixes introduced a regression or a new block on the run's
path. **No block: the run is approved by the posted procedure. A block: fix it, record it, STOP
before running.** Codex CLI 0.167.0-alpha.3.2, model gpt-6.2-sol, effort high. Prompt and answer
stored unchanged.

| Round | File | Verdicts | SHA-256 |
|---|---|---|---|
| 3 | [prototype-round-3-prompt.md](prototype-round-3-prompt.md) | the short prompt | `99c64c20d76f0d1a29d43b5e320627af7401433d3006ee12409ec2328812d989` |
| 3 | [prototype-round-3-answer.md](prototype-round-3-answer.md) | round 2's item 5 RESOLVED, items 1, 2, 3, 4, 6 NOT RESOLVED; **BLOCKS: 5** | `c687c3cb8f96a620db419e113ebcadd0e93ed787f3d8049d62f0871d12fe0205` |

The round used 9,077,403 input tokens (8,389,120 cached) and 39,388 output tokens: **727,671**
review tokens. The three rounds on the prototype together: **1,531,127** review tokens.

**The five blocks, applied in the prototype only (the commit after `d347783`):**
1. **A settled charge counts at once.** Every settlement refreshes the live charge before another
   unit is admitted. Test: a second unit that would pass the cap after the first settles is not
   admitted.
2. **The limits are enforced before they are passed.**
   - Downloads: every HTTP body chunk read through `requests` (`Response.iter_content`) is
     counted, retries and partial transfers included; a chunk past the allowance is refused
     before it is written, the unit ends `DOWNLOAD_ALLOWANCE` and is never retried. The file
     snapshot and the product meter stay as second checks.
   - CPU: each worker is placed in a Windows job whose kernel ends it once its user CPU passes its
     allowance, and ends it when the controller's job handle closes (no orphan can keep working).
   - The settlement includes startup and the end: the worker's process-wide CPU, and the final
     reading by its process handle.
   - Disk: bounded by the download allowances reserved at admission, which the stream now
     enforces.
3. **An interrupted launch.** A worker waits at a start gate until its identity is journaled and
   its job holds it; recovery settles a journal entry without a PID as a dispatch that did no work
   (charged a startup bound of 60 CPU-s), and the unit runs again within the approved run.
4. **A stop never discards a result.** Every end (normal, an allowance, a cap, a supervisor
   failure) confirms the worker's exit, prefers any valid result it wrote for that attempt, writes
   a stop record only when there is none, and drops the worker from the running set only after
   its settlement is durable.
5. **The report:** the descriptive all-24 summary counts only complete pairs and states the
   incomplete count; Q1 to Q4 keep their withholding rule.

**The non-blocking item** (the archive receipt bound to the current staged records) is applied too
(`clean` checks the receipt against the staged file's and the bundle's SHA-256) and recorded on
#59, with no further round.

Tests: `tests/v059`, JUnit 37 passed, 0 failed, 0 errors, 0 skipped (with real worker processes,
the kernel's CPU limit and the stream limit). **By the decision, the work stops here, before the
run:** these fixes have not been reviewed by Codex.

## After the run: one round on the report and the specification

The maintainer's decision of 2026-11-24, received at 05:07 local (#218, comment 7125778250):
- item 1: no round 4 on the code; `331ca03` ran unreviewed, and a pilot checked its accounting;
- item 3: one round on the report and the version-5 specification together.

The round ran in the same conversation (thread `01a20a4f-3ec2-7cb2-8a0a-5990041bd6d7`) on
`cc282b8d`: Codex CLI 0.167.0-alpha.3.2, model gpt-6.2-sol, effort high. Prompt and answer are
stored unchanged.

| Round | File | Verdicts | SHA-256 |
|---|---|---|---|
| review | [review-round-prompt.md](review-round-prompt.md) | the prompt | `61a3fc182577de36e1b9f955ed2755dcd89abfc1f1bd2b7f710a0eea9bd0c73a` |
| review | [review-round-answer.md](review-round-answer.md) | blocking items 3, 6, 7 ANSWERED; 1, 2, 4, 5 PARTLY; **BLOCKS: 8; OVERALL: REFUTED** | `b9e55b7883e86c501800aaf0d2f337a31968cf5750002da5eb3c41e852137bf5` |

- **Tokens:** 12,829,299 input (11,789,440 cached) and 53,670 output, so **1,093,529** review
  tokens.
- **All rounds of this conversation on v0.5.9,** the design round excluded: **2,624,656**
  review tokens.

**What Codex reproduced:**
- the per-TOI table, Q1 to Q5 and the costs;
- the pilot's three differences;
- all 252 unit hashes;
- that the pinned files equal `331ca03`;
- every one of the 82 zero-coverage results is INCONCLUSIVE.

**The eight blocks, all applied** in the commit after `cc282b8`, each in its most conservative
form. The counts of block 6 and the power of block 7 were checked by
`check_codex4.py`, which ran from `.cache/v059/tools/` and is committed, with the same output, as
[docs/validation/v0.5.9/check_codex4.py](../../validation/v0.5.9/check_codex4.py) (the gate
review, finding 5).
1. **The pilot's scope.** It was three batches (3 fetches, 6 bases and 18 probes), and it checked
   only that the accounting agrees under the observed load. No cap or allowance was reached.
2. **Q3.** Three of the four bases triggered the guard. TOI-734.01 E was INCONCLUSIVE from sector
   heterogeneity (82,558 cadences, p = 1.6×10⁻³³), and all 12 of its probes triggered the guard.
   The run did not reproduce v0.5.8's original failures.
3. **The post-hoc observations.** They give a class pattern with no cause:
   - byte identity with v0.5.6 is unknown for 4 of the 13;
   - 8 of the 10 first disagreements were on epoch probes, in a fixed order;
   - 6 of the 10 crossed the background threshold;
   - `aperture_depth` alone determined TOI-399.01 S/p2's REFUTED.
4. **The screen's semantics.** An explicit rule for when a test is assessed, a sensitivity
   refusal counting as not assessed; screen-only tests kept out of `aggregate`; configured roles
   kept; the consensus named as a rule change that needs a blind review.
5. **E's pre-fit grid,** defined from the frozen inputs and the raw span (with its one coarsening
   case), and separated from the probe offsets of the final fit.
6. **The paired endpoint.** It is now "decided on the catalog signal". With that rule the
   prototype gives 6 flips in 16 informative pairs before consensus and 1 in 9 after; the 10 of
   20 and 4 of 12 were raw comparisons. Yield uses the identity-qualified rates and cost the raw
   ones.
7. **Fixed-draw sizing.** It now has n_min, the decision-floor denominator and consequence, and
   the criteria that block the lock. The "400 or more" requirement is removed: 320 pairs give a
   conditional power of 0.916 at f = 0.05.
8. **The historical baseline.** It is now 24 of 100 decidable, and 23 of 100 retained.

**Non-blocking:**
- Applied: the report links to the script's full intervals and per-axis breakdown, and the
  specification states that the route (e) and (d1) gates remain open.
- Recorded on #59.

**No further round.** The rule is one round for exploratory work, and the decision asked for one.
The applied fixes are not reviewed by Codex. Where the answer and the drafts disagreed, the drafts
took Codex's more conservative wording.
