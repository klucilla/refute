"""v0.5 WP8: reproducibility (docs/plans/v0.5-acceptance.md, cases 8.3 and 8.4; #189, #195,
#196). Cases 8.1 and 8.2 (the instructions and the empty-checkout test) are in
test_v05_reproduce.py."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys

import pytest

from refute.packs.tess.discover.pilot import TESS_EB_STATIC
from refute.packs.tess.discover.promotion_v05 import verify_promotion_records
from refute.packs.tess.frozen import (
    TESS_EB_NAME,
    frozen_tess_eb_path,
    place_frozen_tess_eb,
)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# --- 8.4: the frozen TESS-EB folder --------------------------------------------------------


def test_8_4_the_edition_is_copied_to_its_frozen_folder(tmp_path):
    source = tmp_path / "src" / TESS_EB_NAME
    source.parent.mkdir()
    source.write_bytes(b"TIC\tPeriod\n1\t2.5\n")
    sha = _sha(source.read_bytes())
    root = tmp_path / "project"
    dest = place_frozen_tess_eb(source, root, sha)
    assert dest == frozen_tess_eb_path(root, sha)
    assert dest.relative_to(root).as_posix() == f".cache/frozen/tess-eb/{sha}/{TESS_EB_NAME}"
    assert dest.read_bytes() == source.read_bytes() and source.exists()  # copied, not moved
    assert place_frozen_tess_eb(source, root, sha) == dest  # idempotent


def test_8_4_a_wrong_source_or_other_bytes_are_refused(tmp_path):
    source = tmp_path / TESS_EB_NAME
    source.write_bytes(b"one")
    with pytest.raises(ValueError, match="SHA-256"):
        place_frozen_tess_eb(source, tmp_path / "p", "0" * 64)
    sha = _sha(b"one")
    dest = frozen_tess_eb_path(tmp_path / "p", sha)
    dest.parent.mkdir(parents=True)
    dest.write_bytes(b"other")
    with pytest.raises(ValueError, match="never overwritten"):
        place_frozen_tess_eb(source, tmp_path / "p", sha)
    with pytest.raises(ValueError, match="SHA-256"):
        frozen_tess_eb_path(tmp_path, "XYZ")


def test_8_4_a_link_on_the_way_is_refused(tmp_path):
    source = tmp_path / TESS_EB_NAME
    source.write_bytes(b"x")
    sha = _sha(b"x")
    root = tmp_path / "p"
    outside = tmp_path / "outside"
    outside.mkdir()
    (root / ".cache").mkdir(parents=True)
    link = root / ".cache" / "frozen"
    done = subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(link), str(outside)]
        if sys.platform == "win32"
        else ["ln", "-s", str(outside), str(link)],
        capture_output=True,
    )
    if done.returncode != 0:
        pytest.skip("this machine cannot create a directory link")
    try:
        with pytest.raises(ValueError, match="link or a junction"):
            place_frozen_tess_eb(source, root, sha)
        assert not any(outside.iterdir())
    finally:
        os.rmdir(link) if sys.platform == "win32" else link.unlink()  # noqa: B018


def test_8_4_an_existing_temporary_file_is_never_written_through(tmp_path):
    # Codex's end-of-round review of round 3: the temporary file is created exclusively
    source = tmp_path / TESS_EB_NAME
    source.write_bytes(b"x")
    sha = _sha(b"x")
    root = tmp_path / "p"
    dest = frozen_tess_eb_path(root, sha)
    dest.parent.mkdir(parents=True)
    planted = dest.with_name(f"{dest.name}.{os.getpid()}.part")
    planted.write_bytes(b"planted")
    with pytest.raises(FileExistsError):
        place_frozen_tess_eb(source, root, sha)
    assert planted.read_bytes() == b"planted" and not dest.exists()


def test_8_4_a_destination_that_appears_meanwhile_is_not_replaced(tmp_path, monkeypatch):
    from refute.packs.tess import frozen

    source = tmp_path / TESS_EB_NAME
    source.write_bytes(b"x")
    sha = _sha(b"x")
    root = tmp_path / "p"
    dest = frozen_tess_eb_path(root, sha)
    real = frozen.make_parents

    def racing(directory, base):
        real(directory, base)
        dest.write_bytes(b"other")  # another process wins the race

    monkeypatch.setattr(frozen, "make_parents", racing)
    with pytest.raises(ValueError, match="never overwritten"):
        place_frozen_tess_eb(source, root, sha)
    assert dest.read_bytes() == b"other"
    assert [p.name for p in dest.parent.iterdir()] == [dest.name]  # no temporary left


def test_8_x_install_validates_before_creating_anything(tmp_path):
    from refute.core.reproduce import InputError, InputSpec, dest_problem, install

    assert "dot" in dest_problem(".cache/frozen/edition./file.tsv")
    assert "dot" in dest_problem(".cache/frozen/edition/file.")
    bad = InputSpec("x", _sha(b"x"), "https://example.org/x", "outside/../x")
    with pytest.raises(InputError):
        install(b"x", bad, tmp_path)
    assert not any(tmp_path.iterdir())
    good = InputSpec("x", _sha(b"x"), "https://example.org/x", ".cache/frozen/a/x.tsv")
    path = install(b"x", good, tmp_path)
    assert path.read_bytes() == b"x"
    with pytest.raises(FileExistsError):
        install(b"x", good, tmp_path)  # never clobbered


def test_8_4_a_v05_claim_declares_the_edition_at_its_frozen_destination():
    from refute.core.reproduce import InputSpec, dest_problem, specs_problems
    from refute.packs.tess.frozen import tess_eb_input

    sha = TESS_EB_STATIC["sha256"]
    item = tess_eb_input(sha, TESS_EB_STATIC["source_url"])
    assert item["dest"] == f".cache/frozen/tess-eb/{sha}/{TESS_EB_NAME}"
    assert dest_problem(item["dest"]) is None
    assert specs_problems([InputSpec(**item)]) == []


def test_8_4_the_v04_records_are_unchanged():
    assert (
        TESS_EB_STATIC["path"] == ".cache/wt-v021/.cache/v021/tess-eb/vizier/tess_ebs_prsa2022.tsv"
    )


# --- 8.3: a promotion checked against the committed records alone ----------------------------


def _records():
    entries = [
        {"target_key": "TIC-1", "eligible": True},
        {"target_key": "TIC-2", "eligible": False},
    ]
    entries_bytes = json.dumps(entries).encode()
    seals_bytes = json.dumps({"core_sha256": {"TIC-1": "a" * 64, "TIC-2": "b" * 64}}).encode()
    record = {
        "entries": entries,
        "eligible": ["TIC-1"],
        "stage1_records": {
            "entries_sha256": _sha(entries_bytes),
            "seals_sha256": _sha(seals_bytes),
        },
    }
    return record, entries_bytes, seals_bytes


RUN_SET = ["TIC-1", "TIC-2"]


def test_8_3_the_promotion_verifies_without_the_stage1_dossiers():
    record, entries, seals = _records()
    assert verify_promotion_records(record, entries, seals, RUN_SET) == []


def test_8_3_a_tampered_entry_or_seal_fails():
    record, entries, seals = _records()
    tampered = entries.replace(b'"eligible": false', b'"eligible": true')
    assert "entries.json" in verify_promotion_records(record, tampered, seals, RUN_SET)[0]
    tampered_seals = seals.replace(b"a" * 64, b"c" * 64)
    assert "seals.json" in verify_promotion_records(record, entries, tampered_seals, RUN_SET)[0]
    record["eligible"] = ["TIC-1", "TIC-2"]
    assert verify_promotion_records(record, entries, seals, RUN_SET) == [
        "the eligible list does not follow from the committed entries"
    ]


def test_8_3_a_missing_input_is_named():
    record, entries, _ = _records()
    assert verify_promotion_records(record, entries, None, RUN_SET) == ["missing input: seals.json"]
    assert verify_promotion_records(record, None, None, RUN_SET) == [
        "missing input: entries.json",
        "missing input: seals.json",
    ]
