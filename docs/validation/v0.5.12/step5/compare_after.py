"""v0.5.12 step 5: the "after" proofs equal the "before" ones (charter, step 5; criterion 4).

    launch_v3 unit compare-after: {python} -I -B docs/validation/v0.5.12/step5/compare_after.py

- **Golden:** ``step0/golden-before.json`` against ``step0/golden-after.json``.
- **Claim hashes:** ``step0/claim-hashes-before-host.json`` against
  ``step5/claim-hashes-after.json``.

Each pair's ``payload`` is compared byte for byte, as canonical JSON (sorted keys); the
``provenance`` fields (head, versions, script hash) are excluded. The golden payload must list
no error output. The claim payload's only error must be the one known since step 0
(``calibration/v0.5/deviation/claim.generated.yaml``: targets attachment not found). It exits 1
otherwise. Identity verification, not a rerun (charter, section 4).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STEP0 = HERE.parent / "step0"
KNOWN_ERROR = "calibration/v0.5/deviation/claim.generated.yaml"


def payload(path: Path) -> bytes:
    doc = json.loads(path.read_text(encoding="utf-8"))
    return json.dumps(doc["payload"], sort_keys=True, separators=(",", ":")).encode()


def main() -> int:
    pairs = {
        "golden": (STEP0 / "golden-before.json", STEP0 / "golden-after.json"),
        "claim_hashes": (STEP0 / "claim-hashes-before-host.json", HERE / "claim-hashes-after.json"),
    }
    out, ok = {}, True
    for name, (before, after) in pairs.items():
        same = payload(before) == payload(after)
        out[name] = {"before": before.name, "after": after.name, "payload_equal": same}
        ok &= same
    golden = json.loads(pairs["golden"][1].read_text(encoding="utf-8"))["payload"]
    out["golden"]["error_outputs"] = golden["error_outputs"]
    ok &= golden["error_outputs"] == []
    claims = json.loads(pairs["claim_hashes"][1].read_text(encoding="utf-8"))["payload"]["claims"]
    errors = sorted(k for k, v in claims.items() if str(v).startswith("ERROR"))
    out["claim_hashes"].update({"processed": len(claims), "errors": errors})
    ok &= errors == [KNOWN_ERROR]
    out["passed"] = ok
    print(json.dumps(out))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
