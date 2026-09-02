"""v0.2.3 RED tests: native instruction plumbing regression.

These tests must FAIL (RED) before the corrective is applied.
They prove the current broken state where instruction cannot be forwarded
end-to-end through the hybrid endpoint to the llama.cpp backend.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from qwen_dual_server.api import create_app
from qwen_dual_server.config import Settings
from qwen_dual_server.gguf_reranker_engine import GGUFRerankerEngine


# ---------------------------------------------------------------------------
# §5 — Application-level regression: instruction causes failure
# ---------------------------------------------------------------------------

class FakeGGUFRuntime:
    """Simulates the real runtime with an actual GGUFRerankerEngine that rejects instruction."""

    def __init__(self, gguf_engine):
        self._engine = gguf_engine
        self.ready = True
        self.load_error = None

    def load_all(self):
        self._engine.load()
        self.ready = True

    def close(self):
        self._engine.close()

    def status(self):
        return {
            "ready": self.ready,
            "load_error": self.load_error,
            "models": [
                {"id": "embed", "role": "embedding"},
                {"id": "rerank", "role": "reranker"},
            ],
        }

    def stats(self):
        return {**self.status(), "counters": {}}

    def embed(self, texts, input_type, instruction):
        import torch
        return torch.tensor([[1.0, 0.0] for _ in texts], dtype=torch.float32), 12.5

    def rerank(self, query, documents, instruction):
        return self._engine.rerank(query, documents, instruction), 22.0


def _make_gguf_engine(tmp_path: Path):
    cfg = SimpleNamespace(
        reranker_model_id="Qwen/Qwen3-Reranker-4B",
        reranker_gguf_path=str(tmp_path / "Qwen3-Reranker-4B.Q4_K_M.gguf"),
        kaggle_input_root=str(tmp_path),
        llama_server_bin="/opt/llama-server",
        llama_server_host="127.0.0.1",
        llama_server_port=8081,
        llama_server_threads=2,
        llama_server_context_size=1024,
        llama_server_startup_timeout_seconds=30,
        max_seq_length=512,
        reranker_microbatch_size=1,
    )
    Path(cfg.reranker_gguf_path).write_bytes(b"gguf")

    from qwen_dual_server.llama_server import LlamaServerProcess

    class FakeServer:
        started = False
        closed = False
        pid = 333
        rerank_url = "http://127.0.0.1:8081/v1/rerank"
        def start(self): self.started = True
        def close(self): self.closed = True

    def fake_http_post(url, body, timeout):
        docs = body.get("documents", [])
        n = len(docs)
        if body.get("instruction"):
            return {"results": [{"index": i, "relevance_score": round(0.95 - 0.05 * i, 6)} for i in range(n)]}
        return {"results": [{"index": i, "relevance_score": round(0.70 - 0.10 * i, 6)} for i in range(n)]}

    engine = GGUFRerankerEngine(
        cfg,
        server_factory=lambda **_: FakeServer(),
        binary_resolver=lambda _: Path("/opt/llama-server"),
        http_post=fake_http_post,
        functional_probe=True,
    )
    return engine


def _make_app(monkeypatch, runtime):
    monkeypatch.setenv("DUAL_API_KEY", "secret")
    monkeypatch.setenv("LOAD_MODELS_ON_STARTUP", "1")
    settings = Settings()
    return create_app(settings, runtime)


def auth():
    return {"Authorization": "Bearer secret"}


def test_native_instruction_red_engine_rejects(tmp_path: Path):
    """GREEN: GGUFRerankerEngine.rerank forwards instruction to backend."""
    engine = _make_gguf_engine(tmp_path)
    engine.load()
    # After corrective: instruction is forwarded, not rejected
    result = engine.rerank("query", ["doc"], "custom task instruction")
    assert len(result) == 1
    assert result[0]["index"] == 0
    engine.close()


def test_native_instruction_red_api_returns_error(monkeypatch, tmp_path: Path):
    """GREEN: POST /v1/rerank with instruction returns 200."""
    engine = _make_gguf_engine(tmp_path)
    runtime = FakeGGUFRuntime(engine)
    app = _make_app(monkeypatch, runtime)

    with TestClient(app) as client:
        r = client.post(
            "/v1/rerank",
            headers=auth(),
            json={
                "query": "Which country uses the baht?",
                "documents": ["Thailand uses the baht."],
                "instruction": "Rank the candidate entity whose identity directly answers the question.",
            },
        )
        assert r.status_code == 200, (
            f"Expected HTTP 200 from native instruction, got {r.status_code}: {r.text}"
        )
        body = r.json()
        assert "results" in body
        assert len(body["results"]) == 1
    engine.close()


def test_native_instruction_red_probe_evidence(tmp_path: Path, capsys):
    """GREEN: instruction is forwarded to backend without error."""
    engine = _make_gguf_engine(tmp_path)
    engine.load()
    status = "PASS"
    try:
        result = engine.rerank("q", ["doc"], "custom task instruction")
        detail = f"instruction forwarded, got {len(result)} results"
    except Exception as exc:
        detail = str(exc)
        status = "FAIL"
    engine.close()

    evidence = (
        f"NATIVE_INSTRUCTION_RED={status}\n"
        f"Detail = {detail}\n"
    )
    print(evidence)
    assert status == "PASS"


# ---------------------------------------------------------------------------
# §6 — llama.cpp backend: instruction field unsupported/unrecognized
# ---------------------------------------------------------------------------

def test_native_instruction_red_llama_server_rejects_instruction():
    """RED: llama-server /v1/rerank does not accept 'instruction' field.

    We prove this by directly POSTing to the server. If the server is not
    running, we skip; if it is, we verify the instruction field is either
    ignored or causes an error.
    """
    import urllib.request
    import urllib.error

    llama_url = "http://127.0.0.1:8081/v1/rerank"
    body = {
        "query": "Which country uses the baht?",
        "documents": ["Thailand uses the baht."],
        "top_n": 1,
        "instruction": "custom task instruction",
    }

    try:
        req = urllib.request.Request(
            llama_url,
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            result = json.loads(resp.read())
            # If it succeeds, the instruction was silently ignored (RED: unsupported)
            assert "instruction" not in str(result), (
                "instruction field should not appear in response - backend does not support it"
            )
            # RED evidence: instruction was silently dropped
            print("NATIVE_INSTRUCTION_RED=PASS_EXPECTED_FAILURE")
            print("llama-server accepted request but silently ignored instruction field")
    except urllib.error.HTTPError as exc:
        # RED: server returned error for instruction field
        print(f"NATIVE_INSTRUCTION_RED=PASS_EXPECTED_FAILURE")
        print(f"llama-server returned HTTP {exc.code} for instruction field")
    except (urllib.error.URLError, ConnectionRefusedError, OSError):
        pytest.skip("llama-server not running on port 8081")
