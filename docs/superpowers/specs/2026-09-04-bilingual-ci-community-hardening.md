# Bilingual CI and Community Hardening Design

> English | [Tiếng Việt](2026-09-04-bilingual-ci-community-hardening.vi.md)

## Goal

Finalize the public GitHub repository before `v1.0.0` by making all Markdown documentation bilingual (English/Vietnamese), adding a current GitHub Actions CI workflow, completing core `.github` community files, adding README badges/language navigation, and correcting publication-state wording without changing the qualified semantic runtime.

## Constraints

- Keep `qwen3-embedding-reranker-qdrant-stack` at version `1.0.0`.
- Do not modify the five Stage-II protected semantic files.
- Preserve the historical pre-hardening baseline (`111 passed, 3 failed, 1 skipped`) and require the expanded suite to retain the same three-node failure set; CI must reject any *new* failure but may isolate the three known historical environment/Transformers compatibility probes.
- Keep PyTorch out of package/runtime dependencies; CI may install a CPU-only PyTorch build as CI tooling.
- English remains canonical for GitHub/PyPI filenames; Vietnamese companions use `.vi.md`.
- Amend/rewrite the existing tenth logical-history commit; do not create an eleventh public commit.
- No tag, GitHub Release, or PyPI publication in this change.

## Documentation model

Every repository Markdown file has an English canonical file and a Vietnamese companion. Existing English filenames remain unchanged. The Vietnamese companion inserts `.vi` before `.md`, e.g. `SECURITY.md` -> `SECURITY.vi.md`. Each pair contains reciprocal language navigation while preserving code blocks, commands, hashes, model identifiers, API paths, filenames, and qualification constants verbatim.

GitHub issue-template frontmatter remains the first block so GitHub continues to recognize the templates. Language navigation appears after frontmatter in issue templates.

## CI design

`.github/workflows/ci.yml` will use the current major action lines verified on 2026-09-04:

- `actions/checkout@v7`
- `actions/setup-python@v7`
- `actions/upload-artifact@v7`

`actions/cache` is not called directly because `setup-python` provides pip caching. If direct cache usage is added later, the current major is `actions/cache@v5`, not `@v7`.

CI runs on pushes and pull requests to `main`, with least-privilege `contents: read`. It has:

1. **quality** — Python 3.10/3.12 matrix, install CI-only CPU PyTorch plus dev requirements, compile Python, validate shell syntax, run all tests except the three known baseline probes, then run those three probes as non-blocking diagnostic evidence.
2. **package** — Python 3.12, build wheel/sdist, verify metadata and archive contents, and upload `dist/` using `actions/upload-artifact@v7`.

The workflow badge means the blocking CI gates are green; README text explicitly states it is not a claim that the historical audit baseline had zero failures.

## Community files

Add:

- `.github/CODEOWNERS`
- `.github/dependabot.yml`
- `.github/CODE_OF_CONDUCT.md` and `.vi.md`
- `.github/SUPPORT.md` and `.vi.md`
- `.github/ISSUE_TEMPLATE/feature_request.md` and `.vi.md`
- Vietnamese companions for existing issue/PR templates
- `.github/workflows/ci.yml`

Do not add funding or release automation in this phase.

## README badges

Both `README.md` and `README.vi.md` receive matching badges for CI, Python >=3.10, MIT, version 1.0.0, Qdrant 1.18.3, and CPU-qualified Stage-II status, plus reciprocal language links.

## Publication-state correction

Current source is already public on `main`. README, pre-publish notes, release notes, and verification summary must say:

- GitHub source/main: published
- `v1.0.0` tag: not yet created
- GitHub Release: not yet created
- package index/PyPI: not published

## Verification

Before amend/rewrite:

- all Markdown EN/VI pairs exist;
- bilingual links and README badges are present;
- CI YAML parses and contains current action majors;
- `.github` community files exist;
- protected files remain byte-identical to the frozen qualified source;
- manifest/static/package checks pass;
- blocking regression suite has no unexpected failures;
- expanded full local regression records `116 passed, 3 failed, 1 skipped`, with the same three known historical nodes and no new failures;
- final tree is clean.
