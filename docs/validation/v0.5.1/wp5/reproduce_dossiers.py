"""v0.5.1 WP5, row 5.2 (b): one recorded dossier of each TESS version re-run with the current code.

A re-execution of published dossiers: it runs only after the maintainer's approval, recorded on
the tracking issue (#208) with the dossiers and these commands, before it runs (CLAUDE.md,
"Pre-registration process"). Development evidence only; it decides nothing, and it never writes
into a recorded dossier or archive.

The dossiers (chosen before any re-execution by a rule that reads no verdict: in each version's
recorded archive, the dossier with the fewest light-curve files in its ``data/manifest.json``,
ties broken by the target key in string order; the v0.1 failed technical run is not a result and
is left out, and so is a dossier without ``data/manifest.json``):

- v0.1: ``refute-v0.1-calibration.zip`` (asset of release v0.1.0), ``TIC-138819293``;
- v0.2: ``refute-v0.2-calibration.zip`` (asset of release v0.2.0), ``TIC-194736418``;
- v0.4: ``v0.4-stage2-originals.zip`` (Zenodo 10.5281/zenodo.23874043), ``TIC-286480954``;
- v0.5: ``c3-dossiers.zip`` (the C3 run, ``calibration/v0.5/runs/c3-dossiers``),
  ``TIC-151724385``.

No v0.3 dossier: the v0.3 claims are paper claims of the ML pack (no paper code, nothing on the
VM, nothing from ``calibration/v0.3/``).

For one version, ``run <version> --archives <folder>``:

1. checks the archive's SHA-256 against its record, extracts the dossier into a new folder under
   ``.cache/v051/wp5/b/<version>/recorded`` and checks it (``check_dossier``: its manifest, and
   its seal when it has one);
2. rebuilds the claim from the dossier's own bytes (``claim.yaml``, ``claim.lock.json``, the
   attachments) and loads it with the current code. The lock is not verified: the current code
   hash differs from the locked one by construction, so ``refute verify`` gives TAMPERED and
   ``refute calibrate`` / ``refute discover`` refuse to run; this script runs the same
   ``run_target_task`` in-process instead;
3. places the frozen TESS-EB edition (the local copy checked against SHA-256
   ``61cb8749...a323`` and its content SHA-256) where the claim's catalog scan reads it, and runs
   the pack's claim-level check offline;
4. fetches the target's MAST data with the current adapter into a new cache (lightkurve search,
   the files, the TIC queries), each attempt retried after 120 s, at most 5 attempts (the
   transient rule); every file's URL, SHA-256 and retrieval time is recorded;
5. analyzes the target with the provenance of the recorded run (claim, code, lock, run identity)
   and the recorded stage, single-threaded numerical libraries, into a new dossier;
6. compares: ``check_dossier(new, against=recorded)`` (the rule already fixed: identical input
   data hashes, verdict, status and test statuses, key values within a relative 1e-6), the verdict
   and its reason, ``verdict.json`` byte for byte, and ``report.md`` re-rendered from the recorded
   ``verdict.json``. A difference under the fixed rule, or in the verdict or its reason, means the
   recorded dossier was NOT reproduced: the work stops for the maintainer.

Writes ``reproduce-dossiers-<version>.json`` next to this script (exclusively). Exit code 0
reproduced, 1 not reproduced, 2 the step could not run.

``prepare <version> --archives <folder>`` runs steps 1 to 3 only (no network, no analysis).

Amendment 8 of the plan (2026-11-07) adds two steps, run after ``run`` for the same version:

- ``baseline <version>`` (with the project's interpreter): the tag's tracked tree (``src/``,
  ``uv.lock``) extracted by ``git archive`` from the commit the tag points at into
  ``.cache/v051/wp5/b/<version>/tag-code`` (the tag's worktree is never touched); its ``uv.lock``
  equal to the project's except the ``refute`` version line; every loaded ``refute`` module from
  that tree, checked before and after; no bytecode written. The same claim (rebuilt again from the
  recorded dossier's bytes) is analyzed by that code on the SAME inputs (the cache the ``run`` step
  filled, offline: no new download), with the same context, into
  ``.cache/v051/wp5/b/<version>/baseline``.
- ``compare <version>``: (a) the current code's ``verdict.json`` against the tag code's, byte for
  byte, except the download-time fields (``retrieved_utc`` fields whose value is a retrieval time
  in the ``run`` step's fetch manifest) and the run-identity fields (``provenance.run_id``,
  ``provenance.run_git_commit``): any other difference is a regression; (b) the current code's
  ``verdict.json`` against the recorded one, with the ``run`` step's ``check-dossier`` result, each
  difference classified as (i) a download time, (ii) a difference that already exists at the tag
  (the tag code's value equals the current code's there), with a candidate commit of origin
  (``git log -S``, unverified) when it is a key the recording lacks, or (iii) any other: a
  regression. Writes ``reproduce-dossiers-<version>-comparisons.json`` (exclusively). Exit code 0
  no regression, 1 a regression, 2 the step could not run.
"""

