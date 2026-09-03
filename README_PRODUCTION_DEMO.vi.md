# Production Demo: Qwen3 Embedding + Reranker + Qdrant

Demo này tập trung trực tiếp vào cặp model, **không cần Node.js**:

```text
query
  -> Qwen3-Embedding-4B (Transformers CPU FP16)
  -> Qdrant 1.18.3 / collection song ngữ canonical 20K
  -> Top-K candidates
  -> Qwen3-Reranker-4B Q4_K_M (llama.cpp b10699)
  -> kết quả sau rerank
```

Collection canonical là `knowledge_entities_qwen3_4b_text_v21`, gồm 20.000 points, vector 2560 chiều, Cosine, embedding-text `v2.1`. Notebook **restore snapshot**, không seed lại 20K.

## Top-K

Profile đề xuất cho Kaggle:

```text
RETRIEVAL_TOP_K=5
RERANK_TOP_K=5
DISPLAY_TOP_K=5
LLAMA_SERVER_THREADS=2
TORCH_NUM_THREADS=2
```

Chỉ promote K=5 thành mặc định sau khi chạy một fresh Kaggle session và thỏa cả ba điều kiện: Run All <= 600 giây, 3/3 demo cases PASS, `oom_delta=0` và `oom_kill_delta=0`. Nếu không, dùng K=2 làm mặc định bảo thủ.

Người dùng máy mạnh hơn có thể đổi cell cấu hình, ví dụ retrieve 50, rerank 50, display 10 và 8 CPU threads. Đây là khả năng cấu hình, không phải cam kết latency.

Notebook: `notebooks/qwen3_embedding_reranker_qdrant_kaggle_demo.ipynb`.
