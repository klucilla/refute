# Result of the development run of 2304.14390 (DSMCS), 2026-10-18

The development verdict is computed and recorded but does not count (plan 4.5).

## Run

- **Unit and code.** The run was `refute-dev335.service` on the Refute VM, started at
  2026-10-18T14:33:27Z by `scripts/vm/launch-paper.sh` at Refute commit `5f83565`.
- **Network.** The build ran in the build profile (allowlist proxy). The run phase was
  approved only after the port was switched to the pull profile (no proxy) and that profile
  was read back from the status.
- **The claim file.** `dossier/claim_file.json` is byte-identical to `claim.json` (SHA-256
  `4a7a1c510d3079fb77b20bca890ecc265d2abf1bf310185c66bd91c4dca0e5ea`).
- **The dossier.** `dossier/dossier.json` has SHA-256
  `719b66c8392396d553458979a49d82100998f716aaac0f60a3ab5a7467c8c9b4`.

**Logs.** The logs are not published here: the publication rule for logs is fixed before
any seal (#59). The VM keeps them, whole, in the run's dossier.

**What can be checked here, and what is the operator's account.** The published
`dossier.json` holds the verdicts, the checks, the extracted token and the accounting. Some
statements above come from the agent's operational record and have no proof in what is
published:
- the unit, the start time and the Refute commit the run used;
- the switch to the pull profile;
- the resolved path and the bytes of the file read;
- the digest of the built image.

The dossier's contract does not record them yet, an item of #59.

## What it showed

| Part | Outcome |
|---|---|
| Build | `requirements_compiled` (Python 3.10, torch 1.13.1), exit 0, 28 CPU-seconds |
| Run | one run of the README's DAIS command, exit 0, 30,331 CPU-seconds (8.4 of the 96 CPU-hours), 42 minutes |
| Accounting | valid, completeness `complete` |
| Extraction (W3.11a) | the one folder the run named by its date and time was found, and `$.elbo` = -3.9716 was read from it |
| `data_present` | not applicable (`generated_by_repository_code`), carried in the verdict |
| `metric_extracted` | `INCONCLUSIVE`: no route shows the examples (the declared `printed_count` found no count, as `NOTES.md` expected) |
| Claim | **`INCONCLUSIVE`** |

The base-reproduction predicate computed on the one value holds: |-3.97 - (-5.35)| ≤ 1.54,
the tolerance from the reported SD. That reading is recorded only; it decides nothing,
because a gate before it is `INCONCLUSIVE`.

**Coverage of this development run: partial.** The build, the run, the accounting and the
extraction path worked. The coverage of the evaluated population cannot be shown for this
repository without editing its code (`NOTES.md`).
