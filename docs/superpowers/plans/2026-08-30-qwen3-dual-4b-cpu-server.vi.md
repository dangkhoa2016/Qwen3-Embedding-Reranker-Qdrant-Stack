# Kế hoạch triển khai Qwen3 Dual 4B CPU REST Server
> 🌐 Language / Ngôn ngữ: [English](2026-08-30-qwen3-dual-4b-cpu-server.md) | **Tiếng Việt**

> **Dành cho agentic workers:** BẮT BUỘC dùng sub-skill `superpowers:subagent-driven-development` (khuyến nghị) hoặc `superpowers:executing-plans` để triển khai kế hoạch theo từng task. Các bước dùng checkbox (`- [ ]`) để theo dõi.

**Mục tiêu:** Xây dựng và verify một REST inference server single-process, CPU-only cho Qwen3-Embedding-4B và Qwen3-Reranker-4B với memory controls an toàn cho Kaggle và evidence tooling.

**Kiến trúc:** Một FastAPI process sở hữu hai model singleton được tạo lazy. Model load theo tuần tự và bị chặn bởi memory threshold; mọi heavy inference đi qua một global queue/semaphore. Model path được resolve từ read-only Kaggle inputs và public inference yêu cầu Bearer authentication.

**Tech Stack:** Python 3.10+, PyTorch CPU, Transformers 4.51+, FastAPI, Uvicorn, Pydantic v2, psutil, pytest.

**Spec:** `docs/superpowers/specs/2026-08-30-qwen3-dual-4b-cpu-server-design.vi.md`

## Ràng buộc toàn cục

- Chỉ CPU.
- Một process và một Uvicorn worker.
- Global heavy inference concurrency đúng bằng 1.
- Model dtype mặc định `float16`.
- Sequence length mặc định 512.
- Microbatch mặc định 1 cho cả hai model.
- `low_cpu_mem_usage=True`; không dùng `device_map="auto"`.
- `use_cache=False`.
- Model weights phải ở `/kaggle/input` và không bao giờ copy.
- Remote model download tắt trừ khi bật rõ ràng.
- Embedding output là normalized Float32[2560].
- Từ chối load model thứ hai nếu memory headroom thấp hơn gate cấu hình.
- Bất kỳ cgroup OOM/OOM-kill delta nào đều fail acceptance.

---

### Task 1: Pure semantic helpers và model-path validation

**Files:**
- Test: `tests/test_formatting.py`
- Test: `tests/test_pooling.py`
- Test: `tests/test_model_locator.py`
- Create: `src/qwen_dual_server/formatting.py`
- Create: `src/qwen_dual_server/tensor_ops.py`
- Create: `src/qwen_dual_server/model_locator.py`

**Interfaces:**
- Tạo `format_embedding_text`, `format_reranker_pair`, `last_token_pool`, `normalize_embedding_fp32`, `resolve_model_path`.

- [ ] Viết test chứng minh canonical query formatting, raw documents, reranker prompt format, left/right-padding last-token pooling, FP32 normalization, validated local model resolution và ambiguity failure.
- [ ] Chạy test và xác nhận RED vì production modules chưa tồn tại.
- [ ] Implement minimal pure helpers.
- [ ] Chạy test và xác nhận GREEN.

### Task 2: Settings, memory inspection và process singleton guard

**Files:**
- Test: `tests/test_config_memory.py`
- Create: `src/qwen_dual_server/config.py`
- Create: `src/qwen_dual_server/memory.py`
- Create: `src/qwen_dual_server/process_lock.py`

**Interfaces:**
- Tạo `Settings`, `MemorySnapshot`, `capture_memory_snapshot`, `ProcessSingletonLock`.

- [ ] Viết RED tests cho safe defaults, invalid dtype, cgroup event parsing, GiB conversion và lock exclusivity.
- [ ] Implement settings và memory/lock helpers.
- [ ] Chạy GREEN tests.

### Task 3: Embedding và reranker engines

**Files:**
- Test: `tests/test_engine_contracts.py`
- Create: `src/qwen_dual_server/embedding_engine.py`
- Create: `src/qwen_dual_server/reranker_engine.py`

**Interfaces:**
- Tạo `EmbeddingEngine.load/embed/warmup/metadata` và `RerankerEngine.load/rerank/warmup/metadata`.

- [ ] Viết RED tests dùng fake tokenizers/models để chứng minh loader kwargs, CPU dtype checks, FP32 public embedding normalization, rerank ordering và no-cache configuration.
- [ ] Implement lazy Transformers imports để unit tests không cần model weights.
- [ ] Chạy GREEN tests.

### Task 4: Dual runtime và memory gate

**Files:**
- Test: `tests/test_runtime.py`
- Create: `src/qwen_dual_server/runtime.py`

**Interfaces:**
- Tạo `DualModelRuntime.load_all`, `.embed`, `.rerank`, `.status`, `.stats`.

- [ ] Viết RED tests chứng minh Embedding load trước, warm-up xảy ra trước Reranker, low-memory headroom chặn load model thứ hai và readiness false sau bất kỳ load failure nào.
- [ ] Implement sequential loading, counters và memory snapshots.
- [ ] Chạy GREEN tests.

### Task 5: Authenticated FastAPI surface và inference queue

**Files:**
- Test: `tests/test_api.py`
- Create: `src/qwen_dual_server/gate.py`
- Create: `src/qwen_dual_server/schemas.py`
- Create: `src/qwen_dual_server/api.py`
- Create: `src/qwen_dual_server/main.py`

**Interfaces:**
- Tạo `create_app(settings, runtime)` và ASGI object `app`.

- [ ] Viết RED API tests cho health/readiness, Bearer auth, embeddings, rerank, request limits, queue-full response và model metadata.
- [ ] Implement inference gate và API.
- [ ] Chạy GREEN API tests.

### Task 6: Kaggle operator scripts và evidence collection

**Files:**
- Create: `scripts/preflight.py`
- Create: `scripts/start-server.sh`
- Create: `scripts/start-and-monitor.sh`
- Create: `scripts/smoke-http.py`
- Create: `scripts/collect-evidence.sh`
- Create: `.env.example`
- Create: `requirements.txt`
- Create: `requirements-dev.txt`
- Create: `pyproject.toml`
- Create: `README.md`

- [ ] Thêm source-level và shell syntax tests/checks.
- [ ] Đảm bảo scripts không bao giờ write vào `/kaggle/input`.
- [ ] Đảm bảo server script dùng `--workers 1` và bind localhost mặc định.
- [ ] Thêm evidence packaging và checksum generation.

### Task 7: Final verification và release archive

- [ ] Chạy `python -m compileall -q src scripts`.
- [ ] Chạy full `pytest -q` và yêu cầu zero failures theo baseline của kế hoạch lịch sử tại thời điểm đó.
- [ ] Chạy `bash -n` trên mọi shell script.
- [ ] Chạy offline preflight với fake model roots.
- [ ] Initialize Git, commit verified source và tạo ZIP có Git history.
- [ ] Chạy `unzip -t` trên ZIP.
- [ ] Tạo `.sha256` và mechanically verify.
