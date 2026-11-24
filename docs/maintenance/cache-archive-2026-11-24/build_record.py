"""Builds this folder's record of the two .cache cleanups of 2026-11-24 (issue #220; the
maintainer's decision of 2026-11-24, #218 comment 7130900283, item 1), from the local work files
those cleanups wrote. Run once, from the project's virtual environment, on the machine that ran
the cleanups:

    .venv/Scripts/python.exe docs/maintenance/cache-archive-2026-11-24/build_record.py

What it writes (all LF, UTF-8):

- ``a/``: the first cleanup (#218 comment 7122240195, item 5; 57 files): the script that ran
  (``archive_and_clean.py``, copied byte for byte), its archive manifest and its deletion log
  (copied byte for byte), and ``citations-a.json``, computed now from the deletion log: for each
  deleted file, the git-tracked files at HEAD that cite its SHA-256 or its path, and the tracked
  files with the same bytes (a stored copy). No citation search ran before that cleanup; this list
  is computed after it, from the hashes its log recorded.
- ``b/``: the second cleanup (#218 comment 7125778250, item 4; 10,194 files): the four scripts that
  ran (copied byte for byte), its archive manifest and its deletion log (copied byte for byte), and
  ``citations-b.json``: for each archived file, its class and reason as decided before the
  deletion, and the committed records that cite it by SHA-256 or by path, from the citation search
  that ran before the deletion. The two large work files of that search (the survey and the
  classes, above 5 MB) are copied to the Drive with their SHA-256 checked; ``drive-extra.json``
  records them.
- ``summary.json``: counts, bytes, the Drive destinations and the SHA-256 of every file above.
"""

import hashlib
import json
import re
import shutil
import subprocess
import time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
W = ROOT / ".cache/v059"
DRIVE_A = "K:/Meu Drive/Pessoal/Projetos/refute/cache-archive-2026-11-24"
DRIVE_B = "K:/Meu Drive/Pessoal/Projetos/refute/cache-archive-2026-11-24b"
EMPTY = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
HEX_RE = re.compile(r"(?<![0-9a-fA-F])[0-9a-fA-F]{64}(?![0-9a-fA-F])")
COPIES = {
    "a/archive_and_clean.py": W / "tools/archive_and_clean.py",
    "a/manifest-a.json": W / "archive-2026-11-24-manifest.json",
    "a/deletion-log-a.json": W / "cleanup-2026-11-24.json",
    "b/cleanup_survey.py": W / "tools/cleanup_survey.py",
    "b/cleanup_citations.py": W / "tools/cleanup_citations.py",
    "b/cleanup_classify.py": W / "tools/cleanup_classify.py",
    "b/cleanup2.py": W / "tools/cleanup2.py",
    "b/manifest-b.json": W / "cleanup2/archive-manifest.json",
    "b/deletion-log-b.json": W / "cleanup2/cleanup-log.json",
}
DRIVE_EXTRA = {
    "survey.json": W / "cleanup2/survey.json",
    "classes.json": W / "cleanup2/classes.json",
    "citations.json": W / "cleanup2/citations.json",
}


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def write(rel: str, doc) -> None:
    (HERE / rel).write_text(json.dumps(doc, indent=1) + "\n", "utf-8", newline="\n")


def tracked_index():
    """Per git-tracked text file at HEAD: the 64-hex strings it contains and its text; and the
    SHA-256 of every tracked file's bytes."""
    names = (
        subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, check=True)
        .stdout.decode("utf-8")
        .split("\0")
    )
    hex_refs, texts, by_bytes = defaultdict(set), {}, defaultdict(list)
    for rel in names:
        if not rel or rel.startswith("docs/maintenance/cache-archive-2026-11-24/"):
            continue
        p = ROOT / rel
        try:
            data = p.read_bytes()
        except OSError:
            continue
        by_bytes[hashlib.sha256(data).hexdigest()].append(rel)
        if b"\0" in data[:8192]:
            continue
        text = data.decode("utf-8", errors="replace")
        texts[rel] = text
        for m in HEX_RE.finditer(text):
            hex_refs[m.group(0).lower()].add(rel)
    return hex_refs, texts, by_bytes


def citations_a(hex_refs, texts, by_bytes) -> dict:
    log = json.loads((W / "cleanup-2026-11-24.json").read_text("utf-8"))
    rows = []
    for e in log["entries"]:
        if e["status"] != "deleted":
            continue
        path, digest = e["path"], e["sha256"]
        rows.append(
            {
                "path": path,
                "bytes": e["bytes"],
                "sha256": digest,
                "cited_by_hash": [] if digest == EMPTY else sorted(hex_refs.get(digest, ())),
                "cited_by_path": sorted(r for r, t in texts.items() if path in t),
                "same_bytes_tracked": sorted(by_bytes.get(digest, ())),
            }
        )
    return {
        "computed_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "note": "Computed after the deletion, from the SHA-256 the deletion log recorded, against "
        "the git-tracked files at HEAD (this folder excluded). cited_by_path is a literal "
        "search for the file's path. The empty file's hash is not searched.",
        "files": len(rows),
        "cited": sum(bool(r["cited_by_hash"] or r["cited_by_path"]) for r in rows),
        "stored_in_repository": sum(bool(r["same_bytes_tracked"]) for r in rows),
        "rows": rows,
    }


