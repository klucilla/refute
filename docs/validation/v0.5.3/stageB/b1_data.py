"""v0.5.3 stage B, B1: the light-curve files of the C2 hosts B1 reads (#217;
``docs/plans/v0.5.3-stageB1-design.md``, sections 3 and 4). ``method_status: not_validated``.

B1's own cache, ``.cache/v053/stageB/t2a-cache``. Each file of a host's sealed v0.4 dossier
manifest (``c2.references``, refused unless the sealed SHA-256 hold) is taken, in this order:

- **from v0.5.2's checked cache** (``.cache/v052/s2/t2a-cache``), as a hard link, when it is there
  with the sealed SHA-256;
- **otherwise downloaded** by its recorded URL, under the transient rule (5 attempts, 120 s;
  v0.5.2's ``_download``), after the disk quota is checked against its exact sealed size.

Every file must end with its sealed SHA-256. A host with another file's bytes is "changed", and one
with a failed file is "failed"; neither is used. The report records each file's URL, size,
SHA-256, retrieval time and origin (link or download). The adapter's manifests are written as
v0.5.2's ``manifests`` writes them.

Usage: ``fetch <name>`` with ``name`` in ``e4-null`` (the 13 C2 hosts that passed the v0.4 gate,
outside T2a's population) or ``t2a`` (T2a's 84 hosts).
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import b1_forecast as bf  # noqa: E402,I001  (imports ledger_b and v0.5.2's helpers)
from b1_forecast import ft, ledger_b  # noqa: E402

CACHE = ledger_b.ROOT / ".cache/v053/stageB/t2a-cache"
METADATA_BYTES = 1024**2  # the bound reserved per host for its adapter manifest


def c2_records() -> list[dict]:
    return [json.loads(x) for x in ft.C2_RECORDS.read_text("utf-8").splitlines() if x.strip()]


def e4_hosts() -> list[str]:
    """The C2 hosts whose original curve passed the v0.4 gate (status OK): outside T2a's
    population, whose denominator excludes them (``ft.population``)."""
    own = {
        r["target_key"]
        for r in c2_records()
        if r["kind"] == "original" and r.get("status") == "OK" and r["chain"]["v04"]["gate_passed"]
    }
    t2a = {r["key"] for r in ft.population()}
    if own & t2a:
        raise SystemExit("a gate-passing host is in T2a's population: refused")
    return sorted(own)


def t2a_hosts() -> list[str]:
    return sorted({r["key"] for r in ft.population()})


def recorded_sizes() -> dict[str, int]:
    """The files' sizes as v0.5's C2 fetch recorded them (``c2-fetch.json``), by name: the
    bound of each download (the dossier manifests carry no size)."""
    files = json.loads(ft.C2_FETCH.read_text("utf-8"))["files"]
    return {f["name"]: int(f["bytes"]) for fs in files.values() for f in fs}


def bounded_download(url: str, dest: Path, size: int) -> str | None:
    """One file, streamed and refused past its recorded size; the transient rule (5 attempts,
    120 s, v0.5.2's constants); atomic. Returns an error or None."""
    import urllib.request

    error = None
    for attempt in range(ft.ATTEMPTS):
        part = dest.with_suffix(dest.suffix + ".part")
        try:
            got = 0
            with urllib.request.urlopen(url, timeout=300) as response, part.open("wb") as fh:  # noqa: S310
                while chunk := response.read(1 << 20):
                    got += len(chunk)
                    if got > size:
                        raise ValueError(f"more than the recorded {size} bytes")
                    fh.write(chunk)
            part.replace(dest)
            return None
        except Exception as exc:  # noqa: BLE001 - transient: retried, then recorded
            error = f"{type(exc).__name__}: {exc}"
            if part.exists():
                part.unlink()
            if attempt + 1 < ft.ATTEMPTS:
                time.sleep(ft.WAIT_SECONDS)
    return error


def fetch(name: str) -> None:
    from refute.core.hashing import sha256_file
    from refute.packs.tess.calib05 import c2
    from refute.packs.tess.discover.claim import TESS_EB_CACHE_PATH
    from refute.packs.tess.discover.pilot import TESS_EB_STATIC, static_tess_eb

    hosts = {"e4-null": e4_hosts, "t2a": t2a_hosts}[name]()
    dossiers, _ = c2.references(ledger_b.ROOT)
    sizes = recorded_sizes()
    # the whole fetch reserved before any write (Codex's review of B1.3, round 2): the data files
    # not yet present by their recorded sizes, the static TESS-EB catalog by its bytes, and a
    # bound of METADATA_BYTES per host for its adapter manifest
    eb = CACHE / TESS_EB_CACHE_PATH
    eb_bytes = (
        b""
        if eb.exists()
        else static_tess_eb(ledger_b.ROOT / TESS_EB_STATIC["path"], TESS_EB_STATIC)
    )
    need = len(eb_bytes) + METADATA_BYTES * len(hosts) + sum(
        sizes.get(f["name"], 0)
        for key in hosts
        for f in dossiers[key]["manifest"]["files"]
        if not (CACHE / "files" / f["name"]).exists()
    )  # fmt: skip
    if bf.disk_used() - bf._baseline() + need > bf.DISK_QUOTA:
        raise SystemExit("the disk quota of 5 GB would be passed by this fetch: a STOP")
    # every file already present in B1's cache, and every v0.5.2 file a link would take, must
    # have its sealed SHA-256 and recorded size before any write; a mismatch is a STOP, with no
    # automatic replacement (Codex's review of B1.3, round 3)
    for key in hosts:
        for f in dossiers[key]["manifest"]["files"]:
            for path in (CACHE / "files" / f["name"], ft.CACHE / "files" / f["name"]):
                if path.exists() and (
                    path.stat().st_size != sizes.get(f["name"]) or sha256_file(path) != f["sha256"]
                ):
                    raise SystemExit(f"{path.name}: present with other bytes: a STOP")
    if eb_bytes:
        eb.parent.mkdir(parents=True, exist_ok=True)
        eb.write_bytes(eb_bytes)
    folder = CACHE / "files"
    folder.mkdir(parents=True, exist_ok=True)
    old_folder = ft.CACHE / "files"
    report: dict = {"source": "the sealed v0.4 stage-1 dossiers' data manifests", "hosts": {},
                    "changed": {}, "failed": {}}  # fmt: skip
    for key in hosts:
        manifest = json.loads(json.dumps(dossiers[key]["manifest"]))
        records, problems = [], []
        for f in manifest["files"]:
            dest = folder / f["name"]
            origin = "present"
            if not dest.exists():
                size = sizes.get(f["name"])
                if size is None:
                    problems.append(f"{f['name']}: no recorded size")
                    records.append({"name": f["name"], "url": f["url"], "error": "no size"})
                    continue
                # the quota before the write, from the exact recorded size; a hard link counts
                # its size too (disk_used counts it), conservatively
                if bf.disk_used() - bf._baseline() + size > bf.DISK_QUOTA:
                    raise SystemExit("the disk quota of 5 GB would be passed: a STOP")
                old = old_folder / f["name"]
                if old.exists() and sha256_file(old) == f["sha256"]:
                    os.link(old, dest)
                    origin = "linked from v0.5.2's checked cache"
                else:
                    error = bounded_download(f["url"], dest, size)
                    if error:
                        problems.append(f"{f['name']}: {error}")
                        records.append({"name": f["name"], "url": f["url"], "error": error,
                                        "recorded_bytes": size,
                                        "attempted_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                                                       time.gmtime())})  # fmt: skip
                        continue
                    origin = "downloaded"
            got = sha256_file(dest)
            if got != f["sha256"]:
                problems.append(f"{f['name']}: other bytes")
            records.append(
                {"name": f["name"], "url": f["url"], "bytes": dest.stat().st_size, "sha256": got,
                 "origin": origin,
                 "retrieved_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
            )  # fmt: skip
        report["hosts"][key] = records
        if any("other bytes" in p for p in problems):
            report["changed"][key] = problems
        elif problems:
            report["failed"][key] = problems
        print(key, len(records), "ok" if not problems else "problem", flush=True)
    done = [f for files in report["hosts"].values() for f in files if "bytes" in f]
    report["bytes"] = sum(f["bytes"] for f in done)
    report["downloaded_bytes"] = sum(f["bytes"] for f in done if f["origin"] == "downloaded")
    (HERE / f"b1-fetch-{name}.json").write_text(
        json.dumps(report, indent=1, sort_keys=True) + "\n", "utf-8", newline="\n"
    )  # LF, so that the bytes in B1.4's fingerprint are the committed ones
    write_manifests(dossiers, report)
    print("disk used by B1 so far:", bf.disk_after(), "bytes", flush=True)


def write_manifests(dossiers: dict, report: dict) -> None:
    """The adapter's manifests of the checked hosts, as v0.5.2's ``manifests`` writes them."""
    from refute.core.io import dumps_json, write_text
    from refute.packs.tess.adapter import FETCH_SCHEMA, manifest_path

    by_key = ft.targets()
    excluded = set(report["changed"]) | set(report["failed"])
    for key in sorted(set(report["hosts"]) - excluded):
        manifest = json.loads(json.dumps(dossiers[key]["manifest"]))
        tic = int(by_key[key]["tic_id"])
        for f in manifest["files"]:
            f["path"] = f"files/{f['name']}"
            f["format"] = "spoc-fits"
        manifest.update(schema=FETCH_SCHEMA, tic_id=tic, target_key=f"TIC-{tic}", pixel_files=[])
        # serialized once, as write_json writes it; those exact bytes are checked against the
        # bound and written (Codex's review of B1.3, round 3)
        path = manifest_path(CACHE, tic)
        path.parent.mkdir(parents=True, exist_ok=True)
        text = dumps_json(manifest)  # what write_json writes, serialized in memory once
        if len(text.encode("utf-8")) > METADATA_BYTES:
            raise SystemExit(f"{key}: a manifest above its reserved bound: a STOP")
        write_text(path, text)


if __name__ == "__main__":
    # the ledger's lock: a fetch never overlaps a run, so the disk check is exact (Codex's
    # review of B1.3, round 1)
    with ledger_b.Exclusive(f"b1_data {sys.argv[1]} {sys.argv[2]}"):
        {"fetch": lambda: fetch(sys.argv[2])}[sys.argv[1]]()
