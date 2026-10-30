"""v0.4 WP3: injection-recovery and transformed curves (cases 3.1 to 3.11 of
docs/plans/v0.4-acceptance.md). Synthetic data only."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest
from astropy.io import fits

from conftest import target_entry
from refute.core.io import read_json
from refute.packs.tess.adapter import TessAdapter, manifest_path, raw_lengths
from refute.packs.tess.discover import injection as inj
from refute.packs.tess.discover import measure
from refute.packs.tess.discover import transforms as tr
from refute.packs.tess.discover.protocol import TRANSFORMS
from refute.packs.tess.params import TessTestPlan
from refute.packs.tess.synthetic import (
    TARGET_DEC,
    TARGET_RA,
    discovery_plan_dict,
    scenario_data,
    write_spoc_tpf_fits,
    write_synthetic_cache,
)

PLAN = TessTestPlan.model_validate(discovery_plan_dict())


@pytest.fixture(scope="module")
def noise_data():
    return scenario_data("noise", seed=5)


def _injection(depth: float, period: float = 3.1, duration: float = 0.11) -> inj.Injection:
    return inj.Injection(0, period, depth, 0.2, duration, 1325.4)


def test_3_1_a_strong_injection_before_detrending_is_recovered(noise_data):
    injection = _injection(0.004)
    out = measure.chain(inj.inject(noise_data, injection), PLAN, 1)
    result = inj.recovery(injection, out["candidate"], out["gate_passed"])
    assert result["recovered"], (out["candidate"], result)
    assert "centroid_shift" in out["deferred"]


def test_3_1_the_injection_reaches_the_raw_flux_and_the_sap_flux(noise_data):
    injected = inj.inject(noise_data, _injection(0.004))
    assert np.min(injected.lc.flux - noise_data.lc.flux) < -0.003
    sap_new = injected.aux.sectors[0].sap_flux
    sap_old = noise_data.aux.sectors[0].sap_flux
    crowd = noise_data.aux.sectors[0].crowdsap
    assert np.min(sap_new - sap_old) == pytest.approx(-0.004 * crowd, rel=0.05)
    assert injected.aux.pixels is noise_data.aux.pixels  # no pixel file is injected


def test_3_2_an_injection_far_below_the_noise_is_not_recovered_and_counted(noise_data):
    injection = _injection(1e-5)
    out = measure.chain(inj.inject(noise_data, injection), PLAN, 1)
    record = {
        "recovery": inj.recovery(injection, out["candidate"], out["gate_passed"]),
        "crowdsap_missing_sectors": [],
    }
    summary = inj.summarize([record])
    assert summary["injections"] == 1 and summary["recovered"] == 0
    assert summary["recovery_wilson_95"][0] == 0.0


def test_3_3_an_alias_is_counted_apart():
    injection = _injection(0.004, period=2.0)
    result = inj.recovery(injection, {"period_days": 4.0, "t0_btjd": 1325.4}, True)
    assert result["recovered"] is False and result["alias"] == 2.0


def test_3_4_the_injection_stream_is_deterministic_and_prefix_stable():
    seed = inj.stage1_chain_seed("ab" * 32, 12345)
    five = inj.draw_injections(seed, 5, 1325.0, 1.0, 4.44)
    twenty = inj.draw_injections(seed, 20, 1325.0, 1.0, 4.44)
    assert five == twenty[:5]
    assert inj.draw_injections(seed, 20, 1325.0, 1.0, 4.44) == twenty
    for i in twenty:
        assert 0.5 <= i.period_days <= 13.0 and 100e-6 <= i.depth <= 10000e-6
        assert 0.0 <= i.impact <= 0.8 and 1325.0 <= i.t0_btjd <= 1325.0 + i.period_days
        assert i.duration_days > 0
    with pytest.raises(inj.InjectionError):
        inj.draw_injections(seed, 1, 1325.0, None, 4.4)


def test_3_5_the_run_uses_the_locked_values():
    from refute.packs.tess.discover.protocol import INJECTION

    assert (INJECTION.depth_min_ppm, INJECTION.depth_max_ppm) == (100.0, 10000.0)
    assert (INJECTION.period_min_days, INJECTION.period_max_days) == (0.5, 13.0)
    assert INJECTION.impact_max == 0.8 and INJECTION.measurement_prefix == 5


# --- transformed curves -------------------------------------------------------------------


@pytest.fixture
def cache(tmp_path: Path) -> Path:
    """A synthetic cache whose pixel files share the light curve's raw cadence grid."""
    root = tmp_path / "cache"
    data = scenario_data("planet", seed=4)
    manifest = write_synthetic_cache(root, 1, data.lc, data.star, aux=data.aux)
    for record, px in zip(manifest["pixel_files"], data.aux.pixels, strict=True):
        lc_record = next(f for f in manifest["files"] if f["sector"] == record["sector"])
        with fits.open(root / lc_record["path"]) as hdul:
            raw_time = np.asarray(hdul[1].data["TIME"], dtype=float)
        index = np.searchsorted(px.time, raw_time).clip(0, px.time.size - 1)
        grid = replace(px, time=raw_time, flux=px.flux[index], flux_err=px.flux_err[index])
        write_spoc_tpf_fits(root / record["path"], grid, TARGET_RA, TARGET_DEC)
        import hashlib

        record["sha256"] = hashlib.sha256((root / record["path"]).read_bytes()).hexdigest()
    from refute.core.io import write_json

    write_json(manifest_path(root, 1), manifest)
    return root


