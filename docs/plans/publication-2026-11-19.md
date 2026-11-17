# The publication of 2026-11-19: the day's script

**The decision.** The maintainer's decision of 2026-11-16 (#217), item 1e: "Escreva
docs/plans/publication-2026-11-19.md com o roteiro do dia: a ordem exata (começando pela minha
confirmação do período de resposta), cada comando em uma linha, o que conferir depois de cada um,
e o que é meu (publicar a release, o Zenodo, o deploy do site, fechar issues)."

**What this is.** A script prepared on 2026-11-16. Nothing in it has been done.
- **Marked [M]:** the maintainer's steps. They are never the agent's: publishing or changing
  public text, the go-ahead to annex the withheld reviews, the release, the tag, Zenodo, the
  site's approval and deploy, and closing issues.
- **Marked [A]:** steps the agent runs only after the maintainer's go-ahead for that part, on the
  day.
- **Commands** are for Git Bash, from the repository root unless a step says otherwise, one per
  line. `<SHA1>`, `<SHA2>`, `<SHA3>` and `<DOI>` are values noted on the day.
- **The drafts** are outside `main`: the release drafts in `.cache/v05/release/`, the v0.3 drafts
  and tools in `.cache/pub1119/`, and the site's draft on a local branch of the site's repository.
- **A check that fails stops its part.** Nothing below is retried with a changed rule.

## Part 0. The reply period (the first step of the day) [M]

The maintainer confirms the final state of the two notices of 2026-10-20 (#158): "period ended",
with or without a reply.

- **No reply for either paper:** go on to part 1.
- **A reply, a delivery failure, or a request for an extension:** STOP part 1, and nothing says
  "period ended" anywhere: not on #158, and not on the site (the v0.3 sentence of part 3 is then
  left as it is today). Part 2 and the rest of part 3 do not depend on it and may go on. Nothing
  in part 1 is prepared for that case: a reply is published only as its authors allow, and an
  extension moves the period's end.

## Part 1. v0.3: the withheld files of 2309.15704 (#162, steps 1 to 5; #158; #52)

Rehearsed on 2026-11-16 on a copy of the dossier inside `.cache/` (nothing in
`calibration/v0.3/` changed). The annex manifests carry no timestamp, so the expected
`ANNEX.json` hashes are known.

**1.1 [A] Check `main` and the SHA before anything.**

```
git status --short
git rev-parse --abbrev-ref HEAD
git rev-parse HEAD
```

Check: no change listed; the branch is `main`; note the SHA.

**1.2 [M] Post the period's state on #158** (step 1 of #162). The draft is
`.cache/pub1119/v03/issue-158-period-ended.draft.md`. It states only the end of the period and
that no reply came; it does not say the annexes exist. The maintainer reads it, corrects the date
of the check, and posts it or tells the agent to.

```
gh issue comment 158 --body-file .cache/pub1119/v03/issue-158-period-ended.draft.md
```

Check: the comment is on #158 and names no address and no message identifier.

