# Thiết kế Qwen3 Hybrid CPU Runtime

> [English](design.md) | Tiếng Việt

## Transformers FP16 Embedding + llama.cpp GGUF Reranker

**Ngày:** 2026-09-01  
**Trạng thái:** Design sẵn sàng cho implementation review  
**Phạm vi:** Kaggle CPU/RAM-only experimental branch; không yêu cầu Git repository

## 1. Mục tiêu

Giữ nguyên path `Qwen3-Embedding-4B` Transformers FP16 đã được qualification và chỉ thay path `Qwen3-Reranker-4B` Transformers bằng local `llama-server` process phục vụ GGUF reranker.

Public FastAPI contract giữ nguyên:

```text
POST /v1/embeddings
POST /v1/rerank
GET  /health
GET  /ready
GET  /v1/models
GET  /v1/stats
```

Node/Qdrant layer không cần biết reranker backend nào đang active.

## 2. Frozen baseline behavior

Không thay embedding numerical path:

```text
Qwen3-Embedding-4B
Transformers FP16 CPU
-> last-token pooling
-> cast pooled output to FP32
-> L2 normalize in FP32
-> public Float32[2560]
```

Không sửa response format hiện tại của `/v1/embeddings`.

Public rerank response vẫn giữ dạng:

```json
{
  "model": "Qwen/Qwen3-Reranker-4B",
  "results": [
    {
      "index": 0,
      "score": 0.0
    }
  ],
  "meta": {
    "queue_wait_ms": 0.0,
    "inference_ms": 0.0,
    "document_count": 1
  }
}
```

## 3. Initial GGUF candidate

Dùng mirrored Kaggle model:

```text
https://www.kaggle.com/models/dangkhoa2016/giladgd-qwen3-reranker-4b-gguf/
```

Initial candidate basename:

```text
Qwen3-Reranker-4B.Q4_K_M.gguf
```

Upstream mirror reference:

```text
giladgd/Qwen3-Reranker-4B-GGUF
```

Upstream Q4_K_M file:

```text
Qwen3-Reranker-4B.Q4_K_M.gguf
size ~2.5 GB
upstream SHA-256:
941f7d1d1524251c026a797b803ac9575545c5d7aa19b26e0e49661d7720af49
```

Kaggle mirror phải được inspect local trước execution. Runtime không được âm thầm giả định exact Kaggle directory revision number.

## 4. Kiến trúc

```text
                      FastAPI :8000
                           |
              +------------+-------------+
              |                          |
              v                          v
      EmbeddingEngine              GGUFRerankerEngine
      Transformers FP16                   |
              |                            |
              v                            v
 Qwen3-Embedding-4B             localhost llama-server
 /kaggle/input/...                  127.0.0.1:8081
                                           |
                                           v
                              Qwen3-Reranker-4B
                                  Q4_K_M GGUF
```

`DualModelRuntime` vẫn là single public runtime được FastAPI sử dụng.

Backend được chọn bằng configuration:

```text
RERANKER_BACKEND=transformers
RERANKER_BACKEND=llama_cpp
```

Default giữ:

```text
transformers
```

Như vậy frozen baseline chỉ thay đổi khi experimental backend được bật rõ ràng.

## 5. Thay đổi component

### 5.1 `src/qwen_dual_server/config.py`

Thêm các setting:

```text
reranker_backend:
  "transformers" | "llama_cpp"
  default = "transformers"

reranker_gguf_path:
  optional explicit .gguf path

llama_server_bin:
  optional explicit llama-server binary

llama_server_host:
  default = "127.0.0.1"

llama_server_port:
  default = 8081

llama_server_threads:
  default = 2

llama_server_context_size:
  default = 1024

llama_server_startup_timeout_seconds:
  default = 180
```

Environment names:

