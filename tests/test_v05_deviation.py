"""The scripts of the C3 claim-packaging deviation approved on 2026-11-04 (#199;
calibration/v0.5/deviation/README.md), on synthetic inputs only (no network, no real catalog)."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

from conftest import cache_test_dir

ROOT = Path(__file__).resolve().parents[1]
DEVIATION = ROOT / "calibration" / "v0.5" / "deviation"


def _load(name: str):
    if str(DEVIATION) not in sys.path:
        sys.path.insert(0, str(DEVIATION))
    spec = importlib.util.spec_from_file_location(f"v05_deviation_{name}", DEVIATION / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


proj = _load("project_targets")
prep = _load("prepare_tess_eb")
guard = _load("guarded_c3")

TARGETS = """schema: refute-tess-targets-1
generated_utc: '2026-11-04T15:18:39Z'
targets:
- key: TIC-1
  tic_id: 1
  kind: planet
  name: Synthetic b
  published:
    period_days: 3.0
  c3_place: chosen
- key: TIC-2
  tic_id: 2
  kind: false_positive
  name: TOI-2.01
  catalog:
    note: keep me
  c3_place: reserve 1
  fp_class: eclipsing_binary (TOI FP with TIC in TESS-EB)
"""

CLAIM = (
    "# Header line one.\n" + proj.HEADER_END + "id: synthetic\n"
    "attachments:\n" + proj.OLD_ATTACHMENT + "- path: PROTOCOL.md\n  role: protocol\n"
    "test_plan:\n  a: 1\n"
)


def test_projection_removes_exactly_the_two_fields():
    projected, removed = proj.project_targets(TARGETS)
    assert [r["key"] for r in removed] == ["c3_place", "c3_place", "fp_class"]
    assert [r["line"] for r in removed] == [10, 17, 18]
    assert "c3_place" not in projected and "fp_class" not in projected
    assert "    note: keep me\n" in projected
    checks = proj.check_targets(TARGETS, projected, removed)
    assert checks["target_keys_in_order"] == ["TIC-1", "TIC-2"]
    assert checks["removed_c3_place"] == 2 and checks["removed_fp_class"] == 1


def test_projection_refuses_a_block_scalar():
    text = TARGETS.replace("  fp_class: eclipsing_binary", "  fp_class: |\n    eclipsing_binary")
    projected, removed = proj.project_targets(text)
    with pytest.raises(proj.ProjectionError):
        proj.check_targets(text, projected, removed)


def test_projection_refuses_a_missing_field():
    text = TARGETS.replace("  c3_place: chosen\n", "")
    projected, removed = proj.project_targets(text)
    with pytest.raises(proj.ProjectionError):
        proj.check_targets(text, projected, removed)


def test_projection_refuses_a_changed_line():
    projected, removed = proj.project_targets(TARGETS)
    with pytest.raises(proj.ProjectionError):
        proj.check_targets(TARGETS, projected.replace("keep me", "changed"), removed)


def test_claim_patch_changes_only_the_attachments_and_the_header():
    patched = proj.patch_claim(CLAIM)
    checks = proj.check_claim(CLAIM, patched)
    assert checks["attachments"][:2] == [
        {"path": "claim-targets.yaml", "role": "targets"},
        {"path": "selection/targets.yaml", "role": "selection-targets"},
    ]
    with pytest.raises(proj.ProjectionError):
        proj.check_claim(CLAIM, patched.replace("a: 1", "a: 2"))
    with pytest.raises(proj.ProjectionError):
        proj.check_claim(CLAIM, patched.replace("# Header line one.", "# Other header."))
    with pytest.raises(proj.ProjectionError):
        proj.patch_claim(CLAIM.replace("  role: targets\n", "  role: other\n"))


def test_projection_never_writes_over_an_output():
    root = cache_test_dir("v05-deviation")
    (root / proj.OUT_CLAIM).parent.mkdir(parents=True)
    (root / proj.OUT_CLAIM).write_text("existing\n", encoding="utf-8")
    with pytest.raises(proj.ProjectionError, match="never written over"):
        proj.main(root)
    assert (root / proj.OUT_CLAIM).read_text(encoding="utf-8") == "existing\n"


# --- the TESS-EB placement ----------------------------------------------------------------

EDITION = (
    b"#\n# VizieR synthetic header\n#request_date 2026-10-18\n"
    b"TIC\tm_TIC\tRAJ2000\tDEJ2000\tPer\n\t\tdeg\tdeg\td\n---\t-\t---\t---\t---\n"
    b"11\t\t10.0\t20.0\t1.5\n"
)


def _snapshot_root(name: str) -> tuple[Path, dict]:
    from refute.packs.tess.ebcatalog import content_sha256

    root = cache_test_dir(name)
    step = root / "calibration" / "v0.5"
    step.mkdir(parents=True)
    source = root / "edition" / "tess_ebs_prsa2022.tsv"
    source.parent.mkdir()
    source.write_bytes(EDITION)
    raw, content = hashlib.sha256(EDITION).hexdigest(), content_sha256(EDITION)
    snap = {
        "catalog_name": "TESS-EB",
        "cache_path": "v04/tess-eb/tess_ebs_prsa2022.tsv",
        "file": "tess_eb.tsv",
        "redistributed": False,
        "sha256": raw,
        "content_sha256": content,
    }
    (step / "eb_catalog_scan.json").write_text(json.dumps({"snapshots": [snap]}), "utf-8")
    edition = {"path": "edition/tess_ebs_prsa2022.tsv", "content_sha256": content}
    inputs = {"files": [{"name": "tess_eb.tsv", "sha256": raw, "static_edition": edition}]}
    (step / "inputs.json").write_text(json.dumps(inputs), "utf-8")
    return root, prep.expected(root)


def test_placement_copies_once_and_never_writes_over():
    root, want = _snapshot_root("v05-deviation-eb")
    source = Path(want["default_source"])
    first = prep.place(root, Path(".cache-c3"), source, want)
    assert first["action"] == "copied"
    dest = root / ".cache-c3" / "v04" / "tess-eb" / "tess_ebs_prsa2022.tsv"
    assert dest.read_bytes() == EDITION
    assert prep.place(root, Path(".cache-c3"), source, want)["action"] == "already in place"
    dest.write_bytes(EDITION + b"12\t\t1.0\t2.0\t3.0\n")
    with pytest.raises(prep.PlacementError, match="never written over"):
        prep.place(root, Path(".cache-c3"), source, want)
    assert dest.read_bytes().endswith(b"12\t\t1.0\t2.0\t3.0\n")
    assert not list(dest.parent.glob("*.part"))


def test_placement_refuses_other_source_bytes_and_paths_outside():
    root, want = _snapshot_root("v05-deviation-eb2")
    source = root / want["default_source"]
    source.write_bytes(EDITION.replace(b"request_date 2026-10-18", b"request_date 2026-11-04"))
    with pytest.raises(prep.PlacementError, match="SHA-256"):
        prep.place(root, Path("c3"), source, want)
    assert not (root / "c3").exists()
    source.write_bytes(EDITION)
    with pytest.raises(prep.PlacementError, match="not inside"):
        prep.place(root, Path("../outside-c3"), source, want)
    with pytest.raises(prep.PlacementError, match="not inside"):
        prep.place(root, Path("c3"), Path("../elsewhere.tsv"), want)


def test_expected_refuses_hashes_other_than_the_frozen_ones():
    root, _ = _snapshot_root("v05-deviation-eb3")
    inputs_path = root / "calibration" / "v0.5" / "inputs.json"
    inputs = json.loads(inputs_path.read_text("utf-8"))
    inputs["files"][0]["sha256"] = "0" * 64
    inputs_path.write_text(json.dumps(inputs), "utf-8")
    with pytest.raises(prep.PlacementError, match="frozen"):
        prep.expected(root)


# --- the guard ------------------------------------------------------------------------------


def test_guard_refuses_a_projection_that_drifted():
    root = cache_test_dir("v05-deviation-guard")
    (root / proj.SOURCE_TARGETS).parent.mkdir(parents=True)
    (root / proj.SOURCE_TARGETS).write_text(TARGETS, encoding="utf-8")
    projected, _ = proj.project_targets(TARGETS)
    (root / proj.OUT_TARGETS).write_text(projected, encoding="utf-8")
    guard.check_projection(root)
    (root / proj.OUT_TARGETS).write_text(projected.replace("keep me", "x"), encoding="utf-8")
    with pytest.raises(guard.GuardError):
        guard.check_projection(root)


def test_guard_refuses_a_cache_without_the_edition():
    root, _ = _snapshot_root("v05-deviation-guard2")
    with pytest.raises(guard.GuardError, match="prepare_tess_eb"):
        guard.check_catalog(root, Path("c3"))


def test_guard_never_starts_the_frozen_step_unless_verify_passes(monkeypatch):
    import refute.core.lock as lock

    class Failed:
        class status:  # noqa: N801 - the shape of VerifyResult.status
            value = "TAMPERED"

        exit_code = 2
        messages = ["synthetic: the claim changed after the lock"]

    started = []
    monkeypatch.setattr(lock, "verify_claim", lambda path: Failed())
    monkeypatch.setattr(guard.subprocess, "run", lambda *a, **k: started.append(a))
    root = cache_test_dir("v05-deviation-guard3")
    root.mkdir(parents=True)
    monkeypatch.chdir(root)
    for argv in (["c3-run"], ["c3-fetch", "--cache", "c3"]):
        with pytest.raises(guard.GuardError, match="TAMPERED"):
            guard.main(argv)
    assert started == []


def test_guard_refuses_a_claim_plan_other_than_the_rebuilt_one(monkeypatch):
    import refute.packs.tess.calib05.c3run as c3run
    import refute.packs.tess.calib05.plans as plans

    root = cache_test_dir("v05-deviation-guard4")
    step = root / guard.STEP
    step.mkdir(parents=True)
    (step / "inputs.json").write_text("{}", encoding="utf-8")
    (root / guard.CLAIM).write_text("test_plan:\n  a: 1\n", encoding="utf-8")
    monkeypatch.setattr(c3run, "v04_plan_for", lambda root, inputs, step: {"base": True})
    monkeypatch.setattr(plans, "v05_plan", lambda plan: {"a": 1})
    guard.check_plan(root)
    monkeypatch.setattr(plans, "v05_plan", lambda plan: {"a": 2})
    with pytest.raises(guard.GuardError, match="test plan"):
        guard.check_plan(root)
