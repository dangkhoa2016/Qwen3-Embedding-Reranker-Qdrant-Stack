# OpenCode CLI Runbook — Qwen3-Embedding-4B + Qwen3-Reranker-4B CPU/RAM-only Shared REST Server

> English | [Tiếng Việt](OPENCODE_QWEN3_DUAL_4B_CPU_SERVER_KAGGLE_RUNBOOK_2026-08-30.vi.md)

**Date:** 2026-08-30  
**Source release:** `qwen3-dual-4b-cpu-rest-server-v0.1.0-with-git.zip`  
**Target:** fresh Kaggle Notebook, **CPU/RAM only**, approximately 30–32 GiB RAM  
**Purpose:** prove that both Qwen 4B models can coexist in one CPU process, expose authenticated REST APIs, and optionally publish the service through a tunnel for other notebooks.

---

## 0. Mission and non-negotiable rules

Execute this runbook end-to-end. Ordinary failures must be investigated and repaired autonomously using the troubleshooting order in this document. Do not stop merely to report the first stack trace. Preserve evidence before every material workaround.

The two logical models are:

```text
Qwen/Qwen3-Embedding-4B
Qwen/Qwen3-Reranker-4B
```

Expected user-owned Kaggle Models:

```text
dangkhoa2016/qwen-qwen3-embedding-4b
dangkhoa2016/qwen-qwen3-reranker-4b
```

Both have already existed in the user's mirror workflow. The production runtime must load them from read-only `/kaggle/input`; do not download or copy the ~8 GB checkpoints unless this runbook explicitly enters an external-input recovery path.

### Frozen CPU-safe baseline

```text
processes holding models          1
Uvicorn workers                  1
Embedding model instances        1
Reranker model instances         1
global heavy inference           1 at a time
model dtype first attempt         float16
public embedding dtype           float32
embedding dimension              2560
max sequence length              512
embedding microbatch             1
reranker microbatch              1
second-model memory gate         MemAvailable >= 10 GiB
final readiness memory gate      MemAvailable >= 4 GiB
remote model downloads           disabled
HF/Transformers runtime network  offline after install
```

Never solve a failure by silently doing any of the following:

```text
MODEL_DTYPE=float32 against the native BF16 checkpoint
SentenceTransformer(...) production loading
device_map="auto"
Uvicorn --workers > 1
MAX_CONCURRENT_INFERENCE > 1
copying model weights to /kaggle/working
lowering memory gates without evidence
removing Bearer auth before public exposure
changing embedding normalization order
returning FP16/BF16 public vectors
```

The historical CPU FP32 failure mode matters: final weight size can fit while startup conversion/materialization still drives cgroup memory above the limit. Therefore peak memory and `memory.events` are acceptance gates, not optional diagnostics.

---

## 1. Required Kaggle inputs

Create a **fresh CPU Kaggle Notebook**. Attach:

1. `qwen3-dual-4b-cpu-rest-server-v0.1.0-with-git.zip`
2. its `.sha256` sidecar
3. Kaggle Model `dangkhoa2016/qwen-qwen3-embedding-4b`, Transformers/default variation
4. Kaggle Model `dangkhoa2016/qwen-qwen3-reranker-4b`, Transformers/default variation

Do **not** attach Qdrant for the first qualification. This project is a shared model-inference server. Qdrant may remain in client notebooks.

Expected paths often look like:

```text
/kaggle/input/models/dangkhoa2016/qwen-qwen3-embedding-4b/transformers/default/1
/kaggle/input/models/dangkhoa2016/qwen-qwen3-reranker-4b/transformers/default/1
```

Do not hard-code these until preflight validates them. Kaggle mount prefixes can change.

---

## 2. Create one immutable evidence root

```bash
set -euo pipefail
RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)-qwen3-dual-4b-cpu"
export RUN_ROOT="/kaggle/working/$RUN_ID"
mkdir -p "$RUN_ROOT"/{preflight,source,logs,tests,memory,server,smoke,tunnel,evidence,package,tmp}
printf '%s\n' "$RUN_ID" | tee "$RUN_ROOT/RUN_ID.txt"
printf '%s\n' "$RUN_ROOT" | tee "$RUN_ROOT/RUN_ROOT.txt"
```

Never overwrite a prior run directory.

---

## 3. Capture the untouched environment

