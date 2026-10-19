# Publication review of the dossier of 2309.15704

The review that the publication rule of the logs requires before the publication of a dossier
(docs/validation/v0.3/wp3-dossier-provenance-acceptance.md, section 2). The sealed record is
`dossier/`, as the engine wrote it on the VM on 2026-10-19 (run `refute-p230915704.service`,
execution id `0568909021a9bc97d763e4b5b1903010`, Refute `04054f2`); its `MANIFEST.sha256`
has SHA-256 `3215fb9316d211717e672c731bfe3a655c9f3f7c719a43d831df8ada2e30fb4e` and its 15
entries were checked on the host (`refute check-dossier`: OK).

**Verdicts (the engine's).** C1, C2 and C3 INCONCLUSIVE, cause `undetermined`: the environment
was built (rung `requirements_compiled`), every dataset was present at its size, and each
claim's base run (`python run.py --config configs/uci_all.yml`) exited with code 1 at once,
with `TypeError: unsupported operand type(s) for +: 'NoneType' and 'str'` at `run.py` line 152
(the logs below). 0.019 CPU-hours in all.

**The analysis of the cause** is under the right of reply of the protocol
(docs/plans/v0.3-plan.md, section 9): the authors are notified first, and the analysis is
recorded afterwards as a new record, with their reply if they give one. This review records
the engine's verdict and the logs only.

**Datasets.** The eight files (UCI and OpenML;
[sources/2309.15704-data-sources.md](../../sources/2309.15704-data-sources.md)) were fetched and
counted in the VM's cache; their bytes are not in the dossier.

| File | Bytes | Holds data of a dataset? | Content |
|---|---|---|---|
| `MANIFEST.sha256` | 1,519 | no | SHA-256 of the other files |
| `claim_file.json`, `claim_input.json` | 22,876 each | no | the locked claim, resolved |
| `dossier.json` | 32,081 | no; derived counts only | verdicts, gates, split sizes, provenance, accounting |
| `logs/arXiv-2309.15704v2-C1_base_method_s-.log` (and C2, C3) | 956 each | no | TensorFlow's start-up lines, the parsed arguments and the traceback above |
| `logs/setup_build_requirements_compiled.log` | 7,816 | no | the build's resolution and installation |
| `logs/setup_data_*.log` (3) | 0 each | no | empty |
| `profiles/build.json`, `profiles/run.json` | 414, 411 | no | the host's records of the VM's network profile |
| `pyvenv.cfg`, `requirements.lock` | 151, 3,791 | no | the environment's interpreter and resolved lock |
| `sources/3332505b…` | 13 | no; a derived count | `{"rows": 768}` |

**Names, paths and secrets** (a scan of every file, 2026-10-19): none, besides the
repository's public URL in the claim's definitions and the VM's path under `/home/refute`
(the service account, already public).

**Licences.** No dataset bytes are published; the dossier holds Refute's records and the
logs of the run.

**Outcome:** (A) full publication, the maintainer's decision of 2026-10-19 (the cause not
attributed here; see above).
