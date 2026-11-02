"""The input tool of the v0.4 reproduction (calibration/v0.4/reproduce_inputs.py; #189, the
maintainer's Option 1 of 2026-11-01): the TESS-EB header rebuild restores only metadata and never
lets a changed table pass, and a recorded zip is refused when tampered, incomplete, padded,
duplicated or unsafe. Offline, synthetic data only."""

from __future__ import annotations

import hashlib
import importlib.util
import io
import sys
import urllib.error
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


def served(data: bytes):
    """A download that answers every URL with ``data``, without a redirect."""
    return lambda url: (data, url)


def test_the_servers_are_the_cds_then_the_maintainers_mirrors_in_order():
    assert tool.HOSTS == (
        "vizier.cds.unistra.fr",
        "vizier.cfa.harvard.edu",
        "vizier.idia.ac.za",
        "vizier.nao.ac.jp",
        "vizier.china-vo.org",
    )
    url = URL + "&-out.max=unlimited"
    assert tool.on_server(url, "http://vizier.nao.ac.jp") == url.replace(
        "https://vizier.cds.unistra.fr", "http://vizier.nao.ac.jp"
    )


@pytest.mark.parametrize("host", tool.HOSTS)
def test_rebuild_from_every_server_gives_the_frozen_bytes(host):
    fresh = vizier(host, "2026-11-01T16:01:52", ROWS)
    assert tool.rebuild_tess_eb(fresh, FROZEN_DATE, URL) == FROZEN


def test_the_first_server_that_matches_is_used_and_recorded():
    fresh = vizier("vizier.cfa.harvard.edu", "2026-11-01T16:01:52", ROWS)
    data, how = tool.tess_eb(record(), download=served(fresh))
    assert data == FROZEN and how["source"].startswith("https://vizier.cds.unistra.fr")
    assert how["server"] == "vizier.cds.unistra.fr" and how["failed_sources"] == []


def test_a_changed_table_never_passes():
    changed = vizier("vizier.cds.unistra.fr", "2026-11-01T16:01:52", [ROWS[0], ROWS[1] + "1"])
    with pytest.raises(tool.InputError, match="none of the 5 VizieR servers"):
        tool.tess_eb(record(), download=served(changed))


def test_a_changed_header_beyond_the_metadata_is_refused():
    other = FROZEN.replace(b"[V7.6.1]", b"[V7.7.0]")
    with pytest.raises(tool.InputError, match="none of the 5 VizieR servers"):
        tool.tess_eb(record(), download=served(other))


def test_cds_down_cfa_502_idia_ok_and_no_later_server_is_asked():
    fresh = vizier("vizier.idia.ac.za", "2026-11-02T17:41:18", ROWS)
    asked = []

    def download(url):
        asked.append(url)
        if "unistra" in url:
            raise OSError("unreachable")
        if "cfa" in url:
            raise urllib.error.HTTPError(url, 502, "Bad Gateway", None, None)
        return fresh, url

    data, how = tool.tess_eb(record(), download=download)
    assert data == FROZEN and how["server"] == "vizier.idia.ac.za"
    assert [e["error"].split(":")[0] for e in how["failed_sources"]] == ["OSError", "HTTPError"]
    assert len(asked) == 3


def test_a_server_with_different_bytes_is_refused_and_the_next_is_taken():
    reordered = vizier("vizier.cds.unistra.fr", "2026-11-02T19:19:32", ROWS[::-1])
    extra = vizier("vizier.cfa.harvard.edu", "2026-11-02T19:19:32", ROWS).replace(
        b"[V7.6.1]", b"[V7.7.0]"
    )
    good = vizier("vizier.idia.ac.za", "2026-11-02T19:19:32", ROWS)
    answers = {"unistra": reordered, "cfa": extra, "idia": good}

    def download(url):
        return next(v for k, v in answers.items() if k in url), url

    data, how = tool.tess_eb(record(), download=download)
    assert data == FROZEN and how["server"] == "vizier.idia.ac.za"
    first, second = how["failed_sources"]
    assert first["error"].endswith("content SHA-256 differs from the frozen edition")
    assert "content_sha256" in first and "rebuilt_sha256" not in first
    assert second["error"].endswith("raw SHA-256 differs after the header rebuild")
    assert second["rebuilt_sha256"] != record()["sha256"]


