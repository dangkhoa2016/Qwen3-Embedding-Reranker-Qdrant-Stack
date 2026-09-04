# Qwen3 Hybrid CPU Runtime Design
> 🌐 Language / Ngôn ngữ: **English** | [Tiếng Việt](design.vi.md)

## Transformers FP16 Embedding + llama.cpp GGUF Reranker

**Date:** 2026-09-01  
**Status:** Design ready for implementation review  
**Scope:** Kaggle CPU/RAM-only experimental branch; no Git repository required

## 1. Goal

Keep the already-qualified `Qwen3-Embedding-4B` Transformers FP16 path unchanged and replace only the `Qwen3-Reranker-4B` Transformers path with a local `llama-server` process serving a GGUF reranker.

The public FastAPI contract remains:

```text
POST /v1/embeddings
POST /v1/rerank
GET  /health
GET  /ready
GET  /v1/models
GET  /v1/stats
```

The Node/Qdrant layer must not need to know which reranker backend is active.

## 2. Frozen baseline behavior

Do not change the embedding numerical path:

```text
Qwen3-Embedding-4B
Transformers FP16 CPU
-> last-token pooling
-> cast pooled output to FP32
-> L2 normalize in FP32
-> public Float32[2560]
```

Do not modify the existing `/v1/embeddings` response format.

Current rerank public response stays:

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

Use the mirrored Kaggle model:

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

The Kaggle mirror must be inspected locally before execution. The runtime must not silently assume an exact Kaggle directory revision number.

## 4. Architecture

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

`DualModelRuntime` remains the single public runtime used by FastAPI.

The backend is selected by configuration:

```text
RERANKER_BACKEND=transformers
RERANKER_BACKEND=llama_cpp
```

Default stays:

```text
transformers
```

This preserves the frozen baseline unless the experimental backend is explicitly enabled.

## 5. Component changes

### 5.1 `src/qwen_dual_server/config.py`

Add:

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

Responsibilities:

1. honor `RERANKER_GGUF_PATH` if explicit;
2. otherwise recursively scan `/kaggle/input`;
3. prefer exact basename:

```text
Qwen3-Reranker-4B.Q4_K_M.gguf
```

4. reject zero matches;
5. reject multiple exact matches rather than choosing arbitrarily;
6. return the read-only `/kaggle/input/...` file without copying it.

Do not auto-fallback to another quant.

If Q4_K_M is missing, fail closed and show available matching `.gguf` files.

### 5.3 New `src/qwen_dual_server/llama_server.py`

This unit owns the child process only.

Responsibilities:

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

No `-ngl` / GPU offload in this CPU experiment.

The exact supported flags must be checked against the installed `llama-server --help` before real-model execution. If the installed version uses a compatible alias, adapt only the launcher, not the public service contract.

### 5.4 New `src/qwen_dual_server/gguf_reranker_engine.py`

Public interface must mirror the current reranker engine closely enough for `DualModelRuntime`:

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

`rerank()` sends:

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

llama.cpp response uses:

```text
results[].index
results[].relevance_score
```

Adapter returns:

```text
index
score
```

where:

```python
score = float(relevance_score)
```

The adapter must:

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

The current public request permits an optional reranker instruction, while llama.cpp `/v1/rerank` exposes query + documents and does not expose the same Transformers Qwen yes/no prompt controls.

For the first feasibility branch:

```text
instruction is None
-> supported

instruction is supplied
-> fail closed with a clear backend capability error
```

Do not silently concatenate an instruction into the query because that would change scoring semantics without evidence.

This limitation is acceptable for the first GGUF feasibility run and must be recorded in `/v1/models`/documentation.

### 5.6 `src/qwen_dual_server/runtime.py`

Factory behavior:

```python
if settings.reranker_backend == "transformers":
    reranker_engine = RerankerEngine(...)

elif settings.reranker_backend == "llama_cpp":
    reranker_engine = GGUFRerankerEngine(...)
```

Embedding construction is unchanged.

