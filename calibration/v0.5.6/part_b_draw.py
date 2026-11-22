"""v0.5.6 part B (confirmatory): the pool, the drand round and the draw (docs/plans/
v0.5.6-plan-amendment-1.md; the maintainer's decisions of 2026-11-22, 13:00, items 3 and 5;
#218). ``method_status: not_validated``. Limits label: 'WEAKENED; does not meet D1, D2, D4, T2a'.

Steps, each refusing to write over its output:

1. ``pool`` (before the lock): the two strata of the **confirmation half**, from the frame as
   committed (``part-a-frame.csv``, its SHA-256 checked against ``part-a-frame.json``) and the
   prior-exposure scan as committed (``part-b-prep.json``, its SHA-256 checked against the claim):
   - ``planet``: the planet arm (exactly one PSCompPars planet discovered by TESS within 1 %);
   - ``fp``: the open arm with the frame's ``tfopwg_disp_descriptive`` equal to ``FP``;
   - every TIC of ``exposed_tics`` is left out; FA, PC, APC, KP, CP and blank are not drawn.
   Written as the claim's targets attachment (``pool-targets.yaml``, ``refute-tess-targets-1``):
   kinds ``planet`` and ``false_positive``, the TOI's ephemeris as ``published``.
2. ``round <lock-commit>`` (after the lock commit is pushed, as the head of its own push): the
   commit must add ``calibration/v0.5.6/claim.lock.json``. The round is the first drand round
   published at least ``ROUND_MARGIN_SECONDS`` (10 minutes) after the creation time of the CI push
   run of that commit (workflow ``ci.yml``, event ``push``, ``head_sha`` the commit, run attempt
   1; ``refute.drand.round_after``). No such run, or more than one, stops the step.
3. ``draw`` (once the round is published): the lock must verify (``refute verify``: PASS). The
   beacon is fetched and its BLS signature verified (``refute.drand.drand_seed``). Each stratum,
   sorted by TIC, is shuffled with ``random.Random(seed_s)`` (``refute.drand.shuffled``), where
   ``seed_s = int(sha256(randomness_hex + "|v0.5.6|part-b|" + stratum), 16)``. Each TIC in that
   order is checked from MAST **metadata only** with part A's own listing (``part_a_frame.py``:
   author SPOC, exposure exactly 120 s, ``*lc.fits``, the TIC itself, sectors up to 107) for at
   least two predicted transits; the walk stops at ``PER_STRATUM`` eligible TICs. No light curve
   is read. Checks before the record is written: confirmation half, the stratum's rule, no exposed
   TIC, unique TICs, no TIC and no product shared with part A's draw.

The draw's status is ``complete`` (150 per stratum), ``short`` (at least ``MIN_PER_STRATUM``, the
pool exhausted) or ``incomplete`` (fewer: the claim's evaluation ends INCONCLUSIVE).

Usage (from the project root): ``.venv/Scripts/python.exe -B calibration/v0.5.6/part_b_draw.py
pool|round <commit>|draw``.
"""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
VALIDATION = ROOT / "docs/validation/v0.5.6"
FRAME_FILE = VALIDATION / "part-a-frame.csv"
FRAME_RECORD = VALIDATION / "part-a-frame.json"
PREP = VALIDATION / "part-b-prep.json"
PART_A_DRAW = VALIDATION / "part-a-draw.json"
FRAME_CODE = VALIDATION / "part_a_frame.py"
CLAIM = HERE / "claim.yaml"
LOCK = HERE / "claim.lock.json"
POOL = HERE / "pool-targets.yaml"
ROUND = HERE / "part-b-round.json"
DRAW = HERE / "part-b-draw.json"
MAST_CACHE = ROOT / ".cache/v056/partb/mast"
LABEL = "WEAKENED; does not meet D1, D2, D4, T2a"
STRATA = ("planet", "fp")
PER_STRATUM = 150
MIN_PER_STRATUM = 120
ROUND_MARGIN_SECONDS = 600
SEED_TAG = "|v0.5.6|part-b|"
BATCH = 10
LOCK_PATH_IN_REPO = "calibration/v0.5.6/claim.lock.json"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def write_once(path: Path, text: str) -> None:
    if path.exists():
        raise SystemExit(f"{path.name} exists; never written over")
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, "utf-8", newline="\n")
    os.replace(tmp, path)


