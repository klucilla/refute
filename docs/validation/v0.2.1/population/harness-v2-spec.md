# Population harness v2 and Amendment 4: specification

Status: 2026-10-13, **revision 6** (the basis of the v2 implementation). Revision 6 records
in section 8.2 the machine qualification of 2026-10-12 and 2026-10-13: the MemTest86 result,
the criterion changed by the maintainer after seeing it, the corrective action, the residual
risk, the invalidation conditions and the result. Revision 2 incorporated the
maintainer's decisions; revision 3 applied the review of revision 2 by Codex
(`codex-spec-review.md`) and the decision that the campaign runs only on the current machine;
revision 4 applied the review of revision 3 (`codex-spec-review-2.md`) and the maintainer's
decisions on the budget, the localization concession and the machine qualification;
revision 5 closes the three blocking points of the review of revision 4
(`codex-spec-review-3.md`: B1 comparator profiles, B2 in `D6-proposta.md`, B3 the last set of
a chain) and its four non-blocking points. Revision 6 is the one implemented by
`population/population_v2.py`, `population/population_compare.py` and `population/d6.py`
(Amendment 4 of `population-study.md`).

It follows the generation divergence of 2026-10-12 (`D7-relatorio.md`, `D7-errata.md`,
`codex-D7.md`). The cause of the divergence is **unknown**; this specification does not claim
to remove it. It specifies how a divergence is detected, located, preserved and blocked, and
how a campaign proceeds without choosing a result after seeing it.

Scope: a new harness file (proposed name `docs/validation/v0.2.1/population/population_v2.py`)
and Amendment 4 of `population-study.md`. The v1 harness (`population.py`, SHA-256
`408020676340322f4728ce3a8b4eecae505bfbec7ec34643ad9afed0e5a76225`) stays as it is; its
generations (A, B and the diagnostic runs) remain recorded as diagnostics.

## 0. What Amendment 4 replaces, keeps and extends

| Earlier text | Amendment 4 |
|---|---|
| Amendment 1, item a: "It runs twice, in separate processes; the two manifests must be identical byte for byte." | **Replaced** by the K = 3, N = 3 rule of section 8 (and the blocking comparisons there). "The manifest is then committed and frozen. Only after that do M0 and the other points begin." is **kept**. "The expected hash is never updated ... no case is removed" is **kept** and extended by section 15. |
| Amendment 1, item b (serialization) | **Kept**: the case bytes do not change (section 3). |
| Amendment 1, item c (frozen generation environment at tag v0.2.0; the manifest records the environment and the thread pools) | **Environment kept**: the generator runs only in the environment of the v0.2.0 worktree. **Where it is recorded changes**: the Python, NumPy, BLAS, thread variables, thread pools and random-generator fields move from the manifest to the execution record of each generation (section 2), so that the K scientific manifests of a set can be identical; v2 adds the machine record and the dispatch check (sections 5, 8.1). |
| Amendment 1, item d (lots) | **Extended**: every lot is analyzed in two slots (section 9). |
| Amendment 2, C3 (a divergent input hash stops the run) | **Kept**, and a divergence now also writes a lock (section 7). |
| Amendment 2, N10 (infrastructure failures may be resumed) | **Restricted** (sections 8.5 and 12): an observed divergence is never an infrastructure failure; and, in **generation**, an interrupted generation, even by an infrastructure failure, is never resumed: its set is incomplete and consumed. Resumption after an infrastructure failure remains only for analysis, per slot. |
| Amendment 3, R1 (when a lot is finished) | **Extended** to two slots and the completed comparison (section 12). |
| Amendment 3, R2 (committed harness) | **Extended** to the v2 harness and to the frozen comparator (section 12). |
| Amendment 3, N-c (no edit of the branch during generation and measurement) | **Kept**, with one declared exception: the manual, approved commits of locks and resolutions (section 7). |
| Protocol section 9 (a new confirmation needs a new future drand round) | **Restated** in section 16. |
| Protocol section 10 (where results go) | **Adjusted** by section 14. |

## 1. Identity, eligibility and origin

Identity is split in two, so that the scientific artifacts of the K generations of a set can
be byte-identical:

- **Common identity**, carried by the **scientific artifacts** (the scientific manifest and the
  block index) and by nothing that varies between generations: `campaign_id`,
  `campaign_declaration_sha256` (the SHA-256 of the committed campaign declaration,
  section 8.3), the chain (`development` or `confirmation`) and `set` (1..N). The scientific
  artifacts carry **no** generation number, execution identifier, attempt, eligibility or
  origin.
- **Execution identity**, carried by every **execution artifact** (execution record, case
  result, attempt record, comparison report, lock marker, journal entry, resolution record,
  metrics, report): the common identity; `generation` (1..K) for generation executions;
  `point`, `lot` and `slot` (1 or 2) for analysis executions; `execution_id` (a new identifier
  per process start); `attempt`; `eligibility` (`campaign` or `diagnostic`); `origin` (the mode
  and the harness, by SHA-256 and HEAD commit). A generation's execution record points to the
  SHA-256 of the scientific manifest and of the block index it produced; that pointer is what
  ties a scientific artifact to its executions.

