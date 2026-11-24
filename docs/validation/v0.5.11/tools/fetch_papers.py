"""Fetch the three primary papers of the screen tests (charter, step 0, item 1).

    .venv/Scripts/python.exe -I -B docs/validation/v0.5.11/tools/fetch_papers.py

Each PDF is saved under .cache/v0511/papers/ (never committed: the papers are the authors' and
the journals'), up to 3 tries inside this one attempt, each logged (rule (d)). Writes
docs/validation/v0.5.11/papers/fetch-record.json: per paper, the requested URL, the final URL,
the retrieval time (UTC), the bytes, the SHA-256 and the tries.
"""

import hashlib
import json
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT / ".cache" / "v0511" / "papers"
RECORD = ROOT / "docs" / "validation" / "v0.5.11" / "papers" / "fetch-record.json"
PAPERS = [
    ("K25", "https://arxiv.org/pdf/2509.10619v1", "k25-2509.10619v1.pdf"),
    ("T18", "https://arxiv.org/pdf/1710.06758", "t18-1710.06758.pdf"),
    ("SM03", "https://arxiv.org/pdf/astro-ph/0206228", "sm03-astro-ph-0206228.pdf"),
]
UA = "refute-research-fetch/0.5.11 (paper reading for a specification)"


def fetch(url: str) -> tuple[bytes, str]:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read(), r.geturl()


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for key, url, name in PAPERS:
        tries = []
        data = None
        final = None
        for i in range(3):
            t = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            try:
                data, final = fetch(url)
                tries.append({"try": i + 1, "utc": t, "outcome": "ok"})
                break
            except Exception as e:  # noqa: BLE001  (every failure is logged, then retried)
                tries.append({"try": i + 1, "utc": t, "outcome": f"{type(e).__name__}: {e}"})
                time.sleep(5)
        row = {"paper": key, "url": url, "final_url": final, "file": name, "tries": tries}
        if data is not None:
            if not data.startswith(b"%PDF"):
                row["error"] = "not a PDF"
            (OUT / name).write_bytes(data)
            row.update(
                {
                    "retrieved_utc": tries[-1]["utc"],
                    "bytes": len(data),
                    "sha256": hashlib.sha256(data).hexdigest(),
                }
            )
        rows.append(row)
    RECORD.parent.mkdir(parents=True, exist_ok=True)
    doc = {"labels": ["exploratory"], "user_agent": UA, "papers": rows}
    RECORD.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8", newline="\n")
    ok = all("sha256" in r and "error" not in r for r in rows)
    print(json.dumps([{k: r.get(k) for k in ("paper", "bytes", "sha256")} for r in rows]))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