```bash
{
  date -u +%Y-%m-%dT%H:%M:%SZ
  uname -a
  cat /etc/os-release || true
  lscpu || true
  free -h || true
  df -hT /kaggle/working /kaggle/input || true
  echo '=== /proc/meminfo ==='
  cat /proc/meminfo || true
  echo '=== cgroup ==='
  cat /sys/fs/cgroup/memory.max 2>/dev/null || true
  cat /sys/fs/cgroup/memory.current 2>/dev/null || true
  cat /sys/fs/cgroup/memory.peak 2>/dev/null || true
  cat /sys/fs/cgroup/memory.events 2>/dev/null || true
  python --version || true
  python -m pip --version || true
} 2>&1 | tee "$RUN_ROOT/preflight/environment-before.log"

python -m pip freeze | sort > "$RUN_ROOT/preflight/pip-freeze-before.txt"
find /kaggle/input -maxdepth 10 -printf '%y\t%s\t%p\n' 2>/dev/null | sort \
  > "$RUN_ROOT/preflight/kaggle-input-tree.txt"
```

Record PyTorch separately. Do not reinstall it yet:

```bash
python - <<'PY' | tee "$RUN_ROOT/preflight/torch-before.txt"
import torch
print('torch=', torch.__version__)
print('cuda_available=', torch.cuda.is_available())
print('cuda_device_count=', torch.cuda.device_count() if torch.cuda.is_available() else 0)
print('num_threads=', torch.get_num_threads())
PY
```

This is a CPU qualification. A CUDA-capable host is not automatically a failure, but both loaded models must later prove `device=cpu` and the wrapper must not call `.cuda()`.

---

## 4. Locate and verify the source ZIP

Source-integrity semantics: an **authoritative supplied `.sha256` sidecar** is the formal provenance input and is never interchangeable with a **locally generated informational digest** computed from the same archive. The frozen v0.1.0 digest is:

```text
682b612b494d2f3682f7c56f1dd764cfb91117f56f3c9586f6ea1c35eff30a8e
```

Procedure:

1. Locate the source archive.
2. Locate the supplied `.sha256` sidecar independently.
3. Require the sidecar for release/provenance acceptance.
4. Compare sidecar digest to the frozen v0.1.0 digest.
5. Compare archive digest to the same frozen digest.
6. If the sidecar is absent:
   - compute an informational digest only;
   - label provenance `BLOCKED`;
   - do not call that self-generated digest an independent proof.

```bash
SOURCE_ZIP="$(find /kaggle/working /kaggle/input -type f \
  -name 'qwen3-dual-4b-cpu-rest-server-v0.1.0-with-git.zip' -print 2>/dev/null | head -n1)"
SOURCE_SHA="$(find /kaggle/working /kaggle/input -type f \
  -name 'qwen3-dual-4b-cpu-rest-server-v0.1.0-with-git.zip.sha256' -print 2>/dev/null | head -n1)"
FROZEN_V010_SHA='682b612b494d2f3682f7c56f1dd764cfb91117f56f3c9586f6ea1c35eff30a8e'

test -n "$SOURCE_ZIP"
test -f "$SOURCE_ZIP"

ACTUAL="$(sha256sum "$SOURCE_ZIP" | awk '{print $1}')"
printf 'source_zip=%s\n' "$SOURCE_ZIP"

if [ -z "$SOURCE_SHA" ] || [ ! -f "$SOURCE_SHA" ]; then
  {
    echo "SOURCE_PROVENANCE=BLOCKED_AUTHORITATIVE_SIDECAR_MISSING"
    echo "source_zip=$SOURCE_ZIP"
    echo "informational_actual_sha256=$ACTUAL"
    echo "frozen_expected_sha256=$FROZEN_V010_SHA"
  } | tee "$RUN_ROOT/preflight/source-provenance.txt"
  printf '%s  %s\n' "$ACTUAL" "$(basename "$SOURCE_ZIP")" \
    > "$RUN_ROOT/preflight/source-sha256-informational.txt"
  exit 22
fi

EXPECTED="$(awk 'NF {print $1; exit}' "$SOURCE_SHA")"
{
  echo "source_zip=$SOURCE_ZIP"
  echo "authoritative_sidecar=$SOURCE_SHA"
  echo "frozen_expected=$FROZEN_V010_SHA"
  echo "sidecar_expected=$EXPECTED"
  echo "actual=$ACTUAL"
} | tee "$RUN_ROOT/preflight/source-sha256.txt"

test "$EXPECTED" = "$FROZEN_V010_SHA"
test "$ACTUAL"   = "$FROZEN_V010_SHA"
test "$ACTUAL"   = "$EXPECTED"
unzip -t "$SOURCE_ZIP" > "$RUN_ROOT/preflight/source-unzip-test.txt"
```

