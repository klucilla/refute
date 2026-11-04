"""C3 of the v0.5 calibration: the frozen inputs and the selection of the real controls
(calibration/v0.5/PROTOCOL.md, sections 2, 5 and 6).

- ``freeze``: before the protocol commit, one attempt downloads the target lists page (for the
  highest listed sector), finds S_max from MAST, downloads the ExoFOP TOI table and the NASA
  Exoplanet Archive ``pscomppars`` table and the Gaia DR3 EB asset of v0.2.0 (checked against its
  SHA-256 and row count), and copies the TESS-EB static edition (checked against its raw and
  content SHA-256; never redistributed, #33). Each file's URL, retrieval time, size
  and SHA-256 go into ``inputs.json``, with the code hash (``refute-code-1``) of the tree that
  freezes; a file above 5 MB never enters git.
- ``run_selection``: after R_c3, two pools (confirmed planets from ``pscomppars``; eclipsing-binary
  false positives: TOI rows with TFOPWG disposition ``FP`` whose TIC is in TESS-EB), each without
  the targets of v0.1 to v0.4, sorted by TIC ID, shuffled by its R_c3 seed and walked (the v0.4
  domain D-1 to D-9, live MAST and TIC queries) until 8 + 3 stars are accepted: the first 8 run,
  the next 3 are the ordered reserves. Every decision is in the ledger.
- ``select_step``: refuses unless every bound path is the protocol commit's bytes, then the round
  from the commit's CI push run, the verified beacon and the selection.

The v0.4 functions are reused unchanged (``discover.selection``, ``discover.pilot``).
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Any

from refute.drand import shuffled
from refute.packs.tess.calib05.values import C3, PROTOCOL_ID, STEP_DIR
from refute.packs.tess.discover import pilot
from refute.packs.tess.discover import selection as sel
from refute.packs.tess.discover.protocol import DOMAIN
from refute.packs.tess.discover.transforms import stream_seed
from refute.selection.walk import RetryPolicy

ATTEMPTS_DIR = Path(".cache/v05/inputs-attempts")
SELECTION_DIR = "selection"
POOLS = (("planet", "planet-pool"), ("false_positive", "eb-fp-pool"))
# The paths whose bytes must be the protocol commit's when the selection runs.
BOUND_PATHS = (
    "src",
    "pyproject.toml",
    "uv.lock",
    f"{STEP_DIR}/PROTOCOL.md",
    f"{STEP_DIR}/run_calibration.py",
    f"{STEP_DIR}/inputs.json",
    f"{STEP_DIR}/inputs",
    "calibration/targets.yaml",
    "calibration/v0.2/targets.yaml",
    "docs/validation/v0.2.1/reopen/stage-1/real-controls/result.json",
    "calibration/v0.4/selection/targets.yaml",
)


def policy() -> RetryPolicy:
    return RetryPolicy(C3.retry_attempts, C3.retry_backoff_seconds)


# --- the frozen inputs ------------------------------------------------------------------------


def code_record(root: Path) -> dict[str, Any]:
    """The code hash (``refute-code-1``) of the tree that freezes the inputs; the lock at S4 must
    carry the same."""
    from refute.core.codehash import compute_code_hash

    code = compute_code_hash(Path(root))
    return {"algorithm": code.algorithm, "sha256": code.sha256, "files": len(code.files)}


def freeze(
    out_dir: Path,
    root: Path,
    fetch: Callable[[str], bytes] = pilot.download,
    now: Callable[[], str] = pilot.utc_now,
    sector_count: Callable[[int], int] | None = None,
    sleep: Callable[[float], None] | None = None,
    tess_eb_path: Path | None = None,
    tess_eb: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """One freeze attempt in ``out_dir`` (which must not exist); returns ``inputs.json``'s
    content, written there when every input arrived. The TESS-EB static edition is read and
    checked before any download."""
    attempt = pilot._AttemptLog(out_dir, fetch, now, sleep)
    attempt.event({"event": "start", "out_dir": attempt.out_dir.as_posix()})
    edition = tess_eb or pilot.TESS_EB_STATIC
    eb_static = pilot._static_edition(attempt, tess_eb_path, edition)
    page = attempt.keep(
        "target_lists.html", pilot.TARGET_LISTS_PAGE, attempt.get(pilot.TARGET_LISTS_PAGE)
    ).decode("utf-8")
    s_max_record = pilot.latest_spoc_sector(
        pilot.highest_listed_sector(page),
        sector_count or pilot.spoc_sector_count,
        on_query=lambda q: attempt.event({"event": "s_max_query", **q}),
    )
    attempt.event({"event": "s_max", **s_max_record})
    attempt.keep("toi.csv", pilot.TOI_URL, attempt.get(pilot.TOI_URL))
    attempt.keep("pscomppars.csv", pilot.nea_url(), attempt.get(pilot.nea_url()))
    # the TESS-EB static edition and the Gaia DR3 EB asset of v0.2.0 (checked against its
    # SHA-256 and row count), as v0.4 froze them: the claim's catalog attachments read both
    pilot._keep_catalog_editions(attempt, edition, eb_static)
    return attempt.inputs(
        int(s_max_record["s_max"]),
        s_max_record,
        0,
        schema="refute-tess-calib05-inputs-1",
        protocol=PROTOCOL_ID,
        code=code_record(root),
    )


def next_attempt(root: Path) -> Path:
    base = Path(root) / ATTEMPTS_DIR
    numbers = [
        int(p.name.split("-")[1])
        for p in (base.iterdir() if base.is_dir() else [])
        if p.is_dir() and p.name.startswith("attempt-") and p.name.split("-")[1].isdigit()
    ]
    return base / f"attempt-{max(numbers, default=0) + 1:02d}"


def cache_dir(root: Path, inputs: dict[str, Any]) -> Path:
    attempt = inputs.get("attempt")
    if not attempt:
        raise sel.SelectionError("inputs.json names no freeze attempt")
    return Path(root) / ATTEMPTS_DIR / str(attempt)


def freeze_step(root: Path, **kwargs: Any) -> dict[str, Any]:
    """One freeze attempt; on success the small inputs are copied to ``calibration/v0.5/inputs``
    and ``inputs.json`` is written last. Refused when ``inputs.json`` or ``inputs`` exists."""
    root = Path(root)
    step = root / STEP_DIR
    if (step / "inputs.json").exists() or (step / "inputs").exists():
        raise sel.SelectionError("the inputs are frozen once; inputs.json or inputs exists")
    kwargs.setdefault("tess_eb_path", root / pilot.TESS_EB_STATIC["path"])
    cache = next_attempt(root)
    inputs = freeze(cache, root, **kwargs)
    inputs["pool_preview"] = pool_preview(root, cache)
    for item in inputs["files"]:
        if item["in_git"]:
            target = step / "inputs" / item["name"]
            target.parent.mkdir(parents=True, exist_ok=True)
            with open(target, "xb") as handle:
                handle.write((cache / item["name"]).read_bytes())
    with open(step / "inputs.json", "x", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(inputs, indent=2) + "\n")
    return inputs


# --- known targets and pools ------------------------------------------------------------------


def known_targets(root: Path) -> dict[int, str]:
    """The targets of v0.1 to v0.4, development targets included: v0.1, v0.2 and the v0.2.1
    gate-3b planets (``discover.selection.known_targets``), and every target of the v0.4 claim
    (its two controls and its 100 funnel stars, ``calibration/v0.4/selection/targets.yaml``)."""
    import yaml

    out = dict(sel.known_targets(Path(root)))
    doc = yaml.safe_load(
        (Path(root) / "calibration/v0.4/selection/targets.yaml").read_text(encoding="utf-8")
    )
    for target in doc["targets"]:
        out.setdefault(int(target["tic_id"]), f"v0.4 {target['kind']}")
    return out


def pools(
    toi: list[dict[str, str]],
    pscomppars: list[dict[str, str]],
    eb_tics: set[int],
    known: set[int],
) -> dict[str, list[sel.PoolRow]]:
    """The two C3 pools, sorted by TIC ID, without the known targets."""
    planet_tics = {t for t in (sel.parse_tic(r.get("tic_id")) for r in pscomppars) if t}
    planets = sel.planet_pool(pscomppars, C3.planet_min_depth_percent)
    ebs = [p for p in sel.fp_pool(toi, planet_tics, C3.fp_min_depth_ppm) if p.tic_id in eb_tics]
    return {
        "planet": [p for p in planets if p.tic_id not in known],
        "false_positive": [p for p in ebs if p.tic_id not in known],
    }


def _frozen(inputs_dir: Path, inputs: dict[str, Any], name: str) -> bytes:
    recorded = {i["name"]: i["sha256"] for i in inputs["files"]}
    data = (Path(inputs_dir) / name).read_bytes()
    if name not in recorded or hashlib.sha256(data).hexdigest() != recorded[name]:
        raise sel.SelectionError(f"{name} does not match its recorded SHA-256")
    return data


def read_pools(root: Path, inputs_dir: Path, inputs: dict[str, Any]):
    toi = sel.toi_rows(_frozen(inputs_dir, inputs, "toi.csv"))
    pscomppars = sel.pscomppars_rows(_frozen(inputs_dir, inputs, "pscomppars.csv"))
    eb_tics = sel.tess_eb_tics(_frozen(inputs_dir, inputs, "tess_eb.tsv"))
    known = known_targets(root)
    return pools(toi, pscomppars, eb_tics, set(known)), known


def pool_preview(root: Path, cache: Path) -> dict[str, int]:
    """The size of each pool before the round (no seed involved), written into ``inputs.json``."""
    toi = sel.toi_rows((cache / "toi.csv").read_bytes())
    pscomppars = sel.pscomppars_rows((cache / "pscomppars.csv").read_bytes())
    eb_tics = sel.tess_eb_tics((cache / "tess_eb.tsv").read_bytes())
    built = pools(toi, pscomppars, eb_tics, set(known_targets(root)))
    return {kind: len(rows) for kind, rows in built.items()}


def pool_order(pool: list[sel.PoolRow], randomness_hex: str, label: str) -> list[int]:
    """``int(sha256(randomness_hex + "|v0.5|c3|<label>"), 16)``, then sorted by TIC ID and
    shuffled (``refute.drand.shuffled``)."""
    seed = stream_seed(randomness_hex, "v0.5", "c3", label)
    return shuffled([p.tic_id for p in pool], seed, key=lambda tic: tic)


# --- the selection ----------------------------------------------------------------------------


def run_selection(
    inputs_dir: Path,
    inputs: dict[str, Any],
    randomness_hex: str,
    root: Path,
    triage_fn: Callable[[int, Any, int], tuple[bool, str, dict[str, Any]]] = pilot.triage,
    sleep: Callable[[float], None] | None = None,
) -> dict[str, Any]:
    """Both pools walked until ``count + reserves`` stars are accepted (protocol section 5);
    only products up to the frozen S_max count."""
    import time

    sleep = sleep or time.sleep
    s_max = int(inputs["s_max"])
    built, known = read_pools(root, inputs_dir, inputs)
    out: dict[str, Any] = {}
    for kind, label in POOLS:
        count = C3.planets if kind == "planet" else C3.false_positives
        pool = built[kind]
        walked = sel.walk(
            kind,
            pool_order(pool, randomness_hex, label),
            lambda tic: triage_fn(tic, DOMAIN, s_max),
            count + C3.reserves,
            policy(),
            sleep,
        )
        accepted = walked.accepted
        rows = {p.tic_id: p for p in pool}
        out[kind] = {
            "pool_size": len(pool),
            "needed": count,
            "reserves_needed": C3.reserves,
            "walk": walked.to_dict(),
            "chosen": accepted[:count],
            "reserves": accepted[count : count + C3.reserves],
            "rows": {str(t): rows[t].row for t in accepted},
            "names": {str(t): rows[t].name for t in accepted},
            "stopped": walked.stopped,
            "short": max(0, count - len(accepted)),
        }
    return {
        "schema": "refute-tess-calib05-c3-selection-1",
        "randomness": randomness_hex,
        "s_max": s_max,
        "known_targets": {str(k): v for k, v in sorted(known.items())},
        "pools": out,
        "complete": all(not p["stopped"] and len(p["chosen"]) == p["needed"] for p in out.values()),
    }


def ledger(selection: dict[str, Any]) -> list[dict[str, Any]]:
    """Every walked star of both pools, in walk order, with its decision and reason, and its
    place (``chosen``, ``reserve <n>``, or none)."""
    rows = []
    for kind, pool in selection["pools"].items():
        chosen = set(pool["chosen"])
        reserves = {t: i + 1 for i, t in enumerate(pool["reserves"])}
        for d in pool["walk"]["decisions"]:
            place = None
            if d["tic_id"] in chosen:
                place = "chosen"
            elif d["tic_id"] in reserves:
                place = f"reserve {reserves[d['tic_id']]}"
            rows.append(
                {
                    "pool": kind,
                    "position": d["position"],
                    "tic_id": d["tic_id"],
                    "decision": d["decision"],
                    "reason": d["reason"],
                    "place": place,
                }
            )
    return rows


def targets_document(selection: dict[str, Any], inputs: dict[str, Any]) -> dict[str, Any]:
    """The targets of the C3 claim: per pool the chosen stars, then the reserves, in walk
    order; published values copied from their catalog row with their source (v0.5, #194)."""
    from refute.packs.tess.discover.steps import published_period_v05, target_entry

    retrieved = {i["name"]: i["retrieved_utc"] for i in inputs["files"]}
    targets = []
    for kind, source_file, source_name in (
        ("planet", "pscomppars.csv", "NASA Exoplanet Archive pscomppars"),
        ("false_positive", "toi.csv", "ExoFOP TOI table"),
    ):
        pool = selection["pools"][kind]
        evidence = {d["tic_id"]: d["evidence"] for d in pool["walk"]["decisions"]}
        for place, tics in (("chosen", pool["chosen"]), ("reserve", pool["reserves"])):
            for order, tic in enumerate(tics, start=1):
                row = pool["rows"][str(tic)]
                entry = target_entry(
                    kind, tic, pool["names"][str(tic)], row, evidence[tic], retrieved[source_file]
                )
                period, note = published_period_v05(source_name, row)
                entry["published"] = {**entry["published"], **period}
                entry["notes"] = note
                entry["c3_place"] = place if place == "chosen" else f"reserve {order}"
                if kind == "false_positive":
                    entry["fp_class"] = "eclipsing_binary (TOI FP with TIC in TESS-EB)"
                targets.append(entry)
    return {
        "schema": "refute-tess-targets-1",
        "generated_utc": pilot.utc_now(),
        "generator": "refute.packs.tess.calib05.c3select.select_step",
        "selection": {
            "round": selection.get("round"),
            "protocol_commit": selection.get("protocol_commit"),
            "file": "selection.json",
        },
        "targets": targets,
    }


def _git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=False)


