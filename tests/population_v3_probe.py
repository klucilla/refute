"""A probe for tests/test_population_v3.py and tests/test_population_v3_identity.py, run in its own
process (the harness version 3 replaces functions in the loaded version 2, which must not leak
into the test process).

Usage: ``python tests/population_v3_probe.py <mode> <work folder>``; prints one JSON object on its
last line. Modes: ``v3`` (one synthetic case analyzed by a spawned worker of version 2's pool, with
the expected identity of a validated declaration), ``v2`` (version 2 alone: its plan), ``import``
(import version 3 and report its loading state), ``plan`` (build version 3's plan), and the
identity cases of map Amendment 25: ``paths``, ``declaration``, ``declaration-v2``,
``worker-mismatch``, ``callback``, ``resume``, ``close``.
"""

import importlib.util
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POPULATION = ROOT / "docs" / "validation" / "v0.2.1" / "population"


def _import(name):
    sys.path.insert(0, str(POPULATION))
    return importlib.import_module(name)


def _out(obj) -> None:
    print(json.dumps(obj, default=str))


def _analyze_one(v3, work, expected=None):
    """One synthetic case through version 2's pool (patched by version 3)."""
    pv2 = v3.pv2
    case = next(c for c in pv2.population_cases("selftest") if c["class"] == "planet")
    blob, entry, _, _ = pv2.built_case(case)
    cache = work / "cache"
    run_dir = work / "run"
    (run_dir / "cases").mkdir(parents=True, exist_ok=True)
    cache.mkdir(parents=True, exist_ok=True)
    (cache / f"{entry['id']}.rpc").write_bytes(blob)
    identity = {
        "campaign_id": "probe",
        "campaign_declaration_sha256": "0" * 64,
        "chain": "development",
        "set": 1,
        "point": "probe",
        "lot": 1,
        "slot": 1,
        "execution_id": "probe",
        "attempt": 1,
        "eligibility": "diagnostic",
        "origin": {
            "mode": "analyze",
            "harness_sha256": pv2.HARNESS_SHA256,
            "harness_commit": pv2.git(v3.V3_PATH.parent, "rev-parse", "HEAD"),
        },
    }
    # the expected identity, as open_campaign sets it from a validated declaration
    os.environ[v3.EXPECTED_ENV] = json.dumps(expected or v3.STATE["identity"], sort_keys=True)
    declared = {
        "environment": {pv2.DISPATCH_VARIABLE: os.environ.get(pv2.DISPATCH_VARIABLE)},
        "table": pv2.dispatch_table(),
    }
    seen = []
    outcome = pv2.run_pool(
        v3.analyze_task,
        [(entry, str(cache), str(run_dir), identity)],
        1,
        declared,
        on_worker=lambda report: None,
        on_result=lambda i, r: seen.append(r) or None,
    )
    return pv2, entry, run_dir, outcome, seen


def mode_v3(work):
    v3 = _import("population_v3")
    pv2, entry, run_dir, outcome, seen = _analyze_one(v3, work)
    if not outcome.results:
        _out({"error": outcome.error, "stopped": outcome.stopped, "results": None})
        raise SystemExit(1)
    result = next(iter(outcome.results.values()))
    record = json.loads((run_dir / "cases" / f"{entry['id']}.json").read_text(encoding="utf-8"))
    scientific = record["conditions"]["i"]["scientific"]
    _out(
        {
            "error": outcome.error,
            "status": record["status"],
            "main_pid": os.getpid(),
            "worker_pid": result.get("pid"),
            "marker": scientific.get("corrections"),
            "block": scientific["test_plan"]["gauntlet"]["corrections"],
            "harness_sha256": pv2.HARNESS_SHA256,
            "v3_sha256": v3.V3_SHA256,
            "record_origin": record["identity"]["origin"],
            "schema_problems": pv2.validate_record(record, entry, {}),
            "configuration": v3.STATE["config"]["corrections"],
            "journal": v3.journal_entries(run_dir),
            "seen_identity": seen[0].get("m4_identity") if seen else None,
            "expected": v3.STATE["identity"],
            "resume_problems": v3.resume_problems(run_dir),
        }
    )


