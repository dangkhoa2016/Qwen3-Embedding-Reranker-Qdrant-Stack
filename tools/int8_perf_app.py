from fastapi import Request
import torch

from qwen_dual_server.api import create_app
from qwen_dual_server.config import Settings
from qwen_dual_server.runtime import DualModelRuntime
from qwen_dual_server.security import verify_bearer

settings = Settings()
runtime = DualModelRuntime(settings)
app = create_app(settings, runtime)


@app.get("/perf/runtime")
async def perf_runtime(request: Request):
    verify_bearer(request, settings)
    return {
        "torch_num_threads_effective": torch.get_num_threads(),
        "torch_num_interop_threads_effective": torch.get_num_interop_threads(),
        "torch_num_threads_configured": settings.torch_num_threads,
        "torch_num_interop_threads_configured": settings.torch_num_interop_threads,
        "model_dtype_configured": settings.model_dtype,
        "quantization_mode": settings.quantization_mode,
        "embedding_microbatch": settings.embedding_microbatch_size,
        "reranker_microbatch": settings.reranker_microbatch_size,
        "max_seq_length": settings.max_seq_length,
        "max_concurrent_inference": settings.max_concurrent_inference,
    }
