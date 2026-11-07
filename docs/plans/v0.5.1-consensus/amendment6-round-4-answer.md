# Verdict: WEAKENED

All seven objections from rounds 1–3 are applied in commit `20e6e60`. The plan and acceptance agree on the affine rule, operational cutoffs, propagation, and measurement rows. The sensitivity behavior also matches the acceptance. One documentation mismatch remains: the registry comment still describes only the constant-factor case.

## Prior-round objections

1. **Major, content (minimums). Resolved.** The acceptance calls `N_min = 100` and `s_min = 1e-5` provisional operational cutoffs, says they are not mathematical identifiability thresholds, and documents finite-value fitting, standardization, and development evidence. Evidence: [acceptance, lines 257–274](/C:/Projetos/refute/docs/plans/v0.5.1-acceptance.md:257).  
   **Required change:** State the cutoffs as operational conventions, provide the requested development evidence, and specify fit conditioning. **Applied; no further change required.**

2. **Major, content (propagation and development measurement). Resolved.** The paired comparison specifies the same candidate, inputs, and seeds, 4 × 4 verdict tables with denominators for all eligible planets and the D4 subset, status transitions, and the stop conditions. Evidence: [acceptance, lines 301–316](/C:/Projetos/refute/docs/plans/v0.5.1-acceptance.md:301).  
   **Required change:** Define paired outcome fractions and denominators, and specify the D2/D4 stop rule. **Applied; no further change required.**

3. **Moderate, content (row 3a.7). Resolved.** The row requires the not-applicable block with a non-empty reason naming each sector, and records `not_enough_data` for both low-input sectors. Evidence: [acceptance, lines 327–328](/C:/Projetos/refute/docs/plans/v0.5.1-acceptance.md:327).  
   **Required change:** Require the full block shape and explicit per-sector low-input classes. **Applied; no further change required.**

4. **Moderate, content (sabotage). Resolved.** The sabotage verifies both affine sectors meet the cutoffs, requires an applicable block and `detectable: true` on at least one curve, and voids the sabotage if it fails for another reason. Evidence: [acceptance, lines 333–339](/C:/Projetos/refute/docs/plans/v0.5.1-acceptance.md:333).  
   **Required change:** Verify those preconditions and make an unrelated failure invalidate the acceptance. **Applied; no further change required.**

5. **Moderate, content (propagation). Resolved.** A `systematics` PASS requires detectability for every applicable registered rule block, including background and SAP when applicable. The SAP not-applicable block is skipped; the dumps fraction category needs no detectability. Evidence: [acceptance, lines 284–288](/C:/Projetos/refute/docs/plans/v0.5.1-acceptance.md:284), [registry, lines 60–62](/C:/Projetos/refute/src/refute/packs/tess/power.py:60), and [sensitivity rule, lines 162–180](/C:/Projetos/refute/src/refute/core/sensitivity.py:162).  
   **Required change:** Include every applicable registered rule block in the PASS gate and exempt the fraction category. **Applied; no further change required.**

6. **Moderate, wording (plan’s cutoff description). Resolved.** The plan now calls the cutoffs operational and provisional, not mathematical identifiability thresholds, consistent with the acceptance. Evidence: [plan, lines 500–503](/C:/Projetos/refute/docs/plans/v0.5.1-plan.md:500) and [acceptance, lines 257–262](/C:/Projetos/refute/docs/plans/v0.5.1-acceptance.md:257).  
   **Required change:** Use the operational-cutoff wording in the plan. **Applied; no further change required.**

7. **Moderate, wording (limit and measurement rows). Resolved.** The plan and acceptance both distinguish C1’s limitation from the controlled injected-alternative check in row 3a.5 and the independent-noise false-positive check in row 3a.6. Evidence: [plan, lines 508–513](/C:/Projetos/refute/docs/plans/v0.5.1-plan.md:508), [acceptance, lines 294–299](/C:/Projetos/refute/docs/plans/v0.5.1-acceptance.md:294), and [acceptance, lines 326–327](/C:/Projetos/refute/docs/plans/v0.5.1-acceptance.md:326).  
   **Required change:** Identify row 3a.5 as the controlled power check and row 3a.6 as the false-positive check. **Applied; no further change required.**

## Remaining coherence issue

8. **Moderate, wording (registry comment).** The registry entry is correctly conditional (`"sap": "rule?"`), but its adjacent comment describes non-applicability only for SAP and PDCSAP “identical up to a constant factor.” The acceptance replaces that criterion with the broader exact affine relation, of which the constant-factor case is only a special case. Evidence: [registry, lines 60–62](/C:/Projetos/refute/src/refute/packs/tess/power.py:60) and [acceptance, lines 251–275](/C:/Projetos/refute/docs/plans/v0.5.1-acceptance.md:251).  
   **Required change:** Update the registry comment to describe the exact affine criterion and note that constant factor is its special case. The registry’s actual optional-rule setting and the sensitivity behavior are compatible.

No files were modified or write-capable commands run.

