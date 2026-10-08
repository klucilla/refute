"""Adapter v0.2: FITS completeness (issue #1) and SPOC-like FITS round trips, offline."""

from pathlib import Path

import numpy as np
import pytest

from refute.packs.tess.adapter import (
    DataError,
    TessAdapter,
    check_fits_complete,
    discard_if_incomplete,
    download_checked,
    fits_expected_size,
)
from refute.packs.tess.params import TessTestPlan
from refute.packs.tess.synthetic import scenario_data, write_synthetic_cache


def _fits(path: Path) -> Path:
    from astropy.io import fits

    table = fits.BinTableHDU.from_columns(
        [fits.Column(name="TIME", format="D", array=np.arange(20000.0))]
    )
    fits.HDUList([fits.PrimaryHDU(np.zeros((3, 4))), table]).writeto(path)
    return path


def test_expected_size_matches_a_complete_file(tmp_path):
    path = _fits(tmp_path / "a.fits")
    assert fits_expected_size(path) == path.stat().st_size
    check_fits_complete(path)


@pytest.mark.parametrize("keep", [65536, 2880, 100])
def test_truncated_files_are_detected(tmp_path, keep):
    path = _fits(tmp_path / "a.fits")
    data = path.read_bytes()
    assert len(data) > keep
    path.write_bytes(data[:keep])
    with pytest.raises(DataError):
        check_fits_complete(path)


def test_incomplete_files_are_deleted_only_inside_the_cache(tmp_path):
    cache = tmp_path / "cache"
    cache.mkdir()
    inside = _fits(cache / "a.fits")
    inside.write_bytes(inside.read_bytes()[:2880])
    outside = _fits(tmp_path / "b.fits")
    outside.write_bytes(outside.read_bytes()[:2880])
    assert discard_if_incomplete(inside, cache) is True and not inside.exists()
    assert discard_if_incomplete(outside, cache) is False and outside.exists()
    good = _fits(cache / "c.fits")
    assert discard_if_incomplete(good, cache) is False and good.exists()


class _FakeProduct:
    """Stands in for a lightkurve search result row; writes a file like a download would."""

    def __init__(self, truncate: bool, fail: bool = False):
        self.truncate, self.fail = truncate, fail

    def download(self, download_dir: str, **_kwargs):
        path = _fits(Path(download_dir) / "x_lc.fits")
        if self.truncate:
            path.write_bytes(path.read_bytes()[: 65536 if path.stat().st_size > 65536 else 2880])
        if self.fail:
            raise OSError("This file may be corrupt due to an interrupted download")

        class _Obj:
            meta = {"FILENAME": str(path)}

        return _Obj()


def test_download_checked_removes_truncated_downloads(tmp_path):
    with pytest.raises(DataError, match="incomplete"):
        download_checked(_FakeProduct(truncate=True), "x_lc.fits", tmp_path)
    assert not (tmp_path / "x_lc.fits").exists()


def test_download_checked_cleans_up_after_a_failed_download(tmp_path):
    with pytest.raises(DataError, match="removed 1 incomplete"):
        download_checked(_FakeProduct(truncate=True, fail=True), "x_lc.fits", tmp_path)
    assert not (tmp_path / "x_lc.fits").exists()


def test_download_checked_returns_a_complete_file(tmp_path):
    path = download_checked(_FakeProduct(truncate=False), "x_lc.fits", tmp_path)
    assert path.is_file()


def test_spoc_like_fits_round_trip(tmp_path):
    data = scenario_data("blend")
    manifest = write_synthetic_cache(tmp_path, 1, data.lc, data.star, aux=data.aux)
    assert manifest["schema"] == "refute-tess-fetch-2"
    loaded = TessAdapter().load({"tic_id": 1}, TessTestPlan().model_dump(), tmp_path)
    assert loaded.aux is not None
    assert [p.sector for p in loaded.aux.pixels] == [p.sector for p in data.aux.pixels]
    assert loaded.aux.pixels[0].target_xy == pytest.approx((5.0, 5.0), abs=1e-6)
    assert np.array_equal(loaded.aux.pixels[0].aperture, data.aux.pixels[0].aperture)
    assert loaded.aux.sectors[0].crowdsap == pytest.approx(data.aux.sectors[0].crowdsap, rel=1e-6)
    # Momentum dumps are read from the raw quality column; their cadences are removed.
    assert np.allclose(loaded.aux.sectors[0].dump_times, data.aux.sectors[0].dump_times)
    assert len(loaded.lc) == len(data.lc)
    assert np.allclose(loaded.lc.flux, data.lc.flux / np.median(data.lc.flux[:1]), rtol=1e-2)
    assert loaded.aux.neighbors[0].tic_id == 2


def test_pixel_cadences_are_restricted_to_the_light_curve(tmp_path):
    # SPOC leaves PDCSAP empty on some cadences that the target pixel file keeps.
    # The pixel tests must use the same cadences as the light curve.
    from refute.packs.tess.adapter import matching_cadences

    data = scenario_data("planet")
    gap = slice(2000, 2600)
    for aux in data.aux.sectors:
        aux.pdcsap_flux[gap] = np.nan
    write_synthetic_cache(tmp_path, 1, data.lc, data.star, aux=data.aux)
    loaded = TessAdapter().load({"tic_id": 1}, TessTestPlan().model_dump(), tmp_path)
    for px in loaded.aux.pixels:
        lc_time = loaded.lc.time[loaded.lc.sector == px.sector]
        assert px.n_dropped_cadences == 600
        assert px.time.size == lc_time.size == px.flux.shape[0]
        assert np.allclose(px.time, lc_time, rtol=0, atol=1e-6)
    times = np.array([1.0, 2.0, 3.0])
    assert matching_cadences(times, np.array([2.0 + 5e-6, 2.5, 3.0])).tolist() == [
        True,
        False,
        True,
    ]
    assert matching_cadences(np.zeros(0), times).tolist() == [False, False, False]


def test_tampered_cache_file_is_rejected(tmp_path):
    data = scenario_data("planet")
    manifest = write_synthetic_cache(tmp_path, 1, data.lc, data.star, aux=data.aux)
    tpf = tmp_path / manifest["pixel_files"][0]["path"]
    tpf.write_bytes(tpf.read_bytes() + b"x")
    with pytest.raises(DataError, match="SHA-256"):
        TessAdapter().load({"tic_id": 1}, TessTestPlan().model_dump(), tmp_path)
