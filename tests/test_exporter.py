import json
from pathlib import Path

import refute.packs.tess.exporter as exporter_module
from refute.packs.tess.exporter import DISCLAIMER, CandidateParameterExporter

RESULT = {
    "target_key": "TIC-1",
    "tic_id": 1,
    "target_kind": "planet",
    "verdict": "SURVIVED",
    "verdict_reason": "every test passed",
    "candidate": {
        "period": 3.7,
        "t0_bjd": 2458326.3,
        "duration_hours": 2.5,
        "depth_ppm": 2000.0,
        "depth_err": 2e-5,
        "snr": 90.0,
    },
    "global_ephemeris": {"period_err": 1e-6, "t_ref_bjd": 2458700.0, "t_ref_err": 1e-4},
    "tests": [{"name": "snr", "status": "PASS"}],
    "data_summary": {
        "product": {"author": "SPOC", "exptime_seconds": 120, "flux_column": "pdcsap_flux"},
        "sectors": [1, 28],
    },
}


def test_export_writes_a_parameter_sheet_and_never_claims_submission(tmp_path):
    paths = CandidateParameterExporter().export(RESULT, tmp_path / "export")
    assert sorted(p.name for p in paths) == [
        "candidate_parameters.json",
        "candidate_parameters.md",
    ]
    fields = json.loads(
        (tmp_path / "export" / "candidate_parameters.json").read_text(encoding="utf-8")
    )
    assert fields["submitted"] is False
    assert fields["sheet"] == "candidate parameters for a human; not a submission"
    assert fields["period_days"] == 3.7 and fields["period_err_days"] == 1e-6
    assert fields["epoch_bjd_tdb"] == 2458700.0 and fields["epoch_err_days"] == 1e-4
    assert fields["depth_ppm"] == 2000.0 and fields["depth_err_ppm"] == 20.0
    assert fields["duration_hours"] == 2.5 and fields["duration_err_hours"] is None
    assert "not a new candidate" in fields["notes"]
    summary = (tmp_path / "export" / "candidate_parameters.md").read_text(encoding="utf-8")
    assert DISCLAIMER in summary
    assert "NOTHING HAS BEEN SUBMITTED" in summary
    assert "| duration_err_hours | not measured |" in summary


def test_no_ctoi_wording_and_no_submission_promise(tmp_path):
    CandidateParameterExporter().export(RESULT, tmp_path / "export")
    for path in (tmp_path / "export").iterdir():
        text = path.read_text(encoding="utf-8")
        assert "CTOI" not in text.upper()
        assert "prepare a submission" not in text
    source = Path(exporter_module.__file__).read_text(encoding="utf-8")
    assert "ctoi" not in source.lower()
    assert "peer-reviewed" in DISCLAIMER and "never a submission" in DISCLAIMER


def test_exporter_contains_no_network_code():
    source = Path(exporter_module.__file__).read_text(encoding="utf-8")
    for forbidden in ("urllib", "requests", "http.client", "socket", "astroquery", "smtplib"):
        assert forbidden not in source
