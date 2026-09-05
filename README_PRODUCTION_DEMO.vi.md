# Qwen3 Embedding + Reranker + Qdrant Production Demo
> 🌐 Language / Ngôn ngữ: [English](README_PRODUCTION_DEMO.md) | **Tiếng Việt**

Demo này chạy trực tiếp retrieval stack hai model đã được kiểm chứng:

```text
query
  -> Qwen3-Embedding-4B (Transformers CPU FP16)
  -> Qdrant 1.18.3 / canonical 20K bilingual collection
  -> Top-5 candidates
  -> Qwen3-Reranker-4B Q4_K_M (hardened llama.cpp runtime)
  -> final ranked results
```

Canonical collection là `knowledge_entities_qwen3_4b_text_v21`: 20.000 point, vector cosine 2560 chiều. Demo bình thường restore immutable collection snapshot; **không** reseed hoặc re-embed 20K record.

## Cấu hình đã kiểm chứng

```text
RETRIEVAL_TOP_K=5
RERANK_TOP_K=5
DISPLAY_TOP_K=5
LLAMA_SERVER_THREADS=2
TORCH_NUM_THREADS=2
```

Fresh Kaggle verification đạt cả ba semantic case, ghi nhận zero cgroup OOM/OOM-kill và hoàn tất end-to-end Run All trong `594.964s`, nằm trong ngưỡng qualification `600s`.

Đây là reproducibility baseline, không phải cam kết latency cho mọi CPU host. Việc tuning candidate depth hoặc parallelism cần được kiểm chứng độc lập.

## Kaggle inputs bắt buộc

1. Qwen3-Embedding-4B Transformers model.
2. Qwen3-Reranker-4B `Q4_K_M` GGUF.
3. Kaggle Dataset chứa `knowledge_entities_qwen3_4b_text_v21-20260827T013824Z.snapshot`.
4. Hardened llama.cpp runtime package đã được kiểm chứng.

Canonical snapshot identity:

```text
size=283812352 bytes
SHA256=71f12fe14ef51966069347290ad15302d389e488d7904dab6cf0cf190f43064f
```

Mở `notebooks/qwen3_embedding_reranker_qdrant_kaggle_demo.ipynb` và dùng **Run All**.

## Reproducibility pins

- Qdrant: `1.18.3`.
- Qwen3-Reranker-4B GGUF: `Q4_K_M`.
- llama.cpp qualification pin: `b10699`.
- Qdrant collection: `knowledge_entities_qwen3_4b_text_v21`.
- Retrieval default: `K=5`.

Xem `PRODUCTION_QUALIFICATION.vi.md` cho qualification results và `PRODUCTION_DEMO_PROVENANCE.vi.md` cho runtime/data/artifact identities.
