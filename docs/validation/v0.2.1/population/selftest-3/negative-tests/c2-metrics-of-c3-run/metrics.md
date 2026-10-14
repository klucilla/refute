# Population metrics (manifest.json)

Results checked against the orchestrate records: False.

Every point uses the fast plan of the test suite (section 7); false-alarm rates under the calibration plan could be higher. The SNR bands of blends use the expected SNR without the noise of the pixel data, which lowers the SNR of the analyzed light curve (Amendment 2, N2).

## M2 (78d79f5b4495ab7cf7bac5cd2907b25b78c74540)

**Overall approval: FAILS.** The study is approved only if every criterion passes, C6 included. A rate can meet its limit while the study fails. Failed: C1 refuted planets, below, white, C1 refuted planets, near, white, C1 refuted planets, measurable, white, C2 flagged false positives, measurable, white, C3 INCONCLUSIVE, planet, measurable, white, C3 INCONCLUSIVE, false_positive, measurable, white, C4 false alarm, white, C5 planets refuted only by own-TIC eb_catalog, white, C1 refuted planets, below, correlated, C1 refuted planets, near, correlated, C1 refuted planets, measurable, correlated, C2 flagged false positives, measurable, correlated, C3 INCONCLUSIVE, planet, measurable, correlated, C3 INCONCLUSIVE, false_positive, measurable, correlated, C4 false alarm, correlated, C6 analysis errors and missing results.

Result statuses (per condition): {'missing': 73, 'analyzed': 3}

| Criterion | k | n | rate | bound | passes |
|---|---|---|---|---|---|
| C1 refuted planets, below, white | 0 | 0 | - | - | False |
| C1 refuted planets, near, white | 0 | 4 | 0.0000 | 0.5271 | False |
| C1 refuted planets, measurable, white | 0 | 4 | 0.0000 | 0.5271 | False |
| C2 flagged false positives, measurable, white | 0 | 4 | 0.0000 | 0.0000 | False |
| C3 INCONCLUSIVE, planet, measurable, white | 3 | 4 | 0.7500 | 0.9873 | False |
| C3 INCONCLUSIVE, false_positive, measurable, white | 4 | 4 | 1.0000 | 1.0000 | False |
| C4 false alarm, white | 0 | 6 | 0.0000 | 0.3930 | False |
| C5 planets refuted only by own-TIC eb_catalog, white | 1 | 3 | - | - | False |
| C1 refuted planets, below, correlated | 0 | 0 | - | - | False |
| C1 refuted planets, near, correlated | 0 | 4 | 0.0000 | 0.5271 | False |
| C1 refuted planets, measurable, correlated | 0 | 4 | 0.0000 | 0.5271 | False |
| C2 flagged false positives, measurable, correlated | 0 | 4 | 0.0000 | 0.0000 | False |
| C3 INCONCLUSIVE, planet, measurable, correlated | 4 | 4 | 1.0000 | 1.0000 | False |
| C3 INCONCLUSIVE, false_positive, measurable, correlated | 4 | 4 | 1.0000 | 1.0000 | False |
| C4 false alarm, correlated | 0 | 6 | 0.0000 | 0.3930 | False |
| C5 planets refuted only by own-TIC eb_catalog, correlated | 0 | 2 | - | - | True |
| C6 analysis errors and missing results | 42 | - | - | - | False |

Families whose point estimate is worse than their limit:

| Condition | Family | Criterion | k / n | estimate | limit |
|---|---|---|---|---|---|
| i | false_positive|measurable|correlated|eb_secondary | C2 (flagged_identity) | 0 / 1 | 0.0000 | 0.6 |
| i | false_positive|measurable|correlated|eb_secondary | C3 (inconclusive) | 1 / 1 | 1.0000 | 0.2 |
| i | false_positive|measurable|correlated|eb_odd_even | C2 (flagged_identity) | 0 / 1 | 0.0000 | 0.6 |
| i | false_positive|measurable|correlated|eb_odd_even | C3 (inconclusive) | 1 / 1 | 1.0000 | 0.2 |
| i | false_positive|measurable|correlated|blend | C2 (flagged_identity) | 0 / 1 | 0.0000 | 0.6 |
| i | false_positive|measurable|correlated|blend | C3 (inconclusive) | 1 / 1 | 1.0000 | 0.2 |
| i | false_positive|measurable|correlated|variability_masked | C2 (flagged_identity) | 0 / 1 | 0.0000 | 0.6 |
| i | false_positive|measurable|correlated|variability_masked | C3 (inconclusive) | 1 / 1 | 1.0000 | 0.2 |
| i | false_positive|measurable|white|eb_secondary | C2 (flagged_identity) | 0 / 1 | 0.0000 | 0.6 |
| i | false_positive|measurable|white|eb_secondary | C3 (inconclusive) | 1 / 1 | 1.0000 | 0.2 |
| i | false_positive|measurable|white|eb_odd_even | C2 (flagged_identity) | 0 / 1 | 0.0000 | 0.6 |
| i | false_positive|measurable|white|eb_odd_even | C3 (inconclusive) | 1 / 1 | 1.0000 | 0.2 |
| i | false_positive|measurable|white|blend | C2 (flagged_identity) | 0 / 1 | 0.0000 | 0.6 |
| i | false_positive|measurable|white|blend | C3 (inconclusive) | 1 / 1 | 1.0000 | 0.2 |
| i | false_positive|measurable|white|variability_masked | C2 (flagged_identity) | 0 / 1 | 0.0000 | 0.6 |
| i | false_positive|measurable|white|variability_masked | C3 (inconclusive) | 1 / 1 | 1.0000 | 0.2 |
| i | planet|measurable|correlated|two_years | C3 (inconclusive) | 1 / 1 | 1.0000 | 0.2 |
| i | planet|measurable|correlated|three_years | C3 (inconclusive) | 1 / 1 | 1.0000 | 0.2 |
| i | planet|measurable|correlated|few_train | C3 (inconclusive) | 1 / 1 | 1.0000 | 0.2 |
| i | planet|measurable|correlated|variability_some_years | C3 (inconclusive) | 1 / 1 | 1.0000 | 0.2 |
| i | planet|measurable|white|three_years | C3 (inconclusive) | 1 / 1 | 1.0000 | 0.2 |
| i | planet|measurable|white|few_train | C3 (inconclusive) | 1 / 1 | 1.0000 | 0.2 |
| i | planet|measurable|white|variability_some_years | C3 (inconclusive) | 1 / 1 | 1.0000 | 0.2 |
| ii | planet|measurable|white|two_years|own | C5 (refuted_only_by_eb_catalog) | 1 / 1 | 1.0000 | 0.0 |

