"""Append one note to v0.5.12's journal (``log.jsonl``): a deviation or a record that a decision
asks the journal to hold. The note's text is a committed JSON file (the extra argument); this
script adds the event type, the time and the file's SHA-256, and appends one line. It never edits
an existing line.

    launch_v3 unit journal-note:
        {python} -I -B docs/validation/v0.5.12/tools/journal_note.py <note.json>
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
LOG = ROOT / "docs" / "validation" / "v0.5.12" / "log.jsonl"


def main() -> int:
    note_path = ROOT / sys.argv[1]
    data = note_path.read_bytes()
    entry = {
        "event": "note",
        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "note_file": note_path.relative_to(ROOT).as_posix(),
        "note_sha256": hashlib.sha256(data).hexdigest(),
        "note": json.loads(data.decode("utf-8")),
    }
    with LOG.open("a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(entry, sort_keys=True) + "\n")
    print(json.dumps({"appended": entry["note_file"], "sha256": entry["note_sha256"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
