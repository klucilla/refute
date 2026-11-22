"""v0.5.6 part B: the exploratory step before any lock (the maintainer's decisions of 2026-11-22,
13:00, item 2; #218). **Exploratory**: read only on part A's committed records and frame, no new
light curve and no network; never a verdict on any TOI. ``method_status: not_validated``. Limits
label: 'WEAKENED; does not meet D1, D2, D4, T2a'.

It writes ``part-b-prep.json`` and ``part-b-prep.md`` next to this script, refusing to write over
them. Three parts:

1. **The REFUTED cases one by one:** the planet arm's REFUTED records and the open arm's REFUTED
   records whose TOI disposition is FP (the disposition is the frame's ``tfopwg_disp_descriptive``,
   read from ``part-a-frame.csv`` as committed). Per record: every FAIL test, the first decisive
   fatal FAIL in the battery's order (the cause door 2 used), the outcome reason, the signal
   identity, and the found period against the TOI's. A record is a **half-period case** when the
   identity's factor is 0.5 (the battery's candidate at half the TOI's period).
2. **Signal identity against outcome**, per arm and, in the open arm, per disposition, over every
   record with nonzero coverage (the report's denominator).
3. **The prior-exposure scan, redone.** Every file of the commit before part A
   (``EXPOSURE_COMMIT``, the same as part A's frame) is read with part A's own patterns (text
   ``TIC 123`` / ``tic_id: 123``, and TIC columns of CSV/TSV files), and **all** evidence per TIC is
   kept, not only the first. Each file is classed by a rule written before the scan's result was
   used:
   - **catalogue copy** (never exposure): a ``.csv`` or ``.tsv`` file in a folder named
     ``pool_snapshot``, ``inputs``, ``inputs-references`` or ``eb_snapshot`` under
     ``calibration/``, or a file named ``eb_catalog.csv``; these are copies of the TOI table,
     PSCompPars, the CTOI table and the TESS EB catalogue, and name stars Refute never read;
   - **record** (exposure): every other file: records, results, selections, reviews, plans,
     tests and archive manifests of v0.1 to v0.5.5. This class is wide on purpose: a TIC named in
     any of them is excluded from part B, which can only shrink the confirmation strata.
   A second source adds **light curves and pixel files** still on this machine: every
   ``tess*.fits`` file name under ``.cache/`` outside ``.cache/v056/`` (part A's own), whose
   16-digit TIC is read from the name. A TIC is **exposed** when it has at least one record or
   light-curve evidence. The confirmation strata (the confirmation half: the planet arm, and the
   open arm by disposition) are counted before and after the exclusion; eligibility (SPOC
   two-minute data, at least two predicted transits) is decided at part B's draw, so the counts
   here are frame counts, with part A's eligibility rates for scale.

Usage (from the project root):
``.venv/Scripts/python.exe -B docs/validation/v0.5.6/part_b_prep.py``.
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
RECORDS = HERE / "part-a-records.json"
FRAME_FILE = HERE / "part-a-frame.csv"
FRAME_RECORD = HERE / "part-a-frame.json"
DRAW = HERE / "part-a-draw.json"
OUT_JSON = HERE / "part-b-prep.json"
OUT_MD = HERE / "part-b-prep.md"
OUTCOMES = ("SURVIVED", "WEAKENED", "REFUTED", "INCONCLUSIVE")
DISPOSITIONS = ("PC", "APC", "FP", "FA", "KP", "CP")
CATALOGUE_FOLDERS = ("pool_snapshot", "inputs", "inputs-references", "eb_snapshot")
CATALOGUE_NAMES = ("eb_catalog.csv",)
FITS_NAME = re.compile(r"^tess\d+-s\d{4}-(\d{16})-\d{4}-[a-z]_(?:lc|tp)\.fits$")
HALF = 0.5


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


# --- inputs, checked ---------------------------------------------------------------------------


def frame_rows() -> list[dict[str, str]]:
    record = json.loads(FRAME_RECORD.read_text("utf-8"))
    data = FRAME_FILE.read_bytes()
    if _sha(data) != record["frame_sha256"]:
        raise SystemExit("part-a-frame.csv does not match the SHA-256 in part-a-frame.json")
    return list(csv.DictReader(io.StringIO(data.decode("utf-8"))))


def records(frame: dict[int, dict[str, str]]) -> list[dict]:
    bundle = json.loads(RECORDS.read_text("utf-8"))
    out = []
    for item in bundle["records"]:  # the bundle keeps each record file's own SHA-256
        r = item["content"]
        r["_file"], r["_file_sha256"] = item["file"], item["sha256"]
        r["disposition"] = frame[r["tic_id"]]["tfopwg_disp_descriptive"] or "(blank)"
        out.append(r)
    return out


def covered(r: dict) -> bool:  # the same rule as part_a_report.py
    if r.get("status") != "OK":
        return False
    return any((r["tests"].get(n, {}).get("coverage") or 0) > 0 for n in r["decisive"])


def first_fatal(r: dict) -> str | None:  # the same rule as part_a_report.py
    for name, t in r["tests"].items():
        if name in r["decisive"] and t["status"] == "FAIL" and t["severity"] == "fatal":
            return name
    return None


# --- 1. the REFUTED cases ----------------------------------------------------------------------


def case(r: dict) -> dict:
    ident = r.get("identity") or {}
    fails = {
        n: {"severity": t["severity"], "decisive": n in r["decisive"], "message": t["message"]}
        for n, t in r["tests"].items()
        if t["status"] == "FAIL"
    }
    toi_p, found_p = ident.get("toi_period_days"), ident.get("found_period_days")
    return {
        "toi": r["toi"],
        "tic_id": r["tic_id"],
        "arm": r["arm"],
        "disposition": r["disposition"],
        "outcome": r["outcome"],
        "outcome_reason": r["outcome_reason"],
        "first_decisive_fatal_fail": first_fatal(r),
        "fails": fails,
        "toi_period_days": toi_p,
        "found_period_days": found_p,
        "found_over_toi": (found_p / toi_p) if toi_p and found_p else None,
        "identity_factor": ident.get("factor"),
        "epoch_offset_hours": ident.get("epoch_offset_hours"),
        "identity_matched": bool(ident.get("matched")),
        "half_period_case": ident.get("factor") == HALF,
        "candidate_snr": (r.get("candidate") or {}).get("snr"),
        "record_file": r["_file"],
        "record_sha256": r["_file_sha256"],
    }


# --- 2. identity against outcome ---------------------------------------------------------------


def identity_table(rs: list[dict]) -> dict:
    cov = [r for r in rs if covered(r)]
    table = {}
    for matched in (True, False):
        sel = [r for r in cov if bool((r.get("identity") or {}).get("matched")) == matched]
        c = Counter(r["outcome"] for r in sel)
        table["matched" if matched else "not_matched"] = {"n": len(sel)} | {
            o: c.get(o, 0) for o in OUTCOMES
        }
    table["nonzero_coverage"] = len(cov)
    table["records"] = len(rs)
    return table


# --- 3. the exposure scan, redone --------------------------------------------------------------


def catalogue_copy(path: str) -> bool:
    p = path.lower()
    if not p.endswith((".csv", ".tsv")):
        return False
    parts = p.split("/")
    if parts[-1] in CATALOGUE_NAMES:
        return True
    return parts[0] == "calibration" and any(f in parts[:-1] for f in CATALOGUE_FOLDERS)


def scan_commit(paf, in_frame: set[int]) -> tuple[dict[int, set[str]], dict]:
    names = [n for n in paf._git("ls-tree", "-r", "-z", "--name-only", paf.EXPOSURE_COMMIT)
             .decode("utf-8").split("\0") if n]  # fmt: skip
    evidence: dict[int, set[str]] = defaultdict(set)
    unreadable = []
    for path in names:
        try:
            data = paf._git("show", f"{paf.EXPOSURE_COMMIT}:{path}")
        except Exception:  # noqa: BLE001 - counted, never skipped silently
            unreadable.append(path)
            continue
        found: set[int] = set()
        for line in data.split(b"\n"):
            for m in paf.TEXT_TIC.finditer(line):
                found.add(int(m.group(1) or m.group(2)))
        if path.lower().endswith((".csv", ".tsv")):
            text = data.decode("utf-8", "replace")
            lines = [x for x in text.splitlines() if x and not x.startswith("#")]
            if lines:
                delimiter = "\t" if path.lower().endswith(".tsv") else ","
                reader = csv.DictReader(io.StringIO("\n".join(lines)), delimiter=delimiter)
                fields = reader.fieldnames or []
                cols = [c for c in fields if c.strip().lower() in paf.TIC_COLUMNS]
                for row in reader:
                    for c in cols:
                        tic = paf._tic(row.get(c))
                        if tic is not None:
                            found.add(tic)
        for tic in found & in_frame:
            evidence[tic].add(path)
    return evidence, {"commit": paf.EXPOSURE_COMMIT, "files": len(names), "unreadable": unreadable}


def scan_cache(in_frame: set[int]) -> tuple[dict[int, set[str]], int]:
    evidence: dict[int, set[str]] = defaultdict(set)
    cache = ROOT / ".cache"
    seen = 0
    for dirpath, dirnames, filenames in os.walk(cache, followlinks=False):
        rel = Path(dirpath).relative_to(cache).as_posix()
        if rel == "v056" or rel.startswith("v056/"):
            dirnames[:] = []
            continue
        for name in filenames:
            m = FITS_NAME.match(name.lower())
            if not m:
                continue
            seen += 1
            tic = int(m.group(1))
            if tic in in_frame:
                evidence[tic].add(f".cache/{rel}/{name}" if rel != "." else f".cache/{name}")
    return evidence, seen


def exposure(paf, rows: list[dict[str, str]]) -> dict:
    in_frame = {int(r["tic_id"]) for r in rows}
    repo, scan = scan_commit(paf, in_frame)
    lcs, fits_seen = scan_cache(in_frame)
    paths = sorted({p for s in repo.values() for p in s} | {p for s in lcs.values() for p in s})
    index = {p: i for i, p in enumerate(paths)}
    klass = {p: ("light_curve" if p.startswith(".cache/") else
                 "catalogue_copy" if catalogue_copy(p) else "record") for p in paths}  # fmt: skip
    exposed = {}
    for tic in sorted(set(repo) | set(lcs)):
        ev = sorted(repo.get(tic, set()) | lcs.get(tic, set()))
        if any(klass[p] != "catalogue_copy" for p in ev):
            exposed[tic] = ev
    per_tic = {str(t): sorted(index[p] for p in repo.get(t, set()) | lcs.get(t, set()))
               for t in sorted(set(repo) | set(lcs))}  # fmt: skip
    strata = {}
    for half in ("exploration", "confirmation"):
        for arm in ("planet", "open"):
            sel = [r for r in rows if r["half"] == half and r["arm"] == arm]
            groups = {"all": sel}
            if arm == "open":
                for d in DISPOSITIONS + ("(blank)",):
                    groups[d] = [r for r in sel if (r["tfopwg_disp_descriptive"] or "(blank)") == d]
            for g, rs in groups.items():
                strata[f"{half}/{arm}/{g}"] = {
                    "frame": len(rs),
                    "exposed": sum(1 for r in rs if int(r["tic_id"]) in exposed),
                    "after_exclusion": sum(1 for r in rs if int(r["tic_id"]) not in exposed),
                    "part_a_flag": sum(1 for r in rs if r["prior_exposure"] == "True"),
                }
    return {
        "rule": {
            "catalogue_copy": "a .csv or .tsv in a calibration/ folder named "
            + ", ".join(CATALOGUE_FOLDERS)
            + "; or a file named "
            + ", ".join(CATALOGUE_NAMES),
            "record": "every other file of the commit naming the TIC",
            "light_curve": "a tess*.fits file name under .cache/ outside .cache/v056/",
            "exposed": "at least one record or light-curve evidence",
        },
        "scan": scan | {"cache_fits_names_read": fits_seen},
        "paths": [{"path": p, "class": klass[p]} for p in paths],
        "class_counts": dict(Counter(klass.values())),
        "tics_with_evidence": len(per_tic),
        "tics_exposed": len(exposed),
        "evidence_by_tic": per_tic,
        "exposed_tics": sorted(exposed),
        "strata": strata,
    }


# --- main --------------------------------------------------------------------------------------


def main() -> None:
    if OUT_JSON.exists() or OUT_MD.exists():
        raise SystemExit("part B's preparation is recorded; never written over")
    rows = frame_rows()
    frame = {int(r["tic_id"]): r for r in rows}
    rs = records(frame)
    planet = [r for r in rs if r["arm"] == "planet"]
    opn = [r for r in rs if r["arm"] == "open"]
    cases = [case(r) for r in planet if r.get("outcome") == "REFUTED"] + [
        case(r) for r in opn if r.get("outcome") == "REFUTED" and r["disposition"] == "FP"
    ]
    ident = {"planet": identity_table(planet), "open": identity_table(opn)}
    for d in DISPOSITIONS:
        sub = [r for r in opn if r["disposition"] == d]
        if sub:
            ident[f"open/{d}"] = identity_table(sub)
    paf = _frame_module()
    expo = exposure(paf, rows)
    draw = json.loads(DRAW.read_text("utf-8"))
    doc = {
        "schema": "refute-v056-part-b-prep-1",
        "mode": "exploratory",
        "limits_label": LABEL,
        "method_status": "not_validated",
        "decision": "the maintainer's decisions of 2026-11-22 (13:00), item 2; #218",
        "inputs": {
            "records": {"file": RECORDS.name, "sha256": _sha(RECORDS.read_bytes())},
            "frame": {"file": FRAME_FILE.name, "sha256": _sha(FRAME_FILE.read_bytes())},
            "draw": {"file": DRAW.name, "sha256": _sha(DRAW.read_bytes())},
            "frame_code": {
                "file": "part_a_frame.py",
                "sha256": _sha((HERE / "part_a_frame.py").read_bytes()),
            },
        },  # fmt: skip
        "code_sha256": _sha(Path(__file__).read_bytes()),
        "cases": cases,
        "half_period_cases": [c["toi"] for c in cases if c["half_period_case"]],
        "identity_against_outcome": ident,
        "part_a_eligibility": {
            a: {"checked": draw["arms"][a]["checked"], "eligible": draw["arms"][a]["eligible"]}
            for a in ("planet", "open")
        },
        "exposure": expo,
        "written_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    write_once(OUT_JSON, json.dumps(doc, indent=1) + "\n")
    write_once(OUT_MD, markdown(doc))
    summary = {"cases": len(cases), "half": doc["half_period_cases"],
               "exposed": expo["tics_exposed"], "classes": expo["class_counts"]}  # fmt: skip
    print(json.dumps(summary))


def _f(x, nd=4) -> str:
    return "n/a" if x is None else f"{x:.{nd}f}"


def markdown(doc: dict) -> str:
    out = [
        "# v0.5.6 part B: the exploratory step before any lock",
        "",
        "**Exploratory.** Limits label: 'WEAKENED; does not meet D1, D2, D4, T2a'. "
        "`method_status: not_validated`. Read only on part A's committed records and frame, with "
        "no new light curve. Nothing here is a verdict on any TOI or a candidate in a public "
        "claim; the dispositions are the TFOPWG's, from the frame as committed, and agreement "
        "with them is not independence. Generated by `part_b_prep.py` (SHA-256 "
        f"`{doc['code_sha256'][:16]}...`).",
        "",
        "## 1. The REFUTED cases, one by one",
        "",
        "Found/TOI is the battery's period over the TOI's. The first decisive fatal FAIL is the "
        "cause door 2 used.",
        "",
        "| TOI | Arm | Disp. | First decisive fatal FAIL | Other FAILs | TOI period (d) | "
        "Found (d) | Found/TOI | Epoch offset (h) | Identity |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for c in doc["cases"]:
        others = ", ".join(n for n in c["fails"] if n != c["first_decisive_fatal_fail"]) or "none"
        ident = "matched" if c["identity_matched"] else (
            "half period" if c["half_period_case"] else "not matched")  # fmt: skip
        out.append(
            f"| {c['toi']} | {c['arm']} | {c['disposition']} | "
            f"{c['first_decisive_fatal_fail'] or '(none)'} | {others} | "
            f"{_f(c['toi_period_days'])} | {_f(c['found_period_days'])} | "
            f"{_f(c['found_over_toi'], 3)} | {_f(c['epoch_offset_hours'], 2)} | {ident} |"
        )
    out += ["", "The decisive FAIL messages:", ""]
    for c in doc["cases"]:
        n = c["first_decisive_fatal_fail"]
        msg = c["fails"][n]["message"] if n else c["outcome_reason"]
        out.append(f"- **TOI-{c['toi']}** ({n or 'none'}): {msg}")
    half = doc["half_period_cases"]
    out += [
        "",
        "**Half-period cases** (identity factor 0.5): "
        + (", ".join(f"TOI-{t}" for t in half) if half else "none")
        + ". They are logged on #59 as a search and alias defect, never as evidence against "
        "the TOI.",
        "",
        "## 2. Signal identity against outcome (records with nonzero coverage)",
        "",
        "| Group | Identity | n | SURVIVED | WEAKENED | REFUTED | INCONCLUSIVE |",
        "|---|---|---|---|---|---|---|",
    ]
    for g, t in doc["identity_against_outcome"].items():
        for k in ("matched", "not_matched"):
            row = t[k]
            out.append(f"| {g} | {k.replace('_', ' ')} | {row['n']} | "
                       + " | ".join(str(row[o]) for o in OUTCOMES) + " |")  # fmt: skip
    e = doc["exposure"]
    out += [
        "",
        "## 3. Prior exposure, redone",
        "",
        f"All evidence per TIC is kept. Commit `{e['scan']['commit'][:12]}`: "
        f"{e['scan']['files']} files read, {len(e['scan']['unreadable'])} unreadable; "
        f"{e['scan']['cache_fits_names_read']} TESS FITS names read under `.cache/` outside "
        "`.cache/v056/`.",
        "",
        "- **Catalogue copy** (never exposure): " + e["rule"]["catalogue_copy"] + ".",
        "- **Record** (exposure): " + e["rule"]["record"] + ".",
        "- **Light curve** (exposure): " + e["rule"]["light_curve"] + ".",
        "",
        f"Evidence paths by class: {e['class_counts']}. Frame TICs with any evidence: "
        f"{e['tics_with_evidence']}; **exposed: {e['tics_exposed']}**.",
        "",
        "| Half / arm / disposition | Frame | Part A's flag | Exposed (redone) | After exclusion |",
        "|---|---|---|---|---|",
    ]
    for k, s in e["strata"].items():
        if s["frame"]:
            out.append(f"| {k} | {s['frame']} | {s['part_a_flag']} | {s['exposed']} | "
                       f"{s['after_exclusion']} |")  # fmt: skip
    el = doc["part_a_eligibility"]
    out += [
        "",
        "Eligibility (SPOC two-minute data, at least two predicted transits) is decided at the "
        "draw from MAST metadata. For scale, part A found "
        f"{el['planet']['eligible']} eligible of {el['planet']['checked']} checked in the planet "
        f"arm and {el['open']['eligible']} of {el['open']['checked']} in the open arm.",
        "",
        "## Limits",
        "",
        "- The light-curve evidence covers what is still under `.cache/` on this machine and the "
        "archive manifests committed in the repository (class record); files archived to the "
        "Drive and listed nowhere in the repository are not seen.",
        "- The record class is wide on purpose (plans, tests and reviews count), so the exclusion "
        "can only be larger than the use of a TIC strictly requires.",
        "",
    ]
    return "\n".join(out)


if __name__ == "__main__":
    main()
