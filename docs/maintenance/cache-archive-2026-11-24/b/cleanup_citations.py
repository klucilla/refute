"""Read-only: which files of the five .cache folders are cited by a committed record, by path or by
SHA-256 (the decision of 2026-11-24, 05:07, item 4 (a)). Reads every git-tracked text file at HEAD
and the survey written by cleanup_survey.py --hash. Writes .cache/v059/cleanup2/citations.json."""

import json
import re
import subprocess
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SURVEY = ROOT / ".cache/v059/cleanup2/survey.json"
OUT = ROOT / ".cache/v059/cleanup2/citations.json"
PATH_RE = re.compile(r"\.cache[/\\](v052|v053|maint1120|v05|v055)(?=[/\\\s`'\")\],;:]|$)([^\s`'\")\],;]*)")
HEX_RE = re.compile(r"(?<![0-9a-fA-F])[0-9a-fA-F]{64}(?![0-9a-fA-F])")


def main() -> None:
    tracked = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True,
                             check=True).stdout.decode("utf-8").split("\0")
    path_cites = defaultdict(set)  # cited path (as written) -> citing files
    hex_cites = defaultdict(set)  # hash -> citing files
    for rel in tracked:
        if not rel:
            continue
        p = ROOT / rel
        try:
            data = p.read_bytes()
        except OSError:
            continue
        if b"\0" in data[:8192]:
            continue
        text = data.decode("utf-8", errors="replace")
        for m in PATH_RE.finditer(text):
            cited = (".cache/" + m.group(1) + m.group(2).replace("\\", "/")).rstrip(".")
            path_cites[cited].add(rel)
        for m in HEX_RE.finditer(text):
            hex_cites[m.group(0).lower()].add(rel)
    survey = json.loads(SURVEY.read_text("utf-8"))
    by_hash = defaultdict(list)
    for f in survey["files"]:
        by_hash[f["sha256"]].append(f["path"])
    hash_hits = {h: {"files": by_hash[h], "cited_by": sorted(hex_cites[h])}
                 for h in by_hash if h in hex_cites}  # fmt: skip
    existing = {f["path"] for f in survey["files"]}
    path_hits = {}
    for cited, refs in sorted(path_cites.items()):
        under = [x for x in existing if x == cited or x.startswith(cited.rstrip("/") + "/")]
        path_hits[cited] = {"cited_by": sorted(refs), "existing_files": len(under),
                            "existing_bytes": sum(f["bytes"] for f in survey["files"]
                                                  if f["path"] in set(under))}  # fmt: skip
    OUT.write_text(json.dumps({"path_citations": path_hits, "hash_citations": hash_hits},
                              indent=1), "utf-8")  # fmt: skip
    cited_files = {x for v in hash_hits.values() for x in v["files"]}
    print("paths cited:", len(path_hits), "with existing files:",
          sum(1 for v in path_hits.values() if v["existing_files"]))
    print("files cited by hash:", len(cited_files),
          f"{sum(f['bytes'] for f in survey['files'] if f['path'] in cited_files) / 1e6:.1f} MB")


main()
