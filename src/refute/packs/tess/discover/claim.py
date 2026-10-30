"""The v0.4 pilot's claim (calibration/v0.4/PROTOCOL.md, section 12, step 3), written after the
selection from committed files only: one ``discover`` claim for the 2 controls and the 100 funnel
stars of ``selection/targets.yaml``.

- ``test_plan``: every TESS default of this commit written out (protocol section 5: the v0.2
  thresholds on the legacy path, corrections version 1, with the v0.2.1 changes H4 and H9a in
  their defaults; H7 is the controls' signal identity, ``case.signal_identity``), plus the
  ``discovery`` section of the protocol: the
  v0.2 battery and ``eb_catalog`` decisive, ``holdout_by_year`` a required diagnostic, the pixel
  tests at stage 2, ``max_sector`` = S_max, and ``inputs``, the SHA-256 of the files the claim
  depends on outside the code.
- The eclipsing-binary attachments (``refute-eb-catalog-1`` and ``refute-eb-catalog-scan-1``) are
  extracted around each target from the frozen TESS-EB and Gaia DR3 EB snapshots, each checked
  against its hash in ``inputs.json`` first. TESS-EB is not redistributed (#33): its entries are
  reference rows, resolved at run time from a local copy whose content SHA-256 the scan records.

Nothing here queries the network.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
from pathlib import Path
from typing import Any

from refute.packs.tess.discover import pilot
from refute.packs.tess.discover import selection as sel
from refute.packs.tess.discover.protocol import CONTROLS, PROTOCOL_ID, SURVIVED_MEANING

CLAIM_ID = "tess-discover-v0.4-pilot"
CLAIM_NAME = "claim.yaml"
EB_CATALOG = "eb_catalog.csv"
EB_SCAN = "eb_catalog_scan.json"
# The v0.2 extraction radius (calibration/v0.2/select_targets.py), above the match radius of 21.
EXTRACT_RADIUS_ARCSEC = 120.0
# Where a run finds the TESS-EB static edition, relative to its cache folder (the copy is placed
# there before a run; its content SHA-256 is checked before any analysis, and a run stops if it
# differs).
TESS_EB_CACHE_PATH = "v04/tess-eb/tess_ebs_prsa2022.tsv"
# The files whose SHA-256 the claim records (test_plan.discovery.inputs), by key: the protocol,
# the inputs record, the selection output, and every frozen input the selection or the
# deduplication reads, as recorded in inputs.json.
REPOSITORY_INPUTS = {
    "protocol": "PROTOCOL.md",
    "inputs_json": "inputs.json",
    "selection": "selection/selection.json",
}
RECORDED_INPUTS = {
    "target_lists_page": "target_lists.html",
    "frame": "frame.csv",
    "toi": "toi.csv",
    "ctoi": "ctoi.csv",
    "pscomppars": "pscomppars.csv",
    "tess_eb": "tess_eb.tsv",
    "gaia_dr3_eb": "gaia_dr3_eb.csv",
}
DECISIVE = (
    "snr",
    "odd_even",
    "secondary_eclipse",
    "plausibility",
    "centroid_shift",
    "aperture_depth",
    "nearby_contamination",
    "period_alias",
    "systematics",
    "eb_catalog",
)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def discovery_inputs(step_dir: Path, inputs: dict[str, Any]) -> dict[str, str]:
    """The SHA-256 of each file the claim depends on outside the code: the repository files as
    they are on disk, the frozen inputs as ``inputs.json`` records them."""
    recorded = {i["name"]: i["sha256"] for i in inputs["files"]}
    out = {key: _sha((step_dir / path).read_bytes()) for key, path in REPOSITORY_INPUTS.items()}
    for key, name in RECORDED_INPUTS.items():
        if name not in recorded:
            raise sel.SelectionError(f"{name} has no recorded SHA-256 in inputs.json")
        out[key] = recorded[name]
    return out


def claim_test_plan(step_dir: Path, inputs: dict[str, Any]) -> dict[str, Any]:
    """Every default written out, with the protocol's ``discovery`` section."""
    from refute.packs.tess.params import TessTestPlan

    discovery = {
        "version": 1,
        "decisive": list(DECISIVE),
        "diagnostic": ["holdout_by_year"],
        "stages": {"centroid_shift": 2, "aperture_depth": 2},
        "required_diagnostics": ["holdout_by_year"],
        "method_status": "not_validated",
        "survived_meaning": SURVIVED_MEANING,
        "inputs": discovery_inputs(step_dir, inputs),
        "max_sector": int(inputs["s_max"]),
    }
    return TessTestPlan.model_validate({"discovery": discovery}).model_dump(mode="json")


