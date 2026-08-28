from __future__ import annotations

from pathlib import Path
from typing import Callable, Literal

import torch

from .config import Settings
from .engine_common import model_dtype_kwargs, resolve_torch_dtype, validate_model_cpu_dtype
from .quantization import build_torchao_quantization_config, validate_quantized_cpu_model
from .formatting import CANONICAL_EMBEDDING_INSTRUCTION, format_embedding_text
from .tensor_ops import last_token_pool, normalize_embedding_fp32


class EmbeddingEngine:
    dimension = 2560

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
        self.load_report: dict[str, object] | None = None

    def _loaders(self):
        if self._tokenizer_loader is not None and self._model_loader is not None:
            return self._tokenizer_loader, self._model_loader
        from transformers import AutoModel, AutoTokenizer
        return AutoTokenizer.from_pretrained, AutoModel.from_pretrained

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

    def embed(
        self,
        texts: list[str],
        input_type: Literal["query", "document"],
        instruction: str | None,
    ) -> torch.Tensor:
        if self.model is None or self.tokenizer is None:
            raise RuntimeError("embedding model is not loaded")
        outputs: list[torch.Tensor] = []
        step = self.settings.embedding_microbatch_size
        for start in range(0, len(texts), step):
            chunk = texts[start : start + step]
            prepared = [format_embedding_text(text, input_type, instruction) for text in chunk]
            batch = self.tokenizer(
                prepared,
                padding=True,
                truncation=True,
                max_length=self.settings.max_seq_length,
                return_tensors="pt",
            )
            if hasattr(batch, "to"):
                batch = batch.to("cpu")
            else:
                batch = {key: value.to("cpu") for key, value in batch.items()}
            with torch.inference_mode():
                result = self.model(**batch)
                pooled = last_token_pool(result.last_hidden_state, batch["attention_mask"])
                normalized = normalize_embedding_fp32(pooled)
            if normalized.shape[1] != self.dimension:
                raise RuntimeError(
                    f"embedding dimension mismatch: observed={normalized.shape[1]}, expected={self.dimension}"
                )
            outputs.append(normalized.detach().cpu())
        return torch.cat(outputs, dim=0) if outputs else torch.empty((0, self.dimension), dtype=torch.float32)

    def warmup(self) -> None:
        self.embed(["Thailand"], "query", CANONICAL_EMBEDDING_INSTRUCTION)

    def metadata(self) -> dict[str, object]:
        return {
            "id": self.settings.embedding_model_id,
            "role": "embedding",
            "path": str(self.model_path),
            "backend": "transformers",
            "runtime": "pytorch-cpu",
            "device": "cpu",
            "dtype": self.settings.model_dtype if self.settings.quantization_mode == "none" else "mixed-residual",
            "quantization_mode": self.settings.quantization_mode,
            "public_vector_dtype": "float32",
            "dimension": self.dimension,
            "max_seq_length": self.settings.max_seq_length,
            "microbatch_size": self.settings.embedding_microbatch_size,
            "loaded": self.model is not None,
            "load_report": self.load_report,
        }
