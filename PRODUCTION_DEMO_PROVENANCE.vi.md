# Provenance của production demo
> 🌐 Language / Ngôn ngữ: [English](PRODUCTION_DEMO_PROVENANCE.md) | **Tiếng Việt**

Tài liệu này ghi lại public runtime, data và artifact identities dùng cho production demo `1.0.0`.

## Release identity

```text
Package=qwen3-embedding-reranker-qdrant-stack
Version=1.0.0
Author=Đăng Khoa <i.am@dangkhoa.dev>
License=MIT
```

Internal Python package namespace vẫn là `qwen_dual_server`.

## Model và runtime identities

```text
Embedding model=Qwen3-Embedding-4B
Embedding backend=Transformers / PyTorch CPU FP16
Reranker model=Qwen3-Reranker-4B
Reranker format=GGUF Q4_K_M
Reranker GGUF SHA256=941f7d1d1524251c026a797b803ac9575545c5d7aa19b26e0e49661d7720af49
llama.cpp pin=b10699
llama launcher SHA256=28a79707376877f09065fa05fda5a9a6f57dfb4aed01c9918123667e38ae1f41
llama implementation SHA256=c4807f2f10cdf354270ac97c1f091d0846e8154749b4b8347f5f26a40184d425
```

## Qdrant data identity

```text
Qdrant version=1.18.3
collection=knowledge_entities_qwen3_4b_text_v21
points=20000
vector size=2560
distance=cosine
snapshot=knowledge_entities_qwen3_4b_text_v21-20260827T013824Z.snapshot
snapshot size=283812352 bytes
snapshot SHA256=71f12fe14ef51966069347290ad15302d389e488d7904dab6cf0cf190f43064f
```

Production demo restore snapshot này thay vì rebuild collection.

## Behavior đã kiểm chứng

- Retrieval default: `K=5`.
- Semantic validation: 3/3 đạt.
- cgroup OOM và OOM-kill events: zero trong lần chạy đã kiểm chứng.
- End-to-end Run All: `594.964s` trong ngưỡng qualification `600s`.

Xem `PRODUCTION_QUALIFICATION.vi.md` cho complete public qualification summary.

## Các file nhạy cảm với qualification

Các file sau định nghĩa behavior nhạy cảm với qualification:

```text
src/qwen_dual_server/config.py
src/qwen_dual_server/gguf_reranker_engine.py
src/qwen_dual_server/production_demo.py
tests/test_gguf_reranker_engine.py
tests/test_production_demo.py
```

Behavioral changes vào các file này cần explicit review và có thể cần fresh qualification evidence.
