# WP3 addendum: the provenance of a paper's dossier, and the publication rule of its logs

Addendum to [wp3-acceptance.md](wp3-acceptance.md) (the dossier of a paper run), committed
before its tests and code (plan section 11). It closes two items of issue #59 that block the
first lock: "Provenance in the dossier's contract" (the end-of-round review of 2026-10-18)
and "Log publication rule (blocks any publication)" (recorded on 2026-10-18). Ordered by the
maintainer on 2026-10-18 (order of work, item 3). Reviewed by Codex before the code (round
1: the reads of container readers and dataset counts, the binding of the profile records,
the publication outcomes, the order of finalization, the sources kept, the names of the
times; round 2: the bytes kept at the read and addressed by SHA-256, an execution id from
the host, passed checks and clock bounds, the transport of large files, the review of the
whole dossier, the environments without a lock, the diff's bytes; round 3, on the code: the
log's newlines as before, the exact checks and no duplicate key, the profile records and
the claim kept as files, the logs read bound to their copies, a refused record and the
image ID kept, one lock for the store and the entry).

## 0. Why

The dossier of a paper run (`dossier.json`, format `refute-ml-dossier-1`) records the
verdicts, the checks, the extracted tokens and the accounting. It does not record the
Refute commit the engine ran, the systemd unit, the network profiles in force, the file
each value or count was read from, or the image and environment the ladder built.
`calibration/v0.3/dev/2304.14390/RESULT.md` marks these as the operator's account. A sealed
dossier must carry them, so its verification can check them.

The dossier copies the run logs whole, and a log can print what the paper's code prints,
samples of the data included. The rule for publishing them is fixed before the seal, never
after a result is known.

## 1. Provenance (format `refute-ml-dossier-2`)

`dossier.json` gains a `provenance` object; the format becomes `refute-ml-dossier-2` (the
dev dossier of 2304.14390 keeps format 1 and its bytes). Every field is written by the
engine on the VM, not by the operator:

- **`refute`**: the commit of the Refute checkout that holds the imported package
  (`git rev-parse HEAD`), whether its tracked files are unchanged
  (`git status --porcelain --untracked-files=no` empty) and, when they are not, the changed
  paths, the SHA-256 of `git diff HEAD --binary` and the diff's bytes themselves
  (`refute.diff` in the dossier), read when the engine starts, so the code that ran can be
  rebuilt. A changed checkout is recorded, not refused (the lock's code hash is checked by
  the lock).
  No git or no checkout: `null` with the reason.
- **`unit`**: the systemd unit the engine runs in, read from `/proc/self/cgroup` (the last
  path component ending in `.service`), and its `INVOCATION_ID`; outside a unit, `null`.