TARGET = target_entry(1, "planet", 3.7)
PLAN_DICT = discovery_plan_dict()


def _load(cache: Path, transform=None):
    return TessAdapter().load(TARGET, PLAN_DICT, cache, transform=transform)


def test_3_6_the_inverted_curve_reflects_every_flux_and_keeps_the_rest(cache):
    base, inv = _load(cache), _load(cache, tr.Transform(tr.INVERT, {}, "inverted"))
    assert np.allclose(inv.lc.flux, 2.0 - base.lc.flux)
    assert np.array_equal(inv.lc.time, base.lc.time)
    assert np.array_equal(inv.lc.flux_err, base.lc.flux_err)
    for a, b in zip(base.aux.sectors, inv.aux.sectors, strict=True):
        assert np.allclose(b.sap_flux, 2.0 - a.sap_flux)
        assert np.array_equal(b.sap_bkg, a.sap_bkg) and b.crowdsap == a.crowdsap
    for a, b in zip(base.aux.pixels, inv.aux.pixels, strict=True):
        medians = np.nanmedian(a.flux, axis=0)
        assert np.allclose(b.flux, 2.0 * medians - a.flux)
        assert np.array_equal(b.aperture, a.aperture) and b.target_xy == a.target_xy


def test_3_10_a_rotation_moves_every_column_jointly_on_the_raw_grid(cache):
    manifest = read_json(manifest_path(cache, 1))
    lengths = raw_lengths(manifest, cache)
    offsets = {sector: 37 + sector for sector in lengths}
    base = _load(cache)
    rot = _load(cache, tr.Transform(tr.ROTATE, offsets, "rotation-1"))
    for record in manifest["files"]:
        sector = int(record["sector"])
        with fits.open(cache / record["path"]) as hdul:
            raw = hdul[1].data
            pdc = np.asarray(raw["PDCSAP_FLUX"], float)
            sap = np.asarray(raw["SAP_FLUX"], float)
            bkg = np.asarray(raw["SAP_BKG"], float)
            quality = np.asarray(raw["QUALITY"], int)
            time = np.asarray(raw["TIME"], float)
        k = offsets[sector]
        keep = np.roll(quality, k) == 0
        expected_pdc = np.roll(pdc, k)[keep]
        aux = next(a for a in rot.aux.sectors if a.sector == sector)
        assert np.array_equal(aux.time, time[keep])  # time stamps never move
        assert np.allclose(aux.pdcsap_flux, expected_pdc / np.median(expected_pdc))
        sap_k = np.roll(sap, k)[keep]
        assert np.allclose(aux.sap_flux, sap_k / np.median(sap_k))  # SAP moved with PDCSAP
        assert np.allclose(aux.sap_bkg, np.roll(bkg, k)[keep] / np.median(sap_k))
        # a dump is a quality bit: it moves with its cadence even though the mask removes it
        assert np.allclose(aux.dump_times, np.sort(time[np.roll(quality, k) != 0]))
        base_aux = next(a for a in base.aux.sectors if a.sector == sector)
        assert aux.crowdsap == base_aux.crowdsap and aux.flfrcsap == base_aux.flfrcsap
        px = next(p for p in rot.aux.pixels if p.sector == sector)
        assert np.array_equal(px.time, aux.time)  # light curve and pixels aligned


