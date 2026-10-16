# Independent review of the population harness (Phase G)

Three rounds of independent review of the harness of the v0.2.1 synthetic population
study (`../population.py`), each by a fresh review session, delivered to the maintainer in
Portuguese on 2026-10-12. Recorded here by population-study.md, Amendment 3.

| Round | Commit reviewed | Report | Delivered file and SHA-256 |
|---|---|---|---|
| 1 | `6e57b35` | `report-round1.md` | `fase-g-report-round1.txt`, `51172b19a202bcff177cea14f9a22181699761faa63776f9a8781b43844adc47` |
| 2 | `a83e09a` | `report-round2.md` | `fase-g-report-round2.txt`, `8c273e81a1b0e7dc3a3debc7e0d6d7c870b8ded444f437a23cd4fd278cbb0031` |
| 3 | `b7c724c` | `report-round3.md` | `fase-g-report-round3.txt`, `448432cdfe3d73ab25a69c142f426b367a154a5476a7e4a9717b97444e29a3fb` |

Each report file is an English header followed by the delivered file, byte for byte
(after the line `<!-- End of header. The delivered file follows, byte for byte. -->`),
including the progress lines of the review session that come before the report itself.
The SHA-256 of each delivered file was checked against the value given by the maintainer
before it was used.

`verifiers/` holds the reviewer's scripts, command files and kept outputs
(`outputs-round2/`, `outputs-round3/`), copied from the reviewer's folder
`.cache/review-g/keep/`; every copy matched that folder's own `SHA256SUMS` (40 of 40),
and `verifiers/SHA256SUMS` is new and lists every file of `verifiers/`.

**User-name check.** Before the commit, every file of this folder was searched for the
Windows user name, in paths (`C:\Users\<name>` with backslashes, forward slashes or
escaped backslashes) and anywhere, by a script written to a file; a positive control
(a file with the three path forms) was found and replaced by the same script. Result:
0 occurrences in 43 files, so nothing was replaced and no file of this folder differs from
what was delivered.

## Note added on 2026-10-16: records not kept

Recorded at the maintainer's request; the facts are as the maintainer reported them.

- On 2026-10-12 the local folder `.cache/review-g` (the reviewer's folder named above)
  was deleted by a cleanup script of the maintainer, whose only condition was that the
  record of commit `68d13fd` had been committed.
- **Preserved:** the 45 files that commit `68d13fd` added to this folder: this README,
  the reports of the three rounds and `verifiers/`.
- **Not archived:** the raw records that existed only in `r2/` of that folder: `neg/`,
  `out/`, `runs/` and `kill-1.err`.
