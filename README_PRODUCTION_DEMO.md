# Qwen3 Embedding + Reranker + Qdrant Production Demo

> English | [Tiếng Việt](README_PRODUCTION_DEMO.vi.md)

This demo exercises the qualified two-model retrieval stack directly, without a Node.js application layer:

```text
query
  -> Qwen3-Embedding-4B (Transformers CPU FP16)
  -> Qdrant 1.18.3 / canonical 20K bilingual collection
  -> Top-K candidates
  -> Qwen3-Reranker-4B Q4_K_M (hardened llama.cpp runtime)
  -> final ranked results
```

The canonical collection is `knowledge_entities_qwen3_4b_text_v21`: 20,000 points, 2560-dimensional cosine vectors, embedding-text `v2.1`. The normal demo restores the immutable collection snapshot; it does **not** reseed 20K records.

## Qualified Top-K policy

The fresh Stage-II R10 qualification accepted the following Kaggle profile:

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

The acceptance gate was satisfied on a fresh Kaggle Run All: all three semantic cases passed, cgroup OOM/OOM-kill deltas remained zero, and the final post-package Run-All time was `594.964s` within the `600s` budget.

This qualification is a reproducibility baseline, not a latency guarantee for every CPU host. Stronger hosts may experiment with larger candidate pools, but such tuning is outside the qualified default.

## Required Kaggle inputs

1. Qwen3-Embedding-4B Transformers model.
2. Qwen3-Reranker-4B Q4_K_M GGUF.
3. Kaggle Dataset containing `knowledge_entities_qwen3_4b_text_v21-20260827T013824Z.snapshot`.
4. The qualified hardened llama runtime package used by the Stage-II run.

The canonical snapshot identity is:

```text
size=283812352 bytes
SHA256=71f12fe14ef51966069347290ad15302d389e488d7904dab6cf0cf190f43064f
```

Open `notebooks/qwen3_embedding_reranker_qdrant_kaggle_demo.ipynb` and use **Run All**.

## Reproducibility pins

- Qdrant: `1.18.3`.
- Qwen3-Reranker-4B GGUF: `Q4_K_M`.
- llama.cpp qualification lineage: `b10699` with the hardened launcher/implementation identities recorded in `STAGE2_R10_QUALIFICATION.md`.
- Qdrant collection: `knowledge_entities_qwen3_4b_text_v21`.
- Qualified default: `K=5`.
