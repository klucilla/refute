"""v0.5.10, part (d): the Kepler-field census. Exploratory; catalogs and metadata only.

- The false-positive arm: KOIs with status CERTIFIED FP in the Kepler Certified False Positive
  table of the NASA Exoplanet Archive (config "fpwg"). The archive's TAP service has no such table
  and its old API refuses it (both checked 2026-11-24), so it was read from the archive's table
  view (https://exoplanetarchive.ipac.caltech.edu/cgi-bin/TblView/nph-tblView?app=ExoTbls&config=fpwg)
  as rendered on 2026-11-24 (16:02Z), parsed to kepid, KOI and status. Licence: not confirmed.
- The planet arm: planets in pscomppars whose discovery facility is Kepler (transiting).
- Per target: its TIC (pscomppars, or the TIC catalog's KIC column in MAST), and which TESS
  products exist in MAST: SPOC 2-minute light curves, SPOC FFI light curves (TESS-SPOC), and TGLC.
- Bins declared before the run (log.jsonl, census-kepler): TESS magnitude <10, 10-12, 12-14,
  14-16, >=16; transit depth (ppm) <500, 500-1000, 1000-5000, 5000-20000, >=20000.

Writes census-kepler.json. The per-target table stays under .cache/v0510/census/.
"""

from __future__ import annotations

import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from census_common import CACHE, LABEL, fnum, mast_targets, now, tap, tic_of  # noqa: E402

HERE = Path(__file__).resolve().parent
MAG_BINS = [(None, 10), (10, 12), (12, 14), (14, 16), (16, None)]
DEPTH_BINS = [(None, 500), (500, 1000), (1000, 5000), (5000, 20000), (20000, None)]


def label(bins, v):
    if v is None:
        return "unknown"
    for lo, hi in bins:
        if (lo is None or v >= lo) and (hi is None or v < hi):
            return f"{'' if lo is None else lo}-{'' if hi is None else hi}"
    return "unknown"


def kic_to_tic(kics: list[int]) -> dict[int, tuple[int, float | None]]:
    from astroquery.mast import Catalogs

    p = CACHE / "tic-by-kic.json"
    done = json.loads(p.read_text("utf-8")) if p.exists() else {}
    todo = sorted({k for k in kics if str(k) not in done})
    for i in range(0, len(todo), 200):
        batch = [str(k) for k in todo[i : i + 200]]
        res = Catalogs.query_criteria(catalog="Tic", KIC=batch)
        got = {str(int(r["KIC"])): [int(r["ID"]), fnum(r["Tmag"])] for r in res}
        for k in batch:
            done[k] = got.get(k)
        p.write_text(json.dumps(done), "utf-8")
    return {int(k): tuple(v) for k, v in done.items() if v}


