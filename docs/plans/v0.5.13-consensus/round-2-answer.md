## 1. Round-one application

All seven replacements are present in `a7fba55`. **APPLIED** means the replacement is in the draft. The surrounding text still has conflicts listed below.

| Item | Status | Where applied |
|---|---|---|
| 1. Ordered preconditions, BLAS identity, and #227 assertions | `APPLIED` | [Order and steps 1–2](/C:/Projetos/refute/docs/plans/v0.5.13-charter.md:55) |
| 2. Synthetic and real F1 injections, controls, and correction rule | `APPLIED` | [Synthetic experiment](/C:/Projetos/refute/docs/plans/v0.5.13-charter.md:110), [real panel](/C:/Projetos/refute/docs/plans/v0.5.13-charter.md:138) |
| 3. Code-emitted reasons, denominators, strata, and symmetry | `APPLIED` | [Reason map](/C:/Projetos/refute/docs/plans/v0.5.13-charter.md:199), [AND rules](/C:/Projetos/refute/docs/plans/v0.5.13-charter.md:262) |
| 4. Full joint power | `APPLIED` | [Planning model and calculator](/C:/Projetos/refute/docs/plans/v0.5.13-charter.md:289) |
| 5. Exposed-only scope and qualified exposure findings | `APPLIED` | [Part B scope](/C:/Projetos/refute/docs/plans/v0.5.13-charter.md:243), [exposure audit](/C:/Projetos/refute/docs/plans/v0.5.13-charter.md:325) |
| 6. Meter, retry classes, order proof, decisions, and gate | `APPLIED` | [Section 8](/C:/Projetos/refute/docs/plans/v0.5.13-charter.md:391) |
| 7. Split, time box, and comparator annex | `APPLIED` | [Split](/C:/Projetos/refute/docs/plans/v0.5.13-charter.md:36), [annex](/C:/Projetos/refute/docs/plans/v0.5.13-charter.md:380), [time box](/C:/Projetos/refute/docs/plans/v0.5.13-charter.md:478) |

## 2. Blocking defects in the integrated draft

1. **The surrounding text reopens the ordered preconditions.** Line 61 lets step 4 change `src/` alongside #224. Lines 223–224 make an answered stop an alternative branch of the #226 exit criterion, and lines 376–377 let recorded stops stand in for Part A’s passed preconditions. Those clauses should agree with the ordered checks and hard stop in B1(a). [Step order](/C:/Projetos/refute/docs/plans/v0.5.13-charter.md:61), [exit criterion](/C:/Projetos/refute/docs/plans/v0.5.13-charter.md:223), [Part A product](/C:/Projetos/refute/docs/plans/v0.5.13-charter.md:376)

   **Replace line 61:**

   > Step 4 begins after #224 passes. Step 5 begins after the step 4 check passes.

   **Replace exit criterion 1:**

   > **#226 passed.** Every required comparison passed and the maintainer’s pin decision is recorded. Any adopted pin was approved against its exact diff. A byte mismatch, missing output or unverified pin stops Part A and leaves #226 unmet. Following any separately authorized corrective action, all required comparisons must pass before Part A advances.

   **Replace the Part A product bullet:**

   > **Part A’s product:** evidence that the three preconditions passed, the tested reason map and the frozen targets of section 5. If a precondition stops the phase, record it as unmet and preserve its evidence.

2. **The real follow-up can regenerate the same injections, and a missing null result can evade the zero-abstention rule.** Lines 157–158 and 192–193 derive the slots from a seed fixed at charter approval. With the same TICs and slots, that recipe conflicts with the fresh-injection requirement at lines 133–135. Lines 178–185 retain non-evaluable slots in the denominator without explicitly counting them as `not_assessed`. A planned denominator alone would let a missing result reduce the observed null rejection rate. [Real-curve seed and loss rules](/C:/Projetos/refute/docs/plans/v0.5.13-charter.md:157)

   **Replace the charter-seed bullet and add the loss sentence before the panel thresholds:**

   > The base seed is SHA-256 of the lowercase hexadecimal approval commit ID encoded as ASCII. Derive each real-panel slot seed from the base seed, the preapproved measurement ID, the TIC and the slot number. The initial panel uses its own measurement ID. Each approved follow-up uses a different ID and must pass a geometry and input-identity collision check against prior panels before F1 runs. Freeze the derivation and the check in the pushed manifest.
   >
   > A missing, exhausted or non-evaluable planned null or red-control slot counts as `not_assessed` in its activity class and fails that class’s zero-`not_assessed` requirement.

