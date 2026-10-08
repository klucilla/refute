"""eb_catalog: cross-match with eclipsing-binary catalog snapshots (synthetic catalogs)."""

import pytest

from refute.core.verdict import Severity, TestStatus
from refute.packs.tess.ebcatalog import (
    CatalogError,
    check_eb_catalog,
    parse_catalog,
    separation_arcsec,
)
from refute.packs.tess.params import EbCatalogParams, TessTestPlan
from refute.packs.tess.pipeline import analyze_data
from refute.packs.tess.synthetic import TARGET_DEC, TARGET_RA, fast_plan_dict, make_star

HEADER = "catalog,source_id,tic_id,ra_deg,dec_deg,period_days\n"


def _catalog(*rows: str):
    return parse_catalog(HEADER + "".join(r + "\n" for r in rows), "synthetic.csv")


def _offset(arcsec: float) -> float:
    return TARGET_DEC + arcsec / 3600.0


def test_period_match_at_the_target_is_fatal():
    entries = _catalog(f"TESS-EB,1,,{TARGET_RA},{_offset(5)},7.4")  # 2 x 3.7 d
    result = check_eb_catalog(entries, make_star(), 3.7, EbCatalogParams())
    assert result.status is TestStatus.FAIL and result.severity is Severity.FATAL
    assert result.metrics["matches"][0]["period_factor"] == 2.0


def test_match_by_tic_id_far_away_still_counts():
    entries = _catalog(f"Gaia-EB,9,1,{TARGET_RA + 1},{TARGET_DEC},3.7")
    result = check_eb_catalog(entries, make_star(tic_id=1), 3.7, EbCatalogParams())
    assert result.status is TestStatus.FAIL and result.severity is Severity.FATAL
    assert result.metrics["matches"][0]["matched_by"] == "tic_id"


def test_position_match_with_another_period_is_a_warning():
    entries = _catalog(
        f"TESS-EB,2,,{TARGET_RA},{_offset(10)},1.234", f"TESS-EB,3,,{TARGET_RA},{_offset(15)},"
    )
    result = check_eb_catalog(entries, make_star(), 3.7, EbCatalogParams())
    assert result.status is TestStatus.FAIL and result.severity is Severity.WARNING


def test_no_binary_nearby_passes():
    entries = _catalog(f"TESS-EB,4,,{TARGET_RA},{_offset(60)},3.7")
    result = check_eb_catalog(entries, make_star(), 3.7, EbCatalogParams())
    assert result.status is TestStatus.PASS
    assert check_eb_catalog([], make_star(), 3.7, EbCatalogParams()).status is TestStatus.PASS


def test_no_coordinates_is_inconclusive():
    star = make_star()
    star = type(star)(**{**star.to_dict(), "ra_deg": None})
    assert check_eb_catalog([], star, 3.7, EbCatalogParams()).status is TestStatus.INCONCLUSIVE


@pytest.mark.parametrize(
    "text",
    ["catalog,source\nA,1\n", HEADER + "A,1,,10,20\n", HEADER + "A,1,x,10,20,1\n"],
)
def test_malformed_catalogs_are_rejected(text):
    with pytest.raises(CatalogError):
        parse_catalog(text)


def test_separation():
    assert separation_arcsec(10.0, 0.0, 10.0, 1.0 / 3600) == pytest.approx(1.0, rel=1e-6)


def test_catalog_test_runs_only_when_catalogs_are_given():
    from refute.packs.tess.synthetic import scenario_data

    data = scenario_data("planet")
    plan = TessTestPlan.model_validate(fast_plan_dict())
    with_catalog = analyze_data(data, plan, catalogs=_catalog(f"X,1,,{TARGET_RA},{_offset(4)},3.7"))
    names = [t.name for t in with_catalog.tests]
    assert "eb_catalog" in names
    assert with_catalog.verdict == "REFUTED"
