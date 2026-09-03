# Kaggle production-demo execution guide

1. Attach the Qwen3-Embedding-4B Transformers model.
2. Attach the Qwen3-Reranker-4B Q4_K_M GGUF model.
3. Attach the canonical Qdrant 20K Kaggle Dataset containing `knowledge_entities_qwen3_4b_text_v21-20260827T013824Z.snapshot`.
4. Open `notebooks/qwen3_embedding_reranker_qdrant_kaggle_demo.ipynb`.
5. Use **Run All**.

Do not seed/re-embed 20K records. The notebook restores the immutable canonical snapshot.

Default proposal: `RETRIEVAL_TOP_K=5`, `RERANK_TOP_K=5`, `DISPLAY_TOP_K=5`, two CPU threads. A stronger machine can edit the first configuration cell, including profiles such as `50/50/10` and 8 threads.

The final notebook cell decides whether K=5 satisfies the fresh-session release gate (`<=600s`, 3/3 expected top-1, OOM deltas zero). It prints a K=2 fallback recommendation if not.
