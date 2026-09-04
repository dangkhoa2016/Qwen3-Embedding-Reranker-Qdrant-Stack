> English | [Tiếng Việt](PULL_REQUEST_TEMPLATE.vi.md)

## Summary

Describe what this change does and why it is needed.

## Scope

- [ ] Documentation / governance only
- [ ] Package/build metadata
- [ ] Tests/tooling
- [ ] Runtime/API behavior
- [ ] Production-demo behavior

## Qualification boundary

- [ ] I checked whether this change touches a protected semantic file.
- [ ] If a protected semantic file is touched, I have called that out explicitly and explained whether requalification is required.

Protected semantic files for publication-hygiene work:

```text
src/qwen_dual_server/config.py
src/qwen_dual_server/gguf_reranker_engine.py
src/qwen_dual_server/production_demo.py
tests/test_gguf_reranker_engine.py
tests/test_production_demo.py
```

## Verification

List the exact commands run and paste/summarize their exact outcomes. Do not write “all tests pass” when the current verified audit baseline is `116 passed, 3 failed, 1 skipped` (expanded hardening suite; same three historical nodes).

```text
<commands and results>
```

- [ ] No new regression failure was introduced.
- [ ] Static validation appropriate to the changed files was run.
- [ ] Build/manifest/re-extraction checks were rerun if package/publication files changed.
- [ ] Secrets and private paths were removed from logs/evidence.

## Documentation / release impact

List README, production-demo docs, release notes, metadata, or provenance files that need synchronized updates.
