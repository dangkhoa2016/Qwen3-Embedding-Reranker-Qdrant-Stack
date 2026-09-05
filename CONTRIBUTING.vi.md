# Đóng góp
> 🌐 Language / Ngôn ngữ: [English](CONTRIBUTING.md) | **Tiếng Việt**

Cảm ơn bạn đã giúp cải thiện `qwen3-embedding-reranker-qdrant-stack`.

Các hướng dẫn này áp dụng cho public release line `1.0.0`.

## Trước khi bắt đầu

- Dùng `SECURITY.vi.md` cho vulnerability reports. Không công khai security issue chưa được patch trong public issue.
- Giữ thay đổi có phạm vi hẹp và giải thích lý do user-visible hoặc operator-visible.
- Không trộn documentation/package-hygiene work với model-semantic changes trừ khi semantic change là mục tiêu rõ ràng.
- Chỉ dùng repository, release, package-index, documentation hoặc funding URL đã xác minh.

## Development environment

Yêu cầu Python `>=3.10`. PyTorch được chủ đích không cài bởi dự án vì việc chọn PyTorch theo host thuộc trách nhiệm operator.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

Cài PyTorch runtime phù hợp riêng khi cần.

Không commit `.env`, model weights, GGUF files, Qdrant snapshots, runtime binaries, generated evidence, virtual environments hoặc build output.

## Qualification boundary

Các file sau định nghĩa behavior nhạy cảm với qualification:

```text
src/qwen_dual_server/config.py
src/qwen_dual_server/gguf_reranker_engine.py
src/qwen_dual_server/production_demo.py
tests/test_gguf_reranker_engine.py
tests/test_production_demo.py
```

Thay đổi vào các file này không phải documentation/metadata cleanup thông thường. Phải nêu rõ và quyết định có cần fresh production qualification hay không.

Các default production demo đã publish:

```text
Retrieval default: K=5
MAX_INSTRUCTION_CHARS=1024
```

Không thay model semantics, retrieval depth, instruction transport, quantization, concurrency hoặc performance gates nếu không có evidence mới phù hợp.

## Tests và verification

Chạy các test hẹp nhất có liên quan trước, sau đó chạy broader checks phù hợp phạm vi.

Các lệnh thường dùng:

```bash
PYTHONPATH=src pytest -q
python -m compileall -q src scripts
bash -n scripts/*.sh
```

Với package/publication changes, cần xác minh thêm:

- source-manifest integrity;
- wheel và sdist;
- distribution metadata và contents;
- clean wheel installation khi phù hợp;
- consistency của documentation language pairs.

Không claim một check đã pass nếu chưa có fresh output chứng minh.

## Documentation changes

Public documentation phải:

- dùng `1.0.0` làm project release identity;
- mô tả qualification outcomes thay vì internal development history;
- phân biệt dependency/runtime versions với project version;
- giữ các cặp English/Vietnamese nhất quán về kỹ thuật;
- bảo tồn chính xác commands, hashes, paths, model names và verified artifact identities.

Historical development notes nên nằm trong Git history thay vì current public-facing documentation.

## Pull requests

Dùng `.github/PULL_REQUEST_TEMPLATE.vi.md`. Một pull request hữu ích nên nêu:

- thay đổi gì và vì sao;
- files/components bị ảnh hưởng;
- có chạm qualification-sensitive files hay không;
- tests/validation thực tế đã chạy và exact results;
- known limitations hoặc follow-up;
- package metadata, build artifacts hoặc documentation có cần regenerate hay không.

## Style và scope

Ưu tiên thay đổi nhỏ, dễ review. Giữ public API behavior trừ khi API change được nêu rõ. Tránh unrelated refactors trong qualification-sensitive work.

Với shell scripts, giữ fail-closed behavior (`set -euo pipefail` khi phù hợp) và check syntax bằng `bash -n`. Với Python, giữ compatibility với Python `>=3.10`.
