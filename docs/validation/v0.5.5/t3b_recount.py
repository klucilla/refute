"""v0.5.5: T3b's dated recount of the frozen frame (#218; the maintainer's decisions of 2026-11-21,
13:30, item 5; the design is ``docs/plans/v0.5.5-t3b-preparation.md``, fixed before the data).
``method_status: not_validated``.

A count, not a selection. The frame, domain, threshold and readings are the design's:
- the frame: v0.5's C3 false-positive pool, rebuilt from v0.5's frozen inputs (each SHA-256
  checked by ``c3select.read_pools``): 63 members, 41 walked, 11 accepted, 22 never walked;
- reading A: the 22 never walked; reading B: every member not accepted by v0.5 (52), in one
  simultaneous recount; the 11 accepted are earlier targets and are not triaged;
- the domain: v0.4's D-1 to D-9 through ``pilot.triage``, unchanged, with v0.5's frozen S_max;
- the threshold: 11.

v0.5.4's ``t3b_count.py`` supplies the provenance, the per-search logging and the canonical text,
unchanged. Metadata queries to MAST only; no new access to ExoFOP. TESS-EB is under a restricted
licence (#33): per-star rows stay in ``.cache/v055/t3b-recount/``; the repository receives counts
only (``t3b-recount.json``). The process time is charged to v0.5.5's charges.

Usage (from the project root):
``.venv/Scripts/python.exe -B docs/validation/v0.5.5/t3b_recount.py``.
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
V054 = ROOT / "docs/validation/v0.5.4"
for p in (str(V054), str(HERE), str(ROOT / "src")):
    if p not in sys.path:
        sys.path.insert(0, p)
import t3b_count as tc  # noqa: E402  (v0.5.4's, unchanged: provenance, logging, canonical text)

CACHE = ROOT / ".cache/v055/t3b-recount"
OUT = HERE / "t3b-recount.json"
FRAME = {"members": 63, "walked": 41, "accepted_by_v05": 11, "never_walked": 22}
NEEDED = 11
ATTEMPTS, BACKOFF = 5, 120.0
DECISION = "the maintainer's decisions of 2026-11-21 (13:30) at G1, item 5 (#218)"


def readings(members: set[int], walked: set[int], accepted: set[int]) -> dict[str, list[int]]:
    """The design's readings from the frame: A, the members never walked; B, every member not
    accepted by v0.5. Refused unless the frame is the design's."""
    frame = {
        "members": len(members),
        "walked": len(walked & members),
        "accepted_by_v05": len(accepted),
        "never_walked": len(members - walked),
    }
    if frame != FRAME or walked - members or accepted - walked:
        raise SystemExit(f"the frame is {frame}, not the design's: STOP")
    return {"A": sorted(members - walked), "B": sorted(members - accepted)}


def tally(results: dict[int, tuple[bool, str]], stars: list[int]) -> dict:
    """A reading's count over its stars: accepted, rejections by clause, the shortage."""
    k = sum(results[t][0] for t in stars)
    clauses: dict[str, int] = {}
    for t in stars:
        ok, reason = results[t]
        if not ok:
            clause = reason.split(":", 1)[0].strip()
            clauses[clause] = clauses.get(clause, 0) + 1
    return {
        "stars": len(stars),
        "accepted_by_the_domain": k,
        "rejected_by_clause": dict(sorted(clauses.items())),
        "needed": NEEDED,
        "shortage": max(0, NEEDED - k),
    }


def frame_sets() -> tuple[set[int], set[int], set[int]]:
    from refute.packs.tess.calib05 import c3select

    inputs = json.loads(tc.FROZEN.read_text("utf-8"))
    built, _ = c3select.read_pools(ROOT, tc.INPUTS, inputs)  # each catalog's SHA-256 checked
    members = {p.tic_id for p in built["false_positive"]}
    walk = json.loads((ROOT / tc.SELECTION).read_text("utf-8"))["pools"]["false_positive"]["walk"]
    walked = {int(d["tic_id"]) for d in walk["decisions"]}
    accepted = {int(a["tic_id"] if isinstance(a, dict) else a) for a in walk["accepted"]}
    return members, walked, accepted


def sources() -> dict:
    """Each frozen input's source and retrieval date, from v0.5's inputs.json."""
    inputs = json.loads(tc.FROZEN.read_text("utf-8"))
    out = {}

    def walk(node, path=""):
        if isinstance(node, dict):
            if "url" in node and "retrieved_utc" in node:
                out[path or "root"] = {
                    "url": node["url"],
                    "retrieved_utc": node["retrieved_utc"],
                    "sha256": node.get("sha256"),
                }
            for k, v in node.items():
                walk(v, f"{path}.{k}" if path else k)
        elif isinstance(node, list):  # the fix of 2026-11-21: lists were not traversed
            for i, v in enumerate(node):
                walk(v, f"{path}[{i}]")

    walk(inputs)
    return out


