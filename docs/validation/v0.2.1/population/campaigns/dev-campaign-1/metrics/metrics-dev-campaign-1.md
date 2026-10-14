# Population metrics, campaign dev-campaign-1

Eligibility: campaign. computed from eligible campaign evidence.

Accepted risk: Between a detection and the manual commit, the lock marker and the journal exist only on disk and could be deleted or altered by hand; only the commit makes such an action visible.

Every point uses the fast plan of the test suite (section 7); false-alarm rates under the calibration plan could be higher. The SNR bands of blends use the expected SNR without the noise of the pixel data (Amendment 2, N2). Every case was analyzed in two slots whose records are identical (Amendment 4); the values are those of slot 1.

## M0

**Overall approval: FAILS.** The study is approved only if every criterion passes, C6 included. A rate can meet its limit while the study fails. Failed: C1 refuted planets, below, white, C1 refuted planets, near, white, C1 refuted planets, measurable, white, C2 flagged false positives, measurable, white, C3 INCONCLUSIVE, planet, measurable, white, C5 planets refuted only by own-TIC eb_catalog, white, C1 refuted planets, below, correlated, C1 refuted planets, near, correlated, C1 refuted planets, measurable, correlated, C5 planets refuted only by own-TIC eb_catalog, correlated.

Statuses (per condition): {'analyzed': 7600}

| Criterion | k | n | rate | bound | passes |
|---|---|---|---|---|---|
| C1 refuted planets, below, white | 121 | 250 | 0.4840 | 0.5379 | False |
| C1 refuted planets, near, white | 126 | 250 | 0.5040 | 0.5578 | False |
| C1 refuted planets, measurable, white | 63 | 250 | 0.2520 | 0.3012 | False |
| C2 flagged false positives, measurable, white | 161 | 250 | 0.6440 | 0.5911 | False |
| C3 INCONCLUSIVE, planet, measurable, white | 57 | 250 | 0.2280 | 0.2760 | False |
| C3 INCONCLUSIVE, false_positive, measurable, white | 26 | 250 | 0.1040 | 0.1414 | True |
| C4 false alarm, white | 5 | 2200 | 0.0023 | 0.0048 | True |
| C5 planets refuted only by own-TIC eb_catalog, white | 214 | 450 | - | - | False |
| C1 refuted planets, below, correlated | 117 | 250 | 0.4680 | 0.5220 | False |
| C1 refuted planets, near, correlated | 92 | 250 | 0.3680 | 0.4212 | False |
| C1 refuted planets, measurable, correlated | 56 | 250 | 0.2240 | 0.2717 | False |
| C2 flagged false positives, measurable, correlated | 176 | 250 | 0.7040 | 0.6529 | True |
| C3 INCONCLUSIVE, planet, measurable, correlated | 4 | 250 | 0.0160 | 0.0362 | True |
| C3 INCONCLUSIVE, false_positive, measurable, correlated | 15 | 250 | 0.0600 | 0.0909 | True |
| C4 false alarm, correlated | 0 | 600 | 0.0000 | 0.0050 | True |
| C5 planets refuted only by own-TIC eb_catalog, correlated | 282 | 450 | - | - | False |
| C6 analysis errors, missing results and integrity errors | 0 | - | - | - | True |

Families whose point estimate is worse than their limit:

| Condition | Family | Criterion | k / n | estimate | limit |
|---|---|---|---|---|---|
| i | false_positive|measurable|correlated|variability_masked | C2 (flagged_identity) | 0 / 62 | 0.0000 | 0.6 |
| i | false_positive|measurable|white|eb_odd_even | C3 (inconclusive) | 21 / 63 | 0.3333 | 0.2 |
| i | false_positive|measurable|white|variability_masked | C2 (flagged_identity) | 0 / 62 | 0.0000 | 0.6 |
| i | planet|below|correlated|two_years | C1 (refuted) | 15 / 100 | 0.1500 | 0.1 |
| i | planet|below|correlated|three_years | C1 (refuted) | 48 / 50 | 0.9600 | 0.1 |
| i | planet|below|correlated|variability_some_years | C1 (refuted) | 50 / 50 | 1.0000 | 0.1 |
| i | planet|below|white|two_years | C1 (refuted) | 28 / 100 | 0.2800 | 0.1 |
| i | planet|below|white|three_years | C1 (refuted) | 17 / 50 | 0.3400 | 0.1 |
| i | planet|below|white|few_train | C1 (refuted) | 26 / 50 | 0.5200 | 0.1 |
| i | planet|below|white|variability_some_years | C1 (refuted) | 50 / 50 | 1.0000 | 0.1 |
| i | planet|measurable|correlated|variability_some_years | C1 (refuted) | 50 / 50 | 1.0000 | 0.1 |
| i | planet|measurable|white|two_years | C3 (inconclusive) | 42 / 100 | 0.4200 | 0.2 |
| i | planet|measurable|white|few_train | C3 (inconclusive) | 15 / 50 | 0.3000 | 0.2 |
| i | planet|measurable|white|variability_some_years | C1 (refuted) | 50 / 50 | 1.0000 | 0.1 |
| i | planet|near|correlated|three_years | C1 (refuted) | 32 / 50 | 0.6400 | 0.1 |
| i | planet|near|correlated|few_train | C1 (refuted) | 6 / 50 | 0.1200 | 0.1 |
| i | planet|near|correlated|variability_some_years | C1 (refuted) | 50 / 50 | 1.0000 | 0.1 |
| i | planet|near|white|two_years | C1 (refuted) | 25 / 100 | 0.2500 | 0.1 |
| i | planet|near|white|three_years | C1 (refuted) | 38 / 50 | 0.7600 | 0.1 |
| i | planet|near|white|few_train | C1 (refuted) | 13 / 50 | 0.2600 | 0.1 |
| i | planet|near|white|variability_some_years | C1 (refuted) | 50 / 50 | 1.0000 | 0.1 |
| ii | planet|below|correlated|two_years|own | C5 (refuted_only_by_eb_catalog) | 45 / 60 | 0.7500 | 0.0 |
| ii | planet|below|correlated|three_years|own | C5 (refuted_only_by_eb_catalog) | 1 / 30 | 0.0333 | 0.0 |
| ii | planet|below|correlated|few_train|own | C5 (refuted_only_by_eb_catalog) | 27 / 30 | 0.9000 | 0.0 |
| ii | planet|below|white|two_years|own | C5 (refuted_only_by_eb_catalog) | 22 / 60 | 0.3667 | 0.0 |
| ii | planet|below|white|few_train|own | C5 (refuted_only_by_eb_catalog) | 10 / 30 | 0.3333 | 0.0 |
| ii | planet|measurable|correlated|two_years|own | C5 (refuted_only_by_eb_catalog) | 60 / 60 | 1.0000 | 0.0 |
| ii | planet|measurable|correlated|three_years|own | C5 (refuted_only_by_eb_catalog) | 28 / 30 | 0.9333 | 0.0 |
| ii | planet|measurable|correlated|few_train|own | C5 (refuted_only_by_eb_catalog) | 28 / 30 | 0.9333 | 0.0 |
| ii | planet|measurable|white|two_years|own | C5 (refuted_only_by_eb_catalog) | 55 / 60 | 0.9167 | 0.0 |
| ii | planet|measurable|white|three_years|own | C5 (refuted_only_by_eb_catalog) | 27 / 30 | 0.9000 | 0.0 |
| ii | planet|measurable|white|few_train|own | C5 (refuted_only_by_eb_catalog) | 28 / 30 | 0.9333 | 0.0 |
| ii | planet|near|correlated|two_years|own | C5 (refuted_only_by_eb_catalog) | 57 / 60 | 0.9500 | 0.0 |
| ii | planet|near|correlated|three_years|own | C5 (refuted_only_by_eb_catalog) | 10 / 30 | 0.3333 | 0.0 |
| ii | planet|near|correlated|few_train|own | C5 (refuted_only_by_eb_catalog) | 26 / 30 | 0.8667 | 0.0 |
| ii | planet|near|white|two_years|own | C5 (refuted_only_by_eb_catalog) | 43 / 60 | 0.7167 | 0.0 |
| ii | planet|near|white|three_years|own | C5 (refuted_only_by_eb_catalog) | 7 / 30 | 0.2333 | 0.0 |
| ii | planet|near|white|few_train|own | C5 (refuted_only_by_eb_catalog) | 22 / 30 | 0.7333 | 0.0 |

Results by mechanism, condition (i):

| Family | n | refuted | inconclusive | false alarm | flagged (identity) | flagged (old) | refuted only by eb_catalog |
|---|---|---|---|---|---|---|---|
| false_positive|below|correlated|blend | 25 | 22 | 3 | 0 | 21 | 22 | 0 |
| false_positive|below|correlated|eb_odd_even | 25 | 6 | 19 | 0 | 3 | 6 | 0 |
| false_positive|below|correlated|eb_secondary | 25 | 8 | 17 | 0 | 8 | 8 | 0 |
| false_positive|below|correlated|variability_masked | 25 | 23 | 0 | 2 | 0 | 23 | 0 |
| false_positive|below|white|blend | 25 | 18 | 7 | 0 | 16 | 18 | 0 |
| false_positive|below|white|eb_odd_even | 25 | 6 | 19 | 0 | 6 | 6 | 0 |
| false_positive|below|white|eb_secondary | 25 | 8 | 17 | 0 | 6 | 8 | 0 |
| false_positive|below|white|variability_masked | 25 | 25 | 0 | 0 | 0 | 25 | 0 |
| false_positive|measurable|correlated|blend | 62 | 62 | 0 | 0 | 62 | 62 | 0 |
| false_positive|measurable|correlated|eb_odd_even | 63 | 51 | 7 | 5 | 51 | 51 | 0 |
| false_positive|measurable|correlated|eb_secondary | 63 | 63 | 0 | 0 | 63 | 63 | 0 |
| false_positive|measurable|correlated|variability_masked | 62 | 49 | 8 | 5 | 0 | 49 | 0 |
| false_positive|measurable|white|blend | 62 | 62 | 0 | 0 | 61 | 62 | 0 |
| false_positive|measurable|white|eb_odd_even | 63 | 42 | 21 | 0 | 42 | 42 | 0 |
| false_positive|measurable|white|eb_secondary | 63 | 58 | 5 | 0 | 58 | 58 | 0 |
| false_positive|measurable|white|variability_masked | 62 | 60 | 0 | 2 | 0 | 60 | 0 |
| false_positive|near|correlated|blend | 25 | 25 | 0 | 0 | 25 | 25 | 0 |
| false_positive|near|correlated|eb_odd_even | 25 | 7 | 18 | 0 | 7 | 7 | 0 |
| false_positive|near|correlated|eb_secondary | 25 | 18 | 6 | 1 | 18 | 18 | 0 |
| false_positive|near|correlated|variability_masked | 25 | 23 | 2 | 0 | 0 | 23 | 0 |
| false_positive|near|white|blend | 25 | 25 | 0 | 0 | 25 | 25 | 0 |
| false_positive|near|white|eb_odd_even | 25 | 5 | 19 | 1 | 5 | 5 | 0 |
| false_positive|near|white|eb_secondary | 25 | 15 | 10 | 0 | 15 | 15 | 0 |
| false_positive|near|white|variability_masked | 25 | 25 | 0 | 0 | 0 | 25 | 0 |
| no_transit|None|correlated|pure_noise | 240 | 108 | 132 | 0 | 0 | 108 | 0 |
| no_transit|None|correlated|trend | 180 | 69 | 111 | 0 | 0 | 69 | 0 |
| no_transit|None|correlated|trend_variability | 180 | 95 | 85 | 0 | 0 | 95 | 0 |
| no_transit|None|white|pure_noise | 880 | 43 | 837 | 0 | 0 | 43 | 0 |
| no_transit|None|white|trend | 660 | 54 | 606 | 0 | 0 | 54 | 0 |
| no_transit|None|white|trend_variability | 660 | 290 | 365 | 5 | 0 | 290 | 0 |
| planet|below|correlated|few_train | 50 | 4 | 31 | 15 | 3 | 4 | 0 |
| planet|below|correlated|three_years | 50 | 48 | 1 | 1 | 26 | 48 | 0 |
| planet|below|correlated|two_years | 100 | 15 | 81 | 4 | 3 | 15 | 0 |
| planet|below|correlated|variability_some_years | 50 | 50 | 0 | 0 | 1 | 50 | 0 |
| planet|below|white|few_train | 50 | 26 | 23 | 1 | 22 | 26 | 0 |
| planet|below|white|three_years | 50 | 17 | 33 | 0 | 12 | 17 | 0 |
| planet|below|white|two_years | 100 | 28 | 72 | 0 | 25 | 28 | 0 |
| planet|below|white|variability_some_years | 50 | 50 | 0 | 0 | 0 | 50 | 0 |
| planet|measurable|correlated|few_train | 50 | 3 | 1 | 46 | 3 | 3 | 0 |
| planet|measurable|correlated|three_years | 50 | 2 | 0 | 48 | 2 | 2 | 0 |
| planet|measurable|correlated|two_years | 100 | 1 | 3 | 96 | 1 | 1 | 0 |
| planet|measurable|correlated|variability_some_years | 50 | 50 | 0 | 0 | 45 | 50 | 0 |
| planet|measurable|white|few_train | 50 | 3 | 15 | 32 | 3 | 3 | 0 |
| planet|measurable|white|three_years | 50 | 4 | 0 | 46 | 4 | 4 | 0 |
| planet|measurable|white|two_years | 100 | 6 | 42 | 52 | 6 | 6 | 0 |
| planet|measurable|white|variability_some_years | 50 | 50 | 0 | 0 | 11 | 50 | 0 |
| planet|near|correlated|few_train | 50 | 6 | 10 | 34 | 6 | 6 | 0 |
| planet|near|correlated|three_years | 50 | 32 | 0 | 18 | 32 | 32 | 0 |
| planet|near|correlated|two_years | 100 | 4 | 57 | 39 | 4 | 4 | 0 |
| planet|near|correlated|variability_some_years | 50 | 50 | 0 | 0 | 15 | 50 | 0 |
| planet|near|white|few_train | 50 | 13 | 32 | 5 | 13 | 13 | 0 |
| planet|near|white|three_years | 50 | 38 | 1 | 11 | 37 | 38 | 0 |
| planet|near|white|two_years | 100 | 25 | 74 | 1 | 24 | 25 | 0 |
| planet|near|white|variability_some_years | 50 | 50 | 0 | 0 | 0 | 50 | 0 |

Results by mechanism, condition (ii):

