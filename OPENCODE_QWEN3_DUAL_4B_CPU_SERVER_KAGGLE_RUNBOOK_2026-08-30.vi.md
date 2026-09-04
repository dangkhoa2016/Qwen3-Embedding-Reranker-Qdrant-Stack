# OpenCode CLI Runbook — Qwen3-Embedding-4B + Qwen3-Reranker-4B CPU/RAM-only Shared REST Server
> 🌐 Language / Ngôn ngữ: [English](OPENCODE_QWEN3_DUAL_4B_CPU_SERVER_KAGGLE_RUNBOOK_2026-08-30.md) | **Tiếng Việt**

**Ngày:** 2026-08-30  
**Source release:** `qwen3-dual-4b-cpu-rest-server-v0.1.0-with-git.zip`  
**Target:** fresh Kaggle Notebook, **chỉ CPU/RAM**, khoảng 30–32 GiB RAM  
**Mục đích:** chứng minh hai Qwen 4B model có thể cùng resident trong một CPU process, expose authenticated REST API và tùy chọn publish service qua tunnel cho notebook khác.

---

## 0. Nhiệm vụ và các quy tắc không được thương lượng

Thực hiện runbook này end-to-end. Với failure thông thường, phải tự điều tra và sửa theo troubleshooting order trong tài liệu; không dừng chỉ để báo stack trace đầu tiên. Luôn giữ evidence trước mỗi workaround quan trọng.

Hai logical model:

```text
Qwen/Qwen3-Embedding-4B
Qwen/Qwen3-Reranker-4B
```

Expected user-owned Kaggle Models:

```text
dangkhoa2016/qwen-qwen3-embedding-4b
dangkhoa2016/qwen-qwen3-reranker-4b
```

Cả hai đã tồn tại trong mirror workflow của user. Production runtime phải load từ read-only `/kaggle/input`; không download hoặc copy checkpoint khoảng 8 GB trừ khi runbook chủ động đi vào external-input recovery path.

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

Không bao giờ chữa failure bằng cách âm thầm làm một trong các việc sau:

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

Historical CPU FP32 failure mode rất quan trọng: final weight size có thể fit nhưng startup conversion/materialization vẫn đẩy cgroup memory vượt limit. Vì vậy peak memory và `memory.events` là acceptance gates, không phải diagnostic tùy chọn.

---

## 1. Kaggle inputs bắt buộc

Tạo **fresh CPU Kaggle Notebook**. Attach:

1. `qwen3-dual-4b-cpu-rest-server-v0.1.0-with-git.zip`
2. `.sha256` sidecar tương ứng
3. Kaggle Model `dangkhoa2016/qwen-qwen3-embedding-4b`, Transformers/default variation
4. Kaggle Model `dangkhoa2016/qwen-qwen3-reranker-4b`, Transformers/default variation

**Không** attach Qdrant trong first qualification. Project này là shared model-inference server; Qdrant có thể nằm ở client notebook.

Path thường có dạng:

```text
/kaggle/input/models/dangkhoa2016/qwen-qwen3-embedding-4b/transformers/default/1
/kaggle/input/models/dangkhoa2016/qwen-qwen3-reranker-4b/transformers/default/1
```

Không hard-code cho tới khi preflight validate vì Kaggle mount prefix có thể thay đổi.

---

## 2. Tạo một immutable evidence root

```bash
set -euo pipefail
RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)-qwen3-dual-4b-cpu"
export RUN_ROOT="/kaggle/working/$RUN_ID"
mkdir -p "$RUN_ROOT"/{preflight,source,logs,tests,memory,server,smoke,tunnel,evidence,package,tmp}
printf '%s\n' "$RUN_ID" | tee "$RUN_ROOT/RUN_ID.txt"
printf '%s\n' "$RUN_ROOT" | tee "$RUN_ROOT/RUN_ROOT.txt"
```

Không overwrite run directory cũ.

---

## 3. Capture môi trường chưa bị thay đổi

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

Ghi PyTorch riêng và chưa reinstall:

```bash
python - <<'PY' | tee "$RUN_ROOT/preflight/torch-before.txt"
import torch
print('torch=', torch.__version__)
print('cuda_available=', torch.cuda.is_available())
print('cuda_device_count=', torch.cuda.device_count() if torch.cuda.is_available() else 0)
print('num_threads=', torch.get_num_threads())
PY
```

Đây là CPU qualification. Host có CUDA không tự động là failure, nhưng hai model sau này phải chứng minh `device=cpu` và wrapper không được gọi `.cuda()`.

---

## 4. Locate và verify source ZIP

