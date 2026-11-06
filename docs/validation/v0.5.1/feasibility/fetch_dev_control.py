"""v0.5.1 WP3 (c): fetch the light curves of the development control TIC-101395259 (#204).

The maintainer's approval of 2026-11-06 (#208): a fresh MAST download of this development target's
light curves only (no pixel files), into ``.cache/v051/dev/`` (outside git), with the transient
rule (5 attempts, 120 s apart), the disk counted in the cap, and the URL, date and SHA-256 of every
file recorded. The test plan is the v0.5 C3 claim's (``calibration/v0.5/claim.yaml``), with
``target_pixel_files`` off; the frozen TESS adapter fetches. The fetched files are compared with
the SHA-256 that the v0.5 dossier recorded (``TIC-101395259/data/manifest.json`` inside the archive
``c3-dossiers.zip`` on the Drive, read only).

Usage: .venv/Scripts/python.exe docs/validation/v0.5.1/feasibility/fetch_dev_control.py
"""

from __future__ import annotations

import json
import time
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
CACHE = ROOT / ".cache/v051/dev"
TIC = 101395259
DRIVE_ZIP = Path(
    "K:/Meu Drive/Pessoal/Projetos/refute/arquivo-v0.5-calibration/c3-dossiers/c3-dossiers.zip"
)
ATTEMPTS, BACKOFF = 5, 120.0


def main() -> dict:
    import yaml

    from refute.packs.tess.adapter import TessAdapter

    claim = yaml.safe_load((ROOT / "calibration/v0.5/claim.yaml").read_text(encoding="utf-8"))
    plan = claim["test_plan"]
    plan["data"]["target_pixel_files"] = False
    CACHE.mkdir(parents=True, exist_ok=True)
    errors = []
    manifest = None
    for attempt in range(1, ATTEMPTS + 1):
        try:
            manifest = TessAdapter().fetch({"tic_id": TIC}, plan, CACHE)
            break
        except Exception as exc:  # noqa: BLE001 - transient errors retried, then reported
            errors.append(f"attempt {attempt}: {type(exc).__name__}: {exc}")
            if attempt < ATTEMPTS:
                time.sleep(BACKOFF)
    if manifest is None:
        raise SystemExit("the fetch failed: " + "; ".join(errors))
    recorded = {}
    with zipfile.ZipFile(DRIVE_ZIP) as z:
        names = [n for n in z.namelist() if n.endswith("TIC-101395259/data/manifest.json")]
        if names:
            ref = json.loads(z.read(names[0]).decode("utf-8"))
            recorded = {f["name"]: f["sha256"] for f in ref.get("files", [])}
    files = [
        {
            "name": f["name"],
            "sector": f["sector"],
            "bytes": f["bytes"],
            "sha256": f["sha256"],
            "url": f["url"],
            "equal_to_v05_dossier": recorded.get(f["name"]) == f["sha256"]
            if f["name"] in recorded
            else None,
        }
        for f in manifest["files"]
    ]
    return {
        "label": "development data (v0.5.1 WP3 (c), #204); the maintainer's approval of 2026-11-06",
        "target": f"TIC-{TIC}",
        "retrieved_utc": manifest["retrieved_utc"],
        "service": manifest["query"]["service"],
        "files": files,
        "pixel_files": len(manifest["pixel_files"]),
        "attempt_errors": errors,
        "v05_dossier_files_recorded": len(recorded),
        "bytes_total": sum(f["bytes"] for f in files),
    }


if __name__ == "__main__":
    doc = main()
    (HERE / "dev-control-fetch.json").write_text(
        json.dumps(doc, indent=1, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({k: v for k, v in doc.items() if k != "files"}, indent=1))
    print(sum(1 for f in doc["files"] if f["equal_to_v05_dossier"]), "of", len(doc["files"]),
          "files equal to the v0.5 dossier")  # fmt: skip
