# Kế hoạch triển khai Qwen3 Hybrid FP16 Embedding + GGUF Reranker

> [English](implementation-plan.md) | Tiếng Việt

> **Dành cho agentic workers:** BẮT BUỘC dùng test-driven development. Ở thời điểm thử nghiệm GGUF ban đầu, project chưa có Git repository riêng cho nhánh thử nghiệm này, vì vậy mỗi task kết thúc bằng verification/evidence checkpoint thay vì commit.

**Mục tiêu:** Thêm opt-in `llama_cpp` reranker backend phục vụ `Qwen3-Reranker-4B.Q4_K_M.gguf` bằng local `llama-server`, trong khi giữ `Qwen3-Embedding-4B` trên Transformers FP16 path hiện có và bảo toàn public FastAPI rerank contract.

**Kiến trúc:** `DualModelRuntime` giữ embedding engine hiện tại. Khi `RERANKER_BACKEND=llama_cpp`, runtime tạo `GGUFRerankerEngine`, engine này sở hữu child process `llama-server` chỉ bind loopback và adapt kết quả llama.cpp `/v1/rerank` từ `relevance_score` sang `score` của service hiện tại. Backend mặc định vẫn là `transformers`.

**Tech Stack:** Python 3.12, FastAPI, Pydantic v2, PyTorch/Transformers cho embedding, llama.cpp `llama-server` cho GGUF reranking, pytest.

**Spec:** `/mnt/data/2026-09-01-qwen3-hybrid-fp16-embedding-gguf-reranker-design.md`

## Ràng buộc toàn cục

- Không sửa frozen release/tag `v0.1.1`.
- Thử nghiệm này không yêu cầu Git repository.
- Giữ embedding backend = Transformers FP16, dimension 2560.
- Initial reranker GGUF candidate = `Qwen3-Reranker-4B.Q4_K_M.gguf`.
- Chỉ CPU; không GPU offload.
- FastAPI giữ port 8000; internal llama-server mặc định loopback port 8081.
- Public `/v1/rerank` request/response schema không đổi.
- Không âm thầm ghép custom `instruction` vào llama.cpp query.
- Live experiment đầu tiên chỉ K=2.
- Không chạy Q5/Q8 trong first feasibility pass.
- Không bắt đầu Node/Qdrant integration.

---

## Task 1: Additive GGUF locator

**Files:**
- Create: `src/qwen_dual_server/gguf_locator.py`
- Create: `tests/test_gguf_locator.py`

**Tạo:**
- `GGUFResolutionError`
- `resolve_reranker_gguf(explicit_path, kaggle_input_root, preferred_basename) -> Path`

- [ ] Viết RED tests cho explicit path, exact auto-match, zero matches, duplicate exact matches và không silent fallback sang quant khác.
- [ ] Chạy test và yêu cầu fail vì module/function chưa tồn tại.
- [ ] Implement locator deterministic nhỏ nhất để pass.
- [ ] Chạy tests tới GREEN.

## Task 2: llama-server process wrapper

**Files:**
- Create: `src/qwen_dual_server/llama_server.py`
- Create: `tests/test_llama_server.py`

**Tạo:**
- `LlamaServerError`
- `resolve_llama_server_binary(...)`
- `build_llama_server_argv(...)`
- `LlamaServerProcess.start()`
- `LlamaServerProcess.close()`
- `LlamaServerProcess.health_url`
- `LlamaServerProcess.rerank_url`

- [ ] RED: command có model, `--embedding`, `--rerank`, `--pooling rank`, loopback host, configured port, threads=2, context=1024.
- [ ] RED: process launch dùng argv/không shell và owned child bị terminate khi close.
- [ ] Implement minimal wrapper.
- [ ] GREEN toàn bộ wrapper tests.

## Task 3: GGUF reranker HTTP adapter

**Files:**
- Create: `src/qwen_dual_server/gguf_reranker_engine.py`
- Create: `tests/test_gguf_reranker_engine.py`

**Runtime-compatible methods:**
- `load()`
- `warmup()`
- `rerank(query, documents, instruction)`
- `metadata()`
- `close()`

- [ ] RED: `relevance_score` map sang `score`, index được giữ, output sort giảm dần.
- [ ] RED: duplicate/out-of-range/missing/non-finite results fail closed.
- [ ] RED: custom instruction fail closed.
- [ ] RED: metadata báo đúng backend `llama_cpp`, format `gguf`, quantization `Q4_K_M`.
- [ ] Implement minimal adapter và functional startup probe.
- [ ] GREEN toàn bộ adapter tests.

