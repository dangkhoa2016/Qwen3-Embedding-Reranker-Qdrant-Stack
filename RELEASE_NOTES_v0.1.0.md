# v0.1.0 Release Notes
> 🌐 Language / Ngôn ngữ: **English** | [Tiếng Việt](RELEASE_NOTES_v0.1.0.vi.md)

Initial qualification release for a CPU/RAM-only shared Qwen3 search inference server.

Highlights:

- one FastAPI process / one Uvicorn worker;
- Qwen3-Embedding-4B + Qwen3-Reranker-4B singleton residency;
- native Transformers/PyTorch CPU path;
- FP16 default, BF16 configurable candidate, no runtime FP32 fallback;
- last-token pooling and FP32 L2-normalized 2560-d embeddings;
- official Qwen reranker yes/no logit scoring;
- fail-closed Kaggle model discovery;
- staged dual-model load with OOM-delta and memory-headroom gates;
- global inference concurrency fixed at one;
- Bearer auth, rate/request limits, bounded queue;
- public `/ready` is intentionally minimal; detailed model/memory diagnostics require auth;
- startup memory monitor, smoke client, evidence packager and OpenCode Kaggle runbook.

Real two-model Kaggle residency is the next acceptance step. This source release does not claim that result before the supplied runbook is executed on the target ~30 GiB Kaggle CPU environment.
