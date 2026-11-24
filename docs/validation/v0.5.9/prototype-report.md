# v0.5.9: ephemeris entry, exploratory prototype

**Exploratory.** Limits label: 'WEAKENED; does not meet D1, D2, D4, T2a'. `method_status: not_validated`. Never a verdict, a candidate or a disposition; the numbers describe these 24 TOIs only. E enters through the TOI's ephemeris, S through the battery's own search, on the same input bytes.

Rows: 48; run state: complete; structurally valid: True; every TOI complete: True.

## Q1: the 14 changes, E against S

- **Without consensus:** the same decided class in 3 of 14 (0.214; Wilson 95 % 0.076 to 0.476); both INCONCLUSIVE 1 of 14 (0.071; Wilson 95 % 0.013 to 0.315); the same class of either kind 4 of 14 (0.286; Wilson 95 % 0.117 to 0.546). Over the 9 pairs whose two fits stayed on the TOI ephemeris: same decided class 3, both INCONCLUSIVE 1.
- **With consensus:** the same decided class in 1 of 14 (0.071; Wilson 95 % 0.013 to 0.315); both INCONCLUSIVE 9 of 14 (0.643; Wilson 95 % 0.388 to 0.837); the same class of either kind 10 of 14 (0.714; Wilson 95 % 0.454 to 0.883). Over the 9 pairs whose two fits stayed on the TOI ephemeris: same decided class 1, both INCONCLUSIVE 7.

## Q2: the 8 controls keep their class

- Without consensus: 8 of 8 (1.000; Wilson 95 % 0.676 to 1.000).
- With consensus: 8 of 8 (1.000; Wilson 95 % 0.676 to 1.000).

## Q3: the two numerical ERRORs of v0.5.8

- TOI-734.01 E: OK, WEAKENED; warning failure in: nearby_contamination; evaluated True; centroid_shift INCONCLUSIVE; guarded: {'p1:centroid_shift': "numerical failure, INCONCLUSIVE by the v0.5.9 prototype's guard: sector 63's sky covariance (observed) is not positive definite", 'p2:centroid_shift': "numerical failure, INCONCLUSIVE by the v0.5.9 prototype's guard: sector 63's sky covariance (observed) is not positive definite", 'p3:centroid_shift': "numerical failure, INCONCLUSIVE by the v0.5.9 prototype's guard: sector 90's sky covariance (observed) is not positive definite", 'p4:centroid_shift': "numerical failure, INCONCLUSIVE by the v0.5.9 prototype's guard: sector 63's sky covariance (observed) is not positive definite", 'p5:centroid_shift': "numerical failure, INCONCLUSIVE by the v0.5.9 prototype's guard: sector 90's sky covariance (observed) is not positive definite", 'p6:centroid_shift': "numerical failure, INCONCLUSIVE by the v0.5.9 prototype's guard: sector 63's sky covariance (observed) is not positive definite"}.
- TOI-734.01 S: OK, WEAKENED; warning failure in: nearby_contamination; evaluated True; centroid_shift INCONCLUSIVE; guarded: {'base:centroid_shift': "numerical failure, INCONCLUSIVE by the v0.5.9 prototype's guard: sector 90's sky covariance (observed) is not positive definite", 'p1:centroid_shift': "numerical failure, INCONCLUSIVE by the v0.5.9 prototype's guard: sector 90's sky covariance (observed) is not positive definite", 'p2:centroid_shift': "numerical failure, INCONCLUSIVE by the v0.5.9 prototype's guard: sector 63's sky covariance (observed) is not positive definite", 'p3:centroid_shift': "numerical failure, INCONCLUSIVE by the v0.5.9 prototype's guard: sector 63's sky covariance (observed) is not positive definite", 'p4:centroid_shift': "numerical failure, INCONCLUSIVE by the v0.5.9 prototype's guard: sector 90's sky covariance (observed) is not positive definite", 'p5:centroid_shift': "numerical failure, INCONCLUSIVE by the v0.5.9 prototype's guard: sector 63's sky covariance (observed) is not positive definite", 'p6:centroid_shift': "numerical failure, INCONCLUSIVE by the v0.5.9 prototype's guard: sector 90's sky covariance (observed) is not positive definite"}.
- TOI-5218.01 E: OK, INCONCLUSIVE; could not be decided: systematics; evaluated True; centroid_shift INCONCLUSIVE; guarded: {'base:centroid_shift': "numerical failure, INCONCLUSIVE by the v0.5.9 prototype's guard: sector 78's sky covariance (observed) is not positive definite"}.
- TOI-5218.01 S: OK, INCONCLUSIVE; could not be decided: systematics; evaluated True; centroid_shift INCONCLUSIVE; guarded: {'base:centroid_shift': "numerical failure, INCONCLUSIVE by the v0.5.9 prototype's guard: sector 78's sky covariance (observed) is not positive definite"}.
- All four ended with a status and a reason: True; all four evaluated: True.

