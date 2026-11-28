# Publishing raw outputs (Zenodo)

Decided by the maintainer on 2026-10-24, in force **from X2f on**. Sources of every statement
about Zenodo: [sources/zenodo-2026-10-24.md](sources/zenodo-2026-10-24.md) (read on 2026-10-24).

## The rule

1. **Raw outputs larger than 5 MB never enter git.** They are archived to the maintainer's Drive
   with a SHA-256 manifest of source and destination, checked. The repository keeps the script
   that produced them, a summary and that manifest (CLAUDE.md, "Operating rules").
2. **For external reproduction they are published on Zenodo, with a DOI**, as datasets.
3. **What may go there:** only synthetic data and Refute's own results. **Never** data under a
   restricted license (for example the TESS Eclipsing Binary catalog or Gaia DR3 rows, see
   `calibration/v0.2/eb_snapshot/DATA_LICENSE.md`), and **nothing about a paper whose authors'
   reply period is open**.
   **Exception, restricted to v0.4 (the maintainer's decision of 2026-11-01).** The v0.4 pilot's
   dossiers and its two reproduction archives may be published, on Zenodo and elsewhere, although
   they hold Gaia DR3 rows (CC BY-NC 3.0 IGO) and TESS-EB records (CC BY 4.0). This also sets
   aside, for them only, the maintainer's precaution of 2026-10-08/10 not to redistribute TESS-EB
   rows (`calibration/v0.2/eb_snapshot/DATA_LICENSE.md`). Reasoning: these dossiers are sealed, and
   removing the rows would break their seals and the hashes that a third-party reproduction
   checks; the sources permit redistribution with attribution (and, for Gaia, for non-commercial
   use only). Each component keeps its own terms, stated outside the sealed bytes in
   [calibration/v0.4/DATA_LICENSE.md](../calibration/v0.4/DATA_LICENSE.md), with sources. The
   exception is not a general change of this rule, and it grants no right the sources do not
   grant. Recorded in issue #177.
   **Exception, restricted to v0.5 (the maintainer's decision of 2026-11-05).** The v0.5
   calibration's third-party files (`calibration/v0.5/eb_catalog.csv`, with 3 Gaia DR3 rows
   (CC BY-NC 3.0 IGO) and TESS-EB references that are TIC numbers only; the frozen inputs
   `calibration/v0.5/inputs/toi.csv`, `pscomppars.csv` and `target_lists.html`; and
   `calibration/v0.5/inputs-references/pscomppars-references.csv`, added on 2026-11-06) stay in
   the repository and in the release's Zenodo archive, although rule 3 keeps Gaia DR3 rows off
   Zenodo. Reasoning: they are attachments and frozen inputs of the locked C3 claim, whose hashes
   a third-party reproduction checks, and the references the archive asks to cite. Each component
   keeps its own terms, stated in [calibration/v0.5/DATA_LICENSE.md](../calibration/v0.5/DATA_LICENSE.md),
   with sources. No v0.5 data record is published on Zenodo. The exception is not a general
   change of this rule, and it grants no right the sources do not grant. Recorded in issue #199.
   The third-party files of earlier phases that are kept in the repository (the v0.1 and v0.2
   pool snapshots, the v0.2 and v0.4 catalog attachments and the v0.4 frozen inputs) have been in
   each release archive since they were committed, and stay there, with the references file of
   the v0.4 known-planet control added on 2026-11-06; each is listed, with the record that states
   its terms, in [third-party-data.md](third-party-data.md) (the maintainer's decisions of
   2026-11-06, #199).
4. **A license in every record.** Zenodo requires one for every public file (S2). **Synthetic
   datasets: CC-BY-4.0** (Zenodo's default, S5; approved by the maintainer on 2026-10-24); any
   other content gets its license decided in its own record.
5. **Drafts only.** The agent prepares the files, their SHA-256 manifest and the record's
   metadata (title, description, creators, license, the Refute commit and the repository paths
   of the script, summary and manifest) as a **draft**. **The maintainer publishes; the agent
   never publishes a record.** A published record cannot simply be changed: its files can be
   corrected only within 30 days, and a significant change is a new version.
6. **Limits per record:** at most 50 GB and 100 files (S1, S3); more than 20 files are packed in
   a ZIP archive (S4). A larger set is split across records, each with its own manifest, or a
   higher quota is requested by the maintainer.
7. **The record and the repository point at each other:** the record cites the commit and the
   manifest's path; the repository's summary gives the DOI once the maintainer has published.

## The drafts are made through Zenodo's API (decided on 2026-10-24)

The agent creates each draft and uploads its files and metadata with Zenodo's deposit API,
using a personal token of the maintainer with the scope `deposit:write` only (no
`deposit:actions`, so the token cannot publish; no `user:email`).

- **Where it is:** a local file of the maintainer, outside the repository.
- **How it is used:** read from that file only inside the Python process that makes the call to
  Zenodo's API, at the moment of the call, and passed only in the authorization header. It is
  never printed, logged, written to another file, copied into the repository or `.cache/`,
  given as a command-line argument (visible in the process list) or kept in a persistent
  environment variable. The agent never changes, moves or deletes that file.
- **Before the first real use:** the agent confirms only that the file exists and that its
  line holds a value, showing the token's length, never its value.
- **Publishing:** never by the agent (the token does not allow it); the maintainer publishes
  each record from Zenodo's web page.
- **Revoking:** the maintainer revokes the token on Zenodo's **Applications** page (account
  settings, personal access tokens); a new token, if any, follows the same rules.

## Separate: the archive of each release

The Zenodo–GitHub integration archives **each new release** of an enabled repository
automatically (S6). That is the software's archive, made by Zenodo from a GitHub release; it is
separate from the datasets above, which are deposited one by one as drafts and published by the
maintainer.

**The integration is active for this repository:** release v0.2.0 was archived, with version
DOI `10.5281/zenodo.23301001` and concept DOI `10.5281/zenodo.23301000` (issue #53). **Before
the next release**, the `.zenodo.json` of #53 must be on `main`: when present it replaces the
metadata Zenodo takes from `CITATION.cff`, so that each release's record carries the data terms
of each component.

### Papers in their authors' reply period (adopted 2026-11-27, #207, the maintainer's decision X1)

Rule 3's reply-period restriction ("nothing about a paper whose authors' reply period is open")
also applies to every artifact a release makes public, for papers still under embargo.
- **Exception:** item 2 below.
- **Courtesy periods:** governed by item 1.

The artifacts include:
- the Zenodo archive of the release;
- the GitHub release's source ZIP and tarball;
- the wheel and sdist published to PyPI or TestPyPI. The release workflow builds these from
  `main`, which may be another commit than the release tag's.

**Before each release, and again before each package publication:**

1. **The list.**
   - **Where the agent looks.** The agent inventories the papers that the exact commit of each
     artifact holds, and the planned public text (release notes, the release's issue).
   - **What the `reply/` annexes must show** for each paper
     ([right-of-reply.md](right-of-reply.md), items 5 to 7):
     - the notice recorded;
     - any delivery failure;
     - where a reply period applies, its effective deadline, extensions included.
   - **What goes on the list:**
     - every open reply period;
     - every paper whose eligibility for publication is unresolved: a gate not yet passed, or
       missing or ambiguous evidence of the notice or the deadline.

     An unresolved paper is treated as under embargo.
   - **How a mandatory wait is counted:**
     - a deadline given as a date stays open through that date, in the time zone recorded for the
       deadline;
     - an ambiguous cutoff is treated as unresolved;
     - a reply received does not end the wait.
   - **Courtesy periods** ([right-of-reply.md](right-of-reply.md), "Papers with no negative claim")
     do not block, once the notice is recorded and the gate has passed.
   - **Before any public tag or publication,** the list is computed again against the exact
     commit, the actual artifacts and the planned public text, with the current reply and gate
     states.
     - The release's issue records the commit's SHA, the date, and the list or "none".
     - For each package publication it also records the build's SHA and the SHA-256 of the wheel
       and the sdist, before the deployment is approved.
2. **When a release may be published.**
   - **When the check passes:** when no listed paper is still under embargo. The check also passes when the maintainer records in the release's issue
     that every public artifact and text holds only hashes or neutral metadata about each listed
     paper still under embargo ([right-of-reply.md](right-of-reply.md), item 3).
   - **Who publishes:** the maintainer approves the public text, and authorizes each public tag or
     publication only after the check passes. The maintainer starts the publication, including by
     approving the deployment of a package upload.
   - **A paper's results** are published only under the conditions of
     [right-of-reply.md](right-of-reply.md), "Order: notification, gate, publication". **An
     author's reply** is published only with their permission (item 7 there).
3. **If the check blocks a publication.** The release is held, unless item 2 allows it. Git history
   is kept as it is. If a release breached this rule, a separate dated correction is prepared for
   the maintainer's approval, and the next release notes refer to it.
4. **The public record.** The release's issue records the check and the decision. The approved
   release notes summarize the list, or say "none". While an embargo applies, the issue, the notes
   and any public correction use only hashes or neutral metadata about that paper.
