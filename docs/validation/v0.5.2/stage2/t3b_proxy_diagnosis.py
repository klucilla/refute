"""v0.5.2 stage 2: why the proxy of ``t3b_alternatives.py`` rejected 4 of the 11 stars that v0.5's
walk accepted (the maintainer's decision of 2026-11-09, #216, item 3). Counts and clause names
only; the stars are named by their position in v0.5's walk (already public in
``calibration/v0.5/selection/selection.json``). No new star is read, drawn or selected.
``method_status: not_validated``.

For every accepted star the proxy's clauses (read from the refreshed TOI table's columns) are put
next to the values the walk measured (TIC and MAST, the decision's ``evidence``), so that each
rejection is traced to a column that does not carry what the domain rule reads.

Usage: ``.venv/Scripts/python.exe <this file>``; writes ``t3b-proxy-diagnosis.json``.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(HERE))
import t3b_alternatives as alt  # noqa: E402

SELECTION = ROOT / "calibration/v0.5/selection/selection.json"


def clauses(row: dict[str, str]) -> dict:
    sectors = sorted({int(s) for s in re.findall(r"\d+", row.get("Sectors") or "")})
    logg = alt.number(row.get("Stellar log(g) (cm/s^2)"))
    radius = alt.number(row.get("Stellar Radius (R_Sun)"))
    radius_err = alt.number(row.get("Stellar Radius (R_Sun) err"))
    teff = alt.number(row.get("Stellar Eff Temp (K)"))
    tmag = alt.number(row.get("TESS Mag"))
    return {
        "values": {
            "sectors": len(sectors),
            "sector_span": (sectors[-1] - sectors[0]) if sectors else None,
            "logg": logg,
            "radius": radius,
            "radius_err": radius_err,
            "teff": teff,
            "tmag": tmag,
        },
        "fails": [
            name
            for name, ok in (
                ("sectors_at_least_3", len(sectors) >= 3),
                ("sector_span_at_least_12", bool(sectors) and sectors[-1] - sectors[0] >= 12),
                ("logg_at_least_4", logg is not None and logg >= 4.0),
                (
                    "radius_rel_err_at_most_0.25",
                    radius is not None
                    and radius > 0
                    and radius_err is not None
                    and radius_err / radius <= 0.25,
                ),  # fmt: skip
                ("teff_3200_to_7000", teff is not None and 3200.0 <= teff <= 7000.0),
                ("tmag_8_to_12", tmag is not None and 8.0 <= tmag <= 12.0),
            )
            if not ok
        ],
    }


def main() -> None:
    from refute.packs.tess.discover import selection as sel

    fetched = json.loads((HERE / "toi-fetch.json").read_text("utf-8"))
    toi = sel.toi_rows(
        (ROOT / ".cache/v052/toi" / fetched["sha256"] / "toi.csv").read_bytes()
    )  # fmt: skip
    rows_of: dict[int, list] = {}
    for r in toi:
        tic = sel.parse_tic(r.get("TIC ID") or r.get("tic_id"))
        if tic:
            rows_of.setdefault(tic, []).append(r)
    walk = json.loads(SELECTION.read_text("utf-8"))["pools"]["false_positive"]["walk"]
    stars = []
    for d in walk["decisions"]:
        if d["reason"] != "accepted":
            continue
        ev = d["evidence"]
        toi_rows = rows_of.get(int(d["tic_id"]), [])
        per_row = [clauses(r) for r in toi_rows]
        stars.append(
            {
                "walk_position": d["position"],
                "toi_rows": len(toi_rows),
                "proxy_passes_on_some_row": any(not c["fails"] for c in per_row),
                "proxy_by_row": per_row,
                "walk_measured": {
                    "light_curve_sectors": len(ev["light_curve_sectors"]),
                    "light_curve_span_days": ev["light_curve_span_days"],
                    "light_curve_years": len(ev["light_curve_years"]),
                    "tic_logg": ev["tic_logg"],
                    "tic_rad_rel_err": ev["tic_e_rad"] / ev["tic_rad"],
                    "tic_Teff": ev["tic_Teff"],
                    "tic_Tmag": ev["tic_Tmag"],
                },
            }
        )
    rejected = [s for s in stars if not s["proxy_passes_on_some_row"]]
    counts: dict[str, int] = {}
    for s in rejected:
        for name in {f for c in s["proxy_by_row"] for f in c["fails"]}:
            counts[name] = counts.get(name, 0) + 1
    doc = {
        "label": "why the T3b proxy rejected accepted stars; it decides nothing",
        "method_status": "not_validated",
        "accepted": len(stars),
        "rejected_by_the_proxy": len(rejected),
        "failing_clauses_among_rejected": counts,
        "stars": stars,
    }
    (HERE / "t3b-proxy-diagnosis.json").write_text(
        json.dumps(doc, indent=1, sort_keys=True) + "\n", "utf-8"
    )
    for s in rejected:
        print(
            s["walk_position"],
            [c["fails"] for c in s["proxy_by_row"]],
            s["proxy_by_row"][0]["values"] if s["proxy_by_row"] else None,
            s["walk_measured"],
        )  # noqa: E501
    print(counts)


if __name__ == "__main__":
    main()
