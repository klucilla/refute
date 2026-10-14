# Population metrics (manifest-6.json)

Results checked against the orchestrate records: False.

Every point uses the fast plan of the test suite (section 7); false-alarm rates under the calibration plan could be higher. The SNR bands of blends use the expected SNR without the noise of the pixel data, which lowers the SNR of the analyzed light curve (Amendment 2, N2).

## M0 (f4798230f1bca607bcc0e98fe47711a26ec4ee59)

**Overall approval: FAILS.** The study is approved only if every criterion passes, C6 included. A rate can meet its limit while the study fails. Failed: C1 refuted planets, below, white, C1 refuted planets, near, white, C1 refuted planets, measurable, white, C2 flagged false positives, measurable, white, C3 INCONCLUSIVE, planet, measurable, white, C3 INCONCLUSIVE, false_positive, measurable, white, C4 false alarm, white, C1 refuted planets, below, correlated, C1 refuted planets, near, correlated, C1 refuted planets, measurable, correlated, C2 flagged false positives, measurable, correlated, C3 INCONCLUSIVE, planet, measurable, correlated, C3 INCONCLUSIVE, false_positive, measurable, correlated, C4 false alarm, correlated.

Result statuses (per condition): {'analyzed': 10}

| Criterion | k | n | rate | bound | passes |
|---|---|---|---|---|---|
| C1 refuted planets, below, white | 0 | 0 | - | - | False |
| C1 refuted planets, near, white | 0 | 1 | 0.0000 | 0.9500 | False |
| C1 refuted planets, measurable, white | 0 | 1 | 0.0000 | 0.9500 | False |
| C2 flagged false positives, measurable, white | 1 | 1 | 1.0000 | 0.0500 | False |
| C3 INCONCLUSIVE, planet, measurable, white | 0 | 1 | 0.0000 | 0.9500 | False |
| C3 INCONCLUSIVE, false_positive, measurable, white | 0 | 1 | 0.0000 | 0.9500 | False |
| C4 false alarm, white | 0 | 1 | 0.0000 | 0.9500 | False |
| C5 planets refuted only by own-TIC eb_catalog, white | 0 | 0 | - | - | True |
| C1 refuted planets, below, correlated | 0 | 0 | - | - | False |
| C1 refuted planets, near, correlated | 0 | 0 | - | - | False |
| C1 refuted planets, measurable, correlated | 0 | 0 | - | - | False |
| C2 flagged false positives, measurable, correlated | 0 | 0 | - | - | False |
| C3 INCONCLUSIVE, planet, measurable, correlated | 0 | 0 | - | - | False |
| C3 INCONCLUSIVE, false_positive, measurable, correlated | 0 | 0 | - | - | False |
| C4 false alarm, correlated | 0 | 1 | 0.0000 | 0.9500 | False |
| C5 planets refuted only by own-TIC eb_catalog, correlated | 0 | 0 | - | - | True |
| C6 analysis errors and missing results | 0 | - | - | - | True |

Families whose point estimate is worse than their limit:

none

Results by mechanism, condition (i):

| Family | n | refuted | inconclusive | false alarm | flagged (identity) | flagged (old) | refuted only by eb_catalog |
|---|---|---|---|---|---|---|---|
| false_positive|below|white|eb_secondary | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| false_positive|measurable|white|blend | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| no_transit|None|correlated|trend | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| no_transit|None|white|pure_noise | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| planet|measurable|white|few_train | 1 | 0 | 0 | 1 | 0 | 0 | 0 |
| planet|near|white|few_train | 1 | 0 | 1 | 0 | 0 | 0 | 0 |

Results by mechanism, condition (ii):

| Family | n | refuted | inconclusive | false alarm | flagged (identity) | flagged (old) | refuted only by eb_catalog |
|---|---|---|---|---|---|---|---|
| false_positive|below|white|eb_secondary|own | 1 | 1 | 0 | 0 | 0 | 0 | 1 |
| false_positive|measurable|white|blend|own | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| planet|measurable|white|few_train|neighbor | 1 | 1 | 0 | 0 | 0 | 0 | 1 |
| planet|near|white|few_train|independent | 1 | 1 | 0 | 0 | 0 | 0 | 1 |

