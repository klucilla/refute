"""v0.5.4 step 4's second completion part, under a fixed cap (#217; the maintainer's decision of
2026-11-13, item 2: "complete os 14 shards restantes numa parte de complemento com o mesmo
código, as mesmas linhas e o mesmo fingerprint, com um teto fixo de 1,0 CPU-h (sem depender da
projeção de um checkpoint pequeno), revisão do Codex do diff e procedimento na #217 antes. [...]
Se parar de novo, deixe o passo 4 como está e registre."). ``method_status: not_validated``.

**The stop, as a fact.** ``h2_step4_rest`` (``step4_rest.py``) ran 1 of its 15 shards. Its
checkpoint, that one shard, projected 0.060 CPU-h, so its cap was 0.090. The driver's watchdog
ended the workers ("over the cap: the workers were ended") after 0.101 CPU-h. 63 of 77 shards are
done (62 in ``h2_step4``, 1 in ``h2_step4_rest``).

``run``:
1. **Checks.** Step 4's fingerprint and rows, exactly as ``step4_rest.py`` checks them.
   ``h2_step4`` must be reconciled and closed (by ``step4_rest.py``). ``h2_step4_rest`` must hold
   exactly the expected stop, in the ledger and in the driver's folder. No worker of it may be
   alive and no batch open. ``h2_step4_rest2`` must not exist.
2. **The stop as a fact.** ``h2_step4_rest``'s stop is reconciled with this decision's reason, and
   the part is closed as ``step4_rest.py`` closed ``h2_step4``. Nothing is deleted.
3. **The fixed cap** is the part's total charge, at most 1.0 CPU-h, the conservative reading
   (Codex, h2-step4rest2 round 1).
   - 1.0 CPU-h of ``h2_step4_rest``'s unspent allocation moves to ``h2_step4_rest2`` (an atomic
     transfer, after the closure).
   - The run uses **one worker**, so an interrupted batch's crash charge is one shard's limit:
     (1200 s + 20 s) / 3600 = 0.339 CPU-h. With step 4's 12 workers it would be 4.07, more than
     the cap.
   - The driver's cap is what is left after that reserve, over a margin of 1.2 (the 10 %
     overshoot plus the watchdog's polling latency, as ``b1_d2d4_rest.py``'s ``MARGIN``):
     (1.0 − 0.339) / 1.2 = 0.551 CPU-h. It is also bounded by ``ledger_i.hard_cap``.
   - That cap is set as the part's frozen projection before the run, so the driver runs no
     checkpoint. It is labelled in the ledger as a fixed cap, not a projection.
   - **The premise, stated** (Codex, h2-step4rest2 round 2): the total stays within 1.0 if the
     accounting after the watchdog's trigger stays within the room left. That room is 1.0 −
     0.551 × 1.10 − 0.339 = 0.055 CPU-h, 198 CPU-s. The watchdog polls every 0.5 s but has no proven
     reaction bound, so the margin is operational, not a proof.
   - **So the final charge is checked against 1.0** after the run and again before the summary. A
     charge above 1.0 is recorded in the part's row as ``fixed_cap_passed``, and the summary is
     refused: step 4 is left as it is.
   - Step 4's 62 measured shards took 1.75 to 411 CPU-s each (4,684 in all, about 76 per
     shard). So the 14 rows are expected near 0.3 CPU-h.
4. **The run.** The rows done in neither part run through ``budgeted_v3`` with step 4's own
   ``shard``, fingerprint, rows and per-shard limit (1200 s); only the number of workers differs,
   and no result depends on it. An interrupted batch's crash charge counts, as always.

``summarize`` runs step 4's own summary, unchanged, on all 77 shards. The shards come from the
three parts, each row exactly once, every sidecar verified. Its consumption is the three parts'.

A stop of this part leaves step 4 as it is: the stop is recorded and nothing more runs (the
decision's last sentence).
- A stop the driver returns is recorded by ``budgeted``.
- An exception in the run is recorded in the part's row, before it propagates: its unresolved stop,
  and its charge from the driver's own count (``spent_seconds``, which charges an open batch by the
  crash rule).
- A process killed from outside is recorded by the driver's crash rule only when the part is next
  opened. None is planned, so such a stop, with the charge the crash rule gives, is recorded by hand
  in step 4's record.

Usage (from the project root): ``run`` through ``launch_detached.py``, then ``summarize``.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import step4_rest as r1  # noqa: E402,I001  (step4_b0_errors and its imports, ledger_i last)
import budgeted  # noqa: E402
import budgeted_v3  # noqa: E402
import ledger_i  # noqa: E402

s4 = r1.s4
MAIN, REST = r1.MAIN, r1.REST
REST2 = "h2_step4_rest2"
OUT_REST2 = s4.ROOT / ".cache/v054/step4-rest2"
EXPECTED_STOP = "over the cap: the workers were ended"
FIXED_CAP = 1.0  # CPU-h, the maintainer's: the part's total charge
WORKERS = 1  # so that one interrupted batch's crash charge fits inside the fixed cap
MARGIN = 1.2  # the driver's 10 % overshoot plus the watchdog's polling latency
CRASH = WORKERS * (s4.MAX_SHARD_SECONDS + 20.0) / 3600.0
DRIVER_CAP = (FIXED_CAP - CRASH) / MARGIN
SOURCE = REST  # its unspent allocation, as step4_rest.py took h2_step4's
REASON = ("the maintainer's decision of 2026-11-13, item 2 (#217): h2_step4_rest stopped by the "
          "driver's mechanics (its one-shard checkpoint projected 0.060 CPU-h; the watchdog ended "
          "the workers at 0.101); the stop is a fact, the part is closed, and the 14 rows not done "
          "run as h2_step4_rest2 with the same code, rows and fingerprint, under a fixed cap of "
          "1.0 CPU-h")  # fmt: skip


def _transfer_fixed() -> None:
    """One atomic save: the debit, the credit, the fixed cap as the frozen projection, and the
    history (never through ``declare``)."""
    book = budgeted.load()
    parts = book["sections"][ledger_i.SECTION]["parts"]
    src = parts[SOURCE]
    if src["allocation_hours"] - FIXED_CAP < src.get("spent_hours", 0.0) - 1e-9:
        raise SystemExit(f"{SOURCE} cannot give {FIXED_CAP} CPU-h: refused")
    src["allocation_hours"] -= FIXED_CAP
    parts[REST2] = {
        "allocation_hours": FIXED_CAP,
        "projection_hours": DRIVER_CAP,
        "projection_basis": "a fixed cap set by the maintainer (2026-11-13, item 2): 1.0 CPU-h "
        "less one worker's crash reserve, over a margin of 1.2; no checkpoint ran",
    }
    if sum(r["allocation_hours"] for r in parts.values()) > budgeted.LINES[ledger_i.SECTION] + 1e-9:
        raise SystemExit("the allocations would pass the line: refused")
    book.setdefault("transfers", []).append(
        {"utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "from": SOURCE, "to": REST2,
         "hours": FIXED_CAP, "reason": REASON}
    )  # fmt: skip
    budgeted.save(book)


def _record_exception(exc: BaseException, todo: list, fp: str) -> None:
    """The stop and the charge, from the driver's own count; nothing runs again."""
    try:
        hours = r1._handle(OUT_REST2, todo, fp).spent_seconds() / 3600.0
    except Exception:  # the stop is still recorded; the charge is then completed by hand
        hours = None
    book = budgeted.load()
    row = book["sections"][ledger_i.SECTION]["parts"].get(REST2)
    if row is None:
        return
    if "unresolved_stop" not in row:
        row["unresolved_stop"] = f"an exception in the run: {type(exc).__name__}: {exc}"[:500]
    if hours is not None:
        row["spent_hours"] = max(row.get("spent_hours", 0.0), hours)
    else:
        row["charge_unknown"] = "the driver's count could not be read: complete it by hand"
    budgeted.save(book)


