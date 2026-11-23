# v0.5.8: output stability of the v0.5 battery (exploratory)

**Exploratory.** Limits label: 'WEAKENED; does not meet D1, D2, D4, T2a'. `method_status: not_validated`. Never a verdict, a candidate or a disposition; the numbers describe these TOIs only. Each TOI-seeded record is compared with its v0.5.6 record.

Records: 167; complete: True; provenance: {'unknown': 84, 'same': 83}.

## total

- Outputs that changed: 19 of 167 (0.114; Wilson 95 % 0.074 to 0.171).
- Per output: INCONCLUSIVE -> ERROR 3; INCONCLUSIVE -> INCONCLUSIVE 56; INCONCLUSIVE -> SURVIVED 1; REFUTED -> ERROR 1; REFUTED -> INCONCLUSIVE 2; REFUTED -> REFUTED 22; REFUTED -> WEAKENED 1; SURVIVED -> INCONCLUSIVE 6; SURVIVED -> SURVIVED 22; WEAKENED -> ERROR 1; WEAKENED -> INCONCLUSIVE 4; WEAKENED -> WEAKENED 48.
- Status changes per test:
  - `aperture_depth`: 15 of 167 (0.090; Wilson 95 % 0.055 to 0.143); PASS -> INCONCLUSIVE 9; PASS -> NOT OK 4; FAIL -> NOT OK 1; FAIL -> INCONCLUSIVE 1
  - `centroid_shift`: 18 of 167 (0.108; Wilson 95 % 0.069 to 0.164); PASS -> INCONCLUSIVE 6; INCONCLUSIVE -> NOT OK 5; INCONCLUSIVE -> PASS 5; FAIL -> INCONCLUSIVE 1; INCONCLUSIVE -> FAIL 1
  - `duty_cycle`: 6 of 167 (0.036; Wilson 95 % 0.017 to 0.076); PASS -> NOT OK 5; FAIL -> PASS 1
  - `edge_events`: 6 of 167 (0.036; Wilson 95 % 0.017 to 0.076); PASS -> NOT OK 5; INCONCLUSIVE -> PASS 1
  - `event_consistency`: 23 of 167 (0.138; Wilson 95 % 0.094 to 0.198); PASS -> FAIL 5; FAIL -> PASS 2; INCONCLUSIVE -> FAIL 10; PASS -> NOT OK 2; INCONCLUSIVE -> NOT OK 2; FAIL -> INCONCLUSIVE 1; FAIL -> NOT OK 1
  - `nearby_contamination`: 6 of 167 (0.036; Wilson 95 % 0.017 to 0.076); FAIL -> NOT OK 3; PASS -> NOT OK 2; PASS -> FAIL 1
  - `odd_even`: 17 of 167 (0.102; Wilson 95 % 0.065 to 0.157); PASS -> INCONCLUSIVE 7; PASS -> NOT OK 4; PASS -> FAIL 1; FAIL -> NOT OK 1; FAIL -> PASS 2; INCONCLUSIVE -> PASS 2
  - `period_alias`: 7 of 167 (0.042; Wilson 95 % 0.020 to 0.084); PASS -> NOT OK 5; PASS -> INCONCLUSIVE 2
  - `plausibility`: 5 of 167 (0.030; Wilson 95 % 0.013 to 0.068); PASS -> NOT OK 4; INCONCLUSIVE -> NOT OK 1
  - `secondary_eclipse`: 12 of 167 (0.072; Wilson 95 % 0.042 to 0.121); PASS -> NOT OK 5; FAIL -> PASS 2; PASS -> FAIL 2; INCONCLUSIVE -> FAIL 1; PASS -> INCONCLUSIVE 1; INCONCLUSIVE -> PASS 1
  - `single_event`: 6 of 167 (0.036; Wilson 95 % 0.017 to 0.076); PASS -> NOT OK 5; INCONCLUSIVE -> PASS 1
  - `sinusoid`: 6 of 167 (0.036; Wilson 95 % 0.017 to 0.076); PASS -> NOT OK 5; INCONCLUSIVE -> PASS 1
  - `snr`: 5 of 167 (0.030; Wilson 95 % 0.013 to 0.068); PASS -> NOT OK 5
  - `systematics`: 18 of 167 (0.108; Wilson 95 % 0.069 to 0.164); PASS -> INCONCLUSIVE 12; PASS -> NOT OK 1; INCONCLUSIVE -> PASS 1; INCONCLUSIVE -> NOT OK 4
- Tests that never changed: none.

