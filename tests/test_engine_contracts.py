from types import SimpleNamespace

import pytest
import torch

from qwen_dual_server.config import Settings
from qwen_dual_server.embedding_engine import EmbeddingEngine
from qwen_dual_server.engine_common import (
    current_transformers_dtype_keyword,
    model_dtype_kwargs,
    select_dtype_keyword,
)
from qwen_dual_server.formatting import RERANK_PREFIX, RERANK_SUFFIX, format_reranker_pair
from qwen_dual_server.reranker_engine import RerankerEngine


class Batch(dict):
    def to(self, device):
        for k, v in list(self.items()):
            if hasattr(v, "to"):
                self[k] = v.to(device)
        return self


class TruncatingRecordingEmbeddingTokenizer:
    padding_side = "left"
    eos_special_id = 7

    def __call__(self, texts, padding=True, truncation=True, max_length=512, return_tensors="pt", **kwargs):
        if isinstance(texts, str):
            texts = [texts]
        rows = []
        for text in texts:
            ids = [13 + (i % 9) for i in range(len(text.split()))]
            if truncation and max_length:
                ids = ids[: max_length - 1]
            if truncation:
                ids = ids + [self.eos_special_id]
            rows.append(ids)
        width = max(len(row) for row in rows)
        padded = [[0] * (width - len(row)) + row for row in rows]
        mask = [[0] * (width - len(row)) + [1] * len(row) for row in rows]
        return Batch(
            {
                "input_ids": torch.tensor(padded, dtype=torch.long),
                "attention_mask": torch.tensor(mask, dtype=torch.long),
            }
        )


class TruncatingRecordingRerankerTokenizer:
    padding_side = "left"
    pad_token = "<pad>"
    eos_token = "<eos>"
    pad_kwargs = None

    def encode(self, text, add_special_tokens=False):
        return [129 + (i % 11) for i in range(len(text.split()))]

    def convert_tokens_to_ids(self, token):
        return {"no": 0, "yes": 1}[token]

    def __call__(self, texts, padding=False, truncation=None, return_attention_mask=False, max_length=None):
        if isinstance(texts, str):
            texts = [texts]
        ids = [self.encode(text) for text in texts]
        if truncation and max_length:
            ids = [row[:max_length] for row in ids]
        return {"input_ids": ids}

    def pad(self, inputs, padding=True, return_tensors="pt", **kwargs):
        self.pad_kwargs = dict(padding=padding, return_tensors=return_tensors, **kwargs)
        rows = inputs["input_ids"]
        width = max(len(row) for row in rows)
        padded = [[0] * (width - len(row)) + row for row in rows]
        mask = [[0] * (width - len(row)) + [1] * len(row) for row in rows]
        return Batch(
            {
                "input_ids": torch.tensor(padded, dtype=torch.long),
                "attention_mask": torch.tensor(mask, dtype=torch.long),
            }
        )


class RecordingModel(SimpleNamespace):
    def __init__(self, factory):
        super().__init__()
        self._factory = factory
        self.last_batch = None
        self.eval_called = False

    def to(self, device):
        return self

    def parameters(self):
        return iter([torch.nn.Parameter(torch.ones(1, dtype=torch.float16), requires_grad=False)])

    def eval(self):
        self.eval_called = True
        return self

    def __call__(self, **batch):
        self.last_batch = batch
        return self._factory(batch)


class FakeEmbeddingTokenizer:
    padding_side = "left"
    def __call__(self, texts, padding=True, truncation=True, max_length=512, return_tensors="pt"):
        if isinstance(texts, str): texts = [texts]
        n = len(texts)
        return Batch({
            "input_ids": torch.ones((n, 2), dtype=torch.long),
            "attention_mask": torch.ones((n, 2), dtype=torch.long),
        })


class FakeEmbeddingModel:
    def __init__(self):
        self.config = SimpleNamespace(use_cache=True)
        self._p = torch.nn.Parameter(torch.ones(1, dtype=torch.float16), requires_grad=False)
        self.eval_called = False
    def parameters(self): return iter([self._p])
    def eval(self): self.eval_called = True; return self
    def __call__(self, **batch):
        n, seq = batch["input_ids"].shape
        states = torch.zeros((n, seq, 2560), dtype=torch.float16)
        states[:, -1, 0] = 3
        states[:, -1, 1] = 4
        return SimpleNamespace(last_hidden_state=states)


