"""Create the Zenodo DRAFT of the v0.5.8 record (adviser, 2026-11-23). Never publishes.

docs/data-publication.md: the token (scope deposit:write only) is read from the maintainer's
local file only inside this process, at the moment of the calls, and passed only in the
Authorization header; never printed, logged, written elsewhere, or given as an argument.
Refuses to run if a draft was already created (.cache/v058/zenodo-v2/draft.json).
Usage: .venv/Scripts/python.exe -I this.py
"""
import hashlib
import json
import os
import urllib.request
from pathlib import Path

ROOT = Path(r"C:\Projetos\refute")
PKG = ROOT / ".cache" / "v058" / "zenodo-v2"
STATE = PKG / "draft.json"
API = "https://zenodo.org/api/deposit/depositions"


def token() -> str:
    p = Path(os.environ["USERPROFILE"]) / "Downloads" / "refute-v058-draft.txt"
    t = p.read_text(encoding="utf-8").strip()
    if len(t) < 20:
        raise SystemExit("token file looks empty")
    return t


def call(method: str, url: str, body=None, data: bytes | None = None, ctype="application/json"):
    headers = {"Authorization": "Bearer " + token(), "Content-Type": ctype}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=600) as r:
            raw = r.read()
            return r.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as e:
        raise SystemExit(f"HTTP {e.code} on {method} {url.split('?')[0]}: {e.read()[:800]!r}")


def main() -> None:
    if STATE.exists():
        raise SystemExit("a draft already exists: " + STATE.read_text(encoding="utf-8"))
    meta = json.loads((PKG / "metadata.json").read_text(encoding="utf-8"))
    st, dep = call("POST", API, body={})
    dep_id, bucket = dep["id"], dep["links"]["bucket"]
    STATE.write_text(json.dumps({"id": dep_id, "html": dep["links"].get("html")}) + "\n",
                     encoding="utf-8")
    files = sorted((PKG / "record").iterdir())
    for f in files:
        st, res = call("PUT", f"{bucket}/{f.name}", data=f.read_bytes(),
                       ctype="application/octet-stream")
        md5 = hashlib.md5(f.read_bytes()).hexdigest()
        ok = res.get("checksum") == "md5:" + md5 and res.get("size") == f.stat().st_size
        print(f"upload {f.name}: size={res.get('size')} checksum_ok={ok}")
        if not ok:
            raise SystemExit("checksum mismatch")
    st, res = call("PUT", f"{API}/{dep_id}", body={"metadata": meta})
    print("metadata status", st, "state", res.get("state"), "submitted", res.get("submitted"))
    st, res = call("GET", f"{API}/{dep_id}")
    print("draft id", dep_id, "files", len(res.get("files", [])), "state", res.get("state"),
          "submitted", res.get("submitted"))
    print("html", res["links"].get("html"))


if __name__ == "__main__":
    main()
