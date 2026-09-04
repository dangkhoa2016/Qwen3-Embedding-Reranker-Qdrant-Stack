# qwen3-embedding-reranker-qdrant-stack 1.0.0
> 🌐 Language / Ngôn ngữ: [English](RELEASE_NOTES_v1.0.0.md) | **Tiếng Việt**

**Release identity: `qwen3-embedding-reranker-qdrant-stack` `1.0.0`.**
Repository: https://github.com/dangkhoa2016/Qwen3-Embedding-Reranker-Qdrant-Stack. Việc publish source trên GitHub, publish GitHub Release theo tag và publish lên package index là các kênh phát hành riêng, được kiểm chứng độc lập.

## First public release identity

`1.0.0` là public version đầu tiên đã được phê duyệt. Internal qualification labels như `v0.2.3c` và temporary local packaging label `0.2.3rc1` chưa từng là public releases.

```text
Package: qwen3-embedding-reranker-qdrant-stack
Version: 1.0.0
Author: Đăng Khoa <i.am@dangkhoa.dev>
License: MIT
Python: >=3.10
```

## Điểm nổi bật

- CPU-oriented FastAPI service cho Qwen3 embedding và reranking workloads.
- Qwen3-Embedding-4B qualified trên Transformers / PyTorch CPU FP16 path.
- Qwen3-Reranker-4B `Q4_K_M` GGUF production-demo path qua hardened llama.cpp runtime.
- Qdrant `1.18.3` canonical 20K bilingual snapshot workflow.
- Bearer-authenticated `/v1/*` API với fail-closed startup/authentication và conservative CPU concurrency limits.
- Kaggle production-demo notebook có thể tái hiện, provenance records và operator scripts.

## Qualified production baseline

- Stage-II R10 fresh Kaggle qualification: PASS.
- Stage-II corrective chain R3→R10: CLOSED.
- Ba trên ba semantic cases: PASS.
- cgroup OOM và OOM-kill deltas: zero.
- Post-package Run All: `594.964s` trong gate `600s`.
- `K5_DEFAULT=ACCEPT`.
- `K2_FALLBACK=NOT_JUSTIFIED`.
- `FINAL_RELEASE_DEFAULT=K5_READY`.

Timing result chỉ áp dụng qualified environment và không phải general CPU performance guarantee.

## Packaging và publication hygiene

Pre-release work chuẩn bị:

- package/runtime identity `1.0.0`;
- MIT SPDX package metadata và shipped `LICENSE` file;
- author metadata;
- README long-description/package metadata;
- public-facing keywords/classifiers với real GitHub project URLs;
- `MAX_INSTRUCTION_CHARS=1024` trong example configuration;
- source manifest/build hygiene;
- `SECURITY.md`/`.vi.md` và `CONTRIBUTING.md`/`.vi.md`;
- bilingual `.github` issue/pull-request templates, community files và CI workflow.

Qualified production semantic files vẫn được bảo vệ bằng byte-identity checks trong publication-hygiene work.

## External artifacts

Large model weights, GGUF reranker artifact, hardened llama runtime, PyTorch runtime và Qdrant snapshot không bundle trong Python package. Qualified identities và reproduction requirements nằm trong `STAGE2_R10_QUALIFICATION.vi.md`/`.md` và `PRODUCTION_DEMO_PROVENANCE.vi.md`/`.md`.

## Bảo mật và đóng góp

- Vulnerability reporting và deployment-security guidance: `SECURITY.vi.md`/`SECURITY.md`.
- Contribution, testing và requalification-boundary guidance: `CONTRIBUTING.vi.md`/`CONTRIBUTING.md`.

Security vulnerabilities phải được báo riêng thay vì public issue.

## Known test baseline

Pre-hardening audit baseline được giữ lại là `111 passed, 3 failed, 1 skipped`. Một snapshot local audit sau bilingual/governance/CI hardening được bảo tồn ghi nhận:

```text
HISTORICAL_LOCAL_EXPANDED_SUITE=116 passed, 3 failed, 1 skipped
KNOWN_HISTORICAL_FAILURES=3
NEW_REGRESSION_FAILURES=0
FAILURE_SET_MATCHES_PRE_HARDENING_BASELINE=PASS
```

Các con số trên là historical audit evidence, không phải live blocking-CI count. Release-candidate blocking gate ghi nhận:

```text
BLOCKING_CI_SUITE=119 passed, 1 skipped, 3 deselected
HISTORICAL_COMPATIBILITY_PROBES=executed separately
```

Ba engine-contract node là toàn bộ failure set trong historical local audit đã được bảo tồn. CI chạy chúng riêng như compatibility probes, vì vậy kết quả dưới dependency environment hiện tại không viết lại historical record đó. Claim release chính xác là các blocking CI gate pass; release note này không claim một test suite luôn zero-failure trên mọi dependency environment.

## Kênh phát hành

```text
Source repository: GitHub
Release identity: v1.0.0
GitHub Release: kênh release theo tag cho canonical release assets
Package index / PyPI: kênh publication riêng
```

Publication qua một kênh không đồng nghĩa đã publication qua kênh khác; từng kênh được kiểm chứng độc lập.
