"""Write ``calibration/v0.5.6/claim.yaml``, part B's claim, before the lock (docs/plans/
v0.5.6-plan-amendment-1.md; the maintainer's decisions of 2026-11-22, 13:00, item 5; #218).

The test plan is the locked v0.5 C3 claim's (``calibration/v0.5/claim.yaml``), with ``eb_catalog``
taken out of the decisive roles: part A ran the battery without the catalog test, and a claim
without catalog attachments must not give it a role. ``discovery.inputs`` records the SHA-256 of
every file the claim depends on outside the code, so the lock covers them. Run again only before
the lock (it rewrites the claim from the current files); after the lock, any change is TAMPERED.

Usage (from the project root): ``.venv/Scripts/python.exe -B calibration/v0.5.6/part_b_claim.py``.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
V = "docs/validation/v0.5.6/"
INPUTS = {
    "frame": V + "part-a-frame.csv",
    "frame_record": V + "part-a-frame.json",
    "frame_code": V + "part_a_frame.py",
    "prep": V + "part-b-prep.json",
    "prep_code": V + "part_b_prep.py",
    "part_a_run": V + "part_a_run.py",
    "part_a_draw": V + "part-a-draw.json",
    "part_a_records": V + "part-a-records.json",
    "plan": "docs/plans/v0.5.6-plan.md",
    "amendment": "docs/plans/v0.5.6-plan-amendment-1.md",
    "v05_claim": "calibration/v0.5/claim.yaml",
}
HEADER = """\
# Refute v0.5.6 part B: agreement of the labelled v0.5 battery with TFOPWG dispositions.
# docs/plans/v0.5.6-plan-amendment-1.md (the maintainer's decisions of 2026-11-22, 13:00; #218).
# Written by calibration/v0.5.6/part_b_claim.py before the lock. The targets attachment is the
# pool; the drand round, fixed after the lock, orders it (part_b_draw.py); only the drawn TICs
# are run (part_b_run.py), and the claim's verdict comes only from part_b_evaluate.py.
"""


def sha(path: str) -> str:
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def claim() -> dict:
    v05 = yaml.safe_load((ROOT / INPUTS["v05_claim"]).read_text("utf-8"))
    tp = v05["test_plan"]
    disc = tp["discovery"]
    disc["decisive"] = [t for t in disc["decisive"] if t != "eb_catalog"]
    disc["survived_meaning"] = (
        "a target's SURVIVED is recorded and never used alone: the claim's verdict comes from "
        "part_b_evaluate.py (agreement with TFOPWG dispositions); the method is not validated"
    )
    disc["inputs"] = {k: sha(p) for k, p in INPUTS.items()}
    return {
        "schema_version": 1,
        "id": "tess-v0.5.6-part-b-fp-agreement",
        "kind": "discover",
        "pack": "tess",
        "title": "Refute v0.5.6 part B: agreement of the labelled v0.5 battery with TFOPWG "
        "dispositions (WEAKENED; does not meet D1, D2, D4, T2a)",
        "hypothesis": (
            "Among the TOIs of the frame's confirmation half, the v0.5 battery (limits label "
            "'WEAKENED; does not meet D1, D2, D4, T2a') refutes, on the TOI's own signal, a larger "
            "share of the TOIs dispositioned FP by the TFOPWG than of the TOIs matched to "
            "TESS-discovered confirmed planets (Fisher exact, one-sided, alpha 0.05), while its "
            "rate on those planets stays at most 0.05 with an upper Wilson 95 % bound at most "
            "0.10. It measures agreement with TFOPWG dispositions on photometry that overlaps "
            "theirs, never that the battery detects false positives. The hypothesis was suggested "
            "by part A's descriptive table (FP 0/2/5/14 of 21; planet arm 13/16/9/82 of 120) and "
            "was not a pre-written door."
        ),
        "created": "2026-11-22",
        "authors": ["Klauber Lucilla"],
        "definitions": {
            "protocol": "docs/plans/v0.5.6-plan-amendment-1.md, section 4 (its SHA-256 in "
            "test_plan.discovery.inputs.amendment)",
            "strata": "confirmation half of part-a-frame.csv: planet = the planet arm; fp = the "
            "open arm with tfopwg_disp_descriptive FP; TICs in part-b-prep.json exposed_tics "
            "left out; FA, PC, APC, KP, CP and blank not drawn",
            "draw": "150 eligible per stratum (at least 120), in the order of the drand round "
            "fixed after the lock (part_b_draw.py)",
            "event": "status OK, nonzero coverage, outcome REFUTED and identity matched (period "
            "factor 1 within 0.001, epoch within half the TOI's duration)",
            "missing_data": "ERROR counts as a non-event in the denominator and as a loss; "
            "MISSING_PRODUCTS, zero coverage and no record are losses outside the denominator; "
            "more than floor(0.10 x drawn) losses in a stratum make the claim INCONCLUSIVE",
            "verdict": "INCONCLUSIVE if the draw is incomplete or the losses pass the cap; "
            "SURVIVED if p <= 0.05 and the guard holds; WEAKENED if p <= 0.05 and the guard "
            "fails; REFUTED if p > 0.05 (part_b_evaluate.py). Never 'confirmed', 'discovery', "
            "'TRUE' or a planet letter.",
            "known_defects": "OverflowError in gaussian_sigma_from_chi2 via centroid_v5 (#59; "
            "such a target is ERROR); the half-period search defect (#59; not an event)",
            "method_status": "not_validated",
            "limits_label": "WEAKENED; does not meet D1, D2, D4, T2a",
            "max_sector": "S_max = 107 (test_plan.discovery.max_sector).",
        },
        "data_sources": [
            {
                "name": "NASA Exoplanet Archive, TOI table (ephemerides; tfopwg_disp as a stratum)",
                "url": "https://exoplanetarchive.ipac.caltech.edu/TAP/sync",
                "retrieved": "2026-11-22T01:57:39Z",
                "notes": "Read once for part A's frame (part-a-frame.json); never queried again. "
                "Use of tfopwg_disp: docs/plans/sources/v0.5.6-nexsci-answer-2026-11-22.md.",
            },
            {
                "name": "NASA Exoplanet Archive, Planetary Systems Composite Parameters",
                "url": "https://exoplanetarchive.ipac.caltech.edu/TAP/sync",
                "retrieved": "2026-11-22T01:57:41Z",
                "notes": "The planet arm's match (part-a-frame.json).",
            },
            {
                "name": "MAST: SPOC 120-s light curves and target pixel files",
                "url": "https://mast.stsci.edu",
                "retrieved": "at the draw (metadata) and the run (files), after the lock",
                "notes": "Each listing's SHA-256 is in part-b-draw.json; each file's in the "
                "records.",
            },
            {
                "name": "drand mainnet, default chain",
                "url": "https://api.drand.sh",
                "retrieved": "the round fixed by part_b_draw.py round, after the lock",
                "notes": "BLS signature verified (refute.drand).",
            },
        ],
        "attachments": [
            {"path": "pool-targets.yaml", "role": "targets"},
            {"path": "part_b_claim.py", "role": "claim-generator"},
            {"path": "part_b_draw.py", "role": "draw"},
            {"path": "part_b_run.py", "role": "runner"},
            {"path": "part_b_run.diff", "role": "runner-diff"},
            {"path": "part_b_evaluate.py", "role": "evaluation"},
        ],
        "test_plan": tp,
    }


def main() -> None:
    text = HEADER + yaml.safe_dump(claim(), sort_keys=False, allow_unicode=True, width=96)
    (HERE / "claim.yaml").write_text(text, "utf-8", newline="\n")
    print("claim.yaml written")


if __name__ == "__main__":
    main()