Memory-loading behavior changes for the GGUF branch:

```text
1. acquire singleton runtime lock
2. configure torch CPU threads
3. load FP16 embedding model
4. memory checkpoint
5. start/load GGUF llama-server
6. memory checkpoint
7. mark runtime ready
```

`close()` closes both engines; the GGUF engine must terminate its llama-server child.

### 5.7 `/v1/models`

Keep the `data` array.

Embedding row remains baseline-compatible.

GGUF reranker row should truthfully expose:

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

Do not claim Torch dtype or TorchAO quantized module counts for the GGUF child.

### 5.8 `/v1/stats`

Add non-breaking fields rather than remove existing counters:

```text
reranker_backend
reranker_backend_pid
reranker_backend_base_url
reranker_gguf_path
```

Continue to count rerank requests/documents at the FastAPI layer.

## 6. HTTP and error semantics

Internal llama-server is bound only to:

```text
127.0.0.1
```

It is not directly exposed publicly.

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

Production code must be added only after each corresponding RED test is observed.

### TDD 1 — configuration

RED tests:

```text
default backend is transformers
llama_cpp backend parses
invalid backend rejected
llama_cpp requires valid GGUF/binary when runtime resolves them
```

Then implement minimal config fields.

### TDD 2 — GGUF locator

RED tests:

```text
explicit path wins
exact Q4_K_M auto-match succeeds
zero candidates fail
multiple exact matches fail
other quant is not silently selected
```

Then implement `gguf_locator.py`.

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

Use a fake subprocess factory in unit tests; no real model.

Then implement `llama_server.py`.

### TDD 4 — GGUF reranker response adapter

RED tests with a local fake HTTP server/client fixture:

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

Then implement `gguf_reranker_engine.py`.

### TDD 5 — runtime backend selection

RED tests:

```text
transformers backend still creates RerankerEngine
llama_cpp backend creates GGUFRerankerEngine
embedding engine is unchanged
close propagates to GGUF child
```

Then modify `runtime.py`.

### TDD 6 — public API regression

Existing API tests must remain green.

Add API test proving a runtime backed by a fake GGUF engine still returns:

```text
results[].index
results[].score
meta.inference_ms
meta.document_count
```

No public request schema change.

## 8. Kaggle llama.cpp provisioning

Do not depend on network download during model inference.

The experiment may provision `llama-server` in `/kaggle/working` before running.

Preferred order:

```text
1. use an already supplied compatible llama-server binary if present;
2. otherwise build a pinned llama.cpp revision in /kaggle/working;
3. record `llama-server --version`;
4. package version/build evidence.
```

Do not modify `/kaggle/input`.

The model itself must be read directly from the Kaggle model mount.

## 9. First real-model feasibility run

Only candidate:

```text
Q4_K_M
K=2
threads=2
FastAPI concurrency=1
embedding=Transformers FP16
reranker=GGUF llama.cpp
```

Do not run Q5/Q8 in the first pass.

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

This is a feasibility classification only, not a release promotion.

## 10. Explicit non-goals

Do not:

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

## 11. Source files expected to change

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

Later experiment/operator files may add:

```text
scripts/setup-llama-cpp.sh
scripts/start-hybrid-server.sh
tools/run_gguf_reranker_feasibility.sh
```

## 12. Acceptance gate before real model

Before loading the 2.5 GB GGUF:

```text
all deterministic tests PASS
compileall PASS
bash -n scripts PASS
existing embedding/reranker/API regression tests PASS
no canonical v0.1.1 archive modified
```

Then run exactly one Q4_K_M feasibility candidate.

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

The implementation must use the locally mirrored Kaggle `.gguf`; it must not fetch the Hugging Face model at runtime.

## 14. Continuation point

After this design is accepted:

```text
write implementation plan
-> create disposable source workspace
-> TDD implementation
-> deterministic verification
-> package source/evidence
-> provide Kaggle/OpenCode execution runbook
-> run one Q4_K_M real-model feasibility candidate
```
