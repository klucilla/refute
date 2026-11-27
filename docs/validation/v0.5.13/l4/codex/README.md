# Codex's round on the frozen margin manifest (#226)

The maintainer's decisions N3, N4 and O1 (#218). One round, a new conversation, read only, through
`.cache/v04/tools/codex_affinity.ps1` (processors 8 to 31), on the freeze commit
`ba94f3a6ccca09c6868ee00d80429bb09ac01be2`. Labels: `exploratory`, `method_status: not_validated`.

| Item | Value |
| --- | --- |
| [prompt.md](prompt.md) | SHA-256 `453476ec4c4c7ec1c84c8c9f2e2c60189d5b0444f9aac588cc776030e87e0ecb`, 6,406 bytes |
| [answer.md](answer.md), unchanged | SHA-256 `51d67f62937c63663867359a0be80ea112982901af516ab2e93dffc8cda3e933`, 16,851 bytes |
| Thread | `01a21e44-ddad-7c32-85e2-fa0d1c38e0ba` |
| Tokens | 2,923,924 input (2,746,752 cached), 17,524 output (7,153 reasoning) |
| **Verdict** | **`NOT_APPROVABLE`**: 8 blocking items |
| **N3** | **yes**: N1(c) changes the acceptance condition of sections 4 and 6(c); N2 by itself does not |

**What follows from the answer.**
- **The stop.** Under decision O1(c), Codex's "yes" on N3 is a stop. The maintainer's adviser
  proposes a blind review. The freeze stays as the record; no check of amendment 2 and no NR-A2
  ran.
- **Blocking items 1 to 7:**
  - the decision layer misses predicates that reach outputs through object fields, helpers and
    comprehension filters (`rule_block`, `choose_sectors`, `aggregate`);
  - guards and instances need per-path resolution (`search_fn`, `corrections_on`);
  - the reach rule needs evaluation order and per-instance evidence;
  - the loop rule must apply to every row of a serialized instance;
  - some operands marked absent can be reconstructed;
  - the schema's wide patterns tolerate some thresholds and compare some measurements exactly;
  - the comparator has shortcut and claim-inventory gaps.

  None is fixed here. The fixes belong to the next revision, after the maintainer's decision.
- **The declared inputs:** Codex judged that the view of `verdict-v4.txt` could have guided the
  choice of tests, roles and `global_ephemeris` in the map, and that source allows deriving them
  independently. It judged that the `refute_version` search could have guided that field's
  treatment or D4. The record does not establish an actual influence.
