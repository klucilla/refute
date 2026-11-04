"""C2 of the v0.5 calibration: the v0.4 funnel's 100 stars, paired (calibration/v0.5/PROTOCOL.md,
section 4; a reused benchmark, not an independent confirmation).

Per star: its light curves downloaded again into a new cache and checked against the SHA-256
recorded by its v0.4 stage-1 dossier (a changed file makes the star "input changed": counted apart
in the cohort of 100, never run in the paired comparison); then, at stage 1 with the v0.4 claim's
catalogs, both batteries on the same candidate (``discover.paired.paired_chain``) for the original
curve, its 3 transformed curves (1 inverted, 2 per-sector rotations) and its 20 injections, all
regenerated from the v0.4 seeds of R_inj.

**Compatibility** (required infrastructure, plan section 3): the v0.4 battery's outcome of every
curve must equal the v0.4 record of that curve: the stage-1 dossier for an original curve
(candidate period, epoch and SNR; each test's status and emitted severity; the verdict), and the
measurement record for a transformed or injected curve (candidate, gate, verdicts, recovery).
Strings exactly, numbers within a relative ``C2.float_rel_tolerance``. Any mismatch blocks C2: it
is recorded and no curve is excluded to obtain a passing comparison.
"""

from __future__ import annotations

import json
import math
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from refute.packs.tess.calib05.values import C2

V04_DOSSIERS = ".cache/v04/pilot/stage1/funnel-s1"
V04_MEASUREMENTS = ".cache/v04/pilot/measure/funnel/measurements.jsonl"
SURVIVING = ("SURVIVED", "WEAKENED")
KINDS = ("original", "transform", "injection")


@dataclass(frozen=True)
class C2Task:
    """One curve of one star (picklable)."""

    kind: str  # original, transform (slot = position 0, 1, 2) or injection (slot = index)
    target: dict[str, Any]
    test_plan_v04: dict[str, Any]
    cache_dir: str
    slot: int = 0
    seed: int = 0
    k: int = C2.injections_per_curve
    catalog_paths: tuple[str, ...] = field(default_factory=tuple)
    scan_path: str | None = None


def task_id(task: C2Task) -> str:
    return f"{task.target['key']}/{task.kind}/{task.slot}"


def run_task(task: C2Task) -> dict[str, Any]:
    """One curve, both batteries; ``cpu_seconds`` covers the whole task, also when it fails."""
    from refute.packs.tess.adapter import TessAdapter
    from refute.packs.tess.calib05.plans import pair
    from refute.packs.tess.discover import injection as inj
    from refute.packs.tess.discover.measure import load_catalogs, stage_plan, transforms_of
    from refute.packs.tess.discover.paired import paired_chain

    started = time.process_time()
    record: dict[str, Any] = {
        "kind": task.kind,
        "target_key": task.target["key"],
        "slot": task.slot,
    }
    try:
        test_plan = stage_plan(task.test_plan_v04, 1)
        p04, p05 = pair(test_plan)
        cache = Path(task.cache_dir)
        catalogs, scan = load_catalogs(task.catalog_paths, task.scan_path, cache)
        adapter = TessAdapter()
        if task.kind == "original":
            data = adapter.load(task.target, test_plan, cache)
        elif task.kind == "transform":
            transforms, rotations = transforms_of(task.target, cache, task.seed, p04)
            transform = transforms[task.slot]
            record["transform"] = transform.to_dict()
            if transform.kind == "rotate" and (task.slot - 1) in rotations.inconclusive:
                record.update({"status": "INCONCLUSIVE", "reason": "no distinct offsets drawn"})
                record["cpu_seconds"] = time.process_time() - started
                return record
            data = adapter.load(task.target, test_plan, cache, transform=transform)
        elif task.kind == "injection":
            base = adapter.load(task.target, test_plan, cache)
            star = base.star
            drawn = inj.draw_injections(
                task.seed,
                task.k,
                inj.first_time(base),
                star.radius_rsun if star else None,
                star.logg_cgs if star else None,
            )[task.slot]
            record["injection"] = drawn.to_dict()
            data = inj.inject(base, drawn)
        else:
            raise ValueError(f"unknown kind {task.kind!r}")
        chain = paired_chain(data, p04, p05, 1, catalogs, scan)
        record.update({"status": "OK", "chain": chain})
        if task.kind == "injection":
            v04 = chain["v04"]
            record["recovery"] = inj.recovery(drawn, v04["candidate"], v04["gate_passed"])
    except Exception as exc:  # noqa: BLE001 - recorded; the curve stays in its denominators
        record.update({"status": "ERROR", "reason": f"{type(exc).__name__}: {exc}"})
    record["cpu_seconds"] = time.process_time() - started
    return record