from __future__ import annotations

import os

# single-threaded numerical libraries, as in the recorded runs' reproductions (before numpy loads)
for _name in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_name] = "1"

import argparse  # noqa: E402
import hashlib  # noqa: E402
import json  # noqa: E402
import re  # noqa: E402
import shutil  # noqa: E402
import subprocess  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402
import traceback  # noqa: E402
import zipfile  # noqa: E402
from datetime import UTC, datetime  # noqa: E402
from pathlib import Path, PurePosixPath  # noqa: E402
from typing import Any  # noqa: E402

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
WORK = ROOT / ".cache" / "v051" / "wp5" / "b"
FROZEN_TESS_EB = ROOT / ".cache" / "v04" / "tess-eb" / "tess_ebs_prsa2022.tsv"
FROZEN_TESS_EB_SHA256 = "61cb8749ce2ebf87d3fdf495af888b2f803064c67a23c117f742b85598f5a323"
ATTEMPTS = 5
RETRY_SECONDS = 120.0

DOSSIERS = {
    "v0.1": {
        "archive": "refute-v0.1-calibration.zip",
        "sha256": "6f67781dbd3790cae767ff215bb0d7ee5cfed0763112304a3b318a3e987c993d",
        "source": "https://github.com/klucilla/refute/releases/download/v0.1.0/"
        "refute-v0.1-calibration.zip",
        "prefix": "refute-v0.1-calibration/20261007T221214Z-5701c54c/TIC-138819293/",
        "mode": "calibrate",
    },
    "v0.2": {
        "archive": "refute-v0.2-calibration.zip",
        "sha256": "906c6f46ab3dde9c6bd06ac0f9c453b1b388555b35c33990b3a995f0be04c829",
        "source": "https://github.com/klucilla/refute/releases/download/v0.2.0/"
        "refute-v0.2-calibration.zip",
        "prefix": "refute-v0.2-calibration/20261009T155044Z-c9f341d2/TIC-194736418/",
        "mode": "calibrate",
    },
    "v0.4": {
        "archive": "v0.4-stage2-originals.zip",
        "sha256": "003f37c29063bef5b23006ea6f52faf63b35c7770858e34e8e5dfe58ff03024b",
        "source": "https://doi.org/10.5281/zenodo.23874043",
        "prefix": "promoted-s2/TIC-286480954/",
        "mode": "discover",
    },
    "v0.5": {
        "archive": "c3-dossiers.zip",
        "sha256": "fa316636104e99fbafb6caf87db4a1053580bd8100e2d510f0fb3eb9dd1b271e",
        "source": "calibration/v0.5/runs/c3-dossiers/drive-manifest.sha256",
        "prefix": "TIC-151724385/",
        "mode": "discover",
    },
}


class StepError(Exception):
    """The step could not run (not a reproduction result)."""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def safe_rel(name: str) -> PurePosixPath:
    rel = PurePosixPath(name)
    if not name or rel.is_absolute() or any(p in ("", ".", "..") for p in rel.parts):
        raise StepError(f"unsafe member name {name!r}")
    return rel


def new_dir(path: Path) -> Path:
    """A new folder inside WORK (never an existing one, never through a link)."""
    if not path.resolve().is_relative_to(WORK.resolve()):
        raise StepError(f"{path} is outside {WORK}")
    for part in [path, *path.parents]:
        if part.is_symlink() or part.is_junction():
            raise StepError(f"{part} is a link or a junction")
        if part == WORK:
            break
    path.parent.mkdir(parents=True, exist_ok=True)
    path.mkdir()  # raises when it exists: every run starts from new folders
    return path


def extract(spec: dict[str, Any], archives: Path, dest: Path) -> None:
    archive = archives / spec["archive"]
    if sha256_file(archive) != spec["sha256"]:
        raise StepError(f"{archive.name}: its SHA-256 is not the recorded one")
    with zipfile.ZipFile(archive) as z:
        members = [i for i in z.infolist() if i.filename.startswith(spec["prefix"])]
        if not members:
            raise StepError(f"{spec['prefix']} is not in {archive.name}")
        for info in members:
            if info.is_dir():
                continue
            rel = safe_rel(info.filename[len(spec["prefix"]) :])
            out = dest.joinpath(*rel.parts)
            out.parent.mkdir(parents=True, exist_ok=True)
            with open(out, "xb") as handle:
                handle.write(z.read(info))


