"""Item 1 (b) of the maintainer's decision of 2026-11-08 (#216): how many stars crossing the TOI
false positives with another catalog could add to T3b's pool, as a bound. It reads the frozen v0.5
pool inputs only: **no catalog is downloaded or read**, and only counts leave this script (the
TESS-EB rows are never printed). It decides nothing.

Usage (from the project root): ``.venv/Scripts/python.exe <this file>``; writes ``t3b-pool.json``.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
INPUTS_DIR = ROOT / ".cache/v05/inputs-attempts/attempt-01"
SELECTION = ROOT / "calibration/v0.5/selection/selection.json"
NEED_WALK = 41
NEED_ACCEPT = 11


def main():
    from refute.packs.tess.calib05 import c3select
    from refute.packs.tess.calib05.values import C3
    from refute.packs.tess.discover import selection as sel

    toi = sel.toi_rows((INPUTS_DIR / "toi.csv").read_bytes())
    pscomppars = sel.pscomppars_rows((INPUTS_DIR / "pscomppars.csv").read_bytes())
    eb = sel.tess_eb_tics((INPUTS_DIR / "tess_eb.tsv").read_bytes())
    planet_tics = {t for t in (sel.parse_tic(r.get("tic_id")) for r in pscomppars) if t}
    known = set(c3select.known_targets(ROOT))
    fp_all = sel.fp_pool(toi, planet_tics, C3.fp_min_depth_ppm)
    fp = {p.tic_id for p in fp_all} - known
    walk = json.loads(SELECTION.read_text("utf-8"))["pools"]["false_positive"]["walk"]
    walked = {int(d["tic_id"]) for d in walk["decisions"]}
    accepted = {int(t) for t in walk["accepted"]}
    in_eb = fp & eb
    outside_eb = fp - eb
    rate = len(accepted) / len(walked)
    never = in_eb - walked
    doc = {
        "label": "reading of frozen v0.5 inputs; no new catalog was read; it decides nothing",
        "toi_false_positives_with_the_depth_rule_excluding_known_targets": len(fp),
        "of_them_in_tess_eb_the_v05_pool": len(in_eb),
        "of_them_outside_tess_eb": len(outside_eb),
        "the_v05_pool_never_walked": len(never),
        "acceptance_rate_on_the_v05_walk": rate,
        "expected_acceptances_from_the_never_walked": len(never) * rate,
        "acceptances_needed_for_one_confirmation": NEED_ACCEPT,
        "acceptances_short": max(0.0, NEED_ACCEPT - len(never) * rate),
        "upper_bound_on_new_stars_from_any_catalog_cross_match": len(outside_eb),
        "expected_acceptances_if_every_one_of_them_were_catalogued": len(outside_eb) * rate,
        "share_of_them_that_must_be_catalogued_for_one_confirmation": (
            max(0.0, NEED_ACCEPT - len(never) * rate) / (len(outside_eb) * rate)
            if outside_eb
            else None
        ),
        "note": "the number actually in the TESS Ten Thousand Catalog is unknown without its "
        "table, which is not read before the maintainer's approval; the frozen TOI table "
        "is v0.5's (retrieved 2026-11-04)",
    }
    (HERE / "t3b-pool.json").write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n", "utf-8")
    print(json.dumps(doc, indent=1, sort_keys=True))


if __name__ == "__main__":
    main()