def tasks_for(
    target: dict[str, Any],
    test_plan_v04: dict[str, Any],
    cache_dir: Path,
    randomness_inj: str,
    catalog_paths: tuple[str, ...],
    scan_path: str | None,
    k: int = C2.injections_per_curve,
) -> list[C2Task]:
    """The original curve, the 3 transformed curves and the ``k`` injections of one star, with
    the v0.4 seeds of R_inj (``discover.runs.measurement_tasks``)."""
    from refute.packs.tess.discover import injection as inj
    from refute.packs.tess.discover.transforms import stream_seed

    tic = int(target["tic_id"])
    common = {
        "target": target,
        "test_plan_v04": test_plan_v04,
        "cache_dir": str(cache_dir),
        "catalog_paths": tuple(catalog_paths),
        "scan_path": scan_path,
    }
    tr_seed = stream_seed(randomness_inj, "v0.4", "transform", tic)
    inj_seed = inj.stage1_chain_seed(randomness_inj, tic)
    out = [C2Task("original", **common)]
    out += [C2Task("transform", slot=p, seed=tr_seed, **common) for p in range(3)]
    out += [C2Task("injection", slot=i, seed=inj_seed, k=k, **common) for i in range(k)]
    return out


# --- inputs and compatibility -----------------------------------------------------------------


def input_problems(new_manifest: dict[str, Any], old_manifest: dict[str, Any]) -> list[str]:
    """The files of the new download whose SHA-256 differs from the v0.4 dossier's record, or
    that one side lacks (by file name)."""
    new = {f["name"]: f["sha256"] for f in new_manifest.get("files", [])}
    old = {f["name"]: f["sha256"] for f in old_manifest.get("files", [])}
    problems = [f"missing now: {n}" for n in sorted(set(old) - set(new))]
    problems += [f"new file: {n}" for n in sorted(set(new) - set(old))]
    problems += [f"other bytes: {n}" for n in sorted(set(old) & set(new)) if old[n] != new[n]]
    return problems


def _close(a: Any, b: Any) -> bool:
    if isinstance(a, float | int) and isinstance(b, float | int):
        if a == b:
            return True
        scale = max(abs(float(a)), abs(float(b)))
        return math.isfinite(scale) and abs(float(a) - float(b)) <= C2.float_rel_tolerance * scale
    return a == b


def _compare(path: str, mine: Any, ref: Any, out: list[str]) -> None:
    if isinstance(ref, dict):
        if not isinstance(mine, dict):
            out.append(f"{path}: {mine!r} != {ref!r}")
            return
        for key in ref:
            _compare(f"{path}.{key}", mine.get(key), ref[key], out)
    elif isinstance(ref, list):
        if not isinstance(mine, list) or len(mine) != len(ref):
            out.append(f"{path}: {mine!r} != {ref!r}")
            return
        for i, (a, b) in enumerate(zip(mine, ref, strict=True)):
            _compare(f"{path}[{i}]", a, b, out)
    elif not _close(mine, ref):
        out.append(f"{path}: {mine!r} != {ref!r}")


def dossier_reference(verdict: dict[str, Any]) -> dict[str, Any]:
    """What a v0.4 stage-1 dossier records of the v0.4 battery: the candidate, each test's
    status and emitted severity (the holdout, a diagnostic outside the paired chain, left out),
    and the verdict."""
    cand = verdict.get("candidate") or None
    return {
        "candidate": None
        if not cand
        else {"period_days": cand["period"], "t0_btjd": cand["t0"], "snr": cand["snr"]},
        "tests": {
            t["name"]: {"status": t["status"], "severity": t["severity"]}
            for t in verdict.get("tests", [])
            if t["name"] != "holdout_by_year"
        },
        "verdict": verdict.get("verdict"),
    }


MEASUREMENT_FIELDS = (
    "candidate",
    "tests",
    "deferred",
    "catalog_test",
    "verdict",
    "verdict_reason",
    "stage_tests",
    "stage_verdict",
    "stage_verdict_reason",
    "gate_passed",
)


