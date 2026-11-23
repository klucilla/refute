"""v0.5.8 stage 1 (exploratory): the output stability of the v0.5 battery, measured by a
TOI-seeded rerun paired with each TOI's v0.5.6 record (docs/plans/v0.5.8-plan.md; the maintainer's
decision of 2026-11-23, received at 13:27 local, #218, comment 7107165120).

**Another question, the same mode.**
- This reuses v0.5.7's TOI-seeded mode for stability, not equivalence. v0.5.7's stop stands.
- ``docs/validation/v0.5.7/seeded_run.py`` is **not edited**. This script imports it and, in its own
  processes only, points its paths, caps and helpers to v0.5.8.
- The old runner's pilot guard (``rest``) is not used.
- The shifted second seed is **not run**: Codex's design round found that it changes the mode
  (``docs/plans/v0.5.8-consensus/design-round-1-answer.md``, item 3).

**What runs:**
- For each TOI of the set, ``seeded_run.run_one`` runs unchanged: the adapter's download, the
  provenance check against the v0.5.6 record (other sectors are refused), the TOI-seeded candidate,
  the unchanged battery and the ephemeris record.
- Each TOI runs with the test plan its v0.5.6 run used.
- Nothing in ``src/`` changes, and no rule, threshold, refusal or aggregation changes.

**The set** (``stage1-set.json``, written once by ``draw``, committed before any result):
- the 107 matched and decided v0.5.6 records;
- 60 of the 257 matched INCONCLUSIVE records: the keys sorted by TIC, then
  ``random.Random(int(sha256(SEED_TEXT), 16)).sample(keys, 60)``.

**Records** (``.cache/v058/run/records``): ``seeded_run``'s record, plus ``phase``, ``stage`` and
``seed_mode``.
- Every record carries a machine ``started_utc``, ``mode: exploratory``, the limits label,
  ``coverage_state`` and provenance.
- When a run ends before its provenance check, the record gets ``overall: unknown`` with the reason.

**Caps and guards** (the decision, item 3; Codex's design round, blocking items 1, 4 and 5):
- **Disk:** measured under ``.cache/v058``, at admission and by the monitor. Admission is held at
  18 GB, and a sample over 20 GB stops admission.
- **Downloads:** a target is admitted only if the bytes already downloaded in this phase, plus a
  reservation for every target in flight, plus its own stay within 65 GB. A reservation is 1.25
  times the bytes the target's v0.5.6 record downloaded (at least 1 GB). This leaves 5 GB of the
  70 GB cap as a margin for files larger than their reservation.
- **CPU:** 8 CPU-h for the whole phase, charged as in ``seeded_run``: the larger of the records' and
  the workers' measured CPU, plus the controller's, plus an upper bound for any unclean end. No
  target is admitted if its estimate would pass the cap; a target already running finishes.
- **Deadline:** 2026-12-07 23:59 local. No target is admitted after it.
- **The lock** is held by the operating system (``msvcrt.locking`` on an open file), so it is
  released when the process ends.
- **Atomic writes** use a temporary name unique to the process and thread, so that the monitor and
  the controller never share it.
- **Pixel files** are deleted per target, with a manifest.
- **Light curves** are deleted at the end by ``clean``. It deletes the files the adapter's manifests
  list, and also any light curve of a set TIC left without a manifest, each by literal path with
  its SHA-256 logged.

Workers and downloads follow the business-hours limits of ``seeded_run``. Pinned to CPUs 8 to 31
and BelowNormal (``pinrun``). Resumable: a recorded target never runs again.

Usage (from the project root, pinned): ``stability_run.py draw|run|clean``.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import random
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
V057 = ROOT / "docs/validation/v0.5.7"
if str(V057) not in sys.path:
    sys.path.insert(0, str(V057))
import seeded_run as sr  # noqa: E402 - the v0.5.7 runner, imported, never edited

WORK = ROOT / ".cache/v058"
SET_FILE = HERE / "stage1-set.json"
LEDGER = HERE / "stability-ledger.json"
EXTRA_LC_LOG = WORK / "run" / "lc-deletions-without-manifest.json"
SEED_TEXT = b"refute v0.5.8 stage 1: 60 of the 257 matched INCONCLUSIVE records"
CAP_CPU_HOURS = 8.0
CAP_DOWNLOAD_BYTES = 70e9
ADMIT_DOWNLOAD_BYTES = 65e9
DOWNLOAD_RESERVE_FACTOR = 1.25
MIN_DOWNLOAD_RESERVE = 1e9
DEADLINE = dt.datetime(2026, 12, 7, 23, 59)

_ORIGINAL_DISK_BYTES = sr.disk_bytes
_ORIGINAL_PICK = sr._pick


def matched(rec: dict) -> bool:
    return rec.get("status") == "OK" and bool((rec.get("identity") or {}).get("matched"))


def build_set() -> dict:
    """The stage-1 set from the committed v0.5.6 records (pure: the tests call it)."""
    search = sr.search_records()
    decided = sorted(k for k, r in search.items()
                     if matched(r)
                     and r["outcome"] in ("SURVIVED", "WEAKENED", "REFUTED"))  # fmt: skip
    pool = sorted((k for k, r in search.items() if matched(r) and r["outcome"] == "INCONCLUSIVE"),
                  key=lambda k: int(k.split("-")[1]))  # fmt: skip
    seed = int(hashlib.sha256(SEED_TEXT).hexdigest(), 16)
    drawn = random.Random(seed).sample(pool, 60)
    return {
        "schema": "refute-v058-stage1-set-1",
        "mode": "exploratory",
        "limits_label": sr.LABEL,
        "rule": "the 107 matched and decided v0.5.6 records; 60 of the matched INCONCLUSIVE, "
        "the keys sorted by TIC, then random.Random(int(sha256(SEED_TEXT), 16)).sample(keys, 60)",
        "seed_text": SEED_TEXT.decode(),
        "bundles_sha256": {
            p: hashlib.sha256(v.read_bytes()).hexdigest() for p, v in sr.BUNDLES.items()
        },  # fmt: skip
        "decided": decided,
        "inconclusive_pool": len(pool),
        "inconclusive_drawn": drawn,
    }


def set_keys() -> list[str]:
    doc = json.loads(SET_FILE.read_text("utf-8"))
    return [*doc["decided"], *doc["inconclusive_drawn"]]


# --- v0.5.8's own helpers, bound into the imported runner (this process only) -----------------


def disk_bytes(root: Path | None = None) -> int:
    """The disk under ``.cache/v058`` by default (the old default was bound to ``.cache/v057``)."""
    return _ORIGINAL_DISK_BYTES(WORK if root is None else root)


def fingerprints() -> dict[str, str]:
    files = {
        "stability_run": Path(__file__),
        "stability_report": HERE / "stability_report.py",
        "stage1_set": SET_FILE,
        "seeded_run": V057 / "seeded_run.py",
        **{f"plan_{p}": v for p, v in sr.PLANS.items()},
        **{f"draw_{p}": v for p, v in sr.DRAWS.items()},
        **{f"bundle_{p}": v for p, v in sr.BUNDLES.items()},
    }
    return {k: hashlib.sha256(v.read_bytes()).hexdigest() for k, v in files.items()}


def write_json(path: Path, obj: dict) -> str:
    """Atomic write with a temporary name unique to the process and the thread."""
    text = json.dumps(obj, indent=1, default=sr._plain)
    tmp = path.with_name(f"{path.name}.{os.getpid()}.{threading.get_ident()}.tmp")
    tmp.write_text(text, "utf-8", newline="\n")
    os.replace(tmp, path)
    if path.read_text("utf-8") != text:
        raise RuntimeError(f"{path.name} did not read back as written")
    return text


class OsLock:
    """An exclusive lock held by the operating system on an open file: released when the
    process ends, so a stale lock cannot be taken by two starters."""

    def __enter__(self):
        import msvcrt

        path = WORK / "run" / "run.lock"
        path.parent.mkdir(parents=True, exist_ok=True)
        self._fh = open(path, "a+b")  # noqa: SIM115 - held for the whole run
        try:
            self._fh.seek(0)
            msvcrt.locking(self._fh.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError as exc:
            self._fh.close()
            raise SystemExit("refused: the run lock is held by another process") from exc
        return self

    def __exit__(self, *exc):
        import msvcrt

        self._fh.seek(0)
        msvcrt.locking(self._fh.fileno(), msvcrt.LK_UNLCK, 1)
        self._fh.close()


def v056_downloads() -> dict[str, int]:
    """Each target's bytes downloaded in v0.5.6: its record's ``downloaded_bytes``, else
    ``bytes``."""
    out = {}
    for key, r in sr.search_records().items():
        out[key] = int(r.get("downloaded_bytes") or r.get("bytes") or 0)
    return out


_V056_DOWNLOADS: dict[str, int] = {}


def download_reserve(key: str) -> float:
    return max(MIN_DOWNLOAD_RESERVE, DOWNLOAD_RESERVE_FACTOR * _V056_DOWNLOADS.get(key, 0))


def downloaded_so_far() -> int:
    return sum(json.loads(p.read_text("utf-8")).get("downloaded_bytes", 0)
               for p in sorted(sr.RECORDS.glob("TIC-*.json")))  # fmt: skip


def pick(todo: list[dict], in_flight: dict, elapsed: float) -> int | None | str:
    """The imported runner's admission, with the download reservation added."""
    reserved = downloaded_so_far() + sum(download_reserve(v["key"]) for v in in_flight.values())
    fits = [t for t in todo if reserved + download_reserve(t["key"]) <= ADMIT_DOWNLOAD_BYTES]
    if not fits:
        if not in_flight:
            return (f"downloads: {reserved / 1e9:.1f} GB downloaded or reserved; no remaining "
                    f"target fits under {ADMIT_DOWNLOAD_BYTES / 1e9:.0f} GB")  # fmt: skip
        return None
    choice = _ORIGINAL_PICK(fits, in_flight, elapsed)
    if isinstance(choice, int):
        return todo.index(fits[choice])
    return choice


