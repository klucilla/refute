# v0.5.2 stage 1, experiment E2: the matched estimator's candidates (frozen before it runs)

Development seeds only: `int(SHA-256("refute-v052-dev:e2:<kind>:<noise>:<snr>:<P>:<shape>:<i>")[:16], 16)`.
Nothing in `src/` changes (patches inside the experiment's own processes). It decides nothing about
any target; its checks are development checks, distinct from population-equivalence acceptance.
`method_status: not_validated`. Script: [e2_matched.py](e2_matched.py), output `e2-matched.json`.

**Question.** Which estimator can carry `odd_even`, given that the same-data fit shifts the matched
depths and that the mask asymmetry widens the scatter? E1's frozen rule returned NOT ESTABLISHED (one
construction of arm C failed its availability check), with arm D, both windows masked, at `rho` 0.969
to 1.008 (0.983 to 1.008 outside white noise). E2 carries arm D's treatment as a candidate, and the
as-built one as the baseline, without claiming E1 established it.

**An amendment, flagged.** The first frozen version had periods 1.5 and 5.0 d in the rule. A development
smoke (44 units, fingerprint `729397b91d27a347`, seeds of this experiment's namespace) showed the
estimators available on 26 to 38 of 44 units; availability is itself a qualification endpoint, and the
periods were then changed to 3.3 and 7.0 d. That change is **outcome-informed**. So the question is
formally **narrowed to periods 3.3 and 7.0 d**; any recommendation states that restriction; the
short-period question (1.5 d) is **carried forward as unresolved**, and the supplement below only
reports availability, which cannot support a general estimator replacement. A0 at short periods has few
pseudo-windows left (an event's window excludes grid windows within `2 h`), and that limit is reported.

**The null: equal-depth transits with an unknown common shape and depth.** A trapezoid at every event,
the same depth for odd and even, injected into `common.noise_curve` (2 sectors, 1,000 ppm). **Required
cells:** noise (white, correlated, long) x box SNR (12, 30) x period (3.3, 7.0 d) x shape (0.12 d with
ingress 0.1; 0.20 d with 0.2): 24 cells, 40 curves each. **The alternative:** odd events at the depth and
even events at zero (the registered full-depth alternative): noise x SNR x period, shape 0.12 d, 12
cells, 30 curves each. **Short-period supplement (availability only, outside the rule):** a null at 1.5 d,
SNR 12, shape 0.12 d, 20 curves per noise.

**The upstream selection, conditional.** The curve detrended, `search.finalize_candidate` at the true
period with the true duration as the hint (a local finalization **initialized at the truth**, not the
complete production search; a full-search calibration is unresolved), then `series.pipeline_flat` for
that final candidate. The final candidate is shared by every estimator on that curve.

**Estimators** (each gives the odd-minus-even difference and its error; `z = |diff| / error`, a FAIL at
`z >= 3`, as `odd_even` has it). `built` is the **baseline, not eligible** for the choice.

| Name | Shape | Pseudo-window treatment |
|---|---|---|
| `built` (baseline) | fitted on all events, as `check_odd_even` | as built |
| `built_masked` | the same fit | pseudo-windows masked, arm D's comb |
| `candidate_shape` | the final candidate's duration, ingress 0.1, no shift, no additional fit | arm D's comb |
| `crossfit` | the shape fitted on each parity measures the other; each group's error from its own template's windows; `Var(diff) = Var(odd) + Var(even)` | arm D's comb |
| `pseudo_ephemeris` | a **distinct information-weighted estimator** (matched amplitudes weighted by information, not `check_odd_even`'s statistic); the error is the standard deviation of the same statistic at 20 random phases of the same period, at least 3 durations from events and from phase 0.5 | as built, on the flattened series |
| `box` | box depth, the A0 errors and group rule | arm D's comb |

`candidate_shape` is not an a priori shape: the candidate is data-selected upstream, and it removes one
selection step. `crossfit`'s independence of the two group errors is an assumption, and only its
observed pull calibrates it. `pseudo_ephemeris` is a **conditional variance hypothesis**, tested by
these equal-depth simulations; it does not repeat every selection step and does not establish a
rejection tail.

**Measured, with 95 % intervals from a bootstrap over whole curves (2,000 replicates)**, per noise and
per cell: the pull mean and standard deviation, and the availability (a finite difference and a finite
positive error; unavailable curves stay in the denominators). On the alternative: the fraction with `z >=
3` per cell over all scheduled curves, with Wilson intervals. Each estimator's CPU per curve.

**The choice rule, fixed now (descriptive; a development check).** Among the eligible candidates (`built`
excluded), a candidate *qualifies* if:
1. in **every required null cell**: the availability is at least 0.70, `|mean| <= 0.4` and `sd` in
   [0.70, 1.35] (n = 40 per cell: about 2.5 standard errors);
2. pooled per noise: `|mean| <= 0.1`, `sd` in [0.9, 1.1], and availability at least 0.80;
3. **an absolute sensitivity requirement before ranking:** in each of the 12 alternative cells, unconditional
   detection of at least 0.80 (an **exploratory benchmark** below the registered 0.95, given 30 curves
   per cell).

Among those, the highest mean power over the 12 alternative cells; ties within 0.02 go to the simpler, in
the order `box`, `candidate_shape`, `built_masked`, `crossfit`, `pseudo_ephemeris`. If none qualifies, none
is recommended. Agreement only when pooled is named as such. An undefined required cell blocks the
choice.

**`pseudo_ephemeris` affordability, frozen, and part of its qualification:** on the first 5 curves of each
null cell the error is computed twice with independent phase sets. It can qualify only if it is
*affordable*: the mean `|ln(error_1 / error_2)|` is at most 0.20 over **all** the due repeats, and its
ordinary CPU per curve (the real difference and one phase set; the second set is counted apart, as
validation overhead) is at most 5 s. A missing due repeat leaves the precision unestablished and the
candidate does not qualify. (The 16 % scatter of 20 Gaussian replicates is an idealized calculation, and
is not assumed.)

**Runs on 4 processes**, a measured choice (`e3-design.md`, third correction).

**Identity and cost.** A fingerprint (design, script, `runlib`, runner files, E1's result hash, code hash,
resolved plan, constants, numpy, scipy, astropy versions), checked at resume and at summary. Every
record's kind, noise, SNR, period, shape, index and estimator schema are validated, with expected cell
counts; any structural failure, a stopped run, or an undefined statistic that a decision needs gives NOT
ESTABLISHED, naming it, with a null choice. A probe of 44 units covers the factors. `runlib.bounded_run`
checks the spent cost before dispatch, projects against the whole unfinished schedule, and refuses to
continue past **3.0 processor-hours less a 5 % reserve**; workers import first, outside the cost.
