# Contributing
> 🌐 Language / Ngôn ngữ: **English** | [Tiếng Việt](CONTRIBUTING.vi.md)

Thank you for helping improve `qwen3-embedding-reranker-qdrant-stack`.

This project is hosted at https://github.com/dangkhoa2016/Qwen3-Embedding-Reranker-Qdrant-Stack. These guidelines apply to the public repository and to local review work for the `1.0.0` release line.

## Before you start

- Use `SECURITY.md` for vulnerability reports. Do not disclose an unpatched security issue in a public issue.
- Keep changes narrowly scoped and explain the user-visible or operator-visible reason for the change.
- Do not mix documentation/package-hygiene changes with model-semantic changes unless the semantic change is the explicit purpose of the work.
- Use only verified repository, release, package-index, documentation, or funding URLs; do not invent resources that do not exist.

## Development environment

Python `>=3.10` is required. PyTorch is intentionally not pinned/installed by this project because the qualified Kaggle environment supplies it and host-specific PyTorch selection is operator-owned.

A typical local setup is:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

Install an appropriate PyTorch runtime separately when your environment does not already provide one.

Do not commit `.env`, model weights, GGUF files, Qdrant snapshots, runtime binaries, generated evidence, virtual environments, or build output.

## Qualification boundary

The accepted Stage-II R10 qualification is closed unless new evidence directly invalidates it. The following files are protected semantic contract files for publication-hygiene work:

```text
src/qwen_dual_server/config.py
src/qwen_dual_server/gguf_reranker_engine.py
src/qwen_dual_server/production_demo.py
tests/test_gguf_reranker_engine.py
tests/test_production_demo.py
```

A change to any of these files is **not** a routine docs/metadata cleanup. It must be called out explicitly and evaluated for whether Stage-II requalification is required.

Do not casually reopen:

- the H1/H2 semantic experiments;
- K=2 fallback evaluation;
- alternate INT8/GGUF/FP32/FP16 benchmark branches;
- the Stage-II R3→R10 corrective chain;
- the qualified `600s` Run-All gate.

## Tests and verification

For ordinary changes, run the narrowest relevant tests first, then the broader checks required by the scope.

Common commands:

```bash
PYTHONPATH=src pytest -q
python -m compileall -q src scripts
bash -n scripts/*.sh
```

The preserved pre-hardening publication-audit baseline was:

```text
111 passed, 3 failed, 1 skipped
KNOWN_BASELINE_FAILURES=3
```

After adding bilingual/governance/CI hygiene tests, the current expanded local suite records:

```text
116 passed, 3 failed, 1 skipped
BLOCKING_CI_SUITE=116 passed, 1 skipped, 3 deselected
KNOWN_BASELINE_FAILURES=3
NEW_REGRESSION_FAILURES=0
FAILURE_SET_MATCHES_PRE_HARDENING_BASELINE=PASS
```

The same three historical engine-contract nodes remain the only failures. This is not permission to ignore failures: any new failure, unexplained disappearance/replacement of a known failure, or changed failure set must be investigated.

Changes to publication metadata should also verify the built wheel and sdist, including clean wheel installation, version/author/license metadata, manifest integrity, and source re-extraction.

## Documentation changes

Keep the following distinctions precise:

- `1.0.0` is the approved first public version identity;
- `v0.2.3c` is an internal qualified-source label, never a public version;
- `0.2.3rc1` was a temporary local packaging candidate, never published;
- `K5_DEFAULT=ACCEPT`;
- `K2_FALLBACK=NOT_JUSTIFIED`;
- the full regression record is not a zero-failure suite.

Every English/Vietnamese Markdown pair should remain consistent on qualification state, external artifact requirements, and K=5 behavior.

## Pull requests

Use the repository's `.github/PULL_REQUEST_TEMPLATE.md`. A useful pull request should state:

- what changes and why;
- files/components affected;
- whether protected semantic files are touched;
- tests/validation actually run and their exact results;
- any known limitations or follow-up work;
- whether package metadata, build artifacts, or documentation need regeneration.

Do not claim a check passed without fresh output demonstrating that result.

## Style and scope

Prefer small, reviewable changes. Preserve existing public API behavior unless the change explicitly proposes an API change. Avoid unrelated refactors in qualification-sensitive work.

For shell scripts, preserve fail-closed behavior (`set -euo pipefail` where applicable) and check syntax with `bash -n`. For Python, keep changes compatible with the declared Python `>=3.10` baseline.
