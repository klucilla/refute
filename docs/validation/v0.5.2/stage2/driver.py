"""The batch driver of the v0.5.2 stage-2 runs (the maintainer's decision of 2026-11-08, #216, items
8 and 10; revised after Codex's rounds 1 and 2). It knows nothing about any science: a run is a
fixed list of shards, and a shard's function returns canonical bytes.

- **A unit is a shard**, of fixed membership: its identity, the hash of its argument and the run's
  fingerprint (code, environment, plan, inputs, seed namespace, result schema: the caller's) are
  checked before it is skipped. Its result file holds only what the function returned, so the
  assembled result does not depend on interruptions; timing goes to a sidecar. Both are written
  atomically (temporary file, flush, ``os.replace``), the sidecar last, and only a shard with a
  matching sidecar counts as done. A missing, truncated, corrupt or stale shard is refused or
  computed again by the rules of ``_done``.
- **Dispatch is unit by unit.** At most ``workers`` shards are in flight; a new one is submitted
  only when one ends. A batch opens with the worker count of its start time (at most 10 in
  business hours, Monday to Friday 08:00 to 18:00 Brasilia; otherwise the configured number, at
  most 22).
- **A batch lasts at most ``batch_seconds`` (30 minutes), and nothing is interrupted in the
  middle:** a run declares ``max_shard_seconds``, measured from dispatch to completion (worker
  start included); dispatch stops that long before the end of the batch, and the shards in flight
  finish. A shard that outlives its limit is not interrupted either: it is kept, recorded as a
  deviation, and the run stops. So the 30 minutes hold while the declared limit holds.
- **Where it runs.** Logical processors 8 to 31, priority BelowNormal. With ``check_placement``
  (the default) the controller refuses to start outside those processors, and every worker checks
  its own priority and affinity before it computes; with ``pin``, one logical processor per worker.
- **The cap.** Consumption is the live user and kernel time of the batch's own workers, through
  process handles kept open from the first sight of each worker (so a worker that ended still
  answers), plus the controller's own time, discarded work included. A failed query keeps the
  last value, stops dispatch, and from then on charges every worker for the elapsed time. The
  charges are written to ``charges/`` every ``CHARGE_SECONDS`` and whenever the set of workers
  changes, with their identities, apart from the results. **After a crash** every worker ends by
  itself as soon as the controller is gone, and a batch not closed must be reconciled before
  anything runs: the run is refused while any of its workers is still alive; then it is charged
  what was last written plus every worker for a whole shard's limit and one more interval. No
  shard is dispatched once consumption, read at that moment, reaches ``cap_hours``. A watchdog,
  alive until every worker has stopped, ends the workers, by the handles this process holds, when
  consumption passes 10 % above the cap.
- **A stop binds.** Passing the cap by 10 %, a failed accounting and a shard beyond its limit are
  written to ``stop.json``: the run does not continue, and its bytes cannot be assembled, until
  ``reconcile`` records a reason, even when every shard exists.
- **The pause.** No shard is dispatched at or after ``PAUSE_AT`` (2026-11-18 20:00 Brasilia, the
  maintainer's rule); a restart resumes the rest.

A function must return bytes and must turn its expected failures into records (they stay in their
denominators); an exception that reaches the driver stops the run, with the shard unwritten.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import multiprocessing as mp
import os
import sys
import threading
import time
from collections.abc import Callable, Sequence
from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, wait
from pathlib import Path

BRT = dt.timezone(dt.timedelta(hours=-3))
PAUSE_AT = dt.datetime(2026, 11, 18, 20, 0, tzinfo=BRT)
BATCH_SECONDS = 1800.0
MAX_SHARD_SECONDS = 600.0
BUSINESS_WORKERS = 10
MAX_WORKERS = 22
FIRST_CPU, LAST_CPU = 8, 31
OVER_CAP_FACTOR = 1.10
CHARGE_SECONDS = 20.0
BELOW_NORMAL = 0x00004000
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000


def now() -> dt.datetime:
    return dt.datetime.now(BRT)


def is_business(moment: dt.datetime) -> bool:
    moment = moment.astimezone(BRT)
    return moment.weekday() < 5 and 8 <= moment.hour < 18


def workers_for(moment: dt.datetime, configured: int) -> int:
    limit = BUSINESS_WORKERS if is_business(moment) else MAX_WORKERS
    return max(1, min(limit, configured))


def _kernel32():
    import ctypes

    k32 = ctypes.windll.kernel32
    k32.GetCurrentProcess.restype = ctypes.c_void_p
    k32.SetPriorityClass.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
    k32.GetPriorityClass.argtypes = [ctypes.c_void_p]
    k32.GetPriorityClass.restype = ctypes.c_uint32
    k32.SetProcessAffinityMask.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
    k32.GetProcessAffinityMask.argtypes = [ctypes.c_void_p, *[ctypes.c_void_p] * 2]
    k32.OpenProcess.restype = ctypes.c_void_p
    k32.OpenProcess.argtypes = [ctypes.c_uint32, ctypes.c_int, ctypes.c_uint32]
    k32.GetProcessTimes.argtypes = [ctypes.c_void_p, *[ctypes.c_void_p] * 4]
    k32.GetExitCodeProcess.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
    k32.CloseHandle.argtypes = [ctypes.c_void_p]
    return k32


def set_below_normal() -> None:
    """This process, and the workers it starts, at BelowNormal (Windows only)."""
    if sys.platform == "win32":
        k32 = _kernel32()
        if not k32.SetPriorityClass(k32.GetCurrentProcess(), BELOW_NORMAL):
            raise OSError("could not set this process to BelowNormal")


def _own_mask() -> int:
    import ctypes

    k32 = _kernel32()
    process, system = ctypes.c_size_t(), ctypes.c_size_t()
    if not k32.GetProcessAffinityMask(
        k32.GetCurrentProcess(), ctypes.byref(process), ctypes.byref(system)
    ):
        raise OSError("could not read this process's affinity")
    return int(process.value)


def _allowed_mask() -> int:
    return sum(1 << cpu for cpu in range(FIRST_CPU, LAST_CPU + 1))


def check_controller_placement() -> None:
    """Refuse to start on any processor outside 8 to 31 (Windows only)."""
    if sys.platform == "win32" and _own_mask() & ~_allowed_mask():
        raise SystemExit("the controller's affinity reaches processors outside 8 to 31: refused")


def _check_worker_placement(cpu: int | None) -> None:
    """A worker's own check, before it computes anything (Windows only)."""
    if sys.platform != "win32":
        return
    k32 = _kernel32()
    if k32.GetPriorityClass(k32.GetCurrentProcess()) != BELOW_NORMAL:
        raise OSError("a worker is not at BelowNormal")
    mask = _own_mask()
    if mask & ~_allowed_mask():
        raise OSError("a worker's affinity reaches processors outside 8 to 31")
    if cpu is not None and mask != 1 << cpu:
        raise OSError(f"a worker is not pinned to logical processor {cpu}")