def test_invalid_bytes_and_a_redirect_outside_the_list_are_refused():
    good = vizier("vizier.nao.ac.jp", "2026-11-02T19:19:32", ROWS)

    def download(url):
        if "unistra" in url:
            return b"#\n#   VizieR Astronomical Server \xff\xfe\n" + FROZEN, url
        if "cfa" in url:
            return good, "https://elsewhere.example/viz-bin/asu-tsv"
        if "idia" in url:
            raise OSError("unreachable")
        return good, url

    data, how = tool.tess_eb(record(), download=download)
    assert data == FROZEN and how["server"] == "vizier.nao.ac.jp"
    errors = [e["error"] for e in how["failed_sources"]]
    assert "elsewhere.example" in errors[1] and "not in the server list" in errors[1]
    assert len(errors) == 3


def test_all_servers_down_gives_a_clear_error():
    def download(url):
        raise OSError("unreachable")

    with pytest.raises(tool.InputError) as caught:
        tool.tess_eb(record(), download=download)
    message = str(caught.value)
    assert message.startswith("TESS-EB: none of the 5 VizieR servers gave the frozen edition")
    assert record()["sha256"] in message
    assert all(host in message for host in tool.HOSTS)


class FakeResponse:
    def __init__(self, status: int, data: bytes, url: str):
        self.status, self.data, self.url = status, data, url

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self, size: int = -1) -> bytes:
        return self.data if size < 0 else self.data[:size]

    def geturl(self) -> str:
        return self.url


@pytest.mark.parametrize(
    ("status", "size", "match"),
    [(203, 10, "HTTP status 203"), (200, tool.TESS_EB_MAX_BYTES + 1, "larger than")],
)
def test_the_tess_eb_download_needs_status_200_and_a_bounded_size(monkeypatch, status, size, match):
    monkeypatch.setattr(tool.time, "sleep", lambda s: None)
    monkeypatch.setattr(
        tool.urllib.request,
        "urlopen",
        lambda request, timeout: FakeResponse(status, b"x" * size, request.full_url),
    )
    with pytest.raises(tool.InputError, match=match):
        tool.fetch_tess_eb("https://vizier.idia.ac.za/x")


def test_the_tess_eb_download_returns_the_final_url(monkeypatch):
    seen = {}

    def urlopen(request, timeout):
        seen["timeout"] = timeout
        return FakeResponse(200, b"table", "https://vizier.idia.ac.za/final")

    monkeypatch.setattr(tool.urllib.request, "urlopen", urlopen)
    assert tool.fetch_tess_eb("https://vizier.idia.ac.za/x") == (
        b"table",
        "https://vizier.idia.ac.za/final",
    )
    assert seen["timeout"] == tool.TESS_EB_TIMEOUT == 120.0


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


def test_instructions_version_3_is_unchanged():
    text = tool.instructions("a" * 40, "https://example.org/records/1/files", 3, "10.0/x.1")
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    assert digest == "7886fef814fcb2c6ecf92a8e91b87487d7eb62f3a1842327d54beddde2b650a4"


def test_instructions_version_4_checks_out_the_new_commit_and_diffs_it():
    def block(text: str) -> list[str]:
        return text.split("```bash\n")[1].split("```")[0].splitlines()

    archive = "https://example.org/records/1/files"
    v3 = tool.instructions("a" * 40, archive, version=3, doi="10.0/x.1")
    v4 = tool.instructions("b" * 40, archive, version=4, doi="10.0/x.1", reproduced="a" * 40)
    diff = "git diff --exit-code " + "a" * 40 + " " + "b" * 40 + " -- src/ pyproject.toml uv.lock"
    lines = block(v4)
    assert lines[4].startswith(diff)
    assert lines[:4] + lines[5:] == [line.replace("a" * 40, "b" * 40) for line in block(v3)]
    assert "(instructions version 4)" in v4
    assert "ran at `" + "a" * 40 + "`" in v4
    assert all(host in v4 for host in tool.HOSTS)


@pytest.mark.parametrize(
    ("archive", "kwargs"),
    [
        ("https://example.org/files", {"version": 5}),
        ("https://example.org/files", {"version": 3}),
        ("K:/private", {"version": 3, "doi": "10.0/x.1"}),
        ("https://example.org/files", {"version": 4, "doi": "10.0/x.1"}),
        ("https://example.org/files", {"version": 4, "doi": "10.0/x.1", "reproduced": "abc"}),
    ],
)
def test_instructions_refuse_a_bad_version_or_archive(archive, kwargs):
    with pytest.raises(ValueError):
        tool.instructions("a" * 40, archive, **kwargs)
