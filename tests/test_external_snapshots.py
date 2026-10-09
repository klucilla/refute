"""Catalogs that are not redistributed (v0.2: TESS-EB): only identifiers are attached;
the snapshot is downloaded and its content hash checked before any analysis."""

import json

import pytest

from conftest import replicate_claim, target_entry, write_yaml
from refute.core.lock import create_lock
from refute.core.run import execute_run
from refute.packs.tess.ebcatalog import (
    CatalogError,
    EbEntry,
    check_eb_catalog,
    content_sha256,
    parse_catalog,
    prepare_external_snapshots,
    resolve_references,
)
from refute.packs.tess.params import EbCatalogParams
from refute.packs.tess.synthetic import TARGET_DEC, TARGET_RA, make_star

HEADER = "catalog,source_id,tic_id,ra_deg,dec_deg,period_days\n"


def vizier_tsv(date: str, period: str = "7.4") -> bytes:
    """A small VizieR-like TESS-EB response; the date lines change at every query."""
    return (
        f"#\n#   Date: {date} [V7.6.1]\n#INFO\trequest_date={date}\n"
        "TIC\tm_TIC\tRAJ2000\tDEJ2000\tPer\n"
        "\t\tdeg\tdeg\td\n"
        "----------\t-\t--------------\t--------------\t-----------\n"
        f"1\t1\t{TARGET_RA}\t{TARGET_DEC + 5 / 3600}\t{period}\n"
        "2\t1\t10.0\t10.0\t\n"
    ).encode()


def scan_for(content_hash: str) -> dict:
    return {
        "format": "refute-eb-catalog-scan-1",
        "radius_arcsec": 120.0,
        "snapshots": [
            {
                "catalog_name": "TESS-EB",
                "file": "external/tess_ebs.tsv",
                "cache_path": "external/tess_ebs.tsv",
                "url": "https://vizier.example/tess-ebs",
                "parser": "tess-eb-vizier-tsv",
                "content_sha256": content_hash,
                "rows": 2,
                "redistributed": False,
            }
        ],
        "per_target": {"TIC-1": {"tess_eb": 1, "gaia": 0}},
    }


GOOD = content_sha256(vizier_tsv("2026-10-08T14:54:48"))


def test_content_hash_ignores_the_query_date_but_not_the_data():
    assert content_sha256(vizier_tsv("2030-01-01T00:00:00")) == GOOD
    assert content_sha256(vizier_tsv("2026-10-08T14:54:48", period="7.5")) != GOOD


def test_reference_rows_carry_no_catalog_values():
    (ref,) = parse_catalog(HEADER + "TESS-EB,TIC 1 (1),1,,,\n")
    assert ref.is_reference and ref.period_days is None
    with pytest.raises(CatalogError):
        parse_catalog(HEADER + "TESS-EB,TIC 1 (1),1,,,7.4\n")
    with pytest.raises(CatalogError):
        parse_catalog(HEADER + "TESS-EB,TIC 1 (1),1,150.0,,\n")


def test_missing_snapshot_offline_stops(tmp_path):
    with pytest.raises(CatalogError, match="not in the cache"):
        prepare_external_snapshots(scan_for(GOOD), tmp_path, offline=True)


def test_snapshot_is_downloaded_and_verified(tmp_path):
    calls = []

    def fake_download(url):
        calls.append(url)
        return vizier_tsv("2026-12-01T00:00:00")  # another date, same content

    messages = prepare_external_snapshots(scan_for(GOOD), tmp_path, False, fake_download)
    assert calls == ["https://vizier.example/tess-ebs"]
    assert "content SHA-256 verified" in messages[0]
    # Already cached: no second download.
    prepare_external_snapshots(scan_for(GOOD), tmp_path, False, fake_download)
    assert len(calls) == 1


def test_changed_source_stops_the_run(tmp_path):
    def changed(_url):
        return vizier_tsv("2026-12-01T00:00:00", period="7.5")

    with pytest.raises(CatalogError, match="STOP"):
        prepare_external_snapshots(scan_for(GOOD), tmp_path, False, changed)


def test_reference_rows_are_resolved_from_the_verified_copy(tmp_path):
    (tmp_path / "external").mkdir()
    (tmp_path / "external" / "tess_ebs.tsv").write_bytes(vizier_tsv("2026-10-08T14:54:48"))
    entries = parse_catalog(HEADER + "TESS-EB,TIC 1 (1),1,,,\n")
    with pytest.raises(CatalogError, match="unresolved"):
        check_eb_catalog(entries, scan_for(GOOD), "TIC-1", make_star(), 3.7, EbCatalogParams())
    (resolved,) = resolve_references(entries, scan_for(GOOD), tmp_path)
    assert resolved.period_days == 7.4 and resolved.ra_deg == TARGET_RA
    result = check_eb_catalog(
        [resolved], scan_for(GOOD), "TIC-1", make_star(), 3.7, EbCatalogParams()
    )
    assert result.status.value == "FAIL" and result.metrics["matches"][0]["period_factor"] == 2.0
    unknown = [EbEntry("TESS-EB", "TIC 9 (1)", 9, None, None, None)]
    with pytest.raises(CatalogError, match="not found"):
        resolve_references(unknown, scan_for(GOOD), tmp_path)


def test_run_stops_before_any_dossier_when_the_snapshot_is_missing(tmp_path):
    claims = tmp_path / "claims"
    claims.mkdir()
    (claims / "eb_catalog.csv").write_text(HEADER + "TESS-EB,TIC 1 (1),1,,,\n", encoding="utf-8")
    (claims / "eb_catalog_scan.json").write_text(json.dumps(scan_for(GOOD)), encoding="utf-8")
    claim = write_yaml(
        claims / "claim.yaml",
        replicate_claim(
            [target_entry(1, "planet", 3.7)],
            attachments=[
                {"path": "eb_catalog.csv", "role": "eb-catalog"},
                {"path": "eb_catalog_scan.json", "role": "eb-catalog-scan"},
            ],
        ),
    )
    create_lock(claim)
    outcome = execute_run(
        claim, mode="replicate", out_dir=tmp_path / "out", offline=True, cache_dir=tmp_path / "c"
    )
    assert outcome.exit_code == 1
    assert "claim data check failed" in outcome.messages[0]
    assert outcome.run_dir is None and not (tmp_path / "out").exists()
