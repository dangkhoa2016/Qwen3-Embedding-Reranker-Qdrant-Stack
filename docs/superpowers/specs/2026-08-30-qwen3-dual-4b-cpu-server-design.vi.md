# Qwen3 Dual 4B CPU REST Server — Đặc tả thiết kế
> 🌐 Language / Ngôn ngữ: [English](2026-08-30-qwen3-dual-4b-cpu-server-design.md) | **Tiếng Việt**

**Ngày:** 2026-08-30  
**Version:** v0.1.0

## Mục tiêu

Xây dựng một FastAPI process CPU-only giữ đúng một instance `Qwen/Qwen3-Embedding-4B` và một instance `Qwen/Qwen3-Reranker-4B` resident, expose authenticated REST endpoints cho notebook khác và fail closed trước khi lặp lại các OOM/duplicate-worker failure mode từng quan sát trên Kaggle.

## Kiến trúc

```text
remote notebooks
      |
      | HTTPS via optional tunnel
      v
FastAPI :8000 (one process / one worker)
      |
      +-- /v1/embeddings --> Embedding singleton
      |                     FP16/BF16 CPU
      |                     last-token pool
      |                     cast FP32
      |                     L2 normalize FP32
      |
      +-- /v1/rerank -----> Reranker singleton
                            FP16/BF16 CPU
                            official yes/no scoring protocol

All heavy inference passes through one global concurrency gate.
```

## Frozen safety constraints

- Chỉ CPU; CUDA không bao giờ tự động được chọn.
- Compute dtype mặc định: `float16` để khớp embedding runtime đã được chứng minh.
- `low_cpu_mem_usage=True`.
- Không dùng `device_map="auto"`.
- `use_cache=False`.
- Uvicorn workers: đúng 1.
- Process singleton lock ngăn vô tình launch model-host process thứ hai.
- Global heavy-inference concurrency: đúng 1 trong v0.1.0.
- Embedding microbatch mặc định 1.
- Reranker microbatch mặc định 1.
- Max sequence length mặc định 512.
- Model đọc trực tiếp từ `/kaggle/input`; không copy model sang `/kaggle/working`.
- Remote downloads tắt mặc định.
- Load order: Embedding -> warm-up -> memory gate -> Reranker -> warm-up.
- Trước khi load model thứ hai phải còn configurable free-memory headroom.
- Sau warm-up cả hai model, từ chối readiness nếu final MemAvailable thấp hơn configurable floor.
- Public embedding vectors là normalized Float32 ngay cả khi model compute FP16/BF16.
- Public inference endpoints yêu cầu Bearer API key mặc định.

## Embedding semantic contract

Model identity mặc định: `Qwen/Qwen3-Embedding-4B`.

Default query instruction giữ tương thích với proven Qdrant bilingual geography index:

```text
Retrieve the geographic entity that best answers the query
```

Exact query text construction:

```text
Instruct: Retrieve the geographic entity that best answers the query
Query:<user query>
```

Document embeddings dùng raw document text. Request có thể cung cấp custom instruction cho retrieval task khác.

Numerical path:

```text
AutoModel forward
-> last-token pooling
-> pooled.float()
-> torch.nn.functional.normalize(..., p=2, dim=1)
-> Float32[2560]
```

## Reranker contract

Model identity mặc định: `Qwen/Qwen3-Reranker-4B`.

Dùng Qwen Transformers protocol:

1. format instruction/query/document;
2. thêm official system prefix và assistant suffix;
3. score final-token logits cho token `no` và `yes`;
4. tính normalized probability cho `yes`;
5. sort giảm dần trong khi giữ original document indices.

Model hỗ trợ context dài hơn nhiều, nhưng v0.1.0 chủ đích default 512 token vì CPU safety.

## API

Public không cần authentication:

- `GET /health`
- `GET /ready`

Bearer-authenticated:

- `GET /v1/models`
- `GET /v1/stats`
- `POST /v1/embeddings`
- `POST /v1/rerank`

`POST /v1/embeddings` nhận một string hoặc list, cùng `input_type=query|document` và optional instruction.

`POST /v1/rerank` nhận một query và bounded list documents, optional instruction và optional `return_documents`.

## Memory và evidence

Runtime ghi process RSS và cgroup memory snapshots. External scripts còn capture:

- `/proc/<pid>/status` RSS samples;
- `/proc/meminfo` MemAvailable;
- cgroup `memory.current`, `memory.peak`, `memory.events`;
- startup logs;
- smoke responses;
- package versions;
- source checksum.

Một run không được accept nếu `oom` hoặc `oom_kill` tăng.

## Kaggle model discovery

Ưu tiên explicit environment variables:

- `EMBEDDING_MODEL_PATH`
- `RERANKER_MODEL_PATH`

Nếu không có, search `/kaggle/input` để tìm unique validated Transformers model root. Validation inspect `config.json`, Qwen3 architecture/hidden size/layer count, safetensors index và referenced shards. Ambiguity là hard failure.

## Ngoài phạm vi v0.1.0

- Qdrant bên trong server này.
- Automatic model downloading.
- Nhiều Uvicorn workers.
- Parallel embedding/reranking inference.
- GGUF.
- INT8/INT4.
- Long-context production tuning.
- Production-grade multi-node rate limiting.