Source-integrity semantics: **authoritative supplied `.sha256` sidecar** là formal provenance input và không thể thay bằng **locally generated informational digest** tính từ chính archive. Frozen v0.1.0 digest:

```text
682b612b494d2f3682f7c56f1dd764cfb91117f56f3c9586f6ea1c35eff30a8e
```

Quy trình:

1. Locate source archive.
2. Locate supplied `.sha256` sidecar độc lập.
3. Bắt buộc sidecar cho release/provenance acceptance.
4. So sidecar digest với frozen v0.1.0 digest.
5. So archive digest với cùng frozen digest.
6. Nếu thiếu sidecar: chỉ tạo informational digest, đặt provenance `BLOCKED`, và không gọi self-generated digest là independent proof.

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

Authoritative sidecar không optional cho release-qualification run. Local digest chỉ có giá trị diagnostic.

Extract chỉ vào writable storage:

```bash
unzip -q "$SOURCE_ZIP" -d "$RUN_ROOT/source"
export APP="$(find "$RUN_ROOT/source" -maxdepth 2 -type f -name pyproject.toml -printf '%h\n' | head -n1)"
test -n "$APP"
cd "$APP"
printf '%s\n' "$APP" | tee "$RUN_ROOT/preflight/app-root.txt"
```

Nếu có `.git`:

```bash
git status --short --branch | tee "$RUN_ROOT/preflight/git-status-initial.txt"
git log -5 --oneline --decorate | tee "$RUN_ROOT/preflight/git-log-initial.txt"
```

Không sửa source trước fast test baseline.

---

## 5. Chỉ cài Python dependencies tối thiểu

Trước tiên verify preinstalled torch import được. `requirements.txt` được chủ đích bỏ `torch`.

```bash
python - <<'PY'
import torch
print(torch.__version__)
PY
```

Cài service dependencies và capture delta:

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

Nếu `packaging` thiếu, cài `python -m pip install packaging` và record vào install log. Không broad-upgrade notebook environment.

---

## 6. Fast TDD/static verification trước khi load 16 GB weights

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

Các test này chủ đích weight-free và phải pass trước live model work.

Kiểm tra production source không regress về topology nguy hiểm đã biết:

```bash
! grep -R --line-number 'SentenceTransformer(' src scripts
! grep -R --line-number 'device_map.*auto' src scripts
! grep -R --line-number -- '--workers [23456789]' scripts
```

---

## 7. Discover và validate hai read-only Kaggle model roots

Chạy structural preflight được cung cấp:

```bash
PYTHONPATH=src python scripts/preflight.py \
  2>&1 | tee "$RUN_ROOT/preflight/model-preflight.json"
```

Kết quả bắt buộc:

```text
exit code = 0
models.embedding = exactly one validated path
models.reranker  = exactly one validated path
```

Locator validate mà không đọc toàn bộ weight bytes:

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

Nếu discovery ambiguous, **không chọn result đầu tiên**. Inspect candidate rồi set explicit path:

```bash
export EMBEDDING_MODEL_PATH='/kaggle/input/.../qwen-qwen3-embedding-4b/.../1'
export RERANKER_MODEL_PATH='/kaggle/input/.../qwen-qwen3-reranker-4b/.../1'
PYTHONPATH=src python scripts/preflight.py | tee "$RUN_ROOT/preflight/model-preflight-explicit.json"
```

Exact role requirement tránh chọn nhầm PyTorch/fp32 embedding variation hoặc 8B reranker.

---

## 8. Thiết lập FP16 dual-model runtime configuration

Tạo API token mạnh nhưng không ghi vào review archive:

```bash
export DUAL_API_KEY="$(openssl rand -hex 32)"
test ${#DUAL_API_KEY} -ge 32
```

Freeze initial candidate:

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

Lý do FP16 chạy trước: experiment Qwen3-Embedding-4B CPU trước đó đã chứng minh execution dtype này và semantic contract. Không quay lại runtime FP32 conversion chỉ vì source checkpoint là BF16.

Snapshot OOM counters ngay trước live load:

```bash
cat /sys/fs/cgroup/memory.events | tee "$RUN_ROOT/memory/manual-memory.events-before"
cat /sys/fs/cgroup/memory.peak 2>/dev/null | tee "$RUN_ROOT/memory/manual-memory.peak-before" || true
free -h | tee "$RUN_ROOT/memory/free-before-load.txt"
```

---

## 9. Start hai model theo controlled order và monitor mỗi giây

Runtime load order được chủ đích cố định:

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

Chạy:

