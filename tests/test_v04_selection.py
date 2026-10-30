"""v0.4 WP2: frame, exclusions, domain, walk, retries and deduplication (cases 2.1 to 2.10 of
docs/plans/v0.4-acceptance.md). Synthetic inputs only; no network."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

from refute.drand import round_after, shuffled
from refute.packs.tess.discover import dedup as dd
from refute.packs.tess.discover import pilot
from refute.packs.tess.discover import selection as sel
from refute.selection.walk import RetryPolicy, TransientError

ROOT = Path(__file__).resolve().parents[1]


def _list(sector: int, rows: list[tuple[int, float, float, float]]) -> str:
    lines = ["#", f"# Full target list for sector {sector}", "#", "TICID,Camera,CCD,Tmag,RA,Dec"]
    lines += [f"{tic},1,1,{tmag},{ra},{dec}" for tic, tmag, ra, dec in rows]
    return "\n".join(lines) + "\n"


LISTS = {
    1: _list(1, [(10, 9.0, 10.0, -5.0), (20, 10.0, 20.0, 5.0), (30, 11.0, 30.0, 0.0)]),
    2: _list(2, [(10, 9.0, 10.0, -5.0), (20, 10.0, 20.0, 5.0), (40, 8.5, 40.0, 1.0)]),
    3: _list(3, [(10, 9.0, 10.0, -5.0), (20, 10.0, 20.0, 5.0), (30, 11.0, 30.0, 0.0)]),
    4: _list(4, [(30, 11.0, 30.0, 0.0), (50, 9.5, 50.0, 2.0)]),
}


def test_list_urls_takes_one_list_per_sector_and_refuses_ambiguity():
    page = (
        '<a href="https://tess.mit.edu/public/target_lists/2m/all_targets_S001_v1.csv">csv</a>'
        '<a href="https://tess.mit.edu/public/target_lists/2m/all_targets_S002_v1.csv">csv</a>'
        '<a href="https://tess.mit.edu/public/target_lists/20s/all_targets_20s_S002_v1.csv">x</a>'
    )
    assert pilot.sel.list_urls(page, 2)[2].endswith("all_targets_S002_v1.csv")
    with pytest.raises(sel.SelectionError, match="sector 3"):
        sel.list_urls(page, 3)
    twice = page + '<a href="x/target_lists/2m/all_targets_S002_v2.csv">csv</a>'
    with pytest.raises(sel.SelectionError, match="sector 2: 2"):
        sel.list_urls(twice, 2)


def test_a_list_with_an_unexpected_header_is_refused():
    with pytest.raises(sel.SelectionError, match="header"):
        sel.parse_target_list("TIC,Tmag\n1,9\n")


def test_the_frame_keeps_stars_in_at_least_three_sectors():
    frame = sel.build_frame(LISTS)
    assert [s.tic_id for s in frame] == [10, 20, 30]
    assert frame[2].sectors == (1, 3, 4)
    assert sel.read_frame_csv(sel.frame_csv(frame)) == frame


def test_2_1_the_same_inputs_give_the_same_order_and_log():
    def run():
        frame = sel.build_frame(LISTS)
        order = pilot.funnel_order(frame, "ab" * 32)
        log = sel.walk("funnel", order, _triage_all_ok, 2, RetryPolicy(2, 0), lambda _s: None)
        return json.dumps(log.to_dict(), sort_keys=True).encode()

    assert run() == run()


def test_2_2_duplicate_sort_keys_are_refused():
    with pytest.raises(ValueError, match="not unique"):
        shuffled([1, 1, 2], 7, key=lambda x: x)


def test_2_3_catalogued_stars_are_excluded_with_every_reason():
    frame = sel.build_frame(LISTS)
    gaia = np.array([[30.0 + 5.0 / 3600.0, 0.0]])  # 5 arcsec from TIC 30
    out = sel.apply_exclusions(
        frame,
        known={10},
        tic_sets={"TOI": {10}, "CTOI": set(), "pscomppars": set(), "TESS-EB": set()},
        gaia_positions=gaia,
    )
    assert [s.tic_id for s in out.kept] == [20]
    assert out.reasons[10] == ["known_target", "TOI"]
    assert out.reasons[30] == ["Gaia-DR3-EB"]
    counts = out.counts()
    assert counts["first:known_target"] == 1 and counts["any:TOI"] == 1
    assert counts["first:Gaia-DR3-EB"] == 1


def test_a_missing_snapshot_stops_the_exclusions():
    with pytest.raises(sel.SelectionError, match="CTOI"):
        sel.apply_exclusions([], set(), {"TOI": set()}, np.zeros((0, 2)))


TIC_OK = {
    "logg": 4.4,
    "rad": 1.0,
    "e_rad": 0.05,
    "Teff": 5700.0,
    "Tmag": 10.0,
    "contratio": 0.01,
    "ra": 1.0,
    "dec": 2.0,
}
# three sectors over two calendar years, 2018 and 2019 (MJD), more than 300 days apart
LISTING_OK = sel.Listing(((1, 58325.0), (2, 58353.0), (14, 58682.0)), ((1, 0), (2, 0), (14, 0)))


def _triage_all_ok(_tic):
    return sel.domain_check(TIC_OK, LISTING_OK)


@pytest.mark.parametrize(
    ("change", "listing", "rule"),
    [
        ({}, sel.Listing(((1, 58325.0), (2, 58353.0)), ((1, 0), (2, 0))), "D-1"),
        (
            {},
            sel.Listing(((1, 58325.0), (2, 58353.0), (3, 58381.0)), ((1, 0), (2, 0), (3, 0))),
            "D-2",
        ),
        ({}, sel.Listing(LISTING_OK.light_curves, ((1, 0), (2, 0))), "D-3"),
        ({"logg": 3.9}, LISTING_OK, "D-4"),
        ({"e_rad": 0.3}, LISTING_OK, "D-5"),
        ({"Teff": 7100.0}, LISTING_OK, "D-6"),
        ({"Tmag": 12.5}, LISTING_OK, "D-7"),
        ({"contratio": None}, LISTING_OK, "D-8"),
    ],
)
def test_2_4_the_domain_rejects_by_metadata_only_with_the_rule(change, listing, rule):
    ok, reason, evidence = sel.domain_check({**TIC_OK, **change}, listing)
    assert not ok and reason.startswith(rule)
    assert "light_curve_sectors" in evidence


def test_2_4_the_domain_accepts_and_takes_no_signal():
    assert sel.domain_check(TIC_OK, LISTING_OK)[0] is True
    import inspect

    assert list(inspect.signature(sel.domain_check).parameters) == ["tic", "listing", "domain"]


def test_a_tic_answer_without_a_field_stops_the_selection():
    with pytest.raises(sel.SelectionError, match="contratio"):
        sel.domain_check({k: v for k, v in TIC_OK.items() if k != "contratio"}, LISTING_OK)


def test_2_5_a_transient_error_then_success_is_accepted_and_logged():
    calls = {"n": 0}

    def flaky(tic):
        calls["n"] += 1
        if calls["n"] == 1:
            raise TransientError("MAST: timeout")
        return _triage_all_ok(tic)

    log = sel.walk("funnel", [5], flaky, 1, RetryPolicy(3, 0), lambda _s: None)
    assert log.accepted == [5]
    assert log.decisions[0].transient_attempts[0]["error"] == "MAST: timeout"


def test_2_6_exhausted_retries_stop_the_walk_without_a_skip():
    def down(_tic):
        raise TransientError("MAST: HTTP 503")

    log = sel.walk("funnel", [5, 6], down, 1, RetryPolicy(2, 0), lambda _s: None)
    assert log.stopped and log.outcome == "stopped_transient"
    assert [d.tic_id for d in log.decisions] == [5]


def test_a_non_transient_error_propagates():
    def broken(_tic):
        raise KeyError("x")

    with pytest.raises(KeyError):
        sel.walk("funnel", [5], broken, 1, RetryPolicy(2, 0), lambda _s: None)


def test_2_7_the_known_targets_come_from_their_files():
    known = sel.known_targets(ROOT)
    assert 207141131 in known  # v0.1 planet (calibration/targets.yaml)
    assert 207339000 in known  # v0.1 development target
    assert 9989136 in known  # v0.2.1 gate-3b eligible planet
    assert len(known) >= 14 + 21


def test_the_control_pools_follow_the_protocol_filters():
    planets = sel.planet_pool(
        [
            {
                "tic_id": "TIC 1",
                "tran_flag": "1",
                "sy_pnum": "1",
                "pl_orbper": "3",
                "pl_trandep": "0.5",
            },
            {
                "tic_id": "TIC 2",
                "tran_flag": "1",
                "sy_pnum": "2",
                "pl_orbper": "3",
                "pl_trandep": "0.5",
            },
            {
                "tic_id": "TIC 3",
                "tran_flag": "1",
                "sy_pnum": "1",
                "pl_orbper": "14",
                "pl_trandep": "0.5",
            },
            {
                "tic_id": "TIC 4",
                "tran_flag": "1",
                "sy_pnum": "1",
                "pl_orbper": "3",
                "pl_trandep": "0.05",
            },
        ],
        0.1,
    )
    assert [p.tic_id for p in planets] == [1]
    fps = sel.fp_pool(
        [
            {
                "TIC ID": "7",
                "TOI": "100.01",
                "TFOPWG Disposition": "FP",
                "Period (days)": "2",
                "Depth (ppm)": "2000",
            },
            {
                "TIC ID": "8",
                "TOI": "101.01",
                "TFOPWG Disposition": "FP",
                "Period (days)": "2",
                "Depth (ppm)": "2000",
            },
            {
                "TIC ID": "8",
                "TOI": "101.02",
                "TFOPWG Disposition": "PC",
                "Period (days)": "5",
                "Depth (ppm)": "2000",
            },
            {
                "TIC ID": "9",
                "TOI": "102.01",
                "TFOPWG Disposition": "FP",
                "Period (days)": "2",
                "Depth (ppm)": "900",
            },
            {
                "TIC ID": "1",
                "TOI": "103.01",
                "TFOPWG Disposition": "FP",
                "Period (days)": "2",
                "Depth (ppm)": "2000",
            },
        ],
        planet_tics={1},
        min_depth_ppm=1000.0,
    )
    assert [p.tic_id for p in fps] == [7]


def _index(entries):
    return dd.CatalogIndex(entries)


@pytest.mark.parametrize("factor", [1.0, 2.0, 0.5, 3.0, 1.0 / 3.0])
def test_2_8_a_known_period_at_an_alias_matches(factor):
    index = _index([dd.CatalogEntry("TOI-1.01", 5, 10.0, 0.0, 2.0)])
    out = dd.match_catalog("TOI", index, 5, 10.0, 0.0, 2.0 * factor * 1.004)
    assert out.state == dd.MATCH and out.matches[0]["alias_factor"] == factor
    assert out.coverage == 1


def test_2_8_a_nearby_star_matches_by_position_and_a_far_one_does_not():
    near = dd.CatalogEntry("EB near", None, 10.0 + 10 / 3600, 0.0, 2.0)
    far = dd.CatalogEntry("EB far", None, 10.0 + 60 / 3600, 0.0, 2.0)
    out = dd.match_catalog("Gaia-DR3-EB", _index([near, far]), 99, 10.0, 0.0, 2.0)
    assert [m["identifier"] for m in out.matches] == ["EB near"]
    assert out.coverage == 2


def test_2_9_missing_information_is_inconclusive_never_no_match():
    no_period = _index([dd.CatalogEntry("TOI-9.01", 5, 10.0, 0.0, None)])
    out = dd.match_catalog("TOI", no_period, 5, 10.0, 0.0, 2.0)
    assert out.state == dd.INCONCLUSIVE and "without a period" in out.reason
    far = _index([dd.CatalogEntry("x", 777, 50.0, 50.0, 9.0)])
    out = dd.match_catalog("TOI", far, 5, None, None, 2.0)
    assert out.state == dd.INCONCLUSIVE and "no position" in out.reason
    same_tic = _index([dd.CatalogEntry("TOI-1.01", 5, None, None, 2.0)])
    assert dd.match_catalog("TOI", same_tic, 5, None, None, 2.0).state == dd.MATCH


def test_2_9_a_missing_or_empty_snapshot_is_inconclusive_never_no_match():
    assert dd.match_catalog("CTOI", None, 1, 0, 0, 2.0).state == dd.INCONCLUSIVE
    assert dd.match_catalog("CTOI", _index([]), 1, 0, 0, 2.0).state == dd.INCONCLUSIVE
    indexes = {name: _index([dd.CatalogEntry("x", 777, 50, 50, 9.0)]) for name in dd.DEDUP.catalogs}
    indexes["CTOI"] = None
    out = dd.deduplicate(indexes, 1, 0.0, 0.0, 2.0)
    assert out["overall"] == dd.INCONCLUSIVE
    indexes["CTOI"] = _index([dd.CatalogEntry("x", 777, 50, 50, 9.0)])
    assert dd.deduplicate(indexes, 1, 0.0, 0.0, 2.0)["overall"] == dd.NO_MATCH


def test_2_10_a_file_above_5_mb_is_never_in_git():
    small = pilot.record("a", "u", b"x" * 10, "t")
    big = pilot.record("b", "u", b"x" * (5 * 1000**2 + 1), "t")
    assert small["in_git"] is True and big["in_git"] is False
    assert len(big["sha256"]) == 64
    assert pilot.record("lists/all_targets_S001_v1.csv", "u", b"x", "t")["in_git"] is False
    assert pilot.record("frame.csv", "u", b"x", "t")["in_git"] is False
    assert pilot.record("tess_eb.tsv", "u", b"x", "t")["in_git"] is False  # not redistributed


STATIC_EB = (
    b"#INFO\trequest_date=2026-10-18T00:56:26\n"
    b"TIC\tm_TIC\tRAJ2000\tDEJ2000\tPer\n \t \tdeg\tdeg\td\n--\t-\t--\t--\t--\n"
    b"0000000103\t1\t104.0\t00.0\t  1.0000000\n"
)


def _static_eb(root: Path) -> dict:
    """A synthetic TESS-EB static edition under ``root`` and its expected hashes."""
    import hashlib

    from refute.packs.tess.ebcatalog import content_sha256

    path = root / "eb" / "static.tsv"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(STATIC_EB)
    return {
        **pilot.TESS_EB_STATIC,
        "path": "eb/static.tsv",
        "sha256": hashlib.sha256(STATIC_EB).hexdigest(),
        "content_sha256": content_sha256(STATIC_EB),
    }


def _eb_kwargs(root: Path) -> dict:
    return {"tess_eb_path": root / "eb" / "static.tsv", "tess_eb": _static_eb(root)}


def test_the_freeze_checks_the_gaia_asset_hash(tmp_path):
    page = "".join(
        f'<a href="https://tess.mit.edu/public/target_lists/2m/all_targets_S{s:03d}_v1.csv">c</a>'
        for s in (1, 2, 3, 4)
    )

    def fetch(url):
        if url == pilot.TARGET_LISTS_PAGE:
            return page.encode()
        for s in (1, 2, 3, 4):
            if url.endswith(f"S{s:03d}_v1.csv"):
                return LISTS[s].encode()
        if url == pilot.GAIA_EB_URL:
            return b"source_id,ra,dec,frequency\n1,0,0,1\n"
        return b"TIC ID\n1\n"

    with pytest.raises(sel.SelectionError, match="Gaia"):
        pilot.freeze(
            tmp_path / "attempt",
            4,
            fetch=fetch,
            now=lambda: "2026-10-29T00:00:00Z",
            **_eb_kwargs(tmp_path),
        )
    assert (tmp_path / "attempt" / "frame.csv").is_file()


def test_the_push_run_must_be_unique():
    def fetch(runs):
        return lambda _url: json.dumps({"workflow_runs": runs}).encode()

    sha = "a" * 40
    one = [{"head_sha": sha, "run_attempt": 1, "created_at": "2026-11-01T10:00:00Z"}]
    assert pilot.push_run_created_at(sha, fetch(one)) == "2026-11-01T10:00:00Z"
    with pytest.raises(sel.SelectionError, match="0 first-attempt"):
        pilot.push_run_created_at(sha, fetch([]))
    with pytest.raises(sel.SelectionError, match="2 first-attempt"):
        pilot.push_run_created_at(sha, fetch(one + one))


def _inputs(tmp_path: Path) -> tuple[Path, dict]:
    files = {
        "frame.csv": sel.frame_csv(
            [sel.FrameStar(t, (1, 2, 3), 10.0, float(t), 0.0) for t in range(100, 400)]
        ),
        "toi.csv": (
            b"TOI,TIC ID,TFOPWG Disposition,Period (days),Depth (ppm)\n"
            b"500.01,500,FP,2.0,3000\n501.01,501,FP,2.5,4000\n100.01,100,PC,3.0,500\n"
        ),
        "ctoi.csv": b"TIC ID\n101\n",
        "pscomppars.csv": (
            b"pl_name,tic_id,tran_flag,sy_pnum,pl_orbper,pl_trandep\n"
            b"P b,TIC 600,1,1,3.0,0.5\nQ b,TIC 207141131,1,1,3.0,0.5\nR b,TIC 102,1,1,3,0.5\n"
        ),
        "tess_eb.tsv": b"TIC\tm_TIC\tPer\n\t\td\n--\t--\t--\n103\t\t1.0\n",
        "gaia_dr3_eb.csv": b"source_id,ra,dec,frequency\n1,104.0,0.0,1.0\n",
    }
    records = []
    for name, data in files.items():
        (tmp_path / name).write_bytes(data)
        records.append(pilot.record(name, "synthetic", data, "2026-10-29T00:00:00Z"))
    return tmp_path, {"files": records, "s_max": 3}


def test_the_selection_runs_offline_from_the_frozen_inputs(tmp_path):
    inputs_dir, inputs = _inputs(tmp_path)

    def triage(tic, domain, s_max):
        assert s_max == 3
        ok = tic % 3 != 0 or tic in (500, 501, 600)
        return ok, "accepted" if ok else "D-7: Tmag", {"tic": tic, "tmag_max": domain.tmag_max}

    out = pilot.run_selection(inputs_dir, inputs, "ab" * 32, ROOT, triage, lambda _s: None)
    assert out["complete"] is True
    accepted = out["funnel"]["accepted"]
    assert len(accepted) == 100 and len(set(accepted)) == 100
    assert not {100, 101, 102, 103, 104} & set(accepted)  # TOI, CTOI, planet, TESS-EB, Gaia EB
    assert out["controls"]["planet"]["accepted"] == 600  # the known target 207141131 is out
    assert out["controls"]["false_positive"]["accepted"] in (500, 501)
    again = pilot.run_selection(inputs_dir, inputs, "ab" * 32, ROOT, triage, lambda _s: None)
    assert json.dumps(again, sort_keys=True) == json.dumps(out, sort_keys=True)
    other = pilot.run_selection(inputs_dir, inputs, "cd" * 32, ROOT, triage, lambda _s: None)
    assert other["funnel"]["accepted"] != accepted


def test_a_changed_input_stops_the_selection(tmp_path):
    inputs_dir, inputs = _inputs(tmp_path)
    (inputs_dir / "ctoi.csv").write_bytes(b"TIC ID\n999\n")
    with pytest.raises(sel.SelectionError, match="ctoi.csv"):
        pilot.run_selection(inputs_dir, inputs, "ab" * 32, ROOT, lambda t, d, s: (True, "", {}))


def test_the_ladder_relaxes_one_step_at_a_time(tmp_path):
    inputs_dir, inputs = _inputs(tmp_path)

    def triage(tic, domain, s_max):
        if tic == 600:  # the planet passes only with the relaxed Tmag of step 1
            return domain.tmag_max >= 13.0, "D-7", {}
        if tic == 102:  # the other planet of the pool never passes
            return False, "D-4", {}
        return True, "accepted", {}

    out = pilot.run_selection(inputs_dir, inputs, "ab" * 32, ROOT, triage, lambda _s: None)
    planet = out["controls"]["planet"]
    assert [a["step"] for a in planet["attempts"]] == [0, 1]
    assert planet["accepted"] == 600


def test_the_selection_refuses_a_tree_that_is_not_the_protocol_commit(git_repo):
    from conftest import git
    from refute.packs.tess.discover import steps

    (git_repo / "src").mkdir()
    (git_repo / "src" / "a.py").write_text("x = 1\n", encoding="utf-8")
    (git_repo / "pyproject.toml").write_text("[project]\n", encoding="utf-8")
    git(git_repo, "add", "-A")
    git(git_repo, "commit", "-q", "-m", "protocol")
    commit = git(git_repo, "rev-parse", "HEAD").strip()
    assert steps.bound_problems(git_repo, commit) == []
    (git_repo / "src" / "a.py").write_text("x = 2\n", encoding="utf-8")
    assert any("changed since" in p for p in steps.bound_problems(git_repo, commit))
    (git_repo / "src" / "a.py").write_text("x = 1\n", encoding="utf-8")
    (git_repo / "src" / "b.py").write_text("y = 1\n", encoding="utf-8")
    assert any("untracked" in p for p in steps.bound_problems(git_repo, commit))
    assert any("ancestor" in p for p in steps.bound_problems(git_repo, "0" * 40))
    with pytest.raises(sel.SelectionError, match="40-character"):
        steps.select_step(git_repo, "abc")


def test_the_archive_is_checked_from_its_copies(tmp_path):
    from refute.packs.tess.discover import steps

    root = tmp_path / "root"
    cache = root / steps.ATTEMPTS_DIR / "attempt-01"
    cache.mkdir(parents=True)
    inputs_dir, inputs = _inputs(cache)
    inputs["attempt"] = "attempt-01"
    (root / steps.STEP_DIR).mkdir(parents=True)
    (root / steps.STEP_DIR / "inputs.json").write_text(json.dumps(inputs), encoding="utf-8")
    drive = tmp_path / "drive"
    assert steps.archive_step(root, drive=drive) == []
    manifest = (drive / "MANIFEST.sha256").read_text(encoding="utf-8").splitlines()
    assert manifest[-1].endswith(steps.ZIP_NAME) and len(manifest) == len(inputs["files"]) + 2
    with pytest.raises(sel.SelectionError, match="not replaced"):
        steps.archive_step(root, drive=drive)


def test_the_targets_file_lists_the_controls_then_the_funnel_in_walk_order(tmp_path):
    from refute.packs.tess.discover import steps
    from refute.packs.tess.params import TargetsFile

    inputs_dir, inputs = _inputs(tmp_path)

    def triage(tic, domain, s_max):
        return True, "accepted", {"tic": tic}

    out = pilot.run_selection(inputs_dir, inputs, "ab" * 32, ROOT, triage, lambda _s: None)
    out.update({"round": 1, "protocol_commit": "a" * 40})
    document = steps.targets_document(out, inputs)
    parsed = TargetsFile.model_validate(document)
    kinds = [t.kind for t in parsed.targets]
    assert kinds[:2] == ["planet", "false_positive"] and set(kinds[2:]) == {"exploration"}
    assert [t.tic_id for t in parsed.targets[2:]] == out["funnel"]["accepted"]


def test_products_after_s_max_never_count_in_the_domain():
    late = sel.Listing(((1, 58325.0), (2, 58353.0), (90, 60100.0)), ((1, 0.0), (2, 0.0), (90, 0.0)))
    assert sel.domain_check(TIC_OK, late)[0] is True  # with sector 90 it would pass
    assert sel.domain_check(TIC_OK, pilot.up_to(late, 50))[1].startswith("D-1")
    with pytest.raises(sel.SelectionError, match="S_max"):
        pilot.triage(1, sel.DOMAIN, None)


def test_s_max_is_the_highest_sector_with_spoc_light_curves():
    counts = {111: 0, 110: 0, 109: 0, 108: 5}
    out = pilot.latest_spoc_sector(111, lambda s: counts.get(s, 1))
    assert out["s_max"] == 108 and [q["sector"] for q in out["queries"]] == [111, 110, 109, 108]


def test_round_after_is_the_v03_rule():
    sys.path.insert(0, str(ROOT / "calibration" / "v0.3" / "pilot"))
    try:
        import select_pilot
    finally:
        sys.path.pop(0)
    for created in ("2026-10-17T10:00:00Z", "2026-11-02T23:59:59Z", "2026-11-03T00:00:31Z"):
        assert round_after(created) == select_pilot.round_after(created)


def test_angles_parse_from_degrees_and_sexagesimal():
    assert pilot.parse_angle("150.5", hours=False) == 150.5
    assert pilot.parse_angle("10:00:00", hours=True) == pytest.approx(150.0)
    assert pilot.parse_angle("-30:30:00", hours=False) == pytest.approx(-30.5)
    assert pilot.parse_angle("10 00 00", hours=True) == pytest.approx(150.0)
    assert pilot.parse_angle("", hours=False) is None


def test_the_catalog_indexes_come_from_the_frozen_snapshots(tmp_path):
    inputs_dir, inputs = _inputs(tmp_path)
    indexes = pilot.catalog_indexes(inputs_dir, inputs)
    assert set(indexes) == set(dd.DEDUP.catalogs)
    assert indexes["TOI"].size == 3 and indexes["Gaia-DR3-EB"].size == 1
    out = dd.deduplicate(indexes, 500, 500.0, 0.0, 4.0)  # TOI 500.01 at P = 2.0 d, alias 2
    toi = next(c for c in out["catalogs"] if c["catalog"] == "TOI")
    assert toi["state"] == dd.MATCH and toi["matches"][0]["alias_factor"] == 2.0


def test_the_catalog_indexes_check_the_snapshot_hashes(tmp_path):
    inputs_dir, inputs = _inputs(tmp_path)
    (inputs_dir / "tess_eb.tsv").write_bytes(b"TIC\tm_TIC\tPer\n\t\td\n--\t--\t--\n999\t\t1.0\n")
    with pytest.raises(sel.SelectionError, match="tess_eb.tsv"):
        pilot.catalog_indexes(inputs_dir, inputs)
    with pytest.raises(sel.SelectionError, match="no recorded"):
        pilot.catalog_indexes(inputs_dir, {"files": []})


def test_the_page_links_its_lists_relatively():
    page = (
        '<a href="2m/all_targets_S110_v1.csv">csv</a><a href="2m/all_targets_S111_v1.csv">c</a>'
        '<a href="20s/all_targets_20s_S111_v1.csv">x</a><a href="2m/GI_targets_S111_v1.csv">g</a>'
    )
    assert pilot.highest_listed_sector(page) == 111
    with pytest.raises(sel.SelectionError, match="sector 1"):
        sel.list_urls(page, 111)
    relative = "".join(f'<a href="2m/all_targets_S{s:03d}_v1.csv">c</a>' for s in (1, 2))
    urls = sel.list_urls(relative, 2)
    assert urls[2] == "https://tess.mit.edu/public/target_lists/2m/all_targets_S002_v1.csv"


def _fake_fetch(fail_on: str | None = None):
    page = "".join(f'<a href="2m/all_targets_S{s:03d}_v1.csv">c</a>' for s in (1, 2, 3, 4))
    calls = {"n": 0}

    def fetch(url):
        calls["n"] += 1
        if fail_on and fail_on in url:
            raise TimeoutError("timed out")
        if url == pilot.TARGET_LISTS_PAGE:
            return page.encode()
        for s in (1, 2, 3, 4):
            if url.endswith(f"S{s:03d}_v1.csv"):
                return LISTS[s].encode()
        if url == pilot.GAIA_EB_URL:
            return b"source_id,ra,dec,frequency\n1,0,0,1\n"
        return b"TIC ID\n1\n"

    return fetch


def test_a_failed_attempt_keeps_its_folder_and_log_and_the_next_is_new(tmp_path, monkeypatch):
    from refute.packs.tess.discover import steps

    monkeypatch.setattr(pilot.sel, "policy", lambda: RetryPolicy(2, 0))
    root = tmp_path / "root"
    monkeypatch.setattr(pilot, "TESS_EB_STATIC", _static_eb(root))
    with pytest.raises(Exception, match="transient errors on all 2 attempts"):
        steps.freeze_step(root, s_max=4, fetch=_fake_fetch("download_ctoi"), sleep=lambda _s: None)
    first = root / steps.ATTEMPTS_DIR / "attempt-01"
    events = [json.loads(line) for line in (first / "attempt.jsonl").read_text().splitlines()]
    transient = [e for e in events if e["event"] == "transient"]
    assert [e["attempt"] for e in transient] == [1, 2]  # each logged before the next wait
    assert events[-1]["event"] == "failure" and "download_ctoi" in events[-1]["url"]
    files = [e["name"] for e in events if e["event"] == "file"]
    assert "toi.csv" in files and "ctoi.csv" not in files and "tess_eb.tsv" not in files
    assert not (first / "inputs.json").exists()
    before = (first / "toi.csv").read_bytes()
    assert steps.next_attempt(root).name == "attempt-02"
    with pytest.raises(sel.SelectionError, match="Gaia"):  # the fake Gaia bytes never match
        steps.freeze_step(root, s_max=4, fetch=_fake_fetch(), sleep=lambda _s: None)
    assert (first / "toi.csv").read_bytes() == before  # the first attempt is untouched
    assert (root / steps.ATTEMPTS_DIR / "attempt-02" / "tess_eb.tsv").is_file()


def test_a_freeze_never_writes_into_an_existing_folder(tmp_path):
    (tmp_path / "attempt").mkdir()
    with pytest.raises(FileExistsError):
        pilot.freeze(
            tmp_path / "attempt",
            s_max=4,
            fetch=_fake_fetch(),
            sleep=lambda _s: None,
            **_eb_kwargs(tmp_path),
        )


def test_the_selection_reads_only_the_recorded_attempt(tmp_path):
    from refute.packs.tess.discover import steps

    assert steps.cache_dir(tmp_path, {"attempt": "attempt-03"}).name == "attempt-03"
    with pytest.raises(sel.SelectionError, match="no freeze attempt"):
        steps.cache_dir(tmp_path, {})


def test_the_gaia_rule_cost_splits_the_stars_it_alone_excludes_by_separation():
    frame = [
        sel.FrameStar(1, (1, 2, 3), 10.0, 10.0, 0.0),
        sel.FrameStar(2, (1, 2, 3), 10.0, 20.0, 0.0),
        sel.FrameStar(3, (1, 2, 3), 10.0, 30.0, 0.0),
        sel.FrameStar(4, (1, 2, 3), 10.0, 40.0, 0.0),
    ]
    gaia = np.array([[10.0, 1.0 / 3600], [20.0, 4.0 / 3600], [30.0, 15.0 / 3600]])
    sets = {"TOI": {3}, "CTOI": set(), "pscomppars": set(), "TESS-EB": set()}
    out = sel.apply_exclusions(frame, set(), sets, gaia)
    cost = sel.gaia_exclusion_cost(out, frame, gaia)
    assert cost["excluded_by_gaia"] == 3 and cost["excluded_only_by_gaia"] == 2
    assert cost["only_by_gaia_by_separation"] == {
        "0-2 arcsec": 1,
        "2-5 arcsec": 1,
        "5-21 arcsec": 0,
    }


def test_a_non_transient_error_leaves_its_failure_event(tmp_path):
    def broken(url):
        raise KeyError("parse")

    with pytest.raises(KeyError):
        pilot.freeze(
            tmp_path / "a", s_max=4, fetch=broken, sleep=lambda _s: None, **_eb_kwargs(tmp_path)
        )
    events = [json.loads(x) for x in (tmp_path / "a" / "attempt.jsonl").read_text().splitlines()]
    assert events[-1]["event"] == "failure" and "KeyError" in events[-1]["error"]


def test_published_inputs_without_inputs_json_are_never_written_over(tmp_path):
    from refute.packs.tess.discover import steps

    root = tmp_path / "root"
    (root / steps.STEP_DIR / "inputs").mkdir(parents=True)
    with pytest.raises(sel.SelectionError, match="not written over"):
        steps.freeze_step(root, s_max=4, fetch=_fake_fetch(), sleep=lambda _s: None)
    assert not (root / steps.ATTEMPTS_DIR).exists()  # refused before any download


def test_the_tess_eb_static_edition_is_checked_before_any_download(tmp_path):
    calls = []

    def fetch(url):
        calls.append(url)
        return b""

    kwargs = _eb_kwargs(tmp_path)
    with pytest.raises(sel.SelectionError, match="raw SHA-256"):
        pilot.freeze(
            tmp_path / "a",
            s_max=4,
            fetch=fetch,
            tess_eb_path=kwargs["tess_eb_path"],
            tess_eb={**kwargs["tess_eb"], "sha256": "0" * 64},
        )
    with pytest.raises(sel.SelectionError, match="content SHA-256"):
        pilot.freeze(
            tmp_path / "b",
            s_max=4,
            fetch=fetch,
            tess_eb_path=kwargs["tess_eb_path"],
            tess_eb={**kwargs["tess_eb"], "content_sha256": "0" * 64},
        )
    with pytest.raises(FileNotFoundError):
        pilot.freeze(tmp_path / "c", s_max=4, fetch=fetch, tess_eb_path=tmp_path / "none.tsv")
    with pytest.raises(sel.SelectionError, match="static edition"):
        pilot.freeze(tmp_path / "d", s_max=4, fetch=fetch)
    assert calls == []  # nothing was downloaded
    for name in "abcd":
        last = (tmp_path / name / "attempt.jsonl").read_text().splitlines()[-1]
        assert json.loads(last)["event"] == "failure"


def test_a_complete_freeze_records_the_static_edition_and_keeps_it_out_of_git(
    tmp_path, monkeypatch
):
    import hashlib

    from refute.packs.tess.discover import steps

    root = tmp_path / "root"
    monkeypatch.setattr(pilot, "TESS_EB_STATIC", _static_eb(root))
    gaia = b"source_id,ra,dec,frequency\n1,0,0,1\n"
    monkeypatch.setattr(pilot, "GAIA_EB_SHA256", hashlib.sha256(gaia).hexdigest())

    def fetch(url):
        if url == pilot.GAIA_EB_URL:
            return gaia
        return _fake_fetch()(url)

    monkeypatch.setattr(steps, "exclusion_preview", lambda _root, _cache: {})
    inputs = steps.freeze_step(root, s_max=4, fetch=fetch, sleep=lambda _s: None)
    eb = next(f for f in inputs["files"] if f["name"] == "tess_eb.tsv")
    assert eb["in_git"] is False and eb["url"] == pilot.TESS_EB_URL
    assert eb["sha256"] == hashlib.sha256(STATIC_EB).hexdigest()
    edition = eb["static_edition"]
    assert edition["obtained"] == "2026-10-18T00:56:26" and edition["redistributed"] is False
    assert edition["path"] == "eb/static.tsv" and "retrieval.json" in edition["same_as"]
    published = root / steps.STEP_DIR / "inputs"
    assert not (published / "tess_eb.tsv").exists() and (published / "toi.csv").is_file()


def test_the_static_edition_is_the_v02_snapshot_content():
    v02 = json.loads((ROOT / "calibration/v0.2/eb_snapshot/retrieval.json").read_text("utf-8"))
    tess_eb = next(r for r in v02 if r["catalog_name"] == "TESS-EB")
    assert pilot.TESS_EB_STATIC["content_sha256"] == tess_eb["content_sha256"]
    assert pilot.TESS_EB_STATIC["content_rule"] == tess_eb["content_rule"]
    assert pilot.TESS_EB_STATIC["source_url"] == tess_eb["url"]
