#!/usr/bin/env bash
set -Eeuo pipefail
set +x
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODE="${1:---quick}"
case "$MODE" in
  --quick) K_VALUES='2'; EMBED_REPS=1; RERANK_REPS=1 ;;
  --full)  K_VALUES='2,5,10'; EMBED_REPS=2; RERANK_REPS=2 ;;
  *) echo 'usage: bash scripts/run-int8-campaign.sh [--quick|--full]' >&2; exit 64 ;;
esac

export APP="$ROOT"
TS="$(date -u +%Y%m%dT%H%M%SZ)"
export CAMPAIGN_ROOT="/kaggle/working/${TS}-qwen3-embedding-reranker-qdrant-stack-int8-torchao"
mkdir -p "$CAMPAIGN_ROOT"/{tools,corpus,candidates,summary,package}
cp "$ROOT"/tools/{int8_perf_app.py,perf_client.py,monitor_candidate.sh,summarize_int8_candidate.py,run_int8_candidate.sh} "$CAMPAIGN_ROOT/tools/"
cp "$ROOT/corpus/reranker-candidates.json" "$CAMPAIGN_ROOT/corpus/"
sha256sum "$CAMPAIGN_ROOT/corpus/reranker-candidates.json" > "$CAMPAIGN_ROOT/corpus/reranker-candidates.json.sha256"

PYTHONPATH="$ROOT/src" python "$ROOT/scripts/preflight-int8.py" | tee "$CAMPAIGN_ROOT/preflight.log"

"$CAMPAIGN_ROOT/tools/run_int8_candidate.sh" T1-int8-a8w8 int8-a8w8 "$K_VALUES" "$EMBED_REPS" "$RERANK_REPS"
"$CAMPAIGN_ROOT/tools/run_int8_candidate.sh" T2-int8-weight-only int8-weight-only "$K_VALUES" "$EMBED_REPS" "$RERANK_REPS"

PYTHONPATH="$ROOT/src" python - "$CAMPAIGN_ROOT" <<'PY'
import json,sys
from pathlib import Path
root=Path(sys.argv[1]); rows=[]
for p in sorted((root/'candidates').glob('*/evidence/candidate-summary.json')):
    rows.append(json.loads(p.read_text()))
out={
  'campaign':'QWEN3_STACK_TRANSFORMERS_TORCHAO_INT8',
  'frozen_fp16_reference':{
    'embedding_ms':7670.984,
    'reranker_ms':{'2':61569.442,'5':158116.8175,'10':315951.01749999996},
  },
  'candidates':rows,
}
(root/'summary'/'int8-campaign-summary.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
for r in rows:
    print(r['candidate_id'], r['promotion_classification'], r['speedups_vs_frozen_fp16'])
PY

FINAL="qwen3-embedding-reranker-qdrant-stack-int8-torchao-results-${TS}.zip"
cd "$CAMPAIGN_ROOT"
zip -qry "package/$FINAL" candidates summary preflight.log corpus
cd package
sha256sum "$FINAL" > "$FINAL.sha256"
unzip -t "$FINAL" > unzip-test.log
grep -F 'No errors detected' unzip-test.log
sha256sum -c "$FINAL.sha256"
printf '%s\n' "$CAMPAIGN_ROOT" | tee "$ROOT/LAST_INT8_CAMPAIGN_ROOT.txt"
echo "INT8_CAMPAIGN_COMPLETE=$CAMPAIGN_ROOT"
echo "RESULT_ZIP=$CAMPAIGN_ROOT/package/$FINAL"