Results by mechanism, condition (i):

| Family | n | refuted | inconclusive | false alarm | flagged (identity) | flagged (old) | refuted only by eb_catalog |
|---|---|---|---|---|---|---|---|
| false_positive|below|correlated|blend | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| false_positive|below|correlated|eb_odd_even | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| false_positive|below|correlated|eb_secondary | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| false_positive|below|correlated|variability_masked | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| false_positive|below|white|blend | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| false_positive|below|white|eb_odd_even | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| false_positive|below|white|eb_secondary | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| false_positive|below|white|variability_masked | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| false_positive|measurable|correlated|blend | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| false_positive|measurable|correlated|eb_odd_even | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| false_positive|measurable|correlated|eb_secondary | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| false_positive|measurable|correlated|variability_masked | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| false_positive|measurable|white|blend | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| false_positive|measurable|white|eb_odd_even | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| false_positive|measurable|white|eb_secondary | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| false_positive|measurable|white|variability_masked | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| no_transit|None|correlated|pure_noise | 2 | 0 | 2 | 0 | 0 | 0 | 0 |
| no_transit|None|correlated|trend | 2 | 0 | 2 | 0 | 0 | 0 | 0 |
| no_transit|None|correlated|trend_variability | 2 | 0 | 2 | 0 | 0 | 0 | 0 |
| no_transit|None|white|pure_noise | 2 | 0 | 2 | 0 | 0 | 0 | 0 |
| no_transit|None|white|trend | 2 | 0 | 2 | 0 | 0 | 0 | 0 |
| no_transit|None|white|trend_variability | 2 | 0 | 2 | 0 | 0 | 0 | 0 |
| planet|measurable|correlated|few_train | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| planet|measurable|correlated|three_years | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| planet|measurable|correlated|two_years | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| planet|measurable|correlated|variability_some_years | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| planet|measurable|white|few_train | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| planet|measurable|white|three_years | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| planet|measurable|white|two_years | 1 | 0 | 0 | 1 | 0 | 0 | 0 |
| planet|measurable|white|variability_some_years | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| planet|near|correlated|few_train | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| planet|near|correlated|three_years | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| planet|near|correlated|two_years | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| planet|near|correlated|variability_some_years | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| planet|near|white|few_train | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| planet|near|white|three_years | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| planet|near|white|two_years | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| planet|near|white|variability_some_years | 1 | 0 | 1 | 0 | 0 | 0 | 0 |

Results by mechanism, condition (ii):

| Family | n | refuted | inconclusive | false alarm | flagged (identity) | flagged (old) | refuted only by eb_catalog |
|---|---|---|---|---|---|---|---|
| false_positive|below|correlated|blend|independent | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| false_positive|below|correlated|eb_odd_even|own | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| false_positive|below|correlated|eb_secondary|neighbor | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| false_positive|below|correlated|variability_masked|neighbor | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| false_positive|below|white|blend|neighbor | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| false_positive|below|white|eb_odd_even|independent | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| false_positive|below|white|eb_secondary|own | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| false_positive|below|white|variability_masked|own | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| false_positive|measurable|correlated|blend|neighbor | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| false_positive|measurable|correlated|eb_odd_even|independent | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| false_positive|measurable|correlated|eb_secondary|own | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| false_positive|measurable|correlated|variability_masked|own | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| false_positive|measurable|white|blend|own | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| false_positive|measurable|white|eb_odd_even|neighbor | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| false_positive|measurable|white|eb_secondary|independent | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| false_positive|measurable|white|variability_masked|independent | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| planet|measurable|correlated|few_train|independent | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| planet|measurable|correlated|three_years|own | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| planet|measurable|correlated|two_years|neighbor | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| planet|measurable|correlated|variability_some_years|neighbor | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| planet|measurable|white|few_train|neighbor | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| planet|measurable|white|three_years|independent | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| planet|measurable|white|two_years|own | 1 | 1 | 0 | 0 | 0 | 0 | 1 |
| planet|measurable|white|variability_some_years|own | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| planet|near|correlated|few_train|own | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| planet|near|correlated|three_years|neighbor | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| planet|near|correlated|two_years|independent | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| planet|near|correlated|variability_some_years|independent | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| planet|near|white|few_train|independent | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| planet|near|white|three_years|own | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| planet|near|white|two_years|neighbor | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| planet|near|white|variability_some_years|neighbor | 1 | 0 | 1 | 0 | 0 | 0 | 0 |

Attempts refused before dispatch (no results): {'c3-missing-cache-M2': [{'attempt': '20261012T043034922453Z-40544', 'results': 'none', 'reason': 'inputs missing from the cache; no result written', 'installed_commit': '78d79f5b4495ab7cf7bac5cd2907b25b78c74540', 'point_requested': 'M2'}]}

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
