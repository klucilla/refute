# The two-year barriers: results (read only)

The diagnosis declared in [two-year-declaration.md](two-year-declaration.md) (committed and pushed
before the reading, `ee262b5`), run once by [scripts/two_year_reading.py](scripts/two_year_reading.py)
on the R_min study's archive: [two-year-reading.json](two-year-reading.json),
[two-year-geometry.json](two-year-geometry.json). **No lot, no engine run, nothing changed; X2f
not authorized.** Every bound below is a reading of these records (configuration M4, R = 8, the
measurable band), not a bound on a future sample nor on the final configuration.

**Integrity (all passed):** the archive's SHA-256 (`51fa9b3f…6fba30`); the 25 600 `constant`
records, each matching its committed SHA-256, each read once; every record's rounds one per
observing year; the study's committed INCONCLUSIVE counts reproduced in the four groups; every
timing message parsed; the rebuilt years equal to the records' for every two-year target; the
stratified spot check against `build_case` 24 of 24.

## a. The timing rule (two-year targets, measurable band)

Rounds stopped by the rule (the train-only `σ_T` above one train duration):

| Axis | white | AR(1) |
|---|---|---|
| all rounds | 2371 of 4800 (0.49) | 644 of 4800 (0.13) |
| `two_years` (2018 and 2020) | 0.50 | 0.08 |
| `few_train`, 1 / 2 / 3 years apart | 0.24 / 0.50 / 0.70 | 0.04 / 0.24 / 0.48 |
| hidden year 2021 (`few_train`, 3 years) | 0.96 | 0.91 |
| period 1.5–2.5 / 2.5–3.5 / 3.5–4.5 / 4.5–5.5 d | 0.62 / 0.55 / 0.47 / 0.38 | 0.13 / 0.15 / 0.14 / 0.11 |
| lever `g√N` 30–60 / 60–100 / 100–200 / ≥ 200 | 0.11 / 0.48 / 0.49 / 0.91 | 0.01 / 0.08 / 0.09 / 0.80 |
| train transits 3 / 4 / 5–9 / 10–18 | 0.65 / 0.56 / 0.37–0.48 / 0.55–0.63 | 0.50 / 0.32 / 0.04–0.09 / 0.09–0.24 |