| Family | n | refuted | inconclusive | false alarm | flagged (identity) | flagged (old) | refuted only by eb_catalog |
|---|---|---|---|---|---|---|---|
| false_positive|below|correlated|blend|independent | 5 | 4 | 1 | 0 | 3 | 4 | 0 |
| false_positive|below|correlated|blend|neighbor | 5 | 5 | 0 | 0 | 5 | 5 | 0 |
| false_positive|below|correlated|blend|own | 15 | 13 | 2 | 0 | 13 | 13 | 0 |
| false_positive|below|correlated|eb_odd_even|independent | 5 | 5 | 0 | 0 | 0 | 1 | 4 |
| false_positive|below|correlated|eb_odd_even|neighbor | 5 | 5 | 0 | 0 | 1 | 1 | 4 |
| false_positive|below|correlated|eb_odd_even|own | 15 | 14 | 1 | 0 | 2 | 4 | 10 |
| false_positive|below|correlated|eb_secondary|independent | 5 | 5 | 0 | 0 | 2 | 2 | 3 |
| false_positive|below|correlated|eb_secondary|neighbor | 5 | 5 | 0 | 0 | 2 | 2 | 3 |
| false_positive|below|correlated|eb_secondary|own | 15 | 15 | 0 | 0 | 4 | 4 | 11 |
| false_positive|below|correlated|variability_masked|independent | 5 | 5 | 0 | 0 | 0 | 5 | 0 |
| false_positive|below|correlated|variability_masked|neighbor | 5 | 4 | 0 | 1 | 0 | 4 | 0 |
| false_positive|below|correlated|variability_masked|own | 15 | 14 | 0 | 1 | 0 | 14 | 0 |
| false_positive|below|white|blend|independent | 5 | 4 | 1 | 0 | 3 | 4 | 0 |
| false_positive|below|white|blend|neighbor | 5 | 3 | 2 | 0 | 3 | 3 | 0 |
| false_positive|below|white|blend|own | 15 | 11 | 4 | 0 | 10 | 11 | 0 |
| false_positive|below|white|eb_odd_even|independent | 5 | 5 | 0 | 0 | 1 | 1 | 4 |
| false_positive|below|white|eb_odd_even|neighbor | 5 | 4 | 1 | 0 | 1 | 1 | 3 |
| false_positive|below|white|eb_odd_even|own | 15 | 13 | 2 | 0 | 4 | 4 | 9 |
| false_positive|below|white|eb_secondary|independent | 5 | 4 | 1 | 0 | 0 | 0 | 4 |
| false_positive|below|white|eb_secondary|neighbor | 5 | 5 | 0 | 0 | 3 | 3 | 2 |
| false_positive|below|white|eb_secondary|own | 15 | 12 | 3 | 0 | 3 | 5 | 7 |
| false_positive|below|white|variability_masked|independent | 5 | 5 | 0 | 0 | 0 | 5 | 0 |
| false_positive|below|white|variability_masked|neighbor | 5 | 5 | 0 | 0 | 0 | 5 | 0 |
| false_positive|below|white|variability_masked|own | 15 | 15 | 0 | 0 | 0 | 15 | 0 |
| false_positive|measurable|correlated|blend|independent | 12 | 12 | 0 | 0 | 12 | 12 | 0 |
| false_positive|measurable|correlated|blend|neighbor | 12 | 12 | 0 | 0 | 12 | 12 | 0 |
| false_positive|measurable|correlated|blend|own | 38 | 38 | 0 | 0 | 38 | 38 | 0 |
| false_positive|measurable|correlated|eb_odd_even|independent | 13 | 13 | 0 | 0 | 11 | 11 | 2 |
| false_positive|measurable|correlated|eb_odd_even|neighbor | 13 | 13 | 0 | 0 | 9 | 9 | 4 |
| false_positive|measurable|correlated|eb_odd_even|own | 37 | 37 | 0 | 0 | 31 | 31 | 6 |
| false_positive|measurable|correlated|eb_secondary|independent | 12 | 12 | 0 | 0 | 12 | 12 | 0 |
| false_positive|measurable|correlated|eb_secondary|neighbor | 12 | 12 | 0 | 0 | 12 | 12 | 0 |
| false_positive|measurable|correlated|eb_secondary|own | 39 | 39 | 0 | 0 | 39 | 39 | 0 |
| false_positive|measurable|correlated|variability_masked|independent | 13 | 11 | 2 | 0 | 0 | 11 | 0 |
| false_positive|measurable|correlated|variability_masked|neighbor | 13 | 11 | 1 | 1 | 0 | 11 | 0 |
| false_positive|measurable|correlated|variability_masked|own | 36 | 27 | 5 | 4 | 0 | 27 | 0 |
| false_positive|measurable|white|blend|independent | 12 | 12 | 0 | 0 | 11 | 12 | 0 |
| false_positive|measurable|white|blend|neighbor | 12 | 12 | 0 | 0 | 12 | 12 | 0 |
| false_positive|measurable|white|blend|own | 38 | 38 | 0 | 0 | 38 | 38 | 0 |
| false_positive|measurable|white|eb_odd_even|independent | 13 | 13 | 0 | 0 | 9 | 9 | 4 |
| false_positive|measurable|white|eb_odd_even|neighbor | 13 | 13 | 0 | 0 | 9 | 9 | 4 |
| false_positive|measurable|white|eb_odd_even|own | 37 | 37 | 0 | 0 | 24 | 24 | 13 |
| false_positive|measurable|white|eb_secondary|independent | 12 | 12 | 0 | 0 | 10 | 10 | 2 |
| false_positive|measurable|white|eb_secondary|neighbor | 12 | 12 | 0 | 0 | 12 | 12 | 0 |
| false_positive|measurable|white|eb_secondary|own | 39 | 39 | 0 | 0 | 36 | 36 | 3 |
| false_positive|measurable|white|variability_masked|independent | 13 | 12 | 0 | 1 | 0 | 12 | 0 |
| false_positive|measurable|white|variability_masked|neighbor | 13 | 13 | 0 | 0 | 0 | 13 | 0 |
| false_positive|measurable|white|variability_masked|own | 36 | 35 | 0 | 1 | 0 | 35 | 0 |
| false_positive|near|correlated|blend|independent | 5 | 5 | 0 | 0 | 5 | 5 | 0 |
| false_positive|near|correlated|blend|neighbor | 5 | 5 | 0 | 0 | 5 | 5 | 0 |
| false_positive|near|correlated|blend|own | 15 | 15 | 0 | 0 | 15 | 15 | 0 |
| false_positive|near|correlated|eb_odd_even|independent | 5 | 5 | 0 | 0 | 1 | 1 | 4 |
| false_positive|near|correlated|eb_odd_even|neighbor | 5 | 5 | 0 | 0 | 0 | 0 | 5 |
| false_positive|near|correlated|eb_odd_even|own | 15 | 15 | 0 | 0 | 6 | 6 | 9 |
| false_positive|near|correlated|eb_secondary|independent | 5 | 5 | 0 | 0 | 4 | 4 | 1 |
| false_positive|near|correlated|eb_secondary|neighbor | 5 | 5 | 0 | 0 | 1 | 1 | 4 |
| false_positive|near|correlated|eb_secondary|own | 15 | 15 | 0 | 0 | 13 | 13 | 2 |
| false_positive|near|correlated|variability_masked|independent | 5 | 5 | 0 | 0 | 0 | 5 | 0 |
| false_positive|near|correlated|variability_masked|neighbor | 5 | 5 | 0 | 0 | 0 | 5 | 0 |
| false_positive|near|correlated|variability_masked|own | 15 | 13 | 2 | 0 | 0 | 13 | 0 |
| false_positive|near|white|blend|independent | 5 | 5 | 0 | 0 | 5 | 5 | 0 |
| false_positive|near|white|blend|neighbor | 5 | 5 | 0 | 0 | 5 | 5 | 0 |
| false_positive|near|white|blend|own | 15 | 15 | 0 | 0 | 15 | 15 | 0 |
| false_positive|near|white|eb_odd_even|independent | 5 | 5 | 0 | 0 | 1 | 1 | 4 |
| false_positive|near|white|eb_odd_even|neighbor | 5 | 5 | 0 | 0 | 2 | 2 | 3 |
| false_positive|near|white|eb_odd_even|own | 15 | 15 | 0 | 0 | 2 | 2 | 13 |
| false_positive|near|white|eb_secondary|independent | 5 | 5 | 0 | 0 | 4 | 4 | 1 |
| false_positive|near|white|eb_secondary|neighbor | 5 | 5 | 0 | 0 | 1 | 1 | 4 |
| false_positive|near|white|eb_secondary|own | 15 | 15 | 0 | 0 | 10 | 10 | 5 |
| false_positive|near|white|variability_masked|independent | 5 | 5 | 0 | 0 | 0 | 5 | 0 |
| false_positive|near|white|variability_masked|neighbor | 5 | 5 | 0 | 0 | 0 | 5 | 0 |
| false_positive|near|white|variability_masked|own | 15 | 15 | 0 | 0 | 0 | 15 | 0 |
| planet|below|correlated|few_train|independent | 10 | 10 | 0 | 0 | 1 | 1 | 9 |
| planet|below|correlated|few_train|neighbor | 10 | 10 | 0 | 0 | 1 | 1 | 9 |
| planet|below|correlated|few_train|own | 30 | 29 | 1 | 0 | 1 | 2 | 27 |
| planet|below|correlated|three_years|independent | 10 | 10 | 0 | 0 | 5 | 10 | 0 |
| planet|below|correlated|three_years|neighbor | 10 | 9 | 1 | 0 | 5 | 9 | 0 |
| planet|below|correlated|three_years|own | 30 | 30 | 0 | 0 | 16 | 29 | 1 |
| planet|below|correlated|two_years|independent | 20 | 16 | 4 | 0 | 1 | 2 | 14 |
| planet|below|correlated|two_years|neighbor | 20 | 19 | 1 | 0 | 0 | 3 | 16 |
| planet|below|correlated|two_years|own | 60 | 55 | 5 | 0 | 2 | 10 | 45 |
| planet|below|correlated|variability_some_years|independent | 10 | 10 | 0 | 0 | 1 | 10 | 0 |
| planet|below|correlated|variability_some_years|neighbor | 10 | 10 | 0 | 0 | 0 | 10 | 0 |
| planet|below|correlated|variability_some_years|own | 30 | 30 | 0 | 0 | 0 | 30 | 0 |
| planet|below|white|few_train|independent | 10 | 9 | 1 | 0 | 5 | 5 | 4 |
| planet|below|white|few_train|neighbor | 10 | 5 | 5 | 0 | 3 | 5 | 0 |
| planet|below|white|few_train|own | 30 | 26 | 4 | 0 | 14 | 16 | 10 |
| planet|below|white|three_years|independent | 10 | 3 | 7 | 0 | 2 | 3 | 0 |
| planet|below|white|three_years|neighbor | 10 | 3 | 7 | 0 | 3 | 3 | 0 |
| planet|below|white|three_years|own | 30 | 11 | 19 | 0 | 7 | 11 | 0 |
| planet|below|white|two_years|independent | 20 | 10 | 10 | 0 | 3 | 3 | 7 |
| planet|below|white|two_years|neighbor | 20 | 11 | 9 | 0 | 5 | 5 | 6 |
| planet|below|white|two_years|own | 60 | 42 | 18 | 0 | 17 | 20 | 22 |
| planet|below|white|variability_some_years|independent | 10 | 10 | 0 | 0 | 0 | 10 | 0 |
| planet|below|white|variability_some_years|neighbor | 10 | 10 | 0 | 0 | 0 | 10 | 0 |
| planet|below|white|variability_some_years|own | 30 | 30 | 0 | 0 | 0 | 30 | 0 |
| planet|measurable|correlated|few_train|independent | 10 | 10 | 0 | 0 | 1 | 1 | 9 |
| planet|measurable|correlated|few_train|neighbor | 10 | 10 | 0 | 0 | 0 | 0 | 10 |
| planet|measurable|correlated|few_train|own | 30 | 30 | 0 | 0 | 2 | 2 | 28 |
| planet|measurable|correlated|three_years|independent | 10 | 10 | 0 | 0 | 0 | 0 | 10 |
| planet|measurable|correlated|three_years|neighbor | 10 | 10 | 0 | 0 | 0 | 0 | 10 |
| planet|measurable|correlated|three_years|own | 30 | 30 | 0 | 0 | 2 | 2 | 28 |
| planet|measurable|correlated|two_years|independent | 20 | 20 | 0 | 0 | 1 | 1 | 19 |
| planet|measurable|correlated|two_years|neighbor | 20 | 20 | 0 | 0 | 0 | 0 | 20 |
| planet|measurable|correlated|two_years|own | 60 | 60 | 0 | 0 | 0 | 0 | 60 |
| planet|measurable|correlated|variability_some_years|independent | 10 | 10 | 0 | 0 | 10 | 10 | 0 |
| planet|measurable|correlated|variability_some_years|neighbor | 10 | 10 | 0 | 0 | 9 | 10 | 0 |
| planet|measurable|correlated|variability_some_years|own | 30 | 30 | 0 | 0 | 26 | 30 | 0 |
| planet|measurable|white|few_train|independent | 10 | 10 | 0 | 0 | 1 | 1 | 9 |
| planet|measurable|white|few_train|neighbor | 10 | 10 | 0 | 0 | 0 | 0 | 10 |
| planet|measurable|white|few_train|own | 30 | 30 | 0 | 0 | 2 | 2 | 28 |
| planet|measurable|white|three_years|independent | 10 | 10 | 0 | 0 | 0 | 0 | 10 |
| planet|measurable|white|three_years|neighbor | 10 | 10 | 0 | 0 | 1 | 1 | 9 |
| planet|measurable|white|three_years|own | 30 | 30 | 0 | 0 | 3 | 3 | 27 |
| planet|measurable|white|two_years|independent | 20 | 20 | 0 | 0 | 0 | 0 | 20 |
| planet|measurable|white|two_years|neighbor | 20 | 20 | 0 | 0 | 1 | 1 | 19 |
| planet|measurable|white|two_years|own | 60 | 60 | 0 | 0 | 5 | 5 | 55 |
| planet|measurable|white|variability_some_years|independent | 10 | 10 | 0 | 0 | 3 | 10 | 0 |
| planet|measurable|white|variability_some_years|neighbor | 10 | 10 | 0 | 0 | 5 | 10 | 0 |
| planet|measurable|white|variability_some_years|own | 30 | 30 | 0 | 0 | 3 | 30 | 0 |
| planet|near|correlated|few_train|independent | 10 | 10 | 0 | 0 | 1 | 1 | 9 |
| planet|near|correlated|few_train|neighbor | 10 | 10 | 0 | 0 | 1 | 1 | 9 |
| planet|near|correlated|few_train|own | 30 | 30 | 0 | 0 | 4 | 4 | 26 |
| planet|near|correlated|three_years|independent | 10 | 10 | 0 | 0 | 4 | 4 | 6 |
| planet|near|correlated|three_years|neighbor | 10 | 10 | 0 | 0 | 8 | 8 | 2 |
| planet|near|correlated|three_years|own | 30 | 30 | 0 | 0 | 20 | 20 | 10 |
| planet|near|correlated|two_years|independent | 20 | 20 | 0 | 0 | 1 | 1 | 19 |
| planet|near|correlated|two_years|neighbor | 20 | 20 | 0 | 0 | 0 | 0 | 20 |
| planet|near|correlated|two_years|own | 60 | 60 | 0 | 0 | 3 | 3 | 57 |
| planet|near|correlated|variability_some_years|independent | 10 | 10 | 0 | 0 | 4 | 10 | 0 |
| planet|near|correlated|variability_some_years|neighbor | 10 | 10 | 0 | 0 | 0 | 10 | 0 |
| planet|near|correlated|variability_some_years|own | 30 | 30 | 0 | 0 | 11 | 30 | 0 |
| planet|near|white|few_train|independent | 10 | 10 | 0 | 0 | 5 | 5 | 5 |
| planet|near|white|few_train|neighbor | 10 | 10 | 0 | 0 | 0 | 0 | 10 |
| planet|near|white|few_train|own | 30 | 30 | 0 | 0 | 8 | 8 | 22 |
| planet|near|white|three_years|independent | 10 | 10 | 0 | 0 | 6 | 6 | 4 |
| planet|near|white|three_years|neighbor | 10 | 10 | 0 | 0 | 10 | 10 | 0 |
| planet|near|white|three_years|own | 30 | 29 | 1 | 0 | 21 | 22 | 7 |
| planet|near|white|two_years|independent | 20 | 20 | 0 | 0 | 2 | 2 | 18 |
| planet|near|white|two_years|neighbor | 20 | 20 | 0 | 0 | 6 | 6 | 14 |
| planet|near|white|two_years|own | 60 | 60 | 0 | 0 | 16 | 17 | 43 |
| planet|near|white|variability_some_years|independent | 10 | 10 | 0 | 0 | 0 | 10 | 0 |
| planet|near|white|variability_some_years|neighbor | 10 | 10 | 0 | 0 | 0 | 10 | 0 |
| planet|near|white|variability_some_years|own | 30 | 30 | 0 | 0 | 0 | 30 | 0 |

## M1

**Overall approval: FAILS.** The study is approved only if every criterion passes, C6 included. A rate can meet its limit while the study fails. Failed: C1 refuted planets, below, white, C1 refuted planets, near, white, C1 refuted planets, measurable, white, C2 flagged false positives, measurable, white, C3 INCONCLUSIVE, planet, measurable, white, C5 planets refuted only by own-TIC eb_catalog, white, C1 refuted planets, below, correlated, C1 refuted planets, near, correlated, C1 refuted planets, measurable, correlated, C5 planets refuted only by own-TIC eb_catalog, correlated.

Statuses (per condition): {'analyzed': 7600}

| Criterion | k | n | rate | bound | passes |
|---|---|---|---|---|---|
| C1 refuted planets, below, white | 121 | 250 | 0.4840 | 0.5379 | False |
| C1 refuted planets, near, white | 126 | 250 | 0.5040 | 0.5578 | False |
| C1 refuted planets, measurable, white | 63 | 250 | 0.2520 | 0.3012 | False |
| C2 flagged false positives, measurable, white | 161 | 250 | 0.6440 | 0.5911 | False |
| C3 INCONCLUSIVE, planet, measurable, white | 57 | 250 | 0.2280 | 0.2760 | False |
| C3 INCONCLUSIVE, false_positive, measurable, white | 26 | 250 | 0.1040 | 0.1414 | True |
| C4 false alarm, white | 5 | 2200 | 0.0023 | 0.0048 | True |
| C5 planets refuted only by own-TIC eb_catalog, white | 214 | 450 | - | - | False |
| C1 refuted planets, below, correlated | 117 | 250 | 0.4680 | 0.5220 | False |
| C1 refuted planets, near, correlated | 92 | 250 | 0.3680 | 0.4212 | False |
| C1 refuted planets, measurable, correlated | 56 | 250 | 0.2240 | 0.2717 | False |
| C2 flagged false positives, measurable, correlated | 176 | 250 | 0.7040 | 0.6529 | True |
| C3 INCONCLUSIVE, planet, measurable, correlated | 4 | 250 | 0.0160 | 0.0362 | True |
| C3 INCONCLUSIVE, false_positive, measurable, correlated | 15 | 250 | 0.0600 | 0.0909 | True |
| C4 false alarm, correlated | 0 | 600 | 0.0000 | 0.0050 | True |
| C5 planets refuted only by own-TIC eb_catalog, correlated | 282 | 450 | - | - | False |
| C6 analysis errors, missing results and integrity errors | 0 | - | - | - | True |

Families whose point estimate is worse than their limit:

| Condition | Family | Criterion | k / n | estimate | limit |
|---|---|---|---|---|---|
| i | false_positive|measurable|correlated|variability_masked | C2 (flagged_identity) | 0 / 62 | 0.0000 | 0.6 |
| i | false_positive|measurable|white|eb_odd_even | C3 (inconclusive) | 21 / 63 | 0.3333 | 0.2 |
| i | false_positive|measurable|white|variability_masked | C2 (flagged_identity) | 0 / 62 | 0.0000 | 0.6 |
| i | planet|below|correlated|two_years | C1 (refuted) | 15 / 100 | 0.1500 | 0.1 |
| i | planet|below|correlated|three_years | C1 (refuted) | 48 / 50 | 0.9600 | 0.1 |
| i | planet|below|correlated|variability_some_years | C1 (refuted) | 50 / 50 | 1.0000 | 0.1 |
| i | planet|below|white|two_years | C1 (refuted) | 28 / 100 | 0.2800 | 0.1 |
| i | planet|below|white|three_years | C1 (refuted) | 17 / 50 | 0.3400 | 0.1 |
| i | planet|below|white|few_train | C1 (refuted) | 26 / 50 | 0.5200 | 0.1 |
| i | planet|below|white|variability_some_years | C1 (refuted) | 50 / 50 | 1.0000 | 0.1 |
| i | planet|measurable|correlated|variability_some_years | C1 (refuted) | 50 / 50 | 1.0000 | 0.1 |
| i | planet|measurable|white|two_years | C3 (inconclusive) | 42 / 100 | 0.4200 | 0.2 |
| i | planet|measurable|white|few_train | C3 (inconclusive) | 15 / 50 | 0.3000 | 0.2 |
| i | planet|measurable|white|variability_some_years | C1 (refuted) | 50 / 50 | 1.0000 | 0.1 |
| i | planet|near|correlated|three_years | C1 (refuted) | 32 / 50 | 0.6400 | 0.1 |
| i | planet|near|correlated|few_train | C1 (refuted) | 6 / 50 | 0.1200 | 0.1 |
| i | planet|near|correlated|variability_some_years | C1 (refuted) | 50 / 50 | 1.0000 | 0.1 |
| i | planet|near|white|two_years | C1 (refuted) | 25 / 100 | 0.2500 | 0.1 |
| i | planet|near|white|three_years | C1 (refuted) | 38 / 50 | 0.7600 | 0.1 |
| i | planet|near|white|few_train | C1 (refuted) | 13 / 50 | 0.2600 | 0.1 |
| i | planet|near|white|variability_some_years | C1 (refuted) | 50 / 50 | 1.0000 | 0.1 |
| ii | planet|below|correlated|two_years|own | C5 (refuted_only_by_eb_catalog) | 45 / 60 | 0.7500 | 0.0 |
| ii | planet|below|correlated|three_years|own | C5 (refuted_only_by_eb_catalog) | 1 / 30 | 0.0333 | 0.0 |
| ii | planet|below|correlated|few_train|own | C5 (refuted_only_by_eb_catalog) | 27 / 30 | 0.9000 | 0.0 |
| ii | planet|below|white|two_years|own | C5 (refuted_only_by_eb_catalog) | 22 / 60 | 0.3667 | 0.0 |
| ii | planet|below|white|few_train|own | C5 (refuted_only_by_eb_catalog) | 10 / 30 | 0.3333 | 0.0 |
| ii | planet|measurable|correlated|two_years|own | C5 (refuted_only_by_eb_catalog) | 60 / 60 | 1.0000 | 0.0 |
| ii | planet|measurable|correlated|three_years|own | C5 (refuted_only_by_eb_catalog) | 28 / 30 | 0.9333 | 0.0 |
| ii | planet|measurable|correlated|few_train|own | C5 (refuted_only_by_eb_catalog) | 28 / 30 | 0.9333 | 0.0 |
| ii | planet|measurable|white|two_years|own | C5 (refuted_only_by_eb_catalog) | 55 / 60 | 0.9167 | 0.0 |
| ii | planet|measurable|white|three_years|own | C5 (refuted_only_by_eb_catalog) | 27 / 30 | 0.9000 | 0.0 |
| ii | planet|measurable|white|few_train|own | C5 (refuted_only_by_eb_catalog) | 28 / 30 | 0.9333 | 0.0 |
| ii | planet|near|correlated|two_years|own | C5 (refuted_only_by_eb_catalog) | 57 / 60 | 0.9500 | 0.0 |
| ii | planet|near|correlated|three_years|own | C5 (refuted_only_by_eb_catalog) | 10 / 30 | 0.3333 | 0.0 |
| ii | planet|near|correlated|few_train|own | C5 (refuted_only_by_eb_catalog) | 26 / 30 | 0.8667 | 0.0 |
| ii | planet|near|white|two_years|own | C5 (refuted_only_by_eb_catalog) | 43 / 60 | 0.7167 | 0.0 |
| ii | planet|near|white|three_years|own | C5 (refuted_only_by_eb_catalog) | 7 / 30 | 0.2333 | 0.0 |
| ii | planet|near|white|few_train|own | C5 (refuted_only_by_eb_catalog) | 22 / 30 | 0.7333 | 0.0 |

Results by mechanism, condition (i):

| Family | n | refuted | inconclusive | false alarm | flagged (identity) | flagged (old) | refuted only by eb_catalog |
|---|---|---|---|---|---|---|---|
| false_positive|below|correlated|blend | 25 | 22 | 3 | 0 | 21 | 22 | 0 |
| false_positive|below|correlated|eb_odd_even | 25 | 6 | 19 | 0 | 3 | 6 | 0 |
| false_positive|below|correlated|eb_secondary | 25 | 8 | 17 | 0 | 8 | 8 | 0 |
| false_positive|below|correlated|variability_masked | 25 | 23 | 0 | 2 | 0 | 23 | 0 |
| false_positive|below|white|blend | 25 | 18 | 7 | 0 | 16 | 18 | 0 |
| false_positive|below|white|eb_odd_even | 25 | 6 | 19 | 0 | 6 | 6 | 0 |
| false_positive|below|white|eb_secondary | 25 | 8 | 17 | 0 | 6 | 8 | 0 |
| false_positive|below|white|variability_masked | 25 | 25 | 0 | 0 | 0 | 25 | 0 |
| false_positive|measurable|correlated|blend | 62 | 62 | 0 | 0 | 62 | 62 | 0 |
| false_positive|measurable|correlated|eb_odd_even | 63 | 51 | 7 | 5 | 51 | 51 | 0 |
| false_positive|measurable|correlated|eb_secondary | 63 | 63 | 0 | 0 | 63 | 63 | 0 |
| false_positive|measurable|correlated|variability_masked | 62 | 49 | 8 | 5 | 0 | 49 | 0 |
| false_positive|measurable|white|blend | 62 | 62 | 0 | 0 | 61 | 62 | 0 |
| false_positive|measurable|white|eb_odd_even | 63 | 42 | 21 | 0 | 42 | 42 | 0 |
| false_positive|measurable|white|eb_secondary | 63 | 58 | 5 | 0 | 58 | 58 | 0 |
| false_positive|measurable|white|variability_masked | 62 | 60 | 0 | 2 | 0 | 60 | 0 |
| false_positive|near|correlated|blend | 25 | 25 | 0 | 0 | 25 | 25 | 0 |
| false_positive|near|correlated|eb_odd_even | 25 | 7 | 18 | 0 | 7 | 7 | 0 |
| false_positive|near|correlated|eb_secondary | 25 | 18 | 6 | 1 | 18 | 18 | 0 |
| false_positive|near|correlated|variability_masked | 25 | 23 | 2 | 0 | 0 | 23 | 0 |
| false_positive|near|white|blend | 25 | 25 | 0 | 0 | 25 | 25 | 0 |
| false_positive|near|white|eb_odd_even | 25 | 5 | 19 | 1 | 5 | 5 | 0 |
| false_positive|near|white|eb_secondary | 25 | 15 | 10 | 0 | 15 | 15 | 0 |
| false_positive|near|white|variability_masked | 25 | 25 | 0 | 0 | 0 | 25 | 0 |
| no_transit|None|correlated|pure_noise | 240 | 108 | 132 | 0 | 0 | 108 | 0 |
| no_transit|None|correlated|trend | 180 | 69 | 111 | 0 | 0 | 69 | 0 |
| no_transit|None|correlated|trend_variability | 180 | 95 | 85 | 0 | 0 | 95 | 0 |
| no_transit|None|white|pure_noise | 880 | 43 | 837 | 0 | 0 | 43 | 0 |
| no_transit|None|white|trend | 660 | 54 | 606 | 0 | 0 | 54 | 0 |
| no_transit|None|white|trend_variability | 660 | 290 | 365 | 5 | 0 | 290 | 0 |
| planet|below|correlated|few_train | 50 | 4 | 31 | 15 | 3 | 4 | 0 |
| planet|below|correlated|three_years | 50 | 48 | 1 | 1 | 26 | 48 | 0 |
| planet|below|correlated|two_years | 100 | 15 | 81 | 4 | 3 | 15 | 0 |
| planet|below|correlated|variability_some_years | 50 | 50 | 0 | 0 | 1 | 50 | 0 |
| planet|below|white|few_train | 50 | 26 | 23 | 1 | 22 | 26 | 0 |
| planet|below|white|three_years | 50 | 17 | 33 | 0 | 12 | 17 | 0 |
| planet|below|white|two_years | 100 | 28 | 72 | 0 | 25 | 28 | 0 |
| planet|below|white|variability_some_years | 50 | 50 | 0 | 0 | 0 | 50 | 0 |
| planet|measurable|correlated|few_train | 50 | 3 | 1 | 46 | 3 | 3 | 0 |
| planet|measurable|correlated|three_years | 50 | 2 | 0 | 48 | 2 | 2 | 0 |
| planet|measurable|correlated|two_years | 100 | 1 | 3 | 96 | 1 | 1 | 0 |
| planet|measurable|correlated|variability_some_years | 50 | 50 | 0 | 0 | 45 | 50 | 0 |
| planet|measurable|white|few_train | 50 | 3 | 15 | 32 | 3 | 3 | 0 |
| planet|measurable|white|three_years | 50 | 4 | 0 | 46 | 4 | 4 | 0 |
| planet|measurable|white|two_years | 100 | 6 | 42 | 52 | 6 | 6 | 0 |
| planet|measurable|white|variability_some_years | 50 | 50 | 0 | 0 | 11 | 50 | 0 |
| planet|near|correlated|few_train | 50 | 6 | 10 | 34 | 6 | 6 | 0 |
| planet|near|correlated|three_years | 50 | 32 | 0 | 18 | 32 | 32 | 0 |
| planet|near|correlated|two_years | 100 | 4 | 57 | 39 | 4 | 4 | 0 |
| planet|near|correlated|variability_some_years | 50 | 50 | 0 | 0 | 15 | 50 | 0 |
| planet|near|white|few_train | 50 | 13 | 32 | 5 | 13 | 13 | 0 |
| planet|near|white|three_years | 50 | 38 | 1 | 11 | 37 | 38 | 0 |
| planet|near|white|two_years | 100 | 25 | 74 | 1 | 24 | 25 | 0 |
| planet|near|white|variability_some_years | 50 | 50 | 0 | 0 | 0 | 50 | 0 |