The authoritative sidecar is never optional for a release-qualification run. A local digest may be recorded diagnostically, but it is not an independent provenance proof.

Extract only to writable storage:

```bash
unzip -q "$SOURCE_ZIP" -d "$RUN_ROOT/source"
export APP="$(find "$RUN_ROOT/source" -maxdepth 2 -type f -name pyproject.toml -printf '%h\n' | head -n1)"
test -n "$APP"
cd "$APP"
printf '%s\n' "$APP" | tee "$RUN_ROOT/preflight/app-root.txt"
```

If `.git` is present:

```bash
git status --short --branch | tee "$RUN_ROOT/preflight/git-status-initial.txt"
git log -5 --oneline --decorate | tee "$RUN_ROOT/preflight/git-log-initial.txt"
```

Do not edit source before the fast test baseline.

---

## 5. Install only the minimum Python dependencies

First verify the preinstalled torch imports. The supplied `requirements.txt` deliberately omits `torch`.

```bash
python - <<'PY'
import torch
print(torch.__version__)
PY
```

Install the service dependencies and capture the delta:

```bash
python -m pip install -r requirements.txt \
  2>&1 | tee "$RUN_ROOT/logs/pip-install.txt"
python -m pip install -e . --no-deps --no-build-isolation \
  2>&1 | tee "$RUN_ROOT/logs/pip-install-editable.txt"
python -m pip freeze | sort > "$RUN_ROOT/preflight/pip-freeze-after.txt"
```

Hard version gate:

```bash
python - <<'PY' | tee "$RUN_ROOT/preflight/runtime-versions.txt"
import torch, transformers, fastapi, pydantic
from packaging.version import Version
print('torch=', torch.__version__)
print('transformers=', transformers.__version__)
print('fastapi=', fastapi.__version__)
print('pydantic=', pydantic.__version__)
assert Version(transformers.__version__) >= Version('4.51.0')
assert Version(transformers.__version__) < Version('5.0.0')
PY
```

If `packaging` is unexpectedly absent, use `python -m pip install packaging` and record it in the install log. Do not broadly upgrade the notebook environment.

---

## 6. Fast TDD/static verification before loading 16 GB of weights

```bash
set +e
PYTHONPATH=src pytest -q 2>&1 | tee "$RUN_ROOT/tests/pytest-fast.log"
TEST_RC=${PIPESTATUS[0]}
set -e
printf '%s\n' "$TEST_RC" > "$RUN_ROOT/tests/pytest-fast.exitcode"
test "$TEST_RC" = 0

python -m compileall -q src scripts
bash -n scripts/*.sh
```

These tests are intentionally weight-free and must pass before live model work.

Check that production source does not regress to known-dangerous topology:

```bash
! grep -R --line-number 'SentenceTransformer(' src scripts
! grep -R --line-number 'device_map.*auto' src scripts
! grep -R --line-number -- '--workers [23456789]' scripts
```

---

## 7. Discover and validate both read-only Kaggle model roots

Run the provided structural preflight:

```bash
PYTHONPATH=src python scripts/preflight.py \
  2>&1 | tee "$RUN_ROOT/preflight/model-preflight.json"
```

Required result:

```text
exit code = 0
models.embedding = exactly one validated path
models.reranker  = exactly one validated path
```

The locator validates, without reading all weight bytes:

```text
config.json
model_type=qwen3
hidden_size=2560
num_hidden_layers=36
modules.json role signal
model.safetensors.index.json non-empty weight_map
all referenced safetensors shards exist
tokenizer_config.json
```

If discovery is ambiguous, **do not choose the first result**. Set explicit paths after inspecting candidates:

```bash
export EMBEDDING_MODEL_PATH='/kaggle/input/.../qwen-qwen3-embedding-4b/.../1'
export RERANKER_MODEL_PATH='/kaggle/input/.../qwen-qwen3-reranker-4b/.../1'
PYTHONPATH=src python scripts/preflight.py | tee "$RUN_ROOT/preflight/model-preflight-explicit.json"
```

Requiring exact roles protects against accidentally selecting the existing PyTorch/fp32 embedding variation or the 8B reranker.

---

## 8. Establish the FP16 dual-model runtime configuration

