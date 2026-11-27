## 1. Verdict

**`NOT_APPROVABLE` for submission to blind review, round 3.** Revision 3 implements E1 and E2’s direction: no pin, no synthetic v5 verification in Step 1, no source or dependency change, and no supplemental execution to recover margin operands. Four implementation defects remain. None requires reopening the maintainer’s decision.

I verified that §§3.1 and 3.2 reproduce the round 1 wording, allowing for line wrapping. I checked the source references against commit `3a5eba5`. I did not run a verifier or acceptance comparison, modify files, or access the network.

## 2. Blocking items

### 1. A missing operand must leave only its own check unassessed

**Where:** [Revision 3, §4, lines 147–179](C:/Projetos/refute/docs/plans/v0.5.13-charter-amendment-2-rev3.md:147).

The current wording can skip a failed margin in one setting when the same predicate has an absent operand in another. It also allows an ambiguous or unpaired value to be classified as absent without distinguishing a genuine omission from an invalid record or comparator mapping. E1(c) permits a declared limit for an absent operand, while §3.1 still rejects invalid comparison evidence.

**Replace lines 147–165 with:**

> Evaluate each predicate separately in ID-BEFORE and in each required comparison setting. Where both operands are present or can be reconstructed using only that setting’s existing golden, require finite `x` and `t` and `abs(x - t) > 0.000001 * max(abs(x), abs(t))`. Equality fails, including `x = t = 0`. Where the predicate is assessable in both the reference and comparison setting, also require identical predicate outcomes. A failed check in either setting leaves #226 unmet even if another setting lacks an operand.
>
> Evaluate both sides of a case-derived threshold using that setting’s golden values. If serialization uncertainty prevents a reliable reconstruction or could change the predicate or margin result, record the specific unavailable operand and the reason. A genuine absence in the existing golden is a **declared limit of #226**, never a predicate PASS. A missing required file, hash mismatch, malformed or nonfinite token, or invalid mapping remains a failure under §3.1.
>
> List each absent operand by case, setting, test, predicate, source location and reason. Record the counts of assessed, failed and unassessed predicates. The margin condition of #226 is satisfied only when the manifest is complete and every assessable check passes. Carry the full list of declared limits into #226 and every later result that relies on it. Make no supplemental execution to recover an operand.

**Also replace the extra-frequency example at lines 169–173 with:**

> In the v3 and v4 extra-frequency loops, each accepted peak’s `amplitude_snr` is serialized. Each saved v3 and v4 verdict in ID-BEFORE and NR-A1 records all three configured peaks, so these records do not show an early-exit attempt with an unrecorded SNR. The weighted-fit condition-number guard is an example of an operand the goldens do not serialize.

The loop citations are correct. The early-exit conclusion was not supported by the saved fixtures. The residual-box comparison citation is also correct. Its serialized depth and uncertainty are shown at lines 389–390. [v3 loop](C:/Projetos/refute/src/refute/packs/tess/battery_v51.py:134), [weighted-fit guard](C:/Projetos/refute/src/refute/packs/tess/battery_v51.py:41), [v4 comparison](C:/Projetos/refute/src/refute/packs/tess/battery_v52.py:337), [v4 output fields](C:/Projetos/refute/src/refute/packs/tess/battery_v52.py:384)

### 2. Apply the v5 rule to v5 evidence and correct the provenance inventory

**Where:** [Revision 3, §5, lines 186–206 and §7, line 252](C:/Projetos/refute/docs/plans/v0.5.13-charter-amendment-2-rev3.md:186).

Section 5 points v5 to a margin rule whose input artifacts are explicitly the legacy ID-BEFORE and NR-A1 goldens. The provenance inventory also overstates the gap. SciPy is absent from `KEY_PACKAGES`, but the launcher’s `requirements.txt` records its installed version when SciPy is installed. The gap is the version in the analyzing process’s runtime record. That record is taken before analysis, can lack pool information, and includes whether the process is a worker or the main process.

**Replace §5’s operative text and inventory with:**

> For discovery version 5 onward, apply the same typed decision-identity and margin rules to a frozen, version-matched reference and that version’s comparison evidence. The named ID-BEFORE and NR-A1 files and their declared limits apply to #226. Byte identity may be asserted only for a comparison that passes exact byte comparison in the same numerical environment, recorded in the provenance of each execution. No v5 verification belongs to Step 1.
>
> On the current `run_target_task` path, `environment/numeric_runtime.json` records a pre-analysis snapshot in the analyzing process. It records main or worker role, four thread variables, NumPy’s version, its build BLAS when readable, and the inspector’s availability. When the inspector is available, it records `user_api`, `internal_api`, `prefix`, `version` and `num_threads` for the libraries visible at that point.
>
> The launcher’s snapshot supplies Python, platform, machine and selected package versions. It also supplies `environment/requirements.txt` with installed distribution versions, including SciPy when installed, and a copy of `uv.lock` when available. The structured analyzing-process record lacks SciPy’s version, pool `threading_layer`, and processor affinity or usable CPU count. Its timing can also omit libraries loaded later during analysis.
>
> Part B records the v5 reference and comparison evidence, validates what provenance each v5 execution path writes, and addresses the identified gaps under its own approvals. This amendment makes no source change.

Replace §7’s final bullet with **“The v5 evidence and provenance work in §5 is a Part B item and is not scheduled here.”** [Runtime and snapshot source](C:/Projetos/refute/src/refute/core/environment.py:54), [dossier write path](C:/Projetos/refute/src/refute/core/run.py:137), [launcher snapshot](C:/Projetos/refute/src/refute/core/run.py:365)

### 3. Preserve the complete seal and make the Step 1 stop explicit

