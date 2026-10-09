# Selection log (v0.2)

Generated 2026-10-09T15:18:54Z by `calibration/v0.2/select_targets.py`
following `calibration/v0.2/PROTOCOL.md`.

## Seed

- drand chain `8990e7a9aaed2ffed73dbd7092123d6f289930540d7651336225dc172e51b2ce` (pedersen-bls-chained), round 6537566, published 2026-10-09T15:00:00+00:00
- URL: https://api.drand.sh/8990e7a9aaed2ffed73dbd7092123d6f289930540d7651336225dc172e51b2ce/public/6537566 (retrieved 2026-10-09T15:00:50Z)
- randomness: `6203178f500788b092dafc8557309f4225cee9fa7b907eefe819b69525ce325d`
- signature verified with py_ecc 8.0.0 (G2Basic): True
- seed = int(randomness, 16) = 44332122306220873417487815239527185719959535074380635769320531619090132775517

## Exclusions (the 14 known v0.1 targets found in the pools)

- planet pool: TIC 440872576 TOI-3160 A b
- planet pool: TIC 138819293 GJ 436 b
- planet pool: TIC 369327947 LHS 475 b
- planet pool: TIC 398572544 WASP-28 b
- planet pool: TIC 283621618 TOI-5806 b
- planet pool: TIC 36592530 WASP-75 b
- planet pool: TIC 77031414 WASP-173 A b
- planet pool: TIC 374530847 WASP-2 b
- planet pool: TIC 36452991 TOI-2969 b
- planet pool: TIC 207339000 TOI-4427 b
- planet pool: TIC 207141131 HD 18599 b
- false-positive pool: TIC 95129101 TOI-1704.01
- false-positive pool: TIC 285524410 TOI-2848.01
- false-positive pool: TIC 404610583 TOI-5966.01

- Planet pool after exclusions: 475 rows; false-positive pool: 456.

## Candidates, in shuffled order

