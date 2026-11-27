"""The metered launcher of v0.5.13, version 2: launch_v1.py, unchanged, with one stricter check.

    .venv/Scripts/python.exe -I -B docs/validation/v0.5.13/tools/launch_v2.py <unit spec> [...]

It runs ``launch_v1.py`` (a new file, not a revision of it), with two changes, neither of which
touches how a unit runs or how it is metered:
- **the order proof** accepts only a receipt of ``order_proof_v2.py``
  (``order-proofs/<manifest blob SHA-256>.v2.json``, schema ``refute-v0513-order-proof-2``), whose
  checks require the CI run to be completed, its ``plan`` job to have succeeded, and at least one
  other job, all ``skipped``. Version 1's receipt for ID-BEFORE passed vacuously (only ``plan``,
  queued) and is not accepted.
- every ``before`` entry names this launcher and carries its SHA-256 and that of
  ``order_proof_v2.py``.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("launch_v1", _HERE / "launch_v1.py")
v1 = importlib.util.module_from_spec(_spec)
sys.modules["launch_v1"] = v1
_spec.loader.exec_module(v1)

SCHEMA = "refute-v0513-order-proof-2"


def check_order_proof(spec: dict) -> dict | None:
    manifest = spec.get("order_proof")
    if not manifest:
        return None
    blob = v1.committed_sha256(manifest)
    receipt = v1.RECEIPTS / f"{blob}.v2.json"
    if not receipt.exists():
        raise SystemExit(f"refused: no version-2 order-proof receipt for {manifest} ({blob[:12]})")
    r = json.loads(receipt.read_text(encoding="utf-8"))
    if r.get("schema") != SCHEMA or not r.get("passed") or r.get("manifest_sha256") != blob:
        raise SystemExit(f"refused: the order-proof receipt for {manifest} did not pass")
    return {
        "manifest": manifest,
        "manifest_sha256": blob,
        "receipt": receipt.name,
        "evidence_commit": r.get("evidence_commit"),
        "ci_run_id": r.get("ci_run_id"),
    }


def main() -> int:
    me = Path(__file__).resolve().relative_to(v1.ROOT).as_posix()
    proof = "docs/validation/v0.5.13/tools/order_proof_v2.py"
    ids = {me: v1.committed_sha256(me), proof: v1.committed_sha256(proof)}
    v1.check_order_proof = check_order_proof
    inner = v1.append_log

    def tagged(entry: dict) -> None:
        if entry.get("event") == "before":
            entry = dict(entry)
            entry["launcher"] = "launch_v2.py"
            entry["identity_sha256"] = {**ids, **entry.get("identity_sha256", {})}
        inner(entry)

    v1.append_log = tagged
    return v1.main()


if __name__ == "__main__":
    sys.exit(main())
