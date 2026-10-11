"""Parallel execution.

- I/O-bound work (downloads) uses a small thread pool.
- CPU-bound work (analysis) uses ``ProcessPoolExecutor`` with the ``spawn`` start
  method on every platform, so behaviour is identical on Windows and Linux.

The default number of analysis workers is ``os.cpu_count() - 2`` (at least 1). The
environment variable ``REFUTE_WORKERS`` (a positive integer) overrides it; CI sets it
to every core of the runner. The number of workers should change only the
execution, preserving the scientific results; a test comparing worker counts is
planned (docs/validation/v0.2.1/workers-equivalence-acceptance.md).
Tasks must be top-level functions with picklable arguments.
"""

from __future__ import annotations

import multiprocessing
import os
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


def default_workers() -> int:
    override = os.environ.get(WORKERS_ENV, "").strip()
    if override:
        if not override.isdigit() or int(override) < 1:
            raise ValueError(f"{WORKERS_ENV} must be a positive integer, got {override!r}")
        return int(override)
    return max(1, (os.cpu_count() or 1) - 2)


def init_worker() -> None:
    """Worker initializer: one BLAS thread per process and a non-interactive plot backend."""
    for name in _SINGLE_THREAD_ENV:
        os.environ.setdefault(name, "1")
    import matplotlib

    matplotlib.use("Agg")


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
        init_worker()
        return [fn(task) for task in tasks]
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