def rebuild_claim(recorded: Path, claim_dir: Path):
    from refute.core.claim import load_claim

    shutil.copyfile(recorded / "claim.yaml", claim_dir / "claim.yaml")
    shutil.copyfile(recorded / "claim.lock.json", claim_dir / "claim.lock.json")
    attachments = recorded / "attachments"
    if attachments.is_dir():
        for path in sorted(p for p in attachments.rglob("*") if p.is_file()):
            rel = safe_rel(path.relative_to(attachments).as_posix())
            out = claim_dir.joinpath(*rel.parts)
            out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, out)
    loaded = load_claim(claim_dir / "claim.yaml")
    for attachment in loaded.claim.attachments:
        if not loaded.attachment_path(attachment).is_file():
            raise StepError(f"attachment {attachment.path} is not in the dossier")
    return loaded


def place_catalogs(loaded, cache: Path) -> list[dict[str, Any]]:
    """The frozen TESS-EB edition where the claim's scan reads it, then the claim-level check."""
    from refute.packs.tess.ebcatalog import content_sha256, external_snapshots, load_scan

    placed: list[dict[str, Any]] = []
    attachment = loaded.attachment_by_role("eb-catalog-scan")
    if attachment is not None:
        scan = load_scan(loaded.attachment_path(attachment))
        for snap in external_snapshots(scan):
            if snap["catalog_name"] != "TESS-EB":
                raise StepError(f"no frozen copy for the {snap['catalog_name']} snapshot")
            data = FROZEN_TESS_EB.read_bytes()
            if sha256_bytes(data) != FROZEN_TESS_EB_SHA256:
                raise StepError("the frozen TESS-EB copy's SHA-256 differs")
            if content_sha256(data) != snap["content_sha256"]:
                raise StepError("the frozen TESS-EB content SHA-256 is not the scan's")
            dest = cache.joinpath(*safe_rel(snap["cache_path"]).parts)
            dest.parent.mkdir(parents=True, exist_ok=True)
            with open(dest, "xb") as handle:
                handle.write(data)
            placed.append(
                {
                    "catalog": "TESS-EB",
                    "cache_path": snap["cache_path"],
                    "sha256": FROZEN_TESS_EB_SHA256,
                    "content_sha256": snap["content_sha256"],
                    "source": ".cache/v04/tess-eb/tess_ebs_prsa2022.tsv (local frozen copy)",
                }
            )
    messages = loaded.pack.adapter.prepare_claim_data(loaded, cache, True)
    return [*placed, *({"check": m} for m in messages or [])]


def fetch(loaded, target: dict, plan: dict, cache: Path) -> tuple[dict, list[dict]]:
    attempts: list[dict] = []
    for attempt in range(1, ATTEMPTS + 1):
        started = utc_now()
        try:
            manifest = loaded.pack.adapter.fetch(target, plan, cache)
        except Exception as exc:  # noqa: BLE001 - recorded, then retried
            attempts.append(
                {
                    "attempt": attempt,
                    "started_utc": started,
                    "error": f"{type(exc).__name__}: {exc}"[:400],
                }
            )
            if attempt < ATTEMPTS:
                time.sleep(RETRY_SECONDS)
            continue
        attempts.append({"attempt": attempt, "started_utc": started, "ok": True})
        return manifest, attempts
    raise StepError(f"the data fetch failed after {ATTEMPTS} attempts: {attempts}")


def downloads(manifest: dict) -> list[dict]:
    out = []
    for kind in ("files", "pixel_files"):
        for record in manifest.get(kind) or []:
            out.append(
                {
                    "kind": kind,
                    "name": record["name"],
                    "url": record.get("url"),
                    "data_uri": record.get("data_uri"),
                    "sha256": record["sha256"],
                    "bytes": record.get("bytes"),
                    "retrieved_utc": manifest.get("retrieved_utc"),
                }
            )
    return out


def compare_inputs(fetched: dict, recorded: dict) -> dict:
    files_new = {f["name"]: f["sha256"] for f in fetched["files"]}
    files_old = {f["name"]: f["sha256"] for f in recorded["files"]}

    def strip(x: Any) -> Any:
        if isinstance(x, dict):
            return {k: strip(v) for k, v in x.items() if k != "retrieved_utc"}
        if isinstance(x, list):
            return [strip(v) for v in x]
        return x

    return {
        "light_curve_files_equal": files_new == files_old,
        "only_fetched": sorted(set(files_new) - set(files_old)),
        "only_recorded": sorted(set(files_old) - set(files_new)),
        "different_sha256": sorted(
            n for n in set(files_new) & set(files_old) if files_new[n] != files_old[n]
        ),
        "star_equal": strip(fetched.get("star")) == strip(recorded.get("star")),
        "neighbors_equal": strip(fetched.get("neighbors")) == strip(recorded.get("neighbors")),
        "pixel_files_fetched": len(fetched.get("pixel_files") or []),
        "pixel_files_recorded": "not recorded in the dossier",
    }