def frame_module():
    spec = importlib.util.spec_from_file_location("part_a_frame", FRAME_CODE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


def claim_inputs() -> dict[str, str]:
    """The SHA-256 the claim records for the files outside the code."""
    claim = yaml.safe_load(CLAIM.read_text("utf-8"))
    return claim["test_plan"]["discovery"]["inputs"]


def checked(path: Path, expected: str) -> bytes:
    data = path.read_bytes()
    if sha256(data) != expected:
        raise SystemExit(f"{path.name} does not match its recorded SHA-256")
    return data


# --- the strata (pure: the tests call them) ------------------------------------------------


def stratum_of(row: dict[str, str]) -> str | None:
    """``planet``, ``fp`` or None (not drawn), for a confirmation-half frame row."""
    if row["half"] != "confirmation":
        return None
    if row["arm"] == "planet":
        return "planet"
    if row["arm"] == "open" and row["tfopwg_disp_descriptive"] == "FP":
        return "fp"
    return None


def strata(rows: list[dict[str, str]], exposed: set[int]) -> dict[str, list[dict[str, str]]]:
    out: dict[str, list[dict[str, str]]] = {s: [] for s in STRATA}
    for r in rows:
        s = stratum_of(r)
        if s is not None and int(r["tic_id"]) not in exposed:
            out[s].append(r)
    for s in STRATA:
        out[s].sort(key=lambda r: int(r["tic_id"]))
    return out


def stratum_seed(randomness_hex: str, stratum: str) -> int:
    return int(sha256((randomness_hex + SEED_TAG + stratum).encode()), 16)


def order(rows: list[dict[str, str]], randomness_hex: str, stratum: str) -> list[dict[str, str]]:
    from refute.drand import shuffled

    return shuffled(rows, stratum_seed(randomness_hex, stratum), key=lambda r: int(r["tic_id"]))


# --- inputs ----------------------------------------------------------------------------------


def frozen_inputs() -> tuple[list[dict[str, str]], set[int], dict]:
    inputs = claim_inputs()
    record = json.loads(checked(FRAME_RECORD, inputs["frame_record"]))
    data = checked(FRAME_FILE, inputs["frame"])
    if sha256(data) != record["frame_sha256"]:
        raise SystemExit("the frame does not match part-a-frame.json")
    checked(FRAME_CODE, inputs["frame_code"])
    prep = json.loads(checked(PREP, inputs["prep"]))
    rows = list(csv.DictReader(io.StringIO(data.decode("utf-8"))))
    return rows, set(prep["exposure"]["exposed_tics"]), record


# --- 1. the pool -----------------------------------------------------------------------------


def pool() -> None:
    if POOL.exists():
        raise SystemExit("the pool is recorded; never written over")
    rows, exposed, record = frozen_inputs()
    groups = strata(rows, exposed)
    toi = record["sources"]["toi"]
    targets = []
    for s in STRATA:
        for r in groups[s]:
            tic = int(r["tic_id"])
            targets.append(
                {
                    "key": f"TIC-{tic}",
                    "tic_id": tic,
                    "kind": "planet" if s == "planet" else "false_positive",
                    "name": f"TOI-{r['toi']}",
                    "published": {
                        "period_days": float(r["period_days"]),
                        "t0_bjd": float(r["epoch_bjd"]),
                        "depth_ppm": float(r["depth_ppm"]),
                        "duration_hours": float(r["duration_hours"]),
                    },
                    "source": {
                        "name": "NASA Exoplanet Archive, TOI table (TAP)",
                        "url": toi["url"],
                        "retrieved_utc": toi["retrieved_utc"],
                        "reference": "part-a-frame.csv (committed), " + toi["sha256"],
                    },
                    "catalog": {
                        "toi": r["toi"],
                        "arm": r["arm"],
                        "pl_name": r["pl_name"],
                        "tfopwg_disp_descriptive": r["tfopwg_disp_descriptive"],
                        "tmag": r["tmag"],
                        "stratum": s,
                    },
                }
            )
    doc = {
        "schema": "refute-tess-targets-1",
        "generated_utc": utc(),
        "generator": "calibration/v0.5.6/part_b_draw.py pool",
        "selection": {
            "role": "the pool of part B's draw: the drand round orders it after the lock; only "
            "the drawn TICs are run",
            "limits_label": LABEL,
            "method_status": "not_validated",
            "frame_sha256": record["frame_sha256"],
            "exposed_excluded": len(exposed),
            "counts": {s: len(groups[s]) for s in STRATA},
        },
        "targets": targets,
    }
    write_once(POOL, yaml.safe_dump(doc, sort_keys=False, allow_unicode=True, width=100))
    print(doc["selection"]["counts"])


# --- 2. the round ----------------------------------------------------------------------------


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(ROOT), *args], capture_output=True, check=True, text=True
    ).stdout


