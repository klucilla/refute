"""v0.5.6 part B: the prior-exposure scan, second version (the maintainer's decisions of
2026-11-22, 13:00, item 2; Codex's round ``partb`` 1, blocking item 1; #218). **Exploratory**:
read only, no network, no light curve. A new record: ``part-b-prep.json`` (commit 403a480) keeps
its bytes, and its section 3 is superseded by this record.

**Why a second version.** The first scan reused part A's text patterns, which miss a JSON key
``"tic"`` (for example v0.2.1's ``geometry-list.json``, a per-TIC record of MAST-metadata
geometry checks), and it classed catalogue copies by folder, which also classed as copies the
``inputs-references`` CSVs of already selected controls.

**What counts as evidence** that a file names a frame TIC (any one is enough):
1. part A's patterns (``TIC 123``, ``TIC-123``, ``tic_id: 123``), and the same case-insensitively
   with ``tic``, ``tic_id`` or ``ticid`` followed by ``:`` or ``=`` (``"tic": 123``), or by a
   separator and the number (``tic-123``), never inside a word (``statistic 123`` is not);
2. a 16-digit zero-padded TIC between hyphens, as in TESS product names
   (``-0000000123456789-``);
3. in a ``.json`` or ``.jsonl`` file, any value under a key named ``tic``, ``tic_id``, ``ticid``,
   ``tid``, ``tic_ids`` or ``tics`` (any case), as an integer, a digit string, ``TIC 123``, or a
   list of these;
4. in a CSV/TSV file, a TIC column (part A's names);
5. the file's own path, read with 1 and 2.

**Classes** (by path, a written list, decided before the result was used):
- **catalogue copy** (never exposure): the saved answers of catalogue queries, made before any
  selection, which list stars Refute never analysed by being listed there. They are the TOI table
  copies ``calibration/pool_snapshot/exofop_toi.csv``,
  ``calibration/v0.2/pool_snapshot/exofop_toi.csv``, ``calibration/v0.4/inputs/toi.csv`` and
  ``calibration/v0.5/inputs/toi.csv``; the CTOI table ``calibration/v0.4/inputs/ctoi.csv``; and
  the PSCompPars answers ``calibration/pool_snapshot/pscomppars_host_tic_ids.csv``,
  ``calibration/pool_snapshot/pscomppars_planet_pool.csv`` and the same two under
  ``calibration/v0.2/pool_snapshot/``, plus ``calibration/v0.4/inputs/pscomppars.csv`` and
  ``calibration/v0.5/inputs/pscomppars.csv``;
- **record** (exposure): every other file of commit ``EXPOSURE_COMMIT`` (the last before part A)
  that names the TIC. That includes the ``inputs-references`` CSVs, the EB catalogue extracts
  near the targets, selections, results, reviews, plans, tests and archive manifests;
- **light curve** (exposure): a file or folder name under ``.cache/`` outside ``.cache/v056/``
  carrying the TIC as in 2 (TESS light curves, pixel files and their download folders still on
  this machine).

A TIC with at least one record or light-curve evidence is **exposed**. The strata of the
confirmation half are counted before and after the exclusion.

Usage (from the project root):
``.venv/Scripts/python.exe -B docs/validation/v0.5.6/part_b_exposure.py``.
"""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import io
import json
import os
import re
import time
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
LABEL = "WEAKENED; does not meet D1, D2, D4, T2a"
FRAME_FILE = HERE / "part-a-frame.csv"
FRAME_RECORD = HERE / "part-a-frame.json"
OUT_JSON = HERE / "part-b-exposure.json"
OUT_MD = HERE / "part-b-exposure.md"
CATALOGUE_COPIES = (
    "calibration/pool_snapshot/exofop_toi.csv",
    "calibration/pool_snapshot/pscomppars_host_tic_ids.csv",
    "calibration/pool_snapshot/pscomppars_planet_pool.csv",
    "calibration/v0.2/pool_snapshot/exofop_toi.csv",
    "calibration/v0.2/pool_snapshot/pscomppars_host_tic_ids.csv",
    "calibration/v0.2/pool_snapshot/pscomppars_planet_pool.csv",
    "calibration/v0.4/inputs/toi.csv",
    "calibration/v0.4/inputs/ctoi.csv",
    "calibration/v0.4/inputs/pscomppars.csv",
    "calibration/v0.5/inputs/toi.csv",
    "calibration/v0.5/inputs/pscomppars.csv",
)
LOOSE = re.compile(
    rb"(?<![A-Za-z])tic(?:_?id)?[\"']?\s*[:=]\s*[\"']?(?:tic[-_ ]?)?(\d{3,12})"
    rb"|(?<![A-Za-z])tic[-_ ](\d{3,12})",
    re.IGNORECASE,
)
PADDED = re.compile(rb"-(\d{16})-")
JSON_KEYS = {"tic", "tic_id", "ticid", "tid", "tic_ids", "tics"}
STRATA_DISPOSITIONS = ("PC", "APC", "FP", "FA", "KP", "CP")


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _frame_module():
    spec = importlib.util.spec_from_file_location("part_a_frame", HERE / "part_a_frame.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


def write_once(path: Path, text: str) -> None:
    if path.exists():
        raise SystemExit(f"{path.name} exists; never written over")
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, "utf-8", newline="\n")
    os.replace(tmp, path)