```bash
bash scripts/start-and-monitor.sh \
  2>&1 | tee "$RUN_ROOT/logs/start-and-monitor.console.log"
```

Nếu thành công, script in active PID và giữ server chạy.

Inspect ngay:

```bash
cat "$RUN_ROOT/server/startup-result.txt"
tail -200 "$RUN_ROOT/logs/server.log"
tail -20 "$RUN_ROOT/memory/memory-monitor.csv"
cat "$RUN_ROOT/memory/memory.events.after"
cat "$RUN_ROOT/memory/memory.peak.after" 2>/dev/null || true
```

Hard memory gates để PASS:

```text
server /ready = HTTP 200
oom delta      = 0
oom_kill delta = 0
both models report CPU
both models report requested dtype truthfully
final system MemAvailable >= 4 GiB
```

Không suy luận dual-model memory success chỉ vì process còn sống.

---

## 10. Local REST acceptance trước tunnel

Chạy smoke suite được cung cấp:

```bash
mkdir -p "$RUN_ROOT/smoke"
export SERVER_URL='http://127.0.0.1:8000'
export SMOKE_OUTPUT="$RUN_ROOT/smoke/local-smoke.json"
export SMOKE_TIMEOUT_SECONDS=1200
python scripts/smoke-http.py \
  2>&1 | tee "$RUN_ROOT/smoke/local-smoke.console.log"
```

Phải chứng minh:

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

Embedding còn phải advertise:

```text
public_vector_dtype=float32
dimension=2560
```

---

## 11. Compatibility check với existing Node/Qdrant notebook

Server chủ đích giữ canonical default query behavior cũ:

```text
Instruct: Retrieve the geographic entity that best answers the query
Query:<query>
```

Document vẫn raw. Vì vậy existing `knowledge_entities_qwen3_4b_text_v21` client có thể gọi `/v1/embeddings` với:

```json
{
  "input": "quốc gia Đông Nam Á sử dụng đồng baht",
  "input_type": "query"
}
```

Không gửi instruction khác khi query historical Qdrant collection này trừ khi chủ đích muốn embedding-space behavior khác.

Với retrieval application không liên quan, custom instruction được support:

```json
{
  "input": "query text",
  "input_type": "query",
  "instruction": "Given a web search query, retrieve relevant passages that answer the query"
}
```

Reranker cũng nhận bounded custom instruction.

---

## 12. Public exposure — chỉ sau local acceptance PASS

Giữ Uvicorn bind loopback:

```text
127.0.0.1:8000
```

Không restart lên `0.0.0.0` chỉ để tunnel access.

### 12.1 Tìm hoặc cài cloudflared

```bash
command -v cloudflared | tee "$RUN_ROOT/tunnel/cloudflared-path.txt" || true
cloudflared --version 2>&1 | tee "$RUN_ROOT/tunnel/cloudflared-version.txt" || true
```

Nếu thiếu và Kaggle Internet bật, cài official Linux AMD64 binary vào writable storage. Record URL, size, SHA256 và version. Không sửa model files.

Ví dụ:

```bash
CLOUDFLARED="$RUN_ROOT/tmp/cloudflared"
curl -fL --retry 3 \
  -o "$CLOUDFLARED" \
  https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64
chmod +x "$CLOUDFLARED"
sha256sum "$CLOUDFLARED" | tee "$RUN_ROOT/tunnel/cloudflared.sha256"
"$CLOUDFLARED" --version | tee "$RUN_ROOT/tunnel/cloudflared-version.txt"
```

### 12.2 Quick Tunnel cho development/demo

```bash
CLOUDFLARED_BIN="${CLOUDFLARED:-$(command -v cloudflared)}"
nohup "$CLOUDFLARED_BIN" tunnel \
  --no-autoupdate \
  --url http://127.0.0.1:8000 \
  > "$RUN_ROOT/tunnel/cloudflared.log" 2>&1 &
TUNNEL_PID=$!
printf '%s\n' "$TUNNEL_PID" > "$RUN_ROOT/tunnel/cloudflared.pid"
```

Đợi HTTPS URL:

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

Quick Tunnel là demo/development endpoint. Với hostname ổn định lâu dài, dùng named tunnel ở deployment phase sau.

### 12.3 Verify public boundary

Unauthenticated model access vẫn phải fail:

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

Chạy complete smoke remotely:

```bash
export SERVER_URL="$PUBLIC_URL"
export SMOKE_OUTPUT="$RUN_ROOT/smoke/public-smoke.json"
python scripts/smoke-http.py \
  2>&1 | tee "$RUN_ROOT/smoke/public-smoke.console.log"
```

