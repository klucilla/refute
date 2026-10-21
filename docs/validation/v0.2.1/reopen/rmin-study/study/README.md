# The R_min study: its lot, its integrity and its evaluation (2026-10-21)

The lot `study` of map Amendment 27 (`docs/validation/v0.2.1/reopen/m4-implementation-map.md`;
design of Amendment 19, readings of Amendment 26), run and evaluated with the code of branch
`claude/v0-2-1-reopen` at **`2e4ff998ca1596c281abf915222714e1276173f3`** (worktree
`.cache/wt-v021`, its own venv), not with `main`. That worktree stays frozen until the reserve
ends. Nothing here was tuned after the result; the criteria, sizes and readings are those
committed before the lot.

## The run

- Launched on 2026-10-19 11:29 (-03:00) by [scripts/launch-study.ps1](scripts/launch-study.ps1):
  6 workers on logical processors 0 to 7, configuration `M4-rmin-study`
  (`docs/validation/v0.2.1/population/m4-configurations/rmin-study.json`, SHA-256
  `27f2e277…cdb`, block `c5daf69a…53a4d`), the study's own ceiling as deadline (254.815 h).
- Ended on 2026-10-21 08:44 (-03:00):
  [run-report-20261019T142943136714Z.json](run-report-20261019T142943136714Z.json): 25 600
  targets dispatched and submitted, no failure, no dispatch error, the deadline not reached,
  45.24 h, no integrity problem, `complete: true`. No interruption of the process.

## Integrity (at 2e4ff99)

[integrity.json](integrity.json), by [scripts/integrity.py](scripts/integrity.py) through
[scripts/run-with-study-code.ps1](scripts/run-with-study-code.ps1) (the study's venv, no
bytecode written there): `lot_problems` with the manifest prescribed by `lot_manifest("study")`
and the configuration's identity: **no problem**; 76 800 expected records (25 600 targets × 3
scenarios), 76 800 record files. [manifest.json](manifest.json) is the lot's manifest;
[record-digests.json](record-digests.json) gives the SHA-256 of every record file (records
SHA-256 of the lot `2438020e…eeeee`).

## The complete records (on the Drive)