def bound_problems(root: Path, commit: str) -> list[str]:
    """Why the working tree is not the protocol commit's bytes for ``BOUND_PATHS``."""
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


SELECTION_ATTEMPTS = Path(".cache/v05/selection-attempts")


def freeze_commit(root: Path) -> str:
    """The designated freeze commit: the one commit that added both ``inputs.json`` and this
    protocol (any other commit, even with the same bytes, would have another CI push run and so
    another R_c3)."""
    added = {}
    for path in (f"{STEP_DIR}/inputs.json", f"{STEP_DIR}/PROTOCOL.md"):
        out = _git(root, "log", "--diff-filter=A", "--format=%H", "--", path)
        if out.returncode != 0:
            raise sel.SelectionError(f"git log failed: {out.stderr.strip()}")
        added[path] = out.stdout.split()
    commits = {c for found in added.values() for c in found}
    if len(commits) != 1 or any(len(found) != 1 for found in added.values()):
        raise sel.SelectionError(f"no single commit added the protocol and its inputs: {added}")
    return commits.pop()


def _attempt(root: Path, approval_url: str | None) -> Path:
    """A new, exclusive selection attempt folder, reserved before any network access. After an
    attempt that read the round's beacon (its ``round.json``), a new one needs the URL of its
    approval recorded in an issue; an attempt that stopped before (the round not yet published,
    a GitHub error) revealed nothing of the draw."""
    from refute.packs.tess.discover.steps import APPROVAL_URL

    base = Path(root) / SELECTION_ATTEMPTS
    earlier = sorted(p for p in base.iterdir()) if base.is_dir() else []
    revealed = [p.name for p in earlier if (p / "round.json").exists()]
    if revealed and (approval_url is None or not APPROVAL_URL.fullmatch(approval_url)):
        raise sel.SelectionError(
            f"earlier attempts read the beacon {revealed}: a new one needs its approval URL"
        )
    folder = base / f"attempt-{len(earlier) + 1:02d}"
    folder.mkdir(parents=True, exist_ok=False)
    with open(folder / "attempt.json", "x", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps({"approval": approval_url, "utc": pilot.utc_now()}) + "\n")
    return folder


