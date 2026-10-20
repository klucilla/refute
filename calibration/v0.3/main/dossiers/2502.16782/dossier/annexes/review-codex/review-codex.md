Reviewer: codex (second reviewer, another model family), dossier 2502.16782

## Summary (two sentences)

The recorded three `INCONCLUSIVE` outcomes are consistent with the documented Refute limitations, and the three reported communication values match paper version 2. I raise procedural objections because the dossier lacks its declared selection evidence and an independently verifiable preregistration lock, while its execution specifications contain descriptive prose instead of executable commands.

## Objections

| Severity | Evidence | Why it matters |
|---|---|---|
| important | `claim_file.json`, `attachments`, declares `inventory.json` and `draw.json` with hashes, but both files are absent. The dossier contains no selection log or preregistration lock record; `targets[*].approvals` records approval metadata without the underlying records. | The complete inventory, draw order, triage rejections, and locking before execution cannot be independently audited. Matching the included files to their manifest does not establish those procedural properties. |
| important | `claim_file.json`, every `targets[*].run.argv`, contains one prose string beginning `no single command: README 'Reproducing the results'`. The associated transcription describes per-layer server/client tests, summation, and BOLT’s linear contribution without executable steps. | This is not an executable reproduction specification. Even with Dockerfile and external-weight support, the dossier does not specify how to obtain the claimed end-to-end totals. This deficiency does not establish a failure of the paper’s artifact. |

## Checks with no objection

- **Claim values and locations:** C1, C2, and C3 respectively transcribe BERT Medium **6.7 GB**, BERT Large **18.4 GB**, and BERT Base **9.7 GB**. All match the CipherPrune row and communication columns of [paper version 2, page 9, Table 1](https://arxiv.org/pdf/2502.16782v2). These are absolute-value claims, so `type: value` and `comparison: null` are consistent with the selected cells.

- **Included-file integrity:** Independent SHA-256 calculations returned `MANIFEST CHECK True` and `SEAL FILE CHECK True`. All five manifest entries and all six `SEAL.json.files` entries match their recorded hashes. Both claim files hash to `3e59b8353da037e57d03b68817c7b01c947e06ef113555c8b79f4ec842b857ab`, matching `dossier.json.claim_file_sha256` and `profiles/build.json.claim_sha256`.

- **Failure attribution and coverage:** `dossier.json`, `outcome.ladder`, records `refute_error`, zero completed build attempts, and an unsupported Dockerfile build. `logs/setup_build_own_environment.log` explicitly attributes this to Refute version 1. `setup.weights` likewise records unsupported external-weight handling, rather than missing-artifact evidence. The resulting inconclusive gates and zero-coverage base checks follow `docs/verdicts.md`, “Attribution” and “Coverage for paper claims.”

- **Scope and wording:** `dossier.json`, `outcome.profile`, preserves the drawn order, includes all three inconclusive claims in the denominator, reports `has_negative: false`, and uses the headline `3 of 3 drawn claims: INCONCLUSIVE`. `outcome.claims[*].verdict.basic_reproduction_obtained` is false. The inspected engine text makes no positive reproduction claim or judgment about the authors.

- **Recorded patch state:** `dossier.json`, `setup.patches`, contains identical clone and patched manifests, each with 3,434 entries, an empty patch list, and no touched entries. This establishes internal consistency of the recorded manifests, not independent verification of the checkout.

**Checks not completed and why:**

- **Official dossier validation and aggregate seal:** `uv run --frozen --no-sync --offline refute check-dossier …` failed during uv cache initialization, before the checker ran. Direct invocation through the existing virtual environment returned `No module named refute`. No installation was attempted. Consequently, I cannot report a passing `check-dossier` result or independent validation of `SEAL.json.core_sha256`; the file-hash checks above are narrower.
- **Inventory, draw, triage, and lock chronology:** The required records are absent from the permitted inputs. Git history and claim folders were excluded by the review instructions.
- **Pinned repository:** GitHub and raw-content requests for commit `69a0f972cd1b5e26a140a88d3749cb5788fceef8` failed; a direct read-only HTTP request also could not connect. I therefore could not verify the README references, token schedules, documented commands, build dependencies, communication aggregation, or repository bytes against that commit.
- **Execution, data, weights, and robustness:** `outcome.run.steps` records all three base runs as `not_executed`; `setup.weights` records `fetched`, `checked`, and `mounted` as false. There are no measured communication outputs to examine, no actual weight bytes to hash, and no executed attacks or independent metric recomputation to assess.
- **Separate narrative report:** No `report.md` is included. The wording check therefore covers the resolved claim and engine record only.

## Assessment: OBJECTIONS