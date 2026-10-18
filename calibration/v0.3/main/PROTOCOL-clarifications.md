# Clarifications of the main protocol

`PROTOCOL.md` is one of the files that `select_main.py` checks byte for byte against the
protocol commit b01bc78 before every batch and before the claim draw ("Files covered").
Its text is therefore never edited after that commit. Clarifications decided by the
maintainer after the protocol commit are recorded here, dated, and also in
`selection_log.md`, which records the SHA-256 of each version of this file. The
maintainer accepted on 2026-10-18 that this separate file carries the notes on the
protocol. They do not change the frame, the round, the walk order or the closed list of
reasons; they fix how reasons of the triage are read.

## C1 and C2: decided on 2026-10-18, after candidates were seen

**When and why.** Both were decided by the maintainer on 2026-10-18, in the message that
also approved the rerun of batch 4 (the message is labelled "about 00:20" Brasília time;
the agent received it before 2026-10-18T03:14:48Z, when it recorded that approval in issue
#156), **after** the agent had seen and triaged walk positions 1 to 75, and specifically
after the candidates 2305.19518 (position 1) and 2407.17459 (position 37) raised the
questions. They are applied in the same way to **every** candidate of the main walk,
including those already triaged before the decision; `selection_log.md` records, for each
candidate triaged before 2026-10-18, whether its decision changed.

**C1 (reading question R1): the level at which four data and access reasons apply.**
`data_requires_registration_or_terms`, `data_not_public`, `data_license_incompatible` and
`needs_paid_api_or_credentials` apply at the level of the **main results tables** (the
universe of claims of plan 5.2). A candidate is rejected for one of these reasons only if
**no** candidate cell of those tables can be produced without the restricted data or the
paid API. Otherwise these four reasons do not reject it (the other reasons of the closed
list still apply, and every decision still needs the maintainer's approval), and the
cells that depend on the restricted data or the paid API leave the inventory with that
reason. An optional step that uses a paid API
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

## C3: decided on 2026-10-18, after candidates were seen

**When and why.** Decided by the maintainer on 2026-10-18 (message labelled about 09:30
Brasília time), **after** the agent had triaged all 300 candidates of batches 1 to 12, and
specifically after candidates 2305.19518 (position 1), 2502.16782 (position 112) and
2407.11735 (position 230) raised the question. It applies in the same way to every
candidate of the main walk, including those already triaged.

**C3: the size thresholds take the reading of C1.** `dataset_over_budget` (declared
datasets above 5 GB in total) and `pretrained_download_over_budget` (declared model
weights above 2 GB in total) reject a candidate only if **no** candidate cell of the main
results tables can be produced within **all** the limits. The cells that depend on data or
weights above a limit leave the inventory with that reason. `requires_gpu` stays at the
level of the paper, by the definition (a)/(b) of the protocol.

The final report gives the rejection profile in both readings, side by side: the literal
reading of the thresholds (the whole paper) and the per-cell reading of C1 to C3.

## C4 to C9: decided on 2026-10-18, after candidates were seen

**When and why.** Decided by the maintainer on 2026-10-18 (message labelled about 09:50
Brasília time), **after** the agent had triaged positions 1 to 375 and drafted the
inventories of the accepted papers, and specifically after candidates 2305.19518 (1),
2502.16782 (112), 2407.11735 (230) and 2309.15704 (309) raised the questions. They apply
in the same way to every candidate and every cell of the main walk, including those
already triaged.

**C4: the closed list of reasons that exclude a cell from an inventory** (plan 5.2 asks
the protocol for it; `PROTOCOL.md` did not give it):

- `not_produced_by_repository`: the repository's instructions do not produce the number
  (a result copied from another paper, a baseline run with other code, or a variant the
  instructions do not cover);
- the four reasons of C1, read for the cell: `data_requires_registration_or_terms`,
  `data_not_public`, `data_license_incompatible`, `needs_paid_api_or_credentials`;
- the two size reasons of C3, read for the cell: `dataset_over_budget`,
  `pretrained_download_over_budget`;
- `depends_on_unlicensed_code`: producing the cell needs code with no licence (D-5);
- `timing_on_authors_hardware`: a wall-clock time measured on the authors' hardware or
  network.

There is **no** reason for an estimated cost: the budget decides during the run, and the
claim is then `INCONCLUSIVE` (C6).

**C5: data downloaded from its original source.** A dataset that the run downloads
directly from its original source is accepted when that provider publishes it for download
with terms of use that allow research use, even if the terms are only a request to cite.
The terms are recorded in a `sources/` record (URL, date, literal excerpt). Refute does not
redistribute the data: the dossier holds its hashes, not the data. If the original provider
states no terms at all, the cell is `data_license_incompatible`, as in C2.

**C6: a high estimated cost with no statement in the paper or the README.** The cells stay;
the budget decides during the run (plan 4.4: "looks hard" is not a reason; only a stated
cost excludes). An estimate is recorded as information only, never as a reason. A claim
that ends `INCONCLUSIVE` because the budget ran out records a limitation of Refute, never of
the paper.

**C7: 2502.16782 (CipherPrune).** Its cells of wall-clock time leave the inventory
(`timing_on_authors_hardware`); its communication cells (GB) stay. The weights each kept
cell needs are measured against C3 before the acceptance is confirmed.

**C8: comparisons.** A comparison candidate is only one the paper states in its text, always
as a direction (D-10), with the literal excerpt of the paper in the inventory.

**C9: 2309.15704 (MaxWEnt).** Its main-results table is Table 2 (UCI): the introduction
covers it ("several regression and classification datasets"); the abstract's OpenOOD
benchmark is reported only in a figure (Figure 8) and has no configuration in the
repository, so it leaves the inventory.

## The pilot

**The pilot.** In the pilot (`calibration/v0.3/pilot/pilot_triage.md`, candidate #16,
`data_requires_registration_or_terms`) the reading used was the whole paper. The pilot is closed and
none of its papers enters the main sample (filter 7); its decisions are not revisited.