Generate a strong API token but never write it into the review archive:

```bash
export DUAL_API_KEY="$(openssl rand -hex 32)"
test ${#DUAL_API_KEY} -ge 32
```

Freeze the initial candidate:

```bash
export ALLOW_INSECURE_NO_AUTH=0
export ALLOW_REMOTE_MODEL_DOWNLOAD=0
export MODEL_DTYPE=float16
export MAX_SEQ_LENGTH=512
export EMBEDDING_MICROBATCH_SIZE=1
export RERANKER_MICROBATCH_SIZE=1
export MAX_CONCURRENT_INFERENCE=1
export MAX_QUEUE_WAITERS=32
export MAX_EMBEDDING_ITEMS=32
export MAX_RERANK_DOCUMENTS=20
export SECOND_MODEL_MIN_AVAILABLE_GIB=10
export FINAL_MIN_AVAILABLE_GIB=4
export WARMUP_ENABLED=1
export LOAD_MODELS_ON_STARTUP=1
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export TOKENIZERS_PARALLELISM=false
export SERVER_HOST=127.0.0.1
export SERVER_PORT=8000
export STARTUP_TIMEOUT_SECONDS=1200
```

Why FP16 first: the prior Qwen3-Embedding-4B CPU experiment already proved this execution dtype and its semantic contract. Do not return to runtime FP32 conversion just because the source checkpoint is BF16.

Snapshot OOM counters immediately before the live load:

```bash
cat /sys/fs/cgroup/memory.events | tee "$RUN_ROOT/memory/manual-memory.events-before"
cat /sys/fs/cgroup/memory.peak 2>/dev/null | tee "$RUN_ROOT/memory/manual-memory.peak-before" || true
free -h | tee "$RUN_ROOT/memory/free-before-load.txt"
```

---

## 9. Start both models in the controlled order and monitor every second

The runtime load order is deliberately:

```text
process singleton lock
  -> embedding load
  -> embedding warm-up
  -> GC
  -> cgroup OOM delta check
  -> require MemAvailable >= 10 GiB
  -> reranker load
  -> reranker warm-up
  -> GC
  -> cgroup OOM delta check
  -> require final MemAvailable >= 4 GiB
  -> READY
```

Run:

```bash
bash scripts/start-and-monitor.sh \
  2>&1 | tee "$RUN_ROOT/logs/start-and-monitor.console.log"
```

If it succeeds, it prints the active PID and keeps the server running.

Immediately inspect:

```bash
cat "$RUN_ROOT/server/startup-result.txt"
tail -200 "$RUN_ROOT/logs/server.log"
tail -20 "$RUN_ROOT/memory/memory-monitor.csv"
cat "$RUN_ROOT/memory/memory.events.after"
cat "$RUN_ROOT/memory/memory.peak.after" 2>/dev/null || true
```

Hard memory gates for a PASS:

```text
server /ready = HTTP 200
oom delta      = 0
oom_kill delta = 0
both models report CPU
both models report requested dtype truthfully
final system MemAvailable >= 4 GiB
```

Do not infer dual-model memory success merely because the process is alive.

---

## 10. Local REST acceptance before any tunnel

Run the supplied smoke suite:

```bash
mkdir -p "$RUN_ROOT/smoke"
export SERVER_URL='http://127.0.0.1:8000'
export SMOKE_OUTPUT="$RUN_ROOT/smoke/local-smoke.json"
export SMOKE_TIMEOUT_SECONDS=1200
python scripts/smoke-http.py \
  2>&1 | tee "$RUN_ROOT/smoke/local-smoke.console.log"
```

It must prove:

```text
/health = 200
/ready = 200
/v1/models without auth = 401
/v1/models with auth = 200 and exactly two models
embedding dimension = 2560
embedding norm ~= 1.0 after FP32 normalization
reranker places the clearly relevant Thailand/baht passage at rank #1
/v1/stats = 200
```

Inspect authenticated model metadata:

```bash
curl -fsS \
  -H "Authorization: Bearer $DUAL_API_KEY" \
  http://127.0.0.1:8000/v1/models \
  | tee "$RUN_ROOT/server/models-local.json" | python -m json.tool
```

Expected roles:

```text
embedding
reranker
```

Expected runtime family:

```text
backend=transformers
runtime=pytorch-cpu
device=cpu
dtype=float16
```

Embedding must additionally advertise:

```text
public_vector_dtype=float32
dimension=2560
```

