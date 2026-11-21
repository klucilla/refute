"""v0.5.5: R2's own line of caps (#218; the maintainer's decisions of 2026-11-21, 13:30, at G1,
item 1). ``method_status: not_validated``.

**The caps:** Codex review tokens **1.0 M (STOP at 0.8 M)**; agent-days **5 (STOP at 4)**; **CPU 0**
for anything of the new battery version (only the test suite runs). v0.5.5's caps stay as they
are, and R2's work counts on both lines (the conservative side).

**The line** is written once into v0.5.5's ledger (``r2_line``), under the ledger's lock, before
any R2 work: its caps, its opening time and the decision. It touches no part and no charge.

**What counts:**
- tokens: the Codex conversations whose name starts with ``r2``, each counted by its last round's
  uncached input plus output, as every phase counts them (``lv.codex_tokens``). Since the
  maintainer's decisions of 2026-11-21 (15:20), item 4, their events live in
  ``.cache/v055/r2/codex/`` and **count only on R2's line**; v0.5.5's line is reported with and
  without them (``both_lines``);
- agent-days: Claude's session transcripts since the line opened, wall clock over 8-hour days
  (an upper bound), with the active time recorded (``.cache/v052/tools/agent_time.py``);
- CPU: none is allowed for the new version; a step that would need it is a STOP.

``check`` records each check in ``r2-caps.json`` and STOPs when a cap with the step's reservation
would reach 80 %; it also runs v0.5.5's own check (``lv.check_caps``).

Usage: ``r2_line.py open`` (once), ``r2_line.py check <step> <reserve days> <reserve tokens>``.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import ledger_v055 as lv  # noqa: E402

budgeted = lv.budgeted
KEY = "r2_line"
PREFIX = "r2"
CAPS = {"review_tokens": 1_000_000, "agent_days": 5.0, "cpu_hours_new_version": 0.0}
STOP_FRACTION = 0.80
DECISION = "the maintainer's decisions of 2026-11-21 (13:30) at G1, item 1 (#218)"
RECORD = HERE / "r2-caps.json"


def open_line() -> dict:
    """Write R2's line once into the ledger, under its lock; a repeated call checks that the line
    on file is the same and writes nothing."""
    lv.assert_bound()
    with lv.Exclusive("r2 line"):
        book = budgeted.load()
        line = book.get(KEY)
        if line is not None:
            if line.get("caps") != CAPS or line.get("stop_fraction") != STOP_FRACTION:
                raise SystemExit("R2's line on file differs from these caps: a STOP")
            return line
        line = {
            "caps": CAPS,
            "stop_fraction": STOP_FRACTION,
            "opened_utc": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()),
            "counts": "Codex conversations named r2*; agent-days since opened_utc; no CPU for "
            "the new version (the test suite only)",
            "decision": DECISION,
        }
        book[KEY] = line
        budgeted.save(book)
        if not RECORD.exists():
            RECORD.write_text(
                json.dumps({"line": line, "entries": []}, indent=1) + "\n", "utf-8", newline="\n"
            )
        return line


def _line() -> dict:
    line = budgeted.load().get(KEY)
    if line is None:
        raise SystemExit("R2's line is not open: no R2 work before it")
    return line


CODEX_EVENTS = lv.ROOT / ".cache/v055/r2/codex"  # R2's own folder (decisions of 15:20, item 4)


def tokens() -> dict:
    """R2's Codex conversations, from their own folder, counted as ``lv.codex_tokens`` counts
    (each conversation's last round: uncached input plus output). Since the maintainer's
    decisions of 2026-11-21 (15:20), item 4, they count **only** on R2's line: their events live
    apart from v0.5.5's folder, so ``lv.codex_tokens`` no longer sees them."""
    saved = lv.CODEX_EVENTS
    lv.CODEX_EVENTS = CODEX_EVENTS
    try:
        per = dict(lv.codex_tokens()["conversations"])
    finally:
        lv.CODEX_EVENTS = saved
    per = {c: n for c, n in per.items() if c.startswith(PREFIX)}
    return {"conversations": per, "r2": sum(per.values())}


def both_lines() -> dict:
    """v0.5.5's review tokens without R2 (its own folder) and with R2 (the two summed)."""
    v055 = lv.codex_tokens()["phase"]
    r2 = tokens()["r2"]
    return {"v055_without_r2": v055, "r2": r2, "v055_with_r2": v055 + r2}


def agent_days(since: str) -> tuple[float, float]:
    """(wall clock, active) agent-days since ``since`` (UTC), by the transcripts."""
    out = subprocess.run(
        [sys.executable, str(lv.AGENT_TIME), str(lv.TRANSCRIPTS), since],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    wall = float(out.split("wall ")[1].split(" h")[0]) / 8.0
    active = float(out.split("= ")[1].split(" agent-days")[0])
    return wall, active


def check(step: str, reserve_days: float, reserve_tokens: int) -> dict:
    """Both lines: v0.5.5's (``lv.check_caps``) and R2's, each with the step's reservation; R2's
    entry is recorded in ``r2-caps.json`` before the STOP rule is applied."""
    line = _line()
    lv.check_caps(f"r2: {step}", reserve_days, reserve_tokens)
    tok = tokens()
    wall, active = agent_days(line["opened_utc"])
    entry = {
        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "step": step,
        "review_tokens": tok,
        "v055_lines": both_lines(),
        "agent_days_wall": round(wall, 3),
        "agent_days_active": round(active, 3),
        "cpu_hours_new_version": 0.0,
        "reserved": {"agent_days": reserve_days, "review_tokens": reserve_tokens},
    }
    with lv.Exclusive("r2 check", lv.CAPS_LOCK):
        doc = json.loads(RECORD.read_text("utf-8"))
        doc["entries"].append(entry)
        RECORD.write_text(json.dumps(doc, indent=1) + "\n", "utf-8", newline="\n")
    caps = line["caps"]
    if tok["r2"] + reserve_tokens >= STOP_FRACTION * caps["review_tokens"]:
        raise SystemExit("R2's review tokens would reach 80 % of its cap: a STOP")
    if wall + reserve_days >= STOP_FRACTION * caps["agent_days"]:
        raise SystemExit("R2's agent-days (wall-clock bound) would reach 80 % of its cap: a STOP")
    return entry


if __name__ == "__main__":
    if budgeted.LEDGER != lv.HERE / "ledger.json":
        raise SystemExit("budgeted is not pointed at v0.5.5's ledger: refused")
    if sys.argv[1] == "open":
        print(json.dumps(open_line(), indent=1))
    elif sys.argv[1] == "check":
        print(json.dumps(check(sys.argv[2], float(sys.argv[3]), int(sys.argv[4])), indent=1))
