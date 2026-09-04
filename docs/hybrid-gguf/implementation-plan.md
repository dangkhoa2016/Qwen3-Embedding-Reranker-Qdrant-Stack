# Qwen3 Hybrid FP16 Embedding + GGUF Reranker Implementation Plan
> 🌐 Language / Ngôn ngữ: **English** | [Tiếng Việt](implementation-plan.vi.md)

> **For agentic workers:** REQUIRED SUB-SKILL: use test-driven development. This project currently has no Git repository for the GGUF experiment, so each task ends with a verification/evidence checkpoint rather than a commit.

**Goal:** Add an opt-in `llama_cpp` reranker backend that serves `Qwen3-Reranker-4B.Q4_K_M.gguf` with local `llama-server`, while keeping `Qwen3-Embedding-4B` on the existing Transformers FP16 path and preserving the public FastAPI rerank contract.

**Architecture:** `DualModelRuntime` keeps the existing embedding engine. When `RERANKER_BACKEND=llama_cpp`, it constructs `GGUFRerankerEngine`, which owns a loopback-only `llama-server` child process and adapts llama.cpp `/v1/rerank` results from `relevance_score` to the service's existing `score`. The default backend stays `transformers`.

**Tech Stack:** Python 3.12, FastAPI, Pydantic v2, PyTorch/Transformers for embedding, llama.cpp `llama-server` for GGUF reranking, pytest.

**Spec:** `/mnt/data/2026-09-01-qwen3-hybrid-fp16-embedding-gguf-reranker-design.md`

## Global Constraints

- Do not modify frozen release/tag `v0.1.1`.
- No Git repository is required for this experiment.
- Keep embedding backend = Transformers FP16, dimension 2560.
- Initial reranker GGUF candidate = `Qwen3-Reranker-4B.Q4_K_M.gguf`.
- CPU-only; no GPU offload.
- FastAPI stays on port 8000; internal llama-server defaults to loopback port 8081.
- Public `/v1/rerank` request/response schema must remain unchanged.
- Do not silently rewrite custom `instruction` into the llama.cpp query.
- First live experiment is K=2 only.
- Do not run Q5/Q8 in the first feasibility pass.
- Do not start Node/Qdrant integration.

---

## Task 1: Additive GGUF locator

**Files:**
- Create: `src/qwen_dual_server/gguf_locator.py`
- Create: `tests/test_gguf_locator.py`

**Produces:**
- `GGUFResolutionError`
- `resolve_reranker_gguf(explicit_path, kaggle_input_root, preferred_basename) -> Path`

- [ ] Write RED tests for explicit path, exact auto-match, zero matches, duplicate exact matches, and no silent fallback to another quant.
- [ ] Run the tests and require failure because the module/function does not exist.
- [ ] Implement the smallest deterministic locator that passes.
- [ ] Run tests to GREEN.

## Task 2: llama-server process wrapper

**Files:**
- Create: `src/qwen_dual_server/llama_server.py`
- Create: `tests/test_llama_server.py`

**Produces:**
- `LlamaServerError`
- `resolve_llama_server_binary(...)`
- `build_llama_server_argv(...)`
- `LlamaServerProcess.start()`
- `LlamaServerProcess.close()`
- `LlamaServerProcess.health_url`
- `LlamaServerProcess.rerank_url`

- [ ] RED: command includes model, `--embedding`, `--rerank`, `--pooling rank`, loopback host, configured port, threads=2, context=1024.
- [ ] RED: process launch uses argv/no shell and owned child is terminated on close.
- [ ] Implement minimal wrapper.
- [ ] GREEN all wrapper tests.

## Task 3: GGUF reranker HTTP adapter

**Files:**
- Create: `src/qwen_dual_server/gguf_reranker_engine.py`
- Create: `tests/test_gguf_reranker_engine.py`

**Produces runtime-compatible methods:**
- `load()`
- `warmup()`
- `rerank(query, documents, instruction)`
- `metadata()`
- `close()`

- [ ] RED: `relevance_score` maps to `score`, indices preserved, descending output.
- [ ] RED: duplicate/out-of-range/missing/non-finite results fail closed.
- [ ] RED: custom instruction fails closed.
- [ ] RED: metadata truthfully reports backend `llama_cpp`, format `gguf`, quantization `Q4_K_M`.
- [ ] Implement minimal adapter and functional startup probe.
- [ ] GREEN all adapter tests.

## Task 4: Patch Settings and runtime backend selection

**Files modified in the existing experiment tree:**
- `src/qwen_dual_server/config.py`
- `src/qwen_dual_server/runtime.py`
- `.env.example`

**Patch artifact:**
- Create: `tools/apply_hybrid_gguf_patch.py`

**Settings added:**
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

`close()` must call `close()` on engines when present before releasing the process lock.

- [ ] RED patch-fixture tests prove unpatched source does not contain backend fields/factory.
- [ ] Implement fail-closed patcher with exact source anchors.
- [ ] GREEN patch-fixture tests.
- [ ] On Kaggle, apply only to a fresh disposable extraction, never to canonical archive.

## Task 5: Existing API regression

**Existing API evidence says `/v1/rerank` already maps arbitrary engine results containing `index`/`score` directly to the public response. No endpoint rewrite is required.**

- [ ] Verify existing `api.py` remains unchanged.
- [ ] Run existing `tests/test_api.py`.
- [ ] Add only a regression test if the real source suite lacks a fake-reranker public-contract test.

## Task 6: Deterministic verification

Run in the patched disposable source tree:

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

Required before any real GGUF load:

```text
pytest = PASS
compileall = PASS
bash syntax = PASS
embedding source file unchanged = PASS
api.py unchanged unless a regression-only necessity is documented = PASS
```

## Task 7: Kaggle model + llama.cpp preflight

- [ ] Locate mirror under `/kaggle/input` without assuming revision number.
- [ ] Require exact basename `Qwen3-Reranker-4B.Q4_K_M.gguf`.
- [ ] Record size and SHA-256.
- [ ] Require it is read-only source; do not copy model weights.
- [ ] Resolve/provision a pinned `llama-server`.
- [ ] Record `llama-server --version`.
- [ ] Check `llama-server --help` contains rerank capability.
- [ ] Run a direct llama.cpp K=2 functional request before starting the hybrid FastAPI service.

## Task 8: One hybrid feasibility candidate

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

Measure:

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

Compare reranker K2 against historical Transformers FP16 same-runtime:

```text
~60.98 seconds
```

Classification:

```text
>=60s       no practical speed benefit
30-60s      improvement but weak
20-30s      interesting
10-20s      strong candidate
<10s        excellent CPU-demo candidate
```

Stop after packaging this one Q4_K_M feasibility result.
