"""v0.5.2 stage 2: the inventory of T3b's amended sampling frame (the maintainer's decision of
2026-11-08, #216, item 5): how many TOI false positives each catalog adds, as counts only. No
target is selected, no draw is made, no light curve is read, and no row or identifier of a catalog
leaves this script. It uses the frozen v0.5 inputs; the TOI table is refreshed at the selection
step, a stop. ``method_status: not_validated``.

With the argument ``refreshed`` it reads the TOI table of ``toi-fetch.json`` (the maintainer's
decision of 2026-11-09, item 3 (a)) and writes ``t3b-inventory-r2.json``; the other inputs stay
frozen. The T10K copies were deleted after that run (item 4); a new run needs ``fetch_t10k.py``
first.

Frame: a TOI false positive (the v0.5 rule, ``selection.fp_pool``, without already known targets)
that is catalogued, by TIC, in TESS-EB or in the vetted T10K tables (3 and 4), or that lies within
``GAIA_RADII`` arcsec of a Gaia DR3 ``vari_eclipsing_binary`` source. Period consistency, reported
beside each count and not applied to TESS-EB: the catalog period within 1 % of the TOI period, of
its double or of its half. Gaia's frequency is taken as one over its period, and its halves and
doubles are covered by the same test.

Usage (from the project root): ``.venv/Scripts/python.exe <this file>``; writes
``t3b-inventory.json``.
"""

from __future__ import annotations

import csv
import io
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
INPUTS = ROOT / ".cache/v05/inputs-attempts/attempt-01"
SELECTION = ROOT / "calibration/v0.5/selection/selection.json"
FETCH = HERE / "t10k-fetch.json"
GAIA_RADII = (2.0, 21.0)
TOLERANCE = 0.01
NEED_ACCEPT = 11


def t10k_periods() -> dict[int, float]:
    """TIC to period from the two vetted tables (fixed-width: TIC in bytes 1-10; ``Per`` in bytes
    45-53 of Table 3, ``Per-TESS`` in bytes 38-46 of Table 4)."""
    doc = json.loads(FETCH.read_text("utf-8"))
    out: dict[int, float] = {}
    for key, (lo, hi) in {"table3": (44, 53), "table4": (37, 46)}.items():
        row = doc["files"][key]
        name = row["url"].rsplit("/", 1)[1]
        text = (ROOT / ".cache/v052/t10k" / row["sha256"] / name).read_text("utf-8")
        for line in text.splitlines():
            head = line[:10].strip()
            if head.isdigit() and len(line) >= hi:
                out[int(head)] = float(line[lo:hi])
    return out


def consistent(toi_period: float, other: float) -> bool:
    if not (np.isfinite(other) and other > 0):
        return False
    return any(abs(other / (toi_period * k) - 1.0) <= TOLERANCE for k in (0.5, 1.0, 2.0))


def toi_coordinates(rows, tics):
    from astropy.coordinates import SkyCoord

    from refute.packs.tess.discover import selection as sel

    out = {}
    for r in rows:
        tic = sel.parse_tic(r.get("TIC ID"))
        if tic in tics:
            c = SkyCoord(r["RA"], r["Dec"], unit=("hourangle", "deg"))
            out[tic] = (float(c.ra.deg), float(c.dec.deg), float(r["Period (days)"]))
    return out


def gaia_matches(coords, radius):
    """For each TIC, the frequencies of the Gaia EB sources within the radius of the TOI table's
    position: a position-only proxy. The final rule (an established TIC-to-Gaia association, at the
    selection stop) can only remove members from these counts."""
    from scipy.spatial import cKDTree

    from refute.packs.tess.discover import selection as sel

    text = (INPUTS / "gaia_dr3_eb.csv").read_text("utf-8")
    table = np.loadtxt(io.StringIO(text.partition("\n")[2]), delimiter=",", usecols=(1, 2, 3))
    tree = cKDTree(sel._unit(table[:, 0], table[:, 1]))
    chord = 2.0 * np.sin(np.radians(radius / 3600.0) / 2.0)
    tics = sorted(coords)
    points = np.array([coords[t][:2] for t in tics])
    hits = tree.query_ball_point(sel._unit(points[:, 0], points[:, 1]), r=chord)
    return {t: table[h, 2] for t, h in zip(tics, hits, strict=True) if len(h)}


