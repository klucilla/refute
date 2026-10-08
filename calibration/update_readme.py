"""Fill the "Calibration results" section of README.md from the lock and the run summary.

The section lives between the markers ``<!-- CALIBRATION:START -->`` and
``<!-- CALIBRATION:END -->``. Run from the repository root:

    uv run python calibration/update_readme.py            # update README.md in place
    uv run python calibration/update_readme.py --check    # exit 1 if README.md is stale

Another claim (for example the v0.2 calibration) uses its own section markers:

    uv run python calibration/update_readme.py --claim calibration/v0.2/self_claim.yaml \
        --section CALIBRATION-V0.2

Its lock, lock history, results and post-mortem are looked up next to the claim.

The rendered state is derived only from files in the repository:

1. no lock file            -> "lock pending" with the canonical claim hash;
2. lock, no results        -> "locked, not yet run" with claim hash, code hash and commit;
3. results/<run_id>/summary.json -> the self-claim result (PASS or FAIL) and its criteria.

If ``refute verify`` does not return PASS, the section says so. When the only
reason could be that the code changed after the claim's phase closed, the script
looks for a git tag (then the run commit) whose code, hashed from git objects with
the same ``refute-code-1`` algorithm, equals the locked code, and tells the reader
to verify the lock there. It never reports PASS for a checkout it did not verify.
Results are copied as they are, whatever they are. This script lives outside
``src/`` on purpose: it is documentation tooling and is not part of the locked
code hash.
"""

from __future__ import annotations

import argparse
import io
import json
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path
from typing import Any

START = "<!-- CALIBRATION:START -->"
END = "<!-- CALIBRATION:END -->"
ROOT = Path(__file__).resolve().parent.parent
CLAIM = Path("calibration/self_claim.yaml")
LOCK = Path("calibration/self_claim.lock.json")
HISTORY = Path("calibration/LOCK_HISTORY.md")
RESULTS = Path("calibration/results")
POSTMORTEM = Path("calibration/POSTMORTEM.md")


class MarkerError(ValueError):
    """README markers are missing, duplicated or out of order."""


def replace_section(text: str, body: str) -> str:
    if text.count(START) != 1 or text.count(END) != 1:
        raise MarkerError("README.md must contain each calibration marker exactly once")
    head, rest = text.split(START, 1)
    if END not in rest:
        raise MarkerError("the END marker must come after the START marker")
    _, tail = rest.split(END, 1)
    return f"{head}{START}\n{body.strip()}\n{END}{tail}"


def repo_url(root: Path) -> str | None:
    try:
        out = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        ).stdout.strip()
    except OSError:
        return None
    if not out:
        return None
    if out.startswith("git@github.com:"):
        out = "https://github.com/" + out.removeprefix("git@github.com:")
    return out.removesuffix(".git") if out.startswith("https://") else None


def commit_link(commit: str | None, url: str | None) -> str:
    if not commit:
        return "none"
    short = f"`{commit[:12]}`"
    return f"[{short}]({url}/commit/{commit})" if url else short


def ref_link(ref: dict[str, Any], url: str | None) -> str:
    if not ref.get("is_tag"):
        return f"commit {commit_link(ref['ref'], url)}"
    name = f"`{ref['ref']}`"
    return f"tag [{name}]({url}/tree/{ref['ref']})" if url else f"tag {name}"


