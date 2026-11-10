Part B is a legitimate development forecast, and B’s derivation is exact under the stated controls. Its denominator, reconstruction checks, uncertainty, and attribution need corrections.

1. **A, MEDIUM: 20 is a validation boundary, not a limit inherent in selecting four sectors.**  
   [Design section 2](C:/Projetos/refute/docs/plans/v0.5.2-stage2-design.md:89) declares selector constructions at 5, 8, 12 and 20 original sectors, then limits support to 20. This first appears in commit `f400fd3`. The preceding consensus requested a bounded domain or justification for unrestricted use; it did not establish a special statistical breakpoint at 20. I found no measurement establishing such a breakpoint.

   **Require:** describe the refusal as protection against applying A0 calibration outside the selector’s declared validation domain. It counts all sectors in the loaded light curve, even sectors the selector subsequently discards.

2. **A, HIGH: certification through 20 does not automatically transfer to 21–42, or arbitrary counts.**  
   The selection rule is flux-blind **conditional on the fitted ephemeris and cadences**. More original sectors can change that ephemeris, the selected quartet, preprocessing, and the secondary-eclipse decision controlling phase-half exclusion. In particular, [the production path](C:/Projetos/refute/src/refute/packs/tess/pipeline_v52.py:34) performs relevant operations on the full series before restricting measurements to selected sectors.

   **Require:** amend support prospectively to a finite domain, practically through 42, and extend the selector family. Cover the additional counts directly or justify a conservative envelope covering them, including noise differences, gaps, coverage, fitted ephemerides and the complete production preprocessing. Preserve the simultaneous equivalence bounds and familywise error, size the expanded family, and reprice it before acceptance. The existing 135 CPU-h selector estimate does not establish the extension’s cost. Supporting **any** count requires an argument uniform in count and observing geometry; testing 42 alone would not provide that.

   The incentive is substantial but does not supply certification: using the stated counts, the cap leaves at most \(559/615=0.90894\). The historical baseline is \(613/615\), so the minimum is **0.89675**, requiring at least **552 kept injections**. Only seven additional losses fit below that ceiling.

3. **B, LOW: deriving scenario B without another battery run is sound.**  
   In [the refusal logic](C:/Projetos/refute/src/refute/packs/tess/battery_v52.py:74), the cap is checked before certification. Consequently, B equals C through 20 original sectors and A above 20. A equals C through four sectors.

   **Require:** hold every other flag, input and candidate fixed; use the actual loaded sector count; restore the forecast-only constant patch reliably; and assert identical final candidates across batteries, as `paired_chain` does. Do not infer zero sectors when selection metadata is absent. C must remain explicitly counterfactual: forcing `selector_certified=True` supplies no certification evidence.

4. **B, HIGH: matching FITS hashes does not authenticate every scientific input.**  
   `TessAdapter.fetch` also queries current stellar properties and neighbours. Those can change injection generation or battery results while every FITS SHA-256 remains identical. Checking only the historical candidate and stage verdict can miss changes elsewhere in the reference computation.

   **Require:** authenticate the complete file-name/hash set, historical stellar and neighbour inputs, quality filtering, catalogs, plans and injection parameters. Reuse authenticated historical metadata where available. Apply the existing C2 compatibility comparison to the relevant historical measurement fields, including gate and recovery identity, rather than only candidate and stage verdict.

   A mismatch should remain recorded and block a comparable target forecast until resolved. The current [draft implementation](C:/Projetos/refute/docs/validation/v0.5.2/stage2/forecast_t2a.py:251) merely counts mismatch flags and still includes those rows in `meets_minimum`.

5. **B, HIGH: exclusions must not silently change the 615-injection estimand.**  
   Changed files, retrieval failures and execution errors can correlate with sector count and difficulty. Removing their hosts and calculating success among the remaining rows can produce an optimistic forecast.

   **Require:** retain the frozen population and sampled IDs. Report unavailable outcomes explicitly, with pessimistic and optimistic bounds for their contribution. A comparison restricted to authenticated hosts may also be reported, but label its changed population and corresponding baseline separately. Do not replace failed hosts opportunistically or redefine eligibility using newly recovered injections.

6. **B, MEDIUM: stratified sampling is legitimate, but Wilson intervals do not describe the weighted total’s uncertainty.**  
   The historical strata contain **302, 257 and 56 injections**. Seeded sampling without replacement within those fixed strata, weighted by these population counts, estimates this finite benchmark correctly when outcomes are complete. Shared hosts do not invalidate that finite-population sampling argument. They matter if the result is generalized to other hosts.

   **Require:** freeze allocation, seed, sample IDs and any cost-driven fallback before examining outcomes. For aggregate uncertainty, use a stratified finite-population interval. One conservative implementation is simultaneous hypergeometric intervals for the strata, combined using their fixed weights. Marginal Wilson intervals may remain descriptive, clearly labelled. Keep the known historical baseline fixed when expressing uncertainty around the target comparison.

   Budget-truncated completion is not a random sample. Missing paired units must remain unknown. Likewise, 120 synthetic planets does not guarantee 20 eligible cases in either D2 or D4’s separate subset.

7. **B, MEDIUM: per-rule attribution is not currently causal or complete.**  
   Multiple tests can block one injection. The draft’s priority chain assigns one explanation and hides coexisting blockers. It also retains only the refusal string and original count, discarding chosen and contributing sectors. Its sinusoid status comes from the raw gauntlet, whereas the reported verdict follows coverage, sensitivity and stage processing.

   **Require:** retain complete selection metadata and final test statuses, severity, decisive roles and stage deferrals. Report overlapping blockers. Separately report the exact paired transitions A→B and B→C, which isolate the effects of those scenario changes. If an exclusive priority table is useful, label it an accounting convention. “Measured sector count outside the grid” is an observed refusal, not proof that the comb mask caused the loss.

8. **B, MEDIUM: this is development reuse, provided the historical artifacts remain untouched.**  
   The v0.5 C2 records and dossiers are explicitly designated development data in [the v0.5.1 plan](C:/Projetos/refute/docs/plans/v0.5.1-plan.md:181). Reconstructing them for this authorized forecast neither consumes fresh confirmation data nor reruns acceptance. The [maintainer’s decision](https://github.com/klucilla/refute/issues/216#issuecomment-6769733025) explicitly permits the forecast while adequacy continues blocking acceptance.

   **Require:** use a separate cache and new forecast artifacts, preserve all anchored records and dossiers, and fingerprint historical inputs and scenario settings. Reuse reconstruction helpers rather than invoking old workflow steps that write historical output paths. No forecast result may clear the adequacy gate.

9. **B, HIGH: enforce the shared budget and STOP operationally.**  
   The draft T2a cap subtracts D2/D4 spending, but that snapshot does not by itself enforce a cumulative 20 CPU-h limit across both parts and all attempts. The summaries also print failing comparisons without registering a persistent target-failure STOP.

   **Require:** one cumulative forecast budget including previous attempts and overhead, with coordinated dispatch. Persist any required planet-target STOP and prevent subsequent acceptance or budget-dependent work. Freeze the interpretation of sampled uncertainty beforehand: an interval crossing the threshold is unresolved, not evidence of success. A favourable C forecast cannot override an uncertified production configuration.

WEAKENED