Không đưa `DUAL_API_KEY` vào evidence ZIP, notebook screenshot/output, git commit hoặc public URL.

---

## 13. Ví dụ từ Kaggle/Colab notebook khác

Client notebook chỉ cần public URL và secret token:

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

Với Node/Qdrant project, intended flow:

```text
client query
  -> shared /v1/embeddings
  -> client-side Qdrant top-K
  -> shared /v1/rerank on top-K texts
  -> final top-N
```

Server này chủ đích không sở hữu Qdrant.

---

# 14. Autonomous troubleshooting policy

OpenCode CLI nên tiếp tục qua ordinary failures theo đúng thứ tự dưới đây. Mỗi branch phải archive failed log và memory evidence trước khi đổi configuration.

## 14.1 Không tìm thấy model

1. Chạy `find /kaggle/input -name config.json` và inspect tree.
2. Xác nhận expected user-owned model thực sự được attach.
3. Chạy `scripts/preflight.py` không explicit path.
4. Nếu có đúng một valid candidate mỗi role, dùng nó.
5. Nếu ambiguous, set explicit path và rerun preflight.
6. Nếu `qwen-qwen3-reranker-4b` thực sự thiếu, đây là **external-input gate**. Không download checkpoint 8 GB trong production runtime. Record Kaggle model slug cần thiết và chỉ dừng gate này.

## 14.2 `KeyError: 'qwen3'` hoặc unsupported model type

1. Capture `transformers.__version__`.
2. Yêu cầu `transformers >= 4.51.0,<5`.
3. Chỉ cài compatible Transformers 4.x version.
4. Không reinstall torch trừ khi có concrete ABI/import failure chứng minh cần thiết.
5. Rerun fast tests + preflight trước khi load weights lại.

## 14.3 Embedding FP16 load OOM

1. Archive `server.log`, `memory-monitor.csv`, `memory.events.*`, process list.
2. Verify không có heavy Python/Node/Qdrant/model process khác resident.
3. Chỉ kill unrelated/owned process và xác nhận memory quay lại.
4. Retry clean FP16 baseline một lần.
5. Nếu repeatable, dùng **fresh CPU notebook** để loại stale page-cache/process contamination.
6. Không chuyển sang runtime FP32 conversion.
7. Chỉ sau khi FP16 failure được chứng minh reproducible mới chạy **separate controlled BF16 candidate** vì source checkpoints là BF16. Giữ evidence thành run riêng, không overwrite FP16 result.

## 14.4 Embedding load được nhưng `SECOND_MODEL_MIN_AVAILABLE_GIB` chặn Reranker

Đây là safety success, không phải bug.

1. Record `MemAvailable`, cgroup current/peak, Embedding RSS.
2. Kiểm tra unrelated resident process.
3. Restart fresh notebook nếu có contamination.
4. Giữ threshold 10 GiB cho first qualification.
5. Không hạ chỉ để force Reranker load.
6. Nếu clean notebook vẫn <10 GiB, chạy separate BF16 candidate mô tả ở trên.
7. Chỉ đề xuất lower threshold sau khi measured Reranker load peak chứng minh safe margin; không implement policy âm thầm.

## 14.5 Reranker OOM khi Embedding đang resident

1. Archive toàn bộ memory evidence ngay.
2. Xác nhận `oom`/`oom_kill` deltas.
3. Reboot/fresh notebook trước retry nếu đã có OOM kill.
4. Retry `MAX_SEQ_LENGTH=512`, `RERANKER_MICROBATCH_SIZE=1`, warm-up single pair.
5. Giữ global inference concurrency 1.
6. Chỉ thử native BF16 như **separate candidate**, không phải unreported substitution.
7. Không thêm disk offload/device_map tricks trước khi chứng minh simpler native dtype candidates.
8. Nếu cả clean FP16 và BF16 runs OOM ở conservative baseline, classify dual-4B/30-GiB là `MEMORY_FEASIBILITY_FAIL` cùng evidence thay vì che kết quả.

## 14.6 FP16 CPU operator exception

1. Capture exact operator/stack trace và torch version.
2. Reproduce bằng một minimal embedding query hoặc một reranker pair.
3. Thử BF16 như controlled alternate vì hai source checkpoint đều BF16.
4. Giữ pooled embedding/logit post-processing ở FP32.
5. Không silently expand full model sang FP32.

## 14.7 Embedding norm không xấp xỉ 1.0

Required numerical sequence:

```text
model forward in FP16/BF16
-> last-token pooling
-> pooled.float()
-> F.normalize(..., p=2, dim=1) in FP32
-> public Float32[2560]
```

