# Post-release performance roadmap

> English | [Tiếng Việt](roadmap.vi.md)

Current release scope freezes further CPU tuning. Evidence retained from prior qualification:

- Q4_K_M same-host K2: qualified.
- TorchAO INT8: closed; slower on the qualified CPU host.
- llama.cpp `--parallel 2`: no material K5 benefit on the qualified 2-physical-core host.

Post-release candidates, in order:

1. GPU reranker, qualify K5/K10/K20/K50 where practical.
2. GPU embedding + reranker topology.
3. Larger Qdrant candidate pools and larger rerank depths.
4. Adaptive Top-K based on retrieval ambiguity/confidence.
5. Cheap candidate shortlisting before rerank.
6. Dense+sparse Qdrant hybrid retrieval.
7. Separate/distributed inference workers.