```text
RERANKER_BACKEND
RERANKER_GGUF_PATH
LLAMA_SERVER_BIN
LLAMA_SERVER_HOST
LLAMA_SERVER_PORT
LLAMA_SERVER_THREADS
LLAMA_SERVER_CONTEXT_SIZE
LLAMA_SERVER_STARTUP_TIMEOUT_SECONDS
```

Validation rules:

```text
RERANKER_BACKEND=transformers
-> existing reranker path rules remain unchanged

RERANKER_BACKEND=llama_cpp
-> QUANTIZATION_MODE must remain "none"
-> GGUF path must be a readable regular file ending in .gguf
-> llama-server executable must exist/be executable
-> port must not equal FastAPI port
-> GPU offload is not enabled by this experiment
```

### 5.2 New `src/qwen_dual_server/gguf_locator.py`

Trách nhiệm:

1. ưu tiên `RERANKER_GGUF_PATH` nếu được khai báo;
2. nếu không, recursive scan `/kaggle/input`;
3. ưu tiên exact basename `Qwen3-Reranker-4B.Q4_K_M.gguf`;
4. reject zero match;
5. reject multiple exact match thay vì chọn ngẫu nhiên;
6. trả read-only `/kaggle/input/...` file mà không copy.

Không auto-fallback sang quant khác. Nếu Q4_K_M thiếu, fail closed và liệt kê matching `.gguf` files hiện có.

### 5.3 New `src/qwen_dual_server/llama_server.py`

Unit này chỉ sở hữu child process.

Trách nhiệm:

```text
- locate llama-server executable;
- build deterministic CPU-only argv;
- start subprocess;
- capture stdout/stderr to a configured log path;
- poll health/readiness;
- detect early process exit;
- terminate gracefully;
- SIGKILL only after a bounded shutdown timeout;
- never use shell=True.
```

Initial command shape:

```bash
llama-server \
  -m "$RERANKER_GGUF_PATH" \
  --embedding \
  --rerank \
  --pooling rank \
  --host 127.0.0.1 \
  --port 8081 \
  -t 2 \
  -c 1024
```

Không dùng `-ngl` / GPU offload trong CPU experiment này.

Exact supported flags phải được check với installed `llama-server --help` trước real-model execution. Nếu installed version dùng compatible alias thì chỉ adapt launcher, không đổi public service contract.

### 5.4 New `src/qwen_dual_server/gguf_reranker_engine.py`

Public interface phải đủ tương thích với current reranker engine cho `DualModelRuntime`:

```python
load() -> None

rerank(
    query: str,
    documents: list[str],
    instruction: str | None = None,
) -> list[dict[str, object]]

info() -> dict[str, object]

close() -> None
```

`load()`:

```text
- resolve GGUF;
- start llama-server;
- verify endpoint responds;
- send a tiny functional rerank request;
- require finite relevance scores;
- mark engine loaded only after functional proof.
```

`rerank()` gửi:

```http
POST http://127.0.0.1:8081/v1/rerank
Content-Type: application/json
```

Payload:

```json
{
  "query": "<query>",
  "documents": ["<doc1>", "<doc2>"],
  "top_n": 2
}
```

llama.cpp response dùng:

```text
results[].index
results[].relevance_score
```

Adapter trả:

```text
index
score
```

với:

```python
score = float(relevance_score)
```

Adapter phải:

```text
- require HTTP 200;
- require exactly one result per input document when top_n=len(documents);
- require every index in [0, document_count);
- reject duplicate indices;
- require every score finite;
- sort descending by score before returning;
- preserve original document indices.
```

### 5.5 Instruction behavior

Public request hiện cho phép optional reranker instruction, còn llama.cpp `/v1/rerank` chỉ expose query + documents và không có cùng Transformers Qwen yes/no prompt controls.

First feasibility branch:

```text
instruction is None
-> supported

instruction is supplied
-> fail closed with a clear backend capability error
```

Không silently concatenate instruction vào query vì sẽ thay scoring semantics khi chưa có evidence. Limitation này chấp nhận được cho first GGUF feasibility run và phải được document trong `/v1/models`/docs.

