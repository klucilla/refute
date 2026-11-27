## 1. Verdict

**`NOT_APPROVABLE` for submission to blind review, round 1.** The draft leaves the decision comparison underspecified, the worker check can omit workers and BLAS libraries, and exit criterion 1 can pass without either v5 identity result. Part A remains stopped at #226.

I verified the hashes of all 80 saved golden files against the four recorded payloads and checked that both patch hunks reproduce their proposed files. I did not run tests, recompute goldens, modify files, or access the network.

## 2. Blocking items and exact replacements

### 1. Restrict numeric tolerance to typed fields and bind the evidence

**Where:** [Amendment 2, lines 40–41 and 59–68](C:/Projetos/refute/docs/plans/v0.5.13-charter-amendment-2.md:59), [diagnostic, lines 34–57](C:/Projetos/refute/docs/validation/v0.5.13/tools/diag_golden_diff.py:34), [NR-A1 manifest, lines 11–21](C:/Projetos/refute/docs/validation/v0.5.13/manifests/nr-a1.json:11).

**Blocker.** Replacing every number can hide changes to digits in IDs, paths, version strings, or error messages. The diagnostic also reads text and splits lines, which cannot prove raw byte equality. NR-A1 ran goldens and claim hashes at each setting. The recorded 10/10 PASS is from ID-BEFORE and covers ten locked-claim checks, including multiple checks at the same tag. The claim-hash payload also contains a pre-existing error record. [ID-BEFORE manifest](C:/Projetos/refute/docs/validation/v0.5.13/manifests/id-before.json:20), [claim-hash payload](C:/Projetos/refute/docs/validation/v0.5.13/step0/claim-hashes-before.json:18)

**Replace §1’s tag sentence and §3 items 1–4 with:**

> ID-BEFORE records joint PASS for the ten expected locked-claim checks. NR-A1 records golden and claim-hash comparisons at each of its three settings. D1a is a post-hoc characterization.
>
> For each alternate setting, verify the exact golden file inventory and the SHA-256 of each raw file against its recorded payload. Compare the raw bytes in order. The frozen comparator may treat only schema-identified numeric value tokens and explicitly mapped numeric measurement spans in rendered reports as numeric. Require identical field locations, token counts, and all bytes outside those spans, including line endings. Compare IDs, paths, versions, integer counts, configuration, thresholds, and error records exactly. Reject malformed, missing, extra, ambiguous, or nonfinite numeric values. For each paired finite measurement, require `abs(a - b) <= 0.000001 * max(abs(a), abs(b))`, using exact decimal values from the serialized tokens, with zero equal only to zero.
>
> Require the exact protected claim inventory and identical resolved SHA-256 values. Preserve the existing `calibration/v0.5/deviation/claim.generated.yaml` error record byte for byte as a baseline exception. It supplies no claim hash. Require joint PASS for all ten expected locked-claim checks at the setting being certified, with the exact tag and claim identities and evidence of the setting in the verifying execution. Missing per-setting evidence leaves that setting unmet. Any additional verification requires its own authorization and manifest.

### 2. Give `1e-6` an independent purpose and remove the unsupported bound

**Where:** [Amendment 2, lines 75–86 and 129–134](C:/Projetos/refute/docs/plans/v0.5.13-charter-amendment-2.md:75), [v3 weighted least squares, lines 41–50](C:/Projetos/refute/src/refute/packs/tess/battery_v51.py:41).

**Blocker.** A summation error bound relative to the sum of absolute terms does not bound relative error in a small, cancellation-prone output. The implementation forms and inverts weighted normal equations and has a condition-number guard at `1e12`. The draft establishes neither its assumed `κ ≤ 10³` nor the propagation through covariance, residuals, and ratios. The number of digits in a threshold also says nothing about a statistic’s distance from it.

**Replace the justification and remove the corresponding open bound claims in §6:**

> Fix the relative tolerance at `1e-6`, a one-part-per-million engineering reproducibility budget for each finite reported measurement. Its purpose is to bound tolerated change in output values even when the decision agrees. The independent margin check separately requires clearance from the decision cutoffs. The scientific thresholds retain their exact values and comparison operators. This budget provides no floating-point error guarantee.
>
> NR-A1 and D1a, including the observed maximum relative difference of approximately `2.12e-9`, were known when this budget was proposed. This is a post-hoc acceptance amendment. Submit the one-part-per-million budget for explicit judgment on its engineering purpose and freeze it with the amendment before any acceptance comparison. A failed check leaves #226 unmet. Changing the budget requires a new dated rule proposal and fresh blind review.