## Task 4: Patch Settings và runtime backend selection

**Files sửa trong experiment tree hiện có:**
- `src/qwen_dual_server/config.py`
- `src/qwen_dual_server/runtime.py`
- `.env.example`

**Patch artifact:**
- Create: `tools/apply_hybrid_gguf_patch.py`

**Settings thêm:**
- `reranker_backend: Literal["transformers", "llama_cpp"] = "transformers"`
- `reranker_gguf_path: str | None = None`
- `llama_server_bin: str | None = None`
- `llama_server_host = "127.0.0.1"`
- `llama_server_port = 8081`
- `llama_server_threads = 2`
- `llama_server_context_size = 1024`
- `llama_server_startup_timeout_seconds = 180`

**Runtime behavior:**
```python
if settings.reranker_backend == "llama_cpp":
    reranker_engine = GGUFRerankerEngine(settings)
else:
    reranker_path = self._resolve_path("reranker")
    reranker_engine = RerankerEngine(settings, reranker_path)
```

`close()` phải gọi `close()` trên engine khi tồn tại trước khi release process lock.

- [ ] RED patch-fixture tests chứng minh unpatched source không chứa backend fields/factory.
- [ ] Implement fail-closed patcher với exact source anchors.
- [ ] GREEN patch-fixture tests.
- [ ] Trên Kaggle chỉ apply vào fresh disposable extraction, không sửa canonical archive.

## Task 5: Existing API regression

**Existing API evidence cho thấy `/v1/rerank` đã map arbitrary engine results chứa `index`/`score` trực tiếp vào public response. Không cần rewrite endpoint.**

- [ ] Verify existing `api.py` không đổi.
- [ ] Chạy existing `tests/test_api.py`.
- [ ] Chỉ thêm regression test nếu real source suite thiếu fake-reranker public-contract test.

## Task 6: Deterministic verification

Chạy trong patched disposable source tree:

```bash
python -m pytest -q \
  tests/test_gguf_locator.py \
  tests/test_llama_server.py \
  tests/test_gguf_reranker_engine.py \
  tests/test_config_memory.py \
  tests/test_runtime.py \
  tests/test_api.py

python -m compileall -q src
bash -n scripts/*.sh
```

Yêu cầu trước real GGUF load:

```text
pytest = PASS
compileall = PASS
bash syntax = PASS
embedding source file unchanged = PASS
api.py unchanged unless a regression-only necessity is documented = PASS
```

## Task 7: Kaggle model + llama.cpp preflight

- [ ] Locate mirror dưới `/kaggle/input` mà không giả định revision number.
- [ ] Yêu cầu exact basename `Qwen3-Reranker-4B.Q4_K_M.gguf`.
- [ ] Record size và SHA-256.
- [ ] Yêu cầu đây là read-only source; không copy model weights.
- [ ] Resolve/provision pinned `llama-server`.
- [ ] Record `llama-server --version`.
- [ ] Kiểm tra `llama-server --help` có rerank capability.
- [ ] Chạy direct llama.cpp K=2 functional request trước khi start hybrid FastAPI service.

## Task 8: Một hybrid feasibility candidate

Environment:

```text
RERANKER_BACKEND=llama_cpp
MODEL_DTYPE=float16
QUANTIZATION_MODE=none
MAX_SEQ_LENGTH=512
EMBEDDING_MICROBATCH_SIZE=1
MAX_CONCURRENT_INFERENCE=1
TORCH_NUM_THREADS=2
TORCH_NUM_INTEROP_THREADS=1
LLAMA_SERVER_THREADS=2
LLAMA_SERVER_CONTEXT_SIZE=1024
K=2
```

Đo:

```text
embedding correctness + latency
reranker finite scores
Thailand rank
reranker K2 inference_ms
FastAPI wall time
llama-server PID/RSS
FastAPI PID/RSS
cgroup memory.current
MemAvailable
memory.events max/oom/oom_kill deltas
```

So sánh reranker K2 với historical Transformers FP16 same-runtime:

```text
~60.98 seconds
```

Phân loại:

```text
>=60s       no practical speed benefit
30-60s      improvement but weak
20-30s      interesting
10-20s      strong candidate
<10s        excellent CPU-demo candidate
```

Dừng sau khi package đúng một Q4_K_M feasibility result này.
