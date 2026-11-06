# Verdict: **SURVIVED**

The final text is internally consistent:

- **Conditional rule and A0.3:** phase-0.5 windows are excluded only when the candidate’s `secondary_eclipse` returns `FAIL`. A `PASS` or `INCONCLUSIVE` leaves them eligible.
- **INCONCLUSIVE classes:** too few measured events use `not_enough_data`; a non-estimable required correlation uses `insufficient_sensitivity`.
- **A0.8:** injections use the pre-injection phase-0.5 error, and pulls are checked separately for the excluded and included branches. A branch failure invalidates that branch’s errors in the stratum.
- **A0.9 and sabotage:** EB1/EB2 results are reported apart, not made gates. Forced inclusion with a 4σ secondary must fail A0.8; if it does not, A0 cannot proceed.

I found no remaining text change blocking the code change under Amendment 5.