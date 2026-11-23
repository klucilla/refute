"""v0.5.7 (exploratory): the diagnostic rerun of the pilot's two differing TOIs.

Approved by the maintainer's decision of 2026-11-23, received at 11:55 local, item 2. The exact
procedure was posted on #218 (comment 7104767892) before this ran.

**The question, and nothing more:** does the flip come from the seeding, the environment, or the
battery's nondeterminism?

**The runs:** each TOI runs four times, each in a fresh spawned process, in this order:
1. search, run 1;
2. seeded, run 1;
3. search, run 2;
4. seeded, run 2.

**The two modes:**
- **Search:** v0.5.6's runner, unchanged (``calibration/v0.5.6/part_b_run.py``, ``run_one``), with
  part B's test plan. Only its data folder points to ``.cache/v057/data``.
- **Seeded:** v0.5.7's runner, unchanged (``docs/validation/v0.5.7/seeded_run.py``, ``run_one``),
  with the same plan and the TOI's v0.5.6 record as history.

**Inputs:** the files already in ``.cache/v057/data``.
- The pixel files were deleted after the pilot, so the first run of each TOI downloads them again.
  Every run records its downloaded and reused bytes.
- The light curves and the TIC cache are reused.

**The rule, fixed before running** (per TOI; a signature is the outcome and every test's status):
- **nondeterminism:** the two runs of a mode differ from each other;
- **environment:** otherwise, if the search reruns differ from the stored v0.5.6 record;
- **seeding:** otherwise, if both modes reproduce their originals (v0.5.6 and the pilot) and differ
  from each other;
- anything else is reported as found, ``unclassified``.

**Cap:** 0.5 CPU-h; no run starts if it could pass the cap. Pinned to CPUs 8 to 31, BelowNormal
(``pinrun``), one process at a time.

**Exploratory:** never a verdict, a candidate or a disposition.

Usage (from the project root, pinned):

    diagnostic_rerun.py
"""

from __future__ import annotations

import hashlib
import importlib.metadata
import importlib.util
import json
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import get_context
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
PART_B_RUN = ROOT / "calibration/v0.5.6/part_b_run.py"
SEEDED_RUN = HERE / "seeded_run.py"
PLAN_B = ROOT / "calibration/v0.5.6/claim.yaml"
DRAW_B = ROOT / "calibration/v0.5.6/part-b-draw.json"
BUNDLE_B = ROOT / "docs/validation/v0.5.6/part-b-records.json"
PILOT = HERE / "seeded-pilot-records.json"
OUT_JSON = HERE / "diagnostic-rerun.json"
OUT_MD = HERE / "diagnostic-rerun.md"
DATA = ROOT / ".cache/v057/data"
TICS = (299799658, 274138511)
ORDER = (("search", 1), ("seeded", 1), ("search", 2), ("seeded", 2))
CAP_CPU_SECONDS = 0.5 * 3600
LABEL = "WEAKENED; does not meet D1, D2, D4, T2a"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


def environment() -> dict:
    def version(pkg: str) -> str | None:
        try:
            return importlib.metadata.version(pkg)
        except importlib.metadata.PackageNotFoundError:
            return None

    commit = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True,
                            text=True, check=True).stdout.strip()  # fmt: skip
    return {
        "git_commit": commit,
        "uv_lock_sha256": hashlib.sha256((ROOT / "uv.lock").read_bytes()).hexdigest(),
        "python": sys.version.split()[0],
        "packages": {
            p: version(p) for p in ("numpy", "scipy", "astropy", "lightkurve", "astroquery")
        },  # fmt: skip
        "runners_sha256": {
            "part_b_run.py": hashlib.sha256(PART_B_RUN.read_bytes()).hexdigest(),
            "seeded_run.py": hashlib.sha256(SEEDED_RUN.read_bytes()).hexdigest(),
        },
    }


def one_run(mode: str, target: dict, test_plan: dict, hist: dict) -> dict:
    """One run in a fresh process: v0.5.6's or v0.5.7's ``run_one``, unchanged."""
    if mode == "search":
        pb = _load("part_b_run_diag", PART_B_RUN)
        pb.DATA = DATA
        pb.LIGHTKURVE = DATA / "lightkurve"
        rec = pb.run_one(target, test_plan)
    else:
        sr = _load("seeded_run_diag", SEEDED_RUN)
        rec = sr.run_one(target, test_plan, hist)
    rec["environment"] = environment()
    return rec


def signature(rec: dict | None) -> tuple:
    if rec is None or rec.get("status") != "OK":
        return ("not OK", (rec or {}).get("status"))
    tests = tuple(sorted((n, t.get("status")) for n, t in rec.get("tests", {}).items()))
    return (rec.get("outcome"), tests)


def summary(rec: dict) -> dict:
    tests = rec.get("tests") or {}
    sysm = tests.get("systematics") or {}
    return {
        "status": rec.get("status"),
        "outcome": rec.get("outcome"),
        "candidate": rec.get("candidate"),
        "tests": {
            n: {"status": t.get("status"), "message": t.get("message")} for n, t in tests.items()
        },  # fmt: skip
        "systematics": {
            "status": sysm.get("status"),
            "sensitivity": sysm.get("sensitivity"),
            "message": sysm.get("message"),
        },  # fmt: skip
        "downloaded_bytes": rec.get("downloaded_bytes"),
        "reused_bytes": rec.get("reused_bytes"),
        "cpu_seconds": rec.get("cpu_seconds"),
        "reason": rec.get("reason"),
        "environment": rec.get("environment"),
    }