---

## 11. Compatibility check for the existing Node/Qdrant notebook

This server deliberately keeps the prior canonical default query behavior:

```text
Instruct: Retrieve the geographic entity that best answers the query
Query:<query>
```

and documents remain raw. Therefore the existing `knowledge_entities_qwen3_4b_text_v21` client can call `/v1/embeddings` with:

```json
{
  "input": "quốc gia Đông Nam Á sử dụng đồng baht",
  "input_type": "query"
}
```

Do not send a different instruction when querying that historical Qdrant collection unless you intentionally want a different embedding space behavior.

For unrelated retrieval applications, custom instructions are supported:

```json
{
  "input": "query text",
  "input_type": "query",
  "instruction": "Given a web search query, retrieve relevant passages that answer the query"
}
```

The reranker also accepts a bounded custom instruction.

---

## 12. Public exposure — only after local acceptance PASS

Keep Uvicorn bound to loopback:

```text
127.0.0.1:8000
```

Never restart it on `0.0.0.0` merely for tunnel access.

### 12.1 Find or install cloudflared

```bash
command -v cloudflared | tee "$RUN_ROOT/tunnel/cloudflared-path.txt" || true
cloudflared --version 2>&1 | tee "$RUN_ROOT/tunnel/cloudflared-version.txt" || true
```

If missing and Kaggle Internet is enabled, install the official Linux AMD64 binary into writable storage. Record URL, size, SHA256 and version. Do not alter model files.

Example:

```bash
CLOUDFLARED="$RUN_ROOT/tmp/cloudflared"
curl -fL --retry 3 \
  -o "$CLOUDFLARED" \
  https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64
chmod +x "$CLOUDFLARED"
sha256sum "$CLOUDFLARED" | tee "$RUN_ROOT/tunnel/cloudflared.sha256"
"$CLOUDFLARED" --version | tee "$RUN_ROOT/tunnel/cloudflared-version.txt"
```

### 12.2 Quick Tunnel for development/demo

```bash
CLOUDFLARED_BIN="${CLOUDFLARED:-$(command -v cloudflared)}"
nohup "$CLOUDFLARED_BIN" tunnel \
  --no-autoupdate \
  --url http://127.0.0.1:8000 \
  > "$RUN_ROOT/tunnel/cloudflared.log" 2>&1 &
TUNNEL_PID=$!
printf '%s\n' "$TUNNEL_PID" > "$RUN_ROOT/tunnel/cloudflared.pid"
```

Wait for the HTTPS URL:

```bash
PUBLIC_URL=''
for i in $(seq 1 120); do
  PUBLIC_URL="$(grep -Eo 'https://[-a-z0-9]+\.trycloudflare\.com' "$RUN_ROOT/tunnel/cloudflared.log" | tail -n1 || true)"
  [[ -n "$PUBLIC_URL" ]] && break
  kill -0 "$TUNNEL_PID" 2>/dev/null || break
  sleep 1
done
printf '%s\n' "$PUBLIC_URL" | tee "$RUN_ROOT/tunnel/public-url.txt"
test -n "$PUBLIC_URL"
```

Quick Tunnel is a demo/development endpoint. For a stable long-lived hostname, use a named tunnel in a later deployment phase.

### 12.3 Verify the public boundary

Unauthenticated model access must still fail:

```bash
code="$(curl -sS -o "$RUN_ROOT/tunnel/public-unauthorized.json" -w '%{http_code}' \
  "$PUBLIC_URL/v1/models")"
test "$code" = 401
```

Authenticated call:

```bash
curl -fsS --max-time 1200 \
  -H "Authorization: Bearer $DUAL_API_KEY" \
  "$PUBLIC_URL/v1/models" \
  | tee "$RUN_ROOT/tunnel/public-models.json" | python -m json.tool
```

Run the complete smoke remotely:

```bash
export SERVER_URL="$PUBLIC_URL"
export SMOKE_OUTPUT="$RUN_ROOT/smoke/public-smoke.json"
python scripts/smoke-http.py \
  2>&1 | tee "$RUN_ROOT/smoke/public-smoke.console.log"
```

Do not put `DUAL_API_KEY` in the evidence ZIP, notebook output screenshot, git commit, or public URL.

---

## 13. Example from another Kaggle/Colab notebook

The client notebook needs only the public URL and secret token:

