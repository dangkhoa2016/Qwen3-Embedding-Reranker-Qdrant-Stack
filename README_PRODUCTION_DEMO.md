# Qwen3 Embedding + Reranker + Qdrant Production Demo
> 🌐 Language / Ngôn ngữ: **English** | [Tiếng Việt](README_PRODUCTION_DEMO.vi.md)

This demo exercises the qualified two-model retrieval stack directly:

```text
query
  -> Qwen3-Embedding-4B (Transformers CPU FP16)
  -> Qdrant 1.18.3 / canonical 20K bilingual collection
  -> Top-5 candidates
  -> Qwen3-Reranker-4B Q4_K_M (hardened llama.cpp runtime)
  -> final ranked results
```

The canonical collection is `knowledge_entities_qwen3_4b_text_v21`: 20,000 points, 2560-dimensional cosine vectors. The normal demo restores the immutable collection snapshot; it does **not** reseed or re-embed 20K records.

## Qualified configuration

```text
RETRIEVAL_TOP_K=5
RERANK_TOP_K=5
DISPLAY_TOP_K=5
LLAMA_SERVER_THREADS=2
TORCH_NUM_THREADS=2
```

Fresh Kaggle verification passed all three semantic cases, recorded zero cgroup OOM/OOM-kill events, and completed the end-to-end Run All in `594.964s` within the `600s` qualification threshold.

This is a reproducibility baseline, not a latency guarantee for every CPU host. Tuning candidate depth or parallelism requires independent validation.

## Required Kaggle inputs

1. Qwen3-Embedding-4B Transformers model.
2. Qwen3-Reranker-4B `Q4_K_M` GGUF.
3. Kaggle Dataset containing `knowledge_entities_qwen3_4b_text_v21-20260827T013824Z.snapshot`.
4. The qualified hardened llama.cpp runtime package.

Canonical snapshot identity:

```text
size=283812352 bytes
SHA256=71f12fe14ef51966069347290ad15302d389e488d7904dab6cf0cf190f43064f
```

Open `notebooks/qwen3_embedding_reranker_qdrant_kaggle_demo.ipynb` and use **Run All**.

## Reproducibility pins

- Qdrant: `1.18.3`.
- Qwen3-Reranker-4B GGUF: `Q4_K_M`.
- llama.cpp qualification pin: `b10699`.
- Qdrant collection: `knowledge_entities_qwen3_4b_text_v21`.
- Retrieval default: `K=5`.

See `PRODUCTION_QUALIFICATION.md` for qualification results and `PRODUCTION_DEMO_PROVENANCE.md` for runtime/data/artifact identities.
