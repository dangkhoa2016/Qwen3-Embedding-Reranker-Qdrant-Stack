# qwen3-embedding-reranker-qdrant-stack 1.0.0
> 🌐 Language / Ngôn ngữ: **English** | [Tiếng Việt](RELEASE_NOTES_v1.0.0.vi.md)

**Release identity: `qwen3-embedding-reranker-qdrant-stack` `1.0.0`.**

`1.0.0` is the first public release of this project.

```text
Package: qwen3-embedding-reranker-qdrant-stack
Version: 1.0.0
Author: Đăng Khoa <i.am@dangkhoa.dev>
License: MIT
Python: >=3.10
```

## Highlights

- CPU-oriented FastAPI service for Qwen3 embedding and reranking workloads.
- Qwen3-Embedding-4B on the qualified Transformers / PyTorch CPU FP16 path.
- Qwen3-Reranker-4B `Q4_K_M` GGUF production-demo path through a hardened llama.cpp runtime.
- Qdrant `1.18.3` canonical 20K bilingual snapshot workflow.
- Bearer-authenticated `/v1/*` API with fail-closed startup/authentication behavior and conservative CPU concurrency limits.
- Reproducible Kaggle production-demo notebook, operator scripts, qualification summary, and provenance records.

## Production qualification

- Fresh Kaggle CPU qualification: **PASS**.
- Semantic validation: **3/3 PASS**.
- cgroup OOM events: **0**.
- cgroup OOM-kill events: **0**.
- End-to-end Run All: `594.964s`, within the `600s` qualification threshold.
- Default retrieval depth: `K=5`.

The timing result is specific to the qualified environment and is not a general CPU performance guarantee.

## Verification

GitHub CI verifies Python 3.10 and Python 3.12, runs the full blocking regression suite, and verifies wheel/sdist construction.

## Packaging and deployment

- Package/runtime identity is `1.0.0`.
- MIT SPDX/PEP 639 package metadata and the `LICENSE` file are included.
- `MAX_INSTRUCTION_CHARS=1024` is documented in the example configuration.
- Model weights, GGUF files, llama.cpp runtime files, PyTorch, and the Qdrant snapshot are external deployment inputs and are not bundled with the Python package.

Verified qualification results and artifact identities are documented in `PRODUCTION_QUALIFICATION.md` and `PRODUCTION_DEMO_PROVENANCE.md`.

## Security and contributions

- Security and vulnerability-reporting guidance: `SECURITY.md`.
- Contribution and verification guidance: `CONTRIBUTING.md`.

Security vulnerabilities should be reported privately rather than disclosed in a public issue.

## Publication channels

```text
Source repository: GitHub
Release identity: v1.0.0
GitHub Release: tagged release channel for canonical release assets
Package index / PyPI: separate publication channel
```

Publication through one channel does not imply publication through another; each channel is verified independently.
