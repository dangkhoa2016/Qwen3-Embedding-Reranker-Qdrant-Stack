# qwen3-embedding-reranker-qdrant-stack 1.0.0

> English | [Tiếng Việt](RELEASE_NOTES_v1.0.0.vi.md)

**Status: GitHub source published on `main`; first-release tag and GitHub Release pending.**
Repository: https://github.com/dangkhoa2016/Qwen3-Embedding-Reranker-Qdrant-Stack. The source tree is public on `main`; no `v1.0.0` tag or GitHub Release has been created yet at this checkpoint.

## First public release identity

`1.0.0` is the approved first public version of this project. Internal qualification labels such as `v0.2.3c` and the temporary local packaging label `0.2.3rc1` were never public releases.

```text
Package: qwen3-embedding-reranker-qdrant-stack
Version: 1.0.0
Author: Đăng Khoa <i.am@dangkhoa.dev>
License: MIT
Python: >=3.10
```

## Highlights

- CPU-oriented FastAPI service for Qwen3 embedding and reranking workloads.
- Qwen3-Embedding-4B qualified on the Transformers / PyTorch CPU FP16 path.
- Qwen3-Reranker-4B `Q4_K_M` GGUF production-demo path through the hardened llama.cpp runtime.
- Qdrant `1.18.3` canonical 20K bilingual snapshot workflow.
- Bearer-authenticated `/v1/*` API with fail-closed startup/authentication behavior and conservative CPU concurrency limits.
- Reproducible Kaggle production-demo notebook, provenance records, and operator scripts.

## Qualified production baseline

- Stage-II R10 fresh Kaggle qualification: PASS.
- Stage-II corrective chain R3→R10: CLOSED.
- Three of three semantic cases: PASS.
- cgroup OOM and OOM-kill deltas: zero.
- Post-package Run All: `594.964s` within the `600s` gate.
- `K5_DEFAULT=ACCEPT`.
- `K2_FALLBACK=NOT_JUSTIFIED`.
- `FINAL_RELEASE_DEFAULT=K5_READY`.

The timing result is specific to the qualified environment and is not a general CPU performance guarantee.

## Packaging and publication hygiene

The pre-publication work prepares:

- package/runtime identity `1.0.0`;
- MIT SPDX package metadata and shipped `LICENSE` file;
- author metadata;
- README long-description/package metadata;
- public-facing keywords/classifiers with the real GitHub project URLs;
- `MAX_INSTRUCTION_CHARS=1024` in the example configuration;
- source manifest/build hygiene;
- `SECURITY.md` and `CONTRIBUTING.md`;
- `.github` issue and pull-request templates for the public repository.

The qualified production semantic files remain protected by byte-identity checks during this publication-hygiene work.

## External artifacts

Large model weights, the GGUF reranker artifact, hardened llama runtime, PyTorch runtime, and Qdrant snapshot are not bundled with the Python package. The qualified identities and reproduction requirements are documented in `STAGE2_R10_QUALIFICATION.md` and `PRODUCTION_DEMO_PROVENANCE.md`.

## Security and contributions

- Vulnerability reporting and deployment-security guidance: `SECURITY.md`.
- Contribution, testing, and requalification-boundary guidance: `CONTRIBUTING.md`.

Security vulnerabilities should be reported privately rather than disclosed in a public issue.

## Known test baseline

The preserved pre-hardening audit baseline was `111 passed, 3 failed, 1 skipped`. The expanded bilingual/governance/CI-hardening suite records:

```text
116 passed, 3 failed, 1 skipped
BLOCKING_CI_SUITE=116 passed, 1 skipped, 3 deselected
KNOWN_BASELINE_FAILURES=3
NEW_REGRESSION_FAILURES=0
FAILURE_SET_MATCHES_PRE_HARDENING_BASELINE=PASS
```

The same three historical engine-contract nodes remain the only failures. This release note must not be interpreted as claiming a zero-failure full suite.

## Publication status

Publication checkpoint:

```text
Source publication to `main`: complete
Tag `v1.0.0`: not created yet
GitHub Release: not created yet
Package index / PyPI: not published
```

Tagging and GitHub Release creation remain separate verified steps after final repository hardening.
