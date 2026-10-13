# D6, the full run of 2026-10-13

The full D6 of Amendment 4, item 15 (clarifications, item 13): 40 cases of the `determinism`
population, points M0 and M3, the seven configurations, two repetitions each, run from
17:56:29 to 18:20:45 UTC at commit `ed4e728` with `population_v2.py`
`8b3b6ad6aca6e713636b04e40db5a7d253c05458c8b143c38d984100072c1f82`,
`population_compare.py` `0e62dcc4dc99a53fcc319aa513734f31e9d877406cc81e56ea97c80042e2f01f`
and `d6.py` `bef4ab9db52b059ae63bcb6bc27bdc77ec2db51cf8bf762c13278d76f5f70466` (R2 checked
against HEAD before the start). The input campaigns were diagnostics under the git-ignored
`.cache/population/d6-full/`.

**Result: PASS, counts as the D6.** The six conditions of a valid conclusion held; 38 pairs
compared with `d6-science`, 0 differences; 0 control mismatches and 0 check 1 problems; the
control pass found exactly the declared differences (F x R-idx 156, R-rev x R-idx 160,
R-shf x R-idx 144, P24 x P12 112, P24 x F 64, E x R-idx 0, every repetition pair 0); the
negative control passed 11 of 11. A negative result holds only for the contrasts of the
matrix and the inputs exercised.

| File | SHA-256 | Content |
|---|---|---|
| `d6-report.json` | `c47008b43996dc3b080f18e074d5122077bcfa9f94941ba2254c02d06d72e064` | the report of `d6.py check` |
| `d6-declaration.json` | `719e2cfe417b58beec47e251031df23699f7ccd763186e40d5f1c2465f431667` | the D6 declaration (cases, assignment, environments) |
| `d6-timing.json` | `8b416056383cb65c48c650d5a37aa1408b1540064352e515541cd73143604304` | wall time of each step; 1456 s in total |
| `d6-memory.json` | `e62d9813b7b5670f37816ea1aeac705c2021f43b8cc9c64c8afbd0c52b15f0a6` | physical memory in use on the whole machine, sampled every 2 s: 34.38 GB before the start, peak 42.56 GB |

The four files are copied byte for byte from the run (their SHA-256 checked after the copy).
The memory figures cover the whole machine, other programs included.
