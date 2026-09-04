# Qwen3 Dual 4B CPU REST Server

> **Status:** local pre-publication candidate for the first public release, `1.0.0`.  
> This project is still unpublished: there is no remote repository, tag, release, or package-index publication yet.

`qwen3-dual-4b-cpu-rest-server` is a CPU-oriented FastAPI service for Qwen3 embeddings and reranking, plus a reproducible Qdrant production-demo path that was qualified on a fresh Kaggle CPU session.

## What this project provides

- A bearer-authenticated REST API for Qwen3 embeddings and reranking.
- `Qwen/Qwen3-Embedding-4B` through Transformers / PyTorch with the qualified CPU FP16 profile.
- Two reranker backends:
  - Transformers for the generic source-tree default;
  - GGUF `Q4_K_M` through a hardened llama.cpp runtime for the qualified production demo.
- Strict request-size, queue, concurrency, memory-headroom, and startup/readiness checks.
- A canonical Qdrant `1.18.3` 20K bilingual snapshot workflow for the qualified hybrid retrieval demo.
- Reproducibility documentation, evidence/provenance records, operator scripts, and a Kaggle notebook.

The large model files, GGUF artifact, hardened llama runtime, and Qdrant snapshot are intentionally **not bundled** with the Python package.

## Qualified baseline at a glance

The accepted Stage-II R10 qualification state is:

```text
STAGE2_R10_QUALIFICATION=PASS
STAGE2_R3_TO_R10=CLOSED
SEMANTIC_3_OF_3=True
OOM_GATE=PASS
RUN_ALL_WITHIN_600S=True
K5_DEFAULT=ACCEPT
K2_FALLBACK=NOT_JUSTIFIED
FINAL_RELEASE_DEFAULT=K5_READY
```

The measured post-package Run-All time was `594.964s` against a `600s` qualification gate. That narrow result is evidence for the qualified Kaggle setup, **not a general performance guarantee** for arbitrary CPU hosts.

## Architecture

```text
REST request
  -> FastAPI authentication / limits / single-inference gate
  -> Qwen3-Embedding-4B
  -> normalized Float32[2560] embedding

Qualified production-demo path:
query
  -> Qwen3-Embedding-4B (Transformers / PyTorch CPU FP16)
  -> Qdrant 1.18.3 / canonical 20K bilingual snapshot
  -> Top-5 candidates
  -> Qwen3-Reranker-4B Q4_K_M (GGUF / hardened llama.cpp)
  -> final ranked results
```

The qualified production-demo default is `K=5`. K=2 remains an historical fallback branch and is **not justified by the final R10 evidence**.

## Requirements

### Python and PyTorch

Python `>=3.10` is required.

PyTorch is deliberately **not installed by `requirements.txt` or package metadata**. The qualified Kaggle environment already supplies PyTorch, and automatically replacing that runtime can invalidate the tested environment or consume substantial disk space. Install a PyTorch build appropriate for your CPU/host before running this service outside that environment.

### External model/runtime assets

A complete local deployment needs the assets required by the selected backend:

1. `Qwen/Qwen3-Embedding-4B` Transformers model files.
2. For the default Transformers reranker backend, compatible Qwen3 reranker Transformers model files.
3. For the qualified GGUF production-demo backend, `Qwen3-Reranker-4B.Q4_K_M.gguf` plus the qualified hardened llama runtime.
4. For the Qdrant production demo, the canonical `knowledge_entities_qwen3_4b_text_v21-20260827T013824Z.snapshot`.

Exact qualified identities are recorded in `STAGE2_R10_QUALIFICATION.md` and `PRODUCTION_DEMO_PROVENANCE.md`.

## Installation

Because this project has not yet been published to a package index, install the local source candidate rather than assuming a registry package exists:

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

Install the correct PyTorch runtime separately as described above.

## Quick start

The checked-in launcher binds to localhost by default and refuses to start without authentication unless insecure no-auth mode is explicitly enabled.

1. Copy and edit the environment template:

```bash
cp .env.example .env
```

2. At minimum, set a strong API key and valid model paths for the backend you are using:

```text
DUAL_API_KEY=<strong-random-secret>
EMBEDDING_MODEL_PATH=/absolute/path/to/Qwen3-Embedding-4B
RERANKER_MODEL_PATH=/absolute/path/to/Qwen3-Reranker-4B
```

For the GGUF reranker backend, configure instead:

