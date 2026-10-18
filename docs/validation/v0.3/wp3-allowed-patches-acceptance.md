# WP3 addendum: applying the allowed patches of a claim

Addendum to [wp3-acceptance.md](wp3-acceptance.md) (W3.9, the build ladder and the allowed
patches), committed before its tests and code (plan section 11). The design was reviewed
by Codex on 2026-10-18 before any code; its objections are in the text below.

## 0. Why

`build.allowed_patches` exists since WP3: a list of attachments with role `allowed-patch`,
each with a reason, whose bytes are covered by the lock, and `ladder.check_patch` refuses
a patch that is not listed or whose SHA-256 differs. But production never applies a
patch: the repository copy each container gets is the clone as it is. Two papers of the
main sample need one, by the maintainer's decisions of 2026-10-18:

- **2309.15704** downloads its UCI datasets inside `run.py` (`uci_datasets.py`,
  `urllib.request.urlopen` on the UCI, OpenML and naval-mirror URLs), and a run has no
  network. Decision 3: a minimal patch that replaces each URL with the path of the
  verified file, mounted read only; the bytes are those of the official source (and of
  the naval mirror already recorded, SHA-256 `de0ea69d…`), checked in the preparation; the
  computation is untouched. Codex checks line by line that the patch changes nothing but
  the origin of the bytes. A generic local mirror goes to #59 as a later improvement.
- **2302.12465** documents PyTorch and DGL in its README, outside `requirements.txt`.
  Decision 4: the same mechanism.

## 1. The rule (W3.9a)

- **What a patch is.** A unified diff in the git form, the attachment's exact bytes,
  listed in `build.allowed_patches` with its reason; its SHA-256 is covered by the lock
  and checked (`check_patch`) on the bytes read, before anything is parsed.
- **The applier is Refute's own** (Python, on bytes, no `git apply`): Git would accept
  operations this rule forbids (binary patches, type changes, hunks at an offset) and
  writes through the attribute filters and the configuration of the host. The applier
  reads a small closed grammar and refuses anything else:
  - per file, in this order: `diff --git a/<p> b/<p>` with the same `<p>` twice (the
    prefixes `a/` and `b/` are required); for a creation, `new file mode 100644`; at most
    one `index <hex>..<hex>` line, optionally followed by the mode `100644` or, for a
    modification of a file that is executable at the pinned commit, `100755`; then
    `--- a/<p>` and `+++ b/<p>` (a modification) or `--- /dev/null` and `+++ b/<p>`
    (a creation); no other header line;
  - `<p>`: printable ASCII without spaces, quotes or backslashes, relative, with no `..`,
    no `.` and no empty component, not under `.git` or `.refute`; paths are compared by
    their components, here and in the protection of the data paths;
  - hunks `@@ -a,b +c,d @@`, optionally followed by a space and any text (the function
    context Git writes), which is an annotation only and never read as code; `a,b` are in
    the original file and `c,d` in the result, the single-line forms of the unified format
    are accepted, and a creation is `@@ -0,0 +1,N @@`; hunks in increasing,
    non-overlapping order, each with exactly the counted context, removed and added lines;
    positions are compared from zero: the original position is `a` when `b` is 0 and
    `a - 1` otherwise, the result position is `c` when `d` is 0 and `c - 1` otherwise, and
    the result position equals the original one plus the lines the earlier hunks added
    minus those they removed (this covers insertions and deletions with no context, and
    creations);
  - `\ No newline at end of file` only right after a content line that is the last line
    of its side (original or result), once per side, with nothing after it on that side;
  - each file appears once per patch, and in one patch only (two changes to one file are
    one patch).
- **Exact positions.** A hunk applies only at its stated line, with every context and
  removed line equal byte for byte (a carriage return is a byte like any other; nothing is
  normalized): no fuzz, and the context is never searched at another position. A context
  that matches only elsewhere is a refusal.
- **Text only.** A modified or created file, before and after, is valid UTF-8 with no NUL
  byte. Its line endings are kept as they are.
- **Files.** A modification needs a regular file of the clone at `<p>`; a creation needs
  `<p>` absent. The repository root and every ancestor of `<p>` are real folders (a
  missing ancestor of a creation is created as a real folder); the final component is a
  regular file (a modification) or absent (a creation); a symbolic link anywhere, a
  special file, a dangling link or a name that collides with another one by case is a
  refusal.
- **Where it writes.** The patched tree is a private folder of the engine on the VM: no
  container sees it and nothing else writes in it while it is prepared, and its ancestors
  are the engine's. Each folder is opened without following links and every read and
  write is made relative to the open folder (`dir_fd`, `O_NOFOLLOW`); a result is written
  to a new temporary file created exclusively in that folder, then renamed over the target
  in the same folder. A modified file keeps its mode; a created file is `0644`. Before the
  tree is used, no temporary file is left and its manifest is the expected one (section
  3). The applier runs on Linux (the VM); on a platform without `dir_fd` it refuses to
  write (the tests of the parser run everywhere; those of the writing run on Linux).
- **Data paths.** A patch may not touch a data path of the claim, a path under it, or a
  folder above it: the claim's datasets and `data_layout`, whether the dataset is present,
  verified or not.
- **Limits.** A patch of at most 1 MiB, 50 files and 500 hunks; all the patches of a
  claim together at most 4 MiB, 100 files and 1,000 hunks; a file of at most 16 MiB,
  checked on its size before it is read, before and after the patch.