def _check_fixed_cap() -> None:
    used = ledger_i.part_consumption(REST2)
    if used > FIXED_CAP + 1e-9:
        book = budgeted.load()
        row = book["sections"][ledger_i.SECTION]["parts"][REST2]
        row["fixed_cap_passed"] = round(used, 6)
        budgeted.save(book)
        raise SystemExit(f"{REST2} charged {used:.4f} CPU-h, above the fixed {FIXED_CAP}: step 4 "
                         "is left as it is (the decision)")  # fmt: skip


def _done_in(part_out: Path, rows: list, fp: str) -> set:
    return set(r1._handle(part_out, rows, fp)._done())


def run() -> None:
    ledger_i.assert_bound()
    rows, fp = r1._schedule()
    r1._check_fp(rows, fp)
    book = ledger_i._rows()
    if REST2 in book:
        raise SystemExit(f"{REST2} exists already: refused")
    if "unresolved_stop" in book[MAIN] or "projection_at_stop" not in budgeted.load()["sections"][
        ledger_i.SECTION]["parts"][MAIN]:  # fmt: skip
        raise SystemExit(f"{MAIN}: not reconciled and closed: refused")
    rest = r1._handle(r1.OUT_REST, rows, fp)
    pending = book[REST].get("unresolved_stop")
    if pending != EXPECTED_STOP or rest.unresolved_stop() != EXPECTED_STOP:
        raise SystemExit(f"{REST}: not the expected stop ({pending}): refused")
    if rest.workers_still_running():
        raise SystemExit(f"{REST}: workers are still alive: refused")
    for path in sorted(rest.charge_dir.glob("b*.json")):
        if not json.loads(path.read_text("utf-8"))["closed"]:
            raise SystemExit(f"{REST}: an open batch ({path.name}): refused")
    done_main = _done_in(s4.OUT, rows, fp)
    done_rest = _done_in(r1.OUT_REST, rows, fp)
    if done_main & done_rest:
        raise SystemExit("a row is done in two parts: refused")
    todo = [(sid, a) for sid, a in rows if sid not in done_main | done_rest]
    if len(todo) != 14:
        raise SystemExit(f"{len(todo)} rows are left, not the decision's 14: refused")
    ledger_i.check_caps("step4 rest2 run", reserve_days=0.1, reserve_tokens=0, in_h1=False,
                        reserve_bytes=len(todo) * 20_000 + 50_000_000)  # fmt: skip
    # ledger_i.hard_cap's phase term, read before the transition (Codex, round 2): a refusal
    # here leaves nothing created; the part's own term (1.5 x 1.0 over 1.1) is above it
    room = ledger_i.CAP_HOURS - ledger_i.spent() - WORKERS * s4.MAX_SHARD_SECONDS / 3600.0
    if room / ledger_i.OVERSHOOT < DRIVER_CAP:
        raise SystemExit(f"the phase's room ({room:.3f} CPU-h) cannot hold the fixed cap: refused")
    with ledger_i.Exclusive("step4 rest2 transition"):
        budgeted.reconcile(ledger_i.SECTION, REST, REASON)
        if rest.unresolved_stop() is not None:
            rest.reconcile(REASON)
        r1._close(REST)
        _transfer_fixed()
    ledger_i.refuse_new_identity(REST2, fp, todo)
    cap = min(DRIVER_CAP, ledger_i.hard_cap(REST2, WORKERS, s4.MAX_SHARD_SECONDS))
    if cap < DRIVER_CAP - 1e-9:
        raise SystemExit(f"the phase's room ({cap:.3f}) is below the fixed cap's: refused")
    print(f"{REST2}: {len(todo)} shards; driver cap {cap:.3f} CPU-h (fixed cap {FIXED_CAP}, "
          f"crash reserve {CRASH:.3f}); 1 worker; fp {fp}", flush=True)  # fmt: skip
    with ledger_i.Exclusive("step4 rest2 run"):
        try:
            state = budgeted_v3.execute(
                ledger_i.SECTION, REST2, OUT_REST2 / fp, s4.shard, todo, fp, WORKERS, pin=s4.PIN,
                max_shard_seconds=s4.MAX_SHARD_SECONDS, hard_cap_hours=cap,
                pause_at=s4.r1.PAUSE_AT, units=lambda arg: len(arg["items"]),
            )  # fmt: skip
        except BaseException as exc:  # recorded before it propagates (Codex, rounds 1 and 2)
            _record_exception(exc, todo, fp)
            raise
    print(state, flush=True)
    _check_fixed_cap()
    ledger_i.check_caps("step4 rest2 after the run", 0.0, 0, in_h1=False)
    if state != "complete":
        raise SystemExit(f"step 4 is left as it is (the decision): {state}")


