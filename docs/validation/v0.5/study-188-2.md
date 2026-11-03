# #188 study, second run: the BLS power at the true period

Run again with the quantity the specification asks for (docs/plans/v0.5-acceptance.md, WP7), approved by the maintainer and recorded in issue #188 before the run. The first run (`study-188.md`) is kept unchanged as a recorded deviation. Same curves, inversion and modes. Synthetic; not a false-alarm rate; it changes no reporting category of the calibration. `method_status: not_validated`.

Processor time: 0.091 h over 22 workers. Record: `study-188-2.json`.

| Group | Curves | Gate passed | ... at the true period or an alias | Median BLS power at the true period | Median SDE at the true period |
|---|---|---|---|---|---|
| eb/without_prewhitening | 10 | 10 | 7 | 197.9 | 3.4 |
| eb/with_prewhitening | 10 | 10 | 7 | 197.9 | 3.4 |
| sinusoid/without_prewhitening | 10 | 5 | 5 | 12.2 | 5.1 |
| sinusoid/with_prewhitening | 10 | 2 | 2 | 5.8 | 1.1 |
