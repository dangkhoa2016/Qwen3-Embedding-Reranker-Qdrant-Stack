#!/usr/bin/env bash
set -Eeuo pipefail
set +x

CANDIDATE_ID="${1:?candidate id}"
QUANT_MODE="${2:?quantization mode}"
K_VALUES="${3:-2,5,10}"
EMBED_REPS="${4:-2}"
RERANK_REPS="${5:-2}"

: "${CAMPAIGN_ROOT:?}"
: "${APP:?}"

ROOT="$CAMPAIGN_ROOT/candidates/$CANDIDATE_ID"
test ! -e "$ROOT"
mkdir -p "$ROOT"/{logs,memory,server,benchmark,evidence,tmp}
PID=''; MONITOR_PID=''; SECRET_ENV=''; STOP_FILE="$ROOT/tmp/stop-monitor"

cleanup() {
  set +e
  if [[ -n "${MONITOR_PID:-}" ]]; then touch "$STOP_FILE" 2>/dev/null || true; wait "$MONITOR_PID" 2>/dev/null || true; fi
  if [[ -n "${PID:-}" ]] && kill -0 "$PID" 2>/dev/null; then
    kill "$PID" 2>/dev/null || true
    for _ in $(seq 1 30); do kill -0 "$PID" 2>/dev/null || break; sleep 1; done
    kill -KILL "$PID" 2>/dev/null || true; wait "$PID" 2>/dev/null || true
  fi
  unset DUAL_API_KEY 2>/dev/null || true
  [[ -n "${SECRET_ENV:-}" ]] && rm -f "$SECRET_ENV" 2>/dev/null || true
  set -e
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

if pgrep -af '[q]wen_dual_server|[i]nt8_perf_app:app' > "$ROOT/evidence/processes-before.txt"; then
  echo 'BLOCKED_STALE_QWEN_SERVER' >&2
  exit 31
fi

case "$QUANT_MODE" in int8-a8w8|int8-weight-only) ;; *) echo "invalid quantization mode: $QUANT_MODE" >&2; exit 32;; esac

SECRET_ENV="/tmp/qwen3-stack-int8-${CANDIDATE_ID}-$$.env"
umask 077
KEY="$(openssl rand -hex 32)"; test "${#KEY}" -eq 64
printf 'export DUAL_API_KEY=%q\n' "$KEY" > "$SECRET_ENV"; chmod 600 "$SECRET_ENV"; unset KEY
source "$SECRET_ENV"

export QUANTIZATION_MODE="$QUANT_MODE"
export ALLOW_INSECURE_NO_AUTH=0 ALLOW_REMOTE_MODEL_DOWNLOAD=0
export MODEL_DTYPE=float16 MAX_SEQ_LENGTH=512
export EMBEDDING_MICROBATCH_SIZE=1 RERANKER_MICROBATCH_SIZE=1
export MAX_CONCURRENT_INFERENCE=1 MAX_QUEUE_WAITERS=32 MAX_EMBEDDING_ITEMS=32 MAX_RERANK_DOCUMENTS=20
export SECOND_MODEL_MIN_AVAILABLE_GIB="${SECOND_MODEL_MIN_AVAILABLE_GIB:-10}"
export FINAL_MIN_AVAILABLE_GIB="${FINAL_MIN_AVAILABLE_GIB:-4}"
export TORCH_NUM_THREADS="${TORCH_NUM_THREADS:-2}" TORCH_NUM_INTEROP_THREADS=1
export WARMUP_ENABLED=1 LOAD_MODELS_ON_STARTUP=1
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false
export EMBEDDING_MODEL_PATH="${EMBEDDING_MODEL_PATH:-/kaggle/input/models/dangkhoa2016/qwen-qwen3-embedding-4b/transformers/default/1}"
export RERANKER_MODEL_PATH="${RERANKER_MODEL_PATH:-/kaggle/input/models/dangkhoa2016/qwen-qwen3-reranker-4b/transformers/default/1}"
export PYTHONPATH="$APP/src:$CAMPAIGN_ROOT/tools"

python - "$ROOT" "$CANDIDATE_ID" "$QUANT_MODE" "$K_VALUES" "$EMBED_REPS" "$RERANK_REPS" "${TORCH_NUM_THREADS:-2}" <<'PY'
import json, sys
from pathlib import Path
root=Path(sys.argv[1])
obj={"candidate_id":sys.argv[2],"quantization_mode":sys.argv[3],"k_values":sys.argv[4],
     "embedding_reps":int(sys.argv[5]),"rerank_reps":int(sys.argv[6]),"threads":int(sys.argv[7]),
     "interop_threads":1,"reranker_microbatch":1,"embedding_microbatch":1,
     "max_seq_length":512,"startup_seconds":None}
(root/'evidence'/'candidate-config.json').write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n')
PY

cat /sys/fs/cgroup/memory.events > "$ROOT/memory/memory.events.before"
free -h > "$ROOT/memory/free-before.txt"
cat /proc/loadavg > "$ROOT/evidence/loadavg-before.txt"
START_EPOCH="$(date +%s)"

nohup python -m uvicorn int8_perf_app:app --app-dir "$CAMPAIGN_ROOT/tools" --host 127.0.0.1 --port 8000 --workers 1 --no-access-log > "$ROOT/logs/server.log" 2>&1 &
PID=$!; echo "$PID" > "$ROOT/server/server.pid"

