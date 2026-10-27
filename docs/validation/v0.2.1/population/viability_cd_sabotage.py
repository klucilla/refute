"""The sabotages of the C/D viability package's code (acceptance record
``viability-cd-acceptance.md``, section 9).

Each sabotage replaces one literal piece of a module (it must occur exactly once), runs the
matching tests of ``tests/test_viability_cd.py`` through ``scripts/run_tests_affinity.ps1`` with a
JUnit file, and writes the module's original bytes back; it is caught when at least one matching
test fails, the same tests passed on the unmutated code just before (the control), and the file is
afterwards byte for byte what it was and what the index holds (``git diff --quiet``). Never run at
the same time as a full suite.

``python viability_cd_sabotage.py --work DIR --out FILE`` runs S1 to S17 one after the other.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
VC = "docs/validation/v0.2.1/population/viability_cd.py"
EV = "docs/validation/v0.2.1/population/viability_cd_evaluate.py"
TESTS = "tests/test_viability_cd.py"

# (id, criterion, file, literal, replacement, the matching tests' -k expression)
SABOTAGES = (
    ("S1", "G4", VC, "SPAN_DAYS = (25.5, 30.0)", "SPAN_DAYS = (25.0, 30.0)", "g2_to_g4"),
    (
        "S2", "G5", VC,
        "        for t in tics:  # in TIC order",
        "        for t in reversed(tics):  # in TIC order",
        "g5_",
    ),
    (
        "S3", "G6", VC,
        "selected = [ordered[int(i)] for i in perm][: N_SELECTED[a]]",
        "selected = ordered[: N_SELECTED[a]]",
        "g6_",
    ),
    (
        "S4", "K3", VC,
        'text = f"{seed_root}/{alternative}/{NOISE_TAGS[noise]}/{regime}/{int(i)}"',
        'text = f"{seed_root}/{alternative}/{NOISE_TAGS[noise]}/{int(i)}"',
        "test_k_",
    ),
    (
        "S5", "K4", VC,
        "regime, i, i % n_geometries))",
        "regime, i, i % max(1, n_geometries - 1)))",
        "test_k_",
    ),
    ("S6", "L2", VC, "DELTA_DAYS = (-0.5, 0.5)", "DELTA_DAYS = (-1.0, 1.0)", "test_l_a_layout"),
    (
        "S7", "L3", VC,
        '    if not result.conditions["D4"]:',
        '    if False and not result.conditions["D4"]:',
        "test_l_redraws",
    ),
    (
        "S8", "P2", VC,
        'p["var_absent_year"] = int(distinct[position])',
        'p["var_absent_year"] = int(labels[position])',
        "test_p2_",
    ),
    (
        "S9", "R4", VC,
        "base = (np.abs(dt) >= t14) & (np.abs(dt) <= 3.0 * t14)",
        "base = (np.abs(dt) >= 0.5 * t14) & (np.abs(dt) <= 3.0 * t14)",
        "test_r4_",
    ),
    ("S10", "R3", VC, "IDENTITY_TOLERANCE = 0.01", "IDENTITY_TOLERANCE = 0.10", "test_r3_"),
    (
        "S11", "X2", VC,
        '        geometry = geometries[c["extra"]["geometry"]]\n        if not path.exists():',
        '        geometry = geometries[c["extra"]["geometry"]]\n        if True:',
        "test_x_a_",
    ),
    (
        "S12", "X5", VC,
        '"projected_lp_hours": m * n_tasks / 3600.0',
        '"projected_lp_hours": m / 3600.0',
        "test_x5_",
    ),
    (
        "S13", "E2", EV,
        '"insufficient_capacity_hidden_noise": 13,',
        '"insufficient_capacity_hidden_noise": 12,',
        "test_e1_",
    ),
    (
        "S14", "E3", EV,
        '"R2-K": frozenset({6, 10, 11}),',
        '"R2-K": frozenset({6, 10, 11, 12}),',
        "test_e1_ or test_e2_every",
    ),
    (
        "S15", "E6", EV,
        "return pv2.cp_lower(n_pass, n) >= BENCHMARK and",
        "return n_pass / n >= BENCHMARK and",
        "test_e5_",
    ),
    (
        "S16", "E8", EV,
        "var = float(v[grid.index(0.0)])",
        "var = float(np.max(v))",
        "test_e8_the_candidate",
    ),
    ("S17", "E9", EV, 'out["ends"] = True', 'out["ends"] = False', "test_e9_"),
)  # fmt: skip


def junit_counts(path: Path) -> dict:
    root = ET.parse(path).getroot()
    suites = [root] if root.tag == "testsuite" else list(root)
    out = {"tests": 0, "failures": 0, "errors": 0, "skipped": 0, "failed": []}
    for s in suites:
        for k in ("tests", "failures", "errors", "skipped"):
            out[k] += int(s.get(k) or 0)
        for case in s.iter("testcase"):
            if case.find("failure") is not None or case.find("error") is not None:
                out["failed"].append(case.get("name"))
    return out


def run_tests(work: Path, name: str, k: str) -> dict:
    junit = work / f"{name}.xml"
    subprocess.run(
        [
            "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
            str(REPO / "scripts" / "run_tests_affinity.ps1"),
            "-Junit", str(junit), "-Tests", TESTS, "-K", k,
        ],
        cwd=REPO,
        check=False,
        capture_output=True,
        text=True,
    )  # fmt: skip
    if not junit.exists():
        return {"tests": 0, "failures": 0, "errors": 1, "skipped": 0, "failed": ["no JUnit file"]}
    return junit_counts(junit)


def index_clean(rel: str) -> bool:
    return subprocess.run(["git", "diff", "--quiet", "--", rel], cwd=REPO).returncode == 0


def one(sid, criterion, rel, literal, replacement, k, work: Path) -> dict:
    path = REPO / rel
    original = path.read_bytes()
    text = original.decode("utf-8")
    if text.count(literal) != 1 or not index_clean(rel):
        return {
            "id": sid,
            "caught": False,
            "error": "the literal is not unique or the file is dirty",
        }
    control = run_tests(work, f"{sid}-control", k)
    try:
        path.write_bytes(text.replace(literal, replacement).encode("utf-8"))
        sabotaged = run_tests(work, f"{sid}-sabotaged", k)
    finally:
        path.write_bytes(original)
    restored = hashlib.sha256(path.read_bytes()).hexdigest() == hashlib.sha256(
        original
    ).hexdigest() and index_clean(rel)
    control_ok = control["tests"] > 0 and not control["failures"] and not control["errors"]
    failed = sabotaged["failures"] + sabotaged["errors"]
    return {
        "id": sid,
        "criterion": criterion,
        "file": rel,
        "tests": k,
        "control": control,
        "sabotaged": sabotaged,
        "restored": restored,
        "caught": bool(control_ok and failed > 0 and restored),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--work", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    work = Path(args.work)
    work.mkdir(parents=True, exist_ok=True)
    results = []
    for s in SABOTAGES:
        results.append(one(*s, work))
        print(s[0], results[-1]["caught"], flush=True)
    out = {
        "format": "refute-v0.2.1-viability-cd-sabotages/1",
        "all_caught": all(r["caught"] for r in results),
        "sabotages": results,
    }
    with open(args.out, "x", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(out, indent=1, sort_keys=True) + "\n")
    return 0 if out["all_caught"] else 1


if __name__ == "__main__":
    sys.exit(main())