def measurement_reference(record: dict[str, Any]) -> dict[str, Any]:
    """What a v0.4 measurement record holds of the v0.4 battery (its ``chain`` fields shared
    with the paired chain), and the recovery of an injection."""
    chain = record.get("chain") or {}
    out = {"chain": {k: chain[k] for k in MEASUREMENT_FIELDS if k in chain}}
    if record["kind"] == "injection":
        out["recovery"] = {k: record["recovery"][k] for k in ("recovered", "alias")}
        out["injection"] = record["injection"]
    return out


def compat_problems(record: dict[str, Any], reference: dict[str, Any]) -> list[str]:
    """Why a C2 record's v0.4 battery differs from its v0.4 reference (empty when equal)."""
    if record.get("status") != "OK":
        return [f"the C2 task did not complete: {record.get('reason')}"]
    out: list[str] = []
    v04 = record["chain"]["v04"]
    if record["kind"] == "original":
        _compare("candidate", v04["candidate"], reference["candidate"], out)
        _compare("tests", v04["tests"], reference["tests"], out)
        _compare("verdict", v04["verdict"], reference["verdict"], out)
        missing = sorted(set(v04["tests"]) - set(reference["tests"]))
        if missing:
            out.append(f"tests not in the dossier: {missing}")
    else:
        _compare("chain", v04, reference["chain"], out)
        if record["kind"] == "injection":
            _compare("injection", record.get("injection"), reference["injection"], out)
            _compare(
                "recovery",
                {k: record["recovery"][k] for k in ("recovered", "alias")},
                reference["recovery"],
                out,
            )
    return out


V04_SEALS = "calibration/v0.4/runs/stage1/seals.json"
V04_RECORDS = "calibration/v0.4/runs/stage1/records.json"
MEASUREMENTS_KEY = "measure/funnel/measurements.jsonl"


def reference_problems(root: Path) -> list[str]:
    """Why the external v0.4 references cannot be used (empty when they can): the stage-1
    dossiers must be exactly the stars of the committed seal record
    (``calibration/v0.4/runs/stage1/seals.json``, a bound path of the freeze), each dossier's sealed
    core (everything but ``SEAL.json`` and the annexes, so its ``verdict.json`` and
    ``data/manifest.json`` included) must have the recorded SHA-256, and the measurement records
    must have the SHA-256 that ``calibration/v0.4/runs/stage1/records.json`` records."""
    import hashlib

    from refute.core.seal import core_sha256

    root = Path(root)
    seals = json.loads((root / V04_SEALS).read_text(encoding="utf-8"))["core_sha256"]
    recorded = json.loads((root / V04_RECORDS).read_text(encoding="utf-8"))["records_sha256"]
    base = root / V04_DOSSIERS
    present = {p.name for p in base.iterdir() if p.is_dir()} if base.is_dir() else set()
    problems = [f"no dossier: {k}" for k in sorted(set(seals) - present)]
    problems += [f"unexpected dossier: {k}" for k in sorted(present - set(seals))]
    for key in sorted(set(seals) & present):
        if core_sha256(base / key) != seals[key]:
            problems.append(f"{key}: its sealed core differs from the recorded SHA-256")
    path = root / V04_MEASUREMENTS
    if not path.is_file():
        problems.append(f"missing {V04_MEASUREMENTS}")
    elif hashlib.sha256(path.read_bytes()).hexdigest() != recorded[MEASUREMENTS_KEY]:
        problems.append(f"{V04_MEASUREMENTS} differs from the recorded SHA-256")
    return problems


def references(root: Path) -> tuple[dict[str, dict], dict[str, dict]]:
    """The v0.4 references, refused unless ``reference_problems`` is empty: per star its dossier
    (``dossier_reference`` and its data manifest), and per transformed or injected curve its
    measurement record."""
    problems = reference_problems(root)
    if problems:
        raise ValueError("the v0.4 references are not authenticated: " + "; ".join(problems[:5]))
    dossiers = {}
    base = Path(root) / V04_DOSSIERS
    for folder in sorted(p for p in base.iterdir() if p.is_dir()):
        verdict = json.loads((folder / "verdict.json").read_text(encoding="utf-8"))
        manifest = json.loads((folder / "data" / "manifest.json").read_text(encoding="utf-8"))
        dossiers[folder.name] = {"reference": dossier_reference(verdict), "manifest": manifest}
    measurements = {}
    text = (Path(root) / V04_MEASUREMENTS).read_text(encoding="utf-8")
    for line in text.splitlines():
        if not line:
            continue
        r = json.loads(line)
        slot = r["index"] if r["kind"] == "injection" else r["position"]
        measurements[f"{r['target_key']}/{r['kind']}/{slot}"] = measurement_reference(r)
    return dossiers, measurements


