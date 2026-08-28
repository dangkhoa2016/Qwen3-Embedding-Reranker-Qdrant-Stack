from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, model_validator


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    return default if raw is None else int(raw)


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    return default if raw is None else float(raw)


class Settings(BaseModel):
    service_name: str = "qwen3-dual-4b-cpu-rest-server"
    api_key: str | None = None
    allow_insecure_no_auth: bool = False

    embedding_model_id: str = "Qwen/Qwen3-Embedding-4B"
    reranker_model_id: str = "Qwen/Qwen3-Reranker-4B"
    embedding_model_path: str | None = None
    reranker_model_path: str | None = None
    kaggle_input_root: Path = Path("/kaggle/input")
    allow_remote_model_download: bool = False

    model_dtype: Literal["float16", "bfloat16", "float32"] = "float16"
    quantization_mode: Literal["none", "int8-a8w8", "int8-weight-only"] = "none"
    reranker_backend: Literal["transformers", "llama_cpp"] = "transformers"
    reranker_gguf_path: str | None = None
    llama_server_bin: str | None = None
    llama_server_host: str = "127.0.0.1"
    llama_server_port: int = Field(default=8081, ge=1, le=65535)
    llama_server_threads: int = Field(default=2, ge=1, le=256)
    llama_server_context_size: int = Field(default=1024, ge=128, le=131072)
    llama_server_startup_timeout_seconds: int = Field(default=180, ge=1, le=3600)
    max_seq_length: int = Field(default=512, ge=64, le=8192)
    embedding_microbatch_size: int = Field(default=1, ge=1, le=16)
    reranker_microbatch_size: int = Field(default=1, ge=1, le=16)
    max_embedding_items: int = Field(default=32, ge=1, le=256)
    max_rerank_documents: int = Field(default=20, ge=1, le=200)
    max_text_chars: int = Field(default=32_000, ge=256, le=2_000_000)
    max_instruction_chars: int = Field(default=1024, ge=32, le=4096)
    max_request_bytes: int = Field(default=2_000_000, ge=1024, le=100_000_000)
    max_concurrent_inference: Literal[1] = 1
    max_queue_waiters: int = Field(default=32, ge=1, le=1000)
    second_model_min_available_gib: float = Field(default=10.0, ge=1.0, le=128.0)
    final_min_available_gib: float = Field(default=4.0, ge=1.0, le=128.0)

    torch_num_threads: int = Field(default=0, ge=0, le=256)
    torch_num_interop_threads: int = Field(default=1, ge=1, le=16)
    warmup_enabled: bool = True
    load_models_on_startup: bool = True

    rate_limit_requests: int = Field(default=60, ge=1, le=100000)
    rate_limit_window_seconds: int = Field(default=60, ge=1, le=3600)
    trust_proxy_headers: bool = True
    runtime_lock_path: Path = Path("/tmp/qwen3-dual-4b-cpu-rest-server.lock")

    def __init__(self, **data):
        env = {
            "api_key": os.getenv("DUAL_API_KEY"),
            "allow_insecure_no_auth": _env_bool("ALLOW_INSECURE_NO_AUTH", False),
            "embedding_model_path": os.getenv("EMBEDDING_MODEL_PATH"),
            "reranker_model_path": os.getenv("RERANKER_MODEL_PATH"),
            "reranker_backend": os.getenv("RERANKER_BACKEND", "transformers"),
            "reranker_gguf_path": os.getenv("RERANKER_GGUF_PATH"),
            "llama_server_bin": os.getenv("LLAMA_SERVER_BIN"),
            "llama_server_host": os.getenv("LLAMA_SERVER_HOST", "127.0.0.1"),
            "llama_server_port": _env_int("LLAMA_SERVER_PORT", 8081),
            "llama_server_threads": _env_int("LLAMA_SERVER_THREADS", 2),
            "llama_server_context_size": _env_int("LLAMA_SERVER_CONTEXT_SIZE", 1024),
            "llama_server_startup_timeout_seconds": _env_int("LLAMA_SERVER_STARTUP_TIMEOUT_SECONDS", 180),
            "kaggle_input_root": Path(os.getenv("KAGGLE_INPUT_ROOT", "/kaggle/input")),
            "allow_remote_model_download": _env_bool("ALLOW_REMOTE_MODEL_DOWNLOAD", False),
            "model_dtype": os.getenv("MODEL_DTYPE", "float16"),
            "quantization_mode": os.getenv("QUANTIZATION_MODE", "none"),
            "max_seq_length": _env_int("MAX_SEQ_LENGTH", 512),
            "embedding_microbatch_size": _env_int("EMBEDDING_MICROBATCH_SIZE", 1),
            "reranker_microbatch_size": _env_int("RERANKER_MICROBATCH_SIZE", 1),
            "max_embedding_items": _env_int("MAX_EMBEDDING_ITEMS", 32),
            "max_rerank_documents": _env_int("MAX_RERANK_DOCUMENTS", 20),
            "max_text_chars": _env_int("MAX_TEXT_CHARS", 32_000),
            "max_instruction_chars": _env_int("MAX_INSTRUCTION_CHARS", 1024),
            "max_request_bytes": _env_int("MAX_REQUEST_BYTES", 2_000_000),
            "max_concurrent_inference": _env_int("MAX_CONCURRENT_INFERENCE", 1),
            "max_queue_waiters": _env_int("MAX_QUEUE_WAITERS", 32),
            "second_model_min_available_gib": _env_float("SECOND_MODEL_MIN_AVAILABLE_GIB", 10.0),
            "final_min_available_gib": _env_float("FINAL_MIN_AVAILABLE_GIB", 4.0),
            "torch_num_threads": _env_int("TORCH_NUM_THREADS", 0),
            "torch_num_interop_threads": _env_int("TORCH_NUM_INTEROP_THREADS", 1),
            "warmup_enabled": _env_bool("WARMUP_ENABLED", True),
            "load_models_on_startup": _env_bool("LOAD_MODELS_ON_STARTUP", True),
            "rate_limit_requests": _env_int("RATE_LIMIT_REQUESTS", 60),
            "rate_limit_window_seconds": _env_int("RATE_LIMIT_WINDOW_SECONDS", 60),
            "trust_proxy_headers": _env_bool("TRUST_PROXY_HEADERS", True),
            "runtime_lock_path": Path(os.getenv("RUNTIME_LOCK_PATH", "/tmp/qwen3-dual-4b-cpu-rest-server.lock")),
        }
        merged = {k: v for k, v in env.items() if v is not None}
        merged.update(data)
        super().__init__(**merged)

    @model_validator(mode="after")
    def require_auth_by_default(self):
        if not self.allow_insecure_no_auth and not self.api_key:
            raise ValueError("DUAL_API_KEY is required unless ALLOW_INSECURE_NO_AUTH=1")
        return self
