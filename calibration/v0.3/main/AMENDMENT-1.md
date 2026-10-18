# Amendment 1 to the main protocol: the walk goes on to 1,200 candidates

Decided by the maintainer on 2026-10-18 (message labelled about 09:30 Brasília time), after
the stop rule of `PROTOCOL.md` was reached: the walk read 300 candidates (batches 1 to 12,
committed 703dece to cdd3faa) with no approved acceptance and at most 4 acceptances possible
under the decisions then pending. The rejection profile of the first 300 is in
`selection_log.md`. This amendment is committed and pushed **before any position after 300
is read**. The selector computes the whole permutation in memory to slice each batch, as it
did for batches 1 to 12; no candidate after position 300 was read, queried or inspected
before this commit. That last point is the agent's statement: the selector cannot prove it.

`PROTOCOL.md` is not edited (`select_main.py` checked it byte for byte against the original
protocol commit for batches 1 to 12); this file amends it, and is itself one of the files
`select_main.py` checks for batches 13 onward.

## A. The same walk, with a new cap

1. **Same round, same order, same reading code.** The paper round stays **6561788**, the
   round of the original protocol commit `b01bc78ccc0dcad63f083fc3d527f9a1ff5f869d`, fixed
   in `select_main.py` (`PAPER_ROUND`, `ORIGINAL_PROTOCOL`); the script still derives the
   round from that commit's push run by the original rule and refuses to go on if it is not
   6561788. The frame, the filters, the seed, the shuffle and the reading of each candidate
   (arXiv metadata, GitHub metadata, README, root names, the mechanical rejections and the
   `no_license` signal) are unchanged.
2. **New cap: 1,200 candidates (48 batches).** `select_main.py` refuses a 49th batch.
3. **Protocol commit of batches 13 to 48.** The commit that adds this file (the last commit
   of its push) is given as `--protocol-commit` for batches 13 to 48; `select_main.py`
   refuses the original commit for those batches, and any commit other than the one commit
   of the history that adds this file. Each of those batches records both
   commits, the original publication proof and the amendment's own proof (its push run
   exists before the batch is read; in that proof the field `round_published_at` holds the
   time the batch was read, since the amendment fixes no new round, and the margin is 0).
4. Batch N still needs batch N - 1 committed; the walk goes on without waiting for the
   maintainer's approvals, which come in batches, as before. The reasons, their order, the
   triage and the clarifications C1 to C3 (`PROTOCOL-clarifications.md`) are unchanged.

## B. Main sample and development papers

5. **Main sample**: the first 5 accepted papers in walk order (unchanged).
6. **Development papers**: the 6th and 7th accepted papers, if they appear by the cap. If
   they do not, the development papers become the synthetic repositories of the WP4
   catalogue (`docs/validation/v0.3/wp4-acceptance.md`, W4.1 and section 2), with this risk
   recorded: an engine error on a main paper, which a development paper might have shown
   first, leaves that main paper's claims `INCONCLUSIVE`, with no replacement (plan 10.4,
   "never replaced"). A dated note in plan 4.5 records the rule.
7. **When to stop reading.** The agent stops starting new batches once the accepted papers
   (by its proposals) reach 7; if the maintainer's approvals later bring the count below 7,
   the walk resumes at the next batch. Batches read after the 7th acceptance cannot change
   the sample, which is fixed by walk order.

## C. If the cap is reached with fewer than 5 accepted

8. The walk stops at 1,200 (option E of the morning report of 2026-10-18). The agent brings the maintainer the rejection profile, for publication as a
   result (plan 4.4), in both readings, side by side: the literal reading of the
   thresholds and the per-cell reading of C1 to C3.

## Record

The selection log records, for each version of `PROTOCOL-clarifications.md`, its SHA-256.
The Codex review of this amendment (read only) precedes its push.
