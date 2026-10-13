# Test expectations changed after a failure (development runs, before the final self-test)

The self-test driver (`selftest_v2.py`) was written together with the harness, and its
development runs (in `.cache/population/v2-dev/`, not part of this record) found errors in the
driver itself. Every expectation, input or command of the driver that changed after a failure
is listed here; none of them changed the harness, the comparator or the D6 script. The final
self-test ran once with the driver as it is now.

| Step | What failed | What changed | Why |
|---|---|---|---|
| injected differences, "one byte of an array" | the comparator reported the byte in `lc/year`, element 11136, not in `lc/flux` | the injected element moved from `lc/flux` element 123456 to `aux/pixels/1/flux` element 1500000 (block 11 of its segment), and the driver now refuses an element outside its segment | test error: `lc/flux` has 37440 elements, so element 123456 was past its end and the byte fell in a later segment; the comparator located that byte correctly (segment, block and element) |
| result-record injections, "a missing field" | the comparator reported the path with kind `only_in_left`; the driver expected `only_in_right` | the expected kind is `only_in_left` | test error: the field is deleted from the right-hand copy, so it exists only in the left-hand record; `only_in_left` is the correct report |
| overhead, v1 runs | `population.py generate` exited with a usage error (`--cache` is required) | the v1 command passes `--cache` with an empty folder (nothing is written with `--no-store`) | command error: v1 requires `--cache` even when it writes nothing |
| analysis, the list of cases | the declaration held 3 cases instead of 4 | `planet-below-white-0101` replaced by `planet-below-white-0111`, and the driver now refuses a case that is not in the population | test error: index 101 is not in the determinism population (it keeps index 10 j + (j mod 5); for the three-year planets that is 100, 111, 122, 133, 144); 0111 is a three-year planet below threshold with white noise, the mechanism the case was meant to cover |

Changes of the harness during development that were not changes of expectations: the
microcode revision of the machine record was read from the wrong bytes (the registry value
has 4 bytes, not 8); the first generation of a set printed "byte-identical to the earlier
generations" with no earlier generation; and the metrics mode did not yet carry the paired
comparisons, the redraws and the run provenance checks of v1. Each was corrected before the
final self-test, which ran with new declarations (a declaration names the harness by SHA-256,
so every earlier diagnostic campaign refuses the corrected harness).

A first attempt of the final self-test, started in `.cache/population/v2-selftest/`, was
stopped during its overhead step when the missing paired comparisons were found; its lines
are at the top of `selftest-v2-log.txt`, before the marker line, and it is superseded by the
run in `.cache/population/v2-selftest-final/`.
