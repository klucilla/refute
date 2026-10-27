"""The upload times uv recorded for the changed packages' files, against the 7-day rule."""

import json
import sys
import tomllib
from datetime import UTC, datetime, timedelta
from pathlib import Path

lock = tomllib.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
names = set(sys.argv[2].split(","))
now = datetime.now(UTC)
out = {"now_utc": now.isoformat(timespec="seconds"), "exclude_newer": lock.get("options", {})}
for p in lock["package"]:
    if p["name"] not in names:
        continue
    times = [f.get("upload-time") for f in p.get("wheels", []) + [p.get("sdist") or {}]]
    times = sorted(t for t in times if t)
    newest = datetime.fromisoformat(times[-1].replace("Z", "+00:00")) if times else None
    out[p["name"]] = {
        "version": p["version"],
        "files": len(times),
        "newest_upload_utc": times[-1] if times else None,
        "age_days": round((now - newest).total_seconds() / 86400, 2) if newest else None,
        "seven_day_rule": bool(newest and now - newest >= timedelta(days=7)),
    }
print(json.dumps(out, indent=1, default=str))
