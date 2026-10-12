# Population metrics (manifest.json)

Results checked against the orchestrate records: True.

Every point uses the fast plan of the test suite (section 7); false-alarm rates under the calibration plan could be higher. The SNR bands of blends use the expected SNR without the noise of the pixel data, which lowers the SNR of the analyzed light curve (Amendment 2, N2).

## M0 (f4798230f1bca607bcc0e98fe47711a26ec4ee59)

**Overall approval: FAILS.** The study is approved only if every criterion passes, C6 included. A rate can meet its limit while the study fails. Failed: C1 refuted planets, below, white, C1 refuted planets, near, white, C1 refuted planets, measurable, white, C2 flagged false positives, measurable, white, C3 INCONCLUSIVE, planet, measurable, white, C3 INCONCLUSIVE, false_positive, measurable, white, C4 false alarm, white, C5 planets refuted only by own-TIC eb_catalog, white, C1 refuted planets, below, correlated, C1 refuted planets, near, correlated, C1 refuted planets, measurable, correlated, C2 flagged false positives, measurable, correlated, C3 INCONCLUSIVE, planet, measurable, correlated, C3 INCONCLUSIVE, false_positive, measurable, correlated, C4 false alarm, correlated, C5 planets refuted only by own-TIC eb_catalog, correlated.

Result statuses (per condition): {'analyzed': 76}

| Criterion | k | n | rate | bound | passes |
|---|---|---|---|---|---|
| C1 refuted planets, below, white | 0 | 0 | - | - | False |
| C1 refuted planets, near, white | 2 | 4 | 0.5000 | 0.9024 | False |
| C1 refuted planets, measurable, white | 1 | 4 | 0.2500 | 0.7514 | False |
| C2 flagged false positives, measurable, white | 3 | 4 | 0.7500 | 0.2486 | False |
| C3 INCONCLUSIVE, planet, measurable, white | 0 | 4 | 0.0000 | 0.5271 | False |
| C3 INCONCLUSIVE, false_positive, measurable, white | 0 | 4 | 0.0000 | 0.5271 | False |
| C4 false alarm, white | 0 | 6 | 0.0000 | 0.3930 | False |
| C5 planets refuted only by own-TIC eb_catalog, white | 1 | 3 | - | - | False |
| C1 refuted planets, below, correlated | 0 | 0 | - | - | False |
| C1 refuted planets, near, correlated | 2 | 4 | 0.5000 | 0.9024 | False |
| C1 refuted planets, measurable, correlated | 1 | 4 | 0.2500 | 0.7514 | False |
| C2 flagged false positives, measurable, correlated | 3 | 4 | 0.7500 | 0.2486 | False |
| C3 INCONCLUSIVE, planet, measurable, correlated | 0 | 4 | 0.0000 | 0.5271 | False |
| C3 INCONCLUSIVE, false_positive, measurable, correlated | 0 | 4 | 0.0000 | 0.5271 | False |
| C4 false alarm, correlated | 0 | 6 | 0.0000 | 0.3930 | False |
| C5 planets refuted only by own-TIC eb_catalog, correlated | 2 | 2 | - | - | False |
| C6 analysis errors and missing results | 0 | - | - | - | True |

Families whose point estimate is worse than their limit:

| Condition | Family | Criterion | k / n | estimate | limit |
|---|---|---|---|---|---|
| i | false_positive|measurable|correlated|variability_masked | C2 (flagged_identity) | 0 / 1 | 0.0000 | 0.6 |
| i | false_positive|measurable|white|variability_masked | C2 (flagged_identity) | 0 / 1 | 0.0000 | 0.6 |
| i | planet|measurable|correlated|variability_some_years | C1 (refuted) | 1 / 1 | 1.0000 | 0.1 |
| i | planet|measurable|white|variability_some_years | C1 (refuted) | 1 / 1 | 1.0000 | 0.1 |
| i | planet|near|correlated|three_years | C1 (refuted) | 1 / 1 | 1.0000 | 0.1 |
| i | planet|near|correlated|variability_some_years | C1 (refuted) | 1 / 1 | 1.0000 | 0.1 |
| i | planet|near|white|three_years | C1 (refuted) | 1 / 1 | 1.0000 | 0.1 |
| i | planet|near|white|variability_some_years | C1 (refuted) | 1 / 1 | 1.0000 | 0.1 |
| ii | planet|measurable|correlated|three_years|own | C5 (refuted_only_by_eb_catalog) | 1 / 1 | 1.0000 | 0.0 |
| ii | planet|measurable|white|two_years|own | C5 (refuted_only_by_eb_catalog) | 1 / 1 | 1.0000 | 0.0 |
| ii | planet|near|correlated|few_train|own | C5 (refuted_only_by_eb_catalog) | 1 / 1 | 1.0000 | 0.0 |

Results by mechanism, condition (i):

| Family | n | refuted | inconclusive | false alarm | flagged (identity) | flagged (old) | refuted only by eb_catalog |
|---|---|---|---|---|---|---|---|
| false_positive|below|correlated|blend | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| false_positive|below|correlated|eb_odd_even | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| false_positive|below|correlated|eb_secondary | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| false_positive|below|correlated|variability_masked | 1 | 1 | 0 | 0 | 0 | 1 | 0 |
| false_positive|below|white|blend | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| false_positive|below|white|eb_odd_even | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| false_positive|below|white|eb_secondary | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| false_positive|below|white|variability_masked | 1 | 1 | 0 | 0 | 0 | 1 | 0 |
| false_positive|measurable|correlated|blend | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| false_positive|measurable|correlated|eb_odd_even | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| false_positive|measurable|correlated|eb_secondary | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| false_positive|measurable|correlated|variability_masked | 1 | 0 | 0 | 1 | 0 | 0 | 0 |
| false_positive|measurable|white|blend | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| false_positive|measurable|white|eb_odd_even | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| false_positive|measurable|white|eb_secondary | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| false_positive|measurable|white|variability_masked | 1 | 1 | 0 | 0 | 0 | 1 | 0 |
| no_transit|None|correlated|pure_noise | 2 | 0 | 2 | 0 | 0 | 0 | 0 |
| no_transit|None|correlated|trend | 2 | 0 | 2 | 0 | 0 | 0 | 0 |
| no_transit|None|correlated|trend_variability | 2 | 0 | 2 | 0 | 0 | 0 | 0 |
| no_transit|None|white|pure_noise | 2 | 0 | 2 | 0 | 0 | 0 | 0 |
| no_transit|None|white|trend | 2 | 0 | 2 | 0 | 0 | 0 | 0 |
| no_transit|None|white|trend_variability | 2 | 1 | 1 | 0 | 0 | 1 | 0 |
| planet|measurable|correlated|few_train | 1 | 0 | 0 | 1 | 0 | 0 | 0 |
| planet|measurable|correlated|three_years | 1 | 0 | 0 | 1 | 0 | 0 | 0 |
| planet|measurable|correlated|two_years | 1 | 0 | 0 | 1 | 0 | 0 | 0 |
| planet|measurable|correlated|variability_some_years | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| planet|measurable|white|few_train | 1 | 0 | 0 | 1 | 0 | 0 | 0 |
| planet|measurable|white|three_years | 1 | 0 | 0 | 1 | 0 | 0 | 0 |
| planet|measurable|white|two_years | 1 | 0 | 0 | 1 | 0 | 0 | 0 |
| planet|measurable|white|variability_some_years | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| planet|near|correlated|few_train | 1 | 0 | 0 | 1 | 0 | 0 | 0 |
| planet|near|correlated|three_years | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| planet|near|correlated|two_years | 1 | 0 | 0 | 1 | 0 | 0 | 0 |
| planet|near|correlated|variability_some_years | 1 | 1 | 0 | 0 | 0 | 1 | 0 |
| planet|near|white|few_train | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| planet|near|white|three_years | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| planet|near|white|two_years | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| planet|near|white|variability_some_years | 1 | 1 | 0 | 0 | 0 | 1 | 0 |

Results by mechanism, condition (ii):