### 5.6 `src/qwen_dual_server/runtime.py`

Factory behavior:

```python
if settings.reranker_backend == "transformers":
    reranker_engine = RerankerEngine(...)

elif settings.reranker_backend == "llama_cpp":
    reranker_engine = GGUFRerankerEngine(...)
```

Embedding construction không đổi.

Memory-loading behavior của GGUF branch:

```text
1. acquire singleton runtime lock
2. configure torch CPU threads
3. load FP16 embedding model
4. memory checkpoint
5. start/load GGUF llama-server
6. memory checkpoint
7. mark runtime ready
```

`close()` đóng cả engine; GGUF engine phải terminate child `llama-server`.

### 5.7 `/v1/models`

Giữ `data` array.

Embedding row vẫn baseline-compatible.

GGUF reranker row phải truthfully expose:

```json
{
  "role": "reranker",
  "id": "Qwen/Qwen3-Reranker-4B",
  "loaded": true,
  "device": "cpu",
  "backend": "llama_cpp",
  "format": "gguf",
  "quantization": "Q4_K_M",
  "model_path": "/kaggle/input/.../Qwen3-Reranker-4B.Q4_K_M.gguf"
}
```

Không claim Torch dtype hoặc TorchAO quantized module counts cho GGUF child.

### 5.8 `/v1/stats`

Thêm non-breaking fields thay vì xóa counter cũ:

```text
reranker_backend
reranker_backend_pid
reranker_backend_base_url
reranker_gguf_path
```

Tiếp tục đếm rerank requests/documents ở FastAPI layer.

## 6. HTTP và error semantics

Internal llama-server chỉ bind:

```text
127.0.0.1
```

Nó không được expose trực tiếp ra public.

Expected errors:

```text
GGUF not found
-> startup fail closed

llama-server binary missing
-> startup fail closed

llama-server exits during startup
-> startup fail closed with captured log tail

llama-server times out
-> startup fail closed

internal /v1/rerank returns malformed JSON
-> request returns service error; never fabricate score

non-finite relevance_score
-> request fails

custom instruction on first GGUF branch
-> explicit unsupported-capability error
```

## 7. TDD sequence

Production code chỉ được thêm sau khi observed RED test tương ứng.

### TDD 1 — configuration

RED tests:

```text
default backend is transformers
llama_cpp backend parses
invalid backend rejected
llama_cpp requires valid GGUF/binary when runtime resolves them
```

Sau đó implement minimal config fields.

### TDD 2 — GGUF locator

RED tests:

```text
explicit path wins
exact Q4_K_M auto-match succeeds
zero candidates fail
multiple exact matches fail
other quant is not silently selected
```

Sau đó implement `gguf_locator.py`.

### TDD 3 — llama-server command/process wrapper

RED tests:

```text
argv contains --embedding --rerank --pooling rank
argv binds loopback
argv uses configured 2 threads
argv uses configured context
shell=False
close terminates owned child
```

Unit test dùng fake subprocess factory; không load real model. Sau đó implement `llama_server.py`.

### TDD 4 — GGUF reranker response adapter

RED tests với local fake HTTP server/client fixture:

```text
relevance_score maps to score
indices preserved
results sorted descending
duplicate index rejected
out-of-range index rejected
missing result rejected
non-finite score rejected
HTTP failure rejected
```

Sau đó implement `gguf_reranker_engine.py`.

### TDD 5 — runtime backend selection

RED tests:

```text
transformers backend still creates RerankerEngine
llama_cpp backend creates GGUFRerankerEngine
embedding engine is unchanged
close propagates to GGUF child
```

Sau đó modify `runtime.py`.

### TDD 6 — public API regression

Existing API tests phải vẫn green. Thêm API test chứng minh runtime backed bởi fake GGUF engine vẫn trả:

```text
results[].index
results[].score
meta.inference_ms
meta.document_count
```

