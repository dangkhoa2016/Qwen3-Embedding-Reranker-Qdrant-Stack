# Release Notes v0.1.0

> [English](RELEASE_NOTES_v0.1.0.md) | Tiếng Việt

Qualification release ban đầu cho shared Qwen3 search inference server chạy chỉ CPU/RAM.

Điểm nổi bật:

- một FastAPI process / một Uvicorn worker;
- Qwen3-Embedding-4B + Qwen3-Reranker-4B singleton residency;
- native Transformers/PyTorch CPU path;
- mặc định FP16, BF16 là candidate có thể cấu hình, không có runtime FP32 fallback;
- last-token pooling và FP32 L2-normalized embedding 2560 chiều;
- official Qwen reranker yes/no logit scoring;
- fail-closed Kaggle model discovery;
- staged dual-model load với OOM-delta và memory-headroom gates;
- global inference concurrency cố định bằng một;
- Bearer auth, rate/request limits, bounded queue;
- public `/ready` chủ đích tối giản; detailed model/memory diagnostics yêu cầu auth;
- startup memory monitor, smoke client, evidence packager và OpenCode Kaggle runbook.

Real two-model Kaggle residency là acceptance step tiếp theo. Source release này không claim kết quả đó trước khi supplied runbook được chạy trên target Kaggle CPU environment khoảng 30 GiB.
