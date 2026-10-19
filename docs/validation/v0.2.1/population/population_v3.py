"""v0.2.1 synthetic population study harness, version 3: the frozen version 2 measuring a
configuration of the M4 corrections (docs/validation/v0.2.1/reopen/m4-implementation-map.md,
Amendments 17 and 25; the maintainer's decisions of 2026-10-18 on the explicit activation and on
the package of this harness).

Version 2 (``population_v2.py``, SHA-256 pinned below) is never edited: it builds its plan with
``_plan()`` from ``FAST_PLAN`` (the fast search only), so it measures the M3 path. This file loads
version 2 as a module, checks its bytes, and replaces in it only:

- ``_plan()``: ``FAST_PLAN`` plus the corrections block of the **configuration file** named by the
  environment variable ``REFUTE_M4_CONFIGURATION`` (``refute-m4-configuration/1``: a name and a
  complete corrections block with ``version`` 2 and ``enabled`` true, every setting valid);
- ``open_campaign``: version 2's, then the **identity contract** of Amendment 25, A: the
  declaration's ``m4_configuration`` member must name the captured configuration file (its
  resolved path, its format, its name, its bytes' SHA-256); a loading problem of the configuration
  is a declaration problem too, so every operational mode refuses and ``status`` shows it;
- ``analyze_task``: the same function, defined in this module, so that the spawned workers import
  this module first; each worker checks its own captured configuration and its plan's resolved
  block against the expected identity the main process derived from the validated declaration
  (``REFUTE_M4_EXPECTED_IDENTITY``), refuses otherwise, and returns its identity in the result's
  envelope (never in the persisted record, whose schema is closed);
- ``run_pool``: for the analysis, every result's identity is checked by the main process, and an
  **identity journal** in the run folder records a confirmation (case, PID, record SHA-256,
  identity) or a refusal (case, PID, reason) for each; a refused result stops the dispatch;
- ``mode_analyze``: before version 2's, a resume accepts the persisted records of the run folder
  only with a matching confirmation, and none with a refusal or another corrections block;
- ``Execution.close``: a configuration file changed during the execution invalidates it;
- the harness identity (``HARNESS_PATH``, ``HARNESS_SHA256``: a campaign declaration names
  version 3) and R2 (``harness_problems``: this file, version 2 and the configuration file each the
  file of HEAD and unchanged since the start).

Run as version 2 is run, with this file in its place: ``.venv/Scripts/python.exe
docs/validation/v0.2.1/population/population_v3.py <mode> ...``.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path, PurePosixPath
from typing import Any

if __name__ == "__main__":
    # The command line runs the importable module only, so that the configuration is captured
    # once per process and the replacements are installed once (the Codex review of the package),
    # and so that pickled functions name ``population_v3``.
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import population_v3

    raise SystemExit(population_v3.main())
if __name__ == "__mp_main__":
    # A worker spawned from the command line runs this file as ``__mp_main__``: that copy is the
    # module in use, so the pickled functions of ``population_v3`` resolve to it and the
    # configuration is captured and the replacements installed once in the worker too.
    sys.modules.setdefault("population_v3", sys.modules[__name__])

HERE = Path(__file__).resolve().parent
V3_PATH = Path(__file__).resolve()
V3_BYTES = V3_PATH.read_bytes()
V3_SHA256 = hashlib.sha256(V3_BYTES).hexdigest()
V2_PATH = HERE / "population_v2.py"
# The frozen version 2 (its last commit 37c92c9617fb4077b7ec6f3c31c0972193ff0702).
V2_SHA256 = "8b3b6ad6aca6e713636b04e40db5a7d253c05458c8b143c38d984100072c1f82"
CONFIGURATION_ENV = "REFUTE_M4_CONFIGURATION"
EXPECTED_ENV = "REFUTE_M4_EXPECTED_IDENTITY"
CONFIGURATION_FORMAT = "refute-m4-configuration/1"
# Amendment 25, A.2: paths are read from the root of the checkout that holds this file, and a
# configuration is a regular file directly inside this folder.
CHECKOUT_ROOT = HERE.parents[3]
AUTHORIZED_DIR = (
    CHECKOUT_ROOT / "docs" / "validation" / "v0.2.1" / "population" / "m4-configurations"
)
IDENTITY_JOURNAL = "m4-identity-journal.jsonl"


def _load_v2():
    if hashlib.sha256(V2_PATH.read_bytes()).hexdigest() != V2_SHA256:
        raise SystemExit("population_v2.py is not the frozen version 2 (SHA-256)")
    if "population_v2" in sys.modules:
        return sys.modules["population_v2"]
    spec = importlib.util.spec_from_file_location("population_v2", V2_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules["population_v2"] = module
    spec.loader.exec_module(module)
    return module


pv2 = _load_v2()


# --- the path and the capture (Amendment 25, A.2 and A.3) -------------------------------------


def _is_link(p: Path) -> bool:
    is_junction = getattr(p, "is_junction", None)
    return p.is_symlink() or bool(is_junction and is_junction())


def checked_path(
    value: str | os.PathLike,
    *,
    declared: bool = False,
    root: Path | None = None,
    authorized: Path | None = None,
) -> tuple[Path | None, str | None]:
    """The configuration file a path names, or the reason it is refused. A declared path is
    relative, ``/``-separated, without ``..``; any path is read from the checkout's root (an
    environment value may also be absolute); no component from the root to the file may be a
    link or a junction; the file must be a regular file directly inside the authorized folder."""
    root = Path(root or CHECKOUT_ROOT)
    authorized = Path(authorized or AUTHORIZED_DIR)
    text = os.fspath(value)
    if not text:
        return None, "no path"
    if declared:
        if "\\" in text or text.startswith("/") or Path(text).is_absolute() or ":" in text:
            return None, f"the declared path {text!r} is not a relative, /-separated path"
        parts = PurePosixPath(text).parts
        if ".." in parts or "." in parts:
            return None, f"the declared path {text!r} has a '.' or '..' component"
        candidate = root.joinpath(*parts)
    else:
        candidate = Path(text) if Path(text).is_absolute() else root / text
        if ".." in candidate.parts:
            return None, f"the path {text!r} has a '..' component"
    try:
        rel = candidate.relative_to(root)
    except ValueError:
        return None, f"the path {text!r} is outside the checkout"
    walk = root
    for part in rel.parts:
        walk = walk / part
        if _is_link(walk):
            return None, f"the path {text!r} goes through a link or a junction ({part})"
    if not candidate.is_file():
        return None, f"the path {text!r} is not an existing regular file"
    if candidate.resolve().parent != authorized.resolve():
        return None, f"the path {text!r} is not directly inside the authorized folder"
    return candidate.resolve(), None


def _block_sha256(block: dict) -> str:
    from refute.packs.tess.params import CorrectionsParams

    resolved = CorrectionsParams.model_validate(block).model_dump(mode="json")
    return hashlib.sha256(pv2.canonical_json(resolved)).hexdigest()


def capture(path: Path) -> dict[str, Any]:
    """Read the configuration file once: its bytes, parsed and hashed from that one read, and
    checked (the format, a name, a complete version-2 block, every value valid)."""
    from refute.packs.tess.params import CorrectionsParams

    data = Path(path).read_bytes()
    config = json.loads(data)
    block = config.get("corrections") or {}
    if config.get("format") != CONFIGURATION_FORMAT or not config.get("name"):
        raise ValueError(f"not a {CONFIGURATION_FORMAT} file with a name")
    if block.get("version") != 2 or block.get("enabled") is not True:
        raise ValueError("the corrections block must have version 2 and enabled true")
    fields = set(CorrectionsParams.model_fields)
    if set(block) != fields:
        missing, extra = sorted(fields - set(block)), sorted(set(block) - fields)
        raise ValueError(f"the block must write every setting (missing {missing}, extra {extra})")
    CorrectionsParams.model_validate(block)
    rel = Path(path).resolve().relative_to(CHECKOUT_ROOT.resolve()).as_posix()
    return {
        "path": Path(path).resolve(),
        "bytes": data,
        "config": config,
        "identity": {
            "format": CONFIGURATION_FORMAT,
            "name": config["name"],
            "path": rel,
            "sha256": hashlib.sha256(data).hexdigest(),
            "block_sha256": _block_sha256(block),
        },
    }


def _load_state() -> dict[str, Any]:
    """The configuration of this process, or its loading problem (never an exit at import)."""
    try:
        path, why = checked_path(os.environ.get(CONFIGURATION_ENV) or "")
        if why is not None:
            raise ValueError(f"{CONFIGURATION_ENV}: {why}")
        return {"ok": True, "problem": None, **capture(path)}
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        return {"ok": False, "problem": f"M4 configuration not loaded: {exc}"}
    except Exception as exc:  # a validation error of the block
        return {"ok": False, "problem": f"M4 configuration not loaded: {type(exc).__name__}: {exc}"}


STATE = _load_state()


def require_state() -> dict[str, Any]:
    if not STATE["ok"]:
        raise RuntimeError(STATE["problem"])
    return STATE


def _plan():
    from refute.packs.tess.params import TessTestPlan

    state = require_state()
    plan = json.loads(json.dumps(pv2.FAST_PLAN))
    plan.setdefault("gauntlet", {})["corrections"] = dict(state["config"]["corrections"])
    resolved = TessTestPlan.model_validate(plan)
    if not resolved.gauntlet.corrections.active:
        raise RuntimeError("the configuration does not activate M4")
    return resolved


# --- the declaration (Amendment 25, A.1 and A.4) ---------------------------------------------


def m4_declaration_problems(decl: dict) -> list[str]:
    """The problems of a declaration's ``m4_configuration`` member against this process's
    captured configuration (or the loading problem)."""
    if not STATE["ok"]:
        return [STATE["problem"]]
    member = decl.get("m4_configuration")
    if not isinstance(member, dict) or set(member) != {"format", "name", "path", "sha256"}:
        return ["the declaration's m4_configuration member is missing or malformed"]
    problems = []
    path, why = checked_path(str(member.get("path")), declared=True)
    if why is not None:
        problems.append(f"m4_configuration: {why}")
    elif path != STATE["path"]:
        problems.append("m4_configuration names another file than the configuration loaded")
    ident = STATE["identity"]
    for key in ("format", "name", "sha256"):
        if member.get(key) != ident[key]:
            problems.append(f"m4_configuration {key} {member.get(key)!r} is not {ident[key]!r}")
    return problems


_V2_OPEN_CAMPAIGN = pv2.open_campaign


def open_campaign(root, campaign_id):
    camp = _V2_OPEN_CAMPAIGN(root, campaign_id)
    camp.problems.extend(m4_declaration_problems(camp.declaration))
    os.environ.pop(EXPECTED_ENV, None)
    if not camp.problems:
        # the expected identity, only from a declaration with no problem at all, for every
        # worker started later
        os.environ[EXPECTED_ENV] = json.dumps(STATE["identity"], sort_keys=True)
    return camp


# --- the workers and the identity journal (Amendment 25, A.5) --------------------------------


def expected_identity() -> dict | None:
    text = os.environ.get(EXPECTED_ENV)
    try:
        return json.loads(text) if text else None
    except ValueError:
        return None


def _worker_problem() -> str | None:
    expected = expected_identity()
    if expected is None:
        return "no expected M4 identity in this worker's environment"
    if not STATE["ok"]:
        return STATE["problem"]
    if STATE["identity"] != expected:
        return "this worker's M4 configuration is not the expected identity"
    block = pv2._plan().gauntlet.corrections.model_dump(mode="json")
    if hashlib.sha256(pv2.canonical_json(block)).hexdigest() != expected["block_sha256"]:
        return "this worker's plan does not carry the expected corrections block"
    return None


_V2_ANALYZE_TASK = pv2.analyze_task


def analyze_task(task):
    """Version 2's ``analyze_task`` in this module (so a spawned worker imports version 3 first);
    the worker refuses before the inherited analysis unless its identity is the expected one, and
    returns its identity in the result's envelope."""
    entry = task[0]
    why = _worker_problem()
    if why is not None:
        return {"case": entry["id"], "infrastructure": f"m4 identity: {why}", "pid": os.getpid()}
    result = _V2_ANALYZE_TASK(task)
    if "integrity" not in result and "infrastructure" not in result:
        result["m4_identity"] = dict(STATE["identity"])
    return result