def staging(recorded: Path, verdict: dict, mode: str) -> dict:
    if mode != "discover":
        return {}
    stage = (verdict.get("discovery") or {}).get("stage")
    text = (recorded / "REPRODUCE.md").read_text(encoding="utf-8")
    out: dict[str, Any] = {"stage": stage, "promotion_sha256": None}
    match = re.search(r"--promotion (\S+)", text)
    if match:
        record = ROOT / match.group(1)
        out["promotion_record"] = match.group(1)
        out["promotion_sha256"] = sha256_file(record) if record.is_file() else None
    stage_in_text = re.search(r"--stage (\d)", text)
    if stage_in_text and int(stage_in_text.group(1)) != stage:
        raise StepError("the recorded REPRODUCE.md and verdict.json name different stages")
    return out


def context_for(loaded, verdict: dict, mode: str, cache: Path, stage: dict, lock: dict) -> dict:
    """The run context of the recorded run: its provenance from the recorded verdict, the
    locked values from the recorded lock, the claim's text from the claim."""
    prov = verdict.get("provenance") or {}
    context = {
        "mode": mode,
        "run_id": prov.get("run_id"),
        "claim_id": loaded.claim.id,
        "claim_kind": loaded.claim.kind,
        "claim_title": loaded.claim.title,
        "hypothesis": loaded.claim.hypothesis,
        "definitions": loaded.claim.definitions,
        "pass_criteria": loaded.claim.pass_criteria,
        "claim_sha256": prov.get("claim_sha256"),
        "code_sha256": prov.get("code_sha256"),
        "lock_git_commit": prov.get("lock_git_commit"),
        "locked_at_utc": lock.get("locked_at_utc"),
        "claim_path_in_repo": lock.get("claim_path_in_repo"),
        "run_git_commit": prov.get("run_git_commit"),
        "run_git_dirty": False,
        "refute_version": prov.get("refute_version"),
        "pack": prov.get("pack"),
        "attachments": [{"path": a.path, "role": a.role} for a in loaded.claim.attachments],
        "cache_dir": str(cache),
    }
    context.update(stage)
    return context


def git_head() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()