def git_tags(root: Path) -> list[str]:
    """Tags of the repository, newest first (empty when git or tags are unavailable)."""
    try:
        out = subprocess.run(
            ["git", "tag", "--list", "--sort=-creatordate"],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return []
    return [line.strip() for line in out.stdout.splitlines() if line.strip()]


def code_hash_at_ref(root: Path, ref: str) -> str | None:
    """``refute-code-1`` hash of the code stored in git at ``ref`` (no checkout needed).

    The files covered by the code hash are exported with ``git archive`` into a
    temporary directory and hashed with :func:`refute.core.codehash.compute_code_hash`,
    so the algorithm is exactly the one ``refute verify`` uses.
    """
    from refute.core.codehash import CodeHashError, compute_code_hash

    try:
        archive = subprocess.run(
            ["git", "archive", "--format=tar", ref, "--", "src", "pyproject.toml", "uv.lock"],
            cwd=root,
            capture_output=True,
            check=False,
        )
    except OSError:
        return None
    if archive.returncode != 0:
        return None
    with tempfile.TemporaryDirectory() as tmp:
        with tarfile.open(fileobj=io.BytesIO(archive.stdout)) as tar:
            tar.extractall(tmp, filter="data")
        try:
            return compute_code_hash(Path(tmp)).sha256
        except CodeHashError:
            return None


def find_locked_code_ref(
    root: Path, code_sha256: str, extra_commits: list[str]
) -> dict[str, Any] | None:
    """First tag (newest first), then commit, whose code equals the locked code."""
    candidates = [(tag, True) for tag in git_tags(root)]
    candidates += [(commit, False) for commit in extra_commits if commit]
    for ref, is_tag in candidates:
        if code_hash_at_ref(root, ref) == code_sha256:
            return {"ref": ref, "is_tag": is_tag}
    return None


def render(state: dict[str, Any]) -> str:
    url = state.get("repo_url")
    if state["stage"] == "pending":
        return "\n".join(
            [
                "**Status: lock pending.** The self-claim and its targets are written.",
                "`refute lock` will hash them together with the code, from a clean committed",
                "tree, before any calibration light curve is analyzed.",
                "",
                "| Item | Value |",
                "|---|---|",
                f"| Claim | [`{CLAIM.as_posix()}`]({CLAIM.as_posix()}) |",
                f"| Claim SHA-256 (canonical form to be locked) | `{state['claim_sha256']}` |",
                f"| Targets | {state['targets_note']} |",
            ]
        )
    lock = state["lock"]
    verify = state["verify_status"]
    locked_ref = state.get("locked_code_ref") if verify != "PASS" else None
    verify_cell = verify
    if locked_ref:
        verify_cell = f"{verify} on this branch; locked code at {ref_link(locked_ref, url)}"
    rows = [
        "| Item | Value |",
        "|---|---|",
        f"| Claim | [`{CLAIM.as_posix()}`]({CLAIM.as_posix()}) |",
        f"| Claim SHA-256 | `{lock['claim_sha256']}` |",
        f"| Code SHA-256 | `{lock['code']['sha256']}` |",
        f"| Locked from commit | {commit_link(lock.get('git_commit'), url)} |",
        f"| Locked at (UTC) | {lock['locked_at_utc']} |",
        f"| `refute verify` | {verify_cell} |",
        f"| Evidence | [lock file]({LOCK.as_posix()}) · [lock history]({HISTORY.as_posix()}) |",
    ]
    warning = []
    if locked_ref:
        warning = [
            "",
            "> [!NOTE]",
            f"> `refute verify` returns **{verify}** for this claim in this checkout because",
            "> the code here differs from the code it was locked with. The code at",
            f"> {ref_link(locked_ref, url)} has the locked code hash (recomputed from git",
            "> objects). Verify the lock there:",
            ">",
            "> ```bash",
            f"> git checkout {locked_ref['ref']}",
            "> uv sync --frozen",
            f"> uv run refute verify {CLAIM.as_posix()}",
            "> ```",
        ]
    elif verify != "PASS":
        warning = [
            "",
            "> [!WARNING]",
            f"> `refute verify` returns **{verify}** for the self-claim in this checkout.",
        ]
    if state["stage"] == "locked":
        return "\n".join(
            [
                "**Status: locked, not yet run.** The self-claim was locked before any",
                "calibration light curve was analyzed. The result will be published here",
                "whatever it is.",
                "",
                *rows,
                *warning,
            ]
        )
    summary = state["summary"]
    claim = summary["self_claim"]
    run = summary.get("run", {})
    criteria = [
        "| Criterion | Value | Requirement | Passed |",
        "|---|---|---|---|",
        *(
            f"| {c['criterion']} | {c['value']} of {c['of']} | {c['requirement']} | "
            f"{'yes' if c['passed'] else 'no'} |"
            for c in claim["criteria"]
        ),
    ]
    note = claim["note"][:1].upper() + claim["note"][1:]
    links = [f"[summary]({state['summary_md']})"]
    if state.get("runs_md"):
        links.append(f"[run log]({state['runs_md']})")
    if state.get("postmortem"):
        links.append(f"[post-mortem]({state['postmortem']})")
    if state.get("archive_sha256"):
        links.append(f"dossier archive SHA-256 `{state['archive_sha256']}`")
    return "\n".join(
        [
            f"**Self-claim result: {claim['result']}.** {note}.",
            "",
            *criteria,
            "",
            f"Run `{run.get('run_id')}` from commit {commit_link(run.get('run_git_commit'), url)}"
            f" ({run.get('finished_utc')}). " + " · ".join(links),
            "",
            *rows,
            *warning,
        ]
    )


def configure(claim: Path, section: str = "CALIBRATION") -> None:
    """Point the script at another claim and README section (defaults: the v0.1 claim)."""
    global START, END, CLAIM, LOCK, HISTORY, RESULTS, POSTMORTEM
    START = f"<!-- {section}:START -->"
    END = f"<!-- {section}:END -->"
    CLAIM = Path(claim)
    LOCK = CLAIM.with_name(f"{CLAIM.stem}.lock.json")
    HISTORY = CLAIM.parent / "LOCK_HISTORY.md"
    RESULTS = CLAIM.parent / "results"
    POSTMORTEM = CLAIM.parent / "POSTMORTEM.md"


def latest_summary(root: Path) -> Path | None:
    candidates = sorted((root / RESULTS).glob("*/summary.json"))
    return candidates[-1] if candidates else None


def collect_state(root: Path, summary_path: Path | None = None) -> dict[str, Any]:
    from refute.core.claim import load_claim
    from refute.core.lock import verify_claim

    state: dict[str, Any] = {"repo_url": repo_url(root)}
    claim_file = root / CLAIM
    lock_file = root / LOCK
    if not lock_file.is_file():
        loaded = load_claim(claim_file)
        targets = loaded.pack.schema.targets_for_run(loaded)
        planets = sum(1 for t in targets if t.get("kind") == "planet")
        fps = sum(1 for t in targets if t.get("kind") == "false_positive")
        state.update(
            stage="pending",
            claim_sha256=loaded.sha256(),
            targets_note=(
                f"{planets} known planets and {fps} known false positives, selected by the "
                "seeded protocol in [`calibration/PROTOCOL.md`](calibration/PROTOCOL.md)"
            ),
        )
        return state
    state["lock"] = json.loads(lock_file.read_text(encoding="utf-8"))
    state["verify_status"] = verify_claim(claim_file).status.value
    summary_path = summary_path or latest_summary(root)
    if summary_path is None:
        state["stage"] = "locked"
        if state["verify_status"] != "PASS":
            # The lock commit itself has no lock file yet, so only tags are candidates.
            state["locked_code_ref"] = find_locked_code_ref(
                root, state["lock"]["code"]["sha256"], []
            )
        return state
    run_dir = summary_path.parent
    state.update(
        stage="results",
        summary=json.loads(summary_path.read_text(encoding="utf-8")),
        summary_md=(run_dir / "summary.md").relative_to(root).as_posix(),
    )
    runs_md = run_dir / "RUNS.md"
    if runs_md.is_file():
        state["runs_md"] = runs_md.relative_to(root).as_posix()
    postmortem = root / POSTMORTEM
    if postmortem.is_file():
        state["postmortem"] = postmortem.relative_to(root).as_posix()
    archive_hash = run_dir / "dossiers.zip.sha256"
    if archive_hash.is_file():
        state["archive_sha256"] = archive_hash.read_text(encoding="utf-8").split()[0]
    if state["verify_status"] != "PASS":
        run_commit = state["summary"].get("run", {}).get("run_git_commit")
        state["locked_code_ref"] = find_locked_code_ref(
            root, state["lock"]["code"]["sha256"], [run_commit]
        )
    return state


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--readme", type=Path, default=ROOT / "README.md")
    parser.add_argument("--summary", type=Path, default=None, help="summary.json of a run")
    parser.add_argument("--check", action="store_true", help="exit 1 if README.md is stale")
    parser.add_argument("--claim", type=Path, default=CLAIM, help="claim (relative to the root)")
    parser.add_argument("--section", default="CALIBRATION", help="README section marker name")
    args = parser.parse_args(argv)
    configure(args.claim, args.section)
    text = args.readme.read_text(encoding="utf-8")
    updated = replace_section(text, render(collect_state(ROOT, args.summary)))
    if args.check:
        if updated != text:
            print("README.md calibration section is out of date", file=sys.stderr)
            return 1
        print("README.md calibration section is up to date")
        return 0
    if updated != text:
        args.readme.write_bytes(updated.encode("utf-8"))
        print("README.md calibration section updated")
    else:
        print("README.md calibration section already up to date")
    return 0


if __name__ == "__main__":
    sys.exit(main())
