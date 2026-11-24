"""v0.5.10, part (b): route (e) feasibility, the predicted transit windows in new TESS sectors.
Exploratory; public metadata only, no light curve or pixel read.

**New sectors:** 110 to 120. Sector 110 began on 2026-10-31 and its data are not public on
2026-11-24. Their dates and per-camera pointings (RA, Dec, roll) are read from the sector pages
https://tess.mit.edu/observations/sector-<N>/ on 2026-11-24.

**Lists:**
- eumemic/exoplanets `candidates/predictions.csv` at commit e2eee928 (2026-11-04), one row per
  predicted transit, with its 1-sigma timing in minutes;
- the ExoFOP CTOI table (download of 2026-11-24): epoch and period with their errors;
- Refute's own candidates: the 3 promoted cases of the v0.4 pilot (calibration/v0.4/results/
  ledger.jsonl, their stage-1 candidate ephemeris).

**On silicon (a committed geometry check with a declared margin; tess-point is not run):**
- each star is projected gnomonically about each camera's centre and rotated by the roll, with
  both sign conventions of the roll;
- it is on silicon when |x| and |y| are below 12 degrees (the camera's 24-degree field) by more
  than 0.5 degree in both conventions;
- within 0.5 degree of an edge or of a CCD gap (the axes, within 0.25 degree), or when the two
  conventions disagree, it is "unknown". Otherwise it is off.

**Products:** FFIs cover every star on silicon. The 2-minute target lists of these sectors were not
found on the sector pages, so 2-minute data is "not determined". As a proxy only, the script records
whether the star had SPOC 2-minute data in any earlier sector (MAST).

Writes route-e.json. The per-target table stays under .cache/v0510/route-e/.
"""

from __future__ import annotations

import csv
import html
import json
import math
import re
import statistics
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from census_common import LABEL, fnum, mast_targets, now  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
WORK = ROOT / ".cache/v0510/route-e"
SECTORS = range(110, 121)
HALF, MARGIN, GAP = 12.0, 0.5, 0.25
JD_UNIX0 = 2440587.5


def jd(date: datetime) -> float:
    return date.timestamp() / 86400.0 + JD_UNIX0


def sector_pages() -> dict[int, dict]:
    out = {}
    for s in SECTORS:
        text = (WORK / f"sector-{s}.html").read_text("utf-8", errors="replace")
        plain = html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", text)))
        cams = {}
        for m in re.finditer(r"Camera (\d) (-?[\d.]+) (-?[\d.]+) (-?[\d.]+) ", plain):
            cams.setdefault(int(m.group(1)), tuple(float(m.group(i)) for i in (2, 3, 4)))
        dm = re.search(
            r"extend from ([A-Z][a-z]+ \d{1,2})(?:, (\d{4}))? "
            r"through ([A-Z][a-z]+ \d{1,2}), (\d{4})",
            plain,
        )
        if len(cams) != 4 or not dm:
            raise SystemExit(f"sector {s}: pointings or dates not found on its page")
        end = datetime.strptime(f"{dm.group(3)}, {dm.group(4)}", "%B %d, %Y")
        start = datetime.strptime(f"{dm.group(1)}, {dm.group(2) or dm.group(4)}", "%B %d, %Y")
        if start > end:
            start = start.replace(year=start.year - 1)
        dates = (start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))
        out[s] = {
            "cameras": cams,
            "start": dates[0],
            "end": dates[1],
            "jd_start": jd(start),
            "jd_end": jd(end) + 1.0,
        }
    return out


def project(ra, dec, ra0, dec0):
    r, d, r0, d0 = map(math.radians, (ra, dec, ra0, dec0))
    cosc = math.sin(d0) * math.sin(d) + math.cos(d0) * math.cos(d) * math.cos(r - r0)
    if cosc <= 0:
        return None
    x = math.cos(d) * math.sin(r - r0) / cosc
    y = (math.cos(d0) * math.sin(d) - math.sin(d0) * math.cos(d) * math.cos(r - r0)) / cosc
    return math.degrees(math.atan(x)), math.degrees(math.atan(y))


