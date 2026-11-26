"""v0.5.12, the resolved hash of every committed claim (charter, steps 0 and 5; criterion 4),
"before" at the approval commit's ``src/`` and "after" at the seal. A new copy of v0.5.11's
``claim_hashes.py`` (rule (c)); identity verification, not a rerun (charter, section 4).

    launch_v2 unit claim-hashes:
        {python} -I -B docs/validation/v0.5.12/tools/claim_hashes.py <label>

Every tracked YAML file that is a mapping with ``pack`` and ``kind`` is loaded with
``refute.core.claim.load_claim``; its ``LoadedClaim.sha256()`` is recorded, or the error's type and
message. The record ``claim-hashes-<label>.json`` goes to the run's out folder, and the launcher
copies it to ``docs/validation/v0.5.12/step0/``. The payload is ``claims``; ``provenance`` is HEAD
and the script's SHA-256.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import yaml

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
    # imported here, not at the top: ruff sorts it as first-party outside the container and as
    # third-party inside it, so a top-level block could not satisfy both
    from refute.core.claim import load_claim

    out = {}
    for rel in claims():
        try:
            out[rel] = load_claim(ROOT / rel).sha256()
        except Exception as exc:  # noqa: BLE001 - the failure is recorded and compared too
            out[rel] = f"ERROR {type(exc).__name__}: {exc}"
    return out


def main() -> int:
    label = sys.argv[1]
    if label not in ("before", "after"):
        raise SystemExit("label must be before or after")
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, check=True, text=True
    ).stdout.strip()
    doc = {
        "labels": ["exploratory", "method_status: not_validated"],
        "payload": {"claims": hashes()},
        "provenance": {
            "head": head,
            "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        },
    }
    out = Path(os.environ["REFUTE_RUN_OUT"]) / f"claim-hashes-{label}.json"
    out.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8", newline="\n")
    claims_ = doc["payload"]["claims"]
    ok = sum(not v.startswith("ERROR") for v in claims_.values())
    print(json.dumps({"claims": len(claims_), "loaded": ok}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
