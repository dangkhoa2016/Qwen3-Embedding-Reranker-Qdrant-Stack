# Qwen3 Hybrid GGUF Reranker Overlay

> English | [Tiếng Việt](README_OVERLAY_PROVENANCE.vi.md)

This overlay adds an opt-in `llama_cpp` reranker backend to the existing Qwen3 dual-4B CPU server without changing the embedding implementation or the public `/v1/rerank` schema.

## What it adds

- `src/qwen_dual_server/gguf_locator.py`
- `src/qwen_dual_server/llama_server.py`
- `src/qwen_dual_server/gguf_reranker_engine.py`
- unit tests for all three modules
- `tools/apply_hybrid_gguf_patch.py` to patch a fresh disposable source extraction
- `scripts/setup_llama_cpp_b10699.sh` for a pinned llama.cpp CPU binary

## Frozen experiment choices

- Embedding: Qwen3-Embedding-4B, Transformers FP16
- Reranker: Qwen3-Reranker-4B.Q4_K_M.gguf
- Backend: llama.cpp `llama-server`
- llama.cpp pin: b10699
- CPU only
- llama-server loopback only
- llama-server threads: 2
- llama-server context: 1024
- llama prompt cache: disabled (`--cache-ram 0`)
- llama parallel slots: 1
- First real-model benchmark: K=2 only

## Local overlay verification performed by ChatGPT

The overlay unit suite is self-contained and does not load a model:

```text
17 passed
compileall PASS
```

Full regression tests against the actual application source and the real GGUF must be executed on Kaggle after applying the patch.
