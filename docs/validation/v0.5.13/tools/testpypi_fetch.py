"""Download the files TestPyPI publishes for one version of ``refute`` (the maintainer's decision
D5, #218 comment 7207651312): download only, never install; counted by the meter.

    unit testpypi-fetch:  {python} -I -B docs/validation/v0.5.13/tools/testpypi_fetch.py <version>

It reads ``https://test.pypi.org/pypi/refute/<version>/json``, downloads every file it lists into
``.cache/v0513/testpypi/<version>/``, computes each file's SHA-256 and compares it with the
digest the index reports. It writes ``out/testpypi-fetch.json`` (file names, sizes, SHA-256,
the index's digests, URLs, retrieval time) and ``out/transfer.json`` with the bytes received
(the JSON body and every file body). Standard library only (urllib); no token, no credentials.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
UA = {"User-Agent": "refute-testpypi-check"}


def get(url: str) -> bytes:
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r:
        return r.read()


def main() -> int:
    version = sys.argv[1]
    folder = ROOT / ".cache" / "v0513" / "testpypi" / version
    folder.mkdir(parents=True, exist_ok=True)
    meta_url = f"https://test.pypi.org/pypi/refute/{version}/json"
    body = get(meta_url)
    received = len(body)
    meta = json.loads(body)
    rows = []
    for f in meta.get("urls", []):
        data = get(f["url"])
        received += len(data)
        (folder / f["filename"]).write_bytes(data)
        digest = hashlib.sha256(data).hexdigest()
        rows.append({"filename": f["filename"], "bytes": len(data), "sha256": digest,
                     "index_sha256": f.get("digests", {}).get("sha256"),
                     "matches_index": digest == f.get("digests", {}).get("sha256"),
                     "url": f["url"], "packagetype": f.get("packagetype")})  # fmt: skip
    doc = {"utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "metadata_url": meta_url,
           "version": version, "files": rows}  # fmt: skip
    out = Path(os.environ["REFUTE_RUN_OUT"])
    (out / "testpypi-fetch.json").write_text(json.dumps(doc, indent=1) + "\n", "utf-8")
    (out / "transfer.json").write_text(json.dumps({"inbound_bytes": received,
        "basis": "measured: the JSON body and every file body received"}), "utf-8")  # fmt: skip
    print(json.dumps({"files": [(r["filename"], r["bytes"], r["sha256"]) for r in rows]}))
    return 0 if rows and all(r["matches_index"] for r in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