def journal_append(run_dir: str | os.PathLike, entry: dict) -> None:
    path = pv2.inside_project(Path(run_dir) / IDENTITY_JOURNAL, "the M4 identity journal")
    with open(path, "ab") as fh:
        fh.write(pv2.canonical_json(entry) + b"\n")
        fh.flush()
        os.fsync(fh.fileno())


def journal_entries(run_dir: str | os.PathLike) -> list[dict]:
    path = Path(run_dir) / IDENTITY_JOURNAL
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_bytes().splitlines() if line.strip()]


def check_result(run_dir: str | os.PathLike, result: dict) -> dict:
    """The main process's check of one analysis result: a confirmation in the identity journal, or
    a refusal (then the result becomes an infrastructure failure, which stops the dispatch)."""
    expected = expected_identity()
    case, pid = result.get("case"), result.get("pid")
    if "integrity" in result:
        return result
    infra = result.get("infrastructure")
    if infra is None and expected is not None and result.get("m4_identity") == expected:
        journal_append(
            run_dir,
            {
                "kind": "confirmation",
                "case": case,
                "pid": pid,
                "record_sha256": result.get("sha256"),
                "identity": expected,
            },
        )
        return result
    reason = infra or "the result carries no valid M4 identity"
    journal_append(run_dir, {"kind": "refusal", "case": case, "pid": pid, "reason": reason})
    return {**result, "infrastructure": reason}