**Eligibility is never granted by a path.** A campaign mode accepts a scientific artifact as
evidence only if its common identity names the campaign and declaration hash, and K
execution records of the campaign, each with `eligibility` `campaign` and an `execution_id`
started and closed in the campaign journal (section 7), point to its SHA-256. It accepts an
execution artifact only if its execution identity names the campaign, its `eligibility` is
`campaign`, and its `execution_id` is started and closed in the journal. Renaming, moving or
copying files does not change their identity; a `diagnostic` artifact is never accepted, and
**a diagnostic can never be promoted to evidence for approval**, wherever it is.

**Diagnostics** (a `diagnose` mode or separate scripts, as in `.cache/population/diag/`) write
only `diagnostic` artifacts, in directories outside every campaign, may read campaign files,
and never write into a campaign's directories, journal, records or locks.

**Campaign chain.** There are two chains, `development` and `confirmation`. A campaign
declaration names its chain, its predecessor in that chain (campaign id, declaration hash,
and the hash of the resolution or block that ended it) and the sets the chain has already
consumed (section 8.5). A new campaign never resets its chain's counter. The development
chain starts with the v1 generations, recorded as a diagnostic predecessor that consumes no
set.

## 2. Scientific manifest and execution records

Two kinds of output per generation, kept apart:

- the **scientific manifest** (`refute-population-manifest/2`): only what must be identical
  between the K generations of a set: format, serialization, population, harness SHA-256,
  generator commit and `synthetic.py` SHA-256, thresholds, call sequence, the common identity
  (section 1), every case entry (section 3), and the SHA-256 of the block index. It holds no
  generation number, execution identifier, attempt, worker count, order, PID, time, path or
  per-execution configuration;
- the **execution record** (`refute-population-execution/1`), one per generation: the
  execution identity (section 1: generation, execution id, attempt, eligibility, origin), the
  configuration of that execution (workers, order, affinity, environment, thread variables and
  pools, effective dispatch of the main process and of every worker, section 5; the machine
  record of section 8.1), timings, **the SHA-256 of the scientific manifest and of the block
  index it produced**, and the operational data per case.

The K manifests of a set must be byte-identical; their execution records differ by design.

## 3. Hashes by segment and by block of the final blob; layout

**Layout.** The serialization stays `refute-population-serialization/1` (the same bytes as v1).
A blob is the concatenation, without gaps, of the segments `magic` (offset 0), `header_length`
(8 bytes), `header` (the header JSON) and each array in the order of the header's `arrays`
list.

**Per case** (manifest entry):

- `sha256` of the whole blob (as v1);
- `layout`: the header length and, per segment in blob order, `{name, dtype, shape, offset,
  length, sha256}`; every hash is computed over the slice of the **final blob** (a
  `memoryview` of the `bytes` object hashed as a whole), never over arrays before
  serialization;
- enforced coverage: offsets start at 0, each segment starts where the previous one ended, and
  the last ends at `len(blob)`; a gap, overlap or remainder is an integrity error.

