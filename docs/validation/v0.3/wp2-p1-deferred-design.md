# Deferred design: positive attribution of a missing documented script (P1)

Status: **deferred, not in v0.3.** Nothing here is implemented or in force. This document
records a design so that it can be picked up later; it is not an acceptance criterion.

## Decision (the maintainer, 2026-10-16)

- The positive attribution path described below is **not added in v0.3**. The reason:
  its complexity, and the risk of a false `NOT_REPRODUCIBLE`, are larger than its gain in
  v0.3.
- **What stays in force.** This does **not** remove the paths to `NOT_REPRODUCIBLE` already approved:
  - a declared artifact proven absent by HTTP 404 or 410 in all of the N attempts (`proven_absence`, `src/refute/core/paper.py`);
  - a build ladder whose three rungs ran to their end and failed with an error of the procedure itself (`src/refute/packs/ml/ladder.py`).
- Failures of `run_completed` and `metric_extracted` stay `INCONCLUSIVE`, as implemented in #107.
- The dossier keeps recording the facts it observes (exit codes, logs, the tree of the pinned commit), without attributing a cause.

## Starting point (the maintainer's decision earlier on 2026-10-16)

- Only P1 was considered.
- The proof of absence would come from the tree (`git ls-tree`), not from the exit code: Python exits with 2 when the script file does not exist.
- A file that the README or the repository says to generate is excluded, and so is any case in which a documented preparation step failed.
- The transcription of `argv` stays approved and identical to the README.
- P2 to P6 are out of v0.3; see the reasons at the end.

## The design (version 5, after four rounds of Codex review)

Cause `artifact_documented_script_absent`, for the gate `run_completed` of the **base**
runs only: the metric, the attacks and the build are not reached. It would apply only when
**every** condition holds; missing any one, the failure stays `INCONCLUSIVE`.

1. **The procedure is transcribed in full and approved.**
   - The documented procedure is the README of the pinned commit, at the exact paths listed in the claim, plus the code section of the paper, quoted with its location.
   - The transcription approved before the lock holds **all** of its steps, in order: installation, download, extraction, generation, build and the run command.
   - At the approval, the maintainer confirms explicitly that no step was left out. Without that recorded confirmation, P1 does not apply.
   - The run's `argv` is identical to the documented command.
2. **Form of the command.**
   - `argv[0]` is `python` or `python3`, and `argv[1]` is a relative path ending in `.py`, with no `..` and no leading slash. `-m`, `-c` and other interpreters are not covered.
   - The working directory is the documented one (the repository root, unless a documented and transcribed `cd` says otherwise), and it is the one actually used, recorded in the dossier.
   - The script path is `workdir/argv[1]`, normalized and relative to the root.