**My choice:** Keep `1e-6` as an explicit engineering cap if the blind review accepts that purpose. The draft’s derivation does not justify it. I would not substitute another value based on the observed drift.

### 3. Freeze a complete margin manifest and fail closed on unavailable operands

**Where:** [Amendment 2, lines 69–73](C:/Projetos/refute/docs/plans/v0.5.13-charter-amendment-2.md:69), [v3 peak selection, lines 131–147](C:/Projetos/refute/src/refute/packs/tess/battery_v51.py:131), [v4 sinusoid, lines 309–375](C:/Projetos/refute/src/refute/packs/tess/battery_v52.py:309).

**Blocker.** A list of emitted metrics paired with nearby `thresholds` keys would miss compound comparisons and operands that were never serialized. For example, v3 and v4 test each proposed extra peak against `extra_min_snr` before appending it. A rejected peak’s SNR is absent from the saved list. The v4 attenuation branch compares `box_after + 3 * sigma_r` with `0.5 * depth`, using the resolved configuration and case values.

**Replace §3 item 5 with:**

> The margin manifest covers each golden fixture, stage, test, and subcheck. Enumerate every operative numeric predicate that can determine a test status, eligibility for that status, or the aggregate verdict. Include numeric coverage and count cutoffs, compound predicates, and intermediate cutoffs that select the model used by a decision. Trace them from the frozen source and resolved plan, regardless of which fields D1a found changed. Include each potentially applicable predicate and record source-backed evidence for any unevaluated branch. A branch suppressed by short-circuiting is inapplicable only when the controlling predicate and its margin are established.
>
> Before running the acceptance comparator, freeze and hash the fixture list, source and resolved plans, raw input artifacts, comparator, and complete manifest. Each row specifies the case and predicate, source location, comparison operator, units, and exact operand locations or reconstruction formulas. Examples include `difference_sigma` versus `max_sigma`, harmonic significance versus `min_significance`, harmonic semi-amplitude versus `min_amplitude_ratio * candidate.depth`, every attempted extra peak’s SNR versus `extra_min_snr`, and the v4 residual-box comparison. Evaluate full-precision operands with the source’s evaluation order and resolved thresholds.
>
> In both the reference and comparison setting, require finite operands `x` and `t`, identical predicate outcomes, and `abs(x - t) > 0.000001 * max(abs(x), abs(t))`. Equality fails, including `x = t = 0`. For a case-derived threshold, evaluate both sides independently in each setting. If either side is computed from serialized values, establish that serialization uncertainty cannot change the predicate or the margin result. A missing, ambiguous, unpaired, or unreconstructable operand leaves the check unmet. Report the predicate, both operand pairs, margins, and outcome. Supply missing operands only through a separately approved measurement with a frozen manifest and order proof.

**My choice:** Include all operative numeric boundaries, including exact counts used as decision statistics. A boundary hit or missing full-precision operand is a failed check. The current saved goldens cannot establish full coverage of that rule.

### 4. Replace the worker launch, startup verification, and record contract

**Where:** [Runner patch, lines 40–128](C:/Projetos/refute/docs/plans/v0.5.13-amendment-2/runner.patch:40), [Amendment 2, lines 88–107](C:/Projetos/refute/docs/plans/v0.5.13-charter-amendment-2.md:88), [legacy discovery caller](C:/Projetos/refute/src/refute/packs/tess/discover/runs.py:79).

**Blocker.** The multiprocess path uses `spawn`. When the parent environment is stable, it gives each child the requested variables before Python imports. It does not establish the effective pin for every BLAS library. The check explicitly loads NumPy, so SciPy’s separate BLAS can be absent. The initializer discards its result, and submitting `n` probes provides no guarantee of `n` distinct PIDs. The in-process branch can pass with a library already loaded, so it cannot establish the required order. It can also leave a newly loaded library pinned after the environment is restored. The parent-wide override can affect a concurrent legacy launch.

**Replace §4’s runner contract and implement it in the exact diff:**

