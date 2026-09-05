# Contributing
> 🌐 Language / Ngôn ngữ: **English** | [Tiếng Việt](CONTRIBUTING.vi.md)

Thank you for helping improve `qwen3-embedding-reranker-qdrant-stack`.

These guidelines apply to the public `1.0.0` release line.

## Before you start

- Use `SECURITY.md` for vulnerability reports. Do not disclose an unpatched security issue in a public issue.
- Keep changes narrowly scoped and explain the user-visible or operator-visible reason.
- Do not mix documentation/package-hygiene work with model-semantic changes unless the semantic change is the explicit purpose.
- Use only verified repository, release, package-index, documentation, or funding URLs.

## Development environment

Python `>=3.10` is required. PyTorch is intentionally not installed by this project because host-specific PyTorch selection is operator-owned.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

Install an appropriate PyTorch runtime separately when needed.

Do not commit `.env`, model weights, GGUF files, Qdrant snapshots, runtime binaries, generated evidence, virtual environments, or build output.

## Qualification boundary

The following files define qualification-sensitive behavior:

```text
src/qwen_dual_server/config.py
src/qwen_dual_server/gguf_reranker_engine.py
src/qwen_dual_server/production_demo.py
tests/test_gguf_reranker_engine.py
tests/test_production_demo.py
```

A change to these files is not routine documentation/metadata cleanup. Call it out explicitly and decide whether fresh production qualification is required.

The published production-demo defaults are:

```text
Retrieval default: K=5
MAX_INSTRUCTION_CHARS=1024
```

Do not change model semantics, retrieval depth, instruction transport, quantization, concurrency, or performance gates without new evidence appropriate to the change.

## Tests and verification

Run the narrowest relevant tests first, then broader checks required by the scope.

Common commands:

```bash
PYTHONPATH=src pytest -q
python -m compileall -q src scripts
bash -n scripts/*.sh
```

For package/publication changes, also verify:

- source-manifest integrity;
- wheel and sdist construction;
- distribution metadata and contents;
- clean wheel installation where appropriate;
- documentation language-pair consistency.

Do not claim a check passed without fresh output demonstrating that result.

## Documentation changes

Public documentation should:

- use `1.0.0` as the project release identity;
- describe qualification outcomes rather than internal development history;
- keep dependency/runtime versions distinct from the project version;
- keep English/Vietnamese pairs technically consistent;
- preserve commands, hashes, paths, model names, and verified artifact identities accurately.

Historical development notes belong in Git history rather than current public-facing documentation.

## Pull requests

Use `.github/PULL_REQUEST_TEMPLATE.md`. A useful pull request should state:

- what changes and why;
- files/components affected;
- whether qualification-sensitive files are touched;
- tests/validation actually run and their exact results;
- known limitations or follow-up work;
- whether package metadata, build artifacts, or documentation need regeneration.

## Style and scope

Prefer small, reviewable changes. Preserve public API behavior unless an API change is explicit. Avoid unrelated refactors in qualification-sensitive work.

For shell scripts, preserve fail-closed behavior (`set -euo pipefail` where applicable) and check syntax with `bash -n`. For Python, remain compatible with Python `>=3.10`.
