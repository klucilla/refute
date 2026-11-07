"""Amendment 6, development evidence for the SAP applicability rule (decides nothing).

Per sector, on the cadences where both normalized series (each divided by its median) are finite:
the number of cadences, the PDCSAP standard deviation and the largest absolute residual of the
least-squares fit ``SAP_n = a + b (PDCSAP_n - mean) / sd`` (standardized, so the two columns are
orthogonal with unit scale and the design's condition number is 1).

- Real: the six SPOC 2-min light curves of the development control TIC-101395259 (already in
  ``.cache/v051/dev/``, their SHA-256 in ``dev-control-fetch.json``), quality flag 0 only.
- Synthetic: C1's generator (``calib05/c1.py``), family P, development seeds 0 to 19, whose SAP is
  ``1 + CROWDSAP x (PDCSAP - 1)`` (``synthetic.make_sector_aux``).

Run: ``.venv/Scripts/python.exe docs/validation/v0.5.1/feasibility/sap_affine_check.py``; writes
``sap-affine-check.json`` next to this script.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from astropy.io import fits

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
DEV = ROOT / ".cache" / "v051" / "dev" / "lightkurve" / "mastDownload" / "TESS"


def affine_stats(sap: np.ndarray, pdc: np.ndarray) -> dict:
    both = np.isfinite(sap) & np.isfinite(pdc)
    s, p = sap[both], pdc[both]
    s, p = s / np.median(s), p / np.median(p)
    x = (p - p.mean()) / np.std(p)  # standardized: the two columns orthogonal, unit scale
    design = np.column_stack([np.ones(x.size), x])
    coef, *_ = np.linalg.lstsq(design, s, rcond=None)
    resid = s - design @ coef
    return {
        "n_cadences": int(both.sum()),
        "pdcsap_std": float(np.std(p)),
        "slope": float(coef[1]),
        "max_abs_residual": float(np.max(np.abs(resid))),
        "condition_number": float(np.linalg.cond(design)),
    }


def real() -> list[dict]:
    out = []
    for path in sorted(DEV.glob("*/*_lc.fits")):
        with fits.open(path) as hdul:
            d = hdul[1].data
            sector = int(hdul[0].header["SECTOR"])
            good = d["QUALITY"] == 0
            sap = np.asarray(d["SAP_FLUX"], float)[good]
            pdc = np.asarray(d["PDCSAP_FLUX"], float)[good]
        row = {"sector": sector, "file": path.name}
        row["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        row.update(affine_stats(sap, pdc))
        out.append(row)
    return out


def synthetic() -> list[dict]:
    from refute.packs.tess.calib05 import c1

    out = []
    for i in range(20):
        data, truth = c1.generate("P", c1.development_seed("P", i))
        for a in data.aux.sectors:
            row = {"index": i, "sector": int(a.sector), "crowdsap": a.crowdsap}
            row.update(affine_stats(a.sap_flux, a.pdcsap_flux))
            out.append(row)
    return out


def main() -> None:
    r, s = real(), synthetic()
    result = {
        "real_tic_101395259": r,
        "synthetic_c1_p_dev_0_19": s,
        "summary": {
            "real_min_max_abs_residual": min(x["max_abs_residual"] for x in r),
            "real_min_n_cadences": min(x["n_cadences"] for x in r),
            "real_min_pdcsap_std": min(x["pdcsap_std"] for x in r),
            "synthetic_max_max_abs_residual": max(x["max_abs_residual"] for x in s),
            "synthetic_min_n_cadences": min(x["n_cadences"] for x in s),
            "synthetic_min_pdcsap_std": min(x["pdcsap_std"] for x in s),
            "synthetic_max_condition_number": max(x["condition_number"] for x in s),
        },
    }
    (HERE / "sap-affine-check.json").write_text(json.dumps(result, indent=1) + "\n", "utf-8")
    print(json.dumps(result["summary"], indent=1))


if __name__ == "__main__":
    main()
