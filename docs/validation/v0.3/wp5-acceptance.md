# WP5 acceptance: selection

Line numbers refer to docs/plans/v0.3-plan.md at commit 8456780.

Work package WP5 of [docs/plans/v0.3-plan.md](../../plans/v0.3-plan.md) (section 11,
line 884). Issue #48. Also covers #22. Committed **before** the tests and code of the
package (plan lines 871-875).

WP5 builds the selection tooling and tests it offline. It runs **no drand round**,
draws no paper and freezes no inventory: those steps belong to WP7, each with its own
commit and the maintainer's approval.

## 1. What the package must do

### 1.1 Shared drand module (plan lines 167-172)

- **W5.1** `round_time`, `verify_beacon` and `drand_seed` move from
  `calibration/v0.2/select_targets.py` into a shared module under `src/refute/`. Their
  behavior is unchanged. `tests/test_drand.py` passes against the shared module.
- **W5.2** `calibration/v0.2/select_targets.py` keeps working for its recorded use.
  Either it keeps its own copy, or it imports the shared module. A test recomputes,
  offline, the parts of the v0.2 selection that need no network: the seed from the
  recorded beacon and the shuffled order of the recorded snapshot. Both must match
  the v0.2 selection log. The MAST checks of that selection are not repeated.

### 1.2 Frame (plan 4.1 and 4.2, lines 116-161)

- **W5.3** The frame snapshot: the Parquet file of
  `pwc-archive/links-between-paper-and-code`, read with `pyarrow` (WP0, D-18). Its URL,
  revision and SHA-256 are recorded.
- **W5.4** The mechanical filters, in order, with the count after each one:
  1. deduplication by `paper_arxiv_id` and `repo_url`;
  2. `is_official` and `mentioned_in_paper`;
  3. the window, from the new-style arXiv ID;
  4. the category, checked for walked papers only;
  5. one repository per paper;
  6. the out-of-scope keywords;
  7. removal of the pilot papers.
- **W5.5** The adjustment by the pilot: an ordered list of alternatives with triggers,
  applied by code; the first alternative whose trigger fires is used, at most once.

### 1.3 Draw and walk (plan 4.3, lines 163-179)

- **W5.6** The order: sort by arXiv ID, then shuffle with `random.Random(seed)`. The
  walk is logged with one reason from the closed list for each candidate.
- **W5.7** Retries of transient errors (#22). Queries to arXiv, GitHub and Hugging
  Face retry transient errors (timeouts, HTTP 5xx, connection errors) a fixed number
  of times with a fixed backoff. Both values are written in the protocol, which is
  locked before its drand round.
  - Transient errors are logged apart from rule-based rejections: every attempt, with
    its time and error.
  - A candidate still unchecked after the retries **stops the walk** for the
    maintainer; it is never rejected silently.
- **W5.8** If drand is unavailable or a signature fails, the tool stops; it never
  switches the source of randomness (plan lines 178-179).

### 1.4 Claim inventories and draw (plan 5.2, lines 269-314)

- **W5.9** An inventory format with the fields of the claim spec: canonical ID, reading
  order, type, comparison reference, transcription and approvals, and the eligible
  comparison flag. Its SHA-256 is computed over a canonical form.
- **W5.10** The claim draw:
  - shuffle with `random.Random(int.from_bytes(sha256(claim_seed_bytes ||
    arxiv_id_utf8), "big"))` and take K = 3;
  - when the inventory has an eligible comparison and none of the 3 is a comparison,
    replace the 3rd by the first comparison in the shuffled order;
  - with no eligible comparison, take up to 3 value claims and record that no
    comparison was evaluated;
  - with 3 candidates or fewer, take all;
  - replacement after the draw follows the next candidate in the shuffled order, of
    the same type when the comparison must be kept, and only for a reason of the
    closed list.
- **W5.11** **Proof that the inventories were published before the claim round.**
  - **Git dates are not evidence.** Author and committer dates are set by whoever
    makes the commit (https://git-scm.com/docs/git-commit#_commit_information,
    accessed 2026-10-14).
  - **Evidence:** a server-side GitHub timestamp tied to the commit SHA that contains
    the inventories and their hashes. It is the `created_at` of the GitHub Actions run
    started by the push of that commit, read from the GitHub API and saved in the
    protocol record. The inventories are stored in a path that the CI `paths-ignore`
    list does not skip, so that the push starts a run.
  - **Rule:** the evidence must be earlier than the claim round's publication time by
    a margin fixed in the protocol.
  - **Missing evidence:** no run, an API error, or evidence for another SHA makes that
    round unusable for those inventories. The tool refuses to draw; the maintainer
    decides.
  - **Other refusals:** a dirty working tree, an inventory file whose hash differs
    from the published one, and an inventory not in the commit of the evidence.

## 2. Synthetic cases (offline; fixtures for drand, PyPI-free)

**Must pass:**
- the recorded v0.2 round verifies, and its seed matches;
- the filters on a small synthetic frame give the expected counts;
- the draw from a fixed seed gives the same order on Windows and Linux;
- the claim draw with and without an eligible comparison;
- the retry path that succeeds on the second attempt.

**Must fail:**
- a beacon with a wrong signature is refused;
- a transient error that persists stops the walk; it is not a rejection;
- an inventory not pushed before the round is refused;
- a commit with an author and committer date before the round, but whose push (and
  run) happened after it, is refused;
- missing push evidence is refused, and the round is marked unusable;
- a pilot adjustment that is not the first triggered alternative is refused;
- a second adjustment is refused.

## 3. Metrics and evidence

- Test counts come from a JUnit XML file.
- CI is green on the four jobs.
- Each criterion W5.1 to W5.11 is listed in the PR with its test.

## 4. Regression cases

- The existing suite passes, including `tests/test_drand.py`.
- The offline parts of the v0.2 selection (W5.2) match its selection log.