_V2_RUN_POOL = pv2.run_pool


def run_pool(fn, tasks: list, workers: int, declared_dispatch: dict, *, on_worker, on_result):
    if fn is not analyze_task:
        return _V2_RUN_POOL(
            fn, tasks, workers, declared_dispatch, on_worker=on_worker, on_result=on_result
        )

    def checked(i, r):
        return on_result(i, check_result(tasks[i][2], r))

    return _V2_RUN_POOL(
        fn, tasks, workers, declared_dispatch, on_worker=on_worker, on_result=checked
    )


def _plain(value):
    if isinstance(value, dict):
        if "dec" in value:  # the record's typed float
            return float(value["dec"])
        return {k: _plain(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_plain(v) for v in value]
    return value


def _is_sha256(value) -> bool:
    return (
        isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)
    )


def _complete_confirmation(e: dict, expected: dict) -> bool:
    """A confirmation with its whole schema: the kind, the case, a PID, the record's SHA-256 and
    the expected identity (the Codex review of the package: an incomplete one is never valid)."""
    return (
        set(e) == {"kind", "case", "pid", "record_sha256", "identity"}
        and e["kind"] == "confirmation"
        and isinstance(e["case"], str)
        and isinstance(e["pid"], int)
        and not isinstance(e["pid"], bool)
        and _is_sha256(e["record_sha256"])
        and e["identity"] == expected
    )


