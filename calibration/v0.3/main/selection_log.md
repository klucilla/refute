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

Positions 1 and 37 were decided after C1 and C2; their decisions are entered below.

## Clarification C3 and decisions approved on 2026-10-18 (about 09:30 Brasília time)

The maintainer's message labelled about 09:30 Brasília time decided C3 (the size thresholds
take the reading of C1; `PROTOCOL-clarifications.md`), **after** all 300 candidates had
been triaged and after positions 1, 112 and 230 raised the question; approved the agent's
proposals for positions 76 to 300 and for positions 1 and 37, with the decisions below;
accepted that `PROTOCOL-clarifications.md`, separate from `PROTOCOL.md`, carries the notes
on the protocol; and decided amendment 1 (`AMENDMENT-1.md`).

**Re-application of C3 to all 300 candidates.** Only positions 1, 112 and 230 change
(from a size rejection to an acceptance). Every other size rejection has no candidate cell
within all the limits: 74 (every cell needs the 2.78 GB Mini-Omni weights), 90 (the cells
without a paid API need Llama-3-70B), 108 (every fold needs all 63,649 images, about
67 GB), 239, 254 and 282 (every cell needs a model above 2 GB or a paid API).

**Strict order of the reasons.** For 32, 101 and 257 the reasons that come before
`requires_gpu` in the order are checked before the rejection profile is published; the
result is entered here.

| Pos | arXiv | Repository (commit) | Decision | Evidence |
|---|---|---|---|---|
| 1 | 2305.19518 | puar-playground/LRA-diffusion | **accepted** (C3) | the WebVision 1.0 cells exceed 5 GB (the small version alone is 26 + 16 GB, data.vision.ee.ethz.ch, read 2026-10-18) and leave the inventory; ILSVRC2012, WebVision terms and Clothing1M leave by C1; the CIFAR cells remain, to be confirmed in the inventory |
| 37 | 2407.17459 | sewen007/hoiltr (cd67ee1) | rejected: `data_license_incompatible` (C2) | the four datasets of the results: LAW from the DELTR experiments repository, original source Wightman (1998)/LSAC with no known licence (an intermediate repository is not the original source); COMPAS (propublica/compas-analysis) with no licence; (W)NBA with no source named; Boston Marathon (Kaggle) with licence "Unknown". The paid APIs are only in an optional step (C1) |
| 78 | 2402.08946 | jackmiller2003/tiny-gen | rejected: `no_license` | no licence reported by GitHub, none at the root, none in the README |
| 80 | 2409.16546 | AlignedQuant/AlignedKV | rejected: `no_license` | as 78 |
| 85 | 2408.03572 | yifansun99/2d-oob-joint-valuation | rejected: `no_license` | as 78 (the README is two lines) |
| 90 | 2407.06423 | ServiceNow/insight-bench (33c27c1) | rejected: `pretrained_download_over_budget` | the GPT cells need a paid API (C1); the other cells ("llama-3-70b", LLaMA-3-Eval) need meta-llama/Meta-Llama-3-70B (`insightbench/utils/eval_utils.py:33`), 30 shards of about 4.6 GB |
| 101 | 2502.13308 | CampanulaBells/HUGE-GAD (bdf8d2a) | rejected: `requires_gpu` (a) | `main.py:26` `device_ids = 0`; `:56-57` `.to(device_ids)`; `:85` `.cuda()`; no CPU path (strict order: see above) |
| 106 | 2412.15365 | BANG23333/LISA | rejected: `no_license` | as 78 |
| 108 | 2308.02682 | bitbucket gsudmlab/explainingfulldisk (e7d6481) | rejected: `dataset_over_budget` | 63,649 Helioviewer JP2 magnetograms; two files measured at 1,053,540 and 1,075,500 bytes (2026-10-18), about 67 GB; every fold uses all images |
| 111 | 2405.03003 | Chaos96/fourierft | rejected: `no_license` | as 78; the repository holds a README and an image (the code is in Hugging Face PEFT) |
| 112 | 2502.16782 | UCF-Lou-Lab-PET/cipher-prune-inference (69a0f97) | **accepted** (C3) | the declared models (BERT-Medium/Base/Large, GPT2-Base) total about 2.33 GB; the Acc cells and the cells needing the weights leave the inventory; the Time and Comm cells from the repository's EzPC tests remain, to be confirmed in the inventory |
| 130 | 2310.14166 | wongzhenhao/ELGNN (abc51e1) | rejected: `out_of_scope` | the only benchmark, ogbl-ddi, is a drug-drug interaction network; "drug" is in the protocol's keyword list (coherent with 10) |
| 137 | 2305.11476 | Jackory/RPBT (dbf3696) | rejected: `requires_gpu` (b) | "one AMD EPYC 7702 64-Core Processor and one GeForce RTX 3090 GPU"; runs of "almost 12 hours" (PSRO 34 hours), no CPU figure: example (2) of the protocol |
| 145 | 2303.05774 | bszek213/nfl_combine | rejected: `no_license` | as 78 (an empty "License" heading) |
| 150 | 2402.07191 | dingfangyu/GSINA | rejected: `no_license` | as 78 |
| 158 | 2505.19313 | martaaparod/concept_reachability (3f0171b) | rejected: `outside_v03_experimental_scope` | the results are figures only; no results table |
| 170 | 2303.08625 | andruekonst/HRBM | rejected: `no_license` | as 78 |
| 173 | 2405.17879 | langfengQ/tree-diffusion-planner (cebcc00) | rejected: `requires_gpu` (b) | "All experiments are run on the NVIDIA GeForce RTX 3080 GPU core"; planning times only on that GPU (Table F.1) |
| 180 | 2410.03424 | josephjwilson/cayley_graph_propagation (73a2c7c) | rejected: `no_reproduction_instructions` | the repository holds one quick-start notebook; the experiment code is elsewhere |
| 189 | 2402.00904 | Skyorca/Awesome-Graph-Domain-Adaptation-Papers | rejected: `outside_v03_experimental_scope` | a survey; the repository is a paper list |
| 191 | 2310.18496 | craymichael/PostHocExplainerEvaluation | rejected: `no_license` | as 78 |
| 208 | 2505.22756 | cfpark00/RL-Wall (4f1ed95) | rejected: `outside_v03_experimental_scope` | the results are figures; the only table holds hyperparameters (training on H100 GPUs also noted) |
| 213 | 2312.11176 | ningliu-iga/clawNO (1c549db) | rejected: `requires_gpu` (b) | the only time statement: "The runtime is evaluated on a single NVIDIA V100 GPU" (Table 5) |
| 214 | 2410.22376 | krafton-ai/Rare-to-Frequent | rejected: `no_license` | as 78 |
| 217 | 2406.15283 | acoursey3/freeway-anomaly-data (b10c34b) | rejected: `no_reproduction_instructions` | the repository recorded in the frame holds the dataset and a demo; the paper's code is in another repository, and Refute does not change repository by choice |
| 225 | 2312.09961 | jaayala/risk_aware_contextual_bandit | rejected: `no_license` | as 78 |
| 230 | 2407.11735 | walline/prosub (8a28cf3) | **accepted** (C3) | ImageNet100 (Kaggle, 5.63 GB, licence "Unknown") and ImageNet30 cells leave the inventory (C1, C3); the CIFAR cells remain, to be confirmed in the inventory |
| 239 | 2406.13948 | tsinghua-fib-lab/CityGPT (ab8d19b) | rejected: `pretrained_download_over_budget` | ChatGLM3-6B, Llama3-8B, Qwen2.5-7B (Qwen2.5-7B-Instruct alone about 15.2 GB); the other cells need paid APIs |
| 254 | 2412.07472 | tsinghua-fib-lab/SmartAgent (2f2e11e) | rejected: `pretrained_download_over_budget` | backbone Qwen-VL (10 shards of about 1.9 GB) and SeeClick; the other cells need GPT-4/4V |
| 257 | 2503.07315 | qiaoruiyt/GSR (d6f48e5) | rejected: `requires_gpu` (b) | "Running time ... obtained from running a single job on one NVIDIA RTX 3080 GPU with two AMD EPYC 7543 CPUs", no CPU figure (strict order: see above) |
| 280 | 2303.07310 | StanfordCBCL/gROM (687481e) | rejected: `out_of_scope` | reduced-order models of blood flow on patient-specific geometries, healthy and diseased |
| 282 | 2407.03856 | mansicer/Q-Adapter (991ac8b) | rejected: `pretrained_download_over_budget` | every script uses Meta-Llama-3.1-8B-Instruct (four shards, about 16 GB) |

