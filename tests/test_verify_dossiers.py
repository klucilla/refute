"""The dossier verification of the main sample of v0.3
(docs/validation/v0.3/dossier-verification-acceptance.md, section 4). The five published
dossiers are in the repository, so no case needs the network; every must-fail case changes a
copy in a temporary folder."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "calibration/v0.3/main"
SAMPLE = ("2302.12465", "2305.19518", "2309.15704", "2407.11735", "2502.16782")

_spec = importlib.util.spec_from_file_location(
    "verify_dossiers", ROOT / "calibration/v0.3/verify_dossiers.py"
)
vd = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(vd)


def _copy(tmp_path: Path, arxiv: str, name: str = "dossier") -> Path:
    target = tmp_path / arxiv / name
    shutil.copytree(MAIN / "dossiers" / arxiv / "dossier", target)
    return target


def _verify(arxiv: str, dossier: Path) -> dict:
    return vd.verify(arxiv, dossier=dossier, claim_dir=MAIN / "claims" / arxiv / "claim")


def _edit_record(dossier: Path, change) -> None:
    path = dossier / "dossier.json"
    record = json.loads(path.read_bytes())
    change(record)
    path.write_text(json.dumps(record), encoding="utf-8")


def _has(report: dict, prefix: str) -> bool:
    return any(f.startswith(prefix) for f in report["findings"])


# ---- must pass ------------------------------------------------------------------------------


@pytest.mark.parametrize("arxiv", SAMPLE)
def test_published_dossier_is_verified(arxiv):
    report = vd.verify(arxiv)
    assert report["result"] == "VERIFIED", report["findings"]
    assert report["findings"] == []
    assert len(report["claims"]) == 3


def test_a_copy_under_another_folder_name_is_verified(tmp_path):
    report = _verify("2302.12465", _copy(tmp_path, "2302.12465", "renamed"))
    assert report["result"] == "VERIFIED", report["findings"]


# ---- must fail: V1 --------------------------------------------------------------------------


def test_changed_manifest_line_fails(tmp_path):
    d = _copy(tmp_path, "2302.12465")
    manifest = d / "MANIFEST.sha256"
    lines = manifest.read_text(encoding="utf-8").splitlines()
    lines[0] = "0" * 64 + lines[0][64:]
    manifest.write_text("\n".join(lines) + "\n", encoding="utf-8")
    report = _verify("2302.12465", d)
    assert report["result"] == "NOT VERIFIED"
    assert _has(report, "V1")


def test_changed_claim_input_with_manifest_updated_fails_on_the_lock(tmp_path):
    d = _copy(tmp_path, "2309.15704")
    data = (d / "claim_input.json").read_bytes().replace(b'"98.7"', b'"98.8"', 1)
    assert data != (d / "claim_input.json").read_bytes()
    for name in ("claim_input.json", "claim_file.json"):
        (d / name).write_bytes(data)
    digest = hashlib.sha256(data).hexdigest()
    manifest = d / "MANIFEST.sha256"
    lines = []
    for line in manifest.read_text(encoding="utf-8").splitlines():
        if line.endswith(("claim_input.json", "claim_file.json")):
            line = digest + line[64:]
        lines.append(line)
    manifest.write_text("\n".join(lines) + "\n", encoding="utf-8")
    report = _verify("2309.15704", d)
    assert _has(report, "V1 lock")


# ---- must fail: V2, V3 ----------------------------------------------------------------------


def test_changed_verdict_fails(tmp_path):
    d = _copy(tmp_path, "2302.12465")
    _edit_record(d, lambda r: r["outcome"]["claims"][0]["verdict"].update(verdict="FRAGILE"))
    report = _verify("2302.12465", d)
    assert _has(report, "V2 arXiv-2302.12465v3-C1: expected verdict")


def test_changed_computed_fails(tmp_path):
    d = _copy(tmp_path, "2302.12465")
    _edit_record(d, lambda r: r["outcome"]["claims"][1].update(computed="NOT_REPRODUCED"))
    report = _verify("2302.12465", d)
    assert _has(report, "V2 arXiv-2302.12465v3-C2: recomputed REPRODUCED")


def test_invalid_accounting_with_verdicts_unchanged_fails(tmp_path):
    def change(r):
        r["outcome"]["run"]["accounting_valid"] = False
        r["outcome"]["run"]["invalid_reasons"] = ["a synthetic reason"]

    d = _copy(tmp_path, "2302.12465")
    _edit_record(d, change)
    report = _verify("2302.12465", d)
    assert _has(report, "V2 arXiv-2302.12465v3-C1: expected verdict")


def test_changed_profile_fails(tmp_path):
    d = _copy(tmp_path, "2302.12465")
    _edit_record(
        d, lambda r: r["outcome"]["profile"].update(headline="Mixed results: see the claims")
    )
    assert _has(_verify("2302.12465", d), "V3 profile")
    d2 = _copy(tmp_path / "b", "2302.12465")
    _edit_record(d2, lambda r: r["outcome"]["profile"]["counts"].update(REPRODUCED=2))
    assert _has(_verify("2302.12465", d2), "V3 profile")


# ---- must fail: V4, V5 ----------------------------------------------------------------------


def _step(record, phase, claim_suffix, name):
    return next(
        s
        for s in record["outcome"]["run"]["steps"]
        if s["phase"] == phase and (s["claim"] or "").endswith(claim_suffix) and s["step"] == name
    )


def test_failed_base_step_recorded_as_completed_fails(tmp_path):
    def change(r):
        s = _step(r, "base", "C1", "base")
        s["outcome"], s["reason"] = "completed", ""

    d = _copy(tmp_path, "2309.15704")
    _edit_record(d, change)
    report = _verify("2309.15704", d)
    assert _has(report, "V4 base arXiv-2309.15704v2-C1 base: recorded completed")


def test_removed_duplicated_and_extra_steps_fail(tmp_path):
    d = _copy(tmp_path, "2407.11735")
    _edit_record(d, lambda r: r["outcome"]["run"]["steps"].pop())
    assert _has(_verify("2407.11735", d), "V4 steps: missing")

    d2 = _copy(tmp_path / "b", "2407.11735")
    _edit_record(
        d2, lambda r: r["outcome"]["run"]["steps"].append(r["outcome"]["run"]["steps"][-1])
    )
    assert _has(_verify("2407.11735", d2), "V4 steps: a step is recorded twice")

    def extra(r):
        s = dict(r["outcome"]["run"]["steps"][-1])
        s["step"] = "holdout"
        r["outcome"]["run"]["steps"].append(s)

    d3 = _copy(tmp_path / "c", "2407.11735")
    _edit_record(d3, extra)
    assert _has(_verify("2407.11735", d3), "V4 steps: not in the plan")


def test_empty_reason_of_a_not_executed_step_fails(tmp_path):
    d = _copy(tmp_path, "2407.11735")
    _edit_record(d, lambda r: _step(r, "base", "C2", "base").update(reason=""))
    report = _verify("2407.11735", d)
    assert _has(report, "V4 base arXiv-2407.11735v2-C2 base: not_executed with no reason")


def test_a_reason_the_runner_never_gives_fails(tmp_path):
    d = _copy(tmp_path, "2305.19518")
    _edit_record(
        d, lambda r: _step(r, "base", "C1", "base").update(reason="skipped for lack of time")
    )
    report = _verify("2305.19518", d)
    assert _has(report, "V4 base arXiv-2305.19518v2-C1 base: not executed with a reason")


def test_base_obtained_for_a_failed_base_fails(tmp_path):
    def change(r):
        key = r["outcome"]["claims"][0]["key"]
        r["outcome"]["run"]["base_obtained"][key] = True

    d = _copy(tmp_path, "2309.15704")
    _edit_record(d, change)
    report = _verify("2309.15704", d)
    assert _has(report, "V4 run: base_obtained true")


def test_built_with_a_rung_that_did_not_complete_fails(tmp_path):
    d = _copy(tmp_path, "2407.11735")
    _edit_record(d, lambda r: r["outcome"]["ladder"].update(built_with="own_environment"))
    report = _verify("2407.11735", d)
    assert _has(report, "V5 ladder: built_with")


def test_malformed_record_is_a_finding_not_a_crash(tmp_path):
    d = _copy(tmp_path, "2302.12465")
    (d / "dossier.json").write_text("not json", encoding="utf-8")
    report = _verify("2302.12465", d)
    assert report["result"] == "NOT VERIFIED"
    assert _has(report, "the dossier cannot be read")

    d2 = _copy(tmp_path / "b", "2302.12465")
    _edit_record(d2, lambda r: r["outcome"].pop("claims"))
    report2 = _verify("2302.12465", d2)
    assert report2["result"] == "NOT VERIFIED"
