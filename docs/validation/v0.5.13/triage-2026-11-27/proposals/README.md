# Proposals for the maintainer's decision (block W)

**PROPOSED. Not adopted:** nothing here is in force until the maintainer approves it in #218.

## `207-rule.patch`: release archives and papers in a reply period (#207, W1(e))

- **What it is:** an applicable patch to `docs/data-publication.md`, against the file at the commit
  that adds this folder. It adds the section "Papers in their authors' reply period". It is not
  applied: `docs/data-publication.md` is unchanged.
- **The rule:**
  - rule 3's reply-period restriction reaches every artifact a release makes public: the Zenodo
    archive, the GitHub source archives, and the wheel and sdist on PyPI or TestPyPI;
  - a list of the papers concerned is computed from the exact commit and artifacts before each tag
    or publication, and recorded in the release's issue;
  - the rule states when the check passes, and that the maintainer authorizes and starts each
    publication;
  - it gives the path if the check blocks a release, and the public record.
- **It leaves to the maintainer:**
  - whether the exception of item 2 is adopted;
  - whether a dated note is linked to the Zenodo record of v0.4.0.
- **Codex** (read-only, one conversation, thread `01a21f4f-203d-79c0-abca-df83635ecf5e`), three
  rounds, each `WEAKENED`. Their findings are applied, and the last round's single finding is
  applied without a fourth round. The rounds are stored unchanged in `../codex/w1e-r*`.
- **Two departures from Codex's text,** which round 2 accepted:
  - item 2 refers to the order of publication in `right-of-reply.md` instead of copying it;
  - the v0.4.0 question does not state, as a fact, how Zenodo edits published records, since the
    agent did not verify it.