```python
import requests

BASE = "https://YOUR-TUNNEL.trycloudflare.com"
TOKEN = "YOUR_SECRET_FROM_A_PRIVATE_CHANNEL"
H = {"Authorization": f"Bearer {TOKEN}"}

r = requests.post(
    BASE + "/v1/embeddings",
    headers=H,
    json={
        "input": "quốc gia Đông Nam Á sử dụng đồng baht",
        "input_type": "query",
    },
    timeout=1200,
)
r.raise_for_status()
vector = r.json()["data"][0]["embedding"]
print(len(vector))  # 2560

candidates = [
    "Thailand is a country in Southeast Asia. Its currency is the Thai baht.",
    "Canada is a country in North America.",
]
r = requests.post(
    BASE + "/v1/rerank",
    headers=H,
    json={
        "query": "quốc gia Đông Nam Á sử dụng đồng baht",
        "documents": candidates,
        "return_documents": True,
    },
    timeout=1200,
)
r.raise_for_status()
print(r.json())
```

For the Node/Qdrant project, the intended flow is:

```text
client query
  -> shared /v1/embeddings
  -> client-side Qdrant top-K
  -> shared /v1/rerank on top-K texts
  -> final top-N
```

This server intentionally does not own Qdrant.

---

# 14. Autonomous troubleshooting policy

OpenCode CLI should continue through ordinary failures using the following exact order. Every branch must archive the failed log and memory evidence before changing configuration.

## 14.1 Model not found

1. Run `find /kaggle/input -name config.json` and inspect the tree.
2. Confirm the expected user-owned model is actually attached.
3. Run `scripts/preflight.py` with no explicit paths.
4. If exactly one valid candidate exists for each role, use it.
5. If ambiguous, set explicit paths and rerun preflight.
6. If `qwen-qwen3-reranker-4b` is genuinely absent, this is an **external-input gate**. Do not download the 8 GB checkpoint inside the production runtime. Record the required Kaggle model slug and stop only this gate.

## 14.2 `KeyError: 'qwen3'` or unsupported model type

1. Capture `transformers.__version__`.
2. Require `transformers >= 4.51.0,<5`.
3. Install only a compatible Transformers 4.x version.
4. Do not reinstall torch unless a concrete ABI/import failure proves it necessary.
5. Rerun fast tests + preflight before loading weights again.

## 14.3 Embedding FP16 load OOM

1. Archive `server.log`, `memory-monitor.csv`, `memory.events.*`, process list.
2. Verify other heavy Python/Node/Qdrant/model processes are not resident.
3. Kill only unrelated/owned processes and confirm memory returns.
4. Retry on the same clean FP16 baseline once.
5. If repeatable, use a **fresh CPU notebook** to eliminate stale page-cache/process contamination.
6. Do not switch to runtime FP32 conversion.
7. Only after the FP16 failure is proven reproducible may you run a **separate controlled BF16 candidate** because the source checkpoints are BF16. Preserve its evidence as a separate run; never overwrite the FP16 result.

## 14.4 Embedding loads but `SECOND_MODEL_MIN_AVAILABLE_GIB` blocks Reranker

This is a safety success, not a bug.

1. Record `MemAvailable`, cgroup current/peak, Embedding RSS.
2. Check for unrelated resident processes.
3. Restart in a fresh notebook if contamination exists.
4. Keep threshold at 10 GiB for the first qualification.
5. Do not lower it simply to force Reranker load.
6. If a clean notebook still leaves <10 GiB, run the separate BF16 candidate described above.
7. Only propose a lower threshold after measured Reranker load peak demonstrates a safe margin; do not implement that policy silently.

## 14.5 Reranker OOM while Embedding is resident

1. Archive all memory evidence immediately.
2. Confirm `oom`/`oom_kill` deltas.
3. Reboot/fresh notebook before retrying if an OOM kill occurred.
4. Retry `MAX_SEQ_LENGTH=512`, `RERANKER_MICROBATCH_SIZE=1`, warm-up single pair.
5. Keep global inference concurrency 1.
6. Try native BF16 only as a **separate candidate**, never as an unreported substitution.
7. Do not add disk offload/device_map tricks before proving the simpler native dtype candidates.
8. If both FP16 and BF16 clean runs OOM at the conservative baseline, classify dual-4B/30-GiB as `MEMORY_FEASIBILITY_FAIL` with evidence rather than hiding the result.

## 14.6 FP16 CPU operator exception

