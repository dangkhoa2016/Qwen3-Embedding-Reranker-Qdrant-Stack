#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_ROOT="${RUN_ROOT:?RUN_ROOT must point to the active acceptance run}"
SERVER_HOST="${SERVER_HOST:-127.0.0.1}"
SERVER_PORT="${SERVER_PORT:-8000}"
mkdir -p "$RUN_ROOT"/{env,server,evidence,package}

{
  date -u +%Y-%m-%dT%H:%M:%SZ
  uname -a
  cat /etc/os-release 2>/dev/null || true
  lscpu 2>/dev/null || true
  free -h 2>/dev/null || true
  python --version
  python -m pip --version
  python - <<'PY'
try:
 import torch
 print('torch=', torch.__version__)
 print('cuda_available=', torch.cuda.is_available())
except Exception as exc:
 print('torch_error=', repr(exc))
PY
} > "$RUN_ROOT/env/environment.log" 2>&1

python -m pip freeze | sort > "$RUN_ROOT/env/pip-freeze.txt"
cat /proc/meminfo > "$RUN_ROOT/evidence/proc-meminfo.txt" 2>/dev/null || true
cat /sys/fs/cgroup/memory.events > "$RUN_ROOT/evidence/memory.events" 2>/dev/null || true
cat /sys/fs/cgroup/memory.current > "$RUN_ROOT/evidence/memory.current" 2>/dev/null || true
cat /sys/fs/cgroup/memory.peak > "$RUN_ROOT/evidence/memory.peak" 2>/dev/null || true
cat /sys/fs/cgroup/memory.max > "$RUN_ROOT/evidence/memory.max" 2>/dev/null || true
ps -eo pid,ppid,rss,%cpu,%mem,etime,cmd --sort=-rss > "$RUN_ROOT/evidence/processes.txt" 2>/dev/null || true

# Never persist the API secret. Record only whether it was configured.
{
  echo "DUAL_API_KEY=$([[ -n "${DUAL_API_KEY:-}" ]] && echo REDACTED || echo NOT_SET)"
  for name in MODEL_DTYPE MAX_SEQ_LENGTH EMBEDDING_MICROBATCH_SIZE RERANKER_MICROBATCH_SIZE MAX_CONCURRENT_INFERENCE SECOND_MODEL_MIN_AVAILABLE_GIB FINAL_MIN_AVAILABLE_GIB ALLOW_REMOTE_MODEL_DOWNLOAD EMBEDDING_MODEL_PATH RERANKER_MODEL_PATH; do
    printf '%s=%s\n' "$name" "${!name:-}"
  done
} > "$RUN_ROOT/env/runtime-config-sanitized.txt"

curl -sS --max-time 5 "http://${SERVER_HOST}:${SERVER_PORT}/health" > "$RUN_ROOT/server/health.json" || true
curl -sS --max-time 10 "http://${SERVER_HOST}:${SERVER_PORT}/ready" > "$RUN_ROOT/server/ready-final.json" || true
if [[ -n "${DUAL_API_KEY:-}" ]]; then
  curl -sS --max-time 10 -H "Authorization: Bearer ${DUAL_API_KEY}" "http://${SERVER_HOST}:${SERVER_PORT}/v1/models" > "$RUN_ROOT/server/models.json" || true
  curl -sS --max-time 10 -H "Authorization: Bearer ${DUAL_API_KEY}" "http://${SERVER_HOST}:${SERVER_PORT}/v1/stats" > "$RUN_ROOT/server/stats.json" || true
fi

if git -C "$ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git -C "$ROOT" status --short --branch > "$RUN_ROOT/evidence/git-status.txt"
  git -C "$ROOT" log -1 --decorate --oneline > "$RUN_ROOT/evidence/git-head.txt"
fi
find "$ROOT" -maxdepth 4 -type f -not -path '*/.git/*' -printf '%p\t%s\n' | sort > "$RUN_ROOT/evidence/source-tree.txt"

OUT="$RUN_ROOT/package/qwen3-dual-4b-cpu-evidence-$(date -u +%Y%m%dT%H%M%SZ).zip"
python - "$RUN_ROOT" "$OUT" <<'PY'
import os, sys, zipfile
root, out = sys.argv[1:]
with zipfile.ZipFile(out, 'w', compression=zipfile.ZIP_DEFLATED) as z:
    for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d != 'package']
        for f in files:
            p=os.path.join(base,f)
            z.write(p, os.path.relpath(p, root))
print(out)
PY
sha256sum "$OUT" | tee "$OUT.sha256"