def test_3_10_sabotage_rotating_the_flux_alone_is_caught(cache):
    manifest = read_json(manifest_path(cache, 1))
    record = manifest["files"][0]
    with fits.open(cache / record["path"]) as hdul:
        sap = np.asarray(hdul[1].data["SAP_FLUX"], float)
        quality = np.asarray(hdul[1].data["QUALITY"], int)
    k = 50
    rot = _load(cache, tr.Transform(tr.ROTATE, {int(record["sector"]): k}, "r"))
    aux = next(a for a in rot.aux.sectors if a.sector == int(record["sector"]))
    unrotated_sap = sap[np.roll(quality, k) == 0]
    assert not np.allclose(aux.sap_flux, unrotated_sap / np.median(unrotated_sap))


def test_a_pixel_file_on_another_grid_cannot_be_rotated(tmp_path):
    from refute.packs.tess.adapter import DataError

    root = tmp_path / "cache"
    data = scenario_data("planet", seed=4)
    write_synthetic_cache(root, 1, data.lc, data.star, aux=data.aux)  # pixels lack dump cadences
    manifest = read_json(manifest_path(root, 1))
    sector = int(manifest["files"][0]["sector"])
    with pytest.raises(DataError, match="cannot be rotated"):
        _load(root, tr.Transform(tr.ROTATE, {sector: 40}, "r"))


def test_3_7_fixed_offsets_shift_the_phase_between_sectors():
    t = np.arange(0.0, 20.0, 0.01)
    signal = (np.mod(t, 2.0) < 0.1).astype(float)
    a, b = tr.rotate(signal, 0), tr.rotate(signal, 37)
    first_a, first_b = t[np.argmax(a > 0)], t[np.argmax(b > 0)]
    assert first_a != first_b  # the phase of sector b moved
    assert b.sum() == a.sum()  # every transit inside the sector stays visible


def test_3_11_the_offsets_exclude_the_identity_and_differ_between_rotations():
    lengths = {1: 1000, 2: 1000, 3: 50}
    rotations = tr.rotation_offsets(tr.stream_seed("cd" * 32, "v0.4", "transform", 7), lengths)
    assert rotations.unrotated == {3: f"fewer than {TRANSFORMS.min_sector_cadences} cadences"}
    first, second = rotations.offsets
    assert first != second
    for vector in rotations.offsets:
        assert set(vector) == {1, 2}
        assert all(100 <= k <= 900 for k in vector.values())
    again = tr.rotation_offsets(tr.stream_seed("cd" * 32, "v0.4", "transform", 7), lengths)
    assert again.offsets == rotations.offsets


def test_3_11_a_curve_with_no_rotatable_sector_has_inconclusive_rotations():
    rotations = tr.rotation_offsets(1, {1: 10})
    assert rotations.inconclusive == [0, 1]


def test_3_9_and_3_8_stage_1_transformed_curves_and_their_summary(cache):
    task = measure.TransformTask(TARGET, PLAN_DICT, str(cache), seed=11, position=0, stage=1)
    record = measure.run_transform(task)
    assert record["status"] == "OK"
    tests = record["chain"]["tests"]
    assert tests["centroid_shift"]["status"] == "INCONCLUSIVE"
    summary = measure.summarize_transforms([record])
    assert summary["transformed_curves"] == 1
    assert "not a false-alarm rate" in summary["name"]
    assert set(summary) >= {"gate_passed", "survived_stage_tests", "inconclusive"}