# --- evidence (pure: the tests call them) ------------------------------------------------------


def text_tics(paf, data: bytes) -> set[int]:
    found: set[int] = set()
    for m in paf.TEXT_TIC.finditer(data):
        found.add(int(m.group(1) or m.group(2)))
    for m in LOOSE.finditer(data):
        found.add(int(m.group(1) or m.group(2)))
    for m in PADDED.finditer(data):
        found.add(int(m.group(1)))
    return found


def _json_values(value) -> list[int]:
    if isinstance(value, bool):
        return []
    if isinstance(value, int):
        return [value]
    if isinstance(value, str):
        m = re.fullmatch(r"\s*(?:TIC[-_ ]?)?(\d{1,12})\s*", value, re.IGNORECASE)
        return [int(m.group(1))] if m else []
    if isinstance(value, list):
        return [x for v in value for x in _json_values(v)]
    return []


def json_tics(obj) -> set[int]:
    found: set[int] = set()
    stack = [obj]
    while stack:
        o = stack.pop()
        if isinstance(o, dict):
            for k, v in o.items():
                if isinstance(k, str) and k.strip().lower() in JSON_KEYS:
                    found.update(_json_values(v))
                stack.append(v)
        elif isinstance(o, list):
            stack.extend(o)
    return found


def file_tics(paf, path: str, data: bytes) -> set[int]:
    found = text_tics(paf, data) | text_tics(paf, path.encode("utf-8"))
    low = path.lower()
    if low.endswith(".json"):
        try:
            found |= json_tics(json.loads(data))
        except ValueError:
            pass
    elif low.endswith(".jsonl"):
        for line in data.splitlines():
            try:
                found |= json_tics(json.loads(line))
            except ValueError:
                continue
    elif low.endswith((".csv", ".tsv")):
        text = data.decode("utf-8", "replace")
        lines = [x for x in text.splitlines() if x and not x.startswith("#")]
        if lines:
            delimiter = "\t" if low.endswith(".tsv") else ","
            reader = csv.DictReader(io.StringIO("\n".join(lines)), delimiter=delimiter)
            fields = reader.fieldnames or []
            cols = [c for c in fields if c.strip().lower() in paf.TIC_COLUMNS]
            for row in reader:
                for c in cols:
                    tic = paf._tic(row.get(c))
                    if tic is not None:
                        found.add(tic)
    return found


def klass(path: str) -> str:
    if path.startswith(".cache/"):
        return "light_curve"
    return "catalogue_copy" if path in CATALOGUE_COPIES else "record"


# --- scans -------------------------------------------------------------------------------------


