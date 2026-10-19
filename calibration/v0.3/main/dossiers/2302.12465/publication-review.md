# Publication review of the dossier of 2302.12465

The review that the publication rule of the logs requires before the first publication of a
dossier (docs/validation/v0.3/wp3-dossier-provenance-acceptance.md, section 2). The sealed
record is `dossier/`, as the engine wrote it on the VM on 2026-10-19 (run
`refute-p230212465.service`, execution id `795686368741acd9f6b9cd63dafc08ae`, Refute
`04054f2`); its `MANIFEST.sha256` has SHA-256
`0e177c5dc2e80190b2d51f45081f72970f34444672a9243800aa96039271e700` and its 15 entries were
checked on the host.

**The only dataset** the run reads is `datasets/synthetic`, a file of the repository at
`cdb7160f9a2fd90bded8cefa8f591f9a0e47ee6c`, under the repository's single licence, MIT-0
([sources/2302.12465-data-sources.md](../../sources/2302.12465-data-sources.md); its
redistribution is allowed by that licence). The predictor `saved_models/synthetic_model.pth`
is under the same licence. Neither file's bytes are in the dossier.

| File | Bytes | Holds data of a dataset? | Content |
|---|---|---|---|
| `MANIFEST.sha256` | 1,504 | no | SHA-256 of the other files |
| `claim_file.json`, `claim_input.json` | 25,947 each | no | the locked claim, resolved (the paper's published values, Refute's definitions) |
| `dossier.json` | 27,109 | no; derived statistics only | verdicts, gates, the measured values, the split sizes (714), the population sizes (129), provenance, accounting |
| `logs/arXiv-2302.12465v3-C1_base_method_s-.log` | 61,414 | no; derived statistics only | the script's arguments, progress bars, `Average Mask-AUC: 0.9625`, `refute-population-size pagelink 129` |
| `logs/arXiv-2302.12465v3-C2_base_method_s-.log` | 110,671 | no; derived statistics only | arguments, progress bars, `Average Mask-AUC: 0.6053`, `refute-population-size gnnexp 129` |
| `logs/arXiv-2302.12465v3-C3_base_method_s-.log` | 87,004 | no; derived statistics only | arguments, progress bars, `Average Mask-AUC: 0.9625`, `refute-population-size pagelink 129` |
| `logs/arXiv-2302.12465v3-C3_base_reference_s-.log` | 9,937 | no; derived statistics only | arguments, progress bars, `Average Mask-AUC: 0.5799`, `refute-population-size pgexp 129` |
| `logs/setup_build_requirements_compiled.log` | 3,725 | no | the build's resolution and installation |
| `logs/setup_data_UserItemAttr.log`, `logs/setup_data_UserItemAttr__synthetic__datasets_synthetic_.log` | 265 each | no | DGL's backend notice |
| `profiles/build.json`, `profiles/run.json` | 414, 411 | no | the host's records of the VM's network profile (no host value) |
| `pyvenv.cfg`, `requirements.lock` | 151, 1,432 | no | the environment's interpreter and resolved lock |
| `sources/b8afe213…` | 20 | no; a derived count | `{"likes_edges": 714}`, the container reader's answer |

No file holds an example, a label, a feature or a prediction of the dataset: the logs print
the scripts' arguments, progress bars and aggregate values only (each line kind counted on
the host, 2026-10-19). No credential is in the dossier (the run had none); the VM's account
is the service account `refute`.

**Names, paths and secrets** (a scan of every file on the host, 2026-10-19): no Windows path,
host address, e-mail address or token-like string. The only matches are the repository's
public URL in the claim's definitions (`https://github.com/klucilla/refute/issues/158…`, the
approval records already published in the inventories and erratas) and the VM's paths under
`/home/refute` in `dossier.json` (the service account, already public in
`scripts/vm/launch-paper.sh`).

**Size:** every file is far below 50,000,000 bytes (no log compressed) and below 100 MiB
(all go into the repository).

**Outcome:** (A) full publication, the maintainer's choice of 2026-10-19 on this record: the
public dossier is the sealed record, byte for byte, at `dossier/`.