3. **The proof and retry rules leave gaps at the execution boundaries.** Lines 65–68 and 217–219 identify the before and after computations, but the new retry wording requires separately named authorizations for golden computations, and NR-A1 only names step 1. Lines 439–442 also require case IDs in a manifest pushed *before* a draw. That must mean the eligible input frame, since the drawn IDs do not yet exist. Finally, “every execution resumable” at line 476 can be read to allow restarting a failed scientific case without the approval required by §8 and `CLAUDE.md:94–98`. [Identity proofs](/C:/Projetos/refute/docs/plans/v0.5.13-charter.md:65), [order proof](/C:/Projetos/refute/docs/plans/v0.5.13-charter.md:437), [resume rule](/C:/Projetos/refute/docs/plans/v0.5.13-charter.md:472)

   **Add to step 0 and cross-reference from step 5:**

   > This charter authorizes two named identity units, `ID-BEFORE` at step 0 and `ID-AFTER` at step 5, once each. Their sole purpose is to establish protected identity. Use the committed `golden-local`, `claim-hashes` and `verify_locked_tags.py` procedures with the corresponding before or after label and the same protected fixture and tag lists. Push each manifest with the exact commands, inputs, output paths and comparison before execution. NR-A1 covers only the three step 1 settings.

   **Replace the manifest-binding sentence in §8:**

   > The evidence commit binds the source SHA, commands, input and configuration hashes, and trigger. For a draw it binds the ordered eligible input frame and seed. For a probe or measurement it binds the already determined case IDs. Push the draw output before any acquisition or probe that uses it.

   **Replace “every execution resumable”:**

   > Checkpoint at committed batch boundaries. A restart may proceed with independently manifested batches that have never started. Re-executing a started scientific batch or case requires prior #218 approval of the reason and exact procedure, including when no case value was emitted.

4. **The network allowance covers selected products, but the selection requires screening products first.** Lines 420–421 authorize MAST reads for “selected” DEV products. Lines 141–155 require reading the eligible pool products to classify activity before choosing the panel. Line 469 also says downloads are zero otherwise, despite §8 requiring transfer accounting for the other network units. [Panel selection](/C:/Projetos/refute/docs/plans/v0.5.13-charter.md:141), [network units](/C:/Projetos/refute/docs/plans/v0.5.13-charter.md:420), [download cap](/C:/Projetos/refute/docs/plans/v0.5.13-charter.md:469)

   **Replace the MAST allowance and the download-cap basis:**

   > MAST reads are authorized only for reconciled DEV products on the pushed screening manifest, including candidates screened for activity before the final panel is selected. Apply the 40 DEV-H and 40 DEV-T limits, the fallback rule and the exposure check before the corresponding reads.
   >
   > The 3 GB ceiling covers all phase-local inbound bytes from authorized network units, including partial transfers and retries. The only authorized scientific downloads are the manifested DEV products. Record remote CI and reviewer costs separately as specified in section 8.

5. **The seal is asked to account for work that happens after it.** Lines 415–418 put review and closure costs into the seal reconciliation. Lines 451–457 place the final reviews after the seal, against its pushed SHA. The charter needs a defined way to charge that tail without changing the reviewed snapshot or approving a report against stale accounting. [Accounting clause](/C:/Projetos/refute/docs/plans/v0.5.13-charter.md:413), [review order](/C:/Projetos/refute/docs/plans/v0.5.13-charter.md:451)

   **Replace the reconciliation and criterion sentences:**

   > At the seal, reconcile all execution through the sealed journal cursor and reserve headroom for the final review, gate and closure. Review the sealed SHA. Append the post-seal receipts and reconcile the full tail before report approval within the applicable time box and stops. The accounting criterion passes only when the final reconciled caps were measured and met and every outside-meter execution was recorded at once with its estimated cost. If the tail changes a control finding or criterion status, record the change and return to the maintainer before approval.

6. **The rewritten Dallas paragraph retains an unsupported licence statement.** Line 367 asserts CC BY 4.0 without the nearby `sources/` excerpt required by `CLAUDE.md:251–256`. The exposure finding does not depend on the paper’s licence. [Dallas paragraph](/C:/Projetos/refute/docs/plans/v0.5.13-charter.md:366)

   **Replace the parenthetical at lines 366–367:**

   > (arXiv:2610.32949, https://arxiv.org/abs/2610.32949, read on 2026-11-26, PASP 138, 104504. Licence unconfirmed here.)

## 3. `power_v2.py`

**Yes.** It implements the full §5 AND rule under the frozen planning model.

- **Shared counts.** The code enumerates assessed counts by band, then retained planets or surviving FPs conditional on those counts. It applies both the band and pooled outcome bounds to the same outcomes. [Arm enumeration](/C:/Projetos/refute/docs/plans/v0.5.13-charter-prep/power_v2.py:63)
- **Coverage and empty bands.** Both coverage bounds use all frozen cases in the relevant denominator. A band with zero assessed cases is rejected explicitly. A band with zero frozen cases also fails. [Coverage checks](/C:/Projetos/refute/docs/plans/v0.5.13-charter-prep/power_v2.py:69)
- **Signed symmetry.** It derives abstentions from those same assessed counts and checks both Newcombe endpoints against `[-0.15, 0.15]`. It multiplies the independent arm masses under the planning model and applies symmetry to each pair. [Symmetry and joint sum](/C:/Projetos/refute/docs/plans/v0.5.13-charter-prep/power_v2.py:107)

My independent in-memory enumeration gave **0.9459418125**, which rounds to the committed **0.945942**. I reviewed the pinned files without running the preparation scripts. [Committed result](/C:/Projetos/refute/docs/plans/v0.5.13-charter-prep/power-v2.json)

## 4. Verdict

**`NOT_APPROVABLE`**. The round-one choices and joint-power calculation stand. The remaining fixes are to the charter’s ordering, execution permissions, loss handling, and accounting.