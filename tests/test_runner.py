import os
import subprocess
import sys
import textwrap

import pytest

from refute.core import runner
from refute.core.runner import (
    WORKERS_ENV,
    default_workers,
    run_processes,
    run_threads,
    selftest_task,
    selftest_thread_env,
    usable_cpus,
)

THREAD_ENV = ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS")


def test_default_workers_is_usable_cpus_minus_two(monkeypatch):
    monkeypatch.delenv(WORKERS_ENV, raising=False)
    assert default_workers() == max(1, usable_cpus() - 2)


@pytest.mark.parametrize(("cpus", "workers"), [(1, 1), (2, 1), (3, 1), (4, 2), (6, 4), (24, 22)])
def test_default_workers_from_the_allowed_cpus(monkeypatch, cpus, workers):
    monkeypatch.delenv(WORKERS_ENV, raising=False)
    monkeypatch.setattr(runner, "usable_cpus", lambda: cpus)
    assert default_workers() == workers


def test_usable_cpus_is_within_cpu_count():
    assert 1 <= usable_cpus() <= (os.cpu_count() or 1)


def test_windows_api_failure_never_falls_back_to_the_machine_total(monkeypatch):
    def fail():
        raise OSError("GetProcessAffinityMask failed")

    monkeypatch.setattr(runner, "_windows_affinity_count", fail)
    with pytest.raises(OSError):
        usable_cpus("win32")
    monkeypatch.delenv(WORKERS_ENV, raising=False)
    monkeypatch.setattr(runner, "usable_cpus", lambda: usable_cpus("win32"))
    with pytest.raises(OSError):
        default_workers()
    monkeypatch.setenv(WORKERS_ENV, "3")  # the explicit override still works
    assert default_workers() == 3


def test_workers_env_overrides_the_default(monkeypatch):
    monkeypatch.setenv(WORKERS_ENV, "7")
    assert default_workers() == 7
    monkeypatch.setenv(WORKERS_ENV, "")
    assert default_workers() == max(1, usable_cpus() - 2)
    for bad in ("0", "-2", "two", "1.5"):
        monkeypatch.setenv(WORKERS_ENV, bad)
        with pytest.raises(ValueError, match=WORKERS_ENV):
            default_workers()


# A child process reads its affinity directly from the operating system (not through
# refute), restricts itself to its first k allowed CPUs, reads the mask back, and then
# reports usable_cpus() and default_workers(). It prints "SKIP <n>" when fewer than k
# CPUs are allowed. The parent's affinity is never changed.
_CHILD = textwrap.dedent(
    """
    import os, sys
    k = int(sys.argv[1])
    if sys.platform == "win32":
        import ctypes
        from ctypes import wintypes
        k32 = ctypes.WinDLL("kernel32", use_last_error=True)
        k32.GetCurrentProcess.restype = wintypes.HANDLE
        k32.GetProcessAffinityMask.argtypes = [
            wintypes.HANDLE, ctypes.POINTER(ctypes.c_size_t), ctypes.POINTER(ctypes.c_size_t)
        ]
        k32.GetProcessAffinityMask.restype = wintypes.BOOL
        k32.SetProcessAffinityMask.argtypes = [wintypes.HANDLE, ctypes.c_size_t]
        k32.SetProcessAffinityMask.restype = wintypes.BOOL

        def allowed():
            proc, system = ctypes.c_size_t(), ctypes.c_size_t()
            if not k32.GetProcessAffinityMask(
                k32.GetCurrentProcess(), ctypes.byref(proc), ctypes.byref(system)
            ):
                raise SystemExit("GetProcessAffinityMask failed")
            return [i for i in range(64) if proc.value >> i & 1]

        bits = allowed()
        if len(bits) < k:
            print("SKIP", len(bits))
            raise SystemExit(0)
        mask = sum(1 << i for i in bits[:k])
        if not k32.SetProcessAffinityMask(k32.GetCurrentProcess(), mask):
            raise SystemExit("SetProcessAffinityMask failed")
        raw = len(allowed())
    else:
        cpus = sorted(os.sched_getaffinity(0))
        if len(cpus) < k:
            print("SKIP", len(cpus))
            raise SystemExit(0)
        os.sched_setaffinity(0, cpus[:k])
        raw = len(os.sched_getaffinity(0))
    os.environ.pop("REFUTE_WORKERS", None)
    from refute.core.runner import default_workers, usable_cpus
    print(raw, usable_cpus(), default_workers())
    """
)


