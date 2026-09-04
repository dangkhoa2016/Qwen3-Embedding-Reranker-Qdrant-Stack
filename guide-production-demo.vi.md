# Hướng dẫn chạy Kaggle production demo
> 🌐 Language / Ngôn ngữ: [English](guide-production-demo.md) | **Tiếng Việt**

1. Attach model Transformers Qwen3-Embedding-4B.
2. Attach model Qwen3-Reranker-4B Q4_K_M GGUF.
3. Attach canonical Qdrant 20K Dataset chứa `knowledge_entities_qwen3_4b_text_v21-20260827T013824Z.snapshot`.
4. Cung cấp qualified hardened llama runtime package mà notebook yêu cầu.
5. Mở `notebooks/qwen3_embedding_reranker_qdrant_kaggle_demo.ipynb`.
6. Dùng **Run All**.

Không seed/re-embed 20K records. Notebook restore immutable canonical snapshot.

Qualified default:

```text
RETRIEVAL_TOP_K=5
RERANK_TOP_K=5
DISPLAY_TOP_K=5
LLAMA_SERVER_THREADS=2
TORCH_NUM_THREADS=2
K5_DEFAULT=ACCEPT
K2_FALLBACK=NOT_JUSTIFIED
FINAL_RELEASE_DEFAULT=K5_READY
```

Accepted R10 run pass 3/3 semantic cases với zero cgroup OOM/OOM-kill deltas và hoàn tất post-package Run All trong `594.964s`, dưới budget `600s`. K=2 không được justified bởi final qualification evidence.