SOURCES = HERE / "t3b-recount-sources.json"


def write_sources() -> None:
    """A correction as a new record (``t3b-recount.json`` keeps its bytes): its
    ``frozen_inputs`` field came out empty because ``sources`` did not traverse lists. This
    record lists each frozen input's source, retrieval date and SHA-256 from v0.5's inputs.json,
    with no new query, bound to the recount record by its SHA-256."""
    if SOURCES.exists():
        raise SystemExit(f"{SOURCES.name} exists: written once")
    found = sources()
    if not found:
        raise SystemExit("no source found in inputs.json: STOP")
    doc = {
        "label": "v0.5.5 T3b: the recount's frozen inputs, a correction record",
        "method_status": "not_validated",
        "corrects": "t3b-recount.json, its empty frozen_inputs field (a script defect: lists "
        "were not traversed); that record keeps its bytes",
        "recount_record_sha256": hashlib.sha256(OUT.read_bytes()).hexdigest(),
        "inputs_json_sha256": hashlib.sha256(tc.FROZEN.read_bytes()).hexdigest(),
        "frozen_inputs": found,
        "written_utc": tc._utc(),
    }
    SOURCES.write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n", "utf-8", newline="\n")
    print(json.dumps(found, indent=1))


def main() -> None:
    import ledger_v055 as lv

    from refute.packs.tess.discover import pilot
    from refute.packs.tess.discover.protocol import DOMAIN
    from refute.selection.walk import RetriesExhaustedError, RetryPolicy, with_retries

    if OUT.exists():
        raise SystemExit(f"{OUT.name} exists: the recount is written once")
    started = time.process_time()
    prov = tc.provenance()  # binds inputs.json and the selection record before they are read
    s_max = int(json.loads(tc.FROZEN.read_text("utf-8"))["s_max"])
    members, walked, accepted = frame_sets()
    sets = readings(members, walked, accepted)
    CACHE.mkdir(parents=True, exist_ok=True)
    log = CACHE / "decisions.jsonl"
    if log.exists():
        raise SystemExit(f"{log} exists: the recount is written once")
    results: dict[int, tuple[bool, str]] = {}
    retried = 0
    policy = RetryPolicy(ATTEMPTS, BACKOFF)
    original = pilot.sel.transient
    try:
        with log.open("x", encoding="utf-8", newline="\n") as fh:
            for tic in sets["B"]:
                queries: list = []
                tries: list = []
                tc._logging(pilot.sel, original, queries)

                def attempt(tic=tic, tries=tries):
                    entry = {"n": len(tries) + 1, "utc": tc._utc()}
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
                results[tic] = (bool(ok), str(reason))
                line = {"tic_id": tic, "reading_A": tic in sets["A"], "accepted": ok,
                        "reason": reason, "evidence": evidence,
                        "failed_attempts": [vars(a) for a in failures], "attempts": tries,
                        "queries": queries}  # fmt: skip
                fh.write(json.dumps(line, sort_keys=True, default=str) + "\n")
                fh.flush()
    finally:
        pilot.sel.transient = original
    doc = {
        "label": "v0.5.5 T3b: the dated recount of the frozen frame (counts only; it selects, "
        "draws and records nothing)",
        "method_status": "not_validated",
        "decision": DECISION,
        "design": "docs/plans/v0.5.5-t3b-preparation.md",
        "frame": FRAME,
        "frozen_inputs": sources(),
        "provenance": prov,
        "domain": "v0.4 D-1 to D-9 (pilot.triage), unchanged",
        "s_max": s_max,
        "reading_A_never_walked": tally(results, sets["A"]),
        "reading_B_not_accepted_by_v05": tally(results, sets["B"]),
        "excluded": "the 11 stars v0.5 accepted (earlier targets), not triaged",
        "stars_with_a_retried_query": retried,
        "metadata_source": "MAST: the TIC catalog and the SPOC 120-s light-curve and pixel-file "
        "listings, read at the times in the per-star log",
        "per_star_log": "kept in .cache/v055/t3b-recount/ (TESS-EB is under a restricted licence)",
        "per_star_log_sha256": hashlib.sha256(log.read_bytes()).hexdigest(),
        "counted_utc": tc._utc(),
        "note": "a shortage is a counted fact, not a record; availability and infeasibility "
        "records are a stop that is not delegated",
    }
    OUT.write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n", "utf-8", newline="\n")
    used = time.process_time() - started
    lv.charge(f"t3b_recount_{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}", used / 3600.0,
              f"t3b_recount.py: process time {used:.1f} s")  # fmt: skip
    shown = {k: doc[k] for k in ("reading_A_never_walked", "reading_B_not_accepted_by_v05")}
    print(json.dumps(shown, indent=1))


if __name__ == "__main__":
    if sys.argv[1:] == ["sources"]:
        write_sources()
    else:
        main()
