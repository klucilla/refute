"""The input tool of the v0.4 reproduction (calibration/v0.4/reproduce_inputs.py; #189, the
maintainer's Option 1 of 2026-11-01): the TESS-EB header rebuild restores only metadata and never
lets a changed table pass, and a recorded zip is refused when tampered, incomplete, padded,
duplicated or unsafe. Offline, synthetic data only."""

from __future__ import annotations

import hashlib
import importlib.util
import io
import sys
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "reproduce_inputs", ROOT / "calibration" / "v0.4" / "reproduce_inputs.py"
)
tool = importlib.util.module_from_spec(spec)
sys.modules["reproduce_inputs"] = tool
spec.loader.exec_module(tool)

URL = "https://vizier.cds.unistra.fr/viz-bin/asu-tsv?-source=J/X&-out=TIC&-out.max=unlimited"
FROZEN_DATE = "2026-10-18T00:56:26"


def vizier(host: str, date: str, rows: list[str]) -> bytes:
    url = URL.replace("vizier.cds.unistra.fr", host)
    lines = [
        "#",
        f"#   VizieR Astronomical Server {host}",
        f"#    Date: {date} [V7.6.1]",
        f"#INFO\trequest_date={date}\t  Query execution date",
        f"#INFO\trequest={url}\t  Full request URL",
        "",
        "#Column\tTIC\t(A10)\tTESS input catalog",
        "TIC\tPer",
        " \td",
        "----------\t-----------",
        *rows,
        "",
    ]
    return "\n".join(lines).encode("utf-8")


ROWS = ["0185259483\t  0.3105640", "0307990280\t  2.3159117"]
FROZEN = vizier("vizier.cds.unistra.fr", FROZEN_DATE, ROWS)


def record(frozen: bytes = FROZEN) -> dict:
    from refute.packs.tess.ebcatalog import content_sha256

    return {
        "url": URL,
        "sha256": hashlib.sha256(frozen).hexdigest(),
        "static_edition": {"obtained": FROZEN_DATE, "content_sha256": content_sha256(frozen)},
    }


def test_rebuild_from_a_mirror_gives_the_frozen_bytes():
    fresh = vizier("vizier.cfa.harvard.edu", "2026-11-01T16:01:52", ROWS)
    assert tool.rebuild_tess_eb(fresh, FROZEN_DATE, URL) == FROZEN
    data, how = tool.tess_eb(record(), download=lambda url: fresh)
    assert data == FROZEN and how["source"].startswith("https://vizier.cds.unistra.fr")


def test_a_changed_table_never_passes():
    changed = vizier("vizier.cds.unistra.fr", "2026-11-01T16:01:52", [ROWS[0], ROWS[1] + "1"])
    with pytest.raises(tool.InputError, match="no source"):
        tool.tess_eb(record(), download=lambda url: changed)


def test_a_changed_header_beyond_the_metadata_is_refused():
    other = FROZEN.replace(b"[V7.6.1]", b"[V7.7.0]")
    with pytest.raises(tool.InputError, match="no source"):
        tool.tess_eb(record(), download=lambda url: other)


def test_the_cds_failure_falls_to_the_mirror_and_is_recorded():
    fresh = vizier("vizier.cfa.harvard.edu", "2026-11-01T16:01:52", ROWS)

    def download(url):
        if "unistra" in url:
            raise OSError("unreachable")
        return fresh

    data, how = tool.tess_eb(record(), download=download)
    assert data == FROZEN and "cfa" in how["source"]
    assert how["failed_sources"][0]["error"].startswith("OSError")


