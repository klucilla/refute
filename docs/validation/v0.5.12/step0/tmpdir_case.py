"""A minimal pytest case for the temporary-folder fixture (v0.5.12, step 0; #218 comment
7190662570, item 2 (ii)). Run only by ``tmpdir_fixture.py``, by explicit path; it is outside
``tests/`` and outside the suite."""


def test_tmp_path_is_usable(tmp_path):
    p = tmp_path / "probe.txt"
    p.write_text("v0.5.12", encoding="utf-8")
    assert p.read_text(encoding="utf-8") == "v0.5.12"
    sub = tmp_path / "sub"
    sub.mkdir()
    assert sub.is_dir()
