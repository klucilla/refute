"""v0.5.6 part B (confirmatory): the pool, the drand round, the draw and its validation (docs/plans/
v0.5.6-plan-amendment-1.md; the maintainer's decisions of 2026-11-22, 13:00, items 3 and 5;
Codex's round ``partb`` 1 to 3; the decision of 2026-11-22, 14:30, item 2; #218).
``method_status: not_validated``. Limits label: 'WEAKENED; does not meet D1, D2, D4, T2a'.

Steps (each refuses to write over its output, except the pool, which is rewritten only before the
lock):

1. ``pool`` (only before the lock; it refuses once the lock exists): the two strata of the
   **confirmation half**, from the frame as committed (``part-a-frame.csv``) and the
   prior-exposure record as committed (``part-b-exposure.json``, the second version), each
   checked against the SHA-256 the claim records:
   - ``planet``: the planet arm (exactly one PSCompPars planet discovered by TESS within 1 %);
   - ``fp``: the open arm with the frame's ``tfopwg_disp_descriptive`` equal to ``FP``;
   - every TIC of ``exposed_tics`` is left out; FA, PC, APC, KP, CP and blank are not drawn.
   Written as the claim's targets attachment (``pool-targets.yaml``, ``refute-tess-targets-1``).
2. ``check`` (after the lock commit is pushed): the drand round is **fixed in the claim** before
   the lock (``definitions``: the network, the chain hash, the round and its time by the public
   formula genesis + period x (round - 1), chosen about 30 minutes after the lock commit;
   ``part_b_claim.py --drand-round auto``). The lock commit is the one commit that adds
   ``calibration/v0.5.6/claim.lock.json``; its time on GitHub is the creation time of its CI
   push run, read from GitHub (workflow ``ci.yml``, event ``push``, ``head_sha`` the commit, run
   attempt 1). If the round is not after that time, the lock is discarded without a draw and
   redone with a new number (recorded). Writes nothing.
3. ``draw`` (once the round is published): the lock must verify (``refute verify``: PASS), and
   the claim's round must be after the lock's time on GitHub, read again. That round and no other
   is fetched, and its BLS signature verified. Each stratum, sorted by TIC, is shuffled with
   ``random.Random(seed_s)``, where ``seed_s = int(sha256(randomness_hex + "|v0.5.6|part-b|" +
   stratum), 16)``. Each TIC in that order is checked from MAST **metadata only**, with part A's
   own listing (``part_a_frame.py``: author SPOC, exposure exactly 120 s, ``*lc.fits``, the TIC
   itself, sectors up to 107), for at least two predicted transits; the walk stops at
   ``PER_STRATUM`` eligible TICs. The listings are cached in a folder of this round only, and
   **every listing used is kept in the draw record**, so the eligibility can be recounted. No
   light curve is read.
4. ``validate_draw`` (offline; called by the draw before writing, by the runner and by the
   evaluation, which also require the draw to be ``published``: committed, equal to ``HEAD`` and on
   ``origin/main``):
   - the draw names this lock, and the lock commit (from the repository) holds this lock's bytes;
   - the draw's round and the beacon's are the claim's round, and the beacon's BLS signature
     verifies (``refute.drand.verify_beacon``);
   - the claim's round is after the lock's time on GitHub, **read again from GitHub** (network),
     so no file of the draw is taken as evidence of that time;
   - the shuffle is replayed from the beacon's randomness and the pool, and the trail is the
     prefix of that order, each entry at its position with the frame's TOI;
   - every kept listing is this TIC's, within the filters (120-s cadence, sectors up to 107, this
     TIC's ``*lc.fits``), matches its hash and the entry's sectors and products, and recounts to
     the entry's reason;
   - every trail entry has exactly the trail's keys, and the chosen entries are **rebuilt**: the
     trail's own keys, and every other field (ephemerides included) from the frozen frame; they
     must be equal;
   - the TICs are unique, in their stratum, unexposed, and outside part A's draw (by TIC and by
     every listed product); the status follows from the counts.

The draw's status is ``complete`` (150 per stratum), ``short`` (at least ``MIN_PER_STRATUM``, the
pool exhausted) or ``incomplete`` (fewer: the claim's evaluation ends INCONCLUSIVE).

Usage (from the project root): ``.venv/Scripts/python.exe -B calibration/v0.5.6/part_b_draw.py
pool|check|draw``.
"""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import io
import json
import math
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
EXPOSURE = VALIDATION / "part-b-exposure.json"
PART_A_DRAW = VALIDATION / "part-a-draw.json"
FRAME_CODE = VALIDATION / "part_a_frame.py"
CLAIM = HERE / "claim.yaml"
LOCK = HERE / "claim.lock.json"
POOL = HERE / "pool-targets.yaml"
DRAW = HERE / "part-b-draw.json"
MAST_ROOT = ROOT / ".cache/v056/partb"
LABEL = "WEAKENED; does not meet D1, D2, D4, T2a"
STRATA = ("planet", "fp")
PER_STRATUM = 150
MIN_PER_STRATUM = 120
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


