# Main protocol (v0.3, WP7; plan sections 4, 5.2 and 10.1 step 5)

Written on 2026-10-17, **before** the paper round of the main sample is published and
before any paper of the main walk is drawn, read or triaged, after the pilot
(`calibration/v0.3/pilot/`). It fixes the frame, the round of the papers and its proof,
the walk, the triage, the development papers, the stop rule, the inventories and the
claim round, so that none of these can be tuned after a paper is seen. The rules of
reproduction, tolerance, attacks, budget, verdicts, coverage and right of reply are those
of `docs/plans/v0.3-plan.md` and of the acceptance documents, pinned below by commit and
SHA-256; this file only fixes what the plan leaves to the protocol. It follows `CLAUDE.md`
("Pre-registration process").

## Order of steps (each a separate commit, verifiable with git)

1. **This protocol** with `select_main.py`: committed and pushed as the **last commit of its
   push**. Its push run's `created_at` fixes the paper round (section "Random seeds").
2. **Walk, in batches**: `select_main.py --batch N` after the paper round; each batch's
   outputs (`main_walk_batch_NN.json`, `.md`) are committed unchanged before the next batch
   is read. The walk goes on through the batches without waiting for the maintainer's
   approvals of the previous ones.
3. **Triage** of the walked candidates in walk order (the agent proposes each decision with
   its evidence; the maintainer approves each acceptance and each rejection, in batches):
   `selection_log.md` committed with the approvals, and `main_sample.json` (the JSON list
   of the 5 arXiv IDs of the main sample, in walk order) once the 5 are accepted.
4. **Inventories** of the 5 papers of the main sample (plan 5.2); the 5 files and
   `inventories/SHA256SUMS` in one commit, the **last of its push**.
5. **Claim draw** after the claim round: `select_main.py --claims-after <inventory commit>`;
   `claim_draw.json` committed unchanged.
6. **Claims** written and approved, then the **lock** of the 5 papers (plan 10.1 steps 8
   and 9), each step stopping for the maintainer.

## Frame (plan 4.1, 4.2)

The snapshot of the pilot:

| Item | Value |
|---|---|
| Dataset | `pwc-archive/links-between-paper-and-code` (Hugging Face), CC BY-SA 4.0 |
| Revision | `56cc5c1938678c33dedebf5f74fc4e62e2c35381` |
| File | `data/train-00000-of-00001.parquet`, 41,364,239 bytes |
| SHA-256 | `c845ff642112a345f6271bf954d007c6698088d7de525f3f8d5f7d975f142c76` |

**Window and categories: 2023-01 to 2025-06; `cs.LG`, `stat.ML` and `cs.AI`.** The frame
adjustment `add-cs-ai`, the first alternative of the pilot protocol's ordered list whose
trigger fired (1 provisional acceptance of the 20 of the first pilot round, fewer than
3), from `refute.selection.filters.adjustment_record`, approved by the maintainer on
2026-10-17 (`calibration/v0.3/pilot/pilot_triage.md`). It is the one adjustment allowed
(W5.5); there is no other.

Filters, in order, with their counts in each batch's record (`apply_filters`): 0 arXiv ID
and repository URL present; 1 deduplication; 2 `is_official` and `mentioned_in_paper`;
3 new-style arXiv ID in the window; 5 one official repository per paper; 7 **every paper of
the two pilot rounds removed** (the 40 of `pilot_draw.json` and
`pilot_draw_additional.json`, read from the protocol commit). Then, for walked papers only,
4 the arXiv primary category in the list and 6 the out-of-scope keywords (the list of the
pilot protocol, unchanged, `select_pilot.KEYWORDS`).

**Declared bias** (plan 4.1): the archive stops in July 2025, so every paper is more than
15 months old; older repositories break more often.

## Random seeds: drand

Chain, genesis and period as in the pilot protocol (drand mainnet default chain, genesis
1595431050, period 30 s: round N is published at 1595431050 + (N - 1) x 30 s; the BLS
signature is verified by `refute.drand`; `seed = int(randomness, 16)`; if drand is
unavailable or a signature fails, the selection stops and the maintainer decides; the
source of randomness is never switched).

