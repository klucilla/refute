"""v0.2.1 H9(a): a period match under the target's own TIC, in a catalog built from the
same TESS photometry, is a warning, not a fatal failure. Cases A1-A8 of
docs/validation/v0.2.1/H9a-acceptance.md (synthetic catalogs)."""

import pytest
from pydantic import ValidationError

from conftest import replicate_claim, target_entry, write_yaml
from refute.core.claim import load_claim
from refute.core.verdict import Severity, TestStatus
from refute.packs.tess.ebcatalog import check_eb_catalog, parse_catalog
from refute.packs.tess.params import EbCatalogParams
from refute.packs.tess.synthetic import TARGET_DEC, TARGET_RA, make_star

HEADER = "catalog,source_id,tic_id,ra_deg,dec_deg,period_days\n"
SCAN = {
    "format": "refute-eb-catalog-scan-1",
    "radius_arcsec": 120.0,
    "snapshots": [{"file": "eb_snapshot/x.tsv", "sha256": "0" * 64, "rows": 4584}],
    "per_target": {"TIC-1": {"tess_eb": 0, "gaia": 0}},
}
PERIOD = 3.7


def _catalog(*rows):
    return parse_catalog(HEADER + "".join(r + "\n" for r in rows), "synthetic.csv")


def _dec(arcsec):
    return TARGET_DEC + arcsec / 3600.0


def check(entries, params=None, scan=SCAN):
    return check_eb_catalog(
        entries, scan, "TIC-1", make_star(tic_id=1), PERIOD, params or EbCatalogParams()
    )


def _fatal(result):
    return result.status is TestStatus.FAIL and result.severity is Severity.FATAL


def _warning(result):
    return result.status is TestStatus.FAIL and result.severity is Severity.WARNING


# --- A1: own TIC, same photometry, compatible period -> warning ---------------------------


@pytest.mark.parametrize("factor", [1.0, 2.0, 0.5])
@pytest.mark.parametrize("offset", [0.0, 3600.0])  # at the target and one degree away
def test_a1_own_tic_in_tess_eb_is_a_warning(factor, offset):
    row = f"TESS-EB,TIC 1 (1),1,{TARGET_RA},{_dec(offset)},{factor * PERIOD}"
    result = check(_catalog(row))
    assert _warning(result), (result.status, result.severity)
    assert result.metrics["downgraded"] is True
    assert [m["source_id"] for m in result.metrics["downgraded_matches"]] == ["TIC 1 (1)"]
    assert "own TIC" in result.message
    assert "warning, not a fatal failure" in result.message


# --- A2-A5: stay fatal --------------------------------------------------------------------


def test_a2_neighbor_tic_in_tess_eb_stays_fatal():
    result = check(_catalog(f"TESS-EB,TIC 2 (1),2,{TARGET_RA},{_dec(5)},{PERIOD}"))
    assert _fatal(result)
    assert result.metrics["downgraded"] is False


def test_a3_position_only_gaia_row_at_the_target_stays_fatal():
    result = check(_catalog(f"Gaia-DR3-EB,123,,{TARGET_RA},{TARGET_DEC},{PERIOD}"))
    assert _fatal(result)
    assert result.metrics["matches"][0]["separation_arcsec"] == pytest.approx(0.0, abs=1e-6)
    assert result.metrics["downgraded"] is False


def test_a4_own_tic_in_a_catalog_outside_the_list_stays_fatal():
    result = check(_catalog(f"Gaia-DR3-EB,456,1,{TARGET_RA},{TARGET_DEC},{PERIOD}"))
    assert _fatal(result)
    assert result.metrics["matches"][0]["matched_by"] == "tic_id"
    assert result.metrics["downgraded"] is False


@pytest.mark.parametrize("order", ["own-first", "neighbor-first"])
def test_a5_a_neighbor_match_decides_over_the_own_tic(order):
    own = f"TESS-EB,TIC 1 (1),1,{TARGET_RA},{TARGET_DEC},{PERIOD}"
    neighbor = f"TESS-EB,TIC 2 (1),2,{TARGET_RA},{_dec(8)},{PERIOD}"
    rows = (own, neighbor) if order == "own-first" else (neighbor, own)
    result = check(_catalog(*rows))
    assert _fatal(result)
    assert "TIC 2 (1)" in result.message
    assert result.metrics["downgraded"] is False


# --- A6: unchanged cases ------------------------------------------------------------------


def test_a6_other_period_is_still_a_plain_warning():
    result = check(_catalog(f"TESS-EB,TIC 1 (1),1,{TARGET_RA},{TARGET_DEC},1.234"))
    assert _warning(result)
    assert result.metrics["downgraded"] is False
    assert "warning, not a fatal failure" not in result.message


def test_a6_no_match_and_coverage_are_unchanged():
    far = check(_catalog(f"TESS-EB,TIC 3 (1),3,{TARGET_RA},{_dec(60)},{PERIOD}"))
    assert far.status is TestStatus.PASS
    assert far.metrics["downgraded"] is False
    assert check([], scan=None).status is TestStatus.INCONCLUSIVE


# --- A7: the switch -----------------------------------------------------------------------


@pytest.mark.parametrize("factor", [1.0, 2.0, 0.5])
def test_a7_empty_list_restores_the_v02_behavior(factor):
    row = f"TESS-EB,TIC 1 (1),1,{TARGET_RA},{TARGET_DEC},{factor * PERIOD}"
    result = check(_catalog(row), params=EbCatalogParams(same_photometry_catalogs=[]))
    assert _fatal(result)
    assert result.metrics["downgraded"] is False


def test_a7_the_list_is_matched_by_catalog_name():
    params = EbCatalogParams(same_photometry_catalogs=["Gaia-DR3-EB"])
    gaia_own = check(_catalog(f"Gaia-DR3-EB,456,1,{TARGET_RA},{TARGET_DEC},{PERIOD}"), params)
    tess_own = check(_catalog(f"TESS-EB,TIC 1 (1),1,{TARGET_RA},{TARGET_DEC},{PERIOD}"), params)
    assert _warning(gaia_own) and gaia_own.metrics["downgraded"] is True
    assert _fatal(tess_own)


# --- A8: schema ---------------------------------------------------------------------------


@pytest.mark.parametrize("names", [[""], ["  "], ["TESS-EB", ""]])
def test_a8_empty_catalog_names_are_rejected(names):
    # The field must exist and accept valid names, so that the rejection below is the
    # name check and not an unknown-field error.
    assert EbCatalogParams(same_photometry_catalogs=["X"]).same_photometry_catalogs == ["X"]
    with pytest.raises(ValidationError, match="same_photometry_catalogs"):
        EbCatalogParams(same_photometry_catalogs=names)


def test_a8_default_is_resolved(tmp_path):
    claim = write_yaml(tmp_path / "claim.yaml", replicate_claim([target_entry(1, "planet", 3.7)]))
    params = load_claim(claim).claim.test_plan["gauntlet"]["eb_catalog"]
    assert params["same_photometry_catalogs"] == ["TESS-EB"]
