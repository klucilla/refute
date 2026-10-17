"""The v0.3 pilot draw (calibration/v0.3/pilot/PROTOCOL.md; plan sections 4.3 to 4.5).

Run after the pilot's drand round is published, from a clean checkout of main whose
protocol commit was pushed at least an hour before the round. It:

1. checks the proof of publication of the protocol commit (the ``created_at`` of its
   GitHub Actions push run, ``refute.selection.publication``) against the round's time;
2. fetches and verifies the drand round (``refute.drand``), ``seed = int(randomness, 16)``;
3. loads the frame (SHA-256 checked), applies filters 0 to 5, sorts by arXiv ID and
   shuffles with the seed, and takes the first 20 papers (for the additional round,
   after removing the first round's papers);
4. reads, for each, the arXiv metadata and the GitHub repository's metadata and README,
   with the retry policy of the protocol, and applies the mechanical rejections
   (category, keywords, repository unavailable or archived);
5. writes ``pilot_draw.json`` and ``pilot_draw.md`` (never overwriting), and keeps the
   README texts in the local cache only.

It runs no repository code and makes no triage decision beyond the mechanical ones.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from refute import drand
from refute.selection.filters import (
    DEFAULT_CATEGORIES,
    DEFAULT_WINDOW,
    apply_filters,
    category_allowed,
    keyword_hits,
)
from refute.selection.frame import FrameSnapshot, load_frame
from refute.selection.publication import check_publication, fetch_push_runs
from refute.selection.walk import RetryPolicy, transient_query, with_retries

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CACHE = ROOT / ".cache" / "round6" / "pilot"

FRAME_URL = (
    "https://huggingface.co/datasets/pwc-archive/links-between-paper-and-code/resolve/"
    "56cc5c1938678c33dedebf5f74fc4e62e2c35381/data/train-00000-of-00001.parquet"
)
FRAME_REVISION = "56cc5c1938678c33dedebf5f74fc4e62e2c35381"
FRAME_SHA256 = "c845ff642112a345f6271bf954d007c6698088d7de525f3f8d5f7d975f142c76"
PILOT_ROUND = 6561446
PILOT_SIZE = 20
RETRY = RetryPolicy(attempts=3, backoff_seconds=15.0)
REPOSITORY = "klucilla/refute"
WORKFLOW = ".github/workflows/ci.yml"
MARGIN = timedelta(hours=1)
TRIAGE_FILE = "calibration/v0.3/pilot/pilot_triage.md"
DRAW_FILE = "calibration/v0.3/pilot/pilot_draw.json"
ADDITIONAL_NEEDED = "Additional pilot round: needed"
# Every file whose content decides the draw (Codex review of the pilot protocol): the
# protocol, this script, the selection modules it imports and the environment's
# definition. Each must be identical to its version in the protocol commit.
PROTOCOL_FILES = (
    "calibration/v0.3/pilot/PROTOCOL.md",
    "calibration/v0.3/pilot/select_pilot.py",
    "src/refute/__init__.py",
    "src/refute/drand.py",
    "src/refute/selection/__init__.py",
    "src/refute/selection/frame.py",
    "src/refute/selection/filters.py",
    "src/refute/selection/walk.py",
    "src/refute/selection/publication.py",
    "pyproject.toml",
    "uv.lock",
)
KEYWORDS = (
    "clinical", "clinic", "patient", "patients", "medical", "medicine", "diagnosis",
    "diagnostic", "diagnostics", "disease", "diseases", "cancer", "tumor", "tumour",
    "radiology", "healthcare", "health care", "electronic health records", "ehr", "mri",
    "x-ray", "ecg", "eeg", "surgical", "surgery", "drug", "drugs", "pharmaceutical",
    "molecule", "molecules", "molecular", "protein", "proteins", "genomic", "genomics",
    "dna", "rna", "pathogen", "pathogens", "virus", "viral", "toxin", "toxins", "toxicity",
    "chemical", "chemistry", "bioweapon", "biosecurity",
)  # fmt: skip
ATOM = {"a": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
GITHUB_REPO = re.compile(r"^https?://github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+?)(?:\.git)?/?$")


class PilotError(Exception):
    """The pilot draw cannot go on; the maintainer decides."""


# ---- pure parts (tested offline) ---------------------------------------------------------


def parse_arxiv_entry(xml_text: str, arxiv_id: str) -> dict[str, str]:
    """Primary category, title, abstract and versioned id of one arXiv export API answer."""
    root = ET.fromstring(xml_text)
    entries = root.findall("a:entry", ATOM)
    if len(entries) != 1:
        raise PilotError(f"{arxiv_id}: the arXiv answer has {len(entries)} entries")
    entry = entries[0]
    versioned = (entry.findtext("a:id", default="", namespaces=ATOM) or "").rsplit("/", 1)[-1]
    if not versioned.startswith(arxiv_id):
        raise PilotError(f"{arxiv_id}: the arXiv answer is for {versioned!r}")
    primary = entry.find("arxiv:primary_category", ATOM)
    if primary is None or not primary.get("term"):
        raise PilotError(f"{arxiv_id}: no primary category in the arXiv answer")

    def text(tag: str) -> str:
        return " ".join((entry.findtext(tag, default="", namespaces=ATOM) or "").split())

    return {
        "versioned_id": versioned,
        "primary_category": primary.get("term"),
        "title": text("a:title"),
        "abstract": text("a:summary"),
    }


def github_repo(url: str) -> tuple[str, str] | None:
    """(owner, name) of a GitHub repository URL, or None for another host."""
    match = GITHUB_REPO.match(url.strip())
    return (match.group(1), match.group(2)) if match else None


def mechanical(candidate: dict[str, Any]) -> tuple[str | None, str]:
    """The mechanical rejection of a pilot paper, if any: (reason, evidence)."""
    meta = candidate["arxiv"]
    if not category_allowed(meta["primary_category"], DEFAULT_CATEGORIES):
        return "category_outside_list", f"arXiv primary category {meta['primary_category']}"
    hits = keyword_hits(meta["title"], meta["abstract"], KEYWORDS)
    if hits:
        return "out_of_scope", "keywords in title or abstract: " + ", ".join(hits)
    repo = candidate["repository"]
    if repo.get("host") == "github" and not repo.get("exists"):
        return "repository_unavailable", "the GitHub API answers 404 for the repository"
    if repo.get("archived"):
        return "repository_unavailable", "the repository is archived on GitHub"
    return None, ""


def draw_ids(rows: list[dict[str, Any]], seed: int, exclude: set[str]) -> list[dict[str, Any]]:
    """The pilot papers: the filtered frame sorted by arXiv ID, shuffled with the seed,
    without the excluded papers, first PILOT_SIZE."""
    order = drand.shuffled(rows, seed, key=lambda r: r["paper_arxiv_id"])
    return [r for r in order if r["paper_arxiv_id"] not in exclude][:PILOT_SIZE]


# ---- network (run only by the maintainer-approved command) -------------------------------


def _request(url: str, accept: str = "application/json") -> bytes:
    headers = {"User-Agent": "refute-selection", "Accept": accept}
    token = os.environ.get("GITHUB_TOKEN")
    if token and url.startswith("https://api.github.com/"):
        headers["Authorization"] = f"Bearer {token}"
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=60) as r:  # noqa: S310
        return r.read()


def _retried(query, context: str):
    result, failures = with_retries(lambda: transient_query(query, context), RETRY, time.sleep)
    return result, [{"utc": f.utc, "error": f.error} for f in failures]


def read_arxiv(arxiv_id: str) -> tuple[dict[str, str], list[dict[str, str]]]:
    url = "https://export.arxiv.org/api/query?" + urllib.parse.urlencode({"id_list": arxiv_id})
    body, failures = _retried(lambda: _request(url, "application/atom+xml"), f"arXiv {arxiv_id}")
    time.sleep(3)  # arXiv asks for a pause between API calls
    return parse_arxiv_entry(body.decode("utf-8"), arxiv_id), failures


def read_github(repo_url: str, readme_dir: Path, arxiv_id: str) -> tuple[dict[str, Any], list]:
    parsed = github_repo(repo_url)
    if parsed is None:
        return {"host": "other", "url": repo_url}, []
    owner, name = parsed
    base = f"https://api.github.com/repos/{owner}/{name}"
    failures: list = []
    try:
        meta, f1 = _retried(lambda: json.loads(_request(base)), f"GitHub {owner}/{name}")
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return {"host": "github", "url": repo_url, "exists": False}, []
        raise
    failures += f1
    branch = meta["default_branch"]
    head, f2 = _retried(
        lambda: json.loads(_request(f"{base}/commits/{urllib.parse.quote(branch)}")),
        f"GitHub {owner}/{name} head",
    )
    failures += f2
    commit = head["sha"]
    record: dict[str, Any] = {
        "host": "github",
        "url": repo_url,
        "exists": True,
        "full_name": meta["full_name"],
        "archived": bool(meta.get("archived")),
        "default_branch": branch,
        "head_commit": commit,
        "license_spdx": (meta.get("license") or {}).get("spdx_id"),
        "readme": None,
    }
    try:
        readme, f3 = _retried(
            lambda: json.loads(_request(f"{base}/readme?ref={commit}")),
            f"GitHub {owner}/{name} README",
        )
        failures += f3
        content = base64.b64decode(readme["content"])
        readme_dir.mkdir(parents=True, exist_ok=True)
        (readme_dir / f"{arxiv_id}.txt").write_bytes(content)
        record["readme"] = {
            "path": readme["path"],
            "url": f"https://github.com/{meta['full_name']}/blob/{commit}/{readme['path']}",
            "sha256": hashlib.sha256(content).hexdigest(),
            "bytes": len(content),
        }
    except urllib.error.HTTPError as exc:
        if exc.code != 404:
            raise
    return record, failures


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout.strip()


def _in_commit(commit: str, path: str) -> bytes:
    return subprocess.run(
        ["git", "show", f"{commit}:{path}"], cwd=ROOT, check=True, capture_output=True
    ).stdout


def _push_runs(commit: str) -> list:
    return fetch_push_runs(REPOSITORY, commit, lambda url: json.loads(_request(url)))


def publication_proof(commit: str):
    """The protocol commit was pushed at least MARGIN before the **first** pilot round, in
    every run (also the additional one), and every file that decides the draw is the
    committed one (Codex review of the pilot protocol)."""
    if _git("status", "--porcelain"):
        raise PilotError("the working tree is not clean")
    if (
        _git("rev-parse", "HEAD") != commit
        and subprocess.run(
            ["git", "merge-base", "--is-ancestor", commit, "HEAD"], cwd=ROOT
        ).returncode
    ):
        raise PilotError("the protocol commit is not in the checked-out history")
    loaded = Path(drand.__file__).resolve()
    if ROOT / "src" not in loaded.parents:
        raise PilotError(f"refute is loaded from {loaded}, not from this checkout")
    in_commit = {p: hashlib.sha256(_in_commit(commit, p)).hexdigest() for p in PROTOCOL_FILES}
    on_disk = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in PROTOCOL_FILES}
    if in_commit != on_disk:
        changed = sorted(p for p in PROTOCOL_FILES if in_commit[p] != on_disk[p])
        raise PilotError("these files differ from the protocol commit: " + ", ".join(changed))
    return check_publication(
        commit,
        _push_runs(commit),
        drand.round_time(PILOT_ROUND),
        MARGIN,
        True,
        in_commit,
        in_commit,
        list(PROTOCOL_FILES),
        repository=REPOSITORY,
        workflow_path=WORKFLOW,
    )


def round_after(created_at: str) -> int:
    """The first drand round published at least MARGIN after a push run's creation."""
    created = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
    earliest = (created + MARGIN).timestamp()
    number = -(-(int(earliest) - drand.DRAND_GENESIS) // drand.DRAND_PERIOD) + 1
    while drand.round_time(number).timestamp() < earliest:
        number += 1
    return number


def first_with_need(commits: list[str], read) -> str | None:
    """The first commit, in history order, whose triage file records the need for the
    additional round; ``read(commit)`` gives that file's text, or None where it is absent."""
    for commit in commits:
        text = read(commit)
        if text is not None and ADDITIONAL_NEEDED in text:
            return commit
    return None


def _triage_text(commit: str) -> str | None:
    found = subprocess.run(
        ["git", "show", f"{commit}:{TRIAGE_FILE}"], cwd=ROOT, capture_output=True
    )
    return found.stdout.decode("utf-8") if found.returncode == 0 else None


def additional_round(protocol_commit: str, triage_commit: str) -> tuple[int, dict[str, Any]]:
    """The additional round is not fixed in advance (Codex review of the pilot protocol: a
    round known before the first triage ends could steer it). It is the first round
    published at least MARGIN after the push run of **the first commit of main after the
    protocol commit** whose triage file records the need; a later commit that only keeps
    that record is refused, so the commit, and the round, cannot be chosen."""
    history = _git("rev-list", "--reverse", "--first-parent", f"{protocol_commit}..HEAD").split()
    first = first_with_need(history, _triage_text)
    if first is None:
        raise PilotError(f"no commit after the protocol records the need in {TRIAGE_FILE}")
    if triage_commit != first:
        raise PilotError(f"the triage commit must be {first}, the first that records the need")
    runs = [
        r
        for r in _push_runs(triage_commit)
        if r.get("head_sha") == triage_commit
        and r.get("event") == "push"
        and r.get("path") == WORKFLOW
        and (r.get("repository") or {}).get("full_name") == REPOSITORY
        and (r.get("head_repository") or {}).get("full_name") == REPOSITORY
    ]
    if not runs:
        raise PilotError("no push run of the triage commit: the additional round is unknown")
    created = min(r["created_at"] for r in runs)
    return round_after(created), {"triage_commit": triage_commit, "push_run_created_at": created}


def _write_new(path: Path, text: str) -> None:
    # "x": the open itself refuses an existing file, so a second run never overwrites
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--protocol-commit", required=True)
    parser.add_argument("--frame", type=Path, required=True)
    parser.add_argument(
        "--additional-after",
        metavar="TRIAGE_COMMIT",
        help="draw the additional round, fixed by the push of this triage commit",
    )
    args = parser.parse_args(argv)

    proof = publication_proof(args.protocol_commit)
    snapshot = FrameSnapshot(FRAME_URL, FRAME_REVISION, FRAME_SHA256, args.frame)
    rows = load_frame(snapshot)
    filtered, steps = apply_filters(rows, DEFAULT_WINDOW)
    exclude: set[str] = set()
    additional: dict[str, Any] | None = None
    round_number = PILOT_ROUND
    if args.additional_after:
        round_number, additional = additional_round(args.protocol_commit, args.additional_after)
        if datetime.now(UTC) < drand.round_time(PILOT_ROUND):
            raise PilotError("the first pilot round is not published yet")
        first_seed, _ = drand.drand_seed(PILOT_ROUND)
        exclude = {r["paper_arxiv_id"] for r in draw_ids(filtered, first_seed, set())}
        committed = json.loads(_in_commit(args.additional_after, DRAW_FILE))
        if {p["arxiv_id"] for p in committed["papers"]} != exclude:
            raise PilotError("the committed first draw differs from its recomputation")
    if datetime.now(UTC) < drand.round_time(round_number):
        raise PilotError(f"round {round_number} is not published yet")
    suffix = "" if additional is None else "_additional"
    out_json = HERE / f"pilot_draw{suffix}.json"
    out_md = HERE / f"pilot_draw{suffix}.md"
    for path in (out_json, out_md):
        if path.exists():
            raise PilotError(f"{path.name} exists: the draw never overwrites")

    seed, beacon = drand.drand_seed(round_number)
    picked = draw_ids(filtered, seed, exclude)

    papers = []
    for position, row in enumerate(picked, start=1):
        arxiv_id = row["paper_arxiv_id"]
        meta, f_arxiv = read_arxiv(arxiv_id)
        repo, f_github = read_github(row["repo_url"], CACHE / f"readmes{suffix}", arxiv_id)
        candidate = {
            "position": position,
            "arxiv_id": arxiv_id,
            "repo_url": row["repo_url"],
            "framework": row.get("framework"),
            "arxiv": meta,
            "repository": repo,
            "transient_attempts": f_arxiv + f_github,
        }
        reason, evidence = mechanical(candidate)
        candidate["mechanical"] = {"reason": reason, "evidence": evidence}
        papers.append(candidate)
        print(f"{position:2d} {arxiv_id} {meta['primary_category']} {reason or '-'}", flush=True)

    record = {
        "protocol": "calibration/v0.3/pilot/PROTOCOL.md",
        "protocol_commit": args.protocol_commit,
        "publication_proof": proof.__dict__
        | {"inventory_hashes": [list(h) for h in proof.inventory_hashes]},
        "round": round_number,
        "additional": additional,
        "beacon": beacon,
        "seed": str(seed),
        "interpreter": drand.interpreter_record(),
        "frame": snapshot.record(),
        "filters": [
            {"name": s.name, "rows_after": s.rows_after, "papers_after": s.papers_after}
            for s in steps
        ],
        "excluded_first_round": sorted(exclude),
        "papers": papers,
        "drawn_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    lines = [
        f"# Pilot draw, round {round_number}",
        "",
        f"Seed `{seed}`; protocol commit `{args.protocol_commit}`; push run "
        f"{proof.run_id} created {proof.run_created_at}, first pilot round at "
        f"{proof.round_published_at}.",
        "",
        "| # | arXiv | Category | Repository | Mechanical |",
        "|---|---|---|---|---|",
    ]
    for p in papers:
        mech = p["mechanical"]["reason"] or "-"
        lines.append(
            f"| {p['position']} | {p['arxiv_id']} | {p['arxiv']['primary_category']} | "
            f"{p['repo_url']} | {mech} |"
        )
    _write_new(out_json, json.dumps(record, indent=2, ensure_ascii=False) + "\n")
    _write_new(out_md, "\n".join(lines) + "\n")
    print(f"written {out_json.name} and {out_md.name}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except PilotError as exc:
        print(f"STOPPED: {exc}", file=sys.stderr)
        sys.exit(2)
