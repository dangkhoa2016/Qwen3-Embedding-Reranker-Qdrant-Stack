#!/usr/bin/env bash
set -euo pipefail
RUN_ROOT="${RUN_ROOT:?RUN_ROOT must point to the active run}"
PID_FILE="$RUN_ROOT/server/server.pid"
test -f "$PID_FILE"
PID="$(cat "$PID_FILE")"
if kill -0 "$PID" 2>/dev/null; then
  kill "$PID"
  for _ in $(seq 1 30); do
    kill -0 "$PID" 2>/dev/null || exit 0
    sleep 1
  done
  kill -KILL "$PID" 2>/dev/null || true
fi
