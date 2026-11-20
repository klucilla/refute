"""v0.5.5: read v0.5.4's records through v0.5.4's own readers, with nothing written (#218).

Some of v0.5.4's readers (for example ``i4_bound.i1_verified``, called by ``i4_bound.fingerprint``)
assert that ``budgeted`` is bound to v0.5.4's ledger exactly as ``ledger_i`` binds it, the save
function included. ``v054_read()`` binds it that way for the length of a read, with the save
function replaced, in both places the assertion looks, by one that **refuses every write**, and
restores everything on exit (also on an error). Serial use within one process only.
"""

from __future__ import annotations

import contextlib


def _refuse(_ledger: dict) -> None:
    raise RuntimeError("a write to v0.5.4's ledger during a read-only binding: refused")


@contextlib.contextmanager
def v054_read():
    import budgeted
    import ledger_i

    saved = (budgeted.LEDGER, budgeted.LINES, budgeted.HARD_MAXIMUM, budgeted.SPENT_BEFORE,
             budgeted.save, ledger_i._atomic_save)  # fmt: skip
    ledger_i._atomic_save = _refuse
    budgeted.LEDGER = ledger_i.HERE / "ledger.json"
    budgeted.LINES = {ledger_i.SECTION: ledger_i.CAP_HOURS - ledger_i.CHARGES_ROOM}
    budgeted.HARD_MAXIMUM, budgeted.SPENT_BEFORE = ledger_i.CAP_HOURS, 0.0
    budgeted.save = _refuse
    try:
        ledger_i.assert_bound()
        yield
    finally:
        (budgeted.LEDGER, budgeted.LINES, budgeted.HARD_MAXIMUM, budgeted.SPENT_BEFORE,
         budgeted.save, ledger_i._atomic_save) = saved  # fmt: skip