def test_a_stage_1_worker_never_reads_a_pixel_file(cache):
    assert _load(cache).aux.pixels  # the cache holds pixel files
    stage1 = TessAdapter().load(TARGET, measure.stage_plan(PLAN_DICT, 1), cache)
    assert stage1.aux.pixels == []


def test_the_stage_outcome_is_kept_apart_from_the_verdict():
    data = scenario_data("planet", seed=3)
    out = measure.chain(data, PLAN, 1)
    assert out["verdict"] == "INCONCLUSIVE"  # the pixel tests are deferred
    assert "centroid_shift" not in out["stage_tests"]
    assert out["stage_verdict"] in ("SURVIVED", "WEAKENED"), out["stage_verdict_reason"]
    assert out["survived_stage_tests"] is True


def test_3_8_the_injection_summary_has_rates_and_intervals():
    records = [
        {
            "recovery": {"recovered": i < 7, "alias": None, "gate_passed": True},
            "crowdsap_missing_sectors": [],
        }  # fmt: skip
        for i in range(10)
    ]
    summary = inj.summarize(records)
    assert summary["recovered"] == 7 and summary["recovery_rate"] == 0.7
    low, high = summary["recovery_wilson_95"]
    assert low < 0.7 < high
    assert "approximate" in summary["independence"]


def test_the_measurement_tasks_follow_the_seeds_and_the_prefix(cache):
    from refute.packs.tess.discover import runs

    injections, transforms = runs.measurement_tasks(TARGET, PLAN_DICT, cache, "ab" * 32, 7, 2)
    assert [t.index for t in injections] == list(range(7)) and all(t.stage == 1 for t in injections)
    assert [t.position for t in transforms] == [0, 1, 2] and all(t.stage == 2 for t in transforms)
    rest, _ = runs.measurement_tasks(TARGET, PLAN_DICT, cache, "ab" * 32, 7, 2, first_injection=5)
    assert [t.index for t in rest] == [5, 6] and rest[0].seed == injections[0].seed