| Family | n | refuted | inconclusive | false alarm | flagged (identity) | flagged (old) | refuted only by eb_catalog |
|---|---|---|---|---|---|---|---|
| false_positive|below|correlated|blend|independent | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| false_positive|below|correlated|eb_odd_even|own | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| false_positive|below|correlated|eb_secondary|neighbor | 1 | 1 | 0 | 0 | 0 | 0 | 1 |
| false_positive|below|correlated|variability_masked|neighbor | 1 | 1 | 0 | 0 | 0 | 1 | 0 |
| false_positive|below|white|blend|neighbor | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| false_positive|below|white|eb_odd_even|independent | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| false_positive|below|white|eb_secondary|own | 1 | 1 | 0 | 0 | 0 | 0 | 1 |
| false_positive|below|white|variability_masked|own | 1 | 1 | 0 | 0 | 0 | 1 | 0 |
| false_positive|measurable|correlated|blend|neighbor | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| false_positive|measurable|correlated|eb_odd_even|independent | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| false_positive|measurable|correlated|eb_secondary|own | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| false_positive|measurable|correlated|variability_masked|own | 1 | 0 | 0 | 1 | 0 | 0 | 0 |
| false_positive|measurable|white|blend|own | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| false_positive|measurable|white|eb_odd_even|neighbor | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| false_positive|measurable|white|eb_secondary|independent | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| false_positive|measurable|white|variability_masked|independent | 1 | 1 | 0 | 0 | 0 | 1 | 0 |
| planet|measurable|correlated|few_train|independent | 1 | 1 | 0 | 0 | 0 | 0 | 1 |
| planet|measurable|correlated|three_years|own | 1 | 1 | 0 | 0 | 0 | 0 | 1 |
| planet|measurable|correlated|two_years|neighbor | 1 | 1 | 0 | 0 | 0 | 0 | 1 |
| planet|measurable|correlated|variability_some_years|neighbor | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| planet|measurable|white|few_train|neighbor | 1 | 1 | 0 | 0 | 0 | 0 | 1 |
| planet|measurable|white|three_years|independent | 1 | 1 | 0 | 0 | 0 | 0 | 1 |
| planet|measurable|white|two_years|own | 1 | 1 | 0 | 0 | 0 | 0 | 1 |
| planet|measurable|white|variability_some_years|own | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| planet|near|correlated|few_train|own | 1 | 1 | 0 | 0 | 0 | 0 | 1 |
| planet|near|correlated|three_years|neighbor | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| planet|near|correlated|two_years|independent | 1 | 1 | 0 | 0 | 0 | 0 | 1 |
| planet|near|correlated|variability_some_years|independent | 1 | 1 | 0 | 0 | 0 | 1 | 0 |
| planet|near|white|few_train|independent | 1 | 1 | 0 | 0 | 0 | 0 | 1 |
| planet|near|white|three_years|own | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| planet|near|white|two_years|neighbor | 1 | 1 | 0 | 0 | 0 | 0 | 1 |
| planet|near|white|variability_some_years|neighbor | 1 | 1 | 0 | 0 | 0 | 1 | 0 |

Attempts refused before dispatch (no results): {'M0-f479823': [{'attempt': '20261012T042948288168Z-53388', 'results': 'none', 'reason': 'the point cannot be measured in this environment', 'installed_commit': '9d3f36947abdafba35eb657dd5e2e895f5ac14d3', 'point_requested': 'M0'}]}

## M1 (3217db72cae26bc809b62a5239ae6226344e7a26)

**Overall approval: FAILS.** The study is approved only if every criterion passes, C6 included. A rate can meet its limit while the study fails. Failed: C1 refuted planets, below, white, C1 refuted planets, near, white, C1 refuted planets, measurable, white, C2 flagged false positives, measurable, white, C3 INCONCLUSIVE, planet, measurable, white, C3 INCONCLUSIVE, false_positive, measurable, white, C4 false alarm, white, C5 planets refuted only by own-TIC eb_catalog, white, C1 refuted planets, below, correlated, C1 refuted planets, near, correlated, C1 refuted planets, measurable, correlated, C2 flagged false positives, measurable, correlated, C3 INCONCLUSIVE, planet, measurable, correlated, C3 INCONCLUSIVE, false_positive, measurable, correlated, C4 false alarm, correlated, C5 planets refuted only by own-TIC eb_catalog, correlated.

Result statuses (per condition): {'analyzed': 76}

| Criterion | k | n | rate | bound | passes |
|---|---|---|---|---|---|
| C1 refuted planets, below, white | 0 | 0 | - | - | False |
| C1 refuted planets, near, white | 2 | 4 | 0.5000 | 0.9024 | False |
| C1 refuted planets, measurable, white | 1 | 4 | 0.2500 | 0.7514 | False |
| C2 flagged false positives, measurable, white | 3 | 4 | 0.7500 | 0.2486 | False |
| C3 INCONCLUSIVE, planet, measurable, white | 0 | 4 | 0.0000 | 0.5271 | False |
| C3 INCONCLUSIVE, false_positive, measurable, white | 0 | 4 | 0.0000 | 0.5271 | False |
| C4 false alarm, white | 0 | 6 | 0.0000 | 0.3930 | False |
| C5 planets refuted only by own-TIC eb_catalog, white | 1 | 3 | - | - | False |
| C1 refuted planets, below, correlated | 0 | 0 | - | - | False |
| C1 refuted planets, near, correlated | 2 | 4 | 0.5000 | 0.9024 | False |
| C1 refuted planets, measurable, correlated | 1 | 4 | 0.2500 | 0.7514 | False |
| C2 flagged false positives, measurable, correlated | 3 | 4 | 0.7500 | 0.2486 | False |
| C3 INCONCLUSIVE, planet, measurable, correlated | 0 | 4 | 0.0000 | 0.5271 | False |
| C3 INCONCLUSIVE, false_positive, measurable, correlated | 0 | 4 | 0.0000 | 0.5271 | False |
| C4 false alarm, correlated | 0 | 6 | 0.0000 | 0.3930 | False |
| C5 planets refuted only by own-TIC eb_catalog, correlated | 2 | 2 | - | - | False |
| C6 analysis errors and missing results | 0 | - | - | - | True |

Families whose point estimate is worse than their limit:

| Condition | Family | Criterion | k / n | estimate | limit |
|---|---|---|---|---|---|
| i | false_positive|measurable|correlated|variability_masked | C2 (flagged_identity) | 0 / 1 | 0.0000 | 0.6 |
| i | false_positive|measurable|white|variability_masked | C2 (flagged_identity) | 0 / 1 | 0.0000 | 0.6 |
| i | planet|measurable|correlated|variability_some_years | C1 (refuted) | 1 / 1 | 1.0000 | 0.1 |
| i | planet|measurable|white|variability_some_years | C1 (refuted) | 1 / 1 | 1.0000 | 0.1 |
| i | planet|near|correlated|three_years | C1 (refuted) | 1 / 1 | 1.0000 | 0.1 |
| i | planet|near|correlated|variability_some_years | C1 (refuted) | 1 / 1 | 1.0000 | 0.1 |
| i | planet|near|white|three_years | C1 (refuted) | 1 / 1 | 1.0000 | 0.1 |
| i | planet|near|white|variability_some_years | C1 (refuted) | 1 / 1 | 1.0000 | 0.1 |
| ii | planet|measurable|correlated|three_years|own | C5 (refuted_only_by_eb_catalog) | 1 / 1 | 1.0000 | 0.0 |
| ii | planet|measurable|white|two_years|own | C5 (refuted_only_by_eb_catalog) | 1 / 1 | 1.0000 | 0.0 |
| ii | planet|near|correlated|few_train|own | C5 (refuted_only_by_eb_catalog) | 1 / 1 | 1.0000 | 0.0 |

Results by mechanism, condition (i):

| Family | n | refuted | inconclusive | false alarm | flagged (identity) | flagged (old) | refuted only by eb_catalog |
|---|---|---|---|---|---|---|---|
| false_positive|below|correlated|blend | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| false_positive|below|correlated|eb_odd_even | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| false_positive|below|correlated|eb_secondary | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| false_positive|below|correlated|variability_masked | 1 | 1 | 0 | 0 | 0 | 1 | 0 |
| false_positive|below|white|blend | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| false_positive|below|white|eb_odd_even | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| false_positive|below|white|eb_secondary | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| false_positive|below|white|variability_masked | 1 | 1 | 0 | 0 | 0 | 1 | 0 |
| false_positive|measurable|correlated|blend | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| false_positive|measurable|correlated|eb_odd_even | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| false_positive|measurable|correlated|eb_secondary | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| false_positive|measurable|correlated|variability_masked | 1 | 0 | 0 | 1 | 0 | 0 | 0 |
| false_positive|measurable|white|blend | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| false_positive|measurable|white|eb_odd_even | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| false_positive|measurable|white|eb_secondary | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| false_positive|measurable|white|variability_masked | 1 | 1 | 0 | 0 | 0 | 1 | 0 |
| no_transit|None|correlated|pure_noise | 2 | 0 | 2 | 0 | 0 | 0 | 0 |
| no_transit|None|correlated|trend | 2 | 0 | 2 | 0 | 0 | 0 | 0 |
| no_transit|None|correlated|trend_variability | 2 | 0 | 2 | 0 | 0 | 0 | 0 |
| no_transit|None|white|pure_noise | 2 | 0 | 2 | 0 | 0 | 0 | 0 |
| no_transit|None|white|trend | 2 | 0 | 2 | 0 | 0 | 0 | 0 |
| no_transit|None|white|trend_variability | 2 | 1 | 1 | 0 | 0 | 1 | 0 |
| planet|measurable|correlated|few_train | 1 | 0 | 0 | 1 | 0 | 0 | 0 |
| planet|measurable|correlated|three_years | 1 | 0 | 0 | 1 | 0 | 0 | 0 |
| planet|measurable|correlated|two_years | 1 | 0 | 0 | 1 | 0 | 0 | 0 |
| planet|measurable|correlated|variability_some_years | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| planet|measurable|white|few_train | 1 | 0 | 0 | 1 | 0 | 0 | 0 |
| planet|measurable|white|three_years | 1 | 0 | 0 | 1 | 0 | 0 | 0 |
| planet|measurable|white|two_years | 1 | 0 | 0 | 1 | 0 | 0 | 0 |
| planet|measurable|white|variability_some_years | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| planet|near|correlated|few_train | 1 | 0 | 0 | 1 | 0 | 0 | 0 |
| planet|near|correlated|three_years | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| planet|near|correlated|two_years | 1 | 0 | 0 | 1 | 0 | 0 | 0 |
| planet|near|correlated|variability_some_years | 1 | 1 | 0 | 0 | 0 | 1 | 0 |
| planet|near|white|few_train | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| planet|near|white|three_years | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| planet|near|white|two_years | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| planet|near|white|variability_some_years | 1 | 1 | 0 | 0 | 0 | 1 | 0 |

