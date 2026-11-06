## Verdict: WEAKENED

The diagnosis is read correctly, but the acceptance section does not yet support its false-failure claim at the stated rate, and it misses a key planet-side risk for the four-harmonic change.

## Objections

1. **High, the false-failure band is not measurable with 200 cases per group.** Row 3c.2’s limit of 0.0027 is roughly 1 in 370. With 200 cases, even zero observed fatal failures cannot establish that rate with a useful confidence bound. The comparison to the v0.5 count does not fix that.

   **Change 3c.2 to:** “P and PG, 1,400 cases per family and A0 noise model, full chain; report the paired v0.5 comparison and the exact one-sided 97.5% binomial upper bound on the fatal `period_alias` false-failure rate; the upper bound must be at most 0.0027.” If the sample size stays at 200, report the bound and do not claim the 0.0027 criterion was demonstrated.

2. **High, four harmonics could partly absorb a real transit on a variable host.** The current planet cases do not say they include V1/V2 variability, while the V1/V2 row tests variable stars without a planet. A periodic stellar signal near the candidate’s period is exactly where a more flexible Fourier model could reduce the box’s incremental fit and cause a fatal FAIL.

   **Add a row:** “Planets in P and PG on V1 and V2 hosts, with stellar periods at the candidate period and near its harmonics, full chain; measure fatal false-failures against the same bound as 3c.2, with paired v0.5 counts.” This directly tests whether a real transit is preserved when variability and transit coexist.

3. **Medium, four harmonics is a reasonable provisional choice, not a general diagnosis.** The JSON shows all three variants reached 50/50, but only on this control. Four harmonics changes the model’s flexibility while preserving the existing detrending. A one-period window could distort or absorb transit shape through its shorter local baseline; removing detrending makes behavior depend more heavily on upstream flattening. Those tradeoffs make four harmonics the least disruptive of the three candidates, but the single control does not establish it as generally safe.

   **Change:** replace “Four is the smallest number that absorbed the distortion on the development control …” with “Four is the provisional, least-invasive choice among the tested variants; the development control does not establish it as generally optimal. Rows 3c.2 and the added planet-plus-V1/V2 row determine whether it is acceptable.” Keep two harmonics for the historical claims.

4. **Medium, the sensitivity “bands” need an explicit acceptance rule.** Rows 3c.3 and 3c.4 give point-rate language without stating whether the threshold is a raw fraction or a binomial confidence band. The 100-realization sensitivity rule has the same ambiguity: observing 90 failures out of 100 is not strong evidence that the true probability is at least 0.9.

   **Change 3c.3 to:** “FAIL rate has an exact one-sided 95% binomial lower bound of at least 0.9, reported per noise model.” For 3c.4, report the paired difference and a confidence interval for the change from v0.5, alongside the absolute V1/V2 FAIL rates. For 3c.5, define detectability by an exact one-sided lower confidence bound of at least 0.9, rather than a raw count of 90/100.

5. **Medium, the development-control case needs a reproducible fixture requirement.** `.cache/v051/dev/` is local cache data, and the section says these cases run offline on recorded fixtures. The JSON hashes and fetch record document identity, but the acceptance text does not ensure the bytes are available to a later offline run.

   **Change 3c.1 to:** “The development-control light curves are supplied as a recorded, checksum-verified acceptance fixture; absent fixture is an incomplete acceptance run. With 4 harmonics, the control’s PASS is detectable and reported.”

## Sabotage

The two-harmonic sabotage on 3c.1 is measurable: 43/50 is below the stated 90% sensitivity threshold. The 3c.3 sabotage clause is weaker because it says to report the result if the band does not fall, rather than making the sabotage fail.

**Change the sabotage text to:** “With 2 harmonics in version 3, 3c.1 must fail its sensitivity criterion. Report 3c.3 under sabotage as a mechanism diagnostic, not as a required sabotage failure.” The synthetic check on clean sectors did not reproduce the problem, so the segment-edge claim should remain something to measure, not assume.

## Points I Agree With

- The diagnosis is accurate: `alias-dev-control.json` records 43 FAILs as-is and 50 FAILs for each of four harmonics, no detrending, and a one-period window. Here FAIL means the test recognized the injected pure sinusoid, so 43/50 is below the 90% sensitivity rule.
- The result supports the proposed mechanism on this control: the test’s three-period detrending window can distort the sinusoid enough that two harmonics do not absorb it. The clean-sector synthetic check did not reproduce that behavior, so it does not establish the mechanism broadly.
- Four harmonics is the most defensible provisional variant because it leaves detrending and the BIC rule unchanged. The one-period and no-detrending variants also passed this control, but bring separate preprocessing and transit-attenuation risks.
- Keeping historical v0.4/v0.5 behavior unchanged and requiring full-chain planet and variable-star checks are good scope boundaries.

Read-only review only; no files or runtime state were changed.