Results by mechanism, condition (ii):

| Family | n | refuted | inconclusive | false alarm | flagged (identity) | flagged (old) | refuted only by eb_catalog |
|---|---|---|---|---|---|---|---|
| false_positive|below|correlated|blend|independent | 5 | 4 | 1 | 0 | 3 | 4 | 0 |
| false_positive|below|correlated|blend|neighbor | 5 | 5 | 0 | 0 | 5 | 5 | 0 |
| false_positive|below|correlated|blend|own | 15 | 13 | 2 | 0 | 13 | 13 | 0 |
| false_positive|below|correlated|eb_odd_even|independent | 5 | 5 | 0 | 0 | 0 | 1 | 4 |
| false_positive|below|correlated|eb_odd_even|neighbor | 5 | 5 | 0 | 0 | 1 | 1 | 4 |
| false_positive|below|correlated|eb_odd_even|own | 15 | 14 | 1 | 0 | 2 | 4 | 10 |
| false_positive|below|correlated|eb_secondary|independent | 5 | 5 | 0 | 0 | 2 | 2 | 3 |
| false_positive|below|correlated|eb_secondary|neighbor | 5 | 5 | 0 | 0 | 2 | 2 | 3 |
| false_positive|below|correlated|eb_secondary|own | 15 | 15 | 0 | 0 | 4 | 4 | 11 |
| false_positive|below|correlated|variability_masked|independent | 5 | 5 | 0 | 0 | 0 | 5 | 0 |
| false_positive|below|correlated|variability_masked|neighbor | 5 | 4 | 0 | 1 | 0 | 4 | 0 |
| false_positive|below|correlated|variability_masked|own | 15 | 14 | 0 | 1 | 0 | 14 | 0 |
| false_positive|below|white|blend|independent | 5 | 4 | 1 | 0 | 3 | 4 | 0 |
| false_positive|below|white|blend|neighbor | 5 | 3 | 2 | 0 | 3 | 3 | 0 |
| false_positive|below|white|blend|own | 15 | 11 | 4 | 0 | 10 | 11 | 0 |
| false_positive|below|white|eb_odd_even|independent | 5 | 5 | 0 | 0 | 1 | 1 | 4 |
| false_positive|below|white|eb_odd_even|neighbor | 5 | 4 | 1 | 0 | 1 | 1 | 3 |
| false_positive|below|white|eb_odd_even|own | 15 | 13 | 2 | 0 | 4 | 4 | 9 |
| false_positive|below|white|eb_secondary|independent | 5 | 4 | 1 | 0 | 0 | 0 | 4 |
| false_positive|below|white|eb_secondary|neighbor | 5 | 5 | 0 | 0 | 3 | 3 | 2 |
| false_positive|below|white|eb_secondary|own | 15 | 12 | 3 | 0 | 3 | 5 | 7 |
| false_positive|below|white|variability_masked|independent | 5 | 5 | 0 | 0 | 0 | 5 | 0 |
| false_positive|below|white|variability_masked|neighbor | 5 | 5 | 0 | 0 | 0 | 5 | 0 |
| false_positive|below|white|variability_masked|own | 15 | 15 | 0 | 0 | 0 | 15 | 0 |
| false_positive|measurable|correlated|blend|independent | 12 | 12 | 0 | 0 | 12 | 12 | 0 |
| false_positive|measurable|correlated|blend|neighbor | 12 | 12 | 0 | 0 | 12 | 12 | 0 |
| false_positive|measurable|correlated|blend|own | 38 | 38 | 0 | 0 | 38 | 38 | 0 |
| false_positive|measurable|correlated|eb_odd_even|independent | 13 | 13 | 0 | 0 | 11 | 11 | 2 |
| false_positive|measurable|correlated|eb_odd_even|neighbor | 13 | 13 | 0 | 0 | 9 | 9 | 4 |
| false_positive|measurable|correlated|eb_odd_even|own | 37 | 37 | 0 | 0 | 31 | 31 | 6 |
| false_positive|measurable|correlated|eb_secondary|independent | 12 | 12 | 0 | 0 | 12 | 12 | 0 |
| false_positive|measurable|correlated|eb_secondary|neighbor | 12 | 12 | 0 | 0 | 12 | 12 | 0 |
| false_positive|measurable|correlated|eb_secondary|own | 39 | 39 | 0 | 0 | 39 | 39 | 0 |
| false_positive|measurable|correlated|variability_masked|independent | 13 | 11 | 2 | 0 | 0 | 11 | 0 |
| false_positive|measurable|correlated|variability_masked|neighbor | 13 | 11 | 1 | 1 | 0 | 11 | 0 |
| false_positive|measurable|correlated|variability_masked|own | 36 | 27 | 5 | 4 | 0 | 27 | 0 |
| false_positive|measurable|white|blend|independent | 12 | 12 | 0 | 0 | 11 | 12 | 0 |
| false_positive|measurable|white|blend|neighbor | 12 | 12 | 0 | 0 | 12 | 12 | 0 |
| false_positive|measurable|white|blend|own | 38 | 38 | 0 | 0 | 38 | 38 | 0 |
| false_positive|measurable|white|eb_odd_even|independent | 13 | 13 | 0 | 0 | 9 | 9 | 4 |
| false_positive|measurable|white|eb_odd_even|neighbor | 13 | 13 | 0 | 0 | 9 | 9 | 4 |
| false_positive|measurable|white|eb_odd_even|own | 37 | 37 | 0 | 0 | 24 | 24 | 13 |
| false_positive|measurable|white|eb_secondary|independent | 12 | 12 | 0 | 0 | 10 | 10 | 2 |
| false_positive|measurable|white|eb_secondary|neighbor | 12 | 12 | 0 | 0 | 12 | 12 | 0 |
| false_positive|measurable|white|eb_secondary|own | 39 | 39 | 0 | 0 | 36 | 36 | 3 |
| false_positive|measurable|white|variability_masked|independent | 13 | 12 | 0 | 1 | 0 | 12 | 0 |
| false_positive|measurable|white|variability_masked|neighbor | 13 | 13 | 0 | 0 | 0 | 13 | 0 |
| false_positive|measurable|white|variability_masked|own | 36 | 35 | 0 | 1 | 0 | 35 | 0 |
| false_positive|near|correlated|blend|independent | 5 | 5 | 0 | 0 | 5 | 5 | 0 |
| false_positive|near|correlated|blend|neighbor | 5 | 5 | 0 | 0 | 5 | 5 | 0 |
| false_positive|near|correlated|blend|own | 15 | 15 | 0 | 0 | 15 | 15 | 0 |
| false_positive|near|correlated|eb_odd_even|independent | 5 | 5 | 0 | 0 | 1 | 1 | 4 |
| false_positive|near|correlated|eb_odd_even|neighbor | 5 | 5 | 0 | 0 | 0 | 0 | 5 |
| false_positive|near|correlated|eb_odd_even|own | 15 | 15 | 0 | 0 | 6 | 6 | 9 |
| false_positive|near|correlated|eb_secondary|independent | 5 | 5 | 0 | 0 | 4 | 4 | 1 |
| false_positive|near|correlated|eb_secondary|neighbor | 5 | 5 | 0 | 0 | 1 | 1 | 4 |
| false_positive|near|correlated|eb_secondary|own | 15 | 15 | 0 | 0 | 13 | 13 | 2 |
| false_positive|near|correlated|variability_masked|independent | 5 | 5 | 0 | 0 | 0 | 5 | 0 |
| false_positive|near|correlated|variability_masked|neighbor | 5 | 5 | 0 | 0 | 0 | 5 | 0 |
| false_positive|near|correlated|variability_masked|own | 15 | 13 | 2 | 0 | 0 | 13 | 0 |
| false_positive|near|white|blend|independent | 5 | 5 | 0 | 0 | 5 | 5 | 0 |
| false_positive|near|white|blend|neighbor | 5 | 5 | 0 | 0 | 5 | 5 | 0 |
| false_positive|near|white|blend|own | 15 | 15 | 0 | 0 | 15 | 15 | 0 |
| false_positive|near|white|eb_odd_even|independent | 5 | 5 | 0 | 0 | 1 | 1 | 4 |
| false_positive|near|white|eb_odd_even|neighbor | 5 | 5 | 0 | 0 | 2 | 2 | 3 |
| false_positive|near|white|eb_odd_even|own | 15 | 15 | 0 | 0 | 2 | 2 | 13 |
| false_positive|near|white|eb_secondary|independent | 5 | 5 | 0 | 0 | 4 | 4 | 1 |
| false_positive|near|white|eb_secondary|neighbor | 5 | 5 | 0 | 0 | 1 | 1 | 4 |
| false_positive|near|white|eb_secondary|own | 15 | 15 | 0 | 0 | 10 | 10 | 5 |
| false_positive|near|white|variability_masked|independent | 5 | 5 | 0 | 0 | 0 | 5 | 0 |
| false_positive|near|white|variability_masked|neighbor | 5 | 5 | 0 | 0 | 0 | 5 | 0 |
| false_positive|near|white|variability_masked|own | 15 | 15 | 0 | 0 | 0 | 15 | 0 |
| planet|below|correlated|few_train|independent | 10 | 10 | 0 | 0 | 1 | 1 | 9 |
| planet|below|correlated|few_train|neighbor | 10 | 10 | 0 | 0 | 1 | 1 | 9 |
| planet|below|correlated|few_train|own | 30 | 29 | 1 | 0 | 1 | 2 | 27 |
| planet|below|correlated|three_years|independent | 10 | 10 | 0 | 0 | 5 | 10 | 0 |
| planet|below|correlated|three_years|neighbor | 10 | 9 | 1 | 0 | 5 | 9 | 0 |
| planet|below|correlated|three_years|own | 30 | 30 | 0 | 0 | 16 | 29 | 1 |
| planet|below|correlated|two_years|independent | 20 | 16 | 4 | 0 | 1 | 2 | 14 |
| planet|below|correlated|two_years|neighbor | 20 | 19 | 1 | 0 | 0 | 3 | 16 |
| planet|below|correlated|two_years|own | 60 | 55 | 5 | 0 | 2 | 10 | 45 |
| planet|below|correlated|variability_some_years|independent | 10 | 10 | 0 | 0 | 1 | 10 | 0 |
| planet|below|correlated|variability_some_years|neighbor | 10 | 10 | 0 | 0 | 0 | 10 | 0 |
| planet|below|correlated|variability_some_years|own | 30 | 30 | 0 | 0 | 0 | 30 | 0 |
| planet|below|white|few_train|independent | 10 | 9 | 1 | 0 | 5 | 5 | 4 |
| planet|below|white|few_train|neighbor | 10 | 5 | 5 | 0 | 3 | 5 | 0 |
| planet|below|white|few_train|own | 30 | 26 | 4 | 0 | 14 | 16 | 10 |
| planet|below|white|three_years|independent | 10 | 3 | 7 | 0 | 2 | 3 | 0 |
| planet|below|white|three_years|neighbor | 10 | 3 | 7 | 0 | 3 | 3 | 0 |
| planet|below|white|three_years|own | 30 | 11 | 19 | 0 | 7 | 11 | 0 |
| planet|below|white|two_years|independent | 20 | 10 | 10 | 0 | 3 | 3 | 7 |
| planet|below|white|two_years|neighbor | 20 | 11 | 9 | 0 | 5 | 5 | 6 |
| planet|below|white|two_years|own | 60 | 42 | 18 | 0 | 17 | 20 | 22 |
| planet|below|white|variability_some_years|independent | 10 | 10 | 0 | 0 | 0 | 10 | 0 |
| planet|below|white|variability_some_years|neighbor | 10 | 10 | 0 | 0 | 0 | 10 | 0 |
| planet|below|white|variability_some_years|own | 30 | 30 | 0 | 0 | 0 | 30 | 0 |
| planet|measurable|correlated|few_train|independent | 10 | 10 | 0 | 0 | 1 | 1 | 9 |
| planet|measurable|correlated|few_train|neighbor | 10 | 10 | 0 | 0 | 0 | 0 | 10 |
| planet|measurable|correlated|few_train|own | 30 | 30 | 0 | 0 | 2 | 2 | 28 |
| planet|measurable|correlated|three_years|independent | 10 | 10 | 0 | 0 | 0 | 0 | 10 |
| planet|measurable|correlated|three_years|neighbor | 10 | 10 | 0 | 0 | 0 | 0 | 10 |
| planet|measurable|correlated|three_years|own | 30 | 30 | 0 | 0 | 2 | 2 | 28 |
| planet|measurable|correlated|two_years|independent | 20 | 20 | 0 | 0 | 1 | 1 | 19 |
| planet|measurable|correlated|two_years|neighbor | 20 | 20 | 0 | 0 | 0 | 0 | 20 |
| planet|measurable|correlated|two_years|own | 60 | 60 | 0 | 0 | 0 | 0 | 60 |
| planet|measurable|correlated|variability_some_years|independent | 10 | 10 | 0 | 0 | 10 | 10 | 0 |
| planet|measurable|correlated|variability_some_years|neighbor | 10 | 10 | 0 | 0 | 9 | 10 | 0 |
| planet|measurable|correlated|variability_some_years|own | 30 | 30 | 0 | 0 | 26 | 30 | 0 |
| planet|measurable|white|few_train|independent | 10 | 10 | 0 | 0 | 1 | 1 | 9 |
| planet|measurable|white|few_train|neighbor | 10 | 10 | 0 | 0 | 0 | 0 | 10 |
| planet|measurable|white|few_train|own | 30 | 30 | 0 | 0 | 2 | 2 | 28 |
| planet|measurable|white|three_years|independent | 10 | 10 | 0 | 0 | 0 | 0 | 10 |
| planet|measurable|white|three_years|neighbor | 10 | 10 | 0 | 0 | 1 | 1 | 9 |
| planet|measurable|white|three_years|own | 30 | 30 | 0 | 0 | 3 | 3 | 27 |
| planet|measurable|white|two_years|independent | 20 | 20 | 0 | 0 | 0 | 0 | 20 |
| planet|measurable|white|two_years|neighbor | 20 | 20 | 0 | 0 | 1 | 1 | 19 |
| planet|measurable|white|two_years|own | 60 | 60 | 0 | 0 | 5 | 5 | 55 |
| planet|measurable|white|variability_some_years|independent | 10 | 10 | 0 | 0 | 3 | 10 | 0 |
| planet|measurable|white|variability_some_years|neighbor | 10 | 10 | 0 | 0 | 5 | 10 | 0 |
| planet|measurable|white|variability_some_years|own | 30 | 30 | 0 | 0 | 3 | 30 | 0 |
| planet|near|correlated|few_train|independent | 10 | 10 | 0 | 0 | 1 | 1 | 9 |
| planet|near|correlated|few_train|neighbor | 10 | 10 | 0 | 0 | 1 | 1 | 9 |
| planet|near|correlated|few_train|own | 30 | 30 | 0 | 0 | 4 | 4 | 26 |
| planet|near|correlated|three_years|independent | 10 | 10 | 0 | 0 | 4 | 4 | 6 |
| planet|near|correlated|three_years|neighbor | 10 | 10 | 0 | 0 | 8 | 8 | 2 |
| planet|near|correlated|three_years|own | 30 | 30 | 0 | 0 | 20 | 20 | 10 |
| planet|near|correlated|two_years|independent | 20 | 20 | 0 | 0 | 1 | 1 | 19 |
| planet|near|correlated|two_years|neighbor | 20 | 20 | 0 | 0 | 0 | 0 | 20 |
| planet|near|correlated|two_years|own | 60 | 60 | 0 | 0 | 3 | 3 | 57 |
| planet|near|correlated|variability_some_years|independent | 10 | 10 | 0 | 0 | 4 | 10 | 0 |
| planet|near|correlated|variability_some_years|neighbor | 10 | 10 | 0 | 0 | 0 | 10 | 0 |
| planet|near|correlated|variability_some_years|own | 30 | 30 | 0 | 0 | 11 | 30 | 0 |
| planet|near|white|few_train|independent | 10 | 10 | 0 | 0 | 5 | 5 | 5 |
| planet|near|white|few_train|neighbor | 10 | 10 | 0 | 0 | 0 | 0 | 10 |
| planet|near|white|few_train|own | 30 | 30 | 0 | 0 | 8 | 8 | 22 |
| planet|near|white|three_years|independent | 10 | 10 | 0 | 0 | 6 | 6 | 4 |
| planet|near|white|three_years|neighbor | 10 | 10 | 0 | 0 | 10 | 10 | 0 |
| planet|near|white|three_years|own | 30 | 29 | 1 | 0 | 21 | 22 | 7 |
| planet|near|white|two_years|independent | 20 | 20 | 0 | 0 | 2 | 2 | 18 |
| planet|near|white|two_years|neighbor | 20 | 20 | 0 | 0 | 6 | 6 | 14 |
| planet|near|white|two_years|own | 60 | 60 | 0 | 0 | 16 | 17 | 43 |
| planet|near|white|variability_some_years|independent | 10 | 10 | 0 | 0 | 0 | 10 | 0 |
| planet|near|white|variability_some_years|neighbor | 10 | 10 | 0 | 0 | 0 | 10 | 0 |
| planet|near|white|variability_some_years|own | 30 | 30 | 0 | 0 | 0 | 30 | 0 |

## M2

**Overall approval: FAILS.** The study is approved only if every criterion passes, C6 included. A rate can meet its limit while the study fails. Failed: C1 refuted planets, below, white, C1 refuted planets, near, white, C1 refuted planets, measurable, white, C2 flagged false positives, measurable, white, C3 INCONCLUSIVE, planet, measurable, white, C5 planets refuted only by own-TIC eb_catalog, white, C1 refuted planets, below, correlated, C1 refuted planets, near, correlated, C1 refuted planets, measurable, correlated, C5 planets refuted only by own-TIC eb_catalog, correlated.

Statuses (per condition): {'analyzed': 7600}

| Criterion | k | n | rate | bound | passes |
|---|---|---|---|---|---|
| C1 refuted planets, below, white | 114 | 250 | 0.4560 | 0.5100 | False |
| C1 refuted planets, near, white | 117 | 250 | 0.4680 | 0.5220 | False |
| C1 refuted planets, measurable, white | 58 | 250 | 0.2320 | 0.2802 | False |
| C2 flagged false positives, measurable, white | 161 | 250 | 0.6440 | 0.5911 | False |
| C3 INCONCLUSIVE, planet, measurable, white | 61 | 250 | 0.2440 | 0.2928 | False |
| C3 INCONCLUSIVE, false_positive, measurable, white | 28 | 250 | 0.1120 | 0.1503 | True |
| C4 false alarm, white | 0 | 2200 | 0.0000 | 0.0014 | True |
| C5 planets refuted only by own-TIC eb_catalog, white | 222 | 450 | - | - | False |
| C1 refuted planets, below, correlated | 106 | 250 | 0.4240 | 0.4779 | False |
| C1 refuted planets, near, correlated | 91 | 250 | 0.3640 | 0.4171 | False |
| C1 refuted planets, measurable, correlated | 44 | 250 | 0.1760 | 0.2204 | False |
| C2 flagged false positives, measurable, correlated | 176 | 250 | 0.7040 | 0.6529 | True |
| C3 INCONCLUSIVE, planet, measurable, correlated | 4 | 250 | 0.0160 | 0.0362 | True |
| C3 INCONCLUSIVE, false_positive, measurable, correlated | 21 | 250 | 0.0840 | 0.1187 | True |
| C4 false alarm, correlated | 0 | 600 | 0.0000 | 0.0050 | True |
| C5 planets refuted only by own-TIC eb_catalog, correlated | 292 | 450 | - | - | False |
| C6 analysis errors, missing results and integrity errors | 0 | - | - | - | True |

Families whose point estimate is worse than their limit:

