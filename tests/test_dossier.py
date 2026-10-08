"""End-to-end runs on synthetic data written into a temporary cache (no network)."""

from pathlib import Path

import pytest

from conftest import (
    calibration_claim,
    git,
    replicate_claim,
    target_entry,
    targets_file,
    write_yaml,
)
from refute.core.dossier import (
    MANIFEST_NAME,
    check_dossier,
    compare_dossiers,
    verify_manifest,
)
from refute.core.io import read_json
from refute.core.lock import create_lock
from refute.core.run import execute_run
from refute.packs.tess.synthetic import scenario_data, write_synthetic_cache

EXPECTED_FILES = [
    "claim.yaml",
    "claim.lock.json",
    "integrity.json",
    "target.json",
    "verdict.json",
    "report.md",
    "REPRODUCE.md",
    MANIFEST_NAME,
    "data/manifest.json",
    "environment/environment.json",
    "environment/requirements.txt",
    "environment/uv.lock",
    "export/ctoi_fields.json",
    "export/ctoi_summary.md",
    "plots/full.png",
    "plots/phase.png",
    "plots/odd_even.png",
    "plots/secondary.png",
    "plots/holdout_2018.png",
    "plots/holdout_2020.png",
]


def _cache(tmp_path: Path, scenarios: dict[int, str]) -> Path:
    cache = tmp_path / "cache"
    for tic, name in scenarios.items():
        data = scenario_data(name)
        write_synthetic_cache(cache, tic, data.lc, data.star, aux=data.aux)
    return cache


