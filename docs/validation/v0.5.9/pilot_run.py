"""v0.5.9 pilot driver (the maintainer's decision of 2026-11-24, received at 05:07 local, #218,
comment 7125778250, item 2).

**Exploratory.** The first batch of the approved run, restricted to three TOIs: TOI-734.01 and
TOI-5218.01 (v0.5.8's numerical ERRORs) and TOI-2357.01 (a class change). It imports the runner
``prototype_run.py`` of ``331ca03`` unchanged and calls its own steps (``recover``, ``sweep``,
``ready_units``, ``run_batch``) on those three TOIs only, exactly as its ``run`` step does on all
24: the same lock, the same pinned fingerprints, the same caps, allowances and journal. Units it
records are never run again; ``prototype_run.py run`` then continues with the other 21.

It writes its own process identity to ``.cache/v059/pilot/driver.json`` before any dispatch, so
that ``pilot_observe.py`` can measure the controller's CPU independently. It never marks the run
complete; a STOP is recorded in the ledger exactly as ``run`` records it.

Usage (from the project root, pinned): ``pilot_run.py``.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import prototype_run as pr  # noqa: E402 - the approved runner, imported, never edited

PILOT_TOIS = ("2357.01", "734.01", "5218.01")
PILOT_DIR = pr.WORK / "pilot"
DRIVER = PILOT_DIR / "driver.json"


def pilot_targets(all_targets: list[dict]) -> list[dict]:
    """The three pilot TOIs, in the set's order; anything else is refused."""
    out = [t for t in all_targets if str(t["toi"]) in PILOT_TOIS]
    if sorted(str(t["toi"]) for t in out) != sorted(PILOT_TOIS):
        raise SystemExit("the pilot TOIs are not all in the set")
    return out


def driver_identity() -> dict:
    pid = os.getpid()
    return {"pid": pid, "created": pr._creation_time(pid), "utc": pr.sr.utc()}


def pilot() -> None:
    all_targets = pr.targets()
    if len(all_targets) != len(pr.set_keys()):
        raise SystemExit("the set and the draws disagree")
    chosen = pilot_targets(all_targets)
    with pr.OsLock():
        ledger = pr.sr._ledger()
        if ledger.get("state") in ("complete", "abandoned", "stopped"):
            raise SystemExit(f"refused: the run is {ledger.get('state')}")
        if "pinned_fingerprints" not in ledger:  # pinned before the first dispatch
            ledger["pinned_fingerprints"] = pr.fingerprints()
            ledger["pinned_utc"] = pr.sr.utc()
            pr.sr._save_ledger(ledger)
        pr.check_pinned(ledger)
        pr.write_json(DRIVER, driver_identity())
        recovered = pr.recover()
        if recovered:
            print("recovered attempts:", recovered, flush=True)
        if pr.sr.MARKER.exists():
            pr.sr.MARKER.unlink()
        pr.sweep(chosen)
        while True:
            todo = pr.ready_units(chosen)
            if not todo:
                break
            stop = pr.run_batch(todo, "pilot")
            if stop:
                pr.sr._terminal("stopped", stop)
                print("STOP:", stop, flush=True)
                raise SystemExit(2)
        pr.sweep(chosen)
        done = {t["toi"]: pr.target_done(t) for t in chosen}
        print("pilot units recorded", json.dumps(done), json.dumps(pr.charged()), flush=True)


def main(argv: list[str]) -> None:
    if argv:
        raise SystemExit("usage: pilot_run.py")
    pr.point_runner()
    pr.no_link_roots()  # before any directory is created
    pr.sr.isolate_caches()
    pilot()


if __name__ == "__main__":
    main(sys.argv[1:])
