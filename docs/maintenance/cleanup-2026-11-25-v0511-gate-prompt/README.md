# The cleanup of the full gate prompt's source copy (2026-11-25)

This cleanup was asked by the maintainer's decision recorded on 2026-11-25 at 14:02 local (#218,
comment 7168908914, item 2). [cleanup.py](cleanup.py) runs once as the metered unit
`cleanup-gate-prompt` (launch_v9). It is committed before the run, together with the stored
prompt, and writes [record.json](record.json).

**What is deleted:** `.cache/v0511/gate-prompt-full/v0.5.11-gate-prompt-full.txt` (4,043 bytes),
and then its emptied folder.

**Why it is not archived:** the file is stored unchanged in git as
[docs/gates/v0.5.11-gate-prompt-full.txt](../../gates/v0.5.11-gate-prompt-full.txt). It is
already integrated.

**The checks before the deletion:**
- The source's SHA-256 is the maintainer's value,
  `25f0f6a302deac2bcbd824f3f3af153bb6182dca93e896f344c6ac99fee5a5cc`.
- The blob stored at that path in `HEAD` has the same SHA-256.
- The path lies inside that folder, with no link or junction on it.

Nothing outside `.cache` is deleted.