def on_silicon(ra, dec, sector) -> str:
    states = []
    for sign in (1, -1):
        best = "off"
        for ra0, dec0, roll in sector["cameras"].values():
            p = project(ra, dec, ra0, dec0)
            if p is None:
                continue
            a = math.radians(sign * roll)
            x = p[0] * math.cos(a) - p[1] * math.sin(a)
            y = p[0] * math.sin(a) + p[1] * math.cos(a)
            m = max(abs(x), abs(y))
            if m < HALF - MARGIN and min(abs(x), abs(y)) > GAP:
                best = "yes"
                break
            if m < HALF + MARGIN:
                best = "unknown"
        states.append(best)
    if states[0] == states[1]:
        return states[0]
    return "unknown"


def transits(t0, period, sigma0, sigma_p, start, end):
    """Predicted mid-times in [start, end] (JD) and each one's 1-sigma in minutes."""
    if not (t0 and period and period > 0):
        return []
    n0 = math.ceil((start - t0) / period)
    out = []
    n = n0
    while t0 + n * period <= end:
        sig = math.hypot(sigma0 or 0.0, n * (sigma_p or 0.0)) * 1440.0
        out.append((t0 + n * period, sig))
        n += 1
    return out


def load_lists() -> dict[str, list[dict]]:
    lists: dict[str, list[dict]] = {}
    eu = defaultdict(list)
    for r in csv.DictReader((WORK / "eumemic-predictions.csv").open(encoding="utf-8")):
        eu[int(r["TIC"])].append((fnum(r["tc_BJD_TDB"]), fnum(r["sigma_min"]), r["tier"]))
    lists["eumemic"] = [{"tic": t, "predictions": v} for t, v in sorted(eu.items())]
    ct = []
    for r in csv.DictReader((WORK / "ctoi.csv").open(encoding="utf-8")):
        tic = r["TIC ID"].strip()
        if not tic.isdigit():
            continue
        ct.append(
            {
                "tic": int(tic),
                "ra": fnum(r["RA"]),
                "dec": fnum(r["Dec"]),
                "t0": fnum(r["Transit Epoch (BJD)"]),
                "s0": fnum(r["Transit Epoch (BJD) err"]),
                "p": fnum(r["Period (days)"]),
                "sp": fnum(r["Period (days) Error"]),
                "promoted": bool((r["Promoted to TOI"] or "").strip()),
            }
        )
    lists["ctoi"] = ct
    ledger = ROOT / "calibration/v0.4/results/ledger.jsonl"
    led = [json.loads(x) for x in ledger.open(encoding="utf-8") if x.strip()]
    promotion = ROOT / "calibration/v0.4/runs/promotion.json"
    promoted = json.loads(promotion.read_text("utf-8"))["promoted"]
    own = []
    for case in promoted:
        ran = next(x for x in led if x["case_id"] == case and x["type"] == "ran")
        c = ran["data"]["stage1"]["candidate"]
        own.append(
            {
                "tic": int(case.split("-")[1]),
                "t0": c["t0"] + 2457000.0,
                "s0": None,
                "p": c["period"],
                "sp": None,
            }
        )
    lists["refute_own"] = own
    return lists


def coordinates(tics: list[int]) -> dict[int, tuple[float, float]]:
    from astroquery.mast import Catalogs

    p = WORK / "tic-coords.json"
    done = json.loads(p.read_text("utf-8")) if p.exists() else {}
    todo = sorted({t for t in tics if str(t) not in done})
    for i in range(0, len(todo), 200):
        batch = [str(t) for t in todo[i : i + 200]]
        res = Catalogs.query_criteria(catalog="Tic", ID=batch)
        got = {str(int(r["ID"])): [float(r["ra"]), float(r["dec"])] for r in res}
        for t in batch:
            done[t] = got.get(t)
        p.write_text(json.dumps(done), "utf-8")
    return {int(k): tuple(v) for k, v in done.items() if v}