# --- the strata and the order (pure: the tests call them) --------------------------------------


def stratum_of(row: dict) -> str | None:
    """``planet``, ``fp`` or None (not drawn), for a frame row."""
    if row["half"] != "confirmation":
        return None
    if row["arm"] == "planet":
        return "planet"
    if row["arm"] == "open" and row["tfopwg_disp_descriptive"] == "FP":
        return "fp"
    return None


def strata(rows: list[dict], exposed: set[int]) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {s: [] for s in STRATA}
    for r in rows:
        s = stratum_of(r)
        if s is not None and int(r["tic_id"]) not in exposed:
            out[s].append(r)
    for s in STRATA:
        out[s].sort(key=lambda r: int(r["tic_id"]))
    return out


def stratum_seed(randomness_hex: str, stratum: str) -> int:
    return int(sha256((randomness_hex + SEED_TAG + stratum).encode()), 16)


def order(rows: list[dict], randomness_hex: str, stratum: str) -> list[dict]:
    from refute.drand import shuffled

    return shuffled(rows, stratum_seed(randomness_hex, stratum), key=lambda r: int(r["tic_id"]))


TRAIL_KEYS = ("position", "tic_id", "toi", "reason", "predicted_transits", "sectors",
              "products", "listing", "listing_sha256")  # fmt: skip


def chosen_entry(paf, t: dict, row: dict) -> dict:
    """A chosen entry: the trail's own keys (never its listing), then every other frame field
    from the frozen frame row, so no trail field can stand in for an ephemeris."""
    entry = {k: t[k] for k in TRAIL_KEYS if k != "listing"}
    return {**entry, **{f: row[f] for f in paf.FRAME_FIELDS if f not in ("tic_id", "toi")}}


def reason_for(paf, row: dict, windows: list[dict]) -> tuple[str, int]:
    n = paf.predicted(float(row["period_days"]), float(row["epoch_bjd"]), windows)
    if not windows:
        return f"no SPOC 120-s light curve up to sector {paf.MAX_SECTOR}", n
    if n < paf.MIN_PREDICTED:
        return f"{n} predicted transit(s) inside the sectors' time ranges", n
    return "eligible", n


# --- inputs ------------------------------------------------------------------------------------


def frozen_inputs() -> tuple[list[dict], set[int], dict, dict]:
    """The frame rows, the exposed TICs, the frame record and part A's draw, each checked."""
    inputs = claim_inputs()
    record = json.loads(checked(FRAME_RECORD, inputs["frame_record"]))
    data = checked(FRAME_FILE, inputs["frame"])
    if sha256(data) != record["frame_sha256"]:
        raise SystemExit("the frame does not match part-a-frame.json")
    checked(FRAME_CODE, inputs["frame_code"])
    exposure = json.loads(checked(EXPOSURE, inputs["exposure"]))
    part_a = json.loads(checked(PART_A_DRAW, inputs["part_a_draw"]))
    rows = list(csv.DictReader(io.StringIO(data.decode("utf-8"))))
    return rows, set(exposure["exposed_tics"]), record, part_a


def part_a_sets(part_a: dict) -> tuple[set[int], set[str]]:
    tics = {int(c["tic_id"]) for a in part_a["arms"].values() for c in a["trail"]}
    products = {p for a in part_a["arms"].values() for c in a["trail"] for p in c["products"]}
    return tics, products


# --- 1. the pool -------------------------------------------------------------------------------


def pool() -> None:
    if LOCK.exists():
        raise SystemExit("the claim is locked; the pool is never written again")
    rows, exposed, record, _ = frozen_inputs()
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
            "exposure_record": EXPOSURE.name,
            "exposed_excluded": len(exposed),
            "counts": {s: len(groups[s]) for s in STRATA},
        },
        "targets": targets,
    }
    tmp = POOL.with_name(POOL.name + ".tmp")
    text = yaml.safe_dump(doc, sort_keys=False, allow_unicode=True, width=100)
    tmp.write_text(text, "utf-8", newline="\n")
    os.replace(tmp, POOL)
    print(doc["selection"]["counts"])


