"""The committed v0.5 C3 claim (calibration/v0.5/claim.yaml; PROTOCOL.md section 8, step 3; the
S4 deviation of calibration/v0.5/deviation/README.md, #199) against the files it names: it
resolves, every recorded SHA-256 is the file's, its targets are the selection's controls and
reserves in order (the projection of selection/targets.yaml), the catalog extraction covers
every target, its plan is the one c3-run rebuilds with the S2 roles, and the claim is the
generated one with only the declared packaging change. Repository files only, no network."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest
import yaml

from refute.core.claim import load_claim
from refute.packs.tess.calib05 import c3run
from refute.packs.tess.calib05.plans import v05_plan
from refute.packs.tess.calib05.values import C3, V05_DECISIVE, V05_DIAGNOSTIC
from refute.packs.tess.schema import TessClaimSchema

ROOT = Path(__file__).resolve().parent.parent
STEP = ROOT / "calibration" / "v0.5"
CLAIM = STEP / "claim.yaml"
DEVIATION = STEP / "deviation"

pytestmark = pytest.mark.skipif(not CLAIM.is_file(), reason="the v0.5 claim is not written yet")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _projection_module():
    if str(DEVIATION) not in sys.path:
        sys.path.insert(0, str(DEVIATION))
    path = DEVIATION / "project_targets.py"
    spec = importlib.util.spec_from_file_location("v05_claim_committed_projection", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def loaded():
    return load_claim(CLAIM)


@pytest.fixture(scope="module")
def inputs():
    return json.loads((STEP / "inputs.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def selection():
    return json.loads((STEP / "selection" / "selection.json").read_text(encoding="utf-8"))


def test_the_claim_is_the_c3_discover_claim(loaded):
    assert loaded.claim.id == c3run.CLAIM_ID == "tess-calibration-v0.5-c3"
    assert loaded.claim.kind == "discover" and loaded.claim.pack == "tess"
    assert loaded.claim.pass_criteria is None
    assert loaded.claim.definitions["method_status"] == "not_validated"


def test_every_recorded_input_is_the_file(loaded, inputs):
    recorded = loaded.claim.test_plan["discovery"]["inputs"]
    assert set(recorded) == set(c3run.REPOSITORY_INPUTS) | set(c3run.RECORDED_INPUTS)
    for key, path in c3run.REPOSITORY_INPUTS.items():
        assert recorded[key] == _sha(STEP / path), key
    files = {i["name"]: i["sha256"] for i in inputs["files"]}
    for key, name in c3run.RECORDED_INPUTS.items():
        assert recorded[key] == files[name], key
    assert inputs["code"]["sha256"] == (
        "15a9c256b5aa8f6b6f1eb9db511420ee1efca15b95edd9343322d7c3bb52bf8e"
    )


def test_s_max_bounds_every_read(loaded, inputs):
    assert loaded.claim.test_plan["discovery"]["max_sector"] == inputs["s_max"] == 107


def test_the_targets_are_the_selection_in_order(loaded, selection):
    run_keys = [t["key"] for t in TessClaimSchema().targets_for_run(loaded)]
    expected = []
    for pool in ("planet", "false_positive"):
        record = selection["pools"][pool]
        size = C3.planets if pool == "planet" else C3.false_positives
        assert len(record["chosen"]) == size
        assert len(record["reserves"]) == C3.reserves and record["short"] == 0
        expected += [f"TIC-{tic}" for tic in record["chosen"] + record["reserves"]]
    assert run_keys == expected and len(run_keys) == 22
    assert selection["round"] == 6612465 and selection["complete"] is True
    assert selection["beacon"]["signature_verified"] is True
    assert selection["protocol_commit"] == "5f987db383e2d12beaa8583437953b4002799ef7"


def test_the_targets_attachment_is_the_projection_of_the_selection(loaded):
    proj = _projection_module()
    attachment = loaded.attachment_by_role("targets")
    assert attachment.path == "claim-targets.yaml"
    original = loaded.attachment_by_role("selection-targets")
    assert original.path == "selection/targets.yaml"
    source = (STEP / "selection" / "targets.yaml").read_text(encoding="utf-8")
    projected, removed = proj.project_targets(source)
    assert loaded.attachment_path(attachment).read_text(encoding="utf-8") == projected
    assert [r["key"] for r in removed].count("c3_place") == 22
    assert [r["key"] for r in removed].count("fp_class") == 11


def test_the_claim_is_the_generated_one_with_the_declared_change_only():
    proj = _projection_module()
    generated = (DEVIATION / "claim.generated.yaml").read_text(encoding="utf-8")
    assert CLAIM.read_text(encoding="utf-8") == proj.patch_claim(generated)
    record = json.loads((DEVIATION / "projection.json").read_text(encoding="utf-8"))
    for path, digest in {**record["inputs"], **record["outputs"]}.items():
        assert _sha(ROOT / path) == digest, path
    assert _sha(DEVIATION / "project_targets.py") == record["script_sha256"]


def test_the_plan_is_the_one_c3_run_rebuilds_with_the_s2_roles(loaded, inputs):
    plan = yaml.safe_load(CLAIM.read_text(encoding="utf-8"))["test_plan"]
    assert plan == v05_plan(c3run.v04_plan_for(ROOT, inputs, STEP))
    discovery = loaded.claim.test_plan["discovery"]
    assert discovery["decisive"] == list(V05_DECISIVE)
    assert discovery["diagnostic"] == list(V05_DIAGNOSTIC)
    assert "centroid_shift" not in discovery["decisive"]
    assert discovery["method_status"] == "not_validated"


def test_the_catalog_extraction_covers_every_target(loaded, inputs):
    scan_path = loaded.attachment_path(loaded.attachment_by_role("eb-catalog-scan"))
    scan = json.loads(scan_path.read_text(encoding="utf-8"))
    keys = {t["key"] for t in TessClaimSchema().targets_for_run(loaded)}
    assert set(scan["per_target"]) == keys
    match = loaded.claim.test_plan["gauntlet"]["eb_catalog"]["match_radius_arcsec"]
    assert scan["radius_arcsec"] >= match
    files = {i["name"]: i for i in inputs["files"]}
    tess, gaia = scan["snapshots"]
    assert tess["sha256"] == files["tess_eb.tsv"]["sha256"] and tess["redistributed"] is False
    assert tess["content_sha256"] == files["tess_eb.tsv"]["static_edition"]["content_sha256"]
    assert tess["cache_path"] == "v04/tess-eb/tess_ebs_prsa2022.tsv"
    assert gaia["sha256"] == files["gaia_dr3_eb.csv"]["sha256"]
    rows = (STEP / "eb_catalog.csv").read_text(encoding="utf-8").splitlines()[1:]
    assert len(rows) == scan["rows"] == 17
    # TESS-EB is never redistributed: its rows carry no coordinates and no period
    assert all(r.endswith(",,,") for r in rows if r.startswith("TESS-EB,"))


def test_the_attachments_are_committed_files_of_the_step(loaded):
    paths = [a.path for a in loaded.claim.attachments]
    assert paths == [
        "claim-targets.yaml",
        "selection/targets.yaml",
        "PROTOCOL.md",
        "inputs.json",
        "selection/selection.json",
        "eb_catalog.csv",
        "eb_catalog_scan.json",
    ]
    for attachment in loaded.claim.attachments:
        assert loaded.attachment_path(attachment).is_file(), attachment.path
