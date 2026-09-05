# qwen3-embedding-reranker-qdrant-stack 1.0.0
> 🌐 Language / Ngôn ngữ: [English](RELEASE_NOTES_v1.0.0.md) | **Tiếng Việt**

**Release identity: `qwen3-embedding-reranker-qdrant-stack` `1.0.0`.**

`1.0.0` là phiên bản phát hành công khai đầu tiên của dự án này.

```text
Package: qwen3-embedding-reranker-qdrant-stack
Version: 1.0.0
Author: Đăng Khoa <i.am@dangkhoa.dev>
License: MIT
Python: >=3.10
```

## Điểm nổi bật

- FastAPI service theo hướng CPU cho Qwen3 embedding và reranking.
- Qwen3-Embedding-4B trên Transformers / PyTorch CPU FP16 path đã được kiểm chứng.
- Qwen3-Reranker-4B `Q4_K_M` GGUF production-demo path qua llama.cpp runtime đã được harden.
- Qdrant `1.18.3` với canonical snapshot song ngữ 20K point.
- `/v1/*` API có bearer authentication, fail-closed startup/authentication và giới hạn CPU concurrency thận trọng.
- Kaggle production-demo notebook có thể tái hiện, operator scripts, qualification summary và provenance records.

## Kiểm chứng production

- Fresh Kaggle CPU qualification: **PASS**.
- Semantic validation: **3/3 PASS**.
- cgroup OOM events: **0**.
- cgroup OOM-kill events: **0**.
- End-to-end Run All: `594.964s`, nằm trong ngưỡng kiểm chứng `600s`.
- Độ sâu truy hồi mặc định: `K=5`.

Kết quả thời gian chỉ áp dụng cho môi trường đã được kiểm chứng và không phải cam kết hiệu năng chung cho mọi CPU.

## Xác minh

GitHub CI kiểm tra Python 3.10 và Python 3.12, chạy toàn bộ regression suite ở chế độ blocking và xác minh wheel/sdist.

## Packaging và deployment

- Package/runtime identity là `1.0.0`.
- Package metadata MIT theo SPDX/PEP 639 và file `LICENSE` được bao gồm.
- `MAX_INSTRUCTION_CHARS=1024` được ghi trong example configuration.
- Model weights, GGUF files, llama.cpp runtime files, PyTorch và Qdrant snapshot là external deployment inputs và không được bundle trong Python package.

Kết quả qualification và artifact identities đã xác minh nằm trong `PRODUCTION_QUALIFICATION.vi.md` và `PRODUCTION_DEMO_PROVENANCE.vi.md`.

## Bảo mật và đóng góp

- Hướng dẫn security và vulnerability reporting: `SECURITY.vi.md`.
- Hướng dẫn contribution và verification: `CONTRIBUTING.vi.md`.

Security vulnerabilities phải được báo riêng thay vì public issue.

## Kênh phát hành

```text
Source repository: GitHub
Release identity: v1.0.0
GitHub Release: kênh release theo tag cho canonical release assets
Package index / PyPI: kênh publication riêng
```

Publication qua một kênh không đồng nghĩa đã publication qua kênh khác; từng kênh được kiểm chứng độc lập.