def classify(s1: dict, s2: dict, f1: dict, f2: dict, orig_s: dict, orig_f: dict) -> str:
    """The rule fixed before running. ``s1``..``f2`` are run summaries carrying ``_signature``;
    ``orig_s`` and ``orig_f`` are the stored records (v0.5.6 and the pilot)."""
    if s1["_signature"] != s2["_signature"] or f1["_signature"] != f2["_signature"]:
        return "nondeterminism"
    if s1["_signature"] != signature(orig_s):
        return "environment"
    if f1["_signature"] == signature(orig_f) and s1["_signature"] != f1["_signature"]:
        return "seeding"
    return "unclassified"


def main() -> None:
    import yaml

    sr = _load("seeded_run_parent", SEEDED_RUN)
    sr.isolate_caches()  # every cache inside .cache/v057, inherited by the spawned runs
    plan = yaml.safe_load(PLAN_B.read_text("utf-8"))["test_plan"]
    draw = json.loads(DRAW_B.read_text("utf-8"))
    chosen = {c["tic_id"]: (arm, rank, c) for arm in ("planet", "fp")
              for rank, c in enumerate(draw["arms"][arm]["chosen"])}  # fmt: skip
    orig_search = {i["content"]["tic_id"]: i["content"]
                   for i in json.loads(BUNDLE_B.read_text("utf-8"))["records"]}  # fmt: skip
    orig_seeded = {i["content"]["tic_id"]: i["content"]
                   for i in json.loads(PILOT.read_text("utf-8"))["records"]}  # fmt: skip
    spent, runs, stop = 0.0, [], None
    ctx = get_context("spawn")
    for tic in TICS:
        arm, rank, c = chosen[tic]
        target = {**c, "part": "B", "arm": arm, "rank": rank, "key": f"TIC-{tic}"}
        for mode, rep in ORDER:
            estimate = max((r["cpu_seconds"] or 0.0 for r in runs if r["tic_id"] == tic),
                           default=300.0)  # fmt: skip
            if spent + estimate > CAP_CPU_SECONDS:
                stop = f"the cap of 0.5 CPU-h would be passed before {mode} run {rep} of {tic}"
                break
            started = time.time()
            with ProcessPoolExecutor(max_workers=1, mp_context=ctx) as pool:
                rec = pool.submit(one_run, mode, target, plan, orig_search[tic]).result()
            spent += rec.get("cpu_seconds") or 0.0
            runs.append({"tic_id": tic, "toi": c["toi"], "mode": mode, "run": rep,
                         "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(started)),
                         **summary(rec), "_signature": signature(rec)})  # fmt: skip
            print(tic, mode, rep, rec.get("status"), rec.get("outcome"),
                  round(rec.get("cpu_seconds") or 0), flush=True)  # fmt: skip
        if stop:
            break
    answers = {}
    for tic in TICS:
        by = {(r["mode"], r["run"]): r for r in runs if r["tic_id"] == tic}
        if len(by) < 4:
            answers[tic] = "incomplete"
            continue
        s1, s2 = by[("search", 1)], by[("search", 2)]
        f1, f2 = by[("seeded", 1)], by[("seeded", 2)]
        os_, of = orig_search[tic], orig_seeded[tic]
        answers[tic] = {
            "answer": classify(s1, s2, f1, f2, os_, of),
            "search_runs_agree": s1["_signature"] == s2["_signature"],
            "seeded_runs_agree": f1["_signature"] == f2["_signature"],
            "search_reproduces_v056": s1["_signature"] == signature(os_),
            "seeded_reproduces_pilot": f1["_signature"] == signature(of),
            "modes_differ": s1["_signature"] != f1["_signature"],
        }
    doc = {
        "schema": "refute-v057-diagnostic-rerun-1",
        "mode": "exploratory",
        "limits_label": LABEL,
        "method_status": "not_validated",
        "question": "does the flip come from the seeding, the environment, or the battery's "
        "nondeterminism?",
        "procedure": "#218, comment 7104767892",
        "code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "cpu_seconds": spent,
        "stop": stop,
        "answers": {str(k): v for k, v in answers.items()},
        "runs": [{k: v for k, v in r.items() if k != "_signature"} for r in runs],
    }
    OUT_JSON.write_text(json.dumps(doc, indent=1) + "\n", "utf-8", newline="\n")
    OUT_MD.write_text(markdown(doc), "utf-8", newline="\n")
    print(json.dumps({"answers": doc["answers"], "cpu_seconds": round(spent), "stop": stop}))


def markdown(doc: dict) -> str:
    lines = [
        "# v0.5.7: the diagnostic rerun of the pilot's two differing TOIs (exploratory)",
        "",
        f"**Exploratory.** Limits label: '{doc['limits_label']}'. `method_status: "
        "not_validated`. Never a verdict, a candidate or a disposition.",
        "",
        f"Question: {doc['question']} Procedure: {doc['procedure']}. CPU: "
        f"{doc['cpu_seconds'] / 3600:.3f} CPU-h (cap 0.5). Stop: {doc['stop']}.",
        "",
        "| TOI | Mode | Run | Outcome | `systematics` (sensitivity) | Final period (d) | "
        "Final epoch (BTJD) | SNR | Downloaded / reused bytes |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for r in doc["runs"]:
        cand = r.get("candidate") or {}
        sysm = r["systematics"]
        lines.append(
            f"| {r['toi']} | {r['mode']} | {r['run']} | {r['outcome']} | {sysm['status']} "
            f"({sysm['sensitivity']}) | {cand.get('period_days')} | {cand.get('t0_btjd')} | "
            f"{cand.get('snr')} | {r['downloaded_bytes']} / {r['reused_bytes']} |"
        )
    lines += ["", "## Answers (the rule fixed before running)", ""]
    for tic, a in doc["answers"].items():
        lines.append(f"- TIC {tic}: " + (a if isinstance(a, str) else json.dumps(a)))
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    main()