**Paper round (the maintainer's decision of 2026-10-17): the first drand round whose
publication time is at least one hour after the `created_at` of the GitHub Actions push run
of this protocol commit.** In exact terms: with `C` the earliest `created_at` among the
runs of `.github/workflows/ci.yml` in `klucilla/refute` started by the push (`event` =
`push`) of this protocol commit (`head_sha` = its full SHA), read from the GitHub API, the
paper round is the smallest N with `1595431050 + (N - 1) x 30 >= C + 3600` (Unix seconds,
UTC). `select_main.py` computes it (`select_pilot.round_after`) and checks the proof
(`refute.selection.publication.check_publication`: the repository, the workflow, the push
event, the commit, the margin, a clean tree, and every file of "Files covered" byte for
byte as in the protocol commit). A push starts a run only for its last commit, so this
commit is the last of its push; if it has no push run, the round is unknown and the walk
does not start (the maintainer decides). Git dates are never evidence.

**Claim round**: by the same rule, the first round published at least one hour after the
`created_at` of the push run of **the first commit of main after this protocol commit that
adds `calibration/v0.3/main/inventories/SHA256SUMS`**; a later commit that only keeps the
inventories is refused (plan 5.2 step 3, WP5 W5.11). The claim seed is never the paper
seed.

## Walk (plan 4.3)

1. Load the frame (SHA-256 checked); filters 0 to 5 with the window above, and 7.
2. Sort the remaining papers by `paper_arxiv_id` and shuffle them with `random.Random(seed)`
   (`refute.drand.shuffled`): the walk order. The interpreter
   (`refute.drand.interpreter_record`) is recorded with each batch.
3. Batch N reads the candidates in positions `25 x (N - 1) + 1` to `25 x N` of the walk:
   the arXiv metadata, the GitHub repository's metadata (existence, archived, default
   branch and its head commit, license as GitHub reports it), its README at that commit
   and the names of the files at the repository's root. The README texts stay in the local
   cache (they belong to their authors); the record keeps their URL, commit and SHA-256.
