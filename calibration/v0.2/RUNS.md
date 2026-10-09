# Run log of the v0.2 calibration

Each step of `calibration/v0.2/PROTOCOL.md` is recorded here with its evidence.

## Step 1: protocol committed and pushed

- Protocol commit: `16e880d` (with `989b997`, `46bdb34`, `25b8956`, `eb30567`,
  `27f32d7` and `627e6c2` in the same push).
- Push time, from GitHub's repository activity API
  (`GET /repos/klucilla/refute/activity`): **2026-10-09T02:58:52Z**, push to
  `refs/heads/main` from `78824cf` to `16e880d` by `klucilla`.
- Target-selection drand round 6537566 is published at **2026-10-09T15:00:00Z**:
  the protocol was pushed **12 h 01 min 08 s** before it, more than the 1 hour the
  protocol requires.
- Reviewer-selection drand round: 6542966, published at 2026-10-11T12:00:00Z.
- The latest published round when the rounds were set was 6536118
  (2026-10-09T02:56:00Z).

## Step 2: selection

- Command: `uv run --frozen python calibration/v0.2/select_targets.py`, from commit
  `16e880d` with a clean tree except this file; started 2026-10-09T15:00:45Z, ended
  2026-10-09T15:18:54Z, exit code 0.
- drand round 6537566 retrieved 2026-10-09T15:00:50Z from `api.drand.sh`; signature
  verified (py_ecc 8.0.0, G2Basic). Randomness
  `6203178f500788b092dafc8557309f4225cee9fa7b907eefe819b69525ce325d`. Checked again
  on `drand.cloudflare.com`: same randomness, signature verified,
  same seed.
- Pools after exclusions: 475 planets, 456 false positives. Walk: 13 planet positions
  (11 accepted), 40 false-positive positions (10 accepted). 21 targets written, 5
  eb-catalog rows.
- **Error during the walk.** False-positive position 35, TIC 239638934 (TOI-2571.01),
  was rejected with "MAST query failed: Timeout limit of 600 exceeded." instead of a
  data-rule decision. Under the maintainer's instruction to stop on any error, the
  run stopped there: the outputs were not committed and nothing after this step
  was run until the maintainer decided.
- Diagnostic only (no output changed): at 2026-10-09T15:19:37Z the same check
  (`mast_availability`) for TIC 239638934 found one sector (83, 2024) of light curves
  and pixel files, so the data rule would have rejected it; the selected targets would
  be the same.
- **Maintainer's decision (2026-10-09, recorded at 15:25Z):** commit the
  outputs exactly as produced, without any change. Reason: the protocol requires the
  selection outputs to be committed unchanged, and a rerun could change the pools
  (the catalogs are live). The timeout is recorded here; the issue for handling such
  errors in future selections is https://github.com/klucilla/refute/issues/22
  (future phase; nothing implemented now). Nothing was rerun.

## Step 3: new development target (crash and I/O hunt only)

- Target: WASP-93 b (TIC 240681314), the 11th accepted planet, kind `development`
  in `targets.yaml`; excluded from the claim.
- Procedure: a scratch script that follows the per-target path of `refute calibrate`
  without a lock (TESS-EB content-hash check, fetch, offline load, analysis with the
  `eb_catalog.csv` and `eb_catalog_scan.json` attachments, plots, parameter sheet,
  verdict and report), writing a throwaway dossier under the git-ignored `dossiers/`.
  Code at commit `2d4d5ec`, claim-schema default thresholds.
- Time: 2026-10-09T15:26:13Z to 15:27:28Z.
- Data: SPOC 120-s light curves and target pixel files of sectors 17, 57 and 84
  (years 2019, 2022, 2024); 46570 cadences. In every sector the target pixel file
  kept exactly the light curve's cadences (12507, 17990 and 16073).
- Result: **no crash, no I/O or reading error** in any stage. For transparency, the
  analysis found a period of 2.732534 d (published 2.7325321 d) and the verdict
  SURVIVED, with every test PASS.
- Nothing was changed because of this target: no code, threshold, criterion or target.

## Steps 4 and 5: claim and lock

- Claim committed in `e176ac3` (claim SHA-256
  `c9f341d29bea4ec0d125adf3f0822fae4b593beabbdd19aeb339613e7a6b34a8`).
