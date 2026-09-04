# Pre-release publication notes

> English | [Tiếng Việt](PRE_PUBLISH_NOTES.vi.md)

This file records the final pre-tag publication checkpoint for the first public release of `qwen3-embedding-reranker-qdrant-stack`. Source is now published on the GitHub `main` branch; tag, GitHub Release, and package-index publication remain separate steps.

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

GitHub repository and source publication on `main` are complete. No `v1.0.0` tag or GitHub Release has been created yet at this checkpoint, and no package-index publication is implied.

Internal labels `v0.2.3c` and `0.2.3rc1` are provenance only and were never public versions.

## Qualification boundary

Stage-II R10 is closed. Do not reopen H1/H2 experiments, K=2 fallback evaluation, alternate quantization campaigns, or the R3→R10 corrective chain without new evidence that directly invalidates the accepted qualification.

## Protected semantics

The five qualified semantic files listed in `PRODUCTION_DEMO_PROVENANCE.md` must remain byte-identical during publication-hygiene edits.

## Regression verification

The preserved pre-hardening audit baseline was `111 passed, 3 failed, 1 skipped`. The expanded bilingual/governance/CI-hardening suite now records:

```text
116 passed
3 failed
1 skipped
BLOCKING_CI_SUITE=116 passed, 1 skipped, 3 deselected
KNOWN_BASELINE_FAILURES=3
NEW_REGRESSION_FAILURES=0
FAILURE_SET_MATCHES_PRE_HARDENING_BASELINE=PASS
```

Do not rewrite this as “all tests pass.” Any change in the three-node failure set requires investigation before packaging.

## Public-facing repository/package audit

The public-facing audit added/refined `README.md`, PEP 639 package metadata, `SECURITY.md`, `CONTRIBUTING.md`, and `.github` issue/pull-request templates. After the repository was created at https://github.com/dangkhoa2016/Qwen3-Embedding-Reranker-Qdrant-Stack, real project URLs were added to package metadata.

```text
PUBLIC_FACING_REPOSITORY_AUDIT=PASS
GITHUB_TEMPLATES_PREPARED_BILINGUAL=YES
CODE_OF_CONDUCT=PREPARED_BILINGUAL
DEPENDABOT=PREPARED
PROJECT_URLS=REAL_GITHUB_URLS_ADDED
```
