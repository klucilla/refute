"""v0.5.5, R1: a ledger step that raises a part's allocation from the reserve, before the part's
first start (#218; the maintainer's decisions of 2026-11-21, 10:00, at G1, item 1).
``method_status: not_validated``.

**The step ``t2ae2``:** T2a-E's stage 2 (part ``r1_t2ae_2``) from 3.1 to **3.55 CPU-h**, 0.45 from
the reserve. The released runner (``r1_fixed_cap.py``) refused stage 2 on 2026-11-21 because its
effective cap (2.1914) was under 1.3 times the measured projection (1.3 x 1.9872 = 2.5833); the
computed minimum allocation for 4 workers is 3.5311. The runner's bytes stay unchanged: it reads
the part's allocation from the ledger, and checks its margin again itself, under the lock,
against the effective cap.

**Guards, under the ledger's lock, one atomic write:** the part never ran nor started (its
identity, consumption, archived attempts and starts all absent; an earlier refused margin check
is allowed, since it recorded no start); its allocation is the declared 3.1; the reserve covers
the 0.45; the allocations with the charges' room stay inside the 64 CPU-h line and the budget
line. The new allocation and the step's record (``transfers``) are written together. A repeated
call with the step already on file changes nothing (and checks that the ledger still matches).
**After the step, ``lv.declare()``, its command line and the earlier scripts that call it are not
run**: they would restore the earlier table; a ledger found otherwise is reconciled by the
maintainer.

Usage: ``.venv/Scripts/python.exe -B docs/validation/v0.5.5/r1_allocation_step.py t2ae2``.
"""

from __future__ import annotations

import hashlib
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import ledger_v055 as lv  # noqa: E402

budgeted = lv.budgeted
STEPS = {
    "t2ae2": {
        "part": "r1_t2ae_2",
        "before": 3.1,
        "after": 3.55,
        "decision": "the maintainer's decisions of 2026-11-21 (10:00) at G1, item 1 (#218)",
        "reason": "the runner refused stage 2 by its margin: effective cap 2.1914 against 1.3 x "
        "1.9872 = 2.5833; the minimum allocation for 4 workers is 3.5311",
    },
}


def own_sha256() -> str:
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def _never_ran(book: dict, part: str) -> bool:
    row = budgeted._row(book, lv.SECTION, part)
    return (
        "identity" not in row
        and row.get("spent_hours", 0.0) == 0.0
        and not row.get("attempts")
        and not lv._starts(book, part)
    )


def apply(name: str) -> dict:
    """The step ``name`` under the ledger's lock, in one atomic write; returns its record."""
    step = STEPS[name]
    part, before, after = step["part"], step["before"], step["after"]
    delta = round(after - before, 6)
    lv.assert_bound()
    with lv.Exclusive(f"allocation step {name}"):
        book = budgeted.load()
        rows = book.get("sections", {}).get(lv.SECTION, {}).get("parts", {})
        if part not in rows or "r1_reserve" not in rows:
            raise SystemExit("v0.5.5's parts are not declared: refused")
        done = [t for t in book.get("transfers", []) if t.get("step") == name]
        if done:
            if len(done) != 1 or rows[part]["allocation_hours"] != after:
                raise SystemExit(f"the step {name} on file does not match the ledger: a STOP")
            return done[0]
        if not _never_ran(book, part):
            raise SystemExit(f"{part} ran or started: its allocation is not raised")
        if rows[part]["allocation_hours"] != before:
            raise SystemExit(f"{part}: not the declared allocation {before}: refused")
        reserve = round(rows["r1_reserve"]["allocation_hours"] - delta, 6)
        if reserve < 0:
            raise SystemExit("the reserve cannot fund the step: the maintainer's")
        merged = {p: r["allocation_hours"] for p, r in rows.items()}
        merged[part], merged["r1_reserve"] = after, reserve
        if sum(merged.values()) + max(lv._charges(), lv.CHARGES_ROOM) > lv.LINE_HOURS + 1e-9:
            raise SystemExit("the allocations and the charges' room pass the 64 CPU-h line")
        if sum(merged.values()) > budgeted.LINES[lv.SECTION] + 1e-9:
            raise SystemExit(f"{lv.SECTION}: the allocations pass the budget line")
        rows[part]["allocation_hours"] = after  # the part never ran: nothing to archive
        rows["r1_reserve"]["allocation_hours"] = reserve
        record = {
            "step": name,
            "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "to": part,
            "from": {"r1_reserve": delta},
            "allocation_hours": {"before": before, "after": after},
            "reason": step["reason"],
            "decision": step["decision"],
            "script_sha256": own_sha256(),
        }
        book.setdefault("transfers", []).append(record)
        budgeted.save(book)  # one atomic write
        return record


if __name__ == "__main__":
    if budgeted.LEDGER != lv.HERE / "ledger.json":
        raise SystemExit("budgeted is not pointed at v0.5.5's ledger: refused")
    import json

    print(json.dumps(apply(sys.argv[1]), indent=1, sort_keys=True))
