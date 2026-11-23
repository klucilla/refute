# v0.5.8 stage 0: the recommendation's section 1, recounted from the records (exploratory, no doors)

**Exploratory.** Limits label: 'WEAKENED; does not meet D1, D2, D4, T2a'. `method_status: not_validated`.

OK records: 534. Sensitivity blocks with a probability: 4820.

| Margin | PASS blocks near | Refusals near | SURVIVED with a PASS near (of 31) | WEAKENED with a PASS near (of 60) |
|---|---|---|---|---|
| 0.005 | 9 | 8 | 2 | 0 |
| 0.01 | 21 | 21 | 2 | 2 |
| 0.02 | 43 | 31 | 2 | 4 |

- Exact ties: 3: TOI-1062.01 systematics.background; TOI-973.01 period_alias.main; TOI-4188.01 period_alias.main.
- INCONCLUSIVE records: 374; decided only by refusals within 0.02: 0.
- FP events of part B: 17; with the failing statistic within 1 sigma of a threshold stated in the message: ['2208.01', '3165.01', '3753.01']; threshold not stated in the message: ['1008.01', '1061.01', '1323.01', '1536.01', '2111.01', '2173.01', '3060.01', '379.01', '401.01', '4135.01'].
- Fisher one-sided, 13 of 150 against 1 of 150: p = 0.000725.

**Reproduced:** False.

**Differences from the recommendation:**

- margin 0.02: (43, 31, 2, 4) against (43, 30, 2, 4)
- fragile FP events: ['2208.01', '3165.01', '3753.01'] against ['2111.01', '2208.01', '3165.01', '3753.01'] (unparsed: ['1008.01', '1061.01', '1323.01', '1536.01', '2111.01', '2173.01', '3060.01', '379.01', '401.01', '4135.01'])