**Block index** (a separate scientific file per generation, carrying only the common identity,
its SHA-256 recorded in the manifest): for every segment, the SHA-256 of each block of 1 MiB
(2^20 bytes, counted from the segment's start; the last block may be shorter). The segments
(`magic`, `header_length`, `header` and every array) and their blocks cover **every byte of
the blob, the header and the length field included, without gaps**. The bytes of whole
generations are **not retained**.

**Localization concession (accepted by the maintainer for this stage).**

- A divergence is **detected** by the hashes (whole blob, segments, blocks).
- Without the original bytes, the localization **may end at the block**: one segment and one
  block of at most 1 MiB.
- It will **not necessarily be possible** to determine the element, the bits changed or the
  numerical magnitude of the difference.
- A later regeneration does **not** recover the original occurrence; regenerated bytes are a
  new observation, never a capture of the earlier one.
- The tests with deliberately injected differences (section 17) validate the locator **in the
  conditions tested**; they do not demonstrate the capture of every transient failure.
- The figure of about 1.2 TB is what keeping three whole generations would take; it does not
  mean that every capture strategy needs that space. The concession is a choice for this
  stage, not a statement that capture is impossible.

**Double hash.** The whole-blob SHA-256 is computed twice, with two fresh `hashlib` objects,
over the same `bytes` object; unequal digests are an integrity error. It is kept as a
**detector of transient errors in the calculation**, and declared as **not independent** for
systematic defects (same implementation, same buffer, same process). Independent verification
of the hash implementation is a separate offline check (as T3b: `hashlib` against PowerShell
`Get-FileHash` on the same bytes).

**Interpretation** of a divergence: unequal double digests in one process point to the hash
path, memory or registration; equal double digests but different between generations mean
the bytes differ or an error common to both calls (localize by segment and block); a header
difference is a metadata divergence; equal segments with a different whole hash point to
composition, hash or registration.

## 4. Overhead per generation (fixed before the campaign is frozen)

- **Limit:** one v2 generation may take at most 25 % more time than one v1 generation of the
  same population on the same machine, workers and order. This limits the **overhead per
  generation**; it does not limit the total cost of the campaign, which also grows with K = 3
  generations per set instead of two.
- **Measurement, declared before the freeze:** a measurement population with the prefix
  `refute-v0.2.1-population-determinism`, stratified like the development population (the
  same mix of classes, bands, noise models and mechanisms, at 10 % of its size: 520 cases),
  generated hash-only on this machine, 24 workers, index order; six runs alternating v1 and v2
  (v1, v2, v1, v2, v1, v2), each in a new process. Overhead = median(v2) / median(v1) − 1.
- **Margin:** accepted if the overhead is at most **20 %** (5 points of margin for measurement
  noise). Otherwise the double hash is removed first, as a new harness version, and the
  measurement is repeated; if still above 20 %, the result is reported to the maintainer
  before any campaign.
- The decision to keep or remove the double hash is taken and recorded **before** the campaign
  declaration is committed; it never changes during a campaign.

## 5. Dispatch: closed inventory and runtime check

- The campaign declaration holds the **closed inventory** of NumPy dispatch: the full table
  returned by `numpy.lib.introspect.opt_func_info()` (every function and signature with its
  `current` target) expected in the declared environment, and the declared target (for
  example `baseline(X86_V2)` with `NPY_DISABLE_CPU_FEATURES=X86_V3`, or `X86_V3`).
- In the main process and **in every worker**, before the first case, the harness reads the
  effective table, records it in the execution record, and **aborts** (an integrity error,
  recorded) if any entry differs from the declared table, is missing, or cannot be read.
- Reason: NumPy silently ignores dispatch names it does not know (on numpy 2.5.3,
  `NPY_DISABLE_CPU_FEATURES=X86_V3` works; `AVX2 FMA3` and `AVX512F` are ignored without a
  warning; `.cache/population/diag/t3c-log.txt`).
- **Limit, declared:** `opt_func_info` reports the dispatch **target** of NumPy's dispatched
  loops; it does **not** certify the execution path: non-dispatched NumPy code, OpenBLAS,
  SciPy, Astropy and other compiled code are not covered. (On this machine, on one fixed input
  set, `sin`, `exp`, `add` and `multiply` were bit-identical under X86_V3 and X86_V2; that does
  not show it for other inputs or machines.)

## 6. Cache: no silent replacement

When a case is written to the cache and a file already exists at its path, the existing file
is read and hashed: equal bytes are kept (not rewritten); different bytes are an integrity
event: the existing file is left untouched, the new bytes are written beside it under a name
that carries their hash (`<case>.<sha256>.rpc`), the divergence is recorded and the execution
ends (section 7). No path in the cache is ever replaced by `os.replace` over a different
existing file.

## 7. Journal, lock marker and verifiable closure

- **Campaign journal.** Each campaign has an append-only journal at a fixed location derived
  from its `campaign_id`, in the harness's repository
  (`docs/validation/v0.2.1/population/campaigns/<campaign_id>/journal.jsonl`), independent of
  the run directories used. Every entry carries the execution identity (section 1) and the
  SHA-256 of the previous entry (a hash chain). Entries: `started` (written **before the first dispatch**,
  with the PIDs the execution will start as they start), `closed` (every process of the
  execution has ended, verified by its recorded PIDs), `interrupted`, `divergence`.
- **Lock marker at detection.** At the instant a divergence is detected (generation, cache,
  input hash, analysis slots, metrics reconciliation), the harness writes a durable local lock
  marker **keyed by the campaign identity** (in the campaign's directory, with the campaign id,
  declaration hash, unit, evidence paths and hashes, and the budget consumed) and a
  `divergence` journal entry, then ends the execution: no further case is dispatched and it
  waits for every process it started to stop, then writes `closed`.
- **Refusal.** Every campaign mode looks up locks **by campaign id** (the campaign directory
  and the journal), not by the run directory, and refuses to run while a lock marker exists, or
  while the journal holds a `divergence` without a committed resolution, or a `started`
  execution without `closed` (an unreconciled execution).
- **Verifiable closure before any acceptance.** No set, lot or campaign is accepted while any
  execution of the campaign lacks a verified `closed` entry; an execution whose processes
  cannot be shown to have ended stays unreconciled and blocks, until the maintainer records a
  reconciliation (which classifies it as interrupted and consumes budget as in section 8.5).
- **Commit: always manual.** The harness never runs git. Committing a lock marker and its
  journal entries is a **manual step approved by the maintainer**, done after every process
  has stopped and before any other action on the campaign; this is the declared exception to
  N-c (section 12). Until that commit, the local marker and the journal already block every
  campaign mode. A lock is lifted only by a committed resolution record that names the lock by
  its hash and applies a rule registered before the campaign; deleting a marker is not a
  resolution, and the harness checks the git history of the campaign directory for one.
- **Accepted risk, not resolved.** Between the detection and the manual commit, the local
  marker and the journal exist only on disk and could be deleted or altered by hand; only the
  commit makes such an action visible. The house rules forbid automatic git, so this window
  cannot be closed by the harness. It is an **accepted risk, declared, not a resolved one**,
  and every report of the campaign repeats it.

## 8. Generation rule (Amendment 4, decided by the maintainer)

### 8.1 Machine record (in every execution record)

Python, NumPy and scipy-openblas versions and builds (wheel hashes from the v0.2.0
worktree's `uv.lock`); thread variables and pools; affinity; operating system and version
and the C runtime / math library used by NumPy's baseline loops (on Windows, the UCRT
version); CPU model and **microcode revision**; whether the memory has ECC; the **BIOS**
version and the CPU and memory settings; and the **state and profile of the motherboard tuning
software** (EasyTune on this machine), which can change the CPU's behaviour from Windows.

### 8.2 Machine qualification (prerequisite of the campaign on this machine)

The campaign runs **only on the current machine** (AMD Ryzen 9 5900XT, section 8.4). Its
qualification is a **prerequisite**: no generation of a new campaign starts unless the
qualification's result is PASS. The criteria below are fixed **before** any qualification
test runs.

**Run by the maintainer**, each recorded with date, tool version, configuration, duration and
result:

- **MemTest86:** at least **4 full passes** of the declared test set; all testable RAM, with
  the coverage recorded; the parallel mode the machine supports; **zero errors**. A reduced
  first pass does not count as a full pass.
- **y-cruncher:** version and configuration fixed before the run; an explicit list of the
  compatible components selected; at least **4 effective hours**, with every component
  completing at least one cycle; **zero** verification errors, hangs or unexpected restarts.
  The four hours are a requirement of the project, not a certification by the tool's author.

**Complementary evidence:** the three reference cases with their full expected SHA-256
(section 17); the observed dispatch equal to the declared one for each variant (section 5);
D6 passed, its negative controls included (`D6-proposta.md`); the BIOS, microcode, memory
configuration, CPU tuning and EasyTune state recorded (section 8.1).

**Scope.** The tests qualify the configuration that will be used in the study. A relevant
later change (BIOS, microcode, memory, CPU tuning, EasyTune profile, operating system, NumPy
build) invalidates the qualification until a new one passes.

**Result:**

- **PASS**: every requirement executed and met. Only PASS allows a campaign to start.
- **FAIL**: an error or instability observed. The machine is not qualified.
- **INCOMPLETE**: an external interruption, or a requirement not executed. The machine is not
  qualified; INCOMPLETE does not prove a hardware defect.

**Requalification.** An INCOMPLETE qualification may be redone, always **from the start and
in full**, never by completing only what was missing. After a FAIL, a new qualification is
valid only with an identified cause and a documented corrective action; repeating without a
change does not count. **Every qualification attempt, the failed ones included, is recorded
and published.**

**Qualification of 2026-10-12 and 2026-10-13 (recorded in revision 6).**

- **y-cruncher, attempt 1 (2026-10-12): FAIL.** Version 0.8.7 Build 9547 (binary
  `19-ZN2 ~ Kagari`), configuration file `qualificacao-refute.cfg`: `StressTest`,
  `AllocateLocally` true, logical cores 0 to 31, 41768774400 bytes, 120 s per test,
  15000 s in total, `StopOnError` true, tests BKT, BBP, SFTv4, SNT, SVT, FFTv4, N63, VT3. One
  verification error in N63 on logical core 8 (`ConvolutionFailedException: Coefficient is
  too large`), with no hardware event in the Windows log.
- **Diagnostic (2026-10-12)**, not a qualification attempt: N63 alone, 32 threads, about one
  hour, Stop on Error off: 29 of 29 iterations without error. It does not cancel the FAIL and
  does not identify the component.
- **MemTest86 (2026-10-12 to 2026-10-13)**: 4 passes, about 12 hours, memory at 2666 MHz and
  1.20 V (the daily configuration). Tests 0 to 10 without errors. Test 13 (Hammer) failed in
  the 4 passes: 26 errors, all at the same physical address `0x8C7CBD968` (about 35 GiB) and in
  the same bit, always from 1 to 0, also at the slow rate. Interpretation: a weak DRAM cell,
  sensitive to row hammer, in one of the 4 modules; it is the **probable** cause of the three
  generation divergences (A, two cases; C, one case) and of the y-cruncher error of attempt 1
  (an isolated, rare and silent bit, with no WHEA event on memory without ECC). It is **not
  demonstrated**: no divergent byte was captured.
- **Corrective action:** the physical page `0x8C7CBD` (4 KiB) is excluded from use by Windows
  (BCD `badmemorylist`). No module was removed or replaced.
- **MemTest86 criterion, changed by the maintainer after seeing the result, and recorded as
  such:** the run of 2026-10-12 to 13 is accepted, because tests 0 to 10 had no errors and
  every error of test 13 was confined to a single address, whose page is excluded. Reason:
  the exclusion holds only inside Windows, and MemTest86 runs outside it. Under the criterion
  written before the tests (zero errors), this MemTest86 run would have been a FAIL.
- **Residual risk, declared:** the module is still defective and may have other weak cells
  that were not detected; the exclusion holds only while the memory configuration and the BCD
  do not change. The protections of the study (K = 3 in generation, two slots in analysis)
  turn an error of this kind into a block, not into an accepted result.
- **The qualification is invalidated** if any later test shows an error at another address,
  or if the memory, the BIOS or the `badmemorylist` entry changes (besides the changes listed
  under "Scope" above).
- **y-cruncher, attempt 2 (2026-10-13, about 04:27 to 08:40): PASS.** Version 0.8.7 Build
  9547, configured by hand (the program did not find the `.cfg` file): 32 logical cores,
  45.8 GiB (1.43 GiB per thread), NUMA local, 120 s per test, 15000 s in total, Stop on Error
  on, the 8 tests. 15 complete cycles (iterations 0 to 14) with the 8 tests passed, iteration
  15 ended by the 15000 s limit, zero errors, no hang and no restart.
- **State: the machine is QUALIFIED, under the conditions above.** The cause of attempt 1
  remains probable, not demonstrated. The complementary evidence (reference cases, dispatch,
  D6) belongs to the revalidation of v2 (section 17).

Even after a PASS, the cause of the earlier divergences is **not demonstrated**.

### 8.3 Campaign declaration (committed before the first set)

The campaign id, its chain, its predecessor and the sets the chain has consumed (sections 1
and 8.5); the population and seeds; the harness (SHA-256) and the comparator (**SHA-256**,
version and schema, the three profiles of section 11 and their exclusion lists included); the K
generation
configurations; the closed dispatch inventory; the analysis slots and permutations
(section 9); the investigation and eligibility rules (sections 9 and 10); the overhead
decision (section 4); the reference to the PASS qualification record (section 8.2).

### 8.4 Campaign on the current machine: K = 3, N = 3 (decided by the maintainer)

- The campaign runs on the current machine only; running it on another machine is not part
  of the plan.
- A **set** is K = 3 generations of the whole population, each in
  a new main process with new workers, with configurations declared in 8.3 (proposed: 24
  workers in index order; 12 workers in a declared shuffled order; 24 workers in another
  declared shuffled order). A set is complete when its three scientific manifests and block
  indexes are byte-identical.
- The **first complete set** is a candidate; it is accepted only if every execution of the
  campaign is closed (section 7) and the blocking comparisons find nothing. Its manifest is
  then committed and frozen. Cases or executions of different sets are **never combined**.
- **Blocking comparisons (they can only block, never approve):**
  - with the other sets of the campaign: if the candidate differs, in any case, from a value
    that appeared in 2 or more generations of another set of the campaign, the campaign is
    blocked;
  - with the previous campaign, **for the development population only**: every case's
    whole-blob `sha256` is compared with the value repeated in the v1 generations, manifest B
    (`4073d96a0bce901a31241d5c2dd3d7b46192a4731a4ec3996ea1077039b833e9`, the value of B, A2,
    A3, B2 and D); any difference blocks until investigated. (Other populations, such as the
    confirmation, use other seeds and have no such reference.)
- When N is exhausted without an accepted set (section 8.5, the last set), the campaign is
  blocked and another execution condition is sought, as a new campaign in the same chain,
  within the chain's ceiling (section 8.5).

### 8.5 Budget (decided by the maintainer)

- **K = 3** generations per set; **N = 3** sets per campaign.
- **Global ceilings:** at most **6 sets** in the development chain, and a separate ceiling of
  **6 sets** in the confirmation chain. A campaign may use at most the smaller of N and what
  is left of its chain's ceiling.
- Changing the harness, the environment, the machine or the drand round does **not** reset the
  counter of the chain concerned.
- A set **consumes** budget when its first generation starts (`started`), including when it
  ends interrupted (an infrastructure failure, N10, included) or divergent. A generation
  interrupted for any reason leaves its set incomplete and consumed: it is never completed by
  another generation, and it is preserved whole.
- A set with a divergence is preserved whole, the campaign is locked, and the next set starts
  only after a committed resolution, with no silent change of parameters or seeds.
- Diagnostics can never be promoted to evidence for approval (section 1). The earlier
  generations (A, B, A2, A3, B2, C, D and the D2 runs) are diagnostics of the v1 predecessor:
  they consume no set, do not count toward K and are never approved retroactively.
- **Exhaustion and the last set (decided by the maintainer).** Reaching the ceiling only
  prevents **new** sets from starting; it does not affect a set that has already started.
  The sixth set of a chain (the last one allowed) is handled like any other: if it is
  **complete, unanimous** (K identical generations) **and unblocked** (every execution closed,
  the blocking comparisons of section 8.4 find nothing, no lock), it is **accepted normally**.
  If it is incomplete or divergent, the chain is **blocked and its result is published**
  (section 13, integrity-failure report). The same applies when a campaign's own N is reached
  before the chain's ceiling: no new set starts in that campaign, and a set already started is
  judged on its own.
- The ceiling is **never raised after the failures are seen**.
- The number 6 is a decision of **cost and governance**, with **no statistical guarantee**
  attached to it.
- This budget applies **only to generation**. It does **not** authorize repeating analysis
  lots until they agree (section 9).
- A software correction or a change of environment opens a **new campaign** in the same chain,
  justified in writing, preserving the previous one.

## 9. Analysis rule (Amendment 4)

- Every lot is analyzed at every point in **two slots**, each an independent execution (new
  main process and new workers), on the same inputs verified by hash before each execution.
- The two slots use **the same configuration** (workers, affinity, environment) and differ
  **only in the order of the cases**: slot 1 and slot 2 each have a permutation of the
  population **frozen in the campaign declaration**; a lot's cases are dispatched in the
  order their slot's permutation gives them. Dependence on the number of workers is left to D6.
- **Resumption per slot.** An interrupted slot (infrastructure only, section 12) resumes only
  its own remaining cases, in the relative order of its own permutation; the effective
  sequence (PID, position, case) of every execution is recorded. A result **never migrates**
  between slots, and a missing case of one slot is never filled from the other.
- The two complete scientific records (section 10) of every case and condition are compared
  with the frozen comparator (section 11). A divergence: the execution ends, both results are
  preserved, a lock is written (section 7), the lot and the final approval are blocked, and the
  divergence is investigated. Additional executions are diagnostics only and never elect a
  winner by majority; there is **no automatic repetition until agreement**.
- **Resuming after an investigation:** resumption requires a report that identifies the cause
  or declares it unknown, delimits the scope affected and applies an eligibility rule
  registered in the campaign declaration; without a demonstrated cause and an applicable rule,
  the unit stays blocked. A cause demonstrated under an unchanged procedure can invalidate an
  observation only by objective evidence covered by the declared rule, never because it
  disagrees. A correction of code, environment or procedure is a new version and a new
  campaign. A rule that appears only during the investigation may govern a new campaign, with
  that limitation declared, and never legitimizes the old one.
- Cost: the analysis CPU time doubles (from about 6 to 7 hours to about 12 to 14 hours for M0 to
  M3 on this machine; to be measured).

## 10. Complete scientific record and integrity envelope

**Scientific record** (`refute-population-result/3`), per case, condition and slot: the
**complete** output of `refute.packs.tess.pipeline.build_result` of the code being measured
(present at all four points): `verdict`, `verdict_reason`, `candidate`, `global_ephemeris`,
`period_comparison`, every test with `status`, `severity`, `message`, `metrics`, `thresholds`,
`inputs`, `coverage`, `coverage_unit`; `holdout_rounds`, `search_diagnostics`,
`data_summary`, `key_values`, `data_quality_warnings`, `eb_catalog_configured`,
`expected_tests`, `test_plan`; plus the harness's own outcomes (signal identity and factor,
the verdict without `eb_catalog`).

