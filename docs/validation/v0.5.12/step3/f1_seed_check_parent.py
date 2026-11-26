"""v0.5.12 step 3: F-1's seed check at the PARENT of F-1's freeze commit (a new checker, rule (c);
#218 comment 7199932177, item 1).

    {python} -I -B docs/validation/v0.5.12/step3/f1_seed_check_parent.py

The freeze commit is the one that added ``docs/validation/v0.5.12/step3/f1_probe.py``. At its
parent no record of F-1 exists, so the seed's absence there is what "a scenario seed absent from
every committed record" means. It prints the commits and the matches, and exits 1 on any match
or any unresolved commit.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
SEED = "2026112601"
PROBE = "docs/validation/v0.5.12/step3/f1_probe.py"


def git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True)


def main() -> int:
    added = git("log", "--format=%H", "--diff-filter=A", "--", PROBE).stdout.split()
    if len(added) != 1:
        print(json.dumps({"refused": "the freeze commit is not unique", "commits": added}))
        return 1
    freeze = added[0]
    parent = git("rev-parse", f"{freeze}^").stdout.strip()
    r = git("grep", "-l", "-w", SEED, parent)
    matches = [line for line in r.stdout.splitlines() if line]
    ok = r.returncode == 1 and not matches  # git grep exits 1 when nothing matches
    print(json.dumps({"freeze": freeze, "parent": parent, "matches": matches, "absent": ok}))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
