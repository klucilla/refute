"""v0.5.8, correction 2 (exploratory): recount the direction of the refitted SNRs that moved by
more than 10 %, from the committed records only.

It reuses the committed report script's own rules (``stability_report.py``: ``load``, ``v056``,
``snr_of``, ``snr_differs``), so "moved" means exactly door 3's "differs". Nothing is downloaded,
the output goes to stdout as JSON, and with ``--out <path>`` also to that file.

Usage (from the project root):
``.venv/Scripts/python.exe -I docs/validation/v0.5.8/snr_direction_recount.py
--out docs/validation/v0.5.8/snr-direction-recount.json``
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import stability_report as sr  # noqa: E402


def direction(keys: list[str], new: dict, base: dict) -> dict:
    moved = [k for k in keys if sr.snr_differs(new.get(k), base[k]) is True]
    lower = sorted(k for k in moved if sr.snr_of(new[k]) < sr.snr_of(base[k]))
    higher = sorted(k for k in moved if sr.snr_of(new[k]) > sr.snr_of(base[k]))

    def toi(k: str) -> str:
        return (new[k].get("toi") or base[k].get("toi") or k) if k in new else k

    return {
        "moved": len(moved),
        "lower": len(lower),
        "higher": len(higher),
        "higher_targets": [
            {
                "target_key": k,
                "toi": toi(k),
                "snr_v056": str(sr.snr_of(base[k])),
                "snr_v058": str(sr.snr_of(new[k])),
            }
            for k in higher
        ],  # fmt: skip
    }


def main() -> None:
    s = json.loads(sr.SET_FILE.read_text("utf-8"))
    keys = [*s["decided"], *s["inconclusive_drawn"]]
    base = sr.v056()
    new = {r["target_key"]: r for r in sr.load() if r.get("target_key") in set(keys)}
    same = [k for k in keys if ((new.get(k) or {}).get("provenance") or {}).get("overall")
            == "same"]  # fmt: skip
    decided_changed = [k for k in s["decided"] if sr.ok(new.get(k))
                       and sr.outcome(new.get(k)) != sr.outcome(base[k])]  # fmt: skip
    out = {
        "schema": "refute-v058-snr-direction-recount-1",
        "mode": "exploratory",
        "limits_label": sr.LABEL,
        "method_status": "not_validated",
        "records_sha256": hashlib.sha256(sr.BUNDLE.read_bytes()).hexdigest(),
        "report_script_sha256": hashlib.sha256(Path(sr.__file__).read_bytes()).hexdigest(),
        "records": len(new),
        "total": direction(keys, new, base),
        "same": direction(same, new, base),
        "decided_changed_in_completed_runs": direction(decided_changed, new, base),
    }
    text = json.dumps(out, indent=2) + "\n"
    if len(sys.argv) > 2 and sys.argv[1] == "--out":
        with open(sys.argv[2], "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
    print(text, end="")


if __name__ == "__main__":
    main()
