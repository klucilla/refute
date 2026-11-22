"""T3b: the count of the updated frame (#218; the maintainer's addendum of 2026-11-21, 22:45,
item 2: the pause's trigger 5 fired with NExScI's answer; the design is
``docs/plans/v0.5.5-t3b-preparation.md``, section 3, fixed before these data).
``method_status: not_validated``.

A count, not a selection: nothing is drawn, ordered by randomness, chosen, adjudicated or run.

- **The updated frame:** the same frame rule as v0.5's C3 false-positive pool, on a later TOI
  table. ``c3select.pools`` and ``selection.fp_pool``, unchanged, are applied to:
  - the NASA Exoplanet Archive's TOI table, read by v0.5.6 part A's TAP query
    (``.cache/v056/frame/toi.csv``, its SHA-256 checked; the columns mapped to the ExoFOP names
    the rule reads);
  - the Archive's PSCompPars (the same snapshot);
  - the same TESS-EB static edition (``pilot.TESS_EB_STATIC``, checked).
- **The exclusions:** the targets of v0.1 to v0.4 (``c3select.known_targets``) and every target of
  v0.5 (``calibration/v0.5/selection/targets.yaml``, reserves included).
- **The domain:** v0.4's D-1 to D-9 through ``pilot.triage``, unchanged, with v0.5's S_max (107).
- **The order:** ascending TIC, deterministic, with no randomness. The count stops when 11 stars
  are accepted (the threshold): at that point the maintainer stops, because selecting real targets
  and the drand round are his. Otherwise every member is triaged.
- **Retries and logs:** v0.5.4's rules and logging (``t3b_count``): 5 attempts, 120 s apart; a
  failure is never a rejection. Per-star rows name TESS-EB members (a restricted licence, #33),
  so they stay in ``.cache/v056/t3b/``; the repository receives counts only
  (``t3b-updated-count.json``).

Metadata only (MAST's TIC catalog and SPOC listings); no light curve, pixel file or note is read.

Usage (from the project root):
``.venv/Scripts/python.exe docs/validation/v0.5.6/t3b_updated_count.py``.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
V054 = ROOT / "docs/validation/v0.5.4"
for p in (str(V054), str(ROOT / "src")):
    if p not in sys.path:
        sys.path.insert(0, p)
import t3b_count as tc  # noqa: E402  (v0.5.4's, unchanged: logging, canonical text)

FRAME_DIR = ROOT / ".cache/v056/frame"
CACHE = ROOT / ".cache/v056/t3b"
OUT = HERE / "t3b-updated-count.json"
V05_TARGETS = ROOT / "calibration/v0.5/selection/targets.yaml"
NEEDED = 11
S_MAX = 107
ATTEMPTS, BACKOFF = 5, 120.0
DECISION = "the maintainer's addendum of 2026-11-21 (22:45), item 2 (#218)"
MAPPING = {
    "tid": "TIC ID",
    "tfopwg_disp": "TFOPWG Disposition",
    "pl_orbper": "Period (days)",
    "pl_trandep": "Depth (ppm)",
    "toi": "TOI",
}


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def snapshot(name: str) -> tuple[bytes, dict]:
    data = (FRAME_DIR / f"{name}.csv").read_bytes()
    info = json.loads((FRAME_DIR / f"{name}.json").read_text("utf-8"))
    if _sha(data) != info["sha256"]:
        raise SystemExit(f"{name}.csv does not match its recorded SHA-256: STOP")
    return data, info


def mapped_toi(data: bytes) -> list[dict[str, str]]:
    """The Archive's TOI rows under the ExoFOP column names the frame rule reads."""
    rows = csv.DictReader(io.StringIO(data.decode("utf-8")))
    return [{MAPPING[k]: v for k, v in r.items() if k in MAPPING} for r in rows]


def frame() -> tuple[list[int], dict]:
    import yaml

    from refute.packs.tess.calib05 import c3select
    from refute.packs.tess.discover import pilot
    from refute.packs.tess.discover import selection as sel

    toi_data, toi_info = snapshot("toi")
    ps_data, ps_info = snapshot("pscomppars")
    eb = pilot.static_tess_eb(ROOT / pilot.TESS_EB_STATIC["path"], pilot.TESS_EB_STATIC)
    known = set(c3select.known_targets(ROOT))
    v05 = {int(t["tic_id"]) for t in yaml.safe_load(V05_TARGETS.read_text("utf-8"))["targets"]}
    built = c3select.pools(
        mapped_toi(toi_data), sel.pscomppars_rows(ps_data), sel.tess_eb_tics(eb), known
    )
    members = sorted({p.tic_id for p in built["false_positive"]} - v05)
    info = {
        "toi": toi_info,
        "pscomppars": ps_info,
        "tess_eb": {k: pilot.TESS_EB_STATIC[k] for k in ("source_url", "obtained", "sha256")},
        "v05_targets_sha256": _sha(V05_TARGETS.read_bytes()),
        "pool_before_v05_exclusion": len(built["false_positive"]),
        "excluded_v05_targets": len({p.tic_id for p in built["false_positive"]} & v05),
        "members": len(members),
    }
    return members, info


