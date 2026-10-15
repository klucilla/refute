"""Parallel execution.

- I/O-bound work (downloads) uses a small thread pool.
- CPU-bound work (analysis) uses ``ProcessPoolExecutor`` with the ``spawn`` start
  method on every platform, so behaviour is identical on Windows and Linux.

The default number of analysis workers is the number of CPUs this process may use
under its CPU affinity mask, minus 2 (at least 1); see :func:`usable_cpus`. On Windows
neither ``os.cpu_count()`` nor ``os.process_cpu_count()`` reflects the affinity mask
(measured on Python 3.13.5, 2026-10-14), so the mask is read from the Windows API.
The environment variable ``REFUTE_WORKERS`` (a positive integer) overrides it; CI sets
it to every core of the runner. The number of workers should change only the
execution, preserving the scientific results
(docs/validation/v0.2.1/workers-equivalence-acceptance.md).
Tasks must be top-level functions with picklable arguments.
"""

from __future__ import annotations

import multiprocessing
import os
import sys
from collections.abc import Callable, Sequence
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from typing import Any

_SINGLE_THREAD_ENV = (
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
)


WORKERS_ENV = "REFUTE_WORKERS"


def _windows_affinity_count() -> int:
    """Bits set in the process affinity mask. Raises ``OSError`` when the mask cannot
    be read: the machine's total is never used in its place."""
    import ctypes
    from ctypes import wintypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.GetCurrentProcess.restype = wintypes.HANDLE
    kernel32.GetProcessAffinityMask.argtypes = [
        wintypes.HANDLE,
        ctypes.POINTER(ctypes.c_size_t),
        ctypes.POINTER(ctypes.c_size_t),
    ]
    kernel32.GetProcessAffinityMask.restype = wintypes.BOOL
    process_mask = ctypes.c_size_t()
    system_mask = ctypes.c_size_t()
    ok = kernel32.GetProcessAffinityMask(
        kernel32.GetCurrentProcess(), ctypes.byref(process_mask), ctypes.byref(system_mask)
    )
    if not ok:
        raise OSError(ctypes.get_last_error(), "GetProcessAffinityMask failed")
    if process_mask.value == 0:
        raise OSError("GetProcessAffinityMask returned an empty process mask")
    return bin(process_mask.value).count("1")


def usable_cpus(platform: str = sys.platform) -> int:
    """Number of logical CPUs this process may run on, under its affinity mask.

    Windows: ``GetProcessAffinityMask`` (the mask of the process's processor group); if
    it fails, ``OSError`` is raised (set ``REFUTE_WORKERS`` to run anyway). Linux and
    other systems with ``os.sched_getaffinity``: that set. Otherwise
    ``os.cpu_count()``. Always at least 1.
    """
    if platform == "win32":
        return max(1, _windows_affinity_count())
    if hasattr(os, "sched_getaffinity"):
        return max(1, len(os.sched_getaffinity(0)))
    return max(1, os.cpu_count() or 1)


def default_workers() -> int:
    override = os.environ.get(WORKERS_ENV, "").strip()
    if override:
        if not override.isdigit() or int(override) < 1:
            raise ValueError(f"{WORKERS_ENV} must be a positive integer, got {override!r}")
        return int(override)
    return max(1, usable_cpus() - 2)


def init_worker() -> None:
    """Worker initializer: one BLAS thread per process and a non-interactive plot backend."""
    for name in _SINGLE_THREAD_ENV:
        os.environ.setdefault(name, "1")
    import matplotlib

    matplotlib.use("Agg")


def _restore_environ(saved: dict[str, str]) -> None:
    for name in [n for n in os.environ if n not in saved]:
        del os.environ[name]
    for name, value in saved.items():
        if os.environ.get(name) != value:
            os.environ[name] = value


def run_processes[T, R](fn: Callable[[T], R], tasks: Sequence[T], workers: int) -> list[R]:
    """Run ``fn`` over ``tasks`` in worker processes; results keep the task order.

    With ``workers <= 1`` (or a single task) everything runs in the current process,
    which gives identical results and simpler debugging.
    """
    if workers < 1:
        raise ValueError("workers must be >= 1")
    if not tasks:
        return []
    if workers == 1 or len(tasks) == 1:
        # init_worker() changes os.environ (the thread variables, and the first import
        # of matplotlib may set MPLCONFIGDIR). In the current process the whole
        # environment is restored afterwards, as it would be with worker processes,
        # so nothing leaks into later code (#32).
        saved = dict(os.environ)
        try:
            init_worker()
            return [fn(task) for task in tasks]
        finally:
            _restore_environ(saved)
    context = multiprocessing.get_context("spawn")
    with ProcessPoolExecutor(
        max_workers=min(workers, len(tasks)), mp_context=context, initializer=init_worker
    ) as pool:
        futures = [pool.submit(fn, task) for task in tasks]
        return [future.result() for future in futures]


def run_threads[T, R](fn: Callable[[T], R], tasks: Sequence[T], workers: int = 4) -> list[R]:
    """Run ``fn`` over ``tasks`` in threads (for network I/O); results keep the task order."""
    if not tasks:
        return []
    with ThreadPoolExecutor(max_workers=max(1, min(workers, len(tasks)))) as pool:
        futures = [pool.submit(fn, task) for task in tasks]
        return [future.result() for future in futures]


def selftest_task(value: Any) -> tuple[int, Any]:
    """Tiny picklable task used by the test suite to exercise the process pool."""
    return os.getpid(), value * value


def selftest_thread_env(_: Any) -> tuple[int, dict[str, str | None]]:
    """Picklable task used by the test suite: the thread variables a worker sees."""
    return os.getpid(), {name: os.environ.get(name) for name in _SINGLE_THREAD_ENV}
