Reviewer: claude-opus-5-5 (independent session), dossier 2302.12465

## Summary (two sentences)
The dossier is intact against its seal and manifest. All three drawn claims of arXiv 2302.12465v3, Table 4, UserItemAttr (C1 PaGE-Link 0.954, C2 GNNExp-Link 0.608, C3 PaGE-Link > PGExp-Link) match the paper and the pinned code, and the logged values (0.9625, 0.6053, and d_rep = 0.9625 − 0.5799 = 0.3826) support the computed `REPRODUCED` under the rules of docs/verdicts.md. I found no critical or important problem; the objections below are about disclosure and about how much a "REPRODUCED" with no robustness check can say.

## Objections

| Severity | Evidence | Why it matters |
|---|---|---|
| minor | No attack applies to any claim. Every `targets[*].attacks[*].applies` is `false` in claim_file.json, and `definitions.verdict_paths` says the verdict "rests on its base reproduction alone". Each verdict comes from one deterministic run with the hard-coded `set_seed(0)` (pgexplainer_link.py:97; pagelink.py:91; gnnexplainer_link.py:88 at cdb7160). The profile headline in dossier.json (`outcome.profile.headline`) reads "3 of 3 drawn claims: REPRODUCED" and does not qualify this. | Under rule 6 the verdict is correct. A reader of the headline cannot tell that robustness was never tested (no seed or split variation). The paper reports no seeds or variance (Table 4, arXiv HTML v3), so the variance of the published numbers is unknown. |
| minor | C3's reference run adds `--train_pgexplainer`, which is not in the README's documented baseline command (README at cdb7160: `python baselines/{method}.py --dataset_name=aug_citation`). claim_file.json `definitions.reference_pgexp_link` and the C3 `statement` disclose this as "an explicit correction of the documented procedure". The verdict record has no such note: `outcome.claims[2].notes` is `[]`. | The disclosure lives only in the claim. The engine's record and profile show C3 as a plain `REPRODUCED` on a procedure that is not the documented one. The correction itself looks justified: without the flag the mask generator is never trained (pgexplainer_link.py:55, 117-125), and the paper (sec. 6.2) says the mask predictor was re-implemented with its original objectives. |
| minor | C2 and C3 add `--config_path=baselines/baseline_config.yaml --save_explanation` to the baseline commands (claim_file.json `targets[1].run.argv`, `targets[2].comparison.reference_run.argv`). The README shows neither flag. The justifying attachment `2302.12465-errata-2.json` (sha256 e2d82493…) is cited in `attachments` but is not in the dossier. | Both flags are plausible: eval_explanations.py:122-125 needs the saved masks, and baseline_config.yaml has a `synthetic` section. Still, the transcription choice cannot be checked from the dossier alone. |
| minor | The reason given for `leakage` not applying ("there are no train and test examples of the explainer to compare", claim_file.json `targets[*].attacks[4].reason`) is wrong for C3's reference. PGExp-Link trains its mask generator on `train_pos_g` edges (pgexplainer_link.py:117-119) and explains `test_pos_g` edges (127-143). | The decision may still hold, since the split is by edge id with seed 0. But the stated reason does not describe the code, so the non-applicability is not justified as written. |
| minor | `metric_recompute.applies` is `false` for all three claims, because "the recomputer does not average an AUC per pair". The value comes only from the repository's own `eval_explanations.py` (lines 133-145) through the log regex. | No independent scorer checks the published metric. A defect in the artifact's AUC code (utils.py `eval_edge_mask_auc`) would reproduce rather than be caught. This is a limit on Refute's side and is disclosed. |
| minor | The run-phase profile is named `"profile":"pull"`, and its `read_utc` is 2026-10-19T14:56:08Z (profiles/run.json; dossier.json `provenance.profiles.run.record`). The runs started at 14:53:56Z, and build plus data took about 36 s of elapsed time (`outcome.run.steps`), so the read falls inside the C1 base run. `provenance.profile_limits` itself says a profile "tells the profile when it was read, not that it stayed in force". | The dossier does not show which network or isolation profile was in force during the base runs. The impact is likely small: the data and weights are repository files with verified hashes (`setup.repository_weights.synthetic_model.verified: true`), and `base_env` sets the offline flags. |

## Checks with no objection
- **Integrity.**
  - `refute check-dossier` printed "core: intact against its seal" and "OK: manifest intact" (exit 0).
  - The claim hash cb7720a2… agrees across MANIFEST.sha256 (claim_file.json and claim_input.json), dossier.json `claim_file_sha256` and `provenance.claim_input.sha256`, and both profiles' `claim_sha256`.
  - The log hashes in `provenance.logs` and `logs_read` agree with SEAL.json and MANIFEST.sha256.
  - The dataset sha256 a368d8f6… matches `test_plan.datasets[*].sha256` and the clone manifest's `datasets/synthetic`.
  - The weights sha256 a9446dca… matches `test_plan.weights[0]` and the clone manifest.
