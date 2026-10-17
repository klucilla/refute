# Pilot triage, round 6561446

Under `calibration/v0.3/pilot/PROTOCOL.md` (commit `d7dfc40`), on the draw of
`pilot_draw.json` (commit `88d811c`). Metadata and README only for the pilot triage; the
full triage of a provisional acceptance reads the repository's files at the recorded
commit. **No code was run.** The agent proposed each decision with its evidence on
2026-10-17; the maintainer approved each one on 2026-10-17 (about 22:15 and 22:35 UTC, in
the working conversation), and decided the full triage of paper 17 as recorded below.

Evidence: the README at the recorded commit (cached locally, SHA-256 in
`pilot_draw.json`), cited as `README:<line>`; repository files as `<path>:<line>` at the
recorded commit; GitHub's license field as `license_spdx` in `pilot_draw.json`.

## Mechanical rejections (the script; approved as a group)

15 papers: `category_outside_list` (arXiv primary category not `cs.LG` or `stat.ML`):
#1 2312.01872 cs.CR; #3 2305.04397 cs.MA; #4 2310.04225 math.ST; #5 2310.05701 cs.DC;
#6 2303.13675 cs.CL; #7 2310.08130 cs.CL; #9 2411.07705 cs.CY; #10 2402.02430 cs.CV;
#11 2412.02323 cs.CL; #12 2501.14486 cs.RO; #13 2504.11478 cs.CV; #15 2407.11381 cs.CV;
#18 2406.19434 cs.GR; #19 2306.15460 hep-ph; #20 2406.04984 cs.CL.

## Pilot triage of the other 5 (metadata and README)

| # | arXiv | Decision | Reason | Evidence |
|---|---|---|---|---|
| 2 | 2402.13285 (stat.ML) | rejected | `no_license` | `license_spdx` null; the README (32 lines) states no license or authorization |
| 8 | 2505.18568 (cs.LG) | rejected | `no_license` | `license_spdx` null; the README (23 lines) states no license; it names two code bases it builds on (README:22), not a license |
| 14 | 2407.03261 (cs.LG) | rejected | `no_license` | `license_spdx` null; the README (83 lines) states no license. (Also: the raw dataset is to be provided by "the downstream user", README:34-41, not checked further) |
| 16 | 2505.15008 (cs.LG) | rejected | `data_requires_registration_or_terms` | the evaluated data include ImageNet-1K, obtained through ImageNet's own download (README:70-78: "Refer to ... on how to obtain ImageNet1K"), which requires an account and acceptance of terms. (Also applicable, not used: the ImageNet folders are far above 5 GB, `dataset_over_budget`; the commands pass `--gpu 0`, README:34-48.) An operational exclusion, never a scientific failure of the paper |
| 17 | 2401.08819 (cs.LG) | **accepted provisionally** | none at the README level | MIT (`license_spdx`); instructions to install and run (README:5-40); CPU is the default (`--cudaid` default -1, README:38) |

**Provisional acceptances of the first round: 1 of 20.**

## Full triage of the provisional acceptance (development papers, D-3)