Không thay public request schema.

## 8. Kaggle llama.cpp provisioning

Không phụ thuộc network download trong model inference.

Experiment có thể provision `llama-server` trong `/kaggle/working` trước khi run.

Preferred order:

```text
1. use an already supplied compatible llama-server binary if present;
2. otherwise build a pinned llama.cpp revision in /kaggle/working;
3. record `llama-server --version`;
4. package version/build evidence.
```

Không sửa `/kaggle/input`. Model đọc trực tiếp từ Kaggle model mount.

## 9. First real-model feasibility run

Chỉ candidate:

```text
Q4_K_M
K=2
threads=2
FastAPI concurrency=1
embedding=Transformers FP16
reranker=GGUF llama.cpp
```

Không chạy Q5/Q8 trong first pass.

Required real-model proof:

```text
GGUF file identity captured
llama-server version captured
server starts CPU-only
/v1/rerank works
Thailand sentinel ranks #1
all scores finite
K2 measured
OOM delta = 0
oom_kill delta = 0
process RSS/cgroup memory captured
```

Historical comparison target:

```text
Transformers FP16 reranker K2 ~60.98 s
```

First-pass interpretation:

```text
K2 >= 60 s
-> no practical speed benefit

30 s <= K2 < 60 s
-> improvement but weak

20 s <= K2 < 30 s
-> interesting

10 s <= K2 < 20 s
-> strong candidate

K2 < 10 s
-> excellent CPU-demo candidate
```

Đây chỉ là feasibility classification, không phải release promotion.

## 10. Explicit non-goals

Không:

```text
change Qwen3-Embedding-4B away from Transformers FP16
change embedding vector dimension
rebuild Qdrant snapshot
integrate Node/Qdrant yet
run TorchAO INT8 again
run A8W8
test multiple GGUF quants in the first pass
use GPU/TPU
expose llama-server to the internet
modify frozen v0.1.1 release/tag
create a production release
```

## 11. Source files dự kiến thay đổi

Create:

```text
src/qwen_dual_server/gguf_locator.py
src/qwen_dual_server/llama_server.py
src/qwen_dual_server/gguf_reranker_engine.py

tests/test_gguf_locator.py
tests/test_llama_server.py
tests/test_gguf_reranker_engine.py
```

Modify:

```text
src/qwen_dual_server/config.py
src/qwen_dual_server/runtime.py
tests/test_config_memory.py
tests/test_runtime.py
tests/test_api.py
.env.example
```

Later experiment/operator files có thể thêm:

```text
scripts/setup-llama-cpp.sh
scripts/start-hybrid-server.sh
tools/run_gguf_reranker_feasibility.sh
```

## 12. Acceptance gate trước real model

Trước khi load GGUF 2.5 GB:

```text
all deterministic tests PASS
compileall PASS
bash -n scripts PASS
existing embedding/reranker/API regression tests PASS
no canonical v0.1.1 archive modified
```

Sau đó chạy đúng một Q4_K_M feasibility candidate.

## 13. External technical references

Upstream GGUF model:

```text
https://huggingface.co/giladgd/Qwen3-Reranker-4B-GGUF
```

llama.cpp reranker serving behavior:

```text
llama serve -m reranker-model.gguf --rerank

Qwen3 example:
llama serve \
  -hf ggml-org/Qwen3-reranker-0.6B-Q8_0-GGUF:Q8_0 \
  --embedding --rerank --pooling rank \
  --port 8080

POST /v1/rerank
```

Implementation phải dùng local mirrored Kaggle `.gguf`; không fetch Hugging Face model ở runtime.

## 14. Điểm tiếp tục

Sau khi design được accept:

```text
write implementation plan
-> create disposable source workspace
-> TDD implementation
-> deterministic verification
-> package source/evidence
-> provide Kaggle/OpenCode execution runbook
-> run one Q4_K_M real-model feasibility candidate
```