def citations_b() -> dict:
    cit = json.loads((W / "cleanup2/citations.json").read_text("utf-8"))
    classes = {c["path"]: c for c in json.loads((W / "cleanup2/classes.json").read_text("utf-8"))}
    manifest = json.loads((W / "cleanup2/archive-manifest.json").read_text("utf-8"))
    hash_refs = {h: v["cited_by"] for h, v in cit["hash_citations"].items() if h != EMPTY}
    path_refs = {p.rstrip("/"): v["cited_by"] for p, v in cit["path_citations"].items()
                 if v["existing_files"]}  # fmt: skip
    raw = []
    for r in manifest["rows"]:
        p = r["source"]
        c = classes[p]
        under = sorted((q for q in path_refs if p == q or p.startswith(q + "/")), key=len)
        raw.append(
            (
                p,
                r["bytes"],
                r["source_sha256"],
                c["class"],
                c["reason"],
                sorted(hash_refs.get(r["source_sha256"], ())),
                {q: sorted(path_refs[q]) for q in under},
            )
        )
    records = sorted(
        {x for row in raw for x in row[5]} | {x for row in raw for v in row[6].values() for x in v}
    )
    idx = {x: i for i, x in enumerate(records)}
    rows = [
        [p, b, h, cls, why, [idx[x] for x in hr], {q: [idx[x] for x in v] for q, v in pr.items()}]
        for p, b, h, cls, why, hr, pr in raw
    ]
    counts = defaultdict(int)
    for x in rows:
        counts[x[3]] += 1
    head = {
        "note": "From the citation search and the classification that ran before the deletion "
        "(b/cleanup_citations.py, b/cleanup_classify.py), restricted to the archived "
        "files. class 'cited' is a SHA-256 or a path (or a folder above it) cited by a "
        "git-tracked file at the commit of 2026-11-24 the search ran on. Each row is "
        "[path, bytes, sha256, class, reason, cited_by_hash, cited_by_path], where the "
        "citing records are indices into citing_records and cited_by_path maps each cited "
        "path (the file or a folder above it) to its citing records.",
        "files": len(rows),
        "classes": dict(sorted(counts.items())),
        "cited_by_hash_or_path": sum(bool(x[5] or x[6]) for x in rows),
        "citing_records": records,
    }
    return head, rows


def drive_extra() -> dict:
    out = []
    dst_dir = Path(DRIVE_B) / "record"
    dst_dir.mkdir(parents=True, exist_ok=True)
    for name, src in DRIVE_EXTRA.items():
        dst = dst_dir / name
        shutil.copyfile(src, dst)
        a, b = sha(src), sha(dst)
        out.append(
            {
                "source": src.relative_to(ROOT).as_posix(),
                "bytes": src.stat().st_size,
                "destination": dst.as_posix(),
                "source_sha256": a,
                "destination_sha256": b,
                "match": a == b,
            }
        )
    return {
        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "files": out,
        "all_match": all(x["match"] for x in out),
    }


def main() -> None:
    (HERE / "a").mkdir(exist_ok=True)
    (HERE / "b").mkdir(exist_ok=True)
    for rel, src in COPIES.items():
        shutil.copyfile(src, HERE / rel)
        if sha(src) != sha(HERE / rel):
            raise SystemExit(f"copy differs: {rel}")
    hex_refs, texts, by_bytes = tracked_index()
    write("a/citations-a.json", citations_a(hex_refs, texts, by_bytes))
    head, rows = citations_b()
    body = ",\n".join(json.dumps(r, separators=(",", ":")) for r in rows)
    text = json.dumps(head, indent=1)[:-2] + ',\n "rows": [\n' + body + "\n ]\n}\n"
    json.loads(text)
    (HERE / "b/citations-b.json").write_text(text, "utf-8", newline="\n")
    write("b/drive-extra.json", drive_extra())
    ma = json.loads((HERE / "a/manifest-a.json").read_text("utf-8"))
    la = json.loads((HERE / "a/deletion-log-a.json").read_text("utf-8"))
    mb = json.loads((HERE / "b/manifest-b.json").read_text("utf-8"))
    lb = json.loads((HERE / "b/deletion-log-b.json").read_text("utf-8"))
    ca = json.loads((HERE / "a/citations-a.json").read_text("utf-8"))
    cb = json.loads((HERE / "b/citations-b.json").read_text("utf-8"))
    deleted_b = {e["path"]: e["sha256"] for e in lb["entries"]}
    archived_b = {r["source"]: r["destination_sha256"] for r in mb["rows"] if r["match"]}
    files = sorted(
        p.relative_to(HERE).as_posix()
        for p in HERE.rglob("*")
        if p.is_file() and p.name != "summary.json" and "__pycache__" not in p.parts
    )
    summary = {
        "a": {
            "decision": "#218 comment 7122240195, item 5",
            "drive": DRIVE_A,
            "archived": len(ma["files"]),
            "archive_all_match": ma["all_match"],
            "deleted_files": sum(e["status"] == "deleted" for e in la["entries"]),
            "deleted_bytes": la["bytes_deleted"],
            "folders_removed": sum(e["status"] == "folder removed" for e in la["entries"]),
            "deleted_cited": ca["cited"],
            "deleted_stored_in_repository": ca["stored_in_repository"],
        },  # fmt: skip
        "b": {
            "decision": "#218 comment 7125778250, item 4",
            "drive": DRIVE_B,
            "archived": mb["files"],
            "archived_bytes": mb["bytes"],
            "archive_all_match": mb["all_match"],
            "kept": mb["kept"],
            "deleted_files": lb["files_deleted"],
            "deleted_bytes": lb["bytes_deleted"],
            "folders_removed": len(lb["folders_removed"]),
            "every_deleted_file_archived_with_same_sha256": all(
                archived_b.get(p) == h for p, h in deleted_b.items()
            ),  # fmt: skip
            "classes": cb["classes"],
            "cited_by_hash_or_path": cb["cited_by_hash_or_path"],
        },
        "sha256": {f: sha(HERE / f) for f in files},
    }
    write("summary.json", summary)
    print(json.dumps({k: v for k, v in summary.items() if k != "sha256"}, indent=1))


main()
