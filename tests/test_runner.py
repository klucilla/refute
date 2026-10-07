import os

import pytest

from refute.core.runner import default_workers, run_processes, run_threads, selftest_task


def test_default_workers_is_cpu_count_minus_two():
    assert default_workers() == max(1, (os.cpu_count() or 1) - 2)


def test_process_pool_runs_in_other_processes_and_keeps_order():
    results = run_processes(selftest_task, [1, 2, 3, 4, 5], workers=2)
    assert [value for _, value in results] == [1, 4, 9, 16, 25]
    assert any(pid != os.getpid() for pid, _ in results)


def test_single_worker_runs_in_process():
    results = run_processes(selftest_task, [3, 4], workers=1)
    assert [value for _, value in results] == [9, 16]
    assert all(pid == os.getpid() for pid, _ in results)


def test_invalid_worker_count():
    with pytest.raises(ValueError):
        run_processes(selftest_task, [1], workers=0)


def test_threads_keep_order():
    assert run_threads(lambda x: x + 1, [1, 2, 3], workers=3) == [2, 3, 4]
    assert run_processes(selftest_task, [], workers=2) == []
