# #188 study: does an inverted curve keep structure at the true period?

Bounded study of v0.5 WP7 (docs/plans/v0.5-acceptance.md), run once on synthetic curves (seeds of the development rule). It changes no reporting category of the calibration: inverted curves and signal-bearing hosts are reported apart by the plan whatever this shows. Not a false-alarm rate. `method_status: not_validated`.

Processor time: 0.028 h. Record: `study-188.json`.

| Group | Curves | Gate passed | ... at the true period or an alias | Median box SNR at the true period |
|---|---|---|---|---|
| eb/without_prewhitening | 10 | 10 | 7 | 21.5 |
| eb/with_prewhitening | 10 | 10 | 7 | 21.5 |
| sinusoid/without_prewhitening | 10 | 5 | 5 | 5.1 |
| sinusoid/with_prewhitening | 10 | 2 | 2 | 3.7 |
