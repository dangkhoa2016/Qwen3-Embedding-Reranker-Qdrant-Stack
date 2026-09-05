# Qwen3-Embedding-Reranker-Qdrant-Stack
> 🌐 Language / Ngôn ngữ: **English** | [Tiếng Việt](README.vi.md)

[![CI](https://github.com/dangkhoa2016/Qwen3-Embedding-Reranker-Qdrant-Stack/actions/workflows/ci.yml/badge.svg)](https://github.com/dangkhoa2016/Qwen3-Embedding-Reranker-Qdrant-Stack/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-%3E%3D3.10-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Qdrant](https://img.shields.io/badge/Qdrant-1.18.3-red)
![CPU qualified](https://img.shields.io/badge/CPU-qualified-success)

`qwen3-embedding-reranker-qdrant-stack` is a production-oriented retrieval stack built around Qwen3-Embedding-4B, Qwen3-Reranker-4B, and Qdrant. It provides a CPU-oriented FastAPI service and a reproducible 20K-point bilingual Qdrant production demo. It is an embedding/retrieval/reranking project, not a chat-LLM server.

## What this project provides

- Bearer-authenticated REST APIs for Qwen3 embeddings and reranking.
- `Qwen/Qwen3-Embedding-4B` through Transformers / PyTorch with the qualified CPU FP16 profile.
- Two reranker backends:
  - Transformers for the general source-tree default;
  - GGUF `Q4_K_M` through a hardened llama.cpp runtime for the qualified production demo.
- Request-size, queue, concurrency, memory-headroom, startup, and readiness safeguards.
- A canonical Qdrant `1.18.3` 20K bilingual snapshot workflow.
- Reproducibility documentation, operator scripts, provenance records, and an executable Kaggle notebook.

Large model files, the GGUF artifact, llama.cpp runtime, and Qdrant snapshot are intentionally **not bundled** with the Python package.

## Production qualification

The published `1.0.0` production-demo profile was verified on a fresh Kaggle CPU session:

```text
Production qualification: PASS
Semantic validation: 3/3 PASS
cgroup OOM events: 0
cgroup OOM-kill events: 0
Run All: 594.964s
Qualification threshold: 600s
Retrieval default: K=5
```

The timing result is specific to the qualified environment and is **not** a general CPU performance guarantee.

## Architecture

```text
REST request
  -> FastAPI authentication / limits / single-inference gate
  -> Qwen3-Embedding-4B
  -> normalized Float32[2560] embedding

Production-demo retrieval path:
query
  -> Qwen3-Embedding-4B (Transformers / PyTorch CPU FP16)
  -> Qdrant 1.18.3 / canonical 20K bilingual snapshot
  -> Top-5 candidates
  -> Qwen3-Reranker-4B Q4_K_M (GGUF / hardened llama.cpp)
  -> final ranked results
```

The production-demo retrieval depth is `K=5`.

## Requirements

### Python and PyTorch

Python `>=3.10` is required.

PyTorch is deliberately **not installed by `requirements.txt` or package metadata**. Install a PyTorch build appropriate for your host before running the service outside an environment that already provides it.

### External model/runtime assets

A complete deployment needs the assets required by the selected backend:

1. `Qwen/Qwen3-Embedding-4B` Transformers model files.
2. Compatible Qwen3 reranker Transformers files for the Transformers reranker backend.
3. `Qwen3-Reranker-4B.Q4_K_M.gguf` plus the qualified llama.cpp runtime for the GGUF production-demo backend.
4. `knowledge_entities_qwen3_4b_text_v21-20260827T013824Z.snapshot` for the Qdrant production demo.

Verified runtime/data identities are documented in `PRODUCTION_QUALIFICATION.md` and `PRODUCTION_DEMO_PROVENANCE.md`.

## Installation

The project is not currently published to a package index, so install from source:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install .
```

For development/test dependencies:

```bash
python -m pip install -r requirements-dev.txt
```

Install the appropriate PyTorch runtime separately.

## Quick start

The checked-in launcher binds to localhost by default and refuses to start without authentication unless insecure no-auth mode is explicitly enabled.

1. Copy the environment template:

```bash
cp .env.example .env
```

2. Set a strong API key and valid model paths:

```text
DUAL_API_KEY=<strong-random-secret>
EMBEDDING_MODEL_PATH=/absolute/path/to/Qwen3-Embedding-4B
RERANKER_MODEL_PATH=/absolute/path/to/Qwen3-Reranker-4B
```

For the GGUF reranker backend:

```text
RERANKER_BACKEND=llama_cpp
RERANKER_GGUF_PATH=/absolute/path/to/Qwen3-Reranker-4B.Q4_K_M.gguf
LLAMA_SERVER_BIN=/absolute/path/to/qualified/llama-server
```

3. Export the environment and start the service:

```bash
set -a
source .env
set +a
bash scripts/start-server.sh
```

4. Check liveness/readiness:

```bash
curl -s http://127.0.0.1:8000/health
curl -s http://127.0.0.1:8000/ready
```

`/ready` returns HTTP `503` until the runtime is ready.

## API overview

Unauthenticated operational endpoints:

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

Example embedding request:

```bash
curl -s http://127.0.0.1:8000/v1/embeddings \
  -H "Authorization: Bearer $DUAL_API_KEY" \
  -H 'Content-Type: application/json' \
  -d '{"input":"Which Southeast Asian country uses the baht?","input_type":"query"}'
```

Example rerank request:

```bash
curl -s http://127.0.0.1:8000/v1/rerank \
  -H "Authorization: Bearer $DUAL_API_KEY" \
  -H 'Content-Type: application/json' \
  -d '{"query":"capital of Japan","documents":["Tokyo","Osaka"],"return_documents":true}'
```

Optional request instructions are bounded by:

```text
MAX_INSTRUCTION_CHARS=1024
```

## Safe CPU defaults

```text
MODEL_DTYPE=float16
MAX_SEQ_LENGTH=512
EMBEDDING_MICROBATCH_SIZE=1
RERANKER_MICROBATCH_SIZE=1
MAX_CONCURRENT_INFERENCE=1
MAX_INSTRUCTION_CHARS=1024
ALLOW_REMOTE_MODEL_DOWNLOAD=0
UVICORN_WORKERS=1
```

The qualified production-demo profile used two CPU threads. Larger worker counts or parallel inference require independent validation.

## Qualified Qdrant production demo

The demo restores the canonical 20K snapshot; it does not rebuild or re-embed the collection.

Start with:

- `README_PRODUCTION_DEMO.md` — production-demo guide;
- `guide-production-demo.md` — concise Run-All instructions;
- `notebooks/qwen3_embedding_reranker_qdrant_kaggle_demo.ipynb` — executable notebook;
- `PRODUCTION_QUALIFICATION.md` — public qualification summary;
- `PRODUCTION_DEMO_PROVENANCE.md` — runtime/data/artifact provenance.

Verified Qdrant contract:

```text
Qdrant version: 1.18.3
Collection: knowledge_entities_qwen3_4b_text_v21
Points: 20000
Vector size: 2560
Distance: cosine
Retrieval default: K=5
```

## Development and verification

Recommended local checks:

```bash
PYTHONPATH=src pytest -q
python -m compileall -q src scripts
bash -n scripts/*.sh
```

GitHub CI validates Python 3.10 and 3.12, runs the blocking regression suite, executes the three compatibility probes separately, and verifies wheel/sdist construction.

## Security

Read `SECURITY.md` before deployment or vulnerability reporting. Security-sensitive reports must be sent privately rather than posted as public issues.

## Contributing

Contribution and verification expectations are documented in `CONTRIBUTING.md`. Changes to qualification-sensitive runtime files require explicit review and fresh evidence when behavior changes.

## Known limitations

- The qualified baseline is CPU- and Kaggle-specific; it is not a universal throughput or latency guarantee.
- Loading two 4B-class models is memory intensive; operators need adequate host RAM and appropriate swap policy.
- The package does not bundle PyTorch, model weights, GGUF files, Qdrant data, or the llama.cpp runtime.
- The launcher is single-worker by design for the qualified CPU memory model.
- Built-in bearer authentication and fixed-window rate limiting do not replace network isolation, TLS, reverse-proxy hardening, or broader abuse protection for internet-facing deployments.
- GitHub source/release publication and package-index publication are separate release channels.

## Reproducibility and provenance

Qualification results are documented in `PRODUCTION_QUALIFICATION.md`; runtime and artifact identities are documented in `PRODUCTION_DEMO_PROVENANCE.md`.

Changes that affect qualified behavior require fresh qualification evidence.

## License

MIT License. See `LICENSE`.