def mode_paths(work):
    """A2's path cases against a fake checkout under the work folder."""
    v3 = _import("population_v3")
    root = work / "checkout"
    auth = root / "docs" / "validation" / "v0.2.1" / "population" / "m4-configurations"
    auth.mkdir(parents=True, exist_ok=True)
    good = auth / "c.json"
    good.write_bytes(b"{}")
    (root / "elsewhere").mkdir(exist_ok=True)
    (root / "elsewhere" / "c.json").write_bytes(b"{}")
    (auth / "sub").mkdir(exist_ok=True)
    (auth / "sub" / "c.json").write_bytes(b"{}")
    rel = "docs/validation/v0.2.1/population/m4-configurations/c.json"
    cases = {
        "good": (rel, True),
        "absolute": (str(good), True),
        "backslash": (rel.replace("/", "\\"), True),
        "dotdot": (
            "docs/validation/v0.2.1/population/m4-configurations/../m4-configurations/c.json",
            True,
        ),
        "missing": ("docs/validation/v0.2.1/population/m4-configurations/none.json", True),
        "outside_folder": ("elsewhere/c.json", True),
        "nested": ("docs/validation/v0.2.1/population/m4-configurations/sub/c.json", True),
        "env_absolute_good": (str(good), False),
    }
    links = {}
    # a link to the authorized folder (a junction on Windows, a symbolic link elsewhere)
    link_dir = root / "linked"
    try:
        if os.name == "nt":
            import _winapi

            _winapi.CreateJunction(str(auth), str(link_dir))
        else:
            os.symlink(auth, link_dir, target_is_directory=True)
        cases["through_link"] = ("linked/c.json", True)
        links["dir"] = True
    except OSError as exc:
        links["dir"] = f"not created: {exc}"
    try:
        os.symlink(good, auth / "l.json")
        cases["file_link"] = ("docs/validation/v0.2.1/population/m4-configurations/l.json", True)
        links["file"] = True
    except OSError as exc:
        links["file"] = f"not created: {exc}"
    out = {}
    for name, (text, declared) in cases.items():
        path, why = v3.checked_path(text, declared=declared, root=root, authorized=auth)
        out[name] = why
    _out({"cases": out, "links": links})


def _write_declaration(work, cid, member, harness_sha256):
    folder = work / "campaigns" / cid
    folder.mkdir(parents=True, exist_ok=True)
    decl = {
        "format": "refute-population-campaign/1",
        "campaign_id": cid,
        "eligibility": "diagnostic",
        "chain": "development",
        "predecessor": {"note": "probe"},
        "chain_sets_consumed_before": 0,
        "population": "selftest",
        "harness_sha256": harness_sha256,
        "budget": {"K": 3, "N": 3, "chain_ceiling": 6},
        "affinity": "0-7",
        "overhead": {"double_hash": True},
    }
    if member is not None:
        decl["m4_configuration"] = member
    (folder / "declaration.json").write_text(json.dumps(decl), encoding="utf-8")
    return work / "campaigns"


def mode_declaration(work):
    """A1, A2 and A6: the problems version 3 adds for each variant of the member."""
    v3 = _import("population_v3")
    ident = v3.STATE.get("identity") or {}
    good = {k: ident.get(k) for k in ("format", "name", "path", "sha256")}
    variants = {
        "good": good,
        "missing": None,
        "malformed": {"path": good.get("path")},
        "wrong_sha256": {**good, "sha256": "0" * 64},
        "wrong_name": {**good, "name": "another"},
        "wrong_format": {**good, "format": "refute-m4-configuration/0"},
        "absolute_path": {**good, "path": str(v3.CHECKOUT_ROOT / str(good.get("path")))},
        "dotdot_path": {
            **good,
            "path": "docs/validation/../validation/v0.2.1/population/m4-configurations/m4-c1.json",
        },
        "missing_path": {
            **good,
            "path": "docs/validation/v0.2.1/population/m4-configurations/none.json",
        },
        "outside_path": {**good, "path": "docs/validation/v0.2.1/population/population_v3.py"},
    }
    out = {}
    for name, member in variants.items():
        root = _write_declaration(work, f"probe-{name.replace('_', '-')}", member, v3.V3_SHA256)
        camp = v3.pv2.open_campaign(str(root), f"probe-{name.replace('_', '-')}")
        out[name] = [p for p in camp.problems if "m4_configuration" in p or "M4 configuration" in p]
    _out({"m4_problems": out, "state_ok": v3.STATE["ok"]})


