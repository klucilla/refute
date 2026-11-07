## Question 1: Does #212 affect a v0.5.1 criterion?

**Verdict: WEAKENED** for Claude’s position. The reported runs do not show a changed final candidate, verdict, or test status, so they do not establish that a calibration gate fails. But “no criterion is affected” is too categorical.

1. **Important, cross-machine dossier reproducibility is underspecified.**  
   **Evidence:** The plan says the v0.4 and v0.5 batteries must stay reproducible, and row 5.2(b) compares a re-run with a recorded dossier using `check-dossier --against`. The reported stage-1 periods differ by roughly \(2–3\times10^{-4}\), well beyond the stated \(10^{-6}\) key-value tolerance if those diagnostics are compared. The plan and row 5.2 do not specify that reproduction is limited to the maintainer’s machine.  
   **Exact change required:** State whether exact reproduction is guaranteed only in the recorded environment. If cross-machine reproduction is intended, add a multi-platform replay criterion that checks candidate, verdict, and test statuses and specifies how platform-sensitive diagnostics are handled. Otherwise, document the environment needed for the existing reproduction command.

2. **Moderate, row 5.4 is not itself a cross-machine determinism requirement.**  
   **Evidence:** Row 5.4 requires the packaging rehearsal to pass end to end and run in CI. That does not require byte-identical outputs across CI platforms. But if the rehearsal asserts fixed search values or outcomes that depend on near-tied BLS peaks, #212 could make those assertions platform-sensitive.  
   **Exact change required:** Have the rehearsal assert the intended invariant outputs across CI, such as candidate, verdict, and test statuses, and avoid requiring exact equality for the affected diagnostics unless determinism is separately established.

Rows 5.3’s stated comparison is only statuses and verdicts, and the reported cases kept the same candidate. The current evidence therefore does not show that row 5.3 fails. The concern is the broader reproduction wording and any future CI assertion that treats the drifting diagnostics as fixed outputs. Relevant text: [v0.5.1 plan](C:/Projetos/refute/docs/plans/v0.5.1-plan.md:34), [acceptance rows 5.2–5.4](C:/Projetos/refute/docs/plans/v0.5.1-acceptance.md:498).

## Question 2: Row 5.2 after the v0.1 re-execution

**Verdict: REFUTED** for Claude’s overall position. The historical cause is supported, but the claim that row 5.2 is met, and the proposal to replace the approved check, are not.

1. **Important, the v0.1 behavior change predates v0.5.1.**  
   **Evidence:** Current `DataParams.target_pixel_files` defaults to `True`; the omitted `GauntletParams` entries, including `centroid_shift`, also receive defaults. The v0.1 claim omits those v0.2 additions. The reported history identifies their introduction in `deaa4eb`. This supports Claude’s point that the divergence is not a new v0.5.1 regression. See [params.py](C:/Projetos/refute/src/refute/packs/tess/params.py:32) and the [v0.1 claim](C:/Projetos/refute/calibration/self_claim.yaml).

2. **Critical, point 2 misreads the approved row.**  
   **Evidence:** Row 5.2 requires historical claim outputs on recorded fixtures to match, including verdicts, reasons, and `verdict.json`. The approved round-two design explicitly says one archived dossier per version is re-executed to cover that row. Historical reproduction at the locked commit answers a different question. Likewise, matching differential bytes in row 5.2(a) and resolved claim hashes do not establish that later code reproduces recorded dossier results.  
   **Exact change required:** Keep the row 5.2(b) re-execution as approved, report the v0.1 failure, and run the selected v0.2, v0.4, and v0.5 dossiers before proposing any replacement criterion. The approved design and current row are [round-two WP5 design](C:/Projetos/refute/docs/plans/v0.5.1-consensus/wp5-design-round-2-answer.md:9) and [acceptance row 5.2](C:/Projetos/refute/docs/plans/v0.5.1-acceptance.md:498).

3. **Important, the v0.1 outcome is a valid non-reproduction result, but it does not isolate code from changed inputs.**  
   **Evidence:** The script resolves the claim with current defaults and runs the recorded calibration stage, which is appropriate for testing current-code behavior. The recorded report shows matching light-curve hashes, but changed TIC and neighbor records, two fetched pixel files absent from the historical dossier, and a `centroid_shift` failure. v0.1 has no discover stage to misapply and no catalog attachment to place. So the plan resolution is intentional and catalog/stage handling does not explain the failure, but the result combines changed defaults with newly fetched inputs.  
   **Exact change required:** Describe this result as “not reproduced under the fixed rule with current-code inputs,” and do not attribute the `centroid_shift` failure to code alone. Keep the recorded input differences alongside the verdict.

4. **Important, the script’s success predicate does not enforce byte identity.**  
   **Evidence:** It records `verdict_json_byte_identical`, but the `reproduced` predicate checks only `check.ok`, verdict equality, and reason equality. That could mark a later version reproduced even when `verdict.json` bytes differ, contrary to row 5.2’s wording.  
   **Exact change required:** Require `verdict_json_byte_identical` in the predicate, or obtain an explicit acceptance amendment that narrows the byte-identity condition. See [reproduce_dossiers.py](C:/Projetos/refute/docs/validation/v0.5.1/wp5/reproduce_dossiers.py:421).

**Recommendation:** Choose option **(iii)**, run the remaining versions under the approved procedure and report each result. Option (ii) changes the agreed check and needs new approval; row 5.2(a) plus hash compatibility is not a substitute. This was a read-only review; I did not run the reproduction script or tests.

