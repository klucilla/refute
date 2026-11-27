# Correction, 2026-11-27: the abbreviation of the charter's SHA-256

The maintainer's decision G3 (#218, comment 7219180143). Labels: `exploratory`,
`method_status: not_validated`.

## The error

The approved charter of v0.5.13 is `docs/plans/v0.5.13-charter.md` at `04402e7a`. Its SHA-256 is:

**`2832dc4870b0fb094e724a3ff6d6fb6c5710f2da5827791b8fa102c06230c813`**

The maintainer's approval cites it in full (#218, comment 7204660147, item 5). The file at
`04402e7a` hashes to it: the blind-review package's copy `charter.md` was checked against it by
`blind_pack.py` (`26fe01a8`), and its MANIFEST lists it.

Our records abbreviate it as `2832dc48…c230c813`. The correct abbreviation is
`2832dc48…6230c813`, so one character of the abbreviation is wrong (`c` for `6`). The file itself
and its full hash are right. This was an error typing the abbreviation, not a change of any
file.

## Each occurrence

| File | Line | Wrong text | Right text | Introduced by | Handling |
| --- | --- | --- | --- | --- | --- |
| `ROADMAP.md` | 80 | `2832dc48…c230c813` | `2832dc48…6230c813` | `61055e1b` | Working document: **corrected in place**, with an entry in [errata.md](errata.md). |
| `docs/plans/v0.5.13-charter-amendment-1.md` | 13 | `2832dc48…c230c813` | `2832dc48…6230c813` | `69de5f9f` | Approved: **not edited**. This file is its correction. |
| `docs/plans/v0.5.13-charter-amendment-2.md` (revisions 1 and 2) | 8 | `2832dc48…c230c813` | `2832dc48…6230c813` | `89784ceb` | Committed record: **not edited**. |
| `docs/plans/v0.5.13-charter-amendment-2-rev3.md` (revision 3) | 10 | `2832dc48…c230c813` | `2832dc48…6230c813` | `c92ff977` | Committed and hashed (SHA-256 `f5598f00…fffcdc38`): **not edited**. |
| `docs/plans/v0.5.13-amendment-2-blind-review/amendment-1.md` | 13 | `2832dc48…c230c813` | `2832dc48…6230c813` | `d09ab40c` | A byte-for-byte copy in the blind-review package: **not touched** (G5). |
| `docs/plans/v0.5.13-amendment-2-blind-review/amendment-2-revision-3.md` | 10 | `2832dc48…c230c813` | `2832dc48…6230c813` | `d09ab40c` | The same: **not touched** (G5). |

In every row, the full SHA-256 is `2832dc4870b0fb094e724a3ff6d6fb6c5710f2da5827791b8fa102c06230c813`.

**Where the wrong abbreviation is only described, not used as the hash.** These texts quote it
in order to correct it: the message of `26fe01a8` and #218's comments 7219034361 and 7219180143.
`blind_pack.py` first checked the charter against the wrong abbreviation and refused; since
`26fe01a8` it checks the full SHA-256.

## Other abbreviation errors found while checking (not in repository files)

| Where | Wrong text | Right text | Full SHA-256 |
| --- | --- | --- | --- |
| The message of commit `d09ab40c` | `f5598f00...dcc38` | `f5598f00…fffcdc38` | `f5598f0050ada236e3944b623ee42b46888e0f1bc8c9b564ab67b529fffcdc38` (revision 3) |
| #218, comment 7219034361 (the F5 report) | `f5598f00…dcc38` | `f5598f00…fffcdc38` | the same |
| #218, comment 7218201566 (the E6 report) | `257b77c8…a5e1536e` | `257b77c8…ad11536e` | `257b77c87bce99b5527822e09143244410b962ec261f7eccba0665baad11536e` (the deleted `runner.patch`, = `round-1-runner.patch`) |

A commit message and a posted comment are not edited; this table is their correction. From
this correction on, abbreviations are cut from the full hash by the tool that prints it, not
typed.

## Impact

No file, hash, lock, verdict or approval changes.
- Every approval cited the full SHA-256 or the commit, and the files at those commits are
  unchanged.
- The wrong text is an abbreviation that, compared with the full hash, does not match. It cannot
  have selected any other file.