def mode_declaration_v2(work):
    """A3: version 2 alone, with its own harness identity, with and without the extra member."""
    pv2 = _import("population_v2")
    member = {"format": "refute-m4-configuration/1", "name": "x", "path": "p", "sha256": "0" * 64}
    out = {}
    for name, m in (("with", member), ("without", None)):
        root = _write_declaration(work, f"probe-v2-{name}", m, pv2.HARNESS_SHA256)
        camp = pv2.open_campaign(str(root), f"probe-v2-{name}")
        out[name] = sorted(p.replace(f"probe-v2-{name}", "<cid>") for p in camp.problems)
    _out(out)


def mode_worker_mismatch(work):
    """A4: the main process with configuration A (loaded at import) and the worker with a valid
    configuration B (the environment changed before the pool starts): the worker refuses before
    the inherited analysis, the dispatch stops, the journal records a refusal."""
    v3 = _import("population_v3")
    # PROBE_OTHER: the worker's file (default: a different block; probe-same-block.json has the
    # same block under another name and file, so only the identity differs)
    other = (
        POPULATION / "m4-configurations" / os.environ.get("PROBE_OTHER", "probe-non-default.json")
    )
    os.environ[v3.CONFIGURATION_ENV] = str(other)
    pv2, entry, run_dir, outcome, seen = _analyze_one(v3, work)
    _out(
        {
            "results": list(outcome.results.values()),
            "seen": seen,
            "journal": v3.journal_entries(run_dir),
            "record_written": (run_dir / "cases" / f"{entry['id']}.json").exists(),
        }
    )


def mode_callback(work):
    """A4: the main process's check of results, called directly."""
    v3 = _import("population_v3")
    os.environ[v3.EXPECTED_ENV] = json.dumps(v3.STATE["identity"], sort_keys=True)
    run_dir = work / "run"
    run_dir.mkdir(parents=True, exist_ok=True)
    good = {
        "case": "a",
        "pid": 1,
        "sha256": "1" * 64,
        "status": "analyzed",
        "m4_identity": dict(v3.STATE["identity"]),
    }
    bare = {"case": "b", "pid": 2, "sha256": "2" * 64, "status": "analyzed"}
    other = {**good, "case": "c", "m4_identity": {**v3.STATE["identity"], "sha256": "9" * 64}}
    out = {
        k: v3.check_result(run_dir, r)
        for k, r in (("good", good), ("bare", bare), ("other", other))
    }
    _out({"checked": out, "journal": v3.journal_entries(run_dir)})


def mode_resume(work):
    """A4 and A5: a resume accepts a persisted record only with a matching confirmation."""
    v3 = _import("population_v3")
    pv2, entry, run_dir, outcome, seen = _analyze_one(v3, work)
    case = entry["id"]
    journal = run_dir / v3.IDENTITY_JOURNAL
    record = run_dir / "cases" / f"{case}.json"
    out = {"as_written": v3.resume_problems(run_dir)}
    saved = journal.read_bytes()
    journal.unlink()  # an interruption between the inherited write and the confirmation
    out["no_confirmation"] = v3.resume_problems(run_dir)
    journal.write_bytes(saved)
    v3.journal_append(run_dir, {"kind": "refusal", "case": case, "pid": 0, "reason": "probe"})
    out["refused"] = v3.resume_problems(run_dir)
    journal.write_bytes(saved)
    data = record.read_bytes()
    record.write_bytes(data.replace(b'"analyzed"', b'"analyzed" ', 1))
    out["record_changed"] = v3.resume_problems(run_dir)
    record.write_bytes(data)
    os.environ[v3.EXPECTED_ENV] = json.dumps({**v3.STATE["identity"], "block_sha256": "e" * 64})
    out["other_block"] = v3.resume_problems(run_dir)
    _out(out)