1. Capture exact operator/stack trace and torch version.
2. Reproduce with one minimal embedding query or one reranker pair.
3. Try BF16 as the controlled alternate because both source checkpoints are BF16.
4. Keep pooled embedding/logit post-processing in FP32.
5. Do not silently expand the full model to FP32.

## 14.7 Embedding norm is not approximately 1.0

Required numerical sequence is:

```text
model forward in FP16/BF16
-> last-token pooling
-> pooled.float()
-> F.normalize(..., p=2, dim=1) in FP32
-> public Float32[2560]
```

Do not normalize in BF16/FP16 and then cast. This exact issue was previously observed and corrected.

## 14.8 Reranker scores look wrong

Verify the implementation has not drifted from:

```text
formatted pair = <Instruct> + <Query> + <Document>
official Qwen yes/no prefix/suffix
final-position logits
false token = "no"
true token  = "yes"
logits cast to FP32
stack [false,true]
log_softmax -> exp(true)
sort descending
```

Do not replace this with arbitrary hidden-state cosine similarity.

## 14.9 Public endpoint works locally but tunnel fails

1. Keep localhost service running and locally healthy.
2. Check Kaggle Internet setting/DNS.
3. Capture cloudflared version and log.
4. Restart only the tunnel process, not both 4B models.
5. Keep the inference service bound to loopback.
6. If Quick Tunnel is unavailable, local dual-model acceptance can still PASS, but classify `PUBLIC_TUNNEL=BLOCKED_EXTERNAL_NETWORK` and preserve evidence.
7. Do not expose an unauthenticated alternate port.

## 14.10 Queue returns HTTP 429

This is intentional backpressure. Do not increase heavy inference concurrency first.

Client policy:

```text
retry with exponential backoff
or submit fewer concurrent requests
```

Only benchmark concurrency 2 in a future phase after dual-model memory and latency are proven.

---

# 15. Acceptance matrix

Create `$RUN_ROOT/evidence/acceptance-summary.md` with this table and measured values:

| Gate | Required result |
|---|---|
| Source SHA | PASS |
| Fast tests | PASS |
| Model locator | exactly 1 Embedding + 1 Reranker |
| Embedding load | PASS |
| Embedding warm-up | PASS |
| Pre-Reranker MemAvailable | >= 10 GiB |
| Reranker load | PASS |
| Reranker warm-up | PASS |
| Final MemAvailable | >= 4 GiB |
| cgroup oom delta | 0 |
| cgroup oom_kill delta | 0 |
| Uvicorn worker count | 1 |
| Model instances | 1 + 1 |
| Model devices | cpu + cpu |
| Model dtype | truthful candidate dtype |
| Embedding dimension | 2560 |
| Embedding norm | `abs(norm-1) <= 1e-4` |
| Reranker sentinel | relevant passage rank #1 |
| Unauthorized `/v1/models` | 401 |
| Local smoke | PASS |
| Public smoke | PASS, or explicitly BLOCKED_EXTERNAL_NETWORK |
| Secret leakage scan | PASS |

Also report:

```text
peak process RSS during startup (from CSV)
peak cgroup memory.current observed
kernel/cgroup memory.peak
steady process RSS after both models
startup duration
embedding inference latency
reranker 2-document latency
```

Do not fabricate missing metrics.

---

## 16. Long-run stability smoke

After local/public functional acceptance, run a conservative alternating workload. Do not create parallel heavy inference yet.

Suggested 10 cycles:

```bash
for i in $(seq 1 10); do
  echo "cycle=$i"
  SERVER_URL='http://127.0.0.1:8000' \
  SMOKE_OUTPUT="$RUN_ROOT/smoke/cycle-$i.json" \
  python scripts/smoke-http.py \
    >> "$RUN_ROOT/smoke/stability.console.log" 2>&1
  cat /sys/fs/cgroup/memory.current >> "$RUN_ROOT/memory/stability-memory.current"
  cat /sys/fs/cgroup/memory.events >> "$RUN_ROOT/memory/stability-memory.events"
done
```

Required:

```text
10/10 smoke cycles PASS
no OOM delta
no server restart
no non-finite embedding/reranker values
```

CPU latency may be high; correctness/stability is the first goal of v0.1.0.

---

## 17. Collect review evidence

Return to the source root and run:

```bash
cd "$APP"
export SERVER_URL='http://127.0.0.1:8000'
bash scripts/collect-evidence.sh \
  2>&1 | tee "$RUN_ROOT/logs/collect-evidence.log"
```