def _separation_arcsec(ra: float, dec: float, ras: Any, decs: Any) -> Any:
    import numpy as np

    r1, d1, r2, d2 = map(np.radians, (ra, dec, ras, decs))
    h = np.sin((d2 - d1) / 2) ** 2 + np.cos(d1) * np.cos(d2) * np.sin((r2 - r1) / 2) ** 2
    return np.degrees(2 * np.arcsin(np.minimum(1.0, np.sqrt(h)))) * 3600.0


def _checked(inputs_dir: Path, inputs: dict[str, Any], name: str) -> bytes:
    recorded = {i["name"]: i["sha256"] for i in inputs["files"]}
    data = (inputs_dir / name).read_bytes()
    if name not in recorded or _sha(data) != recorded[name]:
        raise sel.SelectionError(f"{name} does not match its recorded SHA-256")
    return data


def eb_attachments(
    targets: list[dict[str, Any]],
    inputs_dir: Path,
    inputs: dict[str, Any],
    tess_eb_content_sha256: str = pilot.TESS_EB_STATIC["content_sha256"],
    gaia_rows: int = pilot.GAIA_EB_ROWS,
) -> tuple[str, dict[str, Any]]:
    """The ``refute-eb-catalog-1`` rows within ``EXTRACT_RADIUS_ARCSEC`` of each target (and
    every TESS-EB entry under the target's own TIC), and the scan record. The centre is the
    target's TIC position recorded by the selection walk (``mast.tic_ra``, ``mast.tic_dec``).
    The two expected values are the frozen editions'; tests pass their synthetic ones."""
    import numpy as np

    from refute.packs.tess.ebcatalog import COLUMNS, content_sha256, parse_tess_eb

    tess_data = _checked(inputs_dir, inputs, "tess_eb.tsv")
    if content_sha256(tess_data) != tess_eb_content_sha256:
        raise sel.SelectionError("tess_eb.tsv is not the TESS-EB static edition")
    tess = parse_tess_eb(tess_data)
    tess_keys = sorted(tess)
    t_ra = np.array([tess[k][0] for k in tess_keys])
    t_dec = np.array([tess[k][1] for k in tess_keys])
    t_tic = np.array([int(k.split()[1]) for k in tess_keys])
    gaia_data = _checked(inputs_dir, inputs, "gaia_dr3_eb.csv")
    gaia = np.genfromtxt(
        io.BytesIO(gaia_data),
        delimiter=",",
        names=True,
        dtype=[("source_id", "i8"), ("ra", "f8"), ("dec", "f8"), ("frequency", "f8")],
    )
    if len(gaia) != gaia_rows:
        raise sel.SelectionError(f"gaia_dr3_eb.csv has {len(gaia)} rows, not {gaia_rows}")
    rows: set[tuple] = set()
    per_target: dict[str, dict[str, int]] = {}
    for target in targets:
        ra, dec = target["mast"].get("tic_ra"), target["mast"].get("tic_dec")
        valid = isinstance(ra, int | float) and isinstance(dec, int | float)
        if not valid or not (math.isfinite(ra) and math.isfinite(dec)) or abs(dec) > 90:
            raise sel.SelectionError(
                f"{target['key']} has no valid position in its selection record"
            )
        near_t = set(
            np.nonzero(_separation_arcsec(ra, dec, t_ra, t_dec) <= EXTRACT_RADIUS_ARCSEC)[0]
        )
        near_t |= set(np.nonzero(t_tic == int(target["tic_id"]))[0])
        for i in near_t:
            rows.add(("TESS-EB", tess_keys[i], int(t_tic[i]), None, None, None))
        near_g = np.nonzero(
            _separation_arcsec(ra, dec, gaia["ra"], gaia["dec"]) <= EXTRACT_RADIUS_ARCSEC
        )[0]
        for i in near_g:
            freq = float(gaia["frequency"][i])
            period = 1.0 / freq if math.isfinite(freq) and freq > 0 else None
            rows.add(
                (
                    "Gaia-DR3-EB",
                    str(int(gaia["source_id"][i])),
                    None,
                    float(gaia["ra"][i]),
                    float(gaia["dec"][i]),
                    period,
                )
            )
        per_target[target["key"]] = {"tess_eb": len(near_t), "gaia": int(len(near_g))}

    def number(value: float | None, fmt: str) -> str:
        return "" if value is None else format(value, fmt)

    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(COLUMNS)
    for catalog, source, tic, r_ra, r_dec, period in sorted(rows, key=lambda r: (r[0], r[1])):
        writer.writerow(
            [
                catalog,
                source,
                "" if tic is None else tic,
                number(r_ra, ".9f"),
                number(r_dec, ".9f"),
                number(period, ".9g"),
            ]
        )
    scan = {
        "format": "refute-eb-catalog-scan-1",
        "attachment": f"{EB_CATALOG} (format refute-eb-catalog-1; TESS-EB as reference rows)",
        "radius_arcsec": EXTRACT_RADIUS_ARCSEC,
        "centre": "each target's TIC position from the selection walk (mast.tic_ra, tic_dec)",
        "snapshots": [
            {
                "catalog_name": "TESS-EB",
                "file": "tess_eb.tsv",
                "cache_path": TESS_EB_CACHE_PATH,
                "url": pilot.TESS_EB_URL,
                "parser": "tess-eb-vizier-tsv",
                "sha256": _sha(tess_data),
                "content_sha256": tess_eb_content_sha256,
                "rows": len(tess),
                "redistributed": False,
            },
            {
                "catalog_name": "Gaia-DR3-EB",
                "file": "gaia_dr3_eb.csv",
                "url": pilot.GAIA_EB_URL,
                "sha256": _sha(gaia_data),
                "rows": int(len(gaia)),
                "redistributed": True,
            },
        ],
        "rows": len(rows),
        "per_target": dict(sorted(per_target.items())),
    }
    return out.getvalue(), scan