> For every nonempty v5+ batch, `run_processes_pinned` partitions the indexed tasks into `min(workers, len(tasks))` nonempty shards and launches one fresh Python interpreter per shard. Pass an explicit child environment with the frozen thread variables forced to `"1"` at OS process creation. Preserve the caller’s environment. Use this path for a single task and for `workers=1`. The worker entry point starts without task-module imports and checks the launch variables before importing the numerical stack or deserializing any task.
>
> At startup, explicitly load the approved NumPy and SciPy numerical paths, including `scipy.linalg`, and any other supported task-specific BLAS providers. Compare the inventory with the frozen backend and library manifest for that environment. Refuse if a required backend is missing, an unexpected backend appears, a count is unreadable, or any effective BLAS count differs from one. Recheck after loading each task module and before invoking it. Recheck before accepting the task result. An unsupported or unverifiable stack fails the batch.
>
> Each child reports its own startup check through the worker protocol, with the run and shard IDs, PID, launch variables, backend and library identity, version, threading layer, and effective counts. Bind that PID to the child the runner launched and to every task index returned by the child. A missing, duplicate, or mismatched startup record, incomplete shard, or child failure rejects the batch. Preserve task order. Persist the startup records and task-to-worker mapping in run evidence outside the golden payload. Record failures without accepting the affected batch. An empty batch records zero workers.
>
> Enable this entry point only for explicitly selected discovery versions 5 onward. Preserve the existing runner, dispatch, and environment behavior for versions 1 through 4. The v5 acceptance fixture uses the actual version-gated entry point and checks persistence of its worker evidence.

**My choice:** Use a fresh child even for one task. An explicit child environment gives the launch-order guarantee without changing the shared parent environment. One mandatory startup record per launched child proves coverage without relying on scheduling.

### 5. Resolve the dependency and deliver an applicable patch with meaningful tests

**Where:** [Amendment 2, lines 101–111](C:/Projetos/refute/docs/plans/v0.5.13-charter-amendment-2.md:101), [runner patch headers](C:/Projetos/refute/docs/plans/v0.5.13-amendment-2/runner.patch:1), [test patch, lines 1–26](C:/Projetos/refute/docs/plans/v0.5.13-amendment-2/test_runner_blas_pin.diff:1), [approved charter, stops and scope](C:/Projetos/refute/docs/plans/v0.5.13-charter.md:537), [approved charter, §12](C:/Projetos/refute/docs/plans/v0.5.13-charter.md:570).

**Blocker.** A fail-closed runtime import still creates a runtime requirement. `threadpoolctl` is transitive in the lock and absent from the project’s direct dependencies. The charter expressly excludes edits to `pyproject.toml` and `uv.lock`. Both proposed patches also target `.cache` paths, and the positive worker test accepts a record with duplicate PIDs or missing task workers. [Project dependencies](C:/Projetos/refute/pyproject.toml:24), [lock entry](C:/Projetos/refute/uv.lock:2580)

**Replace the dependency paragraph with:**

> The v5 runner requires the runtime extra `blas-pin` with `threadpoolctl==3.7.0`. Declare it in `[project.optional-dependencies]` as `blas-pin = ["threadpoolctl==3.7.0"]` and bind its resolution in `uv.lock`. The v5 launch and test manifests explicitly select that extra. This requires a separately reviewed and expressly approved exception to §12 for the exact metadata and lock diff, plus the applicable dependency and execution stops. Until that decision is recorded, keep the runtime diff prepared and #226 stopped. A transitive installation supplies no runtime dependency contract.

**Correct the patch headers** to `a/src/refute/core/runner.py` → `b/src/refute/core/runner.py`, and `/dev/null` → `b/tests/test_runner_blas_pin.py`, with the test `diff --git` paths both under `tests/`. Regenerate the indexes with the revised hunks and include the exact v5 entry-point and dependency diffs required by the chosen design.

**Replace the positive test requirement with:**

> Assert exactly one startup record per launched child, distinct PIDs, and equality of the launched, recorded, and task-executing PID sets. Assert exact task-index coverage and result order. Verify the launch variables in an import-time child fixture and verify both numerical providers in the startup inventory. Exercise a fresh child with a single task and a parent with conflicting settings and already loaded BLAS. Assert that the parent environment and legacy execution are unaffected. Exercise missing verification support, an unchecked or wrong-count second library, and a missing startup acknowledgement through the real worker entry point. Each must reject the batch before it is accepted.

