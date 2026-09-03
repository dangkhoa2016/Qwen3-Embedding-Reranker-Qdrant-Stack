# Qwen3 Embedding + Reranker + Qdrant Production Demo

This demo showcases the two-model retrieval stack directly, without a Node.js application layer:

```text
query
  -> Qwen3-Embedding-4B (Transformers CPU FP16)
  -> Qdrant 1.18.3 / canonical 20K bilingual collection
  -> Top-K candidates
  -> Qwen3-Reranker-4B Q4_K_M (llama.cpp b10699)
  -> final ranked results
```

The canonical collection is `knowledge_entities_qwen3_4b_text_v21`: 20,000 points, 2560-dimensional cosine vectors, embedding-text `v2.1`. The normal demo restores the immutable collection snapshot; it does **not** reseed 20K records.

## Top-K policy

The proposed Kaggle default is:

```text
RETRIEVAL_TOP_K=5
RERANK_TOP_K=5
DISPLAY_TOP_K=5
LLAMA_SERVER_THREADS=2
TORCH_NUM_THREADS=2
```

K=5 becomes the promoted default only after a fresh Kaggle **Run All <= 600 seconds**, all three demo cases pass, and cgroup `oom` / `oom_kill` deltas are zero. If that gate fails, document and use K=2 as the conservative Kaggle default.

A stronger host may try, for example, `50/50/10` with 8 CPU threads. This is configuration support, not a performance guarantee.

## Required Kaggle inputs

1. Qwen3-Embedding-4B Transformers model.
2. Qwen3-Reranker-4B Q4_K_M GGUF.
3. Kaggle Dataset containing `knowledge_entities_qwen3_4b_text_v21-20260827T013824Z.snapshot`.

The snapshot locator verifies the exact basename, 283812352-byte size, and SHA-256 `71f12fe14ef51966069347290ad15302d389e488d7904dab6cf0cf190f43064f`.

Open `notebooks/qwen3_embedding_reranker_qdrant_kaggle_demo.ipynb` and use **Run All**.

## Reproducibility pins

- Qdrant: `1.18.3`, Linux x86_64 MUSL release asset.
- Qwen3-Reranker-4B GGUF: Q4_K_M.
- llama.cpp: `b10699` via the existing pinned setup script.
- Qdrant canonical collection: `knowledge_entities_qwen3_4b_text_v21`.

CPU optimization beyond this profile is deferred. The post-release roadmap includes GPU reranking, larger candidate pools, adaptive Top-K, candidate shortlisting, and hybrid dense+sparse retrieval.
