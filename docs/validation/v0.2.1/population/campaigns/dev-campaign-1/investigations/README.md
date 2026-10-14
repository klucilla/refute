# Read-only scripts behind the campaign 1 diagnosis and investigations

Added at the closure of the population study (2026-10-14; see
`../../../closure-record.md`). The scripts read the frozen manifest (`../../../manifest-dev.json`)
and the result records of campaign 1, which are kept out of git and listed with their SHA-256 in
`../asset-SHA256SUMS` (default location: `.cache/population/campaign-dev-1/runs`). They change
nothing and never replace a file; each takes its output location as an argument.

| Script | Writes | Reads |
|---|---|---|
| `diagnose.py` | `../diagnosis.md`, and `extract-M0.json` and `extract-M3.json` in its work folder (about 22 MB each, not committed) | M0 and M3, slot 1 |
| `holdout_investigation.py` | `../holdout-investigation.md`, `holdout-rounds.json` | M3, slot 1 |
| `c3_inconclusive.py` | `../c3-inconclusive-investigation.md`, `c3-rounds.json` | M3, slot 1 |
| `check_numbers.py` | nothing (prints the comparison) | a Portuguese record and its English translation |

Run them with the project's Python (`.venv/Scripts/python.exe` on Windows, `.venv/bin/python`
elsewhere); `c3_inconclusive.py` uses `scipy`, a project dependency. Options:
`diagnose.py [--records DIR] [--work DIR] [--out FILE]`,
`holdout_investigation.py [--records DIR] [--out-dir DIR]`,
`c3_inconclusive.py [--records DIR] [--out-dir DIR]`.

## Reproduction (2026-10-14)

The three scripts were run again into a new folder, on the records listed in
`../asset-SHA256SUMS`, and every output is byte-identical to the file here:

| File | SHA-256 | Bytes |
|---|---|---|
| `../diagnosis.md` | `19f2cbf0f043aa898dc2f65c0ed26ee14a6c4b2269ab613d002d3a9273687170` | 50968 |
| `../holdout-investigation.md` | `26df9a948a58583c1eb49ad29572b2b973b24dcd110a6a0406e450a3609817ef` | 10163 |
| `../c3-inconclusive-investigation.md` | `9d25811486550c0bce21c147f035a9e2e49b65126d813075b189f1df23af83c2` | 14200 |
| `holdout-rounds.json` | `3faf0c41d053b98f2354f9d97e0f1eb97de233bc701752832ada6d89b0dce9ac` | 302778 |
| `c3-rounds.json` | `08ea3ad9be6eb84655c46d9834167e1dad2cf2a8bde3c8f46ffd31b83e15566d` | 123372 |
| `extract-M0.json` (not committed) | `6aaa4e99ed8bdafcde7169fb95954be823d3d3bfa0c5b6ee6ce754109bc8ca6a` | 22481494 |
| `extract-M3.json` (not committed) | `f33a4b2d2cf820d0905546ef91436cead4950f66e419fd39b84b336dbd44a3c7` | 22713917 |

`diagnosis.md` was written before this folder existed, by the working copy of the script, and
says that its script "was not published". `diagnose.py` here is that script with the analysis and
every output string unchanged; only the plumbing changed (the repository root is found by walking
up, the paths are arguments, the observations text is embedded). Its rerun reproduces
`diagnosis.md` and both extracts byte for byte.

## Translation of the two investigations

The investigations were first written in Portuguese for the maintainer. Those records are not
committed; they are kept in the archive of the study (`../../../closure/archive-summary.md`).
The English scripts here repeat the selection, the calculation and the number formatting of the
Portuguese scripts and translate the text.

| English | Portuguese record (SHA-256) | Numeric tokens |
|---|---|---|
| `../holdout-investigation.md` | `dev1-holdout.md` (`feeb5313361d64258c09245e3035fcc57481c7cbe68f1acc6a669a4a5fd37dfe`) | 251 and 251, identical |
| `../c3-inconclusive-investigation.md` | `dev1-c3-inconclusive.md`, version 2 (`3c1b2732775cdbe0b7c655af6f55521fa75362a00dbaa15f734ab77bf00dda5b`) | 203 and 203, identical |

- `check_numbers.py` compares the numbers of the two versions after the normalizations stated in
  its docstring. Text added in translation (translation notes, the errata, pointers) is between
  `<!-- translation-note -->` markers, which do not render, and is left out of the comparison.
- The JSON outputs equal those of the Portuguese runs: `holdout-rounds.json` equals
  `dev1/holdout-rounds.json` (`93d3fae964a2b398ae2dfc16b2bbda6f2b17776e27c1828946e7d43baaf6b5a1`)
  as parsed JSON; `c3-rounds.json` equals `dev1/c3-rounds.json`
  (`223faec575ef8ede0b87c9eb5363d81706073c16d847254a385b88a14b18d1a5`) once its two old
  Portuguese class names are mapped to the English class names of version 2. The bytes differ
  (line endings, and the class names).
- The Portuguese scripts: `holdout_investigation.py`
  (`5e9ea5f3276477044a05b64afe277722adbf831025bb50a67ae5617e220e9a84`), `c3_inconclusive.py`
  (`f83e81f1b6a3e991b54e89235887645cba68595fb1458dc5e0b4722dd03aec81`), and for the diagnosis
  `diagnose_en.py` (`42406d8c4408ea1c2a12de0845ab803864485b8fe595210b81b7164ae5a51f2c`) with
  `observations_en.md` (`53eaacc876d927875b07a32fea5f776fbd04843a709814835079b51d6fec62e6`).

## Errata of the C3 investigation (2026-10-14)

`../c3-inconclusive-investigation.md` carries a dated errata at its top, in four separate items,
each with its source (Codex review 3, section 5, and section 4 of Claude's critique); version 2
is translated without changes below it. The first item: the omission of the cross term C01
affects the reported lever arm, not directly the counts 21 and 38. The Portuguese version 2 stays
unchanged; its errata is a separate Portuguese file with the same items,
`dev1-c3-inconclusive-errata-v2.md`
(`b2d3fbca41d13e1e06408e6e5a46b23ad3978beeeeee192a631cd731ff3b57d8`), which supersedes a first
version without a source per item, `dev1-c3-inconclusive-errata.md`
(`9d12d4e1259b7922fc2e06c8c6e22bb6911e5a093d749874b24c9b704d84e4cf`), kept. The parity of the
two errata was checked item by item (numeric tokens identical in each of the four items).
