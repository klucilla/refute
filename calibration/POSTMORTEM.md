# Post-mortem: v0.1 self-claim (FAIL)

**The pre-registered v0.1 self-claim failed.** Refute recovered all 10 known
planets and refuted at most 1 of them, but it flagged **0 of 3** known false
positives (at least 2 were required).

Nothing was changed to make the claim pass: thresholds, targets, data and code are
exactly as locked. The result files are in
[`results/20261007T221214Z-5701c54c/`](results/20261007T221214Z-5701c54c/)
([summary](results/20261007T221214Z-5701c54c/summary.md),
[run log](results/20261007T221214Z-5701c54c/RUNS.md)).

> **How to read this document.** Sections marked *Fact* only restate what the
> locked code produced, what the catalogs say, or what happened during the runs.
> Sections marked **post-hoc hypothesis** were written after the run, while
> looking at the results. They are explanations to be tested, not established
> findings, and none of them was pre-registered.

## The claim

> Refute recovers at least 9 of 10 known TESS planets (period within 0.1% of the
> published value), flags at least 2 of 3 known false positives, and gives the
> verdict REFUTED to at most 1 of the 10 known planets.

- Claim `tess-calibration-v0.1`, claim SHA-256
  `5701c54cb088f1d33895f73d98244d0ea214ddb3f861340d8261b817e189a53f`.
- Code SHA-256 `624f5f900334abcdc614a679a3fdc4ce9c9e8a465f2d3e553d71b24c199f4cfa`.
- Locked from commit `5214f2e29de98803aafff3094733ca424ae3dbde` at
  2026-10-07T21:42:15Z; lock and history committed in `821b0d7` and pushed
  before the first run. `refute verify` returned PASS before each run.
- Targets: drawn by the seeded protocol in [PROTOCOL.md](PROTOCOL.md) (seed
  20261007), an easy regime of short periods, deep transits and bright stars.

## Result (Fact)

| Criterion | Value | Requirement | Result |
|---|---|---|---|
| Recovered planets | 10 of 10 | ≥ 9 | pass |
| Flagged false positives | 0 of 3 | ≥ 2 | **fail** |
| Refuted planets (degeneracy guard) | 1 of 10 | ≤ 1 | pass |

| Target | Name | Kind | Verdict | Reason (from the locked tests) |
|---|---|---|---|---|
| TIC 207141131 | HD 18599 b | planet | SURVIVED | every test passed |
| TIC 138819293 | GJ 436 b | planet | SURVIVED | every test passed |
| TIC 77031414 | WASP-173 A b | planet | SURVIVED | every test passed |
| TIC 440872576 | TOI-3160 A b | planet | **REFUTED** | `holdout_by_year` failed for hidden year 2023 (SNR 2.8 < 5.0) |
| TIC 36592530 | WASP-75 b | planet | SURVIVED | every test passed |
| TIC 369327947 | LHS 475 b | planet | SURVIVED | every test passed |
| TIC 398572544 | WASP-28 b | planet | SURVIVED | every test passed |
| TIC 283621618 | TOI-5806 b | planet | SURVIVED | every test passed |
| TIC 374530847 | WASP-2 b | planet | SURVIVED | every test passed |
| TIC 36452991 | TOI-2969 b | planet | SURVIVED | every test passed |
| TIC 285524410 | TOI-2848.01 | false positive | **INCONCLUSIVE** | `plausibility`: no TIC stellar radius available |
| TIC 404610583 | TOI-5966.01 | false positive | SURVIVED | every test passed |
| TIC 95129101 | TOI-1704.01 | false positive | SURVIVED | every test passed |

Every planet's period was found within the tolerance: relative errors from
1.5e-7 (TOI-2969 b) to 2.0e-5 (WASP-2 b), all at the published period, none at
an alias.

## Why the false positives were not flagged

### TOI-2848.01 (TIC 285524410): INCONCLUSIVE

*Fact.* ExoFOP disposition EB (TESS) and FP (TFOPWG), comment "retired as TFOP
FP/EB". Refute found a 25.7% deep signal at 3.02495 d (SNR 81). Odd/even
(0.38 sigma), secondary eclipse (-1.5 sigma) and the blind holdout (2 of 2 years)
passed. The TIC row for this ID has disposition `SPLIT`, Tmag 18.42 (ExoFOP lists
11.42 for the TOI) and no radius, mass or log g. Under the locked rules, a missing
TIC radius makes `plausibility` INCONCLUSIVE, so the verdict is INCONCLUSIVE.

*Fact (arithmetic).* With a depth of 25.7%, the implied companion radius exceeds
the 2.5 R_Jup threshold for any stellar radius above about 0.51 R_sun.