class FakeRerankerTokenizer:
    padding_side = "left"
    pad_token = None
    eos_token = "<eos>"
    def encode(self, text, add_special_tokens=False):
        return [7, 8] if "system" in text else [9, 10]
    def convert_tokens_to_ids(self, token):
        return {"no": 0, "yes": 1}[token]
    def __call__(self, texts, padding=False, truncation="longest_first", return_attention_mask=False, max_length=500):
        if isinstance(texts, str): texts = [texts]
        ids=[]
        for text in texts:
            marker = 2 if "<document>: relevant" in text.lower() else 3
            ids.append([marker, 4, 5])
        return {"input_ids": ids}
    def pad(self, inputs, padding=True, return_tensors="pt", max_length=512):
        rows = inputs["input_ids"]
        width = max(len(x) for x in rows)
        padded = [[0] * (width-len(x)) + x for x in rows]
        mask = [[0] * (width-len(x)) + [1]*len(x) for x in rows]
        return Batch({"input_ids": torch.tensor(padded), "attention_mask": torch.tensor(mask)})


class FakeRerankerModel:
    def __init__(self):
        self.config = SimpleNamespace(use_cache=True)
        self._p = torch.nn.Parameter(torch.ones(1, dtype=torch.float16), requires_grad=False)
        self.eval_called = False
    def parameters(self): return iter([self._p])
    def eval(self): self.eval_called = True; return self
    def __call__(self, **batch):
        b, seq = batch["input_ids"].shape
        logits = torch.zeros((b, seq, 16), dtype=torch.float16)
        # marker survives after prefix at index 2 in our fake protocol.
        for i in range(b):
            relevant = 2 in batch["input_ids"][i].tolist()
            logits[i, -1, 1] = 5.0 if relevant else -5.0
            logits[i, -1, 0] = -5.0 if relevant else 5.0
        return SimpleNamespace(logits=logits)


def settings(monkeypatch):
    monkeypatch.setenv("DUAL_API_KEY", "secret")
    monkeypatch.setenv("LOAD_MODELS_ON_STARTUP", "0")
    return Settings()


def test_embedding_loader_is_cpu_fp16_low_memory_and_output_is_fp32(monkeypatch, tmp_path):
    s = settings(monkeypatch)
    calls = {}
    def tok_loader(path, **kwargs): calls["tok"]=(path, kwargs); return FakeEmbeddingTokenizer()
    def model_loader(path, **kwargs): calls["model"]=(path, kwargs); return FakeEmbeddingModel()
    engine = EmbeddingEngine(s, tmp_path, tokenizer_loader=tok_loader, model_loader=model_loader)
    engine.load()
    assert calls["tok"][1]["local_files_only"] is True
    kwargs = calls["model"][1]
    assert kwargs["local_files_only"] is True
    assert kwargs["low_cpu_mem_usage"] is True
    loaded_key = next(iter(model_dtype_kwargs(torch.float16)))
    assert kwargs[loaded_key] == torch.float16
    assert "torch_dtype" not in kwargs
    assert "device_map" not in kwargs
    assert engine.model.config.use_cache is False
    vectors = engine.embed(["Thailand"], "query", None)
    assert vectors.dtype == torch.float32
    assert vectors.shape == (1, 2560)
    assert torch.allclose(torch.linalg.vector_norm(vectors, dim=1), torch.ones(1), atol=1e-6)


def test_reranker_uses_yes_no_protocol_and_sorts_results(monkeypatch, tmp_path):
    s = settings(monkeypatch)
    calls={}
    def tok_loader(path, **kwargs): calls["tok"]=(path, kwargs); return FakeRerankerTokenizer()
    def model_loader(path, **kwargs): calls["model"]=(path, kwargs); return FakeRerankerModel()
    engine = RerankerEngine(s, tmp_path, tokenizer_loader=tok_loader, model_loader=model_loader)
    engine.load()
    assert calls["model"][1]["low_cpu_mem_usage"] is True
    loaded_key = next(iter(model_dtype_kwargs(torch.float16)))
    assert calls["model"][1][loaded_key] == torch.float16
    assert "torch_dtype" not in calls["model"][1]
    assert "device_map" not in calls["model"][1]
    assert engine.model.config.use_cache is False
    results = engine.rerank("capital", ["irrelevant physics", "relevant Thailand fact"], None)
    assert [item["index"] for item in results] == [1, 0]
    assert results[0]["score"] > 0.99
    assert results[1]["score"] < 0.01