def main() -> None:
    from refute.packs.tess.discover import pilot
    from refute.packs.tess.discover.protocol import DOMAIN
    from refute.selection.walk import RetriesExhaustedError, RetryPolicy, with_retries

    if OUT.exists():
        raise SystemExit(f"{OUT.name} exists: the count is written once")
    started = time.process_time()
    members, info = frame()
    CACHE.mkdir(parents=True, exist_ok=True)
    log = CACHE / "decisions.jsonl"
    if log.exists():
        raise SystemExit(f"{log} exists: the count is written once")
    accepted, clauses, checked = 0, {}, 0
    policy = RetryPolicy(ATTEMPTS, BACKOFF)
    original = pilot.sel.transient
    try:
        with log.open("x", encoding="utf-8", newline="\n") as fh:
            for tic in members:
                if accepted >= NEEDED:
                    break
                queries: list = []
                tries: list = []
                tc._logging(pilot.sel, original, queries)

                def attempt(tic=tic, tries=tries):
                    entry = {"n": len(tries) + 1, "utc": tc._utc()}
                    tries.append(entry)
                    try:
                        answer = pilot.triage(tic, DOMAIN, S_MAX)
                    except BaseException as exc:
                        entry["error"] = f"{type(exc).__name__}: {exc}"
                        raise
                    entry["result"] = "accepted" if answer[0] else "rejected"
                    return answer

                try:
                    (ok, reason, evidence), failures = with_retries(attempt, policy, time.sleep)
                except BaseException as exc:
                    stop = {"tic_id": tic, "stop": f"{type(exc).__name__}: {exc}",
                            "attempts": tries, "queries": queries}  # fmt: skip
                    fh.write(json.dumps(stop, sort_keys=True, default=str) + "\n")
                    fh.flush()
                    why = type(exc).__name__
                    if isinstance(exc, RetriesExhaustedError):
                        why = "transient errors on every attempt"
                    raise SystemExit(f"TIC {tic}: {why}: STOP (resumable by a new record)") from exc
                checked += 1
                if ok:
                    accepted += 1
                else:
                    clause = str(reason).split(":", 1)[0].strip()
                    clauses[clause] = clauses.get(clause, 0) + 1
                line = {"tic_id": tic, "accepted": ok, "reason": reason, "evidence": evidence,
                        "failed_attempts": [vars(a) for a in failures], "attempts": tries,
                        "queries": queries}  # fmt: skip
                fh.write(json.dumps(line, sort_keys=True, default=str) + "\n")
                fh.flush()
    finally:
        pilot.sel.transient = original
    reached = accepted >= NEEDED
    doc = {
        "label": "T3b: the count of the updated frame (counts only; it selects, draws and "
        "records nothing)",
        "method_status": "not_validated",
        "decision": DECISION,
        "design": "docs/plans/v0.5.5-t3b-preparation.md, section 3",
        "inputs": info,
        "domain": "v0.4 D-1 to D-9 (pilot.triage), unchanged",
        "s_max": S_MAX,
        "order": "ascending TIC; no randomness",
        "needed": NEEDED,
        "members_triaged": checked,
        "accepted_by_the_domain": accepted,
        "rejected_by_clause": dict(sorted(clauses.items())),
        "reached_the_threshold": reached,
        "shortage": max(0, NEEDED - accepted) if checked == info["members"] or reached else None,
        "stopped_at_the_threshold": reached and checked < info["members"],
        "per_star_log": "kept in .cache/v056/t3b/ (TESS-EB is under a restricted licence)",
        "per_star_log_sha256": _sha(log.read_bytes()),
        "process_cpu_seconds": round(time.process_time() - started, 3),
        "counted_utc": tc._utc(),
        "note": "a count is a counted fact, not a record; selecting real targets, drand, and "
        "availability or infeasibility records are the maintainer's",
    }
    OUT.write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n", "utf-8", newline="\n")
    shown = ("members_triaged", "accepted_by_the_domain", "reached_the_threshold", "shortage")
    print(json.dumps({k: doc[k] for k in shown}, indent=1))


if __name__ == "__main__":
    main()