def test_measurements_write_their_records_and_costs(cache, tmp_path):
    from refute.packs.tess.discover import runs

    injections, transforms = runs.measurement_tasks(TARGET, PLAN_DICT, cache, "ab" * 32, 1, 1)
    summaries = runs.run_measurements([*injections, transforms[0]], tmp_path / "m", workers=1)
    lines = (tmp_path / "m" / "cost.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2 and all("cpu_seconds" in line for line in lines)
    summary = summaries["TIC-1"]
    assert summary["injections"]["injections"] == 1
    assert summary["transformed_curves"]["transformed_curves"] == 1
    with pytest.raises(FileExistsError):
        runs.run_measurements([*injections], tmp_path / "m", workers=1)


def test_the_continuation_runs_only_the_remaining_injections(cache):
    from refute.packs.tess.discover import runs

    rest, curves = runs.measurement_tasks(
        TARGET, PLAN_DICT, cache, "ab" * 32, 7, 2, first_injection=5, transforms=False
    )
    assert [t.index for t in rest] == [5, 6] and curves == []


def test_a_task_recorded_twice_is_refused_never_counted_twice():
    from refute.packs.tess.discover import runs

    record = {"kind": "injection", "target_key": "TIC-1", "index": 0, "stage": 1,
              "recovery": {"recovered": True, "alias": None, "gate_passed": True},
              "crowdsap_missing_sectors": []}  # fmt: skip
    with pytest.raises(ValueError, match="twice"):
        runs.summarize_records([record, dict(record)])
    other = {**record, "index": 1}
    summary = runs.summarize_records([record, other])["TIC-1"]
    assert summary["injections"]["injections"] == 2


def test_a_failing_task_is_a_record_with_its_cost(tmp_path):
    task = measure.InjectionTask(TARGET, PLAN_DICT, str(tmp_path / "empty"), 1, 0, 1)
    record = measure.run_injection(task)
    assert record["status"] == "ERROR" and record["cpu_seconds"] >= 0
    assert record["recovery"]["recovered"] is False


def test_the_rotation_lengths_stop_at_max_sector(cache):
    plan = TessTestPlan.model_validate(
        {**PLAN_DICT, "discovery": {**PLAN_DICT["discovery"], "max_sector": 1}}
    )
    manifest = read_json(manifest_path(cache, 1))
    first = min(int(f["sector"]) for f in manifest["files"])
    _, rotations = measure.transforms_of(TARGET, cache, 3, plan)
    sectors = {int(s) for vector in rotations.to_dict()["offsets"] for s in vector}
    assert sectors <= {s for s in [first] if s <= 1}


def _box_depth(time, flux, injection):
    """The mean deficit inside the flat bottom, against the median outside the transits."""
    dt = np.mod(time - injection.t0_btjd + 0.5 * injection.period_days, injection.period_days)
    dt = dt - 0.5 * injection.period_days
    inside = np.abs(dt) < 0.3 * injection.duration_days
    outside = np.abs(dt) > injection.duration_days
    return float(np.median(flux[outside]) - np.mean(flux[inside]))


def test_the_sap_dip_is_the_pdcsap_dip_times_crowdsap_in_every_sector(noise_data):
    injection = _injection(0.004)
    injected = inj.inject(noise_data, injection)
    for before, after in zip(noise_data.aux.sectors, injected.aux.sectors, strict=True):
        pdc = _box_depth(after.time, after.pdcsap_flux, injection) - _box_depth(
            before.time, before.pdcsap_flux, injection
        )
        sap = _box_depth(after.time, after.sap_flux, injection) - _box_depth(
            before.time, before.sap_flux, injection
        )
        assert pdc == pytest.approx(0.004, rel=0.05)
        assert sap / pdc == pytest.approx(before.crowdsap, rel=0.05)


def test_the_synthetic_generator_follows_the_same_pdcsap_sap_relation():
    # a natural synthetic transit (scenario "planet"): the generator writes SAP = 1 + c (PDC - 1)
    data = scenario_data("planet", seed=4)
    from refute.packs.tess.synthetic import PLANET

    spec = inj.Injection(0, PLANET.period, PLANET.depth, 0.0, PLANET.duration, PLANET.t0)
    for sector in data.aux.sectors:
        pdc = _box_depth(sector.time, sector.pdcsap_flux, spec)
        sap = _box_depth(sector.time, sector.sap_flux, spec)
        assert sap / pdc == pytest.approx(sector.crowdsap, rel=0.1)


def test_a_missing_crowdsap_is_recorded_and_counted_apart(noise_data):
    sectors = [
        replace(s, crowdsap=None) if i == 0 else s for i, s in enumerate(noise_data.aux.sectors)
    ]
    data = replace(noise_data, aux=replace(noise_data.aux, sectors=sectors))
    assert inj.crowdsap_missing(data) == [int(sectors[0].sector)]
    assert inj.crowdsap_missing(noise_data) == []
    known = {"recovery": {"recovered": True, "alias": None, "gate_passed": True},
             "crowdsap_missing_sectors": []}  # fmt: skip
    missing = {"recovery": {"recovered": True, "alias": None, "gate_passed": True},
               "crowdsap_missing_sectors": [int(sectors[0].sector)]}  # fmt: skip
    summary = inj.summarize([known, missing, dict(missing)])
    assert summary["injections"] == 1 and summary["recovery_rate"] == 1.0
    assert summary["crowdsap_missing"]["injections"] == 2
    assert summary["crowdsap_missing"]["sectors"] == [int(sectors[0].sector)]
    assert "not equivalent" in summary["crowdsap_missing"]["note"]


def test_a_task_that_fails_before_reading_is_in_the_unknown_group(tmp_path):
    task = measure.InjectionTask(TARGET, PLAN_DICT, str(tmp_path / "empty"), 1, 0, 1)
    record = {"kind": "injection", **measure.run_injection(task)}
    assert record["crowdsap_missing_sectors"] is None
    summary = inj.summarize([record])
    assert summary["tasks"] == 1 and summary["injections"] == 0
    assert summary["crowdsap_unknown"]["injections"] == 1
