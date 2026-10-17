"""The v0.3 main walk and claim draw (calibration/v0.3/main/PROTOCOL.md; plan sections 4.3,
4.4, 5.2, 10.1 steps 5 to 8).

Run from a clean checkout of main. Two commands:

- ``--batch N``: after the paper round. Checks the publication of the protocol commit (the
  ``created_at`` of its GitHub Actions push run; the paper round is the first round
  published at least one hour after it), fetches and verifies the round, builds the walk
  order (filters 0 to 5 with the adjusted window, pilot papers removed, sorted by arXiv ID,
  shuffled with the seed), and reads candidates ``25 x (N - 1) + 1`` to ``25 x N`` of the
  walk: arXiv metadata, GitHub metadata, README and the files at the repository's root, with
  the mechanical rejections (category, keywords, repository unavailable) and the
  ``no_license`` signal (GitHub reports no license and no license-like file is at the root;
  a signal only: the agent proposes the decision after reading the README). Batch N needs
  batch N - 1 committed; at most 12 batches (300 candidates, the stop rule).
- ``--claims-after COMMIT``: after the claim round. The claim round is the first round
  published at least one hour after the push run of the first commit of main after the
  protocol commit that adds ``inventories/SHA256SUMS``; ``COMMIT`` must be that commit.
  Draws the claims of every published inventory (``draw_published_claims``).

Outputs are created exclusively (never overwritten). No repository code runs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import urllib.error
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "calibration" / "v0.3" / "pilot"))

import select_pilot as sp  # noqa: E402

from refute import drand  # noqa: E402
from refute.selection.filters import (  # noqa: E402
    Window,
    apply_filters,
    category_allowed,
    keyword_hits,
)
from refute.selection.frame import FrameSnapshot, load_frame  # noqa: E402
from refute.selection.inventory import draw_published_claims, draw_record  # noqa: E402
from refute.selection.publication import check_publication  # noqa: E402

CACHE = ROOT / ".cache" / "round6" / "main"
# the adjustment add-cs-ai of the pilot (pilot_triage.md, approved on 2026-10-17)
WINDOW = Window("2023-01", "2025-06")
CATEGORIES = ("cs.LG", "stat.ML", "cs.AI")
BATCH = 25
MAX_BATCHES = 12  # 300 candidates: the stop rule of the protocol
PILOT_DRAWS = (
    "calibration/v0.3/pilot/pilot_draw.json",
    "calibration/v0.3/pilot/pilot_draw_additional.json",
)
INVENTORY_SUMS = "calibration/v0.3/main/inventories/SHA256SUMS"
# the 5 papers of the main sample, written with the approved selection log (a JSON list of
# arXiv IDs, in walk order); the claim draw needs exactly their 5 inventories
MAIN_SAMPLE = "calibration/v0.3/main/main_sample.json"
LICENSE_LIKE = ("licen", "copying", "notice")
PROTOCOL_FILES = (
    "calibration/v0.3/main/PROTOCOL.md",
    "calibration/v0.3/main/select_main.py",
    "calibration/v0.3/pilot/select_pilot.py",
    *PILOT_DRAWS,
    "src/refute/__init__.py",
    "src/refute/drand.py",
    "src/refute/selection/__init__.py",
    "src/refute/selection/frame.py",
    "src/refute/selection/filters.py",
    "src/refute/selection/walk.py",
    "src/refute/selection/publication.py",
    "src/refute/selection/inventory.py",
    "src/refute/core/__init__.py",
    "src/refute/core/canonical.py",
    "src/refute/core/hashing.py",
    "pyproject.toml",
    "uv.lock",
)


class MainError(Exception):
    """The walk or the claim draw cannot go on; the maintainer decides."""


# ---- pure parts (tested offline) ----------------------------------------------------------


def mechanical(candidate: dict[str, Any]) -> tuple[str | None, str]:
    """The mechanical rejection of a walked paper, if any: (reason, evidence)."""
    meta = candidate["arxiv"]
    if not category_allowed(meta["primary_category"], CATEGORIES):
        return "category_outside_list", f"arXiv primary category {meta['primary_category']}"
    hits = keyword_hits(meta["title"], meta["abstract"], sp.KEYWORDS)
    if hits:
        return "out_of_scope", "keywords in title or abstract: " + ", ".join(hits)
    repo = candidate["repository"]
    if repo.get("host") == "github" and not repo.get("exists"):
        return "repository_unavailable", "the GitHub API answers 404 for the repository"
    if repo.get("archived"):
        return "repository_unavailable", "the repository is archived on GitHub"
    return None, ""


def license_signal(repo: dict[str, Any], root_names: list[str] | None) -> bool:
    """The no_license signal: GitHub reports no license and no license-like file is at the
    repository's root. A signal only, never a decision."""
    if repo.get("host") != "github" or not repo.get("exists") or root_names is None:
        return False
    if repo.get("license_spdx"):
        return False
    return not any(k in name.lower() for name in root_names for k in LICENSE_LIKE)


