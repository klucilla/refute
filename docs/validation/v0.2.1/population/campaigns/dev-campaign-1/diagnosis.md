# Diagnosis of development campaign 1 (M0 and M3)

Read only: the frozen manifest (`../../manifest-dev.json`) and the result records of slot 1 (the two slots are identical: 208 recorded comparisons). Nothing was changed; no new analysis ran. Made by a local read-only script (not published); the result records are listed in `asset-SHA256SUMS`. What follows are counts and values read from the records; **hypotheses are marked as hypotheses**. The result of the campaign is FAILS and is not reinterpreted here. Translated from the maintainer's Portuguese diagnostic record.

Verdicts found in the records: M0: {'INCONCLUSIVE': 2790, 'REFUTED': 1940, 'WEAKENED': 37, 'SURVIVED': 433}, M3: {'INCONCLUSIVE': 2836, 'REFUTED': 1895, 'SURVIVED': 447, 'WEAKENED': 22}

Record statuses: M0: {'analyzed': 5200}, M3: {'analyzed': 5200}

## a) Verdicts by point, noise, band and family (condition i)

`flagged` = the verdict recomputed without `eb_catalog` is REFUTED **and** there is signal identity (the definition of C2), counted for every class as information.

### M0

| class | noise | band | family | n | REFUTED | WEAKENED | INCONCLUSIVE | SURVIVED | other | flagged |
|---|---|---|---|---|---|---|---|---|---|---|
| false_positive | correlated | below | blend | 25 | 22 | 0 | 3 | 0 | 0 | 21 |
| false_positive | correlated | below | eb_odd_even | 25 | 6 | 0 | 19 | 0 | 0 | 3 |
| false_positive | correlated | below | eb_secondary | 25 | 8 | 0 | 17 | 0 | 0 | 8 |
| false_positive | correlated | below | variability_masked | 25 | 23 | 2 | 0 | 0 | 0 | 0 |
| false_positive | correlated | measurable | blend | 62 | 62 | 0 | 0 | 0 | 0 | 62 |
| false_positive | correlated | measurable | eb_odd_even | 63 | 51 | 2 | 7 | 3 | 0 | 51 |
| false_positive | correlated | measurable | eb_secondary | 63 | 63 | 0 | 0 | 0 | 0 | 63 |
| false_positive | correlated | measurable | variability_masked | 62 | 49 | 5 | 8 | 0 | 0 | 0 |
| false_positive | correlated | near | blend | 25 | 25 | 0 | 0 | 0 | 0 | 25 |
| false_positive | correlated | near | eb_odd_even | 25 | 7 | 0 | 18 | 0 | 0 | 7 |
| false_positive | correlated | near | eb_secondary | 25 | 18 | 0 | 6 | 1 | 0 | 18 |
| false_positive | correlated | near | variability_masked | 25 | 23 | 0 | 2 | 0 | 0 | 0 |
| false_positive | white | below | blend | 25 | 18 | 0 | 7 | 0 | 0 | 16 |
| false_positive | white | below | eb_odd_even | 25 | 6 | 0 | 19 | 0 | 0 | 6 |
| false_positive | white | below | eb_secondary | 25 | 8 | 0 | 17 | 0 | 0 | 6 |
| false_positive | white | below | variability_masked | 25 | 25 | 0 | 0 | 0 | 0 | 0 |
| false_positive | white | measurable | blend | 62 | 62 | 0 | 0 | 0 | 0 | 61 |
| false_positive | white | measurable | eb_odd_even | 63 | 42 | 0 | 21 | 0 | 0 | 42 |
| false_positive | white | measurable | eb_secondary | 63 | 58 | 0 | 5 | 0 | 0 | 58 |
| false_positive | white | measurable | variability_masked | 62 | 60 | 2 | 0 | 0 | 0 | 0 |
| false_positive | white | near | blend | 25 | 25 | 0 | 0 | 0 | 0 | 25 |
| false_positive | white | near | eb_odd_even | 25 | 5 | 0 | 19 | 1 | 0 | 5 |
| false_positive | white | near | eb_secondary | 25 | 15 | 0 | 10 | 0 | 0 | 15 |
| false_positive | white | near | variability_masked | 25 | 25 | 0 | 0 | 0 | 0 | 0 |
| no_transit | correlated | None | pure_noise | 240 | 108 | 0 | 132 | 0 | 0 | 0 |
| no_transit | correlated | None | trend | 180 | 69 | 0 | 111 | 0 | 0 | 0 |
| no_transit | correlated | None | trend_variability | 180 | 95 | 0 | 85 | 0 | 0 | 0 |
| no_transit | white | None | pure_noise | 880 | 43 | 0 | 837 | 0 | 0 | 0 |
| no_transit | white | None | trend | 660 | 54 | 0 | 606 | 0 | 0 | 0 |
| no_transit | white | None | trend_variability | 660 | 290 | 5 | 365 | 0 | 0 | 0 |
| planet | correlated | below | few_train | 50 | 4 | 1 | 31 | 14 | 0 | 3 |
| planet | correlated | below | three_years | 50 | 48 | 0 | 1 | 1 | 0 | 26 |
| planet | correlated | below | two_years | 100 | 15 | 0 | 81 | 4 | 0 | 3 |
| planet | correlated | below | variability_some_years | 50 | 50 | 0 | 0 | 0 | 0 | 1 |
| planet | correlated | measurable | few_train | 50 | 3 | 2 | 1 | 44 | 0 | 3 |
| planet | correlated | measurable | three_years | 50 | 2 | 0 | 0 | 48 | 0 | 2 |
| planet | correlated | measurable | two_years | 100 | 1 | 2 | 3 | 94 | 0 | 1 |
| planet | correlated | measurable | variability_some_years | 50 | 50 | 0 | 0 | 0 | 0 | 45 |
| planet | correlated | near | few_train | 50 | 6 | 4 | 10 | 30 | 0 | 6 |
| planet | correlated | near | three_years | 50 | 32 | 2 | 0 | 16 | 0 | 32 |
| planet | correlated | near | two_years | 100 | 4 | 3 | 57 | 36 | 0 | 4 |
| planet | correlated | near | variability_some_years | 50 | 50 | 0 | 0 | 0 | 0 | 15 |
| planet | white | below | few_train | 50 | 26 | 0 | 23 | 1 | 0 | 22 |
| planet | white | below | three_years | 50 | 17 | 0 | 33 | 0 | 0 | 12 |
| planet | white | below | two_years | 100 | 28 | 0 | 72 | 0 | 0 | 25 |
| planet | white | below | variability_some_years | 50 | 50 | 0 | 0 | 0 | 0 | 0 |
| planet | white | measurable | few_train | 50 | 3 | 1 | 15 | 31 | 0 | 3 |
| planet | white | measurable | three_years | 50 | 4 | 2 | 0 | 44 | 0 | 4 |
| planet | white | measurable | two_years | 100 | 6 | 3 | 42 | 49 | 0 | 6 |
| planet | white | measurable | variability_some_years | 50 | 50 | 0 | 0 | 0 | 0 | 11 |
| planet | white | near | few_train | 50 | 13 | 1 | 32 | 4 | 0 | 13 |
| planet | white | near | three_years | 50 | 38 | 0 | 1 | 11 | 0 | 37 |
| planet | white | near | two_years | 100 | 25 | 0 | 74 | 1 | 0 | 24 |
| planet | white | near | variability_some_years | 50 | 50 | 0 | 0 | 0 | 0 | 0 |

