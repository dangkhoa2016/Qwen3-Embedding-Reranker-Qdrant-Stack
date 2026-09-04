# Pull request
> 🌐 Language / Ngôn ngữ: [English](PULL_REQUEST_TEMPLATE.md) | **Tiếng Việt**

## Tóm tắt

Mô tả thay đổi làm gì và vì sao cần thiết.

## Phạm vi

- [ ] Chỉ tài liệu / governance
- [ ] Package/build metadata
- [ ] Tests/tooling
- [ ] Runtime/API behavior
- [ ] Production-demo behavior

## Qualification boundary

- [ ] Tôi đã kiểm tra thay đổi có chạm protected semantic file hay không.
- [ ] Nếu có chạm protected semantic file, tôi đã nêu rõ và giải thích có cần requalification không.

Protected semantic files cho publication-hygiene work:

```text
src/qwen_dual_server/config.py
src/qwen_dual_server/gguf_reranker_engine.py
src/qwen_dual_server/production_demo.py
tests/test_gguf_reranker_engine.py
tests/test_production_demo.py
```

## Verification

Liệt kê command chính xác đã chạy và kết quả chính xác. Không viết “all tests pass” khi audit baseline đã verify là `116 passed, 3 failed, 1 skipped` (expanded hardening suite; same three historical nodes).

```text
<commands and results>
```

- [ ] Không có regression failure mới.
- [ ] Đã chạy static validation phù hợp với các file thay đổi.
- [ ] Đã chạy lại build/manifest/re-extraction checks nếu package/publication files thay đổi.
- [ ] Đã xóa secret và private path khỏi log/evidence.

## Ảnh hưởng tài liệu / release

Liệt kê README, production-demo docs, release notes, metadata hoặc provenance files cần cập nhật đồng bộ.
