# Bilingual CI and Community Hardening Implementation Plan
> 🌐 Language / Ngôn ngữ: **English** | [Tiếng Việt](2026-09-04-bilingual-ci-community-hardening.vi.md)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Finalize bilingual documentation, current CI, GitHub community files, README badges, and publication-state wording before the first `v1.0.0` tag.

**Architecture:** Keep English canonical filenames and add `.vi.md` companions; enforce completeness with repository-hygiene tests. Add one least-privilege CI workflow that separates blocking regression tests from the three historical known probes and builds verified Python distributions.

**Tech Stack:** Python 3.10/3.12, pytest, setuptools/build, GitHub Actions, YAML, Markdown.

**Spec:** `docs/superpowers/specs/2026-09-04-bilingual-ci-community-hardening.md`

## Global Constraints

- Public distribution stays `qwen3-embedding-reranker-qdrant-stack==1.0.0`.
- Do not modify the five protected Stage-II semantic files.
- Preserve the historical `111 passed, 3 failed, 1 skipped` baseline and reject any new failure; the expanded hardening suite may add passing governance tests only.
- GitHub Actions majors: checkout v7, setup-python v7, upload-artifact v7; direct cache, if used, v5.
- PyTorch remains CI-only, not a package dependency.
- Amend the tenth logical-history commit; no new public commit.

---

### Task 1: Add repository-hygiene RED tests

**Files:**
- Modify: `tests/test_public_repository_hygiene.py`

**Interfaces:**
- Consumes: current repository tree.
- Produces: assertions for bilingual Markdown pairs, badges, CI action versions, community files, and publication state.

- [ ] Add tests that fail while `.vi.md` companions, `ci.yml`, community files, badges, and corrected publication state are missing.
- [ ] Run targeted tests and confirm failures are caused by missing requested features.

### Task 2: Add CI and community files

**Files:**
- Create: `.github/workflows/ci.yml`
- Create: `.github/CODEOWNERS`
- Create: `.github/dependabot.yml`
- Create: `.github/CODE_OF_CONDUCT.md`, `.github/CODE_OF_CONDUCT.vi.md`
- Create: `.github/SUPPORT.md`, `.github/SUPPORT.vi.md`
- Create: `.github/ISSUE_TEMPLATE/feature_request.md`, `.vi.md`
- Create: Vietnamese companions for existing issue/PR templates.

**Interfaces:**
- Consumes: `requirements-dev.txt`, `pyproject.toml`, existing pytest node IDs.
- Produces: blocking quality/package CI and GitHub community metadata.

- [ ] Implement least-privilege CI with current action majors and Python 3.10/3.12.
- [ ] Keep three historical tests non-blocking diagnostics while all other tests block on failure.
- [ ] Add bilingual community templates and maintenance configuration.
- [ ] Run targeted tests.

### Task 3: Add bilingual companions for every Markdown file

**Files:**
- Create: `.vi.md` companion for each canonical `.md` that lacks one.
- Modify: canonical Markdown files only as needed for reciprocal language navigation and publication-state corrections.

**Interfaces:**
- Consumes: canonical English Markdown text.
- Produces: equivalent Vietnamese documentation preserving technical literals.

- [ ] Translate root documentation.
- [ ] Translate `docs/hybrid-gguf`, production-demo, and historical plan/spec documentation.
- [ ] Preserve commands, hashes, paths, constants, model names, and evidence values verbatim.
- [ ] Run bilingual completeness tests.

### Task 4: README badges and final publication state

**Files:**
- Modify: `README.md`
- Create/modify: `README.vi.md`
- Modify: `PRE_PUBLISH_NOTES.md`, `RELEASE_NOTES_v1.0.0.md`, `VERIFICATION_SUMMARY.txt`
- Modify: `MANIFEST.in`

**Interfaces:**
- Produces: accurate pre-tag public state and package-visible bilingual governance docs.

- [ ] Add matching CI/Python/MIT/version/Qdrant/CPU-qualified badges and language links to both README files.
- [ ] Remove stale wording that source/main is not yet public.
- [ ] Include core Vietnamese governance docs in sdist manifest.
- [ ] Run targeted tests and static checks.

### Task 5: Full verification and amend history

**Files:**
- No semantic production file changes.
- Amend current logical-history commit 10.

**Interfaces:**
- Consumes: completed repository tree.
- Produces: verified 10-commit bundle and safe force-with-lease rewrite script.

- [ ] Verify all protected files byte-identical to frozen source.
- [ ] Run full pytest and confirm only the three accepted baseline failures in the local audit environment.
- [ ] Validate Markdown pair coverage, YAML parse, shell syntax, manifest, wheel/sdist build, and clean install.
- [ ] Amend commit 10 with author/committer timestamp aligned to 2026-09-04 publication timeline.
- [ ] Create and verify bundle plus guarded rewrite script for the exact current remote HEAD.