def run(version: str, archives: Path, prepare_only: bool) -> int:
    sys.path.insert(0, str(ROOT / "src"))
    from refute.core.dossier import check_dossier
    from refute.core.environment import snapshot
    from refute.core.run import TargetTask, run_target_task

    spec = DOSSIERS[version]
    key = spec["prefix"].rstrip("/").split("/")[-1]
    base = new_dir(WORK / (f"{version}-prepare" if prepare_only else version))
    recorded = new_dir(base / "recorded" / key)
    claim_dir = new_dir(base / "claim")
    cache = new_dir(base / "cache")
    report: dict[str, Any] = {
        "version": version,
        "dossier": key,
        "archive": {k: spec[k] for k in ("archive", "sha256", "source", "prefix")},
        "commit": git_head(),
        "started_utc": utc_now(),
    }
    extract(spec, archives, recorded)
    intact = check_dossier(recorded)
    report["recorded_intact"] = intact.ok
    if not intact.ok:
        raise StepError(f"the recorded dossier is not intact: {intact.integrity_problems}")
    loaded = rebuild_claim(recorded, claim_dir)
    verdict = json.loads((recorded / "verdict.json").read_text(encoding="utf-8"))
    target = json.loads((recorded / "target.json").read_text(encoding="utf-8"))
    stage = staging(recorded, verdict, spec["mode"])
    plan = loaded.claim.test_plan
    if stage:
        plan = loaded.pack.schema.plan_for_stage(plan, stage["stage"])
    report["catalogs"] = place_catalogs(loaded, cache)
    report["stage"] = stage
    if prepare_only:
        report["prepared_only"] = True
        print(json.dumps(report, indent=1))
        return 0

    t0 = time.process_time()
    manifest, attempts = fetch(loaded, target, plan, cache)
    report["fetch_attempts"] = attempts
    report["downloads"] = downloads(manifest)
    recorded_manifest = json.loads((recorded / "data" / "manifest.json").read_text("utf-8"))
    report["inputs"] = compare_inputs(manifest, recorded_manifest)

    lock = json.loads((recorded / "claim.lock.json").read_text(encoding="utf-8"))
    context = context_for(loaded, verdict, spec["mode"], cache, stage, lock)
    new = base / "new" / key
    task = TargetTask(
        pack_name=loaded.pack.name,
        target=target,
        target_key=key,
        test_plan=plan,
        context=context,
        cache_dir=str(cache),
        dossier_dir=str(new),
        claim_filename="claim.yaml",
        claim_bytes=(recorded / "claim.yaml").read_bytes(),
        lock_bytes=(recorded / "claim.lock.json").read_bytes(),
        integrity=json.loads((recorded / "integrity.json").read_text(encoding="utf-8")),
        attachments=tuple(
            (a.path, loaded.attachment_path(a).read_bytes()) for a in loaded.claim.attachments
        ),
        environment=snapshot(ROOT),
    )
    result = run_target_task(task)
    report["processor_seconds"] = time.process_time() - t0
    check = check_dossier(new, against=recorded)
    new_verdict_bytes = (new / "verdict.json").read_bytes()
    old_verdict_bytes = (recorded / "verdict.json").read_bytes()
    rendered = loaded.pack.analyzer.report(verdict, context)
    report["comparison"] = {
        "fixed_rule": {
            "rule": "check_dossier --against: identical input data hashes, verdict, status and "
            "test statuses; key values within a relative 1e-6",
            "ok": check.ok,
            "integrity_problems": check.integrity_problems,
            "differences": check.differences,
        },
        "verdict": {"recorded": verdict.get("verdict"), "new": result.get("verdict")},
        "verdict_reason_equal": verdict.get("verdict_reason") == result.get("verdict_reason"),
        "verdict_reason": {
            "recorded": verdict.get("verdict_reason"),
            "new": result.get("verdict_reason"),
        },
        "verdict_json_byte_identical": new_verdict_bytes == old_verdict_bytes,
        "verdict_json_sha256": {
            "recorded": sha256_bytes(old_verdict_bytes),
            "new": sha256_bytes(new_verdict_bytes),
        },
        "report_rerendered_byte_identical": rendered.encode("utf-8")
        == (recorded / "report.md").read_bytes(),
    }
    if not report["comparison"]["verdict_json_byte_identical"]:
        report["comparison"]["verdict_json_first_differences"] = first_differences(
            json.loads(new_verdict_bytes), verdict
        )
    reproduced = (
        check.ok
        and verdict.get("verdict") == result.get("verdict")
        and report["comparison"]["verdict_reason_equal"]
    )
    report["reproduced_under_the_fixed_rule"] = reproduced
    report["finished_utc"] = utc_now()
    out = HERE / f"reproduce-dossiers-{version}.json"
    with open(out, "x", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(report, indent=1, sort_keys=True) + "\n")
    summary = {k: report[k] for k in ("version", "dossier", "reproduced_under_the_fixed_rule")}
    summary["verdict_json_byte_identical"] = report["comparison"]["verdict_json_byte_identical"]
    print(json.dumps(summary, indent=1))
    return 0 if reproduced else 1


BASELINE_TAG = "v0.5.0-calibration-lock"
BASELINE_COMMIT = "b6249b500d8d7b98a6246dbe0d99a4c55363f1cb"
RUN_IDENTITY = ("$.provenance.run_id", "$.provenance.run_git_commit")
PROJECT_PYTHON = ROOT / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def _git(*args: str, cwd: Path = ROOT, binary: bool = False):
    out = subprocess.run(["git", *args], cwd=cwd, capture_output=True, check=True).stdout
    return out if binary else out.decode("utf-8").strip()


def lock_differences(tag_lock: str, project_lock: str) -> list[str]:
    """Lines of the two uv.lock files that differ, outside the ``refute`` package's version."""
    a, b = tag_lock.splitlines(), project_lock.splitlines()
    if len(a) != len(b):
        return [f"line counts differ: {len(a)} != {len(b)}"]
    out = []
    for i, (x, y) in enumerate(zip(a, b, strict=True)):
        if x != y and not (x.startswith('version = "') and i > 0 and a[i - 1] == 'name = "refute"'):
            out.append(f"line {i + 1}: {x!r} != {y!r}")
    return out


def extract_tag_code(dest: Path) -> None:
    """The tag's tracked tree, from git objects (``git archive``), into a new folder: no
    untracked file can enter it, and the tag's worktree is never touched."""
    if _git("rev-list", "-n", "1", BASELINE_TAG) != BASELINE_COMMIT:
        raise StepError(f"tag {BASELINE_TAG} does not point at {BASELINE_COMMIT}")
    data = _git("archive", "--format=zip", BASELINE_COMMIT, "src", "uv.lock", binary=True)
    import io

    with zipfile.ZipFile(io.BytesIO(data)) as z:
        for info in z.infolist():
            if info.is_dir():
                continue
            rel = safe_rel(info.filename)
            out = dest.joinpath(*rel.parts)
            out.parent.mkdir(parents=True, exist_ok=True)
            with open(out, "xb") as handle:
                handle.write(z.read(info))


