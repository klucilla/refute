"""The allowed patches written into a tree (docs/validation/v0.3/
wp3-allowed-patches-acceptance.md, sections 1 to 3): the anchor on the commit's tree, the
writing relative to open folders, the manifests, the copies and the verification. Linux
only (the applier runs on the VM); the hook refusal runs everywhere."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

from conftest import git
from refute.packs.ml import patches as pt
from refute.packs.ml import production as pd
from refute.packs.ml import repository

LINUX = pytest.mark.skipif(
    sys.platform == "win32" or os.open not in os.supports_dir_fd, reason="Linux, as on the VM"
)
SRC = b"".join(b"line %d\n" % i for i in range(1, 11))


def patch(path: str, old: bytes, new: bytes, line: int = 3) -> bytes:
    p = path.encode()
    return b"diff --git a/%s b/%s\n--- a/%s\n+++ b/%s\n@@ -%d +%d @@\n-%s\n+%s\n" % (
        p,
        p,
        p,
        p,
        line,
        line,
        old,
        new,
    )


def creation(path: str, body: bytes) -> bytes:
    p = path.encode()
    return (
        b"diff --git a/%s b/%s\nnew file mode 100644\n--- /dev/null\n+++ b/%s\n"
        b"@@ -0,0 +1 @@\n+%s\n" % (p, p, p, body)
    )


@pytest.fixture
def clone(git_repo: Path, tmp_path: Path) -> tuple[Path, str, dict]:
    (git_repo / "src").mkdir()
    (git_repo / "src" / "load.py").write_bytes(SRC)
    (git_repo / "requirements.txt").write_bytes(b"numpy==1.26.4\n")
    (git_repo / "run.sh").write_bytes(b"echo 1\n")
    (git_repo / "run.sh").chmod(0o755)
    git(git_repo, "add", "-A")
    git(git_repo, "commit", "-q", "-m", "c")
    commit = git(git_repo, "rev-parse", "HEAD").strip()
    dest = repository.clone(git_repo.as_uri(), tmp_path / "clone")
    repository.checkout(dest, commit)
    entries = pt.commit_entries(repository.ls_tree(dest, commit))
    return dest, commit, entries


@LINUX
def test_a_patch_and_a_creation_are_written_and_recorded(clone, tmp_path):
    src, _, entries = clone
    patches = [
        ("data.patch", patch("src/load.py", b"line 3", b"LINE 3")),
        ("deps.patch", creation("extra/deps.txt", b"torch==1.12.1")),
    ]
    record = pt.prepare(src, tmp_path / "patched", patches, ["data/d.csv"], entries)
    out = tmp_path / "patched"
    assert (out / "src" / "load.py").read_bytes() == SRC.replace(b"line 3\n", b"LINE 3\n")
    assert (out / "extra" / "deps.txt").read_bytes() == b"torch==1.12.1\n"
    assert (out / "run.sh").stat().st_mode & 0o100  # untouched, mode kept
    assert record["touched"]["extra/deps.txt"]["before"] is None
    assert [p["attachment"] for p in record["patches"]] == ["data.patch", "deps.patch"]
    assert not pt.verify(src, tmp_path / "again", patches, ["data/d.csv"], entries, record)


@LINUX
def test_the_clone_must_be_the_commits_tree(clone, tmp_path):
    src, _, entries = clone
    (src / "untracked.py").write_bytes(b"x\n")
    with pytest.raises(pt.PatchError, match="extra"):
        pt.prepare(src, tmp_path / "patched", [], [], entries)


@LINUX
def test_a_link_on_the_path_is_refused(clone, tmp_path):
    src, _, entries = clone
    patches = [("p", patch("src/load.py", b"line 3", b"x"))]
    dest = tmp_path / "patched"
    import shutil

    shutil.copytree(src, tmp_path / "copy", symlinks=True, ignore=shutil.ignore_patterns(".git"))
    (tmp_path / "copy" / "src").rename(tmp_path / "copy" / "real")
    (tmp_path / "copy" / "src").symlink_to(tmp_path / "copy" / "real", target_is_directory=True)
    with pytest.raises(pt.PatchError, match="real folder"):
        pt.write_tree(tmp_path / "copy", pt.plan(patches, []))
    assert not dest.exists()


@LINUX
def test_the_second_patch_refused_leaves_no_tree(clone, tmp_path):
    src, _, entries = clone
    good = ("a", patch("src/load.py", b"line 3", b"x"))
    bad = ("b", patch("requirements.txt", b"other", b"y", line=1))
    with pytest.raises(pt.PatchError):
        pt.prepare(src, tmp_path / "patched", [good, bad], [], entries)
    # the second patch's context does not match: refused when written, so the tree is
    # never used; a new preparation starts from the clone in a new folder
    record = pt.prepare(src, tmp_path / "patched2", [good], [], entries)
    assert record["touched"]["src/load.py"]["before"] is not None


@LINUX
def test_an_executable_files_index_mode_must_be_its_own(clone, tmp_path):
    src, _, entries = clone
    p = (
        b"diff --git a/run.sh b/run.sh\nindex 1234567..89abcde 100644\n--- a/run.sh\n"
        b"+++ b/run.sh\n@@ -1 +1 @@\n-echo 1\n+echo 2\n"
    )
    with pytest.raises(pt.PatchError, match="mode"):
        pt.prepare(src, tmp_path / "patched", [("p", p)], [], entries)
    ok = p.replace(b"100644", b"100755")
    record = pt.prepare(src, tmp_path / "patched2", [("p", ok)], [], entries)
    assert (tmp_path / "patched2" / "run.sh").stat().st_mode & 0o100
    assert record["touched"]["run.sh"]["after"]


@LINUX
def test_a_tampered_record_fails_the_verification(clone, tmp_path):
    src, _, entries = clone
    patches = [("p", patch("src/load.py", b"line 3", b"x"))]
    record = pt.prepare(src, tmp_path / "patched", patches, [], entries)
    for key in ("touched", "patched_manifest", "patches"):
        bad = dict(record)
        bad[key] = {} if key != "patches" else list(reversed(record["patches"])) + [{}]
        assert pt.verify(src, tmp_path / f"v-{key}", patches, [], entries, bad)


@LINUX
def test_a_copy_is_checked_against_the_patched_tree(clone, tmp_path):
    src, _, entries = clone
    record = pt.prepare(src, tmp_path / "patched", [], [], entries)
    folder = tmp_path / "copy"
    pd._copy_repo(tmp_path / "patched", folder)  # noqa: SLF001
    pd.check_copy(folder, record["patched_manifest"])
    (folder / "src" / "load.py").write_bytes(b"changed\n")
    with pytest.raises(pd.ProductionError, match="differs"):
        pd.check_copy(folder, record["patched_manifest"])


def test_a_claim_with_a_hook_route_is_refused_in_production():
    for role, routes in (("method", ["hook"]), ("reference", ["printed_count", "hook"])):
        claim = {"targets": [{"key": "c1", "coverage_evidence": {role: {"routes": [
            {"route": r} for r in routes]}}}]}  # fmt: skip
        with pytest.raises(pd.ProductionError, match="hook route"):
            pd.refuse_hook_routes(claim)
    pd.refuse_hook_routes({"targets": [{"coverage_evidence": {"method": {"routes": [
        {"route": "printed_count"}]}}}]})  # fmt: skip
