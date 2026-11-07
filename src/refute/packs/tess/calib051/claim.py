"""The version-3 ``discover`` claim of the v0.5.1 calibration, generalized from
``calib05.c3run.write_claim``: one claim for a targets document (controls and reserves), with the
v0.4 compatibility plan's thresholds, the version-3 battery (``plans.v051_plan``), ``max_sector``
the inputs' ``s_max``, the SHA-256 of the protocol, the inputs index and the targets in
``discovery.inputs``, and the eclipsing-binary attachments (``discover.claim.eb_attachments``).
It is the claim ``refute discover`` runs. Every file is written once, never over a file."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

from refute.packs.tess.calib051.values import C3, PROTOCOL_ID

CLAIM_NAME = "claim.yaml"
TARGETS_NAME = "claim-targets.yaml"
SELECTION_TARGETS_NAME = "selection-targets.yaml"
PROTOCOL_NAME = "PROTOCOL.md"
INPUTS_NAME = "inputs.json"
EB_CATALOG = "eb_catalog.csv"
EB_SCAN = "eb_catalog_scan.json"
# the selection's own fields, which the TESS targets schema refuses (the v0.5 S4 deviation,
# calibration/v0.5/deviation/README.md): kept in the selection document, removed from the
# claim's targets file
SELECTION_ONLY_KEYS = ("c3_place", "fp_class")
ATTACHMENTS = (
    (TARGETS_NAME, "targets"),
    (SELECTION_TARGETS_NAME, "selection-targets"),
    (PROTOCOL_NAME, "protocol"),
    (INPUTS_NAME, "snapshot-index"),
    (EB_CATALOG, "eb-catalog"),
    (EB_SCAN, "eb-catalog-scan"),
)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def project_targets(targets_doc: dict[str, Any]) -> dict[str, Any]:
    """The claim's targets document: the selection's document without the selection-only keys,
    validated by the TESS targets schema (``params.TargetsFile``) before anything is written."""
    from refute.packs.tess.params import TargetsFile

    projected = copy.deepcopy(targets_doc)
    for target in projected["targets"]:
        for key in SELECTION_ONLY_KEYS:
            target.pop(key, None)
    TargetsFile.model_validate(projected)
    return projected


def write_claim(
    step_dir: Path,
    targets_doc: dict[str, Any],
    inputs_dir: Path,
    test_plan_v04: dict[str, Any],
    created: str,
    *,
    claim_id: str,
    title: str,
    hypothesis: str,
    eb_options: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Write ``selection-targets.yaml`` (the selection's document, its ``c3_place`` and
    ``fp_class`` included), ``claim-targets.yaml`` (its projection, ``project_targets``),
    ``eb_catalog.csv``, ``eb_catalog_scan.json`` and ``claim.yaml`` in ``step_dir``, which must
    already hold ``PROTOCOL.md`` and ``inputs.json``.
    ``eb_options`` passes the expected TESS-EB content SHA-256 and Gaia row count to
    ``eb_attachments`` (the frozen editions' by default; tests pass their synthetic ones)."""
    import yaml

    from refute.packs.tess.calib051.plans import v051_plan
    from refute.packs.tess.discover.claim import eb_attachments

    step = Path(step_dir)
    for name in (PROTOCOL_NAME, INPUTS_NAME):
        if not (step / name).is_file():
            raise FileNotFoundError(f"{step / name} is needed before the claim is written")
    names = (CLAIM_NAME, TARGETS_NAME, SELECTION_TARGETS_NAME, EB_CATALOG, EB_SCAN)
    existing = [n for n in names if (step / n).exists()]
    if existing:
        raise FileExistsError("already written, never written over: " + ", ".join(existing))
    inputs = json.loads((step / INPUTS_NAME).read_text(encoding="utf-8"))
    catalog, scan = eb_attachments(targets_doc["targets"], inputs_dir, inputs, **(eb_options or {}))
    selection_text = yaml.safe_dump(targets_doc, sort_keys=False, allow_unicode=True)
    targets_text = yaml.safe_dump(project_targets(targets_doc), sort_keys=False, allow_unicode=True)
    plan = copy.deepcopy(test_plan_v04)
    plan["discovery"]["inputs"] = {
        "protocol": _sha((step / PROTOCOL_NAME).read_bytes()),
        "inputs_json": _sha((step / INPUTS_NAME).read_bytes()),
        "selection_targets": _sha(selection_text.encode("utf-8")),
        "targets": _sha(targets_text.encode("utf-8")),
    }
    plan["discovery"]["max_sector"] = int(inputs["s_max"])
    test_plan = v051_plan(plan)
    document = {
        "schema_version": 1,
        "id": claim_id,
        "kind": "discover",
        "pack": "tess",
        "title": title,
        "hypothesis": hypothesis,
        "created": created,
        "authors": ["Klauber Lucilla"],
        "definitions": {
            "protocol": f"{PROTOCOL_ID}, {PROTOCOL_NAME}.",
            "signal_identity": (
                "The planet's found period within a relative tolerance of "
                f"{C3.identity_period_tolerance:g} of the published period; the false positive's "
                f"at one of the factors {list(C3.fp_identity_factors)}. Decided before any "
                "disposition is scored."
            ),
            "verdict": (
                "Aggregated from the decisive tests only, with the severity each test emits "
                "(docs/verdicts.md); every INCONCLUSIVE carries its class (WP4). Never "
                "'confirmed', 'discovery', 'TRUE' or a planet letter."
            ),
            "method_status": "not_validated",
            "max_sector": f"S_max = {inputs['s_max']} (test_plan.discovery.max_sector).",
        },
        "data_sources": [
            {
                "name": f["name"],
                "url": f["url"],
                "retrieved": f["retrieved_utc"],
                "notes": f"SHA-256 {f['sha256']}; {INPUTS_NAME}.",
            }
            for f in inputs["files"]
        ],
        "attachments": [{"path": p, "role": r} for p, r in ATTACHMENTS],
        "test_plan": test_plan,
    }
    header = (
        f"# Refute v0.5.1 calibration claim ({PROTOCOL_ID}).\n"
        "# Written by refute.packs.tess.calib051.claim; locked with `refute lock` from a clean\n"
        "# tree.\n"
    )
    contents = {
        TARGETS_NAME: targets_text,
        SELECTION_TARGETS_NAME: selection_text,
        EB_CATALOG: catalog,
        EB_SCAN: json.dumps(scan, indent=2, sort_keys=True) + "\n",
        CLAIM_NAME: header + yaml.safe_dump(document, sort_keys=False, allow_unicode=True),
    }
    for name, text in contents.items():
        with open(step / name, "x", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
    return {"claim": document, "scan": scan}
