"""v0.2.1 workers equivalence: the same locked synthetic calibration run with
``--workers 3``, ``--workers 1`` (also with BLAS thread variables preset to 4) and the
per-target REPRODUCE.md command, each in a new independent process. Criteria E0-E3 of
docs/validation/v0.2.1/workers-equivalence-acceptance.md (with Amendments 1 and 2).

Level (a), the REPRODUCE.md contract (``check_dossier``), decides. Level (b), exact
equality after removing only the allowed operational differences, and the reports and
plots are recorded as diagnostics (a warning and a JSON report), never as failures.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import warnings
from pathlib import Path

import pytest

from conftest import calibration_claim, git, target_entry, targets_file, write_yaml
from refute.core.codehash import compute_code_hash
from refute.core.dossier import check_dossier
from refute.core.lock import create_lock
from refute.packs.tess.synthetic import scenario_data, write_synthetic_cache

TARGETS = {
    11: ("planet", "planet", 3.7),
    12: ("eb_secondary", "false_positive", 2.9),
    13: ("vanishing", "planet", 3.7),
}
KEYS = [f"TIC-{tic}" for tic in TARGETS]
THREAD_VARS = ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS")
PRESET = {"OMP_NUM_THREADS": "4", "OPENBLAS_NUM_THREADS": "4", "MKL_NUM_THREADS": "4"}
RUNTIME_FILE = "environment/numeric_runtime.json"
MARKER = "<RUN_DIR>"
# Literal, not imported: the test must also run against the v0.2 lock (cc9d104), which
# predates REFUTE_WORKERS.
WORKERS_ENV = "REFUTE_WORKERS"
# Legacy mode, only for the declared one-off run against cc9d104 (Amendment 2, item 2):
# E2 then requires the record to be ABSENT and the code under test to have the code hash
# locked in cc9d104; anything else fails.
LEGACY = os.environ.get("REFUTE_EQUIVALENCE_LEGACY_CODE") == "1"
ROOT = Path(__file__).resolve().parents[1]
V02_LOCK = ROOT / "calibration" / "v0.2" / "self_claim.lock.json"
V02_CODE_SHA256 = "2cd8b5c16c9ded3e32335cd95d8b68f46e0676d5183f3129a6cef4e8dfbd1752"
CLI = "import sys; from refute.cli import main; sys.argv[0] = 'refute'; main()"


def _execute(
    claim: Path,
    cwd: Path,
    out: Path,
    run_id: str,
    workers: int,
    cache: Path,
    target: str | None = None,
    preset: dict[str, str] | None = None,
) -> Path:
    """One execution in a new process. The environment is the test process's without
    REFUTE_WORKERS and without the four thread variables (an explicit, repeatable base),
    plus ``preset`` (F4 only)."""
    removed = {WORKERS_ENV, *THREAD_VARS}
    env = {k: v for k, v in os.environ.items() if k not in removed}
    env.update(preset or {})
    args = [
        sys.executable,
        "-c",
        CLI,
        "calibrate",
        "--claim",
        str(claim),
        "--out",
        str(out),
        "--run-id",
        run_id,
        "--workers",
        str(workers),
        "--offline",
        "--cache-dir",
        str(cache),
    ]
    if target:
        args += ["--target", target]
    done = subprocess.run(args, cwd=cwd, env=env, capture_output=True, text=True)
    assert done.returncode == 0, f"{run_id} failed:\n{done.stdout}\n{done.stderr}"
    return out / run_id


@pytest.fixture(scope="module")
def runs(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("workers")
    repo = tmp / "repo"
    repo.mkdir()
    git(repo, "init", "-q")
    cache = tmp / "cache"
    for tic, (scenario, _kind, _period) in TARGETS.items():
        data = scenario_data(scenario, 0)
        write_synthetic_cache(cache, tic, data.lc, data.star, aux=data.aux)
    targets = [target_entry(tic, kind, period) for tic, (_s, kind, period) in TARGETS.items()]
    write_yaml(repo / "calibration" / "targets.yaml", targets_file(targets))
    claim = write_yaml(
        repo / "calibration" / "claim.yaml",
        calibration_claim(
            2, 1, min_recovered_planets=0, min_flagged_false_positives=0, max_refuted_planets=2
        ),
    )
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "synthetic calibration")
    create_lock(claim)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "lock")
    out = tmp / "out"
    runs = {"O": _execute(claim, repo, out, "O", 3, cache)}
    _check_premises(runs["O"])
    runs |= {
        "F": _execute(claim, repo, out, "F", 1, cache),
        "F4": _execute(claim, repo, out, "F4", 1, cache, preset=PRESET),
    }
    for key in KEYS:
        runs[f"R{key[4:]}"] = _execute(claim, repo, out, f"R{key[4:]}", 1, cache, target=key)
    return {"runs": runs, "report": tmp / "workers_equivalence_report.json"}


def _verdict(dossier: Path) -> dict:
    return json.loads((dossier / "verdict.json").read_text(encoding="utf-8"))


def _check_premises(original: Path) -> None:
    """E0: the scenarios represent what they should, in O, before any comparison."""
    planet, fp, vanishing = (_verdict(original / key) for key in KEYS)

    def holdout(verdict):
        return next(t for t in verdict["tests"] if t["name"] == "holdout_by_year")

    assert holdout(planet)["status"] == "PASS", "premise: planet blind holdout PASS"
    assert any(r["access_log"] for r in planet["holdout_rounds"]), "premise: a round read"
    assert holdout(vanishing)["status"] == "FAIL", "premise: vanishing blind holdout FAIL"
    assert fp["verdict"] == "REFUTED", f"premise: false positive REFUTED, got {fp['verdict']}"
    flagged = _summary(original)["self_claim"]["criteria"][1]
    assert flagged["value"] == 1, f"premise: the false positive is flagged, got {flagged}"


def _dossiers(runs):
    """(execution, target key, dossier) for every comparison with O."""
    for name in ("F", "F4"):
        for key in KEYS:
            yield name, key, runs[name] / key
    for key in KEYS:
        yield f"R{key[4:]}", key, runs[f"R{key[4:]}"] / key


# --- E1: level (a), the REPRODUCE.md contract --------------------------------------------


def test_e1_reproduce_contract_holds_for_every_execution(runs):
    original = runs["runs"]["O"]
    failures = []
    for name, key, dossier in _dossiers(runs["runs"]):
        result = check_dossier(dossier, against=original / key)
        if not result.ok:
            failures.append((name, key, result.integrity_problems, result.differences))
    assert failures == []


def _summary(run_dir):
    return json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("name", ["F", "F4"])
def test_e1_full_run_summaries_agree(runs, name):
    o, other = _summary(runs["runs"]["O"]), _summary(runs["runs"][name])
    assert other["self_claim"]["result"] == o["self_claim"]["result"]
    assert [c["value"] for c in other["self_claim"]["criteria"]] == [
        c["value"] for c in o["self_claim"]["criteria"]
    ]
    assert {r["target"]: r["verdict"] for r in other["targets"]} == {
        r["target"]: r["verdict"] for r in o["targets"]
    }


# --- E2: the numerical runtime is recorded ------------------------------------------------


NOT_MEASURED = "the BLAS question is NOT MEASURED"


def _all_dossiers(runs):
    for name, run_dir in runs.items():
        for key in KEYS if not name.startswith("R") else [f"TIC-{name[1:]}"]:
            yield name, key, run_dir / key


def test_e2_numeric_runtime_is_recorded_in_every_dossier(runs):
    records = {}
    if LEGACY:
        code = compute_code_hash().sha256
        assert code == V02_CODE_SHA256, f"legacy mode on code {code}, not the v0.2 lock"
        if V02_LOCK.is_file():
            locked = json.loads(V02_LOCK.read_text(encoding="utf-8"))["code"]["sha256"]
            assert locked == V02_CODE_SHA256, "the v0.2 lock file disagrees"
        for name, key, dossier in _all_dossiers(runs["runs"]):
            assert not (dossier / RUNTIME_FILE).is_file(), f"legacy mode, but {name}/{key} has it"
            records[f"{name}/{key}"] = "absent (code locked in cc9d104)"
        _append_report(runs["report"], "numeric_runtime", records)
        return
    for name, key, dossier in _all_dossiers(runs["runs"]):
        path = dossier / RUNTIME_FILE
        assert path.is_file(), f"missing {path}: {NOT_MEASURED}"
        record = json.loads(path.read_text(encoding="utf-8"))
        for field in (
            "process",
            "thread_env",
            "numpy_version",
            "blas",
            "threadpoolctl_available",
            "threadpools",
        ):
            assert field in record, (name, key, field)
        assert set(record["thread_env"]) == set(THREAD_VARS)
        assert record["process"] == ("worker" if name == "O" else "main"), (name, key)
        assert record["threadpoolctl_available"] is True, f"{name}/{key}: {NOT_MEASURED}"
        assert isinstance(record["blas"], str) and record["blas"], f"{name}/{key}: {NOT_MEASURED}"
        pools = record["threadpools"]
        assert isinstance(pools, list) and pools, f"{name}/{key}: no thread pool, {NOT_MEASURED}"
        for pool in pools:
            threads = pool.get("num_threads")
            valid = isinstance(threads, int) and not isinstance(threads, bool) and threads >= 1
            assert valid, f"{name}/{key}: invalid thread count {pool}, {NOT_MEASURED}"
        blas_pools = [p for p in pools if p.get("user_api") == "blas"]
        assert blas_pools, f"{name}/{key}: no BLAS pool reported, {NOT_MEASURED}"
        if name == "F4":
            effective = [p["num_threads"] for p in blas_pools]
            assert all(n == 4 for n in effective), f"F4/{key}: effective BLAS threads {effective}"
        records[f"{name}/{key}"] = {
            "process": record["process"],
            "thread_env": record["thread_env"],
            "blas": record["blas"],
            "threadpools": [
                {k: p.get(k) for k in ("user_api", "internal_api", "version", "num_threads")}
                for p in pools
            ],
        }
    _append_report(runs["report"], "numeric_runtime", records)
    print(json.dumps(records, indent=1))


# --- E3: level (b) and reports/plots, recorded --------------------------------------------


def _replace_run_dir(text: str, run_dir: Path) -> str:
    """Exact replacement of this execution's run-directory path (its native and POSIX
    spellings, as a run writes them) by MARKER. Nothing else is normalized."""
    return text.replace(str(run_dir), MARKER).replace(run_dir.as_posix(), MARKER)


def _strings(node, run_dir: Path):
    if isinstance(node, dict):
        return {k: _strings(v, run_dir) for k, v in node.items()}
    if isinstance(node, list):
        return [_strings(v, run_dir) for v in node]
    return _replace_run_dir(node, run_dir) if isinstance(node, str) else node


def _normalized_json(path: Path, run_dir: Path, drop: list[tuple[str, ...]]) -> object:
    data = _strings(json.loads(path.read_text(encoding="utf-8")), run_dir)
    for keys in drop:
        node = data
        for k in keys[:-1]:
            node = node.get(k, {}) if isinstance(node, dict) else {}
        if isinstance(node, dict):
            node.pop(keys[-1], None)
    return data


def _differences(a, b, where=""):
    if isinstance(a, dict) and isinstance(b, dict):
        out = []
        for k in sorted(set(a) | set(b), key=str):
            if k not in a or k not in b:
                out.append(f"{where}/{k}: present in only one")
            else:
                out += _differences(a[k], b[k], f"{where}/{k}")
        return out
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            return [f"{where}: lengths {len(a)} != {len(b)}"]
        out = []
        for i, (x, y) in enumerate(zip(a, b, strict=True)):
            out += _differences(x, y, f"{where}[{i}]")
        return out
    return [] if a == b else [f"{where}: {a!r} != {b!r}"]


def _append_report(path: Path, section: str, content) -> None:
    report = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
    report[section] = content
    path.write_text(json.dumps(report, indent=1, sort_keys=True), encoding="utf-8")


def test_e3_exact_equality_is_recorded(runs):
    o = runs["runs"]["O"]
    found = {}
    for name, key, dossier in _dossiers(runs["runs"]):
        a = _normalized_json(
            dossier / "verdict.json", runs["runs"][name], [("provenance", "run_id")]
        )
        b = _normalized_json(o / key / "verdict.json", o, [("provenance", "run_id")])
        diffs = _differences(a, b)
        if diffs:
            found[f"{name}/{key}/verdict.json"] = diffs
    run_fields = [("run", f) for f in ("run_id", "started_utc", "finished_utc", "workers")]
    for name in ("F", "F4"):
        a = _normalized_json(runs["runs"][name] / "summary.json", runs["runs"][name], run_fields)
        b = _normalized_json(o / "summary.json", o, run_fields)
        diffs = _differences(a, b)
        if diffs:
            found[f"{name}/summary.json"] = diffs
    _append_report(runs["report"], "exact_equality", found)
    if found:
        warnings.warn(f"level (b) differences (not failures): {json.dumps(found)}", stacklevel=1)


def test_e3_reports_and_plots_are_recorded(runs):
    o = runs["runs"]["O"]
    found = {}
    for name, key, dossier in _dossiers(runs["runs"]):

        def lines(path, run_dir):
            text = _replace_run_dir(path.read_text(encoding="utf-8"), run_dir)
            return [ln for ln in text.splitlines() if not ln.startswith("- Run: `")]

        if lines(dossier / "report.md", runs["runs"][name]) != lines(o / key / "report.md", o):
            found[f"{name}/{key}/report.md"] = "differs"
        for png in sorted((o / key / "plots").glob("*.png")):
            other = dossier / "plots" / png.name
            if not other.is_file() or other.read_bytes() != png.read_bytes():
                found[f"{name}/{key}/plots/{png.name}"] = "differs"
    _append_report(runs["report"], "reports_and_plots", found)
    if found:
        warnings.warn(f"report/plot differences (not failures): {json.dumps(found)}", stacklevel=1)
