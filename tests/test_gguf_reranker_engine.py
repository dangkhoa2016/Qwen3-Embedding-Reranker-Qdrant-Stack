from pathlib import Path
from types import SimpleNamespace
import math
import pytest

from qwen_dual_server.gguf_reranker_engine import GGUFRerankerEngine, UnsupportedInstructionError


class FakeServer:
    def __init__(self):
        self.started = False
        self.closed = False
        self.pid = 222
        self.rerank_url = "http://127.0.0.1:8081/v1/rerank"

    def start(self):
        self.started = True

    def close(self):
        self.closed = True


def settings(tmp_path: Path):
    return SimpleNamespace(
        reranker_model_id="Qwen/Qwen3-Reranker-4B",
        reranker_gguf_path=str(tmp_path / "Qwen3-Reranker-4B.Q4_K_M.gguf"),
        kaggle_input_root=tmp_path,
        llama_server_bin="/opt/llama-server",
        llama_server_host="127.0.0.1",
        llama_server_port=8081,
        llama_server_threads=2,
        llama_server_context_size=1024,
        llama_server_startup_timeout_seconds=30,
        max_seq_length=512,
        reranker_microbatch_size=1,
    )


def make_engine(tmp_path: Path, payload):
    cfg = settings(tmp_path)
    Path(cfg.reranker_gguf_path).write_bytes(b"gguf")
    server = FakeServer()
    calls = []

    def http_post(url, body, timeout):
        calls.append((url, body, timeout))
        return payload

    engine = GGUFRerankerEngine(
        cfg,
        server_factory=lambda **_: server,
        binary_resolver=lambda _: Path("/opt/llama-server"),
        http_post=http_post,
        functional_probe=False,
    )
    return engine, server, calls


def test_maps_relevance_score_to_score_and_sorts_descending(tmp_path: Path):
    payload = {"results": [
        {"index": 0, "relevance_score": 0.1},
        {"index": 1, "relevance_score": 0.9},
    ]}
    engine, server, calls = make_engine(tmp_path, payload)
    engine.load()
    out = engine.rerank("q", ["a", "b"], None)
    assert out == [{"index": 1, "score": 0.9}, {"index": 0, "score": 0.1}]
    assert calls[-1][1]["top_n"] == 2


@pytest.mark.parametrize("payload, message", [
    ({"results": [{"index": 0, "relevance_score": 1.0}, {"index": 0, "relevance_score": 0.5}]}, "duplicate"),
    ({"results": [{"index": 0, "relevance_score": 1.0}, {"index": 2, "relevance_score": 0.5}]}, "out of range"),
    ({"results": [{"index": 0, "relevance_score": 1.0}]}, "exactly one"),
    ({"results": [{"index": 0, "relevance_score": float("nan")}, {"index": 1, "relevance_score": 0.2}]}, "finite"),
])
def test_malformed_results_fail_closed(tmp_path: Path, payload, message):
    engine, _, _ = make_engine(tmp_path, payload)
    engine.load()
    with pytest.raises(RuntimeError, match=message):
        engine.rerank("q", ["a", "b"], None)


def test_custom_instruction_is_forwarded_when_capability_proved(tmp_path: Path):
    engine, _, calls = make_engine(tmp_path, {"results": [{"index": 0, "relevance_score": 0.9}]})
    engine._supports_custom_instruction = True
    engine.load()
    engine.rerank("q", ["a"], "custom task instruction")
    assert "instruction" in calls[-1][1]
    assert calls[-1][1]["instruction"] == "custom task instruction"


def test_custom_instruction_fails_closed_when_capability_unproven(tmp_path: Path):
    engine, _, calls = make_engine(tmp_path, {"results": [{"index": 0, "relevance_score": 0.9}]})
    engine.load()
    assert engine._supports_custom_instruction is False
    with pytest.raises(UnsupportedInstructionError, match="fail-closed"):
        engine.rerank("q", ["a"], "custom task instruction")
    assert all("instruction" not in body for _, body, _ in calls)


def test_metadata_is_truthful(tmp_path: Path):
    engine, server, _ = make_engine(tmp_path, {"results": []})
    engine.load()
    meta = engine.metadata()
    assert meta["role"] == "reranker"
    assert meta["backend"] == "llama_cpp"
    assert meta["format"] == "gguf"
    assert meta["quantization"] == "Q4_K_M"
    assert meta["device"] == "cpu"
    assert meta["loaded"] is True
    assert meta["supports_custom_instruction"] is False
    assert meta["custom_instruction_probe"] == "not probed"
    assert meta["backend_pid"] == 222
    engine.close()
    assert server.closed is True


def test_capability_probe_sets_supports_custom_instruction_when_scores_differ(tmp_path: Path):
    cfg = settings(tmp_path)
    Path(cfg.reranker_gguf_path).write_bytes(b"gguf")
    server = FakeServer()

    def probe_http_post(url, body, timeout):
        instruction = body.get("instruction")
        if instruction:
            return {"results": [
                {"index": 0, "relevance_score": 0.95},
                {"index": 1, "relevance_score": 0.10},
            ]}
        return {"results": [
            {"index": 0, "relevance_score": 0.70},
            {"index": 1, "relevance_score": 0.30},
        ]}

    engine = GGUFRerankerEngine(
        cfg,
        server_factory=lambda **_: server,
        binary_resolver=lambda _: Path("/opt/llama-server"),
        http_post=probe_http_post,
        functional_probe=True,
    )
    engine.load()
    assert engine._supports_custom_instruction is True
    assert engine.metadata()["supports_custom_instruction"] is True
    engine.close()


def test_capability_probe_fails_closed_when_scores_identical(tmp_path: Path):
    cfg = settings(tmp_path)
    Path(cfg.reranker_gguf_path).write_bytes(b"gguf")
    server = FakeServer()

    def identical_http_post(url, body, timeout):
        return {"results": [
            {"index": 0, "relevance_score": 0.70},
            {"index": 1, "relevance_score": 0.30},
        ]}

    engine = GGUFRerankerEngine(
        cfg,
        server_factory=lambda **_: server,
        binary_resolver=lambda _: Path("/opt/llama-server"),
        http_post=identical_http_post,
        functional_probe=True,
    )
    engine.load()
    assert engine._supports_custom_instruction is False
    assert engine.metadata()["supports_custom_instruction"] is False
    engine.close()

def test_functional_probe_requires_thailand_document_rank_one(tmp_path: Path):
    cfg = settings(tmp_path)
    Path(cfg.reranker_gguf_path).write_bytes(b"gguf")
    server = FakeServer()

    def wrong_http_post(url, body, timeout):
        return {"results": [
            {"index": 1, "relevance_score": 0.9},
            {"index": 0, "relevance_score": 0.1},
        ]}

    engine = GGUFRerankerEngine(
        cfg,
        server_factory=lambda **_: server,
        binary_resolver=lambda _: Path("/opt/llama-server"),
        http_post=wrong_http_post,
        functional_probe=True,
    )
    with pytest.raises(RuntimeError, match="Thailand"):
        engine.load()
    assert server.closed is True