def walk_order(rows: list[dict[str, Any]], seed: int, exclude: set[str]) -> list[dict[str, Any]]:
    """The whole walk: the filtered frame sorted by arXiv ID, shuffled with the seed, the
    pilot papers removed."""
    order = drand.shuffled(rows, seed, key=lambda r: r["paper_arxiv_id"])
    return [r for r in order if r["paper_arxiv_id"] not in exclude]


def batch_slice(n: int) -> slice:
    if not 1 <= n <= MAX_BATCHES:
        raise MainError(f"batch {n}: batches are 1 to {MAX_BATCHES} (the stop rule)")
    return slice(BATCH * (n - 1), BATCH * n)


def first_with_file(commits: list[str], has) -> str | None:
    """The first commit, in history order, that holds ``INVENTORY_SUMS``."""
    for commit in commits:
        if has(commit):
            return commit
    return None


def expected_inventories(sample: Any) -> list[str]:
    """The inventory files the claim draw needs: one per paper of the main sample, exactly
    5 (Codex review of the protocol: the set is checked before the proof)."""
    if (
        not isinstance(sample, list)
        or len(sample) != 5
        or len(set(sample)) != 5
        or not all(isinstance(a, str) and re.fullmatch(r"\d{4}\.\d{4,5}", a) for a in sample)
    ):
        raise MainError("the main sample is a list of 5 distinct new-style arXiv IDs")
    return sorted(f"{a}.json" for a in sample)


def proof_record(proof: Any) -> dict[str, Any]:
    return proof.__dict__ | {"inventory_hashes": [list(h) for h in proof.inventory_hashes]}


def parse_sums(text: str) -> dict[str, str]:
    """``<sha256>  <file name>`` lines -> {file name: sha256}."""
    out = {}
    for line in text.splitlines():
        if line.strip():
            digest, name = line.split(maxsplit=1)
            out[name.strip()] = digest
    return out


# ---- network and git (run only by the protocol's commands) --------------------------------


def _clean() -> None:
    if sp._git("status", "--porcelain"):
        raise MainError("the working tree is not clean")


def _files_unchanged(commit: str) -> dict[str, str]:
    in_commit = {p: hashlib.sha256(sp._in_commit(commit, p)).hexdigest() for p in PROTOCOL_FILES}
    on_disk = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in PROTOCOL_FILES}
    if in_commit != on_disk:
        changed = sorted(p for p in PROTOCOL_FILES if in_commit[p] != on_disk[p])
        raise MainError("these files differ from the protocol commit: " + ", ".join(changed))
    loaded = Path(drand.__file__).resolve()
    if ROOT / "src" not in loaded.parents:
        raise MainError(f"refute is loaded from {loaded}, not from this checkout")
    return in_commit


def _push_created(commit: str) -> tuple[list, str]:
    runs = [
        r
        for r in sp._push_runs(commit)
        if r.get("head_sha") == commit and r.get("event") == "push" and r.get("path") == sp.WORKFLOW
    ]
    if not runs:
        raise MainError(f"no push run of {commit}: the round is unknown")
    return runs, min(r["created_at"] for r in runs)


def paper_round(protocol_commit: str) -> tuple[int, Any]:
    """The paper round, by the protocol's rule, and its publication proof."""
    _clean()
    if subprocess.run(
        ["git", "merge-base", "--is-ancestor", protocol_commit, "HEAD"], cwd=ROOT
    ).returncode:
        raise MainError("the protocol commit is not in the checked-out history")
    files = _files_unchanged(protocol_commit)
    runs, created = _push_created(protocol_commit)
    number = sp.round_after(created)
    proof = check_publication(
        protocol_commit, runs, drand.round_time(number), sp.MARGIN, True, files, files,
        list(PROTOCOL_FILES), repository=sp.REPOSITORY, workflow_path=sp.WORKFLOW,
    )  # fmt: skip
    return number, proof


