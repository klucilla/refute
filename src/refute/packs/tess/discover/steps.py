"""The three steps of the v0.4 selection (calibration/v0.4/PROTOCOL.md, sections 4 and 12), so
that every line they execute is inside the lock's code hash; ``calibration/v0.4/select.py`` only
parses its arguments and calls these.

- ``freeze_step``: download the frozen inputs once (before the protocol commit), copy the small
  ones into the repository and write ``inputs.json``.
- ``archive_step``: archive every input to the Drive with a checked SHA-256 manifest (#172).
- ``select_step``: after the protocol commit is pushed, check that the code, the protocol and the
  inputs in the working tree are the bytes of that commit; then the round from its CI push run,
  the verified beacon and the selection; write the selection output.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import zipfile
from pathlib import Path
from typing import Any

from refute.drand import drand_seed, interpreter_record, round_after, round_time
from refute.packs.tess.discover import pilot
from refute.packs.tess.discover import selection as sel
from refute.packs.tess.discover.protocol import PROTOCOL_ID

STEP_DIR = Path("calibration/v0.4")
CACHE_DIR = Path(".cache/v04/inputs")
DRIVE = Path("K:/Meu Drive/Pessoal/Projetos/refute/arquivo-v0.4-inputs")
ZIP_NAME = "v0.4-inputs.zip"
# The paths whose bytes must be those of the protocol commit when the selection runs: the code,
# the protocol, the selection script, the frozen inputs and the files the exclusions read.
BOUND_PATHS = (
    "src",
    "pyproject.toml",
    "uv.lock",
    "calibration/v0.4/PROTOCOL.md",
    "calibration/v0.4/select.py",
    "calibration/v0.4/inputs.json",
    "calibration/v0.4/inputs",
    "calibration/targets.yaml",
    "calibration/v0.2/targets.yaml",
    "docs/validation/v0.2.1/reopen/stage-1/real-controls/result.json",
)


def freeze_step(root: Path) -> dict[str, Any]:
    inputs_json = root / STEP_DIR / "inputs.json"
    if inputs_json.exists():
        raise sel.SelectionError(f"{inputs_json} exists: the inputs are frozen once")
    cache = root / CACHE_DIR
    inputs = pilot.freeze(cache)
    for item in inputs["files"]:
        if item["in_git"]:
            target = root / STEP_DIR / "inputs" / item["name"]
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(cache / item["name"], target)
    inputs_json.write_text(json.dumps(inputs, indent=2) + "\n", encoding="utf-8", newline="\n")
    return inputs


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def archive_step(root: Path, drive: Path = DRIVE, script: Path | None = None) -> list[str]:
    """A stored zip of every frozen input (sorted members, a fixed date), a MANIFEST.sha256
    (every member, then the zip) and the calling script, copied to ``drive``; then checked from
    the Drive's copies. Nothing is deleted; an existing Drive folder is never replaced. Returns
    the problems (empty when every check passed)."""
    if drive.exists():
        raise sel.SelectionError(f"{drive} exists; not replaced")
    cache = root / CACHE_DIR
    inputs = json.loads((root / STEP_DIR / "inputs.json").read_text(encoding="utf-8"))
    pilot.verify_inputs(cache, inputs)
    local = root / ".cache" / "v04" / "inputs-archive"
    local.mkdir(parents=True, exist_ok=False)
    names = sorted(i["name"] for i in inputs["files"])
    expected = {i["name"]: i["sha256"] for i in inputs["files"]}
    zip_path = local / ZIP_NAME
    with zipfile.ZipFile(zip_path, "x", compression=zipfile.ZIP_STORED) as zf:
        for name in names:
            info = zipfile.ZipInfo(f"inputs/{name}", date_time=(2026, 10, 29, 0, 0, 0))
            zf.writestr(info, (cache / name).read_bytes())
    zip_sha = _sha(zip_path)
    lines = [f"{expected[n]}  inputs/{n}" for n in names] + [f"{zip_sha}  {ZIP_NAME}"]
    manifest = local / "MANIFEST.sha256"
    manifest.write_text(
        "# v0.4 frozen inputs (calibration/v0.4/inputs.json); issue #177\n"
        + "\n".join(lines)
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    drive.mkdir(parents=True)
    copies = [zip_path, manifest] + ([script] if script else [])
    for path in copies:
        shutil.copyfile(path, drive / path.name)
    problems = []
    if _sha(drive / ZIP_NAME) != zip_sha:
        problems.append("the zip's SHA-256 on the Drive differs")
    if (drive / "MANIFEST.sha256").read_bytes() != manifest.read_bytes():
        problems.append("the manifest on the Drive differs")
    with zipfile.ZipFile(drive / ZIP_NAME) as zf:
        if sorted(zf.namelist()) != [f"inputs/{n}" for n in names]:
            problems.append("the members on the Drive are not the inputs")
        for name in names:
            if hashlib.sha256(zf.read(f"inputs/{name}")).hexdigest() != expected[name]:
                problems.append(f"member differs: {name}")
    return problems


def _git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=False)


def bound_problems(root: Path, commit: str) -> list[str]:
    """Why the working tree is not the protocol commit's bytes for ``BOUND_PATHS`` (empty when
    it is): the commit must be an ancestor of HEAD, and those paths must have no difference from
    it, staged, unstaged or untracked."""
    problems = []
    if _git(root, "merge-base", "--is-ancestor", commit, "HEAD").returncode != 0:
        problems.append(f"{commit} is not an ancestor of HEAD")
    diff = _git(root, "diff", "--name-only", commit, "--", *BOUND_PATHS)
    if diff.returncode != 0:
        problems.append(f"git diff failed: {diff.stderr.strip()}")
    elif diff.stdout.strip():
        problems.append("changed since the protocol commit: " + ", ".join(diff.stdout.split()))
    untracked = _git(root, "ls-files", "--others", "--exclude-standard", "--", *BOUND_PATHS)
    if untracked.stdout.strip():
        problems.append("untracked under bound paths: " + ", ".join(untracked.stdout.split()))
    return problems


def target_entry(
    kind: str, tic: int, name: str | None, row: dict | None, evidence: dict, retrieved: str
) -> dict[str, Any]:
    """One entry of ``targets.yaml`` (``refute-tess-targets-1``); published values only for the
    controls, copied from their catalog row."""
    published: dict[str, Any] = {}
    source = {"name": "v0.4 pilot frame", "url": pilot.TARGET_LISTS_PAGE}
    if kind == "planet" and row:
        published = {
            "period_days": sel._float(row.get("pl_orbper")),
            "t0_bjd": sel._float(row.get("pl_tranmid")),
            "duration_hours": sel._float(row.get("pl_trandur")),
        }
        source = {"name": "NASA Exoplanet Archive pscomppars", "url": pilot.NEA_TAP}
    if kind == "false_positive" and row:
        published = {
            "period_days": sel._float(row.get("Period (days)")),
            "t0_bjd": sel._float(row.get("Epoch (BJD)")),
            "depth_ppm": sel._float(row.get("Depth (ppm)")),
            "duration_hours": sel._float(row.get("Duration (hours)")),
        }
        source = {"name": "ExoFOP TOI table", "url": pilot.TOI_URL}
    return {
        "key": f"TIC-{tic}",
        "tic_id": tic,
        "kind": kind,
        "name": name,
        "published": published,
        "source": {**source, "retrieved_utc": retrieved},
        "catalog": row or {},
        "mast": evidence,
        "fp_reason": (row or {}).get("TFOPWG Comment") if kind == "false_positive" else None,
    }


def targets_document(out: dict[str, Any], inputs: dict[str, Any]) -> dict[str, Any]:
    """The targets file of the claim: the two controls, then the 100 funnel stars in walk
    order (the run set is the first N of them)."""
    retrieved = {i["name"]: i["retrieved_utc"] for i in inputs["files"]}
    targets = []
    for kind, source in (("planet", "pscomppars.csv"), ("false_positive", "toi.csv")):
        control = out["controls"][kind]
        walk = control["attempts"][-1]["walk"]
        evidence = {d["tic_id"]: d["evidence"] for d in walk["decisions"]}
        tic = control["accepted"]
        targets.append(
            target_entry(
                kind, tic, control["name"], control["row"], evidence[tic], retrieved[source]
            )
        )
    evidence = {d["tic_id"]: d["evidence"] for d in out["funnel"]["decisions"]}
    for tic in out["funnel"]["accepted"]:
        targets.append(
            target_entry("exploration", tic, None, None, evidence[tic], retrieved["frame.csv"])
        )
    return {
        "schema": "refute-tess-targets-1",
        "generated_utc": pilot.utc_now(),
        "generator": "refute.packs.tess.discover.steps.select_step",
        "selection": {
            "round": out["round"],
            "protocol_commit": out["protocol_commit"],
            "file": "selection.json",
        },
        "targets": targets,
    }


def select_step(root: Path, commit: str) -> dict[str, Any]:
    """The selection after R_sel. Every bound path must be the protocol commit's bytes before
    the round's randomness is read."""
    if len(commit) != 40:
        raise sel.SelectionError("the protocol commit needs its full 40-character SHA")
    problems = bound_problems(root, commit)
    if problems:
        raise sel.SelectionError("; ".join(problems))
    inputs = json.loads((root / STEP_DIR / "inputs.json").read_text(encoding="utf-8"))
    created = pilot.push_run_created_at(commit)
    number = round_after(created)
    seed, beacon = drand_seed(number)
    out = pilot.run_selection(root / CACHE_DIR, inputs, beacon["randomness"], root)
    out.update(
        {
            "protocol": PROTOCOL_ID,
            "protocol_commit": commit,
            "push_run_created_at": created,
            "round": number,
            "round_time_utc": round_time(number).isoformat(),
            "beacon": beacon,
            "seed": str(seed),
            "interpreter": interpreter_record(),
        }
    )
    selection = root / STEP_DIR / "selection"
    selection.mkdir(parents=True, exist_ok=True)
    (selection / "selection.json").write_text(
        json.dumps(out, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    if out["complete"]:
        import yaml

        document = targets_document(out, inputs)
        (selection / "targets.yaml").write_text(
            yaml.safe_dump(document, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
            newline="\n",
        )
    return out


# --- the promotion record's provenance (protocol section 7) ---------------------------------

PROVENANCE_KEYS = (
    "results_commit",
    "entries_path",
    "n_k_commit",
    "n_k_path",
    "inputs_json",
    "inputs_dir",
    "stage1_run_dir",
)


def _show(root: Path, commit: str, path: str) -> bytes | None:
    done = subprocess.run(
        ["git", "show", f"{commit}:{path}"], cwd=root, capture_output=True, check=False
    )
    return done.stdout if done.returncode == 0 else None


def _ancestor(root: Path, older: str, newer: str) -> bool:
    return _git(root, "merge-base", "--is-ancestor", older, newer).returncode == 0


def n_k_problems(
    root: Path, provenance: dict[str, Any], run_commits: list[str]
) -> tuple[int | None, list[str]]:
    """The N of the committed (N, K) decision and why it cannot be used: the decision is read
    from its own commit (``n_k_commit``), unchanged since in HEAD; that commit precedes every
    stage-1 run (an ancestor of each run's commit); and its choice is what ``choose_n_k``
    gives on the costs it records."""
    from refute.packs.tess.discover import funnel

    commit, path = str(provenance["n_k_commit"]), str(provenance["n_k_path"])
    raw = _show(root, commit, path)
    if raw is None:
        return None, [f"the (N, K) decision is not in {commit}"]
    problems = []
    if _show(root, "HEAD", path) != raw:
        problems.append("the (N, K) decision changed after its commit")
    if not run_commits or any(not c or not _ancestor(root, commit, c) for c in run_commits):
        problems.append("the (N, K) decision was not committed before every stage-1 run")
    decision = json.loads(raw)
    try:
        again = funnel.choose_n_k(
            funnel.ControlCosts(**decision["inputs"]),
            float(decision["hours_used"]),
            float(decision["bytes_used"]),
        )
    except (KeyError, TypeError, ValueError) as exc:
        return None, [*problems, f"the (N, K) decision cannot be recomputed: {exc}"]
    if again["chosen"] != decision.get("chosen"):
        problems.append("the (N, K) choice is not what its recorded costs give")
    return (decision.get("chosen") or {}).get("N"), problems


def promotion_problems(
    record: dict[str, Any],
    root: Path,
    identity: dict[str, str],
    run_set: list[str],
    targets: dict[str, dict[str, Any]],
    inputs_sha256: str | None,
    offline: bool = False,
    push_run: Any = None,
) -> list[str]:
    """Everything a promotion record rests on, checked from its provenance before stage 2:

    - the stage-1 entries are recomputed from the stage-1 dossiers, each bound to the locked
      claim (``runs.dossier_problems``), with the deduplication from the frozen snapshots whose
      ``inputs.json`` is the claim's, and compared with the entries of the results commit (an
      ancestor of HEAD);
    - N is the committed (N, K) decision's, fixed before the stage-1 runs (``n_k_problems``);
    - a draw needs the beacon of R_prom: the round after the CI push run of the results commit,
      whose creation time the record carries (``push_run_created_at``); online it is checked
      against the GitHub API, offline the recorded time is used and no query is made.

    ``identity`` holds the locked ``claim_id``, ``claim_sha256`` and ``code_sha256``.
    ``push_run`` replaces ``pilot.push_run_created_at`` in tests."""
    from refute.drand import round_after
    from refute.packs.tess.discover import funnel, runs
    from refute.packs.tess.discover.protocol import PROMOTION

    provenance = record.get("provenance") or {}
    missing = [k for k in PROVENANCE_KEYS if not provenance.get(k)]
    if missing:
        return ["the record's provenance lacks " + ", ".join(missing)]
    commit = str(provenance["results_commit"])
    if not _ancestor(root, commit, "HEAD"):
        return [f"the results commit {commit} is not an ancestor of HEAD"]
    committed_bytes = _show(root, commit, provenance["entries_path"])
    committed = json.loads(committed_bytes)["entries"] if committed_bytes else None
    inputs_bytes = _show(root, "HEAD", provenance["inputs_json"])
    if inputs_bytes is None:
        return ["the inputs record is not committed"]
    if hashlib.sha256(inputs_bytes).hexdigest() != inputs_sha256:
        return ["the inputs record is not the one the claim names"]
    inputs = json.loads(inputs_bytes)
    run_dir = Path(provenance["stage1_run_dir"])
    indexes = pilot.catalog_indexes(Path(provenance["inputs_dir"]), inputs)
    recomputed = runs.stage1_entries(run_dir, run_set, indexes, targets, identity)
    run_commits = []
    for key in run_set:
        path = run_dir / key / "verdict.json"
        if path.is_file():
            prov = json.loads(path.read_text(encoding="utf-8")).get("provenance") or {}
            run_commits.append(str(prov.get("run_git_commit") or ""))
    n_k_chosen, problems = n_k_problems(root, provenance, run_commits)
    eligible = [e for e in recomputed if e["eligibility"]["eligible"]]
    expected_round = None
    if len(eligible) > PROMOTION.cap:
        created = provenance.get("push_run_created_at")
        if not created:
            return [*problems, "a draw needs the results commit's push run time in the record"]
        if not offline:
            live = (push_run or pilot.push_run_created_at)(commit)
            if live != created:
                return [*problems, "the recorded push run time is not the GitHub API's"]
        expected_round = round_after(str(created))
    return problems + funnel.verify_promotion(
        record,
        identity["claim_id"],
        identity["claim_sha256"],
        run_set,
        recomputed,
        committed,
        n_k_chosen,
        expected_round,
    )
