"""The v0.4 pilot's runs after the lock (calibration/v0.4/PROTOCOL.md, sections 4.4, 7 to 10, 12).

A wrapper like run_selection.py: it parses its arguments and calls the locked code
(``refute.core.run.execute_run``, ``refute.packs.tess.discover``, ``refute.drand``); what it adds
is bookkeeping: where the outputs go, the lock check before each step, and the cost of each step
in ``.cache/v04/pilot/cost.jsonl`` (a ``start`` line before it and an ``end`` line after it, so an
interrupted step is visible as a cost not fully known, never as zero).

    .venv/Scripts/python.exe calibration/v0.4/run_pilot.py r-inj --commit <B, full SHA>
        R_inj (section 8): the first drand round at least 1 h after the creation time of B's CI
        push run, its BLS signature verified; written once to calibration/v0.4/runs/r_inj.json.
        B must be the commit that wrote claim.lock.json.

    .venv/Scripts/python.exe calibration/v0.4/run_pilot.py place-tess-eb
        Copy (never move) the frozen TESS-EB static edition of the attempt named by inputs.json
        to the cache path the claim's scan records (claim.py, TESS_EB_CACHE_PATH), after checking
        its SHA-256.

    .venv/Scripts/python.exe calibration/v0.4/run_pilot.py fetch --stage <1|2> --target <key> ...
            [--run-set <JSON list of keys>] [--promotion <record>]
        `refute fetch` of those targets (network), with the bytes of their files recorded.

    .venv/Scripts/python.exe calibration/v0.4/run_pilot.py run --stage <1|2> --run-id <name>
            [--target <key> ...] [--workers <n>] [--promotion <record>] [--online]
        `refute discover` into .cache/v04/pilot/stage<1|2>/<run-id>/, offline after fetch. Online
        (--online) only where the locked code needs the GitHub API, a promotion that needs the
        R_prom draw; an online run also takes the fetch path of its targets (refute.core.run),
        which finds them already in the cache after `fetch`.

    .venv/Scripts/python.exe calibration/v0.4/run_pilot.py measure --name <name> --k <K>
            --transform-stage <1|2> [--first <i>] [--no-transforms] --target <key> ...
        Injections first..K-1 and (unless --no-transforms) the three transformed curves of each
        target, with the seeds of R_inj, into .cache/v04/pilot/measure/<name>/.

    .venv/Scripts/python.exe calibration/v0.4/run_pilot.py n-k --stage1 <run-id> --stage2 <run-id>
            --prefix <name>
        The controls' costs (section 4.4) and the (N, K) decision, written once to
        calibration/v0.4/runs/n_k.json, with the SHA-256 of every record it rests on.

    .venv/Scripts/python.exe calibration/v0.4/run_pilot.py entries --run-id <stage-1 run-id>
        The stage-1 entries of the run set (sections 6 and 7; runs.stage1_entries: each star's
        verdict.json SHA-256, deduplication and eligibility), written once to
        calibration/v0.4/runs/stage1/entries.json, for the results commit (which fixes R_prom).

    .venv/Scripts/python.exe calibration/v0.4/run_pilot.py promote --results-commit <full SHA>
            --run-id <stage-1 run-id>
        The promotion record (section 7; funnel.promotion_record), with the R_prom beacon when
        more than 3 stars are eligible, refused unless steps.promotion_problems finds nothing
        (online: the push run time comes from the GitHub API); written once to
        calibration/v0.4/runs/promotion.json.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from refute.core.runner import _SINGLE_THREAD_ENV  # imports no numerical library

# one thread per numerical library, set before any of them is imported (in this process and in
# the workers, which inherit the environment), so that a parallel run's wall x workers bounds
# its CPU; a value already set to something else stops every step (single_thread_environment)
for _name in _SINGLE_THREAD_ENV:
    os.environ.setdefault(_name, "1")

ROOT = Path(__file__).resolve().parent.parent.parent
CLAIM = ROOT / "calibration" / "v0.4" / "claim.yaml"
LOCK_FILE = "calibration/v0.4/claim.lock.json"
RUNS = ROOT / "calibration" / "v0.4" / "runs"
PILOT = ROOT / ".cache" / "v04" / "pilot"
CACHE = ROOT / ".cache"
COST = PILOT / "cost.jsonl"
# the folders this phase writes in .cache (the frozen inputs, the downloads and their manifests):
# the bytes the 10 GB cap of section 12 counts; the older worktrees in .cache are not this phase's
PHASE_FOLDERS = ("v04", "lightkurve", "refute")
CONTROLS = ("TIC-86396382", "TIC-393911494")
PREFIX = 5  # protocol section 4.4: the first 5 injections of each control's stream
# CPU of the phase before the lock was never metered: the 44 JUnit files of the phase in .cache
# (2026-10-29 to the lock, 2026-10-31T12:25:50Z, outside worktrees) sum 14197 s of wall time;
# counted as 3.94 logical-processor hours, an estimate (one processor per second of wall), not a
# bound; reported apart from the metered hours
PRE_LOCK_HOURS = 3.94
UNMETERED = (
    "CPU before the lock beyond the tests' wall time (the freeze, the selection walk, the claim "
    "and lock steps, test pools using more than one processor) was never metered"
)
# the caps of section 12 (no step starts once the counted use reaches them)
MAX_HOURS = 100.0
MAX_BYTES = 10_000_000_000
LF = "\n"


def utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_once(path: Path, document: dict[str, Any]) -> None:
    """Write a JSON record that must never be written over."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "x", encoding="utf-8", newline=LF) as out:
        out.write(json.dumps(document, indent=2, sort_keys=True) + LF)