Results by mechanism, condition (ii):

| Family | n | refuted | inconclusive | false alarm | flagged (identity) | flagged (old) | refuted only by eb_catalog |
|---|---|---|---|---|---|---|---|
| false_positive|below|correlated|blend|independent | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| false_positive|below|correlated|eb_odd_even|own | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| false_positive|below|correlated|eb_secondary|neighbor | 1 | 1 | 0 | 0 | 0 | 0 | 1 |
| false_positive|below|correlated|variability_masked|neighbor | 1 | 1 | 0 | 0 | 0 | 1 | 0 |
| false_positive|below|white|blend|neighbor | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| false_positive|below|white|eb_odd_even|independent | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| false_positive|below|white|eb_secondary|own | 1 | 1 | 0 | 0 | 0 | 0 | 1 |
| false_positive|below|white|variability_masked|own | 1 | 1 | 0 | 0 | 0 | 1 | 0 |
| false_positive|measurable|correlated|blend|neighbor | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| false_positive|measurable|correlated|eb_odd_even|independent | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| false_positive|measurable|correlated|eb_secondary|own | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| false_positive|measurable|correlated|variability_masked|own | 1 | 0 | 0 | 1 | 0 | 0 | 0 |
| false_positive|measurable|white|blend|own | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| false_positive|measurable|white|eb_odd_even|neighbor | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| false_positive|measurable|white|eb_secondary|independent | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| false_positive|measurable|white|variability_masked|independent | 1 | 1 | 0 | 0 | 0 | 1 | 0 |
| planet|measurable|correlated|few_train|independent | 1 | 1 | 0 | 0 | 0 | 0 | 1 |
| planet|measurable|correlated|three_years|own | 1 | 1 | 0 | 0 | 0 | 0 | 1 |
| planet|measurable|correlated|two_years|neighbor | 1 | 1 | 0 | 0 | 0 | 0 | 1 |
| planet|measurable|correlated|variability_some_years|neighbor | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| planet|measurable|white|few_train|neighbor | 1 | 1 | 0 | 0 | 0 | 0 | 1 |
| planet|measurable|white|three_years|independent | 1 | 1 | 0 | 0 | 0 | 0 | 1 |
| planet|measurable|white|two_years|own | 1 | 1 | 0 | 0 | 0 | 0 | 1 |
| planet|measurable|white|variability_some_years|own | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| planet|near|correlated|few_train|own | 1 | 1 | 0 | 0 | 0 | 0 | 1 |
| planet|near|correlated|three_years|neighbor | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| planet|near|correlated|two_years|independent | 1 | 1 | 0 | 0 | 0 | 0 | 1 |
| planet|near|correlated|variability_some_years|independent | 1 | 1 | 0 | 0 | 0 | 1 | 0 |
| planet|near|white|few_train|independent | 1 | 1 | 0 | 0 | 0 | 0 | 1 |
| planet|near|white|three_years|own | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| planet|near|white|two_years|neighbor | 1 | 1 | 0 | 0 | 0 | 0 | 1 |
| planet|near|white|variability_some_years|neighbor | 1 | 1 | 0 | 0 | 0 | 1 | 0 |

Attempts refused before dispatch (no results): none

## M2 (78d79f5b4495ab7cf7bac5cd2907b25b78c74540)

**Overall approval: FAILS.** The study is approved only if every criterion passes, C6 included. A rate can meet its limit while the study fails. Failed: C1 refuted planets, below, white, C1 refuted planets, near, white, C1 refuted planets, measurable, white, C2 flagged false positives, measurable, white, C3 INCONCLUSIVE, planet, measurable, white, C3 INCONCLUSIVE, false_positive, measurable, white, C4 false alarm, white, C5 planets refuted only by own-TIC eb_catalog, white, C1 refuted planets, below, correlated, C1 refuted planets, near, correlated, C1 refuted planets, measurable, correlated, C2 flagged false positives, measurable, correlated, C3 INCONCLUSIVE, planet, measurable, correlated, C3 INCONCLUSIVE, false_positive, measurable, correlated, C4 false alarm, correlated, C5 planets refuted only by own-TIC eb_catalog, correlated.

Result statuses (per condition): {'analyzed': 76}

| Criterion | k | n | rate | bound | passes |
|---|---|---|---|---|---|
| C1 refuted planets, below, white | 0 | 0 | - | - | False |
| C1 refuted planets, near, white | 2 | 4 | 0.5000 | 0.9024 | False |
| C1 refuted planets, measurable, white | 1 | 4 | 0.2500 | 0.7514 | False |
| C2 flagged false positives, measurable, white | 3 | 4 | 0.7500 | 0.2486 | False |
| C3 INCONCLUSIVE, planet, measurable, white | 0 | 4 | 0.0000 | 0.5271 | False |
| C3 INCONCLUSIVE, false_positive, measurable, white | 0 | 4 | 0.0000 | 0.5271 | False |
| C4 false alarm, white | 0 | 6 | 0.0000 | 0.3930 | False |
| C5 planets refuted only by own-TIC eb_catalog, white | 1 | 3 | - | - | False |
| C1 refuted planets, below, correlated | 0 | 0 | - | - | False |
| C1 refuted planets, near, correlated | 2 | 4 | 0.5000 | 0.9024 | False |
| C1 refuted planets, measurable, correlated | 0 | 4 | 0.0000 | 0.5271 | False |
| C2 flagged false positives, measurable, correlated | 3 | 4 | 0.7500 | 0.2486 | False |
| C3 INCONCLUSIVE, planet, measurable, correlated | 0 | 4 | 0.0000 | 0.5271 | False |
| C3 INCONCLUSIVE, false_positive, measurable, correlated | 1 | 4 | 0.2500 | 0.7514 | False |
| C4 false alarm, correlated | 0 | 6 | 0.0000 | 0.3930 | False |
| C5 planets refuted only by own-TIC eb_catalog, correlated | 2 | 2 | - | - | False |
| C6 analysis errors and missing results | 0 | - | - | - | True |

Families whose point estimate is worse than their limit:

| Condition | Family | Criterion | k / n | estimate | limit |
|---|---|---|---|---|---|
| i | false_positive|measurable|correlated|variability_masked | C2 (flagged_identity) | 0 / 1 | 0.0000 | 0.6 |
| i | false_positive|measurable|correlated|variability_masked | C3 (inconclusive) | 1 / 1 | 1.0000 | 0.2 |
| i | false_positive|measurable|white|variability_masked | C2 (flagged_identity) | 0 / 1 | 0.0000 | 0.6 |
| i | planet|measurable|white|variability_some_years | C1 (refuted) | 1 / 1 | 1.0000 | 0.1 |
| i | planet|near|correlated|three_years | C1 (refuted) | 1 / 1 | 1.0000 | 0.1 |
| i | planet|near|correlated|variability_some_years | C1 (refuted) | 1 / 1 | 1.0000 | 0.1 |
| i | planet|near|white|three_years | C1 (refuted) | 1 / 1 | 1.0000 | 0.1 |
| i | planet|near|white|variability_some_years | C1 (refuted) | 1 / 1 | 1.0000 | 0.1 |
| ii | planet|measurable|correlated|three_years|own | C5 (refuted_only_by_eb_catalog) | 1 / 1 | 1.0000 | 0.0 |
| ii | planet|measurable|white|two_years|own | C5 (refuted_only_by_eb_catalog) | 1 / 1 | 1.0000 | 0.0 |
| ii | planet|near|correlated|few_train|own | C5 (refuted_only_by_eb_catalog) | 1 / 1 | 1.0000 | 0.0 |

Results by mechanism, condition (i):