Attempts refused before dispatch (no results): none

## M3 (9d3f36947abdafba35eb657dd5e2e895f5ac14d3)

**Overall approval: FAILS.** The study is approved only if every criterion passes, C6 included. A rate can meet its limit while the study fails. Failed: C1 refuted planets, below, white, C1 refuted planets, near, white, C1 refuted planets, measurable, white, C2 flagged false positives, measurable, white, C3 INCONCLUSIVE, planet, measurable, white, C3 INCONCLUSIVE, false_positive, measurable, white, C4 false alarm, white, C1 refuted planets, below, correlated, C1 refuted planets, near, correlated, C1 refuted planets, measurable, correlated, C2 flagged false positives, measurable, correlated, C3 INCONCLUSIVE, planet, measurable, correlated, C3 INCONCLUSIVE, false_positive, measurable, correlated, C4 false alarm, correlated.

Result statuses (per condition): {'analyzed': 10}

| Criterion | k | n | rate | bound | passes |
|---|---|---|---|---|---|
| C1 refuted planets, below, white | 0 | 0 | - | - | False |
| C1 refuted planets, near, white | 0 | 1 | 0.0000 | 0.9500 | False |
| C1 refuted planets, measurable, white | 0 | 1 | 0.0000 | 0.9500 | False |
| C2 flagged false positives, measurable, white | 1 | 1 | 1.0000 | 0.0500 | False |
| C3 INCONCLUSIVE, planet, measurable, white | 0 | 1 | 0.0000 | 0.9500 | False |
| C3 INCONCLUSIVE, false_positive, measurable, white | 0 | 1 | 0.0000 | 0.9500 | False |
| C4 false alarm, white | 0 | 1 | 0.0000 | 0.9500 | False |
| C5 planets refuted only by own-TIC eb_catalog, white | 0 | 0 | - | - | True |
| C1 refuted planets, below, correlated | 0 | 0 | - | - | False |
| C1 refuted planets, near, correlated | 0 | 0 | - | - | False |
| C1 refuted planets, measurable, correlated | 0 | 0 | - | - | False |
| C2 flagged false positives, measurable, correlated | 0 | 0 | - | - | False |
| C3 INCONCLUSIVE, planet, measurable, correlated | 0 | 0 | - | - | False |
| C3 INCONCLUSIVE, false_positive, measurable, correlated | 0 | 0 | - | - | False |
| C4 false alarm, correlated | 0 | 1 | 0.0000 | 0.9500 | False |
| C5 planets refuted only by own-TIC eb_catalog, correlated | 0 | 0 | - | - | True |
| C6 analysis errors and missing results | 0 | - | - | - | True |

Families whose point estimate is worse than their limit:

none

Results by mechanism, condition (i):

| Family | n | refuted | inconclusive | false alarm | flagged (identity) | flagged (old) | refuted only by eb_catalog |
|---|---|---|---|---|---|---|---|
| false_positive|below|white|eb_secondary | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| false_positive|measurable|white|blend | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| no_transit|None|correlated|trend | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| no_transit|None|white|pure_noise | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| planet|measurable|white|few_train | 1 | 0 | 0 | 1 | 0 | 0 | 0 |
| planet|near|white|few_train | 1 | 0 | 1 | 0 | 0 | 0 | 0 |

Results by mechanism, condition (ii):

| Family | n | refuted | inconclusive | false alarm | flagged (identity) | flagged (old) | refuted only by eb_catalog |
|---|---|---|---|---|---|---|---|
| false_positive|below|white|eb_secondary|own | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| false_positive|measurable|white|blend|own | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| planet|measurable|white|few_train|neighbor | 1 | 1 | 0 | 0 | 0 | 0 | 1 |
| planet|near|white|few_train|independent | 1 | 1 | 0 | 0 | 0 | 0 | 1 |

Attempts refused before dispatch (no results): none

## Redraws by class, band and mechanism

