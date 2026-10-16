"""ML pack: the repository at its pinned commit (WP3 W3.6, V16), offline, on local git
repositories built by the test (a file:// clone uses no network)."""

import os
import shutil
import subprocess

import pytest

from refute.packs.ml import repository as rp

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="git is not installed")


def git(repo, *args, date=None):
    env = dict(os.environ, GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull)
    if date:
        env.update(GIT_AUTHOR_DATE=date, GIT_COMMITTER_DATE=date)
    done = subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@example.org", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        env=env,
        check=True,
    )
    return done.stdout.strip()


@pytest.fixture
def origin(tmp_path):
    """A repository with three commits on main, a lightweight tag and an annotated tag."""
    repo = tmp_path / "origin"
    repo.mkdir()
    git(repo, "init", "--quiet", "--initial-branch=main")
    commits = []
    for i, date in enumerate(
        ["2024-01-10T12:00:00Z", "2024-02-10T12:00:00Z", "2024-03-10T12:00:00Z"], start=1
    ):
        (repo / "train.py").write_text(f"print({i})\n")
        git(repo, "add", "train.py")
        git(repo, "commit", "--quiet", "-m", f"c{i}", date=date)
        commits.append(git(repo, "rev-parse", "HEAD"))
    git(repo, "tag", "v1.0", commits[0])
    git(repo, "tag", "-a", "v2.0", "-m", "release", commits[1], date="2024-02-11T00:00:00Z")
    return repo, commits


def test_clone_and_resolve_refs_to_full_commits(tmp_path, origin):
    repo, commits = origin
    clone = rp.clone(repo.as_uri(), tmp_path / "clone")
    assert rp.resolve_commit(clone, "v1.0") == commits[0]
    assert rp.resolve_commit(clone, "v2.0") == commits[1]  # annotated tag -> its commit
    assert rp.resolve_commit(clone, commits[2][:10]) == commits[2]
    assert rp.resolve_commit(clone, "origin/main") == commits[2]
    with pytest.raises(rp.RepositoryError):
        rp.resolve_commit(clone, "v9.9")
    with pytest.raises(ValueError):
        rp.resolve_commit(clone, "--all")


def test_a_clone_never_overwrites(tmp_path, origin):
    repo, _ = origin
    (tmp_path / "clone").mkdir()
    with pytest.raises(rp.RepositoryError, match="never overwritten"):
        rp.clone(repo.as_uri(), tmp_path / "clone")
    with pytest.raises(ValueError, match="https"):
        rp.clone("http://example.org/x.git", tmp_path / "other")


def test_the_latest_commit_at_an_instant(tmp_path, origin):
    repo, commits = origin
    clone = rp.clone(repo.as_uri(), tmp_path / "clone")
    assert rp.latest_commit_before(clone, "origin/main", "2024-02-20T00:00:00Z") == commits[1]
    assert rp.latest_commit_before(clone, "origin/main", "2024-02-10T12:00:00Z") == commits[1]
    assert rp.latest_commit_before(clone, "origin/main", "2030-01-01T00:00:00Z") == commits[2]
    with pytest.raises(rp.RepositoryError, match="no commit"):
        rp.latest_commit_before(clone, "origin/main", "2023-01-01T00:00:00Z")
    with pytest.raises(ValueError):
        rp.latest_commit_before(clone, "origin/main", "2024-02-20")


def test_checkout_is_exact(tmp_path, origin):
    repo, commits = origin
    clone = rp.clone(repo.as_uri(), tmp_path / "clone")
    rp.checkout(clone, commits[0])
    assert (clone / "train.py").read_text() == "print(1)\n"
    with pytest.raises(ValueError):
        rp.checkout(clone, "v1.0")  # only a full commit


def test_checkout_never_discards_a_local_change(tmp_path, origin):
    """Codex review: no forced checkout; a change that would be overwritten stops it."""
    repo, commits = origin
    clone = rp.clone(repo.as_uri(), tmp_path / "clone")
    rp.checkout(clone, commits[0])
    (clone / "train.py").write_text("local work\n")
    with pytest.raises(rp.RepositoryError, match="checkout failed"):
        rp.checkout(clone, commits[2])
    assert (clone / "train.py").read_text() == "local work\n"


def test_only_a_clone_made_by_refute_is_checked_out(origin):
    repo, commits = origin
    with pytest.raises(rp.RepositoryError, match="not a clone made by Refute"):
        rp.checkout(repo, commits[0])


def test_the_clone_allows_only_its_own_protocol(tmp_path, monkeypatch):
    calls = []

    def record(repo, *args, config=(), timeout=0):
        calls.append(config)
        (tmp_path / "dest" / ".git").mkdir(parents=True)
        return ""

    monkeypatch.setattr(rp, "_git", record)
    rp.clone("https://example.org/x.git", tmp_path / "dest")
    assert calls == [("protocol.allow=never", "protocol.https.allow=always")]
    with pytest.raises(ValueError, match="https"):
        rp.clone(str(tmp_path / "local"), tmp_path / "other")


def test_the_three_commits_are_recorded(tmp_path, origin):
    repo, commits = origin
    clone = rp.clone(repo.as_uri(), tmp_path / "clone")
    named = rp.record(
        clone,
        arxiv_id="2401.01234",
        version=2,
        version_basis="named_in_readme",
        named_ref="v1.0",
        default_ref="origin/main",
        draw_instant_utc="2024-02-20T00:00:00Z",
    )
    assert named.chosen_commit == commits[0] and named.latest_commit_at_draw == commits[1]
    assert named.as_dict()["paper"] == {"arxiv_id": "2401.01234", "version": 2}
    latest = rp.record(
        clone,
        arxiv_id="2401.01234",
        version=2,
        version_basis="latest_at_draw",
        named_ref=None,
        default_ref="origin/main",
        draw_instant_utc="2024-02-20T00:00:00Z",
    )
    assert latest.chosen_commit == latest.latest_commit_at_draw == commits[1]
    with pytest.raises(ValueError, match="needs the named ref"):
        rp.record(
            clone,
            arxiv_id="2401.01234",
            version=2,
            version_basis="named_in_paper",
            named_ref=None,
            default_ref="origin/main",
            draw_instant_utc="2024-02-20T00:00:00Z",
        )