| Pool | Position | Target | Name | Decision | Reason |
|---|---|---|---|---|---|
| planet | 1 | TIC 118327550 | TOI-244 b | ACCEPTED | accepted |
| planet | 2 | TIC 48506505 | Kepler-447 b | ACCEPTED | accepted |
| planet | 3 | TIC 19028197 | GJ 3470 b | ACCEPTED | accepted |
| planet | 4 | TIC 158561566 | Kepler-14 b | ACCEPTED | accepted |
| planet | 5 | TIC 139528693 | WASP-78 b | ACCEPTED | accepted |
| planet | 6 | TIC 151825527 | TOI-672 b | ACCEPTED | accepted |
| planet | 7 | TIC 68808155 | TOI-5350 b | rejected | data rule not met: light curves years [] span 0 d; pixel files years [] span 0 d (need >= 2 years and >= 300 d for both) |
| planet | 8 | TIC 231670397 | WASP-73 b | ACCEPTED | accepted |
| planet | 9 | TIC 193754373 | TOI-4487 A b | ACCEPTED | accepted |
| planet | 10 | TIC 194736418 | TOI-6038 A b | ACCEPTED | accepted |
| planet | 11 | TIC 97921547 | NGTS-33 b | rejected | data rule not met: light curves years [2024, 2025] span 27 d; pixel files years [2024, 2025] span 27 d (need >= 2 years and >= 300 d for both) |
| planet | 12 | TIC 158588995 | TOI-674 b | ACCEPTED | accepted |
| planet | 13 | TIC 240681314 | WASP-93 b | ACCEPTED | accepted |
| false_positive | 1 | TIC 197959526 | TOI-2303.01 | rejected | data rule not met: light curves years [2020] span 0 d; pixel files years [2020] span 0 d (need >= 2 years and >= 300 d for both) |
| false_positive | 2 | TIC 177126182 | TOI-982.01 | rejected | data rule not met: light curves years [2020] span 0 d; pixel files years [2020] span 0 d (need >= 2 years and >= 300 d for both) |
| false_positive | 3 | TIC 124702477 | TOI-2511.01 | rejected | data rule not met: light curves years [] span 0 d; pixel files years [] span 0 d (need >= 2 years and >= 300 d for both) |
| false_positive | 4 | TIC 33153766 | TOI-653.01 | ACCEPTED | accepted |
| false_positive | 5 | TIC 90919952 | TOI-1118.01 | rejected | data rule not met: light curves years [] span 0 d; pixel files years [] span 0 d (need >= 2 years and >= 300 d for both) |
| false_positive | 6 | TIC 157568289 | TOI-645.01 | rejected | data rule not met: light curves years [2020, 2021] span 27 d; pixel files years [2020, 2021] span 27 d (need >= 2 years and >= 300 d for both) |
| false_positive | 7 | TIC 197650870 | TOI-1481.01 | ACCEPTED | accepted |
| false_positive | 8 | TIC 312259170 | TOI-1529.01 | rejected | data rule not met: light curves years [] span 0 d; pixel files years [] span 0 d (need >= 2 years and >= 300 d for both) |
| false_positive | 9 | TIC 374200604 | TOI-4838.01 | ACCEPTED | accepted |
| false_positive | 10 | TIC 316402246 | TOI-1498.01 | rejected | data rule not met: light curves years [] span 0 d; pixel files years [] span 0 d (need >= 2 years and >= 300 d for both) |
| false_positive | 11 | TIC 317951248 | TOI-995.01 | rejected | data rule not met: light curves years [2020] span 0 d; pixel files years [2020] span 0 d (need >= 2 years and >= 300 d for both) |
| false_positive | 12 | TIC 350445771 | TOI-258.01 | ACCEPTED | accepted |
| false_positive | 13 | TIC 71396541 | TOI-4130.01 | rejected | data rule not met: light curves years [2021] span 0 d; pixel files years [2021] span 0 d (need >= 2 years and >= 300 d for both) |
| false_positive | 14 | TIC 210337597 | TOI-7324.01 | rejected | data rule not met: light curves years [2019] span 0 d; pixel files years [2019] span 0 d (need >= 2 years and >= 300 d for both) |
| false_positive | 15 | TIC 385105624 | TOI-1595.01 | rejected | data rule not met: light curves years [] span 0 d; pixel files years [] span 0 d (need >= 2 years and >= 300 d for both) |
| false_positive | 16 | TIC 106114491 | TOI-5876.01 | rejected | data rule not met: light curves years [2024] span 221 d; pixel files years [2024] span 221 d (need >= 2 years and >= 300 d for both) |
| false_positive | 17 | TIC 81429971 | TOI-598.01 | rejected | data rule not met: light curves years [2021] span 26 d; pixel files years [2021] span 26 d (need >= 2 years and >= 300 d for both) |
| false_positive | 18 | TIC 182943944 | TOI-1017.01 | rejected | data rule not met: light curves years [2021] span 26 d; pixel files years [2021] span 26 d (need >= 2 years and >= 300 d for both) |
| false_positive | 19 | TIC 317507345 | TOI-1615.01 | ACCEPTED | accepted |
| false_positive | 20 | TIC 141631253 | TOI-2987.01 | rejected | data rule not met: light curves years [2023] span 26 d; pixel files years [2023] span 26 d (need >= 2 years and >= 300 d for both) |
| false_positive | 21 | TIC 453230066 | TOI-3643.01 | rejected | data rule not met: light curves years [2022] span 0 d; pixel files years [2022] span 0 d (need >= 2 years and >= 300 d for both) |
| false_positive | 22 | TIC 89535068 | TOI-1983.01 | rejected | data rule not met: light curves years [2021] span 52 d; pixel files years [2021] span 52 d (need >= 2 years and >= 300 d for both) |
| false_positive | 23 | TIC 429295277 | TOI-1998.01 | rejected | data rule not met: light curves years [2021] span 0 d; pixel files years [2021] span 0 d (need >= 2 years and >= 300 d for both) |
| false_positive | 24 | TIC 372505528 | TOI-3994.01 | rejected | data rule not met: light curves years [] span 0 d; pixel files years [] span 0 d (need >= 2 years and >= 300 d for both) |
| false_positive | 25 | TIC 158916431 | TOI-2146.01 | ACCEPTED | accepted |
| false_positive | 26 | TIC 449050247 | TOI-951.01 | rejected | data rule not met: light curves years [2020] span 0 d; pixel files years [2020] span 0 d (need >= 2 years and >= 300 d for both) |
| false_positive | 27 | TIC 252537013 | TOI-6895.01 | rejected | data rule not met: light curves years [2024] span 189 d; pixel files years [2024] span 189 d (need >= 2 years and >= 300 d for both) |
| false_positive | 28 | TIC 316916655 | TOI-441.01 | ACCEPTED | accepted |
| false_positive | 29 | TIC 275384718 | TOI-1996.01 | rejected | data rule not met: light curves years [2021] span 0 d; pixel files years [2021] span 0 d (need >= 2 years and >= 300 d for both) |
| false_positive | 30 | TIC 287190564 | TOI-1309.01 | rejected | data rule not met: light curves years [2021] span 29 d; pixel files years [2021] span 29 d (need >= 2 years and >= 300 d for both) |
| false_positive | 31 | TIC 154459165 | TOI-611.01 | ACCEPTED | accepted |
| false_positive | 32 | TIC 18017227 | TOI-3890.01 | rejected | data rule not met: light curves years [2022] span 0 d; pixel files years [2022] span 0 d (need >= 2 years and >= 300 d for both) |
| false_positive | 33 | TIC 326347927 | TOI-5260.01 | rejected | data rule not met: light curves years [2024] span 0 d; pixel files years [2024] span 0 d (need >= 2 years and >= 300 d for both) |
| false_positive | 34 | TIC 253132689 | TOI-1971.01 | rejected | data rule not met: light curves years [2021] span 27 d; pixel files years [2021] span 27 d (need >= 2 years and >= 300 d for both) |
| false_positive | 35 | TIC 239638934 | TOI-2571.01 | rejected | MAST query failed: Timeout limit of 600 exceeded. |
| false_positive | 36 | TIC 141227133 | TOI-617.01 | rejected | data rule not met: light curves years [2021] span 26 d; pixel files years [2021] span 26 d (need >= 2 years and >= 300 d for both) |
| false_positive | 37 | TIC 294179389 | TOI-1310.01 | ACCEPTED | accepted |
| false_positive | 38 | TIC 99330090 | TOI-3883.01 | rejected | data rule not met: light curves years [2022] span 30 d; pixel files years [2022] span 30 d (need >= 2 years and >= 300 d for both) |
| false_positive | 39 | TIC 186599508 | TOI-1592.01 | rejected | data rule not met: light curves years [2019] span 0 d; pixel files years [2019] span 0 d (need >= 2 years and >= 300 d for both) |
| false_positive | 40 | TIC 315755496 | TOI-2053.01 | ACCEPTED | accepted |
