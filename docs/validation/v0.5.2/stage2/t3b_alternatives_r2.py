"""v0.5.2 stage 2: T3b's counts again, with the proxy corrected (the maintainer's decision of
2026-11-09, #216, item 3). Counts only, as in ``t3b_alternatives.py``: no draw, no light curve, no
identifier leaves this script, no definition is adopted. ``method_status: not_validated``.

**Why the first proxy rejected 4 of the 11 accepted stars** (``t3b_proxy_diagnosis.py``): three
failed D-1/D-2 because the TOI table's ``Sectors`` column lists the sectors of the TOI's alert, not
every sector with a 120-s light curve (one sector each, against 3 to 6 measured by the walk); one
failed D-4 because the TOI table's stellar log g (3.9) is not the TIC value the walk read (4.02).

**The correction.** Sectors come from TESS's 120-s target lists (S001 to S107, the copies of
v0.4's attempt 4, retrieved 2026-10-29 from https://tess.mit.edu/public/target_lists/), the
cadence D-1 counts; D-2's span is approximated by sector numbers (at least 11 apart, about 300
days) and Tmag (D-7) is the list's own TIC value. The TOI table's stellar log g, radius and Teff
are not TIC values, so D-4 to D-6 are no longer applied by the proxy; every clause is checked
against what the walk measured on the 41 walked stars (``proxy_check`` in the output). The proxy
still misses D-3, D-8 and D-2's calendar years, and still must never serve as a domain exclusion.

Usage: ``.venv/Scripts/python.exe <this file>``; writes ``t3b-alternatives-r2.json`` (the first
record, ``t3b-alternatives.json``, stays as it was).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(HERE))
import t3b_alternatives as alt  # noqa: E402

LISTS = ROOT / ".cache/v04/inputs-attempts/attempt-04/lists"
SELECTION = ROOT / "calibration/v0.5/selection/selection.json"
MIN_SECTORS = 3
MIN_SECTOR_GAP = 11  # 11 sectors of about 27.4 days: about 300 days between starts


def list_sectors() -> tuple[dict[int, list[int]], dict[int, float], list[int]]:
    from refute.packs.tess.discover import selection as sel

    sectors: dict[int, list[int]] = {}
    tmag: dict[int, float] = {}
    numbers = []
    for path in sorted(LISTS.glob("all_targets_S*_v*.csv")):
        sector = int(path.name.split("_S")[1][:3])
        numbers.append(sector)
        for row in sel.parse_target_list(path.read_text("utf-8")):
            sectors.setdefault(row.tic_id, []).append(sector)
            if row.tmag is not None and row.tic_id not in tmag:
                tmag[row.tic_id] = row.tmag
    return {t: sorted(set(s)) for t, s in sectors.items()}, tmag, sorted(set(numbers))


def main() -> None:
    from refute.packs.tess.discover import selection as sel

    sectors_of, tmag_of, numbers = list_sectors()

    def clauses(tic: int) -> dict[str, bool]:
        s = sectors_of.get(tic, [])
        tmag = tmag_of.get(tic)
        return {
            "d1_sectors": len(s) >= MIN_SECTORS,
            "d2_span": bool(s) and s[-1] - s[0] >= MIN_SECTOR_GAP,
            "d7_tmag": tmag is not None and 8.0 <= tmag <= 12.0,
        }

    def proxy(row: dict[str, str]) -> bool:
        tic = sel.parse_tic(row.get("TIC ID") or row.get("tic_id"))
        return bool(tic) and all(clauses(tic).values())

    # each clause against the walk's own measurement, on the walked stars that reached it
    walk = json.loads(SELECTION.read_text("utf-8"))["pools"]["false_positive"]["walk"]
    check: dict[str, dict[str, int]] = {}
    accepted_rejected = 0
    for d in walk["decisions"]:
        ev = d.get("evidence") or {}
        mine = clauses(int(d["tic_id"]))
        if d["reason"] == "accepted" and not all(mine.values()):
            accepted_rejected += 1
        truth = {}
        if "light_curve_sectors" in ev:
            truth["d1_sectors"] = len(ev["light_curve_sectors"]) >= MIN_SECTORS
            truth["d2_span"] = len(ev["light_curve_years"]) >= 2 and (
                ev["light_curve_span_days"] >= 300.0
            )
        if ev.get("tic_Tmag") is not None:
            truth["d7_tmag"] = 8.0 <= ev["tic_Tmag"] <= 12.0
        for name, value in truth.items():
            row = check.setdefault(name, {"agree": 0, "proxy_passes_walk_fails": 0,
                                          "proxy_fails_walk_passes": 0})  # fmt: skip
            if mine[name] == value:
                row["agree"] += 1
            elif mine[name]:
                row["proxy_passes_walk_fails"] += 1
            else:
                row["proxy_fails_walk_passes"] += 1
    gaps = [
        s[-1] - s[0]
        for s in (sectors_of.get(int(d["tic_id"]), []) for d in walk["decisions"])
        if s
    ]  # fmt: skip
    extra = {
        "proxy": {
            "version": "r2: 120-s target lists for D-1, D-2 (span by sector number) and D-7",
            "target_lists": f"{LISTS.relative_to(ROOT).as_posix()}, sectors {numbers[0]} to "
            f"{numbers[-1]} ({len(numbers)} lists), retrieved 2026-10-29",
            "accepted_stars_rejected": accepted_rejected,
            "proxy_check_against_the_walk": check,
            "limits": {
                "development_evidence": "the same 41 walked outcomes informed the correction and "
                "its check: agreement on them is not independent validation",
                "d2_boundary_untested": "every walked star passes D-2; the smallest sector gap "
                f"among them is {min(gaps)}, so the 11-sector boundary is never tested, and "
                "sector numbers are not elapsed time (sector lengths vary) nor calendar years",
                "d7_first_list_magnitude": "Tmag is the first list's value, not the walk's exact "
                "TIC value; decisions agree on all 41, boundary cases can differ",
                "d1_lists_not_products": "list membership is not the same as an available SPOC "
                "120-s product; the sector sets agree on all 41",
                "zero_rate_is_a_scenario": "0 of 16 walked stars failing the proxy were accepted: "
                "an observed rate, not a zero probability; the scenarios assume it transports",
            },
        },
        "first_record": "t3b-alternatives.json (the first proxy, kept as it was)",
    }
    alt.main(proxy=proxy, out_name="t3b-alternatives-r2.json", extra=extra)


if __name__ == "__main__":
    main()