- **All or nothing.** Every patch is parsed and checked in full, in the order of
  `build.allowed_patches`, against a separate copy of the clone; only a tree in which every
  patch applied is used. Any refusal stops the paper as a Refute error before the build
  (the claim was written and tested against the pinned commit). No container ever gets a
  partly patched tree; a second preparation starts again from the clone.

## 2. The order of the preparation

1. The clone at the pinned commit, checked as today (`repository.py`), and, before any
   patch, its content tree (without `.git`) equal to the tree of the commit
   (`git ls-tree -r` of the commit: the same paths, types, modes and blobs, no extra
   file); the `repository_file` datasets read and verified from it.
2. The patched tree: a separate copy of the clone, the patches applied (section 1). The
   clone stays as the evidence of the commit.
3. The ladder's inputs (`requirements.txt`, the environment file, the Dockerfile) found in
   the **patched** tree, so a patch to the requirements changes what the ladder builds.
4. The copies of the patched tree for the builds and the runs (the readers get no
   repository).
5. The data paths prepared and the verified data mounted in the runs and readers, as today.

## 3. What is recorded, and what it shows

- **Manifests.** A manifest of content (path, type, mode, size, SHA-256; a link as a
  link with its target, never followed; no `.git`) of the clone, anchored on the commit
  (section 2, step 1), and of the patched tree. Their difference must be exactly the
  files the patches modified or created, with the bytes the patches give, and the folders
  those creations need; any other difference stops the paper.
- **Each copy is checked** against the patched manifest before its container starts, by
  its role: a build or run copy equals the patched tree except the data targets, which
  are declared separately (removed for a `repository_file`, prepared as mount points); a
  reader's folder holds only Refute's script. The manifest of the patched tree keeps the
  original modes; a copy's modes are checked against the deterministic projection the
  preparation applies (today: every copied file gains `o+rw`, every copied folder
  `o+rwx`; the run's root and every folder above a data target are `01777`, including the
  folders created for the mount points), never against the original modes.
- **In the dossier:** the patches in order (bytes and SHA-256, linked to the locked
  attachments), the two manifests, and for each file a patch touched its SHA-256 before
  (absent for a creation) and after.
- **The verification** of the dossier rebuilds the patched tree from the clone at the
  pinned commit and the patches, with the same refusals and without running any code of
  the paper, and requires the same sets and values: an extra file, a missing file, another
  order or an edited manifest fails it.
- **What it shows:** the code tree each build and run container got at its start is the
  pinned commit plus exactly the listed patches, with the verified data mounted at the
  declared targets. **What it does not show:** that nothing changed during a
  run, since a run may write in its own folder (as today); and whether a patch is minimal
  and leaves the computation untouched, which is the claim's reason, reviewed by Codex and
  approved by the maintainer before the lock.

## 4. Out of this addendum

The coverage hook (W3.12c, route (b)) was designed to be installed by an allowed patch,
but its installation contract is not closed: the hook module's bytes, the place of the
wrapper, the mapping of the cited call site (lines of the pinned commit) onto the patched
tree, and the `/work` paths of a container against the host's folder. Until that contract
is written and accepted, production refuses before the preparation any claim file in
which a `hook` route appears, in any target, for the method or the reference, as the only
route or as one of several: such a claim is not supported by this version of production,
a limitation of Refute, never a failure of the artifact. The contract goes to #59. No
claim of the main sample uses the hook route.

## 5. Synthetic cases

**Must pass:** one changed line; a hunk header with Git's function context after `@@`;
several hunks in one file where earlier ones insert lines (`c` follows the shift); an
insertion with no context (`@@ -3,0 +4 @@`) and a deletion with no context
(`@@ -5 +4,0 @@`); a
created file (`@@ -0,0 +1,N @@`), also in a new folder; a modified executable file
(`index … 100755`), whose mode is kept; two patches on two files, in order; a file
with CRLF endings changed with CRLF context; a file with no final newline; the build sees a
requirement the patch added (the ladder reads the patched tree); `repository_file` data
still read from the clone; the runs see the patched bytes; the manifests and the dossier
record the change, and the verification rebuilds the tree.

**Must fail** (a Refute error before the build, or refused at validation):
- not listed; listed with other bytes; empty; over the limits of one patch or of the
  claim; a file over 16 MiB before or after;
- a clone with an extra file that is not in the commit's tree;
- a `hook` route in a claim file (method, reference, sole or alternative route): refused
  before the preparation as unsupported, not as a failure of the artifact;
- a header line out of the stated order, two `index` lines, `100755` for a file that is
  not executable at the commit or for a creation, a path with a `.` component;
- a `\ No newline at end of file` that is not after the last line of its side, twice, or
  followed by a line on that side;
- a hunk whose `c` does not follow the shift of the earlier hunks;
- a header outside the grammar: two different paths in `diff --git`, a rename, a copy, a
  deletion, a mode change, a binary hunk, a symbolic link, a quoted or escaped name, an
  unknown header line, two blocks for one file in one patch, one file in two patches;
- hunks out of order or overlapping, counts that do not match, a line that is neither
  context, removed nor added;
- a context that does not match at its stated line, including one that matches at another
  line; a creation of an existing file; a modification of a missing file;
- a path with `..`, absolute, under `.git` or `.refute`, through a symbolic link, under a
  symbolic link root, a dangling link, a special file, a case collision; a data path, a
  path under one, a folder above one;
- a NUL byte or invalid UTF-8 before or after;
- the second patch of two refused: no container starts, and the patched copy is not used;
- in the dossier: an extra file, a missing file, another order, an edited manifest.

## 6. Regression

A claim with `build.allowed_patches: []` runs exactly as today: the patched tree equals
the clone, and the dossier records an empty list and the clone's manifest.