### M3

| class | noise | band | family | n | REFUTED | WEAKENED | INCONCLUSIVE | SURVIVED | other | flagged |
|---|---|---|---|---|---|---|---|---|---|---|
| false_positive | correlated | below | blend | 25 | 22 | 0 | 3 | 0 | 0 | 21 |
| false_positive | correlated | below | eb_odd_even | 25 | 6 | 0 | 19 | 0 | 0 | 3 |
| false_positive | correlated | below | eb_secondary | 25 | 8 | 0 | 17 | 0 | 0 | 8 |
| false_positive | correlated | below | variability_masked | 25 | 23 | 0 | 2 | 0 | 0 | 0 |
| false_positive | correlated | measurable | blend | 62 | 62 | 0 | 0 | 0 | 0 | 62 |
| false_positive | correlated | measurable | eb_odd_even | 63 | 51 | 1 | 8 | 3 | 0 | 51 |
| false_positive | correlated | measurable | eb_secondary | 63 | 63 | 0 | 0 | 0 | 0 | 63 |
| false_positive | correlated | measurable | variability_masked | 62 | 49 | 0 | 13 | 0 | 0 | 0 |
| false_positive | correlated | near | blend | 25 | 25 | 0 | 0 | 0 | 0 | 25 |
| false_positive | correlated | near | eb_odd_even | 25 | 7 | 0 | 18 | 0 | 0 | 7 |
| false_positive | correlated | near | eb_secondary | 25 | 18 | 0 | 6 | 1 | 0 | 18 |
| false_positive | correlated | near | variability_masked | 25 | 23 | 0 | 2 | 0 | 0 | 0 |
| false_positive | white | below | blend | 25 | 18 | 0 | 7 | 0 | 0 | 16 |
| false_positive | white | below | eb_odd_even | 25 | 6 | 0 | 19 | 0 | 0 | 6 |
| false_positive | white | below | eb_secondary | 25 | 8 | 0 | 17 | 0 | 0 | 6 |
| false_positive | white | below | variability_masked | 25 | 25 | 0 | 0 | 0 | 0 | 0 |
| false_positive | white | measurable | blend | 62 | 62 | 0 | 0 | 0 | 0 | 61 |
| false_positive | white | measurable | eb_odd_even | 63 | 42 | 0 | 21 | 0 | 0 | 42 |
| false_positive | white | measurable | eb_secondary | 63 | 58 | 0 | 5 | 0 | 0 | 58 |
| false_positive | white | measurable | variability_masked | 62 | 60 | 0 | 2 | 0 | 0 | 0 |
| false_positive | white | near | blend | 25 | 25 | 0 | 0 | 0 | 0 | 25 |
| false_positive | white | near | eb_odd_even | 25 | 5 | 0 | 19 | 1 | 0 | 5 |
| false_positive | white | near | eb_secondary | 25 | 15 | 0 | 10 | 0 | 0 | 15 |
| false_positive | white | near | variability_masked | 25 | 25 | 0 | 0 | 0 | 0 | 0 |
| no_transit | correlated | None | pure_noise | 240 | 108 | 0 | 132 | 0 | 0 | 0 |
| no_transit | correlated | None | trend | 180 | 69 | 0 | 111 | 0 | 0 | 0 |
| no_transit | correlated | None | trend_variability | 180 | 95 | 0 | 85 | 0 | 0 | 0 |
| no_transit | white | None | pure_noise | 880 | 43 | 0 | 837 | 0 | 0 | 0 |
| no_transit | white | None | trend | 660 | 54 | 0 | 606 | 0 | 0 | 0 |
| no_transit | white | None | trend_variability | 660 | 290 | 0 | 370 | 0 | 0 | 0 |
| planet | correlated | below | few_train | 50 | 4 | 1 | 31 | 14 | 0 | 3 |
| planet | correlated | below | three_years | 50 | 43 | 0 | 4 | 3 | 0 | 23 |
| planet | correlated | below | two_years | 100 | 15 | 0 | 81 | 4 | 0 | 3 |
| planet | correlated | below | variability_some_years | 50 | 44 | 0 | 6 | 0 | 0 | 1 |
| planet | correlated | measurable | few_train | 50 | 3 | 2 | 1 | 44 | 0 | 3 |
| planet | correlated | measurable | three_years | 50 | 2 | 0 | 0 | 48 | 0 | 2 |
| planet | correlated | measurable | two_years | 100 | 1 | 2 | 3 | 94 | 0 | 1 |
| planet | correlated | measurable | variability_some_years | 50 | 38 | 0 | 0 | 12 | 0 | 33 |
| planet | correlated | near | few_train | 50 | 6 | 4 | 10 | 30 | 0 | 6 |
| planet | correlated | near | three_years | 50 | 32 | 2 | 0 | 16 | 0 | 32 |
| planet | correlated | near | two_years | 100 | 4 | 3 | 57 | 36 | 0 | 4 |
| planet | correlated | near | variability_some_years | 50 | 49 | 0 | 1 | 0 | 0 | 15 |
| planet | white | below | few_train | 50 | 24 | 0 | 26 | 0 | 0 | 20 |
| planet | white | below | three_years | 50 | 12 | 0 | 38 | 0 | 0 | 7 |
| planet | white | below | two_years | 100 | 28 | 0 | 72 | 0 | 0 | 25 |
| planet | white | below | variability_some_years | 50 | 50 | 0 | 0 | 0 | 0 | 0 |
| planet | white | measurable | few_train | 50 | 3 | 1 | 15 | 31 | 0 | 3 |
| planet | white | measurable | three_years | 50 | 4 | 2 | 0 | 44 | 0 | 4 |
| planet | white | measurable | two_years | 100 | 6 | 3 | 42 | 49 | 0 | 6 |
| planet | white | measurable | variability_some_years | 50 | 45 | 0 | 4 | 1 | 0 | 10 |
| planet | white | near | few_train | 50 | 11 | 1 | 34 | 4 | 0 | 11 |
| planet | white | near | three_years | 50 | 33 | 0 | 6 | 11 | 0 | 32 |
| planet | white | near | two_years | 100 | 24 | 0 | 75 | 1 | 0 | 23 |
| planet | white | near | variability_some_years | 50 | 49 | 0 | 1 | 0 | 0 | 0 |

## b) REFUTED planets: fatal tests that failed (ranked by frequency)

Each REFUTED planet counts once for each fatal test with status FAIL; the column "combination" counts the exact set of fatal tests that failed.

### M0, band below: 238 REFUTED planets (of 500, both noise models)

| fatal test FAIL | planets |
|---|---|
| period_alias | 183 |
| holdout_by_year | 171 |
| odd_even | 5 |
| secondary_eclipse | 5 |

| combination | planets |
|---|---|
| holdout_by_year + period_alias | 114 |
| period_alias | 63 |
| holdout_by_year | 51 |
| holdout_by_year + period_alias + secondary_eclipse | 4 |
| odd_even | 3 |
| odd_even + period_alias | 1 |
| holdout_by_year + odd_even + period_alias | 1 |
| holdout_by_year + secondary_eclipse | 1 |

