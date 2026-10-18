"""The repository of an ML paper at its pinned commit (WP3 W3.6; plan section 6.1, lines
384-389, decision D-8).

"Frozen by commit. Use the version explicitly associated with the result (a tag or commit
named in the paper or README); without one, the latest commit on the draw date. Record
the paper version, the chosen commit and the latest commit; tags are resolved to
commits."

This module works on a local clone with the ``git`` program, never running any code of
the repository:

- ``clone`` is the only function that may use the network (W3.7): it is called
  explicitly, by a fetch command, with the URL of the claim;
- ``resolve_commit`` turns a tag, a branch or an abbreviated commit into the full commit
  (``git rev-parse --verify <ref>^{commit}``); an annotated tag resolves to the commit it
  points to;
- ``latest_commit_before`` gives the last commit of a ref whose committer date is at or
  before a given UTC instant (``git rev-list -1 --before``); which instant is "the draw
  date" is fixed by the protocol, not here;
- ``checkout`` puts the working tree of a clone made by ``clone`` at a commit, never
  discarding a local change (no ``--force``: Git refuses when a change would be
  overwritten), and checks that it is exactly that commit, with no change to any tracked
  file;
- ``record`` writes the three commits of D-8 as a dictionary for the dossier.

Git runs with no ``GIT_*`` variable of the environment, with the user's and system
configuration disabled (``GIT_CONFIG_NOSYSTEM``, a global configuration of
``os.devnull``) and with hooks turned off, so no setting of the host changes what is
checked out. The clone allows only the ``https`` protocol, also for redirects (Git limits
the protocols curl may follow to the allowed ones), or only ``file`` for a local test
repository.
"""

from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

HEX40 = re.compile(r"^[0-9a-f]{40}$")
UTC = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
TIMEOUT_S = 600
MARKER = "refute-clone"  # written in the .git folder of a clone made by ``clone``


class RepositoryError(RuntimeError):
    """A git command failed or gave an unexpected answer."""


def _git(
    repo: Path | None, *args: str, config: tuple[str, ...] = (), timeout: float = TIMEOUT_S
) -> str:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(
        {
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_TERMINAL_PROMPT": "0",
        }
    )
    command = ["git", "-c", "core.hooksPath=" + os.devnull, "-c", "core.autocrlf=false"]
    for setting in config:
        command += ["-c", setting]
    if repo is not None:
        command += ["-C", str(repo)]
    try:
        done = subprocess.run(
            [*command, *args],
            capture_output=True,
            text=True,
            env=env,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RepositoryError(f"git {args[0]}: {exc}") from exc
    if done.returncode != 0:
        raise RepositoryError(f"git {args[0]} failed ({done.returncode}): {done.stderr.strip()}")
    return done.stdout


def clone(url: str, dest: Path) -> Path:
    """Clones ``url`` into ``dest`` (which must not exist), with no checkout. The only
    network access of this module."""
    if url.startswith("https://"):
        allowed = "https"
    elif url.startswith("file://"):
        allowed = "file"
    else:
        raise ValueError("only https URLs are cloned (file:// for local tests)")
    if dest.exists():
        raise RepositoryError(f"{dest} already exists; it is never overwritten")
    protocols = ("protocol.allow=never", f"protocol.{allowed}.allow=always")
    _git(None, "clone", "--no-checkout", "--quiet", "--", url, str(dest), config=protocols)
    try:
        (dest / ".git" / MARKER).write_text(url + "\n", encoding="utf-8")
    except OSError as exc:
        raise RepositoryError(f"cannot mark {dest} as a clone of Refute: {exc}") from exc
    return dest


def resolve_commit(repo: Path, ref: str) -> str:
    """The full commit a tag, branch or commit names."""
    if not ref or ref.startswith("-"):
        raise ValueError(f"invalid ref {ref!r}")
    commit = _git(repo, "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}").strip()
    if not HEX40.match(commit):
        raise RepositoryError(f"{ref!r} does not resolve to a commit")
    return commit


def latest_commit_before(repo: Path, ref: str, instant_utc: str) -> str:
    """The last commit reachable from ``ref`` whose committer date is at or before
    ``instant_utc`` (``YYYY-MM-DDTHH:MM:SSZ``)."""
    if not UTC.match(instant_utc):
        raise ValueError("instant_utc is YYYY-MM-DDTHH:MM:SSZ")
    tip = resolve_commit(repo, ref)
    commit = _git(repo, "rev-list", "-1", f"--before={instant_utc}", tip).strip()
    if not HEX40.match(commit):
        raise RepositoryError(f"no commit of {ref!r} at or before {instant_utc}")
    return commit


def checkout(repo: Path, commit: str) -> None:
    """Checks out ``commit`` (detached) and verifies the result: HEAD is that commit and
    no tracked file differs from it."""
    if not HEX40.match(commit):
        raise ValueError("checkout takes a full commit (40 hexadecimal characters)")
    if not (repo / ".git" / MARKER).is_file():
        raise RepositoryError(f"{repo} is not a clone made by Refute; it is never checked out")
    _git(repo, "checkout", "--quiet", "--detach", commit)  # refuses to discard a change
    head = _git(repo, "rev-parse", "HEAD").strip()
    if head != commit:
        raise RepositoryError(f"HEAD is {head}, not {commit}")
    changed = _git(repo, "status", "--porcelain", "--untracked-files=no").strip()
    if changed:
        raise RepositoryError("tracked files differ from the commit after the checkout")


def ls_tree(repo: Path, commit: str) -> str:
    """``git ls-tree -r -z --full-tree`` of ``commit``: the tree the checked-out content
    must equal (wp3-allowed-patches-acceptance.md, section 2)."""
    if not HEX40.match(commit):
        raise ValueError("ls_tree takes a full commit (40 hexadecimal characters)")
    return _git(repo, "ls-tree", "-r", "-z", "--full-tree", commit)


@dataclass(frozen=True)
class CommitRecord:
    """The three commits of D-8, for the dossier."""

    paper_arxiv_id: str
    paper_version: int
    version_basis: str  # named_in_paper, named_in_readme or latest_at_draw
    named_ref: str | None
    chosen_commit: str
    latest_commit_at_draw: str

    def as_dict(self) -> dict[str, object]:
        return {
            "paper": {"arxiv_id": self.paper_arxiv_id, "version": self.paper_version},
            "version_basis": self.version_basis,
            "named_ref": self.named_ref,
            "chosen_commit": self.chosen_commit,
            "latest_commit_at_draw": self.latest_commit_at_draw,
        }


def record(
    repo: Path,
    *,
    arxiv_id: str,
    version: int,
    version_basis: str,
    named_ref: str | None,
    default_ref: str,
    draw_instant_utc: str,
) -> CommitRecord:
    """Resolves the chosen commit and the latest commit at the draw, by the rule of D-8:
    the named ref when the paper or the README names one, otherwise the latest commit of
    ``default_ref`` at the draw instant."""
    latest = latest_commit_before(repo, default_ref, draw_instant_utc)
    if version_basis in ("named_in_paper", "named_in_readme"):
        if not named_ref:
            raise ValueError(f"{version_basis} needs the named ref")
        chosen = resolve_commit(repo, named_ref)
    elif version_basis == "latest_at_draw":
        if named_ref is not None:
            raise ValueError("latest_at_draw takes no named ref")
        chosen = latest
    else:
        raise ValueError(f"unknown version_basis {version_basis!r}")
    return CommitRecord(arxiv_id, version, version_basis, named_ref, chosen, latest)
