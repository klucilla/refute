# X0c: the constant scenario's false FAIL (development evidence, not validation)

Run exactly as declared in [DECLARATION.md](DECLARATION.md) (committed and pushed in `5a657fb`
before the run), from the R_min study's recorded fields only, with the study's code at `2e4ff99`: no
light curve, no engine run, no lot. The records matched their committed digests and passed the
completeness check. Output: [x0c.json](x0c.json). The R_min result is unchanged.

## The cases

| R | group | FAIL targets | FAIL rounds |
|---|---|---|---|
| 8 | white, no variability | 6 | 6 |
| 8 | AR(1), variability | 2 | 2 |
| 20 | AR(1), variability | 5 | 5 |
| 20 | white, variability | 1 | 1 |

One target (`rmin-study-63/planet-measurable-correlated-0247`) is FAIL at both R by the same round,
so there are 13 targets and 13 distinct FAIL rounds (14 entries, one per R). Every target has exactly
one FAIL round. By the diagnosis's case labels: of the six at R = 8 in `white, no variability`, five
are `two_years` and one `few_train` (three train transits, one year away); all seven of the
variability groups are `variability_some_years`.

## The cause, by the declared rules

**All 14 FAIL entries are `train or windows`; none is `hidden measurement`, `both` or `sum only`;
none has its twin unavailable.**

| target (R) | hidden year | `S_meas` | `Z` | `Z_train` | `Z_hidden` | `d_twin / d_train` | `d_hidden / d_train` | `e_hidden / e_pred,2` |
|---|---|---|---|---|---|---|---|---|
| study-12/white-0080 (8) | 2018 | −0.86 | 17.5 | 19.5 | −2.04 | −0.16 | −0.03 | 0.64 |
| study-14/white-0029 (8) | 2020 | 3.19 | 14.6 | 13.5 | 1.18 | 0.21 | 0.14 | 0.56 |
| study-15/white-0002 (8) | 2020 | 1.13 | 20.6 | 19.5 | 1.05 | 0.08 | 0.03 | 0.57 |
| study-3/white-0048 (8) | 2018 | −1.29 | 13.3 | 13.0 | 0.28 | −0.07 | −0.09 | 1.13 |
| study-3/white-0152 (8) | 2019 | 0.09 | 15.5 | 16.2 | −0.73 | −0.04 | 0.00 | 0.80 |
| study-6/white-0017 (8) | 2020 | 3.18 | 26.9 | 27.3 | −0.30 | 0.05 | 0.06 | 0.70 |
| study-57/correlated-0211 (8) | 2019 | 2.28 | 13.5 | 13.7 | −0.24 | 0.12 | 0.13 | 1.11 |
| study-63/correlated-0247 (8, 20) | 2019 | 2.67 | 13.1 | 13.2 | −0.13 | 0.15 | 0.16 | 1.22 |
| study-16/white-0246 (20) | 2020 | 4.81 | 5.68 | 5.24 | 0.44 | 0.49 | 0.45 | 1.10 |
| study-4/correlated-0231 (20) | 2018 | 4.91 | 13.9 | 13.4 | 0.44 | 0.23 | 0.21 | 0.54 |
| study-47/correlated-0203 (20) | 2019 | 4.60 | 8.28 | 8.35 | −0.07 | 0.33 | 0.34 | 0.92 |
| study-47/correlated-0211 (20) | 2019 | 3.28 | 14.2 | 14.9 | −0.70 | 0.12 | 0.16 | 0.61 |
| study-58/correlated-0245 (20) | 2019 | −0.63 | 10.3 | 10.0 | 0.29 | −0.03 | −0.06 | 1.17 |

(The prefixes `refute-v0.2.1-rmin-study-` and `planet-measurable-` are shortened. Every value,
with the decisions, the threshold, the replica counts and the ranks, is in `x0c.json`.)

What the declared rules show:
- **The hidden measurement agrees with the noiseless twin** at the windows measured: `Z_hidden`
  lies between −2.04 and 1.18 in every case (the pull `(d_twin − d_hidden) / e_hidden` between −3.01
  and 1.65; only `white-0080` is beyond 2 in absolute value, at the 0.7% rank of its group). These
  FAIL are **not** a noise excursion of the hidden year's measurement.
