# D2-F not run: authorized funding insufficient; fixed-cap adapter pending

`method_status: not_validated`. The maintainer's decision of 2026-11-20 (21:00), item 2 (#218),
settled with Codex over three rounds
([`docs/plans/v0.5.5-consensus/`](../../plans/v0.5.5-consensus/), conversation `g1`). The text
below is Codex's text of round 2 (in Portuguese in the consensus record, unchanged there), in
English here.

D2-F remains unrun in this governance decision. The authorized transfer is limited to the 14.2
CPU-h of D1-P's part B (set B, refused by set A's futility rule). The estimated projection of 10.4
CPU-h for set A (200 planets × 0.052 CPU-h, an estimate without an auditable measurement) needs a
driver cap of at least 13.52 CPU-h by the 1.3 margin. Even with no reserve, 14.2/1.10 allows only
12.909091 CPU-h. With four workers, a shard limit of 1,200 seconds, the crash reserve and the
nominal poll margin, 16.228111 CPU-h would be needed (18.262278 with ten workers). A top-up from
the reserve is not authorized. The fixed-cap adapter also remains pending implementation and
review (`d2f_floor.py` still calls `budgeted_v3`).

The historical value 0.113865 (`d2f-decision-value.json`) is a conditional predictive estimate,
with no ceiling shown for generator version 2. The derived historical upper count is 14 of 178
(variant 4, generator version 1, with the documented Monte Carlo caveats); in the fixed scenario,
route allows up to 14 per set and up to 18 pooled, subject to the stricter own-unit thresholds.
**It was not shown that route is implausible under the rule (e)1.** This non-run is not an
experimental result nor a conclusion of infeasibility for D2.

**What would let D2-F run:** the maintainer's authorization of about 2.0 more CPU-h from the
reserve (four workers) or about 4.1 (ten workers) beyond the 14.2, and a fixed-cap adapter for
D2-F reviewed by Codex. D2-F's redesign (`docs/plans/v0.5.5-r1-designs-revision-1.md`, section 2)
is ready and unchanged.
