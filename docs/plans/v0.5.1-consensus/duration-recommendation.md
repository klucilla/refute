## Verification

The headline agrees with the summary and records. P has 200 successful records, with 71% not detectable, 61.5% not detectable at target SNR ≥15, and one warning. PG has 190 successful records, with 83.2% not detectable and no warnings. The median uncertainties are about 5.3% for \(\sigma_{T_\max}/T_\max\) and 2.4% for \(\sigma_T/T_\max\).

For binaries, the reported ranges also match: warning fractions are about 25–52% overall, and detectable fractions about 2–47% under \(T_\max(2P)\). Under the per-geometry effect, detectability is 0–8%, with negative effects in 16–26% of cases. **Denominator note:** the binary rates use successful records; two binary cases have 1–2 generation failures each. PG also has 10 generation failures, leaving 190 of 200 successful records.

## Recommendation: item (d)

Make `duration_excess` diagnostic for this round. The current sensitivity rule would make 71% of P inconclusive, far beyond D2’s allowance: at most 29% could remain kept even if every other P case were kept, while D2 requires at least 86.8%. PG’s 83% inconclusive rate also raises a substantial non-regression concern.

The warning still has **diagnostic value**: it flags 25–52% of folded binaries overall, and 92–100% of low-impact binaries at SNR 20–30, while flagging none in the 0.6–0.8 impact bin. The limiting factor is the detectability rule: the roughly 5.3% TIC uncertainty floor leaves little room under the \(3+1.645\) threshold. The per-geometry effect is smaller and sometimes negative, so it makes the sensitivity limitation worse.

One caveat for the maintainer: the script labels \(\sigma_T\) as a development proxy, not the final A0 mechanism. Treat these results as strong feasibility evidence, not acceptance calibration. They support recording no built D1 route for binaries in this round and sending D1 jointly with D2 to the specified infeasibility path after confirmation. See [the measurement script](</C:/Projetos/refute/docs/validation/v0.5.1/feasibility/duration_measurement.py>) and [its summary](</C:/Projetos/refute/docs/validation/v0.5.1/feasibility/duration-measurement.json>).