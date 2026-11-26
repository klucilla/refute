# v0.5.13 charter, amendment 1: preparation and Codex record

This record follows the maintainer's decision of 2026-11-26, item 6 (#218, comment 7204660147), and
the adviser's request:
- count the type mix of the 307 usable KELT-FP false positives;
- write a dated amendment 1 of the charter's section 5;
- have Codex review it in up to 3 rounds, in a new conversation, with divergence resolved by the
  more conservative option.

**The amendment is proposed, not approved:**
[../v0.5.13-charter-amendment-1.md](../v0.5.13-charter-amendment-1.md). The maintainer approves it
by its commit SHA before v0.5.14.

## The preparation (in the order of [log.jsonl](log.jsonl))

1. **[type_count.py](type_count.py) → [type-count.json](type-count.json).** The question was logged
   first.
   - The input: the v0.5.10 census table archived on the Drive, SHA-256 checked against the v0.5.10
     cleanup manifest.
   - The result, over 307 distinct TICs: SB1 172, NEB 49, SB2 27, EB1 17, BEB 17, EB2 8, Giant 6,
     Variable 6, RV0 5.
2. **[power_a1.py](power_a1.py) → [power-a1.json](power-a1.json):** the first draft's planning
   runs, 124 FPs and an all-307 mixture.
3. **[power_a1b.py](power_a1b.py) → [power-a1b.json](power-a1b.json):** the 135-FP variant.
4. **[power_a1c.py](power_a1c.py) → [power-a1c.json](power-a1c.json):** the corrected all-307
   sensitivity check (Codex's round 1, item 2).

All three power scripts import the frozen
[../v0.5.13-charter-prep/power_v2.py](../v0.5.13-charter-prep/power_v2.py) unchanged. They read no
data. The earlier runs are preserved.

## Codex's rounds

**The setup of every round:**
- Codex CLI 0.167.0-alpha.3.2, with the model of its local configuration;
- read only, sandbox read-only, threads 8 to 31;
- one thread, `01a21a02-d111-7d03-a18f-1f4bbe3af59d`: round 1 opened it, and rounds 2 and 3
  resumed it.

| Round | Prompt / answer | Verdict |
|---|---|---|
| 1 | [prompt](codex-round-1-prompt.md) / [answer](codex-round-1-answer.md) | `NOT_APPROVABLE`: 4 blocking items |
| 2 | [prompt](codex-round-2-prompt.md) / [answer](codex-round-2-answer.md) | `NOT_APPROVABLE`: items 1 to 4 applied; one blocking integration item and one editorial item |
| 3 | [prompt](codex-round-3-prompt.md) / [answer](codex-round-3-answer.md) | **`APPROVABLE`** |

**Round 1's key finding.** The first draft measured safety on the 135 non-SB1 FPs only. Codex found
that a relaxation of the approved gate. Its more conservative replacement was applied: the full
307-case cohort stays the confirmatory population, and the 135 non-SB1 and 172 SB1 are
prespecified descriptive groups. No threshold or denominator changes.

**Tokens.** Usage reported by a resumed thread is cumulative, so the thread's total is round 3's
report: **1,039,870 input (955,264 cached) and 12,363 output.**

**The SHA-256 of the answers:**
- round 1: `4da5d4bb…f79593`;
- round 2: `81fd1e54…6c1e2b`;
- round 3: `f6748425…6c2995`.
