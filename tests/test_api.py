from contextlib import asynccontextmanager

import torch
from fastapi.testclient import TestClient

from qwen_dual_server.api import create_app
from qwen_dual_server.config import Settings
from qwen_dual_server.gate import QueueFullError


class FakeRuntime:
    def __init__(self, ready=True): self.ready=ready; self.load_error=None
    def load_all(self): self.ready=True
    def close(self): pass
    def status(self): return {"ready":self.ready,"load_error":self.load_error,"models":[{"id":"embed","role":"embedding"},{"id":"rerank","role":"reranker"}]}
    def stats(self): return {**self.status(), "counters":{}}
    def embed(self, texts, input_type, instruction):
        return torch.tensor([[1.0,0.0] for _ in texts], dtype=torch.float32), 12.5
    def rerank(self, query, documents, instruction):
        return ([{"index":i,"score":0.9-i*0.1} for i in range(len(documents))], 22.0)


class RejectGate:
    @asynccontextmanager
    async def slot(self):
        raise QueueFullError("busy")
        yield 0.0
    def snapshot(self): return {"active":1,"waiters":1}


def make_settings(monkeypatch, **overrides):
    monkeypatch.setenv("DUAL_API_KEY", "secret")
    monkeypatch.setenv("LOAD_MODELS_ON_STARTUP", "0")
    return Settings(**overrides)


def auth(): return {"Authorization":"Bearer secret"}


def test_health_is_public_and_ready_reflects_runtime(monkeypatch):
    app=create_app(make_settings(monkeypatch), FakeRuntime(ready=False))
    with TestClient(app) as client:
        assert client.get("/health").status_code == 200
        r=client.get("/ready")
        assert r.status_code == 503
        assert r.json()["ready"] is False
        assert "models" not in r.json()
        assert "load_error" not in r.json()


def test_v1_routes_require_bearer_auth(monkeypatch):
    app=create_app(make_settings(monkeypatch), FakeRuntime())
    with TestClient(app) as client:
        assert client.get("/v1/models").status_code == 401
        assert client.get("/v1/models", headers={"Authorization":"Bearer wrong"}).status_code == 401
        assert client.get("/v1/models", headers=auth()).status_code == 200


def test_embeddings_endpoint_returns_float32_vectors(monkeypatch):
    app=create_app(make_settings(monkeypatch), FakeRuntime())
    with TestClient(app) as client:
        r=client.post("/v1/embeddings", headers=auth(), json={"input":["a","b"],"input_type":"query"})
        assert r.status_code == 200
        body=r.json()
        assert body["object"] == "list"
        assert body["data"][0]["embedding"] == [1.0,0.0]
        assert body["meta"]["inference_ms"] == 12.5
        assert body["meta"]["queue_wait_ms"] >= 0


def test_rerank_can_return_documents(monkeypatch):
    app=create_app(make_settings(monkeypatch), FakeRuntime())
    with TestClient(app) as client:
        r=client.post("/v1/rerank", headers=auth(), json={
            "query":"q","documents":["doc0","doc1"],"return_documents":True
        })
        assert r.status_code == 200
        body=r.json()
        assert body["results"][0] == {"index":0,"score":0.9,"document":"doc0"}


def test_request_limits_are_enforced(monkeypatch):
    app=create_app(make_settings(monkeypatch, max_rerank_documents=2, max_text_chars=256), FakeRuntime())
    with TestClient(app) as client:
        too_many=client.post("/v1/rerank", headers=auth(), json={"query":"q","documents":["a","b","c"]})
        assert too_many.status_code == 422
        too_large=client.post("/v1/embeddings", headers=auth(), json={"input":"x"*257})
        assert too_large.status_code == 413


def test_queue_full_returns_429(monkeypatch):
    app=create_app(make_settings(monkeypatch), FakeRuntime(), gate=RejectGate())
    with TestClient(app) as client:
        r=client.post("/v1/embeddings", headers=auth(), json={"input":"hello"})
        assert r.status_code == 429
        assert r.json()["detail"] == "inference queue is full"


def test_rate_limit_is_per_client(monkeypatch):
    app=create_app(make_settings(monkeypatch, rate_limit_requests=1, rate_limit_window_seconds=60), FakeRuntime())
    with TestClient(app) as client:
        assert client.get("/v1/models", headers=auth()).status_code == 200
        assert client.get("/v1/models", headers=auth()).status_code == 429
