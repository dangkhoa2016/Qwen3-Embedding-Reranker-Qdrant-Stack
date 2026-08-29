#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_ROOT="${RUN_ROOT:-/kaggle/working/qwen3-dual-4b-run-$(date -u +%Y%m%dT%H%M%SZ)}"
STARTUP_TIMEOUT_SECONDS="${STARTUP_TIMEOUT_SECONDS:-1200}"
SERVER_HOST="${SERVER_HOST:-127.0.0.1}"
SERVER_PORT="${SERVER_PORT:-8000}"
mkdir -p "$RUN_ROOT"/{logs,memory,server,evidence}

EVENTS=/sys/fs/cgroup/memory.events
PEAK=/sys/fs/cgroup/memory.peak
CURRENT=/sys/fs/cgroup/memory.current
printf '%s\n' "$RUN_ROOT" > "$RUN_ROOT/RUN_ROOT.txt"
cat "$EVENTS" 2>/dev/null > "$RUN_ROOT/memory/memory.events.before" || true
cat "$PEAK" 2>/dev/null > "$RUN_ROOT/memory/memory.peak.before" || true

nohup bash "$ROOT/scripts/start-server.sh" > "$RUN_ROOT/logs/server.log" 2>&1 &
PID=$!
printf '%s\n' "$PID" | tee "$RUN_ROOT/server/server.pid"
printf 'timestamp_utc,pid,rss_kib,mem_available_kib,cgroup_current_bytes,cgroup_peak_bytes,oom,oom_kill\n' > "$RUN_ROOT/memory/memory-monitor.csv"

before_oom="$(awk '$1=="oom"{print $2}' "$RUN_ROOT/memory/memory.events.before" 2>/dev/null || echo 0)"
before_kill="$(awk '$1=="oom_kill"{print $2}' "$RUN_ROOT/memory/memory.events.before" 2>/dev/null || echo 0)"
ready=0
start_epoch=$(date +%s)

while true; do
  now=$(date +%s)
  if (( now - start_epoch > STARTUP_TIMEOUT_SECONDS )); then
    echo "ERROR: startup timed out after ${STARTUP_TIMEOUT_SECONDS}s" | tee "$RUN_ROOT/server/startup-result.txt"
    break
  fi
  if ! kill -0 "$PID" 2>/dev/null; then
    echo "ERROR: server process exited before readiness" | tee "$RUN_ROOT/server/startup-result.txt"
    break
  fi

  rss=$(awk '/VmRSS:/{print $2}' "/proc/$PID/status" 2>/dev/null || echo 0)
  avail=$(awk '/MemAvailable:/{print $2}' /proc/meminfo 2>/dev/null || echo 0)
  cur=$(cat "$CURRENT" 2>/dev/null || echo 0)
  peak=$(cat "$PEAK" 2>/dev/null || echo 0)
  oom=$(awk '$1=="oom"{print $2}' "$EVENTS" 2>/dev/null || echo 0)
  kill=$(awk '$1=="oom_kill"{print $2}' "$EVENTS" 2>/dev/null || echo 0)
  printf '%s,%s,%s,%s,%s,%s,%s,%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$PID" "$rss" "$avail" "$cur" "$peak" "$oom" "$kill" >> "$RUN_ROOT/memory/memory-monitor.csv"

  if (( oom > before_oom || kill > before_kill )); then
    echo "ERROR: cgroup OOM event increased during startup: oom ${before_oom}->${oom}, oom_kill ${before_kill}->${kill}" | tee "$RUN_ROOT/server/startup-result.txt"
    break
  fi

  if curl -fsS --max-time 3 "http://${SERVER_HOST}:${SERVER_PORT}/ready" > "$RUN_ROOT/server/ready.json" 2>/dev/null; then
    ready=1
    echo "PASS: dual-model server is ready" | tee "$RUN_ROOT/server/startup-result.txt"
    break
  fi
  sleep 1
done

cat "$EVENTS" 2>/dev/null > "$RUN_ROOT/memory/memory.events.after" || true
cat "$PEAK" 2>/dev/null > "$RUN_ROOT/memory/memory.peak.after" || true

if [[ "$ready" != "1" ]]; then
  tail -200 "$RUN_ROOT/logs/server.log" || true
  kill "$PID" 2>/dev/null || true
  exit 1
fi

echo "RUN_ROOT=$RUN_ROOT"
echo "PID=$PID"