| Family | cases | redrawn | redraws |
|---|---|---|---|
| false_positive|below|eb_secondary | 1 | 0 | {} |
| false_positive|measurable|blend | 1 | 0 | {} |
| no_transit|none|pure_noise | 1 | 0 | {} |
| no_transit|none|trend | 1 | 0 | {} |
| planet|measurable|few_train | 1 | 0 | {} |
| planet|near|few_train | 1 | 0 | {} |

## Paired comparisons M0 -> M3

| Condition | Outcome | Group | n | before | after | difference | up | down | McNemar p |
|---|---|---|---|---|---|---|---|---|---|
| i | refuted | planet | white|measurable | 1 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| i | refuted | planet | white|near | 1 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| i | flagged_identity | false_positive | white|below | 1 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| i | flagged_identity | false_positive | white|measurable | 1 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| i | flagged_old | false_positive | white|below | 1 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| i | flagged_old | false_positive | white|measurable | 1 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| i | inconclusive | planet | white|measurable | 1 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| i | inconclusive | planet | white|near | 1 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| i | inconclusive | false_positive | white|below | 1 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| i | inconclusive | false_positive | white|measurable | 1 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| i | inconclusive | no_transit | correlated|none | 1 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| i | inconclusive | no_transit | white|none | 1 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| i | false_alarm | no_transit | correlated|none | 1 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| i | false_alarm | no_transit | white|none | 1 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii | refuted | planet | white|measurable | 1 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii | refuted | planet | white|near | 1 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii | flagged_identity | false_positive | white|below | 1 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii | flagged_identity | false_positive | white|measurable | 1 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii | flagged_old | false_positive | white|below | 1 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii | flagged_old | false_positive | white|measurable | 1 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii | inconclusive | planet | white|measurable | 1 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii | inconclusive | planet | white|near | 1 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii | inconclusive | false_positive | white|below | 1 | 0.0000 | 1.0000 | 1.0000 | 1 | 0 | 1 |
| ii | inconclusive | false_positive | white|measurable | 1 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | refuted | planet | white|measurable|neighbor | 1 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | refuted | planet | white|near|independent | 1 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_identity | false_positive | white|below|own | 1 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_identity | false_positive | white|measurable|own | 1 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_old | false_positive | white|below|own | 1 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | flagged_old | false_positive | white|measurable|own | 1 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | planet | white|measurable|neighbor | 1 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | planet | white|near|independent | 1 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii by variant | inconclusive | false_positive | white|below|own | 1 | 0.0000 | 1.0000 | 1.0000 | 1 | 0 | 1 |
| ii by variant | inconclusive | false_positive | white|measurable|own | 1 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| i (aggregate, additional) | refuted | planet | all | 2 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| i (aggregate, additional) | flagged_identity | false_positive | all | 2 | 0.5000 | 0.5000 | 0.0000 | 0 | 0 | 1 |
| i (aggregate, additional) | flagged_old | false_positive | all | 2 | 0.5000 | 0.5000 | 0.0000 | 0 | 0 | 1 |
| i (aggregate, additional) | inconclusive | planet | all | 2 | 0.5000 | 0.5000 | 0.0000 | 0 | 0 | 1 |
| i (aggregate, additional) | inconclusive | false_positive | all | 2 | 0.5000 | 0.5000 | 0.0000 | 0 | 0 | 1 |
| i (aggregate, additional) | inconclusive | no_transit | all | 2 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| i (aggregate, additional) | false_alarm | no_transit | all | 2 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii (aggregate, additional) | refuted | planet | all | 2 | 1.0000 | 1.0000 | 0.0000 | 0 | 0 | 1 |
| ii (aggregate, additional) | flagged_identity | false_positive | all | 2 | 0.5000 | 0.5000 | 0.0000 | 0 | 0 | 1 |
| ii (aggregate, additional) | flagged_old | false_positive | all | 2 | 0.5000 | 0.5000 | 0.0000 | 0 | 0 | 1 |
| ii (aggregate, additional) | inconclusive | planet | all | 2 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1 |
| ii (aggregate, additional) | inconclusive | false_positive | all | 2 | 0.0000 | 0.5000 | 0.5000 | 1 | 0 | 1 |