# --- 2. the round (fixed in the claim, before the lock) -----------------------------------------


def _git(*args: str) -> bytes:
    return subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, check=True).stdout


def claim_round() -> dict:
    """The drand round the locked claim fixes (``definitions``: ``drand_network``,
    ``drand_chain_hash``, ``drand_round``, ``drand_round_time_utc``), checked against
    ``refute.drand``'s chain hash and the public formula genesis + period x (round - 1)."""
    from refute.drand import DRAND_CHAIN_HASH, round_time

    d = yaml.safe_load(CLAIM.read_text("utf-8"))["definitions"]
    try:
        number = int(d["drand_round"])
    except (KeyError, ValueError) as exc:
        raise SystemExit("the claim fixes no drand round") from exc
    if d.get("drand_chain_hash") != DRAND_CHAIN_HASH:
        raise SystemExit("the claim's chain hash is not refute.drand's")
    if d.get("drand_round_time_utc") != round_time(number).isoformat():
        raise SystemExit("the claim's round time is not genesis + period x (round - 1)")
    return {
        "network": d.get("drand_network"),
        "chain_hash": d["drand_chain_hash"],
        "round": number,
        "round_time_utc": d["drand_round_time_utc"],
    }


def lock_commit() -> str:
    """The one commit that added the lock file, from the local repository."""
    found = _git("log", "--diff-filter=A", "--format=%H", "--", LOCK_PATH_IN_REPO).decode().split()
    if len(found) != 1:
        raise SystemExit(f"{len(found)} commits add {LOCK_PATH_IN_REPO}; the maintainer decides")
    return found[0]


def github_time(commit: str) -> dict:
    """When the lock commit reached GitHub, read from GitHub (network), never from a file of the
    draw: the creation time of the commit's CI push run (workflow ``ci.yml``, event ``push``,
    ``head_sha`` the commit, run attempt 1). The commit must be on ``origin/main`` and hold the
    lock's bytes. No such run, or more than one, stops (the maintainer decides)."""
    from refute.packs.tess.discover import pilot

    _git("merge-base", "--is-ancestor", commit, "origin/main")
    if sha256(_git("show", f"{commit}:{LOCK_PATH_IN_REPO}")) != sha256(LOCK.read_bytes()):
        raise SystemExit("the lock on disk differs from the lock in its commit")
    answers: list[bytes] = []

    def fetch(url: str) -> bytes:
        data = pilot.download(url)
        answers.append(data)
        return data

    created = pilot.push_run_created_at(commit, fetch=fetch)
    runs = json.loads(answers[-1])["workflow_runs"]
    run = next(r for r in runs if r.get("head_sha") == commit and r.get("run_attempt") == 1)
    keys = ("id", "html_url", "event", "head_sha", "run_attempt", "created_at")
    return {
        "lock_commit": commit,
        "github_time_utc": created,
        "ci_push_run": {k: run.get(k) for k in keys},
        "github_answer_sha256": sha256(answers[-1]),
    }