def resume_problems(
    run_dir: str | os.PathLike,
    cases: list[str] | None = None,
    expected: dict | None = None,
) -> list[str]:
    """Amendment 25, A.5: a persisted record of the run folder is accepted only with a complete
    confirmation in the identity journal that matches its bytes, its PID and the expected
    identity; a refusal, a missing, incomplete or mismatched confirmation, or another corrections
    block is a problem. A record of status ``error`` (a traceback, no conditions) needs its
    confirmation only."""
    expected = expected if expected is not None else expected_identity()
    folder = Path(run_dir) / "cases"
    files = sorted(folder.glob("*.json")) if folder.is_dir() else []
    if cases is not None:
        files = [f for f in files if f.stem in set(cases)]
    if not files:
        return []
    if expected is None:
        return ["no expected M4 identity: the persisted records cannot be checked"]
    entries = journal_entries(run_dir)
    refused = {e.get("case") for e in entries if e.get("kind") == "refusal"}
    confirmed = {
        (e["case"], e["record_sha256"]): e["pid"]
        for e in entries
        if isinstance(e, dict) and _complete_confirmation(e, expected)
    }
    problems = []
    for f in files:
        case = f.stem
        data = f.read_bytes()
        sha = hashlib.sha256(data).hexdigest()
        if case in refused:
            problems.append(f"{case}: its result was refused (identity journal)")
            continue
        if (case, sha) not in confirmed:
            problems.append(
                f"{case}: no complete confirmation of its M4 identity matches the record"
            )
            continue
        try:
            rec = json.loads(data)
            if (rec.get("operational") or {}).get("pid") != confirmed[(case, sha)]:
                problems.append(f"{case}: the confirmation's PID is not the record's")
                continue
            if rec.get("status") == "error":
                continue  # a permanent scientific error: its identity is the confirmation's
            block = _plain(
                rec["conditions"]["i"]["scientific"]["test_plan"]["gauntlet"]["corrections"]
            )
            if _block_sha256(block) != expected["block_sha256"]:
                problems.append(f"{case}: its corrections block is not the expected one")
        except (KeyError, TypeError, ValueError, AttributeError) as exc:
            problems.append(f"{case}: its corrections block cannot be read ({exc})")
    return problems


_V2_MODE_ANALYZE = pv2.mode_analyze