def root_names(full_name: str, commit: str) -> tuple[list[str] | None, list]:
    """The names at the repository's root, and the transient attempts. An answer of the API
    with a client error (4xx: the tree cannot be listed) gives no signal (None); transient
    errors are retried, and when the attempts are exhausted the walk stops (Codex review of
    the protocol: an unread candidate is never passed over)."""
    url = f"https://api.github.com/repos/{full_name}/git/trees/{commit}"
    try:
        tree, failures = sp._retried(
            lambda: json.loads(sp._request(url)), f"GitHub {full_name} tree"
        )
    except urllib.error.HTTPError as exc:
        if 400 <= exc.code < 500:
            return None, []
        raise
    return [t["path"] for t in tree.get("tree", [])], failures


def run_batch(protocol_commit: str, frame: Path, n: int) -> None:
    span = batch_slice(n)
    if n > 1:
        previous = f"calibration/v0.3/main/main_walk_batch_{n - 1:02d}.json"
        if subprocess.run(["git", "cat-file", "-e", f"HEAD:{previous}"], cwd=ROOT).returncode:
            raise MainError(f"batch {n - 1} is not committed")
    number, proof = paper_round(protocol_commit)
    if datetime.now(UTC) < drand.round_time(number):
        raise MainError(f"round {number} is not published yet")
    out_json = HERE / f"main_walk_batch_{n:02d}.json"
    out_md = HERE / f"main_walk_batch_{n:02d}.md"
    for p in (out_json, out_md):
        if p.exists():
            raise MainError(f"{p.name} exists: the walk never overwrites")
    snapshot = FrameSnapshot(sp.FRAME_URL, sp.FRAME_REVISION, sp.FRAME_SHA256, frame)
    rows = load_frame(snapshot)
    exclude: set[str] = set()
    for path in PILOT_DRAWS:
        exclude |= {
            p["arxiv_id"] for p in json.loads(sp._in_commit(protocol_commit, path))["papers"]
        }
    # filter 7 inside apply_filters, so its count is recorded (Codex review of the protocol)
    filtered, steps = apply_filters(rows, WINDOW, exclude)
    seed, beacon = drand.drand_seed(number)
    order = walk_order(filtered, seed, exclude)
    candidates = []
    for position, row in enumerate(order[span], start=span.start + 1):
        arxiv_id = row["paper_arxiv_id"]
        meta, f_arxiv = sp.read_arxiv(arxiv_id)
        repo, f_github = sp.read_github(row["repo_url"], CACHE / "readmes", arxiv_id)
        names, f_tree = (
            root_names(repo["full_name"], repo["head_commit"]) if repo.get("exists") else (None, [])
        )
        candidate = {
            "position": position,
            "arxiv_id": arxiv_id,
            "repo_url": row["repo_url"],
            "arxiv": meta,
            "repository": repo | {"root_names": names},
            "transient_attempts": f_arxiv + f_github + f_tree,
        }
        reason, evidence = mechanical(candidate)
        candidate["mechanical"] = {"reason": reason, "evidence": evidence}
        candidate["no_license_signal"] = reason is None and license_signal(repo, names)
        candidates.append(candidate)
        flag = reason or ("no_license?" if candidate["no_license_signal"] else "-")
        print(f"{position:3d} {arxiv_id} {meta['primary_category']} {flag}", flush=True)
    record = {
        "protocol": "calibration/v0.3/main/PROTOCOL.md",
        "protocol_commit": protocol_commit,
        "publication_proof": proof_record(proof),
        "round": number,
        "beacon": beacon,
        "seed": str(seed),
        "interpreter": drand.interpreter_record(),
        "frame": snapshot.record(),
        "window": {"first": WINDOW.first, "last": WINDOW.last},
        "categories": list(CATEGORIES),
        "filters": [
            {"name": s.name, "rows_after": s.rows_after, "papers_after": s.papers_after}
            for s in steps
        ],
        "pilot_papers_removed": sorted(exclude),
        "walk_length": len(order),
        "batch": n,
        "candidates": candidates,
        "read_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }  # fmt: skip
    lines = [
        f"# Main walk, batch {n} (positions {span.start + 1} to {span.stop})",
        "",
        f"Round {number}; seed `{seed}`; protocol commit `{protocol_commit}`; push run "
        f"{proof.run_id} created {proof.run_created_at}; "
        f"round published {proof.round_published_at}.",
        "",
        "| # | arXiv | Category | Repository | Mechanical | no_license signal |",
        "|---|---|---|---|---|---|",
    ]
    for c in candidates:
        lines.append(
            f"| {c['position']} | {c['arxiv_id']} | {c['arxiv']['primary_category']} | "
            f"{c['repo_url']} | {c['mechanical']['reason'] or '-'} | "
            f"{'yes' if c['no_license_signal'] else '-'} |"
        )
    sp._write_new(out_json, json.dumps(record, indent=2, ensure_ascii=False) + "\n")
    sp._write_new(out_md, "\n".join(lines) + "\n")
    print(f"written {out_json.name} and {out_md.name}")


def run_claims(protocol_commit: str, inventory_commit: str) -> None:
    _clean()
    history = sp._git("rev-list", "--reverse", "--first-parent", f"{protocol_commit}..HEAD").split()

    def has(commit: str) -> bool:
        return not subprocess.run(
            ["git", "cat-file", "-e", f"{commit}:{INVENTORY_SUMS}"], cwd=ROOT
        ).returncode

    first = first_with_file(history, has)
    if first is None or first != inventory_commit:
        raise MainError(
            f"the inventory commit must be {first}, the first that adds {INVENTORY_SUMS}"
        )
    _files_unchanged(protocol_commit)
    runs, created = _push_created(inventory_commit)
    number = sp.round_after(created)
    if datetime.now(UTC) < drand.round_time(number):
        raise MainError(f"claim round {number} is not published yet")
    sums = parse_sums(sp._in_commit(inventory_commit, INVENTORY_SUMS).decode("utf-8"))
    sample = json.loads(sp._in_commit(inventory_commit, MAIN_SAMPLE))
    required = expected_inventories(sample)
    if set(sums) != set(required):
        raise MainError(f"SHA256SUMS lists {sorted(sums)}, not the main sample's {required}")
    folder = "calibration/v0.3/main/inventories/"
    files = {
        n: hashlib.sha256(sp._in_commit(inventory_commit, folder + n)).hexdigest() for n in sums
    }
    for name in required:
        inv = json.loads(sp._in_commit(inventory_commit, folder + name))
        if f"{inv['paper']['arxiv_id']}.json" != name:
            raise MainError(f"{name} is the inventory of {inv['paper']['arxiv_id']}")
    proof = check_publication(
        inventory_commit, runs, drand.round_time(number), sp.MARGIN, True, files, sums,
        required, repository=sp.REPOSITORY, workflow_path=sp.WORKFLOW,
    )  # fmt: skip
    seed, beacon = drand.drand_seed(number)
    draws = []
    for name in sorted(sums):
        inv = json.loads(sp._in_commit(inventory_commit, folder + name))
        draws.append(draw_record(draw_published_claims(inv, proof, number, beacon)))
    out = HERE / "claim_draw.json"
    record = {
        "protocol_commit": protocol_commit,
        "inventory_commit": inventory_commit,
        "round": number,
        "beacon": beacon,
        "seed": str(seed),
        "publication_proof": proof_record(proof),
        "draws": draws,
        "drawn_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }  # fmt: skip
    sp._write_new(out, json.dumps(record, indent=2) + "\n")
    print(f"written {out.name}: round {number}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--protocol-commit", required=True)
    parser.add_argument("--frame", type=Path)
    parser.add_argument("--batch", type=int)
    parser.add_argument("--claims-after", metavar="INVENTORY_COMMIT")
    args = parser.parse_args(argv)
    if args.claims_after:
        run_claims(args.protocol_commit, args.claims_after)
    elif args.batch and args.frame:
        run_batch(args.protocol_commit, args.frame, args.batch)
    else:
        parser.error("give --frame with --batch, or --claims-after")
    return 0


if __name__ == "__main__":
    sys.exit(main())