def _pin_self(cpu: int) -> None:
    if sys.platform == "win32":
        k32 = _kernel32()
        if not k32.SetProcessAffinityMask(k32.GetCurrentProcess(), 1 << cpu):
            raise OSError(f"could not pin this worker to logical processor {cpu}")


def _raw_times(handle):
    import ctypes

    times = [ctypes.c_uint64() for _ in range(4)]
    if not _kernel32().GetProcessTimes(handle, *[ctypes.byref(t) for t in times]):
        return None
    return [t.value for t in times]


def _times(handle) -> float | None:
    """User plus kernel seconds through an open handle, ``None`` if the query fails."""
    raw = _raw_times(handle)
    return None if raw is None else (raw[2] + raw[3]) / 1e7


def still_running(pid: int, created: int) -> bool:
    """Is this process, of this creation time, still alive (Windows only)?"""
    if sys.platform != "win32":
        return False
    import ctypes

    k32 = _kernel32()
    handle = k32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, 0, pid)
    if not handle:
        return False
    try:
        code = ctypes.c_uint32()
        raw = _raw_times(handle)
        alive = k32.GetExitCodeProcess(handle, ctypes.byref(code)) and code.value == 259
        return bool(alive and raw is not None and raw[0] == created)
    finally:
        k32.CloseHandle(handle)