Manually add the current acceptance summary and tunnel logs if not already included.

Secret scan before packaging. Capture grep output outside the scanned tree first, then materialize the result file. This keeps the output file out of its own scan path and fails closed on any scan state:

```bash
TMP_SCAN="$(mktemp)"
trap 'rm -f "$TMP_SCAN"' EXIT

set +e
grep -R --line-number --fixed-string "$DUAL_API_KEY" "$RUN_ROOT" \
  --exclude='*.zip' \
  --exclude='*.sha256' \
  --exclude='secret-scan.txt' \
  > "$TMP_SCAN"
SECRET_RC=$?
set -e

if [ "$SECRET_RC" -eq 1 ]; then
  : > "$RUN_ROOT/evidence/secret-scan.txt"
  printf 'PASS: DUAL_API_KEY not present in review tree\n' \
    > "$RUN_ROOT/evidence/secret-scan-result.txt"
elif [ "$SECRET_RC" -eq 0 ]; then
  cp "$TMP_SCAN" "$RUN_ROOT/evidence/secret-scan.txt"
  printf 'FAIL: DUAL_API_KEY found in review tree\n' \
    > "$RUN_ROOT/evidence/secret-scan-result.txt"
  echo "FAIL: secret found" >&2
  exit 1
else
  printf 'FAIL: secret scan execution error rc=%s\n' "$SECRET_RC" \
    > "$RUN_ROOT/evidence/secret-scan-result.txt"
  echo "FAIL: secret scan execution error rc=$SECRET_RC" >&2
  exit 1
fi

rm -f "$TMP_SCAN"
trap - EXIT
```

If a secret is found, delete/redact the offending evidence and rerun the scan before packaging. Never simply omit the scan result.

The collector creates:

```text
$RUN_ROOT/package/qwen3-dual-4b-cpu-evidence-<UTC>.zip
$RUN_ROOT/package/qwen3-dual-4b-cpu-evidence-<UTC>.zip.sha256
```

Verify:

```bash
EVIDENCE_ZIP="$(find "$RUN_ROOT/package" -name 'qwen3-dual-4b-cpu-evidence-*.zip' -print | tail -n1)"
unzip -t "$EVIDENCE_ZIP" | tee "$RUN_ROOT/package/unzip-test.log"
sha256sum "$EVIDENCE_ZIP"
cat "$EVIDENCE_ZIP.sha256"
```

---

# 18. What OpenCode CLI must return to the user

Return all of the following, not just “it works”:

1. final classification:
   ```text
   DUAL_MODEL_MEMORY_FEASIBILITY=PASS|FAIL
   LOCAL_REST=PASS|FAIL
   PUBLIC_TUNNEL=PASS|BLOCKED_EXTERNAL_NETWORK|FAIL
   ```
2. source Git HEAD after any fixes;
3. exact model paths used;
4. candidate dtype actually loaded;
5. pre-Reranker and final `MemAvailable`;
6. startup peak RSS/cgroup peak;
7. `oom` and `oom_kill` before/after/delta;
8. embedding dimension/norm/latency;
9. reranker sentinel score/rank/latency;
10. local/public endpoint URL (URL is okay; **never return the API key in the artifact**);
11. evidence ZIP path + SHA-256;
12. any code changes made during troubleshooting, each with reason and tests;
13. a short list of unresolved limitations.

If code was changed, run the **entire** fast suite again and create a Git commit before returning evidence.

---

# 19. Expected limitations even if the run passes

A PASS proves a useful low-traffic shared CPU inference appliance. It does **not** prove:

```text
high request concurrency
low latency
24/7 Kaggle availability
stable Quick Tunnel hostname
large reranker candidate lists
32K context on CPU
batch > 1 safety
production SLA
```

Those are later qualification phases. Do not optimize them during this initial residency experiment.

---

# 20. Exact continuation if v0.1.0 passes

Do not immediately increase every limit. Recommended next controlled phases are:

```text
Phase A: benchmark FP16 vs native BF16 dual residency
Phase B: measure reranker top-K = 5/10/20 latency
Phase C: test MAX_CONCURRENT_INFERENCE=2 only if memory/CPU contention allows
Phase D: integrate the shared endpoint into nodejs-qdrant-bilingual-search
Phase E: stable named-tunnel deployment / another long-lived host if needed
```

Change one variable per experiment and preserve the v0.1.0 baseline.

---

## End of Runbook
