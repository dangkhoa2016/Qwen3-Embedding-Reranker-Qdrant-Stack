# Đóng góp
> 🌐 Language / Ngôn ngữ: [English](CONTRIBUTING.md) | **Tiếng Việt**

Cảm ơn bạn đã giúp cải thiện `qwen3-embedding-reranker-qdrant-stack`.

Dự án được host tại https://github.com/dangkhoa2016/Qwen3-Embedding-Reranker-Qdrant-Stack. Các hướng dẫn này áp dụng cho public repository và local review work của release line `1.0.0`.

## Trước khi bắt đầu

- Dùng `SECURITY.vi.md`/`SECURITY.md` để báo vulnerability. Không công khai security issue chưa được patch trong public issue.
- Giữ thay đổi có phạm vi hẹp và giải thích rõ lý do user-visible hoặc operator-visible.
- Không trộn documentation/package-hygiene changes với model-semantic changes, trừ khi semantic change chính là mục đích rõ ràng của công việc.
- Chỉ dùng URL repository, release, package-index, documentation hoặc funding đã được xác minh; không tự tạo resource chưa tồn tại.

## Môi trường phát triển

Yêu cầu Python `>=3.10`. PyTorch chủ đích không bị pin/cài bởi dự án vì qualified Kaggle environment đã cung cấp nó và việc chọn PyTorch theo host thuộc trách nhiệm operator.

Một local setup điển hình:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

Nếu môi trường chưa có PyTorch, hãy cài runtime phù hợp riêng.

Không commit `.env`, model weights, GGUF files, Qdrant snapshots, runtime binaries, generated evidence, virtual environments hoặc build output.

## Qualification boundary

Stage-II R10 qualification đã chấp nhận được xem là đóng, trừ khi có evidence mới trực tiếp làm mất hiệu lực kết quả đó. Các file sau là protected semantic contract files đối với publication-hygiene work:

```text
src/qwen_dual_server/config.py
src/qwen_dual_server/gguf_reranker_engine.py
src/qwen_dual_server/production_demo.py
tests/test_gguf_reranker_engine.py
tests/test_production_demo.py
```

Thay đổi bất kỳ file nào trong số này **không** phải cleanup docs/metadata thông thường. Phải nêu rõ và đánh giá xem có cần Stage-II requalification không.

Không tùy tiện mở lại:

- H1/H2 semantic experiments;
- K=2 fallback evaluation;
- alternate INT8/GGUF/FP32/FP16 benchmark branches;
- Stage-II R3→R10 corrective chain;
- qualified `600s` Run-All gate.

## Tests và verification

Với thay đổi thông thường, chạy narrowest relevant tests trước, rồi các broader checks tương ứng scope.

Các command thường dùng:

```bash
PYTHONPATH=src pytest -q
python -m compileall -q src scripts
bash -n scripts/*.sh
```

Pre-hardening publication-audit baseline được giữ lại là:

```text
111 passed, 3 failed, 1 skipped
KNOWN_BASELINE_FAILURES=3
```

Expanded suite sau bilingual/governance/CI hardening hiện ghi nhận:

```text
116 passed, 3 failed, 1 skipped
BLOCKING_CI_SUITE=116 passed, 1 skipped, 3 deselected
KNOWN_BASELINE_FAILURES=3
NEW_REGRESSION_FAILURES=0
FAILURE_SET_MATCHES_PRE_HARDENING_BASELINE=PASS
```

Ba historical engine-contract node cũ vẫn là toàn bộ failure set. Điều này không cho phép bỏ qua failure: failure mới, sự biến mất/thay thế của known failure mà không có giải thích, hoặc changed failure set đều phải được điều tra.

Thay đổi publication metadata cũng phải verify wheel/sdist đã build, gồm clean wheel installation, version/author/license metadata, manifest integrity và source re-extraction.

## Thay đổi tài liệu

Giữ các phân biệt sau chính xác:

- `1.0.0` là first public version identity đã được phê duyệt;
- `v0.2.3c` là internal qualified-source label, chưa từng là public version;
- `0.2.3rc1` là temporary local packaging candidate, chưa từng publish;
- `K5_DEFAULT=ACCEPT`;
- `K2_FALLBACK=NOT_JUSTIFIED`;
- full regression record không phải zero-failure suite.

Mọi cặp Markdown English/Vietnamese phải đồng bộ về qualification state, external artifact requirements, K=5 behavior và publication state.

## Pull requests

Dùng `.github/PULL_REQUEST_TEMPLATE.md` hoặc bản tiếng Việt tương ứng. Một pull request hữu ích nên nêu:

- thay đổi gì và vì sao;
- file/component bị ảnh hưởng;
- có chạm protected semantic files không;
- tests/validation thực sự đã chạy và exact results;
- known limitations hoặc follow-up work;
- package metadata, build artifacts hoặc documentation có cần regenerate không.

Không claim check đã pass nếu chưa có fresh output chứng minh.

## Style và scope

Ưu tiên thay đổi nhỏ, dễ review. Giữ public API behavior hiện tại trừ khi thay đổi chủ đích đề xuất API change. Tránh unrelated refactor trong qualification-sensitive work.

Với shell scripts, giữ fail-closed behavior (`set -euo pipefail` khi phù hợp) và kiểm tra syntax bằng `bash -n`. Với Python, giữ tương thích baseline Python `>=3.10`.
