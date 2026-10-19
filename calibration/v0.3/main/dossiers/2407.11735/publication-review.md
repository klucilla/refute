# Publication review of the dossier of 2407.11735

The review that the publication rule of the logs requires before the publication of a dossier
(docs/validation/v0.3/wp3-dossier-provenance-acceptance.md, section 2). The sealed record is
`dossier/`, as the engine wrote it on the VM on 2026-10-19 (run `refute-p240711735.service`,
execution id `e9ec2b31a8703c13b2ca18e3916ea047`, Refute `04054f2`); its `MANIFEST.sha256`
has SHA-256 `d1d8243102d7bb1fdc049a6d8e438a3e532125f49e61a6613114551f50f59d0b` and its 5
entries were checked on the host (`refute check-dossier`: OK).

**Datasets.** The run fetched the two CIFAR archives the claim declares (MATLAB versions, from
the CIFAR page; [sources/2407.11735-data-sources.md](../../sources/2407.11735-data-sources.md))
into the VM's cache; their bytes are not in the dossier, and no split was read (the ladder
stopped before the image the readers need).

| File | Bytes | Holds data of a dataset? | Content |
|---|---|---|---|
| `MANIFEST.sha256` | 433 | no | SHA-256 of the other files |
| `claim_file.json`, `claim_input.json` | 25,401 each | no | the locked claim, resolved |
| `dossier.json` | 24,775 | no | the verdicts and gates, the ladder's stop, the datasets' SHA-256 and sizes, the manifests of the clone and of the patched tree (file names and hashes of the repository), provenance, accounting |
| `logs/setup_build_own_environment.log` | 46 | no | one line: `refute: version 1 does not build a Dockerfile` |
| `profiles/build.json` | 414 | no | the host's record of the VM's network profile (no host value) |

**Names, paths and secrets** (a scan of every file on the host, 2026-10-19): no Windows path,
host address or token-like string. The matches are the repository's public URL in the claim's
definitions (`https://github.com/klucilla/refute/issues/158…`, the approval records already
published), file names of the paper's repository that contain `@` in `dossier.json`
(`imagenet100-id.0@5000-label.txt`, `imagenet30-id.0@2600-label.txt`; not addresses) and the
VM's path under `/home/refute` (the service account, already public).

**Size:** every file is far below 50,000,000 bytes and 100 MiB.

**Outcome:** (A) full publication, by the maintainer's standing decision of 2026-10-19 for a
clean review (no data of a dataset, no personal data, no host path or secret, licences that
allow it): the public dossier is the sealed record, byte for byte, at `dossier/`.
