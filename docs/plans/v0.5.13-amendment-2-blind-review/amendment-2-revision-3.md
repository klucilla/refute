# v0.5.13 charter: amendment 2, revision 3 (proposed): decision identity as the reproducibility criterion

> **PROPOSED, not approved.** Written on 2026-11-27 under the maintainer's decision E1 (#218,
> comment 7216128796), which set its direction.
> - It replaces revisions 1 and 2 ([v0.5.13-charter-amendment-2.md](v0.5.13-charter-amendment-2.md)),
>   which stay unchanged as the record.
> - It changes an acceptance rule (Part A's Step 1 rule and exit criterion 1). It therefore needs
>   a **fresh blind review before adoption**, which the maintainer's adviser proposes. The
>   maintainer then approves it by its commit SHA.
> - It amends the charter approved at `04402e7a` (SHA-256 `2832dc48…c230c813`), together with
>   amendment 1 (`69de5f9f`). Neither file is edited.
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

> Versions 1 to 4 get no change of code, pin or configuration. Their **byte-for-byte identity**
> holds in the numerical environment recorded by ID-BEFORE (`step0/golden-before.json`,
> `provenance`), and NR-A1 found it at the inherited default. That environment enters the
> reproduction recipe of each locked claim as a separate dated sidecar
> (`docs/validation/v0.5.13/numerical-environment.md`). The sidecar maps each locked claim and tag
> to the ID-BEFORE record and manifest by hash. It records:
> - the inherited thread variables and the effective thread counts;
> - both BLAS libraries' identities, versions and threading layers;
> - the versions of Python, NumPy and SciPy;
> - the OS and the processor affinity.
>
> No lock, dossier, tag or recorded byte is edited.

## 3. (b) Other thread settings: decision identity

> Under any other thread setting, versions 1 to 4 meet **decision identity** when all of
> sections 3.1 and 3.2 hold, together with the margin check of section 4.

### 3.1 The comparator (Codex round 1, item 1, as written)

> For each alternate setting, verify the exact golden file inventory and the SHA-256 of each raw
> file against its recorded payload. Compare the raw bytes in order. The frozen comparator may
> treat only schema-identified numeric value tokens and explicitly mapped numeric measurement
> spans in rendered reports as numeric. Require identical field locations, token counts, and all
> bytes outside those spans, including line endings. Compare IDs, paths, versions, integer
> counts, configuration, thresholds, and error records exactly. Reject malformed, missing, extra,
> ambiguous, or nonfinite numeric values. For each paired finite measurement, require
> `abs(a - b) <= 0.000001 * max(abs(a), abs(b))`, using exact decimal values from the serialized
> tokens, with zero equal only to zero.
>
> Require the exact protected claim inventory and identical resolved SHA-256 values. Preserve the
> existing `calibration/v0.5/deviation/claim.generated.yaml` error record byte for byte as a
> baseline exception. It supplies no claim hash. Require joint PASS for all ten expected
> locked-claim checks at the setting being certified, with the exact tag and claim identities and
> evidence of the setting in the verifying execution. Missing per-setting evidence leaves that
> setting unmet. Any additional verification requires its own authorization and manifest.

The ten locked-claim checks are verification (`refute verify` through `verify_locked_tags.py`), not
a rerun (CLAUDE.md, Process diet 2, item 4). Section 1 records that they recompute no numerical
output. Their per-setting evidence is a verification run under that setting's thread variables,
with its own manifest.

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
> Before the check runs, the following are frozen and hashed:
> - the fixture list;
> - the source and resolved plans;
> - the existing golden files of ID-BEFORE and of NR-A1's three settings;
> - the comparator;
> - the complete manifest.
>
> Each row of the manifest gives:
> - the case and the predicate;
> - its source location, comparison operator and units;
> - the exact locations of its operands **in the existing golden files**, or a reconstruction
>   formula that uses only values present there.
>
> **Operands come only from the existing goldens** (Codex round 3, item 1, as written):
>
> Evaluate each predicate separately in ID-BEFORE and in each required comparison setting. Where
> both operands are present or can be reconstructed using only that setting's existing golden,
> require finite `x` and `t` and `abs(x - t) > 0.000001 * max(abs(x), abs(t))`. Equality fails,
> including `x = t = 0`. Where the predicate is assessable in both the reference and comparison
> setting, also require identical predicate outcomes. A failed check in either setting leaves
> #226 unmet even if another setting lacks an operand.
>
> Evaluate both sides of a case-derived threshold using that setting's golden values. If
> serialization uncertainty prevents a reliable reconstruction or could change the predicate or
> margin result, record the specific unavailable operand and the reason. A genuine absence in the
> existing golden is a **declared limit of #226**, never a predicate PASS. A missing required
> file, hash mismatch, malformed or nonfinite token, or invalid mapping remains a failure under
> §3.1.
>
> List each absent operand by case, setting, test, predicate, source location and reason. Record
> the counts of assessed, failed and unassessed predicates. The margin condition of #226 is
> satisfied only when the manifest is complete and every assessable check passes. Carry the full
> list of declared limits into #226 and every later result that relies on it. Make no
> supplemental execution to recover an operand.

**Examples known from the source when this was written.** They do not replace the manifest, which
lists every one.
- **The extra-frequency loops** (Codex round 3, item 1, as written): In the v3 and v4
  extra-frequency loops, each accepted peak's `amplitude_snr` is serialized. Each saved v3 and v4
  verdict in ID-BEFORE and NR-A1 records all three configured peaks, so these records do not show
  an early-exit attempt with an unrecorded SNR. The weighted-fit condition-number guard is an
  example of an operand the goldens do not serialize.
  (`src/refute/packs/tess/battery_v51.py:134-147`; `src/refute/packs/tess/battery_v52.py:309-320`;
  the guard: `battery_v51.py:41`.)
- **The v4 residual-box comparison** (`battery_v52.py:337-340`): `box_after + 3 * sigma_r <
  0.5 * depth`. Its operands are present only if `box_after`, `sigma_r` and `depth` map exactly to
  serialized fields (`box_depth_after_model_ppm`, `box_depth_after_model_err_ppm` and the
  candidate's depth). The manifest establishes this, or lists the predicate as a limit.

The check is a new computation over existing records. Its question, quantity and cases are
logged before it runs, and it replaces or re-scores no recorded result (Process diet 2, item 4).

## 5. (d) Version 5 onward

Codex round 3, item 2, as written:

> For discovery version 5 onward, apply the same typed decision-identity and margin rules to a
> frozen, version-matched reference and that version's comparison evidence. The named ID-BEFORE
> and NR-A1 files and their declared limits apply to #226. Byte identity may be asserted only for
> a comparison that passes exact byte comparison in the same numerical environment, recorded in
> the provenance of each execution. No v5 verification belongs to Step 1.
>
> On the current `run_target_task` path, `environment/numeric_runtime.json` records a
> pre-analysis snapshot in the analyzing process. It records main or worker role, four thread
> variables, NumPy's version, its build BLAS when readable, and the inspector's availability.
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

(Sources: `src/refute/core/environment.py:54-104`; `src/refute/core/run.py:137` and `365`.)

## 6. (f) Step 1's rule and Part A's exit criterion 1, replaced

> **1. #226 passed** when all of the following are evidenced:
> - **(a)** For versions 1 to 4, the inherited-default NR-A1 golden bytes, error outputs and
>   claim-hash payload match ID-BEFORE in its recorded numerical environment. The dated sidecar of
>   section 2 is written and maps each locked claim and tag to that record by hash.
> - **(b)** At 1 and 4 threads (NR-A1's existing records), versions 1 to 4 meet decision identity
>   under section 3, with the per-setting evidence of the ten locked-claim checks.
> - **(c)** The margin check of section 4 passes on every predicate with present operands, at each
>   of those settings. Its list of absent operands is recorded one by one as declared limits of
>   #226.
>
> The mechanism of the historical CI difference stays a declared limit of F-1.

Codex round 3, item 3, as written:

> This replaces Step 1's acceptance rule, the Step 1 acceptance clause of stop 2, and exit
> criterion 1. Preserve the original NR-A1 `STOP` and D1a records. Report the amended assessment
> separately, with its date and declared limits. An inherited-default byte mismatch, a failed
> decision-identity or assessable margin check, or missing or unverifiable required evidence
> leaves #226 unmet and Part A stopped before #227. The absent-operand allowance in §4 applies
> only to the margin check. Report untested settings as unverified.
>
> Steps 2–5, criteria 2–6 and all other stop provisions continue to apply. At the seal, recheck
> protected source and artifacts. The once-only named ID-AFTER verifies legacy golden and
> error-output byte identity in ID-BEFORE's recorded numerical environment, claim-hash identity,
> and all ten locked-claim checks. Any required mismatch or missing proof leaves criterion 5
> unmet. Step 5's full CI and accounting requirements continue to apply.
>
> Adoption authorizes no execution or source change. Obtain the applicable approval and manifest
> before producing the sidecar or executing each verification unit. Run the additional tag checks
> offline against the exact expected tags and their approved cached environments, with
> `UV_OFFLINE=1`, under the charter's metering, journal and applicable order-proof rules. Record
> the thread variables supplied to the verifying commands, the tag and claim identities, and all
> ten outcomes at each setting. If a required environment is unavailable offline, stop.

The tag checks are verification under Process diet 2, item 4. The supplied environment is evidence
of which settings the verifier inherited; the verifier itself does not establish effective BLAS
counts. NR-A1 contains no alternate-setting tag runs.

## 7. Open items, stated

- None of these exists yet:
  - the comparator of 3.1;
  - the margin manifest and check of section 4;
  - the per-setting verification runs of 3.1;
  - the sidecar of section 2.
- The list of absent operands exists only once the margin manifest is built. Section 4's examples
  are not that list.
- The v5 evidence and provenance work in §5 is a Part B item and is not scheduled here.
