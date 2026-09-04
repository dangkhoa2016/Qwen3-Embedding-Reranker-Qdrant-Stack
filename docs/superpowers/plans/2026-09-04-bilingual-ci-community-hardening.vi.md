# Kế hoạch triển khai hoàn thiện song ngữ, CI và community files
> 🌐 Language / Ngôn ngữ: [English](2026-09-04-bilingual-ci-community-hardening.md) | **Tiếng Việt**

> **Dành cho agentic workers:** cần dùng sub-skill `superpowers:subagent-driven-development` (khuyến nghị) hoặc `superpowers:executing-plans` để triển khai từng task. Các bước dùng checkbox (`- [ ]`).

**Mục tiêu:** Hoàn thiện tài liệu song ngữ, CI hiện hành, community files GitHub, badge README và wording trạng thái publication trước tag `v1.0.0` đầu tiên.

**Kiến trúc:** Giữ filename tiếng Anh làm canonical và thêm bản `.vi.md`; dùng repository-hygiene tests để bắt thiếu cặp. Thêm một CI workflow quyền tối thiểu, tách regression blocking khỏi ba probe lịch sử đã biết, đồng thời build/verify Python distributions.

**Tech Stack:** Python 3.10/3.12, pytest, setuptools/build, GitHub Actions, YAML, Markdown.

**Spec:** `docs/superpowers/specs/2026-09-04-bilingual-ci-community-hardening.vi.md`

## Ràng buộc toàn cục

- Distribution công khai giữ `qwen3-embedding-reranker-qdrant-stack==1.0.0`.
- Không sửa 5 file semantic Stage-II được bảo vệ.
- Giữ historical baseline `111 passed, 3 failed, 1 skipped` và chặn mọi failure mới; expanded hardening suite chỉ được phép tăng số test pass.
- Major GitHub Actions: checkout v7, setup-python v7, upload-artifact v7; cache trực tiếp nếu dùng là v5.
- PyTorch chỉ là CI-only, không phải package dependency.
- Amend commit logic thứ 10; không thêm public commit mới.

---

### Task 1: Thêm repository-hygiene RED tests

**Files:** `tests/test_public_repository_hygiene.py`.

- [ ] Thêm test cho cặp Markdown EN/VI, badges, phiên bản action trong CI, community files và publication state.
- [ ] Chạy targeted tests và xác nhận fail đúng vì các tính năng yêu cầu chưa tồn tại.

### Task 2: Thêm CI và community files

**Files:** `.github/workflows/ci.yml`, `CODEOWNERS`, `dependabot.yml`, Code of Conduct, Support, feature-request template và các bản `.vi.md` tương ứng.

- [ ] Implement CI quyền tối thiểu với action major hiện hành và Python 3.10/3.12.
- [ ] Giữ 3 historical test làm diagnostic không blocking; mọi test còn lại phải blocking.
- [ ] Thêm community templates song ngữ và maintenance config.
- [ ] Chạy targeted tests.

### Task 3: Tạo bản tiếng Việt cho mọi Markdown

- [ ] Dịch tài liệu root.
- [ ] Dịch `docs/hybrid-gguf`, production-demo và các plan/spec lịch sử.
- [ ] Giữ nguyên command, hash, path, constant, model name và evidence value.
- [ ] Chạy test completeness song ngữ.

### Task 4: Badge README và publication state cuối

- [ ] Thêm badge CI/Python/MIT/version/Qdrant/CPU-qualified và link ngôn ngữ ở cả `README.md`/`README.vi.md`.
- [ ] Xóa wording cũ nói source/main chưa public.
- [ ] Include các governance docs tiếng Việt cốt lõi trong sdist manifest.
- [ ] Chạy targeted/static checks.

### Task 5: Full verification và amend history

- [ ] Verify protected files byte-identical với frozen source.
- [ ] Chạy full pytest và xác nhận chỉ có 3 accepted baseline failures trong local audit environment.
- [ ] Validate pair Markdown, YAML, shell syntax, manifest, wheel/sdist và clean install.
- [ ] Amend commit 10 với timestamp phù hợp timeline publication ngày 04/09/2026.
- [ ] Tạo bundle verify được và script rewrite `force-with-lease` có guard remote HEAD chính xác.
