# Pilot protocol (v0.3, WP5/WP7; plan sections 4.1 to 4.5, D-2 to D-4)

Written on 2026-10-17, **before** the pilot's drand round is published and before any
v0.3 paper is drawn, triaged or read. It fixes how the pilot papers are drawn, how they
are triaged, how the development papers are chosen, and the one adjustment of the frame
the pilot may trigger, so that none of these can be tuned after the papers are seen. It
follows `CLAUDE.md` ("Pre-registration process") and `docs/plans/v0.3-plan.md` section
10.1, step 4.

## Order of steps (each a separate commit, verifiable with git)

1. **This protocol** with `select_pilot.py`: committed and pushed **at least one hour
   before** drand round 6561446 is published (2026-10-17T22:00:00Z). The proof of the push
   time is the `created_at` of the GitHub Actions run of that commit (`refute.selection.
   publication`; git dates are not evidence). If the push cannot happen an hour before,
   the rounds are recomputed and this file is changed **before** it is committed.
2. **Draw**: `select_pilot.py` is run after the round; its outputs (`pilot_draw.json`,
   `pilot_draw.md`) are committed unchanged.
3. **Pilot triage** (metadata and README only): the agent proposes each decision with its
   evidence; the maintainer approves each one; `pilot_triage.md` is committed.
4. **Full triage** of the provisional acceptances, in pilot order, until 2 pass: the
   **development papers** (D-3); committed with the maintainer's approvals.
5. **Adjustment** of the frame, if the trigger of section "Adjustment" fires: recorded in
   the pilot log; it changes the main protocol, which is written after this.

## Frame (plan 4.1)

