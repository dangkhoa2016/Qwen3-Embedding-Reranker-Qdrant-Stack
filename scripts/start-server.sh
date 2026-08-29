#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

: "${SERVER_HOST:=127.0.0.1}"
: "${SERVER_PORT:=8000}"
: "${MAX_CONCURRENT_INFERENCE:=1}"
: "${MODEL_DTYPE:=float16}"
: "${MAX_SEQ_LENGTH:=512}"
: "${EMBEDDING_MICROBATCH_SIZE:=1}"
: "${RERANKER_MICROBATCH_SIZE:=1}"
: "${ALLOW_REMOTE_MODEL_DOWNLOAD:=0}"

if [[ "$MAX_CONCURRENT_INFERENCE" != "1" ]]; then
  echo "ERROR: MAX_CONCURRENT_INFERENCE must remain 1 for the CPU baseline" >&2
  exit 64
fi
if [[ -z "${DUAL_API_KEY:-}" && "${ALLOW_INSECURE_NO_AUTH:-0}" != "1" ]]; then
  echo "ERROR: set DUAL_API_KEY, or explicitly set ALLOW_INSECURE_NO_AUTH=1 for localhost-only testing" >&2
  exit 64
fi

export HF_HUB_OFFLINE="${HF_HUB_OFFLINE:-1}"
export TRANSFORMERS_OFFLINE="${TRANSFORMERS_OFFLINE:-1}"
export TOKENIZERS_PARALLELISM="${TOKENIZERS_PARALLELISM:-false}"
export MAX_CONCURRENT_INFERENCE MODEL_DTYPE MAX_SEQ_LENGTH
export EMBEDDING_MICROBATCH_SIZE RERANKER_MICROBATCH_SIZE ALLOW_REMOTE_MODEL_DOWNLOAD
export PYTHONPATH="$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

# Do not increase workers: every worker could materialize another ~4B+4B model pair.
exec python -m uvicorn qwen_dual_server.main:app \
  --app-dir "$ROOT/src" \
  --host "$SERVER_HOST" \
  --port "$SERVER_PORT" \
  --workers 1 \
  --no-access-log
