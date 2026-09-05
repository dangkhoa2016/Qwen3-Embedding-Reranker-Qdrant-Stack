# Post-release performance roadmap
> 🌐 Language / Ngôn ngữ: **English** | [Tiếng Việt](roadmap.vi.md)

The `1.0.0` release keeps the qualified CPU production-demo configuration stable. Future performance work should be evaluated as new qualification work rather than silently changing the published baseline.

Candidate directions:

1. GPU reranker qualification with larger candidate pools.
2. GPU embedding + reranker topology.
3. Larger Qdrant retrieval pools and rerank depths where resources permit.
4. Adaptive Top-K based on retrieval ambiguity/confidence.
5. Lightweight candidate shortlisting before rerank.
6. Dense+sparse Qdrant hybrid retrieval.
7. Separate or distributed inference workers.

Any promoted change should retain reproducibility, memory-safety evidence, semantic validation, and explicit runtime/data provenance.