def claim_document(
    step_dir: Path, inputs: dict[str, Any], targets_doc: dict[str, Any], created: str
) -> dict[str, Any]:
    """The claim, its attachments named by their paths relative to ``step_dir``."""
    retrieved = {i["name"]: i["retrieved_utc"] for i in inputs["files"]}
    selection = targets_doc["selection"]
    factors = ", ".join(f"{f:g}" for f in CONTROLS.fp_identity_factors)
    return {
        "schema_version": 1,
        "id": CLAIM_ID,
        "kind": "discover",
        "pack": "tess",
        "title": "Refute v0.4 pilot: a funnel search for transit signals, attacked before belief",
        "hypothesis": (
            "Among the 100 funnel stars selected by calibration/v0.4/PROTOCOL.md (the first N "
            "of them run, N from the rule of section 4.4), any transit-like signal Refute finds "
            "in SPOC 120-s light curves of sectors 1 to S_max is attacked by the declared "
            "decisive battery; each case ends in SURVIVED, WEAKENED, REFUTED or INCONCLUSIVE, "
            "with SURVIVED meaning only: " + SURVIVED_MEANING + ". The two known controls "
            "(a planet and a false positive) run first, with the same battery."
        ),
        "created": created,
        "authors": ["Klauber Lucilla"],
        "definitions": {
            "protocol": (
                f"{PROTOCOL_ID}, calibration/v0.4/PROTOCOL.md; the selection of round "
                f"{selection['round']} from the protocol commit {selection['protocol_commit']}."
            ),
            "run_set": (
                "The two controls, then the first N funnel stars in the walk order of "
                "selection/targets.yaml; the stars beyond N are 'not evaluated past stage 1: "
                "N rule' (section 4.4)."
            ),
            "signal_identity": (
                "Controls only (section 4.3): the planet's found period is within a relative "
                f"period_tolerance of {CONTROLS.identity_period_tolerance:g} of the published "
                "period (aliases not counted); the false positive's is within it at one of "
                f"flag_signal_period_factors [{factors}]. The values are code "
                "(refute.packs.tess.discover.protocol.CONTROLS). The epoch difference is "
                "reported, not required."
            ),
            "verdict": (
                "Aggregated from the decisive tests only, with the severity each test emits "
                "(docs/verdicts.md); holdout_by_year is a diagnostic and never changes it. "
                "Never 'confirmed', 'discovery', 'TRUE' or a planet letter."
            ),
            "method_status": (
                "not_validated: nothing in v0.4 is a validated method "
                "(docs/validation/v0.2.1/closing-2026-10-27.md)."
            ),
            "max_sector": (
                f"S_max = {inputs['s_max']}: no product of a later sector is downloaded or read "
                "(test_plan.discovery.max_sector)."
            ),
        },
        "data_sources": [
            {
                "name": "TESS two-minute target lists (frame of sectors 1 to S_max)",
                "url": pilot.TARGET_LISTS_PAGE,
                "retrieved": retrieved["target_lists.html"],
                "notes": (
                    "Assembled from attempt 4 (PROTOCOL.md 4.0, exception); times are estimates; "
                    "every list's URL, size and SHA-256 in inputs.json."
                ),
            },
            {
                "name": "ExoFOP-TESS TOI table",
                "url": pilot.TOI_URL,
                "retrieved": retrieved["toi.csv"],
                "notes": "Exclusions, deduplication and the false-positive pool; inputs.json.",
            },
            {
                "name": "ExoFOP-TESS CTOI table",
                "url": pilot.CTOI_URL,
                "retrieved": retrieved["ctoi.csv"],
                "notes": "Exclusions and deduplication; inputs.json.",
            },
            {
                "name": "NASA Exoplanet Archive, Planetary Systems Composite Parameters",
                "url": pilot.NEA_TAP,
                "retrieved": retrieved["pscomppars.csv"],
                "notes": "Exclusions, deduplication and the planet pool; inputs.json.",
            },
            {
                "name": "TESS-EB, Prsa et al. 2022 (VizieR J/ApJS/258/16/tess-ebs)",
                "url": pilot.TESS_EB_URL,
                "retrieved": retrieved["tess_eb.tsv"],
                "notes": (
                    "The static edition obtained 2026-10-18 (content SHA-256 equal to the v0.2 "
                    f"snapshot's). Not redistributed (#33): {EB_CATALOG} holds reference rows "
                    f"only, resolved at run time from a local copy checked against {EB_SCAN}."
                ),
            },
            {
                "name": "Gaia DR3 eclipsing-binary candidates (the v0.2.0 release asset)",
                "url": pilot.GAIA_EB_URL,
                "retrieved": retrieved["gaia_dr3_eb.csv"],
                "notes": (
                    f"Rows within {EXTRACT_RADIUS_ARCSEC:g} arcsec of the targets, in "
                    f"{EB_CATALOG}; snapshot hash in {EB_SCAN}."
                ),
            },
            {
                "name": "MAST: TIC fields and SPOC 120-s light curve and pixel file listings",
                "url": "https://mast.stsci.edu",
                "retrieved": "2026-10-30",
                "notes": (
                    "Queried live during the selection walk; each answer and its time are in "
                    "selection/selection.json. Data are downloaded at run time, with their "
                    "hashes in every dossier."
                ),
            },
        ],
        "attachments": [
            {"path": "selection/targets.yaml", "role": "targets"},
            {"path": "PROTOCOL.md", "role": "protocol"},
            {"path": "inputs.json", "role": "snapshot-index"},
            {"path": "selection/selection.json", "role": "selection-log"},
            {"path": EB_CATALOG, "role": "eb-catalog"},
            {"path": EB_SCAN, "role": "eb-catalog-scan"},
        ],
        "test_plan": claim_test_plan(step_dir, inputs),
    }