def point_runner() -> None:
    """Point the imported v0.5.7 runner's paths, caps and helpers to v0.5.8 (this process)."""
    sr.WORK = WORK
    sr.DATA = WORK / "data"
    sr.LIGHTKURVE = sr.DATA / "lightkurve"
    sr.RECORDS = WORK / "run" / "records"
    sr.TPF_LOGS = WORK / "run" / "tpf-deletions"
    sr.LC_LOG = WORK / "run" / "lc-deletions.json"
    sr.MARKER = WORK / "run" / "in-flight.json"
    sr.LEDGER = LEDGER
    sr.CAP_CPU_HOURS = CAP_CPU_HOURS
    sr.DEADLINE = DEADLINE
    sr.disk_bytes = disk_bytes
    sr.fingerprints = fingerprints
    sr._write_json = write_json
    sr.RunLock = OsLock
    sr._pick = pick
    _V056_DOWNLOADS.update(v056_downloads())


def stability_target(target: dict, test_plan: dict, hist: dict | None) -> dict:
    """In a worker: the v0.5.7 runner's ``run_one``, unchanged, with v0.5.8's data folder."""
    import seeded_run as w

    w.DATA = WORK / "data"
    w.LIGHTKURVE = w.DATA / "lightkurve"
    rec = w.run_one(target, test_plan, hist)
    if "provenance" not in rec:
        rec["provenance"] = {"overall": "unknown",
                             "reason": f"the run ended ({rec.get('status')}) before the "
                                       "provenance check"}  # fmt: skip
    rec.update({"phase": "v0.5.8", "stage": 1, "seed_mode": "toi-seeded"})
    return rec