def lock_round(commit: str) -> None:
    from refute.drand import round_after, round_time
    from refute.packs.tess.discover.pilot import push_run_created_at

    if ROUND.exists():
        raise SystemExit("the round is recorded; never written over")
    added = _git("show", "--diff-filter=A", "--name-only", "--format=", commit).split()
    if LOCK_PATH_IN_REPO not in added:
        raise SystemExit(f"{commit} does not add {LOCK_PATH_IN_REPO}")
    _git("merge-base", "--is-ancestor", commit, "origin/main")
    created = push_run_created_at(commit)
    number = round_after(created, ROUND_MARGIN_SECONDS)
    doc = {
        "schema": "refute-v056-part-b-round-1",
        "lock_commit": commit,
        "ci_push_run_created_at": created,
        "margin_seconds": ROUND_MARGIN_SECONDS,
        "round": number,
        "round_time_utc": round_time(number).isoformat(),
        "written_utc": utc(),
    }
    write_once(ROUND, json.dumps(doc, indent=1) + "\n")
    print(doc)


# --- 3. the draw -----------------------------------------------------------------------------


def _listing(paf, tics: list[int]) -> None:
    todo = [t for t in tics if not (MAST_CACHE / f"{t}.json").exists()]
    if not todo:
        return
    for tic, items in paf._listing_with_retries(todo).items():
        payload = {"tic_id": tic, "queried_utc": utc(), "products": items}
        tmp = MAST_CACHE / f"{tic}.json.tmp"
        tmp.write_bytes(json.dumps(payload, indent=1).encode())
        os.replace(tmp, MAST_CACHE / f"{tic}.json")


def walk(paf, ordered: list[dict[str, str]]) -> tuple[list[dict], list[dict]]:
    trail: list[dict] = []
    chosen: list[dict] = []
    k = 0
    while len(chosen) < PER_STRATUM and k < len(ordered):
        batch = ordered[k : k + BATCH]
        _listing(paf, [int(r["tic_id"]) for r in batch])
        for position, r in enumerate(batch, start=k):
            if len(chosen) >= PER_STRATUM:
                break
            tic = int(r["tic_id"])
            raw = (MAST_CACHE / f"{tic}.json").read_bytes()
            windows = json.loads(raw)["products"]
            n = paf.predicted(float(r["period_days"]), float(r["epoch_bjd"]), windows)
            if not windows:
                reason = f"no SPOC 120-s light curve up to sector {paf.MAX_SECTOR}"
            elif n < paf.MIN_PREDICTED:
                reason = f"{n} predicted transit(s) inside the sectors' time ranges"
            else:
                reason = "eligible"
            entry = {
                "position": position,
                "tic_id": tic,
                "toi": r["toi"],
                "reason": reason,
                "predicted_transits": n,
                "sectors": sorted({w["sector"] for w in windows}),
                "products": [w["productFilename"] for w in windows],
                "listing_sha256": sha256(raw),
            }
            trail.append(entry)
            if reason == "eligible":
                chosen.append({**entry, **{f: r[f] for f in paf.FRAME_FIELDS if f not in entry}})
        k += len(batch)
    return trail, chosen


