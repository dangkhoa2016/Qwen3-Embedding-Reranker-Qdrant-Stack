import multiprocessing as mp
from pathlib import Path

import pytest
from pydantic import ValidationError

from qwen_dual_server.config import Settings
from qwen_dual_server.memory import bytes_to_gib, parse_memory_events
from qwen_dual_server.process_lock import ProcessSingletonLock, ProcessSingletonLockError


def test_settings_have_cpu_safe_defaults(monkeypatch):
    monkeypatch.setenv("DUAL_API_KEY", "secret")
    s = Settings()
    assert s.model_dtype == "float16"
    assert s.max_seq_length == 512
    assert s.embedding_microbatch_size == 1
    assert s.reranker_microbatch_size == 1
    assert s.max_concurrent_inference == 1
    assert s.second_model_min_available_gib == 10
    assert s.final_min_available_gib == 4
    assert s.allow_remote_model_download is False


def test_settings_reject_unsupported_dtype(monkeypatch):
    monkeypatch.setenv("DUAL_API_KEY", "secret")
    monkeypatch.setenv("MODEL_DTYPE", "int8")
    with pytest.raises(ValidationError):
        Settings()


def test_parse_memory_events_and_gib():
    parsed = parse_memory_events("low 0\nhigh 2\nmax 4\noom 3\noom_kill 1\n")
    assert parsed["oom"] == 3
    assert parsed["oom_kill"] == 1
    assert bytes_to_gib(3 * 1024**3) == 3.0


def _try_lock(path: str, queue):
    try:
        lock = ProcessSingletonLock(Path(path))
        lock.acquire()
    except ProcessSingletonLockError:
        queue.put("blocked")
    else:
        queue.put("acquired")
        lock.release()


def test_process_singleton_lock_blocks_second_process(tmp_path):
    lock_path = tmp_path / "runtime.lock"
    primary = ProcessSingletonLock(lock_path)
    primary.acquire()
    ctx = mp.get_context("spawn")
    q = ctx.Queue()
    p = ctx.Process(target=_try_lock, args=(str(lock_path), q))
    p.start(); p.join(10)
    assert p.exitcode == 0
    assert q.get(timeout=2) == "blocked"
    primary.release()