def _reconfirm(v3, run_dir, record, rec, pid=None):
    """Rewrite a record and its confirmation (as the main process would for those bytes)."""
    data = json.dumps(rec).encode("utf-8")
    record.write_bytes(data)
    import hashlib

    (run_dir / v3.IDENTITY_JOURNAL).unlink()
    v3.journal_append(
        run_dir,
        {
            "kind": "confirmation",
            "case": record.stem,
            "pid": rec["operational"]["pid"] if pid is None else pid,
            "record_sha256": hashlib.sha256(data).hexdigest(),
            "identity": v3.STATE["identity"],
        },
    )


def mode_records(work):
    """Added after the Codex review of the package: every consumer of the records (version 2's
    slot_records), an error record, incomplete confirmations, and the block check isolated."""
    v3 = _import("population_v3")
    pv2, entry, run_dir, outcome, seen = _analyze_one(v3, work)
    case = entry["id"]
    record = run_dir / "cases" / f"{case}.json"
    journal = run_dir / v3.IDENTITY_JOURNAL
    original = json.loads(record.read_bytes())
    out = {"installed": pv2.slot_records is v3.slot_records}

    def consumer():
        _, _, problems = pv2.slot_records(run_dir, [case], {case: entry}, {}, None)
        return [p for p in problems if p.startswith("M4 identity")]

    out["consumer_confirmed"] = consumer()
    saved = journal.read_bytes()
    journal.unlink()
    out["consumer_unconfirmed"] = consumer()
    journal.write_bytes(saved)
    # an incomplete confirmation (no PID) and a confirmation with another PID
    rec = dict(original)
    _reconfirm(v3, run_dir, record, rec)
    entries = [json.loads(x) for x in journal.read_bytes().splitlines()]
    del entries[0]["pid"]
    journal.write_bytes(b"".join(json.dumps(e).encode() + b"\n" for e in entries))
    out["no_pid"] = v3.resume_problems(run_dir)
    _reconfirm(v3, run_dir, record, rec, pid=rec["operational"]["pid"] + 1)
    out["other_pid"] = v3.resume_problems(run_dir)
    # the block check isolated: another block, confirmed for these very bytes
    other = json.loads(json.dumps(original))
    block = other["conditions"]["i"]["scientific"]["test_plan"]["gauntlet"]["corrections"]
    block["r_min"] = block["r_min"] + 1
    _reconfirm(v3, run_dir, record, other)
    out["other_block_confirmed"] = v3.resume_problems(run_dir)
    # an error record (a traceback, no conditions), confirmed
    err = {k: v for k, v in original.items() if k != "conditions"}
    err["status"] = "error"
    err["traceback"] = "probe"
    _reconfirm(v3, run_dir, record, err)
    out["error_confirmed"] = v3.resume_problems(run_dir)
    journal.unlink()
    out["error_unconfirmed"] = v3.resume_problems(run_dir)
    _out(out)


def mode_stop(work):
    """A4: a refused result stops the dispatch (three tasks, a callback returning what version
    2's analysis returns for an infrastructure failure)."""
    v3 = _import("population_v3")
    pv2 = v3.pv2
    planets = [c for c in pv2.population_cases("selftest") if c["class"] == "planet"][:3]
    cache, run_dir = work / "cache", work / "run"
    (run_dir / "cases").mkdir(parents=True, exist_ok=True)
    cache.mkdir(parents=True, exist_ok=True)
    tasks = []
    for case in planets:
        blob, entry, _, _ = pv2.built_case(case)
        (cache / f"{entry['id']}.rpc").write_bytes(blob)
        tasks.append((entry, str(cache), str(run_dir), {"probe": True}))
    os.environ[v3.EXPECTED_ENV] = json.dumps({**v3.STATE["identity"], "sha256": "d" * 64})
    declared = {
        "environment": {pv2.DISPATCH_VARIABLE: os.environ.get(pv2.DISPATCH_VARIABLE)},
        "table": pv2.dispatch_table(),
    }
    outcome = pv2.run_pool(
        v3.analyze_task,
        tasks,
        1,
        declared,
        on_worker=lambda report: None,
        on_result=lambda i, r: "infrastructure" if "infrastructure" in r else None,
    )
    _out(
        {
            "tasks": len(tasks),
            "results": len(outcome.results),
            "stopped": outcome.stopped,
            "journal": v3.journal_entries(run_dir),
        }
    )


