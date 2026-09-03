> **INT8 experimental copy**
>
> This directory is not the canonical v0.1.1 release. For the TorchAO INT8
> A8W8 / weight-only Kaggle experiment, start with **README_INT8_EXPERIMENT.md**.
> The frozen v0.1.1 HEAD/tag remains `684b082c730adf8283efc02a7620c9bee878d18f`.

# Qwen3 Dual 4B CPU REST Server v0.1.1

A conservative, CPU-only shared inference server for:

- `Qwen/Qwen3-Embedding-4B`
- `Qwen/Qwen3-Reranker-4B`

The target is a Kaggle CPU/RAM session where both model checkpoints are attached read-only under `/kaggle/input`, while other notebooks call this server through authenticated REST endpoints.

## Why this implementation is deliberately conservative

Previous Qwen3-Embedding-4B experiments showed that final model size is not the only RAM constraint: startup conversion/materialization can produce a much larger peak. This server therefore starts with one process, one Uvicorn worker, one singleton instance per model, serialized heavy inference, `low_cpu_mem_usage=True`, bounded sequence length and micro-batch 1. It records cgroup OOM counters and refuses to load the second model or become ready if memory headroom is too small.

It intentionally does **not** use `SentenceTransformer(...)`, `device_map="auto"`, multiple Uvicorn workers, runtime FP32 expansion, model downloads by default, Qdrant, or parallel heavy inference.

## Model behavior

Embedding path:

```text
query/document
  -> Qwen3 AutoModel on CPU (FP16 default)
  -> last-token pooling
  -> cast pooled vector to FP32
  -> L2 normalize in FP32
  -> Float32[2560]
```

The default query instruction preserves the existing bilingual Qdrant project's canonical contract:

```text
Instruct: Retrieve the geographic entity that best answers the query
Query:<query>
```

Documents are embedded raw. A caller may supply a bounded custom query instruction for a different retrieval task.

Reranker path follows the Qwen Transformers yes/no scoring protocol: format `<Instruct>`, `<Query>`, `<Document>`, apply the official system/user/assistant framing, read final-position logits for `no` and `yes`, cast logits to FP32, and return the normalized `yes` probability.

## HTTP API

Public liveness/readiness:

```text
GET /health
GET /ready
```

Bearer-authenticated endpoints:

```text
GET  /v1/models
GET  /v1/stats
POST /v1/embeddings
POST /v1/rerank
```

Embedding example:

```bash
curl -sS "$SERVER_URL/v1/embeddings" \
  -H "Authorization: Bearer $DUAL_API_KEY" \
  -H 'Content-Type: application/json' \
  -d '{"input":"Southeast Asian country whose currency is baht","input_type":"query"}'
```

Reranking example:

```bash
curl -sS "$SERVER_URL/v1/rerank" \
  -H "Authorization: Bearer $DUAL_API_KEY" \
  -H 'Content-Type: application/json' \
  -d '{"query":"Which Southeast Asian country uses the baht?","documents":["Thailand uses the Thai baht.","Canada uses the Canadian dollar."],"return_documents":true}'
```

## Kaggle quick start

Use the full OpenCode runbook included at repository root:

```text
OPENCODE_QWEN3_DUAL_4B_CPU_SERVER_KAGGLE_RUNBOOK_2026-08-30.md
```

Minimum manual path:

```bash
python -m pip install -r requirements.txt
python -m pip install -e . --no-deps --no-build-isolation
PYTHONPATH=src pytest -q
python scripts/preflight.py

export DUAL_API_KEY="$(openssl rand -hex 32)"
export MODEL_DTYPE=float16
export MAX_SEQ_LENGTH=512
export MAX_CONCURRENT_INFERENCE=1
export RUN_ROOT="/kaggle/working/qwen3-dual-$(date -u +%Y%m%dT%H%M%SZ)"
bash scripts/start-and-monitor.sh

export SMOKE_OUTPUT="$RUN_ROOT/smoke/smoke.json"
mkdir -p "$RUN_ROOT/smoke"
python scripts/smoke-http.py
```

Do not expose the server publicly until local smoke passes. Keep Uvicorn bound to `127.0.0.1`; put an authenticated tunnel in front of it.

## Safe defaults

```text
MODEL_DTYPE=float16
MAX_SEQ_LENGTH=512
EMBEDDING_MICROBATCH_SIZE=1
RERANKER_MICROBATCH_SIZE=1
MAX_CONCURRENT_INFERENCE=1
SECOND_MODEL_MIN_AVAILABLE_GIB=10
FINAL_MIN_AVAILABLE_GIB=4
MAX_RERANK_DOCUMENTS=20
ALLOW_REMOTE_MODEL_DOWNLOAD=0
UVICORN_WORKERS=1 (hard-coded wrapper)
```

## Tests

Fast tests use fake loaders/tensors and do not need either 8 GB checkpoint:

```bash
PYTHONPATH=src pytest -q
python -m compileall -q src scripts
bash -n scripts/*.sh
```

Real-model proof is intentionally done only in the Kaggle acceptance run so that memory evidence and OOM counters are captured around the actual model load.

## Qdrant production demo (v0.2.0 derived source)

A focused Kaggle demo now combines the qualified hybrid inference service with the canonical Qdrant 20K snapshot. It intentionally does **not** require a Node.js application layer. See `README_PRODUCTION_DEMO.md` (English), `README_PRODUCTION_DEMO.vi.md` (Vietnamese), and `notebooks/qwen3_embedding_reranker_qdrant_kaggle_demo.ipynb`.

The notebook proposes K=5 as the Kaggle default but promotes it only when a fresh Run-All completes within 600 seconds, all three semantic demo cases pass, and cgroup OOM/OOM-kill deltas remain zero; otherwise it reports K=2 as the conservative default.