**Post-hoc hypothesis.** The plausibility test would probably have refuted this
eclipsing binary with a usable stellar radius. The TIC row seems to describe a
faint Gaia source after a split, not the star that dominates the light curve.
Tracked in [#3](https://github.com/klucilla/refute/issues/3).

### TOI-5966.01 (TIC 404610583): SURVIVED

*Fact.* ExoFOP disposition EB/FP, comment "variable host; retired as TFOP
FP/SEB1". Depth 1.08% (SNR 193), implied companion radius 1.05 R_Jup, odd/even
0.15 sigma, secondary 0.4 sigma, holdout 2 of 2 years.

**Post-hoc hypothesis.** A single-lined spectroscopic binary (SEB1) is identified
by radial velocities. Its eclipses can look exactly like a planet transit in a
light curve, so no v0.1 test can separate it.

### TOI-1704.01 (TIC 95129101): SURVIVED

*Fact.* ExoFOP disposition PC/FP, comment "v-shaped; Centroids show source is TIC
95129100". Depth 0.20% (SNR 53), implied companion radius 0.58 R_Jup, odd/even
0.94 sigma, secondary -1.0 sigma, holdout 2 of 2 years.

**Post-hoc hypothesis.** The signal comes from a neighbouring star, which only
pixel-level tests (centroid shift, aperture-dependent depth) can reveal. Those are
planned for v0.2. v0.1 has no shape test for V-shaped eclipses.

## Why a known planet was refuted

### TOI-3160 A b (TIC 440872576): REFUTED

*Fact.* The planet was found at 3.971283 d (published 3.971281 d) and passed SNR,
odd/even, secondary eclipse and plausibility. The blind holdout passed for hidden
year 2025 (SNR 7.2) and failed for hidden year 2023 (SNR 2.8). In the failed round
the training set was one sector (2025): 5 transit times, reduced chi-square 20.5,
period uncertainty 7.6e-4 d. The predicted windows were about ±11 h wide for a
2.3 h transit. The stacked hidden depth was 57990 ± 20747 ppm, an error entirely
from window-to-window scatter (white-noise error 577 ppm), while the transit is
about 7600 ppm deep. The hidden-year plot in the dossier shows the transits inside
the windows, with stacked flux down to about 0.90.

**Post-hoc hypothesis.** The hidden year is detrended with a mask as wide as each
window plus a band, here about 1 day, the same as the 1-day detrending window. The
trend inside each window is then extrapolated, which would create artificial dips
and very different levels between windows. The scatter-based error then suppresses
the SNR. If this is right, the refutation is an artifact of the v0.1 holdout
implementation, not evidence against the planet. Tracked in
[#2](https://github.com/klucilla/refute/issues/2).

## A prediction made before the run, not pre-registered

After target selection and before the lock, in the conversation with the
maintainer, the assistant that built v0.1 (Claude) said that TOI-1704.01
(neighbouring-star signal) and TOI-5966.01 (single-lined binary) would probably not
be flagged by v0.1, and that the "flag at least 2 of 3" criterion might fail. That
prediction was based only on the ExoFOP comments, not on any light-curve analysis.
**It was not pre-registered in the repository**: it is not part of the locked
claim, the protocol or the history, so it carries no evidential weight beyond this
note. The INCONCLUSIVE outcome of TOI-2848.01 was not predicted.

## Technical failure and rerun (Fact)

The first run (`20261007T220242Z-5701c54c`) failed for technical reasons. 8 of 13
targets had a truncated download, and the CLI crashed after writing the summary.
With the maintainer's approval, given before any verdict of that run was
inspected, the run was repeated with a sequential download and an offline
analysis, without changing the locked code. Details, timings and the comparison of
the 5 targets analyzed in both runs (all reproduced) are in
[RUNS.md](results/20261007T221214Z-5701c54c/RUNS.md). The defects are tracked in
[#1](https://github.com/klucilla/refute/issues/1).

## What worked (Fact)

- Period recovery: 10 of 10 planets, all at the published period.
- The degeneracy guard did its job: the gauntlet did not refute planets
  indiscriminately (1 of 10).
- The blind holdout confirmed 12 of 13 targets. In its 37 rounds, all 2178
  logged reads of hidden-year data were centred on a time predicted by the
  train-only ephemeris (access logs in the dossiers).
- The 5 targets analyzed in both runs gave identical results.

## What this result means

- v0.1 cannot flag false positives whose light curves look like planets: blends
  from nearby stars and low-mass stellar companions. It can flag them only when an
  odd/even difference, a secondary eclipse, an implausible size or a failed
  prediction shows up.
- A missing or unreliable stellar radius turns the size test into INCONCLUSIVE,
  which in this run hid a 25.7% deep eclipse.
- The blind holdout can be too fragile when one training year predicts another
  year far away (post-hoc hypothesis above).
- None of this says anything about the planets themselves, which are confirmed by
  other means, nor about the people who studied them.

## Rules for v0.2

1. **The 13 v0.1 targets are now a known set.** Their results have been seen, so
   they cannot be used to validate any fix or new test, including the fixes for
   #1, #2 and #3. They may be used for debugging only, and any such use must be
   declared.
2. **The v0.2 calibration needs a new draw**: a new seed, defined and locked (in a
   new protocol and claim) before any analysis of the new targets. The new draw
   must exclude the 13 v0.1 targets and the v0.1 development target.
3. Fixes are validated on synthetic data first, then by the new locked claim. The
   v0.1 claim is never re-locked or re-run to make it pass; this failure stays
   published as it is.
