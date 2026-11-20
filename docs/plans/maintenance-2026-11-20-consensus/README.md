# Consensus record: the GitHub maintenance of 2026-11-20

Codex's reviews under the maintainer's decision of 2026-11-20, 12:40 (#217): the dependency updates
of both repositories, the archive branches, the decommissioning commands of the VM, and the texts
of #217's closing. Codex ran read only (sandbox read-only), through
`.cache/v04/tools/codex_affinity.ps1` on processors 8 to 31. Every answer is stored here unchanged,
with the model, the effort and the Codex CLI version. Agents propose; nothing here is a verdict on a
claim.

## The maintenance of 2026-11-20 (items 1, 2, 4 and 5)

Codex's review of the dependency updates of both repositories (item 4), the record of the archive branches (item 2), the decommissioning commands of the VM and the archive script (item 5), and the texts of #217's closing and of #218 (item 1), up to 3 rounds. Codex CLI 0.167.0-alpha.3.2 answered in Portuguese, and the answers are stored unchanged.

| Round | File | Model, effort | Verdict | SHA-256 |
|---|---|---|---|---|
| 1 | [maint-round-1-answer.md](maint-round-1-answer.md) | gpt-6.1-sol, high | 4a `SURVIVED` (conditional on the full suite and the 9 locks); 4d `WEAKENED` (lock counts by path); 4b-1 `SURVIVED`, option B; 4b-2 `WEAKENED` (stop before rewriting the saved output); 4b-3 `SURVIVED` (certifi left out and reported); 4c `SURVIVED`, `not_used`; 2 `WEAKENED` (a column label); 5 `WEAKENED` (VM states, the switch, disk chains, a concrete A5); 1 `SURVIVED` | `ba7feecf8b0fa971cef814bfa42528dccfeac00ad5c414ac28e590adb90efb1b` |
| 2 | [maint-round-2-answer.md](maint-round-2-answer.md) | gpt-6.1-sol, high | 4a `SURVIVED`; 4d `WEAKENED` (one unit test failed for the environment); 4b `WEAKENED` (the cutoff comment); 2 `SURVIVED`; 5 `WEAKENED` (the whole disk chain and checkpoints); 4c `SURVIVED` | `455860eabe3f238cc698743b5fd2b59f892db633659d286b88290aa9226a0306` |
| 3 | [maint-round-3-answer.md](maint-round-3-answer.md) | gpt-6.1-sol, high | 4d `SURVIVED`; 4b `SURVIVED`; 5 `SURVIVED` | `9c9274357c6f248ac5e6e78539b9da85a1384391f24e632998d7bfedc78d547f` |

The tokens are cumulative over the conversation `maint`:

- round 1: 930,020 input (830,208 cached) and 10,142 output;
- round 2: 1,750,779 input (1,630,208 cached) and 16,021 output;
- round 3: 2,224,525 input (2,091,264 cached) and 17,929 output;

The conversation counts **151,190** review tokens (the last round's uncached input plus output).

Applied as Codex wrote them:
- **4b-2:** the most conservative option is kept. The synthetic output is not rewritten, and the generator's update stays on a local branch of the site until the maintainer decides on the exception.
- **4d:** the lock changes are reported by path: 64 changed, 45 added, 35 removed, 403 entries. The unit tests were run again with Git's bash first on the PATH: 285 of 285.
- **2:** the column label was corrected on #59.
- **5:** the commands now require both VMs off, check the switch, walk every disk chain including checkpoints, and gate part D on A5's exit 0 and "problems 0".
- **4b:** the cutoff comment of `synthetic/pyproject.toml` was corrected.