Paper 17, 2401.08819, repository `czp16/cde-offline-rl` at
`2e0def649c17f74a87a5d75a89f0a92b03e8390f`. **Decision of the maintainer (2026-10-17):
rejected, `requires_gpu`**, by the literal reading of the pilot protocol ("compute stated
only in GPU time is `requires_gpu`", section "Pilot triage"; plan 4.4: "compute stated
only in GPU time leads to `requires_gpu`"). The paper's only statement of cost is its
computation time comparison: "We use the server with AMD EPYC 7542 32-Core CPU and A5000
GPU. To compare different methods fairly, we report the time of 200,000 steps with batch
size = 512 and defaulted hyper-parameters for baselines." (https://arxiv.org/html/2401.08819v2,
read 2026-10-17; the two sentences checked verbatim; the results are its Table 10, in the
appendix; the section number given by the maintainer, 4.3, was not confirmed by the
agent's reading of the HTML). The maintainer's reason for the literal reading: the same
rule triages the main sample, and no exception for convenience enters the record. The
agent had proposed acceptance, reading that statement as a comparison of methods rather
than the compute of the claims; that reading is not the one recorded.

`needs_paid_api_or_credentials` does **not** apply: a first proposal of it (from
`wandb.init` in `run_cde.py:85-96`) was not approved; W&B turns off completely with the
environment variable `WANDB_MODE=disabled` ("If you set this to disabled wandb will turn
off completely", https://docs.wandb.ai/guides/track/environment-variables/, which now
serves https://docs.coreweave.com/products/wandb/track/environment-variables, read
2026-10-17), and Refute's engine sets it in every run of every paper as part of its fixed
base environment (code covered by the code hash, recorded in each dossier; not a claim
field), so `wandb.init` makes no connection and needs no account.

| Reason (closed list, plan 4.4) | Applies? | Evidence |
|---|---|---|
| `out_of_scope` | no | offline reinforcement learning on D4RL control tasks; no keyword of the list in title or abstract |
| `no_license` | no | `LICENSE`: MIT License, "Copyright (c) 2023 Anonymous authors" |
| `data_requires_registration_or_terms` | no | the D4RL datasets are read by `env.get_dataset()` (`utils/utils.py:8-9`) from D4RL's public server, no account |
| `data_license_incompatible` | no | "all datasets are licensed under the Creative Commons Attribution 4.0 License (CC BY)" (https://github.com/Farama-Foundation/D4RL, read 2026-10-17) |
| `weights_license_incompatible` | no | no pretrained weights; every network is trained from scratch (`run_cde.py:61-83`) |
| `outside_v03_experimental_scope` | no | the paper reports normalized D4RL scores in tables, "the average of last 5 evaluation values with 5 seeds" (arXiv HTML, read 2026-10-17) |
| `data_not_public` | no | public server; sizes by HTTP HEAD on 2026-10-17 |
| `needs_paid_api_or_credentials` | no | W&B off by `WANDB_MODE=disabled` (above); MuJoCo 2.1.0 has no license key ("Removed the entire license manager", https://github.com/google-deepmind/mujoco/releases/tag/2.1.0, read 2026-10-17) |
| `stated_compute_over_budget` | not used | the only statement of cost is in GPU time (next row), which the protocol sends to `requires_gpu` |
| `requires_gpu` | **yes (the decision)** | compute stated only in GPU time: "We use the server with AMD EPYC 7542 32-Core CPU and A5000 GPU. To compare different methods fairly, we report the time of 200,000 steps ..." (arXiv v2). Recorded too: the code has a CPU path (`--cudaid` default -1, `run_cde.py:21`; `cudaid: -1`, `hyper_params/cde/maze2d.yaml:56`), while the README's commands pass `--cudaid 0` (README:36, `run_exp.sh`) |
| `dataset_over_budget` | no | the 9 datasets of `run_exp.sh` total 2.11 GB (largest 0.47 GB, `halfcheetah_medium_expert-v2.hdf5`), below 5 GB |
| `pretrained_download_over_budget` | no | none |
| `ambiguous_repository` | no | one official repository |
| `repository_unavailable` | no | exists, not archived |
| `no_reproduction_instructions` | no | installation (README:5-31) and commands (README:33-40, `run_exp.sh`) |
| `category_outside_list` | no | cs.LG |

Every other reason of the list was checked and does not apply (rows above).

**Also seen, not reasons** ("looks hard" is not a reason): the environment file (`environment.yaml`, Python 3.8, no
channel named) does not list `torch`, `wandb` or `d4rl`, and the MuJoCo 2.1.0 binaries and
the system libraries of `mujoco-py` (README steps 2 to 5) are installed by hand; the
README's `requirements.txt` does not exist at the commit, so only the first rung of the
build ladder applies (`environment.yaml`, version 1 of the docker backend builds it); the
datasets are fetched by Refute's fetcher before any run (the runs have no network) and
given to D4RL through its dataset folder; D4RL's server and the conda channels need
entries in the proxy's allowlist, each with its official source.

**Development papers from the first round: 0.** The 20 papers do not give 2 development
papers, so the additional pilot round of the protocol is drawn (at most one).

Additional pilot round: needed

## Adjustment of the frame (W5.5)

From `refute.selection.filters.adjustment_record` with the ordered list of the protocol
and 1 provisional acceptance:

```json
{
  "pilot_accepted": 1,
  "adjustments_made_before": 0,
  "alternatives": ["wider-window", "add-cs-ai"],
  "applied": "add-cs-ai",
  "reason": "1 pilot papers accepted, fewer than 3: the first alternative whose trigger fires",
  "window": {"first": "2023-01", "last": "2025-06"},
  "categories": ["cs.LG", "stat.ML", "cs.AI"]
}
```

It changes the main protocol only, which is written after this record. The additional
pilot round keeps the pilot's own rules (`cs.LG`, `stat.ML`).

## Rejection profile of the first round

`category_outside_list` 15; `no_license` 3; `data_requires_registration_or_terms` 1;
provisional acceptance 1, rejected at the full triage (`requires_gpu`, the maintainer's
decision by the literal reading of the protocol).
