import pytest
from qwen_dual_server.config import Settings
from qwen_dual_server.memory import MemorySnapshot
from qwen_dual_server.runtime import DualModelRuntime, MemoryHeadroomError


class FakeEngine:
    def __init__(self, role, events):
        self.role=role; self.events=events
    def load(self): self.events.append(f"{self.role}:load")
    def warmup(self): self.events.append(f"{self.role}:warmup")
    def metadata(self): return {"role":self.role, "loaded": True}
    def embed(self, texts, input_type, instruction): self.events.append("embedding:infer"); return [[1.0, 0.0]]
    def rerank(self, query, docs, instruction): self.events.append("reranker:infer"); return [{"index":0,"score":0.9}]


class FakeLock:
    def __init__(self, events): self.events=events
    def acquire(self): self.events.append("lock:acquire")
    def release(self): self.events.append("lock:release")


def snap(avail_gib, oom=0, oom_kill=0):
    gib=1024**3
    return MemorySnapshot(
        process_rss_bytes=1*gib,
        system_available_bytes=int(avail_gib*gib),
        system_total_bytes=30*gib,
        cgroup_current_bytes=5*gib,
        cgroup_peak_bytes=6*gib,
        cgroup_max_bytes=30*gib,
        cgroup_events={"oom":oom,"oom_kill":oom_kill},
    )


def make_settings(monkeypatch, threshold=10.0):
    monkeypatch.setenv("DUAL_API_KEY", "secret")
    monkeypatch.setenv("SECOND_MODEL_MIN_AVAILABLE_GIB", str(threshold))
    monkeypatch.setenv("LOAD_MODELS_ON_STARTUP", "0")
    return Settings()


def test_load_order_warms_embedding_before_second_model(monkeypatch):
    events=[]; samples=iter([snap(25), snap(18), snap(11)])
    rt=DualModelRuntime(
        make_settings(monkeypatch),
        embedding_engine=FakeEngine("embedding", events),
        reranker_engine=FakeEngine("reranker", events),
        memory_provider=lambda: next(samples),
        process_lock=FakeLock(events),
    )
    rt.load_all()
    assert events[:5] == ["lock:acquire","embedding:load","embedding:warmup","reranker:load","reranker:warmup"]
    assert rt.ready is True
    assert rt.status()["load_error"] is None


def test_memory_gate_blocks_reranker_before_oom(monkeypatch):
    events=[]; samples=iter([snap(25), snap(7)])
    rt=DualModelRuntime(
        make_settings(monkeypatch, threshold=10.0),
        embedding_engine=FakeEngine("embedding", events),
        reranker_engine=FakeEngine("reranker", events),
        memory_provider=lambda: next(samples),
        process_lock=FakeLock(events),
    )
    try:
        rt.load_all()
    except MemoryHeadroomError as exc:
        assert "7.0" in str(exc)
    else:
        raise AssertionError("expected MemoryHeadroomError")
    assert "reranker:load" not in events
    assert rt.ready is False
    assert rt.status()["load_error"] is not None


def test_runtime_rejects_new_oom_event_during_load(monkeypatch):
    events=[]; samples=iter([snap(25,0,0), snap(18,1,0)])
    rt=DualModelRuntime(
        make_settings(monkeypatch),
        embedding_engine=FakeEngine("embedding", events),
        reranker_engine=FakeEngine("reranker", events),
        memory_provider=lambda: next(samples),
        process_lock=FakeLock(events),
    )
    try:
        rt.load_all()
    except RuntimeError as exc:
        assert "cgroup OOM" in str(exc)
    else:
        raise AssertionError("expected runtime OOM delta failure")
    assert rt.ready is False


def test_final_memory_gate_blocks_readiness_after_reranker(monkeypatch):
    events=[]; samples=iter([snap(25), snap(18), snap(3)])
    monkeypatch.setenv("FINAL_MIN_AVAILABLE_GIB", "4.0")
    rt=DualModelRuntime(
        make_settings(monkeypatch),
        embedding_engine=FakeEngine("embedding", events),
        reranker_engine=FakeEngine("reranker", events),
        memory_provider=lambda: next(samples),
        process_lock=FakeLock(events),
    )
    with pytest.raises(MemoryHeadroomError, match="final system MemAvailable"):
        rt.load_all()
    assert rt.ready is False


def test_startup_failure_releases_singleton_lock(monkeypatch):
    events=[]; samples=iter([snap(25), snap(7)])
    rt=DualModelRuntime(
        make_settings(monkeypatch, threshold=10.0),
        embedding_engine=FakeEngine("embedding", events),
        reranker_engine=FakeEngine("reranker", events),
        memory_provider=lambda: next(samples),
        process_lock=FakeLock(events),
    )
    with pytest.raises(MemoryHeadroomError):
        rt.load_all()
    assert events[-1] == "lock:release"


def test_startup_failure_closes_loaded_engines_before_lock_release(monkeypatch):
    events=[]; samples=iter([snap(25), snap(18), snap(3)])
    monkeypatch.setenv("FINAL_MIN_AVAILABLE_GIB", "4.0")

    class ClosableEngine(FakeEngine):
        def close(self): self.events.append(f"{self.role}:close")

    rt=DualModelRuntime(
        make_settings(monkeypatch),
        embedding_engine=ClosableEngine("embedding", events),
        reranker_engine=ClosableEngine("reranker", events),
        memory_provider=lambda: next(samples),
        process_lock=FakeLock(events),
    )
    with pytest.raises(MemoryHeadroomError):
        rt.load_all()
    assert events[-3:] == ["reranker:close", "embedding:close", "lock:release"]