def run() -> None:
    keys = set(set_keys())
    targets = [t for t in sr.targets() if t["key"] in keys]
    if len(targets) != len(keys):
        raise SystemExit("the set and the draws disagree")
    sr.run_one = stability_target  # the batch loop submits this wrapper (sr is not edited)
    with sr.RunLock():
        charged = sr.charge_interruption()
        if charged:
            print("interruption charged:", json.dumps(charged), flush=True)
        sr.sweep()
        while any(not (sr.RECORDS / f"{t['key']}.json").exists() for t in targets):
            stop = sr.run_batch(targets, "stage1")
            if stop:
                sr._terminal("stopped", stop)
                print("STOP:", stop, flush=True)
                raise SystemExit(2)
        sr._terminal("complete", "stage 1, TOI-seeded")
        print("all targets recorded", json.dumps(sr._totals()), flush=True)


def clean() -> None:
    """The light curves at the end: the manifest-listed ones (``seeded_run.clean``), then any
    light curve of a set TIC left without a manifest, each logged with its SHA-256."""
    with sr.RunLock():
        sr.clean()
        tics = {int(k.split("-")[1]) for k in set_keys()}
        entries, freed = [], 0
        for tic in sorted(tics):
            for path in sr._tic_files(tic, "_lc.fits"):
                digest = sr.sha256_path(path)
                freed += sr.delete_literal(path, tic, digest, "_lc.fits")
                entries.append({"path": path.relative_to(ROOT).as_posix(), "sha256": digest})
        write_json(EXTRA_LC_LOG, {"utc": sr.utc(), "bytes_deleted": freed, "files": entries})
        print(f"light curves without a manifest deleted: {len(entries)} files, {freed} bytes")


def main(step: str) -> None:
    if step == "draw":
        if SET_FILE.exists():
            raise SystemExit(f"{SET_FILE.name} exists; it is written once")
        doc = build_set()
        SET_FILE.write_text(json.dumps(doc, indent=1) + "\n", "utf-8", newline="\n")
        print(len(doc["decided"]), "decided;", len(doc["inconclusive_drawn"]), "drawn of",
              doc["inconclusive_pool"])  # fmt: skip
        return
    point_runner()
    sr.isolate_caches()
    if step == "run":
        run()
    elif step == "clean":
        clean()
    else:
        raise SystemExit("usage: stability_run.py draw|run|clean")


if __name__ == "__main__":
    main(sys.argv[1])
