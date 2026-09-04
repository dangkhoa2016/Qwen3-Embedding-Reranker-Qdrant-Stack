# Contributing

Thank you for helping improve `qwen3-embedding-reranker-qdrant-stack`.

This source is currently a local pre-publication candidate for the first public release (`1.0.0`). The guidelines below are prepared for the future public repository as well as local review work; they do not imply that a remote repository already exists.

## Before you start

- Use `SECURITY.md` for vulnerability reports. Do not disclose an unpatched security issue in a public issue.
- Keep changes narrowly scoped and explain the user-visible or operator-visible reason for the change.
- Do not mix documentation/package-hygiene changes with model-semantic changes unless the semantic change is the explicit purpose of the work.
- Do not invent repository, release, package-index, documentation, or funding URLs before those resources exist.

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

The verified pre-publication audit environment currently records:

```text
111 passed, 3 failed, 1 skipped
KNOWN_BASELINE_FAILURES=3
NEW_REGRESSION_FAILURES=0
FULL_REGRESSION_BASELINE_MATCH=PASS
```

The three failures are known historical environment/Transformers-compatibility failures from the audit baseline. This is not permission to ignore failures: a new failure, disappearance/replacement of one of the known failures without explanation, or a changed failure set must be investigated.

Changes to publication metadata should also verify the built wheel and sdist, including clean wheel installation, version/author/license metadata, manifest integrity, and source re-extraction.

## Documentation changes

Keep the following distinctions precise:

- `1.0.0` is the approved first public version identity;
- `v0.2.3c` is an internal qualified-source label, never a public version;
- `0.2.3rc1` was a temporary local packaging candidate, never published;
- `K5_DEFAULT=ACCEPT`;
- `K2_FALLBACK=NOT_JUSTIFIED`;
- the full regression record is not a zero-failure suite.

English and Vietnamese production-demo documentation should remain consistent on qualification state, external artifact requirements, and K=5 behavior.

## Pull requests

When a repository is later created, use the prepared `.github/PULL_REQUEST_TEMPLATE.md`. A useful pull request should state:

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