def main() -> None:
    sectors = sector_pages()
    lists = load_lists()
    need = [x["tic"] for x in lists["eumemic"] + lists["refute_own"]]
    need += [x["tic"] for x in lists["ctoi"] if x["ra"] is None]
    coords = coordinates(need)
    all_tics = sorted({x["tic"] for v in lists.values() for x in v})
    two_min, prov_mast = mast_targets(
        "mast-spoc-2min",
        all_tics,
        obs_collection="TESS",
        dataproduct_type="timeseries",
        provenance_name="SPOC",
        t_exptime=[119, 121],
    )
    out = {
        "mode": "exploratory",
        "method_status": "not_validated",
        "limits_label": LABEL,
        "written_utc": now(),
        "new_sectors": {},
        "lists": {},
    }
    for s, v in sectors.items():
        out["new_sectors"][str(s)] = {
            "start": v["start"],
            "end": v["end"],
            "cameras": {str(k): list(c) for k, c in v["cameras"].items()},
        }
    per = []
    for name, items in lists.items():
        stats = {
            "targets": len(items),
            "with_coordinates": 0,
            "on_silicon_yes": 0,
            "on_silicon_unknown_only": 0,
            "with_transit_on_silicon": 0,
            "transits_on_silicon": 0,
            "with_2min_history": 0,
            "with_transit_on_silicon_and_2min_history": 0,
        }
        sigmas = []
        for x in items:
            if name == "ctoi" and x.get("ra") is not None:
                radec = (x["ra"], x["dec"])
            else:
                radec = coords.get(x["tic"])
            if not radec:
                continue
            stats["with_coordinates"] += 1
            states = {s: on_silicon(radec[0], radec[1], v) for s, v in sectors.items()}
            yes = [s for s, st in states.items() if st == "yes"]
            if yes:
                stats["on_silicon_yes"] += 1
            elif "unknown" in states.values():
                stats["on_silicon_unknown_only"] += 1
            hits = []
            for s in yes:
                v = sectors[s]
                if name == "eumemic":
                    hits += [
                        (tc, sg)
                        for tc, sg, _ in x["predictions"]
                        if tc and v["jd_start"] <= tc <= v["jd_end"]
                    ]
                else:
                    hits += transits(x["t0"], x["p"], x["s0"], x["sp"], v["jd_start"], v["jd_end"])
            if hits:
                stats["with_transit_on_silicon"] += 1
                stats["transits_on_silicon"] += len(hits)
                sigmas += [sg for _, sg in hits if sg is not None]
            hist = x["tic"] in two_min
            stats["with_2min_history"] += hist
            stats["with_transit_on_silicon_and_2min_history"] += bool(hits) and hist
            per.append(
                {
                    "list": name,
                    "tic": x["tic"],
                    "sectors": states,
                    "transits": len(hits),
                    "two_min_history": hist,
                }
            )
        stats["timing_sigma_minutes"] = (
            {
                "median": statistics.median(sigmas),
                "p90": sorted(sigmas)[int(0.9 * (len(sigmas) - 1))],
            }
            if sigmas
            else None
        )
        out["lists"][name] = stats
    out["provenance"] = {
        "sectors": "https://tess.mit.edu/observations/sector-<N>/ (110 to 120), read 2026-11-24",
        "eumemic": {
            "repository": "https://github.com/eumemic/exoplanets",
            "file": "candidates/predictions.csv",
            "commit": "e2eee928fd621f75c1621f6b4206d34bb222ae59",
            "licence": "not confirmed (repository LICENSE: MIT; results' licence unread)",
        },
        "ctoi": {
            "url": "https://exofop.ipac.caltech.edu/tess/download_ctoi.php?sort=ctoi&output=csv",
            "retrieved": "2026-11-24",
            "licence": "not confirmed",
        },
        "refute_own": "calibration/v0.4/runs/promotion.json (promoted) and results/ledger.jsonl",
        "coordinates": "MAST TIC catalog (astroquery.mast.Catalogs), for lists without RA/Dec",
        "mast": prov_mast,
        "geometry": {
            "half_field_deg": HALF,
            "margin_deg": MARGIN,
            "gap_deg": GAP,
            "roll": "both sign conventions; disagreement is unknown",
        },
    }
    (WORK / "route-e-targets.json").write_text(json.dumps(per), "utf-8")
    (HERE / "route-e.json").write_text(json.dumps(out, indent=1) + "\n", "utf-8", newline="\n")
    print(json.dumps(out["lists"], indent=1))


if __name__ == "__main__":
    main()