def _logged(triage_fn, folder: Path):
    """``triage_fn`` that appends each answer to the attempt's ``decisions.jsonl`` as it comes."""

    def triage(tic: int, domain: Any, s_max: int):
        ok, reason, evidence = triage_fn(tic, domain, s_max)
        with open(folder / "decisions.jsonl", "a", encoding="utf-8", newline="\n") as log:
            line = {"tic_id": tic, "accepted": ok, "reason": reason, "evidence": evidence}
            log.write(json.dumps(line, sort_keys=True, default=str) + "\n")
        return ok, reason, evidence

    return triage


def select_step(
    root: Path, commit: str, approval_url: str | None = None, **kwargs: Any
) -> dict[str, Any]:
    """The C3 selection after R_c3. Before any network access: ``commit`` must be the designated
    freeze commit, every bound path its bytes, the tree's code hash the frozen one, no selection
    output may exist, and a new attempt folder is reserved; then the round, the beacon and the
    walks, each answer logged as it comes. Writes ``selection/selection.json``,
    ``selection/ledger.json`` and (when complete) ``selection/targets.yaml``, each exclusively."""
    import yaml

    from refute.drand import drand_seed, interpreter_record, round_after, round_time

    root = Path(root)
    if len(commit) != 40:
        raise sel.SelectionError("the protocol commit needs its full 40-character SHA")
    designated = freeze_commit(root)
    if commit != designated:
        raise sel.SelectionError(f"the freeze commit is {designated}, not {commit}")
    problems = bound_problems(root, commit)
    if problems:
        raise sel.SelectionError("; ".join(problems))
    inputs = json.loads((root / STEP_DIR / "inputs.json").read_text(encoding="utf-8"))
    if code_record(root)["sha256"] != inputs["code"]["sha256"]:
        raise sel.SelectionError("the code hash differs from the one frozen in inputs.json")
    folder = root / STEP_DIR / SELECTION_DIR
    if folder.exists():
        raise sel.SelectionError(f"{folder} exists: the selection is written once")
    attempt = _attempt(root, approval_url)
    triage_fn = _logged(kwargs.pop("triage_fn", pilot.triage), attempt)
    created = pilot.push_run_created_at(commit)
    number = round_after(created)
    seed, beacon = drand_seed(number)
    with open(attempt / "round.json", "x", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps({"round": number, "beacon": beacon}, default=str) + "\n")
    out = run_selection(
        cache_dir(root, inputs), inputs, beacon["randomness"], root, triage_fn, **kwargs
    )
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
            "attempt": attempt.name,
        }
    )
    folder.mkdir(parents=True, exist_ok=False)
    files = {
        "selection.json": json.dumps(out, indent=2) + "\n",
        "ledger.json": json.dumps(ledger(out), indent=2) + "\n",
    }
    if out["complete"]:
        files["targets.yaml"] = yaml.safe_dump(
            targets_document(out, inputs), sort_keys=False, allow_unicode=True
        )
    for name, text in files.items():
        with open(folder / name, "x", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
    return out
