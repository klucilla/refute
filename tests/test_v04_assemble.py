"""The attempt assembled from an earlier attempt's files (pilot.assemble, steps.assemble_step;
the maintainer's decision of 2026-10-30). Synthetic files only, no network."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import pytest

from refute.packs.tess.discover import pilot
from refute.packs.tess.discover import selection as sel
from test_v04_selection import LISTS, STATIC_EB, _static_eb

GAIA = b"source_id,ra,dec,frequency\n1,0,0,1\n"
SPEC = {
    **{k: v for k, v in pilot.ASSEMBLY.items() if k != "frame"},
    "source": "attempt-04",
    "s_max": 4,
}
CODE = {"commit": "0" * 40, "clean_paths": ["src"], "sha256": {}}
APPROVAL = "https://github.com/klucilla/refute/issues/177#issuecomment-1"
PAGE = "".join(f'<a href="2m/all_targets_S{s:03d}_v1.csv">c</a>' for s in (1, 2, 3, 4))


def _source(root: Path) -> Path:
    """A source attempt like attempt 4: its files and a reconstructed log (names, sizes,
    SHA-256 and write times, no URL)."""
    source = root / ".cache/v04/inputs-attempts/attempt-04"
    files = {
        "target_lists.html": PAGE.encode(),
        **{f"lists/all_targets_S{s:03d}_v1.csv": LISTS[s].encode() for s in (1, 2, 3, 4)},
        "frame.csv": sel.frame_csv(sel.build_frame(LISTS)),
        "toi.csv": b"TIC ID\n1\n",
        "ctoi.csv": b"TIC ID\n2\n",
        "pscomppars.csv": b"tic_id\n3\n",
    }
    log = [{"event": "reconstructed", "note": "from the files on disk", "utc": "T9"}]
    for i, (name, data) in enumerate(files.items()):
        (source / name).parent.mkdir(parents=True, exist_ok=True)
        (source / name).write_bytes(data)
        log.append(
            {
                "event": "file",
                "name": name,
                "bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
                "written_utc": f"2026-10-29T21:2{i % 10}:00Z",
            }
        )
    (source / "attempt.jsonl").write_text("".join(json.dumps(e) + "\n" for e in log))
    return source


def _fetch(url: str) -> bytes:
    if url == pilot.GAIA_EB_URL:
        return GAIA
    raise AssertionError(f"the assembly downloads only the Gaia asset, not {url}")


@pytest.fixture
def patched(monkeypatch):
    monkeypatch.setattr(pilot, "GAIA_EB_SHA256", hashlib.sha256(GAIA).hexdigest())
    monkeypatch.setattr(pilot, "GAIA_EB_ROWS", 1)


def _assemble(root: Path, source: Path, **kwargs):
    return pilot.assemble(
        root / "attempt-06",
        source,
        APPROVAL,
        CODE,
        fetch=_fetch,
        now=lambda: "2026-10-30T12:00:00Z",
        sector_count=kwargs.pop("sector_count", lambda _s: 1),
        cadence_count=kwargs.pop("cadence_count", lambda s: 10 * s),
        sleep=lambda _s: None,
        assembly=kwargs.pop("assembly", SPEC),
        **_eb(root),
        **kwargs,
    )


def _eb(root: Path) -> dict:
    return {"tess_eb_path": root / "eb" / "static.tsv", "tess_eb": _static_eb(root)}


def _events(folder: Path) -> list[dict]:
    return [json.loads(line) for line in (folder / "attempt.jsonl").read_text().splitlines()]


def _snapshot(folder: Path) -> dict[str, tuple[bytes, int]]:
    return {
        p.relative_to(folder).as_posix(): (p.read_bytes(), os.stat(p).st_mtime_ns)
        for p in folder.rglob("*")
        if p.is_file()
    }


def test_an_assembled_attempt_copies_checks_and_records_the_real_dates(tmp_path, patched):
    source = _source(tmp_path)
    before = _snapshot(source)
    inputs = _assemble(tmp_path, source)
    assert _snapshot(source) == before  # copied, never moved or changed
    log = {e["name"]: e for e in _events(source) if e["event"] == "file"}
    by_name = {f["name"]: f for f in inputs["files"]}
    toi = by_name["toi.csv"]
    assert toi["url"] == pilot.TOI_URL and toi["retrieved_utc"] == log["toi.csv"]["written_utc"]
    assert toi["copied_from"] == "attempt-04" and toi["copied_utc"] == "2026-10-30T12:00:00Z"
    assert (
        toi["retrieved_utc_basis"].startswith("estimate")
        and toi["sha256"] == log["toi.csv"]["sha256"]
    )
    lst = by_name["lists/all_targets_S002_v1.csv"]
    assert lst["url"].endswith("/2m/all_targets_S002_v1.csv") and "page" in lst["url_basis"]
    frame = by_name["frame.csv"]  # derived again, never copied
    assert frame["url"] == pilot.FRAME_DERIVATION and "copied_from" not in frame
    assert frame["same_as_source_frame"] is True and frame["stars"] == inputs["frame_stars"]
    assert len(frame["derived_from"]) == 4
    assert inputs["s_max"] == 4 and [q["sector"] for q in inputs["s_max_record"]["queries"]] == [4]
    assert "attempt-04" in inputs["s_max_record"]["highest_listed_from"]
    assert inputs["s_max_record"]["exptime_range_s"] == pilot.SPOC_120S_EXPTIME
    assert inputs["s_max_record"]["spoc_20s_light_curves"] == {"4": 40}  # recorded, not used
    assert inputs["assembled_from"]["supersedes"]["attempt"] == "attempt-06"
    source_record = inputs["assembled_from"]
    assert (
        source_record["log_sha256"]
        == hashlib.sha256((source / "attempt.jsonl").read_bytes()).hexdigest()
    )
    assert source_record["log_reconstructed_utc"] == "T9" and source_record["files"] == 9
    assert inputs["approval"] == APPROVAL and inputs["code"] == CODE
    assert inputs["seed_state"]["r_sel"] == "not yet determined for this protocol"
    assert by_name["tess_eb.tsv"]["sha256"] == hashlib.sha256(STATIC_EB).hexdigest()
    assert by_name["gaia_dr3_eb.csv"]["rows"] == 1
    events = _events(tmp_path / "attempt-06")
    assert events[0]["mode"] == "assembled" and events[-1]["event"] == "complete"


@pytest.mark.parametrize("name", ["ctoi.csv", "frame.csv"])  # the old frame is checked too
def test_a_source_file_that_differs_from_its_log_stops_the_assembly(tmp_path, patched, name):
    source = _source(tmp_path)
    (source / name).write_bytes(b"TIC ID\n9\n")
    with pytest.raises(sel.SelectionError, match=f"{name} differs"):
        _assemble(tmp_path, source)
    events = _events(tmp_path / "attempt-06")
    assert events[-1]["event"] == "failure" and events[-1]["step"] == "source inventory"
    assert [e for e in events if e["event"] == "failure"] == events[-1:]  # logged once
    assert not [e for e in events if e["event"] == "file" and e["name"] != "tess_eb.tsv"]
    assert not (tmp_path / "attempt-06" / "inputs.json").exists()


def _rewrite_log(source: Path, change) -> None:
    events = [json.loads(line) for line in (source / "attempt.jsonl").read_text().splitlines()]
    (source / "attempt.jsonl").write_text("".join(json.dumps(e) + "\n" for e in change(events)))


def test_a_required_file_or_field_missing_from_the_source_stops_the_assembly(tmp_path, patched):
    source = _source(tmp_path)
    (source / "frame.csv").unlink()
    _rewrite_log(source, lambda ev: [e for e in ev if e.get("name") != "frame.csv"])
    with pytest.raises(sel.SelectionError, match="lacks required files: \\['frame.csv'\\]"):
        _assemble(tmp_path, source)
    other = _source(tmp_path / "second")
    _rewrite_log(
        other,
        lambda ev: [{k: v for k, v in e.items() if k != "written_utc"} for e in ev],
    )
    with pytest.raises(sel.SelectionError, match="no write time"):
        _assemble(tmp_path / "second", other)


def test_any_later_error_is_logged_once_as_the_terminal_failure(tmp_path, patched, monkeypatch):
    source = _source(tmp_path)

    def broken(_lists):
        raise sel.SelectionError("two different lists for a sector")

    monkeypatch.setattr(pilot.sel, "build_frame", broken)
    with pytest.raises(sel.SelectionError, match="two different lists"):
        _assemble(tmp_path, source)
    failures = [e for e in _events(tmp_path / "attempt-06") if e["event"] == "failure"]
    assert len(failures) == 1 and failures[0]["step"] == "assemble"


def test_a_page_without_the_list_of_a_sector_stops_the_assembly(tmp_path, patched):
    source = _source(tmp_path)
    page = PAGE.replace("S002", "S009").encode()  # sector 2 has no list; sector 9 is higher
    (source / "target_lists.html").write_bytes(page)
    _rewrite_log(
        source,
        lambda ev: [
            {**e, "bytes": len(page), "sha256": hashlib.sha256(page).hexdigest()}
            if e.get("name") == "target_lists.html"
            else e
            for e in ev
        ],
    )
    with pytest.raises(sel.SelectionError):
        _assemble(tmp_path, source, assembly={**SPEC, "s_max": 9})
    failures = [e for e in _events(tmp_path / "attempt-06") if e["event"] == "failure"]
    assert len(failures) == 1


@pytest.mark.parametrize("name", ["../toi.csv", "/toi.csv", "lists\\x.csv", "C:x", "lists//x"])
def test_an_unsafe_name_in_the_source_log_stops_the_assembly(tmp_path, patched, name):
    source = _source(tmp_path)
    with open(source / "attempt.jsonl", "a") as handle:
        handle.write(json.dumps({"event": "file", "name": name, "bytes": 0, "sha256": ""}) + "\n")
    with pytest.raises(sel.SelectionError, match="unsafe path"):
        _assemble(tmp_path, source)
    assert _events(tmp_path / "attempt-06")[-1]["step"] == "source inventory"


def test_a_file_missing_from_the_log_or_named_twice_stops_the_assembly(tmp_path, patched):
    source = _source(tmp_path)
    (source / "lists" / "all_targets_S005_v1.csv").write_text("extra")
    with pytest.raises(sel.SelectionError, match="differs from its log"):
        _assemble(tmp_path, source)
    other = _source(tmp_path / "second")
    lines = (other / "attempt.jsonl").read_text().splitlines()
    (other / "attempt.jsonl").write_text("\n".join([*lines, lines[-1]]) + "\n")
    with pytest.raises(sel.SelectionError, match="twice"):
        _assemble(tmp_path / "second", other)


def test_a_different_s_max_from_mast_stops_the_assembly(tmp_path, patched):
    source = _source(tmp_path)
    with pytest.raises(sel.SelectionError, match="S_max 4, not the source's 3"):
        _assemble(tmp_path, source, assembly={**SPEC, "s_max": 3})
    events = _events(tmp_path / "attempt-06")
    assert [e["event"] for e in events][-2:] == ["s_max", "failure"]
    files = [e["name"] for e in events if e["event"] == "file"]
    assert files == ["target_lists.html"]  # no list is copied before S_max is settled


def test_a_mast_failure_is_logged_before_it_stops_the_assembly(tmp_path, patched):
    source = _source(tmp_path)

    def broken(sector):
        if sector == 4:
            return 0  # answered: no light curve yet
        raise TimeoutError("MAST timed out")

    with pytest.raises(sel.SelectionError, match="MAST timed out"):
        _assemble(tmp_path, source, sector_count=broken)
    events = _events(tmp_path / "attempt-06")
    mast = [e for e in events if e["event"] == "mast"]
    assert mast[0]["sector"] == 4 and mast[0]["spoc_120s_light_curves"] == 0  # kept
    assert mast[1]["sector"] == 3 and "MAST timed out" in mast[1]["error"]
    assert events[-1]["step"] == "s_max"


def test_the_assemble_step_needs_an_issue_comment_and_publishes_like_the_freeze(
    tmp_path, patched, monkeypatch
):
    from refute.packs.tess.discover import steps

    root = tmp_path / "root"
    _source(root)
    monkeypatch.setattr(pilot, "ASSEMBLY", SPEC)
    monkeypatch.setattr(pilot, "TESS_EB_STATIC", _static_eb(root))
    monkeypatch.setattr(steps, "exclusion_preview", lambda _root, _cache: {})
    for bad in (
        "https://github.com/klucilla/refute/issues/177",
        "https://github.com/klucilla/refute/issues/177#issuecomment-",
        "https://github.com/klucilla/refute/issues/x#issuecomment-1",
        "https://github.com/other/refute/issues/177#issuecomment-1",
        APPROVAL + "?x",
    ):
        with pytest.raises(sel.SelectionError, match="issue comment"):
            steps.assemble_step(root, bad, code=CODE)
    inputs = steps.assemble_step(
        root,
        APPROVAL,
        code=CODE,
        fetch=_fetch,
        sector_count=lambda _s: 1,
        cadence_count=lambda _s: 0,
        sleep=lambda _s: None,
    )
    assert inputs["attempt"] == "attempt-05"  # the next attempt folder, never the source's
    published = root / steps.STEP_DIR
    assert json.loads((published / "inputs.json").read_text())["approval"] == APPROVAL
    assert (published / "inputs" / "toi.csv").is_file()
    assert not (published / "inputs" / "tess_eb.tsv").exists()
    with pytest.raises(sel.SelectionError, match="frozen once"):
        steps.assemble_step(root, APPROVAL, code=CODE)


def test_the_code_identity_refuses_uncommitted_code(tmp_path):
    from refute.packs.tess.discover import steps

    class Done:
        def __init__(self, out):
            self.stdout = out

    def run(argv, **_kwargs):
        return Done(" M src/refute/x.py\n" if argv[1] == "status" else "abc\n")

    with pytest.raises(sel.SelectionError, match="commit it"):
        steps.code_identity(tmp_path, run=run)


def test_a_failed_cadence_check_stops_the_assembly(tmp_path, patched):
    source = _source(tmp_path)

    def broken(_sector):
        raise TimeoutError("MAST timed out")

    with pytest.raises(sel.SelectionError, match="MAST timed out"):
        _assemble(tmp_path, source, cadence_count=broken)
    assert _events(tmp_path / "attempt-06")[-1]["step"] == "cadence check"


def test_the_supersession_of_attempt_6_keeps_its_counts_as_history():
    old = pilot.ASSEMBLY["supersedes"]
    assert old["recorded_counts"]["107"] == 15160 and "InputWarning" in old["defect"]
    assert old["publication"].startswith(".cache/v04/inputs-attempts/attempt-06/")


def test_a_derived_frame_other_than_the_expected_stops_the_assembly(tmp_path, patched):
    source = _source(tmp_path)
    with pytest.raises(sel.SelectionError, match="not the expected one"):
        _assemble(tmp_path, source, assembly={**SPEC, "frame": {"sha256": "0" * 64, "stars": 3}})
    events = _events(tmp_path / "attempt-06")
    assert events[-1]["step"] == "frame"
    assert "frame.csv" not in [e.get("name") for e in events if e["event"] == "file"]
    assert not (tmp_path / "attempt-06" / "inputs.json").exists()


def test_the_expected_frame_is_attempt_4s():
    assert pilot.ASSEMBLY["frame"]["stars"] == 175739
    assert pilot.ASSEMBLY["frame"]["sha256"].startswith("58504462")
