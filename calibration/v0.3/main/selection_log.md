# Selection log of the main sample (v0.3)

Protocol: `calibration/v0.3/main/PROTOCOL.md` (commit b01bc78), paper round 6561788.
Walk outputs: `main_walk_batch_NN.json` and `.md`, each committed unchanged before the next
batch was read. This log records the full triage of every candidate the batches did not
reject mechanically, with the maintainer's approval of each decision. Only approved
decisions are entered here; proposals not yet approved are not.

Source records: the licence GitHub reports, the names at the repository's root and the
README (URL, commit and SHA-256) of each candidate are in its batch file, read by
`select_main.py` at the time of the batch. Every licence statement of this log has its
source URL, read time and literal value in `sources/triage-sources.md`; other external
facts carry their URL and the date they were read.

## Walk record

| Batch | Positions | Commit | Note |
|---|---|---|---|
| 1 | 1-25 | 703dece | |
| 2 | 26-50 | 551a91f | |
| 3 | 51-75 | d848259 | |
| 4 | 76-100 | 9b0795a | The first attempt stopped at position 100 on an arXiv HTTP 429 (a 4xx, not retried by the protocol); nothing was written. Rerun approved by the maintainer on 2026-10-18 and recorded in issue #156 (comment of 2026-10-18T03:14:48Z) before it ran, with the reason and the exact procedure; the rerun started after 03:15Z, more than 60 minutes after the 429 (about 01:01Z), and its output was written at 03:17:10Z; code, seed, round and pause unchanged. |
| 5 | 101-125 | b5a0df5 | |
| 6 | 126-150 | ee38121 | |
| 7 | 151-175 | 57e5dcc | |
| 8 | 176-200 | 7010092 | |
| 9 | 201-225 | d44111e | |
| 10 | 226-250 | 5aa77ef | |
| 11 | 251-275 | 1287ea8 | |
| 12 | 276-300 | cdd3faa | The 12th batch: the walk reached the protocol's limit of 300 candidates. |

**Stop rule.** The walk read 300 candidates (12 batches). The protocol stops the walk when
it passes 300 candidates without 7 accepted (5 main and 2 development); `select_main.py`
refuses a 13th batch. At the end of batch 12 no candidate has an approved acceptance, and,
by the agent's proposals still awaiting the maintainer's decisions, at most 4 candidates
could be accepted, so the
condition cannot be met: the walk stops and the maintainer decides (rates by reason and the
options are reported to the maintainer).

## Clarifications decided after candidates were seen (2026-10-18)

The maintainer decided two clarifications of the triage on 2026-10-18, in the message that
also approved the rerun of batch 4 (labelled "about 00:20" Brasília time; received by the
agent before 2026-10-18T03:14:48Z), **after** positions 1 to 75 had been triaged and after
candidates
2305.19518 (position 1) and 2407.17459 (position 37) raised the questions. They apply in the
same way to every candidate, including those triaged before the decision. Their full text
is in `PROTOCOL-clarifications.md` (C1 and C2); `PROTOCOL.md` is not edited, because
`select_main.py` checks it byte for byte against the protocol commit.

- **C1:** `data_requires_registration_or_terms`, `data_not_public`,
  `data_license_incompatible` and `needs_paid_api_or_credentials` apply at the level of the
  main-results tables; a candidate is rejected for one of them only if no candidate cell
  can be produced without the restricted data or the paid API.
- **C2:** for a dataset redistributed in the repository without a licence, the licence of
  the dataset's original source counts, recorded in a `sources/` record.
- **The pilot:** pilot candidate #16 was triaged with the whole-paper reading; the pilot
  is closed and outside the sample, and is not revisited.
- **Re-application to the candidates triaged before 2026-10-18:** see the "Effect of C1
  and C2" column below.

## Decisions approved on 2026-10-18 (positions 1 to 75)

Approved by the maintainer on 2026-10-18, in the same message as C1 and C2.

| Pos | arXiv | Repository (commit) | Decision | Evidence | Effect of C1 and C2 |
|---|---|---|---|---|---|
| 2 | 2310.05250 | lucianoavinas/lowrank-gnn-kernels | rejected: `no_license` | no licence reported by GitHub, no licence file at the root, none in the README | none (code licence) |
| 3 | 2506.00577 | masterzhou1/recon | rejected: `no_license` | as above | none |
| 5 | 2305.00604 | felix-petersen/isaac (MIT) | rejected: `no_reproduction_instructions` | the repository holds only `examples/mnist.py` (a figure); no script for Table 1 | none |
| 7 | 2504.01550 | aim-intelligence/repbend | rejected: `no_license` | as #2 | none |
| 10 | 2501.18768 | michael-s-yao/dynamo (MIT) | rejected: `out_of_scope` | `setup.sh` trains surrogates for TFBind8 (DNA), UTR (RNA), ChEMBL and PenalizedLogP (molecules): dual-use biology and chemistry (CLAUDE.md; "dna", "rna", "molecules" are in the protocol's keyword list) | none |
| 18 | 2405.07414 | kyungeun-lee/tabularbinning | rejected: `no_license` | the README's table of contents lists "License" but there is no such section; no licence file | none |
| 20 | 2505.11298 | rpaolino/genvsexp | rejected: `no_license` | as #2 | none |
| 32 | 2305.08676 | IBM/TRAIL (Apache-2.0) | rejected: `requires_gpu` (a) | README "TRAIL requires a GPU for training"; `code/game/gpu_server.py:153` asserts `torch.cuda.is_available()` | none for the decision; the data source github.com/zsoltzombori/plcop (MPTP2078, M2K) has no licence reported by GitHub and no licence file at its root (`sources/triage-sources.md`); the licence of the original MPTP2078 source was not checked, so `data_license_incompatible` may also apply and would then come first in the order |
| 41 | 2305.16886 | eliacunegatti/mge-snn (Apache-2.0) | rejected: `no_reproduction_instructions` | the README points to `graph_data/paper_results` for sections 4.2.1-4.2.3, absent from the tree; no script for the regression, feature-importance or ranking results | none |
| 44 | 2301.13139 | c-alfano/approximate-mirror-policy-optimization | rejected: `no_license` | as #2 | none |
| 72 | 2401.15973 | hamedhemati/omsi | rejected: `no_license` | the repository holds a README only ("SOURCE CODE TBA") | none |
| 74 | 2408.16725 | gpt-omni/mini-omni (MIT) | rejected: `pretrained_download_over_budget` | `lit_model.pth` of gpt-omni/mini-omni is 2,777,267,002 bytes (> 2 GB); the README covers demo and inference only | none |

Positions 1 and 37 were decided after C1 and C2; their decisions are entered when approved.
