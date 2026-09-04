# Qwen3 Dual 4B CPU REST Server Implementation Plan

> English | [Tiếng Việt](2026-08-30-qwen3-dual-4b-cpu-server.vi.md)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and verify a single-process CPU-only REST inference server for Qwen3-Embedding-4B and Qwen3-Reranker-4B with Kaggle-safe memory controls and evidence tooling.

**Architecture:** One FastAPI process owns two lazily constructed model singletons. Model load is sequential and guarded by a memory threshold; all heavy inference uses one global queue/semaphore. Model paths resolve from read-only Kaggle inputs and public inference requires Bearer authentication.

**Tech Stack:** Python 3.10+, PyTorch CPU, Transformers 4.51+, FastAPI, Uvicorn, Pydantic v2, psutil, pytest.

**Spec:** `docs/superpowers/specs/2026-08-30-qwen3-dual-4b-cpu-server-design.md`

## Global Constraints

- CPU only.
- One process and one Uvicorn worker.
- Global heavy inference concurrency exactly 1.
- Default model dtype `float16`.
- Default sequence length 512.
- Default microbatch size 1 for both models.
- `low_cpu_mem_usage=True`; no `device_map="auto"`.
- `use_cache=False`.
- Model weights must stay in `/kaggle/input` and are never copied.
- Remote model download disabled unless explicitly opted in.
- Embedding output is normalized Float32[2560].
- Second-model load is rejected if memory headroom is below the configured gate.
- Any cgroup OOM/OOM-kill delta fails acceptance.

---

### Task 1: Pure semantic helpers and model-path validation

**Files:**
- Test: `tests/test_formatting.py`
- Test: `tests/test_pooling.py`
- Test: `tests/test_model_locator.py`
- Create: `src/qwen_dual_server/formatting.py`
- Create: `src/qwen_dual_server/tensor_ops.py`
- Create: `src/qwen_dual_server/model_locator.py`

**Interfaces:**
- Produces `format_embedding_text`, `format_reranker_pair`, `last_token_pool`, `normalize_embedding_fp32`, `resolve_model_path`.

- [ ] Write tests proving canonical query formatting, raw documents, reranker prompt format, left/right-padding last-token pooling, FP32 normalization, validated local model resolution, and ambiguity failure.
- [ ] Run those tests and confirm RED because production modules do not exist.
- [ ] Implement the minimal pure helpers.
- [ ] Run those tests and confirm GREEN.

### Task 2: Settings, memory inspection, and process singleton guard

**Files:**
- Test: `tests/test_config_memory.py`
- Create: `src/qwen_dual_server/config.py`
- Create: `src/qwen_dual_server/memory.py`
- Create: `src/qwen_dual_server/process_lock.py`

**Interfaces:**
- Produces `Settings`, `MemorySnapshot`, `capture_memory_snapshot`, `ProcessSingletonLock`.

- [ ] Write RED tests for safe defaults, invalid dtype, cgroup event parsing, GiB conversion, and lock exclusivity.
- [ ] Implement settings and memory/lock helpers.
- [ ] Run GREEN tests.

### Task 3: Embedding and reranker engines

**Files:**
- Test: `tests/test_engine_contracts.py`
- Create: `src/qwen_dual_server/embedding_engine.py`
- Create: `src/qwen_dual_server/reranker_engine.py`

**Interfaces:**
- Produces `EmbeddingEngine.load/embed/warmup/metadata` and `RerankerEngine.load/rerank/warmup/metadata`.

- [ ] Write RED tests using fake tokenizers/models proving loader kwargs, CPU dtype checks, FP32 public embedding normalization, rerank ordering, and no-cache configuration.
- [ ] Implement lazy Transformers imports so unit tests do not require model weights.
- [ ] Run GREEN tests.

### Task 4: Dual runtime and memory gate

**Files:**
- Test: `tests/test_runtime.py`
- Create: `src/qwen_dual_server/runtime.py`

**Interfaces:**
- Produces `DualModelRuntime.load_all`, `.embed`, `.rerank`, `.status`, `.stats`.

- [ ] Write RED tests proving Embedding loads first, warm-up occurs before Reranker, low-memory headroom blocks second-model load, and readiness is false after any load failure.
- [ ] Implement sequential loading, counters, and memory snapshots.
- [ ] Run GREEN tests.

### Task 5: Authenticated FastAPI surface and inference queue

**Files:**
- Test: `tests/test_api.py`
- Create: `src/qwen_dual_server/gate.py`
- Create: `src/qwen_dual_server/schemas.py`
- Create: `src/qwen_dual_server/api.py`
- Create: `src/qwen_dual_server/main.py`

**Interfaces:**
- Produces `create_app(settings, runtime)` and ASGI object `app`.

- [ ] Write RED API tests for health/readiness, Bearer auth, embeddings, rerank, request limits, queue-full response, and model metadata.
- [ ] Implement the inference gate and API.
- [ ] Run GREEN API tests.

### Task 6: Kaggle operator scripts and evidence collection

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

- [ ] Add source-level and shell syntax tests/checks.
- [ ] Ensure scripts never write to `/kaggle/input`.
- [ ] Ensure server script uses `--workers 1` and binds localhost by default.
- [ ] Add evidence packaging and checksum generation.

### Task 7: Final verification and release archive

- [ ] Run `python -m compileall -q src scripts`.
- [ ] Run full `pytest -q` and require zero failures.
- [ ] Run `bash -n` on all shell scripts.
- [ ] Run offline preflight against fake model roots.
- [ ] Initialize Git, commit the verified source, and create a ZIP with Git history.
- [ ] Run `unzip -t` on the ZIP.
- [ ] Generate `.sha256` and mechanically verify it.
