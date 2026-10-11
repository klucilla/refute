"""Scratch (read-only): search the versioned repository (every reachable blob) and the
v0.1 release assets for values of the TESS-EB snapshot (content SHA-256 a31936ce...)."""
import collections
import hashlib
import re
import subprocess
import sys
import zipfile
from pathlib import Path

REPO = Path(sys.argv[1])
TSV = Path(sys.argv[2])
ZIPS = {Path(p): h for p, h in (a.split("=") for a in sys.argv[3:])}
EXPECTED = "a31936ce4dc1bfbb27c4e372b145653ef1d97df250df8d1b0fadaa3f0f1b949c"
KNOWN = {158561566: "6.7899645", 316916655: "2.8747759", 317507345: "3.9400619",
         350445771: "3.1904288"}
NL = "\n"

raw = TSV.read_bytes()
lines = [l for l in raw.decode("utf-8").splitlines() if l.strip() and not l.startswith("#")]
content = (NL.join(lines) + NL).encode("utf-8")
digest = hashlib.sha256(content).hexdigest()
print("snapshot content SHA-256:", digest, "OK" if digest == EXPECTED else "MISMATCH")
header = lines[0].split("\t")
rows = []
for l in lines[3:]:  # header, units, dashes
    cells = dict(zip(header, (c.strip() for c in l.split("\t"))))
    if cells.get("TIC", "").isdigit():
        rows.append(cells)
print("rows:", len(rows), "columns:", header)


def sig_digits(s):
    return len(s.replace("-", "").replace(".", "").lstrip("0"))


tokens = {}  # number string -> list of (tic, field)
skipped = 0
for r in rows:
    tic = int(r["TIC"])
    for field in ("Per", "RAJ2000", "DEJ2000"):
        v = r.get(field, "")
        if not v:
            continue
        if sig_digits(v) < 6:  # too unspecific to search; counted
            skipped += 1
            continue
        variants = {v}
        try:
            variants.add(repr(float(v)))
        except ValueError:
            pass
        for t in variants:
            tokens.setdefault(t, []).append((tic, field))
print("search tokens:", len(tokens), "| values skipped (< 6 significant digits):", skipped)

NUMBER = re.compile(rb"(?<![\d.])-?\d+\.\d+(?![\d])")


def scan(name, data, hits):
    for m in NUMBER.finditer(data):
        tok = m.group(0).decode()
        for tic, field in tokens.get(tok, ()):
            hits.append((name, tok, tic, field, str(tic).encode() in data))


# Corpus A: every reachable blob of the repository, one path per blob, one git process.
objs = subprocess.run(["git", "-C", str(REPO), "rev-list", "--objects", "--all"],
                      capture_output=True, text=True, check=True).stdout.splitlines()
paths = {}
for line in objs:
    sha, _, path = line.partition(" ")
    if path:
        paths.setdefault(sha, path)
check = subprocess.run(["git", "-C", str(REPO), "cat-file", "--batch-check"],
                       input=NL.join(paths) + NL, capture_output=True, text=True,
                       check=True).stdout
blobs = [l.split()[0] for l in check.splitlines() if l.split()[1] == "blob"]
out = subprocess.run(["git", "-C", str(REPO), "cat-file", "--batch"],
                     input=(NL.join(blobs) + NL).encode(), capture_output=True,
                     check=True).stdout
hits_a = []
pos = 0
for sha in blobs:
    end = out.index(b"\n", pos)
    size = int(out[pos:end].split()[2])
    data = out[end + 1:end + 1 + size]
    pos = end + 1 + size + 1
    scan(f"{paths[sha]} (blob {sha[:8]})", data, hits_a)
refs = subprocess.run(["git", "-C", str(REPO), "for-each-ref", "--format=%(refname:short)"],
                      capture_output=True, text=True, check=True).stdout.split()
print("refs covered:", ", ".join(refs))
print("repository blobs scanned:", len(blobs))

# Corpus B: v0.1 release assets (local copies, SHA-256 checked against the release notes).
hits_b = []
for z, expected in ZIPS.items():
    h = hashlib.sha256(z.read_bytes()).hexdigest()
    with zipfile.ZipFile(z) as zf:
        members = [i for i in zf.infolist() if not i.is_dir()]
        for info in members:
            scan(f"{z.name}:{info.filename}", zf.read(info), hits_b)
    print(f"{z.name}: SHA-256 {'OK' if h == expected else 'MISMATCH ' + h}; "
          f"members scanned: {len(members)}")

for label, hits in (("REPOSITORY (all reachable blobs)", hits_a), ("v0.1 ASSETS", hits_b)):
    paired = [h for h in hits if h[4]]
    unpaired = [h for h in hits if not h[4]]
    known = [h for h in paired if KNOWN.get(h[2]) == h[1] and h[3] == "Per"]
    other = [h for h in paired if h not in known]
    print(f"\n== {label}: {len(hits)} hits; with the row's TIC in the same file: "
          f"{len(paired)} (the 4 known periods: {len(known)}; other values: {len(other)}); "
          f"without the TIC: {len(unpaired)}")
    by_file = collections.defaultdict(set)
    for h in known:
        by_file[h[0].split(" (blob")[0]].add(h[2])
    for f, tics in sorted(by_file.items()):
        print(f"   known period of TIC {sorted(tics)} in {f}")
    for h in other[:60]:
        print("   OTHER VALUE WITH ITS TIC:", h)
    counts = collections.Counter((h[1], h[3], h[2]) for h in unpaired)
    for (tok, field, tic), n in counts.most_common(20):
        example = next(h[0] for h in unpaired if h[1] == tok)
        print(f"   without TIC: {tok} ({field} of TIC {tic}): {n} hit(s), e.g. {example}")
