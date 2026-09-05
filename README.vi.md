# Qwen3-Embedding-Reranker-Qdrant-Stack
> 🌐 Language / Ngôn ngữ: [English](README.md) | **Tiếng Việt**

[![CI](https://github.com/dangkhoa2016/Qwen3-Embedding-Reranker-Qdrant-Stack/actions/workflows/ci.yml/badge.svg)](https://github.com/dangkhoa2016/Qwen3-Embedding-Reranker-Qdrant-Stack/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-%3E%3D3.10-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Qdrant](https://img.shields.io/badge/Qdrant-1.18.3-red)
![CPU qualified](https://img.shields.io/badge/CPU-qualified-success)

`qwen3-embedding-reranker-qdrant-stack` là retrieval stack định hướng production, xây quanh Qwen3-Embedding-4B, Qwen3-Reranker-4B và Qdrant. Dự án cung cấp FastAPI service theo hướng CPU cùng production demo Qdrant song ngữ 20K point có khả năng tái hiện. Đây là dự án embedding/retrieval/reranking, không phải chat-LLM server.

## Dự án cung cấp những gì

- REST API có bearer authentication cho Qwen3 embeddings và reranking.
- `Qwen/Qwen3-Embedding-4B` qua Transformers / PyTorch với CPU FP16 profile đã được kiểm chứng.
- Hai reranker backend:
  - Transformers cho source-tree mặc định chung;
  - GGUF `Q4_K_M` qua llama.cpp runtime đã được harden cho production demo.
- Kiểm soát request-size, queue, concurrency, memory-headroom, startup và readiness.
- Workflow Qdrant `1.18.3` với canonical snapshot song ngữ 20K point.
- Tài liệu reproducibility, operator scripts, provenance records và Kaggle notebook thực thi được.

Các model file lớn, GGUF artifact, llama.cpp runtime và Qdrant snapshot được chủ đích **không bundle** trong Python package.

## Kiểm chứng production

Production-demo profile của `1.0.0` đã được kiểm chứng trên một fresh Kaggle CPU session:

```text
Production qualification: PASS
Semantic validation: 3/3 PASS
cgroup OOM events: 0
cgroup OOM-kill events: 0
Run All: 594.964s
Qualification threshold: 600s
Retrieval default: K=5
```

Kết quả thời gian chỉ áp dụng cho môi trường đã được kiểm chứng và **không** phải cam kết hiệu năng chung cho mọi CPU.

## Kiến trúc

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

Độ sâu truy hồi của production demo là `K=5`.

## Yêu cầu

### Python và PyTorch

Yêu cầu Python `>=3.10`.

PyTorch được chủ đích **không cài bởi `requirements.txt` hoặc package metadata**. Khi chạy ngoài môi trường đã có sẵn PyTorch, hãy cài bản PyTorch phù hợp với host.

### External model/runtime assets

Một deployment đầy đủ cần các asset theo backend đã chọn:

1. Model files Transformers của `Qwen/Qwen3-Embedding-4B`.
2. Model files Qwen3 reranker Transformers tương thích cho Transformers reranker backend.
3. `Qwen3-Reranker-4B.Q4_K_M.gguf` cùng llama.cpp runtime đã được kiểm chứng cho GGUF production-demo backend.
4. `knowledge_entities_qwen3_4b_text_v21-20260827T013824Z.snapshot` cho Qdrant production demo.

Các runtime/data identity đã được xác minh được ghi trong `PRODUCTION_QUALIFICATION.vi.md` và `PRODUCTION_DEMO_PROVENANCE.vi.md`.

## Cài đặt

Dự án hiện chưa được publish lên package index, vì vậy hãy cài từ source:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install .
```

Development/test dependencies:

```bash
python -m pip install -r requirements-dev.txt
```

Cài PyTorch runtime phù hợp riêng.

## Khởi động nhanh

Launcher được commit bind localhost mặc định và từ chối start nếu không có authentication, trừ khi insecure no-auth mode được bật rõ ràng.

1. Copy environment template:

```bash
cp .env.example .env
```

2. Đặt API key mạnh và model path hợp lệ:

```text
DUAL_API_KEY=<strong-random-secret>
EMBEDDING_MODEL_PATH=/absolute/path/to/Qwen3-Embedding-4B
RERANKER_MODEL_PATH=/absolute/path/to/Qwen3-Reranker-4B
```

Với GGUF reranker backend:

```text
RERANKER_BACKEND=llama_cpp
RERANKER_GGUF_PATH=/absolute/path/to/Qwen3-Reranker-4B.Q4_K_M.gguf
LLAMA_SERVER_BIN=/absolute/path/to/qualified/llama-server
```

3. Export environment và start service:

```bash
set -a
source .env
set +a
bash scripts/start-server.sh
```

4. Kiểm tra liveness/readiness:

```bash
curl -s http://127.0.0.1:8000/health
curl -s http://127.0.0.1:8000/ready
```

`/ready` trả HTTP `503` cho tới khi runtime ready.

## Tổng quan API

Operational endpoints không cần auth:

```text
GET /health
GET /ready
```

Endpoints yêu cầu bearer auth:

```text
GET  /v1/models
GET  /v1/stats
POST /v1/embeddings
POST /v1/rerank
```

Ví dụ embedding request:

```bash
curl -s http://127.0.0.1:8000/v1/embeddings \
  -H "Authorization: Bearer $DUAL_API_KEY" \
  -H 'Content-Type: application/json' \
  -d '{"input":"Which Southeast Asian country uses the baht?","input_type":"query"}'
```

Ví dụ rerank request:

```bash
curl -s http://127.0.0.1:8000/v1/rerank \
  -H "Authorization: Bearer $DUAL_API_KEY" \
  -H 'Content-Type: application/json' \
  -d '{"query":"capital of Japan","documents":["Tokyo","Osaka"],"return_documents":true}'
```

Optional request instructions bị giới hạn bởi:

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

Production-demo profile đã kiểm chứng dùng hai CPU threads. Worker count lớn hơn hoặc parallel inference cần được kiểm chứng độc lập.

## Qualified Qdrant production demo

Demo restore canonical 20K snapshot; không rebuild hoặc re-embed collection.

Bắt đầu với:

- `README_PRODUCTION_DEMO.vi.md` — hướng dẫn production demo;
- `guide-production-demo.vi.md` — hướng dẫn Run-All ngắn gọn;
- `notebooks/qwen3_embedding_reranker_qdrant_kaggle_demo.ipynb` — notebook thực thi;
- `PRODUCTION_QUALIFICATION.vi.md` — qualification summary công khai;
- `PRODUCTION_DEMO_PROVENANCE.vi.md` — provenance runtime/data/artifact.

Qdrant contract đã xác minh:

```text
Qdrant version: 1.18.3
Collection: knowledge_entities_qwen3_4b_text_v21
Points: 20000
Vector size: 2560
Distance: cosine
Retrieval default: K=5
```

## Development và verification

Các check local nên chạy:

```bash
PYTHONPATH=src pytest -q
python -m compileall -q src scripts
bash -n scripts/*.sh
```

GitHub CI kiểm tra Python 3.10 và 3.12, chạy blocking regression suite, chạy riêng ba compatibility probe và xác minh wheel/sdist.

## Bảo mật

Đọc `SECURITY.vi.md` trước deployment hoặc báo vulnerability. Báo cáo security-sensitive phải gửi riêng thay vì public issue.

## Đóng góp

Yêu cầu contribution và verification nằm trong `CONTRIBUTING.vi.md`. Thay đổi vào runtime files nhạy cảm với qualification cần review rõ ràng và fresh evidence khi behavior thay đổi.

## Hạn chế đã biết

- Baseline đã kiểm chứng phụ thuộc CPU và Kaggle; không phải cam kết throughput/latency chung.
- Load hai model cỡ 4B tốn nhiều RAM; operator cần đủ host RAM và swap policy phù hợp.
- Package không bundle PyTorch, model weights, GGUF files, Qdrant data hoặc llama.cpp runtime.
- Launcher chủ đích single-worker theo CPU memory model đã kiểm chứng.
- Built-in bearer authentication và fixed-window rate limiting không thay thế network isolation, TLS, reverse-proxy hardening hay abuse protection đầy đủ khi internet-facing.
- GitHub source/release publication và package-index publication là các kênh riêng.

## Khả năng tái hiện và nguồn gốc

Kết quả qualification nằm trong `PRODUCTION_QUALIFICATION.vi.md`; runtime và artifact identities nằm trong `PRODUCTION_DEMO_PROVENANCE.vi.md`.

Các thay đổi ảnh hưởng behavior đã được kiểm chứng cần fresh qualification evidence.

## Giấy phép

MIT License. Xem `LICENSE`.