**1.3 [A] Check the three withheld files against the SHA-256 values published on 2026-10-20**
(step 2 of #162).

```
sha256sum .cache/seal/reviews/2309.15704/review-opus.md
sha256sum .cache/seal/reviews-codex/2309.15704/review-codex.md
sha256sum .cache/seal/notices/sent/2309.15704-sent-body.txt
```

Check, exactly:

| File | SHA-256 | Bytes |
|---|---|---|
| `review-opus.md` | `e2e16a804a59ccd601f0027ab03617743a0c88558bc25ba6ead72a19d079e2f4` | 9,039 |
| `review-codex.md` | `c34c8724ab14255814be8813b26b805a8a9a189b347a6ce7f6c18f9aba5c2fd0` | 6,702 |
| the notice body | `750c99c91cde29f5419ef2e924c2925fa10a84805fa38e409111295cee7c995c` | 3,232 |

A different value is a STOP: the backup's manifest (#162) is then compared by the maintainer.

**1.4 [A] Put the notice body in a folder of its own, under its published name.**

```
mkdir -p .cache/pub1119/v03/reply-body
cp .cache/seal/notices/sent/2309.15704-sent-body.txt .cache/pub1119/v03/reply-body/notice-body.txt
sha256sum .cache/pub1119/v03/reply-body/notice-body.txt
```

Check: the folder holds that one file, with the SHA-256 `750c99c9…995c`. (The folder exists
since the rehearsal; the copy is repeated so that the day's bytes are checked.)

**1.5 [M] The go-ahead to annex.** The maintainer says, in the session, that the three withheld
files may be attached. This is the non-delegated stop "anexar as revisões retidas da v0.3".
Without it, steps 1.6 to 1.12 do not run.

**1.6 [A] Attach the three annexes, unchanged** (step 3 of #162).

```
uv run --frozen refute annex calibration/v0.3/main/dossiers/2309.15704/dossier review-opus .cache/seal/reviews/2309.15704
uv run --frozen refute annex calibration/v0.3/main/dossiers/2309.15704/dossier review-codex .cache/seal/reviews-codex/2309.15704
uv run --frozen refute annex calibration/v0.3/main/dossiers/2309.15704/dossier reply-body .cache/pub1119/v03/reply-body
```

Check: each command prints the core `314ec192…7d3f` and its `ANNEX.json` SHA-256:

| Annex | Expected `ANNEX.json` SHA-256 |
|---|---|
| `review-opus` | `2907eb8bf4c15eb0da7acdf7a5c354d3c394f51bfd8405e56d4816238e45f188` |
| `review-codex` | `dc24eda1ba372c6789f09afd6ee3d5f6ec00603c6261d5d28639bd565844f3ba` |
| `reply-body` | `8848cab6120e9f0a77b308e94061c574e21a0760b5acb0ce2d6a4b1da9f5e111` |

**1.7 [A] Check the dossier.**

```
uv run --frozen refute check-dossier calibration/v0.3/main/dossiers/2309.15704/dossier
```

Check: "core: intact against its seal"; the five annexes (`reply`, `reply-body`, `review-codex`,
`review-opus`, `verification`) each "intact against its manifest"; "OK: manifest intact".

**1.8 [A] Append the three hashes to `ANNEX-RECORD.md`** (step 4 of #162; append-only; the script
refuses if a hash differs from the table above).

```
.venv/Scripts/python.exe -B .cache/pub1119/v03/apply_annex_record.py
git diff --stat calibration/v0.3/main/ANNEX-RECORD.md
```

Check: "appended … bytes; the first 5644 bytes are unchanged"; the diff shows insertions only.

**1.9 [A] Add the record of the cause's analysis** (step 5 of #162). The draft is
`.cache/pub1119/v03/cause-analysis.draft.md`. The maintainer reads it first; the bracketed fields
and the draft's header lines are settled in the draft before the copy.

```
cp .cache/pub1119/v03/cause-analysis.draft.md calibration/v0.3/main/dossiers/2309.15704/cause-analysis.md
grep -c "\[" calibration/v0.3/main/dossiers/2309.15704/cause-analysis.md
grep -c -i "draft" calibration/v0.3/main/dossiers/2309.15704/cause-analysis.md
```

Check: both counts are 0.

**1.10 [A] Run the affected tests and the dossier verifier.**

```
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/run_tests_affinity.ps1 -Junit .cache/pub1119/junit-v03.xml -Tests tests/test_verify_dossiers.py,tests/test_seal.py
.venv/Scripts/python.exe -B scripts/junit_counts.py .cache/pub1119/junit-v03.xml
uv run --frozen python calibration/v0.3/verify_dossiers.py --out .cache/pub1119/verify-v03 2309.15704
```

Check: "pytest exit=0"; the JUnit counts show no failure and no error; the verifier prints
"2309.15704: VERIFIED", as it did on the untouched dossier on 2026-11-16 (it compares the annex set
with the record's, so a missing row or a missing annex would show as a "V1 annexes" finding).

**1.11 [A] Stage; check privacy and addresses; commit and push** (one commit: the three annexes,
the record, the analysis).

```
git add calibration/v0.3/main/dossiers/2309.15704 calibration/v0.3/main/ANNEX-RECORD.md
git status --short
.venv/Scripts/python.exe -B .cache/v051/tools/privacy_check.py
.venv/Scripts/python.exe -B .cache/pub1119/tools/address_check.py
.venv/Scripts/python.exe -B scripts/commit_checked.py -F .cache/pub1119/v03/commit-annex-2309.draft.txt
git push origin main
git rev-parse HEAD origin/main
```

Check:
- the status lists only files under `calibration/v0.3/main/dossiers/2309.15704/` and
  `ANNEX-RECORD.md`;
- the privacy check reports no hit;
- the address check prints "0 hit(s)" (it looks for e-mail addresses, message headers and
  message identifiers in every staged file, which the privacy check does not; on 2026-11-16 it
  found none in the rehearsal's files);
- the two SHAs are equal. This SHA is `<SHA1>`.

**1.12 [A] Wait for CI on that commit** (in the background, with a 90-minute limit).

```
.venv/Scripts/python.exe -B .cache/pub1119/tools/wait_ci_strict.py 90 <SHA1>
```

Check: the command exits with code 0 and prints "CI succeeded for this commit". Code 1 is a
failed run, and code 2 a deadline with no CI run or an incomplete one. A red run is fixed forward
before part 2's tag.

**1.13 [M] Post the comments that announce the annexes, and close the issues.** The drafts are
in `.cache/pub1119/v03/`; `<SHA1>` replaces the placeholder in each before it is posted.

```
gh issue comment 158 --body-file .cache/pub1119/v03/issue-158-annexes-attached.draft.md
gh issue comment 162 --body-file .cache/pub1119/v03/issue-162-closing.draft.md
gh issue comment 52 --body-file .cache/pub1119/v03/issue-52-closing.draft.md
```

Check: each comment carries `<SHA1>` and names no address. Closing #162 and #52 is the
maintainer's. #135 (the VM's decommission) waited for the period's end and is the maintainer's
decision.

## Part 2. Release 0.5.0

**2.1 [A] A final Codex review of the final drafts, before anything is applied** (the
maintainer's decision of 2026-11-16, 21:40, item 1c). One round, read only, through the affinity
wrapper, on every draft of `.cache/v05/release/` as it stands on the day. Its answer goes,
unchanged, to `docs/plans/publication-2026-11-19-consensus/`.

```
git diff --no-index README.md .cache/v05/release/README.draft.md > .cache/v05/release/README.diff
powershell -NoProfile -ExecutionPolicy Bypass -File .cache/v04/tools/codex_affinity.ps1 -Prompt .cache/pub1119/codex/pub-final-r1-prompt.md -Answer .cache/pub1119/codex/pub-final-r1-answer.md -Events .cache/pub1119/codex/pub-final-r1-events.jsonl
```

Check: the answer ends with `SURVIVED`. With `WEAKENED` or `REFUTED`, the corrections are applied
to the drafts and reviewed again (up to 3 rounds), and nothing of part 2 is applied before a
`SURVIVED` or the maintainer's decision. The prompt is written on the day; it names the drafts,
`metadata-changes.md` and the decisions of 2026-11-16.

**2.2 [M] Read and approve the drafts** in `.cache/v05/release/`: `README.draft.md`,
`release-notes-v0.5.0.en.md` (the Portuguese copy is for reading only), `CITATION.draft.cff`,
`zenodo.draft.json`, and `metadata-changes.md`, which lists every change and each legal
statement's `sources/` record.

**2.2b [A] Check that the README draft still sits on `main`'s README.**

```
git log -1 --format=%H -- README.md
git diff --no-index --stat README.md .cache/v05/release/README.draft.md
```

Check: the last commit of `README.md` starts with `61f7ab0` (the base of the draft); the diff
shows only the draft's changes.

**2.3 [A] Apply the three drafts.**

```
cp .cache/v05/release/README.draft.md README.md
cp .cache/v05/release/CITATION.draft.cff CITATION.cff
cp .cache/v05/release/zenodo.draft.json .zenodo.json
git status --short
```

Check: exactly three files modified.

**2.4 [A] Run the affected tests and the lock check.**

```
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/run_tests_affinity.ps1 -Junit .cache/pub1119/junit-release.xml -Tests tests/test_update_readme.py,tests/test_v05_claim_committed.py,tests/test_v05_deviation.py,tests/test_cli.py,tests/test_verify_locked_tags.py
.venv/Scripts/python.exe -B scripts/junit_counts.py .cache/pub1119/junit-release.xml
.venv/Scripts/python.exe scripts/verify_locked_tags.py
```

Check: "pytest exit=0"; no failure and no error in the JUnit counts; the lock check verifies 9
locks at their tags.

**2.5 [A] Stage; check privacy and addresses; commit and push.** The commit message is written
on the day to `.cache/pub1119/commit-release-0.5.0.txt`, from `metadata-changes.md`, section 2.

```
git add README.md CITATION.cff .zenodo.json
.venv/Scripts/python.exe -B .cache/v051/tools/privacy_check.py
.venv/Scripts/python.exe -B .cache/pub1119/tools/address_check.py
.venv/Scripts/python.exe -B scripts/commit_checked.py -F .cache/pub1119/commit-release-0.5.0.txt
git push origin main
git rev-parse HEAD origin/main
```

Check: no privacy hit; "0 hit(s)" from the address check; the SHAs are equal. This SHA is
`<SHA2>`.

**2.6 [A] Wait for CI on that commit.**

```
.venv/Scripts/python.exe -B .cache/pub1119/tools/wait_ci_strict.py 90 <SHA2>
```

Check: exit code 0 and "CI succeeded for this commit", before the tag. With code 1 or 2, there
is no tag.

**2.7 [M] Tag and publish the release,** on the checked commit, with the English notes as its
body. One way:

```
gh release create v0.5.0 --target <SHA2> --title "Refute v0.5.0" --notes-file .cache/v05/release/release-notes-v0.5.0.en.md
git fetch origin --tags
git rev-parse v0.5.0^{commit}
```

Check: the last command prints `<SHA2>`; the release page shows the notes; the links of the
notes (they use `blob/v0.5.0/` and `tree/v0.5.0/`) open.

**2.8 [M] Zenodo.** The GitHub integration creates the software record of version 0.5.0. The
maintainer checks its metadata against `.zenodo.json` and publishes it if the integration left a
draft. The agent never publishes a record.

Check: the version DOI exists and resolves; the concept DOI `10.5281/zenodo.23301000` lists
0.5.0. The maintainer gives the version DOI, `<DOI>`, to the session.

**2.9 [A] The second, small commit: the 0.5.0 version DOI** in `CITATION.cff` and `README.md`
(rehearsed on copies on 2026-11-16).

```
.venv/Scripts/python.exe -B .cache/pub1119/tools/apply_version_doi.py <DOI>
git diff --stat
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/run_tests_affinity.ps1 -Junit .cache/pub1119/junit-doi.xml -Tests tests/test_update_readme.py,tests/test_cli.py
.venv/Scripts/python.exe -B scripts/junit_counts.py .cache/pub1119/junit-doi.xml
git add README.md CITATION.cff
.venv/Scripts/python.exe -B .cache/v051/tools/privacy_check.py
.venv/Scripts/python.exe -B .cache/pub1119/tools/address_check.py
.venv/Scripts/python.exe -B scripts/commit_checked.py -F .cache/pub1119/commit-version-doi.txt
git push origin main
git rev-parse HEAD origin/main
.venv/Scripts/python.exe -B .cache/pub1119/tools/wait_ci_strict.py 90 <SHA3>
```

Check: the script prints "CITATION.cff and README.md now carry `<DOI>`"; the diff shows two
files; "pytest exit=0" with no failure and no error; no privacy or address hit; the SHAs are
equal (`<SHA3>`); the CI wait exits with code 0. The commit message is written on the day.
The tag `v0.5.0` stays on `<SHA2>`.

## Part 3. The site (its own repository and session)

The draft is the local branch `draft/status-2026-11-19` of the site's repository (commits
`5e02bbf` and `d8b2999`, not pushed). It changes only the status page's editorial text.
The site's own rules apply: no push, no deploy, no DNS and no visibility change without the
maintainer's approval given for that change. The commands below run from the site's repository
root.

**3.1 [A] Register the release, then fetch it.** The fetch refuses a tag that is not in
`releases/registry.json` or has no `releases/v0.5.0/sources.json`. So, by hand first, on the
model of v0.4.0's entries:
- add `v0.5.0` to `releases/registry.json`;
- write `releases/v0.5.0/sources.json` with the files the site will quote: the roadmap, v0.5's
  closing record and gate reviews, the closing records of v0.5.1 to v0.5.3, and v0.5.4's
  second-half report and pause record.

```
git switch draft/status-2026-11-19
npm run fetch -- v0.5.0
```

Check: `releases/v0.5.0/manifest.json` exists and names the tag's commit, `<SHA2>`. The fetch
refuses a file under a right-of-reply embargo; that is a STOP, not something to work around.

**3.2 [A] Rebase the draft's text on the release, by hand,** in `content/status/status.yaml` and
the two string files:
- the phases' purposes are quoted from the v0.5.0 roadmap;
- v0.5 becomes "released", with its results page;
- the commented `source` entries of v0.5.1 to v0.5.4 are enabled, each with its `source` string in
  both languages;
- the v0.3 sentence stays as drafted only if part 0 ended with "period ended"; otherwise it is
  restored to today's text.

**3.3 [A] Commit the text locally** (no push). The translation record names the commit that
holds the reviewed text, so the text is committed before it is accepted.

```
git add content/status/status.yaml src/i18n/en.ts src/i18n/pt-br.ts releases/registry.json releases/v0.5.0
git status --short
git commit -m "Status text and release v0.5.0 for the publication of 2026-11-19 (not yet approved)"
```

Check: the status is clean after the commit, and the branch is still `draft/status-2026-11-19`.

**3.4 [A] Run the site's checks before the approval.**

```
npm run heavy -- npx vitest run tests/unit
npm run heavy -- npm run test:build
```

Check:
- the unit tests fail only on the editorial approval and the translation record (three tests on
  2026-11-16; a fourth, `deploy-scripts`, failed in that session's environment when starting bash
  and is to be re-run);
- the build tests pass, including the scan of numbers in the pages (the draft's sentence with
  the decision's date is checked there).

**3.5 [M] Approve the status text and the translation.** The maintainer reads the built status
page in both languages and approves the text. On that instruction, the agent writes into
`content/status/approval.json` the new SHA-256, the date, the basis, and `approved.site_commit`,
which becomes the full SHA of the commit of 3.3 (today it still names `f03c3e8`). The translation
is then accepted in the reviewer's name:

```
npm run translation:accept -- --by "<the reviewer's name>"
git add content/status/approval.json src/i18n/pt-br.record.json
git status --short
git commit -m "Approval of the status text and the translation record (2026-11-19)"
npm run heavy -- npx vitest run tests/unit
npm run check:launch
```

Check: `approved.site_commit` in the approval record equals the commit of 3.3 (`git rev-parse
HEAD` before this step's commit); the acceptance prints that same commit; the status lists only
the approval record and
the translation record (`src/i18n/pt-br.record.json`), both staged; every unit test passes; the
launch gate prints "LAUNCH GATE: READY" (exit code 0). With BLOCKED or UNVERIFIED there is no
deploy.

**3.6 [M] Push and deploy.** The maintainer asks for the push, and deploys through the site's
own deploy scripts, only after READY.

Check: the public status page shows the approved text and its fingerprint.

## Part 4. Closing the day

**4.1 [M]** decide which issues to close (#162, #52; the tracking issues of v0.5 and of the
correction rounds).

**4.2 [A]** a short report on #217: what was published, each commit's SHA, the CI results, and
what stayed open. Then the session returns to the pause.

## What is not part of the day

- No lock, no drand round, no selection of real targets, no dependency change.
- No change to `ROADMAP.md` or to the advance rule.
- No data record on Zenodo.
- Nothing about TOI-7930 (`toi-7930-sector-check.md` records a check and questions only).
