"""Read-only: classify every file of the five folders for the cleanup (decision of 2026-11-24, 05:07,
item 4). Writes .cache/v059/cleanup2/classes.json and prints a summary.

Classes:
- ``cited``: its SHA-256 appears in a committed file (not the empty-file hash, which proves
  nothing), or its path (or a folder above it) is cited by a committed file;
- ``value``: not cited, but a result, script, log or text record (by extension), outside
  environments and package trees;
- ``regenerable``: a virtual environment, node packages, a build, a package cache, or a
  downloaded data cache that no committed record cites.
"""

import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SURVEY = ROOT / ".cache/v059/cleanup2/survey.json"
CIT = ROOT / ".cache/v059/cleanup2/citations.json"
OUT = ROOT / ".cache/v059/cleanup2/classes.json"
EMPTY = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
ENV_MARKERS = ("/node_modules/", "/.venv/", "/venv/", "/site-packages/", "/Lib/", "/Scripts/",
               "/__pycache__/", "/.astro/", "/dist/", "/.npm/", "/Include/")
VALUE_EXT = {"py", "ps1", "sh", "json", "jsonl", "md", "txt", "log", "csv", "tsv", "xml", "yaml",
             "yml", "html", "err", "out", "zip", "toml", "patch", "diff", "npz", "png", "svg"}
DATA_EXT = {"fits", "bin", "gz", "fz"}


def main() -> None:
    files = json.loads(SURVEY.read_text("utf-8"))["files"]
    cit = json.loads(CIT.read_text("utf-8"))
    hash_refs = {h: v["cited_by"] for h, v in cit["hash_citations"].items() if h != EMPTY}
    cited_paths = [p.rstrip("/") for p, v in cit["path_citations"].items() if v["existing_files"]]
    out, summary, why = [], Counter(), defaultdict(Counter)
    for f in files:
        p, ext = f["path"], f["path"].rsplit(".", 1)[-1].lower()
        env = any(m in "/" + p for m in ENV_MARKERS)
        refs = hash_refs.get(f["sha256"])
        by_path = [c for c in cited_paths if p == c or p.startswith(c + "/")]
        if refs:
            cls, reason = "cited", f"hash in {refs[0]}" + (f" (+{len(refs) - 1})" if len(refs) > 1 else "")
        elif by_path and not env:
            cls, reason = "cited", f"path {max(by_path, key=len)}"
        elif env:
            cls, reason = "regenerable", "environment or package tree"
        elif ext in DATA_EXT:
            cls, reason = "regenerable", "downloaded data or cache, not cited"
        else:
            cls, reason = "value", "result, script, log, record or source"
        top = "/".join(p.split("/")[1:3])
        summary[(top, cls)] += f["bytes"]
        why[cls][reason.split(" in ")[0].split(" (")[0]] += 1
        out.append({**f, "class": cls, "reason": reason})
    OUT.write_text(json.dumps(out, indent=1), "utf-8")
    tot = Counter()
    for (top, cls), b in sorted(summary.items()):
        tot[cls] += b
        print(f"{top:32s} {cls:12s} {b / 1e6:9.1f} MB")
    print({k: round(v / 1e9, 3) for k, v in tot.items()})
    print({k: dict(v) for k, v in why.items()})


main()