| Condition | Family | Criterion | k / n | estimate | limit |
|---|---|---|---|---|---|
| i | false_positive|measurable|correlated|variability_masked | C2 (flagged_identity) | 0 / 62 | 0.0000 | 0.6 |
| i | false_positive|measurable|correlated|variability_masked | C3 (inconclusive) | 13 / 62 | 0.2097 | 0.2 |
| i | false_positive|measurable|white|eb_odd_even | C3 (inconclusive) | 21 / 63 | 0.3333 | 0.2 |
| i | false_positive|measurable|white|variability_masked | C2 (flagged_identity) | 0 / 62 | 0.0000 | 0.6 |
| i | planet|below|correlated|two_years | C1 (refuted) | 15 / 100 | 0.1500 | 0.1 |
| i | planet|below|correlated|three_years | C1 (refuted) | 43 / 50 | 0.8600 | 0.1 |
| i | planet|below|correlated|variability_some_years | C1 (refuted) | 44 / 50 | 0.8800 | 0.1 |
| i | planet|below|white|two_years | C1 (refuted) | 28 / 100 | 0.2800 | 0.1 |
| i | planet|below|white|three_years | C1 (refuted) | 12 / 50 | 0.2400 | 0.1 |
| i | planet|below|white|few_train | C1 (refuted) | 24 / 50 | 0.4800 | 0.1 |
| i | planet|below|white|variability_some_years | C1 (refuted) | 50 / 50 | 1.0000 | 0.1 |
| i | planet|measurable|correlated|variability_some_years | C1 (refuted) | 38 / 50 | 0.7600 | 0.1 |
| i | planet|measurable|white|two_years | C3 (inconclusive) | 42 / 100 | 0.4200 | 0.2 |
| i | planet|measurable|white|few_train | C3 (inconclusive) | 15 / 50 | 0.3000 | 0.2 |
| i | planet|measurable|white|variability_some_years | C1 (refuted) | 45 / 50 | 0.9000 | 0.1 |
| i | planet|near|correlated|three_years | C1 (refuted) | 32 / 50 | 0.6400 | 0.1 |
| i | planet|near|correlated|few_train | C1 (refuted) | 6 / 50 | 0.1200 | 0.1 |
| i | planet|near|correlated|variability_some_years | C1 (refuted) | 49 / 50 | 0.9800 | 0.1 |
| i | planet|near|white|two_years | C1 (refuted) | 24 / 100 | 0.2400 | 0.1 |
| i | planet|near|white|three_years | C1 (refuted) | 33 / 50 | 0.6600 | 0.1 |
| i | planet|near|white|few_train | C1 (refuted) | 11 / 50 | 0.2200 | 0.1 |
| i | planet|near|white|variability_some_years | C1 (refuted) | 49 / 50 | 0.9800 | 0.1 |
| ii | planet|below|correlated|two_years|own | C5 (refuted_only_by_eb_catalog) | 45 / 60 | 0.7500 | 0.0 |
| ii | planet|below|correlated|three_years|own | C5 (refuted_only_by_eb_catalog) | 3 / 30 | 0.1000 | 0.0 |
| ii | planet|below|correlated|few_train|own | C5 (refuted_only_by_eb_catalog) | 27 / 30 | 0.9000 | 0.0 |
| ii | planet|below|white|two_years|own | C5 (refuted_only_by_eb_catalog) | 22 / 60 | 0.3667 | 0.0 |
| ii | planet|below|white|three_years|own | C5 (refuted_only_by_eb_catalog) | 2 / 30 | 0.0667 | 0.0 |
| ii | planet|below|white|few_train|own | C5 (refuted_only_by_eb_catalog) | 10 / 30 | 0.3333 | 0.0 |
| ii | planet|measurable|correlated|two_years|own | C5 (refuted_only_by_eb_catalog) | 60 / 60 | 1.0000 | 0.0 |
| ii | planet|measurable|correlated|three_years|own | C5 (refuted_only_by_eb_catalog) | 28 / 30 | 0.9333 | 0.0 |
| ii | planet|measurable|correlated|few_train|own | C5 (refuted_only_by_eb_catalog) | 28 / 30 | 0.9333 | 0.0 |
| ii | planet|measurable|correlated|variability_some_years|own | C5 (refuted_only_by_eb_catalog) | 8 / 30 | 0.2667 | 0.0 |
| ii | planet|measurable|white|two_years|own | C5 (refuted_only_by_eb_catalog) | 55 / 60 | 0.9167 | 0.0 |
| ii | planet|measurable|white|three_years|own | C5 (refuted_only_by_eb_catalog) | 27 / 30 | 0.9000 | 0.0 |
| ii | planet|measurable|white|few_train|own | C5 (refuted_only_by_eb_catalog) | 28 / 30 | 0.9333 | 0.0 |
| ii | planet|near|correlated|two_years|own | C5 (refuted_only_by_eb_catalog) | 57 / 60 | 0.9500 | 0.0 |
| ii | planet|near|correlated|three_years|own | C5 (refuted_only_by_eb_catalog) | 10 / 30 | 0.3333 | 0.0 |
| ii | planet|near|correlated|few_train|own | C5 (refuted_only_by_eb_catalog) | 26 / 30 | 0.8667 | 0.0 |
| ii | planet|near|white|two_years|own | C5 (refuted_only_by_eb_catalog) | 44 / 60 | 0.7333 | 0.0 |
| ii | planet|near|white|three_years|own | C5 (refuted_only_by_eb_catalog) | 11 / 30 | 0.3667 | 0.0 |
| ii | planet|near|white|few_train|own | C5 (refuted_only_by_eb_catalog) | 23 / 30 | 0.7667 | 0.0 |

Results by mechanism, condition (i):

| Family | n | refuted | inconclusive | false alarm | flagged (identity) | flagged (old) | refuted only by eb_catalog |
|---|---|---|---|---|---|---|---|
| false_positive|below|correlated|blend | 25 | 22 | 3 | 0 | 21 | 22 | 0 |
| false_positive|below|correlated|eb_odd_even | 25 | 6 | 19 | 0 | 3 | 6 | 0 |
| false_positive|below|correlated|eb_secondary | 25 | 8 | 17 | 0 | 8 | 8 | 0 |
| false_positive|below|correlated|variability_masked | 25 | 23 | 2 | 0 | 0 | 23 | 0 |
| false_positive|below|white|blend | 25 | 18 | 7 | 0 | 16 | 18 | 0 |
| false_positive|below|white|eb_odd_even | 25 | 6 | 19 | 0 | 6 | 6 | 0 |
| false_positive|below|white|eb_secondary | 25 | 8 | 17 | 0 | 6 | 8 | 0 |
| false_positive|below|white|variability_masked | 25 | 25 | 0 | 0 | 0 | 25 | 0 |
| false_positive|measurable|correlated|blend | 62 | 62 | 0 | 0 | 62 | 62 | 0 |
| false_positive|measurable|correlated|eb_odd_even | 63 | 51 | 8 | 4 | 51 | 51 | 0 |
| false_positive|measurable|correlated|eb_secondary | 63 | 63 | 0 | 0 | 63 | 63 | 0 |
| false_positive|measurable|correlated|variability_masked | 62 | 49 | 13 | 0 | 0 | 49 | 0 |
| false_positive|measurable|white|blend | 62 | 62 | 0 | 0 | 61 | 62 | 0 |
| false_positive|measurable|white|eb_odd_even | 63 | 42 | 21 | 0 | 42 | 42 | 0 |
| false_positive|measurable|white|eb_secondary | 63 | 58 | 5 | 0 | 58 | 58 | 0 |
| false_positive|measurable|white|variability_masked | 62 | 60 | 2 | 0 | 0 | 60 | 0 |
| false_positive|near|correlated|blend | 25 | 25 | 0 | 0 | 25 | 25 | 0 |
| false_positive|near|correlated|eb_odd_even | 25 | 7 | 18 | 0 | 7 | 7 | 0 |
| false_positive|near|correlated|eb_secondary | 25 | 18 | 6 | 1 | 18 | 18 | 0 |
| false_positive|near|correlated|variability_masked | 25 | 23 | 2 | 0 | 0 | 23 | 0 |
| false_positive|near|white|blend | 25 | 25 | 0 | 0 | 25 | 25 | 0 |
| false_positive|near|white|eb_odd_even | 25 | 5 | 19 | 1 | 5 | 5 | 0 |
| false_positive|near|white|eb_secondary | 25 | 15 | 10 | 0 | 15 | 15 | 0 |
| false_positive|near|white|variability_masked | 25 | 25 | 0 | 0 | 0 | 25 | 0 |
| no_transit|None|correlated|pure_noise | 240 | 108 | 132 | 0 | 0 | 108 | 0 |
| no_transit|None|correlated|trend | 180 | 69 | 111 | 0 | 0 | 69 | 0 |
| no_transit|None|correlated|trend_variability | 180 | 95 | 85 | 0 | 0 | 95 | 0 |
| no_transit|None|white|pure_noise | 880 | 43 | 837 | 0 | 0 | 43 | 0 |
| no_transit|None|white|trend | 660 | 54 | 606 | 0 | 0 | 54 | 0 |
| no_transit|None|white|trend_variability | 660 | 290 | 370 | 0 | 0 | 290 | 0 |
| planet|below|correlated|few_train | 50 | 4 | 31 | 15 | 3 | 4 | 0 |
| planet|below|correlated|three_years | 50 | 43 | 4 | 3 | 23 | 43 | 0 |
| planet|below|correlated|two_years | 100 | 15 | 81 | 4 | 3 | 15 | 0 |
| planet|below|correlated|variability_some_years | 50 | 44 | 6 | 0 | 1 | 44 | 0 |
| planet|below|white|few_train | 50 | 24 | 26 | 0 | 20 | 24 | 0 |
| planet|below|white|three_years | 50 | 12 | 38 | 0 | 7 | 12 | 0 |
| planet|below|white|two_years | 100 | 28 | 72 | 0 | 25 | 28 | 0 |
| planet|below|white|variability_some_years | 50 | 50 | 0 | 0 | 0 | 50 | 0 |
| planet|measurable|correlated|few_train | 50 | 3 | 1 | 46 | 3 | 3 | 0 |
| planet|measurable|correlated|three_years | 50 | 2 | 0 | 48 | 2 | 2 | 0 |
| planet|measurable|correlated|two_years | 100 | 1 | 3 | 96 | 1 | 1 | 0 |
| planet|measurable|correlated|variability_some_years | 50 | 38 | 0 | 12 | 33 | 38 | 0 |
| planet|measurable|white|few_train | 50 | 3 | 15 | 32 | 3 | 3 | 0 |
| planet|measurable|white|three_years | 50 | 4 | 0 | 46 | 4 | 4 | 0 |
| planet|measurable|white|two_years | 100 | 6 | 42 | 52 | 6 | 6 | 0 |
| planet|measurable|white|variability_some_years | 50 | 45 | 4 | 1 | 10 | 45 | 0 |
| planet|near|correlated|few_train | 50 | 6 | 10 | 34 | 6 | 6 | 0 |
| planet|near|correlated|three_years | 50 | 32 | 0 | 18 | 32 | 32 | 0 |
| planet|near|correlated|two_years | 100 | 4 | 57 | 39 | 4 | 4 | 0 |
| planet|near|correlated|variability_some_years | 50 | 49 | 1 | 0 | 15 | 49 | 0 |
| planet|near|white|few_train | 50 | 11 | 34 | 5 | 11 | 11 | 0 |
| planet|near|white|three_years | 50 | 33 | 6 | 11 | 32 | 33 | 0 |
| planet|near|white|two_years | 100 | 24 | 75 | 1 | 23 | 24 | 0 |
| planet|near|white|variability_some_years | 50 | 49 | 1 | 0 | 0 | 49 | 0 |

Results by mechanism, condition (ii):

| Family | n | refuted | inconclusive | false alarm | flagged (identity) | flagged (old) | refuted only by eb_catalog |
|---|---|---|---|---|---|---|---|
| false_positive|below|correlated|blend|independent | 5 | 4 | 1 | 0 | 3 | 4 | 0 |
| false_positive|below|correlated|blend|neighbor | 5 | 5 | 0 | 0 | 5 | 5 | 0 |
| false_positive|below|correlated|blend|own | 15 | 13 | 2 | 0 | 13 | 13 | 0 |
| false_positive|below|correlated|eb_odd_even|independent | 5 | 5 | 0 | 0 | 0 | 1 | 4 |
| false_positive|below|correlated|eb_odd_even|neighbor | 5 | 5 | 0 | 0 | 1 | 1 | 4 |
| false_positive|below|correlated|eb_odd_even|own | 15 | 14 | 1 | 0 | 2 | 4 | 10 |
| false_positive|below|correlated|eb_secondary|independent | 5 | 5 | 0 | 0 | 2 | 2 | 3 |
| false_positive|below|correlated|eb_secondary|neighbor | 5 | 5 | 0 | 0 | 2 | 2 | 3 |
| false_positive|below|correlated|eb_secondary|own | 15 | 15 | 0 | 0 | 4 | 4 | 11 |
| false_positive|below|correlated|variability_masked|independent | 5 | 5 | 0 | 0 | 0 | 5 | 0 |
| false_positive|below|correlated|variability_masked|neighbor | 5 | 4 | 1 | 0 | 0 | 4 | 0 |
| false_positive|below|correlated|variability_masked|own | 15 | 14 | 1 | 0 | 0 | 14 | 0 |
| false_positive|below|white|blend|independent | 5 | 4 | 1 | 0 | 3 | 4 | 0 |
| false_positive|below|white|blend|neighbor | 5 | 3 | 2 | 0 | 3 | 3 | 0 |
| false_positive|below|white|blend|own | 15 | 11 | 4 | 0 | 10 | 11 | 0 |
| false_positive|below|white|eb_odd_even|independent | 5 | 5 | 0 | 0 | 1 | 1 | 4 |
| false_positive|below|white|eb_odd_even|neighbor | 5 | 4 | 1 | 0 | 1 | 1 | 3 |
| false_positive|below|white|eb_odd_even|own | 15 | 13 | 2 | 0 | 4 | 4 | 9 |
| false_positive|below|white|eb_secondary|independent | 5 | 4 | 1 | 0 | 0 | 0 | 4 |
| false_positive|below|white|eb_secondary|neighbor | 5 | 5 | 0 | 0 | 3 | 3 | 2 |
| false_positive|below|white|eb_secondary|own | 15 | 12 | 3 | 0 | 3 | 5 | 7 |
| false_positive|below|white|variability_masked|independent | 5 | 5 | 0 | 0 | 0 | 5 | 0 |
| false_positive|below|white|variability_masked|neighbor | 5 | 5 | 0 | 0 | 0 | 5 | 0 |
| false_positive|below|white|variability_masked|own | 15 | 15 | 0 | 0 | 0 | 15 | 0 |
| false_positive|measurable|correlated|blend|independent | 12 | 12 | 0 | 0 | 12 | 12 | 0 |
| false_positive|measurable|correlated|blend|neighbor | 12 | 12 | 0 | 0 | 12 | 12 | 0 |
| false_positive|measurable|correlated|blend|own | 38 | 38 | 0 | 0 | 38 | 38 | 0 |
| false_positive|measurable|correlated|eb_odd_even|independent | 13 | 13 | 0 | 0 | 11 | 11 | 2 |
| false_positive|measurable|correlated|eb_odd_even|neighbor | 13 | 13 | 0 | 0 | 9 | 9 | 4 |
| false_positive|measurable|correlated|eb_odd_even|own | 37 | 37 | 0 | 0 | 31 | 31 | 6 |
| false_positive|measurable|correlated|eb_secondary|independent | 12 | 12 | 0 | 0 | 12 | 12 | 0 |
| false_positive|measurable|correlated|eb_secondary|neighbor | 12 | 12 | 0 | 0 | 12 | 12 | 0 |
| false_positive|measurable|correlated|eb_secondary|own | 39 | 39 | 0 | 0 | 39 | 39 | 0 |
| false_positive|measurable|correlated|variability_masked|independent | 13 | 11 | 2 | 0 | 0 | 11 | 0 |
| false_positive|measurable|correlated|variability_masked|neighbor | 13 | 11 | 2 | 0 | 0 | 11 | 0 |
| false_positive|measurable|correlated|variability_masked|own | 36 | 27 | 9 | 0 | 0 | 27 | 0 |
| false_positive|measurable|white|blend|independent | 12 | 12 | 0 | 0 | 11 | 12 | 0 |
| false_positive|measurable|white|blend|neighbor | 12 | 12 | 0 | 0 | 12 | 12 | 0 |
| false_positive|measurable|white|blend|own | 38 | 38 | 0 | 0 | 38 | 38 | 0 |
| false_positive|measurable|white|eb_odd_even|independent | 13 | 13 | 0 | 0 | 9 | 9 | 4 |
| false_positive|measurable|white|eb_odd_even|neighbor | 13 | 13 | 0 | 0 | 9 | 9 | 4 |
| false_positive|measurable|white|eb_odd_even|own | 37 | 37 | 0 | 0 | 24 | 24 | 13 |
| false_positive|measurable|white|eb_secondary|independent | 12 | 12 | 0 | 0 | 10 | 10 | 2 |
| false_positive|measurable|white|eb_secondary|neighbor | 12 | 12 | 0 | 0 | 12 | 12 | 0 |
| false_positive|measurable|white|eb_secondary|own | 39 | 39 | 0 | 0 | 36 | 36 | 3 |
| false_positive|measurable|white|variability_masked|independent | 13 | 12 | 1 | 0 | 0 | 12 | 0 |
| false_positive|measurable|white|variability_masked|neighbor | 13 | 13 | 0 | 0 | 0 | 13 | 0 |
| false_positive|measurable|white|variability_masked|own | 36 | 35 | 1 | 0 | 0 | 35 | 0 |
| false_positive|near|correlated|blend|independent | 5 | 5 | 0 | 0 | 5 | 5 | 0 |
| false_positive|near|correlated|blend|neighbor | 5 | 5 | 0 | 0 | 5 | 5 | 0 |
| false_positive|near|correlated|blend|own | 15 | 15 | 0 | 0 | 15 | 15 | 0 |
| false_positive|near|correlated|eb_odd_even|independent | 5 | 5 | 0 | 0 | 1 | 1 | 4 |
| false_positive|near|correlated|eb_odd_even|neighbor | 5 | 5 | 0 | 0 | 0 | 0 | 5 |
| false_positive|near|correlated|eb_odd_even|own | 15 | 15 | 0 | 0 | 6 | 6 | 9 |
| false_positive|near|correlated|eb_secondary|independent | 5 | 5 | 0 | 0 | 4 | 4 | 1 |
| false_positive|near|correlated|eb_secondary|neighbor | 5 | 5 | 0 | 0 | 1 | 1 | 4 |
| false_positive|near|correlated|eb_secondary|own | 15 | 15 | 0 | 0 | 13 | 13 | 2 |
| false_positive|near|correlated|variability_masked|independent | 5 | 5 | 0 | 0 | 0 | 5 | 0 |
| false_positive|near|correlated|variability_masked|neighbor | 5 | 5 | 0 | 0 | 0 | 5 | 0 |
| false_positive|near|correlated|variability_masked|own | 15 | 13 | 2 | 0 | 0 | 13 | 0 |
| false_positive|near|white|blend|independent | 5 | 5 | 0 | 0 | 5 | 5 | 0 |
| false_positive|near|white|blend|neighbor | 5 | 5 | 0 | 0 | 5 | 5 | 0 |
| false_positive|near|white|blend|own | 15 | 15 | 0 | 0 | 15 | 15 | 0 |
| false_positive|near|white|eb_odd_even|independent | 5 | 5 | 0 | 0 | 1 | 1 | 4 |
| false_positive|near|white|eb_odd_even|neighbor | 5 | 5 | 0 | 0 | 2 | 2 | 3 |
| false_positive|near|white|eb_odd_even|own | 15 | 15 | 0 | 0 | 2 | 2 | 13 |
| false_positive|near|white|eb_secondary|independent | 5 | 5 | 0 | 0 | 4 | 4 | 1 |
| false_positive|near|white|eb_secondary|neighbor | 5 | 5 | 0 | 0 | 1 | 1 | 4 |
| false_positive|near|white|eb_secondary|own | 15 | 15 | 0 | 0 | 10 | 10 | 5 |
| false_positive|near|white|variability_masked|independent | 5 | 5 | 0 | 0 | 0 | 5 | 0 |
| false_positive|near|white|variability_masked|neighbor | 5 | 5 | 0 | 0 | 0 | 5 | 0 |
| false_positive|near|white|variability_masked|own | 15 | 15 | 0 | 0 | 0 | 15 | 0 |
| planet|below|correlated|few_train|independent | 10 | 10 | 0 | 0 | 1 | 1 | 9 |
| planet|below|correlated|few_train|neighbor | 10 | 10 | 0 | 0 | 1 | 1 | 9 |
| planet|below|correlated|few_train|own | 30 | 29 | 1 | 0 | 1 | 2 | 27 |
| planet|below|correlated|three_years|independent | 10 | 10 | 0 | 0 | 5 | 10 | 0 |
| planet|below|correlated|three_years|neighbor | 10 | 8 | 2 | 0 | 4 | 7 | 1 |
| planet|below|correlated|three_years|own | 30 | 29 | 1 | 0 | 14 | 26 | 3 |
| planet|below|correlated|two_years|independent | 20 | 16 | 4 | 0 | 1 | 2 | 14 |
| planet|below|correlated|two_years|neighbor | 20 | 19 | 1 | 0 | 0 | 3 | 16 |
| planet|below|correlated|two_years|own | 60 | 55 | 5 | 0 | 2 | 10 | 45 |
| planet|below|correlated|variability_some_years|independent | 10 | 10 | 0 | 0 | 1 | 10 | 0 |
| planet|below|correlated|variability_some_years|neighbor | 10 | 10 | 0 | 0 | 0 | 10 | 0 |
| planet|below|correlated|variability_some_years|own | 30 | 24 | 6 | 0 | 0 | 24 | 0 |
| planet|below|white|few_train|independent | 10 | 9 | 1 | 0 | 4 | 4 | 5 |
| planet|below|white|few_train|neighbor | 10 | 5 | 5 | 0 | 2 | 4 | 1 |
| planet|below|white|few_train|own | 30 | 26 | 4 | 0 | 14 | 16 | 10 |
| planet|below|white|three_years|independent | 10 | 3 | 7 | 0 | 0 | 1 | 2 |
| planet|below|white|three_years|neighbor | 10 | 3 | 7 | 0 | 2 | 2 | 1 |
| planet|below|white|three_years|own | 30 | 11 | 19 | 0 | 5 | 9 | 2 |
| planet|below|white|two_years|independent | 20 | 10 | 10 | 0 | 3 | 3 | 7 |
| planet|below|white|two_years|neighbor | 20 | 11 | 9 | 0 | 5 | 5 | 6 |
| planet|below|white|two_years|own | 60 | 42 | 18 | 0 | 17 | 20 | 22 |
| planet|below|white|variability_some_years|independent | 10 | 10 | 0 | 0 | 0 | 10 | 0 |
| planet|below|white|variability_some_years|neighbor | 10 | 10 | 0 | 0 | 0 | 10 | 0 |
| planet|below|white|variability_some_years|own | 30 | 30 | 0 | 0 | 0 | 30 | 0 |
| planet|measurable|correlated|few_train|independent | 10 | 10 | 0 | 0 | 1 | 1 | 9 |
| planet|measurable|correlated|few_train|neighbor | 10 | 10 | 0 | 0 | 0 | 0 | 10 |
| planet|measurable|correlated|few_train|own | 30 | 30 | 0 | 0 | 2 | 2 | 28 |
| planet|measurable|correlated|three_years|independent | 10 | 10 | 0 | 0 | 0 | 0 | 10 |
| planet|measurable|correlated|three_years|neighbor | 10 | 10 | 0 | 0 | 0 | 0 | 10 |
| planet|measurable|correlated|three_years|own | 30 | 30 | 0 | 0 | 2 | 2 | 28 |
| planet|measurable|correlated|two_years|independent | 20 | 20 | 0 | 0 | 1 | 1 | 19 |
| planet|measurable|correlated|two_years|neighbor | 20 | 20 | 0 | 0 | 0 | 0 | 20 |
| planet|measurable|correlated|two_years|own | 60 | 60 | 0 | 0 | 0 | 0 | 60 |
| planet|measurable|correlated|variability_some_years|independent | 10 | 10 | 0 | 0 | 8 | 8 | 2 |
| planet|measurable|correlated|variability_some_years|neighbor | 10 | 10 | 0 | 0 | 7 | 8 | 2 |
| planet|measurable|correlated|variability_some_years|own | 30 | 30 | 0 | 0 | 18 | 22 | 8 |
| planet|measurable|white|few_train|independent | 10 | 10 | 0 | 0 | 1 | 1 | 9 |
| planet|measurable|white|few_train|neighbor | 10 | 10 | 0 | 0 | 0 | 0 | 10 |
| planet|measurable|white|few_train|own | 30 | 30 | 0 | 0 | 2 | 2 | 28 |
| planet|measurable|white|three_years|independent | 10 | 10 | 0 | 0 | 0 | 0 | 10 |
| planet|measurable|white|three_years|neighbor | 10 | 10 | 0 | 0 | 1 | 1 | 9 |
| planet|measurable|white|three_years|own | 30 | 30 | 0 | 0 | 3 | 3 | 27 |
| planet|measurable|white|two_years|independent | 20 | 20 | 0 | 0 | 0 | 0 | 20 |
| planet|measurable|white|two_years|neighbor | 20 | 20 | 0 | 0 | 1 | 1 | 19 |
| planet|measurable|white|two_years|own | 60 | 60 | 0 | 0 | 5 | 5 | 55 |
| planet|measurable|white|variability_some_years|independent | 10 | 9 | 1 | 0 | 2 | 8 | 1 |
| planet|measurable|white|variability_some_years|neighbor | 10 | 9 | 1 | 0 | 5 | 9 | 0 |
| planet|measurable|white|variability_some_years|own | 30 | 28 | 2 | 0 | 3 | 28 | 0 |
| planet|near|correlated|few_train|independent | 10 | 10 | 0 | 0 | 1 | 1 | 9 |
| planet|near|correlated|few_train|neighbor | 10 | 10 | 0 | 0 | 1 | 1 | 9 |
| planet|near|correlated|few_train|own | 30 | 30 | 0 | 0 | 4 | 4 | 26 |
| planet|near|correlated|three_years|independent | 10 | 10 | 0 | 0 | 4 | 4 | 6 |
| planet|near|correlated|three_years|neighbor | 10 | 10 | 0 | 0 | 8 | 8 | 2 |
| planet|near|correlated|three_years|own | 30 | 30 | 0 | 0 | 20 | 20 | 10 |
| planet|near|correlated|two_years|independent | 20 | 20 | 0 | 0 | 1 | 1 | 19 |
| planet|near|correlated|two_years|neighbor | 20 | 20 | 0 | 0 | 0 | 0 | 20 |
| planet|near|correlated|two_years|own | 60 | 60 | 0 | 0 | 3 | 3 | 57 |
| planet|near|correlated|variability_some_years|independent | 10 | 10 | 0 | 0 | 4 | 10 | 0 |
| planet|near|correlated|variability_some_years|neighbor | 10 | 10 | 0 | 0 | 0 | 10 | 0 |
| planet|near|correlated|variability_some_years|own | 30 | 29 | 1 | 0 | 11 | 29 | 0 |
| planet|near|white|few_train|independent | 10 | 10 | 0 | 0 | 4 | 4 | 6 |
| planet|near|white|few_train|neighbor | 10 | 10 | 0 | 0 | 0 | 0 | 10 |
| planet|near|white|few_train|own | 30 | 30 | 0 | 0 | 7 | 7 | 23 |
| planet|near|white|three_years|independent | 10 | 10 | 0 | 0 | 5 | 5 | 5 |
| planet|near|white|three_years|neighbor | 10 | 10 | 0 | 0 | 10 | 10 | 0 |
| planet|near|white|three_years|own | 30 | 29 | 1 | 0 | 17 | 18 | 11 |
| planet|near|white|two_years|independent | 20 | 20 | 0 | 0 | 2 | 2 | 18 |
| planet|near|white|two_years|neighbor | 20 | 20 | 0 | 0 | 6 | 6 | 14 |
| planet|near|white|two_years|own | 60 | 60 | 0 | 0 | 15 | 16 | 44 |
| planet|near|white|variability_some_years|independent | 10 | 9 | 1 | 0 | 0 | 9 | 0 |
| planet|near|white|variability_some_years|neighbor | 10 | 10 | 0 | 0 | 0 | 10 | 0 |
| planet|near|white|variability_some_years|own | 30 | 30 | 0 | 0 | 0 | 30 | 0 |