def scan_commit(paf, in_frame: set[int]) -> tuple[dict[int, set[str]], dict]:
    names = paf._git("ls-tree", "-r", "-z", "--name-only", paf.EXPOSURE_COMMIT)
    names = [n for n in names.decode("utf-8").split("\0") if n]
    evidence: dict[int, set[str]] = defaultdict(set)
    unreadable = []
    for path in names:
        try:
            data = paf._git("show", f"{paf.EXPOSURE_COMMIT}:{path}")
        except Exception:  # noqa: BLE001 - counted, never skipped silently
            unreadable.append(path)
            continue
        for tic in file_tics(paf, path, data) & in_frame:
            evidence[tic].add(path)
    missing = [p for p in CATALOGUE_COPIES if p not in names]
    if missing:
        raise SystemExit(f"catalogue copies not in the commit: {missing}")
    return evidence, {"commit": paf.EXPOSURE_COMMIT, "files": len(names), "unreadable": unreadable}


def scan_cache(in_frame: set[int]) -> tuple[dict[int, set[str]], int]:
    evidence: dict[int, set[str]] = defaultdict(set)
    cache = ROOT / ".cache"
    names_read = 0
    for dirpath, dirnames, filenames in os.walk(cache, followlinks=False):
        rel = Path(dirpath).relative_to(cache).as_posix()
        if rel == "v056" or rel.startswith("v056/"):
            dirnames[:] = []
            continue
        for name in [*dirnames, *filenames]:
            names_read += 1
            for m in PADDED.finditer(f"-{name}-".encode()):
                tic = int(m.group(1))
                if tic in in_frame:
                    where = f".cache/{rel}/{name}" if rel != "." else f".cache/{name}"
                    evidence[tic].add(where)
    return evidence, names_read


