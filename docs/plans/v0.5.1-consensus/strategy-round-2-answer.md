**Verdict: WEAKENED.** The four revisions are applied correctly, with one remaining qualification. My Round 1 wording was too broad on this point.

1. **Important, D2 and T2a have data-dependent kept thresholds.**  
   The rule forces the new battery’s kept fraction to zero. However, both requirements compare it with the paired v0.4 kept fraction minus 0.10 ([plan definitions](/C:/Projetos/refute/docs/plans/v0.5.1-plan.md:25)). If that comparator is at most 0.10, zero satisfies the kept requirement. Therefore, “cannot reach their kept thresholds, whatever the data” is stronger than the rule establishes.

   **Exact change:** Replace that assertion in [section (b)](/C:/Projetos/refute/docs/validation/v0.5.1/feasibility/strategy/README.md:60) with:

   > Under the strict reading, the new battery’s kept fraction is zero regardless of the data. Consequently, D2’s kept requirement and T2a fail whenever their paired v0.4 kept fraction exceeds 0.10, as it does in the recorded development references (0.967 and approximately 0.997). This condition has not been measured on the confirmation data.

   Carry this qualification into the path table and both recommendation paragraphs, removing the unconditional “whatever the data” claim.

The remaining changes are complete: D4 precedence is correct, the power calculation is appropriately qualified, the mask mechanism remains a supported hypothesis, and the calibration arithmetic is approximately 97 hours, giving approximately 160 remaining hours under A. The revised pool, lag, and D1 qualifications are also consistent.

**My recommendation remains B.** This correction requires wording only, with no additional diagnostic.