## M3

**Overall approval: FAILS.** The study is approved only if every criterion passes, C6 included. A rate can meet its limit while the study fails. Failed: C1 refuted planets, below, white, C1 refuted planets, near, white, C1 refuted planets, measurable, white, C2 flagged false positives, measurable, white, C3 INCONCLUSIVE, planet, measurable, white, C1 refuted planets, below, correlated, C1 refuted planets, near, correlated, C1 refuted planets, measurable, correlated.

Statuses (per condition): {'analyzed': 7600}

| Criterion | k | n | rate | bound | passes |
|---|---|---|---|---|---|
| C1 refuted planets, below, white | 114 | 250 | 0.4560 | 0.5100 | False |
| C1 refuted planets, near, white | 117 | 250 | 0.4680 | 0.5220 | False |
| C1 refuted planets, measurable, white | 58 | 250 | 0.2320 | 0.2802 | False |
| C2 flagged false positives, measurable, white | 161 | 250 | 0.6440 | 0.5911 | False |
| C3 INCONCLUSIVE, planet, measurable, white | 61 | 250 | 0.2440 | 0.2928 | False |
| C3 INCONCLUSIVE, false_positive, measurable, white | 28 | 250 | 0.1120 | 0.1503 | True |
| C4 false alarm, white | 0 | 2200 | 0.0000 | 0.0014 | True |
| C5 planets refuted only by own-TIC eb_catalog, white | 0 | 450 | - | - | True |
| C1 refuted planets, below, correlated | 106 | 250 | 0.4240 | 0.4779 | False |
| C1 refuted planets, near, correlated | 91 | 250 | 0.3640 | 0.4171 | False |
| C1 refuted planets, measurable, correlated | 44 | 250 | 0.1760 | 0.2204 | False |
| C2 flagged false positives, measurable, correlated | 176 | 250 | 0.7040 | 0.6529 | True |
| C3 INCONCLUSIVE, planet, measurable, correlated | 4 | 250 | 0.0160 | 0.0362 | True |
| C3 INCONCLUSIVE, false_positive, measurable, correlated | 21 | 250 | 0.0840 | 0.1187 | True |
| C4 false alarm, correlated | 0 | 600 | 0.0000 | 0.0050 | True |
| C5 planets refuted only by own-TIC eb_catalog, correlated | 0 | 450 | - | - | True |
| C6 analysis errors, missing results and integrity errors | 0 | - | - | - | True |

Families whose point estimate is worse than their limit:

| Condition | Family | Criterion | k / n | estimate | limit |
|---|---|---|---|---|---|
| i | false_positive|measurable|correlated|variability_masked | C2 (flagged_identity) | 0 / 62 | 0.0000 | 0.6 |
| i | false_positive|measurable|correlated|variability_masked | C3 (inconclusive) | 13 / 62 | 0.2097 | 0.2 |
| i | false_positive|measurable|white|eb_odd_even | C3 (inconclusive) | 21 / 63 | 0.3333 | 0.2 |
| i | false_positive|measurable|white|variability_masked | C2 (flagged_identity) | 0 / 62 | 0.0000 | 0.6 |
| i | planet|below|correlated|two_years | C1 (refuted) | 15 / 100 | 0.1500 | 0.1 |
| i | planet|below|correlated|three_years | C1 (refuted) | 43 / 50 | 0.8600 | 0.1 |
| i | planet|below|correlated|variability_some_years | C1 (refuted) | 44 / 50 | 0.8800 | 0.1 |
| i | planet|below|white|two_years | C1 (refuted) | 28 / 100 | 0.2800 | 0.1 |
| i | planet|below|white|three_years | C1 (refuted) | 12 / 50 | 0.2400 | 0.1 |
| i | planet|below|white|few_train | C1 (refuted) | 24 / 50 | 0.4800 | 0.1 |
| i | planet|below|white|variability_some_years | C1 (refuted) | 50 / 50 | 1.0000 | 0.1 |
| i | planet|measurable|correlated|variability_some_years | C1 (refuted) | 38 / 50 | 0.7600 | 0.1 |
| i | planet|measurable|white|two_years | C3 (inconclusive) | 42 / 100 | 0.4200 | 0.2 |
| i | planet|measurable|white|few_train | C3 (inconclusive) | 15 / 50 | 0.3000 | 0.2 |
| i | planet|measurable|white|variability_some_years | C1 (refuted) | 45 / 50 | 0.9000 | 0.1 |
| i | planet|near|correlated|three_years | C1 (refuted) | 32 / 50 | 0.6400 | 0.1 |
| i | planet|near|correlated|few_train | C1 (refuted) | 6 / 50 | 0.1200 | 0.1 |
| i | planet|near|correlated|variability_some_years | C1 (refuted) | 49 / 50 | 0.9800 | 0.1 |
| i | planet|near|white|two_years | C1 (refuted) | 24 / 100 | 0.2400 | 0.1 |
| i | planet|near|white|three_years | C1 (refuted) | 33 / 50 | 0.6600 | 0.1 |
| i | planet|near|white|few_train | C1 (refuted) | 11 / 50 | 0.2200 | 0.1 |
| i | planet|near|white|variability_some_years | C1 (refuted) | 49 / 50 | 0.9800 | 0.1 |

Results by mechanism, condition (i):

| Family | n | refuted | inconclusive | false alarm | flagged (identity) | flagged (old) | refuted only by eb_catalog |
|---|---|---|---|---|---|---|---|
| false_positive|below|correlated|blend | 25 | 22 | 3 | 0 | 21 | 22 | 0 |
| false_positive|below|correlated|eb_odd_even | 25 | 6 | 19 | 0 | 3 | 6 | 0 |
| false_positive|below|correlated|eb_secondary | 25 | 8 | 17 | 0 | 8 | 8 | 0 |
| false_positive|below|correlated|variability_masked | 25 | 23 | 2 | 0 | 0 | 23 | 0 |
| false_positive|below|white|blend | 25 | 18 | 7 | 0 | 16 | 18 | 0 |
| false_positive|below|white|eb_odd_even | 25 | 6 | 19 | 0 | 6 | 6 | 0 |
| false_positive|below|white|eb_secondary | 25 | 8 | 17 | 0 | 6 | 8 | 0 |
| false_positive|below|white|variability_masked | 25 | 25 | 0 | 0 | 0 | 25 | 0 |
| false_positive|measurable|correlated|blend | 62 | 62 | 0 | 0 | 62 | 62 | 0 |
| false_positive|measurable|correlated|eb_odd_even | 63 | 51 | 8 | 4 | 51 | 51 | 0 |
| false_positive|measurable|correlated|eb_secondary | 63 | 63 | 0 | 0 | 63 | 63 | 0 |
| false_positive|measurable|correlated|variability_masked | 62 | 49 | 13 | 0 | 0 | 49 | 0 |
| false_positive|measurable|white|blend | 62 | 62 | 0 | 0 | 61 | 62 | 0 |
| false_positive|measurable|white|eb_odd_even | 63 | 42 | 21 | 0 | 42 | 42 | 0 |
| false_positive|measurable|white|eb_secondary | 63 | 58 | 5 | 0 | 58 | 58 | 0 |
| false_positive|measurable|white|variability_masked | 62 | 60 | 2 | 0 | 0 | 60 | 0 |
| false_positive|near|correlated|blend | 25 | 25 | 0 | 0 | 25 | 25 | 0 |
| false_positive|near|correlated|eb_odd_even | 25 | 7 | 18 | 0 | 7 | 7 | 0 |
| false_positive|near|correlated|eb_secondary | 25 | 18 | 6 | 1 | 18 | 18 | 0 |
| false_positive|near|correlated|variability_masked | 25 | 23 | 2 | 0 | 0 | 23 | 0 |
| false_positive|near|white|blend | 25 | 25 | 0 | 0 | 25 | 25 | 0 |
| false_positive|near|white|eb_odd_even | 25 | 5 | 19 | 1 | 5 | 5 | 0 |
| false_positive|near|white|eb_secondary | 25 | 15 | 10 | 0 | 15 | 15 | 0 |
| false_positive|near|white|variability_masked | 25 | 25 | 0 | 0 | 0 | 25 | 0 |
| no_transit|None|correlated|pure_noise | 240 | 108 | 132 | 0 | 0 | 108 | 0 |
| no_transit|None|correlated|trend | 180 | 69 | 111 | 0 | 0 | 69 | 0 |
| no_transit|None|correlated|trend_variability | 180 | 95 | 85 | 0 | 0 | 95 | 0 |
| no_transit|None|white|pure_noise | 880 | 43 | 837 | 0 | 0 | 43 | 0 |
| no_transit|None|white|trend | 660 | 54 | 606 | 0 | 0 | 54 | 0 |
| no_transit|None|white|trend_variability | 660 | 290 | 370 | 0 | 0 | 290 | 0 |
| planet|below|correlated|few_train | 50 | 4 | 31 | 15 | 3 | 4 | 0 |
| planet|below|correlated|three_years | 50 | 43 | 4 | 3 | 23 | 43 | 0 |
| planet|below|correlated|two_years | 100 | 15 | 81 | 4 | 3 | 15 | 0 |
| planet|below|correlated|variability_some_years | 50 | 44 | 6 | 0 | 1 | 44 | 0 |
| planet|below|white|few_train | 50 | 24 | 26 | 0 | 20 | 24 | 0 |
| planet|below|white|three_years | 50 | 12 | 38 | 0 | 7 | 12 | 0 |
| planet|below|white|two_years | 100 | 28 | 72 | 0 | 25 | 28 | 0 |
| planet|below|white|variability_some_years | 50 | 50 | 0 | 0 | 0 | 50 | 0 |
| planet|measurable|correlated|few_train | 50 | 3 | 1 | 46 | 3 | 3 | 0 |
| planet|measurable|correlated|three_years | 50 | 2 | 0 | 48 | 2 | 2 | 0 |
| planet|measurable|correlated|two_years | 100 | 1 | 3 | 96 | 1 | 1 | 0 |
| planet|measurable|correlated|variability_some_years | 50 | 38 | 0 | 12 | 33 | 38 | 0 |
| planet|measurable|white|few_train | 50 | 3 | 15 | 32 | 3 | 3 | 0 |
| planet|measurable|white|three_years | 50 | 4 | 0 | 46 | 4 | 4 | 0 |
| planet|measurable|white|two_years | 100 | 6 | 42 | 52 | 6 | 6 | 0 |
| planet|measurable|white|variability_some_years | 50 | 45 | 4 | 1 | 10 | 45 | 0 |
| planet|near|correlated|few_train | 50 | 6 | 10 | 34 | 6 | 6 | 0 |
| planet|near|correlated|three_years | 50 | 32 | 0 | 18 | 32 | 32 | 0 |
| planet|near|correlated|two_years | 100 | 4 | 57 | 39 | 4 | 4 | 0 |
| planet|near|correlated|variability_some_years | 50 | 49 | 1 | 0 | 15 | 49 | 0 |
| planet|near|white|few_train | 50 | 11 | 34 | 5 | 11 | 11 | 0 |
| planet|near|white|three_years | 50 | 33 | 6 | 11 | 32 | 33 | 0 |
| planet|near|white|two_years | 100 | 24 | 75 | 1 | 23 | 24 | 0 |
| planet|near|white|variability_some_years | 50 | 49 | 1 | 0 | 0 | 49 | 0 |

Results by mechanism, condition (ii):

