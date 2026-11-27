"""The check of the meter's demonstration (v0.5.13 charter, section 8): it reads the journal only.

    unit demo-check:  {python} -I -B docs/validation/v0.5.13/tools/demo_check.py [journal]

It passes (exit 0) when the last settled attempt of each demonstration shows:
- ``demo cpu-child``: status ok and CPU of at least 6 s (the child's 3 s counted with the parent's);
- ``demo create-delete``: status ok, written bytes of at least 64 MiB, and nothing left behind
  (``o_end`` no larger than ``o_start`` plus 1 MiB);
- ``demo retain-write`` then ``demo retain-check``: the check's ``o_start`` carries at least 32 MiB
  more than the write's ``o_start`` (the retained file, counted by the next unit);
- ``demo-net``: status ok and measured inbound bytes above zero, with a measured basis.
The result is printed and written to ``demo-check.json`` in the run's out folder.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
MIB = 1 << 20


def main() -> int:
    journal = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "docs/validation/v0.5.13/log.jsonl"
    rows = [json.loads(x) for x in journal.read_text(encoding="utf-8").splitlines() if x.strip()]
    befores = {e["attempt_id"]: e for e in rows if e["event"] == "before"}
    pairs = {}
    for e in rows:
        if e["event"] == "after" and e["attempt_id"] in befores:
            b = befores[e["attempt_id"]]
            mode = " ".join(x for x in b["argv"][4:] if not x.startswith("-")) or b["unit"]
            key = b["unit"] if b["unit"] == "demo-net" else f"demo {mode}"
            pairs[key] = (b, e)
    res: dict = {}

    def get(k):
        return pairs.get(k, (None, None))

    b, a = get("demo cpu-child")
    res["cpu_child"] = bool(a and a["status"] == "ok" and a["cpu_s"] >= 6.0)
    b, a = get("demo create-delete")
    res["create_delete"] = bool(
        a
        and a["status"] == "ok"
        and a["write_bytes"] >= 64 * MIB
        and a["o_end"] <= b["o_start"] + MIB
    )
    bw, aw = get("demo retain-write")
    bc, ac = get("demo retain-check")
    res["retained_across_units"] = bool(
        aw and ac and ac["status"] == "ok" and bc["o_start"] - bw["o_start"] >= 32 * MIB
    )
    b, a = get("demo-net")
    declared = "the spec's declared conservative estimate"
    res["transfer_bytes"] = bool(
        a and a["status"] == "ok" and a["download_bytes"] > 0 and a["download_basis"] != declared
    )
    res["passed"] = all(res.values())
    out = Path(os.environ.get("REFUTE_RUN_OUT", ROOT / ".cache" / "v0513"))
    text = json.dumps(res, indent=1) + "\n"
    (out / "demo-check.json").write_text(text, encoding="utf-8", newline="\n")
    print(json.dumps(res))
    return 0 if res["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
