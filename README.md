# Qwen3 Dual-4B CPU REST Server

CPU/RAM-only FastAPI service for a shared Qwen3 embedding + reranking runtime.

The initial qualification baseline keeps one `Qwen/Qwen3-Embedding-4B` instance
and one `Qwen/Qwen3-Reranker-4B` instance resident in one process, uses bounded
CPU FP16 inference, and exposes authenticated embedding and reranking endpoints.

Key safety constraints include one Uvicorn worker, one heavy-inference slot,
fail-closed model discovery, bounded request sizes, memory headroom gates, and
public Float32 normalized embedding vectors.

See `RELEASE_NOTES_v0.1.0.md` and the later qualification documentation for the
full development record.
