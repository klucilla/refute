# Verdict: **WEAKENED**

The ordering and main condition are clear: `secondary_eclipse` runs before A0; only `FAIL` excludes phase-0.5 windows; `INCONCLUSIVE` leaves them included. The threshold cases are appropriate, but three details need fixing before this matches Amendment 5.

1. **Critical, the sabotage fallback weakens the maintainer’s required failure condition.** Amendment 5 says the acceptance must fail when the conditional exclusion is removed and a secondary is above threshold. The fallback says that if it does not fail, this is merely reported and the exclusion remains. That does not say whether A0 itself fails acceptance.

   **Exact text change:** Replace the fallback with: “If the forced-inclusion sabotage does not fail A0.8, A0 fails this acceptance condition and cannot proceed to code. The result is reported to the maintainer for a revised proposal.”

2. **Important, aggregate pulls can hide miscalibration in one branch of the conditional rule.** At 2.5σ or 3σ, noise may make `secondary_eclipse` return either `FAIL` or `PASS`/`INCONCLUSIVE`. Those outcomes select different window sets, so a pull band over the combined trials could pass while the included-window branch is miscalibrated. Also, define the reference error used to set injected depths so the injection is not calibrated against its own effect.

   **Exact text change:** In A0.8, define 2.5σ, 3σ, and 4σ depths from the **pre-injection** phase-0.5 error. Require A0.1/A0.2 pulls separately for trials where `secondary_eclipse` returns `FAIL` (windows excluded) and where it returns `PASS` or `INCONCLUSIVE` (windows included), by stratum and injection depth. Add A0.8 to the per-stratum calibration-failure rule for the affected branch.

3. **Important, the fallback class for a missing correlation is wrong.** The text assigns `not_enough_data` both to too few measured events and to a missing group correlation. A non-estimable correlation is already specified as `insufficient_sensitivity`.

   **Exact text change:** Use `not_enough_data` for too few measured events, and `insufficient_sensitivity` when a required correlation is missing.

A0.9’s separate reporting for EB1 and EB2 is consistent with the approval. The changes above are needed because the acceptance text currently leaves the sabotage gate ambiguous, allows branch-level calibration failures to be masked, and conflicts with A0’s existing INCONCLUSIVE classification.