- `uv run --frozen refute lock calibration/v0.2/self_claim.yaml` at
  2026-10-09T15:29:55Z from `e176ac3` with a clean tree: code SHA-256
  `2cd8b5c16c9ded3e32335cd95d8b68f46e0676d5183f3129a6cef4e8dfbd1752` (38 files),
  6 attachments with the same SHA-256 as the committed selection outputs.
  `refute verify` returned PASS right after the lock.
- CI of the selection commit `2d4d5ec` passed (4 of 4 jobs) before the lock.

## Step 6: calibration

- Fetch: `uv run --frozen refute fetch calibration/v0.2/self_claim.yaml`, one target at
  a time, 2026-10-09T15:30:17Z to 15:50:35Z: TESS-EB content SHA-256 verified,
  20 of 20 targets ok, exit code 0.
- Run: `uv run --frozen refute calibrate --claim calibration/v0.2/self_claim.yaml
  --offline --out dossiers`, from commit `cc9d104` with a clean tree, 2026-10-09T15:50:43Z
  to 15:57:38Z, 30 worker processes, exit code 0. Run id `20261009T155044Z-c9f341d2`.
- Outcome: 20 of 20 targets analyzed, no analysis error. `refute verify` returned PASS
  after the run, and `refute check-dossier` found every one of the 20 dossier manifests
  intact.
- `results/20261009T155044Z-c9f341d2/summary.json` and `summary.md` are copied byte for
  byte from the run directory (same SHA-256) and have not been edited.
- **Self-claim result: FAIL.** Recovered planets 10 of 10 (>= 9, passed); flagged false
  positives without eb_catalog 7 of 10 (>= 6, passed); refuted planets 4 of 10 (<= 1,
  failed). As information, 8 of 10 false positives are REFUTED when every test counts.
- This is the only run. Nothing was rerun or changed after it. Reviews, the release
  and the phase gate are out of scope of this step.

## Step 7: independent reviews (14 of 17)

- **Scope and timing.** The 14 reviews that do not depend on the reviewer draw were
  run on 2026-10-09, at the maintainer's request: the 10 false positives and the 4
  planets with verdict REFUTED (the unexpected verdicts; no false positive SURVIVED).
  Before starting, `PROTOCOL.md` ("Reviews", step 7 of the order of steps) and
  `docs/reviewer-protocol.md` were checked: they require the results to be committed
  first (done in `fe2718c`) and fix the draw of the other 3 planets with drand round
  6542966; neither ties the 14 fixed reviews to that round. The 3 drawn planets are
  reviewed after the round is published (2026-10-11T12:00:00Z).
- **Reviewer.** Claude Opus 5.5 (`claude-opus-5-5`), one fresh session per dossier,
  at most 3 at a time. Each session received only the fixed prompt of
  `docs/reviewer-protocol.md` with the dossier path; no context from the session that
  ran the calibration, no other target's result and no hypothesis.
- **Isolation.** Each session got a byte-identical copy of its dossier (checked with
  `diff -r` and `refute check-dossier`) in its own directory under the git-ignored
  `.cache/review-isolation/`, so that no other dossier was next to it. The copy was
  deleted after the report was attached. Reviewers could still read the repository,
  as the protocol allows (code and git history at the commits named in
  `REPRODUCE.md`); several reports cite `git show`/`git diff` of `e176ac3` and
  `cc9d104`, and two cite files of the local data cache (`.cache/`): the target pixel
  files of TIC 33153766 and the TESS-EB snapshot for TIC 158561566. No report cites
  another target's result.
- **Storage.** Each report is the reviewer's final answer, extracted verbatim from
  the session transcript and attached to the original dossier with
  `uv run --frozen refute review attach <dossier> <report> --reviewer opus-1 --model
  claude-opus-5-5`. After each attachment `refute check-dossier` reported the manifest
  intact. Copies of `review/opus-1.md`, `review/index.json` and `review/index.md` of
  each dossier are in `results/20261009T155044Z-c9f341d2/reviews/<target>/`, identical
  to the dossier files. `refute verify` returned PASS after the reviews.
- **Verdicts.** Reviews never change a verdict; no verdict, summary or dossier
  analysis file was changed.
