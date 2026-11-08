"""Download the two vetted tables of the TESS Ten Thousand Catalog (Kostov et al. 2025, ApJS 279,
50), by the maintainer's approval of 2026-11-08 (#216, item 5), for internal use only.

Only Tables 3 (7,936 new binaries) and 4 (2,065 known binaries), which together are the 10,001
vetted and validated systems. Table 2 (about 900,000 unvetted targets) is not downloaded. The
files stay in ``.cache/v052/t10k/<sha256>/``: no line of them enters git or the public Drive. Each
attempt follows the transient rule of the phase (5 attempts, 120 s). The URL, the date and the
SHA-256 are recorded in ``t10k-fetch.json`` next to this script.

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
OUT = ROOT / ".cache" / "v052" / "t10k"
BASE = "https://content.cld.iop.org/journals/0067-0049/279/2/50/revision1/"
FILES = {"table3": "apjsade2d8t3_mrt.txt", "table4": "apjsade2d8t4_mrt.txt"}
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
    rows = {}
    for name, filename in FILES.items():
        url = BASE + filename
        data = fetch(url)
        sha = hashlib.sha256(data).hexdigest()
        folder = OUT / sha
        folder.mkdir(parents=True, exist_ok=True)
        (folder / filename).write_bytes(data)
        rows[name] = {
            "url": url,
            "retrieved_utc": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
            "bytes": len(data),
            "sha256": sha,
        }
        print(name, len(data), sha, flush=True)
    doc = {
        "label": "the vetted tables of the TESS Ten Thousand Catalog, internal use only (#216)",
        "license_state": "unconfirmed: see docs/plans/sources/ (the data page's statements)",
        "files": rows,
    }
    (HERE / "t10k-fetch.json").write_text(json.dumps(doc, indent=1) + "\n", "utf-8")


if __name__ == "__main__":
    main()