1. **Stable output:** not found: changed class 15 of 107 (0.140; Wilson 95 % 0.087 to 0.218) (at most 5 needed).
2. **Flip predictable from the records:** not found: near 12 of 150 (0.080; Wilson 95 % 0.046 to 0.135) (at least 80 % needed).
3. **More than one optimum:** FOUND: SNR differs by more than 10 % in 15 of 167 (0.090; Wilson 95 % 0.055 to 0.143); SNR missing 5 (at least 9 needed).
4. **The claim's events:** not found: FPs still REFUTED 14 of 17 (at least 15); part B planets REFUTED 1 of 40 (at most 2).

## same

- Outputs that changed: 10 of 83 (0.120; Wilson 95 % 0.067 to 0.208).
- Per output: INCONCLUSIVE -> INCONCLUSIVE 29; REFUTED -> INCONCLUSIVE 2; REFUTED -> REFUTED 15; REFUTED -> WEAKENED 1; SURVIVED -> INCONCLUSIVE 4; SURVIVED -> SURVIVED 9; WEAKENED -> ERROR 1; WEAKENED -> INCONCLUSIVE 2; WEAKENED -> WEAKENED 20.
- Status changes per test:
  - `aperture_depth`: 8 of 83 (0.096; Wilson 95 % 0.050 to 0.179); PASS -> INCONCLUSIVE 6; PASS -> NOT OK 1; FAIL -> INCONCLUSIVE 1
  - `centroid_shift`: 9 of 83 (0.108; Wilson 95 % 0.058 to 0.193); PASS -> INCONCLUSIVE 4; INCONCLUSIVE -> NOT OK 1; INCONCLUSIVE -> PASS 2; FAIL -> INCONCLUSIVE 1; INCONCLUSIVE -> FAIL 1
  - `duty_cycle`: 2 of 83 (0.024; Wilson 95 % 0.007 to 0.084); PASS -> NOT OK 1; FAIL -> PASS 1
  - `edge_events`: 2 of 83 (0.024; Wilson 95 % 0.007 to 0.084); PASS -> NOT OK 1; INCONCLUSIVE -> PASS 1
  - `event_consistency`: 10 of 83 (0.120; Wilson 95 % 0.067 to 0.208); FAIL -> PASS 1; INCONCLUSIVE -> FAIL 7; PASS -> NOT OK 1; PASS -> FAIL 1
  - `nearby_contamination`: 2 of 83 (0.024; Wilson 95 % 0.007 to 0.084); FAIL -> NOT OK 1; PASS -> FAIL 1
  - `odd_even`: 10 of 83 (0.120; Wilson 95 % 0.067 to 0.208); PASS -> INCONCLUSIVE 6; PASS -> NOT OK 1; FAIL -> PASS 2; INCONCLUSIVE -> PASS 1
  - `period_alias`: 1 of 83 (0.012; Wilson 95 % 0.002 to 0.065); PASS -> NOT OK 1
  - `plausibility`: 1 of 83 (0.012; Wilson 95 % 0.002 to 0.065); PASS -> NOT OK 1
  - `secondary_eclipse`: 7 of 83 (0.084; Wilson 95 % 0.041 to 0.164); PASS -> NOT OK 1; FAIL -> PASS 2; PASS -> FAIL 2; INCONCLUSIVE -> FAIL 1; PASS -> INCONCLUSIVE 1
  - `single_event`: 2 of 83 (0.024; Wilson 95 % 0.007 to 0.084); PASS -> NOT OK 1; INCONCLUSIVE -> PASS 1
  - `sinusoid`: 1 of 83 (0.012; Wilson 95 % 0.002 to 0.065); PASS -> NOT OK 1
  - `snr`: 1 of 83 (0.012; Wilson 95 % 0.002 to 0.065); PASS -> NOT OK 1
  - `systematics`: 8 of 83 (0.096; Wilson 95 % 0.050 to 0.179); PASS -> INCONCLUSIVE 7; PASS -> NOT OK 1
- Tests that never changed: none.

1. **Stable output:** not found: changed class 10 of 54 (0.185; Wilson 95 % 0.104 to 0.308) (at most 5 needed).
2. **Flip predictable from the records:** not found: near 8 of 64 (0.125; Wilson 95 % 0.065 to 0.228) (at least 80 % needed).
3. **More than one optimum:** FOUND: SNR differs by more than 10 % in 12 of 83 (0.145; Wilson 95 % 0.085 to 0.236); SNR missing 1 (at least 5 needed).
4. **The claim's events:** not found: FPs still REFUTED 14 of 17 (at least 15); part B planets REFUTED 1 of 40 (at most 2).