**Where:** [Revision 3, §6, lines 222–241](C:/Projetos/refute/docs/plans/v0.5.13-charter-amendment-2-rev3.md:222), [approved charter, Step 1](C:/Projetos/refute/docs/plans/v0.5.13-charter.md:91), [Step 5 and criteria 2–6](C:/Projetos/refute/docs/plans/v0.5.13-charter.md:244).

Revision 3 retains ID-AFTER and criteria 2–6, but its replacement of Step 1 drops the explicit recheck of **protected source and artifacts**. Step 5 originally incorporates that obligation by reference. The draft also says every stop is unchanged immediately after replacing one, and the replacement stop should expressly cover missing or unverifiable required evidence.

**Replace lines 222–241 with:**

> This replaces Step 1’s acceptance rule, the Step 1 acceptance clause of stop 2, and exit criterion 1. Preserve the original NR-A1 `STOP` and D1a records. Report the amended assessment separately, with its date and declared limits. An inherited-default byte mismatch, a failed decision-identity or assessable margin check, or missing or unverifiable required evidence leaves #226 unmet and Part A stopped before #227. The absent-operand allowance in §4 applies only to the margin check. Report untested settings as unverified.
>
> Steps 2–5, criteria 2–6 and all other stop provisions continue to apply. At the seal, recheck protected source and artifacts. The once-only named ID-AFTER verifies legacy golden and error-output byte identity in ID-BEFORE’s recorded numerical environment, claim-hash identity, and all ten locked-claim checks. Any required mismatch or missing proof leaves criterion 5 unmet. Step 5’s full CI and accounting requirements continue to apply.
>
> Adoption authorizes no execution or source change. Obtain the applicable approval and manifest before producing the sidecar or executing each verification unit. Run the additional tag checks offline against the exact expected tags and their approved cached environments, with `UV_OFFLINE=1`, under the charter’s metering, journal and applicable order-proof rules. Record the thread variables supplied to the verifying commands, the tag and claim identities, and all ten outcomes at each setting. If a required environment is unavailable offline, stop.

The tag checks are **verification under Process diet 2 item 4**. The supplied environment is evidence of which settings the verifier inherited. The verifier itself does not establish effective BLAS counts, and `uv sync --frozen` alone does not guarantee offline operation. NR-A1 contains no alternate-setting tag runs. [Process diet 2](C:/Projetos/refute/CLAUDE.md:89), [tag verifier launch path](C:/Projetos/refute/scripts/verify_locked_tags.py:469), [NR-A1 manifest](C:/Projetos/refute/docs/validation/v0.5.13/manifests/nr-a1.json:11)

### 4. Correct the survey’s evidence claim and byte-comparison inventory

**Where:** [Local #231 survey, lines 3 and 17–36](C:/Projetos/refute/.cache/v0513/issue-e1e.md:3).

The main source references are correct. The survey nevertheless implies alternate-setting tag PASS is already on record, describes the code digest as source files only, and misses that the review index directly checks the raw bytes of `verdict.json`. The main manifest also excludes some paths in sealed layouts.

**Replace the context sentence at line 3 with:**

> At 1 and 4 threads, NR-A1 found equal claim-hash payloads and numeric differences in two legacy goldens. ID-BEFORE records joint PASS for the ten expected locked-claim checks. NR-A1 did not run those checks at the alternate settings.

**Replace the code-hash bullet and `verify` conclusion at lines 17–19 with:**

> **The code hash** (`lock.py:577–590`, `codehash.py:71–94`) covers eligible files under `src/` plus `pyproject.toml` and `uv.lock` when present. `verify` hashes recorded claim and attachment content, including numeric values, and checks the recorded code digest. It does not regenerate any scientific numerical result.

**Replace `check-dossier` items 1–3 and the conclusion at line 36 with:**

> **Integrity:** `verify_manifest` hashes the raw bytes of files covered by `MANIFEST.sha256`, including `verdict.json`. In the sealed layout the seal and annexes have separate checks (`dossier.py:76–95`, `121–136`).
>
> **Seal and annexes:** when the sealed layout applies, `check_sealed` checks the core archive digest and each annex’s recorded file hashes (`seal.py:204–220`, `347–357`, `372–392`).
>
> **Reviews:** when a review index exists, `verify_reviews` checks the raw `verdict.json` hash, the analysis-manifest fingerprint and the review-file hashes (`review.py:146–171`). The verdict digest covers its stored floats.
>
> **Conclusion:** These byte checks establish integrity of recorded artifacts. `--against` compares `verdict` and statuses exactly, input hashes exactly, and numeric `key_values` with `math.isclose(rel_tol=1e-6, abs_tol=1e-12)`. It does not compare other test metrics across dossiers.

## 3. Non-blocking items

- **Keep the round 1 quotes and the `1e-6` disclosure.** The draft correctly distinguishes the proposed engineering budget from `check-dossier`’s existing tolerance with an absolute floor. [Revision 3, §3.2](C:/Projetos/refute/docs/plans/v0.5.13-charter-amendment-2-rev3.md:106)
- **Clarify the historical evidence wording.** In §1, “the NR-A1 companion process reported the expected effective thread counts” is more precise than “each pin was verified.” The companion process imported NumPy and SciPy under the matching environment. [NR-A1 manifest](C:/Projetos/refute/docs/validation/v0.5.13/manifests/nr-a1.json:19)
- **Amendment 1 and F-1 carry through.** Revision 3 leaves amendment 1’s population, denominators and scientific thresholds intact. It retains the historical CI mechanism as a declared limit of F-1. [Amendment 1](C:/Projetos/refute/docs/plans/v0.5.13-charter-amendment-1.md:72), [revision 3, §6](C:/Projetos/refute/docs/plans/v0.5.13-charter-amendment-2-rev3.md:208)