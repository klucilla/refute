"""Build the corrected Zenodo package for v0.5.8 (adviser, 2026-11-23).

Copies the nine frozen payload files unchanged from .cache/v058/zenodo/record, adds the root
LICENSE (Apache-2.0, bytes from commit bbfdecc6) for the scripts, rewrites the manifest and the
metadata after one Codex round (.cache/v058/zenodo-review/codex-answer.md). The original package
is not modified. Usage: .venv/Scripts/python.exe -I this.py <correction-2 URL>
"""
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(r"C:\Projetos\refute")
SRC = ROOT / ".cache" / "v058" / "zenodo"
DST = ROOT / ".cache" / "v058" / "zenodo-v2"
COMMIT = "bbfdecc6eac3dfbd3e532cf83cbb006d22c136e5"
MAIN = "4a704f0f05fd9f67e4c2dfbeadb7da22ae981778"
GH = "https://github.com/klucilla/refute"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> None:
    corr2 = sys.argv[1]
    if DST.exists():
        raise SystemExit("zenodo-v2 already exists; not overwriting")
    (DST / "record").mkdir(parents=True)
    old = json.loads((SRC / "record" / "MANIFEST-sha256.json").read_text(encoding="utf-8"))
    manifest = []
    for e in old:
        src = SRC / "record" / e["file"]
        if sha(src) != e["sha256"] or src.stat().st_size != e["bytes"]:
            raise SystemExit(f"mismatch in {e['file']}")
        dst = DST / "record" / e["file"]
        shutil.copyfile(src, dst)
        assert sha(dst) == e["sha256"]
        manifest.append(dict(e, commit=COMMIT))
    lic = subprocess.run(["git", "-C", str(ROOT), "show", f"{COMMIT}:LICENSE"],
                         check=True, capture_output=True).stdout
    (DST / "record" / "LICENSE").write_bytes(lic)
    manifest.append({"file": "LICENSE", "repository_path": "LICENSE", "commit": COMMIT,
                     "bytes": len(lic), "sha256": hashlib.sha256(lic).hexdigest(),
                     "note": "Apache-2.0, the license of the three bundled scripts"})
    (DST / "record" / "MANIFEST-sha256.json").write_text(
        json.dumps(manifest, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")

    tree = f"{GH}/tree/{COMMIT}/docs/validation/v0.5.8"
    blob = f"{GH}/blob/{MAIN}"
    corr1 = f"{blob}/docs/reports/v0.5.8-report-correction-2026-11-23.md"
    desc = (
        "<p>Exploratory Refute v0.5.8 records for 167 TESS Objects of Interest (TOIs). Limits label: "
        "<code>WEAKENED; does not meet D1, D2, D4, T2a</code>. Method status: <code>not_validated</code>. "
        "The outputs describe this sample only. TOI verdicts, candidate claims, dispositions and "
        "discoveries are outside the scope of the dataset.</p>"
        "<p>The comparison pairs v0.5.6 search-mode outputs with TOI-seeded reruns using the same v0.5 "
        "battery. It cannot isolate the effect of the seed. Input-file identity was verified for 83 of "
        "167 targets. Of the 15 refitted signal-to-noise ratios that differed by more than 10%, 13 were "
        "lower and two were higher. The bundled report's \"More than one optimum\" label denotes a "
        "predefined SNR threshold and should be read as a descriptive count. See the "
        f"<a href=\"{corr1}\">first correction</a> and the <a href=\"{corr2}\">second correction</a>.</p>"
        "<p>CC BY 4.0 applies to Refute's original dataset content, the bundled scripts are licensed "
        "under Apache-2.0 (the LICENSE file is included), and third-party catalog values retain their "
        "source terms and applicable acknowledgment and citation requirements.</p>"
        "<p>The nine data and script files are byte-identical to their counterparts in the "
        f"<a href=\"{tree}\">repository snapshot at {COMMIT}</a>. See <code>MANIFEST-sha256.json</code> "
        "for file hashes and repository paths. The records include MAST file manifests. The TESS light "
        "curves and pixel files are not included; they are available from MAST at STScI.</p>"
        "<p>This research has made use of the Exoplanet Follow-up Observation Program (ExoFOP; DOI: "
        "10.26134/ExoFOP5) website, which is operated by the California Institute of Technology, under "
        "contract with the National Aeronautics and Space Administration under the Exoplanet "
        "Exploration Program.</p>"
        "<p>This research has made use of the NASA Exoplanet Archive, which is operated by the "
        "California Institute of Technology, under contract with the National Aeronautics and Space "
        "Administration under the Exoplanet Exploration Program. See "
        "<a href=\"https://doi.org/10.3847/PSJ/ade3c2\">Christiansen et al. (2025)</a>. TESS data were "
        "obtained from MAST at STScI under NASA contract NAS5-26555.</p>"
    )
    meta = {
        "title": "Refute v0.5.8: output stability of the v0.5 battery on 167 TESS TOIs (exploratory records)",
        "upload_type": "dataset",
        "access_right": "open",
        "license": "cc-by-4.0",
        "creators": [{"name": "Lucilla, Klauber", "orcid": "0009-0002-4519-5457"}],
        "keywords": ["falsification", "reproducibility", "exoplanets", "TESS", "stability"],
        "description": desc,
        "related_identifiers": [
            {"identifier": tree, "relation": "isDerivedFrom"},
            {"identifier": f"{blob}/docs/reports/v0.5.8-report.md", "relation": "isDocumentedBy"},
            {"identifier": f"{blob}/docs/reports/v0.5.8-stability-note.md", "relation": "isDocumentedBy"},
            {"identifier": corr1, "relation": "isDocumentedBy"},
            {"identifier": corr2, "relation": "isDocumentedBy"},
        ],
    }
    (DST / "metadata.json").write_text(json.dumps(meta, indent=1, ensure_ascii=False) + "\n",
                                       encoding="utf-8", newline="\n")
    print("files:", len(manifest), "license_sha256:", manifest[-1]["sha256"])


if __name__ == "__main__":
    main()
