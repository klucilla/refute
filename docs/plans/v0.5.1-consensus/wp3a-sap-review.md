## Verdict: WEAKENED

The WP3 (a) approach is mostly aligned, and the version 3 wiring is correctly isolated. The SAP applicability rule needs an explicit acceptance amendment, and the current pooling uses a single median CROWDSAP where the per-sector calculation requires sector-specific values.

## Numbered objections

1. **The affine interpretation fits the apparent intent, but changes the written criterion.** The acceptance says “identical up to a constant factor,” while the synthetic generator uses `SAP = 1 + CROWDSAP × (PDCSAP − 1)`, an affine relation. The draft’s `sap_identical` checks equality of normalized series, so it will not recognize that synthetic case. The resulting SAP check can be applicable and detectable despite carrying no systematics-correction information. See the [acceptance](C:/Projetos/refute/docs/plans/v0.5.1-acceptance.md:248) and [synthetic generator](C:/Projetos/refute/src/refute/packs/tess/synthetic.py:346).

   **Change required:** Amend WP3 (a) to define “no correction” as an exact affine relationship, including the fitting domain and tolerance. That interpretation is consistent with the stated purpose and synthetic example, but it is not what the current wording literally specifies.

2. **The proposed absolute tolerance is reasonable, but needs a stated guard and rationale.** A fixed `1e-9` maximum residual on normalized flux is preferable to a tolerance scaled to sector scatter: a scatter-relative cutoff can become too permissive when the sector is noisy, masking a real departure from affine behavior. But the acceptance does not currently authorize that threshold, and a least-squares fit is uninformative with too few cadences or negligible PDCSAP variation.

   **Change required:** In the amendment, state the absolute normalized-flux tolerance and require enough finite cadences and sufficient PDCSAP variation to make the fit identifiable. The value `1e-9` is plausible for numerical residuals, but I cannot establish it as calibrated from read-only inspection alone.

3. **The difference series is constructed as specified, but the pooled comparison uses the wrong crowding scalar when sectors differ.** The draft forms the required normalized SAP-minus-expected series separately by sector. It then pools the sectors, sets `crowd` to the median CROWDSAP, and uses that scalar for `expected = crowd * g_pdc.mean` and in `sap_block`. That can misstate both the relative difference and sensitivity alternative when sectors have different CROWDSAP values. See [difference construction and pooled comparison](C:/Projetos/refute/src/refute/packs/tess/battery_v51_diff.py:402).

   **Change required:** Compute the expected depth using sector-specific CROWDSAP with the same per-event/group weighting used for the measured difference, and use that same expected-depth construction in the SAP sensitivity simulation.

4. **The A0 error, pseudo-window correlation, registry, and v3 pipeline are otherwise consistent with WP3 (a).** `a0_depth` uses per-event A0 errors and the A0 group variance, and returns `None` for nonpositive event errors or an uncalibrated group error. `window_correlation` pairs pseudo-window values by sector and center and requires A0’s minimum pair count. The conditional `sap: rule?` registry entry matches the explicit not-applicable block; if a required sensitivity block is missing, the sensitivity enforcer refuses a PASS. In the pipeline, version 3 calls the draft checks before the v0.5 path, while older plans retain the existing checks. See [A0 group calculation](C:/Projetos/refute/src/refute/packs/tess/battery_v51_diff.py:105), [correlation](C:/Projetos/refute/src/refute/packs/tess/battery_v51_diff.py:120), [registry](C:/Projetos/refute/src/refute/packs/tess/power.py:54), and [pipeline branches](C:/Projetos/refute/src/refute/packs/tess/pipeline.py:396).

   **Change required:** No change identified here beyond the sector-specific CROWDSAP correction in objection 3. Keep the no-correlation case from producing a detectable block; consider making its inconclusive reason explicit in the result.

Read-only review only; I did not run tests.

