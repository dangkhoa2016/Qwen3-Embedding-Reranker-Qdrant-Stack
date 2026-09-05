# Kiểm chứng production
> 🌐 Language / Ngôn ngữ: [English](PRODUCTION_QUALIFICATION.md) | **Tiếng Việt**

Tài liệu này ghi lại kết quả kiểm chứng production demo công khai cho `qwen3-embedding-reranker-qdrant-stack` `1.0.0`.

## Kết quả kiểm chứng

```text
Production qualification: PASS
Retrieval default: K=5
Semantic validation: 3/3 PASS
cgroup OOM events: 0
cgroup OOM-kill events: 0
Run All threshold: 600s
Verified Run All: 594.964s
```

Kết quả thời gian áp dụng cho môi trường Kaggle CPU đã được kiểm chứng và không phải cam kết hiệu năng chung.

## Semantic validation

1. `Which Southeast Asian country uses the baht?` → `Thailand`, rerank score `0.9858064651489258`.
2. `Thủ đô của Nhật Bản là thành phố nào?` → `Tokyo`, score `0.9770277738571167`; Tokyo-minus-Japan margin `0.06420749425888062`.
3. `Which country has thủ đô Bangkok and uses đồng baht?` → `Thailand`, rerank score `0.9812283515930176`.

## Runtime và data identities

```text
Qdrant version=1.18.3
collection=knowledge_entities_qwen3_4b_text_v21
points=20000
vector size=2560
distance=cosine

snapshot SHA256=71f12fe14ef51966069347290ad15302d389e488d7904dab6cf0cf190f43064f
reranker GGUF SHA256=941f7d1d1524251c026a797b803ac9575545c5d7aa19b26e0e49661d7720af49
llama launcher SHA256=28a79707376877f09065fa05fda5a9a6f57dfb4aed01c9918123667e38ae1f41
llama implementation SHA256=c4807f2f10cdf354270ac97c1f091d0846e8154749b4b8347f5f26a40184d425
```

Identity của hardened llama.cpp runtime đã được xác minh trong lúc qualification bằng executing process và loaded mappings.

## Reranker instruction contract

```text
instruction UTF-8 length=524 bytes
instruction SHA256=81053e1bc7e386372ac6ea12f5523e3ea07c3b35d812f43555b1aa407eda5bc6
MAX_INSTRUCTION_CHARS=1024
```

Thay đổi làm thay đổi qualified semantic behavior cần fresh qualification evidence.