- **Second reviewer (Codex).** Left out: the Codex connection (MCP server `codex`) was
  not connected in this session ("Connection closed"), so the second review of the 4
  unexpected verdicts was not run.

Times are UTC on 2026-10-09: start is when the session was launched (within about
20 s), end is start plus the session's reported duration.

| Target | Name | Kind | Verdict | Start | End | Duration (s) | Reviewer assessment | Report SHA-256 |
|---|---|---|---|---|---|---|---|---|
| TIC 197650870 | TOI-1481.01 | false positive | REFUTED | 17:03:03 | 17:06:38 | 215 | SERIOUS OBJECTIONS | `bf613c5aa0fad7f0f42f2ecd89f00fb86d41a85c83ae457fd77cc73316cb5330` |
| TIC 33153766 | TOI-653.01 | false positive | REFUTED | 17:03:03 | 17:08:46 | 343 | OBJECTIONS | `1d20fea6893117d486085f736840bd1f4dfa8a124a3403f3e7259903fcf38e6a` |
| TIC 374200604 | TOI-4838.01 | false positive | INCONCLUSIVE | 17:03:03 | 17:06:11 | 188 | OBJECTIONS | `6e70b6274f459a01592e90d17ed396c72d2c7d4dba83216dc3e800f20fc15448` |
| TIC 350445771 | TOI-258.01 | false positive | REFUTED | 17:07:26 | 17:11:51 | 265 | OBJECTIONS | `ef87275c2fb5c948b6177e65197fab1e1e08d61b56ea308767cfda4953c66404` |
| TIC 317507345 | TOI-1615.01 | false positive | REFUTED | 17:07:27 | 17:11:49 | 262 | OBJECTIONS | `a1d957af23cd613d44e053ebd2784b017bca6de2ec5839ada80ba6b171497678` |
| TIC 158916431 | TOI-2146.01 | false positive | REFUTED | 17:08:50 | 17:11:37 | 167 | OBJECTIONS | `c3923ccf4d0bed7d1ae720f1f8fa09cba855e8602860488d02197a572eb715c8` |
| TIC 316916655 | TOI-441.01 | false positive | REFUTED | 17:11:52 | 17:14:40 | 168 | OBJECTIONS | `ba15f0ba054f507826e8141f2791ae338c419a2025c4ab0933857476e70aff99` |
| TIC 154459165 | TOI-611.01 | false positive | REFUTED | 17:12:35 | 17:16:42 | 247 | OBJECTIONS | `e98b5bc067c2d9ac7cdd350e1be2793c3196c93007c7f675f8519a81a69aaa3e` |
| TIC 294179389 | TOI-1310.01 | false positive | WEAKENED | 17:12:35 | 17:16:14 | 219 | SERIOUS OBJECTIONS | `9014491aec11a322b1d1f7ffee61bee18323ffd94053e20f718d230442e15ed3` |
| TIC 315755496 | TOI-2053.01 | false positive | REFUTED | 17:14:53 | 17:19:48 | 295 | SERIOUS OBJECTIONS | `84a7a14099447384659e7e46b3dbe3c8b32cf615b80d8aed512b3c5d7245d00a` |
| TIC 118327550 | TOI-244 b | planet | REFUTED | 17:16:17 | 17:19:53 | 216 | SERIOUS OBJECTIONS | `b7ee6640e78e7b12bf165b5d215f8f0a620484a83e6cfb8c5fc9e9f5b5023fe9` |
| TIC 48506505 | Kepler-447 b | planet | REFUTED | 17:16:44 | 17:19:56 | 192 | SERIOUS OBJECTIONS | `17310ae47e88b4bb7428596d909077ee39d12cf28a607838b580c9ba19eae54b` |
| TIC 158561566 | Kepler-14 b | planet | REFUTED | 17:20:29 | 17:24:42 | 253 | SERIOUS OBJECTIONS | `217884dc43d1660a05ed5f40c30ee62c807e6b7dbbf3cc217544b15369cb8e9d` |
| TIC 194736418 | TOI-6038 A b | planet | REFUTED | 17:20:29 | 17:24:05 | 216 | SERIOUS OBJECTIONS | `ac6fe0cae720a8e1e2e8277b0218f5524a4ca01c80faebc652ffcbaad723eed9` |
