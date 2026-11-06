# Verdict: **WEAKENED**

The three round-1 changes are present, and the conditional rule, branch-specific A0.8 pulls, and sabotage now match Amendment 5. One contradiction remains: **A0.3 still unconditionally requires pseudo-windows never to share a cadence with the phase-0.5 window.** That conflicts with the new rule allowing those windows when `secondary_eclipse` returns `PASS` or `INCONCLUSIVE`.

**Exact text change:** In A0.3, replace “never sharing a cadence with a real event's window or the phase-0.5 window” with: “never sharing a cadence with a real event’s window; phase-0.5 overlap follows the conditional exclusion rule above.”

This cannot be left to the acceptance run because A0.3 and the new rule prescribe different window sets. The run cannot determine which definition governs.