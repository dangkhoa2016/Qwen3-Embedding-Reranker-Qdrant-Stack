# Roadmap performance sau release
> 🌐 Language / Ngôn ngữ: [English](roadmap.md) | **Tiếng Việt**

Release scope hiện tại freeze thêm CPU tuning. Evidence được giữ lại từ qualification trước:

- Q4_K_M same-host K2: qualified.
- TorchAO INT8: closed; chậm hơn trên qualified CPU host.
- llama.cpp `--parallel 2`: không có material K5 benefit trên qualified host 2 physical core.

Các candidate sau release, theo thứ tự:

1. GPU reranker, qualify K5/K10/K20/K50 khi thực tế.
2. GPU embedding + reranker topology.
3. Qdrant candidate pools lớn hơn và rerank depth lớn hơn.
4. Adaptive Top-K dựa trên retrieval ambiguity/confidence.
5. Candidate shortlisting rẻ trước rerank.
6. Dense+sparse Qdrant hybrid retrieval.
7. Separate/distributed inference workers.