def summarize() -> None:
    """Step 4's own summary, unchanged, on the 77 shards of the three parts."""
    ledger_i.assert_bound()
    rows, fp = r1._schedule()
    r1._check_fp(rows, fp)
    book = ledger_i._rows()
    ledger = budgeted.load()
    _check_fixed_cap()
    places = ((MAIN, s4.OUT), (REST, r1.OUT_REST), (REST2, OUT_REST2))
    for part, out in places:
        if part not in book or "unresolved_stop" in book[part]:
            raise SystemExit(f"{part}: missing or an unresolved stop: refused")
        if r1._handle(out, rows, fp).unresolved_stop() is not None:
            raise SystemExit(f"{part}: a driver stop: refused")
        if budgeted._open_gates(ledger, ledger_i.SECTION, part):
            raise SystemExit(f"{part}: a failed gate: refused")
    found: dict = {}
    for _, out in places:
        handle = r1._handle(out, rows, fp)
        for sid in handle._done():
            if sid in found:
                raise SystemExit(f"{sid}: done in two parts: refused")
            found[sid] = handle._paths(sid)[0].read_bytes()
    missing = [sid for sid, _ in rows if sid not in found]
    if missing:
        raise SystemExit(f"{len(missing)} shards are not done: refused")
    data = b"".join(found[sid] for sid, _ in rows)

    original = s4.budgeted.assembled

    def assembled(section, part, out, fn, rws, fpx, workers, **kwargs):
        if part == MAIN and section == ledger_i.SECTION:
            if (fpx, rws) != (fp, rows):
                raise SystemExit("an unexpected read of step 4: refused")
            return data
        return original(section, part, out, fn, rws, fpx, workers, **kwargs)  # B0's reader

    consumption = ledger_i.part_consumption

    def three(part):
        if part == MAIN:
            return consumption(MAIN) + consumption(REST) + consumption(REST2)
        return consumption(part)

    saved = (s4.budgeted.assembled, s4.ledger_i.part_consumption)
    s4.budgeted.assembled, s4.ledger_i.part_consumption = assembled, three
    try:
        s4.summarize()
    finally:
        s4.budgeted.assembled, s4.ledger_i.part_consumption = saved


if __name__ == "__main__":
    if budgeted.LEDGER != ledger_i.HERE / "ledger.json":
        raise SystemExit("budgeted is not pointed at v0.5.4's ledger: refused")
    {"run": run, "summarize": summarize}[sys.argv[1]]()