| Family | n | refuted | inconclusive | false alarm | flagged (identity) | flagged (old) | refuted only by eb_catalog |
|---|---|---|---|---|---|---|---|
| false_positive|below|correlated|blend|independent | 5 | 4 | 1 | 0 | 3 | 4 | 0 |
| false_positive|below|correlated|blend|neighbor | 5 | 5 | 0 | 0 | 5 | 5 | 0 |
| false_positive|below|correlated|blend|own | 15 | 13 | 2 | 0 | 13 | 13 | 0 |
| false_positive|below|correlated|eb_odd_even|independent | 5 | 5 | 0 | 0 | 0 | 1 | 4 |
| false_positive|below|correlated|eb_odd_even|neighbor | 5 | 5 | 0 | 0 | 1 | 1 | 4 |
| false_positive|below|correlated|eb_odd_even|own | 15 | 4 | 11 | 0 | 2 | 4 | 0 |
| false_positive|below|correlated|eb_secondary|independent | 5 | 5 | 0 | 0 | 2 | 2 | 3 |
| false_positive|below|correlated|eb_secondary|neighbor | 5 | 5 | 0 | 0 | 2 | 2 | 3 |
| false_positive|below|correlated|eb_secondary|own | 15 | 4 | 11 | 0 | 4 | 4 | 0 |
| false_positive|below|correlated|variability_masked|independent | 5 | 5 | 0 | 0 | 0 | 5 | 0 |
| false_positive|below|correlated|variability_masked|neighbor | 5 | 4 | 1 | 0 | 0 | 4 | 0 |
| false_positive|below|correlated|variability_masked|own | 15 | 14 | 1 | 0 | 0 | 14 | 0 |
| false_positive|below|white|blend|independent | 5 | 4 | 1 | 0 | 3 | 4 | 0 |
| false_positive|below|white|blend|neighbor | 5 | 3 | 2 | 0 | 3 | 3 | 0 |
| false_positive|below|white|blend|own | 15 | 11 | 4 | 0 | 10 | 11 | 0 |
| false_positive|below|white|eb_odd_even|independent | 5 | 5 | 0 | 0 | 1 | 1 | 4 |
| false_positive|below|white|eb_odd_even|neighbor | 5 | 4 | 1 | 0 | 1 | 1 | 3 |
| false_positive|below|white|eb_odd_even|own | 15 | 4 | 11 | 0 | 4 | 4 | 0 |
| false_positive|below|white|eb_secondary|independent | 5 | 4 | 1 | 0 | 0 | 0 | 4 |
| false_positive|below|white|eb_secondary|neighbor | 5 | 5 | 0 | 0 | 3 | 3 | 2 |
| false_positive|below|white|eb_secondary|own | 15 | 5 | 10 | 0 | 3 | 5 | 0 |
| false_positive|below|white|variability_masked|independent | 5 | 5 | 0 | 0 | 0 | 5 | 0 |
| false_positive|below|white|variability_masked|neighbor | 5 | 5 | 0 | 0 | 0 | 5 | 0 |
| false_positive|below|white|variability_masked|own | 15 | 15 | 0 | 0 | 0 | 15 | 0 |
| false_positive|measurable|correlated|blend|independent | 12 | 12 | 0 | 0 | 12 | 12 | 0 |
| false_positive|measurable|correlated|blend|neighbor | 12 | 12 | 0 | 0 | 12 | 12 | 0 |
| false_positive|measurable|correlated|blend|own | 38 | 38 | 0 | 0 | 38 | 38 | 0 |
| false_positive|measurable|correlated|eb_odd_even|independent | 13 | 13 | 0 | 0 | 11 | 11 | 2 |
| false_positive|measurable|correlated|eb_odd_even|neighbor | 13 | 13 | 0 | 0 | 9 | 9 | 4 |
| false_positive|measurable|correlated|eb_odd_even|own | 37 | 31 | 3 | 3 | 31 | 31 | 0 |
| false_positive|measurable|correlated|eb_secondary|independent | 12 | 12 | 0 | 0 | 12 | 12 | 0 |
| false_positive|measurable|correlated|eb_secondary|neighbor | 12 | 12 | 0 | 0 | 12 | 12 | 0 |
| false_positive|measurable|correlated|eb_secondary|own | 39 | 39 | 0 | 0 | 39 | 39 | 0 |
| false_positive|measurable|correlated|variability_masked|independent | 13 | 11 | 2 | 0 | 0 | 11 | 0 |
| false_positive|measurable|correlated|variability_masked|neighbor | 13 | 11 | 2 | 0 | 0 | 11 | 0 |
| false_positive|measurable|correlated|variability_masked|own | 36 | 27 | 9 | 0 | 0 | 27 | 0 |
| false_positive|measurable|white|blend|independent | 12 | 12 | 0 | 0 | 11 | 12 | 0 |
| false_positive|measurable|white|blend|neighbor | 12 | 12 | 0 | 0 | 12 | 12 | 0 |
| false_positive|measurable|white|blend|own | 38 | 38 | 0 | 0 | 38 | 38 | 0 |
| false_positive|measurable|white|eb_odd_even|independent | 13 | 13 | 0 | 0 | 9 | 9 | 4 |
| false_positive|measurable|white|eb_odd_even|neighbor | 13 | 13 | 0 | 0 | 9 | 9 | 4 |
| false_positive|measurable|white|eb_odd_even|own | 37 | 24 | 13 | 0 | 24 | 24 | 0 |
| false_positive|measurable|white|eb_secondary|independent | 12 | 12 | 0 | 0 | 10 | 10 | 2 |
| false_positive|measurable|white|eb_secondary|neighbor | 12 | 12 | 0 | 0 | 12 | 12 | 0 |
| false_positive|measurable|white|eb_secondary|own | 39 | 36 | 3 | 0 | 36 | 36 | 0 |
| false_positive|measurable|white|variability_masked|independent | 13 | 12 | 1 | 0 | 0 | 12 | 0 |
| false_positive|measurable|white|variability_masked|neighbor | 13 | 13 | 0 | 0 | 0 | 13 | 0 |
| false_positive|measurable|white|variability_masked|own | 36 | 35 | 1 | 0 | 0 | 35 | 0 |
| false_positive|near|correlated|blend|independent | 5 | 5 | 0 | 0 | 5 | 5 | 0 |
| false_positive|near|correlated|blend|neighbor | 5 | 5 | 0 | 0 | 5 | 5 | 0 |
| false_positive|near|correlated|blend|own | 15 | 15 | 0 | 0 | 15 | 15 | 0 |
| false_positive|near|correlated|eb_odd_even|independent | 5 | 5 | 0 | 0 | 1 | 1 | 4 |
| false_positive|near|correlated|eb_odd_even|neighbor | 5 | 5 | 0 | 0 | 0 | 0 | 5 |
| false_positive|near|correlated|eb_odd_even|own | 15 | 6 | 9 | 0 | 6 | 6 | 0 |
| false_positive|near|correlated|eb_secondary|independent | 5 | 5 | 0 | 0 | 4 | 4 | 1 |
| false_positive|near|correlated|eb_secondary|neighbor | 5 | 5 | 0 | 0 | 1 | 1 | 4 |
| false_positive|near|correlated|eb_secondary|own | 15 | 13 | 2 | 0 | 13 | 13 | 0 |
| false_positive|near|correlated|variability_masked|independent | 5 | 5 | 0 | 0 | 0 | 5 | 0 |
| false_positive|near|correlated|variability_masked|neighbor | 5 | 5 | 0 | 0 | 0 | 5 | 0 |
| false_positive|near|correlated|variability_masked|own | 15 | 13 | 2 | 0 | 0 | 13 | 0 |
| false_positive|near|white|blend|independent | 5 | 5 | 0 | 0 | 5 | 5 | 0 |
| false_positive|near|white|blend|neighbor | 5 | 5 | 0 | 0 | 5 | 5 | 0 |
| false_positive|near|white|blend|own | 15 | 15 | 0 | 0 | 15 | 15 | 0 |
| false_positive|near|white|eb_odd_even|independent | 5 | 5 | 0 | 0 | 1 | 1 | 4 |
| false_positive|near|white|eb_odd_even|neighbor | 5 | 5 | 0 | 0 | 2 | 2 | 3 |
| false_positive|near|white|eb_odd_even|own | 15 | 2 | 13 | 0 | 2 | 2 | 0 |
| false_positive|near|white|eb_secondary|independent | 5 | 5 | 0 | 0 | 4 | 4 | 1 |
| false_positive|near|white|eb_secondary|neighbor | 5 | 5 | 0 | 0 | 1 | 1 | 4 |
| false_positive|near|white|eb_secondary|own | 15 | 10 | 5 | 0 | 10 | 10 | 0 |
| false_positive|near|white|variability_masked|independent | 5 | 5 | 0 | 0 | 0 | 5 | 0 |
| false_positive|near|white|variability_masked|neighbor | 5 | 5 | 0 | 0 | 0 | 5 | 0 |
| false_positive|near|white|variability_masked|own | 15 | 15 | 0 | 0 | 0 | 15 | 0 |
| planet|below|correlated|few_train|independent | 10 | 10 | 0 | 0 | 1 | 1 | 9 |
| planet|below|correlated|few_train|neighbor | 10 | 10 | 0 | 0 | 1 | 1 | 9 |
| planet|below|correlated|few_train|own | 30 | 2 | 19 | 9 | 1 | 2 | 0 |
| planet|below|correlated|three_years|independent | 10 | 10 | 0 | 0 | 5 | 10 | 0 |
| planet|below|correlated|three_years|neighbor | 10 | 8 | 2 | 0 | 4 | 7 | 1 |
| planet|below|correlated|three_years|own | 30 | 26 | 1 | 3 | 14 | 26 | 0 |
| planet|below|correlated|two_years|independent | 20 | 16 | 4 | 0 | 1 | 2 | 14 |
| planet|below|correlated|two_years|neighbor | 20 | 19 | 1 | 0 | 0 | 3 | 16 |
| planet|below|correlated|two_years|own | 60 | 10 | 48 | 2 | 2 | 10 | 0 |
| planet|below|correlated|variability_some_years|independent | 10 | 10 | 0 | 0 | 1 | 10 | 0 |
| planet|below|correlated|variability_some_years|neighbor | 10 | 10 | 0 | 0 | 0 | 10 | 0 |
| planet|below|correlated|variability_some_years|own | 30 | 24 | 6 | 0 | 0 | 24 | 0 |
| planet|below|white|few_train|independent | 10 | 9 | 1 | 0 | 4 | 4 | 5 |
| planet|below|white|few_train|neighbor | 10 | 5 | 5 | 0 | 2 | 4 | 1 |
| planet|below|white|few_train|own | 30 | 16 | 14 | 0 | 14 | 16 | 0 |
| planet|below|white|three_years|independent | 10 | 3 | 7 | 0 | 0 | 1 | 2 |
| planet|below|white|three_years|neighbor | 10 | 3 | 7 | 0 | 2 | 2 | 1 |
| planet|below|white|three_years|own | 30 | 9 | 21 | 0 | 5 | 9 | 0 |
| planet|below|white|two_years|independent | 20 | 10 | 10 | 0 | 3 | 3 | 7 |
| planet|below|white|two_years|neighbor | 20 | 11 | 9 | 0 | 5 | 5 | 6 |
| planet|below|white|two_years|own | 60 | 20 | 40 | 0 | 17 | 20 | 0 |
| planet|below|white|variability_some_years|independent | 10 | 10 | 0 | 0 | 0 | 10 | 0 |
| planet|below|white|variability_some_years|neighbor | 10 | 10 | 0 | 0 | 0 | 10 | 0 |
| planet|below|white|variability_some_years|own | 30 | 30 | 0 | 0 | 0 | 30 | 0 |
| planet|measurable|correlated|few_train|independent | 10 | 10 | 0 | 0 | 1 | 1 | 9 |
| planet|measurable|correlated|few_train|neighbor | 10 | 10 | 0 | 0 | 0 | 0 | 10 |
| planet|measurable|correlated|few_train|own | 30 | 2 | 1 | 27 | 2 | 2 | 0 |
| planet|measurable|correlated|three_years|independent | 10 | 10 | 0 | 0 | 0 | 0 | 10 |
| planet|measurable|correlated|three_years|neighbor | 10 | 10 | 0 | 0 | 0 | 0 | 10 |
| planet|measurable|correlated|three_years|own | 30 | 2 | 0 | 28 | 2 | 2 | 0 |
| planet|measurable|correlated|two_years|independent | 20 | 20 | 0 | 0 | 1 | 1 | 19 |
| planet|measurable|correlated|two_years|neighbor | 20 | 20 | 0 | 0 | 0 | 0 | 20 |
| planet|measurable|correlated|two_years|own | 60 | 0 | 2 | 58 | 0 | 0 | 0 |
| planet|measurable|correlated|variability_some_years|independent | 10 | 10 | 0 | 0 | 8 | 8 | 2 |
| planet|measurable|correlated|variability_some_years|neighbor | 10 | 10 | 0 | 0 | 7 | 8 | 2 |
| planet|measurable|correlated|variability_some_years|own | 30 | 22 | 0 | 8 | 18 | 22 | 0 |
| planet|measurable|white|few_train|independent | 10 | 10 | 0 | 0 | 1 | 1 | 9 |
| planet|measurable|white|few_train|neighbor | 10 | 10 | 0 | 0 | 0 | 0 | 10 |
| planet|measurable|white|few_train|own | 30 | 2 | 10 | 18 | 2 | 2 | 0 |
| planet|measurable|white|three_years|independent | 10 | 10 | 0 | 0 | 0 | 0 | 10 |
| planet|measurable|white|three_years|neighbor | 10 | 10 | 0 | 0 | 1 | 1 | 9 |
| planet|measurable|white|three_years|own | 30 | 3 | 0 | 27 | 3 | 3 | 0 |
| planet|measurable|white|two_years|independent | 20 | 20 | 0 | 0 | 0 | 0 | 20 |
| planet|measurable|white|two_years|neighbor | 20 | 20 | 0 | 0 | 1 | 1 | 19 |
| planet|measurable|white|two_years|own | 60 | 5 | 21 | 34 | 5 | 5 | 0 |
| planet|measurable|white|variability_some_years|independent | 10 | 9 | 1 | 0 | 2 | 8 | 1 |
| planet|measurable|white|variability_some_years|neighbor | 10 | 9 | 1 | 0 | 5 | 9 | 0 |
| planet|measurable|white|variability_some_years|own | 30 | 28 | 2 | 0 | 3 | 28 | 0 |
| planet|near|correlated|few_train|independent | 10 | 10 | 0 | 0 | 1 | 1 | 9 |
| planet|near|correlated|few_train|neighbor | 10 | 10 | 0 | 0 | 1 | 1 | 9 |
| planet|near|correlated|few_train|own | 30 | 4 | 7 | 19 | 4 | 4 | 0 |
| planet|near|correlated|three_years|independent | 10 | 10 | 0 | 0 | 4 | 4 | 6 |
| planet|near|correlated|three_years|neighbor | 10 | 10 | 0 | 0 | 8 | 8 | 2 |
| planet|near|correlated|three_years|own | 30 | 20 | 0 | 10 | 20 | 20 | 0 |
| planet|near|correlated|two_years|independent | 20 | 20 | 0 | 0 | 1 | 1 | 19 |
| planet|near|correlated|two_years|neighbor | 20 | 20 | 0 | 0 | 0 | 0 | 20 |
| planet|near|correlated|two_years|own | 60 | 3 | 31 | 26 | 3 | 3 | 0 |
| planet|near|correlated|variability_some_years|independent | 10 | 10 | 0 | 0 | 4 | 10 | 0 |
| planet|near|correlated|variability_some_years|neighbor | 10 | 10 | 0 | 0 | 0 | 10 | 0 |
| planet|near|correlated|variability_some_years|own | 30 | 29 | 1 | 0 | 11 | 29 | 0 |
| planet|near|white|few_train|independent | 10 | 10 | 0 | 0 | 4 | 4 | 6 |
| planet|near|white|few_train|neighbor | 10 | 10 | 0 | 0 | 0 | 0 | 10 |
| planet|near|white|few_train|own | 30 | 7 | 20 | 3 | 7 | 7 | 0 |
| planet|near|white|three_years|independent | 10 | 10 | 0 | 0 | 5 | 5 | 5 |
| planet|near|white|three_years|neighbor | 10 | 10 | 0 | 0 | 10 | 10 | 0 |
| planet|near|white|three_years|own | 30 | 18 | 5 | 7 | 17 | 18 | 0 |
| planet|near|white|two_years|independent | 20 | 20 | 0 | 0 | 2 | 2 | 18 |
| planet|near|white|two_years|neighbor | 20 | 20 | 0 | 0 | 6 | 6 | 14 |
| planet|near|white|two_years|own | 60 | 16 | 44 | 0 | 15 | 16 | 0 |
| planet|near|white|variability_some_years|independent | 10 | 9 | 1 | 0 | 0 | 9 | 0 |
| planet|near|white|variability_some_years|neighbor | 10 | 10 | 0 | 0 | 0 | 10 | 0 |
| planet|near|white|variability_some_years|own | 30 | 30 | 0 | 0 | 0 | 30 | 0 |

## Redraws by class, band and mechanism

| Family | cases | redrawn | redraws |
|---|---|---|---|
| false_positive|below|blend | 50 | 0 | {} |
| false_positive|below|eb_odd_even | 50 | 0 | {} |
| false_positive|below|eb_secondary | 50 | 0 | {} |
| false_positive|below|variability_masked | 50 | 9 | {'commensurate_periods': 9} |
| false_positive|measurable|blend | 124 | 6 | {'depth_limit': 7} |
| false_positive|measurable|eb_odd_even | 126 | 0 | {} |
| false_positive|measurable|eb_secondary | 126 | 0 | {} |
| false_positive|measurable|variability_masked | 124 | 16 | {'commensurate_periods': 20} |
| false_positive|near|blend | 50 | 0 | {} |
| false_positive|near|eb_odd_even | 50 | 0 | {} |
| false_positive|near|eb_secondary | 50 | 0 | {} |
| false_positive|near|variability_masked | 50 | 7 | {'commensurate_periods': 7} |
| no_transit|none|pure_noise | 1120 | 0 | {} |
| no_transit|none|trend | 840 | 0 | {} |
| no_transit|none|trend_variability | 840 | 0 | {} |
| planet|below|few_train | 100 | 64 | {'train_transit_count': 158} |
| planet|below|three_years | 100 | 0 | {} |
| planet|below|two_years | 200 | 0 | {} |
| planet|below|variability_some_years | 100 | 0 | {} |
| planet|measurable|few_train | 100 | 54 | {'train_transit_count': 194} |
| planet|measurable|three_years | 100 | 0 | {} |
| planet|measurable|two_years | 200 | 0 | {} |
| planet|measurable|variability_some_years | 100 | 0 | {} |
| planet|near|few_train | 100 | 66 | {'train_transit_count': 181} |
| planet|near|three_years | 100 | 0 | {} |
| planet|near|two_years | 200 | 0 | {} |
| planet|near|variability_some_years | 100 | 0 | {} |

## Paired comparisons M0 -> M1

| Condition | Outcome | Group | n | before | after | difference | up | down | McNemar p |
|---|---|---|---|---|---|---|---|---|---|
| i | refuted | planet | correlated|below | 250 | 0.4680 | 0.4680 | 0.0000 | 0 | 0 | 1 |
| i | refuted | planet | correlated|measurable | 250 | 0.2240 | 0.2240 | 0.0000 | 0 | 0 | 1 |
| i | refuted | planet | correlated|near | 250 | 0.3680 | 0.3680 | 0.0000 | 0 | 0 | 1 |
| i | refuted | planet | white|below | 250 | 0.4840 | 0.4840 | 0.0000 | 0 | 0 | 1 |
| i | refuted | planet | white|measurable | 250 | 0.2520 | 0.2520 | 0.0000 | 0 | 0 | 1 |
| i | refuted | planet | white|near | 250 | 0.5040 | 0.5040 | 0.0000 | 0 | 0 | 1 |
| i | flagged_identity | false_positive | correlated|below | 100 | 0.3200 | 0.3200 | 0.0000 | 0 | 0 | 1 |
| i | flagged_identity | false_positive | correlated|measurable | 250 | 0.7040 | 0.7040 | 0.0000 | 0 | 0 | 1 |
| i | flagged_identity | false_positive | correlated|near | 100 | 0.5000 | 0.5000 | 0.0000 | 0 | 0 | 1 |
| i | flagged_identity | false_positive | white|below | 100 | 0.2800 | 0.2800 | 0.0000 | 0 | 0 | 1 |
| i | flagged_identity | false_positive | white|measurable | 250 | 0.6440 | 0.6440 | 0.0000 | 0 | 0 | 1 |
| i | flagged_identity | false_positive | white|near | 100 | 0.4500 | 0.4500 | 0.0000 | 0 | 0 | 1 |
| i | flagged_old | false_positive | correlated|below | 100 | 0.5900 | 0.5900 | 0.0000 | 0 | 0 | 1 |
| i | flagged_old | false_positive | correlated|measurable | 250 | 0.9000 | 0.9000 | 0.0000 | 0 | 0 | 1 |
| i | flagged_old | false_positive | correlated|near | 100 | 0.7300 | 0.7300 | 0.0000 | 0 | 0 | 1 |
| i | flagged_old | false_positive | white|below | 100 | 0.5700 | 0.5700 | 0.0000 | 0 | 0 | 1 |
| i | flagged_old | false_positive | white|measurable | 250 | 0.8880 | 0.8880 | 0.0000 | 0 | 0 | 1 |
| i | flagged_old | false_positive | white|near | 100 | 0.7000 | 0.7000 | 0.0000 | 0 | 0 | 1 |
| i | inconclusive | planet | correlated|below | 250 | 0.4520 | 0.4520 | 0.0000 | 0 | 0 | 1 |
| i | inconclusive | planet | correlated|measurable | 250 | 0.0160 | 0.0160 | 0.0000 | 0 | 0 | 1 |
| i | inconclusive | planet | correlated|near | 250 | 0.2680 | 0.2680 | 0.0000 | 0 | 0 | 1 |
| i | inconclusive | planet | white|below | 250 | 0.5120 | 0.5120 | 0.0000 | 0 | 0 | 1 |
| i | inconclusive | planet | white|measurable | 250 | 0.2280 | 0.2280 | 0.0000 | 0 | 0 | 1 |
| i | inconclusive | planet | white|near | 250 | 0.4280 | 0.4280 | 0.0000 | 0 | 0 | 1 |
| i | inconclusive | false_positive | correlated|below | 100 | 0.3900 | 0.3900 | 0.0000 | 0 | 0 | 1 |
| i | inconclusive | false_positive | correlated|measurable | 250 | 0.0600 | 0.0600 | 0.0000 | 0 | 0 | 1 |
| i | inconclusive | false_positive | correlated|near | 100 | 0.2600 | 0.2600 | 0.0000 | 0 | 0 | 1 |
| i | inconclusive | false_positive | white|below | 100 | 0.4300 | 0.4300 | 0.0000 | 0 | 0 | 1 |
| i | inconclusive | false_positive | white|measurable | 250 | 0.1040 | 0.1040 | 0.0000 | 0 | 0 | 1 |
| i | inconclusive | false_positive | white|near | 100 | 0.2900 | 0.2900 | 0.0000 | 0 | 0 | 1 |
| i | inconclusive | no_transit | correlated|none | 600 | 0.5467 | 0.5467 | 0.0000 | 0 | 0 | 1 |
| i | inconclusive | no_transit | white|none | 2200 | 0.8218 | 0.8218 | 0.0000 | 0 | 0 | 1 |
| i | false_alarm | no_transit | correlated|none | 600 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| i | false_alarm | no_transit | white|none | 2200 | 0.0023 | 0.0023 | 0.0000 | 0 | 0 | 1 |
| ii | refuted | planet | correlated|below | 250 | 0.9520 | 0.9520 | 0.0000 | 0 | 0 | 1 |
| ii | refuted | planet | correlated|measurable | 250 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii | refuted | planet | correlated|near | 250 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii | refuted | planet | white|below | 250 | 0.6800 | 0.6800 | 0.0000 | 0 | 0 | 1 |
| ii | refuted | planet | white|measurable | 250 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii | refuted | planet | white|near | 250 | 0.9960 | 0.9960 | 0.0000 | 0 | 0 | 1 |
| ii | flagged_identity | false_positive | correlated|below | 100 | 0.3200 | 0.3200 | 0.0000 | 0 | 0 | 1 |
| ii | flagged_identity | false_positive | correlated|measurable | 250 | 0.7040 | 0.7040 | 0.0000 | 0 | 0 | 1 |
| ii | flagged_identity | false_positive | correlated|near | 100 | 0.5000 | 0.5000 | 0.0000 | 0 | 0 | 1 |
| ii | flagged_identity | false_positive | white|below | 100 | 0.2800 | 0.2800 | 0.0000 | 0 | 0 | 1 |
| ii | flagged_identity | false_positive | white|measurable | 250 | 0.6440 | 0.6440 | 0.0000 | 0 | 0 | 1 |
| ii | flagged_identity | false_positive | white|near | 100 | 0.4500 | 0.4500 | 0.0000 | 0 | 0 | 1 |
| ii | flagged_old | false_positive | correlated|below | 100 | 0.5900 | 0.5900 | 0.0000 | 0 | 0 | 1 |
| ii | flagged_old | false_positive | correlated|measurable | 250 | 0.9000 | 0.9000 | 0.0000 | 0 | 0 | 1 |
| ii | flagged_old | false_positive | correlated|near | 100 | 0.7300 | 0.7300 | 0.0000 | 0 | 0 | 1 |
| ii | flagged_old | false_positive | white|below | 100 | 0.5700 | 0.5700 | 0.0000 | 0 | 0 | 1 |
| ii | flagged_old | false_positive | white|measurable | 250 | 0.8880 | 0.8880 | 0.0000 | 0 | 0 | 1 |
| ii | flagged_old | false_positive | white|near | 100 | 0.7000 | 0.7000 | 0.0000 | 0 | 0 | 1 |
| ii | inconclusive | planet | correlated|below | 250 | 0.0480 | 0.0480 | 0.0000 | 0 | 0 | 1 |
| ii | inconclusive | planet | correlated|measurable | 250 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii | inconclusive | planet | correlated|near | 250 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii | inconclusive | planet | white|below | 250 | 0.3200 | 0.3200 | 0.0000 | 0 | 0 | 1 |
| ii | inconclusive | planet | white|measurable | 250 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii | inconclusive | planet | white|near | 250 | 0.0040 | 0.0040 | 0.0000 | 0 | 0 | 1 |
| ii | inconclusive | false_positive | correlated|below | 100 | 0.0400 | 0.0400 | 0.0000 | 0 | 0 | 1 |
| ii | inconclusive | false_positive | correlated|measurable | 250 | 0.0320 | 0.0320 | 0.0000 | 0 | 0 | 1 |
| ii | inconclusive | false_positive | correlated|near | 100 | 0.0200 | 0.0200 | 0.0000 | 0 | 0 | 1 |
| ii | inconclusive | false_positive | white|below | 100 | 0.1400 | 0.1400 | 0.0000 | 0 | 0 | 1 |
| ii | inconclusive | false_positive | white|measurable | 250 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii | inconclusive | false_positive | white|near | 100 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | refuted | planet | correlated|below|independent | 50 | 0.9200 | 0.9200 | 0.0000 | 0 | 0 | 1 |
| ii by variant | refuted | planet | correlated|below|neighbor | 50 | 0.9600 | 0.9600 | 0.0000 | 0 | 0 | 1 |
| ii by variant | refuted | planet | correlated|below|own | 150 | 0.9600 | 0.9600 | 0.0000 | 0 | 0 | 1 |
| ii by variant | refuted | planet | correlated|measurable|independent | 50 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | refuted | planet | correlated|measurable|neighbor | 50 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | refuted | planet | correlated|measurable|own | 150 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | refuted | planet | correlated|near|independent | 50 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | refuted | planet | correlated|near|neighbor | 50 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | refuted | planet | correlated|near|own | 150 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | refuted | planet | white|below|independent | 50 | 0.6400 | 0.6400 | 0.0000 | 0 | 0 | 1 |
| ii by variant | refuted | planet | white|below|neighbor | 50 | 0.5800 | 0.5800 | 0.0000 | 0 | 0 | 1 |
| ii by variant | refuted | planet | white|below|own | 150 | 0.7267 | 0.7267 | 0.0000 | 0 | 0 | 1 |
| ii by variant | refuted | planet | white|measurable|independent | 50 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | refuted | planet | white|measurable|neighbor | 50 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | refuted | planet | white|measurable|own | 150 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | refuted | planet | white|near|independent | 50 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | refuted | planet | white|near|neighbor | 50 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | refuted | planet | white|near|own | 150 | 0.9933 | 0.9933 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_identity | false_positive | correlated|below|independent | 20 | 0.2500 | 0.2500 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_identity | false_positive | correlated|below|neighbor | 20 | 0.4000 | 0.4000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_identity | false_positive | correlated|below|own | 60 | 0.3167 | 0.3167 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_identity | false_positive | correlated|measurable|independent | 50 | 0.7000 | 0.7000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_identity | false_positive | correlated|measurable|neighbor | 50 | 0.6600 | 0.6600 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_identity | false_positive | correlated|measurable|own | 150 | 0.7200 | 0.7200 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_identity | false_positive | correlated|near|independent | 20 | 0.5000 | 0.5000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_identity | false_positive | correlated|near|neighbor | 20 | 0.3000 | 0.3000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_identity | false_positive | correlated|near|own | 60 | 0.5667 | 0.5667 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_identity | false_positive | white|below|independent | 20 | 0.2000 | 0.2000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_identity | false_positive | white|below|neighbor | 20 | 0.3500 | 0.3500 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_identity | false_positive | white|below|own | 60 | 0.2833 | 0.2833 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_identity | false_positive | white|measurable|independent | 50 | 0.6000 | 0.6000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_identity | false_positive | white|measurable|neighbor | 50 | 0.6600 | 0.6600 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_identity | false_positive | white|measurable|own | 150 | 0.6533 | 0.6533 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_identity | false_positive | white|near|independent | 20 | 0.5000 | 0.5000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_identity | false_positive | white|near|neighbor | 20 | 0.4000 | 0.4000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_identity | false_positive | white|near|own | 60 | 0.4500 | 0.4500 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_old | false_positive | correlated|below|independent | 20 | 0.6000 | 0.6000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_old | false_positive | correlated|below|neighbor | 20 | 0.6000 | 0.6000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_old | false_positive | correlated|below|own | 60 | 0.5833 | 0.5833 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_old | false_positive | correlated|measurable|independent | 50 | 0.9200 | 0.9200 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_old | false_positive | correlated|measurable|neighbor | 50 | 0.8800 | 0.8800 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_old | false_positive | correlated|measurable|own | 150 | 0.9000 | 0.9000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_old | false_positive | correlated|near|independent | 20 | 0.7500 | 0.7500 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_old | false_positive | correlated|near|neighbor | 20 | 0.5500 | 0.5500 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_old | false_positive | correlated|near|own | 60 | 0.7833 | 0.7833 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_old | false_positive | white|below|independent | 20 | 0.5000 | 0.5000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_old | false_positive | white|below|neighbor | 20 | 0.6000 | 0.6000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_old | false_positive | white|below|own | 60 | 0.5833 | 0.5833 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_old | false_positive | white|measurable|independent | 50 | 0.8600 | 0.8600 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_old | false_positive | white|measurable|neighbor | 50 | 0.9200 | 0.9200 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_old | false_positive | white|measurable|own | 150 | 0.8867 | 0.8867 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_old | false_positive | white|near|independent | 20 | 0.7500 | 0.7500 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_old | false_positive | white|near|neighbor | 20 | 0.6500 | 0.6500 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_old | false_positive | white|near|own | 60 | 0.7000 | 0.7000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | planet | correlated|below|independent | 50 | 0.0800 | 0.0800 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | planet | correlated|below|neighbor | 50 | 0.0400 | 0.0400 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | planet | correlated|below|own | 150 | 0.0400 | 0.0400 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | planet | correlated|measurable|independent | 50 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | planet | correlated|measurable|neighbor | 50 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | planet | correlated|measurable|own | 150 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | planet | correlated|near|independent | 50 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | planet | correlated|near|neighbor | 50 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | planet | correlated|near|own | 150 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | planet | white|below|independent | 50 | 0.3600 | 0.3600 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | planet | white|below|neighbor | 50 | 0.4200 | 0.4200 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | planet | white|below|own | 150 | 0.2733 | 0.2733 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | planet | white|measurable|independent | 50 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | planet | white|measurable|neighbor | 50 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | planet | white|measurable|own | 150 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | planet | white|near|independent | 50 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | planet | white|near|neighbor | 50 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | planet | white|near|own | 150 | 0.0067 | 0.0067 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | false_positive | correlated|below|independent | 20 | 0.0500 | 0.0500 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | false_positive | correlated|below|neighbor | 20 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | false_positive | correlated|below|own | 60 | 0.0500 | 0.0500 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | false_positive | correlated|measurable|independent | 50 | 0.0400 | 0.0400 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | false_positive | correlated|measurable|neighbor | 50 | 0.0200 | 0.0200 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | false_positive | correlated|measurable|own | 150 | 0.0333 | 0.0333 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | false_positive | correlated|near|independent | 20 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | false_positive | correlated|near|neighbor | 20 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | false_positive | correlated|near|own | 60 | 0.0333 | 0.0333 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | false_positive | white|below|independent | 20 | 0.1000 | 0.1000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | false_positive | white|below|neighbor | 20 | 0.1500 | 0.1500 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | false_positive | white|below|own | 60 | 0.1500 | 0.1500 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | false_positive | white|measurable|independent | 50 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | false_positive | white|measurable|neighbor | 50 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | false_positive | white|measurable|own | 150 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | false_positive | white|near|independent | 20 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | false_positive | white|near|neighbor | 20 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | false_positive | white|near|own | 60 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| i (aggregate, additional) | refuted | planet | all | 1500 | 0.3833 | 0.3833 | 0.0000 | 0 | 0 | 1 |
| i (aggregate, additional) | flagged_identity | false_positive | all | 900 | 0.5467 | 0.5467 | 0.0000 | 0 | 0 | 1 |
| i (aggregate, additional) | flagged_old | false_positive | all | 900 | 0.7844 | 0.7844 | 0.0000 | 0 | 0 | 1 |
| i (aggregate, additional) | inconclusive | planet | all | 1500 | 0.3173 | 0.3173 | 0.0000 | 0 | 0 | 1 |
| i (aggregate, additional) | inconclusive | false_positive | all | 900 | 0.1978 | 0.1978 | 0.0000 | 0 | 0 | 1 |
| i (aggregate, additional) | inconclusive | no_transit | all | 2800 | 0.7629 | 0.7629 | 0.0000 | 0 | 0 | 1 |
| i (aggregate, additional) | false_alarm | no_transit | all | 2800 | 0.0018 | 0.0018 | 0.0000 | 0 | 0 | 1 |
| ii (aggregate, additional) | refuted | planet | all | 1500 | 0.9380 | 0.9380 | 0.0000 | 0 | 0 | 1 |
| ii (aggregate, additional) | flagged_identity | false_positive | all | 900 | 0.5467 | 0.5467 | 0.0000 | 0 | 0 | 1 |
| ii (aggregate, additional) | flagged_old | false_positive | all | 900 | 0.7844 | 0.7844 | 0.0000 | 0 | 0 | 1 |
| ii (aggregate, additional) | inconclusive | planet | all | 1500 | 0.0620 | 0.0620 | 0.0000 | 0 | 0 | 1 |
| ii (aggregate, additional) | inconclusive | false_positive | all | 900 | 0.0311 | 0.0311 | 0.0000 | 0 | 0 | 1 |