**Integrity envelope** around it. A result record has exactly these top-level members (JSON
Pointer paths, RFC 6901):

| Path | Content |
|---|---|
| `/format` | `refute-population-result/3` |
| `/identity` | the execution identity (section 1): `/identity/campaign_id`, `/identity/campaign_declaration_sha256`, `/identity/chain`, `/identity/set` (the set of the frozen manifest analyzed), `/identity/point`, `/identity/lot`, `/identity/slot`, `/identity/execution_id`, `/identity/attempt`, `/identity/eligibility`, `/identity/origin/mode`, `/identity/origin/harness_sha256`, `/identity/origin/harness_commit` |
| `/case` | the case id |
| `/input` | `/input/sha256` (bytes read) and `/input/manifest_entry_sha256` |
| `/status` | `analyzed`, `error` or `missing` |
| `/traceback` | present only with `error` |
| `/conditions` | `/conditions/i` and, except for cases without transit, `/conditions/ii`; each holds `/scientific` (the typed `build_result`) and `/harness_outcomes` (signal identity, its factor, the verdict without `eb_catalog`) |
| `/configuration` | `/configuration/thread_env`, `/configuration/threadpools`, `/configuration/dispatch_table_sha256` |
| `/operational` | `/operational/pid`, `/operational/seconds`, `/operational/peak_memory_mb`, `/operational/started_utc`, `/operational/ended_utc`, `/operational/sequence_position` |
| `/comparison` | `/comparison/status` (`identical`, `divergent`, `pending`) and `/comparison/report_sha256` |
| `/integrity` | `ok` or `blocked` |

