# population_v4: gate 1's evidence

The acceptance record: [../population-v4-acceptance.md](../population-v4-acceptance.md) (commit
`9bb0aaf`). The tests and their failing first run: commit `dc99a32`
([first-run.json](first-run.json)). The code: commit `610bc02`, with Codex's review fixes in
`b9d40c1`. Every output here was generated on `b9d40c1`, in the project's environment before the
dependency update of 2026-10-27. **No lot ran and the engine never ran** (no search, gauntlet,
holdout or verdict).

| Output | Criterion | Result |
|---|---|---|
| [population-1.json](population-1.json), [population-2.json](population-2.json), [population-3.json](population-3.json) | 1 to 6, 8 | Every check passed in each generation, with its required coverage: the 5860 cases of the acceptance population (3730 white, 2130 correlated), each built in memory and discarded; 323 850 994 cadences; 24 480 expected SNRs recomputed independently; 311 475 872 cadences of rebuilt flux (every case but the blends); every attempt replayed |
| [manifest-1.json](manifest-1.json), [manifest-2.json](manifest-2.json), [manifest-3.json](manifest-3.json), [determinism.json](determinism.json) | 7 | The three generations (22 workers, index order; 13, reverse; 7, interleaved) byte-identical: manifest SHA-256 `aee9ecac…12ce2` for all three |
| [sabotages.json](sabotages.json) | 9 | S1 to S9 (ten sabotages) each caught for its named reason, each control passing with positive coverage |
| `order.json` (next commit) | 9 | The order record, tests, code, sabotages' output, checked over the git history |

**The redraws** (population-1.json, `redraws` and `redraws_by_reason`): 380 of the 5860 cases
needed more than one layout attempt (153 rejections by D1, a label collision; 255 by D4, an
orbit or a gap pushed out of its bounds by the quantization or the jitter); 29 parameter redraws
for commensurate periods and 4 for the depth limit, both `population_v2`'s own rules. No other
reason occurs, and none comes from an engine output.

**What this does not show.** The acceptance population is a check population with its own
prefix; it is never analysed. The development population, X6 and X7 are generated later, each
under its own declaration and authorization, and each generation repeats the checks of
criteria 1, 3, 4 and 5 and the three-generation rule. After the dependency update of 2026-10-27
the acceptance population's digests are generated again and compared, and any difference is
recorded.