4. The script applies the mechanical rejections (`category_outside_list`, `out_of_scope` by
   keyword, `repository_unavailable`) and records the **`no_license` signal**: GitHub
   reports no license **and** no file whose name holds `licen`, `copying` or `notice` is at
   the root. **The signal is not a decision** (the maintainer's decision of 2026-10-17): the
   agent proposes `no_license` only after reading the README, and the maintainer approves
   it in a batch.
5. Batch N needs batch N - 1 committed. The commit of each candidate is the head of its
   default branch when its batch is read, recorded with it (plan 6.1 then fixes the
   version used, D-8).

**Retries** (#22, W5.7): every query makes at most 3 attempts in total against transient
errors (timeouts, HTTP 5xx, connection errors), with a 15-second backoff; a candidate still
unread after them (its metadata, README or root listing) stops the walk for the
maintainer; it is never rejected or passed over silently. A root listing the GitHub API
refuses with a client error (4xx) gives no `no_license` signal, which is only a signal.

## Triage (plan 4.4)

The full triage of each candidate not rejected mechanically: the paper, the README and the
repository's files at the recorded commit (LICENSE, dependency files, scripts, data
loaders, configuration), every reason of the closed list with its evidence (file and line,
paper page or section). **No code is run.** One reason is recorded per rejection (the first
that applies, in the order below, with the others that also apply noted).

Closed list (plan 4.4): `out_of_scope`; `no_license` (no license or explicit compatible
authorization in LICENSE, README or other relevant files; D-5);
`data_requires_registration_or_terms`; `data_license_incompatible`;
`weights_license_incompatible`; `outside_v03_experimental_scope`; `data_not_public`;
`needs_paid_api_or_credentials`; `stated_compute_over_budget`; `requires_gpu`;
`dataset_over_budget`; `pretrained_download_over_budget`; `ambiguous_repository`;
`repository_unavailable`; `no_reproduction_instructions`; `category_outside_list`.

Thresholds (plan 4.4): declared datasets above **5 GB** in total; declared model weights
above **2 GB** in total; compute stated by the paper or the README for producing the
claims above the **192 CPU-hours** of the base reproduction.

**`requires_gpu`, operational definition** (the maintainer's decision of 2026-10-17,
coherent with the pilot's decision on 2401.08819). A paper is rejected as `requires_gpu`
when either holds:

- **(a)** the repository's code fixes CUDA with no CPU path: the device is a GPU with no
  setting that runs on CPU (for example `model.cuda()` or `device = "cuda"` with no
  condition and no option that selects the CPU, or a CUDA-only extension that must be
  compiled for the code to run);
- **(b)** the paper or the README states the computation time of its own experiments
  (training or evaluation) only in GPU time, with no figure in CPU time.

Examples: (1) a README that says "training takes 6 hours on one A100" and gives no CPU
figure is `requires_gpu` by (b), even if the code runs on CPU; (2) a paper whose only cost
statement is "we report the time of 200,000 steps ... on a server with a 32-core CPU and an
A5000 GPU" is `requires_gpu` by (b) (the pilot's 2401.08819, approved on 2026-10-17). A paper
that states no computation time and whose code has a CPU path is not `requires_gpu`. When
(b) holds, the compute threshold above is not used for that paper (`requires_gpu` comes
first).

**Recorded in the triage, not a reason:** a repository whose environment can be built only
from its own Dockerfile is triaged as any other; version 1 of the docker backend does not
build a Dockerfile (decided by the maintainer on 2026-10-17; wp3-acceptance.md W3.10b), so
the triage notes it, and its run would end `INCONCLUSIVE` on Refute's side, never as the
artifact's failure.

"Looks hard", "looks broken" or "probably won't reproduce" are never reasons.

## Main sample, development papers and the stop rule

- **Main sample**: the **first 5 accepted** papers in walk order (plan 4.3, D-19). A paper
  admitted is never replaced (plan 10.4).
- **Development papers** (the maintainer's decision of 2026-10-17, plan 4.5 note; the
  alternative "development papers from the main walk" of D-4's table): the accepted papers
  in **positions 6 and 7** of the accepted list, under the same triage, outside the main
  sample. They run as soon as they are approved, in parallel with the inventories and
  claims of the main sample, within 96 CPU-hours each (plan 7.3), and never set or tune a
  threshold, a tolerance or a budget (plan 4.5). Their verdicts are computed and recorded,
  and never counted.
- **Stop rule** (the maintainer's decision of 2026-10-17): if the walk passes **300
  candidates** (12 batches) without **7 accepted** (5 main and 2 development), the walk
  stops; the agent brings the maintainer the rate of each reason and the options the plan
  allows. `select_main.py` refuses a 13th batch.

## Inventories (plan 5.2)

Granularity one numeric cell; canonical ID table, row and column as printed; order the
paper's reading order; the main-results tables are those the abstract or the introduction
refers to as the main result; eligibility: producible by the repository's instructions
within the budget; the format of `refute.selection.inventory` (`refute-ml-inventory-2`),
stored in canonical JSON. Each file: `calibration/v0.3/main/inventories/<arxiv_id>.json`;
their SHA-256 in `calibration/v0.3/main/inventories/SHA256SUMS` (`<sha256>  <file name>`).
Every candidate's transcription, type and reference are approved by the maintainer before
the inventory commit.

## Claim draw (plan 5.2 step 4)

`refute.selection.inventory.draw_published_claims` after the publication proof of the
inventory commit, which covers exactly the 5 inventories of the papers listed in
`main_sample.json` (each file named `<arxiv_id>.json` and holding that paper's
inventory; anything else is refused before the proof): K = 3; when the inventory has an eligible comparison and none of the 3 is
a comparison, the 3rd is replaced by the first comparison in the shuffled order; with 3
candidates or fewer, all; replacement after the draw only for a reason of the closed list,
by the next candidate of the same type when the comparison must be kept.

## Rules pinned from the plan and the acceptance documents

Reproduction and tolerance (plan 6.2, D-10), attacks and their order (6.3, 7.4), budget
(7.3: 384 CPU-hours per paper, 192 basic; 96 per development paper), verdicts and coverage
(8), right of reply (9), the reading interval, the margin M and the tolerance T
(wp3-acceptance.md 1.4a). The measured maxima D and S of WP6 V22 and the constants C, P, N
and σ are written into the claims before the lock (plan 10.1 step 9); they are never
adjusted because of a run of the sample or of the development papers.

| Document | Commit | SHA-256 |
|---|---|---|
| `docs/plans/v0.3-plan.md` | `e07db78d704c30cf9e98ea406db34388c1024d61` | `178ffb1a24f531fd28d485d118e896b318fd52322c9adcdb6b0307b7849ad7b6` |
| `docs/validation/v0.3/wp2-acceptance.md` | `c5d8b12f6a411de801d0bbd8024d2f808d94543f` | `d8c97a2709aa07ca497f4d200ca82ff5c473aa6888e9e4939629b8afe3605d90` |
| `docs/validation/v0.3/wp3-acceptance.md` | `914779dbfc3879af0adc5787cb729ceab51438ef` | `36d6611039233a871a81823cbc740eb217232dada8e0ce39846cce4e4c0bb3de` |
| `docs/validation/v0.3/wp4-acceptance.md` | `dcb266102f7a169a6743468fb21f390915666a73` | `2ebac5073fe4aa2748de1eb84b4d77efb563cde86beea8ac949ca1b131dffe5a` |

## Publication proof

| Item | Value |
|---|---|
| Repository | `klucilla/refute` |
| Workflow | `.github/workflows/ci.yml` |
| Margin | 1 hour before the paper round, and 1 hour before the claim round |
| Push | this protocol commit, and the inventory commit, are each the last commit of their push |
| Files covered | `calibration/v0.3/main/PROTOCOL.md`, `calibration/v0.3/main/select_main.py`, `calibration/v0.3/pilot/select_pilot.py`, `calibration/v0.3/pilot/pilot_draw.json`, `calibration/v0.3/pilot/pilot_draw_additional.json`, `src/refute/__init__.py`, `src/refute/drand.py`, `src/refute/selection/__init__.py`, `frame.py`, `filters.py`, `walk.py`, `publication.py`, `inventory.py`, `src/refute/core/__init__.py`, `canonical.py`, `hashing.py`, `pyproject.toml`, `uv.lock` (`select_main.PROTOCOL_FILES`). At each run they must be byte for byte the files of the protocol commit, and `refute` must be loaded from this checkout |

## Commands (from a clean main, Python of the project's environment)

```
.venv/Scripts/python.exe calibration/v0.3/main/select_main.py --protocol-commit <full SHA of this commit> --frame .cache/round6/frame/train-00000-of-00001.parquet --batch 1
.venv/Scripts/python.exe calibration/v0.3/main/select_main.py --protocol-commit <same SHA> --frame <same file> --batch <N>
.venv/Scripts/python.exe calibration/v0.3/main/select_main.py --protocol-commit <same SHA> --claims-after <full SHA of the inventory commit>
```