| Item | Value |
|---|---|
| Dataset | `pwc-archive/links-between-paper-and-code` (Hugging Face), CC BY-SA 4.0 |
| Revision | `56cc5c1938678c33dedebf5f74fc4e62e2c35381` (last modified 2025-09-10T12:20:22Z) |
| File | `data/train-00000-of-00001.parquet`, 41,364,239 bytes |
| URL | `https://huggingface.co/datasets/pwc-archive/links-between-paper-and-code/resolve/56cc5c1938678c33dedebf5f74fc4e62e2c35381/data/train-00000-of-00001.parquet` |
| SHA-256 | `c845ff642112a345f6271bf954d007c6698088d7de525f3f8d5f7d975f142c76` (equal to the file's LFS object id) |

Retrieved and measured on 2026-10-17 (no randomness used): 300,161 rows; the mechanical
filters leave 70,303 papers (counts below); **no `paper_arxiv_id` ends in a version
suffix** (`vN`), so none is removed or normalized for that reason (#59, review of #78).

| Filter (plan 4.2) | Rows after | Papers after |
|---|---|---|
| 0. arXiv ID and repository URL present | 287,453 | 207,415 |
| 1. deduplication (`paper_arxiv_id`, `repo_url`) | 287,453 | 207,415 |
| 2. `is_official` and `mentioned_in_paper` both true | 157,528 | 151,743 |
| 3. new-style arXiv ID in 2023-01 to 2025-06 | 75,017 | 72,557 |
| 5. one official repository per paper | 70,303 | 70,303 |

Filters 4 (category) and 6 (keywords) need arXiv metadata, so they are applied to the
drawn papers only (section "Pilot triage"). Filter 7 (pilot papers removed) applies to
the main walk, not here.

**Declared bias** (plan 4.1): the archive stops in July 2025, so every paper is more than
15 months old; older repositories break more often.

## Random seed: drand

| Item | Value |
|---|---|
| Chain | drand mainnet, default chain, `8990e7a9aaed2ffed73dbd7092123d6f289930540d7651336225dc172e51b2ce`, `pedersen-bls-chained`, public key as in `src/refute/drand.py` |
| Genesis, period | 1595431050, 30 s; round N is published at genesis + (N - 1) x 30 s |
| **Pilot round** | **6561446**, published **2026-10-17T22:00:00Z** |
| **Additional pilot round** (used only if the first does not give 2 development papers, plan 4.5) | **not fixed in advance**: the first round published at least **one hour after** the GitHub Actions push run of **the first commit of main after the protocol commit** whose `pilot_triage.md` records the maintainer-approved triage of the first round with the line `Additional pilot round: needed`; a later commit that only keeps that record is refused |

The pilot round was set on 2026-10-17 at about 18:50Z against the latest published round
then, 6561064 (2026-10-17T18:49:00Z): 6561446 = 6561064 + 382 rounds of 30 s. A fixed
additional round could be published before the first triage ends and so steer it; the
rule above makes it unknown until that triage is committed. The
script verifies the BLS signature (`refute.drand`, the code of v0.2's
`select_targets.py`), takes `seed = int(randomness, 16)`, and refuses to run before the
round time or without the proof of publication. **If drand is unavailable or a signature
fails, the pilot stops and the maintainer decides**; the source of randomness is never
switched.

## Draw

1. Load the frame (its SHA-256 checked), apply filters 0 to 5 above.
2. Sort the remaining papers by `paper_arxiv_id`, shuffle with `random.Random(seed)`
   (`refute.drand.shuffled`); the interpreter (`refute.drand.interpreter_record`) is
   recorded with the draw.
3. The **pilot papers** are the first **20** of the shuffled list. The additional round,
   if used, shuffles the same filtered frame with its own seed, removes the papers of the
   first pilot (recomputed from round 6561446 and checked against the committed
   `pilot_draw.json`), and takes the first 20 of what remains.
4. For each pilot paper, read only: the arXiv metadata (export API: primary category,
   title, abstract, latest version) and, from GitHub, the repository's metadata (exists,
   archived, default branch and its head commit, license as GitHub reports it) and its
   README at that commit. The README text stays in the local cache (it belongs to its
   authors); the draw records its URL, commit and SHA-256.

**Retries** (#22, W5.7): every query makes at most **3 attempts in total** against
transient errors (timeouts, HTTP 5xx, connection errors), with a **15-second** backoff
between them; a candidate still unread after them stops the draw for the maintainer; it is
never rejected silently. The draw files are created exclusively: a second run never
overwrites them.

## Pilot triage (plan 4.4 and 4.5; metadata and README only)

Applied in pilot order. The agent proposes each decision with its evidence; the
maintainer approves every acceptance and every rejection. **No code is run.**

- **Mechanical, by the script:** `category_outside_list` when the arXiv primary category
  is not `cs.LG` or `stat.ML`; `out_of_scope` when the title or abstract holds a keyword
  of the list below (whole words, any case); `repository_unavailable` when the repository
  does not exist or is archived.
- **From the README and the repository metadata, by the agent with evidence (file and
  line):** `no_license` (no license reported by GitHub and none stated in the README),
  `requires_gpu`, `no_reproduction_instructions`, `data_requires_registration_or_terms`,
  `data_not_public`, `needs_paid_api_or_credentials`, `stated_compute_over_budget`,
  `dataset_over_budget`, `pretrained_download_over_budget`,
  `outside_v03_experimental_scope`, `out_of_scope` (the CLAUDE.md reasons only). The
  thresholds are those of plan 4.4: datasets above 5 GB, weights above 2 GB, stated
  compute above 192 CPU-hours (compute stated only in GPU time is `requires_gpu`).
- A paper with no such reason is **accepted provisionally**. "Looks hard" or "probably
  won't reproduce" are not reasons.

**Out-of-scope keywords** (filter 6; CLAUDE.md: medical or diagnostic claims, dual-use
biology or chemistry): `clinical`, `clinic`, `patient`, `patients`, `medical`,
`medicine`, `diagnosis`, `diagnostic`, `diagnostics`, `disease`, `diseases`, `cancer`,
`tumor`, `tumour`, `radiology`, `healthcare`, `health care`, `electronic health records`,
`ehr`, `mri`, `x-ray`, `ecg`, `eeg`, `surgical`, `surgery`, `drug`, `drugs`,
`pharmaceutical`, `molecule`, `molecules`, `molecular`, `protein`, `proteins`,
`genomic`, `genomics`, `dna`, `rna`, `pathogen`, `pathogens`, `virus`, `viral`, `toxin`,
`toxins`, `toxicity`, `chemical`, `chemistry`, `bioweapon`, `biosecurity`. A human may add
rejections only for the CLAUDE.md out-of-scope reasons, never remove one.

## Development papers (D-3, D-4)

The 2 development papers are the first 2 provisional acceptances, in pilot order, that
pass the **full triage** of plan 4.4: the paper itself and the repository files at the
recorded commit (LICENSE, dependency files, scripts, data loaders, configuration), every
reason of the closed list, with evidence; the maintainer approves each decision. If one
fails, the next provisional acceptance is tried. If the 20 pilot papers do not give 2,
the additional pilot round is drawn under the same rules (at most one); if that is still
not enough, the phase stops for the maintainer. The development papers stay outside the
main sample and are used only to find engine crashes, I/O and accounting errors, and to
exercise the experimental reproduction (plan 10.2), within 96 CPU-hours each; never to
set or tune a threshold, a tolerance or a budget.

## Adjustment of the frame (D-2, W5.5)

An ordered list of alternatives with a trigger, applied by `refute.selection.filters.
choose_adjustment`: the **first** alternative whose trigger fires is applied, at most
once, before the main protocol is committed; there is no choice among alternatives. The
count is the number of the 20 first-round pilot papers accepted provisionally.

| Order | Name | Trigger | Window | Categories |
|---|---|---|---|---|
| 1 | `wider-window` | fewer than 1 accepted provisionally | 2021-01 to 2025-06 | `cs.LG`, `stat.ML`, `cs.AI` |
| 2 | `add-cs-ai` | fewer than 3 accepted provisionally | 2023-01 to 2025-06 | `cs.LG`, `stat.ML`, `cs.AI` |

With 3 or more provisional acceptances the frame is not adjusted. The decision and its
reason go into the pilot log (`adjustment_record`).

## Publication proof

| Item | Value |
|---|---|
| Repository | `klucilla/refute` |
| Workflow | `.github/workflows/ci.yml` |
| Margin | 1 hour before the **first** pilot round (6561446), for both draws |
| Push | the protocol commit, and the triage commit that records the need for an additional round, are each the **last commit of their push**: a push starts a run only for its last commit |
| Files covered | every file that decides the draw: `calibration/v0.3/pilot/PROTOCOL.md`, `calibration/v0.3/pilot/select_pilot.py`, `src/refute/__init__.py`, `src/refute/drand.py`, `src/refute/selection/__init__.py`, `frame.py`, `filters.py`, `walk.py`, `publication.py`, `pyproject.toml`, `uv.lock`. At each run they must be byte for byte the files of the protocol commit, and `refute` must be loaded from this checkout |

## Commands (after the round, from a clean main, Python of the project's environment)

```
.venv/Scripts/python.exe calibration/v0.3/pilot/select_pilot.py --protocol-commit <full SHA of the protocol commit> --frame .cache/round6/frame/train-00000-of-00001.parquet
.venv/Scripts/python.exe calibration/v0.3/pilot/select_pilot.py --protocol-commit <same SHA> --frame <same file> --additional-after <full SHA of the triage commit>
```

The second only if the approved triage records the need.
