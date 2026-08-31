from types import SimpleNamespace

import pytest
import torch
from pydantic import ValidationError

from qwen_dual_server.config import Settings
from qwen_dual_server.embedding_engine import EmbeddingEngine
from qwen_dual_server.reranker_engine import RerankerEngine


class FakeQuantizedWeight:
    pass


FakeQuantizedWeight.__module__ = "torchao.dtypes.affine_quantized_tensor"


class FakeQuantizedModule:
    def __init__(self):
        self.weight = FakeQuantizedWeight()


class FakeQuantizedModel:
    def __init__(self, factory=None):
        self.config = SimpleNamespace(use_cache=True)
        self._p = torch.nn.Parameter(torch.ones(1, dtype=torch.float32), requires_grad=False)
        self._factory = factory

    def parameters(self):
        return iter([self._p])

    def named_modules(self):
        return iter([("", self), ("model.layers.0.self_attn.q_proj", FakeQuantizedModule())])

    def eval(self):
        return self

    def __call__(self, **batch):
        return self._factory(batch)


class Batch(dict):
    def to(self, device):
        for key, value in list(self.items()):
            if hasattr(value, "to"):
                self[key] = value.to(device)
        return self


class FakeEmbeddingTokenizer:
    padding_side = "left"

    def __call__(self, texts, padding=True, truncation=True, max_length=512, return_tensors="pt"):
        if isinstance(texts, str):
            texts = [texts]
        n = len(texts)
        return Batch({
            "input_ids": torch.ones((n, 2), dtype=torch.long),
            "attention_mask": torch.ones((n, 2), dtype=torch.long),
        })


class FakeRerankerTokenizer:
    padding_side = "left"
    pad_token = None
    eos_token = "<eos>"

    def encode(self, text, add_special_tokens=False):
        return [7, 8]

    def convert_tokens_to_ids(self, token):
        return {"no": 0, "yes": 1}[token]

    def __call__(self, texts, padding=False, truncation="longest_first", return_attention_mask=False, max_length=500):
        if isinstance(texts, str):
            texts = [texts]
        return {"input_ids": [[2, 4, 5] for _ in texts]}

    def pad(self, inputs, padding=True, return_tensors="pt", **kwargs):
        rows = inputs["input_ids"]
        width = max(len(row) for row in rows)
        padded = [[0] * (width - len(row)) + row for row in rows]
        mask = [[0] * (width - len(row)) + [1] * len(row) for row in rows]
        return Batch({"input_ids": torch.tensor(padded), "attention_mask": torch.tensor(mask)})


def _embedding_factory(batch):
    n, seq = batch["input_ids"].shape
    states = torch.zeros((n, seq, 2560), dtype=torch.float32)
    states[:, -1, 0] = 3
    states[:, -1, 1] = 4
    return SimpleNamespace(last_hidden_state=states)


def _reranker_factory(batch):
    b, seq = batch["input_ids"].shape
    logits = torch.zeros((b, seq, 16), dtype=torch.float32)
    logits[:, -1, 1] = 5
    logits[:, -1, 0] = -5
    return SimpleNamespace(logits=logits)


def _settings(monkeypatch, mode):
    monkeypatch.setenv("DUAL_API_KEY", "secret")
    monkeypatch.setenv("LOAD_MODELS_ON_STARTUP", "0")
    monkeypatch.setenv("QUANTIZATION_MODE", mode)
    return Settings()


def test_settings_default_keeps_frozen_fp16_behavior(monkeypatch):
    monkeypatch.setenv("DUAL_API_KEY", "secret")
    monkeypatch.delenv("QUANTIZATION_MODE", raising=False)
    settings = Settings()
    assert settings.quantization_mode == "none"
    assert settings.model_dtype == "float16"


@pytest.mark.parametrize("mode", ["int8-a8w8", "int8-weight-only"])
def test_settings_accept_int8_experiment_modes(monkeypatch, mode):
    settings = _settings(monkeypatch, mode)
    assert settings.quantization_mode == mode