| Family | n | refuted | inconclusive | false alarm | flagged (identity) | flagged (old) | refuted only by eb_catalog |
|---|---|---|---|---|---|---|---|
| false_positive|below|correlated|blend | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| false_positive|below|correlated|eb_odd_even | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| false_positive|below|correlated|eb_secondary | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| false_positive|below|correlated|variability_masked | 1 | 1 | 0 | 0 | 0 | 1 | 0 |
| false_positive|below|white|blend | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| false_positive|below|white|eb_odd_even | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| false_positive|below|white|eb_secondary | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| false_positive|below|white|variability_masked | 1 | 1 | 0 | 0 | 0 | 1 | 0 |
| false_positive|measurable|correlated|blend | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| false_positive|measurable|correlated|eb_odd_even | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| false_positive|measurable|correlated|eb_secondary | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| false_positive|measurable|correlated|variability_masked | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| false_positive|measurable|white|blend | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| false_positive|measurable|white|eb_odd_even | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| false_positive|measurable|white|eb_secondary | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| false_positive|measurable|white|variability_masked | 1 | 1 | 0 | 0 | 0 | 1 | 0 |
| no_transit|None|correlated|pure_noise | 2 | 0 | 2 | 0 | 0 | 0 | 0 |
| no_transit|None|correlated|trend | 2 | 0 | 2 | 0 | 0 | 0 | 0 |
| no_transit|None|correlated|trend_variability | 2 | 0 | 2 | 0 | 0 | 0 | 0 |
| no_transit|None|white|pure_noise | 2 | 0 | 2 | 0 | 0 | 0 | 0 |
| no_transit|None|white|trend | 2 | 0 | 2 | 0 | 0 | 0 | 0 |
| no_transit|None|white|trend_variability | 2 | 1 | 1 | 0 | 0 | 1 | 0 |
| planet|measurable|correlated|few_train | 1 | 0 | 0 | 1 | 0 | 0 | 0 |
| planet|measurable|correlated|three_years | 1 | 0 | 0 | 1 | 0 | 0 | 0 |
| planet|measurable|correlated|two_years | 1 | 0 | 0 | 1 | 0 | 0 | 0 |
| planet|measurable|correlated|variability_some_years | 1 | 0 | 0 | 1 | 0 | 0 | 0 |
| planet|measurable|white|few_train | 1 | 0 | 0 | 1 | 0 | 0 | 0 |
| planet|measurable|white|three_years | 1 | 0 | 0 | 1 | 0 | 0 | 0 |
| planet|measurable|white|two_years | 1 | 0 | 0 | 1 | 0 | 0 | 0 |
| planet|measurable|white|variability_some_years | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| planet|near|correlated|few_train | 1 | 0 | 0 | 1 | 0 | 0 | 0 |
| planet|near|correlated|three_years | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| planet|near|correlated|two_years | 1 | 0 | 0 | 1 | 0 | 0 | 0 |
| planet|near|correlated|variability_some_years | 1 | 1 | 0 | 0 | 0 | 1 | 0 |
| planet|near|white|few_train | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| planet|near|white|three_years | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| planet|near|white|two_years | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| planet|near|white|variability_some_years | 1 | 1 | 0 | 0 | 0 | 1 | 0 |

Results by mechanism, condition (ii):

| Family | n | refuted | inconclusive | false alarm | flagged (identity) | flagged (old) | refuted only by eb_catalog |
|---|---|---|---|---|---|---|---|
| false_positive|below|correlated|blend|independent | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| false_positive|below|correlated|eb_odd_even|own | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| false_positive|below|correlated|eb_secondary|neighbor | 1 | 1 | 0 | 0 | 0 | 0 | 1 |
| false_positive|below|correlated|variability_masked|neighbor | 1 | 1 | 0 | 0 | 0 | 1 | 0 |
| false_positive|below|white|blend|neighbor | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| false_positive|below|white|eb_odd_even|independent | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| false_positive|below|white|eb_secondary|own | 1 | 1 | 0 | 0 | 0 | 0 | 1 |
| false_positive|below|white|variability_masked|own | 1 | 1 | 0 | 0 | 0 | 1 | 0 |
| false_positive|measurable|correlated|blend|neighbor | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| false_positive|measurable|correlated|eb_odd_even|independent | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| false_positive|measurable|correlated|eb_secondary|own | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| false_positive|measurable|correlated|variability_masked|own | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| false_positive|measurable|white|blend|own | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| false_positive|measurable|white|eb_odd_even|neighbor | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| false_positive|measurable|white|eb_secondary|independent | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| false_positive|measurable|white|variability_masked|independent | 1 | 1 | 0 | 0 | 0 | 1 | 0 |
| planet|measurable|correlated|few_train|independent | 1 | 1 | 0 | 0 | 0 | 0 | 1 |
| planet|measurable|correlated|three_years|own | 1 | 1 | 0 | 0 | 0 | 0 | 1 |
| planet|measurable|correlated|two_years|neighbor | 1 | 1 | 0 | 0 | 0 | 0 | 1 |
| planet|measurable|correlated|variability_some_years|neighbor | 1 | 1 | 0 | 0 | 0 | 0 | 1 |
| planet|measurable|white|few_train|neighbor | 1 | 1 | 0 | 0 | 0 | 0 | 1 |
| planet|measurable|white|three_years|independent | 1 | 1 | 0 | 0 | 0 | 0 | 1 |
| planet|measurable|white|two_years|own | 1 | 1 | 0 | 0 | 0 | 0 | 1 |
| planet|measurable|white|variability_some_years|own | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| planet|near|correlated|few_train|own | 1 | 1 | 0 | 0 | 0 | 0 | 1 |
| planet|near|correlated|three_years|neighbor | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| planet|near|correlated|two_years|independent | 1 | 1 | 0 | 0 | 0 | 0 | 1 |
| planet|near|correlated|variability_some_years|independent | 1 | 1 | 0 | 0 | 0 | 1 | 0 |
| planet|near|white|few_train|independent | 1 | 1 | 0 | 0 | 0 | 0 | 1 |
| planet|near|white|three_years|own | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| planet|near|white|two_years|neighbor | 1 | 1 | 0 | 0 | 0 | 0 | 1 |
| planet|near|white|variability_some_years|neighbor | 1 | 1 | 0 | 0 | 0 | 1 | 0 |

Attempts refused before dispatch (no results): none

## M3 (9d3f36947abdafba35eb657dd5e2e895f5ac14d3)

**Overall approval: FAILS.** The study is approved only if every criterion passes, C6 included. A rate can meet its limit while the study fails. Failed: C1 refuted planets, below, white, C1 refuted planets, near, white, C1 refuted planets, measurable, white, C2 flagged false positives, measurable, white, C3 INCONCLUSIVE, planet, measurable, white, C3 INCONCLUSIVE, false_positive, measurable, white, C4 false alarm, white, C1 refuted planets, below, correlated, C1 refuted planets, near, correlated, C1 refuted planets, measurable, correlated, C2 flagged false positives, measurable, correlated, C3 INCONCLUSIVE, planet, measurable, correlated, C3 INCONCLUSIVE, false_positive, measurable, correlated, C4 false alarm, correlated.

Result statuses (per condition): {'analyzed': 76}

| Criterion | k | n | rate | bound | passes |
|---|---|---|---|---|---|
| C1 refuted planets, below, white | 0 | 0 | - | - | False |
| C1 refuted planets, near, white | 2 | 4 | 0.5000 | 0.9024 | False |
| C1 refuted planets, measurable, white | 1 | 4 | 0.2500 | 0.7514 | False |
| C2 flagged false positives, measurable, white | 3 | 4 | 0.7500 | 0.2486 | False |
| C3 INCONCLUSIVE, planet, measurable, white | 0 | 4 | 0.0000 | 0.5271 | False |
| C3 INCONCLUSIVE, false_positive, measurable, white | 0 | 4 | 0.0000 | 0.5271 | False |
| C4 false alarm, white | 0 | 6 | 0.0000 | 0.3930 | False |
| C5 planets refuted only by own-TIC eb_catalog, white | 0 | 3 | - | - | True |
| C1 refuted planets, below, correlated | 0 | 0 | - | - | False |
| C1 refuted planets, near, correlated | 2 | 4 | 0.5000 | 0.9024 | False |
| C1 refuted planets, measurable, correlated | 0 | 4 | 0.0000 | 0.5271 | False |
| C2 flagged false positives, measurable, correlated | 3 | 4 | 0.7500 | 0.2486 | False |
| C3 INCONCLUSIVE, planet, measurable, correlated | 0 | 4 | 0.0000 | 0.5271 | False |
| C3 INCONCLUSIVE, false_positive, measurable, correlated | 1 | 4 | 0.2500 | 0.7514 | False |
| C4 false alarm, correlated | 0 | 6 | 0.0000 | 0.3930 | False |
| C5 planets refuted only by own-TIC eb_catalog, correlated | 0 | 2 | - | - | True |
| C6 analysis errors and missing results | 0 | - | - | - | True |

Families whose point estimate is worse than their limit:

| Condition | Family | Criterion | k / n | estimate | limit |
|---|---|---|---|---|---|
| i | false_positive|measurable|correlated|variability_masked | C2 (flagged_identity) | 0 / 1 | 0.0000 | 0.6 |
| i | false_positive|measurable|correlated|variability_masked | C3 (inconclusive) | 1 / 1 | 1.0000 | 0.2 |
| i | false_positive|measurable|white|variability_masked | C2 (flagged_identity) | 0 / 1 | 0.0000 | 0.6 |
| i | planet|measurable|white|variability_some_years | C1 (refuted) | 1 / 1 | 1.0000 | 0.1 |
| i | planet|near|correlated|three_years | C1 (refuted) | 1 / 1 | 1.0000 | 0.1 |
| i | planet|near|correlated|variability_some_years | C1 (refuted) | 1 / 1 | 1.0000 | 0.1 |
| i | planet|near|white|three_years | C1 (refuted) | 1 / 1 | 1.0000 | 0.1 |
| i | planet|near|white|variability_some_years | C1 (refuted) | 1 / 1 | 1.0000 | 0.1 |

Results by mechanism, condition (i):