The envelope feeds C6 (section 13). `build_result` at the four points contains no time or
process field (the only clock call in the pack, in the data adapter, is not on the synthetic
path); its whole content is compared.

**Typed contract** (closed list; anything else is an error recorded as a harness `error`,
never silently converted):

| Value | Encoding |
|---|---|
| `None`, `bool`, `numpy.bool_` | JSON `null` / `true` / `false` |
| `int`, and `numpy` signed and unsigned integers within the int64 range | JSON integer (outside the range: error) |
| `str` | JSON string |
| `float`, `numpy.float64` | `{"f64": "<16 hex digits, the big-endian IEEE 754 binary64 bit pattern>", "dec": "<repr of the value>"}`; non-finite values have `dec` equal to `"nan"`, `"inf"` or `"-inf"` and keep their bits (sign and NaN payload); for finite values, `dec` must parse back to the same bits (checked when writing and reading) |
| `numpy.float32`, `numpy.float16` | error (not expected in `build_result`; to be widened only by a new schema) |
| `list`, `tuple` | JSON array, in order |
| `dict` with `str` keys | JSON object, keys sorted |
| NumPy arrays, other NumPy or Python types | error |

The bits are captured from the original value before any conversion that could normalize it.
JSON is UTF-8, keys sorted, no spaces.

