#!/usr/bin/env bash
set -Eeuo pipefail
set +x
umask 077
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

QDRANT_VERSION=1.18.3
QDRANT_COLLECTION=knowledge_entities_qwen3_4b_text_v21
QDRANT_SNAPSHOT_NAME=knowledge_entities_qwen3_4b_text_v21-20260827T013824Z.snapshot
QDRANT_SNAPSHOT_BYTES=283812352
QDRANT_SNAPSHOT_SHA256=71f12fe14ef51966069347290ad15302d389e488d7904dab6cf0cf190f43064f
RUN_ROOT="${PRODUCTION_DEMO_RUN_ROOT:-/kaggle/working/qwen3-hybrid-qdrant-production-demo}"
QDRANT_STORAGE_PATH="${QDRANT_STORAGE_PATH:-$RUN_ROOT/qdrant/storage}"
QDRANT_LOG="$RUN_ROOT/qdrant/qdrant.log"
QDRANT_PID_FILE="$RUN_ROOT/qdrant/qdrant.pid"
mkdir -p "$RUN_ROOT/qdrant" "$RUN_ROOT/evidence"

case "$QDRANT_STORAGE_PATH" in
  /kaggle/working/*) ;;
  *) echo "ERROR: live Qdrant storage must be under /kaggle/working: $QDRANT_STORAGE_PATH" >&2; exit 2 ;;
esac

if [[ -z "${QDRANT_BIN:-}" ]]; then
  setup_out="$(bash "$ROOT/scripts/setup-qdrant-production-demo.sh")"
  printf '%s\n' "$setup_out"
  QDRANT_BIN="$(printf '%s\n' "$setup_out" | sed -n 's/^QDRANT_BIN=//p' | tail -n1)"
fi
[[ -x "$QDRANT_BIN" ]] || { echo "ERROR: QDRANT_BIN missing" >&2; exit 2; }

if [[ -z "${QDRANT_BACKUP:-}" ]]; then
  locator_json="$(python "$ROOT/scripts/locate-canonical-qdrant-snapshot.py")"
  QDRANT_BACKUP="$(python -c 'import json,sys; print(json.load(sys.stdin)["path"])' <<<"$locator_json")"
fi
[[ -f "$QDRANT_BACKUP" ]] || { echo "ERROR: snapshot missing: $QDRANT_BACKUP" >&2; exit 2; }
actual_bytes="$(stat -c '%s' "$QDRANT_BACKUP")"
actual_sha="$(sha256sum "$QDRANT_BACKUP" | awk '{print $1}')"
[[ "$actual_bytes" == "$QDRANT_SNAPSHOT_BYTES" ]] || { echo "ERROR: snapshot byte-size mismatch" >&2; exit 2; }
[[ "$actual_sha" == "$QDRANT_SNAPSHOT_SHA256" ]] || { echo "ERROR: snapshot SHA-256 mismatch" >&2; exit 2; }

if curl -fsS --max-time 2 http://127.0.0.1:6333/ >/dev/null 2>&1; then
  echo "ERROR: port 6333 is already serving; refusing to kill an unowned process" >&2
  exit 2
fi
rm -rf "$QDRANT_STORAGE_PATH"
mkdir -p "$QDRANT_STORAGE_PATH"
export QDRANT__STORAGE__STORAGE_PATH="$QDRANT_STORAGE_PATH"
export QDRANT__SERVICE__HOST=127.0.0.1
export QDRANT__SERVICE__HTTP_PORT=6333
nohup "$QDRANT_BIN" >"$QDRANT_LOG" 2>&1 &
QDRANT_PID=$!
printf '%s\n' "$QDRANT_PID" > "$QDRANT_PID_FILE"

ready=0
for _ in $(seq 1 120); do
  if curl -fsS --max-time 3 http://127.0.0.1:6333/ > "$RUN_ROOT/evidence/qdrant-root.json"; then ready=1; break; fi
  kill -0 "$QDRANT_PID" 2>/dev/null || { tail -100 "$QDRANT_LOG" >&2; exit 1; }
  sleep 1
done
[[ "$ready" == 1 ]] || { echo "ERROR: Qdrant readiness timeout" >&2; exit 1; }

curl -fSs --connect-timeout 10 --max-time 1800 -X POST \
  "http://127.0.0.1:6333/collections/${QDRANT_COLLECTION}/snapshots/upload?wait=true&priority=snapshot" \
  -F "snapshot=@${QDRANT_BACKUP}" \
  > "$RUN_ROOT/evidence/qdrant-snapshot-upload.json"

collection_ok=0
for _ in $(seq 1 300); do
  if curl -fsS --max-time 5 "http://127.0.0.1:6333/collections/${QDRANT_COLLECTION}" \
      > "$RUN_ROOT/evidence/qdrant-collection.json"; then
    if python - "$RUN_ROOT/evidence/qdrant-collection.json" <<'PY'
import json, sys
body=json.load(open(sys.argv[1]))["result"]
vectors=body["config"]["params"]["vectors"]
ok=(
    body.get("status") == "green" and
    body.get("points_count") == 20000 and
    body.get("indexed_vectors_count") == 20000 and
    vectors.get("size") == 2560 and
    vectors.get("distance") == "Cosine"
)
raise SystemExit(0 if ok else 1)
PY
    then collection_ok=1; break; fi
  fi
  kill -0 "$QDRANT_PID" 2>/dev/null || break
  sleep 1
done
[[ "$collection_ok" == 1 ]] || { echo "ERROR: restored collection invariants failed" >&2; exit 1; }

echo "QDRANT_RESTORE=PASS"
echo "QDRANT_COLLECTION=$QDRANT_COLLECTION"
echo "QDRANT_URL=http://127.0.0.1:6333"
echo "QDRANT_PID=$QDRANT_PID"
