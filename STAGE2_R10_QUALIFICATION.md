# Stage-II R10 qualification

This document records the closed production-demo qualification state used as provenance for the first public package candidate.

```text
STAGE2_R10_QUALIFICATION=PASS
STAGE2_R3_TO_R10=CLOSED
R11=NOT_JUSTIFIED

WORKING_DEFAULT_K=5
K5_DEFAULT=ACCEPT
K2_FALLBACK=NOT_JUSTIFIED
FINAL_RELEASE_DEFAULT=K5_READY

SEMANTIC_3_OF_3=True
VI_TOKYO_MINUS_JAPAN=0.06420749425888062
OOM_GATE=PASS
RUN_ALL_BUDGET_SECONDS=600
POST_PACKAGE_RUN_ALL_SECONDS=594.964
RUN_ALL_WITHIN_600S=True
```

## Qualified semantic cases

1. `Which Southeast Asian country uses the baht?` → `Thailand`, rerank score `0.9858064651489258`.
2. `Thủ đô của Nhật Bản là thành phố nào?` → `Tokyo`, score `0.9770277738571167`; Tokyo-minus-Japan margin `0.06420749425888062`.
3. `Which country has thủ đô Bangkok and uses đồng baht?` → `Thailand`, rerank score `0.9812283515930176`.

## OOM gate

```text
oom_delta=0
oom_kill_delta=0
OOM_GATE=PASS
```

## Runtime and data identities

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

The hardened runtime identity was proven through `/proc/<pid>/exe` and `/proc/<pid>/maps` during qualification.

## H3 semantic instruction

```text
length=524 UTF-8 bytes
SHA256=81053e1bc7e386372ac6ea12f5523e3ea07c3b35d812f43555b1aa407eda5bc6
MAX_INSTRUCTION_CHARS=1024
```

The native reranker instruction transport remains frozen. This publication document does not alter production semantics.