def main(toi_path: Path = INPUTS / "toi.csv", out_name: str = "t3b-inventory.json", note: str = ""):
    from scipy import stats

    from refute.packs.tess.calib05 import c3select
    from refute.packs.tess.calib05.values import C3
    from refute.packs.tess.discover import selection as sel

    csv.field_size_limit(10_000_000)
    toi = sel.toi_rows(toi_path.read_bytes())
    planets = sel.pscomppars_rows((INPUTS / "pscomppars.csv").read_bytes())
    eb = sel.tess_eb_tics((INPUTS / "tess_eb.tsv").read_bytes())
    planet_tics = {t for t in (sel.parse_tic(r.get("tic_id")) for r in planets) if t}
    known = set(c3select.known_targets(ROOT))
    fp = {p.tic_id for p in sel.fp_pool(toi, planet_tics, C3.fp_min_depth_ppm)} - known
    walk = json.loads(SELECTION.read_text("utf-8"))["pools"]["false_positive"]["walk"]
    walked = {int(d["tic_id"]) for d in walk["decisions"]}
    accepted = len(walk["accepted"])
    coords = toi_coordinates(toi, fp)
    t10k = t10k_periods()
    in_eb = fp & eb
    in_t10k = (fp & set(t10k)) - eb
    t10k_ok = {t for t in in_t10k if consistent(coords[t][2], t10k[t])}
    toi_tics = {t for t in (sel.parse_tic(r.get("TIC ID")) for r in toi) if t}
    hosts = toi_tics & set(t10k)
    dispositions: dict = {}
    for r in toi:
        if sel.parse_tic(r.get("TIC ID")) in hosts:
            name = (r.get("TFOPWG Disposition") or "blank").strip() or "blank"
            dispositions[name] = dispositions.get(name, 0) + 1
    doc = {
        "label": "inventory of the amended T3b frame; counts only; it selects nothing",
        "method_status": "not_validated",
        "toi_table": note or "the frozen v0.5 table (of 2026-11-04); refreshed at the selection",
        "toi_false_positives": len(fp),
        "v05_walk": {"walked": len(walked), "accepted": accepted},
        "tess_eb": {"members": len(in_eb), "never_walked": len(in_eb - walked)},
        "t10k_vetted_rows": len(t10k),
        "t10k_added_beyond_tess_eb": len(in_t10k),
        "t10k_added_period_consistent": len(t10k_ok),
        "t10k_toi_hosts": {
            "stars": len(hosts),
            "toi_rows_by_tfopwg_disposition": dispositions,
            "false_positives_among_them": len(hosts & fp),
            "in_tess_eb": len(hosts & eb),
        },
        "gaia": {},
    }
    # the eligible set is the union of the memberships that qualify on their own: a T10K member
    # whose period disagrees does not hide a Gaia membership that qualifies
    qualified = in_eb | t10k_ok
    for radius in GAIA_RADII:
        matches = gaia_matches(coords, radius)
        added = set(matches) - qualified
        unique = {t for t in added if len(matches[t]) == 1}
        ok = {
            t for t in unique if matches[t][0] > 0 and consistent(coords[t][2], 1 / matches[t][0])
        }
        doc["gaia"][f"{radius:g}_arcsec"] = {
            "matched": len(matches),
            "added_beyond_the_qualified_tess_eb_and_t10k": len(added),
            "added_with_exactly_one_gaia_eb": len(unique),
            "added_unique_and_period_consistent": len(ok),
            "identity": "position-only proxy; the established association can only remove members",
        }
    rate = accepted / len(walked)
    rejected = len(walked) - accepted
    lo, hi = stats.beta.ppf([0.025, 0.975], [accepted, accepted + 1], [rejected + 1, rejected])
    never = len(in_eb - walked)
    scenarios = {
        "tess_eb_only": never,
        "with_t10k_period_consistent": never + len(t10k_ok),
        "with_t10k_all": never + len(in_t10k),
    }
    doc["expected_acceptances_at_the_v05_yield"] = {
        "yield": rate,
        "yield_95_interval": [float(lo), float(hi)],
        "needed": NEED_ACCEPT,
        "note": "the yield of a TESS-EB walk, not established for the other catalogs",
        "scenarios": {
            k: {"never_walked_stars": v, "expected": v * rate, "low": v * lo, "high": v * hi}
            for k, v in scenarios.items()
        },
    }
    (HERE / out_name).write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n", "utf-8")
    print(json.dumps(doc, indent=1, sort_keys=True))


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT / "src"))
    if sys.argv[1:] == ["refreshed"]:
        fetched = json.loads((HERE / "toi-fetch.json").read_text("utf-8"))
        main(
            ROOT / ".cache/v052/toi" / fetched["sha256"] / "toi.csv",
            "t3b-inventory-r2.json",
            f"toi-fetch.json, retrieved {fetched['retrieved_utc']}; other inputs frozen",
        )
    else:
        main()