def write_claim(
    step_dir: Path, inputs_dir: Path, inputs: dict[str, Any], created: str, **expected: Any
) -> dict[str, Any]:
    """Write ``eb_catalog.csv``, ``eb_catalog_scan.json`` and ``claim.yaml`` in ``step_dir``,
    once: an existing file is never written over. ``expected`` goes to ``eb_attachments``."""
    import yaml

    paths = [step_dir / name for name in (CLAIM_NAME, EB_CATALOG, EB_SCAN)]
    existing = [p.name for p in paths if p.exists()]
    if existing:
        raise sel.SelectionError("already written, never written over: " + ", ".join(existing))
    targets_doc = yaml.safe_load((step_dir / "selection" / "targets.yaml").read_text("utf-8"))
    catalog, scan = eb_attachments(targets_doc["targets"], inputs_dir, inputs, **expected)
    document = claim_document(step_dir, inputs, targets_doc, created)
    header = (
        "# Refute v0.4 pilot claim (calibration/v0.4/PROTOCOL.md, section 12, step 3).\n"
        "# Written by calibration/v0.4/write_claim.py (refute.packs.tess.discover.claim) after\n"
        "# the selection: the v0.2 thresholds on the legacy path with H4, H7 and H9a (every\n"
        "# default of this commit written out). Locked with `refute lock` from a clean tree.\n"
    )
    contents = {
        EB_CATALOG: catalog,
        EB_SCAN: json.dumps(scan, indent=2, sort_keys=True) + "\n",
        CLAIM_NAME: header + yaml.safe_dump(document, sort_keys=False, allow_unicode=True),
    }
    for name, text in contents.items():  # everything is built before the first write
        with open(step_dir / name, "x", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
    return {"claim": document, "scan": scan}