class CpuTracker:
    """The owned workers' cumulative processor time, by handles kept open, with monotone counters
    (Windows only: elsewhere it reports zero and the committed time stands in)."""

    def __init__(self) -> None:
        self.handles: dict[int, object] = {}
        self.last: dict[int, float] = {}
        self.created: dict[int, int] = {}
        self.failed_queries = 0
        self.failing_since: float | None = None
        self.lock = threading.Lock()

    def observe(self, pids) -> None:
        if sys.platform != "win32":
            return
        with self.lock:
            for pid in pids:
                if pid not in self.handles:
                    handle = _kernel32().OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, 0, pid)
                    if handle:
                        self.handles[pid] = handle
                        raw = _raw_times(handle)
                        self.created[pid] = raw[0] if raw else 0

    def total(self) -> float:
        """The sum of the last good values; a failure starts ``failing_since``, and it stays."""
        with self.lock:
            for pid, handle in self.handles.items():
                value = _times(handle)
                if value is None:
                    self.failed_queries += 1
                    if self.failing_since is None:
                        self.failing_since = time.monotonic()
                    continue
                self.last[pid] = max(self.last.get(pid, 0.0), value)
            return sum(self.last.values())

    def identities(self) -> dict[str, int]:
        with self.lock:
            return {str(pid): created for pid, created in self.created.items()}

    def close(self) -> None:
        with self.lock:
            for handle in self.handles.values():
                _kernel32().CloseHandle(handle)
            self.handles.clear()


def _die_with_the_controller() -> None:
    """A worker ends as soon as its controller is gone: left alone, it would block forever on a
    queue whose other ends its siblings hold, or finish a shard nobody counts."""
    parent = mp.parent_process()
    if parent is None:
        return

    def watch() -> None:
        parent.join()
        os._exit(1)

    threading.Thread(target=watch, daemon=True).start()


def _init_worker(counter, pin, initializer, check) -> None:
    _die_with_the_controller()
    cpu = None
    if pin:
        with counter.get_lock():
            index = counter.value
            counter.value += 1
        cpu = pin[index % len(pin)]
        _pin_self(cpu)
    if check:
        _check_worker_placement(cpu)
    if initializer is not None:
        initializer()


def _call(fn, sid, arg):
    cpu_start, wall_start = time.process_time(), time.monotonic()
    data = fn(arg)
    if not isinstance(data, bytes):
        raise TypeError("a shard's function must return bytes")
    return sid, data, time.process_time() - cpu_start, time.monotonic() - wall_start


def _atomic(path: Path, data: bytes) -> None:
    tmp = path.with_name(path.name + ".tmp")
    with open(tmp, "wb") as fh:
        fh.write(data)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _arg_hash(arg) -> str:
    return _sha(repr(arg).encode())


