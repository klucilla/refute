"""Comparator and locator of the population harness v2 (``refute-population-compare/1``).

Specification: ``.cache/population/diag/harness-v2-spec.md`` (sections 3, 10 and 11) and
Amendment 4 of ``docs/validation/v0.2.1/population-study.md``. This file is frozen per
campaign: its SHA-256, version, schema and the three profiles with their path lists are
recorded in the campaign declaration and in every comparison report. A change is a new
comparator (a new file with a new name) and a new campaign.

It uses only the Python standard library, so it runs in any of the environments.

What it compares:

- **Blobs** (``refute-population-serialization/1``): each blob's layout is parsed on its own
  (magic, header length, header JSON, ``arrays`` list, offsets, lengths, coverage); a
  different layout is a structural divergence and the second blob is never read with the
  first blob's table. With identical layouts: the first differing byte, its segment and its
  block of 1 MiB; for the header, the JSON paths; for an array, the first differing element
  (unravelled) and the count of elements whose bytes differ; then, only as an explanation,
  the largest absolute and relative differences and the ULP distribution. Differences only
  in the sign of zero or in a NaN payload are counted apart and never treated as equal.
- **Manifest entries and block indexes** (no bytes): the segment and block that differ. The
  localization ends there (the concession of section 3 of the specification).
- **Result records** (``refute-population-result/3``): structure (paths, types), then values
  by their typed encoding (the bits of every float), skipping exactly the paths of the
  profile named by the caller. There is no default profile.
"""

from __future__ import annotations

import hashlib
import json
import math
import struct
from pathlib import Path

SCHEMA = "refute-population-compare/1"
VERSION = "1"
SERIALIZATION = "refute-population-serialization/1"
MAGIC = (SERIALIZATION + "\n").encode("ascii")
BLOCK_SIZE = 1 << 20
COMPARATOR_PATH = Path(__file__).resolve()
COMPARATOR_SHA256 = hashlib.sha256(COMPARATOR_PATH.read_bytes()).hexdigest()

# The 13 paths excluded from the comparison of the two analysis slots (specification,
# section 10). Exactly these and no others.
SLOTS_EXCLUDED = (
    "/identity/slot",
    "/identity/execution_id",
    "/identity/attempt",
    "/identity/origin/harness_commit",
    "/operational/pid",
    "/operational/seconds",
    "/operational/peak_memory_mb",
    "/operational/started_utc",
    "/operational/ended_utc",
    "/operational/sequence_position",
    "/comparison/status",
    "/comparison/report_sha256",
    "/integrity",
)

# The three frozen profiles (specification, section 11, item 5). ``exclude``: every path is
# compared except these and their members; ``only``: only these paths and their members.
PROFILES = {
    "slots": {
        "mode": "exclude",
        "paths": list(SLOTS_EXCLUDED),
        "forbidden": ["/control"],
        "used_for": "the two analysis slots of a lot",
    },
    "d6-science": {
        "mode": "exclude",
        "paths": [
            *SLOTS_EXCLUDED,
            "/configuration/thread_env",
            "/configuration/threadpools",
            "/configuration/dispatch_table_sha256",
            "/control",
        ],
        "forbidden": [],
        "used_for": "the science between the variants of the D6 test",
    },
    "d6-control": {
        "mode": "only",
        "paths": ["/control"],
        "forbidden": [],
        "used_for": "the control pass of the D6 test",
    },
}