- **`times`**, each named by the event it marks: `engine_started_utc` (the entry point,
  before the clone and the fetches), `run_started_utc` (the harness built, before the
  setup), `runs_finished_utc` (the paper's outcome returned) and `dossier_written_utc`.
  The unit's own start and stop are not read (systemd keeps them); the engine's first and
  last events are the times it can vouch for.
- **`profiles`**: the VM port's network profile at the build and at the runs, as declared by
  the host. The host's switch scripts (versioned in `scripts/vm/`) read the endpoint's
  status, check it, and write a record `refute-vm-profile-1` on the VM:
  `{format, execution_id, paper, claim_sha256, phase, profile, read_utc, checks,
  script_sha256}`, where `execution_id` is 32 lowercase hex digits the host's launcher
  generates for this launch, before the build's record is written, and also gives the
  engine (`--execution-id`); `phase` is `build` or `run`; `profile` is `build` or `pull`;
  `checks` is exactly `{adapter_on_configured_switch, entries_of_the_profile}` (the adapter
  on the configured switch; the profile's port entries, with no proxy entry for `pull`),
  each `true`; and `script_sha256` is
  the SHA-256 of the script that wrote it. The build record is given with
  `--profile-status <file>` and read at the start; the run record is the content of the
  run-phase flag, read when the flag appears (the host writes it atomically). A run-phase
  flag or a build record needs `--execution-id`. The engine refuses the record unless:
  ASCII bytes, no key twice at any level, every string ASCII; exactly these fields, each with
  its type; the `execution_id` the engine was given;
  `paper` is this run's paper id; `claim_sha256` is the SHA-256 of this run's claim file's
  bytes; the phase and profile are `build`/`build` at the start, `run`/`pull` at the runs;
  every check is `true`; `read_utc` is a UTC time no later than the record's consumption,
  and the run one no earlier than the end of the setup, each with an allowance of 300
  seconds for the difference between the host's and the VM's clocks. A refused build record
  stops the engine before anything runs; a refused run record (an empty flag included)
  stops the paper as a Refute error before its first base run. The bytes the engine
  consumed are kept, before the check, as the file `profiles/<phase>.json` of the dossier,
  with their SHA-256 (a refused run record too, with the reason of the refusal), never read
  again later. Limits, stated in the dossier: the records are the operator's declaration, written
  by the host's scripts from the endpoint's status, not signed by the endpoint; each says
  what the profile was when it was read, not that it stayed in force for the whole interval.
  The records hold no host value (no VM name, path, switch or address).
- **`reads`**: every file a value, a coverage count or a count of a container reader was
  read from in a run's folder, recorded for the whole paper run (not per read session):
  the container, the path relative to the run's folder as resolved, the SHA-256 and the size
  of the bytes read. The single reader of a run's outputs (`extract.read_output_bytes`)
  records at the read, before any parsing, so bytes read stay recorded when the parsing or
  the value then fails; a failed read is not recorded. A container reader's answer
  (`out/counts.json`, `readers.read_answer`) is recorded the same way. At the read, the
  bytes are also kept in an engine store of the run folder, named by their SHA-256. Entries
  are kept once per container, path and SHA-256; one path read with two different SHA-256 is
  recorded twice, marked `divergent`, and both versions are kept.
- **`logs_read`**: every log a value or a count was read from (the `from: log` metric, a
  `printed_count` on the log): the log's SHA-256 and size at the read, its container, and
  its binding to the `logs` manifest entry of the same path, which must have the same
  SHA-256 and size; a read with no entry, or whose bytes differ from the copy, is recorded as
  unbound with the reason. The text the selectors get is the one `Path.read_text` gave
  before (newlines translated), so no extraction changes.
- **`claim_input`**: the claim file as the engine received it, byte for byte
  (`claim_input.json`), with its SHA-256, the one the profile records name; it is distinct
  from `claim_file.json`, the canonical form, and from its hash.
- **`datasets`**: each dataset counted at the preparation (`readers.split_counts` on Refute's
  fetched or verified copy): its name, the SHA-256 and size of the copy the counts were read
  from (the claim's declared identity, already checked by the fetch), and the counts.
- **`environment`**: the rung that built the image (the ladder's `built_with`) and the ID of
  the image it committed (`docker image inspect`, read after a setup that completed, before
  any check that can stop the paper, so a stop keeps it). For a
  rung that resolves a lock (`requirements_compiled`, `requirements_compiled_next_python`):
  that rung's `requirements.lock` and `pyvenv.cfg`, copied into the dossier from that rung's
  folder (not from the first folder a glob finds), with their SHA-256. For
  `own_environment` (micromamba), which writes neither: both `null` with the reason. With no
  rung built: `rung` and `image_id` `null` with the reason; a local image of an earlier run
  is never attributed to this one. `complete` is false, with the reason, when a rung that
  resolves a lock left no lock or no `pyvenv.cfg`: an incomplete provenance, never shown as
  a documented environment.
- **`logs`**: a manifest of every log file copied into the dossier: its path in the dossier,
  its SHA-256 and size as written by the run and, for a log stored compressed (section 2),
  the stored file's name and SHA-256. The engine's console (`engine.log`, the unit's
  standard output, outside the run folder) is not part of the dossier; what it reports is
  in `dossier.json`.
- **`sources`**: the bytes of every file in `reads`, copied from the engine's store into the
  dossier as `sources/<sha256>` (one file per distinct content, so two versions of one path
  never collide) and checked on the bytes stored in the dossier; each `reads` entry names its
  `source`. The verification can then redo each extraction from the bytes. A read whose
  bytes were not kept (no store open) names no source, with the reason, and its verification
  is then declared partial. (A file larger than the extraction limit is never read, so never
  kept.)

**The order of finalization.** (1) The paper's outcome is final; (2) the logs, the sources,
the lock and `pyvenv.cfg` are copied (compressed where section 2 says), and their raw and
stored SHA-256 computed and checked; (3) `dossier.json` is written with the manifests; (4)
`MANIFEST.sha256` is written over every file of the folder (`core.dossier.write_manifest`),
`dossier.json` included; (5) only then can the authorized seal be made (`core.seal`, which
requires an intact manifest). The internal manifests never list `dossier.json`; the external
one does.

## 2. The publication rule of the logs (fixed before the seal)

- **The sealed record is the raw record.** The dossier folder is written once by the engine
  and sealed as written. Nothing is removed, reworded or reformatted afterwards, and the
  folder is excluded from linters and hooks, like `calibration/*/audit/`.
- **No content filter.** No log is filtered for content, before or after the seal: what a
  paper's code printed is part of the evidence. The engine gives no credential to a
  container: a run gets `BASE_ENV` and the setup's extra variables (recorded in the
  dossier) only, no network;
  a build gets the allowlist proxy's address (already public in `scripts/vm/launch-paper.sh`).
  The VM's account is the service account `refute`. That no credential is given does not
  establish that everything printed may be redistributed: that is the next point.
- **Two outcomes, fixed now.** Before the first publication of a dossier, a review recorded
  with it states, for each file of the dossier (the logs, the `sources`, which can hold
  whole predictions or labels, and the attachments), whether it holds data of a dataset (and
  which), and the redistribution status of that dataset, as a sourced record (CLAUDE.md,
  issue #34) or as `pending`. On that record, the maintainer chooses one of two outcomes for the dossier:
  **(A) full publication**: the public dossier is the sealed record, byte for byte; or
  **(B) the raw record kept, not published**: the sealed record is archived (its SHA-256 in
  the seal) and a public derivative is published as a new record that names the sealed
  record's SHA-256, the rule by which it was derived (covering the logs, the `sources` and
  the attachments) and the parts whose verification is no longer public; it is never
  presented as the original. A pending redistribution question
  stays declared as pending; no license is presumed. Neither outcome changes the sealed
  record.
- **Size.** A log larger than 50,000,000 bytes is stored compressed (gzip, level 9, no file
  name, modification time 0) under its name plus `.gz`, with the raw log's SHA-256 and size
  in the manifest; a log of 50,000,000 bytes or less is stored as written. Compression is
  lossless, so this is no redaction; the verification decompresses and checks the raw
  SHA-256.
- **Transport, apart from the compression.** The 50,000,000 bytes decide when a log is
  compressed, not where a file is published. GitHub warns above 50 MiB and blocks a file
  larger than 100 MiB pushed to a repository, and asks for releases for large files
  (https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github,
  read on 2026-10-18). Before a publication, the stored size of every file of the sealed
  record is measured: files of at most 100 MiB go into the repository; a larger one (a
  compressed log that stays large, for example) goes as a release asset, or, above that
  channel's limit, in parts from which the exact sealed bytes are rebuilt and checked
  against their SHA-256. No transport truncates a log or changes a sealed record.

## 3. Cases

**Must pass:** a dossier with every provenance field; a metric file's read recorded with its
container, resolved path, SHA-256 and size, once even when several readers share it; a read
recorded when the parsing of its bytes then fails; a container reader's `counts.json`
recorded; a log read recorded and bound to the manifest; a dataset's counts referenced by
the SHA-256 of the copy; a log of 50,000,000 bytes stored as written and one of 50,000,001
stored compressed, whose decompressed bytes have the manifest's raw SHA-256; the sources
copied and equal to the reads, checked on the bytes in the dossier; two versions of one
path both kept, under their own SHA-256; `MANIFEST.sha256` intact over the folder; a run
record `{phase: run, profile: pull}` of this execution, paper and claim, every check
`true`, lets the runs start; a build record `{phase: build, profile: build}` likewise lets
the engine start; the lock and `pyvenv.cfg` copied from the rung that built the image; an
`own_environment` build and a run with no rung built recorded with `null` and their reasons;
a changed checkout recorded with its paths, the diff's SHA-256 and `refute.diff`.

**Must fail:** a run record with profile `build`, an empty or malformed flag, a record of
another execution (an older record of the same paper and claim included), of another
paper or another claim, with a check that is not `true`, an extra or missing field, a time
more than 300 seconds before the end of the setup or after its consumption (a Refute error
before the first base run); a build record whose profile is not `build`, or of another
execution, paper or claim (refused at the start); a run-phase flag or a build record without
`--execution-id`; a failed read recorded as a read; one path read with two SHA-256 not
marked divergent; stored bytes whose SHA-256 differs from the read; a dossier file missing
or altered after the manifest (the manifest's verification reports it).

## 4. Regression

A paper run without `--profile-status` records `profiles.build` as `null` with the reason
"not given"; every other behavior of a run is unchanged.