3. **Absence proven by the complete inventory of the tree.**
   - There is **one canonical inventory**: the bytes of `git ls-tree -r -t -z --full-tree <commit>`, with modes, types, objects and directory entries, NUL-delimited. Its SHA-256 is computed over those bytes.
   - Every other check (names, modes of the ancestors) is derived from it by literal comparison.
   - Any read error excludes P1: an invalid commit, an unavailable object, an exit code other than 0.
   - **No entry of any kind** exists at the exact path: no file, no directory (`040000`), no link, no submodule. A directory `train.py/` holding `__main__.py` can be run by `python train.py` (https://docs.python.org/3/using/cmdline.html#interface-options, accessed 2026-10-16).
   - The rule would only convert a FAIL of `run_completed`; a PASS never changes.
4. **No diverted ancestor.**
   - No ancestor of the path is, in the tree, a symbolic link (`120000`) or a submodule (`160000`).
   - There is no submodule anywhere in the tree, since its content cannot be checked through the inventory.
5. **No ambiguous candidate.**
   - Every path of the inventory decodes as strict UTF-8; a name that does not decode excludes P1.
   - The script path, compared with `casefold`, matches no path of the inventory.
   - The script's base name, compared with `casefold`, matches the base name of no path of the inventory, in any folder: for `train.py`, the presence of `src/Train.py` excludes P1.
6. **Not a file to be generated.** P1 does not apply when any of the following holds.
   - **(a) A preparation step can write into the tree.** P1 applies only when **every** transcribed preparation step is of one of two kinds:
     - **An installation of wheels only, into an environment outside the tree:**
       - a `pip install` whose requirements (with every `-r` file read from the pinned commit) are all distribution names with a version or a range;
       - no `-e`, `.`, local path, `file:`, VCS URL or archive URL;
       - no `--target`/`-t`, `--prefix`, `--root`, `--src` or `--user`;
       - run by Refute with an isolated configuration: `PIP_CONFIG_FILE` set to the null device, and no `PIP_*` variable taken from the README;
       - into an environment whose folder is outside the tree;
       - with a recorded `pip install --report` showing that **every** installed item came from a `.whl` file.

       This excludes:
       - any source distribution, because its build hooks run arbitrary code;
       - any destination that reaches the tree, such as `--target .` or `PIP_TARGET` (https://pip.pypa.io/en/stable/cli/pip_install/#cmdoption-t);
       - the build of a local project, which runs in the project folder and can leave artifacts there (https://pip.pypa.io/en/stable/topics/local-project-installs/#build-artifacts). Both pages were accessed on 2026-10-16.

       Conda is out of P1, because a conda package can carry post-link scripts.
     - **A download with an explicit destination**, which is not the script path nor one of its ancestors. An extraction must declare its destination folder, which must not be an ancestor of the script either.

     Any other step excludes P1, **even if it does not name the script**: code of the repository (a script, `make`, `setup.py`, `pip install .`, `bash prepare.sh`), a generation, a build of the tree itself, or an uncertain destination.
   - **(b) A `.gitignore` covers the path.**
     - Some `.gitignore` **of the pinned commit** has a **positive** rule that matches the path or one of its ancestors. Machine-wide excludes and `.git/info/exclude` are not read.
     - Each positive rule is evaluated alone, with git's semantics, in the folder of its file. A negation (`!`) does not cancel it: the rule is conservative.
   - **(c) The name is quoted outside the README.**
     - The script's base name appears in a blob of the pinned commit other than the transcribed READMEs.
     - The search is on **bytes**: in every blob, binaries included, ASCII-case-insensitive, with the base name encoded in UTF-8, UTF-16LE and UTF-16BE.
     - The occurrences are recorded.
     - An unreadable blob excludes P1, and so does a compressed blob (zip, including `.whl` and `.jar`; gzip; bzip2; xz; zstd; 7z), recognized by its leading bytes.
     - **Declared limit:** the absence of an occurrence does not prove that no instruction generates the script. That guarantee comes from (a); this search is an extra, conservative layer.
7. **Preparation complete, and a build ladder that does not touch the tree.**
   - Every transcribed preparation step ran to its end with exit code 0, and `environment_build` passed.
   - The ladder rung that built the environment follows the rules of 6(a):
     - rung 1 (`own_environment`) excludes P1, since the repository's Dockerfile runs arbitrary code and `environment.yml` is conda;
     - rungs 2 and 3 (`requirements_compiled`) apply only with no editable, local, VCS or archive requirement, wheels only, and an environment outside the tree.
   - A step that failed, was interrupted, did not run or was skipped excludes P1.
8. **Complete attempts.**
   - The base runs were attempted by the claim's procedure, in the number fixed before the lock.
   - None was stopped by a guard, the budget or an error of Refute.
9. **The interpreter did not open the script, in every attempt.** These are necessary conditions, not the proof:
   - the stderr of each attempt holds Python's message `can't open file '<path>': [Errno 2]` for the script's path;
   - right after each attempt, the **absence is confirmed** on the file system where the run took place (inspected in the container), without following links, for the exact path and for each ancestor that should contain it. Any other answer excludes P1: a permission, read or inspection error, an entry of any kind, or an ancestor that is a link.

   The exit code (2) is only recorded.

**Coverage.** The script never started, so no example was examined. The rule would follow
the model of `proven_absence` (`src/refute/core/paper.py`):
- a procedural coverage rule specific to P1;
- decided by its attribution (`NOT_REPRODUCIBLE`) **before** the rule that turns a zero-coverage FAIL into `INCONCLUSIVE`;
- only with every condition above, complete attempts, and an inventory that was read (a recorded entry count above 0).

This would extend the coverage rule and would need the maintainer's explicit approval.

**Evidence in the dossier:**
- the commit, and the inventory with its SHA-256 and entry count;
- the derived checks of the path and its ancestors;
- the (empty) lists of homonyms and other spellings;
- the `.gitignore` rules evaluated;
- the (empty) list of occurrences of the base name;
- the preparation steps with their destinations and exit codes, and the `pip install --report`;
- the ladder rung;
- the working directory;
- for each attempt: its exit code, its full stderr and the absence check made after it.

**Verdict, if it applied:** `NOT_REPRODUCIBLE`, under plan section 8.2: "the documented command fails in the built environment".

## The open point at the time of deferral (Claude and Codex disagreed; a point of verdict)

**The problem.** A start-up customization can write the message `can't open file …` to
stderr itself, and end the interpreter before the script is opened, with the path absent.
Such a customization is a `.pth` file with an executable line or a `sitecustomize.py`,
installed by a wheel, and both run before the program
(https://docs.python.org/3.12/library/site.html, accessed 2026-10-16). In that case the
tree, the message and the later absence all agree, yet the attempt never reached the
script. Condition 9 narrows this window but does not close it.

- **Codex's position:** without verifiable evidence that the start-up is trustworthy and that the message came from the interpreter, such cases stay `INCONCLUSIVE`.
- **Claude's proposal, condition 10 (not reviewed by Codex: it was written after the fifth and last round):**
  - in the effective environment, before the attempts, list every `sitecustomize.py` and `usercustomize.py` on `sys.path`, and every executable `.pth` line (one that starts with `import`);
  - accept only what is on a closed list of SHA-256 hashes fixed before the lock (for example the `distutils-precedence.pth` of setuptools, in the locked versions);
  - anything else excludes P1.
- **The three exits considered:**
  1. Codex's: no P1 without evidence such as condition 10.
  2. Claude's: conditions 9 and 10, with 10 reviewed by Codex.
  3. Condition 9 only, accepting the trust limit. Not recommended.

The maintainer deferred the whole path instead (decision above).

## Tests that a later implementation would need (synthetic, offline)

**Must give `NOT_REPRODUCIBLE`:**
- the README says `python train.py`, the commit has no `train.py`, there is no preparation, and no `.gitignore` or other file names it;
- the same with a successful, irrelevant preparation: wheels only (`numpy==1.26.4`, `torch>=2.1`), an environment outside the tree, a `--report` showing wheels only, and a download to `data/`;
- the positive case queried from a subfolder: with `--full-tree` the inventory is the same and the result is unchanged;
- a valid P1 with zero scientific coverage, through the procedural rule.

**Preservation:** a `run_completed` PASS stays PASS, and the claim aggregates as usual.

**Must stay `INCONCLUSIVE`:**
- **Preparation:**
  - a preparation step left out of the transcription;
  - a step that did not run, was interrupted or failed;
  - an extraction without a destination;
  - a destination that is an ancestor of the script;
  - `-e .`, `.`, a local path, a VCS URL;
  - `--target .` or `PIP_TARGET`;
  - an sdist in the `--report`;
  - an environment inside the tree;
  - conda;
  - ladder rung 1, or rung 2 with an sdist;
  - `make` or `bash prepare.sh`.
- **`.gitignore`:** the script covered at the root, in a nested `.gitignore`, or with a later negation.
- **Quotations:** the name in a `Makefile`, in a binary, in UTF-16, in another case, or in a test or changelog; a zip blob anywhere.
- **Tree:**
  - a homonym in another folder, `Train.py`, `src/Train.py`;
  - an undecodable name;
  - a directory `train.py/` with `__main__.py`;
  - a start-up customization that creates the script;
  - stderr without the message;
  - an ancestor that is a link or a submodule, or a submodule anywhere;
  - a different working directory.
- **Git:** an invalid commit; an unavailable object.
- **Command:** `python -m package.train`, or another interpreter.
- **Attempts:** incomplete attempts; a guard stop; an exhausted budget; an error of Refute.
- **Scope:**
  - the same facts in `metric_extracted` or in an attack;
  - exit code 2 from `argparse` with the file present;
  - an inventory with 0 entries;
  - an ordinary FAIL below the negative minimum.

## P2 to P6 (out of v0.3, with the reason)

- **P2 (`SyntaxError` on every rung):** code written only for Python 2 **can** raise `SyntaxError` on every rung, which are all Python 3, without being a defect of the artifact. Not every Python 2/3 incompatibility is syntactic, and the rule could not tell that case from a real error.
- **P3 (`ImportError` of an internal module):** it depends on the working directory and `PYTHONPATH`, which are on Refute's side.
- **P4 (an absolute path of the author's machine):** an option documented elsewhere can change the path, so the proof does not close.
- **P5 (an output file never written):** the name can be built at run time.
- **P6 (a missing dependency):** no new cause; it follows the attribution `environment_build` already has under plan section 8.2.

## Review record

Codex reviewed the preview read-only in five rounds on 2026-10-16:
- **Round 1:** generated files that are not named; `ls-tree` depending on the current folder (measured: `git -C src ls-tree 02027a9 -- src/refute/core/paper.py` prints nothing with exit 0, while `--full-tree` finds the file); ancestors; coverage; vague `.gitignore` and search rules; tests; P2 and P6.
- **Round 2:** `pip install -r` can build a local project in the tree; bytes and Unicode mixed in names; UTF-16; two undefined tests.
- **Round 3:** a directory `train.py/__main__.py`; `--target` and `PIP_TARGET`; sdist hooks.
- **Round 4:** start-up customizations; the PASS test listed under `INCONCLUSIVE`; two inventories instead of one.
- **Round 5:** the origin of the stderr message, and the definition of the absence check after an attempt. **Closed without consensus** on the first of these (above).
