"""v0.5.4: T3b's eligibility count of the approved frame's 22 remaining stars (#217; the
maintainer's decision of 2026-11-12, night, item 6; the design is
``docs/plans/v0.5.4-t3b-eligibility-count.md``). ``method_status: not_validated``.

A count, not a selection: nothing is drawn, ordered by randomness, chosen, adjudicated or run. Every
one of the 22 TESS-EB members of v0.5's false-positive pool that v0.5's walk never reached goes
through v0.5's own domain triage, unchanged (``pilot.triage`` with the v0.4 domain D-1 to D-9 and
v0.5's frozen S_max). These are metadata queries to MAST only (the TIC catalog and the SPOC 120-s
product listings); no light curve, pixel file or ExoFOP note is read, and ExoFOP is not accessed
again (the TOI table is v0.5's frozen copy).

**Provenance** (Codex, h2-t3b round 1):
- the pools come from ``c3select.read_pools``, which checks each frozen input's SHA-256;
- the files ``known_targets`` reads must equal their bytes at v0.5's freeze commit;
- v0.5's selection record must equal its committed bytes;
- the frame must be 63 members, 41 walked and 11 accepted, with 22 left.

**Retries:** each star's triage runs under ``with_retries`` with 5 attempts and 120 s of backoff.
The failed attempts are logged; exhausted retries stop the count, and a failure is never turned
into a rejection.

**Each search is logged on its own**, failed attempts included: the TIC query and the two MAST
searches (120-s light curves, pixel files), each with its context, its UTC time, and either the
SHA-256 of a canonical text of its answer or its error. The log goes through ``sel.transient``,
which ``pilot`` calls for every search; it is restored at the end. Any stop writes the star's
partial log first. ``inputs.json`` itself is bound to v0.5's freeze commit before it is read.

TESS-EB is under a restricted licence (#33), so per-star rows stay in ``.cache/v054/t3b-count/``;
the repository receives the counts only (``t3b-count.json``).

Usage (from the project root): ``.venv/Scripts/python.exe docs/validation/v0.5.4/t3b_count.py``.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
INPUTS = ROOT / ".cache/v05/inputs-attempts/attempt-01"
FROZEN = ROOT / "calibration/v0.5/inputs.json"
SELECTION = "calibration/v0.5/selection/selection.json"
KNOWN_FILES = (
    "calibration/targets.yaml",
    "calibration/v0.2/targets.yaml",
    "docs/validation/v0.2.1/reopen/stage-1/real-controls/result.json",
    "calibration/v0.4/selection/targets.yaml",
)
CACHE = ROOT / ".cache/v054/t3b-count"
OUT = HERE / "t3b-count.json"
FRAME = {"members": 63, "walked": 41, "accepted_by_v05": 11}
EXPECTED = 22
NEEDED = 11
ATTEMPTS, BACKOFF = 5, 120.0


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _git(*args: str) -> bytes:
    out = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, check=True)
    return out.stdout


def provenance() -> dict:
    """Every input other than the three frozen catalogs, bound to a commit; any difference
    stops."""
    sys.path.insert(0, str(ROOT / "src"))
    from refute.packs.tess.calib05 import c3select

    freeze = c3select.freeze_commit(ROOT)
    out = {"v05_freeze_commit": freeze, "files": {}}
    for path in ("calibration/v0.5/inputs.json", *KNOWN_FILES):
        now = (ROOT / path).read_bytes()
        if now != _git("show", f"{freeze}:{path}"):
            raise SystemExit(f"{path}: not its bytes at v0.5's freeze commit: STOP")
        out["files"][path] = _sha(now)
    added = _git("log", "--diff-filter=A", "--format=%H", "--", SELECTION).decode().split()
    if len(added) != 1:
        raise SystemExit(f"{SELECTION}: {len(added)} commits added it: STOP")
    now = (ROOT / SELECTION).read_bytes()
    if now != _git("show", f"HEAD:{SELECTION}"):
        raise SystemExit(f"{SELECTION}: differs from its committed bytes: STOP")
    out["files"][SELECTION] = _sha(now)
    out["selection_commit"] = added[0]
    return out


def remaining() -> tuple[list[int], dict]:
    """The approved frame's members that v0.5's walk never reached."""
    sys.path.insert(0, str(ROOT / "src"))
    from refute.packs.tess.calib05 import c3select

    inputs = json.loads(FROZEN.read_text("utf-8"))
    built, _ = c3select.read_pools(ROOT, INPUTS, inputs)  # each catalog's SHA-256 checked
    members = {p.tic_id for p in built["false_positive"]}
    walk = json.loads((ROOT / SELECTION).read_text("utf-8"))["pools"]["false_positive"]["walk"]
    walked = {int(d["tic_id"]) for d in walk["decisions"]}
    frame = {
        "members": len(members),
        "walked": len(walked & members),
        "accepted_by_v05": len(walk["accepted"]),
    }
    left = sorted(members - walked)
    if frame != FRAME or len(left) != EXPECTED or walked - members:
        raise SystemExit(f"the frame is {frame} with {len(left)} left: STOP")
    return left, frame


def _canonical(answer) -> str:
    """A canonical text of a search's answer: an astropy table's rows (a lightkurve search result
    through its ``table``), as strings."""
    table = getattr(answer, "table", answer)
    try:
        rows = [[str(v) for v in row] for row in table]
        cols = list(getattr(table, "colnames", []))
    except TypeError:
        return json.dumps(str(answer))
    return json.dumps({"columns": cols, "rows": rows})


def _logging(sel, original, queries: list) -> None:
    """Wrap ``sel.transient``, through which ``pilot.tic_fields`` and ``pilot.listing`` make every
    search (one TIC query, two MAST searches), so that each search is logged on its own, with its
    context, its UTC time, and either the SHA-256 of its answer or its error. Always from the
    original function, so that no wrapper nests across stars."""

    def logged(call, context):
        entry = {"context": context, "utc": _utc()}
        queries.append(entry)
        try:
            answer = original(call, context)
        except BaseException as exc:
            entry["error"] = f"{type(exc).__name__}: {exc}"
            raise
        entry["answer_sha256"] = _sha(_canonical(answer).encode())
        return answer

    sel.transient = logged


def _utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def main() -> None:
    sys.path.insert(0, str(ROOT / "src"))
    from refute.packs.tess.discover import pilot
    from refute.packs.tess.discover.protocol import DOMAIN
    from refute.selection.walk import RetriesExhaustedError, RetryPolicy, with_retries

    if OUT.exists():
        raise SystemExit(f"{OUT.name} exists: the count is written once")
    prov = provenance()  # binds inputs.json to v0.5's freeze commit before it is read
    s_max = int(json.loads(FROZEN.read_text("utf-8"))["s_max"])
    left, frame = remaining()
    CACHE.mkdir(parents=True, exist_ok=True)
    log = CACHE / "decisions.jsonl"
    if log.exists():
        raise SystemExit(f"{log} exists: the count is written once")
    accepted, clauses, retried = 0, {}, 0
    policy = RetryPolicy(ATTEMPTS, BACKOFF)
    original = pilot.sel.transient
    try:
        with log.open("x", encoding="utf-8", newline="\n") as fh:
            for tic in left:
                queries: list = []  # every search of this star, failed attempts included
                tries: list = []  # every triage attempt of this star, with its outcome
                _logging(pilot.sel, original, queries)

                def attempt(tic=tic, tries=tries):
                    entry = {"n": len(tries) + 1, "utc": _utc()}
                    tries.append(entry)
                    try:
                        answer = pilot.triage(tic, DOMAIN, s_max)
                    except BaseException as exc:
                        entry["error"] = f"{type(exc).__name__}: {exc}"
                        raise
                    entry["result"] = "accepted" if answer[0] else "rejected"
                    return answer

                try:
                    (ok, reason, evidence), failures = with_retries(attempt, policy, time.sleep)
                except BaseException as exc:  # the partial log is kept before the stop
                    stop = {"tic_id": tic, "stop": f"{type(exc).__name__}: {exc}",
                            "attempts": tries, "queries": queries}  # fmt: skip
                    fh.write(json.dumps(stop, sort_keys=True) + "\n")
                    fh.flush()
                    why = type(exc).__name__
                    if isinstance(exc, RetriesExhaustedError):
                        why = "transient errors on every attempt"
                    raise SystemExit(f"TIC {tic}: {why}: STOP") from exc
                retried += bool(failures)
                line = {"tic_id": tic, "accepted": ok, "reason": reason, "evidence": evidence,
                        "failed_attempts": [vars(a) for a in failures], "attempts": tries,
                        "queries": queries}  # fmt: skip
                fh.write(json.dumps(line, sort_keys=True, default=str) + "\n")
                fh.flush()
                if ok:
                    accepted += 1
                else:
                    clause = reason.split(":", 1)[0].strip()
                    clauses[clause] = clauses.get(clause, 0) + 1
    finally:
        pilot.sel.transient = original
    doc = {
        "label": "v0.5.4 T3b: the eligibility count of the approved frame's remaining stars "
        "(counts only; it selects nothing)",
        "method_status": "not_validated",
        "decision": "the maintainer's decision of 2026-11-12 (night), item 6 (#217)",
        "frame": frame,
        "provenance": prov,
        "triaged": len(left),
        "accepted_by_the_domain": accepted,
        "rejected_by_clause": dict(sorted(clauses.items())),
        "stars_with_a_retried_query": retried,
        "frame_domain_eligible_in_all": frame["accepted_by_v05"] + accepted,
        "in_all_note": "11 from v0.5's queries of 2026-11 and k from today's queries: not one "
        "simultaneous recount of the 63",
        "needed_for_a_new_confirmation_sample": NEEDED,
        "shortage": max(0, NEEDED - accepted),
        "domain": "v0.4 D-1 to D-9 (pilot.triage), unchanged",
        "s_max": s_max,
        "per_star_log_sha256": _sha(log.read_bytes()),
        "per_star_log": "kept in .cache/v054/t3b-count/ (TESS-EB is under a restricted licence)",
        "counted_utc": _utc(),
        "note": "a shortage is a counted fact, not an infeasibility record",
    }
    OUT.write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n", "utf-8", newline="\n")
    print(json.dumps({k: doc[k] for k in ("accepted_by_the_domain", "rejected_by_clause",
                                          "shortage")}, indent=1))  # fmt: skip


if __name__ == "__main__":
    main()
