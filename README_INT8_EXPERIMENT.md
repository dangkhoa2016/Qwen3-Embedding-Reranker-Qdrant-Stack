# Qwen3 Dual-4B CPU — Transformers + TorchAO INT8 experiment
> 🌐 Language / Ngôn ngữ: **English** | [Tiếng Việt](README_INT8_EXPERIMENT.vi.md)

This is an **experimental copy** of frozen `qwen3-dual-4b-cpu-rest-server v0.1.1`.
The canonical v0.1.1 release/history/tag are not modified.

## Goal

Compare the already-measured FP16 baseline against two CPU INT8 candidates while
preserving the same tokenizer, embedding pooling/normalization, reranker yes/no
scoring protocol, max sequence length, microbatch size, and bilingual benchmark corpus.

Candidates:

- `T1-int8-a8w8`: `Int8DynamicActivationInt8WeightConfig` (A8W8)
- `T2-int8-weight-only`: `Int8WeightOnlyConfig` (A16W8 / weight-only)

Frozen FP16 Phase-E references (not rerun):

- embedding: `7670.984 ms`
- reranker K=2: `61569.442 ms`
- reranker K=5: `158116.8175 ms`
- reranker K=10: `315951.01749999996 ms`
- peak observed process RSS: `19.665172576904297 GiB`

Promotion gate:

- semantic/correctness gates PASS;
- OOM and OOM-kill deltas remain zero;
- K=2 reranker speedup is at least `1.5x`;
- observed peak process RSS is reduced by at least `25%` versus frozen FP16.

## Kaggle inputs

Attach the same local Transformers model variations used by v0.1.1. Defaults:

```text
/kaggle/input/models/dangkhoa2016/qwen-qwen3-embedding-4b/transformers/default/1
/kaggle/input/models/dangkhoa2016/qwen-qwen3-reranker-4b/transformers/default/1
```

If Kaggle mounts them elsewhere, export `EMBEDDING_MODEL_PATH` and
`RERANKER_MODEL_PATH` before running the campaign.

## 1. Extract

```bash
cd /kaggle/working
unzip -q qwen3-dual-4b-cpu-int8-torchao-experiment-v0.1.0.zip
cd qwen3-dual-4b-cpu-int8-torchao-experiment-v0.1.0
```

## 2. Install INT8 support without replacing PyTorch

Internet must be enabled for this setup step unless torchao is already available.

```bash
bash scripts/setup-int8.sh 2>&1 | tee setup-int8.log
```

The setup script installs `torchao==0.18.0` from the PyTorch CPU index with
`--no-deps`, then proves the preinstalled `torch` version did not change.

## 3. Preflight

```bash
export PYTHONPATH="$PWD/src"
python scripts/preflight-int8.py | tee preflight-int8.log
```

This does **not** load the 4B models. It checks model discovery and TorchAO config
construction.

## 4. Quick feasibility campaign

Runs both INT8 candidates with K=2, one unreported warm-up plus one measured run.

```bash
bash scripts/run-int8-campaign.sh --quick 2>&1 | tee int8-quick.log
```

Use this first. It minimizes wasted Kaggle CPU time if TorchAO gives little benefit.

## 5. Full qualification campaign

Only after quick mode looks promising:

```bash
bash scripts/run-int8-campaign.sh --full 2>&1 | tee int8-full.log
```

Full mode measures K=2/5/10 with one unreported warm-up and two measured repetitions
per K and two measured embedding repetitions.

## Manual server mode

A8W8:

```bash
export DUAL_API_KEY="$(openssl rand -hex 32)"
export QUANTIZATION_MODE=int8-a8w8
export TORCH_NUM_THREADS=2
bash scripts/start-int8-server.sh
```

Weight-only:

```bash
export DUAL_API_KEY="$(openssl rand -hex 32)"
export QUANTIZATION_MODE=int8-weight-only
export TORCH_NUM_THREADS=2
bash scripts/start-int8-server.sh
```

The public API remains:

```text
GET  /health
GET  /ready
GET  /v1/models
GET  /v1/stats
POST /v1/embeddings
POST /v1/rerank
```

## Evidence generated per candidate

```text
candidates/<candidate>/
├── benchmark/benchmark.json
├── evidence/candidate-config.json
├── evidence/candidate-summary.json
├── evidence/models.json
├── evidence/perf-runtime.json
├── evidence/stats-before.json
├── evidence/stats-after.json
├── memory/memory.events.before
├── memory/memory.events.after
├── memory/benchmark-monitor.csv
└── logs/
```

The campaign additionally produces:

```text
summary/int8-campaign-summary.json
package/qwen3-dual-4b-cpu-int8-torchao-results-<UTC>.zip
package/<same>.zip.sha256
package/unzip-test.log
```

## Important interpretation

TorchAO INT8 support in Transformers is officially documented for CPU, but this
package intentionally treats Qwen3-Embedding-4B and Qwen3-Reranker-4B compatibility
as something to **prove**, not assume. The model loader fails closed unless it can
observe TorchAO quantized weight tensor modules after load.

Do not change the canonical v0.1.1 tag/history based on this experiment. If both
INT8 candidates fail the promotion gate, the next intended branch is dual-4B GGUF /
llama.cpp feasibility rather than further FP16 tuning.