def round_is_after(number: int, github_time_utc: str) -> bool:
    """True when round ``number`` is published strictly after ``github_time_utc``."""
    from datetime import UTC, datetime

    from refute.drand import round_time

    when = datetime.strptime(github_time_utc, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
    return round_time(number) > when


def check() -> None:
    """After the lock commit is pushed: is the claim's round after the lock's time on GitHub? If
    not, the lock is discarded without a draw and redone with a new number (the decision of
    2026-11-22, 14:30, item 2). Writes nothing."""
    rnd, gh = claim_round(), github_time(lock_commit())
    ok = round_is_after(rnd["round"], gh["github_time_utc"])
    print(json.dumps({**rnd, **gh, "round_after_github_time": ok}, indent=1))
    if not ok:
        raise SystemExit("the round had passed when the lock reached GitHub: discard the lock")


# --- 3. the draw -------------------------------------------------------------------------------


def _listing(paf, cache: Path, tics: list[int]) -> None:
    todo = [t for t in tics if not (cache / f"{t}.json").exists()]
    if not todo:
        return
    for tic, items in paf._listing_with_retries(todo).items():
        payload = {"tic_id": tic, "queried_utc": utc(), "products": items}
        tmp = cache / f"{tic}.json.tmp"
        tmp.write_bytes(json.dumps(payload, indent=1).encode())
        os.replace(tmp, cache / f"{tic}.json")


def walk(paf, cache: Path, ordered: list[dict]) -> list[dict]:
    """The trail: each checked TIC in order with its kept listing, until PER_STRATUM eligible."""
    trail: list[dict] = []
    eligible = 0
    k = 0
    while eligible < PER_STRATUM and k < len(ordered):
        batch = ordered[k : k + BATCH]
        _listing(paf, cache, [int(r["tic_id"]) for r in batch])
        for position, r in enumerate(batch, start=k):
            if eligible >= PER_STRATUM:
                break
            tic = int(r["tic_id"])
            raw = (cache / f"{tic}.json").read_bytes()
            listing = json.loads(raw)
            reason, n = reason_for(paf, r, listing["products"])
            trail.append(
                {
                    "position": position,
                    "tic_id": tic,
                    "toi": r["toi"],
                    "reason": reason,
                    "predicted_transits": n,
                    "sectors": sorted({w["sector"] for w in listing["products"]}),
                    "products": [w["productFilename"] for w in listing["products"]],
                    "listing": listing,
                    "listing_sha256": sha256(raw),
                }
            )
            eligible += reason == "eligible"
        k += len(batch)
    return trail


def draw() -> None:
    from refute.core.lock import verify_claim
    from refute.drand import drand_seed, interpreter_record

    if DRAW.exists():
        raise SystemExit("the draw is recorded; never written over")
    result = verify_claim(CLAIM)
    if result.status.value != "PASS":
        raise SystemExit(f"the lock does not verify: {result.status.value} {result.messages}")
    rnd = claim_round()
    gh = github_time(lock_commit())
    if not round_is_after(rnd["round"], gh["github_time_utc"]):
        raise SystemExit(
            "the claim's round had passed when the lock reached GitHub: the lock is discarded "
            "without a draw and redone with a new number (recorded)"
        )
    seed, beacon = drand_seed(rnd["round"])
    if int(beacon["randomness"], 16) != seed:
        raise SystemExit("the beacon's randomness does not match its seed")
    rows, exposed, record, _ = frozen_inputs()
    groups = strata(rows, exposed)
    paf = frame_module()
    cache = MAST_ROOT / f"mast-round-{int(rnd['round'])}"
    cache.mkdir(parents=True, exist_ok=True)
    arms = {}
    for s in STRATA:
        ordered = order(groups[s], beacon["randomness"], s)
        trail = walk(paf, cache, ordered)
        by_tic = {int(r["tic_id"]): r for r in ordered}
        chosen = [
            chosen_entry(paf, t, by_tic[t["tic_id"]]) for t in trail if t["reason"] == "eligible"
        ]
        arms[s] = {"pool": len(ordered), "checked": len(trail), "eligible": len(chosen),
                   "chosen": [{k: v for k, v in c.items() if k != "listing"} for c in chosen],
                   "trail": trail}  # fmt: skip
    counts = [arms[s]["eligible"] for s in STRATA]
    status = (
        "complete"
        if all(n == PER_STRATUM for n in counts)
        else "incomplete"
        if any(n < MIN_PER_STRATUM for n in counts)
        else "short"
    )
    out = {
        "schema": "refute-v056-part-b-draw-2",
        "mode": "confirmatory",
        "limits_label": LABEL,
        "method_status": "not_validated",
        "status": status,
        "lock_sha256": sha256(LOCK.read_bytes()),
        "round": {**rnd, **gh},
        "beacon": beacon,
        "interpreter": interpreter_record(),
        "frame_sha256": record["frame_sha256"],
        "code_sha256": sha256(Path(__file__).read_bytes()),
        "seed_rule": "int(sha256(randomness_hex + '" + SEED_TAG + "' + stratum), 16); the "
        "stratum sorted by TIC, then random.Random(seed).shuffle",
        "listing": "MAST metadata (astroquery Observations), part A's listing and filters; "
        "every listing used is kept in the trail",
        "written_utc": utc(),
        "arms": arms,
    }
    problems = validate_draw(out)
    if problems:
        raise SystemExit(f"the draw failed its checks: {problems}")
    write_once(DRAW, json.dumps(out, indent=1) + "\n")
    print({s: v["eligible"] for s, v in arms.items()}, status)


# --- 4. validation (offline) -------------------------------------------------------------------


def published(path: Path) -> list[str]:
    """The problems that keep ``path`` from counting as published: it must be tracked, equal to
    ``HEAD``, and its last commit must be on ``origin/main``."""
    rel = path.relative_to(ROOT).as_posix()

    def git(*args: str) -> subprocess.CompletedProcess:
        return subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True)

    if git("ls-files", "--error-unmatch", rel).returncode != 0:
        return [f"{rel} is not committed"]
    if git("diff", "--quiet", "HEAD", "--", rel).returncode != 0:
        return [f"{rel} differs from HEAD"]
    last = git("log", "-1", "--format=%H", "--", rel).stdout.decode().strip()
    if not last or git("merge-base", "--is-ancestor", last, "origin/main").returncode != 0:
        return [f"{rel} is not on origin/main"]
    return []


