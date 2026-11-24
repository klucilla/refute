"""v0.5.10, part (c): the route (d1) census. Exploratory; catalogs and metadata only.

- The false-positive arm: the KELT-FP catalog (Collins et al. 2018, AJ 156, 234;
  https://arxiv.org/abs/1803.01869), from the machine-readable table in the paper's arXiv source
  (https://arxiv.org/e-print/1803.01869v2, read 2026-11-24; the CDS VizieR copy was not reachable
  that day). Its licence is **not confirmed**: only counts and summaries are committed.
- The planet arm: transiting planets in the NASA Exoplanet Archive's pscomppars whose discovery
  facility is not TESS.
- Per target: SPOC 2-minute light curves in MAST (at least one sector), prior exposure in Refute's
  records, TOI status and TFOPWG disposition.

Writes census-d1.json and census-d1.md. The per-target table stays under .cache/v0510/census/.
"""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from census_common import (  # noqa: E402
    CACHE,
    LABEL,
    exposed_tics,
    fnum,
    mast_targets,
    now,
    quantiles,
    tap,
    tic_of,
)

HERE = Path(__file__).resolve().parent
KELT = CACHE / "arxiv-kelt/x/KELT_False_Positive_Catalog_20180531.csv"
KELT_SHA = "72b21cce9115f3a667ab9866f391ad461a2f6ea001bd07a87786a17a386e7386"


def main() -> None:
    raw = KELT.read_bytes()
    if hashlib.sha256(raw).hexdigest() != KELT_SHA:
        raise SystemExit("the KELT-FP table is not the recorded file")
    kelt = list(csv.DictReader(raw.decode("utf-8").splitlines()))
    types = Counter(r["FP_type_name"] for r in kelt)
    research_seven = ("NEB", "SB1", "SB2", "EB1", "BEB", "Giant", "EB2")
    planets, prov_pl = tap(
        "pscomppars-transiting",
        "select pl_name, hostname, tic_id, disc_facility, discoverymethod, pl_orbper, "
        "pl_trandep, sy_tmag, sy_vmag from pscomppars where tran_flag=1",
    )
    planets = [p for p in planets if "TESS" not in (p["disc_facility"] or "")]
    tois, prov_toi = tap("toi-all", "select tid, toi, tfopwg_disp from toi")
    toi_of: dict[int, list[str]] = {}
    for t in tois:
        tid = tic_of(t["tid"])
        if tid:
            toi_of.setdefault(tid, []).append(t["tfopwg_disp"] or "")
    exposed, prov_exp = exposed_tics()
    arms = {
        "kelt_fp": [
            {
                "tic": tic_of(r["TIC_ID"]),
                "period": fnum(r["Period_days"]),
                "depth": fnum(r["KELT_depth_mmag"]),
                "depth_unit": "mmag (KELT)",
                "mag": fnum(r["Vmag"]),
                "mag_unit": "V",
                "type": r["FP_type_name"],
            }
            for r in kelt
        ],
        "planets_not_tess": [
            {
                "tic": tic_of(p["tic_id"]),
                "period": fnum(p["pl_orbper"]),
                "depth": fnum(p["pl_trandep"]),
                "depth_unit": "percent",
                "mag": fnum(p["sy_tmag"]),
                "mag_unit": "TESS",
                "facility": p["disc_facility"],
            }
            for p in planets
        ],
    }
    all_tics = sorted({x["tic"] for a in arms.values() for x in a if x["tic"]})
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
        "arms": {},
    }
    per_target = []
    for name, rows in arms.items():
        with_tic = [x for x in rows if x["tic"]]
        tics = {x["tic"] for x in with_tic}
        spoc = {t for t in tics if t in two_min}
        unexposed = {t for t in tics if t not in exposed}
        usable = spoc & unexposed
        toi = {t for t in tics if t in toi_of}
        disp = Counter(d for t in usable for d in toi_of.get(t, []) if t in toi_of)
        sup = [x for x in with_tic if x["tic"] in usable]
        out["arms"][name] = {
            "rows": len(rows),
            "with_tic": len(with_tic),
            "unique_tics": len(tics),
            "spoc_2min": len(spoc),
            "not_exposed": len(unexposed),
            "usable": len(usable),
            "toi_overlap": len(toi),
            "usable_that_are_tois": len(usable & toi),
            "usable_toi_dispositions": dict(sorted(disp.items())),
            "usable_support": {
                "period_days": quantiles([x["period"] for x in sup]),
                "depth": quantiles([x["depth"] for x in sup]),
                "depth_unit": rows[0]["depth_unit"],
                "magnitude": quantiles([x["mag"] for x in sup]),
                "magnitude_band": rows[0]["mag_unit"],
            },
        }
        for x in with_tic:
            per_target.append(
                {
                    **x,
                    "arm": name,
                    "spoc_2min": x["tic"] in two_min,
                    "exposed": x["tic"] in exposed,
                    "toi": toi_of.get(x["tic"]),
                }
            )
    space = ("Kepler", "K2", "CoRoT", "Spitzer", "Hubble", "James Webb", "CHEOPS", "Gaia")
    usable_pl = [
        x
        for x in per_target
        if x["arm"] == "planets_not_tess" and x["spoc_2min"] and not x["exposed"]
    ]
    ground = [x for x in usable_pl if not any(s in (x["facility"] or "") for s in space)]
    out["arms"]["planets_not_tess"]["usable_by_facility"] = dict(
        Counter(x["facility"] for x in usable_pl).most_common()
    )
    out["arms"]["planets_not_tess"]["usable_ground_based"] = {
        "rule": "discovery facility names none of: " + ", ".join(space),
        "usable": len({x["tic"] for x in ground}),
        "period_days": quantiles([x["period"] for x in ground]),
        "depth_percent": quantiles([x["depth"] for x in ground]),
        "magnitude_tess": quantiles([x["mag"] for x in ground]),
    }
    out["kelt_fp_types"] = dict(types.most_common())
    out["kelt_fp_total"] = {
        "rows": len(kelt),
        "research_sum_of_seven_types": sum(types[t] for t in research_seven),
        "the_other_types": {t: n for t, n in types.items() if t not in research_seven},
        "reconciled": sum(types.values()) == len(kelt),
    }
    out["provenance"] = {
        "kelt_fp": {
            "url": "https://arxiv.org/e-print/1803.01869v2",
            "file": "KELT_False_Positive_Catalog_20180531.csv",
            "sha256": KELT_SHA,
            "read_utc": "2026-11-24",
            "licence": "not confirmed",
        },
        "pscomppars": {**prov_pl, "licence": "not confirmed"},
        "toi": {**prov_toi, "licence": "not confirmed"},
        "mast": prov_mast,
        "exposure": prov_exp,
    }
    (CACHE / "census-d1-targets.json").write_text(json.dumps(per_target), "utf-8")
    (HERE / "census-d1.json").write_text(json.dumps(out, indent=1) + "\n", "utf-8", newline="\n")
    print(
        json.dumps(
            {
                k: {
                    kk: v[kk]
                    for kk in ("unique_tics", "spoc_2min", "not_exposed", "usable", "toi_overlap")
                }
                for k, v in out["arms"].items()
            },
            indent=1,
        )
    )


if __name__ == "__main__":
    main()
