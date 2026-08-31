from __future__ import annotations
import json
import os
import platform
from pathlib import Path

import torch
import torchao
import transformers

from qwen_dual_server.config import Settings
from qwen_dual_server.model_locator import resolve_model_path
from qwen_dual_server.quantization import build_torchao_quantization_config

os.environ.setdefault("DUAL_API_KEY", "preflight-only-not-a-live-secret")
os.environ.setdefault("LOAD_MODELS_ON_STARTUP", "0")
settings = Settings()

report = {
    "python": platform.python_version(),
    "torch": torch.__version__,
    "transformers": transformers.__version__,
    "torchao": torchao.__version__,
    "cuda_available": torch.cuda.is_available(),
    "cpu_count": os.cpu_count(),
    "embedding_model_path": str(resolve_model_path("embedding", settings.embedding_model_path, settings.kaggle_input_root)),
    "reranker_model_path": str(resolve_model_path("reranker", settings.reranker_model_path, settings.kaggle_input_root)),
    "quantization_configs": {},
}
for mode in ("int8-a8w8", "int8-weight-only"):
    cfg = build_torchao_quantization_config(mode)
    report["quantization_configs"][mode] = type(cfg).__name__
print(json.dumps(report, indent=2, sort_keys=True))
if torch.cuda.is_available():
    print("NOTE: CUDA is visible, but this campaign still pins device_map=cpu")
print("INT8_PREFLIGHT=PASS")
