# Pull request
> 🌐 Language / Ngôn ngữ: **English** | [Tiếng Việt](PULL_REQUEST_TEMPLATE.vi.md)

## Summary

Describe what this change does and why it is needed.

## Scope

- [ ] Documentation / governance only
- [ ] Package/build metadata
- [ ] Tests/tooling
- [ ] Runtime/API behavior
- [ ] Production-demo behavior

## Qualification boundary

- [ ] I checked whether this change touches a qualification-sensitive file.
- [ ] If it does, I explained whether fresh qualification evidence is required.

Qualification-sensitive files:

```text
src/qwen_dual_server/config.py
src/qwen_dual_server/gguf_reranker_engine.py
src/qwen_dual_server/production_demo.py
tests/test_gguf_reranker_engine.py
tests/test_production_demo.py
```

## Verification

List the exact commands run and their exact outcomes.

```text
<commands and results>
```

- [ ] Relevant regression/static checks were run.
- [ ] Build/manifest/re-extraction checks were rerun if package/publication files changed.
- [ ] Secrets and private paths were removed from logs/evidence.
- [ ] Documentation links and English/Vietnamese pairs were checked when documentation changed.

## Documentation / release impact

List README, production-demo docs, release notes, metadata, or provenance files that need synchronized updates.
