"""A stand-in for the docker CLI in the docker backend's tests (CI has no Docker).

Usage: fake_docker.py <state dir> <cgroup root> <docker arguments...>

It keeps each container in ``<state dir>/<id>.json`` and plays the systemd slices of the
VM under ``<cgroup root>``: the container's slice (``cpu.stat``, ``cgroup.events``) and its
scope (``cpu.max``, ``cpu.max.burst``). The command of a container is
``work <cpu seconds> <exit code> [<rate in CPUs>]``: ``start --attach`` adds usage at that
rate until the seconds are used or the container is killed, prints a line, and exits with
the code. ``--cpu-quota 0`` plays a container whose quota is max.
"""

from __future__ import annotations

import json
import sys
import time
import uuid
from pathlib import Path

state, root, args = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3:]
state.mkdir(parents=True, exist_ok=True)


def option(name: str, default: str | None = None) -> str | None:
    return args[args.index(name) + 1] if name in args else default


def slice_dir(slice_name: str) -> Path:
    parts = slice_name.removesuffix(".slice").split("-")  # refute-<paper>-<c>
    return root / "refute.slice" / f"refute-{parts[1]}.slice" / slice_name


def write(path: Path, text: str) -> None:
    # replaced in one step, as a cgroup file is read whole: a reader never sees it empty
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="ascii")
    for _ in range(50):
        try:
            tmp.replace(path)
            return
        except PermissionError:  # Windows: the reader holds the file open for a moment
            time.sleep(0.005)
    tmp.replace(path)


def load(cid: str) -> dict:
    return json.loads((state / f"{cid}.json").read_text(encoding="utf-8"))


command = args[0]
if command == "create":
    cid = uuid.uuid4().hex + uuid.uuid4().hex
    rest = args[1:]
    # the image is the first argument that is not an option or an option's value
    flags_with_value = set(
        "--name --cgroup-parent --cpu-period --cpu-quota --memory --memory-swap --shm-size "
        "--pids-limit --cap-drop --security-opt --mount --workdir --network --env --tmpfs --user "
        "--entrypoint".split()
    )
    i = 0
    while i < len(rest):
        if rest[i] in flags_with_value:
            i += 2
        elif rest[i].startswith("--"):
            i += 1
        else:
            break
    image, cmd = rest[i], rest[i + 1 :]
    record = {
        "args": args,
        "image": image,
        "cmd": cmd,
        "slice": option("--cgroup-parent"),
        "quota": option("--cpu-quota"),
        "period": option("--cpu-period"),
        "exit": None,
    }
    (state / f"{cid}.json").write_text(json.dumps(record), encoding="utf-8")
    print(cid)
elif command == "start":
    cid = args[-1]
    rec = load(cid)
    own = slice_dir(rec["slice"])
    scope = own / f"docker-{cid}.scope"
    quota = "max" if rec["quota"] == "0" else rec["quota"]
    write(scope / "cpu.max", f"{quota} {rec['period']}\n")
    write(scope / "cpu.max.burst", "0\n")
    seconds, code = float(rec["cmd"][1]), int(rec["cmd"][2])
    rate = float(rec["cmd"][3]) if len(rec["cmd"]) > 3 else 1.0
    usage = 0
    write(own / "cgroup.events", "populated 1\nfrozen 0\n")
    write(own / "cpu.stat", f"usage_usec {usage}\n")
    print("started", flush=True)
    killed = state / f"{cid}.killed"
    parent = own.parent / "cpu.stat"  # the paper's slice: the sum of its containers
    base = int(parent.read_text().split()[1]) if parent.exists() else 0
    step = 0.02
    while usage < seconds * 1_000_000 and not killed.exists():
        time.sleep(step)
        usage += int(rate * step * 1_000_000)
        write(own / "cpu.stat", f"usage_usec {usage}\n")
        write(parent, f"usage_usec {base + usage}\n")
    write(own / "cgroup.events", "populated 0\nfrozen 0\n")
    rec["exit"] = 137 if killed.exists() else code
    (state / f"{cid}.json").write_text(json.dumps(rec), encoding="utf-8")
    sys.exit(rec["exit"])
elif command == "image":
    # image inspect --format '{{json .Config.Volumes}}' <image>: an image named "...volume..."
    # plays one that declares a VOLUME
    print('{"/data":{}}' if "volume" in args[-1] else "null")
elif command == "kill":
    (state / f"{args[-1]}.killed").write_text("", encoding="ascii")
elif command == "inspect":
    print(load(args[-1])["exit"])
elif command == "commit":
    (state / f"{args[1]}.committed").write_text(args[2], encoding="utf-8")
elif command == "rm":
    (state / f"{args[-1]}.removed").write_text("", encoding="ascii")
else:
    sys.exit(f"fake docker: unknown command {command}")
