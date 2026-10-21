# X0a and X0b: results (development evidence, not validation)

Run exactly as declared in [DECLARATION.md](DECLARATION.md) (committed and pushed in `ccd43f2`
before the run), from the R_min study's recorded fields only, with the study's code at `2e4ff99`:
no light curve, no engine run, no lot. The records matched their committed digests and passed the
completeness check (one round per observing year). Outputs: [x0a.json](x0a.json),
[x0b.json](x0b.json). The R_min result is unchanged: no R_min was validated. Nothing here
validates specification B; it shows what B does to these records.

## X0a. Where the disappearing scenario's false PASS come from

| R | group | PASS targets / decided | the last round's gate | the PASS rounds | `S_meas` of the PASS rounds (median, 5 to 95%) |
|---|---|---|---|---|---|
| 8 | AR(1), variability | 26 / 241 | decision 1: 16; decision 2: 10 | one year before the last: 16; two years before: 10 | 16.8 (7.0 to 29.0) |
| 8 | AR(1), no variability | 1 / 1172 | measured, PASS | the last year itself | 5.15 |
| 8 | white, no variability | 1 / 630 | measured, PASS | the last year itself | 5.41 |
| 8 | white, variability | 0 / 41 | | | |
| 20 | AR(1), variability | 42 / 467 | decision 1: 21; decision 2: 10; hidden noise: 9; train replicas: 1; measured, PASS: 1 | one year before the last: 27; two before: 14; the last year: 1 | 13.9 (5.4 to 26.2) |
| 20 | the three other groups | 0 | | | |

All the `AR(1), variability` PASS targets have **three observing years** (as all its decided
disappearing targets do). At R = 8, every one's last-year round was stopped by a capacity
decision, and the PASS came from an earlier year, where the signal is unaltered and strongly
detected (median `S_meas` 16.8): these false PASS are the aggregation's, the altered year never
decided. At R = 20 the same holds for 41 of the 42 (their last round stopped by a capacity decision,
the hidden noise or the train replicas); the 42nd target's last-year round was measured and PASSed,
a detection in the year without the signal. The two isolated cases of the groups without variability are of
another kind: the last-year round was measured and PASSed just above `min_snr` (5.15 and 5.41) on a
year without the signal, a detection by noise in the predicted windows.

## X0b. Specification B applied to these records

R = 8 (R = 20 in [x0b.json](x0b.json)); "decided" = PASS or FAIL.

| group / scenario | today: PASS, FAIL | under B: PASS, FAIL | decided / total, today → B | the error, today → B |
|---|---|---|---|---|
| AR(1), no variability / constant | 1344, 0 | 874, 0 | 21.0% → 13.7% | false FAIL 0/1344 → 0/874 |
| AR(1), variability / constant | 474, 2 | 34, 2 | 7.44% → 0.56% | false FAIL 2/476 (0.42%) → **2/36 (5.6%)**; over all: 2/6400 both |
| white, no variability / constant | 795, 6 | 401, 6 | 12.5% → 6.4% | false FAIL 6/801 (0.75%) → **6/407 (1.47%)**; over all: 6/6400 both |
| white, variability / constant | 81, 0 | 3, 0 | 1.27% → 0.05% | false FAIL 0/81 → 0/3 |
| AR(1), no variability / disappearing | 1, 1171 | 0, 1171 | 18.3% → 18.3% | false PASS 1/1172 → **0/1171** |
| AR(1), variability / disappearing | 26, 215 | 0, 215 | 3.77% → 3.36% | false PASS 26/241 (10.8%) → **0/215** |
| white, no variability / disappearing | 1, 629 | 0, 629 | 9.84% → 9.83% | false PASS 1/630 → **0/629** |
| white, variability / disappearing | 0, 41 | 0, 41 | 0.64% → 0.64% | 0/41 → 0/41 |
| AR(1), no variability / weakened | 989, 184 | 45, 184 | 18.3% → 3.6% | no label |
| AR(1), variability / weakened | 175, 85 | 1, 85 | 4.06% → 1.34% | no label |
| white, no variability / weakened | 546, 84 | 9, 84 | 9.84% → 1.45% | no label |
| white, variability / weakened | 13, 28 | 0, 28 | 0.64% → 0.44% | no label |

What B does here:
- **It removes every false PASS of the disappearing scenario**, at R = 8 and R = 20, including the
  last-year detections in the year without the signal (two at R = 8, one at R = 20). That effect
  comes from the other years: those targets turned INCONCLUSIVE because another year was undecided,
  not because of their last-year detection; B does not address a last-year detection when every year
  PASSes.
- **It costs utility, most where the yield was already lowest**: the decided constant targets fall
  by a third to a half without variability, and by more than 90% with it (`AR(1), variability`
  474 → 34 PASS; `white, variability` 81 → 3). The undecided years of the targets turned from PASS
  to INCONCLUSIVE are mostly stopped by decision 1, by decision 2 and by the hidden noise (for
  example `AR(1), variability`, constant: 570, 205 and 10 rounds), and by the timing rule in the
  weakened scenario without variability.
- **The false FAIL's count does not change (FAIL keeps its precedence), but its fraction among the
  decided rises** as the denominator shrinks: 0.42% → 5.6% in `AR(1), variability` (2 of 36) and
  0.75% → 1.47% in `white, no variability`. Over all targets it is the same (2/6400, 6/6400).
- **Years without a predicted transit window:** none. No round of these records stopped with
  `no_predicted_window` (0 of 201 600 rounds; the reason exists in the engine and survives the
  derivation, but this lot never reached it), so no target is INCONCLUSIVE under B for that reason
  (0 everywhere, at every R, in every scenario). These records therefore do **not** exercise what B
  does when such a year occurs.
- **The weakened scenario's PASS mostly disappear** (for example 989 → 45): their weakened last year
  was not decided while the other years PASSed; under specification A this is abstention, not error.

## The scripts and the files

Run from `.cache/merge-v021/rmin/` with `../../rmin-study/study/scripts/run-with-study-code.ps1`
(the study's code and venv at `2e4ff99`), importing the diagnosis's committed `diagnosis.py` for its
gate classification. The copies here were formatted by ruff and their import path pointed at the
committed diagnosis script; `x0.py` as committed was run once more and gave both outputs byte for
byte.

| File | SHA-256 as run | SHA-256 here |
|---|---|---|
| `scripts/x0.py` | `24a6b65fb37cc9d146316da2c8e23147f32ce50ae80fc61f850739dc561d1bd5` | `e183a1de133c73da7a3f1688e0c895fa866e52cf9e7710c33ecb56e6d14a1eae` |
| `scripts/x0_view.py` | `feecb975c8ee868df208669760f7fd9a6d33ee95ca46728ffd5c231997abdb0f` | `f7f63f72dc1d231cb7f7b917f3bb2510a92230feaa60922874bd9757311524fc` |
| `x0a.json` | `25fda7ae3656421e91561111fad996362d816ff40d416c12ea3dadb75237ce29` | the same |
| `x0b.json` | `4d271dab365ef212e731d15450948fb26f4acb902ac41d91fe26d1cc39e4ebeb` | the same |

These numbers describe this lot under the R_min study's gates (the b/s pairs of bs-choice); they
are not a measurement of B under the corrected gates, which belongs to the pilot (experiment plan,
X5) after its own authorization.
