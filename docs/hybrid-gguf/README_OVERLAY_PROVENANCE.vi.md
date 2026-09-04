# Qwen3 Hybrid GGUF Reranker Overlay
> 🌐 Language / Ngôn ngữ: [English](README_OVERLAY_PROVENANCE.md) | **Tiếng Việt**

Overlay này thêm opt-in `llama_cpp` reranker backend vào Qwen3 dual-4B CPU server hiện có mà không thay embedding implementation hoặc public `/v1/rerank` schema.

## Những gì overlay thêm

- `src/qwen_dual_server/gguf_locator.py`
- `src/qwen_dual_server/llama_server.py`
- `src/qwen_dual_server/gguf_reranker_engine.py`
- unit tests cho cả ba module
- `tools/apply_hybrid_gguf_patch.py` để patch một fresh disposable source extraction
- `scripts/setup_llama_cpp_b10699.sh` cho pinned llama.cpp CPU binary

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

## Local overlay verification do ChatGPT thực hiện

Overlay unit suite là self-contained và không load model:

```text
17 passed
compileall PASS
```

Full regression tests với actual application source và real GGUF phải được chạy trên Kaggle sau khi apply patch.
