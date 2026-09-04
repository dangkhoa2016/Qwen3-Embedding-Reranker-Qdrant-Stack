# Qwen3 Dual-4B CPU — Thử nghiệm Transformers + TorchAO INT8
> 🌐 Language / Ngôn ngữ: [English](README_INT8_EXPERIMENT.md) | **Tiếng Việt**

Đây là **bản copy thử nghiệm** của frozen `qwen3-dual-4b-cpu-rest-server v0.1.1`.
Canonical v0.1.1 release/history/tag không bị thay đổi.

## Mục tiêu

So sánh FP16 baseline đã đo với hai CPU INT8 candidate trong khi giữ nguyên tokenizer, embedding pooling/normalization, reranker yes/no scoring protocol, max sequence length, microbatch size và bilingual benchmark corpus.

Candidates:

- `T1-int8-a8w8`: `Int8DynamicActivationInt8WeightConfig` (A8W8)
- `T2-int8-weight-only`: `Int8WeightOnlyConfig` (A16W8 / weight-only)

Frozen FP16 Phase-E references (không chạy lại):

- embedding: `7670.984 ms`
- reranker K=2: `61569.442 ms`
- reranker K=5: `158116.8175 ms`
- reranker K=10: `315951.01749999996 ms`
- peak observed process RSS: `19.665172576904297 GiB`

Promotion gate:

- semantic/correctness gates PASS;
- OOM và OOM-kill deltas vẫn zero;
- K=2 reranker speedup tối thiểu `1.5x`;
- observed peak process RSS giảm tối thiểu `25%` so với frozen FP16.

## Kaggle inputs

Attach cùng local Transformers model variations đã dùng bởi v0.1.1. Defaults:

```text
/kaggle/input/models/dangkhoa2016/qwen-qwen3-embedding-4b/transformers/default/1
/kaggle/input/models/dangkhoa2016/qwen-qwen3-reranker-4b/transformers/default/1
```

Nếu Kaggle mount ở vị trí khác, export `EMBEDDING_MODEL_PATH` và `RERANKER_MODEL_PATH` trước khi chạy campaign.

## 1. Extract

```bash
cd /kaggle/working
unzip -q qwen3-dual-4b-cpu-int8-torchao-experiment-v0.1.0.zip
cd qwen3-dual-4b-cpu-int8-torchao-experiment-v0.1.0
```

## 2. Cài INT8 support mà không thay PyTorch

Internet phải bật ở bước setup này trừ khi torchao đã có sẵn.

```bash
bash scripts/setup-int8.sh 2>&1 | tee setup-int8.log
```

Setup script cài `torchao==0.18.0` từ PyTorch CPU index với `--no-deps`, sau đó chứng minh preinstalled `torch` version không thay đổi.

## 3. Preflight

```bash
export PYTHONPATH="$PWD/src"
python scripts/preflight-int8.py | tee preflight-int8.log
```

Bước này **không** load model 4B. Nó kiểm tra model discovery và TorchAO config construction.

## 4. Quick feasibility campaign

Chạy cả hai INT8 candidate với K=2, một warm-up không report và một measured run.

```bash
bash scripts/run-int8-campaign.sh --quick 2>&1 | tee int8-quick.log
```

Hãy chạy bước này trước để giảm lãng phí Kaggle CPU time nếu TorchAO ít có lợi.

## 5. Full qualification campaign

Chỉ chạy sau khi quick mode cho tín hiệu khả quan:

```bash
bash scripts/run-int8-campaign.sh --full 2>&1 | tee int8-full.log
```

Full mode đo K=2/5/10 với một warm-up không report và hai measured repetitions mỗi K, cùng hai measured embedding repetitions.

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

Public API giữ nguyên:

```text
GET  /health
GET  /ready
GET  /v1/models
GET  /v1/stats
POST /v1/embeddings
POST /v1/rerank
```

## Evidence tạo ra cho mỗi candidate

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

Campaign còn tạo:

```text
summary/int8-campaign-summary.json
package/qwen3-dual-4b-cpu-int8-torchao-results-<UTC>.zip
package/<same>.zip.sha256
package/unzip-test.log
```

## Cách diễn giải quan trọng

TorchAO INT8 support trong Transformers được document chính thức cho CPU, nhưng package này chủ đích xem compatibility của Qwen3-Embedding-4B và Qwen3-Reranker-4B là thứ cần **chứng minh**, không được giả định. Model loader fail-closed nếu không quan sát được TorchAO quantized weight tensor modules sau load.

Không thay canonical v0.1.1 tag/history dựa trên experiment này. Nếu cả hai INT8 candidate fail promotion gate, intended branch tiếp theo là dual-4B GGUF / llama.cpp feasibility thay vì tiếp tục FP16 tuning.
