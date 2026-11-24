"""Build the verified wheelhouse of part (f) (Codex's blocking item 1).

For each pin of requirements.txt, read PyPI's JSON for that exact version and select the one
artifact for Windows x64 CPython 3.12 whose SHA-256 is among the pinned hashes. The one sdist is
fbpca 1.0 (no wheel on PyPI; it is built offline later, blocking item 2). Each artifact must have
been uploaded before 2026-11-17T00:00:00Z. A missing, late or mismatched artifact is rejected.

``plan`` writes wheelhouse-manifest.json (filename, URL, upload time, SHA-256, size) without
downloading. ``fetch`` downloads the manifest's artifacts into the wheelhouse, at most two at a
time, and checks each SHA-256; a mismatch deletes nothing and is reported.

Usage: python wheelhouse.py plan|fetch WHEELHOUSE_DIR
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
REQUIREMENTS = HERE / "requirements.txt"
MANIFEST = HERE / "wheelhouse-manifest.json"
CUTOFF = "2026-11-17T00:00:00"
SDIST_ALLOWED = {"fbpca"}
# Compatible tags for CPython 3.12 on win_amd64, best first.
TAG_ORDER = [
    re.compile(r"-cp312-cp312-win_amd64\.whl$"),
    re.compile(r"-cp3\d+-abi3-win_amd64\.whl$"),
    re.compile(r"-py3-none-win_amd64\.whl$"),
    re.compile(r"-cp312-none-any\.whl$"),
    re.compile(r"-py3-none-any\.whl$"),
    re.compile(r"-py2\.py3-none-any\.whl$"),
]
UA = {"User-Agent": "refute-v0510-wheelhouse"}


def pins() -> list[tuple[str, str, set[str]]]:
    out: list[tuple[str, str, set[str]]] = []
    cur: tuple[str, str, set[str]] | None = None
    for line in REQUIREMENTS.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^([A-Za-z0-9_.\-]+)==([^\s\\;]+)", line)
        if m:
            cur = (m.group(1), m.group(2), set())
            out.append(cur)
            continue
        h = re.search(r"--hash=sha256:([0-9a-f]{64})", line)
        if h and cur is not None:
            cur[2].add(h.group(1))
    return out


def pypi_files(name: str, version: str) -> list[dict]:
    url = f"https://pypi.org/pypi/{name}/{version}/json"
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        return json.load(r)["urls"]


def select(name: str, version: str, hashes: set[str]) -> dict:
    files = [f for f in pypi_files(name, version) if f["digests"]["sha256"] in hashes]
    chosen = None
    for pat in TAG_ORDER:
        hits = [f for f in files if pat.search(f["filename"])]
        if hits:
            chosen = hits[0]
            break
    if chosen is None and name.lower() in SDIST_ALLOWED:
        sd = [f for f in files if f["packagetype"] == "sdist"]
        chosen = sd[0] if sd else None
    if chosen is None:
        return {"name": name, "version": version, "rejected": "no compatible pinned artifact"}
    rec = {
        "name": name,
        "version": version,
        "filename": chosen["filename"],
        "url": chosen["url"],
        "upload_time": chosen["upload_time_iso_8601"],
        "sha256": chosen["digests"]["sha256"],
        "size": chosen["size"],
        "packagetype": chosen["packagetype"],
    }
    if chosen["upload_time_iso_8601"][:19] >= CUTOFF:
        rec["rejected"] = f"uploaded at or after {CUTOFF}Z"
    return rec


def plan() -> int:
    recs = []
    for name, version, hashes in pins():
        recs.append(select(name, version, hashes))
        time.sleep(0.05)
    rejected = [r for r in recs if "rejected" in r]
    doc = {
        "schema": "refute-v0510-wheelhouse-1",
        "mode": "exploratory",
        "source": "https://pypi.org/pypi/<name>/<version>/json",
        "read_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "target": "CPython 3.12, win_amd64",
        "cutoff_utc": CUTOFF + "Z",
        "requirements_sha256": hashlib.sha256(REQUIREMENTS.read_bytes()).hexdigest(),
        "count": len(recs),
        "rejected": len(rejected),
        "total_bytes": sum(r.get("size", 0) for r in recs),
        "artifacts": recs,
    }
    MANIFEST.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8")
    print(f"{len(recs)} pins, {len(rejected)} rejected, {doc['total_bytes']} bytes")
    for r in rejected:
        print("REJECTED", r["name"], r["version"], r["rejected"])
    return 1 if rejected else 0


def fetch_one(rec: dict, dest: Path) -> tuple[str, int, str]:
    path = dest / rec["filename"]
    if path.exists() and hashlib.sha256(path.read_bytes()).hexdigest() == rec["sha256"]:
        return rec["filename"], 0, "present"
    req = urllib.request.Request(rec["url"], headers=UA)
    with urllib.request.urlopen(req, timeout=300) as r:
        data = r.read()
    got = hashlib.sha256(data).hexdigest()
    if got != rec["sha256"]:
        return rec["filename"], len(data), f"MISMATCH {got}"
    path.write_bytes(data)
    return rec["filename"], len(data), "ok"


def fetch(dest: Path) -> int:
    doc = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if doc["rejected"]:
        print("the manifest has rejected artifacts; nothing is fetched")
        return 1
    dest.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=2) as ex:
        results = list(ex.map(lambda r: fetch_one(r, dest), doc["artifacts"]))
    bad = [r for r in results if r[2] not in ("ok", "present")]
    total = sum(r[1] for r in results)
    print(f"fetched {len(results)} artifacts, {total} bytes downloaded, {len(bad)} bad")
    for b in bad:
        print("BAD", b)
    return 1 if bad else 0


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] not in ("plan", "fetch"):
        print(__doc__)
        return 2
    if sys.argv[1] == "plan":
        return plan()
    return fetch(Path(sys.argv[2]))


if __name__ == "__main__":
    raise SystemExit(main())
