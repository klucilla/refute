"""v0.5.11, proof (ii) of the charter's section 2.3: the resolved hash of every committed claim,
before and after the `src/` change.

    .venv/Scripts/python.exe -I -B docs/validation/v0.5.11/tools/claim_hashes.py <label>

Every tracked YAML file that is a mapping with ``pack`` and ``kind`` is loaded with
``refute.core.claim.load_claim``. Its ``LoadedClaim.sha256()`` is recorded, or the error's type
and message if it does not load. Writes docs/validation/v0.5.11/step1/claim-hashes-<label>.json.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import yaml

from refute.core.claim import load_claim

ROOT = Path(__file__).resolve().parents[4]


def claims() -> list[str]:
    out = subprocess.run(
        ["git", "ls-files", "*.yaml", "*.yml"], cwd=ROOT, capture_output=True, check=True, text=True
    )
    found = []
    for rel in out.stdout.splitlines():
        try:
            data = yaml.safe_load((ROOT / rel).read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001 - not a claim if it is not readable YAML
            continue
        if isinstance(data, dict) and "pack" in data and "kind" in data:
            found.append(rel)
    return sorted(found)


def hashes() -> dict[str, str]:
    out = {}
    for rel in claims():
        try:
            out[rel] = load_claim(ROOT / rel).sha256()
        except Exception as exc:  # noqa: BLE001 - the failure is recorded and compared too
            out[rel] = f"ERROR {type(exc).__name__}: {exc}"
    return out


def main() -> int:
    label = sys.argv[1]
    # "after-fix": the record after correction 1's src/ commit (#218 comment 7162573384, item 2)
    if label not in ("before", "after", "after-fix"):
        raise SystemExit("label must be before, after or after-fix")
    doc = {
        "labels": ["exploratory", "method_status: not_validated"],
        "head": subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, check=True, text=True
        ).stdout.strip(),
        "claims": hashes(),
    }
    out = ROOT / "docs" / "validation" / "v0.5.11" / "step1" / f"claim-hashes-{label}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8", newline="\n")
    ok = sum(not v.startswith("ERROR") for v in doc["claims"].values())
    print(json.dumps({"claims": len(doc["claims"]), "loaded": ok}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
