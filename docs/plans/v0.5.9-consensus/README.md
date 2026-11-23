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