| Family | n | refuted | inconclusive | false alarm | flagged (identity) | flagged (old) | refuted only by eb_catalog |
|---|---|---|---|---|---|---|---|
| false_positive|below|correlated|blend | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| false_positive|below|correlated|eb_odd_even | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| false_positive|below|correlated|eb_secondary | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| false_positive|below|correlated|variability_masked | 1 | 1 | 0 | 0 | 0 | 1 | 0 |
| false_positive|below|white|blend | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| false_positive|below|white|eb_odd_even | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| false_positive|below|white|eb_secondary | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| false_positive|below|white|variability_masked | 1 | 1 | 0 | 0 | 0 | 1 | 0 |
| false_positive|measurable|correlated|blend | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| false_positive|measurable|correlated|eb_odd_even | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| false_positive|measurable|correlated|eb_secondary | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| false_positive|measurable|correlated|variability_masked | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| false_positive|measurable|white|blend | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| false_positive|measurable|white|eb_odd_even | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| false_positive|measurable|white|eb_secondary | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| false_positive|measurable|white|variability_masked | 1 | 1 | 0 | 0 | 0 | 1 | 0 |
| no_transit|None|correlated|pure_noise | 2 | 0 | 2 | 0 | 0 | 0 | 0 |
| no_transit|None|correlated|trend | 2 | 0 | 2 | 0 | 0 | 0 | 0 |
| no_transit|None|correlated|trend_variability | 2 | 0 | 2 | 0 | 0 | 0 | 0 |
| no_transit|None|white|pure_noise | 2 | 0 | 2 | 0 | 0 | 0 | 0 |
| no_transit|None|white|trend | 2 | 0 | 2 | 0 | 0 | 0 | 0 |
| no_transit|None|white|trend_variability | 2 | 1 | 1 | 0 | 0 | 1 | 0 |
| planet|measurable|correlated|few_train | 1 | 0 | 0 | 1 | 0 | 0 | 0 |
| planet|measurable|correlated|three_years | 1 | 0 | 0 | 1 | 0 | 0 | 0 |
| planet|measurable|correlated|two_years | 1 | 0 | 0 | 1 | 0 | 0 | 0 |
| planet|measurable|correlated|variability_some_years | 1 | 0 | 0 | 1 | 0 | 0 | 0 |
| planet|measurable|white|few_train | 1 | 0 | 0 | 1 | 0 | 0 | 0 |
| planet|measurable|white|three_years | 1 | 0 | 0 | 1 | 0 | 0 | 0 |
| planet|measurable|white|two_years | 1 | 0 | 0 | 1 | 0 | 0 | 0 |
| planet|measurable|white|variability_some_years | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| planet|near|correlated|few_train | 1 | 0 | 0 | 1 | 0 | 0 | 0 |
| planet|near|correlated|three_years | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| planet|near|correlated|two_years | 1 | 0 | 0 | 1 | 0 | 0 | 0 |
| planet|near|correlated|variability_some_years | 1 | 1 | 0 | 0 | 0 | 1 | 0 |
| planet|near|white|few_train | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| planet|near|white|three_years | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| planet|near|white|two_years | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| planet|near|white|variability_some_years | 1 | 1 | 0 | 0 | 0 | 1 | 0 |

Results by mechanism, condition (ii):

| Family | n | refuted | inconclusive | false alarm | flagged (identity) | flagged (old) | refuted only by eb_catalog |
|---|---|---|---|---|---|---|---|
| false_positive|below|correlated|blend|independent | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| false_positive|below|correlated|eb_odd_even|own | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| false_positive|below|correlated|eb_secondary|neighbor | 1 | 1 | 0 | 0 | 0 | 0 | 1 |
| false_positive|below|correlated|variability_masked|neighbor | 1 | 1 | 0 | 0 | 0 | 1 | 0 |
| false_positive|below|white|blend|neighbor | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| false_positive|below|white|eb_odd_even|independent | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| false_positive|below|white|eb_secondary|own | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| false_positive|below|white|variability_masked|own | 1 | 1 | 0 | 0 | 0 | 1 | 0 |
| false_positive|measurable|correlated|blend|neighbor | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| false_positive|measurable|correlated|eb_odd_even|independent | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| false_positive|measurable|correlated|eb_secondary|own | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| false_positive|measurable|correlated|variability_masked|own | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| false_positive|measurable|white|blend|own | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| false_positive|measurable|white|eb_odd_even|neighbor | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| false_positive|measurable|white|eb_secondary|independent | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| false_positive|measurable|white|variability_masked|independent | 1 | 1 | 0 | 0 | 0 | 1 | 0 |
| planet|measurable|correlated|few_train|independent | 1 | 1 | 0 | 0 | 0 | 0 | 1 |
| planet|measurable|correlated|three_years|own | 1 | 0 | 0 | 1 | 0 | 0 | 0 |
| planet|measurable|correlated|two_years|neighbor | 1 | 1 | 0 | 0 | 0 | 0 | 1 |
| planet|measurable|correlated|variability_some_years|neighbor | 1 | 1 | 0 | 0 | 0 | 0 | 1 |
| planet|measurable|white|few_train|neighbor | 1 | 1 | 0 | 0 | 0 | 0 | 1 |
| planet|measurable|white|three_years|independent | 1 | 1 | 0 | 0 | 0 | 0 | 1 |
| planet|measurable|white|two_years|own | 1 | 0 | 0 | 1 | 0 | 0 | 0 |
| planet|measurable|white|variability_some_years|own | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| planet|near|correlated|few_train|own | 1 | 0 | 0 | 1 | 0 | 0 | 0 |
| planet|near|correlated|three_years|neighbor | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| planet|near|correlated|two_years|independent | 1 | 1 | 0 | 0 | 0 | 0 | 1 |
| planet|near|correlated|variability_some_years|independent | 1 | 1 | 0 | 0 | 0 | 1 | 0 |
| planet|near|white|few_train|independent | 1 | 1 | 0 | 0 | 0 | 0 | 1 |
| planet|near|white|three_years|own | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| planet|near|white|two_years|neighbor | 1 | 1 | 0 | 0 | 0 | 0 | 1 |
| planet|near|white|variability_some_years|neighbor | 1 | 1 | 0 | 0 | 0 | 1 | 0 |

Attempts refused before dispatch (no results): none

## Redraws by class, band and mechanism

| Family | cases | redrawn | redraws |
|---|---|---|---|
| false_positive|below|blend | 2 | 0 | {} |
| false_positive|below|eb_odd_even | 2 | 0 | {} |
| false_positive|below|eb_secondary | 2 | 0 | {} |
| false_positive|below|variability_masked | 2 | 0 | {} |
| false_positive|measurable|blend | 2 | 0 | {} |
| false_positive|measurable|eb_odd_even | 2 | 0 | {} |
| false_positive|measurable|eb_secondary | 2 | 0 | {} |
| false_positive|measurable|variability_masked | 2 | 0 | {} |
| no_transit|none|pure_noise | 4 | 0 | {} |
| no_transit|none|trend | 4 | 0 | {} |
| no_transit|none|trend_variability | 4 | 0 | {} |
| planet|measurable|few_train | 2 | 1 | {'train_transit_count': 4} |
| planet|measurable|three_years | 2 | 0 | {} |
| planet|measurable|two_years | 2 | 0 | {} |
| planet|measurable|variability_some_years | 2 | 0 | {} |
| planet|near|few_train | 2 | 1 | {'train_transit_count': 5} |
| planet|near|three_years | 2 | 0 | {} |
| planet|near|two_years | 2 | 0 | {} |
| planet|near|variability_some_years | 2 | 0 | {} |

## Paired comparisons M0 -> M1