def append_cost(line: dict[str, Any]) -> None:
    PILOT.mkdir(parents=True, exist_ok=True)
    with open(COST, "a", encoding="utf-8", newline=LF) as out:
        out.write(json.dumps({"utc": utc_now(), **line}, sort_keys=True) + LF)


def folder_bytes(folder: Path) -> int:
    return sum(p.stat().st_size for p in folder.rglob("*") if p.is_file()) if folder.is_dir() else 0


def phase_bytes() -> dict[str, int]:
    return {name: folder_bytes(CACHE / name) for name in PHASE_FOLDERS}


def head() -> str:
    done = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True
    )
    return done.stdout.strip()


def locked() -> tuple[Any, dict[str, dict[str, Any]], dict[str, str]]:
    """The locked claim, its targets by key and its identity (claim id, claim and code hash),
    after `refute verify` passes on it; anything else stops the step."""
    from refute.core.claim import load_claim
    from refute.core.io import read_json
    from refute.core.lock import VerifyStatus, lock_path_for, verify_claim

    integrity = verify_claim(CLAIM)
    if integrity.status is not VerifyStatus.PASS:
        raise SystemExit(f"refute verify: {integrity.status.value}: {integrity.messages}")
    loaded = load_claim(CLAIM)
    targets = {t["key"]: t for t in loaded.pack.schema.targets_for_run(loaded)}
    lock = read_json(lock_path_for(CLAIM))
    identity = {
        "claim_id": loaded.claim.id,
        "claim_sha256": lock["claim_sha256"],
        "code_sha256": lock["code"]["sha256"],
    }
    return loaded, targets, identity


def cached_bytes(tic_id: int, kind: str = "lc") -> int:
    """Bytes of a star's cached files of ``kind`` (``lc`` or ``tpf``), by its manifest."""
    from refute.core.io import read_json
    from refute.packs.tess.adapter import manifest_path

    path = manifest_path(CACHE, tic_id)
    if not path.is_file():
        return 0
    manifest = read_json(path)
    key = "files" if kind == "lc" else "pixel_files"
    return sum((CACHE / f["path"]).stat().st_size for f in manifest.get(key) or [])