def test_settings_reject_unknown_quantization_mode(monkeypatch):
    monkeypatch.setenv("DUAL_API_KEY", "secret")
    monkeypatch.setenv("QUANTIZATION_MODE", "int4-surprise")
    with pytest.raises(ValidationError):
        Settings()


def test_torchao_factory_maps_a8w8_and_weight_only(monkeypatch):
    from qwen_dual_server.quantization import build_torchao_quantization_config

    calls = []

    class A8W8:
        def __init__(self):
            calls.append("a8w8")

    class W8:
        def __init__(self):
            calls.append("w8")

    class Wrapper:
        def __init__(self, *, quant_type):
            self.quant_type = quant_type

    a = build_torchao_quantization_config(
        "int8-a8w8", torchao_config_cls=Wrapper, a8w8_cls=A8W8, weight_only_cls=W8
    )
    w = build_torchao_quantization_config(
        "int8-weight-only", torchao_config_cls=Wrapper, a8w8_cls=A8W8, weight_only_cls=W8
    )
    assert calls == ["a8w8", "w8"]
    assert isinstance(a.quant_type, A8W8)
    assert isinstance(w.quant_type, W8)


def test_embedding_int8_loader_uses_cpu_torchao_contract(monkeypatch, tmp_path):
    s = _settings(monkeypatch, "int8-a8w8")
    calls = {}
    sentinel = object()

    monkeypatch.setattr(
        "qwen_dual_server.embedding_engine.build_torchao_quantization_config",
        lambda mode: sentinel,
    )

    def tok_loader(path, **kwargs):
        return FakeEmbeddingTokenizer()

    def model_loader(path, **kwargs):
        calls.update(kwargs)
        return FakeQuantizedModel(_embedding_factory)

    engine = EmbeddingEngine(s, tmp_path, tokenizer_loader=tok_loader, model_loader=model_loader)
    engine.load()
    assert calls["quantization_config"] is sentinel
    assert calls["device_map"] == "cpu"
    assert calls["dtype"] == "auto"
    assert calls["low_cpu_mem_usage"] is True
    assert engine.load_report["quantization_mode"] == "int8-a8w8"
    assert engine.load_report["quantized_weight_modules"] >= 1
    vector = engine.embed(["Thailand"], "query", None)
    assert vector.dtype == torch.float32
    assert vector.shape == (1, 2560)


def test_reranker_int8_loader_preserves_yes_no_scoring(monkeypatch, tmp_path):
    s = _settings(monkeypatch, "int8-weight-only")
    calls = {}
    sentinel = object()

    monkeypatch.setattr(
        "qwen_dual_server.reranker_engine.build_torchao_quantization_config",
        lambda mode: sentinel,
    )

    def tok_loader(path, **kwargs):
        return FakeRerankerTokenizer()

    def model_loader(path, **kwargs):
        calls.update(kwargs)
        return FakeQuantizedModel(_reranker_factory)

    engine = RerankerEngine(s, tmp_path, tokenizer_loader=tok_loader, model_loader=model_loader)
    engine.load()
    assert calls["quantization_config"] is sentinel
    assert calls["device_map"] == "cpu"
    assert calls["dtype"] == "auto"
    assert engine.load_report["quantization_mode"] == "int8-weight-only"
    results = engine.rerank("capital of Thailand", ["Bangkok is the capital of Thailand."], None)
    assert results[0]["index"] == 0
    assert results[0]["score"] > 0.99


def test_quantized_validator_fails_closed_without_quantized_weight_evidence():
    from qwen_dual_server.quantization import validate_quantized_cpu_model

    class PlainModel:
        def __init__(self):
            self._p = torch.nn.Parameter(torch.ones(1), requires_grad=False)
        def parameters(self):
            return iter([self._p])
        def named_modules(self):
            return iter([("", self)])

    with pytest.raises(RuntimeError, match="no TorchAO quantized weight"):
        validate_quantized_cpu_model(PlainModel(), "int8-a8w8")
