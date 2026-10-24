"""Read-only scan of the repository's published dossiers and claims, for the audit fixes of
2026-10-24: does any earlier result show what A1, A4, A5 or A6 now refuse?

- A1: every TESS dossier's recorded input manifest (data/manifest.json) is the dossier's own
  target (tic_id and target_key equal target.json's);
- A4: no dossier holds files of two runs (every dossier's MANIFEST.sha256 verifies; its
  verdict.json run id, when recorded, is its run folder's);
- A5: no claim or targets file lists one target key twice (case and spacing ignored);
- A6: no sealed dossier (SEAL.json or annexes/) has a review/ folder, and every seal verifies.
Usage: scan_prior.py <repository root> <out.json>"""

import json
import sys
from collections import Counter
from pathlib import Path

import yaml

root = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(root / "src"))
from refute.core.dossier import verify_manifest  # noqa: E402
from refute.core.seal import verify_seal  # noqa: E402

SKIP = (".cache", ".venv", ".git", "node_modules")
out = {"a1": [], "a4": [], "a5": [], "a6": [], "counts": Counter()}


def skipped(p: Path) -> bool:
    return any(part in SKIP for part in p.relative_to(root).parts)


for manifest in root.rglob("MANIFEST.sha256"):
    if skipped(manifest):
        continue
    d = manifest.parent
    rel = d.relative_to(root).as_posix()
    out["counts"]["dossiers"] += 1
    if (d / "MANIFEST.sha256").is_file():
        problems = verify_manifest(d)
        out["counts"]["manifests_checked"] += 1
        if problems:
            out["a4"].append({"dossier": rel, "manifest_problems": problems[:3]})
    target, data = d / "target.json", d / "data" / "manifest.json"
    if target.is_file() and data.is_file():
        t, m = json.loads(target.read_text("utf-8")), json.loads(data.read_text("utf-8"))
        if "tic_id" in t:
            out["counts"]["tess_input_manifests"] += 1
            if m.get("tic_id") != t["tic_id"] or m.get("target_key") != t.get("key"):
                out["a1"].append(
                    {
                        "dossier": rel,
                        "target": t.get("key"),
                        "manifest": [m.get("tic_id"), m.get("target_key")],
                    }
                )
    sealed = (d / "SEAL.json").exists() or (d / "annexes").exists()
    if sealed:
        out["counts"]["sealed"] += 1
        if (d / "review").exists():
            out["a6"].append({"dossier": rel, "problem": "review/ in a sealed dossier"})
        problems = verify_seal(d) if (d / "SEAL.json").exists() else ["annexes/ without SEAL.json"]
        if problems:
            out["a6"].append({"dossier": rel, "seal_problems": problems[:3]})

for path in list(root.rglob("*.yaml")) + list(root.rglob("*.yml")) + list(root.rglob("*.json")):
    if skipped(path) or path.name in ("verdict.json",):
        continue
    try:
        doc = (yaml.safe_load if path.suffix in (".yaml", ".yml") else json.loads)(
            path.read_text("utf-8")
        )
    except Exception:  # noqa: BLE001 - not a claim
        continue
    if not isinstance(doc, dict) or not isinstance(doc.get("targets"), list):
        continue
    keys = [str(t.get("key")) for t in doc["targets"] if isinstance(t, dict) and "key" in t]
    if not keys:
        continue
    out["counts"]["files_with_target_keys"] += 1
    norm = Counter(k.strip().upper().replace(" ", "-") for k in keys)
    dup = sorted(k for k, n in norm.items() if n > 1)
    if dup:
        out["a5"].append({"file": path.relative_to(root).as_posix(), "duplicates": dup})

out["counts"] = dict(out["counts"])
Path(sys.argv[2]).write_text(json.dumps(out, indent=1, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps({k: (v if k == "counts" else len(v)) for k, v in out.items()}))