| Condition | Outcome | Group | n | before | after | difference | up | down | McNemar p |
|---|---|---|---|---|---|---|---|---|---|
| i | refuted | planet | correlated|measurable | 4 | 0.2500 | 0.2500 | 0.0000 | 0 | 0 | 1 |
| i | refuted | planet | correlated|near | 4 | 0.5000 | 0.5000 | 0.0000 | 0 | 0 | 1 |
| i | refuted | planet | white|measurable | 4 | 0.2500 | 0.2500 | 0.0000 | 0 | 0 | 1 |
| i | refuted | planet | white|near | 4 | 0.5000 | 0.5000 | 0.0000 | 0 | 0 | 1 |
| i | flagged_identity | false_positive | correlated|below | 4 | 0.2500 | 0.2500 | 0.0000 | 0 | 0 | 1 |
| i | flagged_identity | false_positive | correlated|measurable | 4 | 0.7500 | 0.7500 | 0.0000 | 0 | 0 | 1 |
| i | flagged_identity | false_positive | white|below | 4 | 0.2500 | 0.2500 | 0.0000 | 0 | 0 | 1 |
| i | flagged_identity | false_positive | white|measurable | 4 | 0.7500 | 0.7500 | 0.0000 | 0 | 0 | 1 |
| i | flagged_old | false_positive | correlated|below | 4 | 0.5000 | 0.5000 | 0.0000 | 0 | 0 | 1 |
| i | flagged_old | false_positive | correlated|measurable | 4 | 0.7500 | 0.7500 | 0.0000 | 0 | 0 | 1 |
| i | flagged_old | false_positive | white|below | 4 | 0.5000 | 0.5000 | 0.0000 | 0 | 0 | 1 |
| i | flagged_old | false_positive | white|measurable | 4 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| i | inconclusive | planet | correlated|measurable | 4 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| i | inconclusive | planet | correlated|near | 4 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| i | inconclusive | planet | white|measurable | 4 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| i | inconclusive | planet | white|near | 4 | 0.5000 | 0.5000 | 0.0000 | 0 | 0 | 1 |
| i | inconclusive | false_positive | correlated|below | 4 | 0.5000 | 0.5000 | 0.0000 | 0 | 0 | 1 |
| i | inconclusive | false_positive | correlated|measurable | 4 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| i | inconclusive | false_positive | white|below | 4 | 0.5000 | 0.5000 | 0.0000 | 0 | 0 | 1 |
| i | inconclusive | false_positive | white|measurable | 4 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| i | inconclusive | no_transit | correlated|none | 6 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| i | inconclusive | no_transit | white|none | 6 | 0.8333 | 0.8333 | 0.0000 | 0 | 0 | 1 |
| i | false_alarm | no_transit | correlated|none | 6 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| i | false_alarm | no_transit | white|none | 6 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii | refuted | planet | correlated|measurable | 4 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii | refuted | planet | correlated|near | 4 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii | refuted | planet | white|measurable | 4 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii | refuted | planet | white|near | 4 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii | flagged_identity | false_positive | correlated|below | 4 | 0.2500 | 0.2500 | 0.0000 | 0 | 0 | 1 |
| ii | flagged_identity | false_positive | correlated|measurable | 4 | 0.7500 | 0.7500 | 0.0000 | 0 | 0 | 1 |
| ii | flagged_identity | false_positive | white|below | 4 | 0.2500 | 0.2500 | 0.0000 | 0 | 0 | 1 |
| ii | flagged_identity | false_positive | white|measurable | 4 | 0.7500 | 0.7500 | 0.0000 | 0 | 0 | 1 |
| ii | flagged_old | false_positive | correlated|below | 4 | 0.5000 | 0.5000 | 0.0000 | 0 | 0 | 1 |
| ii | flagged_old | false_positive | correlated|measurable | 4 | 0.7500 | 0.7500 | 0.0000 | 0 | 0 | 1 |
| ii | flagged_old | false_positive | white|below | 4 | 0.5000 | 0.5000 | 0.0000 | 0 | 0 | 1 |
| ii | flagged_old | false_positive | white|measurable | 4 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii | inconclusive | planet | correlated|measurable | 4 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii | inconclusive | planet | correlated|near | 4 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii | inconclusive | planet | white|measurable | 4 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii | inconclusive | planet | white|near | 4 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii | inconclusive | false_positive | correlated|below | 4 | 0.2500 | 0.2500 | 0.0000 | 0 | 0 | 1 |
| ii | inconclusive | false_positive | correlated|measurable | 4 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii | inconclusive | false_positive | white|below | 4 | 0.2500 | 0.2500 | 0.0000 | 0 | 0 | 1 |
| ii | inconclusive | false_positive | white|measurable | 4 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | refuted | planet | correlated|measurable|independent | 1 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | refuted | planet | correlated|measurable|neighbor | 2 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | refuted | planet | correlated|measurable|own | 1 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | refuted | planet | correlated|near|independent | 2 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | refuted | planet | correlated|near|neighbor | 1 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | refuted | planet | correlated|near|own | 1 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | refuted | planet | white|measurable|independent | 1 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | refuted | planet | white|measurable|neighbor | 1 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | refuted | planet | white|measurable|own | 2 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | refuted | planet | white|near|independent | 1 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | refuted | planet | white|near|neighbor | 2 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | refuted | planet | white|near|own | 1 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_identity | false_positive | correlated|below|independent | 1 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_identity | false_positive | correlated|below|neighbor | 2 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_identity | false_positive | correlated|below|own | 1 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_identity | false_positive | correlated|measurable|independent | 1 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_identity | false_positive | correlated|measurable|neighbor | 1 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_identity | false_positive | correlated|measurable|own | 2 | 0.5000 | 0.5000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_identity | false_positive | white|below|independent | 1 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_identity | false_positive | white|below|neighbor | 1 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_identity | false_positive | white|below|own | 2 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_identity | false_positive | white|measurable|independent | 2 | 0.5000 | 0.5000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_identity | false_positive | white|measurable|neighbor | 1 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_identity | false_positive | white|measurable|own | 1 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_old | false_positive | correlated|below|independent | 1 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_old | false_positive | correlated|below|neighbor | 2 | 0.5000 | 0.5000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_old | false_positive | correlated|below|own | 1 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_old | false_positive | correlated|measurable|independent | 1 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_old | false_positive | correlated|measurable|neighbor | 1 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_old | false_positive | correlated|measurable|own | 2 | 0.5000 | 0.5000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_old | false_positive | white|below|independent | 1 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_old | false_positive | white|below|neighbor | 1 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_old | false_positive | white|below|own | 2 | 0.5000 | 0.5000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_old | false_positive | white|measurable|independent | 2 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_old | false_positive | white|measurable|neighbor | 1 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_old | false_positive | white|measurable|own | 1 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | planet | correlated|measurable|independent | 1 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | planet | correlated|measurable|neighbor | 2 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | planet | correlated|measurable|own | 1 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | planet | correlated|near|independent | 2 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | planet | correlated|near|neighbor | 1 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | planet | correlated|near|own | 1 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | planet | white|measurable|independent | 1 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | planet | white|measurable|neighbor | 1 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | planet | white|measurable|own | 2 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | planet | white|near|independent | 1 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | planet | white|near|neighbor | 2 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | planet | white|near|own | 1 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | false_positive | correlated|below|independent | 1 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | false_positive | correlated|below|neighbor | 2 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | false_positive | correlated|below|own | 1 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | false_positive | correlated|measurable|independent | 1 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | false_positive | correlated|measurable|neighbor | 1 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | false_positive | correlated|measurable|own | 2 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | false_positive | white|below|independent | 1 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | false_positive | white|below|neighbor | 1 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | false_positive | white|below|own | 2 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | false_positive | white|measurable|independent | 2 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | false_positive | white|measurable|neighbor | 1 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | false_positive | white|measurable|own | 1 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| i (aggregate, additional) | refuted | planet | all | 16 | 0.3750 | 0.3750 | 0.0000 | 0 | 0 | 1 |
| i (aggregate, additional) | flagged_identity | false_positive | all | 16 | 0.5000 | 0.5000 | 0.0000 | 0 | 0 | 1 |
| i (aggregate, additional) | flagged_old | false_positive | all | 16 | 0.6875 | 0.6875 | 0.0000 | 0 | 0 | 1 |
| i (aggregate, additional) | inconclusive | planet | all | 16 | 0.1250 | 0.1250 | 0.0000 | 0 | 0 | 1 |
| i (aggregate, additional) | inconclusive | false_positive | all | 16 | 0.2500 | 0.2500 | 0.0000 | 0 | 0 | 1 |
| i (aggregate, additional) | inconclusive | no_transit | all | 12 | 0.9167 | 0.9167 | 0.0000 | 0 | 0 | 1 |
| i (aggregate, additional) | false_alarm | no_transit | all | 12 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii (aggregate, additional) | refuted | planet | all | 16 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii (aggregate, additional) | flagged_identity | false_positive | all | 16 | 0.5000 | 0.5000 | 0.0000 | 0 | 0 | 1 |
| ii (aggregate, additional) | flagged_old | false_positive | all | 16 | 0.6875 | 0.6875 | 0.0000 | 0 | 0 | 1 |
| ii (aggregate, additional) | inconclusive | planet | all | 16 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii (aggregate, additional) | inconclusive | false_positive | all | 16 | 0.1250 | 0.1250 | 0.0000 | 0 | 0 | 1 |

## Paired comparisons M1 -> M2

