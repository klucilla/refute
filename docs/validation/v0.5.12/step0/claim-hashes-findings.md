# v0.5.12: the "before" claim hashes ran blind in the container (2026-11-26)

The maintainer's decision of #218 comment 7191720023, item 1: in the container and in order, the
one repetition of the "before" golden, the "before" claim hashes, M1's input identity, and M1. "If
any one fails: STOP." The claim hashes ran, but every claim failed to load, so the work stopped
before M1.

## What ran (journal `log.jsonl`)

| Unit | Status | Result |
|---|---|---|
| `golden-local before` (the approved repetition) | ok | 20 outputs, no error output; record `step0/golden-before.json`. Its `verdict-v1` to `verdict-v4` hashes equal those of v0.5.11's `step1/golden-after-fix.json`, made outside the container. |
| `claim-hashes before` | ok (exit 0), **but blind** | **0 of 11 claims loaded.** Each gives `ClaimError: unknown domain pack 'tess'` (or `'ml'`) `(installed packs: none)`. Record `step0/claim-hashes-before.json`. Outside the container, v0.5.11 loaded 10 of them. |
| `m1-inputs` | ok | 21,000 cases' input hashes frozen. No clash with v0.5.11's 400 recorded calibration inputs, and no duplicate. Record `step1/m1-inputs.json`. No F1 call. |
| `inspect` packs-diag | ok | Diagnostic, exploratory and post hoc. |
| `inspect` venv-unreadable | ok | Diagnostic, exploratory and post hoc. |

**A slip of order.** `m1-inputs` was launched right after `claim-hashes before` returned exit 0,
before its record was read. It is the next approved unit and calls no F1, so nothing was measured.
Still, the stop rule called for reading each result before going on.

## The cause

- `refute`'s domain packs are found through the entry points of
  `.venv/Lib/site-packages/refute-0.5.0.dist-info/entry_points.txt`
  (`refute.core.pack.available_packs`).
- In the container, that file and `METADATA` raise `PermissionError`, so `entry_points` returns
  nothing. `RECORD` and `direct_url.json` in the same folder open.
- Opening the first byte of every file under `.venv` from the container shows that **1,249 of
  18,376 files are unreadable** there. Among them:
  - the editable `.pth`, which was already met;
  - `refute`'s entry points and metadata;
  - the whole of Pillow, which matplotlib uses;
  - `certifi`, `filelock` and `aiohttp`;
  - `dateutil`'s zone data;
  - many packages' metadata.

  These files evidently do not carry the inherited read grant of the project folder.
- So the container's environment is incomplete in a way the meter's demonstration did not reveal.
  - The golden happens not to touch those files.
  - The claim hashes do touch them.
  - M1 might not touch them, but nothing shows it, and a hidden import of an unreadable module
    would fail it.

## What a fix needs (not done; the maintainer's decision)

- **(e) Make the cvenv self-contained, from local copies.** Copy `.venv/Lib/site-packages`
  (about 565 MB) into `.cache/v0512/cvenv/Lib/site-packages`, from outside the container.
  - Each file's SHA-256 is checked, and the copies inherit the cvenv's grant.
  - The line that adds `.venv`'s site-packages is dropped, and the editable `.pth` (naming `src`)
    is kept.
  - The phase-wide disk bound would carry about 0.85 GB (2 GB ceiling).
  - Then `cvenv-check`, a fixture that imports every top-level package and reads every
    `entry_points.txt` in the container, and the claim hashes "before" again.
- **(b) Run outside the AppContainer,** under a dated charter amendment, every unit that needs the
  full environment: the claim hashes, the pytest units, and perhaps M1.

The prepared but not yet run files of option (d) (`tools/subst_map.py`, `step0/tmpdir_pytest_d.py`
and their unit) are committed with this record. Option (d) was to come after M1, which has not
run.
