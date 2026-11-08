# v0.5.2 stage 1, experiment E3: the sinusoid under stellar trends (frozen before it runs)

Development seeds only: `int(SHA-256("refute-v052-dev:e3:<case>:<noise>:<i>")[:16], 16)`. Nothing in
`src/` changes (patches inside the experiment's own processes). It decides nothing about any target.
`method_status: not_validated`. Script: [e3_sinusoid.py](e3_sinusoid.py), output `e3-sinusoid.json`.

**Question.** WP3 (b) failed in the two noise models with a stellar trend (false failures of 18 to 25 %
against a limit of 0.27 %). The trend in those models is itself a sinusoid of period 3 to 10 d and
semi-amplitude up to 2000 ppm. Are the failures concentrated where the trend cannot be separated
from a tested harmonic, and does a change of the joint nuisance model help elsewhere without losing
the detection the test exists for?

**The curves** (`acceptance/wp3b.py`, `_planet_curve`: two sectors, period 3.3 d, duration 0.12 d),
noise `trend` and `correlated_trend`:
- **The planets**, the original population: 150 curves per SNR (12, 20) and noise.
- **Supplementary alternatives, kept apart from that population** (SNR 20; 100 curves per noise and
  case; a sinusoid of semi-amplitude 2 depths): at exactly Q = P/2, P, 2P (row 3.8 (a)), counted by
  **Q itself flagged**; and a **near-harmonic control** at `|f - 1/P| T_span = 0.75`, inside the band
  the `narrow` arm opens, counted by P flagged. The registered one-depth alternative is reported
  separately through the test's detectable blocks.

**Arms, on the same curves.** `built` (up to 3 extra frequencies, exclusion `1 / T_span`); `extra6` (up
to 6); `narrow` (exclusion `0.5 / T_span`, 3 extra).

**Recorded per unit:** from the test's own retained cadences, the span, the separation from each
harmonic and the nearest; each harmonic's fitted amplitude, error and significance, and its
detectable block; the raw and the final status; the known noise-free trend projected through the
trial's own selected joint design (the method of row 3.7), giving the amplitude the trend alone would
give at each harmonic. `s >= 1` is a nominal separation category, not established identifiability; a
low injected amplitude is an attribution diagnostic, not proof about the fitted harmonic.

**Tables**, each with Wilson 95 % intervals, per SNR and noise (the alternatives per noise and case),
every scheduled curve in the denominators, raw and final PASS, FAIL and INCONCLUSIVE apart, and the
unconditional result beside every conditional one: the failures by `s` (below 0.5, 0.5 to 1, 1 to 2,
above 2) and by the trend's semi-amplitude over the depth (below 0.5, 0.5 to 1, above 1), cross-tabulated.

**Reading, fixed now (descriptive).**
1. The failures are *concentrated at the unseparated trends* if at least 90 % of the `built` failures,
   per SNR and noise cell, have `s` below 1. Failures from a trend with a semi-amplitude below 0.5
   depths are reported apart. With no failure, concentration is undefined and stated so.
2. A nuisance arm is *worth carrying to the specification* only if, in every SNR and noise cell:
   (a) among the planets with `s >= 1`, the paired change of an adverse endpoint (**a final FAIL or a
   final INCONCLUSIVE**) from `built` has a 95 % interval below 0, the status transitions being
   reported, so that a FAIL turned INCONCLUSIVE earns nothing; (b) that arm's raw failure rate there
   has an upper Wilson bound of at most 0.05, **an exploratory screening threshold**, far from
   certifying the 0.0027 requirement, which stays unresolved; (c) in each exact-harmonic alternative
   cell, the arm's detection is at least 0.90 (an absolute benchmark tied to the 0.95 target) and the
   paired detection change from `built` has a lower 95 % bound above -0.05; (d) on the near-harmonic
   control, the same paired non-regression; (e) at SNR 20, the fraction of planets with every
   applicable harmonic detectable is at least 0.95. An INCONCLUSIVE never counts as a solved case.
   Paired binary changes use a conservative simultaneous interval (exact bounds for the probabilities
   of gain and of loss, each at 97.5 %), so identical pairs do not give zero uncertainty. For any
   alternative cell, including the near-harmonic control, the `built` arm must recover the target at
   least at 0.90; otherwise preservation cannot be judged and the result is NOT ESTABLISHED.

**The population is not changed**: planets with unseparated trends stay in every denominator, and a
result on the separated subset cannot establish acceptance on the unchanged population. If the
unseparated failures are what remains, the conflict between the false-failure limit and the
detectability requirement is reported at the stop.

**Identity and cost.** Records carry a fingerprint (design, script, runner files, code hash, resolved
plan, constants, numpy, scipy, astropy versions), checked at resume and at summary; expected arms and
metadata are validated against each scheduled unit. Any mismatch, an incomplete schedule, a failed
unit, or an undefined statistic that a decision needs gives NOT ESTABLISHED, naming the arm and cell,
with the recommendation null; empty descriptive bins stay null. The records' schema is validated before
any aggregation, and each unit keeps the full per-harmonic sensitivity blocks. **A probe** of 40 units
(covering every case, noise and SNR) records the projected cost before the full run. The run
(`runlib.bounded_run`) checks the spent cost before any dispatch, projects against the whole unfinished
schedule, refuses to continue when that passes **1.5 processor-hours less a 5 % reserve**, sizes each
batch to the remaining budget and counts the CPU of failed units. A run that stops, or whose spent
cost ends above the cap, is NOT ESTABLISHED. **A recorded disagreement with Codex** (its round 3,
objection 3): Codex asks for live enforcement that terminates executing workers at the cap. This
experiment uses batch-level enforcement with a reserve, and a persisted state that the summary checks:
the cap is a budget guard on a 1.5-hour diagnostic inside the 12-hour stage cap, which is what binds,
and a batch's overshoot is bounded by its size. The disagreement goes to the maintainer at the stop,
with both arguments.
