# Kaggle production-demo execution guide
> 🌐 Language / Ngôn ngữ: **English** | [Tiếng Việt](guide-production-demo.vi.md)

1. Attach the Qwen3-Embedding-4B Transformers model.
2. Attach the Qwen3-Reranker-4B `Q4_K_M` GGUF model.
3. Attach the canonical Qdrant 20K Dataset containing `knowledge_entities_qwen3_4b_text_v21-20260827T013824Z.snapshot`.
4. Provide the qualified hardened llama.cpp runtime package expected by the notebook.
5. Open `notebooks/qwen3_embedding_reranker_qdrant_kaggle_demo.ipynb`.
6. Use **Run All**.

Do not seed or re-embed 20K records. The notebook restores the immutable canonical snapshot.

Qualified configuration:

```text
RETRIEVAL_TOP_K=5
RERANK_TOP_K=5
DISPLAY_TOP_K=5
LLAMA_SERVER_THREADS=2
TORCH_NUM_THREADS=2
```

The verified run passed 3/3 semantic cases, recorded zero cgroup OOM/OOM-kill events, and completed the end-to-end Run All in `594.964s` within the `600s` qualification threshold.

See `PRODUCTION_QUALIFICATION.md` and `PRODUCTION_DEMO_PROVENANCE.md` for the complete public verification record.
