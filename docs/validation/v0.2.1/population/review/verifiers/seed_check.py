"""Seed collision check (population-study.md, section 5; Amendment 1, item c). Computes
only seed strings; it builds no case. Written by the Phase G reviewer."""

import ctypes
import hashlib
import importlib.util
import sys

k32 = ctypes.windll.kernel32
k32.GetCurrentProcess.restype = ctypes.c_void_p
k32.SetProcessAffinityMask(ctypes.c_void_p(k32.GetCurrentProcess()), ctypes.c_size_t(0xFFFFFF00))

spec = importlib.util.spec_from_file_location("population_under_review", sys.argv[1])
pop = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pop)


def h8(text):
    return int.from_bytes(hashlib.sha256(text.encode("utf-8")).digest()[:8], "big")


# A future drand randomness is a 64-hex-digit string; a fixed stand-in is used only to
# check that a confirmation prefix cannot collide with the dev and self-test prefixes.
STANDIN = "ab" * 32
pops = {"dev": pop.population_cases("dev"), "selftest": pop.population_cases("selftest"),
        "confirm(stand-in)": pop.population_cases("confirm:" + STANDIN)}
all_seeds = {}
for name, cases in pops.items():
    ids = [c["id"] for c in cases]
    assert len(ids) == len(set(ids)), f"{name}: repeated ids"
    mine = []
    for c in cases:
        band = c["band"] or "none"
        prefix = {"dev": pop.DEV_PREFIX, "selftest": pop.SELFTEST_PREFIX}.get(name, STANDIN)
        s = h8(f"{prefix}|{c['class']}|{band}|{c['noise']}|{c['index']}")
        if str(s) != c["seed"]:
            raise SystemExit(f"{c['id']}: seed differs from my formula")
        mine.append(s)
        for derived, label in ((s, "case"), (h8(f"{s}|noise"), "noise"), (h8(f"{s}|aux"), "aux"),
                               (h8(f"{s}|aux") + 1000, "aux+1000 (make_aux)")):
            all_seeds.setdefault(derived, []).append((name, c["id"], label))
    print(f"{name}: {len(cases)} cases, {len(set(mine))} distinct case seeds")
dups = {k: v for k, v in all_seeds.items() if len(v) > 1}
print(f"derived seeds (case, noise, aux, aux+1000) over all three populations: {len(all_seeds)} distinct, {len(dups)} collisions")
small = [k for k in all_seeds if k < 1000]
print(f"seeds below 1000 (test suite 0-9, H3 0-59): {len(small)}")
counts = {}
for c in pops["dev"]:
    key = (c["class"], c["band"], c["noise"], c["mechanism"], c["catalog_variant"])
    counts[key] = counts.get(key, 0) + 1
by_class = {}
for c in pops["dev"]:
    by_class[(c["class"], c["noise"])] = by_class.get((c["class"], c["noise"]), 0) + 1
print("dev cases by class and noise:", by_class)
few = [c["extra"] for c in pops["dev"] if c["mechanism"] == "few_train" and c["band"] == "near" and c["noise"] == "white"]
print("few_train distances:", {d: sum(e["distance_years"] == d for e in few) for d in (1, 2, 3)},
      "train transits:", {t: sum(e["train_transits"] == t for e in few) for t in (3, 4)})
var = {}
for c in pops["dev"]:
    if c["class"] != "no_transit" and c["band"] == "measurable" and c["noise"] == "white":
        var[(c["class"], c["catalog_variant"])] = var.get((c["class"], c["catalog_variant"]), 0) + 1
print("catalog variants (measurable, white):", var)
mech = {}
for c in pops["dev"]:
    if c["noise"] == "correlated":
        mech[(c["class"], c["band"], c["mechanism"])] = mech.get((c["class"], c["band"], c["mechanism"]), 0) + 1
print("mechanisms (correlated):", mech)
