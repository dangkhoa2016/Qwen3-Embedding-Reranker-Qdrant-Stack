# Kaggle production-demo execution guide

> English | [Tiếng Việt](guide-production-demo.vi.md)

1. Attach the Qwen3-Embedding-4B Transformers model.
2. Attach the Qwen3-Reranker-4B Q4_K_M GGUF model.
3. Attach the canonical Qdrant 20K Dataset containing `knowledge_entities_qwen3_4b_text_v21-20260827T013824Z.snapshot`.
4. Provide the qualified hardened llama runtime package expected by the notebook.
5. Open `notebooks/qwen3_embedding_reranker_qdrant_kaggle_demo.ipynb`.
6. Use **Run All**.

Do not seed/re-embed 20K records. The notebook restores the immutable canonical snapshot.

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

The accepted R10 run passed 3/3 semantic cases with zero cgroup OOM/OOM-kill deltas and completed the post-package Run All in `594.964s` under the `600s` budget. K=2 is not justified by the final qualification evidence.