def mode_transport(work):
    """A5: the expected identity is published only by an opening with no problem at all, and the
    main process never keeps one it inherited."""
    os.environ["REFUTE_M4_EXPECTED_IDENTITY"] = '{"inherited": true}'
    v3 = _import("population_v3")
    out = {"inherited_cleared": v3.EXPECTED_ENV not in os.environ}
    ident = v3.STATE["identity"]
    member = {k: ident[k] for k in ("format", "name", "path", "sha256")}

    class Camp:
        def __init__(self, problems):
            self.declaration = {"m4_configuration": member}
            self.problems = list(problems)

    v3._V2_OPEN_CAMPAIGN = lambda root, cid: Camp([])
    v3.open_campaign("r", "c")
    out["clean_published"] = v3.expected_identity() == ident
    v3._V2_OPEN_CAMPAIGN = lambda root, cid: Camp(["a version 2 problem"])
    v3.open_campaign("r", "c")
    out["problem_unpublished"] = v3.EXPECTED_ENV not in os.environ
    _out(out)


def mode_cli_capture(work):
    """A3: the command line captures the configuration once per process."""
    import pathlib
    import runpy

    config = Path(os.environ["REFUTE_M4_CONFIGURATION"]).resolve()
    reads = []
    real = pathlib.Path.read_bytes

    def counting(self):
        if Path(self).resolve() == config:
            reads.append(1)
        return real(self)

    pathlib.Path.read_bytes = counting
    sys.argv = [
        "population_v3.py",
        "dispatch-table",
        "--out",
        str(work / "d.json"),
        "--cpus",
        "0-7",
    ]
    sys.path.insert(0, str(POPULATION))
    try:
        runpy.run_path(str(POPULATION / "population_v3.py"), run_name="__main__")
    except SystemExit:
        pass
    _out({"reads": len(reads)})


def mode_close(work):
    """A5: a configuration changed during an execution invalidates its close."""
    v3 = _import("population_v3")
    copy = work / "copy.json"
    copy.write_bytes(v3.STATE["bytes"])
    v3.STATE = {**v3.STATE, "path": copy}
    calls = {"lock": [], "close": []}
    v3.pv2.write_lock = lambda camp, identity, unit, reason, evidence: calls["lock"].append(reason)
    v3._V2_CLOSE = lambda self, payload: calls["close"].append(payload) or True

    class Ex:
        camp = None
        identity = {"execution_id": "probe"}

    unchanged = v3.close(Ex(), {"result": "analyzed"})
    copy.write_bytes(v3.STATE["bytes"] + b" ")
    changed = v3.close(Ex(), {"result": "analyzed"})
    _out(
        {
            "unchanged": unchanged,
            "changed": changed,
            "calls": calls,
            "installed": v3.pv2.Execution.close is v3.close,
        }
    )


def main() -> None:
    mode, work = sys.argv[1], Path(sys.argv[2])
    work.mkdir(parents=True, exist_ok=True)
    if mode == "import":
        v3 = _import("population_v3")
        _out({"imported": True, "state_ok": v3.STATE["ok"], "problem": v3.STATE["problem"]})
        return
    if mode == "plan":
        v3 = _import("population_v3")
        v3.pv2._plan()
        _out({"plan": True})
        return
    if mode == "capture":
        v3 = _import("population_v3")
        try:
            v3.capture(Path(os.environ["PROBE_CAPTURE"]))
            _out({"error": None})
        except Exception as exc:
            _out({"error": f"{type(exc).__name__}: {exc}"})
        return
    if mode == "v2":
        pv2 = _import("population_v2")
        _out({"active": pv2._plan().gauntlet.corrections.active})
        return
    {
        "v3": mode_v3,
        "paths": mode_paths,
        "declaration": mode_declaration,
        "declaration-v2": mode_declaration_v2,
        "worker-mismatch": mode_worker_mismatch,
        "callback": mode_callback,
        "resume": mode_resume,
        "close": mode_close,
        "records": mode_records,
        "stop": mode_stop,
        "transport": mode_transport,
        "cli-capture": mode_cli_capture,
    }[mode](work)


if __name__ == "__main__":
    main()
