"""Download the ExoFOP-TESS TOI table again, by the maintainer's decision of 2026-11-09 (#216, item
3 (a)), for the counts of T3b's inventory only: no draw, no target selected, no light curve read.

The copy stays in the git-ignored ``.cache/v052/toi/<sha256>/``; no row of it enters this folder.
Each attempt follows the transient rule of the phase (5 attempts, 120 s). The URL, the UTC time, the
size and the SHA-256 are recorded in ``toi-fetch.json`` next to this script, and a second download
would be a new record, never an overwrite. ``method_status: not_validated``.

Usage (from the project root): ``.venv/Scripts/python.exe <this file>``.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
OUT = ROOT / ".cache" / "v052" / "toi"
RECORD = HERE / "toi-fetch.json"
URL = "https://exofop.ipac.caltech.edu/tess/download_toi.php?sort=toi&output=csv"
ATTEMPTS = 5
TIMEOUT = 120


def fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "refute-research-fetch/0.5.2"})
    last = None
    for attempt in range(1, ATTEMPTS + 1):
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
                return response.read()
        except OSError as exc:
            last = exc
            print("attempt", attempt, "failed:", type(exc).__name__, flush=True)
            time.sleep(5 * attempt)
    raise SystemExit(f"{url}: {ATTEMPTS} attempts failed: {last}")


def main() -> None:
    if RECORD.exists():
        raise SystemExit("toi-fetch.json exists: a further download is a new record")
    data = fetch(URL)
    if not data.startswith(b"TIC ID,") and b"TIC ID" not in data[:200]:
        raise SystemExit("the response is not the TOI table")
    sha = hashlib.sha256(data).hexdigest()
    folder = OUT / sha
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "toi.csv").write_bytes(data)
    doc = {
        "label": "the ExoFOP-TESS TOI table, for T3b's counts only (#216)",
        "url": URL,
        "retrieved_utc": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
        "bytes": len(data),
        "sha256": sha,
    }
    RECORD.write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n", "utf-8")
    print(len(data), sha, flush=True)


if __name__ == "__main__":
    main()