def baseline(version: str) -> int:
    """The same claim, on the same inputs, analyzed by the code of tag v0.5.0-calibration-lock."""
    if Path(sys.executable).resolve() != PROJECT_PYTHON.resolve():
        raise StepError(f"run this step with the project's interpreter {PROJECT_PYTHON}")
    spec = DOSSIERS[version]
    key = spec["prefix"].rstrip("/").split("/")[-1]
    base = WORK / version
    recorded = base / "recorded" / key
    cache = base / "cache"
    if not (base / "new" / key / "verdict.json").is_file():
        raise StepError(f"run the `run` step for {version} first")
    code_root = new_dir(base / "tag-code")
    extract_tag_code(code_root)
    drift = lock_differences(
        (code_root / "uv.lock").read_text(encoding="utf-8"),
        (ROOT / "uv.lock").read_text(encoding="utf-8"),
    )
    if drift:
        raise StepError(f"the tag's uv.lock differs from the project's: {drift[:5]}")
    sys.dont_write_bytecode = True  # the extracted tree stays as git wrote it
    sys.path.insert(0, str(code_root / "src"))
    import refute
    from refute.core.environment import snapshot
    from refute.core.run import TargetTask, run_target_task

    def foreign_modules() -> list[str]:
        return sorted(
            name
            for name, module in list(sys.modules.items())
            if (name == "refute" or name.startswith("refute."))
            and getattr(module, "__file__", None)
            and not Path(module.__file__).resolve().is_relative_to(code_root / "src")
        )

    if foreign_modules():
        raise StepError(f"refute modules imported from outside the tag's code: {foreign_modules()}")
    if not Path(refute.__file__).resolve().is_relative_to(code_root / "src"):
        raise StepError(f"refute was imported from {refute.__file__}")
    claim_dir = new_dir(base / "baseline-claim")
    out = base / "baseline" / key
    if out.exists():
        raise StepError(f"{out} exists")
    loaded = rebuild_claim(recorded, claim_dir)
    verdict = json.loads((recorded / "verdict.json").read_text(encoding="utf-8"))
    target = json.loads((recorded / "target.json").read_text(encoding="utf-8"))
    stage = staging(recorded, verdict, spec["mode"])
    plan = loaded.claim.test_plan
    if stage:
        plan = loaded.pack.schema.plan_for_stage(plan, stage["stage"])
    # the same inputs: the cache the `run` step filled, checked offline; nothing is downloaded
    loaded.pack.adapter.prepare_claim_data(loaded, cache, True)
    lock = json.loads((recorded / "claim.lock.json").read_text(encoding="utf-8"))
    context = context_for(loaded, verdict, spec["mode"], cache, stage, lock)
    t0 = time.process_time()
    task = TargetTask(
        pack_name=loaded.pack.name,
        target=target,
        target_key=key,
        test_plan=plan,
        context=context,
        cache_dir=str(cache),
        dossier_dir=str(out),
        claim_filename="claim.yaml",
        claim_bytes=(recorded / "claim.yaml").read_bytes(),
        lock_bytes=(recorded / "claim.lock.json").read_bytes(),
        integrity=json.loads((recorded / "integrity.json").read_text(encoding="utf-8")),
        attachments=tuple(
            (a.path, loaded.attachment_path(a).read_bytes()) for a in loaded.claim.attachments
        ),
        environment=snapshot(code_root),
    )
    result = run_target_task(task)
    if foreign_modules():
        raise StepError(f"refute modules imported from outside the tag's code: {foreign_modules()}")
    print(
        json.dumps(
            {
                "version": version,
                "dossier": key,
                "baseline_tag": BASELINE_TAG,
                "baseline_commit": BASELINE_COMMIT,
                "refute_imported_from": "the tag's tree extracted by git archive",
                "refute_modules_checked": sum(
                    1 for n in sys.modules if n == "refute" or n.startswith("refute.")
                ),
                "verdict": result.get("verdict"),
                "processor_seconds": time.process_time() - t0,
            },
            indent=1,
        )
    )
    return 0


