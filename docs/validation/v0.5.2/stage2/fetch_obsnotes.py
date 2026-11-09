"""Download the ExoFOP-TESS observing notes, by the maintainer's decision of 2026-11-09 (#216, item
3 (b), "the disposition and comments of TFOP on ExoFOP"), for T3b's counts only: no draw, no target
selected.

The notes hold community text and usernames. The copy stays in the git-ignored
``.cache/v052/toi/<sha256>/``; no row, name or identifier of it enters this folder. Each attempt
follows the transient rule of the phase (5 attempts, 120 s). The URL, the UTC time, the size and the
SHA-256 are recorded in ``obsnotes-fetch.json``; a further download would be a new record.
``method_status: not_validated``.

Usage (from the project root): ``.venv/Scripts/python.exe <this file>``.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path

import fetch_toi

HERE = Path(__file__).resolve().parent
RECORD = HERE / "obsnotes-fetch.json"
URL = "https://exofop.ipac.caltech.edu/tess/download_obsnotes.php?sort=id&output=csv"


def main() -> None:
    if RECORD.exists():
        raise SystemExit("obsnotes-fetch.json exists: a further download is a new record")
    data = fetch_toi.fetch(URL)
    if not data.startswith(b"ID,TIC ID,"):
        raise SystemExit("the response is not the notes table")
    sha = hashlib.sha256(data).hexdigest()
    folder = fetch_toi.OUT / sha
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "obsnotes.csv").write_bytes(data)
    doc = {
        "label": "the ExoFOP-TESS observing notes, for T3b's counts only (#216)",
        "url": URL,
        "retrieved_utc": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
        "bytes": len(data),
        "sha256": sha,
    }
    RECORD.write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n", "utf-8")
    print(len(data), sha, flush=True)


if __name__ == "__main__":
    main()
