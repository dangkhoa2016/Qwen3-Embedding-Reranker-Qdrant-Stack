# Thiết kế hoàn thiện song ngữ, CI và community files
> 🌐 Language / Ngôn ngữ: [English](2026-09-04-bilingual-ci-community-hardening.md) | **Tiếng Việt**

## Mục tiêu

Hoàn thiện repository GitHub công khai trước `v1.0.0`: tạo cặp tài liệu tiếng Anh/tiếng Việt cho toàn bộ Markdown, bổ sung GitHub Actions CI hiện hành, hoàn thiện các file community cốt lõi trong `.github`, thêm badge/chuyển ngôn ngữ cho README và sửa trạng thái publication cho đúng, nhưng không thay đổi runtime semantic đã được qualification.

## Ràng buộc

- Giữ distribution `qwen3-embedding-reranker-qdrant-stack` ở version `1.0.0`.
- Không sửa 5 file semantic được bảo vệ của Stage-II.
- Giữ historical pre-hardening baseline (`111 passed, 3 failed, 1 skipped`) và yêu cầu expanded suite giữ nguyên three-node failure set; CI phải chặn mọi failure *mới* nhưng có thể tách 3 probe lịch sử liên quan environment/Transformers thành diagnostic không blocking.
- Không thêm PyTorch vào package/runtime dependencies; CI có thể cài PyTorch CPU như tooling riêng của CI.
- Tiếng Anh là filename canonical cho GitHub/PyPI; bản tiếng Việt dùng hậu tố `.vi.md`.
- Amend/rewrite commit logic thứ 10 hiện tại; không tạo commit công khai thứ 11.
- Chưa tạo tag, GitHub Release hay publish PyPI trong thay đổi này.

## Mô hình tài liệu

Mỗi file Markdown trong repository có một bản tiếng Anh canonical và một bản tiếng Việt. Filename tiếng Anh hiện tại được giữ nguyên. Bản tiếng Việt chèn `.vi` trước `.md`, ví dụ `SECURITY.md` -> `SECURITY.vi.md`. Mỗi cặp có link chuyển ngôn ngữ hai chiều; code block, command, hash, model identifier, API path, filename và qualification constant được giữ nguyên.

YAML frontmatter của GitHub issue template vẫn phải nằm đầu file để GitHub nhận diện template; link ngôn ngữ đặt sau frontmatter.

## Thiết kế CI

`.github/workflows/ci.yml` dùng các major action hiện hành đã xác minh ngày 04/09/2026:

- `actions/checkout@v7`
- `actions/setup-python@v7`
- `actions/upload-artifact@v7`

Không gọi trực tiếp `actions/cache` vì `setup-python` có pip cache. Nếu sau này dùng cache trực tiếp thì major hiện hành là `actions/cache@v5`, không phải `@v7`.

CI chạy trên push và pull request vào `main`, với quyền tối thiểu `contents: read`. Có hai job:

1. **quality** — matrix Python 3.10/3.12, cài PyTorch CPU chỉ cho CI cùng dev requirements, compile Python, kiểm tra shell syntax, chạy toàn bộ test trừ 3 baseline probe đã biết, sau đó chạy 3 probe đó như diagnostic không blocking.
2. **package** — Python 3.12, build wheel/sdist, verify metadata/nội dung archive và upload `dist/` bằng `actions/upload-artifact@v7`.

Badge CI chỉ có nghĩa các gate blocking đang xanh; README phải nói rõ đây không phải tuyên bố baseline audit lịch sử có 0 failure.

## Community files

Bổ sung:

- `.github/CODEOWNERS`
- `.github/dependabot.yml`
- `.github/CODE_OF_CONDUCT.md` và `.vi.md`
- `.github/SUPPORT.md` và `.vi.md`
- `.github/ISSUE_TEMPLATE/feature_request.md` và `.vi.md`
- bản tiếng Việt cho các issue/PR template hiện có
- `.github/workflows/ci.yml`

Không thêm funding hoặc release automation ở giai đoạn này.

## Badge README

Cả `README.md` và `README.vi.md` có cùng badge cho CI, Python >=3.10, MIT, version 1.0.0, Qdrant 1.18.3, trạng thái CPU-qualified Stage-II và link chuyển ngôn ngữ hai chiều.

## Sửa trạng thái publication

Source hiện đã công khai trên `main`. README, pre-publish notes, release notes và verification summary phải ghi đúng:

- GitHub source/main: đã publish
- tag `v1.0.0`: chưa tạo
- GitHub Release: chưa tạo
- package index/PyPI: chưa publish

## Verification

Trước khi amend/rewrite:

- mọi Markdown có đủ cặp EN/VI;
- link song ngữ và badge README tồn tại;
- CI YAML parse được và dùng đúng major action hiện hành;
- đủ community files trong `.github`;
- protected files byte-identical với frozen qualified source;
- manifest/static/package checks pass;
- blocking regression không có failure ngoài baseline;
- expanded full local regression ghi nhận `116 passed, 3 failed, 1 skipped`, giữ nguyên ba historical node và không có failure mới;
- final tree sạch.
