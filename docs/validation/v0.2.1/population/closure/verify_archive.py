"""Verify a copy of the archive of the v0.2.1 population study against its manifest (read-only).

The archive is a copy of the folder .cache/population/ of the repository, taken as the
snapshot recorded in archive-summary.md (next to this script). Its manifest lists every file with
its SHA-256, size, path relative to that folder and set (A, B, C). The expected values (snapshot
id, manifest SHA-256, manifest path inside the archive, declared exclusion, file count per set)
are read from the block that starts with the line "[verify_archive]" in archive-summary.md.

Checks:
1. the sets: only A, B and C are known; an unknown set or an empty selection is refused;
2. the manifest given with --manifest (required): its path and SHA-256 are printed, and the
   SHA-256 must equal the expected value;
3. the selected rows: their count must equal the expected count for the chosen sets; for every
   row, ARCHIVE_ROOT/<path> must exist with the same size and SHA-256 (hashing in parallel,
   os.cpu_count() - 2 processes by default; the effective affinity mask is printed first);
4. files under ARCHIVE_ROOT that the manifest does not name are listed as extra (not an error);
   the declared exclusion (the manifest itself) is reported apart.

"ARCHIVE VERIFIED" is printed only if the selection is not empty, its count equals the expected
count and every selected file is verified. Nothing is written under ARCHIVE_ROOT; the JSON report
is written only to --report. The user name is masked in printed paths.

Usage:
  python verify_archive.py ARCHIVE_ROOT --manifest FILE [--sets A,B,C] [--report FILE]
                           [--workers N] [--expected-manifest-sha256 HEX]

Independent verification of a copy, with the manifest that travels inside it:
  python verify_archive.py COPY --manifest COPY/<manifest path inside the archive> --sets A,B,C

--expected-manifest-sha256 replaces the recorded value; it exists only for negative controls
(a manifest with one altered row) and is never needed to verify the archive.
Exit status: 0 verified; 1 not verified (a file missing or different, or a count that differs);
2 refused (unknown set, empty selection, manifest missing or not the expected one, bad usage).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor
from datetime import UTC, datetime
from pathlib import Path

HEADER = "sha256\tsize_bytes\tpath\tset\tcited\tother_copies\tin_repo"
KNOWN_SETS = ("A", "B", "C")
HERE = Path(__file__).resolve().parent
SUMMARY = HERE / "archive-summary.md"


def affinity_mask() -> str:
    if sys.platform == "win32":
        import ctypes
        from ctypes import wintypes

        k = ctypes.WinDLL("kernel32", use_last_error=True)
        k.GetCurrentProcess.restype = wintypes.HANDLE
        k.GetProcessAffinityMask.argtypes = [
            wintypes.HANDLE, ctypes.POINTER(ctypes.c_size_t), ctypes.POINTER(ctypes.c_size_t)
        ]
        proc, system = ctypes.c_size_t(), ctypes.c_size_t()
        if k.GetProcessAffinityMask(k.GetCurrentProcess(), ctypes.byref(proc), ctypes.byref(system)):
            return hex(proc.value)
        return "unknown"
    return "cpus " + ",".join(str(c) for c in sorted(os.sched_getaffinity(0)))


def mask(text: str) -> str:
    """The path as printed: the home folder becomes ~ and the login name <user>."""
    home = str(Path.home())
    out = text.replace(home, "~")
    name = os.environ.get("USERNAME") or os.environ.get("USER") or ""
    if len(name) >= 2:
        low = out.lower()
        i = low.find(name.lower())
        while i >= 0:
            out = out[:i] + "<user>" + out[i + len(name):]
            low = out.lower()
            i = low.find(name.lower(), i + len("<user>"))
    return out


def expected_values() -> dict[str, str]:
    lines = SUMMARY.read_text(encoding="utf-8").splitlines()
    try:
        start = lines.index("[verify_archive]")
    except ValueError as exc:
        raise SystemExit("archive-summary.md has no [verify_archive] block") from exc
    values = {}
    for line in lines[start + 1:]:
        if not line.strip() or line.startswith("```"):
            break
        key, _, value = line.partition(":")
        values[key.strip()] = value.strip()
    return values


def sha_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()


def check(task: tuple[str, str, str, int]) -> tuple[str, str]:
    root, rel, digest, size = task
    p = Path(root) / rel
    if not p.is_file():
        return rel, "missing"
    if p.stat().st_size != size:
        return rel, "size differs"
    if sha_file(p) != digest:
        return rel, "SHA-256 differs"
    return rel, "ok"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("archive_root", type=Path)
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--sets", default="A,B,C")
    ap.add_argument("--report", type=Path, default=None)
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 4) - 2))
    ap.add_argument("--expected-manifest-sha256", default=None)
    args = ap.parse_args()

    print("affinity mask:", affinity_mask())
    exp = expected_values()
    snap = exp.get("snapshot_id", "?")
    exclusion = exp.get("declared_exclusion", "")
    print(f"snapshot: {snap}")

    requested = [s.strip() for s in args.sets.split(",") if s.strip()]
    unknown = sorted({s for s in requested if s not in KNOWN_SETS})
    if unknown:
        print(f"REFUSED: unknown set(s) {unknown}; known sets: {list(KNOWN_SETS)}")
        return 2
    sets = sorted(set(requested))
    if not sets:
        print("REFUSED: empty selection of sets")
        return 2

    manifest = args.manifest
    print(f"manifest: {mask(str(manifest))}")
    if not manifest.is_file():
        print("REFUSED: manifest not found")
        return 2
    msha = sha_file(manifest)
    expected_sha = args.expected_manifest_sha256 or exp.get("manifest_sha256", "")
    origin = "override for a negative control" if args.expected_manifest_sha256 else (
        "archive-summary.md")
    print(f"manifest SHA-256: {msha}")
    print(f"expected SHA-256: {expected_sha} ({origin})")
    if msha != expected_sha:
        print("REFUSED: the manifest is not the expected one")
        return 2
    if not args.archive_root.is_dir():
        print("REFUSED: ARCHIVE_ROOT is not a folder")
        return 2

    lines = manifest.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0] != HEADER:
        print("REFUSED: unexpected manifest header")
        return 2
    rows = []
    for line in lines[1:]:
        digest, size, rel, s, *_ = line.split("\t")
        rows.append((digest, int(size), rel, s))
    selected = [r for r in rows if r[3] in sets]
    expected_count = sum(int(exp.get(f"files_{s}", "-1")) for s in sets)
    print(f"sets: {','.join(sets)}; rows selected {len(selected)}; expected {expected_count}")
    print(f"declared exclusion: {exclusion}")
    if not selected:
        print("REFUSED: empty selection (no manifest row in the chosen sets)")
        return 2

    root = str(args.archive_root.resolve())
    tasks = [(root, rel, digest, size) for digest, size, rel, _ in selected]
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        results = list(pool.map(check, tasks, chunksize=64))

    named = {r[2] for r in rows}
    extra, exclusion_present = [], False
    for p in args.archive_root.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(args.archive_root).as_posix()
        if rel in named:
            continue
        if rel == exclusion.split(" ")[0]:
            exclusion_present = True
        else:
            extra.append(rel)
    extra.sort()
    counts: dict[str, int] = {}
    for _, status in results:
        counts[status] = counts.get(status, 0) + 1
    problems = [(rel, status) for rel, status in results if status != "ok"]
    selected_bytes = sum(r[1] for r in selected)
    n_ok = counts.get("ok", 0)
    print(f"files checked: {len(selected)} ({selected_bytes} bytes)")
    for status, n in sorted(counts.items()):
        print(f"  {status}: {n}")
    for rel, status in problems[:50]:
        print(f"  {status}: {rel}")
    if len(problems) > 50:
        print(f"  ... and {len(problems) - 50} more (see --report)")
    print(f"declared exclusion present in the archive: {exclusion_present}")
    print(f"extra files not in the manifest: {len(extra)}")
    for rel in extra[:20]:
        print(f"  extra: {rel}")
    count_ok = len(selected) == expected_count and n_ok == expected_count
    if not count_ok:
        print(f"count differs from the expected: verified {n_ok}, expected {expected_count}")
    ok = bool(selected) and count_ok and not problems
    verdict = "ARCHIVE VERIFIED" if ok else "ARCHIVE NOT VERIFIED"
    print(f"{verdict}: snapshot {snap}, sets {','.join(sets)}, {n_ok} of {expected_count} files, "
          f"manifest {msha}")
    if args.report is not None:
        if args.report.exists():
            print(f"{args.report.name} exists; report not written")
        else:
            with open(args.report, "x", encoding="utf-8", newline="\n") as fh:
                fh.write(json.dumps({
                    "verified_utc": datetime.now(UTC).isoformat(timespec="seconds"),
                    "snapshot_id": snap,
                    "manifest_sha256": msha,
                    "expected_manifest_sha256": expected_sha,
                    "sets": sets,
                    "expected_count": expected_count,
                    "files_checked": len(selected),
                    "bytes_checked": selected_bytes,
                    "counts": counts,
                    "problems": problems,
                    "declared_exclusion": exclusion,
                    "declared_exclusion_present": exclusion_present,
                    "extra_files": extra,
                    "verified": ok,
                    "affinity_mask": affinity_mask(),
                }, indent=1) + "\n")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