| Condition | Outcome | Group | n | before | after | difference | up | down | McNemar p |
|---|---|---|---|---|---|---|---|---|---|
| i | refuted | planet | correlated|measurable | 4 | 0.2500 | 0.0000 | -0.2500 | 0 | 1 | 1 |
| i | refuted | planet | correlated|near | 4 | 0.5000 | 0.5000 | 0.0000 | 0 | 0 | 1 |
| i | refuted | planet | white|measurable | 4 | 0.2500 | 0.2500 | 0.0000 | 0 | 0 | 1 |
| i | refuted | planet | white|near | 4 | 0.5000 | 0.5000 | 0.0000 | 0 | 0 | 1 |
| i | flagged_identity | false_positive | correlated|below | 4 | 0.2500 | 0.2500 | 0.0000 | 0 | 0 | 1 |
| i | flagged_identity | false_positive | correlated|measurable | 4 | 0.7500 | 0.7500 | 0.0000 | 0 | 0 | 1 |
| i | flagged_identity | false_positive | white|below | 4 | 0.2500 | 0.2500 | 0.0000 | 0 | 0 | 1 |
| i | flagged_identity | false_positive | white|measurable | 4 | 0.7500 | 0.7500 | 0.0000 | 0 | 0 | 1 |
| i | flagged_old | false_positive | correlated|below | 4 | 0.5000 | 0.5000 | 0.0000 | 0 | 0 | 1 |
| i | flagged_old | false_positive | correlated|measurable | 4 | 0.7500 | 0.7500 | 0.0000 | 0 | 0 | 1 |
| i | flagged_old | false_positive | white|below | 4 | 0.5000 | 0.5000 | 0.0000 | 0 | 0 | 1 |
| i | flagged_old | false_positive | white|measurable | 4 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| i | inconclusive | planet | correlated|measurable | 4 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| i | inconclusive | planet | correlated|near | 4 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| i | inconclusive | planet | white|measurable | 4 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| i | inconclusive | planet | white|near | 4 | 0.5000 | 0.5000 | 0.0000 | 0 | 0 | 1 |
| i | inconclusive | false_positive | correlated|below | 4 | 0.5000 | 0.5000 | 0.0000 | 0 | 0 | 1 |
| i | inconclusive | false_positive | correlated|measurable | 4 | 0.0000 | 0.2500 | 0.2500 | 1 | 0 | 1 |
| i | inconclusive | false_positive | white|below | 4 | 0.5000 | 0.5000 | 0.0000 | 0 | 0 | 1 |
| i | inconclusive | false_positive | white|measurable | 4 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| i | inconclusive | no_transit | correlated|none | 6 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| i | inconclusive | no_transit | white|none | 6 | 0.8333 | 0.8333 | 0.0000 | 0 | 0 | 1 |
| i | false_alarm | no_transit | correlated|none | 6 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| i | false_alarm | no_transit | white|none | 6 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii | refuted | planet | correlated|measurable | 4 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii | refuted | planet | correlated|near | 4 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii | refuted | planet | white|measurable | 4 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii | refuted | planet | white|near | 4 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii | flagged_identity | false_positive | correlated|below | 4 | 0.2500 | 0.2500 | 0.0000 | 0 | 0 | 1 |
| ii | flagged_identity | false_positive | correlated|measurable | 4 | 0.7500 | 0.7500 | 0.0000 | 0 | 0 | 1 |
| ii | flagged_identity | false_positive | white|below | 4 | 0.2500 | 0.2500 | 0.0000 | 0 | 0 | 1 |
| ii | flagged_identity | false_positive | white|measurable | 4 | 0.7500 | 0.7500 | 0.0000 | 0 | 0 | 1 |
| ii | flagged_old | false_positive | correlated|below | 4 | 0.5000 | 0.5000 | 0.0000 | 0 | 0 | 1 |
| ii | flagged_old | false_positive | correlated|measurable | 4 | 0.7500 | 0.7500 | 0.0000 | 0 | 0 | 1 |
| ii | flagged_old | false_positive | white|below | 4 | 0.5000 | 0.5000 | 0.0000 | 0 | 0 | 1 |
| ii | flagged_old | false_positive | white|measurable | 4 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii | inconclusive | planet | correlated|measurable | 4 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii | inconclusive | planet | correlated|near | 4 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii | inconclusive | planet | white|measurable | 4 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii | inconclusive | planet | white|near | 4 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii | inconclusive | false_positive | correlated|below | 4 | 0.2500 | 0.2500 | 0.0000 | 0 | 0 | 1 |
| ii | inconclusive | false_positive | correlated|measurable | 4 | 0.0000 | 0.2500 | 0.2500 | 1 | 0 | 1 |
| ii | inconclusive | false_positive | white|below | 4 | 0.2500 | 0.2500 | 0.0000 | 0 | 0 | 1 |
| ii | inconclusive | false_positive | white|measurable | 4 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | refuted | planet | correlated|measurable|independent | 1 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | refuted | planet | correlated|measurable|neighbor | 2 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | refuted | planet | correlated|measurable|own | 1 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | refuted | planet | correlated|near|independent | 2 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | refuted | planet | correlated|near|neighbor | 1 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | refuted | planet | correlated|near|own | 1 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | refuted | planet | white|measurable|independent | 1 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | refuted | planet | white|measurable|neighbor | 1 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | refuted | planet | white|measurable|own | 2 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | refuted | planet | white|near|independent | 1 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | refuted | planet | white|near|neighbor | 2 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | refuted | planet | white|near|own | 1 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_identity | false_positive | correlated|below|independent | 1 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_identity | false_positive | correlated|below|neighbor | 2 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_identity | false_positive | correlated|below|own | 1 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_identity | false_positive | correlated|measurable|independent | 1 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_identity | false_positive | correlated|measurable|neighbor | 1 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_identity | false_positive | correlated|measurable|own | 2 | 0.5000 | 0.5000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_identity | false_positive | white|below|independent | 1 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_identity | false_positive | white|below|neighbor | 1 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_identity | false_positive | white|below|own | 2 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_identity | false_positive | white|measurable|independent | 2 | 0.5000 | 0.5000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_identity | false_positive | white|measurable|neighbor | 1 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_identity | false_positive | white|measurable|own | 1 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_old | false_positive | correlated|below|independent | 1 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_old | false_positive | correlated|below|neighbor | 2 | 0.5000 | 0.5000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_old | false_positive | correlated|below|own | 1 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_old | false_positive | correlated|measurable|independent | 1 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_old | false_positive | correlated|measurable|neighbor | 1 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_old | false_positive | correlated|measurable|own | 2 | 0.5000 | 0.5000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_old | false_positive | white|below|independent | 1 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_old | false_positive | white|below|neighbor | 1 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_old | false_positive | white|below|own | 2 | 0.5000 | 0.5000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_old | false_positive | white|measurable|independent | 2 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_old | false_positive | white|measurable|neighbor | 1 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_old | false_positive | white|measurable|own | 1 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | planet | correlated|measurable|independent | 1 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | planet | correlated|measurable|neighbor | 2 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | planet | correlated|measurable|own | 1 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | planet | correlated|near|independent | 2 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | planet | correlated|near|neighbor | 1 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | planet | correlated|near|own | 1 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | planet | white|measurable|independent | 1 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | planet | white|measurable|neighbor | 1 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | planet | white|measurable|own | 2 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | planet | white|near|independent | 1 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | planet | white|near|neighbor | 2 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | planet | white|near|own | 1 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | false_positive | correlated|below|independent | 1 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | false_positive | correlated|below|neighbor | 2 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | false_positive | correlated|below|own | 1 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | false_positive | correlated|measurable|independent | 1 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | false_positive | correlated|measurable|neighbor | 1 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | false_positive | correlated|measurable|own | 2 | 0.0000 | 0.5000 | 0.5000 | 1 | 0 | 1 |
| ii by variant | inconclusive | false_positive | white|below|independent | 1 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | false_positive | white|below|neighbor | 1 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | false_positive | white|below|own | 2 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | false_positive | white|measurable|independent | 2 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | false_positive | white|measurable|neighbor | 1 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | false_positive | white|measurable|own | 1 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| i (aggregate, additional) | refuted | planet | all | 16 | 0.3750 | 0.3125 | -0.0625 | 0 | 1 | 1 |
| i (aggregate, additional) | flagged_identity | false_positive | all | 16 | 0.5000 | 0.5000 | 0.0000 | 0 | 0 | 1 |
| i (aggregate, additional) | flagged_old | false_positive | all | 16 | 0.6875 | 0.6875 | 0.0000 | 0 | 0 | 1 |
| i (aggregate, additional) | inconclusive | planet | all | 16 | 0.1250 | 0.1250 | 0.0000 | 0 | 0 | 1 |
| i (aggregate, additional) | inconclusive | false_positive | all | 16 | 0.2500 | 0.3125 | 0.0625 | 1 | 0 | 1 |
| i (aggregate, additional) | inconclusive | no_transit | all | 12 | 0.9167 | 0.9167 | 0.0000 | 0 | 0 | 1 |
| i (aggregate, additional) | false_alarm | no_transit | all | 12 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii (aggregate, additional) | refuted | planet | all | 16 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii (aggregate, additional) | flagged_identity | false_positive | all | 16 | 0.5000 | 0.5000 | 0.0000 | 0 | 0 | 1 |
| ii (aggregate, additional) | flagged_old | false_positive | all | 16 | 0.6875 | 0.6875 | 0.0000 | 0 | 0 | 1 |
| ii (aggregate, additional) | inconclusive | planet | all | 16 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii (aggregate, additional) | inconclusive | false_positive | all | 16 | 0.1250 | 0.1875 | 0.0625 | 1 | 0 | 1 |

## Paired comparisons M2 -> M3