def single_thread_environment() -> dict[str, str | None]:
    """The thread variables, set to 1 at import before any numerical library (the workers inherit
    them): a parallel run's wall x workers bounds its CPU only when each is 1."""
    found = {name: os.environ.get(name) for name in _SINGLE_THREAD_ENV}
    wrong = {k: v for k, v in found.items() if v != "1"}
    if wrong:
        raise SystemExit(f"thread variables other than 1 in the environment: {wrong}")
    return found


def cap_guard() -> dict[str, Any]:
    """No step starts once the counted use reaches a cap of section 12 (the metered hours plus
    the estimate before the lock; the bytes in the phase's folders), or while a step's cost is
    not fully known."""
    used, unknown = hours_used(cost_lines())
    in_cache = sum(phase_bytes().values())
    if unknown:
        raise SystemExit("steps with a cost not fully known: " + "; ".join(unknown))
    if used + PRE_LOCK_HOURS >= MAX_HOURS or in_cache >= MAX_BYTES:
        raise SystemExit(
            f"a cap is reached: {used:.2f} h metered + {PRE_LOCK_HOURS} h before the lock, "
            f"{in_cache} bytes in the phase's folders"
        )
    return {"hours_metered": used, "hours_before_lock_estimate": PRE_LOCK_HOURS, "bytes": in_cache}


