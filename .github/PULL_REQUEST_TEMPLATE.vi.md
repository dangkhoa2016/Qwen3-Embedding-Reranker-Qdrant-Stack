# Pull request
> 🌐 Language / Ngôn ngữ: [English](PULL_REQUEST_TEMPLATE.md) | **Tiếng Việt**

## Tóm tắt

Mô tả thay đổi làm gì và vì sao cần thiết.

## Phạm vi

- [ ] Chỉ documentation / governance
- [ ] Package/build metadata
- [ ] Tests/tooling
- [ ] Runtime/API behavior
- [ ] Production-demo behavior

## Qualification boundary

- [ ] Tôi đã kiểm tra thay đổi có chạm qualification-sensitive file hay không.
- [ ] Nếu có, tôi đã giải thích có cần fresh qualification evidence hay không.

Qualification-sensitive files:

```text
src/qwen_dual_server/config.py
src/qwen_dual_server/gguf_reranker_engine.py
src/qwen_dual_server/production_demo.py
tests/test_gguf_reranker_engine.py
tests/test_production_demo.py
```

## Verification

Liệt kê exact commands đã chạy và exact outcomes.

```text
<commands and results>
```

- [ ] Relevant regression/static checks đã chạy.
- [ ] Build/manifest/re-extraction checks đã chạy lại nếu package/publication files thay đổi.
- [ ] Secrets và private paths đã được loại khỏi logs/evidence.
- [ ] Documentation links và English/Vietnamese pairs đã được kiểm tra khi documentation thay đổi.

## Documentation / release impact

Liệt kê README, production-demo docs, release notes, metadata hoặc provenance files cần synchronized updates.