| Condition | Outcome | Group | n | before | after | difference | up | down | McNemar p |
|---|---|---|---|---|---|---|---|---|---|
| i | refuted | planet | correlated|measurable | 4 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| i | refuted | planet | correlated|near | 4 | 0.5000 | 0.5000 | 0.0000 | 0 | 0 | 1 |
| i | refuted | planet | white|measurable | 4 | 0.2500 | 0.2500 | 0.0000 | 0 | 0 | 1 |
| i | refuted | planet | white|near | 4 | 0.5000 | 0.5000 | 0.0000 | 0 | 0 | 1 |
| i | flagged_identity | false_positive | correlated|below | 4 | 0.2500 | 0.2500 | 0.0000 | 0 | 0 | 1 |
| i | flagged_identity | false_positive | correlated|measurable | 4 | 0.7500 | 0.7500 | 0.0000 | 0 | 0 | 1 |
| i | flagged_identity | false_positive | white|below | 4 | 0.2500 | 0.2500 | 0.0000 | 0 | 0 | 1 |
| i | flagged_identity | false_positive | white|measurable | 4 | 0.7500 | 0.7500 | 0.0000 | 0 | 0 | 1 |
| i | flagged_old | false_positive | correlated|below | 4 | 0.5000 | 0.5000 | 0.0000 | 0 | 0 | 1 |
| i | flagged_old | false_positive | correlated|measurable | 4 | 0.7500 | 0.7500 | 0.0000 | 0 | 0 | 1 |
| i | flagged_old | false_positive | white|below | 4 | 0.5000 | 0.5000 | 0.0000 | 0 | 0 | 1 |
| i | flagged_old | false_positive | white|measurable | 4 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| i | inconclusive | planet | correlated|measurable | 4 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| i | inconclusive | planet | correlated|near | 4 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| i | inconclusive | planet | white|measurable | 4 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| i | inconclusive | planet | white|near | 4 | 0.5000 | 0.5000 | 0.0000 | 0 | 0 | 1 |
| i | inconclusive | false_positive | correlated|below | 4 | 0.5000 | 0.5000 | 0.0000 | 0 | 0 | 1 |
| i | inconclusive | false_positive | correlated|measurable | 4 | 0.2500 | 0.2500 | 0.0000 | 0 | 0 | 1 |
| i | inconclusive | false_positive | white|below | 4 | 0.5000 | 0.5000 | 0.0000 | 0 | 0 | 1 |
| i | inconclusive | false_positive | white|measurable | 4 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| i | inconclusive | no_transit | correlated|none | 6 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| i | inconclusive | no_transit | white|none | 6 | 0.8333 | 0.8333 | 0.0000 | 0 | 0 | 1 |
| i | false_alarm | no_transit | correlated|none | 6 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| i | false_alarm | no_transit | white|none | 6 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii | refuted | planet | correlated|measurable | 4 | 1.0000 | 0.7500 | -0.2500 | 0 | 1 | 1 |
| ii | refuted | planet | correlated|near | 4 | 1.0000 | 0.7500 | -0.2500 | 0 | 1 | 1 |
| ii | refuted | planet | white|measurable | 4 | 1.0000 | 0.7500 | -0.2500 | 0 | 1 | 1 |
| ii | refuted | planet | white|near | 4 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii | flagged_identity | false_positive | correlated|below | 4 | 0.2500 | 0.2500 | 0.0000 | 0 | 0 | 1 |
| ii | flagged_identity | false_positive | correlated|measurable | 4 | 0.7500 | 0.7500 | 0.0000 | 0 | 0 | 1 |
| ii | flagged_identity | false_positive | white|below | 4 | 0.2500 | 0.2500 | 0.0000 | 0 | 0 | 1 |
| ii | flagged_identity | false_positive | white|measurable | 4 | 0.7500 | 0.7500 | 0.0000 | 0 | 0 | 1 |
| ii | flagged_old | false_positive | correlated|below | 4 | 0.5000 | 0.5000 | 0.0000 | 0 | 0 | 1 |
| ii | flagged_old | false_positive | correlated|measurable | 4 | 0.7500 | 0.7500 | 0.0000 | 0 | 0 | 1 |
| ii | flagged_old | false_positive | white|below | 4 | 0.5000 | 0.5000 | 0.0000 | 0 | 0 | 1 |
| ii | flagged_old | false_positive | white|measurable | 4 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii | inconclusive | planet | correlated|measurable | 4 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii | inconclusive | planet | correlated|near | 4 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii | inconclusive | planet | white|measurable | 4 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii | inconclusive | planet | white|near | 4 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii | inconclusive | false_positive | correlated|below | 4 | 0.2500 | 0.2500 | 0.0000 | 0 | 0 | 1 |
| ii | inconclusive | false_positive | correlated|measurable | 4 | 0.2500 | 0.2500 | 0.0000 | 0 | 0 | 1 |
| ii | inconclusive | false_positive | white|below | 4 | 0.2500 | 0.5000 | 0.2500 | 1 | 0 | 1 |
| ii | inconclusive | false_positive | white|measurable | 4 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | refuted | planet | correlated|measurable|independent | 1 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | refuted | planet | correlated|measurable|neighbor | 2 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | refuted | planet | correlated|measurable|own | 1 | 1.0000 | 0.0000 | -1.0000 | 0 | 1 | 1 |
| ii by variant | refuted | planet | correlated|near|independent | 2 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | refuted | planet | correlated|near|neighbor | 1 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | refuted | planet | correlated|near|own | 1 | 1.0000 | 0.0000 | -1.0000 | 0 | 1 | 1 |
| ii by variant | refuted | planet | white|measurable|independent | 1 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | refuted | planet | white|measurable|neighbor | 1 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | refuted | planet | white|measurable|own | 2 | 1.0000 | 0.5000 | -0.5000 | 0 | 1 | 1 |
| ii by variant | refuted | planet | white|near|independent | 1 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | refuted | planet | white|near|neighbor | 2 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | refuted | planet | white|near|own | 1 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_identity | false_positive | correlated|below|independent | 1 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_identity | false_positive | correlated|below|neighbor | 2 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_identity | false_positive | correlated|below|own | 1 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_identity | false_positive | correlated|measurable|independent | 1 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_identity | false_positive | correlated|measurable|neighbor | 1 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_identity | false_positive | correlated|measurable|own | 2 | 0.5000 | 0.5000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_identity | false_positive | white|below|independent | 1 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_identity | false_positive | white|below|neighbor | 1 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_identity | false_positive | white|below|own | 2 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_identity | false_positive | white|measurable|independent | 2 | 0.5000 | 0.5000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_identity | false_positive | white|measurable|neighbor | 1 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_identity | false_positive | white|measurable|own | 1 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_old | false_positive | correlated|below|independent | 1 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_old | false_positive | correlated|below|neighbor | 2 | 0.5000 | 0.5000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_old | false_positive | correlated|below|own | 1 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_old | false_positive | correlated|measurable|independent | 1 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_old | false_positive | correlated|measurable|neighbor | 1 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_old | false_positive | correlated|measurable|own | 2 | 0.5000 | 0.5000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_old | false_positive | white|below|independent | 1 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_old | false_positive | white|below|neighbor | 1 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_old | false_positive | white|below|own | 2 | 0.5000 | 0.5000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_old | false_positive | white|measurable|independent | 2 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_old | false_positive | white|measurable|neighbor | 1 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_old | false_positive | white|measurable|own | 1 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | planet | correlated|measurable|independent | 1 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | planet | correlated|measurable|neighbor | 2 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | planet | correlated|measurable|own | 1 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | planet | correlated|near|independent | 2 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | planet | correlated|near|neighbor | 1 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | planet | correlated|near|own | 1 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | planet | white|measurable|independent | 1 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | planet | white|measurable|neighbor | 1 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | planet | white|measurable|own | 2 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | planet | white|near|independent | 1 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | planet | white|near|neighbor | 2 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | planet | white|near|own | 1 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | false_positive | correlated|below|independent | 1 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | false_positive | correlated|below|neighbor | 2 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | false_positive | correlated|below|own | 1 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | false_positive | correlated|measurable|independent | 1 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | false_positive | correlated|measurable|neighbor | 1 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | false_positive | correlated|measurable|own | 2 | 0.5000 | 0.5000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | false_positive | white|below|independent | 1 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | false_positive | white|below|neighbor | 1 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | false_positive | white|below|own | 2 | 0.0000 | 0.5000 | 0.5000 | 1 | 0 | 1 |
| ii by variant | inconclusive | false_positive | white|measurable|independent | 2 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | false_positive | white|measurable|neighbor | 1 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | false_positive | white|measurable|own | 1 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| i (aggregate, additional) | refuted | planet | all | 16 | 0.3125 | 0.3125 | 0.0000 | 0 | 0 | 1 |
| i (aggregate, additional) | flagged_identity | false_positive | all | 16 | 0.5000 | 0.5000 | 0.0000 | 0 | 0 | 1 |
| i (aggregate, additional) | flagged_old | false_positive | all | 16 | 0.6875 | 0.6875 | 0.0000 | 0 | 0 | 1 |
| i (aggregate, additional) | inconclusive | planet | all | 16 | 0.1250 | 0.1250 | 0.0000 | 0 | 0 | 1 |
| i (aggregate, additional) | inconclusive | false_positive | all | 16 | 0.3125 | 0.3125 | 0.0000 | 0 | 0 | 1 |
| i (aggregate, additional) | inconclusive | no_transit | all | 12 | 0.9167 | 0.9167 | 0.0000 | 0 | 0 | 1 |
| i (aggregate, additional) | false_alarm | no_transit | all | 12 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii (aggregate, additional) | refuted | planet | all | 16 | 1.0000 | 0.8125 | -0.1875 | 0 | 3 | 0.25 |
| ii (aggregate, additional) | flagged_identity | false_positive | all | 16 | 0.5000 | 0.5000 | 0.0000 | 0 | 0 | 1 |
| ii (aggregate, additional) | flagged_old | false_positive | all | 16 | 0.6875 | 0.6875 | 0.0000 | 0 | 0 | 1 |
| ii (aggregate, additional) | inconclusive | planet | all | 16 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii (aggregate, additional) | inconclusive | false_positive | all | 16 | 0.1875 | 0.2500 | 0.0625 | 1 | 0 | 1 |
