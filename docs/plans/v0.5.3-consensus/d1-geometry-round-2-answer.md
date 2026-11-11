1. **Cost/gate, applied and correct:** [d1_geometry.py:26](/C:/Projetos/refute/docs/validation/v0.5.3/stageA/d1_geometry.py:26). The 7.7 CPU-h estimate is supported. The execution gate remains operational, rather than enforced here. **Six hours remaining alone is insufficient:** the computed cap subtracts a 4 CPU-h reserve and divides by 1.10. Approximately **12.5 CPU-h remaining** supports the present estimate; retain the checkpoint’s binding cap check.

2. **Threshold, applied and correct:** [d1_geometry.py:174](/C:/Projetos/refute/docs/validation/v0.5.3/stageA/d1_geometry.py:174). The maximum of the separate family quantiles provides the stated empirical control for both families. Noise pooling and the calibration-sample qualification are appropriate.

3. **Fingerprint, applied and correct:** [d1_geometry.py:88](/C:/Projetos/refute/docs/validation/v0.5.3/stageA/d1_geometry.py:88). Both wrappers, the historical JSONL and the v0.4 claim are now covered.

4. **Checkpoint, partially applied:** [d1_geometry.py:122](/C:/Projetos/refute/docs/validation/v0.5.3/stageA/d1_geometry.py:122) correctly fixes the projection units. **Remaining blocker:** the family coverage requested in round 1 is absent at [d1_geometry.py:65](/C:/Projetos/refute/docs/validation/v0.5.3/stageA/d1_geometry.py:65). The actual probe is `P-0150, P-0630, PG-0310, PG-0770, EB2-0290`, with **no EB1**. Reorder or interleave the schedule so the frozen checkpoint includes all four families.

5. **Reporting, applied and correct:** [d1_geometry.py:137](/C:/Projetos/refute/docs/validation/v0.5.3/stageA/d1_geometry.py:137), [:180](/C:/Projetos/refute/docs/validation/v0.5.3/stageA/d1_geometry.py:180), [:202](/C:/Projetos/refute/docs/validation/v0.5.3/stageA/d1_geometry.py:202). Strict exceedances handle ties correctly; family counts and folded EB1’s fraction are correct.

6. **Prior verified finding retained:** seeds, reused computation, diagnostic labeling and historical isolation remain unchanged. No correction needed.

**Verdict: Do not run this revision yet. Correct checkpoint coverage; once the full budget gate holds, no other blocking defect remains.**