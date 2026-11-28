# Codex check, one round: the corrected X2 texts against the maintainer's condition (block Y, item Y2)

You are a read-only reviewer. You must not edit any file and must not run anything that writes. A
read-only `git diff --no-index` is allowed. Do not open `K:\Meu Drive\Pessoal\Segurança`.

**The maintainer's condition (Y2), translated:** the diff between the current draft and the
corrected one contains only:
- (i) the change of the count and of the sentences named in Y1;
- (ii) the 4 new rows of the table;
- (iii) the removal of the "DRAFT" header.

**What Y1 named:**
- **(a) The correction file:**
  - it says "34 files whose paths name the paper: 30 under claims/ and dossiers/, and 4 under
    inventories/, lock-verification/ and sources/";
  - it puts the 34 in the table;
  - it adds "#207 reported 30 files; that count covered claims/ and dossiers/ only. Other files of
    the archive mention the paper in their text; they are not listed here."
- **(b) The Zenodo note:** "includes 30 files about arXiv:2309.15704, under
  `calibration/v0.3/main/claims/2309.15704/` and `calibration/v0.3/main/dossiers/2309.15704/`"
  becomes "includes 34 files whose paths name arXiv:2309.15704 (30 under calibration/v0.3/main/claims/
  and dossiers/, and 4 under inventories/, lock-verification/ and sources/); other files mention it
  in their text". The rest of the note stays as it is.

**The files:**
- **The correction file:**
  - current: `C:\Projetos\refute\.cache\v0513\x2\v0.4.0-release-archive-correction-2026-11-27.md`;
  - corrected: `C:\Projetos\refute\.cache\v0513\x2\corrected-correction.md`.
- **The Zenodo note:**
  - current: `C:\Projetos\refute\.cache\v0513\x2\zenodo-v0.4.0-description-note.md`;
  - corrected: `C:\Projetos\refute\.cache\v0513\x2\corrected-zenodo-note.md`.
- **The 4 new rows** must match the v0.4.0 tree as listed through the meter:
  `C:\Projetos\refute\.cache\v0513\runs\git-read__ecbfe8adadfa\stdout.txt` (the output of
  `git ls-tree -r -l --full-tree v0.4.0`). For each new row, check its path, size and blob there.
  Also check that exactly 34 listed paths contain "2309.15704".

**Your only task:** say whether each diff contains only (i), (ii) and (iii). Do not review anything
else.

**Answer:** `SURVIVED` if the condition holds for both files, otherwise `REFUTED`, with each line of
the diff that falls outside it. Short.