## Paired comparisons M1 -> M2

| Condition | Outcome | Group | n | before | after | difference | up | down | McNemar p |
|---|---|---|---|---|---|---|---|---|---|
| i | refuted | planet | correlated|below | 250 | 0.4680 | 0.4240 | -0.0440 | 0 | 11 | 0.0009766 |
| i | refuted | planet | correlated|measurable | 250 | 0.2240 | 0.1760 | -0.0480 | 0 | 12 | 0.0004883 |
| i | refuted | planet | correlated|near | 250 | 0.3680 | 0.3640 | -0.0040 | 0 | 1 | 1 |
| i | refuted | planet | white|below | 250 | 0.4840 | 0.4560 | -0.0280 | 0 | 7 | 0.01562 |
| i | refuted | planet | white|measurable | 250 | 0.2520 | 0.2320 | -0.0200 | 0 | 5 | 0.0625 |
| i | refuted | planet | white|near | 250 | 0.5040 | 0.4680 | -0.0360 | 0 | 9 | 0.003906 |
| i | flagged_identity | false_positive | correlated|below | 100 | 0.3200 | 0.3200 | 0.0000 | 0 | 0 | 1 |
| i | flagged_identity | false_positive | correlated|measurable | 250 | 0.7040 | 0.7040 | 0.0000 | 0 | 0 | 1 |
| i | flagged_identity | false_positive | correlated|near | 100 | 0.5000 | 0.5000 | 0.0000 | 0 | 0 | 1 |
| i | flagged_identity | false_positive | white|below | 100 | 0.2800 | 0.2800 | 0.0000 | 0 | 0 | 1 |
| i | flagged_identity | false_positive | white|measurable | 250 | 0.6440 | 0.6440 | 0.0000 | 0 | 0 | 1 |
| i | flagged_identity | false_positive | white|near | 100 | 0.4500 | 0.4500 | 0.0000 | 0 | 0 | 1 |
| i | flagged_old | false_positive | correlated|below | 100 | 0.5900 | 0.5900 | 0.0000 | 0 | 0 | 1 |
| i | flagged_old | false_positive | correlated|measurable | 250 | 0.9000 | 0.9000 | 0.0000 | 0 | 0 | 1 |
| i | flagged_old | false_positive | correlated|near | 100 | 0.7300 | 0.7300 | 0.0000 | 0 | 0 | 1 |
| i | flagged_old | false_positive | white|below | 100 | 0.5700 | 0.5700 | 0.0000 | 0 | 0 | 1 |
| i | flagged_old | false_positive | white|measurable | 250 | 0.8880 | 0.8880 | 0.0000 | 0 | 0 | 1 |
| i | flagged_old | false_positive | white|near | 100 | 0.7000 | 0.7000 | 0.0000 | 0 | 0 | 1 |
| i | inconclusive | planet | correlated|below | 250 | 0.4520 | 0.4880 | 0.0360 | 9 | 0 | 0.003906 |
| i | inconclusive | planet | correlated|measurable | 250 | 0.0160 | 0.0160 | 0.0000 | 0 | 0 | 1 |
| i | inconclusive | planet | correlated|near | 250 | 0.2680 | 0.2720 | 0.0040 | 1 | 0 | 1 |
| i | inconclusive | planet | white|below | 250 | 0.5120 | 0.5440 | 0.0320 | 8 | 0 | 0.007812 |
| i | inconclusive | planet | white|measurable | 250 | 0.2280 | 0.2440 | 0.0160 | 4 | 0 | 0.125 |
| i | inconclusive | planet | white|near | 250 | 0.4280 | 0.4640 | 0.0360 | 9 | 0 | 0.003906 |
| i | inconclusive | false_positive | correlated|below | 100 | 0.3900 | 0.4100 | 0.0200 | 2 | 0 | 0.5 |
| i | inconclusive | false_positive | correlated|measurable | 250 | 0.0600 | 0.0840 | 0.0240 | 6 | 0 | 0.03125 |
| i | inconclusive | false_positive | correlated|near | 100 | 0.2600 | 0.2600 | 0.0000 | 0 | 0 | 1 |
| i | inconclusive | false_positive | white|below | 100 | 0.4300 | 0.4300 | 0.0000 | 0 | 0 | 1 |
| i | inconclusive | false_positive | white|measurable | 250 | 0.1040 | 0.1120 | 0.0080 | 2 | 0 | 0.5 |
| i | inconclusive | false_positive | white|near | 100 | 0.2900 | 0.2900 | 0.0000 | 0 | 0 | 1 |
| i | inconclusive | no_transit | correlated|none | 600 | 0.5467 | 0.5467 | 0.0000 | 0 | 0 | 1 |
| i | inconclusive | no_transit | white|none | 2200 | 0.8218 | 0.8241 | 0.0023 | 5 | 0 | 0.0625 |
| i | false_alarm | no_transit | correlated|none | 600 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| i | false_alarm | no_transit | white|none | 2200 | 0.0023 | 0.0000 | -0.0023 | 0 | 5 | 0.0625 |
| ii | refuted | planet | correlated|below | 250 | 0.9520 | 0.9200 | -0.0320 | 0 | 8 | 0.007812 |
| ii | refuted | planet | correlated|measurable | 250 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii | refuted | planet | correlated|near | 250 | 1.0000 | 0.9960 | -0.0040 | 0 | 1 | 1 |
| ii | refuted | planet | white|below | 250 | 0.6800 | 0.6800 | 0.0000 | 0 | 0 | 1 |
| ii | refuted | planet | white|measurable | 250 | 1.0000 | 0.9840 | -0.0160 | 0 | 4 | 0.125 |
| ii | refuted | planet | white|near | 250 | 0.9960 | 0.9920 | -0.0040 | 0 | 1 | 1 |
| ii | flagged_identity | false_positive | correlated|below | 100 | 0.3200 | 0.3200 | 0.0000 | 0 | 0 | 1 |
| ii | flagged_identity | false_positive | correlated|measurable | 250 | 0.7040 | 0.7040 | 0.0000 | 0 | 0 | 1 |
| ii | flagged_identity | false_positive | correlated|near | 100 | 0.5000 | 0.5000 | 0.0000 | 0 | 0 | 1 |
| ii | flagged_identity | false_positive | white|below | 100 | 0.2800 | 0.2800 | 0.0000 | 0 | 0 | 1 |
| ii | flagged_identity | false_positive | white|measurable | 250 | 0.6440 | 0.6440 | 0.0000 | 0 | 0 | 1 |
| ii | flagged_identity | false_positive | white|near | 100 | 0.4500 | 0.4500 | 0.0000 | 0 | 0 | 1 |
| ii | flagged_old | false_positive | correlated|below | 100 | 0.5900 | 0.5900 | 0.0000 | 0 | 0 | 1 |
| ii | flagged_old | false_positive | correlated|measurable | 250 | 0.9000 | 0.9000 | 0.0000 | 0 | 0 | 1 |
| ii | flagged_old | false_positive | correlated|near | 100 | 0.7300 | 0.7300 | 0.0000 | 0 | 0 | 1 |
| ii | flagged_old | false_positive | white|below | 100 | 0.5700 | 0.5700 | 0.0000 | 0 | 0 | 1 |
| ii | flagged_old | false_positive | white|measurable | 250 | 0.8880 | 0.8880 | 0.0000 | 0 | 0 | 1 |
| ii | flagged_old | false_positive | white|near | 100 | 0.7000 | 0.7000 | 0.0000 | 0 | 0 | 1 |
| ii | inconclusive | planet | correlated|below | 250 | 0.0480 | 0.0800 | 0.0320 | 8 | 0 | 0.007812 |
| ii | inconclusive | planet | correlated|measurable | 250 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii | inconclusive | planet | correlated|near | 250 | 0.0000 | 0.0040 | 0.0040 | 1 | 0 | 1 |
| ii | inconclusive | planet | white|below | 250 | 0.3200 | 0.3200 | 0.0000 | 0 | 0 | 1 |
| ii | inconclusive | planet | white|measurable | 250 | 0.0000 | 0.0160 | 0.0160 | 4 | 0 | 0.125 |
| ii | inconclusive | planet | white|near | 250 | 0.0040 | 0.0080 | 0.0040 | 1 | 0 | 1 |
| ii | inconclusive | false_positive | correlated|below | 100 | 0.0400 | 0.0600 | 0.0200 | 2 | 0 | 0.5 |
| ii | inconclusive | false_positive | correlated|measurable | 250 | 0.0320 | 0.0520 | 0.0200 | 5 | 0 | 0.0625 |
| ii | inconclusive | false_positive | correlated|near | 100 | 0.0200 | 0.0200 | 0.0000 | 0 | 0 | 1 |
| ii | inconclusive | false_positive | white|below | 100 | 0.1400 | 0.1400 | 0.0000 | 0 | 0 | 1 |
| ii | inconclusive | false_positive | white|measurable | 250 | 0.0000 | 0.0080 | 0.0080 | 2 | 0 | 0.5 |
| ii | inconclusive | false_positive | white|near | 100 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | refuted | planet | correlated|below|independent | 50 | 0.9200 | 0.9200 | 0.0000 | 0 | 0 | 1 |
| ii by variant | refuted | planet | correlated|below|neighbor | 50 | 0.9600 | 0.9400 | -0.0200 | 0 | 1 | 1 |
| ii by variant | refuted | planet | correlated|below|own | 150 | 0.9600 | 0.9133 | -0.0467 | 0 | 7 | 0.01562 |
| ii by variant | refuted | planet | correlated|measurable|independent | 50 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | refuted | planet | correlated|measurable|neighbor | 50 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | refuted | planet | correlated|measurable|own | 150 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | refuted | planet | correlated|near|independent | 50 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | refuted | planet | correlated|near|neighbor | 50 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | refuted | planet | correlated|near|own | 150 | 1.0000 | 0.9933 | -0.0067 | 0 | 1 | 1 |
| ii by variant | refuted | planet | white|below|independent | 50 | 0.6400 | 0.6400 | 0.0000 | 0 | 0 | 1 |
| ii by variant | refuted | planet | white|below|neighbor | 50 | 0.5800 | 0.5800 | 0.0000 | 0 | 0 | 1 |
| ii by variant | refuted | planet | white|below|own | 150 | 0.7267 | 0.7267 | 0.0000 | 0 | 0 | 1 |
| ii by variant | refuted | planet | white|measurable|independent | 50 | 1.0000 | 0.9800 | -0.0200 | 0 | 1 | 1 |
| ii by variant | refuted | planet | white|measurable|neighbor | 50 | 1.0000 | 0.9800 | -0.0200 | 0 | 1 | 1 |
| ii by variant | refuted | planet | white|measurable|own | 150 | 1.0000 | 0.9867 | -0.0133 | 0 | 2 | 0.5 |
| ii by variant | refuted | planet | white|near|independent | 50 | 1.0000 | 0.9800 | -0.0200 | 0 | 1 | 1 |
| ii by variant | refuted | planet | white|near|neighbor | 50 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | refuted | planet | white|near|own | 150 | 0.9933 | 0.9933 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_identity | false_positive | correlated|below|independent | 20 | 0.2500 | 0.2500 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_identity | false_positive | correlated|below|neighbor | 20 | 0.4000 | 0.4000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_identity | false_positive | correlated|below|own | 60 | 0.3167 | 0.3167 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_identity | false_positive | correlated|measurable|independent | 50 | 0.7000 | 0.7000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_identity | false_positive | correlated|measurable|neighbor | 50 | 0.6600 | 0.6600 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_identity | false_positive | correlated|measurable|own | 150 | 0.7200 | 0.7200 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_identity | false_positive | correlated|near|independent | 20 | 0.5000 | 0.5000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_identity | false_positive | correlated|near|neighbor | 20 | 0.3000 | 0.3000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_identity | false_positive | correlated|near|own | 60 | 0.5667 | 0.5667 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_identity | false_positive | white|below|independent | 20 | 0.2000 | 0.2000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_identity | false_positive | white|below|neighbor | 20 | 0.3500 | 0.3500 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_identity | false_positive | white|below|own | 60 | 0.2833 | 0.2833 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_identity | false_positive | white|measurable|independent | 50 | 0.6000 | 0.6000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_identity | false_positive | white|measurable|neighbor | 50 | 0.6600 | 0.6600 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_identity | false_positive | white|measurable|own | 150 | 0.6533 | 0.6533 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_identity | false_positive | white|near|independent | 20 | 0.5000 | 0.5000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_identity | false_positive | white|near|neighbor | 20 | 0.4000 | 0.4000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_identity | false_positive | white|near|own | 60 | 0.4500 | 0.4500 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_old | false_positive | correlated|below|independent | 20 | 0.6000 | 0.6000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_old | false_positive | correlated|below|neighbor | 20 | 0.6000 | 0.6000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_old | false_positive | correlated|below|own | 60 | 0.5833 | 0.5833 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_old | false_positive | correlated|measurable|independent | 50 | 0.9200 | 0.9200 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_old | false_positive | correlated|measurable|neighbor | 50 | 0.8800 | 0.8800 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_old | false_positive | correlated|measurable|own | 150 | 0.9000 | 0.9000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_old | false_positive | correlated|near|independent | 20 | 0.7500 | 0.7500 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_old | false_positive | correlated|near|neighbor | 20 | 0.5500 | 0.5500 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_old | false_positive | correlated|near|own | 60 | 0.7833 | 0.7833 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_old | false_positive | white|below|independent | 20 | 0.5000 | 0.5000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_old | false_positive | white|below|neighbor | 20 | 0.6000 | 0.6000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_old | false_positive | white|below|own | 60 | 0.5833 | 0.5833 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_old | false_positive | white|measurable|independent | 50 | 0.8600 | 0.8600 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_old | false_positive | white|measurable|neighbor | 50 | 0.9200 | 0.9200 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_old | false_positive | white|measurable|own | 150 | 0.8867 | 0.8867 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_old | false_positive | white|near|independent | 20 | 0.7500 | 0.7500 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_old | false_positive | white|near|neighbor | 20 | 0.6500 | 0.6500 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_old | false_positive | white|near|own | 60 | 0.7000 | 0.7000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | planet | correlated|below|independent | 50 | 0.0800 | 0.0800 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | planet | correlated|below|neighbor | 50 | 0.0400 | 0.0600 | 0.0200 | 1 | 0 | 1 |
| ii by variant | inconclusive | planet | correlated|below|own | 150 | 0.0400 | 0.0867 | 0.0467 | 7 | 0 | 0.01562 |
| ii by variant | inconclusive | planet | correlated|measurable|independent | 50 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | planet | correlated|measurable|neighbor | 50 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | planet | correlated|measurable|own | 150 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | planet | correlated|near|independent | 50 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | planet | correlated|near|neighbor | 50 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | planet | correlated|near|own | 150 | 0.0000 | 0.0067 | 0.0067 | 1 | 0 | 1 |
| ii by variant | inconclusive | planet | white|below|independent | 50 | 0.3600 | 0.3600 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | planet | white|below|neighbor | 50 | 0.4200 | 0.4200 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | planet | white|below|own | 150 | 0.2733 | 0.2733 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | planet | white|measurable|independent | 50 | 0.0000 | 0.0200 | 0.0200 | 1 | 0 | 1 |
| ii by variant | inconclusive | planet | white|measurable|neighbor | 50 | 0.0000 | 0.0200 | 0.0200 | 1 | 0 | 1 |
| ii by variant | inconclusive | planet | white|measurable|own | 150 | 0.0000 | 0.0133 | 0.0133 | 2 | 0 | 0.5 |
| ii by variant | inconclusive | planet | white|near|independent | 50 | 0.0000 | 0.0200 | 0.0200 | 1 | 0 | 1 |
| ii by variant | inconclusive | planet | white|near|neighbor | 50 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | planet | white|near|own | 150 | 0.0067 | 0.0067 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | false_positive | correlated|below|independent | 20 | 0.0500 | 0.0500 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | false_positive | correlated|below|neighbor | 20 | 0.0000 | 0.0500 | 0.0500 | 1 | 0 | 1 |
| ii by variant | inconclusive | false_positive | correlated|below|own | 60 | 0.0500 | 0.0667 | 0.0167 | 1 | 0 | 1 |
| ii by variant | inconclusive | false_positive | correlated|measurable|independent | 50 | 0.0400 | 0.0400 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | false_positive | correlated|measurable|neighbor | 50 | 0.0200 | 0.0400 | 0.0200 | 1 | 0 | 1 |
| ii by variant | inconclusive | false_positive | correlated|measurable|own | 150 | 0.0333 | 0.0600 | 0.0267 | 4 | 0 | 0.125 |
| ii by variant | inconclusive | false_positive | correlated|near|independent | 20 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | false_positive | correlated|near|neighbor | 20 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | false_positive | correlated|near|own | 60 | 0.0333 | 0.0333 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | false_positive | white|below|independent | 20 | 0.1000 | 0.1000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | false_positive | white|below|neighbor | 20 | 0.1500 | 0.1500 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | false_positive | white|below|own | 60 | 0.1500 | 0.1500 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | false_positive | white|measurable|independent | 50 | 0.0000 | 0.0200 | 0.0200 | 1 | 0 | 1 |
| ii by variant | inconclusive | false_positive | white|measurable|neighbor | 50 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | false_positive | white|measurable|own | 150 | 0.0000 | 0.0067 | 0.0067 | 1 | 0 | 1 |
| ii by variant | inconclusive | false_positive | white|near|independent | 20 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | false_positive | white|near|neighbor | 20 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | false_positive | white|near|own | 60 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| i (aggregate, additional) | refuted | planet | all | 1500 | 0.3833 | 0.3533 | -0.0300 | 0 | 45 | 5.684e-14 |
| i (aggregate, additional) | flagged_identity | false_positive | all | 900 | 0.5467 | 0.5467 | 0.0000 | 0 | 0 | 1 |
| i (aggregate, additional) | flagged_old | false_positive | all | 900 | 0.7844 | 0.7844 | 0.0000 | 0 | 0 | 1 |
| i (aggregate, additional) | inconclusive | planet | all | 1500 | 0.3173 | 0.3380 | 0.0207 | 31 | 0 | 9.313e-10 |
| i (aggregate, additional) | inconclusive | false_positive | all | 900 | 0.1978 | 0.2089 | 0.0111 | 10 | 0 | 0.001953 |
| i (aggregate, additional) | inconclusive | no_transit | all | 2800 | 0.7629 | 0.7646 | 0.0018 | 5 | 0 | 0.0625 |
| i (aggregate, additional) | false_alarm | no_transit | all | 2800 | 0.0018 | 0.0000 | -0.0018 | 0 | 5 | 0.0625 |
| ii (aggregate, additional) | refuted | planet | all | 1500 | 0.9380 | 0.9287 | -0.0093 | 0 | 14 | 0.0001221 |
| ii (aggregate, additional) | flagged_identity | false_positive | all | 900 | 0.5467 | 0.5467 | 0.0000 | 0 | 0 | 1 |
| ii (aggregate, additional) | flagged_old | false_positive | all | 900 | 0.7844 | 0.7844 | 0.0000 | 0 | 0 | 1 |
| ii (aggregate, additional) | inconclusive | planet | all | 1500 | 0.0620 | 0.0713 | 0.0093 | 14 | 0 | 0.0001221 |
| ii (aggregate, additional) | inconclusive | false_positive | all | 900 | 0.0311 | 0.0411 | 0.0100 | 9 | 0 | 0.003906 |

