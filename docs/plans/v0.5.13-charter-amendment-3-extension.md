# v0.5.13 charter: amendment 3 (proposed, 2026-11-27): the extension of the time box

> **PROPOSED, not approved.** Written on 2026-11-27 under the maintainer's decision K3 (#218,
> comment 7223240289), which chose the extension over a close at the deadline.
> - **How it is approved:** the maintainer approves it in #218 by its SHA-256, before the current
>   deadline, 2026-12-04T00:13:24Z.
> - **What it amends:** the charter approved at `04402e7a4cae71fd7bab8a7157dd38a36a4d2e60`
>   (SHA-256 `2832dc4870b0fb094e724a3ff6d6fb6c5710f2da5827791b8fa102c06230c813`), together with
>   amendment 1 (`69de5f9f5df0ea621dc6bc7d036f3f1b02448199`, SHA-256
>   `cd2a689231688b5e22c3e6c9602a706fbbca37b7de16ea087417227d5cdbaefc`), approved in #218, comment
>   7207651312, item D2. Neither file is edited, and amendment 2 is not changed by this one.
>
> **Labels:** `exploratory`, `method_status: not_validated`.

## 1. The extension

**The rule it uses.** The charter's section 9 (Codex r1, item 7, as written):

> Execution stops seven calendar days after approval unless the maintainer records one extension
> before expiry, with its reason and new deadline.

ROADMAP.md, "How phases work", item 3, says the same: an extension is recorded before expiry,
with its reason and a new deadline, one at a time. The charter allows one extension, and this
amendment uses it.

- **The current deadline:** 2026-12-04T00:13:24Z, seven calendar days after the opening at
  2026-11-27T00:13:24Z.
- **The new deadline:** **2026-12-18T00:13:24Z.**
- **The reason:** by J2's estimate (section 3), the work left in Part A does not fit the time box,
  even with no failed check. On 2026-11-27 about 6.3 days remained, and the estimate is 9 to 15
  sessions, about 7.5 to 11.5 days.
- **A checkpoint on 2026-12-11:** a short progress report in #218, against J2's estimate. For each
  item it gives the estimate, what was used and what is left.

## 2. What does not change

- **Nothing else changes.** Part A's targets and exit criteria, its steps, its caps and its stops
  stay as the charter, amendment 1 and the adopted revision of amendment 2 set them.
- The rest of the time box text applies to the new deadline, unchanged:
  - at the stop, every criterion is marked met, failed or not run;
  - expiry closes and advances nothing;
  - the maintainer alone records closure under the advance rule.
- The extension relaxes no target and changes no verdict, lock or anchored byte.
- **The checkpoints of section 9 are not re-dated:** "step 0 and step 1 by day 2; step 2 by day 3;
  step 3 by day 5; step 4 and the seal by day 7", each counted from the approval. A missed
  checkpoint is still reported in #218 the same day.

## 3. The results known when this was written

**J2's estimate** ([`docs/validation/v0.5.13/j2/README.md`](../validation/v0.5.13/j2/README.md),
commit `2bc8fba26cf85ded49cf72370540c17d7c8e72e4`). It is an estimate from the measured pace, and
it assumes no failed check:

| Item | Sessions | Days |
| --- | --- | --- |
| #226 (step 1) | 3 to 4 | 2 to 3 |
| #227 (step 2) | 1 to 2 | 1 to 1.5 |
| #224 (step 3) | 3 to 5 | 2.5 to 4 |
| Step 4 (the reason map) | 1 to 2 | 1 to 1.5 |
| Step 5 (the seal) | 1 to 2 | 1 to 1.5 |
| **Total** | **9 to 15** | **about 7.5 to 11.5** |

#224 is the largest and least certain item. A failed check that needs a specification correction
with a fresh blind review could need more time than this extension gives.

**The state of #226 (step 1): not met.**
- **NR-A1** stopped: byte identity was not met at 1 and 4 threads
  (`docs/validation/v0.5.13/step1/comparison-nr-a1.json`). D1a recorded which fields differ.
- **Amendment 2:**
  - revision 4 was adopted (#218, comment 7222329150, item I1);
  - the second blind review returned revision 5 as `NOT_APPROVABLE`;
  - revision 6 is proposed and not adopted: commit `c6236e91a6bbb108b06e731c2d272ce6b9bd2a57`,
    SHA-256 `86a3853e3d052e5f65c2b3049e58f913abb105997109d362f07056801e235b7c`.
  - Under decision K4, nothing of amendment 2 has run: not the manifest, the freeze, the checks or
    NR-A2.
- **Made under revision 4** (decision I2, `docs/validation/v0.5.13/i2/README.md`):
  - the raw goldens, committed at `a90442645a8fa007d64ed7d2154f61e77caf7a05`;
  - the sidecar `docs/validation/v0.5.13/numerical-environment.md`;
  - the inventory of 2,746 comparison and selection sites, of which none is resolved as a manifest
    row.
- **The count of decision-layer predicates** (decision J1(b)): 173 for version 4, cumulative.

**The other steps.** Of the charter's steps, only step 0 is complete. Steps 2 to 5 (#227, #224,
the reason map and the seal) have not started. By J2's estimate, step 1 cannot meet its
checkpoint of day 2.

**The cost so far:** about 0.7 of Part A's 8 CPU-h. The time box, not the CPU cap, binds.
