# v0.5.13 charter: amendment 4 (proposed, 2026-11-27): the checkpoints of section 9, re-dated

> **PROPOSED, not approved.** Written on 2026-11-27 under the maintainer's decision L3 (#218,
> comment 7223634913).
> - **How it is approved:** the maintainer approves it in #218 by its SHA-256.
> - **What it amends:** the charter approved at `04402e7a4cae71fd7bab8a7157dd38a36a4d2e60`
>   (SHA-256 `2832dc4870b0fb094e724a3ff6d6fb6c5710f2da5827791b8fa102c06230c813`), with amendment 1
>   (`69de5f9f5df0ea621dc6bc7d036f3f1b02448199`, SHA-256
>   `cd2a689231688b5e22c3e6c9602a706fbbca37b7de16ea087417227d5cdbaefc`), amendment 2, revision 6
>   (`c6236e91a6bbb108b06e731c2d272ce6b9bd2a57`, SHA-256
>   `86a3853e3d052e5f65c2b3049e58f913abb105997109d362f07056801e235b7c`), and amendment 3
>   (`5d99b7b06bbf51d54d1929f91e199ec4e705e682`, SHA-256
>   `e6981c1645c2531729b166b6f334d1750ace0f3999c619a3640200a56428aac4`). None of them is edited.
>
> **Labels:** `exploratory`, `method_status: not_validated`.

## 1. The change: the checkpoints only

The charter's section 9 says:

> Checkpoints: step 0 and step 1 by day 2; step 2 by day 3; step 3 by day 5; step 4 and the seal by
> day 7. A missed checkpoint is reported in #218 the same day.

Amendment 3 moved the deadline to 2026-12-18T00:13:24Z and left these checkpoints unchanged. This
amendment replaces the first sentence with:

> Checkpoints: step 0 by day 2 (2026-11-29); step 1 by 2026-12-03; step 2 by 2026-12-05; step 3
> by 2026-12-11; step 4 and the seal by 2026-12-17. A checkpoint dated by its day is met by the
> end of that day, 23:59:59 UTC.

The second sentence stays: a missed checkpoint is reported in #218 the same day.

**Nothing else changes.** Part A's targets and exit criteria, steps, caps, stops, the deadline of
amendment 3 and its checkpoint report of 2026-12-11 stay as they are.

## 2. Why these dates

They are the maintainer's proposal in L3. They are checked against J2's estimate
([`docs/validation/v0.5.13/j2/README.md`](../validation/v0.5.13/j2/README.md), commit
`2bc8fba26cf85ded49cf72370540c17d7c8e72e4`), counted from 2026-11-27, with the days added up in
order. The estimate assumes no failed check.

| Checkpoint | J2: days for the item | J2: cumulative days | Cumulative end | Proposed date | Margin to the upper end |
| --- | --- | --- | --- | --- | --- |
| Step 1 (#226) | 2 to 3 | 2 to 3 | 2026-11-29 to 2026-11-30 | 2026-12-03 | 3 days |
| Step 2 (#227) | 1 to 1.5 | 3 to 4.5 | 2026-11-30 to 2026-12-01 | 2026-12-05 | 4 days |
| Step 3 (#224) | 2.5 to 4 | 5.5 to 8.5 | 2026-12-02 to 2026-12-05 | 2026-12-11 | 6 days |
| Step 4 (the reason map) | 1 to 1.5 | 6.5 to 10 | 2026-12-03 to 2026-12-07 | 2026-12-17 | 10 days |
| Step 5 (the seal) | 1 to 1.5 | 7.5 to 11.5 | 2026-12-04 to 2026-12-08 | 2026-12-17 | 9 days |

Each proposed date is at or after the upper end of the estimate, and the last one is before the
deadline of amendment 3. The estimate does not ask for a different date, so the proposal is kept
as it stands. The margins leave room for the maintainer's approvals and for one specification
correction, which the estimate does not include. Step 3 falls on the day of amendment 3's progress
report.

## 3. The results known when this was written

- **Step 0** is complete (2026-11-27), so its checkpoint of day 2 is met.
- **Step 1 (#226) is not met.**
  - NR-A1 stopped: byte identity was not met at 1 and 4 threads.
  - Amendment 2, revision 6, is adopted (#218, comment 7223634913, item L1).
  - Its margin manifest, the comparator, the schema and the span map are being prepared (item
    L4). No check of amendment 2 and no NR-A2 has run.
- **Amendment 3 is approved** (item L2): the deadline is 2026-12-18T00:13:24Z.
- **Steps 2 to 5 have not started.**
- **Until this amendment is approved,** a missed checkpoint of the charter's original schedule is
  reported in #218 in one line, the same day (item L3). No checkpoint had been missed when this
  was written: step 1's original checkpoint of day 2 falls on 2026-11-29.
- **CPU:** about 0.74 of Part A's 8 CPU-h.