READY=0
for _ in $(seq 1 1200); do
  if ! kill -0 "$PID" 2>/dev/null; then break; fi
  oom_before="$(awk '$1=="oom"{print $2}' "$ROOT/memory/memory.events.before")"
  kill_before="$(awk '$1=="oom_kill"{print $2}' "$ROOT/memory/memory.events.before")"
  oom_now="$(awk '$1=="oom"{print $2}' /sys/fs/cgroup/memory.events)"
  kill_now="$(awk '$1=="oom_kill"{print $2}' /sys/fs/cgroup/memory.events)"
  if (( oom_now > oom_before || kill_now > kill_before )); then break; fi
  if curl -fsS --max-time 3 http://127.0.0.1:8000/ready > "$ROOT/server/ready.json" 2>/dev/null; then READY=1; break; fi
  sleep 1
done
STARTUP_SECONDS="$(( $(date +%s) - START_EPOCH ))"
python - "$ROOT/evidence/candidate-config.json" "$STARTUP_SECONDS" <<'PY'
import json,sys
from pathlib import Path
p=Path(sys.argv[1]); x=json.loads(p.read_text()); x['startup_seconds']=int(sys.argv[2]); p.write_text(json.dumps(x,indent=2,sort_keys=True)+'\n')
PY

if [[ "$READY" != 1 ]]; then
  cat /sys/fs/cgroup/memory.events > "$ROOT/memory/memory.events.after"
  tail -300 "$ROOT/logs/server.log" > "$ROOT/evidence/server-tail.txt" || true
  echo "CANDIDATE_LOAD_FAIL=$CANDIDATE_ID" >&2
  exit 41
fi

python - "$ROOT" <<'PY'
import json,os,sys,urllib.request
from pathlib import Path
root=Path(sys.argv[1]); key=os.environ['DUAL_API_KEY']
def get(path):
    req=urllib.request.Request('http://127.0.0.1:8000'+path,headers={'Authorization':f'Bearer {key}'})
    with urllib.request.urlopen(req,timeout=30) as r:return json.loads(r.read())
models=get('/v1/models'); runtime=get('/perf/runtime'); stats=get('/v1/stats')
assert len(models['data'])==2
assert all(x['loaded'] is True for x in models['data'])
assert all(x['device']=='cpu' for x in models['data'])
assert all(x['quantization_mode']==os.environ['QUANTIZATION_MODE'] for x in models['data'])
assert all((x.get('load_report') or {}).get('quantized_weight_modules',0)>0 for x in models['data'])
assert runtime['quantization_mode']==os.environ['QUANTIZATION_MODE']
assert runtime['torch_num_threads_effective']==int(os.environ['TORCH_NUM_THREADS'])
assert runtime['torch_num_interop_threads_effective']==1
(root/'evidence'/'models.json').write_text(json.dumps(models,indent=2,sort_keys=True)+'\n')
(root/'evidence'/'perf-runtime.json').write_text(json.dumps(runtime,indent=2,sort_keys=True)+'\n')
(root/'evidence'/'stats-before.json').write_text(json.dumps(stats,indent=2,sort_keys=True)+'\n')
PY

rm -f "$STOP_FILE"
"$CAMPAIGN_ROOT/tools/monitor_candidate.sh" "$PID" "$ROOT/memory/benchmark-monitor.csv" "$STOP_FILE" > "$ROOT/logs/monitor.log" 2>&1 &
MONITOR_PID=$!

set +e
python "$CAMPAIGN_ROOT/tools/perf_client.py" --corpus "$CAMPAIGN_ROOT/corpus/reranker-candidates.json" --out "$ROOT/benchmark/benchmark.json" --embedding-reps "$EMBED_REPS" --rerank-reps "$RERANK_REPS" --k "$K_VALUES" > "$ROOT/logs/benchmark-client.log" 2>&1
BENCH_RC=$?
set -e
touch "$STOP_FILE"; wait "$MONITOR_PID" || true; MONITOR_PID=''
cat /sys/fs/cgroup/memory.events > "$ROOT/memory/memory.events.after"
free -h > "$ROOT/memory/free-after.txt"
tail -300 "$ROOT/logs/server.log" > "$ROOT/evidence/server-tail.txt" || true
if [[ "$BENCH_RC" -ne 0 ]]; then echo "CANDIDATE_BENCHMARK_FAIL=$CANDIDATE_ID rc=$BENCH_RC" >&2; exit 42; fi

python - "$ROOT/evidence/stats-after.json" <<'PY'
import json,os,sys,urllib.request
req=urllib.request.Request('http://127.0.0.1:8000/v1/stats',headers={'Authorization':f"Bearer {os.environ['DUAL_API_KEY']}"})
with urllib.request.urlopen(req,timeout=30) as r: obj=json.loads(r.read())
open(sys.argv[1],'w').write(json.dumps(obj,indent=2,sort_keys=True)+'\n')
PY

python "$CAMPAIGN_ROOT/tools/summarize_int8_candidate.py" "$ROOT" | tee "$ROOT/logs/summarizer.log"

TMP_SCAN="$(mktemp)"
set +e
grep -R --binary-files=without-match --line-number --fixed-string "$DUAL_API_KEY" "$ROOT" --exclude='*.zip' --exclude='*.sha256' > "$TMP_SCAN"
SECRET_RC=$?
set -e
if [[ "$SECRET_RC" -ne 1 ]]; then cp "$TMP_SCAN" "$ROOT/evidence/secret-scan.txt" 2>/dev/null || true; rm -f "$TMP_SCAN"; echo "SECRET_SCAN_FAIL=$CANDIDATE_ID" >&2; exit 51; fi
: > "$ROOT/evidence/secret-scan.txt"; echo 'PASS: exact API key absent from candidate tree' > "$ROOT/evidence/secret-scan-result.txt"; rm -f "$TMP_SCAN"

cleanup; trap - EXIT INT TERM; PID=''; SECRET_ENV=''
echo "CANDIDATE_COMPLETE=$CANDIDATE_ID"
