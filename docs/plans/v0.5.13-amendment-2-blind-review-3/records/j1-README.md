# J1: the count of decision-layer predicates, from source only

The maintainer's decision J1(b) (#218, comment 7222879969). Labels: `exploratory`,
`method_status: not_validated`. No golden was opened.

The committed unit `decision-count` (`docs/validation/v0.5.13/tools/decision_count.py`) wrote
[decision-count.json](decision-count.json).

**The rule, stated in full in the tool's docstring:**
- A *decision site* is the test of an `if`, `elif` or conditional expression whose branch, at its
  own level, does one of:
  - builds a `TestResult`;
  - calls `_inconclusive`, `_not_run` or `not_applicable_block`;
  - names a `TestStatus`;
  - assigns or appends to a decision name: `status`, `verdict`, `inconclusive_class`, `reason`,
    `eligible`, `can_fail`, `fail_allowed`, `flagged`, `decisive`, `failing`, `passed`.
- Its predicates are the atoms of the test after splitting `and`/`or`.
- The modules are grouped by the version that first uses them, following the dispatch of
  `pipeline.attack_candidate`.

| Version | New modules | New predicates | Cumulative |
| --- | --- | --- | --- |
| 1 | `pipeline`, `battery`, `gauntlet`, `core/verdict`, `ebcatalog`, `holdout` | 102 | **102** |
| 2 | `battery_v5`, `power`, `core/sensitivity`, `centroid_v5` | 28 | **130** |
| 3 | `battery_v51`, `battery_v51_diff`, `a0`, `core/inconclusive`, `duration` | 27 | **157** |
| 4 | `pipeline_v52`, `battery_v52`, `a0_v4` | 16 | **173** |

**What the count is, and is not:**
- **A feasibility count, and a floor.** The rule finds only decisions set directly in a branch.
  `power.py`, `a0.py`, `a0_v4.py` and `core/inconclusive.py` count 0, although they compute
  eligibility and classes through returned values. Their decisions reach the outputs through
  callers whose branches the rule does count, but not all are found.
- **Counted by module group, not by fixture.** A module counts whole in the first version that
  uses it.
- **Its size.** Next to the 2,746 sites of the full inventory (I2), the decision layer is about
  170 to 250 predicates over the four versions. That puts the scoped manifest of revision 5 in the
  order of days of work, not weeks.
