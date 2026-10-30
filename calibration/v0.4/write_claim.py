"""Write the v0.4 pilot's claim (calibration/v0.4/PROTOCOL.md, section 12, step 3).

A wrapper: it calls ``refute.packs.tess.discover.steps.claim_step``, so every line it executes is
inside the lock's code hash. Run once, after the selection output is committed:

    .venv/Scripts/python.exe calibration/v0.4/write_claim.py

It writes calibration/v0.4/claim.yaml, eb_catalog.csv and eb_catalog_scan.json, and refuses if
any of them exists. No network access.
"""

from __future__ import annotations

import sys
from pathlib import Path

from refute.packs.tess.discover import steps

ROOT = Path(__file__).resolve().parent.parent.parent


def main() -> int:
    out = steps.claim_step(ROOT)
    scan = out["scan"]
    plan = out["claim"]["test_plan"]["discovery"]
    print(
        f"claim {out['claim']['id']}: max_sector {plan['max_sector']}; "
        f"{len(scan['per_target'])} targets; {scan['rows']} catalog rows within "
        f"{scan['radius_arcsec']:g} arcsec"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
