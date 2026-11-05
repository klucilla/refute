"""Exit criterion 6, the recorded deviation of 2026-11-05 (#199): fetch the TESS-EB table from an
official VizieR mirror, because the CDS host the claim's scan records did not answer.

The query is the scan's own (``calibration/v0.5/eb_catalog_scan.json``, the TESS-EB external
snapshot's ``url``) with only the host replaced: ``vizier.cfa.harvard.edu`` first,
``vizier.idia.ac.za`` as the reserve. The answer is written, never over a file, to
``.cache/v05/c6-prep/<host>/<file name of the scan's cache_path>``, a preparation folder outside
the clean clone; its raw SHA-256 and its content SHA-256 (``refute.packs.tess.ebcatalog.
content_sha256``, the rule the frozen code applies) are recorded in ``fetch.json`` next to it.
The script stops (exit 1) unless the content SHA-256 equals the scan's ``content_sha256``.

The TESS-EB table is never committed nor archived to the public Drive (#33).

Run from the repository root: ``.venv/Scripts/python.exe calibration/v0.5/deviation/
fetch_tess_eb_mirror.py``
"""

from __future__ import annotations

import hashlib
import json
import sys
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

SCAN = Path("calibration/v0.5/eb_catalog_scan.json")
PREP = Path(".cache/v05/c6-prep")
CDS_HOST = "vizier.cds.unistra.fr"
MIRRORS = ("vizier.cfa.harvard.edu", "vizier.idia.ac.za")


def tess_eb_snapshot(root: Path) -> dict:
    from refute.packs.tess.ebcatalog import external_snapshots

    scan = json.loads((root / SCAN).read_text(encoding="utf-8"))
    snaps = [s for s in external_snapshots(scan) if s["parser"] == "tess-eb-vizier-tsv"]
    if len(snaps) != 1:
        raise SystemExit(f"expected one TESS-EB snapshot in the scan, found {len(snaps)}")
    return snaps[0]


def mirror_url(url: str, host: str) -> str:
    parts = urllib.parse.urlsplit(url)
    if parts.netloc != CDS_HOST:
        raise SystemExit(f"the scan's URL host is {parts.netloc}, not {CDS_HOST}")
    return urllib.parse.urlunsplit(parts._replace(netloc=host))


def main() -> int:
    from refute.packs.tess.ebcatalog import content_sha256

    root = Path.cwd()
    snap = tess_eb_snapshot(root)
    name = Path(snap["cache_path"]).name
    attempts = []
    for host in MIRRORS:
        url = mirror_url(snap["url"], host)
        stamp = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "refute"})
            with urllib.request.urlopen(request, timeout=180) as response:  # noqa: S310
                data = response.read()
        except Exception as exc:  # noqa: BLE001 - recorded; the reserve host is tried
            attempts.append({"host": host, "url": url, "utc": stamp, "error": repr(exc)})
            continue
        folder = root / PREP / host
        folder.mkdir(parents=True, exist_ok=True)
        with open(folder / name, "xb") as handle:
            handle.write(data)
        record = {
            "host": host,
            "url": url,
            "recorded_url": snap["url"],
            "utc": stamp,
            "bytes": len(data),
            "raw_sha256": hashlib.sha256(data).hexdigest(),
            "content_sha256": content_sha256(data),
            "expected_content_sha256": snap["content_sha256"],
            "cache_path": snap["cache_path"],
            "file": (PREP / host / name).as_posix(),
            "earlier_attempts": attempts,
        }
        record["content_matches"] = record["content_sha256"] == snap["content_sha256"]
        with open(folder / "fetch.json", "x", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(record, indent=2) + "\n")
        print(json.dumps(record, indent=2))
        return 0 if record["content_matches"] else 1
    print(json.dumps({"attempts": attempts}, indent=2))
    return 1


if __name__ == "__main__":
    sys.exit(main())
