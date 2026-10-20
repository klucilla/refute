Reviewer: codex (second reviewer, another model family), dossier 2302.12465

## Summary (two sentences)

The sealed core passes integrity checks, and the logged measurements support the three recorded numerical decisions under the declared rules. Important procedural evidence is absent from the dossier, preventing independent verification of selection, preregistration chronology, and the applied modifications.

## Objections

| Severity | Evidence | Why it matters |
|---|---|---|
| important | `claim_file.json`, `attachments`: `inventory.json`, `draw.json`, and `2302.12465-errata-2.json` are referenced by hash but absent, confirmed by `Test-Path`. No selection log is supplied. | The complete inventory, draw procedure, transcription corrections, and triage rejections cannot be audited as required by the reviewer protocol. The three selected entries alone cannot establish selection compliance. |
| important | `SEAL.json` authenticates the present core; `claim_file.json`, `targets[*].approvals`, records approval times and commit identifiers. No preregistration lock record is included. | Present integrity does not establish that these exact commands, tolerances, exclusions, and populations were locked before execution. Preregistration chronology remains unverified, without implying that it was violated. |
| important | `claim_file.json`, `attachments`, references two patches and four population-count files, all absent. `dossier.json`, `setup.patches`, supplies manifests and before/after hashes, but no patch contents. | Hashes identify unavailable evidence without exposing its behavior. I cannot independently establish that the applied modifications only restore declared dependencies and print coverage, or validate the pre-lock derivation of the 129-pair population. |

## Checks with no objection

- **Core integrity passes.** Running the existing project CLI with bytecode writing disabled and `PYTHONPATH=C:\Projetos\refute\src` returned `core: intact against its seal` and `OK: manifest intact`. Independent PowerShell SHA-256 checks examined all 15 manifest entries and 16 seal entries, with zero mismatches. The sealed core hash is `d18e74776aa886de1ec271c3d31f40dc7f9001452b4aaca41031a674e20366f1`.

- **Claim and log bindings agree.** The hashes of `claim_file.json` and `claim_input.json` match `dossier.json.claim_file_sha256`, `provenance.claim_input.sha256`, and the seal. All four entries in `provenance.logs_read` match their supplied logs in hash and size.

- **Selected numerical transcriptions match the paper.** Version 3, PDF page 7, Table 4 gives UserItemAttr values of 0.954 for PaGE-Link, 0.608 for GNNExp-Link, and 0.578 for PGExp-Link. Section 6.3 describes edge-mask ROC-AUC against ground-truth paths and supports the selected comparison direction. [Paper v3](https://arxiv.org/pdf/2302.12465v3)

- **The recorded arithmetic is consistent.**

  | Claim | Evidence | Check |
  |---|---|---|
  | C1 | `logs/arXiv-2302.12465v3-C1_base_method_s-.log`, `Average Mask-AUC` | `|0.9625 − 0.954| = 0.0085 ≤ 0.01908` |
  | C2 | `logs/arXiv-2302.12465v3-C2_base_method_s-.log`, `Average Mask-AUC` | `|0.6053 − 0.608| = 0.0027 ≤ 0.01216` |
  | C3 | Corresponding C3 method/reference logs | `0.9625 − 0.5799 = 0.3826 > 0`, matching `comparison_mode="direction"` |

- **Coverage is positive and internally consistent.** Every base log prints `refute-population-size … 129`, matching `targets[*].metric.n_examples`. The supplied count source contains `{"likes_edges": 714}`. In `dossier.json.outcome.run.steps`, every recorded container exits zero, with no OOM kill or recorded interruption.

- **Verdict ordering is internally consistent with the declared exclusions.** `outcome.claims[*].base` contains passing gates and base checks. Every attack and metric recomputation is declared inapplicable in the claim, so the recorded aggregation follows `docs/verdicts.md` conditional on those declarations being justified.

- **Scope and text are appropriately bounded.** `definitions.scope` explicitly excludes training the frozen link predictor. `definitions.reference_pgexp_link` discloses the corrected PGExplainer command, and the reference log records `train_pgexplainer True`. `outcome.profile` preserves drawn order, denominator three, and the scoped headline “3 of 3 drawn claims: REPRODUCED.”

**Checks not completed and reasons:**

- The pinned repository commit `cdb7160f9a2fd90bded8cefa8f591f9a0e47ee6c` was unreachable: browser requests returned internal errors, and PowerShell reported inability to connect. Consequently, command fidelity, seed/split restrictions, attack exclusions, model loading, evaluator behavior, and recomputation applicability could not be independently checked against code.
- Inventory construction, draw compliance, triage rejections, lock chronology, errata, patch behavior, and population-count derivation could not be checked because the corresponding evidence is absent.
- Dataset, checkpoint, and ground-truth-label bytes are absent. Their recorded hashes agree where repeated, but I could not independently hash those artifacts, verify pair identities, or recompute mask AUCs.
- Training and robustness reruns were not performed because they would create files, contrary to the read-only restriction.
- PDF screenshot rendering failed with `Cache miss`; paper checks used the extracted versioned PDF text and versioned HTML.

## Assessment: OBJECTIONS