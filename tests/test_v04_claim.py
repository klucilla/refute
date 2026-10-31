"""v0.4 step 3 (calibration/v0.4/PROTOCOL.md, section 12): the pilot's claim is written from the
committed selection, with its eclipsing-binary attachments extracted from the frozen snapshots,
and the controls' signal identity of section 4.3. Synthetic data only."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
import yaml

from conftest import target_entry, targets_file, write_yaml
from refute.core.claim import load_claim
from refute.packs.tess.discover import claim
from refute.packs.tess.discover.case import build_case, signal_identity
from refute.packs.tess.discover.selection import SelectionError
from refute.packs.tess.ebcatalog import content_sha256

TESS_EB = (
    "#RESOURCE=synthetic\n"
    "TIC\tm_TIC\tRAJ2000\tDEJ2000\tPer\n"
    "\t\tdeg\tdeg\td\n"
    "----\t--\t----\t----\t----\n"
    "11\t1\t10.0100\t-20.0000\t2.5\n"  # 36 arcsec from TIC-1
    "12\t1\t50.0000\t40.0000\t1.1\n"  # far from every target
    "2\t1\t80.0000\t10.0000\t3.3\n"  # the second target's own TIC, far from its position
)
GAIA = (
    "source_id,ra,dec,frequency\n"
    "4295806720123456789,10.0000,-20.0100,0.5\n"  # 36 arcsec from TIC-1
    "4295806720123456790,10.2000,-20.0000,0.5\n"  # 676 arcsec from TIC-1
    "4295806720123456791,30.0000,5.0000,0.0\n"  # on TIC-2, no period
)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _record(name: str, data: bytes) -> dict:
    return {"name": name, "sha256": _sha(data), "retrieved_utc": "2026-10-29T21:24:00Z"}


@pytest.fixture
def step(tmp_path: Path):
    step_dir = tmp_path / "calibration" / "v0.4"
    inputs_dir = tmp_path / "attempt"
    inputs_dir.mkdir(parents=True)
    small = {n: n.encode() for n in ("target_lists.html", "frame.csv", "toi.csv", "ctoi.csv")}
    small["pscomppars.csv"] = b"pscomppars"
    files = {**small, "tess_eb.tsv": TESS_EB.encode(), "gaia_dr3_eb.csv": GAIA.encode()}
    for name, data in files.items():
        (inputs_dir / name).write_bytes(data)
    inputs = {
        "s_max": 107,
        "attempt": "attempt-07",
        "files": [_record(n, d) for n, d in files.items()],
    }
    step_dir.mkdir(parents=True)
    (step_dir / "PROTOCOL.md").write_bytes(b"# protocol\n")
    (step_dir / "inputs.json").write_bytes(json.dumps(inputs).encode())
    planet = target_entry(1, "planet", 3.7, name="Synthetic b")
    explore = target_entry(2, "exploration", None)
    planet["mast"] = {"tic_ra": 10.0, "tic_dec": -20.0}
    explore["mast"] = {"tic_ra": 30.0, "tic_dec": 5.0}
    doc = targets_file([planet, explore])
    doc["selection"] = {"round": 6598335, "protocol_commit": "0" * 40, "file": "selection.json"}
    write_yaml(step_dir / "selection" / "targets.yaml", doc)
    (step_dir / "selection" / "selection.json").write_bytes(b'{"complete": true}\n')
    expected = {"tess_eb_content_sha256": content_sha256(TESS_EB.encode()), "gaia_rows": 3}
    return step_dir, inputs_dir, inputs, expected


def test_the_claim_resolves_with_its_inputs_and_s_max(step):
    step_dir, inputs_dir, inputs, expected = step
    claim.write_claim(step_dir, inputs_dir, inputs, "2026-10-30", **expected)
    loaded = load_claim(step_dir / "claim.yaml")
    assert loaded.claim.kind == "discover" and loaded.claim.id == claim.CLAIM_ID
    discovery = loaded.claim.test_plan["discovery"]
    assert discovery["max_sector"] == 107
    assert discovery["decisive"] == list(claim.DECISIVE)
    assert discovery["diagnostic"] == ["holdout_by_year"]
    assert discovery["stages"] == {"centroid_shift": 2, "aperture_depth": 2}
    recorded = {i["name"]: i["sha256"] for i in inputs["files"]}
    on_disk = {
        "protocol": _sha((step_dir / "PROTOCOL.md").read_bytes()),
        "inputs_json": _sha((step_dir / "inputs.json").read_bytes()),
        "selection": _sha((step_dir / "selection" / "selection.json").read_bytes()),
    }
    assert discovery["inputs"] == {
        **on_disk,
        **{key: recorded[name] for key, name in claim.RECORDED_INPUTS.items()},
    }
    roles = {a.role: a.path for a in loaded.claim.attachments}
    assert roles["targets"] == "selection/targets.yaml"
    assert (
        roles["eb-catalog"] == "eb_catalog.csv"
        and roles["eb-catalog-scan"] == "eb_catalog_scan.json"
    )
    # the legacy path: corrections block version 1, disabled
    assert loaded.claim.test_plan["gauntlet"]["corrections"]["version"] == 1
    assert loaded.claim.test_plan["gauntlet"]["corrections"]["enabled"] is False
    assert loaded.claim.pass_criteria is None


def test_the_catalog_rows_are_extracted_around_each_target(step):
    step_dir, inputs_dir, inputs, expected = step
    out = claim.write_claim(step_dir, inputs_dir, inputs, "2026-10-30", **expected)
    lines = (step_dir / "eb_catalog.csv").read_text("utf-8").splitlines()
    assert lines[0] == "catalog,source_id,tic_id,ra_deg,dec_deg,period_days"
    rows = [line.split(",") for line in lines[1:]]
    # TESS-EB as reference rows only: a neighbour within 120 arcsec and the target's own TIC
    assert ["TESS-EB", "TIC 11 (1)", "11", "", "", ""] in rows
    assert ["TESS-EB", "TIC 2 (1)", "2", "", "", ""] in rows
    assert not any(r[1] == "TIC 12 (1)" for r in rows)
    gaia = {r[1]: r for r in rows if r[0] == "Gaia-DR3-EB"}
    assert set(gaia) == {"4295806720123456789", "4295806720123456791"}  # full 19-digit ids
    assert gaia["4295806720123456789"][5] == "2"
    assert gaia["4295806720123456791"][5] == ""  # a zero frequency has no period
    scan = out["scan"]
    assert scan["per_target"] == {
        "TIC-1": {"tess_eb": 1, "gaia": 1},
        "TIC-2": {"tess_eb": 1, "gaia": 1},
    }
    assert scan["radius_arcsec"] >= 21.0
    tess, gaia_snap = scan["snapshots"]
    assert tess["redistributed"] is False and tess["cache_path"] == claim.TESS_EB_CACHE_PATH
    assert tess["content_sha256"] == expected["tess_eb_content_sha256"]
    assert gaia_snap["rows"] == 3 and gaia_snap["redistributed"] is True


def test_nothing_is_written_over_and_nothing_partial_is_left(step):
    step_dir, inputs_dir, inputs, expected = step
    (step_dir / "eb_catalog.csv").write_text("old", encoding="utf-8")
    with pytest.raises(SelectionError, match="never written over"):
        claim.write_claim(step_dir, inputs_dir, inputs, "2026-10-30", **expected)
    assert not (step_dir / "claim.yaml").exists()
    (step_dir / "eb_catalog.csv").unlink()
    doc = yaml.safe_load((step_dir / "selection" / "targets.yaml").read_text("utf-8"))
    doc["targets"][1]["mast"] = {"tic_ra": None, "tic_dec": 5.0}
    write_yaml(step_dir / "selection" / "targets.yaml", doc)
    with pytest.raises(SelectionError, match="no valid position"):
        claim.write_claim(step_dir, inputs_dir, inputs, "2026-10-30", **expected)
    assert not any((step_dir / n).exists() for n in ("claim.yaml", "eb_catalog.csv"))


@pytest.mark.parametrize("name", ["tess_eb.tsv", "gaia_dr3_eb.csv"])
def test_a_snapshot_that_is_not_the_recorded_one_stops_the_step(step, name):
    step_dir, inputs_dir, inputs, expected = step
    (inputs_dir / name).write_bytes((inputs_dir / name).read_bytes() + b"\n")
    with pytest.raises(SelectionError, match="recorded SHA-256"):
        claim.write_claim(step_dir, inputs_dir, inputs, "2026-10-30", **expected)


def test_the_tess_eb_snapshot_must_be_the_static_edition(step):
    step_dir, inputs_dir, inputs, expected = step
    with pytest.raises(SelectionError, match="static edition"):
        claim.write_claim(
            step_dir,
            inputs_dir,
            inputs,
            "2026-10-30",
            **{**expected, "tess_eb_content_sha256": "0" * 64},
        )


def _verdict(published: float | None, found: float | None, t0_pub=None, t0_found=None) -> dict:
    return {
        "period_comparison": {"published_period_days": published, "found_period_days": found},
        "published": {"t0_bjd": t0_pub},
        "candidate": None if found is None else {"t0_bjd": t0_found},
    }


@pytest.mark.parametrize(
    ("kind", "found", "factor"),
    [
        ("planet", 3.0029, 1.0),  # relative error 0.00097
        ("planet", 3.0031, None),  # 0.00103: outside
        ("planet", 6.0, None),  # aliases do not count for the planet
        ("false_positive", 6.0, 2.0),
        ("false_positive", 1.5, 0.5),
        ("false_positive", 9.0, None),  # 3P is not a declared factor
    ],
)
def test_signal_identity_of_the_controls(kind, found, factor):
    out = signal_identity(_verdict(3.0, found), kind)
    assert out["matched_factor"] == factor
    assert out["identified"] is (factor is not None)
    assert out["period_tolerance"] == 0.001


def test_signal_identity_reports_the_epoch_and_ignores_funnel_stars():
    out = signal_identity(_verdict(3.0, 3.0, t0_pub=2459000.0, t0_found=2459300.1), "planet")
    assert out["epoch_difference_days"] == pytest.approx(0.1)
    assert out["epoch_note"] == "reported, not required"
    # reported also when the period does not match (Codex round review of the lock commits)
    missed = signal_identity(_verdict(3.0, 3.5, t0_pub=2459000.0, t0_found=2459003.4), "planet")
    assert missed["identified"] is False
    assert missed["epoch_difference_days"] == pytest.approx(-0.1)
    half = signal_identity(_verdict(3.0, 2.0, t0_pub=2459000.0, t0_found=2459001.0), "planet")
    assert half["epoch_difference_days"] == pytest.approx(-1.0)  # the range is [-P/2, P/2)
    assert signal_identity(_verdict(3.0, None), "planet")["identified"] is False
    assert signal_identity(_verdict(3.0, 3.0), "exploration") is None
    case = build_case(_verdict(3.0, 3.0), {"kind": "false_positive"}, None, None)
    assert case["identity"]["signal_identity"]["identified"] is True
