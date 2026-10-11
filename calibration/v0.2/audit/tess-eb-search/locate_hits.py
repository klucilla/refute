"""Scratch (read-only): give the line of every hit of tess_eb_search.py in the members of
the zips passed. The tokens and the number pattern are built by the same code as in
tess_eb_search.py (copied); the totals are printed so they can be checked against the
script's own counts."""
import re
import sys
import zipfile
from pathlib import Path

TSV = Path(sys.argv[1])
ZIPS = [Path(p) for p in sys.argv[2:]]
NL = "\n"

raw = TSV.read_bytes()
lines = [l for l in raw.decode("utf-8").splitlines() if l.strip() and not l.startswith("#")]
header = lines[0].split("\t")
rows = []
for l in lines[3:]:  # header, units, dashes
    cells = dict(zip(header, (c.strip() for c in l.split("\t"))))
    if cells.get("TIC", "").isdigit():
        rows.append(cells)


def sig_digits(s):
    return len(s.replace("-", "").replace(".", "").lstrip("0"))


tokens = {}
for r in rows:
    tic = int(r["TIC"])
    for field in ("Per", "RAJ2000", "DEJ2000"):
        v = r.get(field, "")
        if not v or sig_digits(v) < 6:
            continue
        variants = {v}
        try:
            variants.add(repr(float(v)))
        except ValueError:
            pass
        for t in variants:
            tokens.setdefault(t, []).append((tic, field))

NUMBER = re.compile(rb"(?<![\d.])-?\d+\.\d+(?![\d])")

for z in ZIPS:
    total = 0
    with zipfile.ZipFile(z) as zf:
        for info in (i for i in zf.infolist() if not i.is_dir()):
            data = zf.read(info)
            for m in NUMBER.finditer(data):
                tok = m.group(0).decode()
                for tic, field in tokens.get(tok, ()):
                    total += 1
                    line = data.count(b"\n", 0, m.start()) + 1
                    paired = str(tic).encode() in data
                    print(f"{z.name}\t{info.filename}\t{line}\t{tok}\t{tic}\t{field}\t{paired}")
    print(f"# {z.name}: {total} hits")