**My choice:** Declare `threadpoolctl` as a v5 runtime extra, behind the explicit charter exception. Environment variables alone cannot supply the effective-count check D1b requires.

### 6. Replace the Step 1 stop rule and exit criterion 1 together

**Where:** [Amendment 2, lines 45–57 and 98–127](C:/Projetos/refute/docs/plans/v0.5.13-charter-amendment-2.md:113), [approved charter, Step 1](C:/Projetos/refute/docs/plans/v0.5.13-charter.md:91), [approved charter, seal and exit criteria](C:/Projetos/refute/docs/plans/v0.5.13-charter.md:244).

**Blocker.** The draft replaces exit criterion 1 but leaves Step 1’s original byte-mismatch rule standing. Its new criterion omits the explicit inherited-default byte comparison and both actual v5 comparisons. It substitutes runner adoption and tests while deferring the only real caller to Part B. Section 3 also defines its reference as ID-BEFORE, which has no v5 golden.

**Replace the operative Step 1 acceptance and stop text and exit criterion 1 with:**

> **#226 passes only when all of the following are evidenced.**
>
> 1. For versions 1 through 4, the inherited-default NR-A1 golden bytes, error outputs, and claim-hash payload match ID-BEFORE in its recorded numerical environment. The dated reproduction sidecar maps each locked claim and tag to the ID-BEFORE record and manifest by hash. It records the inherited thread variables, effective thread counts, both BLAS library identities, versions and threading layers, Python, NumPy, SciPy, OS, and processor affinity. The sidecar records the verified reproduction environment for these fixtures. No v1–v4 pin or code change is authorized.
> 2. The existing 1-thread and 4-thread records each pass the amended decision-identity comparator and complete margin check, with the required per-setting tag evidence. Preserve the original NR-A1 `STOP` and D1a records. The new result is a dated assessment under the amended rule. Apply the same rule to any additional authorized thread setting while matching the other numerical-environment inputs. Report untested settings as unverified.
> 3. For v5, freeze a separate synthetic golden fixture and reference under an approved manifest before the comparison. An independently launched replay through the approved v5 entry point at one effective BLAS thread per worker must match every v5 golden byte. At 4 threads and the recorded inherited-default setting, compare against that same v5 reference using the complete decision-identity rule. Use a separately authorized verification harness for alternate settings, with the same scientific code, inputs and configuration and effective-count evidence. The production entry point continues to refuse any count other than one. The exact v5 source diff, any dependency exception, and the execution manifests require their applicable approvals. Pin unit tests and worker records are required evidence and do not substitute for either v5 golden comparison.
> 4. The historical CI mechanism remains a declared limit of F-1. Its resolution is outside this check.
>
> This replaces the conflicting Step 1 acceptance language and the Step 1 clause of stop 2. Any required mismatch, missing result, failed margin, or unverified pin leaves #226 unmet and Part A stopped before #227. The separate source and dependency stops, Steps 2–5, and exit criteria 2–6 continue to apply. At the seal, the named ID-AFTER verifies legacy byte identity in ID-BEFORE’s recorded environment, claim-hash identity, and all ten locked-claim checks, as required by criterion 5. Amendment review and adoption alone authorize no rerun or source change.

**My choice:** Keep actual v5 evidence in criterion 1, as D1b directs. If the v5 entry point or fixture cannot exist before Part B under the approved sequence, #226 stays stopped until the maintainer resolves that sequencing conflict through a separate rule decision and blind review.

## 3. Non-blocking items

- **Keep the disclosure and limits.** The draft correctly dates the proposal, discloses the known `2.12e-9`, labels D1a post hoc, and keeps the historical CI mechanism unresolved. F-1 showed a sufficient factor on one machine. [F-1 closure record](C:/Projetos/refute/docs/validation/v0.5.12/close/issue-blas-threads.md:7)
- **Publish a small review index with the revised package.** The linked amendment README is absent. Use it to identify the exact reviewed artifacts and hashes, including the reproduction sidecar and comparison manifest. The current cached golden bytes matched their recorded hashes, so they provide inputs for a later authorized comparator. [Draft review-record link](C:/Projetos/refute/docs/plans/v0.5.13-charter-amendment-2.md:13)