def _round_problems(
    draw_doc: dict, rnd: dict, lock_sha: str, check_commit: bool, check_ci: bool
) -> list[str]:
    """The draw's round against the claim's; with ``check_commit``, the lock commit (from the
    repository) holds this lock; with ``check_ci``, the round is after the lock's time on GitHub,
    read again from GitHub (network), never from the draw."""
    problems = []
    if (draw_doc.get("round") or {}).get("round") != rnd["round"]:
        problems.append("the draw's round is not the claim's")
    if check_commit:
        try:
            commit = lock_commit()
            held = sha256(_git("show", f"{commit}:{LOCK_PATH_IN_REPO}"))
        except (SystemExit, subprocess.CalledProcessError) as exc:
            return [*problems, f"the lock commit cannot be read: {exc}"]
        if held != lock_sha:
            problems.append("the lock commit does not hold this lock")
    if check_ci:
        try:
            gh = github_time(lock_commit())
        except (SystemExit, Exception) as exc:  # noqa: BLE001 - any failure is a problem
            return [*problems, f"the lock's time on GitHub cannot be read: {exc}"]
        if not round_is_after(rnd["round"], gh["github_time_utc"]):
            problems.append("the claim's round is not after the lock's time on GitHub")
    return problems


def _beacon_problems(draw_doc: dict, number: int, verify_signature: bool) -> list[str]:
    from refute.drand import verify_beacon

    beacon = draw_doc.get("beacon") or {}
    if beacon.get("round") != number:
        return ["the beacon is not the claim's round"]
    if not verify_signature:
        ok = sha256(bytes.fromhex(beacon.get("signature", ""))) == beacon.get("randomness")
        return [] if ok else ["the beacon's randomness is not sha256(signature)"]
    try:
        seed = verify_beacon(int(number), beacon)
    except Exception as exc:  # noqa: BLE001 - any failure is a problem
        return [f"the beacon does not verify: {exc}"]
    return [] if int(beacon["randomness"], 16) == seed else ["the beacon's seed differs"]


def _listing_problems(paf, t: dict, tic: int) -> list[str]:
    listing = t["listing"]
    windows = listing.get("products", [])
    problems = []
    if listing.get("tic_id") != tic:
        problems.append("its listing names another TIC")
    for w in windows:
        name = str(w.get("productFilename", ""))
        try:
            exptime = float(w.get("exptime"))
            sector = w.get("sector")
            t_min, t_max = float(w.get("t_min_mjd")), float(w.get("t_max_mjd"))
        except (TypeError, ValueError):
            problems.append("a listed product has an unreadable cadence or time range")
            continue
        if not (math.isfinite(exptime) and abs(exptime - paf.EXPTIME) <= 1e-6):
            problems.append("a listed product is not a 120-s cadence")
        if not (isinstance(sector, int) and 1 <= sector <= paf.MAX_SECTOR):
            problems.append(f"a listed sector is not an integer from 1 to {paf.MAX_SECTOR}")
        if not (math.isfinite(t_min) and math.isfinite(t_max) and t_min < t_max):
            problems.append("a listed product has an invalid time range")
        if not name.endswith("lc.fits") or f"-{tic:016d}-" not in name:
            problems.append("a listed product is not this TIC's light curve")
    if t["sectors"] != sorted({w["sector"] for w in windows}):
        problems.append("its sectors are not the listing's")
    if t["products"] != [w["productFilename"] for w in windows]:
        problems.append("its products are not the listing's")
    return problems


