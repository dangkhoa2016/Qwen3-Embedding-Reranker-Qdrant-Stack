# Production Demo: Qwen3 Embedding + Reranker + Qdrant

Demo này chạy trực tiếp stack retrieval hai model đã được qualification, **không cần Node.js**:

```text
query
  -> Qwen3-Embedding-4B (Transformers CPU FP16)
  -> Qdrant 1.18.3 / collection song ngữ canonical 20K
  -> Top-K candidates
  -> Qwen3-Reranker-4B Q4_K_M (hardened llama.cpp runtime)
  -> kết quả sau rerank
```

Collection canonical là `knowledge_entities_qwen3_4b_text_v21`, gồm 20.000 points, vector 2560 chiều, Cosine, embedding-text `v2.1`. Notebook **restore snapshot**, không seed lại 20K.

## Chính sách Top-K đã qualification

Fresh Stage-II R10 qualification đã chấp nhận profile Kaggle:

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

Gate cuối đã PASS trên fresh Kaggle Run All: 3/3 semantic cases PASS, `oom_delta=0`, `oom_kill_delta=0`, và post-package Run-All là `594.964s`, nằm trong budget `600s`.

Đây là baseline tái lập đã qualification, không phải cam kết latency cho mọi CPU host. Máy mạnh hơn có thể thử candidate pool lớn hơn, nhưng tuning đó không thuộc default đã qualification.

## Kaggle inputs bắt buộc

1. Qwen3-Embedding-4B Transformers model.
2. Qwen3-Reranker-4B Q4_K_M GGUF.
3. Dataset chứa snapshot `knowledge_entities_qwen3_4b_text_v21-20260827T013824Z.snapshot`.
4. Hardened llama runtime đúng lineage đã dùng trong Stage-II.

Snapshot canonical:

```text
size=283812352 bytes
SHA256=71f12fe14ef51966069347290ad15302d389e488d7904dab6cf0cf190f43064f
```

Notebook: `notebooks/qwen3_embedding_reranker_qdrant_kaggle_demo.ipynb`. Chạy **Run All**.