```text
RERANKER_BACKEND=llama_cpp
RERANKER_GGUF_PATH=/absolute/path/to/Qwen3-Reranker-4B.Q4_K_M.gguf
LLAMA_SERVER_BIN=/absolute/path/to/qualified/llama-server-patched
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

`/ready` returns HTTP `503` until the runtime reports ready.

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

Request instructions are optional and bounded by:

```text
MAX_INSTRUCTION_CHARS=1024
```

Other request/concurrency limits are documented in `.env.example` and enforced by the application settings.

## Safe CPU defaults

The publication candidate preserves the qualified conservative profile:

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

The production-demo profile used two CPU threads during qualification. Do not treat larger worker counts or parallel inference as validated simply because the host has more cores.

## Qualified Qdrant production demo

The production demo restores the canonical 20K snapshot; it does not rebuild or re-embed the collection.

Start with:

- `README_PRODUCTION_DEMO.md` — English production-demo guide;
- `README_PRODUCTION_DEMO.vi.md` — Vietnamese production-demo guide;
- `guide-production-demo.md` — concise Run-All instructions;
- `notebooks/qwen3_embedding_reranker_qdrant_kaggle_demo.ipynb` — executable notebook;
- `STAGE2_R10_QUALIFICATION.md` — accepted qualification summary;
- `PRODUCTION_DEMO_PROVENANCE.md` — source/runtime/artifact provenance.

Qualified Qdrant contract:

```text
Qdrant version: 1.18.3
Collection: knowledge_entities_qwen3_4b_text_v21
Points: 20000
Vector size: 2560
Distance: cosine
Retrieval default: K=5
```

## Authentication and deployment safety

Authentication is fail-closed by default:

```text
DUAL_API_KEY=<required unless explicitly disabled>
ALLOW_INSECURE_NO_AUTH=0
```

`ALLOW_INSECURE_NO_AUTH=1` is intended only for controlled localhost testing. The supplied launcher binds to `127.0.0.1` by default and does not configure public TLS termination.

`TRUST_PROXY_HEADERS=1` means client rate-limit identity may use `X-Forwarded-For`. Keep that setting only when requests pass through a trusted reverse proxy that sanitizes forwarding headers; otherwise set `TRUST_PROXY_HEADERS=0`.

See `SECURITY.md` before exposing the service outside a trusted local environment.

## Development and verification

Targeted/static checks:

```bash
PYTHONPATH=src pytest -q
python -m compileall -q src scripts
bash -n scripts/*.sh
```

The verified pre-publication audit baseline is:

```text
110 passed, 3 failed, 1 skipped
KNOWN_BASELINE_FAILURES=3
NEW_REGRESSION_FAILURES=0
FULL_REGRESSION_BASELINE_MATCH=PASS
```

Those three failures are known historical environment/Transformers-compatibility failures in the qualification audit environment. Do **not** rewrite that record as “all tests pass.” Any new failure or a changed failure set must be investigated before packaging.

## Security

Please read `SECURITY.md` before deployment or vulnerability reporting. Security-sensitive reports should be sent privately rather than posted as public issues.

## Contributing

Contribution and verification expectations are in `CONTRIBUTING.md`. In particular, the Stage-II qualified semantic files have an explicit requalification boundary: publication-hygiene changes must not silently change them.

Local `.github` issue and pull-request templates are prepared for a future repository, but their presence here does **not** imply that a GitHub repository already exists.

## Known limitations

- The qualified baseline is CPU- and Kaggle-specific; it is not a universal throughput or latency guarantee.
- Loading two 4B-class models is memory intensive. The runtime uses memory-headroom and OOM gates, but operators still need adequate host RAM and swap policy.
- The package does not bundle PyTorch, model weights, GGUF files, Qdrant data, or the hardened llama runtime.
- The launcher is single-worker by design for the qualified CPU memory model.
- Built-in bearer authentication and fixed-window rate limiting are not substitutes for network isolation, TLS, reverse-proxy hardening, or broader abuse protection when internet-facing.
- The current source remains a local pre-publication candidate. Repository URLs, tags, releases, and package-index links must not be invented before those resources actually exist.

## Reproducibility and provenance

Qualification evidence and provenance are documented in `PRODUCTION_DEMO_PROVENANCE.md`, `STAGE2_R10_QUALIFICATION.md`, `PRE_PUBLISH_NOTES.md`, and `VERIFICATION_SUMMARY.txt`.

Changes that affect qualified behavior require fresh qualification evidence; contributor guidance is documented in `CONTRIBUTING.md`.

## License

MIT License. See `LICENSE`.