def all_differences(a: Any, b: Any, path: str = "$", out: list | None = None) -> list[dict]:
    """Every difference between ``a`` (one output) and ``b`` (another), as JSON paths."""
    out = [] if out is None else out
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            if k not in b:
                out.append({"path": f"{path}.{k}", "kind": "only_first", "first": a[k]})
            elif k not in a:
                out.append({"path": f"{path}.{k}", "kind": "only_second", "second": b[k]})
            else:
                all_differences(a[k], b[k], f"{path}.{k}", out)
    elif isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        for i, (x, y) in enumerate(zip(a, b, strict=True)):
            all_differences(x, y, f"{path}[{i}]", out)
    elif a != b:
        out.append({"path": path, "kind": "value", "first": a, "second": b})
    return out


def lookup(doc: Any, path: str) -> tuple[bool, Any]:
    """The value at a JSON path written by ``all_differences`` (``$.a.b[2].c``)."""
    node = doc
    for part in re.findall(r"\.([^.\[]+)|\[(\d+)\]", path[1:]):
        name, index = part
        if name:
            if not isinstance(node, dict) or name not in node:
                return False, None
            node = node[name]
        else:
            if not isinstance(node, list) or int(index) >= len(node):
                return False, None
            node = node[int(index)]
    return True, node


def set_path(doc: Any, path: str, value: Any) -> None:
    """Set the value at an existing JSON path written by ``all_differences``."""
    parts = re.findall(r"\.([^.\[]+)|\[(\d+)\]", path[1:])
    node = doc
    for name, index in parts[:-1]:
        node = node[name] if name else node[int(index)]
    name, index = parts[-1]
    if name:
        node[name] = value
    else:
        node[int(index)] = value