def main() -> None:
    rows = list(csv.reader((CACHE / "fpwg-rows.csv").read_text("utf-8").splitlines()))
    cfp = {}
    for r in rows:
        koi = re.search(r"K\d{5}\.\d{2}", r[3])
        if koi and r[5] == "CERTIFIED FP" and r[2].isdigit():
            cfp[koi.group(0)] = int(r[2])
    status = Counter(r[5] for r in rows if len(r) > 5)
    cum, prov_cum = tap(
        "koi-cumulative", "select kepoi_name, kepid, koi_depth, koi_kepmag from cumulative"
    )
    depth = {c["kepoi_name"]: fnum(c["koi_depth"]) for c in cum}
    tic_map = kic_to_tic(list(cfp.values()))
    planets, prov_pl = tap(
        "pscomppars-transiting",
        "select pl_name, hostname, tic_id, disc_facility, discoverymethod, pl_orbper, "
        "pl_trandep, sy_tmag, sy_vmag from pscomppars where tran_flag=1",
    )
    kep = [p for p in planets if (p["disc_facility"] or "") == "Kepler"]
    arms = {
        "certified_fp": [
            {
                "id": koi,
                "tic": (tic_map.get(kid) or (None,))[0],
                "tmag": (tic_map.get(kid) or (None, None))[1],
                "depth_ppm": depth.get(koi),
            }
            for koi, kid in sorted(cfp.items())
        ],
        "kepler_planets": [
            {
                "id": p["pl_name"],
                "tic": tic_of(p["tic_id"]),
                "tmag": fnum(p["sy_tmag"]),
                "depth_ppm": (fnum(p["pl_trandep"]) or 0) * 1e4 if fnum(p["pl_trandep"]) else None,
            }
            for p in kep
        ],
    }
    all_tics = sorted({x["tic"] for a in arms.values() for x in a if x["tic"]})
    two, prov2 = mast_targets(
        "mast-spoc-2min",
        all_tics,
        obs_collection="TESS",
        dataproduct_type="timeseries",
        provenance_name="SPOC",
        t_exptime=[119, 121],
    )
    ffi, provf = mast_targets("mast-tess-spoc", all_tics, provenance_name="TESS-SPOC")
    tglc, provt = mast_targets("mast-tglc", all_tics, provenance_name="TGLC")
    out = {
        "mode": "exploratory",
        "method_status": "not_validated",
        "limits_label": LABEL,
        "written_utc": now(),
        "fpwg_status_counts": dict(status.most_common()),
        "arms": {},
    }
    per = []
    for name, items in arms.items():
        with_tic = [x for x in items if x["tic"]]
        prod = {"spoc_2min": two, "tess_spoc_ffi": ffi, "tglc": tglc}
        arm = {
            "rows": len(items),
            "with_tic": len(with_tic),
            "by_product": {k: sum(x["tic"] in v for x in with_tic) for k, v in prod.items()},
            "any_product": sum(any(x["tic"] in v for v in prod.values()) for x in with_tic),
        }
        specs = (("by_tmag", MAG_BINS, "tmag"), ("by_depth_ppm", DEPTH_BINS, "depth_ppm"))
        for key, bins, field in specs:
            table = {}
            for x in with_tic:
                b = label(bins, x[field])
                row = table.setdefault(b, {"n": 0, "spoc_2min": 0, "tess_spoc_ffi": 0, "tglc": 0})
                row["n"] += 1
                for k, v in prod.items():
                    row[k] += x["tic"] in v
            arm[key] = dict(sorted(table.items()))
        out["arms"][name] = arm
        per += [{**x, "arm": name, **{k: x["tic"] in v for k, v in prod.items()}} for x in with_tic]
    out["tglc_note"] = (
        "TGLC: no MAST observation was found under a TIC target name for any target; whether "
        "MAST indexes TGLC under another target name (for example a Gaia DR3 id) was not "
        "confirmed on 2026-11-24, so the TGLC counts are NOT DETERMINED, not zero"
    )
    out["provenance"] = {
        "fpwg": {
            "url": "https://exoplanetarchive.ipac.caltech.edu/cgi-bin/TblView/"
            "nph-tblView?app=ExoTbls&config=fpwg",
            "read": "2026-11-24T16:02:48Z (rendered table view; TAP has no fpwg table)",
            "licence": "not confirmed",
        },
        "cumulative": {**prov_cum, "licence": "not confirmed"},
        "pscomppars": {**prov_pl, "licence": "not confirmed"},
        "mast": [prov2, provf, provt],
        "tic_crossmatch": "MAST TIC catalog, KIC column (astroquery.mast.Catalogs)",
    }
    (CACHE / "census-kepler-targets.json").write_text(json.dumps(per), "utf-8")
    (HERE / "census-kepler.json").write_text(
        json.dumps(out, indent=1) + "\n", "utf-8", newline="\n"
    )
    summary = {k: {"with_tic": v["with_tic"], **v["by_product"]} for k, v in out["arms"].items()}
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
