# Publication review of the dossier of 2305.19518

The review that the publication rule of the logs requires before the publication of a dossier
(docs/validation/v0.3/wp3-dossier-provenance-acceptance.md, section 2). The sealed record is
`dossier/`, as the engine wrote it on the VM on 2026-10-19 (run `refute-p230519518.service`,
execution id `0715eb05ba03120236a3bbcac118bb33`, Refute `04054f2`); its `MANIFEST.sha256`
has SHA-256 `006cfc789f1cce6b3a65eb40bde23f07f727768603b475993a2b6146ffd8a0e0` and its 13
entries were checked on the host (`refute check-dossier`: OK).

**Verdicts (the engine's).** C1 and C3 INCONCLUSIVE: they need the CLIP weights declared from
outside the repository, which version 1 does not fetch (not run). C2 INCONCLUSIVE, cause
`undetermined`: its run ended at once with `ModuleNotFoundError: No module named
'pkg_resources'` (`openai-clip`'s `clip/clip.py` line 6, imported by `train_CIFAR.py` line 8
for every encoder).

**Diagnosis (2026-10-19, no new run).** The failure comes from Refute's construction of the
environment, not from a defect of the artifact: the rung builds a `uv` virtual environment,
which does not install `setuptools` (the image's venv: Python 3.9.25, no `setuptools`, no
`pkg_resources`), while the standard venv of Python 3.9 that a reader of the README would
create includes it; the repository's `requirements.txt` does not declare it and the resolved
lock (11 packages) does not hold it. C2 would end INCONCLUSIVE in any case by the measured
limits (memory at 12 GiB and a budget of about 7 CPU-hours per epoch for 200 epochs). Why the
budget measurement of 2026-10-18 passed this import was not determined: it used the same base
image, commit, `exclude_newer`, lock and uv version, and its image was deleted in the disk
cleanup of 2026-10-19. A fix (`setuptools` in the rungs with Python < 3.12) changes the frozen
code and comes after the seal (#59).

**Datasets.** The two CIFAR archives (python versions; [sources/2305.19518-data-sources.md](../../sources/2305.19518-data-sources.md))
were fetched and counted in the VM's cache; their bytes are not in the dossier.

| File | Bytes | Holds data of a dataset? | Content |
|---|---|---|---|
| `MANIFEST.sha256` | 1,384 | no | SHA-256 of the other files |
| `claim_file.json`, `claim_input.json` | 23,081 each | no | the locked claim, resolved |
| `dossier.json` | 41,395 | no; derived counts only | verdicts, gates, split sizes, provenance, accounting |
| `logs/arXiv-2305.19518v2-C2_base_method_s-.log` | 492 | no | the traceback above |
| `logs/setup_build_requirements_compiled.log` | 2,565 | no | the build's resolution and installation |
| `logs/setup_data_*.log` (3) | 0 each | no | empty |
| `profiles/build.json`, `profiles/run.json` | 414, 411 | no | the host's records of the VM's network profile |
| `pyvenv.cfg`, `requirements.lock` | 149, 784 | no | the environment's interpreter and resolved lock |
| `sources/70bffd67…` | 31 | no; a derived count | `{"test": 10000, "train": 50000}` |

**Names, paths and secrets** (a scan of every file, 2026-10-19): none, besides the
repository's public URL in the claim's definitions and the VM's path under `/home/refute`
(the service account, already public).

**Outcome:** (A) full publication, the maintainer's decision of 2026-10-19.
