"""The criterion-6 deviation of 2026-11-05 (#199): the mirror URL and the placement of the
mirror's TESS-EB file in a clean clone, on synthetic files only (no network)."""

from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path

import pytest

from conftest import cache_test_dir

ROOT = Path(__file__).resolve().parents[1]
DEVIATION = ROOT / "calibration" / "v0.5" / "deviation"


def _load(name: str):
    spec = importlib.util.spec_from_file_location(f"v05_c6_{name}", DEVIATION / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


fetch = _load("fetch_tess_eb_mirror")
repro = _load("reproduce_c6_mirror")

TSV = (
    b"#VizieR header\n#query date 2026-11-05\n"
    b"TIC\tm_TIC\tRAJ2000\tDEJ2000\tPer\n1\t0\t1.0\t2.0\t3.0\n"
)


def test_the_mirror_url_changes_only_the_host():
    url = (
        "https://vizier.cds.unistra.fr/viz-bin/asu-tsv?-source=J/ApJS/258/16/tess-ebs"
        "&-out=TIC,m_TIC,RAJ2000,DEJ2000,Per&-out.max=unlimited"
    )
    out = fetch.mirror_url(url, "vizier.cfa.harvard.edu")
    assert out == url.replace("vizier.cds.unistra.fr", "vizier.cfa.harvard.edu")
    with pytest.raises(SystemExit, match="not vizier.cds"):
        fetch.mirror_url("https://example.org/x", "vizier.cfa.harvard.edu")


def test_the_scan_of_the_c3_claim_has_one_tess_eb_snapshot():
    snap = fetch.tess_eb_snapshot(ROOT)
    assert snap["cache_path"] == "v04/tess-eb/tess_ebs_prsa2022.tsv"
    assert snap["content_sha256"].startswith("a31936ce")


def _clone(base: Path, content_sha: str) -> Path:
    clone = base / "clone"
    (clone / "calibration/v0.5").mkdir(parents=True)
    scan = {
        "snapshots": [
            {
                "catalog_name": "TESS-EB",
                "redistributed": False,
                "parser": "tess-eb-vizier-tsv",
                "cache_path": "v04/tess-eb/t.tsv",
                "url": "https://vizier.cds.unistra.fr/x",
                "content_sha256": content_sha,
            }
        ]
    }
    (clone / repro.SCAN).write_text(json.dumps(scan), encoding="utf-8")
    return clone


def test_place_copies_a_matching_file_once_and_refuses_a_mismatch(request):
    from refute.packs.tess import ebcatalog

    base = cache_test_dir("v05-c6", request)
    source = base / "mirror.tsv"
    base.mkdir(parents=True, exist_ok=True)
    source.write_bytes(TSV)
    clone = _clone(base, ebcatalog.content_sha256(TSV))
    record = repro.place(clone, source)
    assert (clone / ".cache/v04/tess-eb/t.tsv").read_bytes() == TSV
    assert record["destination"] == ".cache/v04/tess-eb/t.tsv"
    assert record["content_sha256"] == record["claim_content_sha256"]
    with pytest.raises(FileExistsError):
        repro.place(clone, source)
    other = _clone(cache_test_dir("v05-c6", request), "0" * 64)
    with pytest.raises(RuntimeError, match="content SHA-256"):
        repro.place(other, source)


def test_the_mirror_source_must_be_a_checked_fetch_in_the_prep_folder(request, monkeypatch):
    import hashlib

    base = cache_test_dir("v05-c6", request)
    host = "vizier.cfa.harvard.edu"
    prep = base / "prep"
    (prep / host).mkdir(parents=True)
    (prep / host / "t.tsv").write_bytes(TSV)
    record = {
        "host": host,
        "content_matches": True,
        "file": (prep / host / "t.tsv").as_posix(),
        "raw_sha256": hashlib.sha256(TSV).hexdigest(),
    }
    (prep / host / "fetch.json").write_text(json.dumps(record), encoding="utf-8")
    monkeypatch.setattr(repro, "PREP", prep)
    fetched, source = repro.mirror_source(prep / host / "fetch.json")
    assert source.read_bytes() == TSV and fetched["host"] == host
    (prep / host / "t.tsv").write_bytes(TSV + b"x")
    with pytest.raises(SystemExit, match="raw SHA-256"):
        repro.mirror_source(prep / host / "fetch.json")
    record["host"] = "example.org"
    (prep / host / "fetch.json").write_text(json.dumps(record), encoding="utf-8")
    with pytest.raises(SystemExit, match="approved mirror"):
        repro.mirror_source(prep / host / "fetch.json")
    outside = base / "fetch.json"
    outside.write_text(json.dumps(record), encoding="utf-8")
    with pytest.raises(SystemExit, match="not inside"):
        repro.mirror_source(outside)


def test_a_junction_on_the_way_to_the_mirror_file_is_refused(request, monkeypatch):
    import hashlib

    winapi = pytest.importorskip("_winapi")
    if not hasattr(winapi, "CreateJunction"):
        pytest.skip("no junctions on this system")
    base = cache_test_dir("v05-c6", request)
    host = "vizier.cfa.harvard.edu"
    real = base / "real"
    real.mkdir(parents=True)
    (real / "t.tsv").write_bytes(TSV)
    prep = base / "prep"
    prep.mkdir()
    winapi.CreateJunction(str(real), str(prep / host))
    record = {
        "host": host,
        "content_matches": True,
        "file": (prep / host / "t.tsv").as_posix(),
        "raw_sha256": hashlib.sha256(TSV).hexdigest(),
    }
    (base / "prep-fetch").mkdir()
    monkeypatch.setattr(repro, "PREP", prep)
    fetch_json = prep / "fetch.json"
    fetch_json.write_text(json.dumps(record), encoding="utf-8")
    try:
        with pytest.raises(SystemExit, match="not inside"):
            repro.mirror_source(fetch_json)
    finally:
        os.rmdir(prep / host)  # removes the junction itself, never its target


def test_a_run_without_placement_or_with_an_unexpected_command_fails(request, monkeypatch):
    import hashlib

    base = cache_test_dir("v05-c6", request)
    host = "vizier.cfa.harvard.edu"
    prep = base / "prep"
    (prep / host).mkdir(parents=True)
    (prep / host / "t.tsv").write_bytes(TSV)
    fetch_json = prep / host / "fetch.json"
    fetch_json.write_text(
        json.dumps(
            {
                "host": host,
                "content_matches": True,
                "file": (prep / host / "t.tsv").as_posix(),
                "raw_sha256": hashlib.sha256(TSV).hexdigest(),
                "url": "u",
                "utc": "t",
                "content_sha256": "c",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(repro, "PREP", prep)
    monkeypatch.chdir(ROOT)
    cases = (
        ("cd ..", "cd outside"),
        ("cd", "cd outside"),
        ("python evil.py", "not expected"),
        ("uv run python evil.py", "not expected"),
    )
    for i, (block, error) in enumerate(cases):
        dossier = base / f"dossier-{i}"
        dossier.mkdir()
        (dossier / "REPRODUCE.md").write_text(f"```bash\n{block}\n```\n", encoding="utf-8")
        work = cache_test_dir("v05-c6", request)
        assert repro.main([str(dossier), str(work), str(fetch_json)]) == 1
        record = json.loads((work / "reproduce.json").read_text(encoding="utf-8"))
        assert record["result"] == "FAIL"
        assert error in record["steps"][0]["error"]