def mode_analyze(args) -> int:
    """Version 2's analysis after the resume check of the run folder, against the captured
    identity (the campaign is opened once, by version 2's mode, through ``open_campaign``); a
    loading problem refuses at once."""
    if not STATE["ok"]:
        pv2.refuse("the M4 configuration is not loaded", [STATE["problem"]])
    run_dir = pv2.inside_project(args.out, "--out")
    problems = resume_problems(run_dir, expected=STATE["identity"])
    if problems:
        pv2.refuse("existing results without a confirmed M4 identity", problems)
    return _V2_MODE_ANALYZE(args)


_V2_SLOT_RECORDS = pv2.slot_records


def slot_records(run_dir, lot, by_id, expect, allowed=None):
    """Version 2's reader of a lot's records (``compare-slots``, the resume of ``orchestrate``,
    ``metrics``), plus the M4 identity of every record it reads (the Codex review of the
    package: every consumer, not only ``analyze``)."""
    recs, hashes, problems = _V2_SLOT_RECORDS(run_dir, lot, by_id, expect, allowed)
    present = [c for c in lot if (Path(run_dir) / "cases" / f"{c}.json").is_file()]
    problems += [f"M4 identity: {p}" for p in resume_problems(run_dir, present)]
    return recs, hashes, problems


# --- the close (Amendment 25, A.6) and R2 ----------------------------------------------------


def configuration_changed() -> bool:
    if not STATE["ok"]:
        return True
    try:
        return Path(STATE["path"]).read_bytes() != STATE["bytes"]
    except OSError:
        return True


_V2_CLOSE = pv2.Execution.close


def close(self, payload: dict) -> bool:
    if configuration_changed():
        pv2.write_lock(
            self.camp,
            self.identity,
            {"kind": "m4_configuration", "execution_id": self.identity["execution_id"]},
            "the M4 configuration changed on disk during the execution",
            [
                {
                    "path": str(STATE.get("path")),
                    "sha256_at_start": STATE.get("identity", {}).get("sha256"),
                }
            ],
        )
        _V2_CLOSE(self, {**payload, "m4_configuration_changed": True})
        return False
    return _V2_CLOSE(self, payload)


def harness_problems() -> tuple[str, list[str]]:
    """R2 for version 3: this file, version 2 and the configuration file are each the file of
    HEAD and unchanged since the process started; then version 2's own checks of the comparator."""
    head = pv2.git(V3_PATH.parent, "rev-parse", "HEAD")
    problems = pv2.committed_problems(V3_PATH, V3_SHA256)
    problems += pv2.committed_problems(V2_PATH, V2_SHA256)
    if STATE["ok"]:
        problems += pv2.committed_problems(STATE["path"], STATE["identity"]["sha256"])
        if configuration_changed():
            problems.append("the configuration file changed on disk after this process started")
    else:
        problems.append(STATE["problem"])
    if pv2.file_sha256(V3_PATH) != V3_SHA256:
        problems.append("the harness (version 3) changed on disk after this process started")
    if pv2.file_sha256(V2_PATH) != V2_SHA256:
        problems.append("population_v2.py changed on disk after this process started")
    problems += pv2.committed_problems(pv2.COMPARATOR_PATH, pv2.COMPARATOR_SHA256_AT_START)
    if pv2.file_sha256(pv2.COMPARATOR_PATH) != pv2.COMPARATOR_SHA256_AT_START:
        problems.append("the comparator file changed on disk after this process started")
    if pv2.CMP.COMPARATOR_SHA256 != pv2.COMPARATOR_SHA256_AT_START:
        problems.append("the comparator module loaded is not the file read at start")
    return head, problems


def install() -> None:
    """Apply the replacements to the loaded version 2 (idempotent)."""
    pv2._plan = _plan
    pv2.open_campaign = open_campaign
    pv2.analyze_task = analyze_task
    pv2.run_pool = run_pool
    pv2.mode_analyze = mode_analyze
    pv2.slot_records = slot_records
    pv2.Execution.close = close
    pv2.harness_problems = harness_problems
    pv2.HARNESS_PATH = V3_PATH
    pv2.HARNESS_SHA256 = V3_SHA256


install()


def main(argv: list[str] | None = None) -> int:
    # The main process never keeps an expected identity it inherited: it publishes its own after a
    # clean opening of the campaign. (Done here, at the explicit entry, and not at import: a
    # spawned worker imports this file too and must keep the identity it inherited.)
    os.environ.pop(EXPECTED_ENV, None)
    return pv2.main(argv)
