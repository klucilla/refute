"""D6: test of systematic dependence of the analysis (D6-proposta.md, revision 4).

Detects systematic dependence of the scientific result on the process history, the order
of the cases, the partition between workers and the NumPy dispatch target, **in the
contrasts of the declared matrix only**. A negative result holds only for those contrasts
and the inputs exercised. It is not a detector of the rare event of D7.

It uses the record builder of ``population_v2.py`` (the complete scientific record, typed)
and its comparator (profiles ``d6-science`` and ``d6-control``), and adds to every record,
in every configuration, the control section ``/control/cases_before_in_process``.

Subcommands (``python d6.py <sub> --help``):

- ``plan``: the D6 declaration: the closed list of cases (rule ``select_cases``, from an
  accepted manifest of the ``determinism`` population), the 7 configurations with their
  declared assignment (process positions and ordered case lists, no PIDs), the dispatch
  table declared for each variant, the points and the repetitions.
- ``run``: one configuration, repetition and point: the declared processes, each analyzing
  its list in order; records and the execution record (observed identification).
- ``check``: check 1 (observed configuration and sequence against the declaration), the
  conditions of a valid conclusion, check 2 (``d6-science``) and the control pass
  (``d6-control``); the result PASS, FAIL or INCOMPLETE.
- ``negative-control``: injected differences in copies of records (located by
  ``d6-science``) and a wrong configuration injected in a copy of E's execution record
  (refused by check 1).

Inputs: the cases of the declaration, generated in K = 3 new processes as a diagnostic
campaign of ``population_v2.py`` (identical in every segment and block, accepted by
``check-set``), then written to a cache by ``regenerate``; every input is checked by hash
against the accepted manifest before each execution.
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import copy
import hashlib
import multiprocessing
import os
import struct
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import population_v2 as v2  # noqa: E402

CMP = v2.CMP
D6_PATH = Path(__file__).resolve()
D6_SHA256 = hashlib.sha256(D6_PATH.read_bytes()).hexdigest()
DECLARATION_FORMAT = "refute-population-d6/1"
EXECUTION_FORMAT = "refute-population-d6-execution/1"
REPORT_FORMAT = "refute-population-d6-report/1"
CONFIGURATIONS = ("F", "R-idx", "R-rev", "R-shf", "P24", "P12", "E")
E_ENVIRONMENT = {"NPY_DISABLE_CPU_FEATURES": "X86_V3"}
CONTRASTS = (
    ("F", "R-idx"),
    ("R-rev", "R-idx"),
    ("R-shf", "R-idx"),
    ("P24", "P12"),
    ("E", "R-idx"),
    ("P24", "F"),
)
SHUFFLE_SEED = 20261012


# --- the closed list of cases ------------------------------------------------------------


def _commensurate_margin(p1: float, p2: float) -> float:
    ratio = p1 / p2
    return min(abs(ratio - p / q) for q in range(1, 5) for p in range(1, 81))


def select_cases(manifest: dict, n: int = 40) -> list[str]:
    """The declared rule, applied to the generation parameters of an accepted manifest of
    the ``determinism`` population (never to analysis results), in this order until ``n``
    distinct cases: the mechanisms that diverged in the v1 generations (two cases each);
    one case per class, noise model and mechanism; per class with a transit, the cases with
    the expected-SNR ratio r just above and just below 1.0 and 1.5; the two masked-variability
    cases with the smallest margin to a commensurate ratio; then the remaining cases by id."""
    cases = sorted(manifest["cases"], key=lambda e: e["id"])
    chosen: list[str] = []

    def add(ids):
        for i in ids:
            if i not in chosen and len(chosen) < n:
                chosen.append(i)

    def where(**kw):
        return [e for e in cases if all(e.get(k) == v for k, v in kw.items())]

    add(
        [
            e["id"]
            for e in where(
                **{"class": "planet", "band": "below", "noise": "white", "mechanism": "two_years"}
            )
        ][:2]
    )
    add(
        [
            e["id"]
            for e in where(
                **{"class": "planet", "band": "below", "noise": "white", "mechanism": "three_years"}
            )
        ][:2]
    )
    add(
        [
            e["id"]
            for e in where(
                **{"class": "no_transit", "noise": "white", "mechanism": "trend_variability"}
            )
        ][:2]
    )
    for cls in ("planet", "false_positive", "no_transit"):
        for noise in ("white", "correlated"):
            for mech in sorted({e["mechanism"] for e in where(**{"class": cls})}):
                add(
                    [e["id"] for e in where(**{"class": cls, "noise": noise, "mechanism": mech})][
                        :1
                    ]
                )
    for cls in ("planet", "false_positive"):
        group = [e for e in where(**{"class": cls}) if "r_actual" in e["parameters"]]
        for threshold in (1.0, 1.5):
            above = sorted(
                (e for e in group if e["parameters"]["r_actual"] >= threshold),
                key=lambda e: e["parameters"]["r_actual"],
            )
            below = sorted(
                (e for e in group if e["parameters"]["r_actual"] < threshold),
                key=lambda e: -e["parameters"]["r_actual"],
            )
            add([e["id"] for e in above[:1] + below[:1]])
    masked = [
        e for e in where(**{"mechanism": "variability_masked"}) if "var_period" in e["parameters"]
    ]
    masked.sort(
        key=lambda e: _commensurate_margin(e["parameters"]["period"], e["parameters"]["var_period"])
    )
    add([e["id"] for e in masked[:2]])
    add([e["id"] for e in cases])
    return chosen


def assignment(configuration: str, cases: list[str]) -> list[list[str]]:
    """The declared assignment: for each process position, its ordered list of cases."""
    if configuration == "F":
        return [[c] for c in cases]
    if configuration in ("R-idx", "E"):
        return [list(cases)]
    if configuration == "R-rev":
        return [list(reversed(cases))]
    if configuration == "R-shf":
        return [v2._ordered(list(cases), f"shuffle:{SHUFFLE_SEED}")]
    if configuration in ("P24", "P12"):
        w = 24 if configuration == "P24" else 12
        return [cases[k::w] for k in range(w) if cases[k::w]]
    raise SystemExit(f"unknown configuration {configuration}")


def control_values(configuration: str, cases: list[str]) -> dict[str, int]:
    """The declared value of /control/cases_before_in_process for every case."""
    out = {}
    for lst in assignment(configuration, cases):
        for k, c in enumerate(lst):
            out[c] = k
    return out


# --- plan --------------------------------------------------------------------------------


def mode_plan(args) -> int:
    target = Path(args.out)
    if target.exists():
        raise SystemExit(f"{target} exists; it is never replaced")
    manifest = v2.read_json(Path(args.selection_manifest))
    if manifest.get("population") != "determinism":
        raise SystemExit("the selection manifest is not of the determinism population")
    cases = select_cases(manifest, 40)
    if args.limit:
        cases = cases[: args.limit]
    default = v2.read_json(Path(args.dispatch_default))
    e_table = v2.read_json(Path(args.dispatch_e))
    if e_table["environment"] != E_ENVIRONMENT:
        raise SystemExit(f"the E table was not read under {E_ENVIRONMENT}")
    decl = {
        "format": DECLARATION_FORMAT,
        "d6_sha256": D6_SHA256,
        "harness_sha256": v2.HARNESS_SHA256,
        "comparator": CMP.identity(),
        "smoke": bool(args.limit),
        "note": (
            f"SMOKE RUN OF THE D6 MACHINERY WITH {len(cases)} CASES: NOT THE D6 "
            "(which has 40 cases at M0 and M3)"
            if args.limit
            else "the D6 of D6-proposta.md, revision 4"
        ),
        "inputs": {"campaign_root": args.inputs_root, "campaign_id": args.inputs_campaign},
        "selection": {
            "manifest_sha256": v2.file_sha256(Path(args.selection_manifest)),
            "rule": select_cases.__doc__,
        },
        "cases": cases,
        "points": args.points,
        "repetitions": [1, 2],
        "configurations": {
            name: {
                "assignment": assignment(name, cases),
                "control_values": control_values(name, cases),
                "dispatch": {
                    "environment": E_ENVIRONMENT if name == "E" else default["environment"],
                    "table": (e_table if name == "E" else default)["table"],
                },
            }
            for name in CONFIGURATIONS
        },
        "contrasts": [list(c) for c in CONTRASTS],
        "shuffle_seed": SHUFFLE_SEED,
        "result_rule": (
            "PASS only with the six conditions of a valid conclusion and no difference in "
            "check 2; FAIL on any scientific difference, a control that does not report what "
            "it should, or a record with status error; INCOMPLETE on a missing analysis, an "
            "execution invalidated by check 1, an external interruption, or an input that "
            "does not match its hash (redone from the start, in full)."
        ),
    }
    sha = v2.write_json(target, decl)
    print(f"D6 declaration {target}: {len(cases)} cases; SHA-256 {sha}")
    return 0


# --- run ---------------------------------------------------------------------------------


def _init(declared_dispatch: dict) -> None:
    from refute.core.runner import init_worker

    init_worker()


def d6_task(task: tuple) -> dict:
    """One declared process position: analyze its list in order, adding the control
    section to every record."""
    position, entries, cache, run_dir, identity, declared_dispatch = task
    table, digest, problems = v2.dispatch_problems(declared_dispatch)
    problems += v2.single_thread_problems()
    sequence, written = [], []
    for k, entry in enumerate(entries):
        out = Path(run_dir) / "cases" / f"{entry['id']}.json"
        try:
            blob = v2.read_input(Path(cache), entry)
        except (v2.IntegrityEventError, v2.InfrastructureError) as exc:
            return {
                "position": position,
                "pid": os.getpid(),
                "sequence": sequence,
                "input_problem": f"{entry['id']}: {exc}",
                "dispatch_problems": problems,
            }
        record = v2.analysis_record(entry, blob, identity, k)
        record["control"] = {"cases_before_in_process": k}
        data = v2.record_bytes(record)
        v2.write_atomic(out, data)
        sequence.append([os.getpid(), k, entry["id"]])
        written.append(hashlib.sha256(data).hexdigest())
    return {
        "position": position,
        "pid": os.getpid(),
        "sequence": sequence,
        "configuration": v2.worker_configuration(),
        "dispatch_table_sha256": digest,
        "dispatch_problems": problems,
        "records_sha256": written,
    }


def _inputs(decl: dict) -> tuple[dict, dict]:
    camp = v2.open_campaign(decl["inputs"]["campaign_root"], decl["inputs"]["campaign_id"])
    entries, _ = v2.read_journal(camp)
    acc = v2.accepted_set(entries)
    if acc is None:
        raise SystemExit("the inputs campaign has no accepted set")
    path = Path(acc["payload"]["manifest"])
    if v2.file_sha256(path) != acc["payload"]["manifest_sha256"]:
        raise SystemExit("the accepted inputs manifest differs from the journal")
    manifest = v2.read_json(path)
    return {e["id"]: e for e in manifest["cases"]}, acc


def run_one(
    decl: dict, decl_sha: str, configuration: str, rep: int, point: str, cache: Path, out_root: Path
) -> dict:
    by_id, acc = _inputs(decl)
    cfg = decl["configurations"][configuration]
    run_dir = out_root / f"{configuration}-rep{rep}-{point}"
    (run_dir / "cases").mkdir(parents=True, exist_ok=False)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    identity = {
        "campaign_id": f"d6-{decl_sha[:12]}",
        "campaign_declaration_sha256": decl_sha,
        "chain": "development",
        "set": 1,
        "point": point,
        "lot": 0,
        "slot": rep,
        "execution_id": f"{stamp}-{os.getpid()}-{configuration}-{rep}",
        "attempt": 1,
        "eligibility": "diagnostic",
        "origin": {
            "mode": "d6",
            "harness_sha256": v2.HARNESS_SHA256,
            "harness_commit": v2.git(v2.HARNESS_PATH.parent, "rev-parse", "HEAD"),
        },
    }
    for c in decl["cases"]:
        if v2.file_sha256(cache / f"{c}.rpc") != by_id[c]["sha256"]:
            raise SystemExit(f"input {c} does not match the accepted manifest; nothing analyzed")
    tasks = [
        (pos, [by_id[c] for c in lst], str(cache), str(run_dir), identity, cfg["dispatch"])
        for pos, lst in enumerate(cfg["assignment"])
    ]
    saved = {k: os.environ.get(k) for k in E_ENVIRONMENT}
    env = cfg["dispatch"]["environment"]
    for k in E_ENVIRONMENT:
        if env.get(k) is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = env[k]
    started = v2.utc_now()
    t0 = time.perf_counter()
    try:
        context = multiprocessing.get_context("spawn")
        with cf.ProcessPoolExecutor(
            max_workers=min(24, len(tasks)),
            mp_context=context,
            initializer=_init,
            initargs=(cfg["dispatch"],),
            max_tasks_per_child=1,
        ) as pool:
            results = list(pool.map(d6_task, tasks))
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
    record = {
        "format": EXECUTION_FORMAT,
        "identity": identity,
        "configuration": configuration,
        "repetition": rep,
        "point": point,
        "d6_sha256": D6_SHA256,
        "declaration_sha256": decl_sha,
        "inputs_manifest_sha256": acc["payload"]["manifest_sha256"],
        "checkout": v2.refute_checkout(),
        "started_utc": started,
        "ended_utc": v2.utc_now(),
        "wall_seconds": round(time.perf_counter() - t0, 3),
        "processes": results,
        "closed": True,
    }
    v2.write_json(run_dir / "execution.json", record)
    return record


def mode_run(args) -> int:
    decl_path = Path(args.declaration)
    decl, decl_sha = v2.read_json(decl_path), v2.file_sha256(decl_path)
    if decl["d6_sha256"] != D6_SHA256 or decl["harness_sha256"] != v2.HARNESS_SHA256:
        raise SystemExit("the D6 declaration names another d6.py or harness")
    checkout = v2.refute_checkout()
    _, _, problems = v2.binding_problems(args.point, checkout)
    if problems:
        raise SystemExit(f"point {args.point} refused: {problems}")
    configs = args.configuration or list(CONFIGURATIONS)
    for configuration in configs:
        for rep in args.repetition or decl["repetitions"]:
            rec = run_one(
                decl, decl_sha, configuration, rep, args.point, Path(args.cache), Path(args.out)
            )
            print(
                f"{configuration} rep {rep} {args.point}: {len(rec['processes'])} "
                f"process(es), {rec['wall_seconds']} s",
                flush=True,
            )
    return 0


# --- check ---------------------------------------------------------------------------------


def check_one(decl: dict, run_dir: Path, configuration: str, by_id: dict) -> tuple[list[str], dict]:
    """Check 1 for one execution, and its records (validated by the closed schema plus the
    control section)."""
    problems: list[str] = []
    ex_path = run_dir / "execution.json"
    if not ex_path.is_file():
        return [f"{run_dir.name}: no execution record (missing or interrupted)"], {}
    ex = v2.read_json(ex_path)
    cfg = decl["configurations"][configuration]
    want_table = hashlib.sha256(v2.canonical_json(cfg["dispatch"]["table"])).hexdigest()
    positions = {p["position"]: p for p in ex["processes"]}
    if sorted(positions) != list(range(len(cfg["assignment"]))):
        problems.append(
            f"{run_dir.name}: process positions {sorted(positions)} differ from the declaration"
        )
    pids: dict[int, int] = {}
    seen: dict[str, int] = {}
    for pos, lst in enumerate(cfg["assignment"]):
        p = positions.get(pos)
        if p is None:
            continue
        if p.get("dispatch_problems"):
            problems.append(
                f"{run_dir.name} position {pos}: dispatch or threads {p['dispatch_problems'][:3]}"
            )
        if p.get("dispatch_table_sha256") != want_table:
            problems.append(
                f"{run_dir.name} position {pos}: dispatch table differs from the variant's "
                "declaration"
            )
        conf = p.get("configuration") or {}
        if conf.get("thread_env") != {v: "1" for v in v2.THREAD_VARIABLES}:
            problems.append(f"{run_dir.name} position {pos}: thread variables differ")
        if any(t.get("num_threads") != 1 for t in conf.get("threadpools") or [{}]):
            problems.append(
                f"{run_dir.name} position {pos}: a thread pool has more than one thread"
            )
        if [s[2] for s in p["sequence"]] != lst or [s[1] for s in p["sequence"]] != list(
            range(len(lst))
        ):
            problems.append(
                f"{run_dir.name} position {pos}: the observed sequence differs from the "
                "declared list"
            )
        if p["pid"] in pids:
            problems.append(
                f"{run_dir.name}: PID {p['pid']} appears at positions {pids[p['pid']]} and {pos}"
            )
        pids[p["pid"]] = pos
        for s in p["sequence"]:
            if s[2] in seen:
                problems.append(f"{run_dir.name}: case {s[2]} analyzed by two positions")
            seen[s[2]] = pos
            if s[0] != p["pid"]:
                problems.append(f"{run_dir.name}: case {s[2]} recorded with another PID")
    recs = {}
    for c in decl["cases"]:
        f = run_dir / "cases" / f"{c}.json"
        if f.is_file():
            recs[c] = v2.read_json(f)
            conf = recs[c].get("configuration") or {}
            if conf.get("dispatch_table_sha256") != want_table:
                problems.append(
                    f"{run_dir.name} {c}: the record's dispatch table differs from the declaration"
                )
    return problems, recs


def mode_check(args) -> int:
    decl_path = Path(args.declaration)
    decl, decl_sha = v2.read_json(decl_path), v2.file_sha256(decl_path)
    by_id, acc = _inputs(decl)
    out_root = Path(args.out)
    check1: list[str] = []
    missing: list[str] = []
    invalid: list[str] = []
    errors: list[str] = []
    records: dict[tuple[str, int, str], dict] = {}
    for point in decl["points"]:
        for configuration in CONFIGURATIONS:
            for rep in decl["repetitions"]:
                run_dir = out_root / f"{configuration}-rep{rep}-{point}"
                p, recs = check_one(decl, run_dir, configuration, by_id)
                check1 += p
                for c in decl["cases"]:
                    rec = recs.get(c)
                    if rec is None:
                        missing.append(f"{run_dir.name} {c}")
                        continue
                    expect = {
                        "campaign_declaration_sha256": decl_sha,
                        "point": point,
                        "slot": rep,
                        "lot": 0,
                        "eligibility": "diagnostic",
                    }
                    found = v2.validate_record(
                        rec, by_id[c], expect, extra_top=frozenset({"control"})
                    )
                    if set(rec.get("control") or {}) != {"cases_before_in_process"}:
                        found.append(f"{c}: control section differs from the schema")
                    invalid += [f"{run_dir.name} {x}" for x in found]
                    if rec.get("status") == "error":
                        errors.append(f"{run_dir.name} {c}")
                    records[(configuration, rep, point, c)] = rec
    pairs = []
    for point in decl["points"]:
        for a, b in decl["contrasts"]:
            for rep in decl["repetitions"]:
                pairs.append(((a, rep, point), (b, rep, point), f"{a} x {b}"))
        for configuration in CONFIGURATIONS:
            pairs.append(
                (
                    (configuration, 1, point),
                    (configuration, 2, point),
                    f"{configuration} rep 1 x rep 2",
                )
            )
    science, control = [], []
    control_tally: dict[str, dict[str, int]] = {}
    for left, right, label in pairs:
        for c in decl["cases"]:
            ra, rb = records.get((*left, c)), records.get((*right, c))
            if ra is None or rb is None:
                continue
            rep = CMP.compare_records(
                ra, rb, "d6-science", labels=(f"{left[0]}-{left[1]}", f"{right[0]}-{right[1]}")
            )
            if rep["status"] != "identical":
                science.append(
                    {
                        "contrast": label,
                        "point": left[2],
                        "case": c,
                        "status": rep["status"],
                        "differences": rep["differences"][:10],
                        "problems": rep["problems"][:5],
                    }
                )
            ctl = CMP.compare_records(ra, rb, "d6-control")
            va = decl["configurations"][left[0]]["control_values"][c]
            vb = decl["configurations"][right[0]]["control_values"][c]
            found = ctl["status"] != "identical"
            tally = control_tally.setdefault(label, {"expected": 0, "found": 0})
            tally["expected"] += int(va != vb)
            tally["found"] += int(found)
            if found != (va != vb):
                control.append(
                    {
                        "contrast": label,
                        "point": left[2],
                        "case": c,
                        "expected_difference": va != vb,
                        "reported": ctl["status"],
                        "differences": ctl["differences"][:3],
                    }
                )
    nc_path = out_root / "negative-control.json"
    negative = v2.read_json(nc_path) if nc_path.is_file() else None
    conditions = {
        "1_all_present": not missing,
        "2_status_analyzed": not errors and not missing,
        "3_inputs_verified": not any("input SHA-256" in x for x in invalid),
        "4_records_complete_and_typed": not invalid,
        "5_integrity_and_closed": all(
            (out_root / f"{cf_}-rep{r}-{p}" / "execution.json").is_file()
            for p in decl["points"]
            for cf_ in CONFIGURATIONS
            for r in decl["repetitions"]
        ),
        "6_check1_and_negative_control": not check1
        and bool(negative and negative.get("passed"))
        and not control,
    }
    if errors or science or control or (negative is not None and not negative.get("passed")):
        result = "FAIL"
    elif not all(conditions.values()):
        result = "INCOMPLETE"
    else:
        result = "PASS"
    report = {
        "format": REPORT_FORMAT,
        "declaration_sha256": decl_sha,
        "smoke": decl.get("smoke"),
        "note": decl.get("note"),
        "result": result,
        "conditions": conditions,
        "check1": check1,
        "missing": missing[:200],
        "invalid": invalid[:200],
        "errors": errors,
        "science_differences": science[:200],
        "control_mismatches": control[:200],
        "control_differences_by_contrast": control_tally,
        "pairs_compared": len(pairs),
        "negative_control": negative,
        "profiles": {n: CMP.profile_sha256(n) for n in ("d6-science", "d6-control")},
    }
    target = Path(args.report)
    v2.write_json(target, report)
    print(
        f"D6 {'SMOKE ' if decl.get('smoke') else ''}result: {result}; conditions "
        f"{conditions}; science differences {len(science)}; control mismatches "
        f"{len(control)}; check 1 problems {len(check1)}"
    )
    return 0 if result == "PASS" else 2


# --- negative control (injected differences and a wrong configuration) --------------------


def _floats(rec: dict) -> list[str]:
    return [
        p
        for p, item in CMP.flatten(rec).items()
        if item[0] == "float" and item[2] not in ("nan", "inf", "-inf")
    ]


def _get(rec, path):
    for part in path.split("/")[1:]:
        part = part.replace("~1", "/").replace("~0", "~")
        rec = rec[int(part)] if isinstance(rec, list) else rec[part]
    return rec


def mode_negative_control(args) -> int:
    decl_path = Path(args.declaration)
    decl = v2.read_json(decl_path)
    by_id, _ = _inputs(decl)
    out_root = Path(args.out)
    point = decl["points"][0]
    c = decl["cases"][0]
    rec = v2.read_json(out_root / f"R-idx-rep1-{point}" / "cases" / f"{c}.json")
    floats = _floats(rec)
    metric = next(p for p in floats if "/metrics/" in p)
    results = []

    def expect(label, a, b, status, path):
        rep = CMP.compare_records(a, b, "d6-science")
        paths = [d["path"] for d in rep["differences"]]
        ok = rep["status"] == status and (
            path in paths if status == "divergent" else any(path in p for p in rep["problems"])
        )
        if status == "divergent":
            ok = ok and len(paths) == 1
        results.append(
            {
                "label": label,
                "ok": ok,
                "status": rep["status"],
                "paths": paths[:3],
                "problems": rep["problems"][:2],
            }
        )

    def setf(r, path, bits):
        val = _get(r, path)
        x = struct.unpack(">d", bits.to_bytes(8, "big"))[0]
        val["f64"] = f"{bits:016x}"
        val["dec"] = "nan" if x != x else repr(x)

    x = copy.deepcopy(rec)
    s = x["conditions"]["i"]["scientific"]
    s["verdict_reason"] = (s["verdict_reason"] or "")[:-1] + (
        "x" if not (s["verdict_reason"] or "").endswith("x") else "y"
    )
    expect(
        "one byte changed (a string)",
        rec,
        x,
        "divergent",
        "/conditions/i/scientific/verdict_reason",
    )
    a, b = copy.deepcopy(rec), copy.deepcopy(rec)
    setf(a, metric, 0x0000000000000000)
    setf(b, metric, 0x8000000000000000)
    expect("the sign of a zero", a, b, "divergent", metric)
    a, b = copy.deepcopy(rec), copy.deepcopy(rec)
    setf(a, metric, 0x7FF8000000000001)
    setf(b, metric, 0x7FF8000000000002)
    expect("the payload of a NaN", a, b, "divergent", metric)
    x = copy.deepcopy(rec)
    h = x["input"]["manifest_entry_sha256"]
    x["input"]["manifest_entry_sha256"] = ("0" if h[0] != "0" else "1") + h[1:]
    expect("a header field (/input)", rec, x, "divergent", "/input/manifest_entry_sha256")
    x = copy.deepcopy(rec)
    bits = int(_get(x, metric)["f64"], 16) + 1
    setf(x, metric, bits)
    expect("a metric value", rec, x, "divergent", metric)
    x = copy.deepcopy(rec)
    del x["conditions"]["i"]["scientific"]["verdict"]
    expect("a missing field", rec, x, "divergent", "/conditions/i/scientific/verdict")
    x = copy.deepcopy(rec)
    x["conditions"]["i"]["scientific"]["extra"] = True
    expect("an extra field", rec, x, "divergent", "/conditions/i/scientific/extra")
    x = copy.deepcopy(rec)
    _get(x, metric)["dec"] = repr(float(_get(x, metric)["dec"]) + 1.0)
    expect("a float whose dec and f64 disagree", rec, x, "invalid", metric)
    x = copy.deepcopy(rec)
    x["control"]["cases_before_in_process"] += 7
    rep = CMP.compare_records(rec, x, "d6-science")
    results.append(
        {
            "label": "a control difference is not science (d6-science)",
            "ok": rep["status"] == "identical",
            "status": rep["status"],
        }
    )
    rep = CMP.compare_records(rec, x, "d6-control")
    results.append(
        {
            "label": "a control difference is found by d6-control",
            "ok": rep["status"] == "divergent"
            and [d["path"] for d in rep["differences"]] == ["/control/cases_before_in_process"],
            "status": rep["status"],
        }
    )
    # A wrong configuration injected: a copy of E's execution with the default table.
    e_dir = out_root / f"E-rep1-{point}"
    wrong = out_root / "negative-control-wrong-E"
    if not wrong.exists():
        (wrong / "cases").mkdir(parents=True)
        ex = v2.read_json(e_dir / "execution.json")
        default_sha = hashlib.sha256(
            v2.canonical_json(decl["configurations"]["R-idx"]["dispatch"]["table"])
        ).hexdigest()
        for p in ex["processes"]:
            p["dispatch_table_sha256"] = default_sha
        v2.write_json(wrong / "execution.json", ex)
    p, _ = check_one(decl, wrong, "E", by_id)
    results.append(
        {
            "label": "E with the default dispatch table is refused by check 1",
            "ok": any("dispatch table differs" in x for x in p),
            "check1": p[:3],
        }
    )
    report = {
        "results": results,
        "passed": all(r["ok"] for r in results),
        "record": f"R-idx-rep1-{point}/{c}",
    }
    target = out_root / "negative-control.json"
    v2.write_json(target, report)
    for r in results:
        print(f"{'OK   ' if r['ok'] else 'WRONG'} {r['label']}")
    print(f"negative control: {'PASSED' if report['passed'] else 'FAILED'}")
    return 0 if report["passed"] else 2


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="sub", required=True)
    p = sub.add_parser("plan")
    p.add_argument("--selection-manifest", required=True)
    p.add_argument("--dispatch-default", required=True)
    p.add_argument("--dispatch-e", required=True)
    p.add_argument("--inputs-root", required=True)
    p.add_argument("--inputs-campaign", required=True)
    p.add_argument("--points", nargs="+", default=["M0", "M3"])
    p.add_argument("--limit", type=int, help="a smoke run with the first cases only (not the D6)")
    p.add_argument("--out", required=True)
    r = sub.add_parser("run")
    r.add_argument("--declaration", required=True)
    r.add_argument("--point", required=True)
    r.add_argument("--cache", required=True)
    r.add_argument("--out", required=True)
    r.add_argument("--configuration", nargs="*")
    r.add_argument("--repetition", nargs="*", type=int)
    c = sub.add_parser("check")
    c.add_argument("--declaration", required=True)
    c.add_argument("--out", required=True)
    c.add_argument("--report", required=True)
    n = sub.add_parser("negative-control")
    n.add_argument("--declaration", required=True)
    n.add_argument("--out", required=True)
    for x in (p, r, c, n):
        x.add_argument("--cpus", default="8-31")
    args = parser.parse_args()
    print(f"affinity: {v2.set_affinity(args.cpus)}", flush=True)
    return {
        "plan": mode_plan,
        "run": mode_run,
        "check": mode_check,
        "negative-control": mode_negative_control,
    }[args.sub](args)


if __name__ == "__main__":
    sys.exit(main())
