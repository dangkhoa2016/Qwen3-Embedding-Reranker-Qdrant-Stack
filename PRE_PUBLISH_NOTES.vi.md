# Ghi chú publication trước khi tạo tag
> 🌐 Language / Ngôn ngữ: [English](PRE_PUBLISH_NOTES.md) | **Tiếng Việt**

File này ghi lại final pre-tag publication checkpoint cho public release đầu tiên của `qwen3-embedding-reranker-qdrant-stack`. Source hiện đã được publish trên branch GitHub `main`; tag, GitHub Release và package-index publication vẫn là các bước riêng.

```text
PUBLIC_VERSION=1.0.0
AUTHOR=Đăng Khoa <i.am@dangkhoa.dev>
LICENSE=MIT
PUBLICATION_STATE=GITHUB_SOURCE_PUBLISHED_ON_MAIN
REMOTE_REPOSITORY=https://github.com/dangkhoa2016/Qwen3-Embedding-Reranker-Qdrant-Stack
GITHUB_REPOSITORY=https://github.com/dangkhoa2016/Qwen3-Embedding-Reranker-Qdrant-Stack
MAIN_SOURCE=PUBLISHED
TAG=NONE
RELEASE=NONE
```

GitHub repository và source publication trên `main` đã hoàn tất. Tại checkpoint này chưa tạo tag `v1.0.0` hoặc GitHub Release và cũng không ngụ ý đã publish package index.

Internal labels `v0.2.3c` và `0.2.3rc1` chỉ là provenance và chưa từng là public versions.

## Qualification boundary

Stage-II R10 đã đóng. Không mở lại H1/H2 experiments, K=2 fallback evaluation, alternate quantization campaigns hoặc R3→R10 corrective chain nếu không có evidence mới trực tiếp làm mất hiệu lực qualification đã chấp nhận.

## Protected semantics

Năm qualified semantic files được liệt kê trong `PRODUCTION_DEMO_PROVENANCE.vi.md`/`PRODUCTION_DEMO_PROVENANCE.md` phải giữ byte-identical trong publication-hygiene edits.

## Regression verification

Pre-hardening audit baseline được giữ lại là `111 passed, 3 failed, 1 skipped`. Expanded suite sau bilingual/governance/CI hardening hiện ghi nhận:

```text
116 passed
3 failed
1 skipped
BLOCKING_CI_SUITE=116 passed, 1 skipped, 3 deselected
KNOWN_BASELINE_FAILURES=3
NEW_REGRESSION_FAILURES=0
FAILURE_SET_MATCHES_PRE_HARDENING_BASELINE=PASS
```

Không được viết lại thành “all tests pass”. Mọi thay đổi trong three-node failure set đều phải được điều tra trước packaging.

## Public-facing repository/package audit

Public-facing audit đã thêm/chỉnh `README.md`, PEP 639 package metadata, `SECURITY.md`, `CONTRIBUTING.md` và `.github` issue/pull-request templates. Sau khi repository được tạo tại https://github.com/dangkhoa2016/Qwen3-Embedding-Reranker-Qdrant-Stack, các project URL thật đã được thêm vào package metadata.

```text
PUBLIC_FACING_REPOSITORY_AUDIT=PASS
GITHUB_TEMPLATES_PREPARED_BILINGUAL=YES
CODE_OF_CONDUCT=PREPARED_BILINGUAL
DEPENDABOT=PREPARED
PROJECT_URLS=REAL_GITHUB_URLS_ADDED
```
