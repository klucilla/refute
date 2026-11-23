# v0.5.6 part B: the claim's verdict

**SURVIVED** (p = 4.726e-05 <= 0.05 and the guard holds). Limits label: 'WEAKENED; does not meet D1, D2, D4, T2a'. `method_status: not_validated`. The claim measures agreement with TFOPWG dispositions on overlapping photometry, never that the battery detects false positives.

| Stratum | Drawn | Losses (cap) | Denominator | Events | Rate | Wilson 95 % |
|---|---|---|---|---|---|---|
| planet | 150 | 2 (15) | 150 | 1 | 0.007 | 0.001 to 0.037 |
| fp | 150 | 3 (15) | 150 | 17 | 0.113 | 0.072 to 0.174 |

```
{
 "primary_fisher_one_sided_p": 4.726007352337025e-05,
 "primary_fisher_one_sided_p_exact": "169884831031/3594679787093252",
 "alpha": 0.05,
 "guard": {
  "planet_event_rate": 0.006666666666666667,
  "rate_max": 0.05,
  "wilson95_upper": 0.03679283977481815,
  "upper_max": 0.1,
  "holds": true
 },
 "secondary_refuted_fisher_one_sided_p": 8.972184394659935e-05,
 "secondary_survived_planet_above_fp_p": 0.005503973573758897
}
```
