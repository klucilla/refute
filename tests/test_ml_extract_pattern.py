"""An extraction file in a folder named by the run (docs/validation/v0.3/
wp3-extraction-pattern-acceptance.md, W3.11a), offline."""

from __future__ import annotations

import os

import pytest

from refute.packs.ml import extract as ex
from refute.packs.ml import integration as ig
from refute.packs.ml.schema import Extraction, Predictions

PATTERN = "out/results/exp/*/models/stats.json"


def write(root, folder: str, value: str = "-5.35", name: str = "stats.json"):
    path = root / "out" / "results" / "exp" / folder / "models" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('{"elbo": ' + value + "}", encoding="utf-8")
    return path


def selector(file: str = PATTERN) -> dict:
    return {"from": "file", "file": file, "json_path": "$.elbo", "unit": "native"}


def test_the_one_folder_the_run_created_is_read_and_its_path_recorded(tmp_path):
    write(tmp_path, "2026_10_18_14-00-00")
    got = ex.extract(selector(), tmp_path, "", None)
    assert got.value == ex.Extracted("-5.35", got.value, got.source).value
    assert got.source == "file:out/results/exp/2026_10_18_14-00-00/models/stats.json"


def test_seed_and_wildcard_in_one_path(tmp_path):
    path = tmp_path / "out" / "s7" / "run-a" / "stats.json"
    path.parent.mkdir(parents=True)
    path.write_text('{"elbo": 1.5}', encoding="utf-8")
    got = ex.extract(selector("out/s{seed}/*/stats.json"), tmp_path, "", 7)
    assert got.token == "1.5"


def test_a_folder_without_the_whole_path_is_not_a_match(tmp_path):
    write(tmp_path, "kept")
    (tmp_path / "out" / "results" / "exp" / "empty" / "models").mkdir(parents=True)
    assert ex.extract(selector(), tmp_path, "", None).token == "-5.35"


@pytest.mark.parametrize("second", ["-5.35", "-9.0", "not json", None])
def test_two_matches_never_give_a_value_whatever_they_hold(tmp_path, second):
    write(tmp_path, "a")
    if second is None:  # a candidate that cannot be read as a file
        (tmp_path / "out" / "results" / "exp" / "b" / "models" / "stats.json").mkdir(parents=True)
    else:
        write(tmp_path, "b", second)
    with pytest.raises(ex.ExtractionError, match="2 paths match"):
        ex.extract(selector(), tmp_path, "", None)


def test_no_folder_gives_no_value(tmp_path):
    with pytest.raises(ex.ExtractionError, match="0 paths match"):
        ex.extract(selector(), tmp_path, "", None)


def test_an_output_present_before_the_run_is_seen(tmp_path):
    assert not ex.output_present(tmp_path, PATTERN)
    write(tmp_path, "old")
    assert ex.output_present(tmp_path, PATTERN)
    assert ex.output_present(tmp_path, "out/results/exp/old/models/stats.json")


def test_a_folder_in_place_of_the_file_is_not_read(tmp_path):
    (tmp_path / "out" / "results" / "exp" / "a" / "models" / "stats.json").mkdir(parents=True)
    with pytest.raises(ex.ExtractionError, match="regular file"):
        ex.extract(selector(), tmp_path, "", None)


def test_a_file_with_a_second_hard_link_is_not_read(tmp_path):
    path = write(tmp_path, "a")
    try:
        os.link(path, tmp_path / "elsewhere.json")
    except OSError:
        pytest.skip("hard links cannot be created here")
    with pytest.raises(ex.ExtractionError, match="single link"):
        ex.extract(selector(), tmp_path, "", None)
    # the same rule for a fixed path
    with pytest.raises(ex.ExtractionError, match="single link"):
        ex.extract(selector("out/results/exp/a/models/stats.json"), tmp_path, "", None)


