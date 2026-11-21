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
line. The new allocation and the step's record (``transfers``, with the reserve before and
after) are written together. A repeated call writes nothing and checks the whole record, the
target's allocation, the reserve against the record and any later transfer that took from it,
and both lines; any divergence is a STOP (``_verify_on_file``; Codex, t2s round 1).
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


def _expected(name: str) -> dict:
    """The fields a step's record must hold (besides its time and the reserve before and
    after)."""
    step = STEPS[name]
    return {
        "to": step["part"],
        "from": {"r1_reserve": round(step["after"] - step["before"], 6)},
        "allocation_hours": {"before": step["before"], "after": step["after"]},
        "reason": step["reason"],
        "decision": step["decision"],
        "script_sha256": own_sha256(),
    }


def _lines_hold(rows: dict) -> bool:
    total = sum(r["allocation_hours"] for r in rows.values())
    return (
        total + max(lv._charges(), lv.CHARGES_ROOM) <= lv.LINE_HOURS + 1e-9
        and total <= budgeted.LINES[lv.SECTION] + 1e-9
    )


def _verify_on_file(book: dict, rows: dict, name: str) -> dict:
    """A repeated call (Codex, t2s round 1): "exactly one record with the target, the source,
    the amount, the allocations before and after, the decision and the SHA matching the step;
    the reserve before and after recorded; the reserve checked against that record and any later
    demonstrable transfers, besides both budget lines. Any divergence or reconciliation that
    cannot be shown causes a STOP, with no write." The later demonstrable transfers are the
    ``transfers`` records after this one that take from the reserve."""
    transfers = book.get("transfers", [])
    idx = [i for i, t in enumerate(transfers) if t.get("step") == name]
    stop = f"the step {name} on file does not match the ledger: a STOP"
    if len(idx) != 1:
        raise SystemExit(stop)
    record = transfers[idx[0]]
    want = _expected(name)
    reserve = record.get("reserve_hours") or {}
    if (
        any(record.get(k) != v for k, v in want.items())
        or set(record) != {"step", "utc", "reserve_hours", *want}
        or round(reserve.get("before", 0.0) - want["from"]["r1_reserve"], 6) != reserve.get("after")
    ):
        raise SystemExit(stop)
    later = sum(t.get("from", {}).get("r1_reserve", 0.0) for t in transfers[idx[0] + 1 :])
    if (
        rows[want["to"]]["allocation_hours"] != want["allocation_hours"]["after"]
        or abs(rows["r1_reserve"]["allocation_hours"] - (reserve["after"] - later)) > 1e-9
        or not _lines_hold(rows)
    ):
        raise SystemExit(stop)
    return record


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
            return _verify_on_file(book, rows, name)  # no write
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
        reserve_before = rows["r1_reserve"]["allocation_hours"]
        rows[part]["allocation_hours"] = after  # the part never ran: nothing to archive
        rows["r1_reserve"]["allocation_hours"] = reserve
        record = {
            "step": name,
            "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            **_expected(name),
            "reserve_hours": {"before": reserve_before, "after": reserve},
        }
        book.setdefault("transfers", []).append(record)
        budgeted.save(book)  # one atomic write
        return record


if __name__ == "__main__":
    if budgeted.LEDGER != lv.HERE / "ledger.json":
        raise SystemExit("budgeted is not pointed at v0.5.5's ledger: refused")
    import json

    print(json.dumps(apply(sys.argv[1]), indent=1, sort_keys=True))