def test_select_dtype_keyword_prefers_modern_dtype():
    assert select_dtype_keyword({"dtype", "foo"}) == "dtype"


def test_select_dtype_keyword_falls_back_to_legacy_torch_dtype():
    assert select_dtype_keyword({"torch_dtype", "foo"}) == "torch_dtype"


def test_select_dtype_keyword_fails_closed_if_neither_supported():
    with pytest.raises(RuntimeError, match="dtype"):
        select_dtype_keyword({"foo"})


def test_current_transformers_prefers_dtype_keyword():
    import inspect
    from transformers import PreTrainedModel

    names = set(inspect.signature(PreTrainedModel.from_pretrained).parameters)
    if "dtype" in names or "torch_dtype" in names:
        assert select_dtype_keyword(names) == "dtype"
    else:
        # transformers 4.57.x funnels `dtype` through **kwargs, so name
        # lookup cannot see it; require the truthful capability probe instead.
        assert current_transformers_dtype_keyword() == "dtype"


def test_model_dtype_kwargs_selects_modern_loaded_dtype():
    kwargs = model_dtype_kwargs(torch.float16)
    assert kwargs == {current_transformers_dtype_keyword(): torch.float16}


def _embedding_output_factory(batch):
    n, seq = batch["input_ids"].shape
    states = torch.zeros((n, seq, 2560), dtype=torch.float16)
    states[:, -1, 0] = 3
    states[:, -1, 1] = 4
    return SimpleNamespace(last_hidden_state=states)


def test_embedding_oversized_input_is_bounded_with_eos_retained(monkeypatch, tmp_path):
    s = settings(monkeypatch)
    tokenizer = TruncatingRecordingEmbeddingTokenizer()
    model = RecordingModel(_embedding_output_factory)

    def tok_loader(path, **kwargs):
        return tokenizer

    def model_loader(path, **kwargs):
        return model

    engine = EmbeddingEngine(s, tmp_path, tokenizer_loader=tok_loader, model_loader=model_loader)
    engine.load()
    oversized = "Thailand " * 2000
    engine.embed([oversized], "query", None)
    model_inputs = model.last_batch
    assert int(model_inputs["input_ids"].shape[-1]) <= 512
    assert int(model_inputs["attention_mask"].shape[-1]) <= 512
    lengths = model_inputs["attention_mask"].sum(dim=1)
    assert int(lengths.max()) <= 512
    for i in range(model_inputs["input_ids"].shape[0]):
        valid_len = int(lengths[i])
        final_valid = int(model_inputs["input_ids"][i, valid_len - 1])
        assert final_valid == tokenizer.eos_special_id


def test_reranker_oversized_pair_is_bounded_and_pad_kwargs_are_clean(monkeypatch, tmp_path):
    s = settings(monkeypatch)
    tokenizer = TruncatingRecordingRerankerTokenizer()
    engine = RerankerEngine(s, tmp_path)
    engine.tokenizer = tokenizer
    engine.prefix_tokens = tokenizer.encode(RERANK_PREFIX, add_special_tokens=False)
    engine.suffix_tokens = tokenizer.encode(RERANK_SUFFIX, add_special_tokens=False)
    engine.token_false_id = int(tokenizer.convert_tokens_to_ids("no"))
    engine.token_true_id = int(tokenizer.convert_tokens_to_ids("yes"))

    long_query = "Which Southeast Asian country uses the baht? " * 60
    long_document = ("Thailand is a country in Southeast Asia. Its currency is the Thai baht "
                     "and its capital is Bangkok. ") * 60
    formatted = format_reranker_pair(long_query, long_document, None)
    assert "<Instruct>" in formatted
    assert "<Query>" in formatted
    assert "<Document>" in formatted

    batch = engine._tokenize_pairs([formatted])
    assert int(batch["input_ids"].shape[-1]) <= 512
    assert int(batch["attention_mask"].shape[-1]) <= 512

    assert engine.token_false_id == 0
    assert engine.token_true_id == 1
    assert engine.prefix_tokens == tokenizer.encode(RERANK_PREFIX, add_special_tokens=False)
    assert engine.suffix_tokens == tokenizer.encode(RERANK_SUFFIX, add_special_tokens=False)

    pad_kwargs = tokenizer.pad_kwargs
    assert pad_kwargs["padding"] is True
    assert "max_length" not in pad_kwargs