**Comparison** of the two slots uses the comparator's profile **`slots`** (section 11): the
whole record except a **closed list of excluded paths**, exactly these and no others (part of
the comparator's schema, `refute-population-compare/1`, frozen with its SHA-256 in the
campaign declaration):

1. `/identity/slot`
2. `/identity/execution_id`
3. `/identity/attempt`
4. `/identity/origin/harness_commit` (the harness itself is compared through
   `/identity/origin/harness_sha256`)
5. `/operational/pid`
6. `/operational/seconds`
7. `/operational/peak_memory_mb`
8. `/operational/started_utc`
9. `/operational/ended_utc`
10. `/operational/sequence_position`
11. `/comparison/status`
12. `/comparison/report_sha256`
13. `/integrity`

Everything else is compared, `/configuration` included (thread variables, pools and the
dispatch table are configuration, not operational). A path not in the schema is compared,
never ignored; a path present on one side only is a difference; the list cannot be extended
during a campaign (a new list is a new comparator and a new campaign).

## 11. Comparator and locator (`refute-population-compare/1`, frozen per campaign)

1. **Structure first.** Each blob's layout is parsed on its own (magic, header length, header
   JSON, `arrays` list, offsets and lengths, coverage). Different header lengths, names,
   dtypes, shapes or offsets are reported as a **structural divergence**; the second blob is
   never read with the first blob's table.
