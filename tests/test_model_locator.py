import json
from pathlib import Path

import pytest

from qwen_dual_server.model_locator import ModelResolutionError, resolve_model_path, validate_model_root


def make_model(root: Path, role: str) -> Path:
    root.mkdir(parents=True)
    vocab_size = 151665 if role == "embedding" else 151669
    (root / "config.json").write_text(json.dumps({
        "model_type": "qwen3",
        "architectures": ["Qwen3ForCausalLM"],
        "hidden_size": 2560,
        "num_hidden_layers": 36,
        "vocab_size": vocab_size,
        "torch_dtype": "bfloat16",
    }))
    modules = ([{"idx": 0, "type": "sentence_transformers.models.Transformer"},
                {"idx": 1, "type": "sentence_transformers.models.Pooling", "path": "1_Pooling"}]
               if role == "embedding" else
               [{"idx": 0, "type": "sentence_transformers.base.modules.transformer.Transformer"},
                {"idx": 1, "type": "sentence_transformers.cross_encoder.modules.logit_score.LogitScore", "path": "1_LogitScore"}])
    (root / "modules.json").write_text(json.dumps(modules))
    (root / "model-00001-of-00002.safetensors").write_bytes(b"x")
    (root / "model-00002-of-00002.safetensors").write_bytes(b"y")
    (root / "model.safetensors.index.json").write_text(json.dumps({
        "weight_map": {
            "model.embed_tokens.weight": "model-00001-of-00002.safetensors",
            "model.layers.0.self_attn.q_proj.weight": "model-00002-of-00002.safetensors",
        }
    }))
    (root / "tokenizer_config.json").write_text("{}")
    return root


def test_validate_embedding_and_reranker_roots(tmp_path):
    emb = make_model(tmp_path / "embedding", "embedding")
    rer = make_model(tmp_path / "reranker", "reranker")
    assert validate_model_root(emb, "embedding") == emb
    assert validate_model_root(rer, "reranker") == rer
    with pytest.raises(ModelResolutionError):
        validate_model_root(emb, "reranker")


def test_resolve_explicit_model_path(tmp_path):
    emb = make_model(tmp_path / "models" / "embed", "embedding")
    assert resolve_model_path("embedding", explicit_path=str(emb), input_root=tmp_path) == emb.resolve()


def test_discovery_fails_closed_on_ambiguity(tmp_path):
    make_model(tmp_path / "a" / "embedding", "embedding")
    make_model(tmp_path / "b" / "embedding", "embedding")
    with pytest.raises(ModelResolutionError, match="ambiguous"):
        resolve_model_path("embedding", explicit_path=None, input_root=tmp_path)
