"""Scratch: pack the files of a folder into a zip (members = file names, fixed
timestamps, stored), so that tess_eb_search.py can scan them as zip members unchanged.
Prints the SHA-256 of the zip and of each member."""
import hashlib
import sys
import zipfile
from pathlib import Path

src, out = Path(sys.argv[1]), Path(sys.argv[2])
files = sorted(p for p in src.iterdir() if p.is_file())
with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_STORED) as zf:
    for p in files:
        info = zipfile.ZipInfo(p.name, date_time=(2026, 10, 11, 0, 0, 0))
        zf.writestr(info, p.read_bytes())
for p in files:
    print(f"member {p.name} {p.stat().st_size} {hashlib.sha256(p.read_bytes()).hexdigest()}")
print("zip", out.name, hashlib.sha256(out.read_bytes()).hexdigest())