2. **Bytes.** With identical layouts: the first differing byte offset, its segment and block;
   for the header, the JSON path; for an array, the element index (unravelled) and the count of
   elements whose bytes differ. Without the bytes, the block index locates the segment and the
   block, and the localization **ends there** (the concession of section 3).
3. **Numeric explanation afterwards, only as explanation:** largest absolute and relative
   differences and the ULP distribution over the differing elements; differences only in the
   sign of zero or in a NaN payload are counted and reported separately and are never treated
   as equal.
4. Result records are compared the same way: structure (schema, paths), then values by their
   typed encoding (bits for floats), skipping exactly the excluded paths of the **profile**
   in use (below), and nothing else.
5. **Profiles.** The comparator has exactly three frozen profiles. Every comparison names one
   profile; there is no default profile, and an unknown or missing profile name is an error.
   Every comparison report records the profile name and the SHA-256 of its exclusion list.

   | Profile | Used for | Excluded paths (exactly these, no others) |
   |---|---|---|
   | `slots` | the two analysis slots of a lot (section 9) | the 13 paths of section 10. Campaign records never carry `/control`; a record with `/control` is a schema error under this profile |
   | `d6-science` | the science between the variants of the D6 test (`D6-proposta.md`) | the 13 paths of `slots`, plus `/configuration/thread_env`, `/configuration/threadpools`, `/configuration/dispatch_table_sha256` and `/control` (17 in all); the D6 checks the configuration separately, against each variant's declaration, and the control section in its own pass |
   | `d6-control` | the control pass of the D6 test | every path **except** `/control` and its members: this profile compares only the control section, which every D6 record carries in every configuration |

   The control pass contract: it runs on the same records as the `d6-science` pass, compares
   only `/control`, and must report a difference exactly where the D6 declares one and nowhere
   else (`D6-proposta.md`, negative control). A profile cannot be added or changed during a
   campaign or a D6 run; a new profile is a new comparator.
6. The comparator's file SHA-256, version, schema and the three profiles with their exclusion
   lists are frozen in the campaign declaration (section 8.3) and recorded in every report.

## 12. Integration with R1, R2, N10 and N-c