| test | message (numbers as #) | n |
|---|---|---|
| period_alias | a sinusoid at the found period explains the dip (adding a transit improves the BIC by # < #) | 183 |
| holdout_by_year | prediction failed for hidden year(s) #, #, # | 93 |
| holdout_by_year | prediction failed for hidden year(s) #, # | 52 |
| holdout_by_year | prediction failed for hidden year(s) # | 26 |
| odd_even | odd/even depth difference # sigma (> #) | 5 |
| secondary_eclipse | eclipse at phase #: # sigma, depth ratio # (>= #) | 5 |

| signal identity | fatal test FAIL | planets |
|---|---|---|
| candidate = another signal | holdout_by_year | 126 |
| candidate = another signal | odd_even | 2 |
| candidate = another signal | period_alias | 132 |
| candidate = another signal | secondary_eclipse | 5 |
| candidate = injected signal | holdout_by_year | 45 |
| candidate = injected signal | odd_even | 3 |
| candidate = injected signal | period_alias | 51 |

| noise | mechanism | fatal test FAIL | n |
|---|---|---|---|
| correlated | few_train | holdout_by_year | 1 |
| correlated | few_train | odd_even | 2 |
| correlated | few_train | period_alias | 1 |
| correlated | three_years | holdout_by_year | 48 |
| correlated | three_years | odd_even | 1 |
| correlated | three_years | period_alias | 16 |
| correlated | two_years | holdout_by_year | 2 |
| correlated | two_years | odd_even | 2 |
| correlated | two_years | period_alias | 12 |
| correlated | variability_some_years | holdout_by_year | 50 |
| correlated | variability_some_years | period_alias | 41 |
| correlated | variability_some_years | secondary_eclipse | 1 |
| white | few_train | holdout_by_year | 2 |
| white | few_train | period_alias | 24 |
| white | three_years | holdout_by_year | 17 |
| white | three_years | period_alias | 11 |
| white | two_years | holdout_by_year | 1 |
| white | two_years | period_alias | 28 |
| white | variability_some_years | holdout_by_year | 50 |
| white | variability_some_years | period_alias | 50 |
| white | variability_some_years | secondary_eclipse | 4 |

### M0, band near: 218 REFUTED planets (of 500, both noise models)

| fatal test FAIL | planets |
|---|---|
| holdout_by_year | 191 |
| period_alias | 123 |
| secondary_eclipse | 5 |
| odd_even | 3 |

| combination | planets |
|---|---|
| holdout_by_year + period_alias | 93 |
| holdout_by_year | 92 |
| period_alias | 25 |
| holdout_by_year + period_alias + secondary_eclipse | 5 |
| odd_even | 2 |
| holdout_by_year + odd_even | 1 |

| test | message (numbers as #) | n |
|---|---|---|
| period_alias | a sinusoid at the found period explains the dip (adding a transit improves the BIC by # < #) | 123 |
| holdout_by_year | prediction failed for hidden year(s) # | 76 |
| holdout_by_year | prediction failed for hidden year(s) #, #, # | 65 |
| holdout_by_year | prediction failed for hidden year(s) #, # | 50 |
| secondary_eclipse | eclipse at phase #: # sigma, depth ratio # (>= #) | 5 |
| odd_even | odd/even depth difference # sigma (> #) | 3 |

| signal identity | fatal test FAIL | planets |
|---|---|---|
| candidate = another signal | holdout_by_year | 86 |
| candidate = another signal | period_alias | 85 |
| candidate = another signal | secondary_eclipse | 5 |
| candidate = injected signal | holdout_by_year | 105 |
| candidate = injected signal | odd_even | 3 |
| candidate = injected signal | period_alias | 38 |

| noise | mechanism | fatal test FAIL | n |
|---|---|---|---|
| correlated | few_train | holdout_by_year | 6 |
| correlated | three_years | holdout_by_year | 32 |
| correlated | two_years | holdout_by_year | 3 |
| correlated | two_years | odd_even | 1 |
| correlated | variability_some_years | holdout_by_year | 50 |
| correlated | variability_some_years | period_alias | 34 |
| correlated | variability_some_years | secondary_eclipse | 1 |
| white | few_train | holdout_by_year | 7 |
| white | few_train | odd_even | 1 |
| white | few_train | period_alias | 6 |
| white | three_years | holdout_by_year | 38 |
| white | three_years | period_alias | 12 |
| white | two_years | holdout_by_year | 5 |
| white | two_years | odd_even | 1 |
| white | two_years | period_alias | 22 |
| white | variability_some_years | holdout_by_year | 50 |
| white | variability_some_years | period_alias | 49 |
| white | variability_some_years | secondary_eclipse | 4 |

### M0, band measurable: 119 REFUTED planets (of 500, both noise models)

| fatal test FAIL | planets |
|---|---|
| holdout_by_year | 115 |
| period_alias | 41 |
| odd_even | 3 |
| secondary_eclipse | 2 |

| combination | planets |
|---|---|
| holdout_by_year | 75 |
| holdout_by_year + period_alias | 38 |
| odd_even | 3 |
| holdout_by_year + period_alias + secondary_eclipse | 2 |
| period_alias | 1 |

| test | message (numbers as #) | n |
|---|---|---|
| holdout_by_year | prediction failed for hidden year(s) #, #, # | 57 |
| period_alias | a sinusoid at the found period explains the dip (adding a transit improves the BIC by # < #) | 41 |
| holdout_by_year | prediction failed for hidden year(s) # | 38 |
| holdout_by_year | prediction failed for hidden year(s) #, # | 20 |
| odd_even | odd/even depth difference # sigma (> #) | 3 |
| secondary_eclipse | eclipse at phase #: # sigma, depth ratio # (>= #) | 2 |

| signal identity | fatal test FAIL | planets |
|---|---|---|
| candidate = another signal | holdout_by_year | 44 |
| candidate = another signal | period_alias | 39 |
| candidate = another signal | secondary_eclipse | 2 |
| candidate = injected signal | holdout_by_year | 71 |
| candidate = injected signal | odd_even | 3 |
| candidate = injected signal | period_alias | 2 |

| noise | mechanism | fatal test FAIL | n |
|---|---|---|---|
| correlated | few_train | holdout_by_year | 1 |
| correlated | few_train | odd_even | 2 |
| correlated | three_years | holdout_by_year | 2 |
| correlated | two_years | odd_even | 1 |
| correlated | variability_some_years | holdout_by_year | 50 |
| correlated | variability_some_years | period_alias | 5 |
| white | few_train | holdout_by_year | 3 |
| white | three_years | holdout_by_year | 4 |
| white | two_years | holdout_by_year | 5 |
| white | two_years | period_alias | 1 |
| white | variability_some_years | holdout_by_year | 50 |
| white | variability_some_years | period_alias | 35 |
| white | variability_some_years | secondary_eclipse | 2 |

### M3, band below: 220 REFUTED planets (of 500, both noise models)

| fatal test FAIL | planets |
|---|---|
| period_alias | 183 |
| holdout_by_year | 53 |
| odd_even | 5 |
| secondary_eclipse | 5 |

| combination | planets |
|---|---|
| period_alias | 158 |
| holdout_by_year | 33 |
| holdout_by_year + period_alias | 19 |
| period_alias + secondary_eclipse | 4 |
| odd_even | 3 |
| odd_even + period_alias | 1 |
| holdout_by_year + odd_even + period_alias | 1 |
| secondary_eclipse | 1 |

| test | message (numbers as #) | n |
|---|---|---|
| period_alias | a sinusoid at the found period explains the dip (adding a transit improves the BIC by # < #) | 183 |
| holdout_by_year | prediction failed for hidden year(s) # | 24 |
| holdout_by_year | prediction failed for hidden year(s) #, # | 23 |
| holdout_by_year | prediction failed for hidden year(s) #, #, # | 6 |
| odd_even | odd/even depth difference # sigma (> #) | 5 |
| secondary_eclipse | eclipse at phase #: # sigma, depth ratio # (>= #) | 5 |

| signal identity | fatal test FAIL | planets |
|---|---|---|
| candidate = another signal | holdout_by_year | 25 |
| candidate = another signal | odd_even | 2 |
| candidate = another signal | period_alias | 132 |
| candidate = another signal | secondary_eclipse | 5 |
| candidate = injected signal | holdout_by_year | 28 |
| candidate = injected signal | odd_even | 3 |
| candidate = injected signal | period_alias | 51 |

| noise | mechanism | fatal test FAIL | n |
|---|---|---|---|
| correlated | few_train | holdout_by_year | 1 |
| correlated | few_train | odd_even | 2 |
| correlated | few_train | period_alias | 1 |
| correlated | three_years | holdout_by_year | 35 |
| correlated | three_years | odd_even | 1 |
| correlated | three_years | period_alias | 16 |
| correlated | two_years | holdout_by_year | 2 |
| correlated | two_years | odd_even | 2 |
| correlated | two_years | period_alias | 12 |
| correlated | variability_some_years | holdout_by_year | 11 |
| correlated | variability_some_years | period_alias | 41 |
| correlated | variability_some_years | secondary_eclipse | 1 |
| white | few_train | period_alias | 24 |
| white | three_years | holdout_by_year | 1 |
| white | three_years | period_alias | 11 |
| white | two_years | period_alias | 28 |
| white | variability_some_years | holdout_by_year | 3 |
| white | variability_some_years | period_alias | 50 |
| white | variability_some_years | secondary_eclipse | 4 |

### M3, band near: 208 REFUTED planets (of 500, both noise models)

| fatal test FAIL | planets |
|---|---|
| period_alias | 123 |
| holdout_by_year | 106 |
| secondary_eclipse | 5 |
| odd_even | 3 |

| combination | planets |
|---|---|
| period_alias | 96 |
| holdout_by_year | 82 |
| holdout_by_year + period_alias | 22 |
| period_alias + secondary_eclipse | 4 |
| odd_even | 2 |
| holdout_by_year + period_alias + secondary_eclipse | 1 |
| holdout_by_year + odd_even | 1 |

| test | message (numbers as #) | n |
|---|---|---|
| period_alias | a sinusoid at the found period explains the dip (adding a transit improves the BIC by # < #) | 123 |
| holdout_by_year | prediction failed for hidden year(s) # | 66 |
| holdout_by_year | prediction failed for hidden year(s) #, # | 38 |
| secondary_eclipse | eclipse at phase #: # sigma, depth ratio # (>= #) | 5 |
| odd_even | odd/even depth difference # sigma (> #) | 3 |
| holdout_by_year | prediction failed for hidden year(s) #, #, # | 2 |

| signal identity | fatal test FAIL | planets |
|---|---|---|
| candidate = another signal | holdout_by_year | 14 |
| candidate = another signal | period_alias | 85 |
| candidate = another signal | secondary_eclipse | 5 |
| candidate = injected signal | holdout_by_year | 92 |
| candidate = injected signal | odd_even | 3 |
| candidate = injected signal | period_alias | 38 |

| noise | mechanism | fatal test FAIL | n |
|---|---|---|---|
| correlated | few_train | holdout_by_year | 6 |
| correlated | three_years | holdout_by_year | 32 |
| correlated | two_years | holdout_by_year | 3 |
| correlated | two_years | odd_even | 1 |
| correlated | variability_some_years | holdout_by_year | 28 |
| correlated | variability_some_years | period_alias | 34 |
| correlated | variability_some_years | secondary_eclipse | 1 |
| white | few_train | holdout_by_year | 5 |
| white | few_train | odd_even | 1 |
| white | few_train | period_alias | 6 |
| white | three_years | holdout_by_year | 28 |
| white | three_years | period_alias | 12 |
| white | two_years | holdout_by_year | 4 |
| white | two_years | odd_even | 1 |
| white | two_years | period_alias | 22 |
| white | variability_some_years | period_alias | 49 |
| white | variability_some_years | secondary_eclipse | 4 |

### M3, band measurable: 102 REFUTED planets (of 500, both noise models)

| fatal test FAIL | planets |
|---|---|
| holdout_by_year | 73 |
| period_alias | 41 |
| odd_even | 3 |
| secondary_eclipse | 2 |

| combination | planets |
|---|---|
| holdout_by_year | 58 |
| period_alias | 25 |
| holdout_by_year + period_alias | 14 |
| odd_even | 3 |
| holdout_by_year + period_alias + secondary_eclipse | 1 |
| period_alias + secondary_eclipse | 1 |

| test | message (numbers as #) | n |
|---|---|---|
| holdout_by_year | prediction failed for hidden year(s) #, # | 49 |
| period_alias | a sinusoid at the found period explains the dip (adding a transit improves the BIC by # < #) | 41 |
| holdout_by_year | prediction failed for hidden year(s) # | 24 |
| odd_even | odd/even depth difference # sigma (> #) | 3 |
| secondary_eclipse | eclipse at phase #: # sigma, depth ratio # (>= #) | 2 |

| signal identity | fatal test FAIL | planets |
|---|---|---|
| candidate = another signal | holdout_by_year | 15 |
| candidate = another signal | period_alias | 39 |
| candidate = another signal | secondary_eclipse | 2 |
| candidate = injected signal | holdout_by_year | 58 |
| candidate = injected signal | odd_even | 3 |
| candidate = injected signal | period_alias | 2 |

| noise | mechanism | fatal test FAIL | n |
|---|---|---|---|
| correlated | few_train | holdout_by_year | 1 |
| correlated | few_train | odd_even | 2 |
| correlated | three_years | holdout_by_year | 2 |
| correlated | two_years | odd_even | 1 |
| correlated | variability_some_years | holdout_by_year | 36 |
| correlated | variability_some_years | period_alias | 5 |
| white | few_train | holdout_by_year | 3 |
| white | three_years | holdout_by_year | 4 |
| white | two_years | holdout_by_year | 5 |
| white | two_years | period_alias | 1 |
| white | variability_some_years | holdout_by_year | 22 |
| white | variability_some_years | period_alias | 35 |
| white | variability_some_years | secondary_eclipse | 2 |

## c) `variability_some_years` planets

### M0: 300 cases, verdicts {'REFUTED': 300}; {'no signal identity': 228, 'signal identity': 72}

- ratio of the found period to the planet period (sorted sample): 0.09981, 0.1367, 0.1674, 0.184, 0.2133, 0.2453, 0.2768, 0.3198, 0.4062, 0.5684, 1, 1
- ratio of the found period to the variability period (sorted sample): 0.9928, 0.9976, 0.9989, 0.9999, 1, 1, 1.002, 1.997, 2, 2.059, 4.911, 8.042

| fatal test FAIL | cases |
|---|---|
| holdout_by_year | 300 |
| period_alias | 214 |
| secondary_eclipse | 12 |

| test | message (numbers as #) | n |
|---|---|---|
| period_alias | a sinusoid at the found period explains the dip (adding a transit improves the BIC by # < #) | 214 |
| holdout_by_year | prediction failed for hidden year(s) #, #, # | 151 |
| holdout_by_year | prediction failed for hidden year(s) #, # | 89 |
| holdout_by_year | prediction failed for hidden year(s) # | 60 |
| secondary_eclipse | eclipse at phase #: # sigma, depth ratio # (>= #) | 12 |

### M3: 300 cases, verdicts {'REFUTED': 275, 'INCONCLUSIVE': 12, 'SURVIVED': 13}; {'no signal identity': 228, 'signal identity': 72}

- ratio of the found period to the planet period (sorted sample): 0.09981, 0.1367, 0.1674, 0.184, 0.2133, 0.2453, 0.2768, 0.3198, 0.4062, 0.5684, 1, 1
- ratio of the found period to the variability period (sorted sample): 0.9928, 0.9976, 0.9989, 0.9999, 1, 1, 1.002, 1.997, 2, 2.059, 4.911, 8.042

| fatal test FAIL | cases |
|---|---|
| period_alias | 214 |
| holdout_by_year | 100 |
| secondary_eclipse | 12 |

| test | message (numbers as #) | n |
|---|---|---|
| period_alias | a sinusoid at the found period explains the dip (adding a transit improves the BIC by # < #) | 214 |
| holdout_by_year | prediction failed for hidden year(s) #, # | 77 |
| holdout_by_year | prediction failed for hidden year(s) # | 23 |
| secondary_eclipse | eclipse at phase #: # sigma, depth ratio # (>= #) | 12 |

## d) C2 white (`variability_masked`) and C3 of white planets (`two_years`, `few_train`)

### M0, `variability_masked` false positives, measurable, white (62 cases)

- verdict without `eb_catalog`: {'REFUTED': 60, 'WEAKENED': 2}
- signal identity (found period = f x eclipse period, f in 1, 2, 1/2, tolerance 0.001): {False: 62}
- ratio of the found period to the injected eclipse period: 0.114, 0.132, 0.145, 0.164, 0.168, 0.193, 0.206, 0.245, 0.259, 0.299, 0.362, 0.457, 0.509
- ratio of the found period to the injected variability period: 0.998, 0.999, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2
- fatal tests FAIL (condition i): {'period_alias': 58, 'secondary_eclipse': 10}

### M0, `two_years` planets, measurable, white: 42 of 100 INCONCLUSIVE

| test INCONCLUSIVE | cases |
|---|---|
| holdout_by_year | 42 |

| source | message (numbers as #) | n |
|---|---|---|
| holdout round | train-only timing uncertainty in the hidden year (# h) exceeds # transit duration(s) (# h) | 84 |
| holdout_by_year | no hidden year could be tested | 42 |

### M0, `few_train` planets, measurable, white: 15 of 50 INCONCLUSIVE

| test INCONCLUSIVE | cases |
|---|---|
| holdout_by_year | 15 |

| source | message (numbers as #) | n |
|---|---|---|
| holdout round | train-only timing uncertainty in the hidden year (# h) exceeds # transit duration(s) (# h) | 30 |
| holdout_by_year | no hidden year could be tested | 15 |

### M3, `variability_masked` false positives, measurable, white (62 cases)

- verdict without `eb_catalog`: {'REFUTED': 60, 'INCONCLUSIVE': 2}
- signal identity (found period = f x eclipse period, f in 1, 2, 1/2, tolerance 0.001): {False: 62}
- ratio of the found period to the injected eclipse period: 0.114, 0.132, 0.145, 0.164, 0.168, 0.193, 0.206, 0.245, 0.259, 0.299, 0.362, 0.457, 0.509
- ratio of the found period to the injected variability period: 0.998, 0.999, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2
- fatal tests FAIL (condition i): {'period_alias': 58, 'secondary_eclipse': 10}

### M3, `two_years` planets, measurable, white: 42 of 100 INCONCLUSIVE

| test INCONCLUSIVE | cases |
|---|---|
| holdout_by_year | 42 |

| source | message (numbers as #) | n |
|---|---|---|
| holdout round | train-only timing uncertainty in the hidden year (# h) exceeds # transit duration(s) (# h) | 84 |
| holdout_by_year | no hidden year could be tested | 42 |

### M3, `few_train` planets, measurable, white: 15 of 50 INCONCLUSIVE

| test INCONCLUSIVE | cases |
|---|---|
| holdout_by_year | 15 |

| source | message (numbers as #) | n |
|---|---|---|
| holdout round | train-only timing uncertainty in the hidden year (# h) exceeds # transit duration(s) (# h) | 30 |
| holdout_by_year | no hidden year could be tested | 15 |

## e) Example cases (3 per pattern, M3, condition i)

### below planets REFUTED by `period_alias` (outside variability_some_years)

- `planet-below-correlated-0004` (planet, below, correlated, two_years): verdict REFUTED; injected P=2.1076 d, depth=0.0005891, t0=1325.9146; candidate P=0.5484341, depth=2928 ppm, SNR=411; identity=False, without eb_catalog=REFUTED
  - plausibility FAIL (warning): duration 9.00 h is 5.61 times the circular-orbit maximum (1.61 h) [stellar_mass_source=TIC mass]
  - centroid_shift INCONCLUSIVE (fatal): only 0 usable sector(s) (< 1) []
  - aperture_depth INCONCLUSIVE (fatal): the transit is not detected in the pixel photometry (core 0.5 sigma, large 0.6 sigma, both < 3.0): the depths cannot be compared [n_sectors=2]
  - period_alias FAIL (fatal): a sinusoid at the found period explains the dip (adding a transit improves the BIC by -10.5 < 10) [n_in_transit_cadences=25686]
  - holdout_by_year INCONCLUSIVE (fatal): no hidden year could be tested [n_fail=0, n_inconclusive=2, n_pass=0]
- `planet-below-correlated-0016` (planet, below, correlated, two_years): verdict REFUTED; injected P=5.384092 d, depth=0.0008347, t0=1328.4938; candidate P=0.5405649, depth=415.3 ppm, SNR=57.8; identity=False, without eb_catalog=REFUTED
  - plausibility FAIL (warning): duration 8.40 h is 5.44 times the circular-orbit maximum (1.54 h) [stellar_mass_source=TIC mass]
  - centroid_shift INCONCLUSIVE (fatal): only 0 usable sector(s) (< 1) []
  - aperture_depth INCONCLUSIVE (fatal): the transit is not detected in the pixel photometry (core 1.2 sigma, large 1.1 sigma, both < 3.0): the depths cannot be compared [n_sectors=2]
  - period_alias FAIL (fatal): a sinusoid at the found period explains the dip (adding a transit improves the BIC by -6.5 < 10) [n_in_transit_cadences=24266]
  - holdout_by_year INCONCLUSIVE (fatal): no hidden year could be tested [n_fail=0, n_inconclusive=2, n_pass=0]
- `planet-below-correlated-0020` (planet, below, correlated, two_years): verdict REFUTED; injected P=1.568282 d, depth=0.0004945, t0=1325.8112; candidate P=0.5006535, depth=580.3 ppm, SNR=78.7; identity=False, without eb_catalog=REFUTED
  - plausibility FAIL (warning): duration 4.42 h is 2.92 times the circular-orbit maximum (1.52 h) [stellar_mass_source=TIC mass]
  - centroid_shift INCONCLUSIVE (fatal): only 0 usable sector(s) (< 1) []
  - aperture_depth INCONCLUSIVE (fatal): the transit is not detected in the pixel photometry (core 0.6 sigma, large 0.5 sigma, both < 3.0): the depths cannot be compared [n_sectors=2]
  - period_alias FAIL (fatal): a sinusoid at the found period explains the dip (adding a transit improves the BIC by 2.2 < 10) [n_in_transit_cadences=13713]
  - holdout_by_year INCONCLUSIVE (fatal): no hidden year could be tested [n_fail=0, n_inconclusive=2, n_pass=0]

### near planets REFUTED by `holdout_by_year` (outside variability_some_years)

- `planet-near-correlated-0011` (planet, near, correlated, two_years): verdict REFUTED; injected P=2.654175 d, depth=0.001102, t0=1325.9303; candidate P=2.65418, depth=1022 ppm, SNR=46.3; identity=True, without eb_catalog=REFUTED
  - holdout_by_year FAIL (fatal): prediction failed for hidden year(s) 2018 [n_fail=1, n_inconclusive=1, n_pass=0]
- `planet-near-correlated-0059` (planet, near, correlated, two_years): verdict REFUTED; injected P=4.692052 d, depth=0.001493, t0=1325.8444; candidate P=4.692044, depth=1681 ppm, SNR=65; identity=True, without eb_catalog=REFUTED
  - holdout_by_year FAIL (fatal): prediction failed for hidden year(s) 2020 [n_fail=1, n_inconclusive=1, n_pass=0]
- `planet-near-correlated-0081` (planet, near, correlated, two_years): verdict REFUTED; injected P=4.519134 d, depth=0.001657, t0=1329.2386; candidate P=4.51913, depth=1734 ppm, SNR=61.2; identity=True, without eb_catalog=REFUTED
  - holdout_by_year FAIL (fatal): prediction failed for hidden year(s) 2018 [n_fail=1, n_inconclusive=1, n_pass=0]

### measurable planets REFUTED by `holdout_by_year` (outside variability_some_years)

- `planet-measurable-correlated-0122` (planet, measurable, correlated, three_years): verdict REFUTED; injected P=5.262115 d, depth=0.001515, t0=1330.1503; candidate P=5.262103, depth=1457 ppm, SNR=69; identity=True, without eb_catalog=REFUTED
  - holdout_by_year FAIL (fatal): prediction failed for hidden year(s) 2018 [n_fail=1, n_inconclusive=0, n_pass=2]
- `planet-measurable-correlated-0146` (planet, measurable, correlated, three_years): verdict REFUTED; injected P=3.442998 d, depth=0.003037, t0=1327.8244; candidate P=3.442997, depth=2833 ppm, SNR=141; identity=True, without eb_catalog=REFUTED
  - period_alias FAIL (warning): period within 1% of a known systematic period (3.425 d) [n_in_transit_cadences=1628]
  - holdout_by_year FAIL (fatal): prediction failed for hidden year(s) 2018 [n_fail=1, n_inconclusive=0, n_pass=2]
- `planet-measurable-correlated-0199` (planet, measurable, correlated, few_train): verdict REFUTED; injected P=3.622694 d, depth=0.002982, t0=1325.3971; candidate P=3.622698, depth=2820 ppm, SNR=97; identity=True, without eb_catalog=REFUTED
  - holdout_by_year FAIL (fatal): prediction failed for hidden year(s) 2018 [n_fail=1, n_inconclusive=0, n_pass=1]

### `variability_some_years` planets

- `planet-below-correlated-0200` (planet, below, correlated, variability_some_years): verdict REFUTED; injected P=4.055717 d, depth=0.0006873, t0=1328.7324; candidate P=0.9885733, depth=780.6 ppm, SNR=114; identity=False, without eb_catalog=REFUTED
  - plausibility FAIL (warning): duration 8.10 h is 4.31 times the circular-orbit maximum (1.88 h) [stellar_mass_source=TIC mass]
  - period_alias FAIL (fatal): a sinusoid at the found period explains the dip (adding a transit improves the BIC by 2.0 < 10) [n_in_transit_cadences=19101]
  - holdout_by_year INCONCLUSIVE (fatal): no hidden year could be tested [n_fail=0, n_inconclusive=3, n_pass=0]
- `planet-below-correlated-0201` (planet, below, correlated, variability_some_years): verdict REFUTED; injected P=1.713438 d, depth=0.0004233, t0=1325.8197; candidate P=0.6055141, depth=1204 ppm, SNR=210; identity=False, without eb_catalog=REFUTED
  - plausibility FAIL (warning): duration 9.00 h is 5.55 times the circular-orbit maximum (1.62 h) [stellar_mass_source=TIC mass]
  - centroid_shift INCONCLUSIVE (fatal): only 0 usable sector(s) (< 1) []
  - period_alias FAIL (fatal): a sinusoid at the found period explains the dip (adding a transit improves the BIC by -10.7 < 10) [n_in_transit_cadences=34936]
  - holdout_by_year INCONCLUSIVE (fatal): no hidden year could be tested [n_fail=0, n_inconclusive=3, n_pass=0]
- `planet-below-correlated-0202` (planet, below, correlated, variability_some_years): verdict REFUTED; injected P=5.289322 d, depth=0.000603, t0=1330.0412; candidate P=0.6827001, depth=2328 ppm, SNR=396; identity=False, without eb_catalog=REFUTED
  - plausibility FAIL (warning): duration 9.00 h is 5.28 times the circular-orbit maximum (1.71 h) [stellar_mass_source=TIC mass]
  - centroid_shift INCONCLUSIVE (fatal): only 0 usable sector(s) (< 1) []
  - period_alias FAIL (fatal): a sinusoid at the found period explains the dip (adding a transit improves the BIC by -7.5 < 10) [n_in_transit_cadences=30862]
  - holdout_by_year INCONCLUSIVE (fatal): no hidden year could be tested [n_fail=0, n_inconclusive=3, n_pass=0]

### `variability_masked` false positives, white, measurable

- `false_positive-measurable-white-0188` (false_positive, measurable, white, variability_masked): verdict REFUTED; injected P=2.117865 d, depth=0.0003978, t0=1325.5487; candidate P=0.7828337, depth=849.2 ppm, SNR=133; identity=False, without eb_catalog=REFUTED
  - plausibility FAIL (warning): duration 7.20 h is 4.12 times the circular-orbit maximum (1.75 h) [stellar_mass_source=TIC mass]
  - period_alias FAIL (fatal): a sinusoid at the found period explains the dip (adding a transit improves the BIC by -10.2 < 10) [n_in_transit_cadences=14465]
  - holdout_by_year INCONCLUSIVE (fatal): no hidden year could be tested [n_fail=0, n_inconclusive=2, n_pass=0]
- `false_positive-measurable-white-0189` (false_positive, measurable, white, variability_masked): verdict REFUTED; injected P=3.111813 d, depth=0.0008088, t0=1326.2197; candidate P=0.5548527, depth=3894 ppm, SNR=598; identity=False, without eb_catalog=REFUTED
  - plausibility FAIL (warning): duration 9.00 h is 5.54 times the circular-orbit maximum (1.62 h) [stellar_mass_source=TIC mass]
  - centroid_shift INCONCLUSIVE (fatal): only 0 usable sector(s) (< 1) []
  - period_alias FAIL (fatal): a sinusoid at the found period explains the dip (adding a transit improves the BIC by -10.3 < 10) [n_in_transit_cadences=25316]
  - holdout_by_year INCONCLUSIVE (fatal): no hidden year could be tested [n_fail=0, n_inconclusive=2, n_pass=0]
- `false_positive-measurable-white-0190` (false_positive, measurable, white, variability_masked): verdict REFUTED; injected P=4.952478 d, depth=0.001217, t0=1329.3462; candidate P=0.6254679, depth=2739 ppm, SNR=81; identity=False, without eb_catalog=REFUTED
  - secondary_eclipse FAIL (fatal): eclipse at phase 0.5: 24.3 sigma, depth ratio 0.886 (>= 0.1) [n_secondary_events=81]
  - plausibility FAIL (warning): duration 3.80 h is 2.28 times the circular-orbit maximum (1.67 h) [stellar_mass_source=TIC mass]
  - period_alias FAIL (fatal): a sinusoid at the found period explains the dip (adding a transit improves the BIC by -10.5 < 10) [n_in_transit_cadences=9475]
  - holdout_by_year INCONCLUSIVE (fatal): no hidden year could be tested [n_fail=0, n_inconclusive=2, n_pass=0]

### `two_years` planets, measurable, white, INCONCLUSIVE

- `planet-measurable-white-0004` (planet, measurable, white, two_years): verdict INCONCLUSIVE; injected P=2.216529 d, depth=0.0002761, t0=1326.8205; candidate P=2.216531, depth=243.8 ppm, SNR=16.4; identity=True, without eb_catalog=INCONCLUSIVE
  - holdout_by_year INCONCLUSIVE (fatal): no hidden year could be tested [n_fail=0, n_inconclusive=2, n_pass=0]
- `planet-measurable-white-0006` (planet, measurable, white, two_years): verdict INCONCLUSIVE; injected P=3.459983 d, depth=0.0002709, t0=1325.297; candidate P=3.460006, depth=282.9 ppm, SNR=16.7; identity=True, without eb_catalog=INCONCLUSIVE
  - holdout_by_year INCONCLUSIVE (fatal): no hidden year could be tested [n_fail=0, n_inconclusive=2, n_pass=0]
- `planet-measurable-white-0007` (planet, measurable, white, two_years): verdict INCONCLUSIVE; injected P=2.941769 d, depth=0.00041, t0=1325.6998; candidate P=2.941783, depth=392.8 ppm, SNR=23.4; identity=True, without eb_catalog=INCONCLUSIVE
  - holdout_by_year INCONCLUSIVE (fatal): no hidden year could be tested [n_fail=0, n_inconclusive=2, n_pass=0]

### `few_train` planets, measurable, white, INCONCLUSIVE

- `planet-measurable-white-0157` (planet, measurable, white, few_train): verdict INCONCLUSIVE; injected P=3.361148 d, depth=0.0004997, t0=1325.8226; candidate P=3.361111, depth=473.9 ppm, SNR=22.4; identity=True, without eb_catalog=INCONCLUSIVE
  - holdout_by_year INCONCLUSIVE (fatal): no hidden year could be tested [n_fail=0, n_inconclusive=2, n_pass=0]
- `planet-measurable-white-0170` (planet, measurable, white, few_train): verdict INCONCLUSIVE; injected P=3.976373 d, depth=0.0007079, t0=1327.8216; candidate P=3.976359, depth=665.2 ppm, SNR=31.1; identity=True, without eb_catalog=INCONCLUSIVE
  - holdout_by_year INCONCLUSIVE (fatal): no hidden year could be tested [n_fail=0, n_inconclusive=2, n_pass=0]
- `planet-measurable-white-0171` (planet, measurable, white, few_train): verdict INCONCLUSIVE; injected P=3.208614 d, depth=0.0004181, t0=1325.2243; candidate P=3.208644, depth=441.4 ppm, SNR=22.7; identity=True, without eb_catalog=INCONCLUSIVE
  - holdout_by_year INCONCLUSIVE (fatal): no hidden year could be tested [n_fail=0, n_inconclusive=2, n_pass=0]

## f) Sanity of the synthetic population (planets)

In the manifest, `expected_snr` holds the expected SNR **per unit depth** (c_k of section 3): SNR_k = depth x c_k. Recomputed here: r = min(global/7.1, train(y)/7.1, hidden(y)/5.0) x depth, compared with the recorded `r_actual` and with the band. The recovery uses the M3 candidate and only the cases in which it is the injected signal with factor 1 (rows `[f=1]`): the period (ratio - 1), the depth (candidate / depth of the injected trapezoid, which is not the mean box depth), Refute's SNR / expected global SNR (different definitions: the ratio only describes), the ephemeris (phase distance of the candidate t0 from the injected t0, in durations) and the duration.

### band below: 500 planets

- r recomputed equal to the recorded `r_actual`: 500 of 500
- r inside the declared band: 500 of 500
- signal identity (fraction, all): 0.532 (266 of 500)
- Refute snr gate PASS (fraction, all): 0.838 (419 of 500)

| quantity | n | min | p10 | median | p90 | max |
|---|---|---|---|---|---|---|
| r | 500 | 0.5016 | 0.5599 | 0.7536 | 0.9491 | 0.9987 |
| expected_global_snr | 500 | 4.375 | 5.585 | 7.617 | 9.884 | 12.25 |
| [f=1] P_found/P_injected - 1 | 264 | -0.0004999 | -1.146e-05 | 1.23e-07 | 1.16e-05 | 0.0007861 |
| [f=1] depth_found/depth_injected | 264 | 0.7217 | 0.8706 | 1.046 | 1.229 | 1.778 |
| [f=1] measured_SNR/expected_global_SNR, correlated | 152 | 3.307 | 4.006 | 4.806 | 5.65 | 6.277 |
| [f=1] |dt0| in durations (phase) | 264 | 2.553e-05 | 0.002453 | 0.01729 | 0.0973 | 7.517 |
| [f=1] duration_found/injected | 264 | 0.3296 | 0.8699 | 0.9476 | 1.009 | 1.407 |
| [f=1] measured_SNR/expected_global_SNR, white | 112 | 0.8152 | 0.902 | 1.069 | 1.271 | 1.433 |

Which ratio sets the "below" band (the smallest), by mechanism, and whether the expected global SNR is also below 7.1:

| mechanism | smallest ratio | global SNR < 7.1 | planets |
|---|---|---|---|
| few_train | train | False | 84 |
| few_train | train | True | 16 |
| three_years | hidden | False | 24 |
| three_years | hidden | True | 20 |
| three_years | train | False | 22 |
| three_years | train | True | 34 |
| two_years | train | False | 129 |
| two_years | train | True | 71 |
| variability_some_years | hidden | False | 23 |
| variability_some_years | hidden | True | 30 |
| variability_some_years | train | False | 17 |
| variability_some_years | train | True | 30 |

### band near: 500 planets

- r recomputed equal to the recorded `r_actual`: 500 of 500
- r inside the declared band: 500 of 500
- signal identity (fraction, all): 0.824 (412 of 500)
- Refute snr gate PASS (fraction, all): 0.998 (499 of 500)

| quantity | n | min | p10 | median | p90 | max |
|---|---|---|---|---|---|---|
| r | 500 | 1 | 1.045 | 1.26 | 1.454 | 1.499 |
| expected_global_snr | 500 | 8.719 | 10.15 | 12.51 | 15.71 | 20.11 |
| [f=1] P_found/P_injected - 1 | 410 | -0.0007954 | -6.399e-06 | -1.239e-08 | 7.351e-06 | 0.0007002 |
| [f=1] depth_found/depth_injected | 410 | 0.7214 | 0.868 | 0.9911 | 1.117 | 1.379 |
| [f=1] measured_SNR/expected_global_SNR, correlated | 214 | 2.117 | 3.866 | 4.618 | 5.211 | 5.906 |
| [f=1] |dt0| in durations (phase) | 410 | 1.462e-05 | 0.002278 | 0.01157 | 0.05193 | 4.351 |
| [f=1] duration_found/injected | 410 | 0.4363 | 0.9049 | 0.9502 | 0.995 | 1.332 |
| [f=1] measured_SNR/expected_global_SNR, white | 196 | 0.7763 | 0.8985 | 1.018 | 1.122 | 1.377 |

### band measurable: 500 planets

- r recomputed equal to the recorded `r_actual`: 500 of 500
- r inside the declared band: 500 of 500
- signal identity (fraction, all): 0.912 (456 of 500)
- Refute snr gate PASS (fraction, all): 1.000 (500 of 500)

| quantity | n | min | p10 | median | p90 | max |
|---|---|---|---|---|---|---|
| r | 500 | 1.504 | 1.727 | 3.036 | 5.295 | 5.994 |
| expected_global_snr | 500 | 13.48 | 17.2 | 30.24 | 52.97 | 73.86 |
| [f=1] P_found/P_injected - 1 | 456 | -0.0008381 | -3.788e-06 | 4.079e-08 | 3.455e-06 | 0.0005731 |
| [f=1] depth_found/depth_injected | 456 | 0.7725 | 0.9312 | 0.9781 | 1.044 | 1.296 |
| [f=1] measured_SNR/expected_global_SNR, correlated | 245 | 2.169 | 2.83 | 4.701 | 5.003 | 5.509 |
| [f=1] |dt0| in durations (phase) | 456 | 2.716e-05 | 0.002083 | 0.008763 | 0.02372 | 5.202 |
| [f=1] duration_found/injected | 456 | 0.7579 | 0.901 | 0.9422 | 0.974 | 1.107 |
| [f=1] measured_SNR/expected_global_SNR, white | 211 | 0.6209 | 0.9217 | 0.9958 | 1.055 | 1.183 |

## Observations (not causal conclusions)

The tables above are the basis. What follows summarizes what they show; every causal reading
is marked **Hypothesis** and was not tested.

1. **The population agrees with its generation parameters (item f).** In all 1500 planets,
   `r` recomputed from `expected_snr` and the depth equals the recorded `r_actual` and falls
   in the declared band. When Refute's candidate is the injected signal (factor 1), period,
   ephemeris, depth and duration agree: |P/P_inj - 1| < 0.001 in every case, median phase
   offset of t0 from 0.009 to 0.017 durations, median depth 0.98 to 1.05 times the injected
   depth, median duration 0.94 to 0.95 times. No defect of the population appears in these
   quantities.
2. **Refute's SNR agrees with the expected SNR in white noise and not in correlated noise.**
   With the right signal, Refute's SNR divided by the expected global SNR: median 1.00 to 1.07
   in white noise; 4.6 to 4.8 in correlated noise, in the three bands. The expected SNR of
   section 3 includes the AR(1) covariance. **Hypothesis:** Refute's SNR treats the noise as
   white and overstates the significance in correlated noise. Observed consequence: 83.8% of
   the "below" planets pass Refute's own SNR gate.
3. **The "below" band is always set by a single year.** In the 500 "below" planets, the ratio
   that sets the band is the train ratio (403) or the hidden-year ratio (97), never the global
   one; 299 of the 500 have an expected global SNR of 7.1 or more (table of item f). This is
   the design of section 3, not a generation error.
4. **Half of the "below" planets do not have the injected signal as their candidate.** Only
   53.2% (266 of 500) have signal identity; in "near", 82.4%; in "measurable", 91.2%. Among the
   REFUTED planets of M3, below band, 132 of the 183 `period_alias` failures are of candidates
   that are not the injected signal (the candidate is another signal: variability, trend or
   noise; see the examples, with periods of 0.5 to 1 d). C1 counts these cases as refuted
   planets, because the criterion counts the target's verdict.
5. **`period_alias` is the main fatal test in the below and near planets** ("a sinusoid at the
   found period explains the dip", BIC gain < 10): 183 below and 123 near planets at M0 and at
   M3 (the test did not change between the points). It also fails with the right signal: 51
   below and 38 near planets with signal identity. **Hypothesis:** at low SNR, the BIC gain of
   a box over a sinusoid does not reach 10 even for a real transit, and the test records a lack
   of evidence as a fatal FAIL instead of INCONCLUSIVE.
6. **`holdout_by_year` with the right signal remains the main cause in near and measurable at
   M3:** 92 near and 58 measurable planets with signal identity ("prediction failed for hidden
   year(s)"). In near, the holdout failures concentrate in `three_years` (32 in correlated
   noise, 28 in white) and in correlated `variability_some_years` (28); in measurable, in
   `variability_some_years` (36 correlated, 22 white). From M0 to M3 (the effect of H4, at M2),
   holdout failures fall sharply for candidates that are not the signal (126 to 25 in below),
   but little with the right signal (105 to 92 in near). **Hypotheses, not tested:** in
   `three_years`, the prediction of a hidden year from the other two fails for a reason not
   examined here; in `variability_some_years`, the variability present in the hidden year
   distorts the measurement of the transit times; in correlated noise, the underestimated error
   (item 2) may make the prediction too narrow. (A complementary read-only investigation of
   these failures was made afterwards; it is not part of this translation.)
7. **`variability_some_years` (300 planets):** in 228 the candidate is not the planet; the ratio
   of the found period to the variability period is 1 or 2 (sample in item c). The
   `period_alias` test correctly identifies that candidate as a sinusoid, and the target's
   verdict is REFUTED. At M0 all 300 are REFUTED; at M3, 275 (12 INCONCLUSIVE and 13 SURVIVED),
   through the fall of the holdout failures. **Hypothesis:** the search finds the variability,
   stronger than the transit (amplitude 2 to 4 times the depth), and the variability is not
   removed before the search.
8. **C2 white, `variability_masked` (0 of 62 flagged):** 60 of 62 are REFUTED without
   `eb_catalog`, but none has signal identity: the period found is that of the variability
   (ratio 1 or 2), not that of the eclipse (ratio 0.11 to 0.51). The false positive is refuted
   for the wrong reason (the candidate is the sinusoid), and the identity rule of H7 does not
   count it. The same pattern in correlated noise (0 of 62). **Hypothesis:** the same as item 7
   (the search finds the variability).
9. **C3 of the white measurable planets (`two_years` 42 of 100, `few_train` 15 of 50
   INCONCLUSIVE):** in all of them, `holdout_by_year` is INCONCLUSIVE because, in both rounds,
   "the train-only timing uncertainty in the hidden year exceeds 1 transit duration"; no hidden
   year could be tested. The candidate is the right signal in the examples. In correlated noise
   the same mechanism has only 3 INCONCLUSIVE. **Hypothesis:** with two years two years apart
   (or few train transits), propagating the ephemeris from a single year exceeds the limit of
   1 duration in white noise; in correlated noise the underestimated error (item 2) keeps the
   uncertainty below the limit and the test runs (and fails, item 6).

**Tool versus population (the request of item f).** None of the quantities checked points to
a defect of the synthetic population: bands, parameters, periods, ephemerides, depths and
durations agree. The patterns behind C1, C2 and C3 lie in how the tool treats the data: the
candidate chosen (items 4, 7, 8), the `period_alias` rule at low SNR (item 5) and the holdout
(items 6 and 9), with the SNR in correlated noise (item 2) as a possible common factor.

## Conclusion

No defect of the population appeared in the checks performed. The diagnosis points to
limitations of the tool, whose causes and corrections still need to be tested.