@pytest.mark.parametrize("where", ["file", "folder_after", "folder_before"])
def test_a_symbolic_link_on_the_path_is_not_followed(tmp_path, where):
    real = write(tmp_path, "real")
    base = tmp_path / "out" / "results" / "exp"
    try:
        if where == "file":
            (base / "a" / "models").mkdir(parents=True)
            (base / "a" / "models" / "stats.json").symlink_to(real)
            (base / "real" / "models" / "stats.json").rename(tmp_path / "moved.json")
            (base / "a" / "models" / "stats.json").unlink()
            (base / "a" / "models" / "stats.json").symlink_to(tmp_path / "moved.json")
        elif where == "folder_after":
            (base / "a").mkdir()
            (base / "a" / "models").symlink_to(real.parent, target_is_directory=True)
            (real).rename(tmp_path / "moved.json")
            (base / "real" / "models" / "stats.json").write_text("{}", encoding="utf-8")
            (base / "real").rename(tmp_path / "gone")
        else:
            (tmp_path / "elsewhere" / "results" / "exp" / "a" / "models").mkdir(parents=True)
            (tmp_path / "elsewhere" / "results" / "exp" / "a" / "models" / "stats.json").write_text(
                '{"elbo": 1}', encoding="utf-8"
            )
            (base / "real").rename(tmp_path / "gone")
            os.rmdir(base)
            os.rmdir(tmp_path / "out" / "results")
            (tmp_path / "out" / "results").symlink_to(
                tmp_path / "elsewhere" / "results", target_is_directory=True
            )
    except OSError:
        pytest.skip("symbolic links cannot be created here")
    with pytest.raises(ex.ExtractionError):
        ex.extract(selector(), tmp_path, "", None)


@pytest.mark.parametrize(
    "file",
    [
        "out/*/*/stats.json",
        "out/**/stats.json",
        "out/a*/stats.json",
        "out/a?/stats.json",
        "out/[ab]/stats.json",
    ],
)
def test_other_patterns_are_refused_at_validation(file):
    with pytest.raises(ValueError):
        Extraction.model_validate(selector(file))
    with pytest.raises(ex.ExtractionError):
        ex.output_present(__import__("pathlib").Path("."), file)


def test_a_predictions_file_holds_no_pattern():
    with pytest.raises(ValueError, match="no pattern"):
        Predictions.model_validate(
            {"file": "preds/*/p.npy", "format": "npy", "fields": {"y_true": "t", "y_pred": "p"}}
        )


def test_a_predictions_path_that_becomes_a_pattern_is_refused(tmp_path):
    """A method named '*' put into {method} must not turn the predictions file into a
    pattern (Codex review): the final path is checked, after its placeholders."""
    (tmp_path / "preds").mkdir()
    (tmp_path / "preds" / "a.csv").write_bytes(b"t,p\n1,1\n")
    with pytest.raises(ex.ExtractionError, match="no pattern"):
        ex.read_output_bytes(tmp_path, "preds/*.csv", None, pattern=False)
    raw, where, _ = ex.read_output_bytes(tmp_path, "preds/a.csv", None, pattern=False)
    assert raw == b"t,p\n1,1\n" and where == "file:preds/a.csv"


def test_one_read_per_file_in_a_session(tmp_path, monkeypatch):
    """Every reader of one file of one run shares one resolution and one read."""
    write(tmp_path, "a")
    calls = []
    real = ex._read_bytes  # noqa: SLF001

    def counting(*args):
        calls.append(args)
        return real(*args)

    monkeypatch.setattr(ex, "_read_bytes", counting)
    with ex.read_session():
        first = ex.extract(selector(), tmp_path, "", None)
        write(tmp_path, "b")  # a second match afterwards changes nothing in the session
        second = ex.extract(selector(), tmp_path, "", None)
    assert first == second and len(calls) == 1
    with pytest.raises(ex.ExtractionError, match="2 paths match"):  # outside the session
        ex.extract(selector(), tmp_path, "", None)


def test_a_failing_read_is_an_extraction_error(tmp_path, monkeypatch):
    write(tmp_path, "a")

    def broken(fd):
        raise OSError(5, "input/output error")

    monkeypatch.setattr(ex.os, "fstat", broken)
    with pytest.raises(ex.ExtractionError, match="cannot read"):
        ex.extract(selector(), tmp_path, "", None)


def test_a_count_and_its_evidence_come_from_the_one_resolved_file(tmp_path):
    path = tmp_path / "out" / "results" / "exp" / "r1" / "models" / "count.json"
    path.parent.mkdir(parents=True)
    path.write_text('{"n": 4000}', encoding="utf-8")
    count_selector = {
        "from": "file",
        "file": "out/results/exp/*/models/count.json",
        "json_path": "$.n",
    }
    count, piece = ig._count(count_selector, tmp_path, "", None)  # noqa: SLF001
    assert count == 4000
    assert piece.source == ig._file_source(path)  # noqa: SLF001
    write(tmp_path, "r2", name="count.json")  # a second match: no count at all
    with pytest.raises(ex.ExtractionError, match="2 paths match"):
        ig._count(count_selector, tmp_path, "", None)  # noqa: SLF001