- **R1 (extended).** A lot is finished only when: both slots have every result valid at every
  point; each slot has its record 3 (results re-read, with hashes); the comparison of the two
  slots is completed with every case `identical`, recorded with its hash (record 3c); and the
  inputs-deleted record 4 exists. The completion rules of Amendment 3 apply per slot (a missing
  record 3 is rebuilt from that slot's own results); a missing comparison is run before
  record 4; any divergence between records and results, or between the slots, writes a lock.
- **R2 (extended).** The rule covers the v2 harness file and the frozen comparator: every
  campaign mode refuses unless both are byte for byte the files of HEAD and their SHA-256
  equal the campaign declaration.
- **N10 (restricted).** Only infrastructure failures (memory, operating system, an
  interruption) may be resumed, and only for the cases without a result, per slot. An
  **observed divergence** (generation, cache, input hash, slots, reconciliation) is never an
  infrastructure failure and never follows that resumption: it writes a lock.
- **N-c.** No edit of the branch during generation and measurement, except the commits the
  maintainer asks for; the manual, approved commits of lock markers, journal entries and
  resolutions are the declared exception. The harness SHA-256 is still checked at the end of
  each point.

## 13. Metrics

- **Criteria unchanged:** C1 to C6, their limits and bounds do not change. A blocked lot, a
  divergent case and a case `missing` or `error` in either slot count as **integrity errors in
  C6** and block the approval.
- **Reconciliation:** before computing anything, `metrics` checks that every case id of the
  frozen manifest appears exactly once per point, condition and slot, with an envelope; that
  the denominators per stratum equal the manifest's counts; and recomputes the aggregated
  metrics from the eligible records and compares them with any aggregated metrics already
  recorded. Any mismatch is a divergence (lock).
- **Integrity-failure report mode:** for a locked campaign, `metrics --integrity-report` reads
  all the evidence (eligible and diagnostic, each labelled), never lifts or requires lifting
  the lock, never computes an approval, and writes a publishable report whose approval is
  "BLOCKED: integrity failure", listing every lock, divergence and resolution.

## 14. Records and where they go (adjusts section 10 of the protocol)

- **Committed:** the campaign declaration, journal, lock markers and resolutions (manually,
  section 7); per lot, the index of the SHA-256 of every result record; the aggregated metrics;
  every divergence in full (both records, comparison report, lock).
- **Published as a compressed release asset:** the complete result records, in the same
  decision as the reference cases (pending the Zenodo question of Amendment 3).
- The size of the complete records is measured in the v2 self-test.
- Protocol section 10 ("one new file per measurement ... every per-case outcome") becomes: the
  per-case outcomes are committed as a hash index and published in full as an asset.

## 15. Explicit prohibitions

- Never update a frozen manifest (or any expected hash) to accept an observed variant.
- Never regenerate or re-analyze repeatedly until a result matches, and never use a later
  coincidence as the resolution of an earlier divergence.
- Never replace the evidence of an earlier attempt (cache files, manifests, block indexes,
  records, results, journal entries).
- Never combine cases or executions of different sets, slots or campaigns.
- Never accept a diagnostic artifact as campaign evidence.

## 16. Confirmation

The confirmation population is a separate campaign. If the code, the harness, the generation,
the comparator or the plan change after the confirmation has been examined, the previous
attempt is preserved and published, and the new confirmation needs a **new future drand
round** (protocol section 9). The comparison with manifest B never applies to it.

## 17. Revalidation of v2 (before any campaign)

- **Reference cases:** `f3951b9e85d21ea8cbc42a23074ad5b442498d049bfbb51896c6277c85192c4e`,
  `a7dd6266f4ffd30f3cead01987a301c64db2086791a7296e0db55f3f416055c4` and
  `1817b9f776969ae050ba6cd7b1849dda968595041dabe37711390cec7b37b724` (necessary, not
  sufficient).
- **New determinism cases** (prefix `refute-v0.2.1-population-determinism`), including the
  mechanisms that diverged (planets below threshold with white noise, two and three observing
  years; no transit with trend and variability, white noise), in K = 3 fresh processes,
  identical in every segment and block.
- **Capture validated with deliberate differences** in copies, each located by the comparator
  at the right offset, segment, block and field: one byte of an array; the sign of one zero;
  the payload of one NaN; one header field; a structural change (another shape); and, in
  result records, one metric value, a missing field, an extra field, and a float whose `dec`
  and `f64` disagree. The same injected blob differences are also located **with only the
  manifests and block indexes** (no bytes), to the right segment and block, which is all the
  concession of section 3 promises.
- The journal and lock: a simulated divergence writes the marker and the journal entry, every
  campaign mode then refuses, and a run started under another directory for the same campaign
  refuses too.
- The overhead per generation (section 4), the size of the records (section 14), and D6 with
  result PASS under its declared condition of valid conclusion (`D6-proposta.md`).
- The machine qualification (section 8.2) with result PASS, recorded before the campaign
  declaration.

## 18. Residual risk

The K = 3 path accepts a residual risk: three identical generations and two identical slots
make an undetected transient error unlikely but do not demonstrate the absence of a defect,
and they do not detect a systematic one. D6 tests systematic dependence only on its matrix.