def canonical(obj) -> bytes:
    return json.dumps(
        obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")


def profile_sha256(name: str) -> str:
    """SHA-256 of a profile's definition (its mode and its path lists)."""
    p = profile(name)
    return hashlib.sha256(canonical({"name": name, **p})).hexdigest()


def profile(name: str | None) -> dict:
    if not name or name not in PROFILES:
        raise ValueError(f"unknown or missing comparator profile {name!r}; there is no default")
    return PROFILES[name]


def identity() -> dict:
    """What a campaign declaration freezes about this comparator."""
    return {
        "schema": SCHEMA,
        "version": VERSION,
        "sha256": COMPARATOR_SHA256,
        "block_size": BLOCK_SIZE,
        "profiles": {n: {**p, "sha256": profile_sha256(n)} for n, p in PROFILES.items()},
    }


# --- JSON pointers and the typed float encoding ------------------------------------------


def pointer(parts) -> str:
    """RFC 6901 JSON Pointer of a list of keys and indexes."""
    return "".join("/" + str(p).replace("~", "~0").replace("/", "~1") for p in parts)


def is_typed_float(value) -> bool:
    return (
        isinstance(value, dict)
        and set(value) == {"f64", "dec"}
        and isinstance(value["f64"], str)
        and isinstance(value["dec"], str)
    )


def float_problem(value: dict) -> str | None:
    """Why a typed float is invalid (None if it is valid): 16 lowercase hex digits, and a
    ``dec`` that names the same value (non-finite: ``nan``, ``inf``, ``-inf`` by class; finite:
    parses back to the same bits)."""
    bits = value["f64"]
    if len(bits) != 16 or any(c not in "0123456789abcdef" for c in bits):
        return f"f64 {bits!r} is not 16 lowercase hex digits"
    x = struct.unpack(">d", bytes.fromhex(bits))[0]
    dec = value["dec"]
    if math.isnan(x):
        return None if dec == "nan" else f"dec {dec!r} for a NaN"
    if math.isinf(x):
        want = "inf" if x > 0 else "-inf"
        return None if dec == want else f"dec {dec!r} for {want}"
    try:
        back = struct.pack(">d", float(dec)).hex()
    except ValueError:
        return f"dec {dec!r} is not a number"
    if dec in ("nan", "inf", "-inf") or back != bits:
        return f"dec {dec!r} does not give the bits {bits}"
    return None


def flatten(value, parts=()) -> dict[str, tuple]:
    """Every path of a JSON value with its kind and value; containers carry their keys or
    length, a typed float is a leaf."""
    out: dict[str, tuple] = {}
    path = pointer(parts)
    if is_typed_float(value):
        out[path] = ("float", value["f64"], value["dec"])
    elif isinstance(value, dict):
        out[path] = ("object", tuple(sorted(value)))
        for k in sorted(value):
            out.update(flatten(value[k], (*parts, k)))
    elif isinstance(value, list):
        out[path] = ("array", len(value))
        for i, v in enumerate(value):
            out.update(flatten(v, (*parts, i)))
    elif value is None:
        out[path] = ("null", None)
    elif isinstance(value, bool):
        out[path] = ("bool", value)
    elif isinstance(value, int):
        out[path] = ("int", value)
    elif isinstance(value, str):
        out[path] = ("str", value)
    else:
        out[path] = ("unsupported", repr(value))
    return out


def _under(path: str, roots) -> bool:
    return any(path == r or path.startswith(r + "/") for r in roots)


def _ordered_bits(bits: str) -> int:
    """The IEEE 754 bit pattern as an integer that orders like the values (for ULPs)."""
    n = int(bits, 16)
    return (1 << 63) - (n & ((1 << 63) - 1)) - 1 if n >> 63 else n + (1 << 63)


def float_explanation(a_bits: str, b_bits: str) -> dict:
    a = struct.unpack(">d", bytes.fromhex(a_bits))[0]
    b = struct.unpack(">d", bytes.fromhex(b_bits))[0]
    out: dict = {"left": a_bits, "right": b_bits}
    if math.isnan(a) and math.isnan(b):
        out["kind"] = "nan_payload"
    elif a == 0.0 and b == 0.0:
        out["kind"] = "sign_of_zero"
    elif math.isnan(a) or math.isnan(b) or math.isinf(a) or math.isinf(b):
        out["kind"] = "non_finite"
    else:
        out["kind"] = "value"
        out["abs_diff"] = repr(abs(a - b))
        scale = max(abs(a), abs(b))
        out["rel_diff"] = repr(abs(a - b) / scale) if scale else "0.0"
        out["ulps"] = abs(_ordered_bits(a_bits) - _ordered_bits(b_bits))
    return out


# --- result records ----------------------------------------------------------------------


def record_problems(rec, name: str) -> list[str]:
    """Problems of the typed encoding of a record: invalid floats and unsupported values."""
    problems = []
    for path, item in flatten(rec).items():
        if item[0] == "float":
            p = float_problem({"f64": item[1], "dec": item[2]})
            if p:
                problems.append(f"{name}{path}: invalid typed float: {p}")
        elif item[0] == "unsupported":
            problems.append(f"{name}{path}: unsupported value {item[1]}")
    return problems


def compare_records(left, right, profile_name: str, *, labels=("left", "right")) -> dict:
    """Compare two decoded result records under a named profile."""
    prof = profile(profile_name)
    fa, fb = flatten(left), flatten(right)
    problems = record_problems(left, labels[0]) + record_problems(right, labels[1])
    for name, flat in zip(labels, (fa, fb), strict=True):
        for root in prof["forbidden"]:
            if any(_under(p, [root]) for p in flat):
                problems.append(f"{name}: {root} is not allowed under profile {profile_name}")

    def compared(path: str) -> bool:
        if path == "":
            return prof["mode"] == "exclude"
        if prof["mode"] == "exclude":
            return not _under(path, prof["paths"])
        return _under(path, prof["paths"])

    differences = []
    for path in sorted(set(fa) | set(fb)):
        if not compared(path):
            continue
        a, b = fa.get(path), fb.get(path)
        if a is None or b is None:
            # Only the topmost missing path is reported, not every member below it.
            parent = path.rsplit("/", 1)[0]
            if parent in fa and parent in fb:
                differences.append(
                    {"path": path, "kind": f"only_in_{labels[0] if b is None else labels[1]}"}
                )
            continue
        if a[0] != b[0]:
            differences.append({"path": path, "kind": "type", "left": a[0], "right": b[0]})
        elif a[0] == "object":
            continue  # its members are compared one by one
        elif a[0] == "array":
            if a[1] != b[1]:
                differences.append({"path": path, "kind": "length", "left": a[1], "right": b[1]})
        elif a[0] == "float":
            if a[1] != b[1] or a[2] != b[2]:
                differences.append({"path": path, **float_explanation(a[1], b[1]), "type": "float"})
        elif a[1] != b[1]:
            differences.append({"path": path, "kind": "value", "left": a[1], "right": b[1]})
    status = "invalid" if problems else ("identical" if not differences else "divergent")
    return {
        "format": SCHEMA,
        "comparator_sha256": COMPARATOR_SHA256,
        "profile": profile_name,
        "profile_sha256": profile_sha256(profile_name),
        "left_sha256": hashlib.sha256(canonical(left)).hexdigest(),
        "right_sha256": hashlib.sha256(canonical(right)).hexdigest(),
        "status": status,
        "problems": problems,
        "differences": differences,
        "counts": {
            "differences": len(differences),
            "sign_of_zero": sum(d.get("kind") == "sign_of_zero" for d in differences),
            "nan_payload": sum(d.get("kind") == "nan_payload" for d in differences),
        },
    }


# --- blobs -------------------------------------------------------------------------------


class LayoutError(ValueError):
    """A blob whose layout cannot be parsed or does not cover every byte."""


DTYPE_SIZE = {"<f8": 8, "<i8": 8, "|b1": 1}


def parse_layout(blob: bytes) -> dict:
    """The segments of one blob, parsed from that blob only."""
    if not blob.startswith(MAGIC):
        raise LayoutError("the blob does not start with the serialization magic")
    pos = len(MAGIC)
    if len(blob) < pos + 8:
        raise LayoutError("the blob ends inside the header length")
    size = int.from_bytes(blob[pos : pos + 8], "little")
    head_start = pos + 8
    if len(blob) < head_start + size:
        raise LayoutError("the blob ends inside the header")
    try:
        header = json.loads(blob[head_start : head_start + size].decode("utf-8"))
        arrays = header["arrays"]
    except (ValueError, KeyError, TypeError) as exc:
        raise LayoutError(f"the header is not valid ({type(exc).__name__}: {exc})") from None
    segments = [
        {"name": "magic", "dtype": None, "shape": None, "offset": 0, "length": len(MAGIC)},
        {"name": "header_length", "dtype": None, "shape": None, "offset": pos, "length": 8},
        {"name": "header", "dtype": None, "shape": None, "offset": head_start, "length": size},
    ]
    offset = head_start + size
    for item in arrays:
        name, dtype, shape = item
        if dtype not in DTYPE_SIZE:
            raise LayoutError(f"array {name}: unsupported dtype {dtype!r}")
        count = 1
        for n in shape:
            count *= n
        length = count * DTYPE_SIZE[dtype]
        segments.append(
            {"name": name, "dtype": dtype, "shape": list(shape), "offset": offset, "length": length}
        )
        offset += length
    if offset != len(blob):
        raise LayoutError(f"the segments end at {offset}, the blob has {len(blob)} bytes")
    return {"header_length": size, "header": header, "segments": segments}


def coverage_problems(segments: list[dict], total: int) -> list[str]:
    """Offsets start at 0, each segment starts where the previous ended, the last ends at
    the end of the blob."""
    problems, pos = [], 0
    for s in segments:
        if s["offset"] != pos:
            problems.append(f"segment {s['name']} starts at {s['offset']}, expected {pos}")
        pos = s["offset"] + s["length"]
    if pos != total:
        problems.append(f"the last segment ends at {pos}, the blob has {total} bytes")
    return problems


def _structure(layout: dict) -> list:
    return [
        [s["name"], s["dtype"], s["shape"], s["offset"], s["length"]] for s in layout["segments"]
    ]


def _unravel(index: int, shape: list[int]) -> list[int]:
    out = []
    for n in reversed(shape):
        out.append(index % n if n else 0)
        index = index // n if n else 0
    return list(reversed(out)) if shape else []


def _first_difference(a: memoryview, b: memoryview, lo: int, hi: int) -> int:
    """The first offset in [lo, hi) where the bytes differ (they are known to differ)."""
    chunk = 1 << 16
    for start in range(lo, hi, chunk):
        stop = min(start + chunk, hi)
        if a[start:stop] != b[start:stop]:
            return next(i for i in range(start, stop) if a[i] != b[i])
    raise ValueError("no differing byte in the range")


def _differing_elements(a: memoryview, b: memoryview, size: int) -> list[int]:
    """Indexes of the elements whose bytes differ, found chunk by chunk."""
    found, chunk = [], 1 << 16
    for start in range(0, len(a), chunk):
        if a[start : start + chunk] == b[start : start + chunk]:
            continue
        stop = min(start + chunk, len(a))
        for e in range(start // size, (stop + size - 1) // size):
            if a[e * size : (e + 1) * size] != b[e * size : (e + 1) * size]:
                found.append(e)
    return found


def compare_blobs(left: bytes, right: bytes, *, labels=("left", "right")) -> dict:
    """Locate the difference between two blobs: structure first, then bytes."""
    report: dict = {
        "format": SCHEMA,
        "comparator_sha256": COMPARATOR_SHA256,
        "kind": "blob",
        "left_sha256": hashlib.sha256(left).hexdigest(),
        "right_sha256": hashlib.sha256(right).hexdigest(),
        "left_bytes": len(left),
        "right_bytes": len(right),
    }
    if left == right:
        return {**report, "status": "identical"}
    layouts = []
    for name, blob in zip(labels, (left, right), strict=True):
        try:
            layouts.append(parse_layout(blob))
        except LayoutError as exc:
            return {**report, "status": "structural", "unparseable": name, "reason": str(exc)}
    la, lb = layouts
    if _structure(la) != _structure(lb):
        sa, sb = _structure(la), _structure(lb)
        report["status"] = "structural"
        report["structure"] = {
            "header_length": [la["header_length"], lb["header_length"]],
            "segments_only_left": [s for s in sa if s not in sb][:20],
            "segments_only_right": [s for s in sb if s not in sa][:20],
        }
        report["header_paths"] = _json_differences(la["header"], lb["header"])
        return report
    report["status"] = "bytes"
    ma, mb = memoryview(left), memoryview(right)
    segments = []
    for s in la["segments"]:
        lo, hi = s["offset"], s["offset"] + s["length"]
        if ma[lo:hi] == mb[lo:hi]:
            continue
        first = _first_difference(ma, mb, lo, hi)
        item = {
            "segment": s["name"],
            "first_differing_offset": first,
            "offset_in_segment": first - lo,
            "block": (first - lo) // BLOCK_SIZE,
            "blocks": sorted(
                {
                    (i - lo) // BLOCK_SIZE
                    for i in range(lo, hi, BLOCK_SIZE)
                    if ma[i : min(i + BLOCK_SIZE, hi)] != mb[i : min(i + BLOCK_SIZE, hi)]
                }
            ),
        }
        if s["name"] == "header":
            item["header_paths"] = _json_differences(la["header"], lb["header"])
        elif s["dtype"] is not None:
            size = DTYPE_SIZE[s["dtype"]]
            idx = _differing_elements(ma[lo:hi], mb[lo:hi], size)
            item["elements_differing"] = len(idx)
            item["first_element"] = _unravel(idx[0], s["shape"]) if idx else None
            item["explanation"] = _explain(ma[lo:hi], mb[lo:hi], s["dtype"], idx)
        segments.append(item)
    report["first_differing_offset"] = segments[0]["first_differing_offset"] if segments else None
    report["segments"] = segments
    return report


def _explain(a: memoryview, b: memoryview, dtype: str, idx: list[int]) -> dict:
    """Numeric explanation of the differing elements (only an explanation)."""
    if dtype == "<f8":
        kinds: dict[str, int] = {}
        max_abs, max_rel, ulps = 0.0, 0.0, []
        for e in idx:
            ab = bytes(a[e * 8 : e * 8 + 8])[::-1].hex()
            bb = bytes(b[e * 8 : e * 8 + 8])[::-1].hex()
            x = float_explanation(ab, bb)
            kinds[x["kind"]] = kinds.get(x["kind"], 0) + 1
            if x["kind"] == "value":
                max_abs = max(max_abs, float(x["abs_diff"]))
                max_rel = max(max_rel, float(x["rel_diff"]))
                ulps.append(x["ulps"])
        hist: dict[str, int] = {}
        for u in ulps:
            key = str(u) if u <= 4 else "5-16" if u <= 16 else "17-1024" if u <= 1024 else ">1024"
            hist[key] = hist.get(key, 0) + 1
        return {
            "by_kind": kinds,
            "max_abs_diff": repr(max_abs),
            "max_rel_diff": repr(max_rel),
            "ulp_histogram": hist,
        }
    if dtype == "<i8":
        diffs = [
            abs(
                int.from_bytes(a[e * 8 : e * 8 + 8], "little", signed=True)
                - int.from_bytes(b[e * 8 : e * 8 + 8], "little", signed=True)
            )
            for e in idx
        ]
        return {"max_abs_diff": max(diffs) if diffs else 0}
    return {"booleans_differing": len(idx)}


def _json_differences(a, b, limit: int = 50) -> list[dict]:
    fa, fb = flatten(a), flatten(b)
    out = []
    for path in sorted(set(fa) | set(fb)):
        if fa.get(path) != fb.get(path):
            out.append({"path": path, "left": fa.get(path), "right": fb.get(path)})
            if len(out) >= limit:
                break
    return out


# --- manifests and block indexes (no bytes) ----------------------------------------------


def locate_without_bytes(entry_a: dict, entry_b: dict, blocks_a: dict, blocks_b: dict) -> dict:
    """The segments and blocks where two cases differ, from their manifest entries
    (layout, segment hashes) and block indexes only. The localization ends at the block."""
    la, lb = entry_a.get("layout") or {}, entry_b.get("layout") or {}

    def shape(layout):
        return [
            [s.get("name"), s.get("dtype"), s.get("shape"), s.get("offset"), s.get("length")]
            for s in layout.get("segments", [])
        ]

    out: dict = {
        "sha256": [entry_a.get("sha256"), entry_b.get("sha256")],
        "concession": "without the bytes, the localization ends at the block",
    }
    if la.get("header_length") != lb.get("header_length") or shape(la) != shape(lb):
        out["status"] = "structural"
        out["header_length"] = [la.get("header_length"), lb.get("header_length")]
        sa, sb = shape(la), shape(lb)
        out["segments_only_left"] = [s for s in sa if s not in sb][:20]
        out["segments_only_right"] = [s for s in sb if s not in sa][:20]
        return out
    segments = []
    for sa, sb in zip(la["segments"], lb["segments"], strict=True):
        name = sa["name"]
        ba, bb = blocks_a.get(name), blocks_b.get(name)
        if sa.get("sha256") == sb.get("sha256") and ba == bb:
            continue
        item = {"segment": name, "segment_sha256": [sa.get("sha256"), sb.get("sha256")]}
        if ba is None or bb is None or len(ba) != len(bb):
            item["blocks"] = "block lists missing or of different length"
        else:
            diff = [i for i, (x, y) in enumerate(zip(ba, bb, strict=True)) if x != y]
            item["blocks"] = [
                {
                    "block": i,
                    "offset": sa["offset"] + i * BLOCK_SIZE,
                    "length": min(BLOCK_SIZE, sa["length"] - i * BLOCK_SIZE),
                }
                for i in diff
            ]
        segments.append(item)
    out["status"] = "blocks" if segments else "whole_hash_only"
    out["segments"] = segments
    return out


def compare_manifests(man_a: dict, man_b: dict, blocks_a: dict, blocks_b: dict) -> dict:
    """Compare two scientific manifests and their block indexes, case by case."""
    header = {k: v for k, v in man_a.items() if k != "cases"}
    header_b = {k: v for k, v in man_b.items() if k != "cases"}
    by_a = {e["id"]: e for e in man_a.get("cases", [])}
    by_b = {e["id"]: e for e in man_b.get("cases", [])}
    cases = []
    for cid in sorted(set(by_a) | set(by_b)):
        ea, eb = by_a.get(cid), by_b.get(cid)
        if ea is None or eb is None:
            cases.append({"case": cid, "status": "only_in_" + ("right" if ea is None else "left")})
            continue
        if canonical(ea) == canonical(eb):
            continue
        cases.append(
            {
                "case": cid,
                "status": "differs",
                "entry_paths": _json_differences(ea, eb),
                "location": locate_without_bytes(
                    ea,
                    eb,
                    (blocks_a.get("cases") or {}).get(cid, {}),
                    (blocks_b.get("cases") or {}).get(cid, {}),
                ),
            }
        )
    return {
        "format": SCHEMA,
        "comparator_sha256": COMPARATOR_SHA256,
        "kind": "manifests",
        "header_paths": _json_differences(header, header_b),
        "cases_compared": len(set(by_a) | set(by_b)),
        "cases_differing": len(cases),
        "cases": cases,
        "status": "identical"
        if not cases and canonical(header) == canonical(header_b)
        else "differs",
    }
