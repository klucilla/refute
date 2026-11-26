"""A4 (#218, comment 7203695669): build the wheel and the sdist offline into .cache and
record their content and size. Publishes nothing; changes no dependency."""

import hashlib
import json
import subprocess
import tarfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / ".cache" / "v0513prep" / "dist"
GUARD = ("pyproject.toml", "uv.lock")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


before = {name: sha(ROOT / name) for name in GUARD}
OUT.mkdir(parents=True, exist_ok=True)
proc = subprocess.run(
    ["uv", "build", "--offline", "--out-dir", str(OUT)],
    cwd=ROOT,
    capture_output=True,
    text=True,
)
after = {name: sha(ROOT / name) for name in GUARD}
record = {
    "command": "uv build --offline --out-dir .cache/v0513prep/dist",
    "exit_code": proc.returncode,
    "stderr_tail": proc.stderr.splitlines()[-15:],
    "dependency_files_unchanged": before == after,
    "sha256_before": before,
    "sha256_after": after,
    "artifacts": [],
}
for art in sorted(OUT.iterdir()):
    entry = {"name": art.name, "bytes": art.stat().st_size, "sha256": sha(art)}
    if art.suffix == ".whl":
        with zipfile.ZipFile(art) as z:
            infos = z.infolist()
        entry["members"] = len(infos)
        entry["uncompressed_bytes"] = sum(i.file_size for i in infos)
        tops: dict[str, list[int]] = {}
        for i in infos:
            parts = i.filename.split("/")
            key = "/".join(parts[:2]) if parts[0] == "refute" else parts[0]
            t = tops.setdefault(key, [0, 0])
            t[0] += 1
            t[1] += i.file_size
        entry["by_folder"] = {k: {"files": v[0], "bytes": v[1]} for k, v in sorted(tops.items())}
        entry["non_python"] = sorted(
            (i.filename, i.file_size)
            for i in infos
            if not i.filename.endswith(".py") and ".dist-info/" not in i.filename
        )
        entry["largest"] = sorted(((i.file_size, i.filename) for i in infos), reverse=True)[:10]
    elif art.name.endswith(".tar.gz"):
        with tarfile.open(art) as t:
            members = [m for m in t.getmembers() if m.isfile()]
        entry["members"] = len(members)
        entry["uncompressed_bytes"] = sum(m.size for m in members)
        tops2: dict[str, list[int]] = {}
        for m in members:
            parts = m.name.split("/")
            key = "/".join(parts[1:3]) if len(parts) > 2 else parts[-1]
            t2 = tops2.setdefault(key, [0, 0])
            t2[0] += 1
            t2[1] += m.size
        entry["by_folder"] = {k: {"files": v[0], "bytes": v[1]} for k, v in sorted(tops2.items())}
        entry["largest"] = sorted(((m.size, m.name) for m in members), reverse=True)[:10]
    record["artifacts"].append(entry)
(OUT.parent / "a4-build.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
print(json.dumps({k: record[k] for k in ("exit_code", "dependency_files_unchanged")}))
