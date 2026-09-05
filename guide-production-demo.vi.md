# Hướng dẫn chạy Kaggle production demo
> 🌐 Language / Ngôn ngữ: [English](guide-production-demo.md) | **Tiếng Việt**

1. Attach Qwen3-Embedding-4B Transformers model.
2. Attach Qwen3-Reranker-4B `Q4_K_M` GGUF model.
3. Attach canonical Qdrant 20K Dataset chứa `knowledge_entities_qwen3_4b_text_v21-20260827T013824Z.snapshot`.
4. Cung cấp hardened llama.cpp runtime package mà notebook yêu cầu.
5. Mở `notebooks/qwen3_embedding_reranker_qdrant_kaggle_demo.ipynb`.
6. Dùng **Run All**.

Không seed hoặc re-embed 20K record. Notebook restore immutable canonical snapshot.

Cấu hình đã kiểm chứng:

```text
RETRIEVAL_TOP_K=5
RERANK_TOP_K=5
DISPLAY_TOP_K=5
LLAMA_SERVER_THREADS=2
TORCH_NUM_THREADS=2
```

Lần chạy đã xác minh đạt 3/3 semantic case, ghi nhận zero cgroup OOM/OOM-kill và hoàn tất end-to-end Run All trong `594.964s`, nằm trong ngưỡng qualification `600s`.

Xem `PRODUCTION_QUALIFICATION.vi.md` và `PRODUCTION_DEMO_PROVENANCE.vi.md` để biết đầy đủ public verification record.
