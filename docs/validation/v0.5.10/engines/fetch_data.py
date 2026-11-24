"""Fetch again the 24 TOIs' light curves and pixel files of v0.5.9, checked against its manifests.

Part (f) of the v0.5.10 charter and its amendment (section 9). For each fetch unit of
docs/validation/v0.5.9/prototype-units.json, every file of ``light_curve_manifest`` and
``tpf_manifest`` is downloaded from MAST (the recorded URL, else the recorded ``data_uri``, else
the product name) into .cache/v0510/data/<target>/, and its SHA-256 is compared with the recorded
one. A mismatch or a missing hash is recorded, and that file is marked unusable. Runs in the
project's environment (standard library only), at most two downloads at a time; resumable (a
present file with the recorded hash is not downloaded again).

Output: data-check.json beside this script (per file: target, sector, kind, bytes, recorded and
observed SHA-256, status), and the bytes downloaded by this run.

Usage: python fetch_data.py [--only TIC-...]
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[3]
UNITS = PROJECT / "docs/validation/v0.5.9/prototype-units.json"
SET = PROJECT / "docs/validation/v0.5.9/prototype-set.json"
DATA = PROJECT / ".cache/v0510/data"
OUT = HERE / "data-check.json"
MAST = "https://mast.stsci.edu/api/v0.1/Download/file?uri="
UA = {"User-Agent": "refute-v0510-fetch"}


def plan() -> list[dict]:
    units = json.loads(UNITS.read_text(encoding="utf-8"))["units"]
    order = json.loads(SET.read_text(encoding="utf-8"))["order"]
    fetch = {
        u["content"]["target_key"]: u["content"] for u in units if u["content"]["kind"] == "fetch"
    }
    items = []
    for key in order:
        c = fetch[key]
        manifests = (
            ("lc", c.get("light_curve_manifest") or []),
            ("tpf", c.get("tpf_manifest") or []),
        )
        for kind, man in manifests:
            for f in man:
                url = f.get("url")
                if not url and f.get("data_uri"):
                    url = MAST + urllib.parse.quote(f["data_uri"], safe=":/")
                if not url:
                    url = MAST + "mast:TESS/product/" + f["name"]
                items.append(
                    {
                        "target": key,
                        "toi": c["toi"],
                        "kind": kind,
                        "sector": f.get("sector"),
                        "name": f["name"],
                        "url": url,
                        "recorded_bytes": f.get("bytes"),
                        "recorded_sha256": f.get("sha256"),
                    }
                )
    return items


def fetch(item: dict) -> dict:
    dest = DATA / item["target"] / item["name"]
    dest.parent.mkdir(parents=True, exist_ok=True)
    rec = dict(item)
    downloaded = 0
    if dest.exists():
        data = dest.read_bytes()
    else:
        data = None
        for attempt in range(1, 4):
            try:
                req = urllib.request.Request(item["url"], headers=UA)
                with urllib.request.urlopen(req, timeout=600) as r:
                    data = r.read()
                downloaded = len(data)
                rec["attempts"] = attempt
                break
            except Exception as e:  # recorded, not hidden
                rec.setdefault("errors", []).append(f"{type(e).__name__}: {e}")
                time.sleep(5 * attempt)
        if data is None:
            rec["status"] = "download_failed"
            rec["downloaded_bytes"] = 0
            return rec
        tmp = dest.with_suffix(dest.suffix + ".part")
        tmp.write_bytes(data)
        tmp.replace(dest)
    got = hashlib.sha256(data).hexdigest()
    rec["observed_sha256"] = got
    rec["observed_bytes"] = len(data)
    rec["downloaded_bytes"] = downloaded
    if not item["recorded_sha256"]:
        rec["status"] = "no_recorded_hash"
    elif got == item["recorded_sha256"]:
        rec["status"] = "match"
    else:
        rec["status"] = "mismatch"
    return rec


def main() -> int:
    items = plan()
    if "--only" in sys.argv:
        only = sys.argv[sys.argv.index("--only") + 1]
        items = [i for i in items if i["target"] == only]
    started = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with ThreadPoolExecutor(max_workers=2) as ex:
        recs = list(ex.map(fetch, items))
    counts: dict[str, int] = {}
    for r in recs:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    doc = {
        "schema": "refute-v0510-data-check-1",
        "mode": "exploratory",
        "source": "docs/validation/v0.5.9/prototype-units.json, fetch units' manifests",
        "started_utc": started,
        "ended_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "files": len(recs),
        "status_counts": counts,
        "downloaded_bytes": sum(r.get("downloaded_bytes", 0) for r in recs),
        "bytes_on_disk": sum(r.get("observed_bytes", 0) for r in recs),
        "records": recs,
    }
    if "--only" not in sys.argv:
        OUT.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8")
    keys = ("files", "status_counts", "downloaded_bytes", "bytes_on_disk")
    print(json.dumps({k: doc[k] for k in keys}))
    return 0 if set(counts) <= {"match"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