Không normalize trong BF16/FP16 rồi mới cast. Exact issue này đã từng được quan sát và sửa.

## 14.8 Reranker score có vẻ sai

Verify implementation không drift khỏi:

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

Không thay bằng arbitrary hidden-state cosine similarity.

## 14.9 Public endpoint chạy local nhưng tunnel fail

1. Giữ localhost service chạy và healthy local.
2. Kiểm tra Kaggle Internet setting/DNS.
3. Capture cloudflared version và log.
4. Chỉ restart tunnel process, không restart cả hai model 4B.
5. Giữ inference service bind loopback.
6. Nếu Quick Tunnel unavailable, local dual-model acceptance vẫn có thể PASS, nhưng classify `PUBLIC_TUNNEL=BLOCKED_EXTERNAL_NETWORK` và preserve evidence.
7. Không expose unauthenticated alternate port.

## 14.10 Queue trả HTTP 429

Đây là intentional backpressure. Không tăng heavy inference concurrency trước.

Client policy:

```text
retry with exponential backoff
or submit fewer concurrent requests
```

Chỉ benchmark concurrency 2 ở phase tương lai sau khi dual-model memory và latency được chứng minh.

---

# 15. Acceptance matrix

Tạo `$RUN_ROOT/evidence/acceptance-summary.md` với bảng này và measured values:

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

Cũng report:

```text
peak process RSS during startup (from CSV)
peak cgroup memory.current observed
kernel/cgroup memory.peak
steady process RSS after both models
startup duration
embedding inference latency
reranker 2-document latency
```

Không fabricate missing metrics.

---

## 16. Long-run stability smoke

Sau local/public functional acceptance, chạy conservative alternating workload. Chưa tạo parallel heavy inference.

Đề xuất 10 cycles:

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

CPU latency có thể cao; correctness/stability là mục tiêu đầu tiên của v0.1.0.

---

## 17. Thu thập review evidence

Quay lại source root và chạy:

```bash
cd "$APP"
export SERVER_URL='http://127.0.0.1:8000'
bash scripts/collect-evidence.sh \
  2>&1 | tee "$RUN_ROOT/logs/collect-evidence.log"
```

Thêm thủ công current acceptance summary và tunnel logs nếu chưa có.

Secret scan trước packaging. Capture grep output ngoài scanned tree rồi mới materialize result file để output file không tự nằm trong scan path và mọi scan state đều fail closed đúng cách:

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

Nếu tìm thấy secret, delete/redact offending evidence và rerun scan trước packaging. Không được bỏ qua scan result.

Collector tạo:

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

# 18. OpenCode CLI phải trả gì cho user

Trả tất cả mục sau, không chỉ “it works”:

1. final classification:
   ```text
   DUAL_MODEL_MEMORY_FEASIBILITY=PASS|FAIL
   LOCAL_REST=PASS|FAIL
   PUBLIC_TUNNEL=PASS|BLOCKED_EXTERNAL_NETWORK|FAIL
   ```
2. source Git HEAD sau mọi fix;
3. exact model paths đã dùng;
4. candidate dtype thực sự load;
5. pre-Reranker và final `MemAvailable`;
6. startup peak RSS/cgroup peak;
7. `oom` và `oom_kill` before/after/delta;
8. embedding dimension/norm/latency;
9. reranker sentinel score/rank/latency;
10. local/public endpoint URL (URL được phép; **không bao giờ trả API key trong artifact**);
11. evidence ZIP path + SHA-256;
12. mọi code change trong troubleshooting, mỗi change có reason và tests;
13. danh sách ngắn unresolved limitations.

Nếu code thay đổi, chạy lại **entire** fast suite và tạo Git commit trước khi trả evidence.

---

# 19. Expected limitations dù run PASS

PASS chứng minh một low-traffic shared CPU inference appliance hữu ích. Nó **không** chứng minh:

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

Đó là các qualification phase sau. Không optimize chúng trong initial residency experiment này.

---

# 20. Exact continuation nếu v0.1.0 PASS

Không tăng mọi limit ngay. Recommended next controlled phases:

```text
Phase A: benchmark FP16 vs native BF16 dual residency
Phase B: measure reranker top-K = 5/10/20 latency
Phase C: test MAX_CONCURRENT_INFERENCE=2 only if memory/CPU contention allows
Phase D: integrate the shared endpoint into nodejs-qdrant-bilingual-search
Phase E: stable named-tunnel deployment / another long-lived host if needed
```

Mỗi experiment chỉ đổi một biến và preserve v0.1.0 baseline.

---

## Kết thúc Runbook
