"""Stage the catalog queries of part (f) before any offline run (Codex's blocking item 4).

For each of the 24 TOIs, in the project's environment (astroquery, no engine code):
- the TIC rows within 10 TESS pixels (202.5 arcsec) of the target, as TRICERATOPS 1.1.0 asks
  for them (``Catalogs.query_object("TIC<id>", radius, catalog="TIC")``);
- the Gaia DR3 field population that TRICERATOPS's ``query_gaia_background`` reads: the same
  ADQL (G < 21 inside a circle of 0.1 square degrees around the target).

The tables stay under .cache/v0510/staged/ and are never committed (Gaia's and the TIC's rows
are not exported). The committed output, staged-catalogs.json, holds only counts, query texts,
the service URLs, the times and the SHA-256 of each staged file.
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
import time
from pathlib import Path

import astropy.units as u

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[3]
STAGED = PROJECT / ".cache/v0510/staged"
OUT = HERE / "staged-catalogs.json"
SET = PROJECT / "docs/validation/v0.5.9/prototype-set.json"
ADQL = (
    "SELECT phot_g_mean_mag, phot_bp_mean_mag, phot_rp_mean_mag, "
    "parallax, parallax_over_error "
    "FROM gaiadr3.gaia_source "
    "WHERE 1 = CONTAINS(POINT('ICRS', ra, dec), "
    "CIRCLE('ICRS', {0}, {1}, {2})) "
    "AND phot_g_mean_mag < {3}"
)


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    from astroquery.gaia import Gaia
    from astroquery.mast import Catalogs

    order = json.loads(SET.read_text(encoding="utf-8"))["order"]
    if len(sys.argv) > 1:
        order = [k for k in order if k in sys.argv[1:]]
    (STAGED / "tic").mkdir(parents=True, exist_ok=True)
    (STAGED / "gaia").mkdir(parents=True, exist_ok=True)
    recs = []
    for key in order:
        tic = int(key.split("-")[1])
        rec = {"target": key}
        tic_path = STAGED / "tic" / f"{key}.ecsv"
        gaia_path = STAGED / "gaia" / f"{key}.ecsv"
        try:
            if not tic_path.exists():
                t = Catalogs.query_object(f"TIC{tic}", radius=10 * 20.25 * u.arcsec, catalog="TIC")
                t.write(tic_path, format="ascii.ecsv", overwrite=True)
            from astropy.table import Table

            t = Table.read(tic_path, format="ascii.ecsv")
            rec["tic_rows"] = len(t)
            rec["target_first"] = int(t[0]["ID"]) == tic
            ra, dec = float(t[0]["ra"]), float(t[0]["dec"])
            rec["tic_sha256"] = sha(tic_path)
            if not gaia_path.exists():
                radius = math.sqrt(0.1 / math.pi)
                q = ADQL.format(ra, dec, radius, 21.0)
                Gaia.ROW_LIMIT = -1
                try:
                    g = Gaia.launch_job(q, verbose=False).get_results()
                    if len(g) >= 2000:
                        g = Gaia.launch_job_async(q, verbose=False).get_results()
                except Exception:
                    g = Gaia.launch_job_async(q, verbose=False).get_results()
                g.write(gaia_path, format="ascii.ecsv", overwrite=True)
            g = Table.read(gaia_path, format="ascii.ecsv")
            rec["gaia_rows"] = len(g)
            rec["gaia_sha256"] = sha(gaia_path)
            rec["status"] = "staged"
        except Exception as exc:  # recorded; the engine then records the input as unavailable
            rec["status"] = "failed"
            rec["error"] = f"{type(exc).__name__}: {exc}"[:500]
        recs.append(rec)
        print(json.dumps(rec))
    doc = {
        "schema": "refute-v0510-staged-catalogs-1",
        "mode": "exploratory",
        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "tic_query": "astroquery.mast.Catalogs.query_object('TIC<id>', radius=202.5 arcsec, "
        "catalog='TIC') (MAST, https://mast.stsci.edu)",
        "gaia_query": ADQL.format("<ra>", "<dec>", "sqrt(0.1/pi)", 21.0)
        + " (ESA Gaia archive, https://gea.esac.esa.int/archive/)",
        "terms": "Gaia DR3 rows and TIC rows are kept under .cache only and never committed; "
        "Gaia: ESA/Gaia/DPAC credit, terms recorded in docs/data-publication.md as restricted",
        "targets": recs,
    }
    if len(sys.argv) == 1:
        OUT.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8")
    return 0 if all(r["status"] == "staged" for r in recs) else 1


if __name__ == "__main__":
    raise SystemExit(main())
