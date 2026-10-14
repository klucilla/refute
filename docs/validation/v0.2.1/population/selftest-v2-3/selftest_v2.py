"""Third self-test of the population harness v2, after the corrections of the second code
review (Amendment 4, clarifications of 2026-10-13); not a measurement.

Every step runs ``population_v2.py`` (and, for the overhead, ``population.py``) as separate
processes in diagnostic campaigns under ``.cache/population/v2-selftest-3/campaigns``
(never the default campaigns root), and appends every command and its output to
``selftest-v2-log.txt`` next to this file. The populations are ``selftest`` (prefix
``refute-v0.2.1-population-selftest``) and ``determinism`` (prefix
``refute-v0.2.1-population-determinism``); no development case is generated or analyzed.

Usage (with the Python of the repository's virtual environment, affinity 8 to 31):
  selftest_v2.py <step>   step: declare | reference | overhead | determinism | inject |
                          lock | analysis | records | d6smoke | blockers | summary
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import shutil
import struct
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
POP = HERE.parent
REPO = POP.parents[3]
sys.path.insert(0, str(POP))
import population_v2 as v2  # noqa: E402

CMP = v2.CMP
V1 = POP / "population.py"
V2 = POP / "population_v2.py"
# V2_SELFTEST_WORK (development runs only): another work folder, with the log inside it.
WORK = Path(os.environ.get("V2_SELFTEST_WORK") or REPO / ".cache" / "population" / "v2-selftest-3")
QUALIFICATION = REPO / ".cache" / "population" / "diag" / "qualificacao" / "qualificacao.json"
ROOT = WORK / "campaigns"
LOG = WORK / "dev-log.txt" if os.environ.get("V2_SELFTEST_WORK") else HERE / "selftest-v2-log.txt"
PLANTED = b"not the bytes of the case\n"
GEN_PY = Path(r"C:\Projetos\refute\.worktrees\v0.2.0\.venv\Scripts\python.exe")
POINT_PY = {
    "M0": GEN_PY,
    "M3": Path(r"C:\Projetos\refute\.worktrees\M3-9d3f369\.venv\Scripts\python.exe"),
}
CPUS = "8-31"
REFERENCE = {
    "planet-measurable-white-0000": (
        "f3951b9e85d21ea8cbc42a23074ad5b442498d049bfbb51896c6277c85192c4e"
    ),
    "planet-measurable-correlated-0000": (
        "a7dd6266f4ffd30f3cead01987a301c64db2086791a7296e0db55f3f416055c4"
    ),
    "false_positive-measurable-white-0004": (
        "1817b9f776969ae050ba6cd7b1849dda968595041dabe37711390cec7b37b724"
    ),
}
# Cases of the analysis step: the mechanisms that diverged in the v1 generations (planets
# below threshold with white noise, two and three years; no transit with trend and
# variability, white noise) and a blend.
ANALYSIS_CASES = [
    "planet-below-white-0000",
    "planet-below-white-0111",
    "no_transit-none-white-1544",
    "false_positive-measurable-white-0133",
]


def _masked(text: str) -> str:
    """The text with the Windows user name replaced by <user> (it is never logged)."""
    name = os.environ.get("USERNAME", "")
    return text.replace(name, "<user>") if len(name) >= 3 else text


def log(text: str) -> None:
    text = _masked(text)
    WORK.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(text.rstrip("\n") + "\n")
    print(text, flush=True)


def run(cmd: list, *, expect: int | None = 0, label: str = "") -> tuple[int, str, float]:
    """Run a command, log it and its output, and return (code, output, wall seconds)."""
    shown = " ".join(str(c).replace(str(REPO), "<repo>") for c in cmd)
    log(f"$ {label + ': ' if label else ''}{shown}")
    t0 = time.perf_counter()
    res = subprocess.run([str(c) for c in cmd], capture_output=True, text=True, encoding="utf-8")
    wall = time.perf_counter() - t0
    out = (res.stdout + res.stderr).replace(str(REPO), "<repo>")
    for line in out.splitlines()[-60:]:
        log(f"  {line}")
    log(f"  [exit {res.returncode}, wall {wall:.1f} s]")
    if expect is not None and res.returncode != expect:
        raise SystemExit(f"unexpected exit {res.returncode} (expected {expect}): {shown}")
    return res.returncode, out, wall


def dispatch_table(python: Path) -> dict:
    out = WORK / f"dispatch-{python.parents[2].name}.json"
    if not out.exists():
        run([python, V2, "dispatch-table", "--out", out, "--cpus", CPUS])
    return json.loads(out.read_bytes())


def declaration(cid: str, population: str, cases: list[str] | None, configs: list[dict], **kw):
    table = dispatch_table(GEN_PY)
    ids = [c["id"] for c in v2.population_cases(population)]
    if cases is not None:
        keep = set(cases)
        if keep - set(ids):
            raise SystemExit(f"cases not in the population: {sorted(keep - set(ids))}")
        ids = [i for i in ids if i in keep]
    qual = REPO / ".cache" / "population" / "diag" / "qualificacao" / "qualificacao.md"
    slots = {}
    for s, order in (("1", "shuffle:11"), ("2", "shuffle:22")):
        slots[s] = {"order": order, "order_sha256": v2.order_sha256(v2._ordered(ids, order))}
    decl = {
        "format": v2.DECLARATION_FORMAT,
        "campaign_id": cid,
        "eligibility": "diagnostic",
        "chain": "development",
        "predecessor": {"note": "self-test campaign: no predecessor; consumes no set of any chain"},
        "chain_sets_consumed_before": 0,
        "population": population,
        "harness_sha256": v2.HARNESS_SHA256,
        "comparator": CMP.identity(),
        "budget": {"K": 3, "N": 3, "chain_ceiling": 6},
        "generation_configurations": configs,
        "dispatch": {
            "environment": table["environment"],
            "target": sorted({t for sigs in table["table"].values() for t in sigs.values() if t}),
            "table": table["table"],
        },
        "analysis": {"workers": 24, "lot_size": kw.get("lot_size", 50), "slots": slots},
        "reference_manifest": None,
        "rules": {
            "investigation": "self-test: no investigation; every lock is expected",
            "resolution": [
                {"id": "selftest-simulated", "text": "a lock written on purpose by the self-test"}
            ],
        },
        "overhead": {"double_hash": True},
        "affinity": CPUS,
        "qualification": {
            "record": ".cache/population/diag/qualificacao/qualificacao.md",
            "sha256": v2.file_sha256(qual),
            "result": "PASS, under the conditions recorded there",
        },
        "machine_declared": {
            "memory": "4 x 16 GiB, 2666 MHz, 1.20 V (daily configuration)",
            "badmemorylist": "physical page 0x8C7CBD excluded (maintainer's record)",
            "bios_cpu_settings": "not recorded",
            "easytune_profile": "not recorded",
        },
    }
    if cases is not None:
        decl["cases"] = ids
    folder = ROOT / cid
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / "declaration.json"
    if path.exists():
        log(f"declaration {cid} exists (SHA-256 {v2.file_sha256(path)}); kept")
        return
    sha = v2.write_json(path, decl)
    log(f"declaration {cid}: {len(ids)} cases, SHA-256 {sha}")


def harness(python: Path, mode: str, cid: str, *args, expect: int | None = 0, label=""):
    return run(
        [python, V2, mode, "--root", ROOT, "--campaign", cid, *args, "--cpus", CPUS],
        expect=expect,
        label=label,
    )


def step_declare() -> None:
    WORK.mkdir(parents=True, exist_ok=True)
    log(f"# declare {datetime.now(UTC).isoformat(timespec='seconds')}")
    log(f"harness population_v2.py SHA-256 {v2.HARNESS_SHA256}")
    log(f"comparator population_compare.py SHA-256 {CMP.COMPARATOR_SHA256}")
    for prof in ("slots", "d6-science", "d6-control"):
        log(f"profile {prof}: SHA-256 {CMP.profile_sha256(prof)}")
    m3 = dispatch_table(POINT_PY["M3"])
    gen = dispatch_table(GEN_PY)
    log(f"dispatch table v0.2.0 {gen['sha256']}, M3 {m3['sha256']} (equal: {gen == m3})")
    declaration(
        "v2-selftest-reference",
        "selftest",
        list(REFERENCE),
        [
            {"workers": 1, "order": "index"},
            {"workers": 2, "order": "reverse"},
            {"workers": 3, "order": "shuffle:7"},
        ],
    )
    declaration(
        "v2-selftest-determinism",
        "determinism",
        None,
        [
            {"workers": 24, "order": "index"},
            {"workers": 12, "order": "shuffle:20261013"},
            {"workers": 24, "order": "shuffle:31"},
        ],
    )
    declaration(
        "v2-selftest-overhead", "determinism", None, [{"workers": 24, "order": "index"}] * 3
    )
    declaration(
        "v2-selftest-lock",
        "selftest",
        ["planet-measurable-white-0000", "no_transit-none-white-0000"],
        [{"workers": 2, "order": "index"}] * 3,
    )
    declaration(
        "v2-selftest-interrupt",
        "selftest",
        [
            "planet-measurable-white-0000",
            "planet-measurable-white-0002",
            "planet-measurable-white-0004",
        ],
        [{"workers": 1, "order": "index"}] * 3,
    )
    for cid in ("v2-selftest-concurrent", "v2-selftest-workerlock", "v2-selftest-cmpdamage"):
        declaration(
            cid,
            "selftest",
            ["planet-measurable-white-0000", "no_transit-none-white-0000"],
            [{"workers": 2, "order": "index"}] * 3,
        )
    declaration(
        "v2-selftest-analysis",
        "determinism",
        ANALYSIS_CASES,
        [{"workers": 4, "order": "index"}] * 3,
        lot_size=2,
    )


def step_reference() -> None:
    cid = "v2-selftest-reference"
    log(f"# reference cases {datetime.now(UTC).isoformat(timespec='seconds')}")
    out = WORK / "out" / cid
    cache = WORK / "cache-reference"
    harness(
        GEN_PY, "generate", cid, "--set", "1", "--generation", "1", "--out", out, "--cache", cache
    )
    for g in (2, 3):
        harness(GEN_PY, "generate", cid, "--set", "1", "--generation", str(g), "--out", out)
    harness(GEN_PY, "check-set", cid, "--set", "1")
    manifest = json.loads((out / "manifest-set1-gen1.json").read_bytes())
    for e in manifest["cases"]:
        ok = REFERENCE[e["id"]] == e["sha256"]
        log(f"reference {e['id']}: {e['sha256']} {'EXPECTED' if ok else 'DIFFERS'}")
        stored = cache / f"{e['id']}.rpc"
        log(f"  stored file SHA-256 {v2.file_sha256(stored)} ({stored.stat().st_size} bytes)")
        if not ok:
            raise SystemExit("a reference case differs")


def _v1_ids() -> Path:
    path = WORK / "determinism-ids.txt"
    if not path.exists():
        ids = [c["id"] for c in v2.population_cases("determinism")]
        path.write_text("\n".join(ids) + "\n", encoding="utf-8")
    return path


def step_overhead() -> None:
    """Section 4: six runs alternating v1 and v2, each a new process, hash only, 24 workers,
    index order, on the 520 cases of the measurement population. Overhead =
    median(v2) / median(v1) - 1, from the wall time of each process (start to exit)."""
    cid = "v2-selftest-overhead"
    log(f"# overhead {datetime.now(UTC).isoformat(timespec='seconds')}")
    ids = _v1_ids()
    out = WORK / "out" / cid
    out.mkdir(parents=True, exist_ok=True)
    walls = {"v1": [], "v2": []}
    for k in (1, 2, 3):
        v1_manifest = out / f"v1-run{k}.json"
        _, _, w1 = run(
            [
                GEN_PY,
                V1,
                "generate",
                "--population",
                "confirm:" + v2.DETERMINISM_PREFIX,
                "--cases-from",
                ids,
                "--cache",
                WORK / "cache-v1-hash-only",
                "--no-store",
                "--manifest",
                v1_manifest,
                "--workers",
                "24",
                "--order",
                "index",
                "--cpus",
                CPUS,
            ],
            label=f"v1 run {k}",
        )
        walls["v1"].append(w1)
        _, _, w2 = harness(
            GEN_PY,
            "generate",
            cid,
            "--set",
            "1",
            "--generation",
            str(k),
            "--out",
            out,
            label=f"v2 run {k}",
        )
        walls["v2"].append(w2)
    harness(GEN_PY, "check-set", cid, "--set", "1")
    med = {k: sorted(v)[1] for k, v in walls.items()}
    overhead = med["v2"] / med["v1"] - 1
    log(
        f"overhead walls v1 {[round(x, 1) for x in walls['v1']]} "
        f"v2 {[round(x, 1) for x in walls['v2']]}"
    )
    log(
        f"overhead = median(v2) / median(v1) - 1 = {med['v2']:.1f} / {med['v1']:.1f} - 1 = "
        f"{overhead * 100:.1f} % (limit 25 %, accepted up to 20 %): "
        f"{'ACCEPTED' if overhead <= 0.20 else 'ABOVE THE MARGIN'}"
    )
    v2m = json.loads((out / "manifest-set1-gen1.json").read_bytes())
    v2sha = {e["id"]: e["sha256"] for e in v2m["cases"]}
    for k in (1, 2, 3):
        v1m = json.loads((out / f"v1-run{k}.json").read_bytes())
        same = sum(v2sha.get(e["id"]) == e["sha256"] for e in v1m["cases"])
        log(f"v1 run {k}: {same} of {len(v1m['cases'])} case SHA-256 equal to v2 (of {len(v2sha)})")
    (out / "overhead.json").write_text(
        json.dumps({"walls": walls, "medians": med, "overhead": overhead}, indent=1),
        encoding="utf-8",
    )


def step_determinism() -> None:
    cid = "v2-selftest-determinism"
    log(f"# determinism {datetime.now(UTC).isoformat(timespec='seconds')}")
    out = WORK / "out" / cid
    for g in (1, 2, 3):
        harness(GEN_PY, "generate", cid, "--set", "1", "--generation", str(g), "--out", out)
    harness(GEN_PY, "check-set", cid, "--set", "1")
    m = json.loads((out / "manifest-set1-gen1.json").read_bytes())
    b = json.loads((out / "blocks-set1-gen1.json").read_bytes())
    log(
        f"determinism: {len(m['cases'])} cases; segments "
        f"{sum(len(e['layout']['segments']) for e in m['cases'])}; blocks "
        f"{sum(len(x) for c in b['cases'].values() for x in c.values())}; manifests and block "
        "indexes of the three generations byte-identical (check-set accepted)"
    )
    for name in (
        "planet-below-white-0000",
        "planet-below-white-0111",
        "no_transit-none-white-1544",
    ):
        e = next(x for x in m["cases"] if x["id"] == name)
        log(f"  {name}: mechanism {e['mechanism']}, SHA-256 {e['sha256']}")


# --- injected differences ----------------------------------------------------------------


def _segment(entry_layout: dict, name: str) -> dict:
    return next(s for s in entry_layout["segments"] if s["name"] == name)


def _set_f8(blob: bytearray, offset: int, bits: int) -> None:
    blob[offset : offset + 8] = struct.pack("<Q", bits)


def step_inject() -> None:
    log(f"# injected differences {datetime.now(UTC).isoformat(timespec='seconds')}")
    cache = WORK / "cache-reference"
    original = (cache / "planet-measurable-white-0000.rpc").read_bytes()
    _, layout, blocks, problems = v2.case_hashes(original)
    assert not problems
    results = []

    def check(label: str, a: bytes, b: bytes, expect: dict) -> None:
        rep = CMP.compare_blobs(a, b)
        _, la, ba, _ = v2.case_hashes(a)
        _, lb, bb, _ = v2.case_hashes(b)
        loc = CMP.locate_without_bytes(
            {"sha256": "a", "layout": la}, {"sha256": "b", "layout": lb}, ba, bb
        )
        ok = rep["status"] == expect["status"]
        detail = {}
        if expect["status"] == "bytes":
            s = rep["segments"][0]
            ok = ok and len(rep["segments"]) == 1 and s["segment"] == expect["segment"]
            ok = (
                ok
                and s["first_differing_offset"] == expect["offset"]
                and s["block"] == expect["block"]
            )
            if "element" in expect:
                ok = ok and s["first_element"] == expect["element"] and s["elements_differing"] == 1
            if "kind" in expect:
                ok = ok and s["explanation"]["by_kind"] == {expect["kind"]: 1}
            if "header_path" in expect:
                ok = ok and any(d["path"] == expect["header_path"] for d in s["header_paths"])
            ok_loc = loc["status"] == "blocks" and len(loc["segments"]) == 1
            ok_loc = ok_loc and loc["segments"][0]["segment"] == expect["segment"]
            ok_loc = ok_loc and [x["block"] for x in loc["segments"][0]["blocks"]] == [
                expect["block"]
            ]
            detail = {
                "segment": s["segment"],
                "offset": s["first_differing_offset"],
                "block": s["block"],
                "element": s.get("first_element"),
                "explanation": s.get("explanation"),
                "header_paths": [d["path"] for d in s.get("header_paths", [])][:3],
                "without_bytes": [
                    (x["segment"], [y["block"] for y in x["blocks"]]) for x in loc["segments"]
                ],
            }
        else:
            ok_loc = loc["status"] == "structural"
            detail = {"structure": rep.get("structure"), "without_bytes": loc["status"]}
        results.append(
            {
                "label": label,
                "located_with_bytes": ok,
                "located_without_bytes": ok_loc,
                "detail": detail,
            }
        )
        log(
            f"{label}: with bytes {'OK' if ok else 'WRONG'}; without bytes "
            f"{'OK' if ok_loc else 'WRONG'}; {json.dumps(detail)[:400]}"
        )

    seg = _segment(layout, "aux/pixels/1/flux")
    e = 1_500_000  # an element in block 11 of the segment
    if e >= seg["length"] // 8:
        raise SystemExit("the element is outside the segment")
    off = seg["offset"] + e * 8 + 3
    b = bytearray(original)
    b[off] ^= 0x10
    shape = seg["shape"]
    element = [e // (shape[1] * shape[2]), (e // shape[2]) % shape[1], e % shape[2]]
    check(
        "one byte of an array",
        original,
        bytes(b),
        {
            "status": "bytes",
            "segment": "aux/pixels/1/flux",
            "offset": off,
            "block": (e * 8 + 3) // v2.BLOCK_SIZE,
            "element": element,
        },
    )
    seg = _segment(layout, "aux/sectors/0/sap_bkg")
    e = 100
    off = seg["offset"] + e * 8
    a, b = bytearray(original), bytearray(original)
    _set_f8(a, off, 0x0000000000000000)
    _set_f8(b, off, 0x8000000000000000)
    check(
        "the sign of one zero",
        bytes(a),
        bytes(b),
        {
            "status": "bytes",
            "segment": "aux/sectors/0/sap_bkg",
            "offset": off + 7,
            "block": (e * 8) // v2.BLOCK_SIZE,
            "element": [e],
            "kind": "sign_of_zero",
        },
    )
    seg = _segment(layout, "lc/flux_err")
    e = 7
    off = seg["offset"] + e * 8
    a, b = bytearray(original), bytearray(original)
    _set_f8(a, off, 0x7FF8000000000001)
    _set_f8(b, off, 0x7FF8000000000002)
    check(
        "the payload of one NaN",
        bytes(a),
        bytes(b),
        {
            "status": "bytes",
            "segment": "lc/flux_err",
            "offset": off,
            "block": 0,
            "element": [e],
            "kind": "nan_payload",
        },
    )
    seg = _segment(layout, "header")
    head = original[seg["offset"] : seg["offset"] + seg["length"]]
    key = b'"attempt_seed":"'
    pos = head.index(key) + len(key)
    digit = head[pos : pos + 1]
    new = b"1" if digit != b"1" else b"2"
    b = bytearray(original)
    b[seg["offset"] + pos] = new[0]
    check(
        "one header field",
        original,
        bytes(b),
        {
            "status": "bytes",
            "segment": "header",
            "offset": seg["offset"] + pos,
            "block": pos // v2.BLOCK_SIZE,
            "header_path": "/attempt_seed",
        },
    )
    meta, arrays = v2.deserialize(original)
    names = [a[0] for a in meta["arrays"]]
    dtypes = {a[0]: a[1] for a in meta["arrays"]}
    arrays["lc/time"] = arrays["lc/time"][:-1]
    base = {k: v for k, v in meta.items() if k != "arrays"}
    changed = v2.serialize(base, [(n, arrays[n], dtypes[n]) for n in names])
    check("a structural change (another shape)", original, changed, {"status": "structural"})
    (WORK / "inject").mkdir(parents=True, exist_ok=True)
    (WORK / "inject" / "blob-results.json").write_text(
        json.dumps(results, indent=1), encoding="utf-8"
    )
    bad = [
        r["label"] for r in results if not (r["located_with_bytes"] and r["located_without_bytes"])
    ]
    log(
        f"blob injections: {len(results) - len(bad)} of {len(results)} located as expected "
        f"{bad or ''}"
    )


def _first_float_path(rec: dict, prefix: str) -> str:
    for path, item in CMP.flatten(rec).items():
        if path.startswith(prefix) and item[0] == "float" and item[2] not in ("nan", "inf", "-inf"):
            return path
    raise SystemExit(f"no float under {prefix}")


def _get(rec, path):
    for part in path.split("/")[1:]:
        part = part.replace("~1", "/").replace("~0", "~")
        rec = rec[int(part)] if isinstance(rec, list) else rec[part]
    return rec


def step_records() -> None:
    """Result-record injections, on copies of a real slot-1 record of the analysis step."""
    log(f"# result-record injections {datetime.now(UTC).isoformat(timespec='seconds')}")
    run1 = WORK / "runs" / "M3-slot1" / "cases" / "planet-below-white-0000.json"
    run2 = WORK / "runs" / "M3-slot2" / "cases" / "planet-below-white-0000.json"
    r1, r2 = json.loads(run1.read_bytes()), json.loads(run2.read_bytes())
    rep = CMP.compare_records(r1, r2, "slots")
    log(
        f"real slot 1 vs slot 2 (profile slots): {rep['status']}, "
        f"{rep['counts']['differences']} differences"
    )
    results = []

    def check(label, a, b, status, path, kind=None):
        rep = CMP.compare_records(a, b, "slots")
        paths = [d["path"] for d in rep["differences"]]
        ok = rep["status"] == status
        if status == "divergent":
            ok = ok and paths == [path] and (kind is None or rep["differences"][0]["kind"] == kind)
        else:
            ok = ok and any(path in p for p in rep["problems"])
        results.append(
            {
                "label": label,
                "ok": ok,
                "status": rep["status"],
                "paths": paths,
                "problems": rep["problems"][:3],
            }
        )
        log(
            f"{label}: {'OK' if ok else 'WRONG'} (status {rep['status']}, paths {paths[:3]}, "
            f"problems {rep['problems'][:2]})"
        )

    path = _first_float_path(r1, "/conditions/i/scientific/tests")
    x = copy.deepcopy(r1)
    val = _get(x, path)
    bits = int(val["f64"], 16) + 1
    val["f64"] = f"{bits:016x}"
    val["dec"] = repr(struct.unpack(">d", bits.to_bytes(8, "big"))[0])
    check("one metric value (one ULP)", r1, x, "divergent", path, "value")
    x = copy.deepcopy(r1)
    del x["conditions"]["i"]["scientific"]["verdict_reason"]
    check(
        "a missing field",
        r1,
        x,
        "divergent",
        "/conditions/i/scientific/verdict_reason",
        "only_in_left",
    )
    x = copy.deepcopy(r1)
    x["conditions"]["i"]["scientific"]["extra_field"] = 1
    check(
        "an extra field",
        r1,
        x,
        "divergent",
        "/conditions/i/scientific/extra_field",
        "only_in_right",
    )
    x = copy.deepcopy(r1)
    val = _get(x, path)
    val["dec"] = repr(float(val["dec"]) * 2 + 1)
    check("a float whose dec and f64 disagree", r1, x, "invalid", path)
    x = copy.deepcopy(r1)
    x["control"] = {"cases_before_in_process": 0}
    rep = CMP.compare_records(r1, x, "slots")
    ok = rep["status"] == "invalid" and any("/control" in p for p in rep["problems"])
    results.append(
        {"label": "a /control section under the profile slots", "ok": ok, "status": rep["status"]}
    )
    log(f"a /control section under the profile slots: {'OK' if ok else 'WRONG'} ({rep['status']})")
    x = copy.deepcopy(r1)
    x["operational"]["pid"] = 1
    x["identity"]["execution_id"] = "other"
    rep = CMP.compare_records(r1, x, "slots")
    ok = rep["status"] == "identical"
    results.append(
        {"label": "excluded paths only (pid, execution id)", "ok": ok, "status": rep["status"]}
    )
    log(f"excluded paths only (pid, execution id): {'OK' if ok else 'WRONG'} ({rep['status']})")
    (WORK / "inject").mkdir(parents=True, exist_ok=True)
    (WORK / "inject" / "record-results.json").write_text(
        json.dumps(results, indent=1), encoding="utf-8"
    )
    bad = [r["label"] for r in results if not r["ok"]]
    log(f"record injections: {len(results) - len(bad)} of {len(results)} as expected {bad or ''}")


def step_lock() -> None:
    """A divergence simulated through the cache rule (a different file already at a case's
    path): the lock marker and the journal entry are written, every campaign mode then
    refuses, also with another output directory; assembled copies show that a missing
    marker does not unblock, that a resolution with a registered rule does, and that an
    execution without a closure blocks until it is reconciled."""
    cid = "v2-selftest-lock"
    log(f"# journal and lock {datetime.now(UTC).isoformat(timespec='seconds')}")
    out = WORK / "out" / cid
    cache = WORK / "cache-lock"
    cache.mkdir(parents=True, exist_ok=True)
    planted = cache / "planet-measurable-white-0000.rpc"
    if not planted.exists():
        planted.write_bytes(PLANTED)
    harness(
        GEN_PY,
        "generate",
        cid,
        "--set",
        "1",
        "--generation",
        "1",
        "--out",
        out,
        "--cache",
        cache,
        expect=2,
    )
    log(f"planted file untouched: {planted.read_bytes() == PLANTED}")
    side = sorted(p.name for p in cache.glob("planet-measurable-white-0000.*.rpc"))
    log(f"new bytes written beside it: {side}")
    camp_dir = ROOT / cid
    log(f"lock markers: {sorted(p.name for p in (camp_dir / 'locks').glob('*.json'))}")
    other = WORK / "out" / f"{cid}-other-dir"
    harness(
        GEN_PY,
        "generate",
        cid,
        "--set",
        "1",
        "--generation",
        "2",
        "--out",
        other,
        expect=1,
        label="refusal (another directory)",
    )
    harness(GEN_PY, "check-set", cid, "--set", "1", expect=1, label="refusal")
    harness(
        GEN_PY,
        "regenerate",
        cid,
        "--manifest",
        out / "none.json",
        "--cache",
        cache,
        "--lot",
        "0",
        expect=1,
        label="refusal",
    )
    harness(
        POINT_PY["M3"],
        "analyze",
        cid,
        "--manifest",
        out / "none.json",
        "--cache",
        cache,
        "--out",
        other,
        "--point",
        "M3",
        "--lot",
        "0",
        "--slot",
        "1",
        expect=1,
        label="refusal",
    )
    harness(
        GEN_PY,
        "compare-slots",
        cid,
        "--manifest",
        out / "none.json",
        "--point",
        "M3",
        "--lot",
        "0",
        "--runs",
        other,
        other,
        "--records",
        other,
        expect=1,
        label="refusal",
    )
    harness(
        GEN_PY,
        "orchestrate",
        cid,
        "--manifest",
        out / "none.json",
        "--project",
        REPO,
        "--cache",
        cache,
        "--generator-python",
        GEN_PY,
        "--point",
        f"M3={POINT_PY['M3']}={other}",
        "--records",
        other,
        expect=1,
        label="refusal",
    )
    harness(GEN_PY, "metrics", cid, "--out", other / "metrics.json", expect=1, label="refusal")
    report = out / "integrity-report.json"
    if not report.exists():
        harness(
            GEN_PY,
            "metrics",
            cid,
            "--integrity-report",
            "--out",
            report,
            label="integrity-failure report",
        )
    rep = json.loads(report.read_bytes())
    log(
        f"integrity report approval: {rep['approval']}; locks {len(rep['locks'])}; "
        f"divergences {len(rep['divergences'])}"
    )
    # Assembled states (copies only; nothing is deleted).
    states = WORK / "lock-states"
    for state in ("no-marker", "resolved", "unclosed"):
        root = states / state
        target = root / cid
        if target.exists():
            continue
        shutil.copytree(
            camp_dir,
            target,
            ignore=shutil.ignore_patterns(
                "journal.lock", *(["lock-*.json"] if state == "no-marker" else [])
            ),
        )
    lock_file = sorted((camp_dir / "locks").glob("lock-*.json"))[0]
    resolution = states / "resolved" / cid / "resolutions" / "resolution-selftest.json"
    if not resolution.exists():
        resolution.parent.mkdir(parents=True, exist_ok=True)
        v2.write_json(
            resolution,
            {
                "format": v2.RESOLUTION_FORMAT,
                "campaign_id": cid,
                "lock_sha256": v2.file_sha256(lock_file),
                "rule": "selftest-simulated",
                "text": "self-test: the lock was written on purpose",
            },
        )
    unclosed = states / "unclosed" / cid
    resolution2 = unclosed / "resolutions" / "resolution-selftest.json"
    if not resolution2.exists():
        resolution2.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(resolution, resolution2)
        entries, _ = v2.read_journal(v2.Campaign(states / "unclosed", cid, False))
        last = entries[-1]
        ident = dict(entries[0]["identity"])
        ident["execution_id"] = "selftest-assembled-unclosed"
        line = {
            "format": v2.JOURNAL_FORMAT,
            "seq": len(entries),
            "prev_sha256": last["_sha256"],
            "utc": v2.utc_now(),
            "kind": "started",
            "identity": ident,
            "payload": {"main_pid": 999999, "assembled": True},
        }
        with open(unclosed / "journal.jsonl", "ab") as fh:
            fh.write(v2.canonical_json(line) + b"\n")
    for state in ("no-marker", "resolved", "unclosed"):
        root = states / state
        code, outp, _ = run(
            [GEN_PY, V2, "status", "--root", root, "--campaign", cid, "--cpus", CPUS],
            label=f"status {state}",
        )
        blocking = json.loads(outp[outp.index("{") :])["blocking"]
        log(f"state {state}: blocking {len(blocking)} {blocking[:3]}")
    run(
        [
            GEN_PY,
            V2,
            "reconcile",
            "--root",
            states / "unclosed",
            "--campaign",
            cid,
            "--execution-id",
            "selftest-assembled-unclosed",
            "--reason",
            "self-test: assembled execution without a closure",
            "--cpus",
            CPUS,
        ],
        label="reconcile",
    )
    code, outp, _ = run(
        [GEN_PY, V2, "status", "--root", states / "unclosed", "--campaign", cid, "--cpus", CPUS],
        label="status unclosed after reconcile",
    )
    log(
        "state unclosed after reconcile: blocking "
        f"{json.loads(outp[outp.index('{') :])['blocking']}"
    )


def step_analysis() -> None:
    cid = "v2-selftest-analysis"
    log(f"# analysis, two slots, M0 and M3 {datetime.now(UTC).isoformat(timespec='seconds')}")
    out = WORK / "out" / cid
    for g in (1, 2, 3):
        harness(GEN_PY, "generate", cid, "--set", "1", "--generation", str(g), "--out", out)
    harness(GEN_PY, "check-set", cid, "--set", "1")
    manifest = out / "manifest-set1-gen1.json"
    cache = WORK / "cache-analysis"  # inside .cache/population/, as orchestrate requires
    records = WORK / "records-analysis"
    runs = WORK / "runs"
    points = [f"{p}={POINT_PY[p]}={runs / p}" for p in ("M0", "M3")]
    args = [
        "--manifest",
        manifest,
        "--project",
        REPO,
        "--cache",
        cache,
        "--generator-python",
        GEN_PY,
        "--records",
        records,
    ]
    for p in points:
        args += ["--point", p]
    harness(GEN_PY, "orchestrate", cid, *args)
    harness(GEN_PY, "orchestrate", cid, *args, label="orchestrate again on the finished state")
    metrics = WORK / "out" / cid / "metrics.json"
    if not metrics.exists():
        harness(
            GEN_PY,
            "metrics",
            cid,
            "--manifest",
            manifest,
            "--records",
            records,
            "--point",
            f"M0={runs / 'M0'}",
            "--point",
            f"M3={runs / 'M3'}",
            "--out",
            metrics,
        )
    sizes = [f.stat().st_size for f in runs.glob("*/cases/*.json")]
    log(
        f"result records: {len(sizes)} files, {sum(sizes)} bytes, mean "
        f"{sum(sizes) / len(sizes):.0f} bytes per record (one case, one slot, one point)"
    )


def step_d6smoke() -> None:
    """A reduced run of the D6 machinery (not the D6): the first 13 cases of the declared
    rule, at M3 only, the 7 configurations twice; then the negative control and the check."""
    import d6

    log(f"# D6 smoke (not the D6) {datetime.now(UTC).isoformat(timespec='seconds')}")
    det = json.loads(
        (WORK / "out" / "v2-selftest-determinism" / "manifest-set1-gen1.json").read_bytes()
    )
    cases = d6.select_cases(det, 40)[:13]
    log(f"D6 rule, first 13 of 40: {cases}")
    cid = "v2-selftest-d6inputs"
    declaration(
        cid, "determinism", cases, [{"workers": 13, "order": "index"}] * 3, lot_size=len(cases)
    )
    out = WORK / "out" / cid
    for g in (1, 2, 3):
        if not (out / f"manifest-set1-gen{g}.json").exists():
            harness(GEN_PY, "generate", cid, "--set", "1", "--generation", str(g), "--out", out)
    entries, _ = v2.read_journal(v2.Campaign(ROOT, cid, False))
    if v2.accepted_set(entries) is None:
        harness(GEN_PY, "check-set", cid, "--set", "1")
    cache = WORK / "cache-d6"
    if not cache.exists():
        harness(
            GEN_PY,
            "regenerate",
            cid,
            "--manifest",
            out / "manifest-set1-gen1.json",
            "--cache",
            cache,
            "--lot",
            "0",
        )
    m3 = POINT_PY["M3"]
    default = WORK / "dispatch-default-M3.json"
    if not default.exists():
        run([m3, V2, "dispatch-table", "--out", default, "--cpus", CPUS])
    e_table = WORK / "dispatch-E-M3.json"
    if not e_table.exists():
        os.environ["NPY_DISABLE_CPU_FEATURES"] = "X86_V3"
        try:
            run(
                [m3, V2, "dispatch-table", "--out", e_table, "--cpus", CPUS],
                label="NPY_DISABLE_CPU_FEATURES=X86_V3",
            )
        finally:
            os.environ.pop("NPY_DISABLE_CPU_FEATURES", None)
    d6_script = POP / "d6.py"
    d6dir = WORK / "d6-smoke"
    decl = d6dir / "d6-declaration.json"
    if not decl.exists():
        d6dir.mkdir(parents=True, exist_ok=True)
        run(
            [
                m3,
                d6_script,
                "plan",
                "--selection-root",
                ROOT,
                "--selection-campaign",
                "v2-selftest-determinism",
                "--dispatch-default",
                default,
                "--dispatch-e",
                e_table,
                "--inputs-root",
                ROOT,
                "--inputs-campaign",
                cid,
                "--points",
                "M3",
                "--limit",
                "13",
                "--out",
                decl,
                "--cpus",
                CPUS,
            ]
        )
    runs = d6dir / "runs"
    sequential = [c for c in ("R-idx", "R-rev", "R-shf", "E")]
    procs = []
    t0 = time.perf_counter()
    for c in sequential:
        for rep in (1, 2):
            if (runs / f"{c}-rep{rep}-M3").exists():
                continue
            cmd = [
                m3,
                d6_script,
                "run",
                "--declaration",
                decl,
                "--point",
                "M3",
                "--cache",
                cache,
                "--out",
                runs,
                "--configuration",
                c,
                "--repetition",
                str(rep),
                "--cpus",
                CPUS,
            ]
            log("$ (background) " + " ".join(str(x).replace(str(REPO), "<repo>") for x in cmd))
            procs.append(
                subprocess.Popen(
                    [str(x) for x in cmd],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                )
            )
    for c in ("F", "P24", "P12"):
        for rep in (1, 2):
            if not (runs / f"{c}-rep{rep}-M3").exists():
                run(
                    [
                        m3,
                        d6_script,
                        "run",
                        "--declaration",
                        decl,
                        "--point",
                        "M3",
                        "--cache",
                        cache,
                        "--out",
                        runs,
                        "--configuration",
                        c,
                        "--repetition",
                        str(rep),
                        "--cpus",
                        CPUS,
                    ]
                )
    for p in procs:
        text, _ = p.communicate()
        for line in text.splitlines()[-5:]:
            log(f"  {line}")
        log(f"  [exit {p.returncode}]")
    log(f"D6 smoke executions: wall {time.perf_counter() - t0:.0f} s")
    run([m3, d6_script, "negative-control", "--declaration", decl, "--out", runs, "--cpus", CPUS])
    report = d6dir / "d6-smoke-report.json"
    if not report.exists():
        run(
            [
                m3,
                d6_script,
                "check",
                "--declaration",
                decl,
                "--out",
                runs,
                "--report",
                report,
                "--cpus",
                CPUS,
            ],
            expect=None,
        )


def step_blockers() -> None:
    """One test per blocking finding of the code review (codex-code-review.md), after the
    lock, analysis and D6 smoke steps. Results in blockers.json; every test must pass."""
    log(f"# blocking findings of the code review {datetime.now(UTC).isoformat(timespec='seconds')}")
    results: list[dict] = []

    def note(test: str, ok: bool, detail="") -> None:
        results.append({"test": test, "ok": bool(ok), "detail": str(detail)[:400]})
        log(f"{'OK   ' if ok else 'WRONG'} {test}: {str(detail)[:300]}")

    acid = "v2-selftest-analysis"
    aout = WORK / "out" / acid
    manifest = aout / "manifest-set1-gen1.json"
    runs = WORK / "runs"
    # B1: a second analysis of a unit in another folder is refused.
    code, out, _ = harness(
        POINT_PY["M3"],
        "analyze",
        acid,
        "--manifest",
        manifest,
        "--cache",
        WORK / "cache-analysis",
        "--out",
        WORK / "runs-second" / "M3-slot1",
        "--point",
        "M3",
        "--lot",
        "0",
        "--slot",
        "1",
        expect=None,
        label="B1 second analysis of a unit in another folder",
    )
    note(
        "B1 second analysis in another folder refused", code == 1 and "bound to" in out, out[-200:]
    )
    # B2: a record with an empty scientific section is refused and counts as an error.
    rec = json.loads((runs / "M3-slot1" / "cases" / "planet-below-white-0000.json").read_bytes())
    entry = next(
        e
        for e in json.loads(manifest.read_bytes())["cases"]
        if e["id"] == "planet-below-white-0000"
    )
    empty = copy.deepcopy(rec)
    empty["conditions"]["i"]["scientific"] = {}
    problems = v2.validate_record(empty, entry, {})
    view = v2.condition_view(empty, "i", "ok")
    note(
        "B2 empty scientific record refused, counted as an error in C6",
        any("scientific record without" in p for p in problems) and view["status"] == "error",
        problems[:2],
    )
    # B2: metrics refuses a lot without record 4 (an assembled copy of the records, nothing
    # deleted; the journal copy names the same run directories).
    state = WORK / "blocker-states" / "no-record-4"
    if not state.exists():
        shutil.copytree(
            ROOT / acid, state / "campaigns" / acid, ignore=shutil.ignore_patterns("journal.lock")
        )
        shutil.copytree(
            WORK / "records-analysis",
            state / "records",
            ignore=shutil.ignore_patterns("lot-0001-*-4-inputs-deleted.json"),
        )
    code, out, _ = run(
        [
            GEN_PY,
            V2,
            "metrics",
            "--root",
            state / "campaigns",
            "--campaign",
            acid,
            "--manifest",
            manifest,
            "--records",
            state / "records",
            "--point",
            f"M0={runs / 'M0'}",
            "--point",
            f"M3={runs / 'M3'}",
            "--out",
            state / "metrics.json",
            "--cpus",
            CPUS,
        ],
        expect=None,
        label="B2 metrics without record 4 of lot 1",
    )
    note(
        "B2 metrics refuses a lot without record 4", code == 1 and "no record 4" in out, out[-200:]
    )
    # B3: the chain's counter (in-process, on a separate strict-like root under WORK).
    root = WORK / "blocker-states" / "chain-root"
    for cid, pred, before in (
        ("chain-a", {"kind": "v1-diagnostic"}, 0),
        ("chain-b", None, 5),
        ("chain-c", {"kind": "v1-diagnostic"}, 0),
    ):
        f = root / cid / "declaration.json"
        if not f.exists():
            f.parent.mkdir(parents=True, exist_ok=True)
            d = {"campaign_id": cid, "chain": "development", "chain_sets_consumed_before": before}
            if pred is None:
                a = root / "chain-a" / "declaration.json"
                pred = {"campaign_id": "chain-a", "campaign_declaration_sha256": v2.file_sha256(a)}
            d["predecessor"] = pred
            v2.write_json(f, d)
    camp_b = v2.Campaign(
        root, "chain-b", False, json.loads((root / "chain-b" / "declaration.json").read_bytes())
    )
    problems = v2.chain_problems(camp_b, root)
    note(
        "B3 wrong count before and a sibling campaign of the chain refused",
        any("counts 5 sets" in p for p in problems) and any("chain-c" in p for p in problems),
        problems,
    )
    # B4: a strict declaration cannot restrict the population, and dev needs manifest B.
    p = v2.strict_declaration_problems(
        {"population": "dev", "chain": "development", "cases": ["x"]}
    )
    note(
        "B4 case list and missing manifest B refused in a strict declaration",
        any("case list" in x for x in p) and any("manifest B" in x for x in p),
        p,
    )
    # B5: the D6 smoke report and a wrong qualification hash do not open a campaign.
    smoke = WORK / "d6-smoke" / "d6-smoke-report.json"
    rel = smoke.relative_to(REPO).as_posix()
    p = v2.prerequisite_problems(
        {
            "qualification": {"path": rel, "sha256": "0" * 64, "result": "PASS"},
            "d6": {"path": rel, "sha256": v2.file_sha256(smoke)},
        }
    )
    note(
        "B5 a smoke D6 and a wrong qualification hash refused as prerequisites",
        any("full matrix" in x for x in p) and any("qualification record" in x for x in p),
        p,
    )
    # B5-D6: the smoke report does not count as the D6; a forged control value is caught.
    report = json.loads(smoke.read_bytes())
    note(
        "B5-D6 a run without M0 and the 40 cases does not count as the D6",
        report["counts_as_d6"] is False
        and report["result"].startswith("PASS (smoke")
        and any("points" in x for x in report["matrix_problems"])
        and any("40 distinct cases" in x for x in report["matrix_problems"]),
        report["matrix_problems"],
    )
    forged = WORK / "blocker-states" / "d6-forged-control"
    if not forged.exists():
        shutil.copytree(WORK / "d6-smoke" / "runs", forged)
        # A consistent forgery: the control value changed AND the execution record updated
        # with the new file's SHA-256, so that only the check of the declared value can
        # catch it.
        target = sorted((forged / "R-idx-rep1-M3" / "cases").glob("*.json"))[1]
        old_sha = v2.file_sha256(target)
        r = json.loads(target.read_bytes())
        r["control"]["cases_before_in_process"] += 1
        target.write_bytes(v2.record_bytes(r))
        new_sha = v2.file_sha256(target)
        ex_path = forged / "R-idx-rep1-M3" / "execution.json"
        ex = json.loads(ex_path.read_bytes())
        for p in ex["processes"]:
            p["records_sha256"] = [new_sha if s == old_sha else s for s in p["records_sha256"]]
        ex_path.write_bytes(v2.canonical_json(ex) + b"\n")
    out_report = WORK / "blocker-states" / "d6-forged-report.json"
    if not out_report.exists():
        run(
            [
                POINT_PY["M3"],
                POP / "d6.py",
                "check",
                "--declaration",
                WORK / "d6-smoke" / "d6-declaration.json",
                "--out",
                forged,
                "--report",
                out_report,
                "--cpus",
                CPUS,
            ],
            expect=None,
            label="B5-D6 check with a forged control value",
        )
    fr = json.loads(out_report.read_bytes())
    note(
        "B5-D6 a consistently forged control value is caught by the declared value (not PASS)",
        not fr["result"].startswith("PASS")
        and any("control value" in x for x in fr["check1"])
        and not any("differ from the SHA-256" in x for x in fr["check1"]),
        [fr["result"], fr["check1"][:2]],
    )
    # B6: a worker reporting a dispatch problem writes a lock at once (in-process).
    wcamp = v2.open_campaign(str(ROOT), "v2-selftest-workerlock")
    if not (wcamp.dir / "locks").exists():
        ident = v2.new_execution_identity(wcamp, "generate", 1, 1, generation=1)
        ex = v2.Execution(
            wcamp, ident, {"note": "self-test"}, {"kind": "generation", "set": 1}, lambda e: []
        )
        ex.worker(
            {"pid": 999999, "problems": ["dispatch table differs (simulated by the self-test)"]}
        )
    locks = sorted((wcamp.dir / "locks").glob("lock-*.json"))
    note("B6 a worker's dispatch problem writes a lock", len(locks) == 1, [x.name for x in locks])
    # B7: in the lock step, the divergence entry precedes the closure, which names the evidence.
    entries, _ = v2.read_journal(v2.Campaign(ROOT, "v2-selftest-lock", False))
    kinds = [e["kind"] for e in entries]
    closed = next(e for e in entries if e["kind"] == "closed")
    evidence = closed["payload"].get("evidence")
    note(
        "B7 the lock is written at detection, before the closure; the evidence file exists",
        "divergence" in kinds
        and kinds.index("divergence") < kinds.index("closed")
        and closed["payload"].get("lock_sha256")
        and evidence
        and Path(evidence).is_file(),
        [kinds, evidence],
    )
    # B8: two simultaneous executions of the same unit: exactly one starts.
    (WORK / "blocker-states").mkdir(parents=True, exist_ok=True)
    ccid = "v2-selftest-concurrent"
    cj = ROOT / ccid / "journal.jsonl"
    if not cj.exists():
        cmds = [
            [
                str(x)
                for x in [
                    GEN_PY,
                    V2,
                    "generate",
                    "--root",
                    ROOT,
                    "--campaign",
                    ccid,
                    "--set",
                    "1",
                    "--generation",
                    "1",
                    "--out",
                    WORK / "out" / f"{ccid}-{k}",
                    "--cpus",
                    CPUS,
                ]
            ]
            for k in (1, 2)
        ]
        log("$ (two at once) " + " | ".join(" ".join(c).replace(str(REPO), "<repo>") for c in cmds))
        procs = [
            subprocess.Popen(c, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            for c in cmds
        ]
        outs = [p.communicate()[0] for p in procs]
        codes = []
        for k, (p, o) in enumerate(zip(procs, outs, strict=True), 1):
            last = o.strip().splitlines()[-1] if o.strip() else ""
            log(f"  [process {k}, PID {p.pid}, exit {p.returncode}] {last}")
            codes.append(p.returncode)
        v2.write_json(WORK / "blocker-states" / "concurrent-exits.json", {"exits": codes})
    codes = json.loads((WORK / "blocker-states" / "concurrent-exits.json").read_bytes())["exits"]
    entries, _ = v2.read_journal(v2.Campaign(ROOT, ccid, False))
    started = [e for e in entries if e["kind"] == "started"]
    closed = [e for e in entries if e["kind"] == "closed"]
    note(
        "B8 two simultaneous executions of one unit: one ran to its closure (exit 0), the "
        "other was refused (exit 1)",
        sorted(codes) == [0, 1] and len(started) == 1 and len(closed) == 1,
        [codes, len(started), len(closed)],
    )
    # B9: diagnostic metrics are labelled.
    md = (aout / "metrics.md").read_text(encoding="utf-8")
    mj = json.loads((aout / "metrics.json").read_bytes())
    note(
        "B9 diagnostic metrics labelled 'DIAGNOSTIC: not an approval'",
        md.startswith("# DIAGNOSTIC: not an approval")
        and mj["approval_status"] == "DIAGNOSTIC: not an approval"
        and mj["eligibility"] == "diagnostic",
        md.splitlines()[0],
    )
    # B10: another affinity than the declared one is refused.
    code, out, _ = run(
        [
            POINT_PY["M3"],
            V2,
            "analyze",
            "--root",
            ROOT,
            "--campaign",
            acid,
            "--manifest",
            manifest,
            "--cache",
            WORK / "cache-analysis",
            "--out",
            runs / "M3-slot1",
            "--point",
            "M3",
            "--lot",
            "0",
            "--slot",
            "1",
            "--cpus",
            "8-30",
        ],
        expect=None,
        label="B10 analyze with another affinity",
    )
    note("B10 another affinity refused", code == 1 and "affinity" in out, out[-200:])
    # B11: campaign ids with '..' or an absolute path are refused.
    for bad in ("..", "C:\\outside", "a/../b"):
        code, out, _ = run(
            [GEN_PY, V2, "status", "--root", ROOT, "--campaign", bad, "--cpus", CPUS],
            expect=None,
            label="B11",
        )
        note(
            f"B11 campaign id {bad!r} refused", code == 1 and "plain folder name" in out, out[-150:]
        )
    # Containment: an output outside the project is refused before anything is written.
    outside = REPO.parent / "outside-refute-v2-test" / "metrics.json"  # never created
    code, out, _ = run(
        [
            GEN_PY,
            V2,
            "metrics",
            "--root",
            ROOT,
            "--campaign",
            acid,
            "--manifest",
            manifest,
            "--records",
            WORK / "records-analysis",
            "--point",
            f"M0={runs / 'M0'}",
            "--out",
            outside,
            "--cpus",
            CPUS,
        ],
        expect=None,
        label="containment: --out outside the project",
    )
    note(
        "containment: --out outside the project refused, nothing created",
        code == 1 and "not inside the project" in out and not outside.parent.exists(),
        out[-150:],
    )
    # N6: the user's home directory is masked.
    name = os.environ.get("USERNAME", "")
    masked = v2.mask_user(f"C:\\Users\\{name}\\AppData\\x.py and /c/Users/{name}/y")
    note(
        "N6 the user's home directory is masked",
        name not in masked and masked.count("<user>") == 2,
        "masked",
    )
    # N3: a malformed f64 gives an invalid report, not an exception.
    a = {"x": {"f64": "zz", "dec": "1.0"}}
    b = {"x": {"f64": "3ff0000000000000", "dec": "1.0"}}
    rep = CMP.compare_records(a, b, "d6-science")
    note("N3 a malformed f64 is reported as invalid", rep["status"] == "invalid", rep["status"])
    path = WORK / "blockers.json"
    if not path.exists():
        v2.write_json(path, {"results": results, "passed": all(r["ok"] for r in results)})
    bad = [r["test"] for r in results if not r["ok"]]
    log(f"blocking findings: {len(results) - len(bad)} of {len(results)} as expected {bad or ''}")


def step_blockers3() -> None:
    """One test per blocking finding of the second code review (codex-code-review-2.md) and
    per non-blocking correction of the same round. Results in blockers3.json."""
    log(f"# second code review {datetime.now(UTC).isoformat(timespec='seconds')}")
    results: list[dict] = []
    states = WORK / "blocker-states"
    states.mkdir(parents=True, exist_ok=True)

    def note(test: str, ok: bool, detail="") -> None:
        results.append({"test": test, "ok": bool(ok), "detail": str(detail)[:400]})
        log(f"{'OK   ' if ok else 'WRONG'} {test}: {str(detail)[:300]}")

    # B5: the qualification result and conditions come from the structured record.
    qual = json.loads(QUALIFICATION.read_bytes())
    snapshot = v2.machine_snapshot()
    note(
        "B5 the real qualification record passes on this machine (positive control)",
        v2.qualification_problems(qual, snapshot) == [],
        v2.qualification_problems(qual, snapshot),
    )
    failed = {**qual, "result": "FAIL"}
    p = v2.qualification_problems(failed, snapshot)
    note(
        "B5 a qualification record with result FAIL is refused", any("not PASS" in x for x in p), p
    )
    changed = copy.deepcopy(qual)
    changed["validity_conditions_machine_checked"]["bios_version"] = "F9"
    p = v2.qualification_problems(changed, snapshot)
    note("B5 a qualification of another BIOS is refused", any("bios_version" in x for x in p), p)
    # B5: a D6 report of another version does not count; the current version does.
    smoke = json.loads((WORK / "d6-smoke" / "d6-smoke-report.json").read_bytes())
    current = {
        **smoke,
        "result": "PASS",
        "counts_as_d6": True,
        "d6_sha256": v2.file_sha256(POP / "d6.py"),
        "harness_sha256": v2.HARNESS_SHA256,
        "profiles": {n: CMP.profile_sha256(n) for n in ("d6-science", "d6-control")},
    }
    old = {**current, "d6_sha256": "0" * 64}
    for name, doc in (("current", current), ("old", old)):
        path = states / f"d6-report-{name}-version.json"
        if not path.exists():
            v2.write_json(path, doc)
    qual_rel = QUALIFICATION.relative_to(REPO).as_posix()

    def prereq(name):
        path = states / f"d6-report-{name}-version.json"
        return v2.prerequisite_problems(
            {
                "qualification": {"path": qual_rel, "sha256": v2.file_sha256(QUALIFICATION)},
                "d6": {"path": path.relative_to(REPO).as_posix(), "sha256": v2.file_sha256(path)},
            },
            snapshot,
        )

    note(
        "B5 an assembled D6 PASS of the current versions passes the gate (positive control)",
        prereq("current") == [],
        prereq("current"),
    )
    note(
        "B5 a D6 report of another version of d6.py is refused",
        any("another version" in x for x in prereq("old")),
        prereq("old"),
    )
    # B5-D6: a selection manifest of a restricted campaign is refused by the plan.
    target = states / "d6-plan-from-subset.json"
    code, out, _ = run(
        [
            POINT_PY["M3"],
            POP / "d6.py",
            "plan",
            "--selection-root",
            ROOT,
            "--selection-campaign",
            "v2-selftest-analysis",
            "--dispatch-default",
            WORK / "dispatch-default-M3.json",
            "--dispatch-e",
            WORK / "dispatch-E-M3.json",
            "--inputs-root",
            ROOT,
            "--inputs-campaign",
            "v2-selftest-d6inputs",
            "--points",
            "M0",
            "M3",
            "--out",
            target,
            "--cpus",
            CPUS,
        ],
        expect=None,
        label="B5-D6 plan from a campaign restricted to 4 cases",
    )
    note(
        "B5-D6 a D6 planned from a subset of the population is refused",
        code == 1 and "whole determinism population" in out and not target.exists(),
        out[-200:],
    )
    decl = json.loads((WORK / "d6-smoke" / "d6-declaration.json").read_bytes())
    swapped = copy.deepcopy(decl)
    swapped["cases"] = [*decl["cases"][:-1], "planet-near-white-0000"]
    sys.path.insert(0, str(POP))
    import d6

    p = d6.selection_problems(swapped)
    note(
        "B5-D6 a declared case list that is not the rule is caught",
        any("declared rule" in x for x in p),
        p,
    )
    p = d6.selection_problems(decl)
    note("B5-D6 the real declaration recomputes from its selection (positive control)", p == [], p)
    # B7: an interruption after the detection keeps the observations.
    icid = "v2-selftest-interrupt"
    cache = WORK / "cache-interrupt"
    cache.mkdir(parents=True, exist_ok=True)
    planted = cache / "planet-measurable-white-0000.rpc"
    if not planted.exists():
        planted.write_bytes(PLANTED)
    journal = ROOT / icid / "journal.jsonl"
    if not journal.exists():
        cmd = [
            str(x)
            for x in [
                GEN_PY,
                V2,
                "generate",
                "--root",
                ROOT,
                "--campaign",
                icid,
                "--set",
                "1",
                "--generation",
                "1",
                "--out",
                WORK / "out" / icid,
                "--cache",
                cache,
                "--cpus",
                CPUS,
            ]
        ]
        log("$ (to be stopped after the detection) " + " ".join(cmd).replace(str(REPO), "<repo>"))
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        deadline = time.monotonic() + 120
        while time.monotonic() < deadline:
            if journal.exists() and b'"kind":"divergence"' in journal.read_bytes():
                break
            time.sleep(0.05)
        workers = [
            e["payload"]["pid"]
            for e in v2.read_journal(v2.Campaign(ROOT, icid, False))[0]
            if e["kind"] == "process"
        ]
        proc.kill()  # this process only, by its PID
        for pid in workers:  # its workers, by the PIDs recorded in the journal
            try:
                os.kill(pid, 9)
            except OSError:
                pass
        proc.communicate()
        log(f"  stopped PID {proc.pid} and its workers {workers} after the divergence entry")
    entries, _ = v2.read_journal(v2.Campaign(ROOT, icid, False))
    kinds = [e["kind"] for e in entries]
    obs_path = Path(next(e for e in entries if e["kind"] == "started")["payload"]["observations"])
    lines = [json.loads(x) for x in obs_path.read_bytes().splitlines() if x.strip()]
    first = next((x for x in lines if x["case"] == "planet-measurable-white-0000"), None)
    note(
        "B7 a stop after the detection keeps the observation of the divergent case (entry, "
        "blocks, problems) and the lock",
        "divergence" in kinds
        and "closed" not in kinds
        and first is not None
        and first["entry"].get("layout")
        and first["blocks"]
        and first["problems"],
        [kinds, len(lines)],
    )
    # B2: a registered comparison report that is missing or altered is damaged evidence.
    dcamp = v2.open_campaign(str(ROOT), "v2-selftest-cmpdamage")
    present = states / "comparison-registered.json"
    if not present.exists():
        v2.write_json(present, {"format": v2.SLOTS_REPORT_FORMAT, "note": "self-test"})
        ident = v2.new_execution_identity(dcamp, "compare-slots", 1, 1, point="M3", lot=0)
        v2.append_journal(
            dcamp,
            "compared",
            ident,
            {"point": "M3", "lot": 0, "report": str(present), "report_sha256": "1" * 64},
        )
        v2.append_journal(
            dcamp,
            "compared",
            ident,
            {
                "point": "M3",
                "lot": 1,
                "report": str(states / "never-written.json"),
                "report_sha256": "2" * 64,
            },
        )
    altered = v2.registered_comparison(dcamp, "M3", 0)
    missing = v2.registered_comparison(dcamp, "M3", 1)
    absent = v2.registered_comparison(dcamp, "M3", 2)
    note(
        "B2 a registered comparison report altered or missing is damaged (a lock); one not "
        "registered is only unfinished",
        altered[2] and missing[2] and not absent[2] and absent[0] is None,
        [altered[1], missing[1], absent[1]],
    )
    # Non-blocking: successor, home folder, default root, the /home mask.
    root = states / "chain-root"
    d = root / "chain-d" / "declaration.json"
    if not d.exists():
        d.parent.mkdir(parents=True, exist_ok=True)
        v2.write_json(
            d,
            {
                "campaign_id": "chain-d",
                "chain": "confirmation",
                "chain_sets_consumed_before": 0,
                "predecessor": {"kind": "none"},
            },
        )
    e = root / "chain-e" / "declaration.json"
    if not e.exists():
        e.parent.mkdir(parents=True, exist_ok=True)
        v2.write_json(
            e,
            {
                "campaign_id": "chain-e",
                "chain": "confirmation",
                "chain_sets_consumed_before": 0,
                "predecessor": {
                    "campaign_id": "chain-d",
                    "campaign_declaration_sha256": v2.file_sha256(d),
                },
            },
        )
    camp_d = v2.Campaign(root, "chain-d", False, json.loads(d.read_bytes()))
    p = v2.chain_problems(camp_d, root)
    note(
        "a predecessor with a successor stays usable, marked superseded (no new set)",
        p == [] and camp_d.superseded,
        [p, camp_d.superseded],
    )
    note(
        "the project folder is not inside the user's home directory",
        v2.home_problems() == [],
        v2.home_problems(),
    )
    name = os.environ.get("USERNAME", "")
    masked = v2.mask_user(f"/home/{name}/x and C:\\Users\\{name}\\y")
    note(
        "the mask covers /home/<user> and C:\\Users\\<user>",
        name not in masked and masked.count("<user>") == 2,
        "masked",
    )
    note(
        "the default campaigns root is contained in the project",
        bool(v2.inside_project(v2.DEFAULT_ROOT, "root")),
        "",
    )
    path = WORK / "blockers3.json"
    if not path.exists():
        v2.write_json(path, {"results": results, "passed": all(r["ok"] for r in results)})
    bad = [r["test"] for r in results if not r["ok"]]
    log(f"second review findings: {len(results) - len(bad)} of {len(results)} as expected {bad}")


def step_summary() -> None:
    lines = []
    for f in sorted(HERE.iterdir()):
        if f.is_file() and f.name != "SHA256SUMS":
            lines.append(f"{hashlib.sha256(f.read_bytes()).hexdigest()}  {f.name}")
    (HERE / "SHA256SUMS").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


STEPS = {
    "declare": step_declare,
    "reference": step_reference,
    "overhead": step_overhead,
    "determinism": step_determinism,
    "inject": step_inject,
    "lock": step_lock,
    "analysis": step_analysis,
    "records": step_records,
    "d6smoke": step_d6smoke,
    "blockers": step_blockers,
    "blockers3": step_blockers3,
    "summary": step_summary,
}

if __name__ == "__main__":
    STEPS[sys.argv[1]]()