The other candidates of batches 4 to 12 were rejected mechanically (their batch files).

**Accepted so far, in walk order:** 2305.19518 (1), 2502.16782 (112), 2407.11735 (230);
each with the cells confirmed in its inventory.

## Amendment 1 walk (protocol commit 073692b) and the decisions of 2026-10-18 (about 09:50)

| Batch | Positions | Commit | Note |
|---|---|---|---|
| 13 | 301-325 | 1d03bd1 | the first batch read from the amendment's commit |
| 14 | 326-350 | b95c01d | the 7th acceptance (by the agent's proposals) is position 338 |
| 15 | 351-375 | 2e0c815 | read before the stop; the agent then stopped starting batches (AMENDMENT-1 item 7); batch 16 was started and stopped before it wrote anything |

The maintainer's message labelled about 09:50 Brasília time decided C4 to C9
(`PROTOCOL-clarifications.md`) after positions 1 to 375 had been triaged and the inventories
drafted, and approved the following decisions.

**Strict order of the reasons (approved).** 32 keeps `requires_gpu` (a): the original
source of MPTP2078 (github.com/JUrban/MPTP2078, `COPYING`) allows GPL-3.0 or CC BY-SA 3.0
and the paper states no total compute above the budget. 257 keeps `requires_gpu` (b):
CivilComments is CC0 (WILDS), so C1 does not reject. **101 changes** to
`data_license_incompatible`, with `requires_gpu` (a) also noted: Amazon and YelpChi come
through CARE-GNN (Apache-2.0), an intermediate repository, and their original sources
(McAuley and Leskovec 2013; Rayana and Akoglu 2015) state no licence; the JODIE/SNAP page
(Reddit) states none; the source of the Facebook dataset (Xu et al. 2022) was not located.

| Pos | arXiv | Repository (commit) | Decision | Evidence |
|---|---|---|---|---|
| 308 | 2406.11016 | dwgnr/optimized-speculative-sampling (823428f) | rejected: `requires_gpu` (a) | the method is a custom CUDA kernel compiled with nvcc (`--use_custom_sampler`); the times are per-step GPU profiles (Table 6) |
| 309 | 2309.15704 | antoinedemathelin/maxwent-expe (c67aa62) | **accepted** | Table 2 (C9); UCI data CC BY 4.0, kin8nm from DELVE (C5) |
| 317 | 2310.01224 | Yukayo/MobGT | rejected: `no_license` | no licence reported by GitHub, none at the root, none in the README |
| 324 | 2404.17673 | hariharan20/MLDEnv | rejected: `no_license` | as 317 |
| 325 | 2302.12465 | amazon-science/page-link-path-based-gnn-explanation (cdb7160) | **accepted** | Table 4, UserItemAttr cells (the authors' synthetic graph, repository MIT-0); AugCitation leaves (C2) |
| 331 | 2412.09842 | uzn36/DP-SynGen | rejected: `no_license` | as 317 |
| 335 | 2304.14390 | jzenn/DSMCS (72f9ebe) | **accepted** | Tables 1 to 3; synthetic targets; CPU path |
| 338 | 2407.20299 | ggflow123/DDRL (6ffb086) | **accepted** | Tables 2 and 3 (Procgen); teacher models on Hugging Face (apache-2.0); CPU path |
| 341 | 2407.12415 | Zh-XY22/FreDF | rejected: `no_license` | as 317 (no README) |
| 345 | 2308.04836 | thaihungle/SM (b46d376) | rejected: `requires_gpu` (b) | "On our Nvidia A100 GPUs ... 11h 38m and 12h 10m"; no CPU figure |
| 358 | 2407.19421 | PanChengN/I-PINN | rejected: `no_license` | as 317 |
| 372 | 2412.08310 | MatthiasKohn/ES-MLP | rejected: `no_license` | as 317 |
| 373 | 2402.04898 | Sentient-Sports/Strain-of-Success | rejected: `no_license` | as 317 |
| 374 | 2305.18246 | hmishfaq/LMC-LSVI (b987709) | rejected: `outside_v03_experimental_scope` | the Atari results are in figures only; Table 1 holds theoretical bounds |

The other candidates of batches 13 to 15 were rejected mechanically (their batch files).

**Sample (decided 2026-10-18):** main sample 2305.19518 (1), 2502.16782 (112),
2407.11735 (230), 2309.15704 (309), 2302.12465 (325); development papers 2304.14390 (335)
and 2407.20299 (338). If C5 or C7 leaves a main paper with no valid cell, amendment 1
applies: the 6th accepted moves up and the walk goes on.

**C5 applied.** CIFAR-10/100 (www.cs.toronto.edu/~kriz/cifar.html: "If you're going to use
this dataset, please cite the tech report"): accepted for 2305.19518 and 2407.11735.
kin8nm (original source DELVE, whose copyright notice grants use "for non-commercial
purposes only"): accepted for 2309.15704. Tiny ImageNet (cs231n.stanford.edu download, no
terms found at the source): its cells of 2407.11735 are `data_license_incompatible`.
Refute does not redistribute data: the run fetches each dataset into a cache on the VM and
mounts it read only; the dossier holds the claim file, the canonical record with the
hashes, the logs and the requirements lock (`src/refute/packs/ml/production.py`,
`write_dossier`), never a dataset. The logs are copied whole, so output that a repository
prints itself would be in them.

**C7 measured.** The BOLT weights bundles (Google Drive folder linked from
cmu-cryptosystems/BOLT, read 2026-10-18): `bolt_word_elimination.zip` 779.8 MB, `bolt.zip`
779.8 MB, `iron.zip` 1.07 GB; each communication cell needs one bundle, under 2 GB.

## Versions of PROTOCOL-clarifications.md

SHA-256 of the file's bytes as committed. Any later version is added here in the commit
that changes the file.

| Version | Commit | Content | SHA-256 |
|---|---|---|---|
| 1 | 0b1e63f | C1, C2 | `8c08ac5b4407dd76d2b3ede276fdf20374efd610d252e572002e2e1c610a1958` |
| 2 | 9ec21de | C1, C2 (Codex review) | `0d8ca4a89e1fcc3507d2c943e20ae04f94b2178ec4dd16321fc182de4bbb0f02` |
| 3 | acb5ec3 | C1, C2, C3 | `df5efa365eca21a9dc197b4f49b58363137965366e51f1ff949e9fedb101c025` |
| 4 | the commit that adds this row | C1 to C9 | `62f17c049bf64615222bb38deb7eb1106641b4f9c1c02b24c0311000b0bfa96e` |