@pytest.fixture(scope="module")
def replicate_run(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("replicate")
    cache = _cache(tmp, {1: "planet"})
    claim = write_yaml(
        tmp / "claims" / "claim.yaml", replicate_claim([target_entry(1, "planet", 3.7)])
    )
    create_lock(claim)
    first = execute_run(
        claim,
        mode="replicate",
        out_dir=tmp / "out",
        workers=1,
        offline=True,
        run_id="a",
        cache_dir=cache,
    )
    second = execute_run(
        claim,
        mode="replicate",
        out_dir=tmp / "out",
        workers=1,
        offline=True,
        run_id="b",
        cache_dir=cache,
    )
    return tmp, first, second


def test_replicate_run_writes_a_complete_dossier(replicate_run):
    _, first, _ = replicate_run
    assert first.exit_code == 0, first.messages
    dossier = first.run_dir / "TIC-1"
    for name in EXPECTED_FILES:
        assert (dossier / name).is_file(), name
    assert verify_manifest(dossier) == []
    verdict = read_json(dossier / "verdict.json")
    assert verdict["verdict"] == "SURVIVED"
    assert verdict["status"] == "OK"
    assert {t["name"] for t in verdict["tests"]} == {
        "snr",
        "odd_even",
        "secondary_eclipse",
        "plausibility",
        "centroid_shift",
        "aperture_depth",
        "nearby_contamination",
        "period_alias",
        "systematics",
        "holdout_by_year",
    }
    assert verdict["eb_catalog_configured"] is False
    assert verdict["key_values"]["period_days"] == pytest.approx(3.7, rel=1e-3)
    manifest = read_json(dossier / "data/manifest.json")
    assert manifest["schema"] == "refute-tess-data-manifest-2"
    assert manifest["product"]["product"].startswith("TESS SPOC")
    assert all(len(f["sha256"]) == 64 for f in manifest["files"])
    assert any(f.get("kind") == "target pixel file" for f in manifest["files"])
    reproduce = (dossier / "REPRODUCE.md").read_text(encoding="utf-8")
    assert "uv sync --frozen" in reproduce
    # Issue #7: a runnable clone line and an explained dossier placeholder.
    assert "git clone https://github.com/klucilla/refute.git refute" in reproduce
    assert "<URL of the Refute repository>" not in reproduce
    assert "the folder that contains this" in reproduce
    assert "refute replicate" in reproduce and "--target TIC-1" in reproduce
    assert "check-dossier" in reproduce
    integrity = read_json(dossier / "integrity.json")
    assert integrity["status"] == "PASS"
    assert (first.run_dir / "summary.json").is_file()
    assert (first.run_dir / "summary.md").is_file()


def test_rerun_reproduces_the_dossier(replicate_run):
    _, first, second = replicate_run
    assert second.exit_code == 0
    assert compare_dossiers(second.run_dir / "TIC-1", first.run_dir / "TIC-1") == []
    result = check_dossier(second.run_dir / "TIC-1", first.run_dir / "TIC-1")
    assert result.ok


def test_tampered_dossier_is_detected(replicate_run, tmp_path):
    _, first, _ = replicate_run
    import shutil

    copy = tmp_path / "copy"
    shutil.copytree(first.run_dir / "TIC-1", copy)
    (copy / "report.md").write_text("edited", encoding="utf-8")
    assert verify_manifest(copy) == ["modified file: report.md"]
    verdict = read_json(copy / "verdict.json")
    verdict["verdict"] = "REFUTED"
    (copy / "verdict.json").write_text(__import__("json").dumps(verdict), encoding="utf-8")
    differences = compare_dossiers(copy, first.run_dir / "TIC-1")
    assert any(d.startswith("verdict:") for d in differences)


def test_offline_run_without_cache_records_an_error(tmp_path):
    claim = write_yaml(
        tmp_path / "claims" / "claim.yaml", replicate_claim([target_entry(7, "planet", 3.7)])
    )
    create_lock(claim)
    outcome = execute_run(
        claim,
        mode="replicate",
        out_dir=tmp_path / "out",
        workers=1,
        offline=True,
        cache_dir=tmp_path / "empty-cache",
    )
    assert outcome.exit_code == 0
    verdict = read_json(outcome.run_dir / "TIC-7" / "verdict.json")
    assert verdict["status"] == "ERROR"
    assert verdict["verdict"] == "INCONCLUSIVE"
    assert "no cached data" in verdict["error"]
    assert verify_manifest(outcome.run_dir / "TIC-7") == []


def test_unlocked_claim_is_refused(tmp_path):
    claim = write_yaml(tmp_path / "claim.yaml", replicate_claim([target_entry(1, "planet", 3.7)]))
    outcome = execute_run(claim, mode="replicate", out_dir=tmp_path / "out", offline=True)
    assert outcome.exit_code == 1
    outcome = execute_run(claim, mode="calibrate", out_dir=tmp_path / "out", offline=True)
    assert outcome.exit_code == 1


def test_calibration_run_evaluates_the_self_claim(git_repo, tmp_path):
    cache = _cache(tmp_path, {11: "planet", 12: "planet_three_years", 21: "eb_equal", 31: "planet"})
    targets = [
        target_entry(11, "planet", 3.7),
        target_entry(12, "planet", 3.7),
        target_entry(21, "false_positive", 1.6),
        target_entry(31, "development", 3.7),
    ]
    write_yaml(git_repo / "calibration" / "targets.yaml", targets_file(targets))
    claim = write_yaml(git_repo / "calibration" / "claim.yaml", calibration_claim(2, 1))
    git(git_repo, "add", "-A")
    git(git_repo, "commit", "-q", "-m", "commit A")
    create_lock(claim)

    outcome = execute_run(
        claim,
        mode="calibrate",
        out_dir=tmp_path / "out",
        workers=3,
        offline=True,
        run_id="cal",
        cache_dir=cache,
    )
    assert outcome.exit_code == 0, outcome.messages
    summary = outcome.summary
    assert summary["self_claim"]["result"] == "PASS", summary["self_claim"]
    keys = sorted(row["target"] for row in summary["targets"])
    assert keys == ["TIC-11", "TIC-12", "TIC-21"], "the development target is never run"
    assert not (outcome.run_dir / "TIC-31").exists()
    criteria = {c["criterion"]: c for c in summary["self_claim"]["criteria"]}
    assert criteria["recovered planets"]["value"] == 2
    assert criteria["flagged false positives"]["value"] == 1
    assert criteria["refuted planets (degeneracy guard)"]["value"] == 0
    text = (outcome.run_dir / "summary.md").read_text(encoding="utf-8")
    assert "Self-claim result: **PASS**" in text
    assert "easy regime" in text
    report = (outcome.run_dir / "TIC-11" / "report.md").read_text(encoding="utf-8")
    assert "easy regime" in report

    partial = execute_run(
        claim,
        mode="calibrate",
        targets=["TIC-11"],
        out_dir=tmp_path / "out",
        workers=1,
        offline=True,
        run_id="partial",
        cache_dir=cache,
    )
    assert partial.summary["self_claim"]["result"] == "NOT_EVALUATED"
