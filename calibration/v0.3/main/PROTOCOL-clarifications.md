# Clarifications of the main protocol

`PROTOCOL.md` is one of the files that `select_main.py` checks byte for byte against the
protocol commit b01bc78 before every batch and before the claim draw ("Files covered").
Its text is therefore never edited after that commit. Clarifications decided by the
maintainer after the protocol commit are recorded here, dated, and also in
`selection_log.md`. They do not change the frame, the round, the walk order or the
closed list of reasons; they fix how two reasons of the triage are read.

## C1 and C2: decided on 2026-10-18, after candidates were seen

**When and why.** Both were decided by the maintainer on 2026-10-18 (about 00:20 Brasília
time), **after** the agent had seen and triaged walk positions 1 to 75, and specifically
after the candidates 2305.19518 (position 1) and 2407.17459 (position 37) raised the
questions. They are applied in the same way to **every** candidate of the main walk,
including those already triaged before the decision; `selection_log.md` records, for each
candidate triaged before 2026-10-18, whether its decision changed.

**C1 (reading question R1): the level at which four data and access reasons apply.**
`data_requires_registration_or_terms`, `data_not_public`, `data_license_incompatible` and
`needs_paid_api_or_credentials` apply at the level of the **main results tables** (the
universe of claims of plan 5.2). A candidate is rejected for one of these reasons only if
**no** candidate cell of those tables can be produced without the restricted data or the
paid API. Otherwise it is accepted, and the cells that depend on the restricted data or
the paid API leave the inventory with that reason. An optional step that uses a paid API
does not count when the results of the main tables do not depend on it.

C1 names these four reasons. The thresholds `dataset_over_budget` (declared datasets
above 5 GB in total) and `pretrained_download_over_budget` (declared model weights above
2 GB in total) are not among them and keep the text of the protocol.

**C2 (reading question R2): data redistributed in a repository without a stated
license.** For a dataset redistributed inside the repository with no license of its own,
the license that counts is the license of the dataset's **original source**. The agent
looks for the original source and records its URL, the date it was read and a short
literal excerpt (a `sources/` record). Original source with a compatible license: the
dataset is accepted, with its source recorded. Original source with no known license, or
with an incompatible one: `data_license_incompatible` (read at the level fixed by C1).

**The pilot.** In the pilot (`calibration/v0.3/pilot/pilot_triage.md`, candidate #16,
`data_requires_registration`) the reading used was the whole paper. The pilot is closed and
none of its papers enters the main sample (filter 7); its decisions are not revisited.
