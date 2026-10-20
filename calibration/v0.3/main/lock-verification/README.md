# Verification of the five v0.3 locks after the v0.2.1 integration

A new record of 2026-10-20, by the maintainer's decision of that day. No published dossier,
claim, lock or record of v0.3 is changed by it.

## What changed

On 2026-10-20 `main` was fast-forwarded from `b6f5346cbf2d6c5398b3da2ec37d91a6ae1c87bc` to
`5b86736714a1da16ae08c8fc4a7483712a459be2`, the integration of the v0.2.1 reopening
(`claude/v0-2-1-reopen`, `2e4ff99`) with the sealed v0.3. It changes 12 code files (11 under
`src/refute/packs/tess/` and `src/refute/core/lock_compat.py`) and nothing under
`calibration/`.

## What it means for the v0.3 locks

**From commit `5b86736` on, `refute verify` on `main` returns `TAMPERED` for the five v0.3
main-sample locks, by design.** `refute verify` hashes the code of the tree it runs in
(`src/`, `pyproject.toml`, `uv.lock`), and that code is no longer the code the locks froze
(code hash `3165e1417ebe1f9474145076000f14f3b561b2cdd55f8c2b6b36ffde26e17322`, commit
`b6f5346`). The code is the only component that differs: the claims, every attachment and the
`LOCK_HISTORY.md` entries match their locks, and the files named as changed are exactly the 12
code files of the integration ([on-main-5b86736/](on-main-5b86736/)). `TAMPERED` keeps its
meaning, "different code"; it is not changed or projected for these locks
([docs/lock-format.md](../../../../docs/lock-format.md), "The v0.3 locks").

**Their verification is `scripts/verify_locked_tags.py` at the tag `v0.3.0-main-lock`**
(annotated; tag object `3e5b96c975d2175e9f4356ce8269948d5fb935f4`, commit `b6f5346`; issue
#164). From `5b86736` or later, from the project root:

    .venv/Scripts/python.exe scripts/verify_locked_tags.py

It checks out each tag in a clean worktree under `.cache/lock-compat/`, runs `uv sync --frozen`
there and `refute verify` on each claim. For the five v0.3 locks (list `DIRECT_LOCKS`) it
requires the tag to point to `b6f5346`, a clean checkout, the exact identity of each lock and a
direct `PASS` with no projection; the joint result needs all seven claims (v0.1, v0.2 and the
five of v0.3). The integrity of a dossier (`refute check-dossier`,
`calibration/v0.3/verify_dossiers.py`) is a different check and does not replace it.

## The run recorded here

On 2026-10-20 (`verified_at_utc` in each output), from `5b86736`, after the tag was published:
joint `PASS`, 7 of 7 ([at-tag/summary.json](at-tag/summary.json)). On the same commit:
`verify_dossiers.py` `VERIFIED` and `refute check-dossier` "core: intact against its seal" for
the five dossiers. Before the promotion, the full suite on `5b86736` (3480 tests, 0 failures,
0 errors, 70 skipped, from the JUnit XML) and CI run 39369145960 (16 of 16 jobs; it tested the
pull-request merge commit `9c8c67c`, whose tree `40f4ddb8f651e6f6d503540877d0fc8ecaa98ef4` is the
tree of `5b86736`, with `main` at `b6f5346`; draft PR #163, never merged through the pull
request: GitHub marked it, and the draft PR #157 of `claude/v0-2-1-reopen`, as merged by itself
when their head commits reached `main` by the fast-forward, and deleted both head branches
(the repository deletes head branches on merge); both branches were pushed back at the same
commits, `5b86736` and `2e4ff99`, the same day).

The v0.2.1 work in progress (the `R_min` study and its reserve) runs on the code of branch
`claude/v0-2-1-reopen` at `2e4ff99`, and its records cite that commit, not `main`.

## Files

| File | SHA-256 |
|---|---|
| `at-tag/summary.json` | `3ce72077db65cd3fdabfba20d58915a625588d98e8922fffd52177fa72fca05e` |
| `at-tag/v0.1.0__calibration__self_claim.yaml.json` | `d7dd98305cbe329dc21bee8bb6bfb1edf5833d85e4975e771a89eb2b7d78ba28` |
| `at-tag/v0.2.0-calibration-lock__calibration__v0.2__self_claim.yaml.json` | `04145dda784ed3087fa877ce9363a1cad319a8b44b6a542337880f8eb76c60c5` |
| `at-tag/v0.3.0-main-lock__calibration__v0.3__main__claims__2302.12465__claim__claim.yaml.json` | `6734ea10ec08536936108c12d1403b274d9b9f96982b8d02fb2b65a6755db5a0` |
| `at-tag/v0.3.0-main-lock__calibration__v0.3__main__claims__2305.19518__claim__claim.yaml.json` | `779fd2bd313edc5a72bfb586a7624b96cd339bc567b5f702080c7764ece4a0c2` |
| `at-tag/v0.3.0-main-lock__calibration__v0.3__main__claims__2309.15704__claim__claim.yaml.json` | `77b15018b96effc45dc1677ff8da361521c6ee48b85bc8b57460a3ca7331b5ea` |
| `at-tag/v0.3.0-main-lock__calibration__v0.3__main__claims__2407.11735__claim__claim.yaml.json` | `e6b5dd7f763e99ce962fc80fb3af9b5a4ed20ea2306ed363459348eca541c9bc` |
| `at-tag/v0.3.0-main-lock__calibration__v0.3__main__claims__2502.16782__claim__claim.yaml.json` | `ea7a58482feed2323b2d57dabc4287615b5c1aec028e3887c136c819eeb72c14` |
| `on-main-5b86736/2302.12465.json` | `1f990b7abd5655e9182dcf79bd0b835519bab11f8ca585cb773c5a01f6d849b1` |
| `on-main-5b86736/2305.19518.json` | `b28be192bf35f5deda25a7beccd36bdea2692f470744fc116eadf925aeff76b6` |
| `on-main-5b86736/2309.15704.json` | `2407921fe998f8e1ca34878d4085b9b3d77e76eacb9bb8dbb77243eb7b88e615` |
| `on-main-5b86736/2407.11735.json` | `14db63ef969c6d72b1474c32e7c875e24afc2c06aef0b300ffb78b535066a54e` |
| `on-main-5b86736/2502.16782.json` | `51ad93ab89df77afed01e8de512e3fdcf91c9ecc4fa9c755ad6596519e4b9759` |
