"""Independent byte-level check of refute-population-serialization/1 (Amendment 1, item b).
Written by the Phase G reviewer; does not import the harness or refute."""

import ctypes
import hashlib
import json
import math
import re
import sys

import numpy as np

k32 = ctypes.windll.kernel32
k32.GetCurrentProcess.restype = ctypes.c_void_p
k32.SetProcessAffinityMask(ctypes.c_void_p(k32.GetCurrentProcess()), ctypes.c_size_t(0xFFFFFF00))

MAGIC = b"refute-population-serialization/1\n"
ALLOWED = {"<f8": 8, "<i8": 8, "|b1": 1}


def floats(obj, out):
    if isinstance(obj, dict):
        for v in obj.values():
            floats(v, out)
    elif isinstance(obj, list):
        for v in obj:
            floats(v, out)
    elif isinstance(obj, float):
        out.append(obj)
    return out


def expected_order(meta):
    names = ["lc/time", "lc/flux", "lc/flux_err", "lc/sector", "lc/year"]
    for k in range(len(meta["data"]["aux"]["sectors"])):
        names += [f"aux/sectors/{k}/{f}" for f in ("time", "pdcsap_flux", "sap_flux", "sap_bkg", "dump_times")]
    for k in range(len(meta["data"]["aux"]["pixels"])):
        names += [f"aux/pixels/{k}/{f}" for f in ("time", "flux", "flux_err", "aperture")]
    return names


def main(path, manifest_path):
    blob = open(path, "rb").read()
    case_id = path.replace("\\", "/").rsplit("/", 1)[1][: -len(".rpc")]
    entry = {c["id"]: c for c in json.load(open(manifest_path, encoding="utf-8"))["cases"]}[case_id]
    problems = []
    if hashlib.sha256(blob).hexdigest() != entry["sha256"]:
        problems.append("sha256 differs from the manifest")
    if not blob.startswith(MAGIC):
        problems.append("magic line")
    pos = len(MAGIC)
    size = int.from_bytes(blob[pos : pos + 8], "little")
    pos += 8
    head = blob[pos : pos + size]
    pos += size
    text = head.decode("utf-8")
    meta = json.loads(text)
    # canonical: re-encode must give the same bytes
    again = json.dumps(meta, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    if again.encode("utf-8") != head:
        problems.append("metadata is not canonical JSON")
    if re.search(r"NaN|Infinity", text):
        problems.append("NaN/Infinity in metadata")
    for f in floats(meta, []):
        if not math.isfinite(f) or float(repr(f)) != f:
            problems.append(f"float {f!r}")
    # seeds as decimal strings
    for key in ("seed",):
        if not isinstance(meta["case"][key], str) or not meta["case"][key].isdigit():
            problems.append("case seed not a decimal string")
    if not isinstance(meta["attempt_seed"], str) or not meta["attempt_seed"].isdigit():
        problems.append("attempt seed not a decimal string")
    # no local path or time of day
    for pat in (r"[A-Za-z]:[\\/]", r"Projetos", r"\\\\", r"20\d\d-\d\d-\d\dT", r"\d\d:\d\d:\d\d"):
        if re.search(pat, text):
            problems.append(f"metadata matches {pat!r}")
    names = [a[0] for a in meta["arrays"]]
    if names != expected_order(meta):
        problems.append(f"array order {names}")
    total = 0
    arrays = {}
    for name, dtype, shape in meta["arrays"]:
        if dtype not in ALLOWED:
            problems.append(f"{name}: dtype {dtype}")
        n = ALLOWED[dtype] * (math.prod(shape) if shape else 1)
        raw = blob[pos : pos + n]
        if dtype == "|b1" and not set(raw) <= {0, 1}:
            problems.append(f"{name}: boolean bytes other than 0/1")
        arrays[name] = np.frombuffer(raw, dtype=np.dtype(dtype)).reshape(shape)
        pos += n
        total += n
    if pos != len(blob):
        problems.append(f"{len(blob) - pos} trailing bytes")
    shapes = {a[0]: a[2] for a in meta["arrays"]}
    for k in range(len(meta["data"]["aux"]["pixels"])):
        if shapes[f"aux/pixels/{k}/flux"][1:] != [11, 11] or shapes[f"aux/pixels/{k}/aperture"] != [11, 11]:
            problems.append("pixel shapes")
    want = {"id", "class", "band", "noise", "index", "mechanism", "catalog_variant", "seed", "extra"}
    if set(meta["case"]) != want:
        problems.append(f"case keys {sorted(meta['case'])}")
    top = {"serialization", "case", "attempt_seed", "redraws", "parameters", "expected_snr", "catalog", "data", "arrays"}
    if set(meta) != top:
        problems.append(f"top keys {sorted(meta)}")
    lc = arrays["lc/flux"]
    extra = ""
    if meta["case"]["mechanism"] == "blend":
        p = meta["parameters"]
        t = arrays["lc/time"]
        dt = np.mod(t - p["t0"] + 0.5 * p["period"], p["period"]) - 0.5 * p["period"]
        out = np.abs(dt) > p["duration"]
        # high-pass: differences of consecutive cadences remove the slow trend
        resid = np.diff(lc[out]) / math.sqrt(2)
        extra = f"; out-of-transit point-to-point scatter {np.std(resid) * 1e6:.0f} ppm"
    print(
        f"{case_id}: {len(blob)} bytes, metadata {size} bytes, {len(names)} arrays, "
        f"{total} array bytes; problems: {problems or 'none'}{extra}"
    )
    print("  data keys:", sorted(meta["data"]), "| product:", meta["data"]["product"])
    print("  star retrieved_utc:", meta["data"]["star"]["retrieved_utc"], "| data_manifest:", meta["data"]["data_manifest"])


if __name__ == "__main__":
    for p in sys.argv[2:]:
        main(p, sys.argv[1])