def canonical_bytes(doc: Any) -> bytes:
    """The bytes ``refute.core.io.dumps_json`` and the dossier writer give for a parsed JSON
    document (sorted keys, 2-space indent, UTF-8, LF, trailing newline)."""
    text = json.dumps(doc, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n"
    return text.replace("\r\n", "\n").encode("utf-8")


def key_origin(path: str) -> str | None:
    """A CANDIDATE commit of origin, unverified: the oldest commit under src/ whose diff changes
    the number of occurrences of the path's last key name (``git log -S``). It may be unrelated
    to the output field; it is checked by reading that commit before it is cited on #213."""
    name = re.findall(r"\.([^.\[]+)", path)[-1]
    log = subprocess.run(
        ["git", "log", "--format=%h %ad %s", "--date=short", "--reverse", "-S", name, "--", "src/"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.splitlines()
    return log[0][:120] if log else None


def download_times(cache: Path, tic_id: int) -> set[str]:
    """Every ``retrieved_utc`` in the current run's fetch manifest for this target: the times of
    the data downloaded that day (the files, the TIC star and neighbour queries)."""
    path = cache / "refute" / "tess" / f"TIC-{tic_id}.json"
    found: set[str] = set()

    def walk(x: Any) -> None:
        if isinstance(x, dict):
            for k, v in x.items():
                if k == "retrieved_utc" and isinstance(v, str):
                    found.add(v)
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)

    walk(json.loads(path.read_text(encoding="utf-8")))
    return found


def is_download_time(path: str, value: Any, times: set[str]) -> bool:
    """A ``retrieved_utc`` field whose value is the time of data downloaded that day."""
    return path.endswith(".retrieved_utc") and value in times


def compare(version: str) -> int:
    spec = DOSSIERS[version]
    key = spec["prefix"].rstrip("/").split("/")[-1]
    base = WORK / version
    files = {
        name: base / folder / key / "verdict.json"
        for name, folder in (("current", "new"), ("tag", "baseline"), ("recorded", "recorded"))
    }
    for name, path in files.items():
        if not path.is_file():
            raise StepError(f"no {name} verdict.json at {path}")
    raw = {name: path.read_bytes() for name, path in files.items()}
    doc = {name: json.loads(data) for name, data in raw.items()}
    times = download_times(base / "cache", int(doc["recorded"]["tic_id"]))
    run_report = json.loads((HERE / f"reproduce-dossiers-{version}.json").read_text("utf-8"))
    report: dict[str, Any] = {
        "version": version,
        "dossier": key,
        "commit": git_head(),
        "tag": {"name": "v0.5.0-calibration-lock", "commit": BASELINE_COMMIT},
        "verdict": {name: d.get("verdict") for name, d in doc.items()},
        "verdict_reason": {name: d.get("verdict_reason") for name, d in doc.items()},
        "verdict_json_sha256": {name: sha256_bytes(data) for name, data in raw.items()},
    }
    # (a) the current code against the tag's code, the same claim and inputs
    a_diffs = all_differences(doc["current"], doc["tag"])
    # only value differences of fields present in both outputs are allowed (never an added or
    # removed field)
    allowed = [
        d
        for d in a_diffs
        if d["kind"] == "value"
        and (
            d["path"] in RUN_IDENTITY
            or (
                is_download_time(d["path"], d["first"], times)
                and is_download_time(d["path"], d["second"], times)
            )
        )
    ]
    a_regressions = [d for d in a_diffs if d not in allowed]
    # byte identity outside the allowed fields: the tag's output with only the allowed values
    # replaced by the current ones, serialized as the dossier writer does, must be the current
    # output's bytes; the tag's own bytes must be that serialization of its parsed document
    expected = json.loads(raw["tag"])
    for d in allowed:
        set_path(expected, d["path"], d["first"])
    tag_canonical = canonical_bytes(doc["tag"]) == raw["tag"]
    outside_exceptions = canonical_bytes(expected) == raw["current"] and tag_canonical
    if not outside_exceptions and not a_regressions:
        a_regressions.append(
            {"path": "(bytes)", "kind": "serialization", "tag_bytes_canonical": tag_canonical}
        )
    report["a_current_vs_tag"] = {
        "byte_identical": raw["current"] == raw["tag"],
        "byte_identical_outside_the_allowed_fields": outside_exceptions,
        "allowed_differences": allowed,
        "regressions": a_regressions,
    }
    # (b) the current code against the recorded dossier, each difference classified
    classified = []
    for d in all_differences(doc["current"], doc["recorded"]):
        entry = {"path": d["path"], "kind": d["kind"]}
        if d["kind"] == "value":
            entry |= {"current": d["first"], "recorded": d["second"]}
        elif d["kind"] == "only_first":
            entry |= {"current": d["first"], "recorded": "(absent)"}
        else:
            entry |= {"current": "(absent)", "recorded": d["second"]}
        found_current, at_current = lookup(doc["current"], d["path"])
        found_tag, at_tag = lookup(doc["tag"], d["path"])
        if d["kind"] == "value" and is_download_time(d["path"], d["first"], times):
            entry["class"] = "i: the time of data downloaded that day"
        elif found_tag == found_current and at_tag == at_current:
            entry["class"] = "ii: already at tag v0.5.0-calibration-lock"
            if d["kind"] == "only_first":
                entry["origin_candidate_unverified"] = key_origin(d["path"])
        else:
            entry["class"] = "iii: regression"
        classified.append(entry)
    report["b_current_vs_recorded"] = {
        "check_dossier_against_recorded": {
            "source": f"reproduce-dossiers-{version}.json (the `run` step)",
            **run_report["comparison"]["fixed_rule"],
        },
        "byte_identical": raw["current"] == raw["recorded"],
        "differences": classified,
        "counts": {
            c: sum(1 for e in classified if e["class"].startswith(c + ":"))
            for c in ("i", "ii", "iii")
        },
    }
    regression = bool(a_regressions) or report["b_current_vs_recorded"]["counts"]["iii"] > 0
    report["regression"] = regression
    out = HERE / f"reproduce-dossiers-{version}-comparisons.json"
    with open(out, "x", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(report, indent=1, sort_keys=True, default=str) + "\n")
    print(
        json.dumps(
            {
                "version": version,
                "a_byte_identical": report["a_current_vs_tag"]["byte_identical"],
                "a_regressions": len(a_regressions),
                "b_counts": report["b_current_vs_recorded"]["counts"],
                "regression": regression,
            },
            indent=1,
        )
    )
    return 1 if regression else 0


def first_differences(a: Any, b: Any, path: str = "$", out: list | None = None) -> list[str]:
    out = [] if out is None else out
    if len(out) >= 20:
        return out
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a or k not in b:
                out.append(f"{path}.{k}: present only in {'new' if k in a else 'recorded'}")
            else:
                first_differences(a[k], b[k], f"{path}.{k}", out)
    elif isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        for i, (x, y) in enumerate(zip(a, b, strict=True)):
            first_differences(x, y, f"{path}[{i}]", out)
    elif a != b:
        out.append(f"{path}: new {a!r:.80} != recorded {b!r:.80}")
    return out


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("step", choices=("prepare", "run", "baseline", "compare"))
    parser.add_argument("version", choices=sorted(DOSSIERS))
    parser.add_argument("--archives", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.step == "baseline":
            return baseline(args.version)
        if args.step == "compare":
            return compare(args.version)
        if args.archives is None:
            raise StepError(f"{args.step} needs --archives")
        return run(args.version, args.archives, args.step == "prepare")
    except StepError as exc:
        print(f"STOP (the step could not run): {exc}")
        return 2
    except Exception:  # noqa: BLE001
        traceback.print_exc()
        return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
