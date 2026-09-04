# Qwen3 Dual 4B CPU REST Server — Design Specification

> English | [Tiếng Việt](2026-08-30-qwen3-dual-4b-cpu-server-design.vi.md)

**Date:** 2026-08-30
**Version:** v0.1.0

## Goal

Build one CPU-only FastAPI process that keeps exactly one `Qwen/Qwen3-Embedding-4B` instance and one `Qwen/Qwen3-Reranker-4B` instance resident, exposes authenticated REST endpoints for other notebooks, and fails closed before repeating the OOM and duplicate-worker failure modes previously observed on Kaggle.

## Architecture

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

- CPU only; CUDA is never selected automatically.
- Default compute dtype: `float16` to match the already-proven embedding runtime.
- `low_cpu_mem_usage=True`.
- `device_map="auto"` is not used.
- `use_cache=False`.
- Uvicorn workers: exactly 1.
- Process singleton lock prevents accidentally launching a second model-host process.
- Global heavy-inference concurrency: exactly 1 in v0.1.0.
- Embedding microbatch: 1 by default.
- Reranker microbatch: 1 by default.
- Max sequence length: 512 by default.
- Models are read directly from `/kaggle/input`; no model copy to `/kaggle/working`.
- Remote downloads are disabled by default.
- Load order is Embedding -> warm-up -> memory gate -> Reranker -> warm-up.
- Before loading the second model, require configurable free-memory headroom.
- After both models warm up, refuse readiness if final MemAvailable is below a configurable floor.
- Public embedding vectors are normalized Float32 even when model compute is FP16/BF16.
- Public inference endpoints require a Bearer API key by default.

## Embedding semantic contract

Default model identity: `Qwen/Qwen3-Embedding-4B`.

Default query instruction remains compatible with the proven Qdrant bilingual geography index:

```text
Retrieve the geographic entity that best answers the query
```

Exact query text construction:

```text
Instruct: Retrieve the geographic entity that best answers the query
Query:<user query>
```

Document embeddings use raw document text. Requests may supply a custom instruction for other retrieval tasks.

Numerical path:

```text
AutoModel forward
-> last-token pooling
-> pooled.float()
-> torch.nn.functional.normalize(..., p=2, dim=1)
-> Float32[2560]
```

## Reranker contract

Default model identity: `Qwen/Qwen3-Reranker-4B`.

Use the Qwen Transformers protocol:

1. format instruction/query/document;
2. add the official system prefix and assistant suffix;
3. score the final-token logits for tokens `no` and `yes`;
4. compute normalized probability for `yes`;
5. sort descending while preserving original document indices.

The model supports much longer contexts, but v0.1.0 deliberately defaults to 512 tokens for CPU safety.

## API

Public without authentication:

- `GET /health`
- `GET /ready`

Bearer-authenticated:

- `GET /v1/models`
- `GET /v1/stats`
- `POST /v1/embeddings`
- `POST /v1/rerank`

`POST /v1/embeddings` accepts one string or a list plus `input_type=query|document` and an optional instruction.

`POST /v1/rerank` accepts one query and a bounded list of documents, optional instruction, and optional `return_documents`.

## Memory and evidence

Runtime records process RSS and cgroup memory snapshots. External scripts additionally capture:

- `/proc/<pid>/status` RSS samples;
- `/proc/meminfo` MemAvailable;
- cgroup `memory.current`, `memory.peak`, `memory.events`;
- startup logs;
- smoke responses;
- package versions;
- source checksum.

A run is not accepted if `oom` or `oom_kill` increases.

## Kaggle model discovery

Prefer explicit environment variables:

- `EMBEDDING_MODEL_PATH`
- `RERANKER_MODEL_PATH`

Otherwise search `/kaggle/input` for a unique validated Transformers model root. Validation inspects `config.json`, Qwen3 architecture/hidden size/layer count, safetensors index and referenced shards. Ambiguity is a hard failure.

## Out of scope for v0.1.0

- Qdrant inside this server.
- Automatic model downloading.
- Multiple Uvicorn workers.
- Parallel embedding and reranking inference.
- GGUF.
- INT8/INT4.
- Long-context production tuning.
- Production-grade multi-node rate limiting.