# --- the summaries and the targets ------------------------------------------------------------


def _surviving(records: list[dict[str, Any]], battery: str) -> int:
    return sum(
        r["chain"][battery]["gate_passed"] and r["chain"][battery]["stage_verdict"] in SURVIVING
        for r in records
        if r.get("status") == "OK"
    )


def _rule(decidable: bool, passed: bool) -> str:
    if not decidable:
        return "NOT DECIDABLE"
    return "PASS" if passed else "FAIL"


def summarize(
    records: list[dict[str, Any]],
    input_changed: dict[str, list[str]],
    development: set[str],
    compat: dict[str, list[str]],
) -> dict[str, Any]:
    """The C2 report: the cohort, the compatibility state, the originals (all stars and the
    prespecified subset without the development stars), the transformed curves and the
    injections by host, and the targets T2a to T2c (each PASS, FAIL or NOT DECIDABLE; none
    blocks the phase). With any compatibility mismatch, no target is evaluated."""
    from refute.packs.tess.discover.paired import (
        injection_groups,
        transformed_groups,
    )
    from refute.packs.tess.discover.paired import (
        summarize as group_summary,
    )

    originals = [r for r in records if r["kind"] == "original"]
    own_signal = {
        r["target_key"]
        for r in originals
        if r.get("status") == "OK" and r["chain"]["v04"]["gate_passed"]
    }
    transforms = [{**r, "position": r["slot"]} for r in records if r["kind"] == "transform"]
    injections = [r for r in records if r["kind"] == "injection"]
    mismatches = {k: v for k, v in compat.items() if v}
    out: dict[str, Any] = {
        "cohort": {
            "stars": C2.stars,
            "input_changed": dict(sorted(input_changed.items())),
            "authenticated": C2.stars - len(input_changed),
            "statement": "every C2 result is conditional on the authenticated available inputs",
        },
        "compatibility": {
            "curves_checked": len(compat),
            "mismatches": dict(sorted(mismatches.items())),
            "state": "blocked" if mismatches else "established",
        },
        "originals_all": group_summary(originals, "originals (all authenticated stars)"),
        "originals_subset": group_summary(
            [r for r in originals if r["target_key"] not in development],
            "originals (without the development stars)",
        ),
        "transformed": transformed_groups(transforms, own_signal),
        "injections": injection_groups(injections, own_signal),
        "development_stars": sorted(development),
    }
    if mismatches:
        out["targets"] = {"state": "not evaluated: compatibility is not established"}
        return out
    floor = C2.not_decidable_below
    neg = out["injections"]["original_gate_negative"]["among_recovered"]
    n = neg["denominator"]
    s04 = neg["v04_stage_verdicts"]["SURVIVED"] + neg["v04_stage_verdicts"]["WEAKENED"]
    s05 = neg["v05_stage_verdicts"]["SURVIVED"] + neg["v05_stage_verdicts"]["WEAKENED"]
    targets: dict[str, Any] = {
        "T2a": {
            "denominator": n,
            "v04_survival": s04 / n if n else None,
            "v05_survival": s05 / n if n else None,
            "result": _rule(n >= floor, n > 0 and s05 / n >= s04 / n - C2.t2a_margin),
        }
    }
    for kind in ("inverted", "rotated"):
        group = [r for r in transforms if (r["slot"] == 0) == (kind == "inverted")]
        v04, v05 = _surviving(group, "v04"), _surviving(group, "v05")
        targets[f"T2b-{kind}"] = {
            "denominator": len(group),
            "v04_surviving_detections": v04,
            "v05_surviving_detections": v05,
            "result": _rule(len(group) >= floor, v05 <= v04),
        }
    subset = [
        r for r in originals if r["target_key"] not in development and r.get("status") == "OK"
    ]
    v04 = sum(r["chain"]["v04"]["stage_verdict"] == "SURVIVED" for r in subset)
    v05 = sum(r["chain"]["v05"]["stage_verdict"] == "SURVIVED" for r in subset)
    targets["T2c"] = {
        "denominator": len(subset),
        "v04_survived": v04,
        "v05_survived": v05,
        "result": _rule(len(subset) >= floor, v05 <= v04),
    }
    out["targets"] = targets
    return out
