# D7 — Diagnosis of the generation divergence (2026-10-12)

Harness `408020676340…` unchanged; nothing committed; outputs in `.cache/population/diag/`.

## D0 — evidence preserved
`dev-gen/` intact: 16 files (`diag/dev-gen-SHA256SUMS`), checked again at the end.

## D1 — repetitions without instrumentation (harness, generate --no-store)
| Run | Workers | Order | Manifest SHA-256 | Time |
|---|---|---|---|---|
| A | 24 | index | 206d7af1… | 268.1 s |
| B | 12 | shuffle:20261012 | 4073d96a… | 252.6 s |
| A2 | 24 | index | 4073d96a… | 277.3 s |
| A3 | 24 | index | 4073d96a… | 269.1 s |
| B2 | 12 | shuffle:20261012 | 4073d96a… | 255.9 s |
| C | 24 | shuffle:20261012 | 1d7f7b7c… | 274.2 s |
| D | 12 | index | 4073d96a… | 260.2 s |

Divergences (only the case's `sha256`; parameters, SNRs and draws equal):
- A: planet-below-white-0016 (32742c90… instead of f4dc3550…) and planet-below-white-0100 (e06fa3a4… instead of 46a2101f…);
- C: no_transit-none-white-1731 (5b2cf0b6… instead of 4a7acd5f…);
- B = A2 = A3 = B2 = D byte for byte. A2 and A3 do not reproduce A; the divergent cases change.

## D2 — instrumented (configuration A, 9 times)
0 divergences in 9 × 5200 cases; PID and sequence per process in `d2-run*/sequences.json`; pools of 1 thread. The divergence did not reproduce with the instrumentation; the hypothesis remains open.

## D3 — bytes
No divergent variant was captured (A and C were hash only; D2 did not diverge). The comparison of arrays could not be made. Control: the same variant written in different runs is identical in every array.

## D4 — new process vs reused process
3 cases × 5 scenarios (new; the exact sequence of D2; the earlier ones in index order; 50 cases without a planet; 400 cases), each in a new process, 12 in parallel: the 15 targets and the 1786 cases of the sequences gave the repeated value of B. No dependence on the history.

## Conclusions, corrections and test: see the session message (not published).