def cmd_r_inj(commit: str) -> int:
    from refute import drand
    from refute.packs.tess.discover import pilot

    path = RUNS / "r_inj.json"
    if path.exists():
        print(f"{path} exists; R_inj is fixed once")
        return 1
    done = subprocess.run(
        ["git", "log", "-n", "1", "--format=%H", "--", LOCK_FILE],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    if done.stdout.strip() != commit:
        print(f"{commit} is not the commit B that wrote {LOCK_FILE} ({done.stdout.strip()})")
        return 1
    created = pilot.push_run_created_at(commit)
    number = drand.round_after(created)
    published = drand.round_time(number)
    if published > datetime.now(UTC):
        print(f"round {number} is published at {published.isoformat()}; run again after it")
        return 2
    _seed, beacon = drand.drand_seed(number)
    write_once(
        path,
        {
            "round_name": "R_inj",
            "rule": "PROTOCOL.md section 8: the first drand round at least 1 hour after the "
            "creation time of the CI push run of the lock's commit B",
            "commit": commit,
            "push_run_created_at": created,
            "round": number,
            "round_time_utc": published.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "chain_hash": drand.DRAND_CHAIN_HASH,
            "beacon": beacon,
            "signature_verified": True,
            "retrieved_utc": utc_now(),
        },
    )
    print(f"R_inj: round {number} ({published.isoformat()}), randomness {beacon['randomness']}")
    return 0


def cmd_place_tess_eb() -> int:
    from refute.packs.tess.discover import steps
    from refute.packs.tess.discover.claim import TESS_EB_CACHE_PATH

    inputs = json.loads((ROOT / "calibration" / "v0.4" / "inputs.json").read_text("utf-8"))
    record = next(f for f in inputs["files"] if f["name"] == "tess_eb.tsv")
    source = steps.cache_dir(ROOT, inputs) / "tess_eb.tsv"
    if sha256_file(source) != record["sha256"]:
        print(f"{source} is not the frozen TESS-EB file")
        return 1
    target = CACHE / TESS_EB_CACHE_PATH
    if target.exists():
        same = sha256_file(target) == record["sha256"]
        print(f"{target} exists; {'the same bytes' if same else 'DIFFERENT bytes: stop'}")
        return 0 if same else 1
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    copied = sha256_file(target) == record["sha256"]
    print(f"copied to {target}: SHA-256 {'checked' if copied else 'DIFFERS'}")
    return 0 if copied else 1


def cmd_fetch(stage: int, keys: list[str], promotion: str | None) -> int:
    threads = single_thread_environment()
    _loaded, targets, _identity = locked()
    budget = cap_guard()
    step = uuid.uuid4().hex
    before = phase_bytes()
    append_cost(
        {
            "event": "start",
            "step": step,
            "kind": "fetch",
            "stage": stage,
            "targets": keys,
            "budget": budget,
            "thread_environment": threads,
        }
    )
    started = time.monotonic()
    refute = Path(sys.executable).parent / ("refute.exe" if os.name == "nt" else "refute")
    command = [str(refute), "fetch", str(CLAIM), "--stage", str(stage)]
    for key in keys:
        command += ["--target", key]
    if promotion:
        command += ["--promotion", promotion]
    done = subprocess.run(command, cwd=ROOT, check=False)
    per_star = {
        key: {
            "lc_bytes": cached_bytes(int(targets[key]["tic_id"]), "lc"),
            "tpf_bytes": cached_bytes(int(targets[key]["tic_id"]), "tpf"),
        }
        for key in keys
    }
    append_cost(
        {
            "event": "end",
            "step": step,
            "kind": "fetch",
            "exit_code": done.returncode,
            "wall_seconds": time.monotonic() - started,
            "phase_bytes_before": before,
            "phase_bytes_after": phase_bytes(),
            "per_star": per_star,
        }
    )
    return done.returncode


def cmd_run(
    stage: int,
    run_id: str,
    keys: list[str] | None,
    workers: int,
    promotion: str | None,
    online: bool,
) -> int:
    from refute.core.run import execute_run

    locked()
    threads = single_thread_environment()
    budget = cap_guard()
    step = uuid.uuid4().hex
    append_cost(
        {
            "event": "start",
            "step": step,
            "kind": "run",
            "budget": budget,
            "stage": stage,
            "run_id": run_id,
            "targets": keys,
            "workers": workers,
            "thread_environment": threads,
            "git_head": head(),
        }
    )
    cpu0, wall0 = time.process_time(), time.monotonic()
    outcome = execute_run(
        CLAIM,
        mode="discover",
        targets=keys,
        out_dir=PILOT / f"stage{stage}",
        workers=workers,
        offline=not online,
        run_id=run_id,
        cache_dir=CACHE,
        stage=stage,
        promotion=promotion,
    )
    cpu, wall = time.process_time() - cpu0, time.monotonic() - wall0
    for message in outcome.messages:
        print(message)
    append_cost(
        {
            "event": "end",
            "step": step,
            "kind": "run",
            "exit_code": outcome.exit_code,
            # with one worker the analysis runs in this process, so its CPU time is the run's;
            # with more, the workers' time is not visible here: wall x workers (each worker
            # single-threaded, checked above) plus this process's own time bounds it
            "cpu_seconds": cpu if workers == 1 else None,
            "cpu_seconds_upper_bound": cpu if workers == 1 else wall * workers + cpu,
            "wall_seconds": wall,
            "run_dir": str(outcome.run_dir.relative_to(ROOT)) if outcome.run_dir else None,
        }
    )
    return outcome.exit_code


def cmd_measure(
    name: str, k: int, first: int, transforms: bool, transform_stage: int, keys: list[str]
) -> int:
    from refute.core.runner import default_workers
    from refute.packs.tess.discover import runs

    loaded, targets, _identity = locked()
    threads = single_thread_environment()
    budget = cap_guard()
    r_inj = json.loads((RUNS / "r_inj.json").read_text("utf-8"))
    randomness = r_inj["beacon"]["randomness"]
    catalogs = (str(ROOT / "calibration" / "v0.4" / "eb_catalog.csv"),)
    scan = str(ROOT / "calibration" / "v0.4" / "eb_catalog_scan.json")
    tasks: list[Any] = []
    for key in keys:
        injections, curves = runs.measurement_tasks(
            targets[key],
            loaded.claim.test_plan,
            CACHE,
            randomness,
            k,
            transform_stage,
            catalogs,
            scan,
            first_injection=first,
            transforms=transforms,
        )
        tasks += injections + curves
    out = PILOT / "measure" / name
    workers = min(default_workers(), len(tasks))
    step = uuid.uuid4().hex
    append_cost(
        {
            "event": "start",
            "step": step,
            "kind": "measure",
            "budget": budget,
            "name": name,
            "targets": keys,
            "k": k,
            "first_injection": first,
            "transforms": transforms,
            "transform_stage": transform_stage,
            "tasks": len(tasks),
            "workers": workers,
            "thread_environment": threads,
            "r_inj_round": r_inj["round"],
            "git_head": head(),
        }
    )
    wall0 = time.monotonic()
    summaries = runs.run_measurements(tasks, out, workers)
    wall = time.monotonic() - wall0
    write_once(out / "summary.json", {"summaries": summaries, "r_inj_round": r_inj["round"]})
    append_cost({"event": "end", "step": step, "kind": "measure", "wall_seconds": wall})
    print(json.dumps(summaries, indent=2, sort_keys=True))
    return 0


def cost_lines() -> list[dict[str, Any]]:
    if not COST.is_file():
        return []
    return [json.loads(line) for line in COST.read_text("utf-8").splitlines() if line]


def step_pairs(lines: list[dict[str, Any]]) -> tuple[dict[str, dict], dict[str, dict]]:
    starts = {line["step"]: line for line in lines if line.get("event") == "start"}
    ends = {line["step"]: line for line in lines if line.get("event") == "end"}
    return starts, ends


def measured_cpu_seconds(name: str) -> float:
    """CPU of a measurement step from its per-task records (kept per chunk, so the tasks of an
    interrupted step that finished are counted)."""
    path = PILOT / "measure" / name / "cost.jsonl"
    if not path.is_file():
        return 0.0
    lines = [json.loads(x) for x in path.read_text("utf-8").splitlines() if x]
    return sum(float(x.get("cpu_seconds") or 0.0) for x in lines)


def hours_used(lines: list[dict[str, Any]]) -> tuple[float, list[str]]:
    """Logical-processor hours of the pilot's steps since the lock, and the steps whose cost is
    not fully known (started, never ended: their known part is counted, the rest is not)."""
    starts, ends = step_pairs(lines)
    seconds, unknown = 0.0, []
    for step, start in starts.items():
        end = ends.get(step)
        if start["kind"] == "measure":
            seconds += measured_cpu_seconds(start["name"])
        elif start["kind"] == "run" and end is not None:
            seconds += float(end["cpu_seconds_upper_bound"])
        elif start["kind"] == "fetch" and end is not None:
            # one process (single-threaded libraries) waiting on the network: its wall time
            seconds += float(end["wall_seconds"])
        if end is None:
            unknown.append(f"{start['kind']} {start.get('run_id') or start.get('name') or step}")
    return seconds / 3600, unknown


def prefix_problems(records: list[dict[str, Any]]) -> list[str]:
    """The prefix must be exactly injections 0..4 at stage 1 and transformed curves 0..2 at
    stage 2 of each control, each once."""
    problems = []
    for key in CONTROLS:
        mine = [r for r in records if r["target_key"] == key]
        injections = sorted((r["index"], r["stage"]) for r in mine if r["kind"] == "injection")
        curves = sorted((r["position"], r["stage"]) for r in mine if r["kind"] == "transform")
        if injections != [(i, 1) for i in range(PREFIX)]:
            problems.append(f"{key}: injections {injections}")
        if curves != [(p, 2) for p in range(3)]:
            problems.append(f"{key}: transformed curves {curves}")
    if {r["target_key"] for r in records} - set(CONTROLS):
        problems.append("records of other targets in the prefix")
    return problems


def run_line(lines: list[dict[str, Any]], stage: int, run_id: str) -> tuple[dict, dict] | None:
    starts, ends = step_pairs(lines)
    for step, start in starts.items():
        if start["kind"] == "run" and start["stage"] == stage and start["run_id"] == run_id:
            return start, ends.get(step) or {}
    return None


def cmd_n_k(stage1_run: str, stage2_run: str, prefix: str) -> int:
    from refute.packs.tess.discover import funnel, runs

    path = RUNS / "n_k.json"
    if path.exists():
        print(f"{path} exists; the (N, K) decision is made once")
        return 1
    _loaded, targets, identity = locked()
    lines = cost_lines()
    found = {
        stage: run_line(lines, stage, rid) for stage, rid in ((1, stage1_run), (2, stage2_run))
    }
    for stage, pair in found.items():
        if pair is None:
            print(f"no stage-{stage} run of the controls")
            return 1
        start, end = pair
        if sorted(start["targets"] or []) != sorted(CONTROLS) or end.get("exit_code") != 0:
            print(f"the stage-{stage} run must hold both controls and be complete")
            return 1
    start1, end1 = found[1]
    if start1["workers"] != 1:
        print("the controls' stage-1 run must have one worker (its CPU time is then exact)")
        return 1
    records = runs.read_records(PILOT / "measure" / prefix / "measurements.jsonl")
    problems = prefix_problems(records)
    if problems:
        print("the measurement prefix is not the protocol's: " + "; ".join(problems))
        return 1
    used, unknown = hours_used(lines)
    if unknown:
        print("steps with a cost not fully known: " + "; ".join(unknown))
        return 1
    injections = [r for r in records if r["kind"] == "injection"]
    curves = [r for r in records if r["kind"] == "transform"]
    hour = 3600.0
    costs = funnel.ControlCosts(
        h_stage1=float(end1["cpu_seconds"]) / len(CONTROLS) / hour,
        # the holdout runs inside the stage-1 analysis (refute discover), so its time is in
        # h_stage1; H(N, K) uses only their sum
        h_holdout=0.0,
        h_injection=sum(float(r["cpu_seconds"]) for r in injections) / len(injections) / hour,
        h_transform=sum(float(r["cpu_seconds"]) for r in curves) / len(curves) / hour,
        bytes_light_curves=sum(cached_bytes(int(targets[key]["tic_id"]), "lc") for key in CONTROLS)
        / len(CONTROLS),
    )
    in_cache = phase_bytes()
    decision = funnel.choose_n_k(costs, used + PRE_LOCK_HOURS, float(sum(in_cache.values())))
    statuses: dict[str, int] = {}
    for record in records:
        label = f"{record['kind']}:{record.get('status')}"
        statuses[label] = statuses.get(label, 0) + 1
    from refute.packs.tess.adapter import manifest_path

    decision["provenance"] = {
        "rule": "PROTOCOL.md section 4.4; costs from the controls' measurement prefix",
        "claim": identity,
        "stage1_run": stage1_run,
        "stage2_run": stage2_run,
        "prefix": prefix,
        "prefix_statuses": statuses,
        "h_stage1_note": "the CPU time of the whole stage-1 run of each control (one worker, in "
        "process): preparation, analysis with the holdout, and the dossier",
        "h_holdout_note": "the holdout runs inside the stage-1 analysis; its time is in h_stage1",
        "h_transform_note": "the controls' transformed curves run the full battery (stage 2), "
        "more than a funnel star's stage-1 curve; an operational assumption, not a measured "
        "bound for every star",
        "hours_used_rule": "the pilot's steps since the lock in .cache/v04/pilot/cost.jsonl (a "
        "parallel run counted as wall x workers + the parent's CPU), plus "
        f"{PRE_LOCK_HOURS} h for the phase before the lock (never metered; the wall time of "
        "the phase's JUnit files, one processor per second, an estimate)",
        "hours_used_since_lock": used,
        "hours_used_before_lock_estimate": PRE_LOCK_HOURS,
        "hours_unmetered": UNMETERED,
        "hours_note": "the metered hours, the estimate before the lock and the unmetered CPU are "
        "reported apart; whether the estimate suffices for the 100-hour cap is the maintainer's "
        "decision, reported to them with this record",
        "bytes_used_rule": "bytes present in the phase's .cache folders "
        + ", ".join(PHASE_FOLDERS)
        + " (the frozen inputs and the downloads); not a peak of occupation",
        "bytes_used_by_folder": in_cache,
        "records_sha256": {
            "cost.jsonl": sha256_file(COST),
            f"measure/{prefix}/measurements.jsonl": sha256_file(
                PILOT / "measure" / prefix / "measurements.jsonl"
            ),
            f"measure/{prefix}/cost.jsonl": sha256_file(PILOT / "measure" / prefix / "cost.jsonl"),
            **{
                f"manifest {key}": sha256_file(manifest_path(CACHE, int(targets[key]["tic_id"])))
                for key in CONTROLS
            },
        },
        "wrapper": {"path": "calibration/v0.4/run_pilot.py", "git_head": head()},
        "decided_utc": utc_now(),
    }
    write_once(path, decision)
    print(json.dumps(decision, indent=2, sort_keys=True))
    return 0 if decision["chosen"] else 3


INPUTS_JSON = "calibration/v0.4/inputs.json"
RUN_SET = "calibration/v0.4/runs/funnel_run_set.json"
ENTRIES = "calibration/v0.4/runs/stage1/entries.json"
N_K = "calibration/v0.4/runs/n_k.json"


def frozen_inputs() -> tuple[dict[str, Any], Path]:
    """inputs.json and the folder of the frozen files it names (the freeze attempt)."""
    from refute.packs.tess.discover import steps

    inputs = json.loads((ROOT / INPUTS_JSON).read_text("utf-8"))
    return inputs, steps.cache_dir(ROOT, inputs)


def stage1_dir(run_id: str) -> Path:
    return PILOT / "stage1" / run_id


def cmd_entries(run_id: str) -> int:
    from refute.packs.tess.discover import pilot, runs

    path = ROOT / ENTRIES
    if path.exists():
        print(f"{path} exists; the stage-1 entries are written once")
        return 1
    _loaded, targets, identity = locked()
    inputs, inputs_dir = frozen_inputs()
    indexes = pilot.catalog_indexes(inputs_dir, inputs)
    run_set = json.loads((ROOT / RUN_SET).read_text("utf-8"))
    entries = runs.stage1_entries(stage1_dir(run_id), run_set, indexes, targets, identity)
    eligible = [e["target_key"] for e in entries if e["eligibility"]["eligible"]]
    write_once(
        path,
        {
            "rule": "PROTOCOL.md sections 6 and 7: refute.packs.tess.discover.runs.stage1_entries "
            "over the run set, from each stage-1 dossier's bytes and the frozen snapshots",
            "claim": identity,
            "stage1_run_dir": stage1_dir(run_id).relative_to(ROOT).as_posix(),
            "run_set": RUN_SET,
            "run_set_sha256": sha256_file(ROOT / RUN_SET),
            "eligible": eligible,
            "entries": entries,
        },
    )
    print(f"{len(entries)} entries, {len(eligible)} eligible: {eligible}")
    return 0


def cmd_promote(results_commit: str, run_id: str) -> int:
    from refute import drand
    from refute.packs.tess.discover import funnel, pilot, steps
    from refute.packs.tess.discover.protocol import PROMOTION

    path = RUNS / "promotion.json"
    if path.exists():
        print(f"{path} exists; the promotion record is written once")
        return 1
    loaded, targets, identity = locked()
    shown = subprocess.run(
        ["git", "show", f"{results_commit}:{ENTRIES}"], cwd=ROOT, capture_output=True, check=False
    )
    if shown.returncode != 0:
        print(f"{ENTRIES} is not in {results_commit}")
        return 1
    entries = json.loads(shown.stdout)["entries"]
    n_k_commit = subprocess.run(
        ["git", "log", "-n", "1", "--format=%H", "--", N_K],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    decision = json.loads((ROOT / N_K).read_text("utf-8"))
    _inputs, inputs_dir = frozen_inputs()
    provenance: dict[str, Any] = {
        "results_commit": results_commit,
        "entries_path": ENTRIES,
        "n_k_commit": n_k_commit,
        "n_k_path": N_K,
        "inputs_json": INPUTS_JSON,
        "inputs_dir": inputs_dir.relative_to(ROOT).as_posix(),
        "stage1_run_dir": stage1_dir(run_id).relative_to(ROOT).as_posix(),
    }
    beacon = None
    eligible = [e for e in entries if e["eligibility"]["eligible"]]
    if len(eligible) > PROMOTION.cap:
        created = pilot.push_run_created_at(results_commit)
        number = drand.round_after(created)
        published = drand.round_time(number)
        if published > datetime.now(UTC):
            print(f"R_prom is round {number}, published at {published.isoformat()}; run after it")
            return 2
        _seed, beacon = drand.drand_seed(number)
        provenance["push_run_created_at"] = created
    record = funnel.promotion_record(
        identity["claim_id"],
        identity["claim_sha256"],
        int(decision["chosen"]["N"]),
        entries,
        beacon,
        provenance,
    )
    run_set = json.loads((ROOT / RUN_SET).read_text("utf-8"))
    inputs_sha = loaded.claim.test_plan["discovery"]["inputs"]["inputs_json"]
    problems = steps.promotion_problems(record, ROOT, identity, run_set, targets, inputs_sha)
    if problems:
        print("the promotion record is refused: " + "; ".join(problems))
        return 1
    write_once(path, record)
    print(f"eligible {record['eligible']}; promoted {record['promoted']}")
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="step", required=True)
    sub.add_parser("r-inj").add_argument("--commit", required=True)
    sub.add_parser("place-tess-eb")
    fetch = sub.add_parser("fetch")
    fetch.add_argument("--stage", type=int, required=True, choices=(1, 2))
    fetch.add_argument("--promotion")
    run = sub.add_parser("run")
    run.add_argument("--stage", type=int, required=True, choices=(1, 2))
    run.add_argument("--run-id", required=True)
    run.add_argument("--workers", type=int, default=1)
    run.add_argument("--promotion")
    run.add_argument("--online", action="store_true")
    measure = sub.add_parser("measure")
    measure.add_argument("--name", required=True)
    measure.add_argument("--k", type=int, required=True)
    measure.add_argument("--first", type=int, default=0)
    measure.add_argument("--no-transforms", action="store_true")
    measure.add_argument("--transform-stage", type=int, required=True, choices=(1, 2))
    for step in (fetch, run, measure):
        step.add_argument("--target", action="append", default=[])
        # a JSON list of target keys, in order (the funnel's run set): a long list is not
        # passed through the launcher's command line
        step.add_argument("--run-set")
    n_k = sub.add_parser("n-k")
    n_k.add_argument("--stage1", required=True)
    n_k.add_argument("--stage2", required=True)
    n_k.add_argument("--prefix", required=True)
    sub.add_parser("entries").add_argument("--run-id", required=True)
    promote = sub.add_parser("promote")
    promote.add_argument("--results-commit", required=True)
    promote.add_argument("--run-id", required=True)
    args = parser.parse_args(argv)
    if args.step == "entries":
        return cmd_entries(args.run_id)
    if args.step == "promote":
        return cmd_promote(args.results_commit, args.run_id)
    if args.step == "r-inj":
        return cmd_r_inj(args.commit)
    if args.step == "place-tess-eb":
        return cmd_place_tess_eb()
    if args.step == "n-k":
        return cmd_n_k(args.stage1, args.stage2, args.prefix)
    keys = list(args.target)
    if args.run_set:
        keys += json.loads(Path(args.run_set).read_text("utf-8"))
    if len(set(keys)) != len(keys):
        parser.error("a target is named twice")
    if not keys and args.step != "run":
        parser.error("name the targets with --target or --run-set")
    if args.step == "fetch":
        return cmd_fetch(args.stage, keys, args.promotion)
    if args.step == "run":
        return cmd_run(
            args.stage, args.run_id, keys or None, args.workers, args.promotion, args.online
        )
    return cmd_measure(
        args.name, args.k, args.first, not args.no_transforms, args.transform_stage, keys
    )


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
