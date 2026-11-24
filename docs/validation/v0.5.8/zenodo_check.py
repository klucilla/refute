"""v0.5.8 Zenodo record: compare the MD5 of every published file (Zenodo's public API) with the
local files that were uploaded, and print the record's public facts (DOI, licence, date).

Read-only: one GET to the public API, no token. Usage (from the project root):
``.venv/Scripts/python.exe -I docs/validation/v0.5.8/zenodo_check.py <local record folder>
[--out <json>]``
"""

from __future__ import annotations

import hashlib
import json
import sys
import urllib.request
from pathlib import Path

API = "https://zenodo.org/api/records/24485272"


def md5(path: Path) -> str:
    h = hashlib.md5()  # noqa: S324 - Zenodo's own checksum, compared, not used for security
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def main() -> None:
    local = Path(sys.argv[1])
    req = urllib.request.Request(API, headers={"User-Agent": "refute-record-check"})
    with urllib.request.urlopen(req, timeout=60) as r:  # noqa: S310 - a fixed https URL
        record = json.loads(r.read().decode("utf-8"))
    rows = []
    for f in record.get("files", []):
        name = f["key"]
        remote = str(f.get("checksum", "")).removeprefix("md5:")
        path = local / name
        mine = md5(path) if path.exists() else None
        rows.append({"file": name, "size": f.get("size"), "zenodo_md5": remote, "local_md5": mine,
                     "match": mine == remote})  # fmt: skip
    meta = record.get("metadata", {})
    out = {
        "api": API,
        "doi": record.get("doi"),
        "conceptdoi": record.get("conceptdoi"),
        "created": record.get("created"),
        "publication_date": meta.get("publication_date"),
        "license": meta.get("license"),
        "title": meta.get("title"),
        "files": rows,
        "all_match": bool(rows) and all(r["match"] for r in rows),
        "count": len(rows),
    }
    text = json.dumps(out, indent=1) + "\n"
    if len(sys.argv) > 3 and sys.argv[2] == "--out":
        Path(sys.argv[3]).write_text(text, "utf-8", newline="\n")
    print(text, end="")


if __name__ == "__main__":
    main()
