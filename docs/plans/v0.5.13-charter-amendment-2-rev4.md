# v0.5.13 charter: amendment 2, revision 4 (proposed): decision identity as the reproducibility criterion

> **PROPOSED, not approved.** Written on 2026-11-27 under the maintainer's decision H2 (#218,
> comment 7219469262). The direction is still that of decision E1 (#218, comment 7216128796).
> - It replaces revision 3 ([v0.5.13-charter-amendment-2-rev3.md](v0.5.13-charter-amendment-2-rev3.md),
>   commit `c92ff9777824d6facc65d6ddc781c6492b4b9387`, SHA-256
>   `f5598f0050ada236e3944b623ee42b46888e0f1bc8c9b564ab67b529fffcdc38`), which stays unchanged as the
>   record, as do revisions 1 and 2 ([v0.5.13-charter-amendment-2.md](v0.5.13-charter-amendment-2.md)).
> - It applies the six blocking items of revision 3's blind review
>   ([v0.5.13-amendment-2-blind-review-result/](v0.5.13-amendment-2-blind-review-result/README.md))
>   with their replacement texts exactly as written (marked "blind review, item N"). It also applies
>   the maintainer's decisions (a) to (k) of H2, taken before any result (marked "decision H2(x)").
>   The committed diff from revision 3 ties each changed hunk to its item or decision.
> - It changes an acceptance rule (Part A's Step 1 rule and exit criterion 1). The maintainer's
>   adviser checks it, and the maintainer adopts it by its SHA-256. No Codex round: the three
>   rounds were used.
> - It amends the charter approved at `04402e7a4cae71fd7bab8a7157dd38a36a4d2e60` (SHA-256
>   `2832dc4870b0fb094e724a3ff6d6fb6c5710f2da5827791b8fa102c06230c813`), together with amendment 1
>   (`69de5f9f5df0ea621dc6bc7d036f3f1b02448199`, SHA-256
>   `cd2a689231688b5e22c3e6c9602a706fbbca37b7de16ea087417227d5cdbaefc`), which the maintainer
>   approved in #218, comment 7207651312, item D2. Neither file is edited.
>
> **The direction (E1), not reopened with Codex:**
> - no synthetic v5 verification in Step 1;
> - no thread pin;
> - the object of reproducibility is the **decision**, not the last digits.
>
> **Removed from the amendment:**
> - the pinned worker, the patches of `src/` and the `blas-pin` extra;
> - the request for an exception to §12, which the maintainer denied (E2).
>
> **Codex round 3** ran in the same conversation and checked only this revision's implementation
> of that direction ([review record](v0.5.13-amendment-2/README.md)).
> - Its verdict was **`NOT_APPROVABLE`**, with four blocking items, none of which reopens the
>   direction.
> - Their replacement texts are adopted below as written (marked "Codex round 3, item N"). Item 4,
>   on the survey, is applied as a correction comment on #231.
> - Round 3 was the last round, so **this text, as revised after round 3, has not been reviewed
>   again by Codex**. Whether it goes to blind review is the maintainer's adviser's proposal.
>
> **No change to `src/`, `tests/`, `pyproject.toml` or `uv.lock`.**
>
> **Labels:** `exploratory`, `method_status: not_validated`.

## 1. The results known when this was written

**NR-A1** (Step 1; `docs/validation/v0.5.13/step1/comparison-nr-a1.json`). Each setting ran once,
in a fresh process, after its order proof.
- **The inherited default** (OpenBLAS: `libscipy_openblas` 0.3.34 and 0.3.31, 24 threads under
  the meter's affinity of processors 8 to 31): the golden and claim-hash payloads are byte for
  byte equal to ID-BEFORE's.
- **1 thread and 4 threads:**
  - the NR-A1 companion process reported the expected effective thread counts, and the claim
    hashes are equal;
  - two golden outputs differ, `verdict-v3.txt` and `verdict-v4.txt`;
  - under the charter's Step 1 rule, Part A stopped.

**D1a** (`docs/validation/v0.5.13/step1/diag-golden-diff.json`), a new diagnostic, exploratory and
post hoc. At both settings:
- `verdict-v3.txt` differs in 13 of 2,259 lines, and `verdict-v4.txt` in 15 of 2,385;
- no non-numeric line differs (a text comparison after replacing numbers, not a raw-byte proof);
- the fields that differ are `beta`, `amplitude_snr`, `significance`, `semi_amplitude_ppm`,
  `semi_amplitude_err_ppm`, `box_depth_after_model_ppm` and `box_depth_after_model_err_ppm`;
- the largest relative difference is 2.12e-9.

**The tag evidence** (Codex round 1, item 1): ID-BEFORE records joint PASS for the ten expected
locked-claim checks. NR-A1 records golden and claim-hash comparisons at each of its three settings.
D1a is a post-hoc characterization.

**The survey of E1(e)** (#231, exploratory) found the following.
- `refute verify` hashes recorded claim and attachment content, including numeric values, and
  checks the recorded code digest. It does not regenerate any scientific numerical result.
- `refute check-dossier --against` already compares recomputed key values with a relative
  tolerance of 1e-6 (and an absolute floor of 1e-12), not by bytes.

**Also known:** v0.5.12's F-1 found the thread count to be a sufficient factor for these digits,
on one machine. The mechanism of the historical CI difference stays its declared limit.

## 2. (a) Versions 1 to 4: no change

Blind review, item 5, as written:

> Versions 1 to 4 get no change of code, pin or configuration. Their **byte-for-byte identity** was observed in two executions on one machine: ID-BEFORE (`step0/golden-before.json`) and NR-A1's inherited default (`step1/comparison-nr-a1.json`, `nr-a1-default`). It is asserted for those executions' recorded numerical environment and for no other. That environment enters the reproduction recipe of each locked claim as a separate dated sidecar (`docs/validation/v0.5.13/numerical-environment.md`). The sidecar maps each locked claim and tag to the ID-BEFORE record and manifest by hash. It records, each with the record and SHA-256 it is copied from:
> - the inherited thread variables and the effective thread counts;
> - both BLAS libraries' identities, versions and threading layers;
> - the versions of Python, NumPy and SciPy;
> - the OS and the processor affinity.
>
> A value that ID-BEFORE's `provenance` does not hold is copied from another existing hashed record of the same execution, named with its hash, or is written as "not recorded by ID-BEFORE". ID-BEFORE's `provenance` holds `system` and no OS version, no processor affinity, no processor model and no OpenBLAS kernel; the sidecar says so. Nothing is measured again or inferred to fill it.
>
> No lock, dossier, tag or recorded byte is edited.

The sidecar also states (decision H2(h), blind review, non-blocking item 11) that ID-BEFORE's
effective thread counts come from a companion process: `child_threadpool_info`, read by a child
interpreter that imports NumPy and SciPy under the same thread variables
(`docs/validation/v0.5.13/tools/identity.py:37-55`). They do not come from the process that
produced the goldens. The record is `docs/validation/v0.5.13/step0/golden-before.json` (SHA-256
`5eaf5424df933682d881c83abc0938de7f237a68f2b40f1a3ddcbf1f4b5229a8`).

## 3. (b) Other thread settings: decision identity

> Under any other thread setting, versions 1 to 4 meet **decision identity** when all of
> sections 3.1 and 3.2 hold, together with the margin check of section 4.

**NR-A2** (decision H2(a)). One setting never run before, **2 threads**, becomes the named
verification NR-A2: the goldens and the claim hashes, once, in a fresh process.
- It runs only after both the freeze commit of section 4 and the adoption of this amendment.
- It is the only prospective evidence of this rule, and it enters decision identity as the other
  settings do (sections 3, 4 and 6).
- No pin is made in the code; the setting is the thread variables supplied to its process.
- It is a separate execution: it needs its own approval and manifest before it runs.

### 3.1 The comparator (Codex round 1, item 1, as written; changed only by decisions H2(b), H2(c), H2(g) and H2(h))

> For each alternate setting, verify the exact golden file inventory and the SHA-256 of each raw
> file against the payload recorded for that same setting. Compare the raw bytes in order. The frozen comparator may
> treat only schema-identified numeric value tokens and explicitly mapped numeric measurement
> spans in rendered reports as numeric. Require identical field locations, token counts, and all
> bytes outside those spans, including line endings. Compare IDs, paths, versions, integer
> counts, configuration, thresholds, and error records exactly. Reject malformed, missing, extra
> or ambiguous numeric values. A nonfinite token is accepted only when the same token appears at
> the same location in both settings; otherwise it is a failure. For each paired finite measurement, require
> `abs(a - b) <= 0.000001 * max(abs(a), abs(b))`, using exact decimal values from the serialized
> tokens, with zero equal only to zero.
>
> Require the exact protected claim inventory and identical resolved SHA-256 values. Preserve the
> existing `calibration/v0.5/deviation/claim.generated.yaml` error record byte for byte as a
> baseline exception. It supplies no claim hash. The ten locked-claim checks are not run at 1, 2
> or 4 threads; they remain in ID-BEFORE and ID-AFTER. Any additional verification requires its
> own authorization and manifest.

**The recorded payloads and the raw goldens** (decision H2(b)).
- The payload recorded for each setting is that setting's own record:
  - `step0/golden-before.json` for ID-BEFORE;
  - `step1/golden-nr-a1-default.json`, `golden-nr-a1-t1.json` and `golden-nr-a1-t4.json` for
    NR-A1;
  - NR-A2's own record once it exists.
- The raw golden files of ID-BEFORE and of NR-A1's three settings enter git **before** the freeze
  commit of section 4, each with its line endings checked against its committed blob. If their
  total exceeds 5 MB, they go to the Drive with a SHA-256 manifest of source and destination,
  under CLAUDE.md's rule on raw outputs, and the repository keeps that manifest.

**The baseline exception** (decision H2(h), blind review, non-blocking item 10).
- The error record is line 18 of `docs/validation/v0.5.13/step0/claim-hashes-before.json` (SHA-256
  `581234e23531d2369397c3c5b1e15699346a2ac64219cfde9596f6a569485a5f`): `"ERROR ClaimError: invalid
  claim: targets attachment not found: selection/targets.yaml"`.
- No earlier decision accepted it as an exception. The maintainer's adoption of this amendment is
  that acceptance.

**The ten locked-claim checks** (decision H2(g)). They are not checked at 1, 2 or 4 threads.
- They recompute nothing: `refute verify` hashes recorded claim and attachment content and checks
  the recorded code digest (#231).
- They stay in ID-BEFORE and in ID-AFTER.

### 3.2 The tolerance (Codex round 1, item 2, as written)

> Fix the relative tolerance at `1e-6`, a one-part-per-million engineering reproducibility budget
> for each finite reported measurement. Its purpose is to bound tolerated change in output values
> even when the decision agrees. The independent margin check separately requires clearance from
> the decision cutoffs. The scientific thresholds retain their exact values and comparison
> operators. This budget provides no floating-point error guarantee.
>
> NR-A1 and D1a, including the observed maximum relative difference of approximately `2.12e-9`,
> were known when this budget was proposed. This is a post-hoc acceptance amendment. Submit the
> one-part-per-million budget for explicit judgment on its engineering purpose and freeze it with
> the amendment before any acceptance comparison. A failed check leaves #226 unmet. Changing the
> budget requires a new dated rule proposal and fresh blind review.

The first amendment draft proposed `1e-6`, and the value is not changed in response to the observed
drift. It equals `check-dossier`'s existing `DEFAULT_RELATIVE_TOLERANCE`
(`src/refute/core/dossier.py:29`). The comparator here has no absolute floor.

## 4. (c) The margin check: only the operands present in the existing goldens

> The margin manifest covers each golden fixture, stage, test and subcheck. It enumerates every
> operative numeric predicate that can determine a test status, eligibility for that status, or
> the aggregate verdict, traced from the frozen source and resolved plan, regardless of which
> fields D1a found changed. This includes:
> - numeric coverage and count cutoffs;
> - compound predicates;
> - intermediate cutoffs that select the model used by a decision.
>
> Before the comparator of §3.1 or the margin check reads a golden file, the following are frozen, hashed, committed and pushed in one order-proof commit under the charter's section 8:
> - the fixture list;
> - the source commit and code digest that produced each set of goldens, and the resolved plans;
> - the existing golden files of ID-BEFORE and of NR-A1's three settings, each by SHA-256;
> - the comparator, with its schema and its mapping of numeric spans;
> - the complete manifest, including its classification of each operand as present or absent.
>
> The check does not establish the completeness of the manifest or of the span mapping. Before it runs, Codex reviews both against the frozen source (read-only, one round), and the maintainer approves them in #218 by hash. An operative predicate or numeric span found missing afterwards voids the result: #226 returns to unmet until a corrected manifest passes the same steps, and the first result is preserved.
>
> Each row of the manifest gives:
> - the case and the predicate;
> - its source location, comparison operator and units;
> - the exact locations of its operands **in the existing golden files**, or a reconstruction
>   formula that uses only values present there.
>
> **Operands come only from the existing goldens** (blind review, items 2 and 1, as written):
>
> Evaluate each predicate separately in ID-BEFORE and in each required comparison setting. `x` and `t` are the values of the left and right operand expressions of the comparison exactly as written at the predicate's source location, with no algebraic rearrangement; the manifest quotes that source expression. A conjunction or disjunction is split into its comparisons, each a row, and a non-comparison conjunct such as a finiteness test is its own row. Where both operands are present or can be reconstructed using only that setting's existing golden, compute them in exact rational arithmetic from the serialized decimal tokens, and require finite `x` and `t` and `abs(x - t) > 0.000001 * max(abs(x), abs(t))`. Equality fails, including `x = t = 0`. In addition, recompute `x` and `t` with every mapped measurement `v` replaced by `v * (1 - 0.000001)` and by `v * (1 + 0.000001)`, over all combinations, and require the same predicate outcome and `x != t` at every combination. Thresholds, configuration and integer counts are not varied. The manifest states why each formula is monotone in each measurement over those intervals; a row without that statement fails. Where the predicate is assessable in both the reference and comparison setting, also require identical predicate outcomes. A failed check in either setting leaves #226 unmet even if another setting lacks an operand.
>
> A predicate whose operands are all integers or configuration values requires only the same
> outcome in both settings; the margin check does not apply to it (decision H2(d)).
>
> Evaluate both sides of a case-derived threshold using that setting's golden values. Classify each operand as present or absent from the frozen source, the resolved plan and the golden file's schema alone, without regard to any operand value. The frozen manifest fixes that classification. An operand is absent only when no serialized field, and no reconstruction formula that is independent of the values, yields it. Where an operand is present, bound the effect of its serialization by one unit in the last serialized digit of each token, and evaluate the predicate and the margin at both ends of that bound. If the outcome or the margin result differs between the ends, the check **fails**; it is never reclassified as unavailable. A genuine absence in the existing golden is a **declared limit of #226**, never a predicate PASS. A missing required file, hash mismatch, malformed or nonfinite token, or invalid mapping remains a failure under §3.1.
>
> List each absent operand by case, setting, test, predicate, source location and reason. Record the counts of assessed, failed and unassessed predicates, in total and per golden fixture, test and setting. The margin condition of #226 is satisfied only when the manifest is complete, every assessable check passes, and no coverage is zero: for each golden fixture and setting for which the manifest lists a predicate, at least one predicate is assessed. Zero assessed predicates for a fixture and setting leaves the margin condition unmet, never satisfied. Before #226 is recorded as met, the maintainer approves the list of declared limits and the three counts in #218, citing the hash of the margin record. Carry the full list of declared limits into #226 and every later result that relies on it. Make no supplemental execution to recover an operand.

**Examples known from the source when this was written.** They do not replace the manifest, which
lists every one. (Decision H2(e) corrects these against the source, cited by file and line.)
- **The extra-frequency loops.**
  - Version 3 runs `battery_v51.check_sinusoid` (`src/refute/packs/tess/pipeline.py:454-457`),
    and version 4 runs `battery_v52.check_sinusoid` (`src/refute/packs/tess/pipeline_v52.py:186`).
  - Each loop (`src/refute/packs/tess/battery_v51.py:134-147`;
    `src/refute/packs/tess/battery_v52.py:309-320`) runs at most `sinusoid_extra_frequencies`
    times. That is 3 by default (`src/refute/packs/tess/params.py:370`).
  - The loop stops at the first attempt whose SNR is at most `sinusoid_extra_min_snr` (4.0 by
    default, `params.py:371`), or whose joint fit raises `LinAlgError`. Each accepted peak's
    `amplitude_snr` is serialized; the attempt that stops the loop is not.
  - Whether each saved verdict records three peaks is not established here. The frozen manifest
    establishes it per case, without regard to values (blind review, item 1).
  - **The weighted-fit condition-number guard** (`src/refute/packs/tess/battery_v51.py:46-47`:
    `np.linalg.cond(normal) > 1e12` raises `LinAlgError`, in `_wls`, defined at line 41) is an
    example of an operand the goldens do not serialize.
- **The v4 residual-box comparison** (`src/refute/packs/tess/battery_v52.py:338-340`):
  `math.isfinite(sigma_r) and box_after + ATTENUATION_SIGMAS * sigma_r < (ATTENUATION_FRACTION * depth)`.
  - `ATTENUATION_SIGMAS = 3.0` and `ATTENUATION_FRACTION = 0.5` (`battery_v52.py:36-37`).
  - Under blind review item 2, the finiteness test is its own row.
  - Its operands are present only if `box_after`, `sigma_r` and `depth` map exactly to serialized
    fields (`box_depth_after_model_ppm`, `box_depth_after_model_err_ppm` and the candidate's
    depth). The manifest establishes this, or lists the predicate as a limit.

Blind review, item 6, as written:

> The check is a new computation over existing, exposed records, and its rule was written with NR-A1 and D1a known. Its question, quantity and cases are logged before it runs. It changes no recorded result: NR-A1's `STOP` stands as recorded. Its result is exploratory and post hoc. It is used here as evidence for an engineering precondition of an exploratory phase, under the maintainer's decision E1, and for nothing else. It is not a confirmation under Process diet 2, item 4, and it supports no claim, verdict or acceptance of a scientific result.

## 5. (d) Version 5 onward

Codex round 3, item 2, as written (the parenthesis on the thread variables is decision H2(e)):

> For discovery version 5 onward, apply the same typed decision-identity and margin rules to a
> frozen, version-matched reference and that version's comparison evidence. The named ID-BEFORE
> and NR-A1 files and their declared limits apply to #226. Byte identity may be asserted only for
> a comparison that passes exact byte comparison in the same numerical environment, recorded in
> the provenance of each execution. No v5 verification belongs to Step 1.
>
> On the current `run_target_task` path, `environment/numeric_runtime.json` records a
> pre-analysis snapshot in the analyzing process. It records main or worker role, four thread
> variables (`THREAD_VARIABLES`, `src/refute/core/environment.py:46-51`: `OMP_NUM_THREADS`,
> `OPENBLAS_NUM_THREADS`, `MKL_NUM_THREADS` and `NUMEXPR_NUM_THREADS`; ID-BEFORE and NR-A1 record
> the first three, `docs/validation/v0.5.13/tools/identity.py:37`), NumPy's version, its build BLAS when readable, and the inspector's availability.
> When the inspector is available, it records `user_api`, `internal_api`, `prefix`, `version`
> and `num_threads` for the libraries visible at that point.
>
> The launcher's snapshot supplies Python, platform, machine and selected package versions. It
> also supplies `environment/requirements.txt` with installed distribution versions, including
> SciPy when installed, and a copy of `uv.lock` when available. The structured analyzing-process
> record lacks SciPy's version, pool `threading_layer`, and processor affinity or usable CPU
> count. Its timing can also omit libraries loaded later during analysis.
>
> Part B records the v5 reference and comparison evidence, validates what provenance each v5
> execution path writes, and addresses the identified gaps under its own approvals. This
> amendment makes no source change.

Decision H2(f) (blind review, non-blocking item 8, as suggested): For version 5 onward, an absent
operand leaves the margin condition unmet unless that version's own approved charter declares it a
limit before the evidence is produced.

(Sources: `src/refute/core/environment.py:54-104`; `src/refute/core/run.py:137` and `365`.)

## 6. (f) Step 1's rule and Part A's exit criterion 1, replaced

> **1. #226 passed** when all of the following are evidenced:
> - **(a)** For versions 1 to 4, the inherited-default NR-A1 golden bytes, error outputs and
>   claim-hash payload match ID-BEFORE in its recorded numerical environment. The dated sidecar of
>   section 2 is written and maps each locked claim and tag to that record by hash.
> - **(b)** At 1 and 4 threads (NR-A1's existing records) and at 2 threads (NR-A2, section 3),
>   versions 1 to 4 meet decision identity under section 3.
> - **(c)** The margin check of section 4 passes on every predicate with present operands, at each of those settings, with no zero coverage as section 4 defines it. Its list of absent operands is recorded one by one as declared limits of #226 and approved by the maintainer in #218 by the hash of the margin record.
>
> The mechanism of the historical CI difference stays a declared limit of F-1.
>
> Wherever #226 is cited as met under this rule (in #226, the phase report, Part B's charter and every later result that relies on it), it carries the label **'#226 met under amendment 2 (decision identity, post hoc, on exposed records); the charter's byte-identity rule was not met at 1 and 4 threads (NR-A1: STOP); N declared limits'**, with N from the margin record. Under the charter's section 2, Part B may rely on #226 only with that label, and only if the maintainer's approval of this amendment says so explicitly.

Codex round 3, item 3, as written (the ID-AFTER sentences are blind review, item 5; the last
paragraph is changed by decisions H2(a) and H2(g)):

> This replaces Step 1's acceptance rule, the Step 1 acceptance clause of stop 2, and exit
> criterion 1. Preserve the original NR-A1 `STOP` and D1a records. Report the amended assessment
> separately, with its date and declared limits. An inherited-default byte mismatch, a failed
> decision-identity or assessable margin check, or missing or unverifiable required evidence
> leaves #226 unmet and Part A stopped before #227. The absent-operand allowance in §4 applies
> only to the margin check. Report untested settings as unverified.
>
> Steps 2–5, criteria 2–6 and all other stop provisions continue to apply. At the seal, recheck
> protected source and artifacts. The once-only named ID-AFTER verifies legacy golden and error-output byte identity, claim-hash identity, and all ten locked-claim checks. Its recorded provenance must equal ID-BEFORE's in every field of `provenance.blas` and in `python`, `numpy`, `scipy` and `system`. A difference in any of those fields, a byte mismatch or a missing proof leaves criterion 5 unmet. Step 5's full CI and accounting requirements continue to apply.
>
> Adoption authorizes no execution or source change. Obtain the applicable approval and manifest
> before producing the sidecar or executing each verification unit. NR-A2 runs once, offline, in a
> fresh process, after the freeze commit of section 4 and the adoption of this amendment, under the
> charter's metering, journal and applicable order-proof rules, with its own approval and manifest.

The ten locked-claim checks run only in ID-BEFORE (recorded) and ID-AFTER (decision H2(g)).

**Also replaced** (decision H2(j), blind review, non-blocking item 13): no pin is made, so the
following become stale and are replaced by this amendment:
- the pin clause of the charter's stop 2, "and the pin itself, as a `src/` change, by its exact
  diff" (charter, lines 539-540);
- the charter's risk 1, "The pin moves a byte of versions 1 to 4." (charter, line 563).

## 7. Open items, stated

- None of these exists yet:
  - the comparator of 3.1;
  - the margin manifest and check of section 4;
  - the commit of the raw goldens of section 3.1 (decision H2(b)) and the freeze commit of
    section 4;
  - NR-A2 (section 3);
  - the sidecar of section 2.
- The list of absent operands exists only once the margin manifest is built. Section 4's examples
  are not that list.
- The v5 evidence and provenance work in §5 is a Part B item and is not scheduled here.