def validate_draw(
    draw_doc: dict,
    lock_bytes: bytes | None = None,
    *,
    claim_rnd: dict | None = None,
    verify_signature: bool = True,
    check_commit: bool = True,
    check_ci: bool = True,
) -> list[str]:
    """Every check the runner and the evaluation rely on, replayed offline. Returns the problems
    (empty when the draw is valid). The draw, the runner and the evaluation call it with the
    defaults: the round read from the locked claim, the beacon's BLS signature verified, the lock
    commit read from the repository, and the lock's time read from GitHub (network). The offline
    tests pass a synthetic round and turn the three checks off for a synthetic beacon, commit and
    run, and test the first two apart."""
    problems: list[str] = []
    lock_bytes = LOCK.read_bytes() if lock_bytes is None else lock_bytes
    lock_sha = sha256(lock_bytes)
    if draw_doc.get("schema") != "refute-v056-part-b-draw-2":
        problems.append("unknown schema")
    if draw_doc.get("lock_sha256") != lock_sha:
        problems.append("the draw does not name this lock")
    rnd = claim_round() if claim_rnd is None else claim_rnd
    problems += _round_problems(draw_doc, rnd, lock_sha, check_commit, check_ci)
    problems += _beacon_problems(draw_doc, rnd["round"], verify_signature)
    randomness = (draw_doc.get("beacon") or {}).get("randomness", "")
    rows, exposed, _, part_a = frozen_inputs()
    groups = strata(rows, exposed)
    a_tics, a_products = part_a_sets(part_a)
    paf = frame_module()
    seen: set[int] = set()
    counts = {}
    for s in STRATA:
        arm = draw_doc.get("arms", {}).get(s)
        if arm is None:
            problems.append(f"{s}: missing")
            continue
        ordered = order(groups[s], randomness, s)
        trail = arm["trail"]
        if [t["tic_id"] for t in trail] != [int(r["tic_id"]) for r in ordered[: len(trail)]]:
            problems.append(f"{s}: the trail is not the prefix of the replayed order")
            continue
        by_tic = {int(r["tic_id"]): r for r in ordered}
        expected_chosen = []
        for position, t in enumerate(trail):
            tic = t["tic_id"]
            row = by_tic[tic]
            where = f"{s}: TIC {tic}"
            if set(t) != set(TRAIL_KEYS):
                problems.append(f"{where}: its keys are not the trail's")
                continue
            if t.get("position") != position or t.get("toi") != row["toi"]:
                problems.append(f"{where}: its position or TOI is not the frame's")
            if sha256(json.dumps(t["listing"], indent=1).encode()) != t["listing_sha256"]:
                problems.append(f"{where}: its listing does not match its hash")
            bad_listing = _listing_problems(paf, t, tic)
            if bad_listing:  # never recounted from a listing outside the filters
                problems += [f"{where}: {p}" for p in bad_listing]
                continue
            reason, n = reason_for(paf, row, t["listing"]["products"])
            if (reason, n) != (t["reason"], t["predicted_transits"]):
                problems.append(f"{where}: its reason does not recount")
            if reason == "eligible":
                expected_chosen.append(chosen_entry(paf, t, row))
        n_eligible = len(expected_chosen)
        if n_eligible > PER_STRATUM:
            problems.append(f"{s}: more than {PER_STRATUM} eligible in the trail")
        if n_eligible < PER_STRATUM and len(trail) != len(ordered):
            problems.append(f"{s}: the walk stopped before {PER_STRATUM} with the pool left")
        if arm.get("chosen") != expected_chosen:
            problems.append(f"{s}: the chosen entries are not rebuilt from the frame and trail")
        chosen = [c["tic_id"] for c in expected_chosen]
        if set(chosen) & seen or len(set(chosen)) != len(chosen):
            problems.append(f"{s}: a TIC drawn twice")
        seen |= set(chosen)
        if set(chosen) & exposed:
            problems.append(f"{s}: an exposed TIC")
        if set(chosen) & a_tics:
            problems.append(f"{s}: a TIC of part A")
        if {p for t in trail for p in t["products"]} & a_products:
            problems.append(f"{s}: a product of part A")
        if any(stratum_of(by_tic[c]) != s for c in chosen):
            problems.append(f"{s}: a TIC outside the stratum")
        counts[s] = len(chosen)
    if len(counts) == len(STRATA):
        expected = (
            "complete"
            if all(n == PER_STRATUM for n in counts.values())
            else "incomplete"
            if any(n < MIN_PER_STRATUM for n in counts.values())
            else "short"
        )
        if draw_doc.get("status") != expected:
            problems.append(f"the status is {draw_doc.get('status')}, the counts give {expected}")
    return problems


if __name__ == "__main__":
    step = sys.argv[1] if len(sys.argv) > 1 else ""
    if step == "pool":
        pool()
    elif step == "check":
        check()
    elif step == "draw":
        draw()
    else:
        raise SystemExit("usage: part_b_draw.py pool | check | draw")