def zip_bytes(members: list[tuple[str, bytes]]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for name, data in members:
            archive.writestr(name, data)
    return buffer.getvalue()


MEMBERS = [("funnel-s1/TIC-1/verdict.json", b"{}"), ("funnel-s1/TIC-2/verdict.json", b"[]")]
NAMES = {name for name, _ in MEMBERS}


def test_a_recorded_zip_is_read():
    data = zip_bytes(MEMBERS)
    members = tool.read_zip(data, hashlib.sha256(data).hexdigest(), NAMES)
    assert members == dict(MEMBERS)


@pytest.mark.parametrize(
    ("members", "match"),
    [
        (MEMBERS[:1], "differ from the record"),
        ([*MEMBERS, ("funnel-s1/TIC-3/verdict.json", b"{}")], "differ from the record"),
        ([*MEMBERS, ("../escape.json", b"{}")], "unsafe"),
        ([*MEMBERS, ("C:/abs.json", b"{}")], "unsafe"),
        ([*MEMBERS, ("funnel-s1/CON/x.json", b"{}")], "unsafe"),
        ([*MEMBERS, ("funnel-s1/a./x.json", b"{}")], "unsafe"),
        ([*MEMBERS, ("funnel-s1/", b"")], "directory"),
        ([MEMBERS[0], MEMBERS[0], MEMBERS[1]], "duplicate"),
        ([*MEMBERS, ("FUNNEL-S1/TIC-1/verdict.json", b"{}")], "duplicate"),
    ],
)
def test_a_bad_zip_is_refused(members, match):
    data = zip_bytes(members)
    with pytest.raises(tool.InputError, match=match):
        tool.read_zip(data, hashlib.sha256(data).hexdigest(), NAMES)


def test_a_tampered_zip_is_refused():
    data = zip_bytes(MEMBERS)
    expected = hashlib.sha256(data).hexdigest()
    with pytest.raises(tool.InputError, match="SHA-256"):
        tool.read_zip(zip_bytes([MEMBERS[0], (MEMBERS[1][0], b"[1]")]), expected, NAMES)


def test_written_zips_are_deterministic(tmp_path):
    files = {"b/x.json": b"1", "a/y.json": b"2"}
    first = tool.write_zip(tmp_path / "one.zip", files)
    second = tool.write_zip(tmp_path / "two.zip", dict(reversed(list(files.items()))))
    assert first == second
    with pytest.raises(FileExistsError):
        tool.write_zip(tmp_path / "one.zip", files)


def test_destinations_stay_in_the_clone_and_are_new(tmp_path, monkeypatch):
    monkeypatch.setattr(tool, "ROOT", tmp_path)
    for bad in ("../out", "/abs", "a/../../b", "C:/x"):
        with pytest.raises(tool.InputError):
            tool.inside(bad)
    target = tool.inside(".cache/v04/x.tsv")
    tool.write_new(target, b"1")
    with pytest.raises(tool.InputError, match="not a fresh clone"):
        tool.write_new(target, b"1")


def test_a_link_on_the_way_is_refused_before_writing(tmp_path, monkeypatch):
    clone, outside = tmp_path / "clone", tmp_path / "outside"
    clone.mkdir()
    outside.mkdir()
    link = clone / ".cache"
    try:
        if sys.platform == "win32":
            import _winapi

            _winapi.CreateJunction(str(outside), str(link))
        else:
            link.symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("this system cannot create a directory link")
    monkeypatch.setattr(tool, "ROOT", clone)
    with pytest.raises(tool.InputError):
        tool.write_new(clone / ".cache" / "v04" / "reproduce" / "prepare.json", b"{}")
    assert list(outside.iterdir()) == []


def test_instructions_write_every_command():
    text = tool.instructions("a" * 40, "ARCHIVE")
    assert "set -euo pipefail" in text
    assert text.count("uv run refute discover") == 5
    assert text.count("--promotion calibration/v0.4/runs/promotion.json") == 3
    assert text.count("uv run refute check-dossier") == 5
    assert "git checkout " + "a" * 40 in text
    assert "do not amend acceptance criterion 2" in text


def test_instructions_version_2_is_unchanged():
    # the text of REPRODUCE-2.md, before version 3 was added
    text = tool.instructions("a" * 40, "ARCHIVE")
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    assert digest == "298cf2fb02c99497463abda1dc7e37a3a85e4741883280647e978a58cbd063fc"


def test_instructions_version_3_changes_only_the_archive():
    def block(text: str) -> list[str]:
        return text.split("```bash\n")[1].split("```")[0].splitlines()

    archive = "https://example.org/records/1/files"
    v2 = tool.instructions("a" * 40, "ARCHIVE")
    v3 = tool.instructions("a" * 40, archive, version=3, doi="10.0/x.1")
    assert block(v3) == [line.replace("ARCHIVE", archive) for line in block(v2)]
    assert "(instructions version 3)" in v3
    assert "https://doi.org/10.0/x.1" in v3
    assert "private archive, so a third party cannot" not in v3
    assert "do not\namend acceptance criterion 2" in v3


@pytest.mark.parametrize(
    ("archive", "kwargs"),
    [
        ("https://example.org/files", {"version": 4}),
        ("https://example.org/files", {"version": 3}),
        ("K:/private", {"version": 3, "doi": "10.0/x.1"}),
    ],
)
def test_instructions_refuse_a_bad_version_or_archive(archive, kwargs):
    with pytest.raises(ValueError):
        tool.instructions("a" * 40, archive, **kwargs)