These are marginal tables, described, not a causal separation:
- The stopped fraction is highest at the largest lever `g√N` (0.91 white, 0.80 AR(1) above 200)
  and grows with the distance between the years (`few_train` from 1 to 3 years); in white noise it
  falls with the period (0.62 to 0.38), in AR(1) it does not change monotonically; three train
  transits (`few_train`'s first orbit) have the highest stopped fraction in both noise models,
  and four also a high one, especially in AR(1). Amendment 28's earlier diagnosis
  attributed about 99.99% of `σ_T²` in these layouts to the train period's error; that share is
  **not remeasured here**.
- **White stops about 3.7 times as often as AR(1)** over these rounds pooled (the ratio is not
  uniform across layouts). A plausible hypothesis about the generator, **not tested here**: the
  measurable band is set by the expected SNR under each noise model, so the AR(1) planets are
  deeper for the same band, which could make their train timing more precise. It would be a
  property of the generator's design, not of real stars.
- `σ_T/T14` of the stopped rounds (the rule's message): white `(1, 1.5]` 715, `(1.5, 2]` 432,
  `(2, 3]` 544, `> 3` 677; AR(1) 327, 131, 108, 75; and, apart, the rounds whose **rounded** point
  value is at most 1 although the rule stopped them (their exact ratio above 1): 3 white, 3 AR(1).
  The rounds that pass the rule carry no `σ_T`: not identifiable for them.

## b. T4 at its best (variant A, two-year curves only)

Of the stopped rounds, **T4 would admit** (`σ_T/T14` in `(1, 3]` by the rounding interval) white
1692 definitely and 7 ambiguous, 672 excluded (`> 3`); AR(1) 569 definite, 75 excluded. The train
fundamentals are not recorded: assumed absent (the favourable case). Every admitted round counted
as PASS, every other round as recorded:

| Noise, two years | Holdout PASS as read, spec B | With T4 at its best, spec B (legacy) | Selected residual categories (spec B, targets) |
|---|---|---|---|
| white | 0.085 | **0.26** (0.745) | hidden noise undetermined 778, timing beyond T4 451, capacity 288 + 72 with timing |
| AR(1) | 0.261 | **0.28** (0.617) | hidden noise undetermined 659, capacity 559 + 131 with hidden noise, capacity hidden 125 |

- **T4 alone recovers little under specification B**: a two-year curve needs both of its years
  decided, and the other year is blocked by the undetermined hidden noise or by a capacity decision.
  Under the legacy rule (one PASS year suffices) T4 alone would lift white two-year from 0.21 to
  0.75.

## c. The undetermined hidden noise

- **The recorded cause is (i) in every round:** white 1131 of 1131, AR(1) 1110 of 1110 have the
  field `hidden_noise_undetermined` true, **every replica count zero at every `dP`** (a nonempty
  count list; no valid replica depth counted: the replica bands are read, and the undetermined
  branch suppresses the depth measurement), in `two_years` (both years) and `few_train` (both
  years, at every distance).
  Cause (ii), replicas below R with the noise determined, does not occur here.
- **Which sub-cause** of (i) (no replica band covered, or every hidden sector excluded by A1: too
  few bins at the transit's scale, or no noise scale): **not identifiable with the current
  records** (neither the replicas registered nor A1's per-sector reasons are recorded). Grid sizes
  of these rounds: white 1–20 points 172, 20–40 659, 40–60 300; AR(1) 555, 408, 147.
- **Observable by the engine: yes.** `replica_stats` computes it from the replica bands of the
  hidden year and A1's estimate (`holdout.py`, lines 619 to 694; `rednoise.py`, the exclusion of a
  sector with too few bins), before any transit window is read; the engine can record the
  sub-cause, these records do not.
- **No committed plan specifies a repair of this barrier.** Spec C changes the capacity decisions
  only; T4 requires the hidden noise determined for its PASS; the attenuation front concerns the
  measured depth. Indirect effects of those fronts on it are not excluded.

> **Interpretation (the maintainer's record of 2026-10-23):** zero replica depths counted does
> **not** prove that there are no windows: with the noise model undetermined the code stops
> measuring the replicas. The records do not distinguish replica bands without coverage, sectors
> excluded for too few bins, and the absence of a usable noise scale. "One sector has no room for
> replicas" is a **hypothesis**. The hidden-noise front is **deferred** (its cause and its repair
> not established), not closed as a physical limit.

## d. The combined optimistic bound

Every round INCONCLUSIVE by a capacity decision, by the timing rule and by the undetermined hidden
noise counted as PASS; standardized to the population study's quotas (150, 50, 50 of 250):

| Reading | white, legacy / spec B | AR(1), legacy / spec B | G1 by regime (spec B) |
|---|---|---|---|
| as read | 51.0 / 25.1 | 91.4 / 55.2 | none reached |
| capacity only (the viability check) | 161.4 / 114.6 | 215.6 / 169.2 | three-year and variability only |
| T4 only (with ambiguous) | 130.8 / 51.4 | 123.8 / 58.3 | none |
| **d1: capacity + T4's timing + hidden noise** | **242.1 / 210.7** | **249.9 / 240.4** | **every regime**: white 2 years 0.758, 3+ 0.999, variability 0.942; AR(1) 0.958, 0.996, 0.938 |
| d2: capacity + every timing round + hidden noise | 249.4 / 245.3 | 250.0 / 245.6 | every regime |

- **Only the three resolved together** bring the white noise above the 195 of C1 and C3 under
  specification B on these records (210.7), and G1's count in `white, 2 years` (0.758 against
  0.673); no one of them does it alone. The pairs were not among the declared readings; **Codex's
  arithmetic on the stored residual categories** (not rerun by the script) gives, white, spec B:
  capacity + T4 about 157.5, capacity + hidden noise about 148.2, T4 + hidden noise about 100.0, all
  below 195, and their two-year fractions below 101 of 150.
- What still blocks after d1 (spec B, two-year targets): white 575 targets, the timing beyond T4's
  scope 554, replicas below `R` in the train 12, too few train transit times 7,
  `not_detected_not_inconsistent` 2; AR(1) the timing beyond T4's scope 74, replicas 25, too few
  transit times 2.
- The same caveats: favourable substitutions, never an engine run; the gate, the gauntlet and the
  candidate's identity not included; a reading of the M4 configuration's records, not of the final
  configuration, whose viability is not identifiable from them.

> **Interpretation (the maintainer's record of 2026-10-23):** the optimistic reading (210.7
> against 195) shows only that, under favourable substitutions, an evident impossibility
> disappears; it does **not** show that implementable repairs would produce it. It assumes PASS
> in rounds blocked today and leaves out the global gate, the full battery and the candidate's
> identity; releasing a round can reveal a FAIL. The 195 already carry the Clopper-Pearson bounds
> of C1 and C3; the requirement is not applied twice.
