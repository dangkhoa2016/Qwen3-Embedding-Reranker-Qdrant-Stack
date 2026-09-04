# qwen3-embedding-reranker-qdrant-stack 1.0.0

**Status: local pre-publication draft.**  
This project has not yet been published and has no remote repository, tag, or release.

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
- public-facing keywords/classifiers without invented project URLs;
- `MAX_INSTRUCTION_CHARS=1024` in the example configuration;
- source manifest/build hygiene;
- `SECURITY.md` and `CONTRIBUTING.md`;
- local `.github` issue and pull-request templates for a future repository.

The qualified production semantic files remain protected by byte-identity checks during this publication-hygiene work.

## External artifacts

Large model weights, the GGUF reranker artifact, hardened llama runtime, PyTorch runtime, and Qdrant snapshot are not bundled with the Python package. The qualified identities and reproduction requirements are documented in `STAGE2_R10_QUALIFICATION.md` and `PRODUCTION_DEMO_PROVENANCE.md`.

## Security and contributions

- Vulnerability reporting and deployment-security guidance: `SECURITY.md`.
- Contribution, testing, and requalification-boundary guidance: `CONTRIBUTING.md`.

Security vulnerabilities should be reported privately rather than disclosed in a public issue.

## Known test baseline

The verified local regression baseline is:

```text
111 passed, 3 failed, 1 skipped
KNOWN_BASELINE_FAILURES=3
NEW_REGRESSION_FAILURES=0
FULL_REGRESSION_BASELINE_MATCH=PASS
```

The three failures are known historical environment/Transformers-compatibility failures in the audit baseline. This release note must not be interpreted as claiming a zero-failure full suite.

## Publication status

Creating a repository, adding a remote, pushing, creating tags/releases, or publishing wheel/sdist artifacts remains outside this draft and requires an explicit later publication decision.
