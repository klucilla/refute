"""Probe of the subprocess backend tests (tests/test_ml_runner.py, tests/test_ml_orchestrate.py):
one cataloged synthetic fixture (src/refute/packs/ml/synthetic.py) whose behaviour is chosen by
its arguments, so that no test writes its own script. Uses the standard library only.

    probe.py exit CODE                 print "acc=91.2" and exit with CODE
    probe.py busy SECONDS              use SECONDS of CPU time, then print "acc=91.2"
    probe.py idle SECONDS              sleep SECONDS without output
    probe.py chatty                    print a line every 0.1 s, 300 times
    probe.py beat FILE CPU_SECONDS     append to FILE while using CPU_SECONDS of CPU time
    probe.py tick FILE                 append to FILE 100 times, every 0.05 s
    probe.py wait ARGS...              run "probe.py ARGS..." as a child and wait for it
    probe.py detach ARGS...            start "probe.py ARGS..." as a child and exit at once
    probe.py tree SECONDS              wait for "probe.py wait busy SECONDS", then for
                                       "probe.py busy SECONDS" (children and a grandchild)
    probe.py train SEED                write out/m-SEED.json and print "final acc=91.25"
    probe.py job FOLDER NAME           use 0.05 s of CPU, then write FOLDER/NAME with the
                                       start and end of the run (monotonic nanoseconds)
"""

import json
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve()


def child(args):
    return [sys.executable, "-I", str(HERE), *args]


def busy(seconds):
    end = time.process_time() + seconds
    while time.process_time() < end:
        pass


def main(argv):
    mode, args = argv[0], argv[1:]
    if mode == "exit":
        print("acc=91.2", flush=True)
        return int(args[0])
    if mode == "busy":
        busy(float(args[0]))
        print("acc=91.2", flush=True)
        return 0
    if mode == "idle":
        time.sleep(float(args[0]))
        return 0
    if mode == "chatty":
        for i in range(300):
            print(i, flush=True)
            time.sleep(0.1)
        return 0
    if mode == "beat":
        end = time.process_time() + float(args[1])
        while time.process_time() < end:
            with open(args[0], "a") as handle:
                handle.write("x")
        return 0
    if mode == "tick":
        for _ in range(100):
            with open(args[0], "a") as handle:
                handle.write("x")
            time.sleep(0.05)
        return 0
    if mode == "wait":
        return subprocess.run(child(args), check=False).returncode
    if mode == "detach":
        subprocess.Popen(child(args))
        return 0
    if mode == "tree":
        subprocess.run(child(["wait", "busy", args[0]]), check=True)
        subprocess.run(child(["busy", args[0]]), check=True)
        return 0
    if mode == "train":
        seed = int(args[0])
        Path("out").mkdir(exist_ok=True)
        Path("out", f"m-{seed}.json").write_text(json.dumps({"test": {"acc": 91.25}}))
        print("final acc=91.25")
        return 0
    if mode == "job":
        start = time.monotonic_ns()
        busy(0.05)
        name = args[1].replace("/", "_")
        Path(args[0]).mkdir(parents=True, exist_ok=True)
        Path(args[0], name).write_text(f"{start} {time.monotonic_ns()}")
        return 0
    print(f"unknown mode {mode!r}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