`K:/Meu Drive/Pessoal/Projetos/refute/arquivo-v0.2.1-rmin-study/` (the maintainer's Drive):
`rmin-study-run-2e4ff99.zip` (stored, 76 806 members: the run folder and the launch script and
logs), SHA-256 `51fa9b3fab62eda7ed8dee24dd521d251ea12cd7dab77d94902353e6624fba30`; its
`MANIFEST.sha256` (here as [archive-MANIFEST.sha256](archive-MANIFEST.sha256)) and the script
[scripts/archive.py](scripts/archive.py). Checked from the Drive's copy: the zip's SHA-256,
every member's SHA-256 against its source file, the manifest's bytes: no difference. Nothing
was deleted.

## The evaluation (at 2e4ff99)

[study-evaluation.json](study-evaluation.json): `rmin_study.py evaluate-study` with the
committed pairs of `bs-choice` (`bs-choice-evaluation.json`, re-derived from `bs-choice/` and
found equal), `complete: true`, **`chosen_r_min: null`: option (c)**. No `R` of
{8, 10, 12, 15, 20} meets criteria 1 to 5 in all four groups.
[study-evaluation-summary.json](study-evaluation-summary.json) and
[scripts/summarize.py](scripts/summarize.py) give the tables below (interruption reasons grouped
by kind, the text before their first number).

| R | group | false FAIL: n / FAILs / upper | coverage: ±1 / ±2 / median | disappearance: n / lower | weakening n | all |
|---|---|---|---|---|---|---|
| 8 | white, no variability | 802 / 6 / 0.0181 (fails) | 0.663 / 0.920 / +0.005 (ok) | 630 / 0.990 (ok) | 0 (fails) | no |
| 8 | white, variability | 81 / 0 / 0.0553 (fails) | 0.691 / 0.926 / -0.142 (ok) | 41 / 0.894 (fails) | 0 (fails) | no |
| 8 | AR(1), no variability | 1344 / 0 / 0.0034 (ok) | 0.736 / 0.952 / -0.019 (ok) | 1172 / 0.994 (ok) | 0 (fails) | no |
| 8 | AR(1), variability | 477 / 2 / 0.0175 (fails) | 0.677 / 0.952 / -0.051 (ok) | 210 / 0.978 (ok) | 0 (fails) | no |
| 10 | white, no variability | 794 / 6 / 0.0183 (fails) | 0.661 / 0.919 / +0.010 (fails) | 622 / 0.989 (ok) | 0 (fails) | no |
| 10 | white, variability | 81 / 0 / 0.0553 (fails) | 0.691 / 0.926 / -0.142 (ok) | 41 / 0.894 (fails) | 0 (fails) | no |
| 10 | AR(1), no variability | 1313 / 0 / 0.0035 (ok) | 0.737 / 0.950 / -0.022 (ok) | 1141 / 0.994 (ok) | 0 (fails) | no |
| 10 | AR(1), variability | 477 / 2 / 0.0175 (fails) | 0.677 / 0.952 / -0.051 (ok) | 210 / 0.978 (ok) | 0 (fails) | no |
| 12 | white, no variability | 640 / 3 / 0.0156 (fails) | 0.669 / 0.931 / -0.024 (ok) | 477 / 0.986 (ok) | 0 (fails) | no |
| 12 | white, variability | 94 / 0 / 0.0478 (fails) | 0.702 / 0.915 / -0.129 (fails) | 49 / 0.910 (fails) | 0 (fails) | no |
| 12 | AR(1), no variability | 1131 / 0 / 0.0041 (ok) | 0.738 / 0.949 / -0.003 (ok) | 945 / 0.993 (ok) | 0 (fails) | no |
| 12 | AR(1), variability | 505 / 3 / 0.0198 (fails) | 0.681 / 0.954 / -0.038 (ok) | 220 / 0.979 (ok) | 0 (fails) | no |
| 15 | white, no variability | 479 / 1 / 0.0138 (fails) | 0.660 / 0.937 / -0.034 (ok) | 369 / 0.982 (ok) | 0 (fails) | no |
| 15 | white, variability | 207 / 0 / 0.0220 (fails) | 0.710 / 0.947 / -0.048 (ok) | 104 / 0.938 (ok) | 0 (fails) | no |
| 15 | AR(1), no variability | 853 / 0 / 0.0054 (fails) | 0.740 / 0.947 / -0.026 (ok) | 683 / 0.993 (ok) | 0 (fails) | no |
| 15 | AR(1), variability | 688 / 4 / 0.0168 (fails) | 0.679 / 0.948 / -0.011 (ok) | 316 / 0.974 (ok) | 0 (fails) | no |
| 20 | white, no variability | 390 / 0 / 0.0117 (fails) | 0.697 / 0.946 / -0.113 (ok) | 306 / 0.985 (ok) | 0 (fails) | no |
| 20 | white, variability | 336 / 1 / 0.0196 (fails) | 0.676 / 0.935 / +0.018 (ok) | 179 / 0.975 (ok) | 0 (fails) | no |
| 20 | AR(1), no variability | 581 / 0 / 0.0079 (fails) | 0.721 / 0.960 / -0.010 (ok) | 482 / 0.990 (ok) | 0 (fails) | no |
| 20 | AR(1), variability | 859 / 5 / 0.0152 (fails) | 0.704 / 0.956 / +0.016 (ok) | 401 / 0.975 (ok) | 0 (fails) | no |

The limits (`rmin_evaluate.py`, Amendment 26, reading 2): false FAIL at least 866 eligible
constant targets and an upper bound at most 0.02; coverage ±1 in [0.60, 0.76], ±2 in
[0.92, 0.98], |median| at most 0.2; disappearance at least 83 and a lower bound at least 0.80;
weakening at least 101 and a lower bound at least 0.50; one-sided Clopper-Pearson at
1 − 0.05/5 per bound.

**Interruptions at R = 8** (criterion 6, reported; INCONCLUSIVE targets and rounds of each
scenario; the full counts per reason, per R, are in the summary):

| group | scenario | INCONCLUSIVE targets | INCONCLUSIVE rounds | main round reasons |
|---|---|---|---|---|
| white, no variability | constant | 5599 / 6400 (0.875) | 12953 / 14400 (0.900) | timing 6506, insufficient_capacity_train 4361, hidden_noise_undetermined 1133, train_snr_below_gate 632 |
| white, no variability | disappearing | 5770 / 6400 (0.902) | 13768 / 14400 (0.956) | train_snr_below_gate 5659, insufficient_capacity_train 3430, timing 3430 |
| white, no variability | weakened | 5770 / 6400 (0.902) | 13725 / 14400 (0.953) | timing 4675, train_snr_below_gate 4308, insufficient_capacity_train 3576 |
| white, variability | constant | 6319 / 6400 (0.987) | 19087 / 19200 (0.994) | insufficient_capacity_train 15420, train_noise_undetermined 1691, train_snr_below_gate 1420 |
| white, variability | disappearing | 6359 / 6400 (0.994) | 19159 / 19200 (0.998) | insufficient_capacity_train 11600, train_snr_below_gate 4022, train_noise_undetermined 2737 |
| white, variability | weakened | 6359 / 6400 (0.994) | 19159 / 19200 (0.998) | insufficient_capacity_train 12105, train_snr_below_gate 3681, train_noise_undetermined 2612 |
| AR(1), no variability | constant | 5056 / 6400 (0.790) | 11859 / 14400 (0.824) | insufficient_capacity_train 6631, timing 3426, hidden_noise_undetermined 1155 |
| AR(1), no variability | disappearing | 5228 / 6400 (0.817) | 13204 / 14400 (0.917) | insufficient_capacity_train 4641, timing 2685, train_noise_undetermined 2625 |
| AR(1), no variability | weakened | 5227 / 6400 (0.817) | 13087 / 14400 (0.909) | insufficient_capacity_train 5044, timing 3760, train_noise_undetermined 1713 |
| AR(1), variability | constant | 5924 / 6400 (0.926) | 18574 / 19200 (0.967) | insufficient_capacity_train 16112, train_noise_undetermined 1253, insufficient_capacity_hidden_noise 490 |
| AR(1), variability | disappearing | 6159 / 6400 (0.962) | 18945 / 19200 (0.987) | insufficient_capacity_train 12282, train_noise_undetermined 3553, duration_period_ratio_above_max 1319 |
| AR(1), variability | weakened | 6140 / 6400 (0.959) | 18916 / 19200 (0.985) | insufficient_capacity_train 13098, train_noise_undetermined 3097, duration_period_ratio_above_max 1137 |

("timing" is the rule's reason "train-only timing uncertainty in the hidden year".)

## A finding after the result: the weakening criterion cannot be met

Recorded after the result, as a result; no change, amendment or rerun follows from it here.
[diagnosis-weakening.json](diagnosis-weakening.json) ([scripts/diag_weakening.py](scripts/diag_weakening.py),
read only, at 2e4ff99): the weakening criterion has **n = 0 in every group at every R**. Its
filter admits a weakened target only when its last round passes decisions 1 and 2, which need
`S_pred,2` at least the capacity threshold, and `0.3 · S_pred,2 ≤ 3`, that is `S_pred,2 ≤ 10`.
With the pairs of `bs-choice` (b from 0.58 to 0.80, s from 2.5 to 2.9) the capacity threshold is
above 10 at R = 8, 10, 12 and 15 for every number of years (11.27 to 13.13), so there the two
conditions never hold together, by construction, whatever the data. At R = 20 it is 9.89 for two
observing years (10.14 and 10.31 for three and four), which leaves only the window
`9.89 ≤ S_pred,2 ≤ 10` of two-year curves; no target fell in it (the smallest `S_pred,2` of the
decision-passing weakened targets at R = 20 is 10.16; at R = 8 to 15, from 11.42 to 13.07). So
the criterion's minimum of 101 cannot be reached at R = 8 to 15 and is out of reach in practice
at R = 20. Under the maintainer's rule for criterion failures, a contradiction of the specification
is the maintainer's to decide (an amendment declared after the result, reviewed by Codex,
retested on new seeds with the same criterion and size). Option (c) does not depend on it alone:
the false-FAIL minimum of 866 is reached only by `AR(1), no variability` (at R = 8, 10 and 12),
and other criteria fail in other groups.

## Files

| File | SHA-256 |
|---|---|
| `archive-MANIFEST.sha256` | `99163fac91350b2a0c11cad9edb497d4f32b9509ab9eae91bf374fc802c8678d` |
| `diagnosis-weakening.json` | `294b08871849f7dbd9faa1c7c7787498852a21a9107654031f0fa0bfcdfc8095` |
| `integrity.json` | `bf23456dd3505730f273dae6a24da9b6bf955d7421d015118b3f9314db03a126` |
| `manifest.json` | `61acbc6a30cc4d4abb5e55a00d834aaed75fc7c8127e4d98a0b86d8b814e899c` |
| `record-digests.json` | `47837ef0fc787bb3488be96ef2e49b9a690457037b7251c9394fb6ee33a08ef6` |
| `run-report-20261019T142943136714Z.json` | `49334a5af512268a77d10ddeec648fb71ddce3bef17803b91863246ce087e7e8` |
| `study-evaluation-summary.json` | `a763ef017171c2ca64f445fe004a0a2009f7922856a0014c0289eef1c5596c0f` |
| `study-evaluation.json` | `caa97afc1eaafa167fa80c88cf42150ebd1f379629e0e84b8927f15729141c7e` |

The scripts in `scripts/` were run from `.cache/merge-v021/rmin/`; their copies here were then
formatted by ruff (layout only). `summarize.py` as committed gives the same summary, byte for
byte. `launch-study.ps1` is the launch script as run.
