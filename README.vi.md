# Qwen3-Embedding-Reranker-Qdrant-Stack

[![CI](https://github.com/dangkhoa2016/Qwen3-Embedding-Reranker-Qdrant-Stack/actions/workflows/ci.yml/badge.svg)](https://github.com/dangkhoa2016/Qwen3-Embedding-Reranker-Qdrant-Stack/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-%3E%3D3.10-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Qdrant](https://img.shields.io/badge/Qdrant-1.18.3-red)
![CPU qualified](https://img.shields.io/badge/CPU-qualified-success)

> [English](README.md) | Tiếng Việt

> **Ghi chú badge CI:** badge CI màu xanh có nghĩa các gate blocking của repository đã pass. Nó không thay đổi audit record local được bảo tồn, trong đó có ba failure lịch sử đã biết liên quan environment/Transformers compatibility.

> **Repository:** https://github.com/dangkhoa2016/Qwen3-Embedding-Reranker-Qdrant-Stack  
> **Release line:** `1.0.0` là public release identity đầu tiên. Việc publish lên package index là bước riêng với GitHub publication.

`qwen3-embedding-reranker-qdrant-stack` là một retrieval stack định hướng production, xây quanh Qwen3-Embedding-4B, Qwen3-Reranker-4B và Qdrant. Dự án cung cấp FastAPI service theo hướng CPU cùng một production-demo Qdrant 20K point có khả năng tái hiện, đã được qualification trên một fresh Kaggle CPU session. Đây là dự án embedding/retrieval/reranking, **không phải chat-LLM server**.

Public release identity đầu tiên là:

```text
Package: qwen3-embedding-reranker-qdrant-stack
Version: 1.0.0
Author: Đăng Khoa <i.am@dangkhoa.dev>
License: MIT
Python: >=3.10
Repository: https://github.com/dangkhoa2016/Qwen3-Embedding-Reranker-Qdrant-Stack
```

Các label nội bộ như `v0.2.3c` và label local tạm thời `0.2.3rc1` chỉ là qualification/provenance identifiers. Chúng chưa từng là public release.

Lưu ý compatibility: internal Python package đã qualification vẫn là `qwen_dual_server`, và protected runtime configuration vẫn chứa historical internal service/lock identifier `qwen3-dual-4b-cpu-rest-server`. Các chuỗi này được giữ lại để bảo toàn qualification compatibility và không phải public distribution identity.

## Dự án cung cấp những gì

- REST API có bearer authentication cho Qwen3 embeddings và reranking.
- `Qwen/Qwen3-Embedding-4B` qua Transformers / PyTorch với qualified CPU FP16 profile.
- Hai reranker backend:
  - Transformers cho default chung của source tree;
  - GGUF `Q4_K_M` qua hardened llama.cpp runtime cho qualified production demo.
- Kiểm tra chặt request-size, queue, concurrency, memory-headroom và startup/readiness.
- Workflow với Qdrant `1.18.3` canonical 20K bilingual snapshot cho qualified retrieval demo.
- Tài liệu reproducibility, evidence/provenance records, operator scripts và Kaggle notebook.

Các model file lớn, GGUF artifact, hardened llama runtime và Qdrant snapshot được chủ đích **không bundle** trong Python package.

## Qualified baseline tóm tắt

Trạng thái Stage-II R10 qualification đã chấp nhận:

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

Thời gian post-package Run-All đo được là `594.964s` so với qualification gate `600s`. Kết quả sát ngưỡng này là evidence cho đúng qualified Kaggle setup, **không phải cam kết performance chung** cho mọi CPU host.

## Kiến trúc

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

Default của qualified production demo là `K=5`. K=2 chỉ còn là historical fallback branch và **không được justified bởi final R10 evidence**.

## Yêu cầu

### Python và PyTorch

Yêu cầu Python `>=3.10`.

PyTorch được chủ đích **không cài bởi `requirements.txt` hoặc package metadata**. Qualified Kaggle environment đã cung cấp PyTorch; tự động thay runtime đó có thể làm mất tính tương đương với môi trường test hoặc tiêu tốn nhiều disk. Khi chạy ngoài môi trường đó, hãy tự cài PyTorch build phù hợp với CPU/host của bạn.

### External model/runtime assets

Một local deployment đầy đủ cần các asset phù hợp backend đã chọn:

1. Model files Transformers của `Qwen/Qwen3-Embedding-4B`.
2. Với Transformers reranker backend mặc định, model files Qwen3 reranker tương thích.
3. Với qualified GGUF production-demo backend, `Qwen3-Reranker-4B.Q4_K_M.gguf` cùng qualified hardened llama runtime.
4. Với Qdrant production demo, canonical `knowledge_entities_qwen3_4b_text_v21-20260827T013824Z.snapshot`.

Exact qualified identities được ghi trong `STAGE2_R10_QUALIFICATION.vi.md`/`STAGE2_R10_QUALIFICATION.md` và `PRODUCTION_DEMO_PROVENANCE.vi.md`/`PRODUCTION_DEMO_PROVENANCE.md`.

## Cài đặt

Vì dự án chưa được publish lên package index, hãy cài từ source hiện tại thay vì giả định registry package đã tồn tại:

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

Cài PyTorch runtime phù hợp riêng như mô tả ở trên.

## Khởi động nhanh

Launcher được commit bind localhost mặc định và từ chối start nếu không có authentication, trừ khi insecure no-auth mode được bật rõ ràng.

1. Copy và chỉnh environment template:

```bash
cp .env.example .env
```

2. Tối thiểu, đặt API key mạnh và model path hợp lệ cho backend đang dùng:

```text
DUAL_API_KEY=<strong-random-secret>
EMBEDDING_MODEL_PATH=/absolute/path/to/Qwen3-Embedding-4B
RERANKER_MODEL_PATH=/absolute/path/to/Qwen3-Reranker-4B
```

Với GGUF reranker backend, dùng:

```text
RERANKER_BACKEND=llama_cpp
RERANKER_GGUF_PATH=/absolute/path/to/Qwen3-Reranker-4B.Q4_K_M.gguf
LLAMA_SERVER_BIN=/absolute/path/to/qualified/llama-server-patched
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

`/ready` trả HTTP `503` cho tới khi runtime báo ready.

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

Request instruction là optional và bị giới hạn bởi:

```text
MAX_INSTRUCTION_CHARS=1024
```

Các request/concurrency limit khác được mô tả trong `.env.example` và enforce bởi application settings.

## Safe CPU defaults

Publication candidate giữ conservative profile đã qualification:

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

Production-demo profile dùng hai CPU threads trong qualification. Không được coi worker count lớn hơn hoặc parallel inference là validated chỉ vì host có nhiều core hơn.

## Qualified Qdrant production demo

Production demo restore canonical 20K snapshot; nó không rebuild hoặc re-embed collection.

Bắt đầu với:

- `README_PRODUCTION_DEMO.md` — hướng dẫn production demo tiếng Anh;
- `README_PRODUCTION_DEMO.vi.md` — hướng dẫn production demo tiếng Việt;
- `guide-production-demo.md` / `.vi.md` — hướng dẫn Run-All ngắn gọn;
- `notebooks/qwen3_embedding_reranker_qdrant_kaggle_demo.ipynb` — notebook thực thi;
- `STAGE2_R10_QUALIFICATION.md` / `.vi.md` — qualification summary đã chấp nhận;
- `PRODUCTION_DEMO_PROVENANCE.md` / `.vi.md` — provenance source/runtime/artifact.

Qualified Qdrant contract:

```text
Qdrant version: 1.18.3
Collection: knowledge_entities_qwen3_4b_text_v21
Points: 20000
Vector size: 2560
Distance: cosine
Retrieval default: K=5
```

## Authentication và deployment safety

Authentication fail-closed mặc định:

```text
DUAL_API_KEY=<required unless explicitly disabled>
ALLOW_INSECURE_NO_AUTH=0
```

`ALLOW_INSECURE_NO_AUTH=1` chỉ dành cho controlled localhost testing. Launcher đi kèm bind `127.0.0.1` mặc định và không tự cấu hình public TLS termination.

`TRUST_PROXY_HEADERS=1` nghĩa client rate-limit identity có thể dùng `X-Forwarded-For`. Chỉ giữ setting này khi request đi qua trusted reverse proxy có sanitize forwarding headers; nếu không hãy đặt `TRUST_PROXY_HEADERS=0`.

Đọc `SECURITY.vi.md`/`SECURITY.md` trước khi expose service ra ngoài trusted local environment.

## Development và verification

Targeted/static checks:

```bash
PYTHONPATH=src pytest -q
python -m compileall -q src scripts
bash -n scripts/*.sh
```

Pre-hardening publication-audit baseline được giữ lại là:

```text
111 passed, 3 failed, 1 skipped
KNOWN_BASELINE_FAILURES=3
```

Sau khi bổ sung các test về song ngữ/governance/CI hygiene, expanded local suite hiện tại ghi nhận:

```text
116 passed, 3 failed, 1 skipped
BLOCKING_CI_SUITE=116 passed, 1 skipped, 3 deselected
KNOWN_BASELINE_FAILURES=3
NEW_REGRESSION_FAILURES=0
FAILURE_SET_MATCHES_PRE_HARDENING_BASELINE=PASS
```

Ba historical engine-contract node cũ vẫn là toàn bộ failure set. **Không** được viết lại kết quả này thành “all tests pass”. Mọi failure mới hoặc failure set bị thay đổi đều phải được điều tra trước packaging.

## Bảo mật

Đọc `SECURITY.vi.md`/`SECURITY.md` trước deployment hoặc báo vulnerability. Báo cáo security-sensitive phải gửi riêng thay vì public issue.

## Đóng góp

Yêu cầu contribution và verification nằm trong `CONTRIBUTING.vi.md`/`CONTRIBUTING.md`. Đặc biệt, Stage-II qualified semantic files có requalification boundary rõ ràng: publication-hygiene changes không được âm thầm thay đổi chúng.

GitHub issue và pull-request templates nằm dưới `.github/`.

## Hạn chế đã biết

- Qualified baseline phụ thuộc CPU và Kaggle; không phải cam kết throughput/latency chung.
- Load hai model cỡ 4B tốn nhiều RAM. Runtime có memory-headroom và OOM gates nhưng operator vẫn cần host RAM và swap policy phù hợp.
- Package không bundle PyTorch, model weights, GGUF files, Qdrant data hoặc hardened llama runtime.
- Launcher chủ đích single-worker theo qualified CPU memory model.
- Built-in bearer authentication và fixed-window rate limiting không thay thế network isolation, TLS, reverse-proxy hardening hay abuse protection đầy đủ khi internet-facing.
- Source đã được publish trên branch `main` của repository. Tag `v1.0.0` và GitHub Release chưa được tạo; package-index/PyPI publication vẫn là bước riêng.

## Reproducibility và provenance

Frozen Stage-II qualified source mang internal label `v0.2.3c`; label này chưa từng được publish. Publication-hygiene work cho `1.0.0` giới hạn ở package identity, licensing, documentation, governance files, manifest/build hygiene và public-facing metadata khác, trừ khi thay đổi tương lai chủ động mở lại qualification.

Protected Stage-II semantic files được theo dõi trong `PRODUCTION_DEMO_PROVENANCE.vi.md`/`PRODUCTION_DEMO_PROVENANCE.md` và `CONTRIBUTING.vi.md`/`CONTRIBUTING.md`.

Xem thêm `PRE_PUBLISH_NOTES.vi.md`/`PRE_PUBLISH_NOTES.md` và `VERIFICATION_SUMMARY.txt` để phân biệt qualification provenance với first-public-release identity.

## Giấy phép

MIT License. Xem `LICENSE`.