- **Patches.** `setup.patches.touched` lists only `eval_explanations.py` (+82 bytes, consistent with one added print line) and `requirements.txt`. The requirements change is +25 bytes, which matches exactly the two lines `torch==1.12.1` and `dgl==0.9.1`, the versions the README declares. The lock (requirements.lock) has torch 1.12.1 and dgl 0.9.1, and every other pin equals requirements.txt at cdb7160. Python is 3.10.22 (pyvenv.cfg); the README tested 3.10.6.
- **Transcription against the paper** (arXiv 2302.12465v3, HTML version, Table 4 "ROC-AUC scores on learned masks", row UserItemAttr): GNNExp-Link 0.608, PGExp-Link 0.578, PaGE-Link 0.954. Section 6.3 contains the quoted sentence "PaGE-Link outperforms both baseline explainers" verbatim. The metric (mask ROC-AUC against ground-truth path edges) and the split (test links, sec. 6.2: train:validation:test = 7:1:2) agree with claim_file.json `metric`, `inventory.transcription` and `source`.
- **Commands.**
  - The C1 and C3 method command is the README's documented synthetic PaGE-Link command plus the documented eval command, verbatim.
  - The logs confirm the configuration took effect: config.yaml gives lr 0.01 and 20 epochs for pagelink; baseline_config.yaml gives lr 0.001 and 100 epochs for gnnexp, and train_pgexplainer True for pgexp; `saved_model_name synthetic_model` in every log.
- **Population and coverage.**
  - The test links are 144 (tqdm 0/144 in the logs; 714 × 0.2 ≈ 143-144).
  - Every run printed `refute-population-size <explainer> 129`, matching `metric.n_examples` 129 and `derived_splits.test_links.expected_examples` 129.
  - The cited code lines (eval_explanations.py 94-109, 133-139, 141-145 at cdb7160) do define the population (pred > 0.5 on the 2-hop subgraph), one AUC per pair, and the mean.
  - `data_present`: likes_edges 714 against 714 expected, with size_tolerance 0 (sources/b8afe213… = `{"likes_edges": 714}`).
- **Each check follows from its input.**
  - C1: |0.9625 − 0.954| = 0.0085 ≤ 0.02 × 0.954 = 0.01908 (log line 870).
  - C2: |0.6053 − 0.608| = 0.0027 ≤ 0.01216 (log line 1615).
  - C3: 0.9625 − 0.5799 = 0.3826 > 0, with `comparison_mode` "direction" (C3 method log line 1265; reference log line 39).
  - The C1 and C3 method runs, in separate containers, gave the identical 0.9625, which is consistent with determinism.
  - Every container exited 0 with `oom_kills` 0, and `saved_explanations` is absent from the clone manifest, so the masks were produced fresh by each run.
- **Verdict rules** (docs/verdicts.md, order 0-6):
  - every gate has status PASS with coverage ≥ the minimum of 1 (`coverage_minimum`);
  - there is no fatal failure;
  - the base reproduction is complete;
  - there are no expected attacks, so rules 4 and 5 cannot apply;
  - rule 6 therefore gives `REPRODUCED` for each claim, which is the result in `outcome.claims[*].verdict.verdict`;
  - `outcome.run.completeness` is "complete" and `accounting_valid` is true.
- **Text.** No statement in claim_file.json or dossier.json is about the authors. The C3 statement discloses its correction, and the claims are worded as values reproduced from the repository's saved link predictor, loaded frozen; nothing is presented as more than that.

## Checks I could not do
- **Claim inventory, draw and triage.** `inventory.json`, `draw.json`, the errata, the selection or triage log, the two patch files and the population-count scripts and records are cited by hash in `attachments` but are not in the dossier. I could not check that the inventory was built by the protocol, that the draw followed its rule, any triage rejection, the literal patch contents, or the count of 129 made before the lock.
- **Lock.** No lock file is in the dossier, so the claim-to-lock hash agreement was not checked beyond what check-dossier verifies against SEAL.json.
- **Paper PDF.** I could not render the PDF (pdftoppm is missing). I read the arXiv HTML rendering of v3 instead.
- **Untrained PGExp-Link run.** I did not run anything, so I cannot say what the documented command without `--train_pgexplainer` would have produced.

## Assessment: OBJECTIONS
All six objections are minor, and none affects the computed verdicts.