def main() -> None:
    if OUT_JSON.exists() or OUT_MD.exists():
        raise SystemExit("the exposure record is written; never written over")
    record = json.loads(FRAME_RECORD.read_text("utf-8"))
    data = FRAME_FILE.read_bytes()
    if _sha(data) != record["frame_sha256"]:
        raise SystemExit("part-a-frame.csv does not match part-a-frame.json")
    rows = list(csv.DictReader(io.StringIO(data.decode("utf-8"))))
    in_frame = {int(r["tic_id"]) for r in rows}
    paf = _frame_module()
    repo, scan = scan_commit(paf, in_frame)
    lcs, names_read = scan_cache(in_frame)
    evidence = defaultdict(set)
    for src in (repo, lcs):
        for t, ps in src.items():
            evidence[t] |= ps
    paths = sorted({p for ps in evidence.values() for p in ps})
    index = {p: i for i, p in enumerate(paths)}
    classes = {p: klass(p) for p in paths}
    exposed = sorted(
        t for t, ps in evidence.items() if any(classes[p] != "catalogue_copy" for p in ps)
    )
    exposed_set = set(exposed)
    strata = {}
    for half in ("exploration", "confirmation"):
        for arm in ("planet", "open"):
            sel = [r for r in rows if r["half"] == half and r["arm"] == arm]
            groups = {"all": sel}
            if arm == "open":
                for d in (*STRATA_DISPOSITIONS, "(blank)"):
                    groups[d] = [r for r in sel if (r["tfopwg_disp_descriptive"] or "(blank)") == d]
            for g, rs in groups.items():
                strata[f"{half}/{arm}/{g}"] = {
                    "frame": len(rs),
                    "exposed": sum(1 for r in rs if int(r["tic_id"]) in exposed_set),
                    "after_exclusion": sum(1 for r in rs if int(r["tic_id"]) not in exposed_set),
                }
    by_path = Counter(p for t in exposed for p in evidence[t] if classes[p] != "catalogue_copy")
    doc = {
        "schema": "refute-v056-part-b-exposure-2",
        "mode": "exploratory",
        "limits_label": LABEL,
        "method_status": "not_validated",
        "decision": "the maintainer's decisions of 2026-11-22 (13:00), item 2; Codex partb "
        "round 1, item 1; #218",
        "supersedes": "part-b-prep.json section 'exposure' (its bytes unchanged)",
        "inputs": {
            "frame": {"file": FRAME_FILE.name, "sha256": _sha(data)},
            "frame_code": {
                "file": "part_a_frame.py",
                "sha256": _sha((HERE / "part_a_frame.py").read_bytes()),
            },
        },  # fmt: skip
        "code_sha256": _sha(Path(__file__).read_bytes()),
        "rule": {
            "catalogue_copies": list(CATALOGUE_COPIES),
            "record": "every other file of the commit naming the TIC",
            "light_curve": "a file or folder name under .cache/ outside .cache/v056/ with the "
            "16-digit TIC",
            "exposed": "at least one record or light-curve evidence",
        },
        "scan": scan | {"cache_names_read": names_read},
        "paths": [{"path": p, "class": classes[p]} for p in paths],
        "class_counts": dict(Counter(classes.values())),
        "exposing_paths_by_tic_count": dict(by_path.most_common()),
        "tics_with_evidence": len(evidence),
        "tics_exposed": len(exposed),
        "evidence_by_tic": {
            str(t): sorted(index[p] for p in evidence[t]) for t in sorted(evidence)
        },
        "exposed_tics": exposed,
        "strata": strata,
        "written_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    write_once(OUT_JSON, json.dumps(doc, indent=1) + "\n")
    write_once(OUT_MD, markdown(doc))
    conf = {k: v["after_exclusion"] for k, v in strata.items() if k in
            ("confirmation/planet/all", "confirmation/open/FP")}  # fmt: skip
    print(json.dumps({"exposed": len(exposed), "classes": doc["class_counts"], "pools": conf}))


def markdown(doc: dict) -> str:
    out = [
        "# v0.5.6 part B: prior exposure, second version",
        "",
        "**Exploratory.** Limits label: 'WEAKENED; does not meet D1, D2, D4, T2a'. "
        "`method_status: not_validated`. Read only, no light curve. This record supersedes "
        "section 3 of `part-b-prep.md` (whose bytes do not change): the first scan missed JSON "
        'keys such as `"tic"` and classed catalogue copies by folder (Codex\'s round `partb` 1, '
        f"item 1). Generated by `part_b_exposure.py` (SHA-256 `{doc['code_sha256'][:16]}...`).",
        "",
        f"Commit `{doc['scan']['commit'][:12]}`: {doc['scan']['files']} files read, "
        f"{len(doc['scan']['unreadable'])} unreadable; {doc['scan']['cache_names_read']} names "
        "read under `.cache/` outside `.cache/v056/`.",
        "",
        "**Catalogue copies** (never exposure): "
        + ", ".join(f"`{p}`" for p in doc["rule"]["catalogue_copies"])
        + ". **Record** (exposure): every other file naming the TIC. **Light curve** "
        "(exposure): " + doc["rule"]["light_curve"] + ".",
        "",
        f"Evidence paths by class: {doc['class_counts']}. Frame TICs with any evidence: "
        f"{doc['tics_with_evidence']}; **exposed: {doc['tics_exposed']}**.",
        "",
        "The files that expose the most TICs:",
        "",
    ]
    for p, n in list(doc["exposing_paths_by_tic_count"].items())[:15]:
        out.append(f"- `{p}`: {n}")
    out += [
        "",
        "| Half / arm / disposition | Frame | Exposed | After exclusion |",
        "|---|---|---|---|",
    ]
    for k, s in doc["strata"].items():
        if s["frame"]:
            out.append(f"| {k} | {s['frame']} | {s['exposed']} | {s['after_exclusion']} |")
    out += [
        "",
        "## Limits",
        "",
        "- Files archived to the Drive and named nowhere in the repository, and records kept "
        "only under `.cache/` (whose contents are not read, only names), are not seen.",
        "- The record class and the loose patterns are wide on purpose: a false match can only "
        "shrink the strata.",
        "",
    ]
    return "\n".join(out)


if __name__ == "__main__":
    main()