class Run:
    """One resumable run: ``shards`` is a list of ``(id, argument)``, in schedule order."""

    def __init__(
        self,
        out: Path,
        fn: Callable,
        shards: Sequence[tuple[str, object]],
        fingerprint: str,
        cap_hours: float,
        workers: int,
        initializer: Callable | None = None,
        pin: Sequence[int] | None = None,
        clock: Callable[[], dt.datetime] = now,
        pause_at: dt.datetime = PAUSE_AT,
        batch_seconds: float = BATCH_SECONDS,
        max_shard_seconds: float = MAX_SHARD_SECONDS,
        check_placement: bool = True,
    ):
        ids = [s for s, _ in shards]
        if len(set(ids)) != len(ids):
            raise SystemExit("two shards share an identity")
        if pin and any(c < FIRST_CPU or c > LAST_CPU for c in pin):
            raise SystemExit("a pinned processor is outside 8 to 31")
        if max_shard_seconds >= batch_seconds:
            raise SystemExit("a shard's limit must leave room inside the batch")
        self.out, self.fn, self.shards = out, fn, list(shards)
        self.fingerprint, self.cap_hours, self.workers = fingerprint, cap_hours, workers
        self.initializer, self.pin, self.clock = initializer, list(pin or []), clock
        self.pause_at, self.batch_seconds = pause_at, batch_seconds
        self.max_shard_seconds, self.check_placement = max_shard_seconds, check_placement
        self.data_dir, self.side_dir, self.charge_dir = (
            out / "shards",
            out / "sidecars",
            out / "charges",
        )
        self.stop_path = out / "stop.json"

    def _paths(self, sid: str):
        return self.data_dir / f"{sid}.bin", self.side_dir / f"{sid}.json"

    def _done(self) -> dict[str, dict]:
        """The finished shards. No sidecar: not done (any data file is overwritten). A sidecar of
        another fingerprint or argument, a missing file or a content mismatch: the run is refused,
        never silently repaired. A sidecar of a shard outside the schedule: refused."""
        known = dict(self.shards)
        done = {}
        if self.side_dir.exists():
            for path in self.side_dir.glob("*.json"):
                if path.stem not in known:
                    raise SystemExit(f"shard {path.stem}: not in this schedule: refused")
        for sid, arg in self.shards:
            data_path, side_path = self._paths(sid)
            if not side_path.exists():
                continue
            side = json.loads(side_path.read_text("utf-8"))
            if side["fingerprint"] != self.fingerprint:
                raise SystemExit(f"shard {sid}: a record of another fingerprint: refused")
            if side["arg_sha256"] != _arg_hash(arg):
                raise SystemExit(f"shard {sid}: a record of another argument: refused")
            if not data_path.exists() or _sha(data_path.read_bytes()) != side["sha256"]:
                raise SystemExit(f"shard {sid}: its file does not match its sidecar: refused")
            done[sid] = side
        return done

    def _log(self, **line) -> None:
        with (self.out / "progress.jsonl").open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({"at": self.clock().isoformat(), **line}, sort_keys=True) + "\n")

    def _store(self, sid: str, arg, data: bytes, cpu: float, workers: int) -> None:
        data_path, side_path = self._paths(sid)
        _atomic(data_path, data)
        side = {
            "sha256": _sha(data),
            "arg_sha256": _arg_hash(arg),
            "cpu_seconds": cpu,
            "workers": workers,
            "fingerprint": self.fingerprint,
        }
        _atomic(side_path, json.dumps(side, sort_keys=True).encode())

    def _crash_charge(self, workers: int) -> float:
        """What a batch not closed adds: every worker for a whole shard and one more interval."""
        return workers * (self.max_shard_seconds + CHARGE_SECONDS)

    def spent_seconds(self) -> float:
        """Every batch's charge, with the crash charge of those not closed."""
        total = 0.0
        if self.charge_dir.exists():
            for path in sorted(self.charge_dir.glob("b*.json")):
                doc = json.loads(path.read_text("utf-8"))
                total += max(doc["seconds"], doc["committed"])
                if not doc["closed"]:
                    total += self._crash_charge(doc["workers"])
        return total

    def _write_charge(self, name, seconds, committed, workers, closed, pids) -> None:
        doc = {
            "seconds": seconds,
            "committed": committed,
            "workers": workers,
            "closed": closed,
            "pids": pids,
        }
        _atomic(self.charge_dir / name, json.dumps(doc, sort_keys=True).encode())

    def workers_still_running(self) -> list[int]:
        """The workers of the batches not closed that are still alive."""
        alive = []
        if self.charge_dir.exists():
            for path in sorted(self.charge_dir.glob("b*.json")):
                doc = json.loads(path.read_text("utf-8"))
                if not doc["closed"]:
                    alive += [int(p) for p, c in doc["pids"].items() if still_running(int(p), c)]
        return alive

    def _reconcile_crashes(self) -> None:
        """Close every batch left open by a crash, or refuse while its workers are alive."""
        alive = self.workers_still_running()
        if alive:
            raise SystemExit(f"workers of a crashed batch are still running: {alive}: refused")
        for path in sorted(self.charge_dir.glob("b*.json")):
            doc = json.loads(path.read_text("utf-8"))
            if not doc["closed"]:
                doc["seconds"] = max(doc["seconds"], doc["committed"]) + self._crash_charge(
                    doc["workers"]
                )
                doc["closed"] = True
                doc["reconciled_after_a_crash"] = True
                _atomic(path, json.dumps(doc, sort_keys=True).encode())
                self._log(event="crash_reconciled", batch=path.name, seconds=doc["seconds"])

    def _record_stop(self, state: str) -> str:
        doc = {"state": state, "at": self.clock().isoformat()}
        _atomic(self.stop_path, json.dumps(doc, sort_keys=True).encode())
        return state

    def unresolved_stop(self) -> str | None:
        if self.stop_path.exists():
            return json.loads(self.stop_path.read_text("utf-8"))["state"]
        return None

    def reconcile(self, reason: str) -> None:
        """Record why an unresolved stop may be passed; the stop stays on file, renamed."""
        if not self.stop_path.exists():
            raise SystemExit("there is no unresolved stop")
        doc = json.loads(self.stop_path.read_text("utf-8"))
        doc["reconciled_reason"] = reason
        count = len(list(self.out.glob("stop-reconciled-*.json")))
        _atomic(
            self.out / f"stop-reconciled-{count:03d}.json", json.dumps(doc, sort_keys=True).encode()
        )
        self.stop_path.unlink()
        self._log(event="stop_reconciled", reason=reason)

    def completed(self) -> bool:
        """Every shard done, the last state complete, and no unresolved stop."""
        path = self.out / "state.json"
        if self.unresolved_stop() is not None or not path.exists():
            return False
        return json.loads(path.read_text("utf-8"))["state"] == "complete" and len(
            self._done()
        ) == len(self.shards)

    def _batch(self, todo, workers, spent_hours) -> str | None:
        """Dispatch unit by unit until the batch's end, the cap or the pause. Returns a state that
        ends the run, or ``None`` when the next batch may open."""
        name = f"b{len(list(self.charge_dir.glob('b*.json'))):05d}.json"
        controller_start = time.process_time()
        counter = mp.Value("i", 0)
        opened = time.monotonic()
        tracker = CpuTracker()
        stop_dog = threading.Event()
        flag: dict = {}
        box = {"committed": 0.0}
        pending: dict = {}
        queue = list(todo)
        args = dict(self.shards)
        pool = ProcessPoolExecutor(
            max_workers=workers,
            initializer=_init_worker,
            initargs=(counter, self.pin, self.initializer, self.check_placement),
        )

        def live_seconds() -> float:
            tracker.observe(list(getattr(pool, "_processes", {}) or {}))
            own = tracker.total() + time.process_time() - controller_start
            if tracker.failing_since is not None:  # conservative: every worker, for all that time
                own += workers * (time.monotonic() - tracker.failing_since)
            return max(own, box["committed"])

        def watchdog() -> None:
            limit = self.cap_hours * OVER_CAP_FACTOR
            last_charge = 0.0
            known = 0
            while not stop_dog.wait(0.5):
                seconds = live_seconds()
                pids = tracker.identities()
                if time.monotonic() - last_charge >= CHARGE_SECONDS or len(pids) != known:
                    self._write_charge(name, seconds, box["committed"], workers, False, pids)
                    last_charge, known = time.monotonic(), len(pids)
                used = spent_hours + seconds / 3600.0
                if used > limit and "over" not in flag:
                    flag["over"] = used
                    for proc in list((getattr(pool, "_processes", {}) or {}).values()):
                        proc.kill()

        self._write_charge(name, 0.0, 0.0, workers, False, {})
        dog = threading.Thread(target=watchdog, daemon=True)
        dog.start()
        error = None
        window = self.batch_seconds - self.max_shard_seconds
        try:
            while queue or pending:
                while queue and len(pending) < workers and "over" not in flag:
                    if time.monotonic() - opened >= window or self.clock() >= self.pause_at:
                        break
                    if spent_hours + live_seconds() / 3600.0 >= self.cap_hours:
                        break
                    if "slow" in flag or tracker.failing_since is not None:
                        break
                    sid, arg = queue.pop(0)
                    pending[pool.submit(_call, self.fn, sid, arg)] = time.monotonic()
                if not pending:
                    break
                finished, _ = wait(pending, timeout=1.0, return_when=FIRST_COMPLETED)
                for future in finished:
                    wall = time.monotonic() - pending.pop(future)
                    sid, data, cpu, _ = future.result()
                    self._store(sid, args[sid], data, cpu, workers)
                    box["committed"] += cpu
                    if wall > self.max_shard_seconds:
                        flag["slow"] = (sid, wall)
        except Exception as exc:  # noqa: BLE001 - kept until every worker has stopped
            error = exc
        finally:
            # the watchdog keeps counting, and can still end the workers, until they have stopped
            pool.shutdown(wait=True, cancel_futures=True)
            stop_dog.set()
            dog.join()
            pids = tracker.identities()
            self._write_charge(name, live_seconds(), box["committed"], workers, True, pids)
            failing = tracker.failing_since is not None
            if tracker.failed_queries:
                self._log(event="failed_cpu_queries", count=tracker.failed_queries)
            tracker.close()
        if "over" in flag:
            self._log(event="over_cap", used_hours=flag["over"], cap_hours=self.cap_hours)
            return self._record_stop("over the cap: the workers were ended")
        if error is not None:
            raise error
        if failing:
            return self._record_stop("stopped: the CPU accounting failed")
        if "slow" in flag:
            sid, wall = flag["slow"]
            self._log(event="shard_over_limit", shard=sid, seconds=wall)
            return self._record_stop(f"stopped: shard {sid} ran beyond its declared limit")
        return None

    def execute(self) -> str:
        """Run batches until done, the cap, the pause or a stop; returns the state."""
        for folder in (self.data_dir, self.side_dir, self.charge_dir):
            folder.mkdir(parents=True, exist_ok=True)
        stopped = self.unresolved_stop()
        if stopped is not None:
            raise SystemExit(f"an unresolved stop ({stopped}): reconcile it first")
        self._reconcile_crashes()
        if self.check_placement:
            check_controller_placement()
        set_below_normal()
        # in the parent, so that a worker has it before anything imports numpy: the bytes of a
        # floating-point result may depend on the number of threads
        for name in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
            os.environ[name] = "1"
        state = "complete"
        while True:
            todo = [s for s in self.shards if s[0] not in self._done()]
            if not todo:
                break
            spent = self.spent_seconds() / 3600.0
            moment = self.clock()
            if moment >= self.pause_at:
                state = "paused: the maintainer's pause time"
                break
            if spent >= self.cap_hours:
                state = "stopped: the cap is reached"
                break
            workers = workers_for(moment, self.workers)
            self._log(event="batch", todo=len(todo), workers=workers, spent_hours=spent)
            ended = self._batch(todo, workers, spent)
            if ended is not None:
                state = ended
                break
        doc = {
            "state": state,
            "shards": len(self.shards),
            "done": len(self._done()),
            "spent_hours": self.spent_seconds() / 3600.0,
            "cap_hours": self.cap_hours,
            "fingerprint": self.fingerprint,
        }
        _atomic(self.out / "state.json", (json.dumps(doc, sort_keys=True) + "\n").encode())
        return state

    def assemble(self) -> bytes:
        """Every shard's bytes in schedule order; refused while a shard is missing or a stop is
        unresolved."""
        stopped = self.unresolved_stop()
        if stopped is not None:
            raise SystemExit(f"an unresolved stop ({stopped}): reconcile it first")
        done = self._done()
        missing = [s for s, _ in self.shards if s not in done]
        if missing:
            raise SystemExit(f"{len(missing)} shards are not done")
        return b"".join(self._paths(s)[0].read_bytes() for s, _ in self.shards)
