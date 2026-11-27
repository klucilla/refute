# Codex's rounds 2 and 3 on the comparator, schema, span mapping and NR-A2's manifest (S5)

The maintainer's decision S5 (#218, comment 7227283917). These are the second and third rounds
of the conversation of R3(b), resumed with `codex_affinity.ps1 -Thread`, read only, on processors
8 to 31. Labels: `exploratory`, `method_status: not_validated`.

| Round | Freeze reviewed | Prompt | Answer (unchanged, in Portuguese) | Verdict |
| --- | --- | --- | --- | --- |
| 1 (R3(b)) | `8b15cede2a64ee37eff08869eae81b3bf5aff19b` | [../../r3/codex/prompt.md](../../r3/codex/prompt.md) | [../../r3/codex/answer.md](../../r3/codex/answer.md), SHA-256 `931e20fa9fe6e20a5dd44ae6f4d000c086bf8785dd8bc52dc4ac0328093b59cd` | `NOT_APPROVABLE`, 6 blocking |
| 2 | `780d49121cbc837ad870a5265dcae76365696dbd` | [prompt-r2.md](prompt-r2.md) | [answer-r2.md](answer-r2.md), 11,276 bytes, SHA-256 `0cf0212193db9e184275c5d803c564d5de02b217f113ea2710b355f15d9fbf8f` | `NOT_APPROVABLE`, 6 blocking |
| 3, the last | `2e86f48442f2a8c009075e5f346e48776c783696` | [prompt-r3.md](prompt-r3.md) | [answer-r3.md](answer-r3.md), 7,699 bytes, SHA-256 `72e2778df1f34c952b5a31b32f02e89100e734fa3dda330606e45ea5aa227f48` | **`NOT_APPROVABLE`, 4 blocking** |

**Thread:** `01a21e91-52fc-76d0-a749-6c5cda7ce113`. A resumed thread reports cumulative usage.
These numbers are copied from the events files by the unit `store-file`.

| After round | Input tokens (cached) | Output tokens (reasoning) |
| --- | --- | --- |
| 1 | 2,541,097 (2,383,488) | 12,958 (4,774) |
| 2 | 6,045,266 (5,820,928) | 25,623 (9,768) |
| 3 | 8,360,210 (8,098,432) | 34,479 (13,272) |

**Round 3's blocking items** (rendered in English; the answer is the source):
1. **The mixed-notation rule accepts changes to counts and versions.** It accepts
   `candidate.n_transits` from `100` to `100.00001`, and `v05.discovery_version` from `4` to
   `4.0`. Equal cadence rows still pass with an empty or `n/a` fraction or a `bogus` count.
2. **The claim entry is rebuilt as key + ":" + value,** so the whitespace around the separator
   is not compared.
3. **Nothing proves that the run came after the freeze, the manifest and the receipt's commit.**
   - The receipt's file list is taken from the receipt, not from the commit it attests.
   - `journal_bound` accepted an `after` written before its `before`, from another unit, with a
     different proof commit.
4. **Nothing ties the executed source to the authorized tree.** The record's head is not tied to
   the run's `before.head`, and the launcher does not require `src/` to match the authorized
   commit.

**What follows.** Under S5, round 3 was the last. The agent stopped without correcting these
items. The comparator and its schema are not approved, NR-A2's manifest is not committed, and
nothing ran on goldens.