@pytest.mark.skipif(
    not (sys.platform == "win32" or hasattr(os, "sched_setaffinity")),
    reason="needs Windows or os.sched_setaffinity to restrict the affinity of a child",
)
@pytest.mark.parametrize(("k", "expected_workers"), [(1, 1), (2, 1), (4, 2), (6, 4)])
def test_default_workers_follows_the_affinity_mask(k, expected_workers):
    env = {key: value for key, value in os.environ.items() if key != WORKERS_ENV}
    out = subprocess.run(
        [sys.executable, "-c", _CHILD, str(k)],
        capture_output=True,
        text=True,
        check=True,
        env=env,
    ).stdout.split()
    if out[0] == "SKIP":
        pytest.skip(f"the operating system allows this process only {out[1]} CPUs, k = {k}")
    raw, cpus, workers = map(int, out)
    assert (raw, cpus, workers) == (k, k, expected_workers)


def test_process_pool_runs_in_other_processes_and_keeps_order():
    results = run_processes(selftest_task, [1, 2, 3, 4, 5], workers=2)
    assert [value for _, value in results] == [1, 4, 9, 16, 25]
    assert any(pid != os.getpid() for pid, _ in results)


def test_single_worker_runs_in_process():
    results = run_processes(selftest_task, [3, 4], workers=1)
    assert [value for _, value in results] == [9, 16]
    assert all(pid == os.getpid() for pid, _ in results)


# W2.16 (#32): an in-process run leaves os.environ exactly as it was -----------------


def _set_thread_env(monkeypatch, preset):
    for name in THREAD_ENV:
        if preset is None:
            monkeypatch.delenv(name, raising=False)
        else:
            monkeypatch.setenv(name, preset)


@pytest.mark.parametrize("preset", [None, "4"])
@pytest.mark.parametrize(("workers", "tasks"), [(1, [0, 1]), (4, [0])])
def test_in_process_run_leaves_the_environment_unchanged(monkeypatch, preset, workers, tasks):
    _set_thread_env(monkeypatch, preset)
    before = dict(os.environ)
    results = run_processes(selftest_thread_env, tasks, workers=workers)
    assert all(pid == os.getpid() for pid, _ in results)
    assert all(seen == {name: (preset or "1") for name in THREAD_ENV} for _, seen in results)
    assert dict(os.environ) == before


@pytest.mark.parametrize("preset", [None, "4"])
def test_in_process_run_restores_the_environment_after_an_exception(monkeypatch, preset):
    _set_thread_env(monkeypatch, preset)
    before = dict(os.environ)

    def boom(_):
        raise RuntimeError("task failed")

    with pytest.raises(RuntimeError, match="task failed"):
        run_processes(boom, [0], workers=1)
    assert dict(os.environ) == before


# A fresh child process where the first import of matplotlib cannot use MPLCONFIGDIR
# (it names a file), so matplotlib sets MPLCONFIGDIR to a temporary directory during
# init_worker(). The whole environment must be the same after the run.
_MPL_CHILD = textwrap.dedent(
    """
    import os
    from refute.core.runner import run_processes
    before = dict(os.environ)
    seen = run_processes(lambda _: os.environ.get("MPLCONFIGDIR"), [0], workers=1)[0]
    print(seen != before["MPLCONFIGDIR"], dict(os.environ) == before)
    """
)


def test_in_process_run_restores_a_variable_set_by_the_matplotlib_import(tmp_path):
    not_a_dir = tmp_path / "mplconfig-is-a-file"
    not_a_dir.write_text("", encoding="utf-8")
    scratch = tmp_path / "tmp"
    scratch.mkdir()
    env = {key: value for key, value in os.environ.items() if key != "MPLCONFIGDIR"}
    env.update(MPLCONFIGDIR=str(not_a_dir), TMP=str(scratch), TEMP=str(scratch))
    env["TMPDIR"] = str(scratch)
    out = subprocess.run(
        [sys.executable, "-c", _MPL_CHILD],
        capture_output=True,
        text=True,
        check=True,
        env=env,
    ).stdout.split()
    assert out == ["True", "True"]  # matplotlib changed it inside; restored after


def test_spawned_workers_set_thread_variables_for_themselves(monkeypatch):
    _set_thread_env(monkeypatch, None)
    before = dict(os.environ)
    results = run_processes(selftest_thread_env, [0, 1, 2], workers=2)
    assert all(pid != os.getpid() for pid, _ in results)
    assert all(seen == {name: "1" for name in THREAD_ENV} for _, seen in results)
    assert dict(os.environ) == before


def test_invalid_worker_count():
    with pytest.raises(ValueError):
        run_processes(selftest_task, [1], workers=0)


def test_threads_keep_order():
    assert run_threads(lambda x: x + 1, [1, 2, 3], workers=3) == [2, 3, 4]
    assert run_processes(selftest_task, [], workers=2) == []
