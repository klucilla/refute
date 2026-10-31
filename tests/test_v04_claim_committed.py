"""The committed v0.4 pilot claim (calibration/v0.4/claim.yaml, PROTOCOL.md section 12, step 3)
against the files it names: it resolves, every recorded SHA-256 is the file's, the targets are the
selection's in walk order, the catalog extraction covers every target, and the roles, stages and
thresholds are the protocol's. Repository files only, no network."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
import yaml

from refute.core.claim import load_claim
from refute.packs.tess.discover import claim as claim_module
from refute.packs.tess.discover import pilot
from refute.packs.tess.discover.protocol import CONTROLS, SELECTION, SURVIVED_MEANING
from refute.packs.tess.params import TessTestPlan

ROOT = Path(__file__).resolve().parent.parent
STEP = ROOT / "calibration" / "v0.4"
CLAIM = STEP / "claim.yaml"

pytestmark = pytest.mark.skipif(not CLAIM.is_file(), reason="the v0.4 claim is not written yet")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture(scope="module")
def loaded():
    return load_claim(CLAIM)


@pytest.fixture(scope="module")
def inputs():
    return json.loads((STEP / "inputs.json").read_text(encoding="utf-8"))


def test_the_claim_is_the_pilot_discover_claim(loaded):
    assert loaded.claim.id == claim_module.CLAIM_ID
    assert loaded.claim.kind == "discover" and loaded.claim.pack == "tess"
    assert loaded.claim.pass_criteria is None


def test_every_recorded_input_is_the_file(loaded, inputs):
    recorded = loaded.claim.test_plan["discovery"]["inputs"]
    assert set(recorded) == set(claim_module.REPOSITORY_INPUTS) | set(claim_module.RECORDED_INPUTS)
    for key, path in claim_module.REPOSITORY_INPUTS.items():
        assert recorded[key] == _sha(STEP / path), key
    files = {i["name"]: i["sha256"] for i in inputs["files"]}
    for key, name in claim_module.RECORDED_INPUTS.items():
        assert recorded[key] == files[name], key
    assert recorded["tess_eb"] == pilot.TESS_EB_STATIC["sha256"]
    assert recorded["gaia_dr3_eb"] == pilot.GAIA_EB_SHA256


def test_s_max_bounds_every_read(loaded, inputs):
    assert loaded.claim.test_plan["discovery"]["max_sector"] == inputs["s_max"] == 107


def test_the_targets_are_the_selection_in_walk_order(loaded):
    selection = json.loads((STEP / "selection" / "selection.json").read_text(encoding="utf-8"))
    path = loaded.attachment_path(loaded.attachment_by_role("targets"))
    targets = yaml.safe_load(path.read_text(encoding="utf-8"))["targets"]
    controls = [selection["controls"][k]["accepted"] for k in ("planet", "false_positive")]
    assert [t["tic_id"] for t in targets] == controls + selection["funnel"]["accepted"]
    assert [t["kind"] for t in targets[:2]] == ["planet", "false_positive"]
    assert {t["kind"] for t in targets[2:]} == {"exploration"}
    assert len(targets) == 2 + SELECTION.funnel_accepted
    assert selection["complete"] is True and selection["beacon"]["signature_verified"] is True


def test_the_catalog_extraction_covers_every_target(loaded):
    scan_path = loaded.attachment_path(loaded.attachment_by_role("eb-catalog-scan"))
    scan = json.loads(scan_path.read_text(encoding="utf-8"))
    targets_path = loaded.attachment_path(loaded.attachment_by_role("targets"))
    keys = {t["key"] for t in yaml.safe_load(targets_path.read_text(encoding="utf-8"))["targets"]}
    assert set(scan["per_target"]) == keys
    match = loaded.claim.test_plan["gauntlet"]["eb_catalog"]["match_radius_arcsec"]
    assert scan["radius_arcsec"] >= match == SELECTION.match_radius_arcsec
    tess, gaia = scan["snapshots"]
    assert tess["content_sha256"] == pilot.TESS_EB_STATIC["content_sha256"]
    assert tess["redistributed"] is False and tess["sha256"] == pilot.TESS_EB_STATIC["sha256"]
    assert gaia["sha256"] == pilot.GAIA_EB_SHA256 and gaia["rows"] == pilot.GAIA_EB_ROWS
    rows = (STEP / "eb_catalog.csv").read_text(encoding="utf-8").splitlines()[1:]
    assert len(rows) == scan["rows"]
    # TESS-EB is never redistributed: its rows carry no coordinates and no period
    assert all(r.endswith(",,,") for r in rows if r.startswith("TESS-EB,"))


def test_the_roles_stages_and_thresholds_are_the_protocols(loaded):
    discovery = loaded.claim.test_plan["discovery"]
    assert discovery["decisive"] == list(claim_module.DECISIVE)
    assert discovery["diagnostic"] == ["holdout_by_year"]
    assert discovery["required_diagnostics"] == ["holdout_by_year"]
    assert discovery["stages"] == {"centroid_shift": 2, "aperture_depth": 2}
    assert discovery["method_status"] == "not_validated"
    assert discovery["survived_meaning"] == SURVIVED_MEANING
    plan = dict(loaded.claim.test_plan)
    plan.pop("discovery")
    assert plan == TessTestPlan().model_dump(mode="json")  # every default, the legacy path
    assert plan["gauntlet"]["corrections"]["version"] == 1


def test_the_definitions_state_the_controls_identity_rule(loaded):
    text = loaded.claim.definitions["signal_identity"]
    assert f"period_tolerance of {CONTROLS.identity_period_tolerance:g}" in text
    factors = ", ".join(f"{f:g}" for f in CONTROLS.fp_identity_factors)
    assert f"flag_signal_period_factors [{factors}]" in text


def test_the_attachments_are_committed_files_of_the_step(loaded):
    for attachment in loaded.claim.attachments:
        assert loaded.attachment_path(attachment).is_file(), attachment.path