## Paired comparisons M2 -> M3

| Condition | Outcome | Group | n | before | after | difference | up | down | McNemar p |
|---|---|---|---|---|---|---|---|---|---|
| i | refuted | planet | correlated|below | 250 | 0.4240 | 0.4240 | 0.0000 | 0 | 0 | 1 |
| i | refuted | planet | correlated|measurable | 250 | 0.1760 | 0.1760 | 0.0000 | 0 | 0 | 1 |
| i | refuted | planet | correlated|near | 250 | 0.3640 | 0.3640 | 0.0000 | 0 | 0 | 1 |
| i | refuted | planet | white|below | 250 | 0.4560 | 0.4560 | 0.0000 | 0 | 0 | 1 |
| i | refuted | planet | white|measurable | 250 | 0.2320 | 0.2320 | 0.0000 | 0 | 0 | 1 |
| i | refuted | planet | white|near | 250 | 0.4680 | 0.4680 | 0.0000 | 0 | 0 | 1 |
| i | flagged_identity | false_positive | correlated|below | 100 | 0.3200 | 0.3200 | 0.0000 | 0 | 0 | 1 |
| i | flagged_identity | false_positive | correlated|measurable | 250 | 0.7040 | 0.7040 | 0.0000 | 0 | 0 | 1 |
| i | flagged_identity | false_positive | correlated|near | 100 | 0.5000 | 0.5000 | 0.0000 | 0 | 0 | 1 |
| i | flagged_identity | false_positive | white|below | 100 | 0.2800 | 0.2800 | 0.0000 | 0 | 0 | 1 |
| i | flagged_identity | false_positive | white|measurable | 250 | 0.6440 | 0.6440 | 0.0000 | 0 | 0 | 1 |
| i | flagged_identity | false_positive | white|near | 100 | 0.4500 | 0.4500 | 0.0000 | 0 | 0 | 1 |
| i | flagged_old | false_positive | correlated|below | 100 | 0.5900 | 0.5900 | 0.0000 | 0 | 0 | 1 |
| i | flagged_old | false_positive | correlated|measurable | 250 | 0.9000 | 0.9000 | 0.0000 | 0 | 0 | 1 |
| i | flagged_old | false_positive | correlated|near | 100 | 0.7300 | 0.7300 | 0.0000 | 0 | 0 | 1 |
| i | flagged_old | false_positive | white|below | 100 | 0.5700 | 0.5700 | 0.0000 | 0 | 0 | 1 |
| i | flagged_old | false_positive | white|measurable | 250 | 0.8880 | 0.8880 | 0.0000 | 0 | 0 | 1 |
| i | flagged_old | false_positive | white|near | 100 | 0.7000 | 0.7000 | 0.0000 | 0 | 0 | 1 |
| i | inconclusive | planet | correlated|below | 250 | 0.4880 | 0.4880 | 0.0000 | 0 | 0 | 1 |
| i | inconclusive | planet | correlated|measurable | 250 | 0.0160 | 0.0160 | 0.0000 | 0 | 0 | 1 |
| i | inconclusive | planet | correlated|near | 250 | 0.2720 | 0.2720 | 0.0000 | 0 | 0 | 1 |
| i | inconclusive | planet | white|below | 250 | 0.5440 | 0.5440 | 0.0000 | 0 | 0 | 1 |
| i | inconclusive | planet | white|measurable | 250 | 0.2440 | 0.2440 | 0.0000 | 0 | 0 | 1 |
| i | inconclusive | planet | white|near | 250 | 0.4640 | 0.4640 | 0.0000 | 0 | 0 | 1 |
| i | inconclusive | false_positive | correlated|below | 100 | 0.4100 | 0.4100 | 0.0000 | 0 | 0 | 1 |
| i | inconclusive | false_positive | correlated|measurable | 250 | 0.0840 | 0.0840 | 0.0000 | 0 | 0 | 1 |
| i | inconclusive | false_positive | correlated|near | 100 | 0.2600 | 0.2600 | 0.0000 | 0 | 0 | 1 |
| i | inconclusive | false_positive | white|below | 100 | 0.4300 | 0.4300 | 0.0000 | 0 | 0 | 1 |
| i | inconclusive | false_positive | white|measurable | 250 | 0.1120 | 0.1120 | 0.0000 | 0 | 0 | 1 |
| i | inconclusive | false_positive | white|near | 100 | 0.2900 | 0.2900 | 0.0000 | 0 | 0 | 1 |
| i | inconclusive | no_transit | correlated|none | 600 | 0.5467 | 0.5467 | 0.0000 | 0 | 0 | 1 |
| i | inconclusive | no_transit | white|none | 2200 | 0.8241 | 0.8241 | 0.0000 | 0 | 0 | 1 |
| i | false_alarm | no_transit | correlated|none | 600 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| i | false_alarm | no_transit | white|none | 2200 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii | refuted | planet | correlated|below | 250 | 0.9200 | 0.6200 | -0.3000 | 0 | 75 | 5.294e-23 |
| ii | refuted | planet | correlated|measurable | 250 | 1.0000 | 0.5040 | -0.4960 | 0 | 124 | 9.404e-38 |
| ii | refuted | planet | correlated|near | 250 | 0.9960 | 0.6240 | -0.3720 | 0 | 93 | 2.019e-28 |
| ii | refuted | planet | white|below | 250 | 0.6800 | 0.5440 | -0.1360 | 0 | 34 | 1.164e-10 |
| ii | refuted | planet | white|measurable | 250 | 0.9840 | 0.5440 | -0.4400 | 0 | 110 | 1.541e-33 |
| ii | refuted | planet | white|near | 250 | 0.9920 | 0.6800 | -0.3120 | 0 | 78 | 6.617e-24 |
| ii | flagged_identity | false_positive | correlated|below | 100 | 0.3200 | 0.3200 | 0.0000 | 0 | 0 | 1 |
| ii | flagged_identity | false_positive | correlated|measurable | 250 | 0.7040 | 0.7040 | 0.0000 | 0 | 0 | 1 |
| ii | flagged_identity | false_positive | correlated|near | 100 | 0.5000 | 0.5000 | 0.0000 | 0 | 0 | 1 |
| ii | flagged_identity | false_positive | white|below | 100 | 0.2800 | 0.2800 | 0.0000 | 0 | 0 | 1 |
| ii | flagged_identity | false_positive | white|measurable | 250 | 0.6440 | 0.6440 | 0.0000 | 0 | 0 | 1 |
| ii | flagged_identity | false_positive | white|near | 100 | 0.4500 | 0.4500 | 0.0000 | 0 | 0 | 1 |
| ii | flagged_old | false_positive | correlated|below | 100 | 0.5900 | 0.5900 | 0.0000 | 0 | 0 | 1 |
| ii | flagged_old | false_positive | correlated|measurable | 250 | 0.9000 | 0.9000 | 0.0000 | 0 | 0 | 1 |
| ii | flagged_old | false_positive | correlated|near | 100 | 0.7300 | 0.7300 | 0.0000 | 0 | 0 | 1 |
| ii | flagged_old | false_positive | white|below | 100 | 0.5700 | 0.5700 | 0.0000 | 0 | 0 | 1 |
| ii | flagged_old | false_positive | white|measurable | 250 | 0.8880 | 0.8880 | 0.0000 | 0 | 0 | 1 |
| ii | flagged_old | false_positive | white|near | 100 | 0.7000 | 0.7000 | 0.0000 | 0 | 0 | 1 |
| ii | inconclusive | planet | correlated|below | 250 | 0.0800 | 0.3240 | 0.2440 | 61 | 0 | 8.674e-19 |
| ii | inconclusive | planet | correlated|measurable | 250 | 0.0000 | 0.0120 | 0.0120 | 3 | 0 | 0.25 |
| ii | inconclusive | planet | correlated|near | 250 | 0.0040 | 0.1560 | 0.1520 | 38 | 0 | 7.276e-12 |
| ii | inconclusive | planet | white|below | 250 | 0.3200 | 0.4560 | 0.1360 | 34 | 0 | 1.164e-10 |
| ii | inconclusive | planet | white|measurable | 250 | 0.0160 | 0.1400 | 0.1240 | 31 | 0 | 9.313e-10 |
| ii | inconclusive | planet | white|near | 250 | 0.0080 | 0.2800 | 0.2720 | 68 | 0 | 6.776e-21 |
| ii | inconclusive | false_positive | correlated|below | 100 | 0.0600 | 0.2700 | 0.2100 | 21 | 0 | 9.537e-07 |
| ii | inconclusive | false_positive | correlated|measurable | 250 | 0.0520 | 0.0640 | 0.0120 | 3 | 0 | 0.25 |
| ii | inconclusive | false_positive | correlated|near | 100 | 0.0200 | 0.1300 | 0.1100 | 11 | 0 | 0.0009766 |
| ii | inconclusive | false_positive | white|below | 100 | 0.1400 | 0.3000 | 0.1600 | 16 | 0 | 3.052e-05 |
| ii | inconclusive | false_positive | white|measurable | 250 | 0.0080 | 0.0720 | 0.0640 | 16 | 0 | 3.052e-05 |
| ii | inconclusive | false_positive | white|near | 100 | 0.0000 | 0.1800 | 0.1800 | 18 | 0 | 7.629e-06 |
| ii by variant | refuted | planet | correlated|below|independent | 50 | 0.9200 | 0.9200 | 0.0000 | 0 | 0 | 1 |
| ii by variant | refuted | planet | correlated|below|neighbor | 50 | 0.9400 | 0.9400 | 0.0000 | 0 | 0 | 1 |
| ii by variant | refuted | planet | correlated|below|own | 150 | 0.9133 | 0.4133 | -0.5000 | 0 | 75 | 5.294e-23 |
| ii by variant | refuted | planet | correlated|measurable|independent | 50 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | refuted | planet | correlated|measurable|neighbor | 50 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | refuted | planet | correlated|measurable|own | 150 | 1.0000 | 0.1733 | -0.8267 | 0 | 124 | 9.404e-38 |
| ii by variant | refuted | planet | correlated|near|independent | 50 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | refuted | planet | correlated|near|neighbor | 50 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | refuted | planet | correlated|near|own | 150 | 0.9933 | 0.3733 | -0.6200 | 0 | 93 | 2.019e-28 |
| ii by variant | refuted | planet | white|below|independent | 50 | 0.6400 | 0.6400 | 0.0000 | 0 | 0 | 1 |
| ii by variant | refuted | planet | white|below|neighbor | 50 | 0.5800 | 0.5800 | 0.0000 | 0 | 0 | 1 |
| ii by variant | refuted | planet | white|below|own | 150 | 0.7267 | 0.5000 | -0.2267 | 0 | 34 | 1.164e-10 |
| ii by variant | refuted | planet | white|measurable|independent | 50 | 0.9800 | 0.9800 | 0.0000 | 0 | 0 | 1 |
| ii by variant | refuted | planet | white|measurable|neighbor | 50 | 0.9800 | 0.9800 | 0.0000 | 0 | 0 | 1 |
| ii by variant | refuted | planet | white|measurable|own | 150 | 0.9867 | 0.2533 | -0.7333 | 0 | 110 | 1.541e-33 |
| ii by variant | refuted | planet | white|near|independent | 50 | 0.9800 | 0.9800 | 0.0000 | 0 | 0 | 1 |
| ii by variant | refuted | planet | white|near|neighbor | 50 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | refuted | planet | white|near|own | 150 | 0.9933 | 0.4733 | -0.5200 | 0 | 78 | 6.617e-24 |
| ii by variant | flagged_identity | false_positive | correlated|below|independent | 20 | 0.2500 | 0.2500 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_identity | false_positive | correlated|below|neighbor | 20 | 0.4000 | 0.4000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_identity | false_positive | correlated|below|own | 60 | 0.3167 | 0.3167 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_identity | false_positive | correlated|measurable|independent | 50 | 0.7000 | 0.7000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_identity | false_positive | correlated|measurable|neighbor | 50 | 0.6600 | 0.6600 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_identity | false_positive | correlated|measurable|own | 150 | 0.7200 | 0.7200 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_identity | false_positive | correlated|near|independent | 20 | 0.5000 | 0.5000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_identity | false_positive | correlated|near|neighbor | 20 | 0.3000 | 0.3000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_identity | false_positive | correlated|near|own | 60 | 0.5667 | 0.5667 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_identity | false_positive | white|below|independent | 20 | 0.2000 | 0.2000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_identity | false_positive | white|below|neighbor | 20 | 0.3500 | 0.3500 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_identity | false_positive | white|below|own | 60 | 0.2833 | 0.2833 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_identity | false_positive | white|measurable|independent | 50 | 0.6000 | 0.6000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_identity | false_positive | white|measurable|neighbor | 50 | 0.6600 | 0.6600 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_identity | false_positive | white|measurable|own | 150 | 0.6533 | 0.6533 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_identity | false_positive | white|near|independent | 20 | 0.5000 | 0.5000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_identity | false_positive | white|near|neighbor | 20 | 0.4000 | 0.4000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_identity | false_positive | white|near|own | 60 | 0.4500 | 0.4500 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_old | false_positive | correlated|below|independent | 20 | 0.6000 | 0.6000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_old | false_positive | correlated|below|neighbor | 20 | 0.6000 | 0.6000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_old | false_positive | correlated|below|own | 60 | 0.5833 | 0.5833 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_old | false_positive | correlated|measurable|independent | 50 | 0.9200 | 0.9200 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_old | false_positive | correlated|measurable|neighbor | 50 | 0.8800 | 0.8800 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_old | false_positive | correlated|measurable|own | 150 | 0.9000 | 0.9000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_old | false_positive | correlated|near|independent | 20 | 0.7500 | 0.7500 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_old | false_positive | correlated|near|neighbor | 20 | 0.5500 | 0.5500 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_old | false_positive | correlated|near|own | 60 | 0.7833 | 0.7833 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_old | false_positive | white|below|independent | 20 | 0.5000 | 0.5000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_old | false_positive | white|below|neighbor | 20 | 0.6000 | 0.6000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_old | false_positive | white|below|own | 60 | 0.5833 | 0.5833 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_old | false_positive | white|measurable|independent | 50 | 0.8600 | 0.8600 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_old | false_positive | white|measurable|neighbor | 50 | 0.9200 | 0.9200 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_old | false_positive | white|measurable|own | 150 | 0.8867 | 0.8867 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_old | false_positive | white|near|independent | 20 | 0.7500 | 0.7500 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_old | false_positive | white|near|neighbor | 20 | 0.6500 | 0.6500 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_old | false_positive | white|near|own | 60 | 0.7000 | 0.7000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | planet | correlated|below|independent | 50 | 0.0800 | 0.0800 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | planet | correlated|below|neighbor | 50 | 0.0600 | 0.0600 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | planet | correlated|below|own | 150 | 0.0867 | 0.4933 | 0.4067 | 61 | 0 | 8.674e-19 |
| ii by variant | inconclusive | planet | correlated|measurable|independent | 50 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | planet | correlated|measurable|neighbor | 50 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | planet | correlated|measurable|own | 150 | 0.0000 | 0.0200 | 0.0200 | 3 | 0 | 0.25 |
| ii by variant | inconclusive | planet | correlated|near|independent | 50 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | planet | correlated|near|neighbor | 50 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | planet | correlated|near|own | 150 | 0.0067 | 0.2600 | 0.2533 | 38 | 0 | 7.276e-12 |
| ii by variant | inconclusive | planet | white|below|independent | 50 | 0.3600 | 0.3600 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | planet | white|below|neighbor | 50 | 0.4200 | 0.4200 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | planet | white|below|own | 150 | 0.2733 | 0.5000 | 0.2267 | 34 | 0 | 1.164e-10 |
| ii by variant | inconclusive | planet | white|measurable|independent | 50 | 0.0200 | 0.0200 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | planet | white|measurable|neighbor | 50 | 0.0200 | 0.0200 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | planet | white|measurable|own | 150 | 0.0133 | 0.2200 | 0.2067 | 31 | 0 | 9.313e-10 |
| ii by variant | inconclusive | planet | white|near|independent | 50 | 0.0200 | 0.0200 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | planet | white|near|neighbor | 50 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | planet | white|near|own | 150 | 0.0067 | 0.4600 | 0.4533 | 68 | 0 | 6.776e-21 |
| ii by variant | inconclusive | false_positive | correlated|below|independent | 20 | 0.0500 | 0.0500 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | false_positive | correlated|below|neighbor | 20 | 0.0500 | 0.0500 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | false_positive | correlated|below|own | 60 | 0.0667 | 0.4167 | 0.3500 | 21 | 0 | 9.537e-07 |
| ii by variant | inconclusive | false_positive | correlated|measurable|independent | 50 | 0.0400 | 0.0400 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | false_positive | correlated|measurable|neighbor | 50 | 0.0400 | 0.0400 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | false_positive | correlated|measurable|own | 150 | 0.0600 | 0.0800 | 0.0200 | 3 | 0 | 0.25 |
| ii by variant | inconclusive | false_positive | correlated|near|independent | 20 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | false_positive | correlated|near|neighbor | 20 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | false_positive | correlated|near|own | 60 | 0.0333 | 0.2167 | 0.1833 | 11 | 0 | 0.0009766 |
| ii by variant | inconclusive | false_positive | white|below|independent | 20 | 0.1000 | 0.1000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | false_positive | white|below|neighbor | 20 | 0.1500 | 0.1500 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | false_positive | white|below|own | 60 | 0.1500 | 0.4167 | 0.2667 | 16 | 0 | 3.052e-05 |
| ii by variant | inconclusive | false_positive | white|measurable|independent | 50 | 0.0200 | 0.0200 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | false_positive | white|measurable|neighbor | 50 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | false_positive | white|measurable|own | 150 | 0.0067 | 0.1133 | 0.1067 | 16 | 0 | 3.052e-05 |
| ii by variant | inconclusive | false_positive | white|near|independent | 20 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | false_positive | white|near|neighbor | 20 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | false_positive | white|near|own | 60 | 0.0000 | 0.3000 | 0.3000 | 18 | 0 | 7.629e-06 |
| i (aggregate, additional) | refuted | planet | all | 1500 | 0.3533 | 0.3533 | 0.0000 | 0 | 0 | 1 |
| i (aggregate, additional) | flagged_identity | false_positive | all | 900 | 0.5467 | 0.5467 | 0.0000 | 0 | 0 | 1 |
| i (aggregate, additional) | flagged_old | false_positive | all | 900 | 0.7844 | 0.7844 | 0.0000 | 0 | 0 | 1 |
| i (aggregate, additional) | inconclusive | planet | all | 1500 | 0.3380 | 0.3380 | 0.0000 | 0 | 0 | 1 |
| i (aggregate, additional) | inconclusive | false_positive | all | 900 | 0.2089 | 0.2089 | 0.0000 | 0 | 0 | 1 |
| i (aggregate, additional) | inconclusive | no_transit | all | 2800 | 0.7646 | 0.7646 | 0.0000 | 0 | 0 | 1 |
| i (aggregate, additional) | false_alarm | no_transit | all | 2800 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii (aggregate, additional) | refuted | planet | all | 1500 | 0.9287 | 0.5860 | -0.3427 | 0 | 514 | 3.729e-155 |
| ii (aggregate, additional) | flagged_identity | false_positive | all | 900 | 0.5467 | 0.5467 | 0.0000 | 0 | 0 | 1 |
| ii (aggregate, additional) | flagged_old | false_positive | all | 900 | 0.7844 | 0.7844 | 0.0000 | 0 | 0 | 1 |
| ii (aggregate, additional) | inconclusive | planet | all | 1500 | 0.0713 | 0.2280 | 0.1567 | 235 | 0 | 3.622e-71 |
| ii (aggregate, additional) | inconclusive | false_positive | all | 900 | 0.0411 | 0.1356 | 0.0944 | 85 | 0 | 5.17e-26 |
