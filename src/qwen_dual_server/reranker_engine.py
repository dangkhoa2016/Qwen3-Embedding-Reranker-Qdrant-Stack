from __future__ import annotations

from pathlib import Path
from typing import Callable

import torch

from .config import Settings
from .engine_common import model_dtype_kwargs, resolve_torch_dtype, validate_model_cpu_dtype
from .quantization import build_torchao_quantization_config, validate_quantized_cpu_model
from .formatting import DEFAULT_RERANK_INSTRUCTION, RERANK_PREFIX, RERANK_SUFFIX, format_reranker_pair


class RerankerEngine:
    def __init__(
        self,
        settings: Settings,
        model_path: Path | str,
        *,
        tokenizer_loader: Callable | None = None,
        model_loader: Callable | None = None,
    ):
        self.settings = settings
        self.model_path = Path(model_path)
        self._tokenizer_loader = tokenizer_loader
        self._model_loader = model_loader
        self.tokenizer = None
        self.model = None
        self.prefix_tokens: list[int] = []
        self.suffix_tokens: list[int] = []
        self.token_false_id: int | None = None
        self.token_true_id: int | None = None
        self.load_report: dict[str, object] | None = None

    def _loaders(self):
        if self._tokenizer_loader is not None and self._model_loader is not None:
            return self._tokenizer_loader, self._model_loader
        from transformers import AutoModelForCausalLM, AutoTokenizer
        return AutoTokenizer.from_pretrained, AutoModelForCausalLM.from_pretrained

    def load(self) -> None:
        if self.model is not None:
            return
        tokenizer_loader, model_loader = self._loaders()
        local_only = not self.settings.allow_remote_model_download
        dtype = resolve_torch_dtype(self.settings.model_dtype)
        self.tokenizer = tokenizer_loader(
            str(self.model_path),
            local_files_only=local_only,
            padding_side="left",
        )
        if getattr(self.tokenizer, "pad_token", None) is None and getattr(self.tokenizer, "eos_token", None) is not None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        if self.settings.quantization_mode == "none":
            load_kwargs = model_dtype_kwargs(dtype)
        else:
            load_kwargs = {
                "dtype": "auto",
                "device_map": "cpu",
                "quantization_config": build_torchao_quantization_config(self.settings.quantization_mode),
            }
        self.model = model_loader(
            str(self.model_path),
            local_files_only=local_only,
            low_cpu_mem_usage=True,
            **load_kwargs,
        )
        self.model.eval()
        if hasattr(self.model, "config"):
            self.model.config.use_cache = False
        if self.settings.quantization_mode == "none":
            self.load_report = validate_model_cpu_dtype(self.model, dtype)
        else:
            self.load_report = validate_quantized_cpu_model(self.model, self.settings.quantization_mode)
        self.token_false_id = int(self.tokenizer.convert_tokens_to_ids("no"))
        self.token_true_id = int(self.tokenizer.convert_tokens_to_ids("yes"))
        if self.token_false_id < 0 or self.token_true_id < 0 or self.token_false_id == self.token_true_id:
            raise RuntimeError("reranker tokenizer cannot resolve distinct yes/no token ids")
        self.prefix_tokens = list(self.tokenizer.encode(RERANK_PREFIX, add_special_tokens=False))
        self.suffix_tokens = list(self.tokenizer.encode(RERANK_SUFFIX, add_special_tokens=False))
        reserved = len(self.prefix_tokens) + len(self.suffix_tokens)
        if reserved >= self.settings.max_seq_length:
            raise RuntimeError(
                f"reranker prefix/suffix reserve {reserved} tokens, exceeding max_seq_length={self.settings.max_seq_length}"
            )

    def _tokenize_pairs(self, formatted_pairs: list[str]):
        available = self.settings.max_seq_length - len(self.prefix_tokens) - len(self.suffix_tokens)
        inputs = self.tokenizer(
            formatted_pairs,
            padding=False,
            truncation="longest_first",
            return_attention_mask=False,
            max_length=available,
        )
        rows = []
        for ids in inputs["input_ids"]:
            rows.append(self.prefix_tokens + list(ids) + self.suffix_tokens)
        batch = self.tokenizer.pad(
            {"input_ids": rows},
            padding=True,
            return_tensors="pt",
        )
        if hasattr(batch, "to"):
            return batch.to("cpu")
        return {key: value.to("cpu") for key, value in batch.items()}

    def _score_batch(self, formatted_pairs: list[str]) -> list[float]:
        batch = self._tokenize_pairs(formatted_pairs)
        with torch.inference_mode():
            final_logits = self.model(**batch).logits[:, -1, :].float()
            false_vector = final_logits[:, self.token_false_id]
            true_vector = final_logits[:, self.token_true_id]
            two = torch.stack([false_vector, true_vector], dim=1)
            probabilities = torch.log_softmax(two, dim=1)[:, 1].exp()
        return [float(value) for value in probabilities.detach().cpu().tolist()]

    def rerank(self, query: str, documents: list[str], instruction: str | None) -> list[dict[str, object]]:
        if self.model is None or self.tokenizer is None:
            raise RuntimeError("reranker model is not loaded")
        results: list[dict[str, object]] = []
        step = self.settings.reranker_microbatch_size
        for start in range(0, len(documents), step):
            chunk = documents[start : start + step]
            formatted = [format_reranker_pair(query, document, instruction) for document in chunk]
            scores = self._score_batch(formatted)
            for offset, score in enumerate(scores):
                results.append({"index": start + offset, "score": score})
        results.sort(key=lambda item: float(item["score"]), reverse=True)
        return results

    def warmup(self) -> None:
        self.rerank("capital of Thailand", ["Bangkok is the capital of Thailand."], DEFAULT_RERANK_INSTRUCTION)

    def metadata(self) -> dict[str, object]:
        return {
            "id": self.settings.reranker_model_id,
            "role": "reranker",
            "path": str(self.model_path),
            "backend": "transformers",
            "runtime": "pytorch-cpu",
            "device": "cpu",
            "dtype": self.settings.model_dtype if self.settings.quantization_mode == "none" else "mixed-residual",
            "quantization_mode": self.settings.quantization_mode,
            "max_seq_length": self.settings.max_seq_length,
            "microbatch_size": self.settings.reranker_microbatch_size,
            "loaded": self.model is not None,
            "load_report": self.load_report,
        }