def draw() -> None:
    from refute.core.lock import verify_claim
    from refute.drand import drand_seed

    if DRAW.exists():
        raise SystemExit("the draw is recorded; never written over")
    result = verify_claim(CLAIM)
    if result.status.value != "PASS":
        raise SystemExit(f"the lock does not verify: {result.status.value} {result.messages}")
    rnd = json.loads(ROUND.read_text("utf-8"))
    seed, beacon = drand_seed(int(rnd["round"]))
    randomness = beacon["randomness"]
    if int(randomness, 16) != seed:
        raise SystemExit("the beacon's randomness does not match its seed")
    rows, exposed, record = frozen_inputs()
    groups = strata(rows, exposed)
    paf = frame_module()
    part_a = json.loads(PART_A_DRAW.read_text("utf-8"))
    a_tics = {c["tic_id"] for a in part_a["arms"].values() for c in a["trail"]}
    a_products = {p for a in part_a["arms"].values() for c in a["trail"] for p in c["products"]}
    MAST_CACHE.mkdir(parents=True, exist_ok=True)
    arms, status = {}, "complete"
    for s in STRATA:
        ordered = order(groups[s], randomness, s)
        trail, chosen = walk(paf, ordered)
        tics = [c["tic_id"] for c in chosen]
        products = {p for c in chosen for p in c["products"]}
        problems = []
        if len(set(tics)) != len(tics):
            problems.append("a TIC drawn twice")
        if any(stratum_of(c) != s for c in chosen):
            problems.append("a TIC outside the stratum")
        if set(tics) & exposed:
            problems.append("an exposed TIC")
        if set(tics) & a_tics:
            problems.append("a TIC of part A")
        if products & a_products:
            problems.append("a product of part A")
        if problems:
            raise SystemExit(f"{s}: the draw failed its checks: {problems}")
        if len(chosen) < MIN_PER_STRATUM:
            status = "incomplete"
        elif len(chosen) < PER_STRATUM and status == "complete":
            status = "short"
        arms[s] = {"pool": len(ordered), "checked": len(trail), "eligible": len(chosen),
                   "chosen": chosen, "trail": trail}  # fmt: skip
    out = {
        "schema": "refute-v056-part-b-draw-1",
        "mode": "confirmatory",
        "limits_label": LABEL,
        "method_status": "not_validated",
        "status": status,
        "lock_sha256": sha256(LOCK.read_bytes()),
        "round": rnd,
        "beacon": beacon,
        "frame_sha256": record["frame_sha256"],
        "code_sha256": sha256(Path(__file__).read_bytes()),
        "seed_rule": "int(sha256(randomness_hex + '" + SEED_TAG + "' + stratum), 16); the "
        "stratum sorted by TIC, then random.Random(seed).shuffle",
        "listing": "MAST metadata (astroquery Observations), part A's listing and filters",
        "disjoint_from_part_a": {"tics": True, "products": True},
        "written_utc": utc(),
        "arms": arms,
    }
    write_once(DRAW, json.dumps(out, indent=1) + "\n")
    print({s: v["eligible"] for s, v in arms.items()}, status)


if __name__ == "__main__":
    step = sys.argv[1] if len(sys.argv) > 1 else ""
    if step == "pool":
        pool()
    elif step == "round" and len(sys.argv) == 3:
        lock_round(sys.argv[2])
    elif step == "draw":
        draw()
    else:
        raise SystemExit("usage: part_b_draw.py pool | round <lock-commit> | draw")
