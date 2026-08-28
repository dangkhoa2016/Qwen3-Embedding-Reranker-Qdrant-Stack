from __future__ import annotations

import gc
import os
import time
from pathlib import Path
from typing import Callable

import torch

from .config import Settings
from .embedding_engine import EmbeddingEngine
from .memory import MemorySnapshot, capture_memory_snapshot
from .model_locator import ModelResolutionError, resolve_model_path
from .process_lock import ProcessSingletonLock
from .reranker_engine import RerankerEngine
from .gguf_reranker_engine import GGUFRerankerEngine


class MemoryHeadroomError(RuntimeError):
    pass


def _event_delta(before: MemorySnapshot, after: MemorySnapshot, key: str) -> int:
    return int(after.cgroup_events.get(key, 0)) - int(before.cgroup_events.get(key, 0))


class DualModelRuntime:
    def __init__(
        self,
        settings: Settings,
        *,
        embedding_engine=None,
        reranker_engine=None,
        memory_provider: Callable[[], MemorySnapshot] = capture_memory_snapshot,
        process_lock=None,
    ):
        self.settings = settings
        self._memory_provider = memory_provider
        self._lock = process_lock or ProcessSingletonLock(settings.runtime_lock_path)
        self.ready = False
        self.load_error: str | None = None
        self.memory_history: dict[str, dict[str, object]] = {}
        self.started_at = time.time()
        self.counters = {
            "embedding_requests": 0,
            "embedding_items": 0,
            "rerank_requests": 0,
            "rerank_documents": 0,
        }
        self.timings_ms = {"embedding_total": 0.0, "rerank_total": 0.0}

        if embedding_engine is None:
            embedding_path = self._resolve_path("embedding")
            embedding_engine = EmbeddingEngine(settings, embedding_path)
        if reranker_engine is None:
            if self.settings.reranker_backend == "llama_cpp":
                if self.settings.quantization_mode != "none":
                    raise ValueError("QUANTIZATION_MODE must be none when RERANKER_BACKEND=llama_cpp")
                reranker_engine = GGUFRerankerEngine(settings)
            else:
                reranker_path = self._resolve_path("reranker")
                reranker_engine = RerankerEngine(settings, reranker_path)
        self.embedding_engine = embedding_engine
        self.reranker_engine = reranker_engine

    def _resolve_path(self, role: str):
        explicit = self.settings.embedding_model_path if role == "embedding" else self.settings.reranker_model_path
        try:
            return resolve_model_path(role, explicit, self.settings.kaggle_input_root)
        except ModelResolutionError:
            if not self.settings.allow_remote_model_download:
                raise
            return self.settings.embedding_model_id if role == "embedding" else self.settings.reranker_model_id

    def _capture(self, label: str) -> MemorySnapshot:
        snap = self._memory_provider()
        self.memory_history[label] = snap.to_dict()
        return snap

    @staticmethod
    def _assert_no_oom_delta(before: MemorySnapshot, after: MemorySnapshot) -> None:
        oom = _event_delta(before, after, "oom")
        kill = _event_delta(before, after, "oom_kill")
        if oom > 0 or kill > 0:
            raise RuntimeError(f"cgroup OOM event increased during model load: oom_delta={oom}, oom_kill_delta={kill}")

    def _configure_torch(self) -> None:
        if self.settings.torch_num_threads > 0:
            torch.set_num_threads(self.settings.torch_num_threads)
        try:
            torch.set_num_interop_threads(self.settings.torch_num_interop_threads)
        except RuntimeError:
            # PyTorch permits this only before inter-op work starts. Existing notebook state may have initialized it.
            pass

    def load_all(self) -> None:
        if self.ready:
            return
        self.load_error = None
        self._lock.acquire()
        try:
            self._configure_torch()
            baseline = self._capture("before_load")

            self.embedding_engine.load()
            if self.settings.warmup_enabled:
                self.embedding_engine.warmup()
            gc.collect()
            after_embedding = self._capture("after_embedding")
            self._assert_no_oom_delta(baseline, after_embedding)
            if after_embedding.system_available_gib < self.settings.second_model_min_available_gib:
                raise MemoryHeadroomError(
                    "refusing to load reranker: system MemAvailable "
                    f"{after_embedding.system_available_gib:.1f} GiB is below "
                    f"SECOND_MODEL_MIN_AVAILABLE_GIB={self.settings.second_model_min_available_gib:.1f}"
                )

            self.reranker_engine.load()
            if self.settings.warmup_enabled:
                self.reranker_engine.warmup()
            gc.collect()
            after_reranker = self._capture("after_reranker")
            self._assert_no_oom_delta(baseline, after_reranker)
            if after_reranker.system_available_gib < self.settings.final_min_available_gib:
                raise MemoryHeadroomError(
                    "refusing readiness: final system MemAvailable "
                    f"{after_reranker.system_available_gib:.1f} GiB is below "
                    f"FINAL_MIN_AVAILABLE_GIB={self.settings.final_min_available_gib:.1f}"
                )
            self.ready = True
        except Exception as exc:
            self.ready = False
            self.load_error = f"{type(exc).__name__}: {exc}"
            for engine in (self.reranker_engine, self.embedding_engine):
                close = getattr(engine, "close", None)
                if close is not None:
                    close()
            self._lock.release()
            raise

    def close(self) -> None:
        self.ready = False
        for engine in (self.reranker_engine, self.embedding_engine):
            close = getattr(engine, "close", None)
            if close is not None:
                close()
        self._lock.release()

    def _require_ready(self) -> None:
        if not self.ready:
            raise RuntimeError(f"runtime is not ready: {self.load_error or 'models not loaded'}")

    def embed(self, texts: list[str], input_type: str, instruction: str | None):
        self._require_ready()
        start = time.perf_counter()
        result = self.embedding_engine.embed(texts, input_type, instruction)
        elapsed = (time.perf_counter() - start) * 1000
        self.counters["embedding_requests"] += 1
        self.counters["embedding_items"] += len(texts)
        self.timings_ms["embedding_total"] += elapsed
        return result, elapsed

    def rerank(self, query: str, documents: list[str], instruction: str | None):
        self._require_ready()
        start = time.perf_counter()
        result = self.reranker_engine.rerank(query, documents, instruction)
        elapsed = (time.perf_counter() - start) * 1000
        self.counters["rerank_requests"] += 1
        self.counters["rerank_documents"] += len(documents)
        self.timings_ms["rerank_total"] += elapsed
        return result, elapsed

    def status(self) -> dict[str, object]:
        return {
            "ready": self.ready,
            "load_error": self.load_error,
            "uptime_seconds": round(time.time() - self.started_at, 3),
            "models": [self.embedding_engine.metadata(), self.reranker_engine.metadata()],
            "memory": self.memory_history,
        }

    def stats(self) -> dict[str, object]:
        current = self._memory_provider().to_dict()
        return {
            **self.status(),
            "counters": dict(self.counters),
            "timings_ms": dict(self.timings_ms),
            "current_memory": current,
            "pid": os.getpid(),
        }