## Q4: decided outputs, without and with consensus

- the 24, E: without 10 of 24 (0.417; Wilson 95 % 0.245 to 0.612); with 8 of 24 (0.333; Wilson 95 % 0.180 to 0.533); lost to consensus 2.
- the 24, S: without 20 of 24 (0.833; Wilson 95 % 0.641 to 0.933); with 12 of 24 (0.500; Wilson 95 % 0.314 to 0.686); lost to consensus 8.
- the 14 changes, E: without 3 of 14 (0.214; Wilson 95 % 0.076 to 0.476); with 1 of 14 (0.071; Wilson 95 % 0.013 to 0.315); lost to consensus 2.
- the 14 changes, S: without 13 of 14 (0.929; Wilson 95 % 0.685 to 0.987); with 5 of 14 (0.357; Wilson 95 % 0.163 to 0.612); lost to consensus 8.

## Q5: cost

- probe `epoch`, whole unit: 60 units, CPU mean 59 s, median 59 s, max 185 s.
- probe `epoch`, evaluation: 60 units, CPU mean 57 s, median 57 s, max 181 s.
- probe `period`, whole unit: 60 units, CPU mean 59 s, median 60 s, max 185 s.
- probe `period`, evaluation: 60 units, CPU mean 57 s, median 57 s, max 181 s.
- probe `duration`, whole unit: 60 units, CPU mean 59 s, median 58 s, max 184 s.
- probe `duration`, evaluation: 60 units, CPU mean 56 s, median 56 s, max 180 s.
- E, fit: 24 units, CPU mean 15 s, median 10 s, max 68 s.
- E, base evaluation: 21 units, CPU mean 59 s, median 43 s, max 205 s.
- S, fit: 24 units, CPU mean 17 s, median 15 s, max 44 s.
- S, base evaluation: 24 units, CPU mean 59 s, median 43 s, max 205 s.
- fetch: 24 units, CPU mean 8 s, median 8 s, max 15 s.
- Downloads (manifest): 5.85 GB over 24 TOIs (mean 0.244).
- Downloads (metered): 5.87 GB over 24 TOIs (mean 0.245).
- Ledger: {'cpu_hours_charged': 4.1216, 'downloaded_bytes_charged': None, 'disk_peak_bytes': 4773538245, 'batches': 6, 'state': 'complete', 'state_reason': 'every required unit of the set is recorded'}.

## Descriptions (not marks)

- Entries unresolved: {'E': 3}; fits on the TOI ephemeris: {'E': 21, 'S': 20}; first disagreeing axis: {'S:period': 1, 'S:epoch': 7, 'E:epoch': 1, 'E:duration': 1}.
- Over the 24 complete pairs of the 24 (0 incomplete, left out), same decided class: without consensus 10 of 24 (0.417; Wilson 95 % 0.245 to 0.612); with consensus 8 of 24 (0.333; Wilson 95 % 0.180 to 0.533).