- **The windows measured carry far less signal than the train depth says:** `Z_train` from 5.2 to
  27.3, `d_twin / d_train` from −0.16 to 0.49. The records cannot separate, by the declared rules, a
  train depth above the truth from predicted windows (or a `dP`) that missed the transits (the
  limitation declared: no injected parameter, no train ephemeris, no `σ_T` in these records).
- **Neither more PASS nor a smaller `e_pred` would correct these errors:** the FAIL comes from the
  depth compared, not from the capacity decisions or the hidden noise.

## The context distributions (eligible constant rounds with the twin ok)

| R | group | rounds | `Z_train ≥ 3` | `Z_hidden ≥ 3` | 1.4826 MAD of the pull |
|---|---|---|---|---|---|
| 8 | AR(1), no variability | 2541 | 304 (12.0%) | 3 (0.12%) | 0.885 |
| 8 | AR(1), variability | 629 | 63 (10.0%) | 0 | 0.878 |
| 8 | white, no variability | 1449 | 275 (19.0%) | 0 | 0.975 |
| 8 | white, variability | 114 | 8 (7.0%) | 1 (0.88%) | 0.868 |
| 20 | AR(1), no variability | 1308 | 30 (2.3%) | 0 | 0.901 |
| 20 | AR(1), variability | 1183 | 95 (8.0%) | 1 (0.08%) | 0.839 |
| 20 | white, no variability | 939 | 23 (2.4%) | 0 | 0.914 |
| 20 | white, variability | 556 | 29 (5.2%) | 1 (0.18%) | 0.933 |

A `Z_train ≥ 3` is common among the eligible rounds (7% to 19% at R = 8): most of those rounds are
still detected (PASS) or left INCONCLUSIVE; a FAIL needs, in addition, `S_meas < 5`. Every FAIL round
lies at a rank of 0.991 or more of its group's `Z_train`. A `Z_hidden ≥ 3` is rare (at most 3 rounds
in a group). The pull's MAD scale below 1 is across targets, not across realizations, and is not a
measurement of `e_hidden`'s calibration (that is X2's question).

## R changes which FAIL appear

At R = 20 all six R = 8 FAIL rounds of `white, no variability` become INCONCLUSIVE (the hidden
replicas below R, or the train replicas), as does one of the two of `AR(1), variability`, and five
new FAIL appear in the variability groups:
rounds stopped at R = 8 by a capacity decision are measured at R = 20, whose pair gives a lower
threshold (10.1 against 12.5 or 12.9). **Releasing a gate brought new FAIL here**, as the
maintainer's qualification of 2026-10-21 (item 5) warns.

## Not declared, written apart

[exploratory.md](exploratory.md): a reading of the reported values that the declared rules do not
make (the size of `d_twin / d_train`), and proposals; nothing there was run.

## The scripts and the files

Run from `.cache/merge-v021/rmin/` with `../../rmin-study/study/scripts/run-with-study-code.ps1` (the
study's code and venv at `2e4ff99`), importing the diagnosis's `diagnosis.py` beside it as X0 did. The
copies here were formatted by ruff and their import path pointed at the committed diagnosis script;
`x0c.py` as committed was run once more and gave `x0c.json` byte for byte.

| File | SHA-256 as run | SHA-256 here |
|---|---|---|
| `scripts/x0c.py` | `943b27a232d7ca422d36f5d5fcc2588502138bc13ba9cff93ed440eb1360c1ab` | `53b1ac08d67238a5e45c3d3e60390cff4c4b68ee33dc5b1d2fa0a38aa8f219cd` |
| `scripts/x0c_view.py` | `d4a975292e2e9c19e1867abac6636edc624362abf74dd20141b2396002310552` | `ac40543da271c0b5946df14106dd13a1022081aa71b07b1ec05bbe5fd21c02ce` |
| `x0c.json` | `f4976467f056425a3f7b1988664209a7bc594d3942187f3581b013f9be17a51c` | the same |
